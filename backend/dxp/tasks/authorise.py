"""Task authorisation and its recovery (Story 10.8, AD-29, V38, V45). A24.

`tasks.authorise(report_id, reviewer)` settles the task step of an accepted approval. It reads
the report's stored `approval` record (V45), so the normal path and the recovery path are the
same code and keep the original approval's identity: its Reviewer, its request ID and the
intended `task_id = derive("task_", report_id)`.

In **one Atlas transaction** (V38) it evaluates `authorise_task` under the Reviewer grant
(`sam@v1`) with the derived Decision ID `derive("dec_", approval.decision_id, "authorise_task")`
and then:

- allowed: inserts the `tasks` document (the gap as its `question`; `queued` with the backend
  flag `task_run` on, the task itself being the durable queue entry, `authorised` and never
  queued with it off), issues the task grant `task-<hex>@v1` (`gate.grants.issue_task_grant`)
  and sets the report's `approval.task_step: "done"`;
- blocked: records the blocked Decision and sets `approval.task_step: "blocked"` with the
  reason; no task and no grant. The evidence stays accepted.

Either all of it is saved or none of it. `"done"` and `"blocked"` are terminal: a retry or a
recovery returns what is stored and never evaluates again.

`recover_authorisations()` completes every accepted report whose `approval.task_step` is still
`"pending"` (a crash between acceptance and authorisation), rechecking authority through the
gate as it stands now, with no Reviewer click. Its Decision records `origin: "recovery"`.

Nothing here imports `tasks/run.py` (A25): authorising never executes.
"""

from __future__ import annotations

import importlib
import logging
from datetime import UTC, datetime
from typing import Any

from dxp import feature_enabled, store
from dxp.api.models import Principal, Task
from dxp.gate import grants
from dxp.identity import derive

# The package __init__ re-exports functions with the same names as these modules, so the
# modules are taken from sys.modules explicitly.
rd = importlib.import_module("dxp.reports.decide")

log = logging.getLogger("dxp.tasks.authorise")

TASK_RUN_FLAG = "task_run"
DEFAULT_CONDITION = "non-small cell lung cancer"
DEFAULT_TESTING = ["ctDNA or plasma", "tissue profiling"]
MAX_RESULTS = 5


class TaskNotAuthorised(Exception):
    """The `authorise_task` Decision was blocked (now or earlier); no task exists."""

    def __init__(self, decision: dict[str, Any] | None, reason: str) -> None:
        super().__init__(reason)
        self.decision = decision
        self.reason = reason


class NotAnApproval(LookupError):
    """The report is not an accepted approval with an approval record."""


def task_id_for(report_id: str) -> str:
    return derive("task_", report_id)


def authorise_decision_id(approval_decision_id: str) -> str:
    """AD-29: one `authorise_task` Decision per approval, whoever evaluates it."""
    return derive("dec_", approval_decision_id, "authorise_task")


def task_model(doc: dict[str, Any]) -> Task:
    return Task.model_validate({**doc, "id": doc["_id"]})


def task_params(report: dict[str, Any], scope: dict[str, Any] | None) -> dict[str, Any]:
    """The params answer the report's gap (V26, V33): early stage, ctDNA or plasma testing with
    tissue profiling, posted results, at most 5 records."""
    recommended = ((report.get("recommended_task") or {}).get("params")) or {}
    condition = recommended.get("condition") or (scope or {}).get("condition") or DEFAULT_CONDITION
    return {
        "condition": condition,
        "stage": "early",
        "testing": list(recommended.get("testing") or DEFAULT_TESTING),
        "has_results": True,
        "max": min(int(recommended.get("max") or MAX_RESULTS), MAX_RESULTS),
    }


def build_task(
    report: dict[str, Any],
    task_id: str,
    decision_id: str,
    params: dict[str, Any],
    queued: bool,
    authorised_by: str,
    at: datetime,
) -> dict[str, Any]:
    """The `tasks` document (pure; AD-14 Task)."""
    question = (report.get("gap") or "").strip()
    if not question:
        raise ValueError(f"report {report['_id']} names no gap for the task to answer")
    return {
        "_id": task_id,
        "report_id": report["_id"],
        "kind": "search_related",
        "question": question,
        "params": params,
        "grant_id": grants.task_grant_id(task_id),
        "grant_version": 1,
        "status": "queued" if queued else "authorised",
        "error": None,
        "queued_at": at if queued else None,
        "run_id": None,
        "authorised_by_decision_id": decision_id,
        "authorised_by": authorised_by,
        "result": None,
        "created_at": at,
    }


async def _emit_status(task: dict[str, Any], stamp: dict[str, Any], session: Any = None) -> None:
    await store.emit_event(
        {
            "type": "task_status_changed",
            "dedupe_key": f"task_status_changed|{task['_id']}|{task['status']}",
            "mode": "live",
            "run_id": None,
            "stamp": stamp,
            "decision_id": task.get("authorised_by_decision_id"),
            "report_id": task.get("report_id"),
            "task_id": task["_id"],
            "status": task["status"],
        },
        session=session,
    )


async def _stored_outcome(report: dict[str, Any], approval: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """A terminal task step: the stored task (if any) and the stored `authorise_task` Decision."""
    database = rd.db()
    decision = await database["decisions"].find_one({"_id": authorise_decision_id(approval["decision_id"])})
    task = await database["tasks"].find_one({"_id": approval.get("task_id") or task_id_for(report["_id"])})
    return task, decision


async def authorise_report(report_id: str, reviewer_id: str | None = None, origin: str | None = None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Settle the task step of an accepted approval. Returns `(task, decision)` documents;
    `task` is None when the step is blocked."""
    report = await rd.get_report(report_id)
    if report is None:
        raise rd.ReportNotFound(report_id)
    approval = report.get("approval") or {}
    if report.get("status") != "accepted" or not approval.get("decision_id"):
        raise NotAnApproval(f"report {report_id} is {report.get('status')}, not an accepted approval")
    if approval.get("task_step") in ("done", "blocked"):
        return await _stored_outcome(report, approval)

    task_id = approval.get("task_id") or task_id_for(report_id)
    who = approval.get("reviewer") or approval.get("decided_by") or reviewer_id or rd.REVIEWER_GRANT
    grant = await rd.reviewer_grant(who)
    scope = await rd.db()["research_scopes"].find_one({"_id": report.get("scope_id")}) if report.get("scope_id") else None
    params = task_params(report, scope)
    queued = feature_enabled(TASK_RUN_FLAG)
    decision_id = authorise_decision_id(approval["decision_id"])
    holder: dict[str, Any] = {}

    async def work(session: Any) -> None:
        holder.clear()
        ctx = rd.reviewer_context(
            who,
            grant,
            approval.get("request_id") or rd.new_request_id(),
            report,
            extra_cause={"approval_decision_id": approval["decision_id"]},
            origin=origin,
        )
        action = {
            "kind": rd.AUTHORISE_KIND,
            "destination": rd.LEDGER,
            "target": rd.report_target(report, task_id=task_id),
            "inputs": {
                "decision_id": decision_id,
                "question": report.get("gap"),
                "params": params,
                "status": "queued" if queued else "authorised",
                "task_grant_id": grants.task_grant_id(task_id),
            },
            "evidence_ref": rd.report_evidence(report),
            "decision_id": decision_id,
        }
        decision = await rd.evaluate(ctx, action, session)
        holder["decision"] = decision
        if not rd.is_allowed(decision):
            await rd.mark_task_step(
                report_id, "blocked", reason=rd.failure_reason(decision), authorise_decision_id=decision["_id"], session=session
            )
            return
        tasks = rd.db()["tasks"]
        task = await tasks.find_one({"_id": task_id}, session=session)
        if task is None:
            task = build_task(report, task_id, decision["_id"], params, queued, who, datetime.now(UTC))
            await tasks.insert_one(task, session=session)
            await _emit_status(task, decision.get("stamp") or rd.reviewer_stamp(who), session)
        await grants.issue_task_grant(task_model(task), rd.decision_model(decision), session)
        await rd.mark_task_step(report_id, "done", task_id=task_id, authorise_decision_id=decision["_id"], session=session)
        await rd.settle_action(decision, "done", session=session)
        holder["task"] = task

    await rd.in_transaction(work)
    return holder.get("task"), holder.get("decision")


async def authorise(report_id: str, reviewer: Principal) -> Task:
    """Gated authorise_task: the Decision, the task (queued with task_run on, else authorised),
    its grant and the queue entry in one transaction. Raises `TaskNotAuthorised` (with the
    blocked Decision) when the step is blocked."""
    task, decision = await authorise_report(report_id, reviewer.id if reviewer is not None else None)
    if task is None:
        raise TaskNotAuthorised(decision, rd.failure_reason(decision))
    return task_model(task)


async def recover_authorisations() -> None:
    """Complete accepted reports with approval.task_step "pending" (V45): authority is
    rechecked as it stands now; no Reviewer click; safe to repeat."""
    pending = [
        r["_id"]
        async for r in rd.db()["reports"].find({"status": "accepted", "approval.task_step": "pending"}, {"_id": 1})
    ]
    for report_id in pending:
        try:
            await authorise_report(report_id, origin="recovery")
        except Exception:
            log.exception("could not complete the task step of report %s", report_id)
