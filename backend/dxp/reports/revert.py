"""Revert one approval (AD-31, V48, supporting, revert flag). A26.

`reports.revert(report_id, note, reviewer)`:

- A note is required (400, before the gate). An unknown report is 404.
- Only an `accepted` report is evaluated. A report that is `reverting` or `reverted` returns its
  current state and the same Decision (a revert in `reverting` is finished first); any other
  status raises `NotRevertable` (409) and records no Decision.
- The gate evaluates `revert_report` under the Reviewer's grant (`sam@v1`): destination
  `ledger`, the Reviewer stamp, `run_id: null`, a server-generated `request_id` and
  `cause { report_id, origin_run_id }`; the target is the report and its `scope_id` (check 2).
  The gate derives the Decision ID without the request ID,
  `derive("dec_", "-", "revert_report", "-", report_id)`, so a retry finds the same Decision
  and a blocked revert is final. Blocked: only the Decision; the report stays `accepted`.
- Allowed: one conditional write claims `accepted` -> `reverting` with
  `revert { decision_id, request_id, by, at, note, step: "pending" }`; then `finish_reverting`
  reverses every applied proposal through `ledger.revert_proposal()`, moves the accepted
  relationships to `reverted`, and marks the report `reverted` (`reverted_by`, `reverted_at`,
  `revert.step: "done"`) with `report_reverted`. Each step is idempotent, so
  `recover_reverting()` (start hook and every revert call) finishes an interrupted revert.

Nothing is deleted or edited back: the approval Decision, the applied proposal and the source
version stay. `reports` imports nothing from `tasks`: the route cancels the task.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from dxp import ledger, store
from dxp.api.models import Decision, Principal, Report
from dxp.identity import derive

# The package __init__ re-exports a function named `decide`, so the module is taken explicitly.
rd = importlib.import_module("dxp.reports.decide")

log = logging.getLogger("dxp.reports.revert")

REVERT_KIND = "revert_report"


class NotRevertable(ValueError):
    """The report is not `accepted` (409). Carries the report's current status."""

    def __init__(self, report_id: str, status: str | None) -> None:
        super().__init__(f"report {report_id} is {status}; only an accepted report can be reverted")
        self.report_id = report_id
        self.status = status


def revert_decision_id(report_id: str) -> str:
    """The gate's ID for a report's one `revert_report` Decision (V48, AD-31)."""
    return derive("dec_", "-", REVERT_KIND, "-", report_id)


async def _stored_decision(report_id: str) -> dict[str, Any] | None:
    return await rd.db()["decisions"].find_one({"_id": revert_decision_id(report_id)})


async def removed_count(report: dict[str, Any]) -> int:
    """How many accepted updates of this report were removed (applied reverse proposals)."""
    ids = list(report.get("proposal_ids") or [])
    if not ids:
        return 0
    return await rd.db()["proposals"].count_documents(
        {"reverts_proposal_id": {"$in": ids}, "op": "remove", "status": "applied"}
    )


async def _result(report_id: str, decision: dict[str, Any] | None) -> tuple[Report, Decision, int]:
    report = await rd.get_report(report_id)
    stored = await _stored_decision(report_id)
    chosen = stored or decision
    return rd.report_model(report), rd.decision_model(chosen), await removed_count(report)


async def revert(report_id: str, note: str, reviewer: Principal) -> tuple[Report, Decision, int]:
    """Gated revert_report under sam@v1; claim accepted -> reverting with the revert record;
    ledger.revert_proposal per applied proposal; report and relationships reverted.
    Returns the report, the Decision and the number of accepted updates removed."""
    if not (note or "").strip():
        raise rd.NoteRequired("A revert needs a note.")
    report = await rd.get_report(report_id)
    if report is None:
        raise rd.ReportNotFound(report_id)
    status = report.get("status")
    if status in ("reverting", "reverted"):
        await finish_reverting(report_id)
        return await _result(report_id, None)
    if status != "accepted":
        raise NotRevertable(report_id, status)

    grant = await rd.reviewer_grant(reviewer.id)
    request_id = rd.new_request_id()
    ctx = rd.reviewer_context(reviewer.id, grant, request_id, report)
    proposed = {
        "kind": REVERT_KIND,
        "destination": rd.LEDGER,
        "target": rd.report_target(report),
        "inputs": {"note": note},
        "evidence_ref": rd.report_evidence(report),
    }
    decision = await rd.evaluate(ctx, proposed)
    if not rd.is_allowed(decision):
        return await _result(report_id, decision)

    revert_record = {
        "decision_id": decision["_id"],
        "request_id": request_id,
        "by": reviewer.id,
        "at": rd.now(),
        "note": note,
        "step": "pending",
    }
    res = await rd.db()["reports"].update_one(
        {"_id": report_id, "status": "accepted"},
        {"$set": {"status": "reverting", "revert": revert_record}},
    )
    await finish_reverting(report_id)
    await rd.settle_action(decision, "done" if res.modified_count else "failed")
    return await _result(report_id, decision)


async def finish_reverting(report_id: str) -> dict[str, Any] | None:
    """Reverse the report's applied proposals, revert its accepted relationships and mark it
    `reverted`. Idempotent: a report no longer `reverting` is left as it is."""
    report = await rd.get_report(report_id)
    if report is None or report.get("status") != "reverting":
        return report
    revert_record = report.get("revert") or {}
    decision = await rd.db()["decisions"].find_one({"_id": revert_record.get("decision_id")})
    if decision is None:
        raise LookupError(f"report {report_id}: revert Decision {revert_record.get('decision_id')} not found")
    decision_model = rd.decision_model(decision)
    for proposal_id in report.get("proposal_ids") or []:
        p = await rd.db()["proposals"].find_one({"_id": proposal_id}, {"status": 1, "op": 1})
        if p is None or p.get("op") == "remove" or p.get("status") != "applied":
            continue
        await ledger.revert_proposal(proposal_id, decision_model)

    related = [
        {**rel, "status": "reverted"} if rel.get("status") == "accepted" else rel
        for rel in (report.get("related") or [])
    ]
    at = rd.now()
    res = await rd.db()["reports"].update_one(
        {"_id": report_id, "status": "reverting"},
        {
            "$set": {
                "status": "reverted",
                "related": related,
                "reverted_by": revert_record.get("by"),
                "reverted_at": at,
                "revert.step": "done",
            }
        },
    )
    if res.modified_count:
        await store.emit_event(
            {
                "type": "report_reverted",
                "dedupe_key": f"report_reverted|{report_id}",
                "mode": "live",
                "run_id": None,
                "stamp": decision.get("stamp") or rd.reviewer_stamp(revert_record.get("by") or rd.REVIEWER_GRANT),
                "decision_id": decision["_id"],
                "action_id": decision.get("action_id"),
                "report_id": report_id,
                "status": "reverted",
            }
        )
    return await rd.get_report(report_id)


async def recover_reverting() -> None:
    """Finish every report left in `reverting` (AD-31). Runs from the API start hook and at the
    start of every revert call; a report it cannot finish is logged and left in `reverting`."""
    stuck = [r["_id"] async for r in rd.db()["reports"].find({"status": "reverting"}, {"_id": 1})]
    for report_id in stuck:
        try:
            await finish_reverting(report_id)
        except Exception:
            log.exception("report %s stays reverting: its revert could not be finished", report_id)
