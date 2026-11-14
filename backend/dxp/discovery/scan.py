"""discovery.scan (A05, Story 10.1, AD-25, V2, V40).

`scan(scope_id, ctx)` runs inside a `discover` run (or, through `run_scan`, a task's run):

1. reads the research scope and its cursor;
2. takes one admission, item key `"<scope_id>|search_source|-|<scope_id>|<cursor>"` (AD-21);
3. evaluates the gate as `search_source` to `source:clinicaltrials.gov`, target
   `"<scope_id>|<cursor>"`, before any request; a blocked scan makes no request and leaves only
   the gate's one blocked Decision;
4. claims the gate's `queued` action (`queued` -> `dispatching`, conditional, AD-20) and queries
   the ClinicalTrials.gov API v2 with `query.term` = the scope's assay names and search terms
   (OR-joined, quoted), `query.cond` = the scope's condition and
   `filter.advanced = AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]`, every page up to a fixed cap;
5. writes each result as an immutable source version and points its `source_items` document at
   it (`sources.load.store_record`, window "discovered", `scope_ids`);
6. records the action `delivered` with `{ http_status, cursor_from, cursor_to, source_refs, count }`
   FIRST, then advances the cursor, by one conditional update on the scope's `version` and current
   cursor (adding 1 to `version`), only when every page was read, the run is still `running` and
   the action was settled; a failed, blocked or stopped scan, or a failed settle, leaves it where
   it was, so nothing is skipped and the cursor never moves while the action is `dispatching`;
7. records `Run.scan { cursor_from, cursor_to, query, source_refs }` and one `scan_finished` event, so the
   run audit shows the sources fetched with the cursor used and the cursor after (V14).

`search_source` is a read: a timeout or error is `failed` and raises `ScanError`; the cursor is
unchanged. The returned source refs are in last-update order, newest first, with the verified
scope's `priority_refs` first (the anchor verified at 10:45, for DXP_DEMO_PACE); `Run.scan.source_refs`
holds them in that order, and `scan_finished` also records the ordering rule and the priority list.

Writers: `runs.scan` only through `runs.record_scan()` (A07+A11) and the action's status and result
only through `actions.record_source_result()` (A09); this module writes source items, source
versions and the scope cursor, and emits `scan_finished`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from dxp import actions, gate, runs, store
from dxp.api.models import ProposedAction, RunContext, Target
from dxp.sources import ctgov
from dxp.sources import load as source_load

DESTINATION = "source:clinicaltrials.gov"
KIND = "search_source"
SCOPES = "research_scopes"
ORDER_RULE = "priority_refs first, then last_update_post_date descending"


class ScanError(RuntimeError):
    """The scan did not finish: the action is `failed` and the cursor did not move."""


@dataclass
class ScanOutcome:
    status: str  # done | blocked | not_admitted | failed
    scope_id: str
    cursor_from: str | None = None
    cursor_to: str | None = None
    cursor_advanced: bool = False
    complete: bool = False
    source_refs: list[str] = field(default_factory=list)
    changed_refs: list[str] = field(default_factory=list)  # known items that moved to a new version (V40)
    query: dict[str, Any] = field(default_factory=dict)
    decision_id: str | None = None
    action_id: str | None = None
    http_status: int | None = None


def _db() -> Any:
    return store.get_db()


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# The query (V2, AD-25)
# ---------------------------------------------------------------------------


def _strings(values: Any) -> list[str]:
    return [v for v in (values or []) if isinstance(v, str) and v.strip()]


def search_terms(scope: dict[str, Any]) -> list[str]:
    """The scope's assay names, then its search terms (`aliases`, AD-25). Search terms only widen
    the query; they never resolve a name to a Diagnostic (V34). The gate's check 2 allows exactly
    these terms (A06)."""
    terms = _strings(scope.get("assays")) + _strings(scope.get("aliases"))
    out: list[str] = []
    for t in terms:
        if t not in out:
            out.append(t)
    return out


def condition_terms(scope: dict[str, Any]) -> list[str]:
    """The scope's condition, then any `condition_aliases` (for example "NSCLC")."""
    out = _strings([scope.get("condition")])
    for t in _strings(scope.get("condition_aliases")):
        if t not in out:
            out.append(t)
    return out


def build_query(scope: dict[str, Any], cursor: str) -> dict[str, str]:
    conds = condition_terms(scope)
    cond = conds[0] if len(conds) == 1 else ctgov.or_terms(conds)
    return {
        "query.term": ctgov.or_terms(search_terms(scope)),
        "query.cond": cond,
        "filter.advanced": ctgov.last_update_filter(cursor),
    }


# ---------------------------------------------------------------------------
# Action settling (AD-20 claim and observed outcome, with this module as the sender)
# ---------------------------------------------------------------------------


async def _emit(type_: str, dedupe_key: str, ctx: RunContext, **fields: Any) -> None:
    await store.emit_event(
        type_, dedupe_key=dedupe_key, stamp=ctx.stamp.model_dump(), run_id=ctx.run_id, mode=ctx.mode, **fields
    )


async def _claim(action_id: str) -> dict[str, Any] | None:
    """`queued` -> `dispatching` through the actions module (A09, AD-20). Returns None when this
    worker claimed it; otherwise the existing action (read only)."""
    if await actions.record_source_result(action_id, status="dispatching", result=None):
        return None
    return await _db()["actions"].find_one({"_id": action_id}) or {"_id": action_id, "status": "missing"}


async def _settle(action_id: str | None, status: str, result: dict[str, Any]) -> bool:
    """`dispatching` -> `delivered` | `failed` with the observed result, through the actions module.
    True when this call settled the action (or there is no action to settle)."""
    if not action_id:
        return True
    return bool(await actions.record_source_result(action_id, status=status, result=result))


async def _run_status(run_id: str | None) -> str | None:
    if not run_id:
        return None
    run = await _db()["runs"].find_one({"_id": run_id}, {"status": 1})
    return (run or {}).get("status")


# ---------------------------------------------------------------------------
# The scan
# ---------------------------------------------------------------------------


async def scan(scope_id: str, ctx: RunContext) -> list[str]:
    """Gated search_source to source:clinicaltrials.gov; returns the source_refs updated since the
    scope's cursor; the cursor advances only after the scan finishes."""
    return (await run_scan(scope_id, ctx)).source_refs


async def run_scan(
    scope_id: str,
    ctx: RunContext,
    *,
    max_results: int | None = None,
    advance_cursor: bool | None = None,
) -> ScanOutcome:
    """The scan with its outcome. `max_results` caps the records (a task's grant limit, A25, sent to
    the gate as the requested count). The cursor moves only for an uncapped scan unless
    `advance_cursor` says otherwise: a capped search never moves the discover scope's cursor."""
    if advance_cursor is None:
        advance_cursor = max_results is None
    if not ctx.run_id:
        raise ValueError("discovery.scan runs only inside a run (AD-17)")
    scope = await _db()[SCOPES].find_one({"_id": scope_id})
    if scope is None:
        raise LookupError(f"research scope {scope_id!r} not found")
    raw_cursor = (scope.get("cursor") or {}).get("last_update_post_date")
    cursor = source_load.cursor_text(raw_cursor)
    if not cursor:
        raise ValueError(f"{scope_id}: the scope has no cursor (OD2)")
    query = build_query(scope, cursor)
    outcome = ScanOutcome(status="not_admitted", scope_id=scope_id, cursor_from=cursor, cursor_to=cursor, query=query)

    target = f"{scope_id}|{cursor}"
    admission = await runs.admit(ctx.run_id, f"{scope_id}|{KIND}|-|{target}")
    if admission is None:
        return outcome  # not admitted: nothing attempted, no request
    try:
        actx = ctx.model_copy(update={"admission_id": admission.id})
        decision = await gate.evaluate(
            actx,
            ProposedAction(
                kind=KIND,
                destination=DESTINATION,
                target=Target(scope_id=scope_id),
                inputs={
                    "scope_id": scope_id,
                    "cursor": cursor,
                    "query": {
                        "scope_id": scope_id,
                        "terms": search_terms(scope),
                        "condition": scope.get("condition"),
                        "condition_terms": condition_terms(scope),
                        "cursor": cursor,
                        "params": query,
                    },
                    "requested_count": max_results,
                },
            ),
        )
        outcome.decision_id = decision.id
        outcome.action_id = decision.action_id
        if decision.outcome != "allowed":
            outcome.status = "blocked"
            return outcome  # the gate recorded the Decision and action_blocked; no request

        if outcome.action_id:
            existing = await _claim(outcome.action_id)
            if existing is not None:
                # A repeat of the same run step: never query twice.
                result = existing.get("result") or {}
                if existing.get("status") == "delivered":
                    outcome.status = "done"
                    outcome.source_refs = list(result.get("source_refs") or [])
                    outcome.cursor_to = result.get("cursor_to", cursor)
                    return outcome
                raise ScanError(f"search_source action {outcome.action_id} is {existing.get('status')}, not queued")

        try:
            found = await ctgov.search(
                query["query.term"], query["query.cond"], cursor, max_results=max_results
            )
            outcome.http_status = found.http_status
            outcome.complete = found.complete
            records = [ctgov.parse_study(s) for s in found.studies]
            for record in records:
                stored = await source_load.store_record(
                    record, window="discovered", set_name="discover", scope_id=scope_id, run_id=ctx.run_id
                )
                if stored.changed:
                    outcome.changed_refs.append(stored.source_ref)
        except Exception as exc:
            outcome.status = "failed"
            await _settle(
                outcome.action_id, "failed",
                {"http_status": getattr(exc, "http_status", None), "cursor_from": cursor, "cursor_to": cursor,
                 "source_refs": [], "count": 0},
            )
            raise ScanError(f"scan of {scope_id} failed: {type(exc).__name__}") from exc

        priority = _strings(scope.get("priority_refs"))
        outcome.source_refs = ctgov.order_refs(records, priority)
        seen = max((r["last_update_post_date"] for r in records if r.get("last_update_post_date")), default=None)
        new_cursor = max(cursor, seen) if seen else cursor

        cond: dict[str, Any] = {"_id": scope_id, "cursor.last_update_post_date": raw_cursor}
        if "version" in scope:
            cond["version"] = scope["version"]
        will_advance = (
            advance_cursor
            and outcome.complete
            and await _run_status(ctx.run_id) == "running"
            and await _db()[SCOPES].find_one(cond, {"_id": 1}) is not None  # nobody moved it since our read
        )

        # The action is settled BEFORE the cursor moves (PR #27 review, item e): a failure to settle
        # raises or returns False and leaves the cursor where it was, so the cursor can never have
        # moved while the action is still `dispatching`. The result's cursor_to is the cursor this
        # scan sets; Run.scan records whether the conditional update below then matched.
        outcome.status = "done"
        settled = await _settle(
            outcome.action_id, "delivered",
            {"http_status": outcome.http_status, "cursor_from": cursor,
             "cursor_to": new_cursor if will_advance else cursor,
             "source_refs": outcome.source_refs, "count": len(outcome.source_refs)},
        )
        if will_advance and settled:
            res = await _db()[SCOPES].update_one(
                cond,
                {
                    "$set": {"cursor": {"last_update_post_date": new_cursor, "set_at": _now(), "set_by_run_id": ctx.run_id}},
                    "$inc": {"version": 1},
                },
            )
            outcome.cursor_advanced = bool(res.matched_count)
        if outcome.cursor_advanced:
            outcome.cursor_to = new_cursor

        await runs.record_scan(
            ctx.run_id,
            {"cursor_from": cursor, "cursor_to": outcome.cursor_to, "query": query,
             "source_refs": outcome.source_refs, "count": len(outcome.source_refs),
             "complete": outcome.complete, "cursor_advanced": outcome.cursor_advanced},
        )
        await _emit(
            "scan_finished", f"scan_finished|{ctx.run_id}|{scope_id}|{cursor}", ctx,
            scope_id=scope_id, decision_id=decision.id, action_id=outcome.action_id,
            cursor_from=cursor, cursor_to=outcome.cursor_to, cursor_advanced=outcome.cursor_advanced,
            complete=outcome.complete, count=len(outcome.source_refs), changed_refs=outcome.changed_refs,
            source_refs=outcome.source_refs, order={"rule": ORDER_RULE, "priority_refs": priority},
        )
        return outcome
    finally:
        await runs.release(admission.id)

