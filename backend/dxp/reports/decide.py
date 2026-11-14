"""The report decision and its recovery (Story 10.8, AD-29, V8, V27, V38, V43, V45). A24.

`reports.decide()` is the only place a report leaves `pending`:

- It is gated first as `decide_report` under the Reviewer's grant (`sam@v1`), with
  `run_id: null`, the Reviewer stamp, a server-generated `request_id` and
  `cause { report_id, origin_run_id }`. Blocked: the Decision is recorded and nothing changes.
- **Approve.** One conditional write claims the report `pending` -> `accepting` and stores the
  `approval` record (the decision, request, Reviewer, note, correction, the intended
  `task_id = derive("task_", report_id)` and `task_step: "pending"`), so the unfinished task
  step is saved before the report can become `accepted` (V45). Then, in one Atlas transaction,
  every pending proposal of the report is applied through `ledger.apply()` (all or nothing),
  its relationships become `accepted`, the report becomes `accepted` and `report_decided` is
  emitted. A crash after the claim is finished by `recover_accepting()`; the task step is
  finished by `tasks.recover_authorisations()` (A24, `tasks/authorise.py`).
- **Reject.** In one transaction the report and its pending proposals become `rejected` with
  the note; nothing is promoted and no task is authorised. The memory is created by the
  route through `memory.create()` (AD-28), not here.
- A report that is not `pending` is returned unchanged with its existing Decisions.

The demo's one update is a scope evidence-collection proposal with `diagnostic_id: null`
(V43): nothing here assumes a Diagnostic; the Decision's target is the report and its scope.

`reports` never imports `tasks` (AD-29): the route orchestrates. The helpers below that write
the report on behalf of the task step (`mark_task_step`, `attach_memory`) live here because
`reports` is the only writer of `reports`.
"""

from __future__ import annotations

import logging
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel

from dxp import gate, ledger, store
from dxp.api.models import Decision, Principal, Report
from dxp.identity import derive

log = logging.getLogger("dxp.reports.decide")

DECIDE_KIND = "decide_report"
AUTHORISE_KIND = "authorise_task"
MEMORY_KIND = "create_memory"
LEDGER = "ledger"
# The Reviewer grant every human kind is evaluated under when the caller's own person grant
# cannot be found (AD-18: sam@v1).
REVIEWER_GRANT = "sam"
# Kinds shown with a report's decision (V14 "After the run").
REPORT_DECISION_KINDS = (DECIDE_KIND, AUTHORISE_KIND, MEMORY_KIND)


class ReportNotFound(LookupError):
    """No report has this ID (404)."""


class NoteRequired(ValueError):
    """A reject, or an approval with a correction, came without a note (400, before the gate)."""


class AcceptanceIncomplete(RuntimeError):
    """A proposal of the report did not end `applied`; the report stays `accepting`."""


# ---------------------------------------------------------------------------
# Small shared helpers (also used by tasks/authorise.py and the route)
# ---------------------------------------------------------------------------


def now() -> datetime:
    return datetime.now(UTC)


def db() -> Any:
    return store.get_db()


def new_request_id() -> str:
    """Server-generated request ID for a Reviewer decision (D20)."""
    return "req_" + secrets.token_hex(8)


def as_doc(decision: Any) -> dict[str, Any] | None:
    """A Decision as a plain document with both `_id` and `id`, whatever the gate returned
    (A06's dict-shaped Decision or the AD-14 model)."""
    if decision is None:
        return None
    if isinstance(decision, BaseModel):
        data = decision.model_dump()
    else:
        data = dict(decision)
    data.setdefault("_id", data.get("id"))
    data.setdefault("id", data.get("_id"))
    return data


def decision_model(decision: Any) -> Decision:
    """The AD-14 `Decision`, from A06's model or a stored document."""
    if isinstance(decision, Decision):
        return decision
    return Decision.model_validate(as_doc(decision) or {})


def report_model(doc: dict[str, Any]) -> Report:
    return Report.model_validate({**doc, "id": doc["_id"]})


def is_allowed(decision: dict[str, Any] | None) -> bool:
    return bool(decision) and decision.get("outcome") == "allowed"


def failure_reason(decision: dict[str, Any] | None) -> str:
    """The failed check and its detail, for "Follow-up task not authorised: <reason>"."""
    if not decision:
        return "not evaluated"
    failed = decision.get("failed_check")
    for check in decision.get("checks") or []:
        if check.get("check") == failed and check.get("detail"):
            return f"{failed}: {check['detail']}"
    return failed or "blocked"


async def in_transaction(work: Callable[[Any], Awaitable[Any]]) -> Any:
    """Run `work(session)` in one Atlas transaction: all of its writes are saved or none."""
    async with store.get_client().start_session() as session:
        return await session.with_transaction(work)


async def get_report(report_id: str, session: Any = None) -> dict[str, Any] | None:
    return await db()["reports"].find_one({"_id": report_id}, session=session)


async def reviewer_grant(principal_id: str, session: Any = None) -> dict[str, Any] | None:
    """The latest version of the caller's person grant (for a Reviewer write, check 1 reads the
    caller's grant, AD-19). None if the principal has none."""
    return await db()["grants"].find_one(
        {"principal": principal_id, "kind": "person"}, sort=[("version", -1)], session=session
    )


def reviewer_stamp(reviewer_id: str, grant_id: str | None = None, grant_version: int | None = None) -> dict[str, Any]:
    return {
        "kind": "reviewer",
        "run_id": None,
        "agent": None,
        "initiated_by": reviewer_id,
        "principal": reviewer_id,
        "grant_id": grant_id,
        "grant_version": grant_version,
    }


def reviewer_context(
    reviewer_id: str,
    grant: dict[str, Any] | None,
    request_id: str,
    report: dict[str, Any],
    *,
    extra_cause: dict[str, Any] | None = None,
    origin: str | None = None,
    session: Any = None,
) -> dict[str, Any]:
    """The gate context of a Reviewer decision on a report: `run_id: null`, the Reviewer stamp,
    the request ID and `cause { report_id, origin_run_id }` (AD-17, D20)."""
    grant_id = (grant or {}).get("grant_id") or REVIEWER_GRANT
    version = (grant or {}).get("version")
    ctx: dict[str, Any] = {
        "kind": "reviewer",
        "principal": reviewer_id,
        "initiated_by": reviewer_id,
        "grant_id": grant_id,
        "grant_version": version,
        "request_id": request_id,
        "cause": {"report_id": report["_id"], "origin_run_id": report.get("run_id"), **(extra_cause or {})},
        "stamp": reviewer_stamp(reviewer_id, grant_id, version),
        "mode": "live",
        "report_id": report["_id"],
    }
    if origin:
        ctx["origin"] = origin
    if session is not None:
        ctx["session"] = session
    return ctx


def report_target(report: dict[str, Any], **extra: Any) -> dict[str, Any]:
    """A report decision's target: the report and its scope; no Diagnostic is assumed (V43)."""
    return {
        "report_id": report["_id"],
        "scope_id": report.get("scope_id"),
        "diagnostic_id": None,
        "diagnostic_ids": list(report.get("diagnostic_ids") or []),
        **extra,
    }


def report_evidence(report: dict[str, Any]) -> dict[str, Any]:
    """The reviewed source version, pinned (V40)."""
    return {"report_id": report["_id"], "source_ref": report.get("source_ref"), "version_id": report.get("version_id")}


async def settle_action(decision: dict[str, Any] | None, status: str, session: Any = None) -> None:
    """Settle the DxP-state action of an allowed human decision (`queued` -> `done` | `failed`),
    through the gate's own helper when it has one (A06)."""
    mark = getattr(gate, "mark_action", None)
    if mark is None or not decision or not decision.get("action_id"):
        return
    await mark(decision["action_id"], status, session=session)


# ---------------------------------------------------------------------------
# Reading a report's decisions
# ---------------------------------------------------------------------------


def _decision_order(d: dict[str, Any]) -> tuple[Any, ...]:
    at = d.get("decided_at") or datetime.min.replace(tzinfo=UTC)
    if at.tzinfo is None:
        at = at.replace(tzinfo=UTC)
    return (at, d.get("seq") or 0, d["_id"])


async def decisions_for(report_id: str, session: Any = None) -> list[dict[str, Any]]:
    """The report's own Reviewer Decisions (decide, authorise, memory), oldest first."""
    cursor = db()["decisions"].find(
        {"target.report_id": report_id, "kind": {"$in": list(REPORT_DECISION_KINDS)}}, session=session
    )
    docs = [d async for d in cursor]
    docs.sort(key=_decision_order)
    return docs


def merge_decisions(stored: list[dict[str, Any]], *extra: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Stored decisions plus any in hand that are not stored (a gate that records nothing)."""
    seen = {d["_id"] for d in stored}
    merged = list(stored)
    for d in extra:
        if d and d.get("_id") not in seen:
            merged.append(d)
            seen.add(d["_id"])
    return merged


async def current_state(report_id: str, *extra: dict[str, Any] | None) -> tuple[Report, list[Decision]]:
    report = await get_report(report_id)
    if report is None:
        raise ReportNotFound(report_id)
    decisions = merge_decisions(await decisions_for(report_id), *extra)
    return report_model(report), [decision_model(d) for d in decisions]


# ---------------------------------------------------------------------------
# reports.decide
# ---------------------------------------------------------------------------


def require_note(action: str, note: str | None, correction: str | None) -> None:
    """A reject needs a note; so does an approval with a correction (400 before the gate)."""
    has_note = bool((note or "").strip())
    if action == "reject" and not has_note:
        raise NoteRequired("A reject needs a note.")
    if (correction or "").strip() and not has_note:
        raise NoteRequired("A correction needs a note.")


async def decide(
    report_id: str,
    action: Literal["approve", "reject"],
    note: str | None,
    correction: str | None,
    reviewer: Principal,
) -> tuple[Report, list[Decision]]:
    """Gated decide_report; the claim pending -> accepting stores the approval record (V45);
    ledger.apply per proposal, all or nothing."""
    require_note(action, note, correction)
    report = await get_report(report_id)
    if report is None:
        raise ReportNotFound(report_id)
    if report.get("status") != "pending":
        # A second decision does nothing and returns the current state (V38).
        return await current_state(report_id)

    grant = await reviewer_grant(reviewer.id)
    request_id = new_request_id()
    ctx = reviewer_context(reviewer.id, grant, request_id, report)
    proposed = {
        "kind": DECIDE_KIND,
        "destination": LEDGER,
        "target": report_target(report),
        "inputs": {"action": action, "note": note, "correction": correction},
        "evidence_ref": report_evidence(report),
    }
    decision = await evaluate(ctx, proposed)
    if not is_allowed(decision):
        return await current_state(report_id, decision)

    if action == "approve":
        claimed = await _claim_accepting(report, decision, request_id, reviewer.id, note, correction)
        if not claimed:
            # Another request claimed it first: this one changes nothing (one apply).
            await settle_action(decision, "failed")
            return await current_state(report_id, decision)
        await finish_accepting(report_id)
    else:
        rejected = await _reject(report, decision, reviewer.id, note)
        if not rejected:
            await settle_action(decision, "failed")
            return await current_state(report_id, decision)
    await settle_action(decision, "done")
    return await current_state(report_id, decision)


async def _claim_accepting(
    report: dict[str, Any],
    decision: dict[str, Any],
    request_id: str,
    reviewer_id: str,
    note: str | None,
    correction: str | None,
) -> bool:
    """`pending` -> `accepting` with the approval record, in one conditional write (V45)."""
    approval = {
        "decision_id": decision["_id"],
        "request_id": request_id,
        "reviewer": reviewer_id,
        "decided_by": reviewer_id,
        "decided_at": now(),
        "note": note,
        "correction": correction,
        "task_id": derive("task_", report["_id"]),
        "task_step": "pending",
    }
    res = await db()["reports"].update_one(
        {"_id": report["_id"], "status": "pending"},
        {"$set": {"status": "accepting", "approval": approval, "decision_id": decision["_id"]}},
    )
    return bool(res.modified_count)


async def apply_proposal(proposal_id: str, decided_by: str | None, session: Any) -> None:
    """Apply one proposal inside the caller's transaction: A06's `ledger.apply_with` carries
    the Reviewer and the session; the frozen `ledger.apply(proposal_id)` is the fallback."""
    apply_with = getattr(ledger, "apply_with", None)
    if apply_with is not None:
        await apply_with(proposal_id, review="accepted", decided_by=decided_by, session=session)
    else:
        await ledger.apply(proposal_id)


async def evaluate(ctx: dict[str, Any], action: dict[str, Any], session: Any = None) -> dict[str, Any] | None:
    """`gate.evaluate`, or A06's `gate.evaluate_in` when a session must carry the evaluation
    into the caller's transaction (V38). Returns the Decision as a document."""
    evaluate_in = getattr(gate, "evaluate_in", None)
    if session is not None and evaluate_in is not None:
        return as_doc(await evaluate_in(ctx, action, session))
    if session is not None:
        ctx = {**ctx, "session": session}
    return as_doc(await gate.evaluate(ctx, action))


async def finish_accepting(report_id: str) -> dict[str, Any] | None:
    """Apply the report's proposals, accept its relationships and mark it `accepted`, in one
    transaction. Idempotent: a report no longer `accepting` is left as it is."""
    report = await get_report(report_id)
    if report is None or report.get("status") != "accepting":
        return report
    approval = report.get("approval") or {}
    decided_by = approval.get("reviewer") or approval.get("decided_by")
    proposal_ids = list(report.get("proposal_ids") or [])

    async def work(session: Any) -> None:
        for proposal_id in proposal_ids:
            await apply_proposal(proposal_id, decided_by, session)
        cursor = db()["proposals"].find({"_id": {"$in": proposal_ids}}, {"status": 1}, session=session)
        stored = {p["_id"]: p.get("status") async for p in cursor}
        missing = [pid for pid in proposal_ids if stored.get(pid) != "applied"]
        if missing:
            raise AcceptanceIncomplete(f"report {report_id}: proposals not applied: {missing}")
        current = await get_report(report_id, session=session)
        if current is None or current.get("status") != "accepting":
            return
        related = [
            {**rel, "status": "accepted"} if rel.get("status") == "pending" else rel
            for rel in (current.get("related") or [])
        ]
        at = now()
        res = await db()["reports"].update_one(
            {"_id": report_id, "status": "accepting"},
            {
                "$set": {
                    "status": "accepted",
                    "related": related,
                    "decided_by": decided_by,
                    "decided_at": approval.get("decided_at") or at,
                    "accepted_at": at,
                    "note": approval.get("note"),
                }
            },
            session=session,
        )
        if res.modified_count:
            await _emit_decided(current, "accepted", decided_by, approval.get("decision_id"), session)

    await in_transaction(work)
    return await get_report(report_id)


async def _reject(report: dict[str, Any], decision: dict[str, Any], reviewer_id: str, note: str | None) -> bool:
    """`pending` -> `rejected` for the report and its pending proposals, in one transaction."""
    holder: dict[str, bool] = {}

    async def work(session: Any) -> None:
        at = now()
        res = await db()["reports"].update_one(
            {"_id": report["_id"], "status": "pending"},
            {
                "$set": {
                    "status": "rejected",
                    "decided_by": reviewer_id,
                    "decided_at": at,
                    "note": note,
                    "decision_id": decision["_id"],
                }
            },
            session=session,
        )
        holder["rejected"] = bool(res.modified_count)
        if not res.modified_count:
            return
        for proposal_id in report.get("proposal_ids") or []:
            changed = await db()["proposals"].update_one(
                {"_id": proposal_id, "status": "pending"},
                {"$set": {"status": "rejected", "reason": note, "decided_by": reviewer_id, "decided_at": at}},
                session=session,
            )
            if changed.modified_count:
                await store.emit_event(
                    {
                        "type": "proposal_rejected",
                        "dedupe_key": f"proposal_rejected|{proposal_id}",
                        "mode": "live",
                        "run_id": None,
                        "stamp": decision.get("stamp"),
                        "decision_id": decision["_id"],
                        "proposal_id": proposal_id,
                        "report_id": report["_id"],
                    },
                    session=session,
                )
        await _emit_decided(report, "rejected", reviewer_id, decision["_id"], session)

    await in_transaction(work)
    return holder.get("rejected", False)


async def _emit_decided(
    report: dict[str, Any], status: str, reviewer_id: str | None, decision_id: str | None, session: Any
) -> None:
    await store.emit_event(
        {
            "type": "report_decided",
            "dedupe_key": f"report_decided|{report['_id']}",
            "mode": "live",
            "run_id": None,
            "stamp": reviewer_stamp(reviewer_id or REVIEWER_GRANT),
            "decision_id": decision_id,
            "report_id": report["_id"],
            "status": status,
        },
        session=session,
    )


# ---------------------------------------------------------------------------
# Writes on behalf of the task step and the memory step (reports is the only writer)
# ---------------------------------------------------------------------------


async def mark_task_step(
    report_id: str,
    step: Literal["done", "blocked"],
    *,
    task_id: str | None = None,
    reason: str | None = None,
    authorise_decision_id: str | None = None,
    session: Any = None,
) -> bool:
    """`approval.task_step` `pending` -> `done` | `blocked`, conditional (V45). Called inside
    `tasks.authorise()`'s transaction."""
    update: dict[str, Any] = {"approval.task_step": step, "approval.authorise_decision_id": authorise_decision_id}
    if step == "done":
        update["task_id"] = task_id
    else:
        update["approval.reason"] = reason
        update["approval.message"] = f"Follow-up task not authorised: {reason}"
    res = await db()["reports"].update_one(
        {"_id": report_id, "status": "accepted", "approval.task_step": "pending"}, {"$set": update}, session=session
    )
    return bool(res.modified_count)


async def attach_memory(report_id: str, memory_id: str) -> None:
    """Record the memory a reject or a correction created ("Memory saved", V46)."""
    await db()["reports"].update_one({"_id": report_id, "memory_id": None}, {"$set": {"memory_id": memory_id}})


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------


async def recover_accepting() -> None:
    """Finish every report left in `accepting` (AD-29): re-apply its proposals (no-ops if
    done), then mark it `accepted`. Its `approval.task_step` stays `pending` for
    `tasks.recover_authorisations()`."""
    stuck = [r["_id"] async for r in db()["reports"].find({"status": "accepting"}, {"_id": 1})]
    for report_id in stuck:
        try:
            await finish_accepting(report_id)
        except AcceptanceIncomplete:
            log.warning("report %s stays accepting: a proposal did not apply", report_id)
