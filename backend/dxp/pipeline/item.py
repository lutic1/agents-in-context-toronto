"""One Source item through the run (Story 1.7, AD-12, V21, V40): extract, check, retrieve,
remember, relate, draft, gate, file, notify.

Rules kept here:
- The item's `version_id` is read once, from the Source item's current pointer, and pinned:
  it goes into the extraction input, every Finding, the retrieval exclusion, the new side of
  every relationship, both drafts, the report and the alert's evidence reference (V40).
- One admission per action (D22), taken after extraction and before the gate, with
  `item_key = "<source_ref>|<kind>|<diagnostic_id or '-'>|<target>"`; every admission is
  released once, in a `finally`, whatever the action's outcome. A refused admission means
  that action is not attempted (`runs.admit` counts it).
- Two gated drafts (V21): `reports.draft()` returns the final draft at the top level and
  `drafts`, each self-contained (draft 1 without memories, draft 2 with them). Each draft is
  filed with its own `reports.file(draft, ctx, final)` call under its own admission: every
  draft but the last with `final=False` (gate only, nothing written, no `updates`), the last
  with `final=True` (#38). Targets are `"<report_id>|draft1"`, `|draft2`. If the last is
  blocked, the item redrafts once (`attempt: 1`, targets `|draft<n>.r1`, new Decisions); a
  second block ends the item with nothing filed (V7).
- One `notify_slack` per filed report, dispatched by the run alone through
  `actions.dispatch()` after the final `reports.file` succeeds (V11; `reports.file` never
  sends it). A blocked report gets no alert. A blocked alert (A09 raises `ActionBlocked`) is a
  blocked step, not an item failure. The version is marked processed only after the alert's
  outcome is recorded. The run never calls ElevenLabs or HeyGen (V29).
- The node never raises: an error becomes a failure line with a code, never source text.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from dxp import actions, identity, llm, memory, reports, retrieval, runs
from dxp.api.models import EvidenceRef, ProposedAction, RunContext, Target
from dxp.pipeline import config, progress

log = logging.getLogger("dxp.pipeline")

# The gate's claim-check vocabulary (V7, V22): a record without posted results asks for the
# memories about performance or results claims (M1 on the demo path).
NO_RESULTS_CLAIM_KIND = "claim_performed_or_results"


@dataclass
class RunInfo:
    """What every item of one run shares."""

    run_id: str
    ctx: RunContext
    scope_id: str | None
    team_id: str | None
    seeded_names: list[str]
    tracker: progress.Progress


@dataclass
class ItemResult:
    source_ref: str
    status: str  # done | failed | skipped | not_started
    version_id: str | None = None
    report_id: str | None = None
    filed: bool = False
    draft_decisions: list[Any] = field(default_factory=list)
    alert: Any = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "status": self.status,
            "version_id": self.version_id,
            "report_id": self.report_id,
            "filed": self.filed,
            "error": self.error,
        }


class ItemFailed(Exception):
    """An item failure with a code; its message never holds source text."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


# ---------------------------------------------------------------------------
# Small helpers: other PRs may return pydantic models or plain dicts
# ---------------------------------------------------------------------------


def get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def plain(obj: Any) -> Any:
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        return dump()
    return obj


def outcome(decision: Any) -> str | None:
    return get(decision, "outcome")


def admission_id(admission: Any) -> str | None:
    if admission is None:
        return None
    if isinstance(admission, str):
        return admission
    return get(admission, "id") or get(admission, "_id")


def item_key(source_ref: str, kind: str, diagnostic_id: str | None, target: str) -> str:
    return f"{source_ref}|{kind}|{diagnostic_id or '-'}|{target}"


async def admit(run_id: str, key: str) -> str | None:
    return admission_id(await runs.admit(run_id, key))


async def release(admission_ids: list[str]) -> None:
    for adm in admission_ids:
        try:
            await runs.release(adm)
        except Exception as exc:  # noqa: BLE001 - one failed release must not skip the others
            log.warning("release failed admission=%s error=%s", adm, type(exc).__name__)


def with_admission(ctx: RunContext, adm: str) -> RunContext:
    return ctx.model_copy(update={"admission_id": adm})


def is_a09(exc: BaseException, name: str) -> bool:
    """A09's `actions.dispatch` raises named exceptions. Matched by name so this module does
    not depend on A09 being merged."""
    cls = getattr(actions, name, None)
    if isinstance(cls, type) and isinstance(exc, cls):
        return True
    return type(exc).__name__ == name


def is_action_blocked(exc: BaseException) -> bool:
    """The gate blocked the action: A09 recorded the Decision; nothing was sent."""
    return is_a09(exc, "ActionBlocked")


# A09 errors that end the notify step without failing the item (nothing was sent):
# the webhook or base URL is missing or malformed (the action stays queued), or the report
# could not be read.
NOTIFY_NOT_SENT = ("SenderNotConfigured", "ReportNotFound")


def report_id_for(run_id: str, source_ref: str) -> str:
    return identity.derive("rep_", run_id, source_ref)


def check_report(drafted: Any, version_id: str) -> dict[str, Any]:
    """`reports.draft()` (A19+A20) returns the final draft's fields at the top level and
    `drafts`, the self-contained drafts to file in order (draft 1 without memories, draft 2 with
    them, V21). Only the final draft carries `updates`, as `[{finding_id, change}]`. Every
    draft is pinned to the item's version (V40)."""
    drafted = plain(drafted)
    if not isinstance(drafted, dict):
        raise ItemFailed("draft_shape")
    drafted = dict(drafted)
    if drafted.get("version_id") not in (None, version_id):
        raise ItemFailed("draft_version_mismatch")
    drafted["version_id"] = version_id  # V40: the report uses the version this item pinned
    drafts = []
    for one in drafted.get("drafts") or []:
        one = dict(plain(one))
        if one.get("version_id") not in (None, version_id):
            raise ItemFailed("draft_version_mismatch")
        one["version_id"] = version_id
        drafts.append(one)
    drafted["drafts"] = drafts or None
    return drafted


def draft_targets(drafted: dict[str, Any], report_id: str) -> list[tuple[dict[str, Any] | None, str]]:
    """The AD-3 gate target of each draft `reports.file()` will evaluate, in order, matching
    A19+A20's `gate_target`: `<report_id>|draft<n>`, or `|draft<n>.r<k>` on redraft k."""
    attempt = int(drafted.get("attempt") or 0)
    suffix = f".r{attempt}" if attempt else ""
    drafts = drafted.get("drafts") or [None]
    out = []
    for index, one in enumerate(drafts):
        number = int(((one or drafted).get("draft")) or (index + 1))
        out.append((one, f"{report_id}|draft{number}{suffix}"))
    return out


def change_target(finding_id: Any, change: dict[str, Any]) -> str:
    """AD-3 target of a per-change file_proposal: the proposal ID A06 will derive,
    `derive("p_", finding_id, field, value)`, else "<field>|<value>"."""
    if change.get("proposal_id"):
        return str(change["proposal_id"])
    fld, value = change.get("field"), change.get("value")
    if finding_id and fld is not None and value is not None:
        return identity.derive("p_", str(finding_id), str(fld), str(value))
    return f"{fld}|{value}"


def memory_tags(item: dict[str, Any]) -> dict[str, Any] | None:
    """Memories are matched on claim kind, never assay (V22). A record without posted results
    asks for the memories of claim kind `claim_performed_or_results` (M1 on the demo path)."""
    if item.get("has_results") is True:
        return None
    return {"claim_kind": NO_RESULTS_CLAIM_KIND}


def is_early_research(findings: list[dict[str, Any]]) -> bool:
    try:
        from dxp.schema.registry import is_early_research as early
    except ImportError:  # pragma: no cover - A02 is on main
        return False
    for f in findings:
        stage = get(get(f, "stage_evidence"), "stage")
        if stage and early(stage):
            return True
    return False


# ---------------------------------------------------------------------------
# The steps
# ---------------------------------------------------------------------------


async def load(source_ref: str, info: RunInfo) -> tuple[dict[str, Any], str] | None:
    """The item dict for extraction and its pinned version ID; None when already processed."""
    src, version = await progress.load_source(source_ref)
    if src is None:
        raise ItemFailed("source_item_missing")
    if version is None:
        raise ItemFailed("source_version_missing")
    version_id = version["_id"]
    if progress.processed(src, info.scope_id, version_id):
        return None
    item = {k: v for k, v in src.items() if k not in ("_id", "processed", "embedding")}
    item.update({k: v for k, v in version.items() if k not in ("_id", "embedding")})
    item.update({"source_ref": source_ref, "version_id": version_id})
    return item, version_id


async def extract(item: dict[str, Any], info: RunInfo) -> list[dict[str, Any]] | None:
    """`llm.extract` then `llm.check` on each Finding. None: not relevant (done, nothing filed)."""
    extraction = plain(await llm.extract(item, info.seeded_names))
    status = get(extraction, "status", "extracted")
    if status == "not_relevant":
        return None
    if status == "failed":
        codes = [get(f, "code") for f in get(extraction, "failures") or [] if get(f, "code")]
        raise ItemFailed("extract_failed" + (f":{codes[0]}" if codes else ""))
    item["extraction"] = {
        k: extraction.get(k)
        for k in ("mentions", "unresolved_names", "intervention_texts", "nct_id")
        if isinstance(extraction, dict) and k in extraction
    }
    source_text = item.get("raw_text") or item.get("evidence_text") or ""
    findings: list[dict[str, Any]] = []
    for raw in get(extraction, "findings") or []:
        finding = dict(plain(raw))
        checked = plain(await llm.check(finding, source_text))
        if isinstance(checked, dict) and checked:
            finding = {**finding, **checked}
        # V40: a Finding is pinned to the version the item read.
        if finding.get("version_id") not in (None, item["version_id"]):
            raise ItemFailed("finding_version_mismatch")
        finding["version_id"] = item["version_id"]
        finding.setdefault("source_ref", item["source_ref"])
        findings.append(finding)
    return findings


def discovery_text(item: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    text = item.get("evidence_text")
    if text:
        return str(text)
    summaries = [str(f.get("summary")) for f in findings if f.get("summary")]
    return " ".join(summaries) or str(item.get("title") or item.get("source_ref"))


async def related_items(retrieved: Any) -> list[dict[str, Any]]:
    """Load each retrieved item at the version the retrieval pinned (V40)."""
    out: list[dict[str, Any]] = []
    method = get(retrieved, "method")
    for entry in get(retrieved, "items") or []:
        ref, version_id, score = get(entry, "ref"), get(entry, "version_id"), get(entry, "score")
        if not ref:
            continue
        if str(ref).startswith("f_"):
            doc = await progress.load_finding(ref)
            kind = "finding"
        else:
            doc = await progress.load_version(version_id) if version_id else None
            if doc is None:
                src, doc = await progress.load_source(ref)
                version_id = (doc or {}).get("_id")
            kind = "source_item"
        if doc is None:
            continue
        related = {k: v for k, v in doc.items() if k not in ("_id", "embedding")}
        related.update(
            {"ref": ref, "related_kind": kind, "version_id": version_id or related.get("version_id"),
             "score": score, "retrieval_method": method}
        )
        if kind == "source_item":
            related.setdefault("source_ref", ref)
        out.append(related)
    return out


async def relate_all(new_item: dict[str, Any], related: list[dict[str, Any]]) -> list[Any]:
    """One `reports.relate()` per related item. A failure leaves that item out; it never
    fails the item (Story 10.3: relate itself already turns model errors into
    `related_unestablished`)."""
    out = []
    for other in related:
        try:
            out.append(await reports.relate(new_item, other))
        except Exception as exc:  # noqa: BLE001
            log.warning("relate failed ref=%s error=%s", other.get("ref"), type(exc).__name__)
    return out


def plain_draft(one: Any) -> dict[str, Any]:
    """A self-contained draft as `reports.file` takes it: one draft, never the `drafts` list."""
    out = dict(plain(one))
    out.pop("drafts", None)
    return out


async def file_report(drafted: dict[str, Any], item: dict[str, Any], report_id: str, info: RunInfo,
                      result: ItemResult) -> Any:
    """File the drafts with A19+A20's contract (#38, Luis's rulings of 14 Nov):
    `reports.file(draft, ctx, final)` once per draft, in order, each draft under its own
    admission. Every draft but the last is filed with `final=False` (gate only: its Decision
    is recorded, nothing is written) and carries no `updates`. The last is filed with
    `final=True`, carrying the updates `[{finding_id, change}]`, each `change` holding its own
    `admission_id` (D22), and `blocked_draft_decision_id` (the first blocked earlier draft).
    `reports.file` never sends the alert; `notify` does, after this returns allowed.

    Every admission (one per draft target, one per update of the final draft) is taken before
    any `reports.file` call. If any is refused (the run is stopping), every admission held is
    released and nothing is filed: no draft is gated and no report is written without one of
    its updates. Returns the final Decision, or None when an admission was refused. Every
    admission is released once, after the calls."""
    source_ref = item["source_ref"]
    drafts = [plain_draft(one) for one in (drafted.get("drafts") or [drafted])]
    targets = draft_targets({**drafted, "drafts": drafts}, report_id)
    final_draft = drafts[-1]
    raw_updates = final_draft.get("updates")
    if raw_updates is None:
        raw_updates = drafted.get("updates") or []
    held: list[str] = []
    try:
        draft_admissions: list[str] = []
        for _, target in targets:
            adm = await admit(info.run_id, item_key(source_ref, "file_proposal", None, target))
            if adm is None:
                return None  # not admitted: the run is stopping; nothing attempted
            held.append(adm)
            draft_admissions.append(adm)
        updates = []
        for update in raw_updates:
            update = dict(plain(update))
            change = dict(plain(update.get("change") or {}))
            key = item_key(source_ref, "file_proposal", change.get("diagnostic_id"),
                           change_target(update.get("finding_id"), change))
            adm = await admit(info.run_id, key)
            if adm is None:
                return None  # (4) a refused change: release everything, file nothing
            held.append(adm)
            change["admission_id"] = adm  # A06's ledger.file gates the change under it
            updates.append({"finding_id": update.get("finding_id"), "change": change})

        blocked_earlier = None
        for one, adm in zip(drafts[:-1], draft_admissions[:-1]):
            gate_only = {k: v for k, v in one.items() if k != "updates"}  # non-final drafts carry no updates
            decision = await reports.file(gate_only, with_admission(info.ctx, adm), final=False)
            result.draft_decisions.append(decision)
            if outcome(decision) == "blocked" and blocked_earlier is None:
                blocked_earlier = get(decision, "id") or get(decision, "_id")
        final = {**final_draft, "updates": updates, "blocked_draft_decision_id": blocked_earlier}
        decision = await reports.file(final, with_admission(info.ctx, draft_admissions[-1]), final=True)
    finally:
        await release(held)
    result.draft_decisions.append(decision)
    return decision


async def filed_report(report_id: str) -> dict[str, Any] | None:
    return await progress.load_report(report_id)


async def notify(report: dict[str, Any], item: dict[str, Any], report_id: str, info: RunInfo) -> Any:
    """The report's one notify_slack (V11). A10 is its only sender (Luis's ruling, 14 Nov):
    `reports.file` never creates it, so it is dispatched here once, with its own admission,
    only after the final `reports.file` has committed the report (A09 reads it outside any
    transaction). A blocked alert, an unconfigured sender and a report A09 cannot read are
    non-fatal: the item is still done. Returns the Action, a marker, or None when the alert's
    admission was refused (nothing attempted, outcome not recorded)."""
    # Same rule as A09's action ID: the stored report's first diagnostic_ids entry (written by
    # reports.file after ledger.file), else "-" (V43), so admission key and action ID line up.
    diagnostic_ids = [d for d in report.get("diagnostic_ids") or [] if d]
    dx = diagnostic_ids[0] if diagnostic_ids else None
    adm = await admit(info.run_id, item_key(item["source_ref"], "notify_slack", dx, report_id))
    if adm is None:
        return None
    try:
        action = ProposedAction(
            kind="notify_slack",
            destination=config.SLACK_DESTINATION,
            target=Target(report_id=report_id, diagnostic_id=dx, scope_id=info.scope_id),
            # A06 reads target parts that Target lacks from inputs (source_ref, diagnostic_ids).
            inputs={
                "report_id": report_id,
                "source_ref": item["source_ref"],
                "version_id": item["version_id"],
                "diagnostic_ids": diagnostic_ids,
                "script_hash": report.get("script_hash"),
                "headline": report.get("headline"),
            },
            evidence_ref=EvidenceRef(source_ref=item["source_ref"], version_id=item["version_id"], report_id=report_id),
        )
        try:
            return await actions.dispatch(action, with_admission(info.ctx, adm))
        except Exception as exc:
            not_sent = next((name for name in NOTIFY_NOT_SENT if is_a09(exc, name)), None)
            if not_sent:
                log.warning("alert not sent run=%s report=%s error=%s", info.run_id, report_id, not_sent)
                await info.tracker.note_failure(item["source_ref"], f"notify: {not_sent}")
                return {"status": "not_sent", "error": not_sent}
            if not is_action_blocked(exc):
                raise
            # The gate blocked the alert: A09 recorded its Decision and action_blocked event;
            # nothing was sent. A blocked step, not an item failure.
            log.info("alert blocked run=%s report=%s", info.run_id, report_id)
            blocked = get(exc, "decision")
            return {"status": "blocked",
                    "decision_id": get(exc, "decision_id") or get(blocked, "id") or get(blocked, "_id")}
    finally:
        await release([adm])


async def process(source_ref: str, info: RunInfo) -> ItemResult:
    """Run one item end to end; never raises (except cancellation)."""
    result = ItemResult(source_ref=source_ref, status="failed")
    tracker = info.tracker
    step = "load"
    try:
        status = await progress.run_status(info.run_id)
        if status != "running":
            result.status = "not_started"  # stopped before this item: nothing attempted
            return result
        await tracker.step(source_ref, step)
        loaded = await load(source_ref, info)
        if loaded is None:
            result.status = "skipped"
            await tracker.item_done(source_ref)
            return result
        item, version_id = loaded
        result.version_id = version_id
        report_id = report_id_for(info.run_id, source_ref)
        result.report_id = report_id
        item.update({"run_id": info.run_id, "scope_id": info.scope_id, "team_id": info.team_id, "report_id": report_id})

        step = "extract"
        await tracker.step(source_ref, step)
        findings = await extract(item, info)
        if findings is None:
            result.status = "done"
            await tracker.item_done(source_ref)
            return result
        for f in findings:
            await progress.save_finding(f, info.run_id, info.ctx.stamp)
        early = is_early_research(findings)

        step = "retrieve"
        await tracker.step(source_ref, step)
        text = discovery_text(item, findings)
        retrieved = await retrieval.related(info.scope_id, text, config.RELATED_K, [source_ref])
        item["retrieval"] = plain(retrieved)

        step = "remember"
        await tracker.step(source_ref, step)
        memories: list[Any] = []
        if info.team_id:
            memories, memory_retrieval = await memory.retrieve(info.team_id, text, memory_tags(item))
            item["memory_retrieval"] = plain(memory_retrieval)

        step = "relate"
        await tracker.step(source_ref, step)
        new_item = {**item, "findings": findings}
        relationships = await relate_all(new_item, await related_items(retrieved))

        decision = None
        for attempt in range(2):  # one redraft after a blocked report (V7, Story 10.7)
            step = "draft" if attempt == 0 else "redraft"
            await tracker.step(source_ref, step)
            drafted = check_report(
                await reports.draft({**item, "attempt": attempt}, findings, relationships, list(memories)), version_id)
            step = "file"
            await tracker.step(source_ref, step)
            decision = await file_report(drafted, item, report_id, info, result)
            if decision is None or outcome(decision) == "allowed":
                break
        if decision is not None and outcome(decision) == "allowed":
            result.filed = True
            report = await filed_report(report_id) or {}
            step = "notify"
            await tracker.step(source_ref, step)
            result.alert = await notify(report, item, report_id, info)
            # (6) Processed only once the alert's outcome is recorded (sent, blocked, or not
            # sent with a failure line). If notify raised, or its admission was refused, the
            # version stays unprocessed so a rerun sends the alert (A09's action ID keeps it one).
            if result.alert is not None:
                await progress.mark_processed(source_ref, info.scope_id, version_id, info.run_id)

        result.status = "done"
        await tracker.item_done(source_ref, early_research=early)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - each item catches its own error (AD-12)
        code = exc.code if isinstance(exc, ItemFailed) else type(exc).__name__
        result.status = "failed"
        result.error = f"{step}: {code}"
        log.warning("item failed run=%s ref=%s %s", info.run_id, source_ref, result.error)
        try:
            await tracker.item_failed(source_ref, result.error)
        except Exception:  # noqa: BLE001
            log.warning("could not record the failure of %s", source_ref)
    finally:
        try:
            await tracker.recount()
        except Exception:  # noqa: BLE001
            log.warning("could not recount run %s", info.run_id)
    return result
