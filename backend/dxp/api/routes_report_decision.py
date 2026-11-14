"""The report decision and tasks (Story 10.8, AD-29, V27, V38, V45, V46). No route starts a task. A24.

`POST /reports/<report_id>/decision { action: approve | reject, note, correction }`:

1. The caller is resolved server-side from `X-DxP-Key` (D17); a body field never confers
   permission. A reject without a note (or a correction without a note) is 400 before the gate.
2. Recovery first (AD-29): `ledger.recover_applying()`, `reports.recover_accepting()`,
   `tasks.recover_authorisations()`.
3. `reports.decide()` (gated `decide_report`).
4. On an accepted approval whose task step is still pending: `tasks.authorise()` (gated
   `authorise_task`; Decision, task, grant and queue entry in one transaction).
5. With the backend flag `task_run` on (`DXP_FEATURES`): `tasks.dispatch_next()` once.
6. On a reject or an approval with a correction: `memory.create()` (gated `create_memory`,
   AD-28). "Memory saved" is said only after it succeeds (V46); a retried decision repairs a
   memory step that did not finish.

A report that is not pending returns its current state, decisions, task and memory, completing
only a missing step and never starting a second run (V38). The response's `message` carries the
approval sentence (V27, V38).

`GET /tasks?report_id=` and `GET /tasks/<task_id>` read the `tasks` collection.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Query, Request

from dxp import feature_enabled, ledger, memory, store
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError

# The package __init__ re-exports functions with the same names as these modules, so the
# modules are taken from sys.modules explicitly.
rd = importlib.import_module("dxp.reports.decide")
ta = importlib.import_module("dxp.tasks.authorise")
td = importlib.import_module("dxp.tasks.dispatch")

log = logging.getLogger("dxp.api.report_decision")

router = APIRouter()
OWNER = "A24"
KEY_HEADER = "X-DxP-Key"
TASK_RUN_FLAG = "task_run"

# Test seam for the V45 crash test: called after the report is accepted and before
# tasks.authorise(). Never set outside tests.
fault_hook: Callable[[str], Any] | None = None

APPROVED = "Approved: {count} {noun} accepted."
TASK_NOT_RUN = "Follow-up task authorised; not run."
TASK_PENDING_REVIEW = "Follow-up task authorised; its findings will be pending review."
TASK_NOT_AUTHORISED = "Follow-up task not authorised: {reason}."
TASK_STEP_PENDING = "Follow-up task authorisation pending."
REJECTED = "Rejected: no update accepted; no task authorised."
MEMORY_SAVED = "Memory saved."
NOT_DECIDED = "Decision blocked: {reason}."


async def _caller(request: Request) -> m.Principal:
    key = request.headers.get(KEY_HEADER) or ""
    if not key:
        raise ApiError(401, "unknown_key", "Missing API key.")
    principal = await auth.resolve_actor(key)
    if principal.kind == "seed":
        raise ApiError(403, "seed_key_not_accepted", "The seed key is for the command line only.")
    return principal


def approval_message(report: dict[str, Any], task: dict[str, Any] | None, accepted_count: int) -> str:
    """The V27 / V38 sentence. "Approved" is not "accepted" for the task."""
    head = APPROVED.format(count=accepted_count, noun="update" if accepted_count == 1 else "updates")
    approval = report.get("approval") or {}
    if task is not None:
        tail = TASK_NOT_RUN if task.get("status") == "authorised" else TASK_PENDING_REVIEW
    elif approval.get("task_step") == "blocked":
        tail = TASK_NOT_AUTHORISED.format(reason=(approval.get("reason") or "blocked").rstrip("."))
    else:
        tail = TASK_STEP_PENDING
    return f"{head} {tail}"


def decision_message(report: dict[str, Any], task: dict[str, Any] | None, accepted_count: int,
                     decisions: list[dict[str, Any]], memory_saved: bool) -> str | None:
    status = report.get("status")
    if status in ("accepted", "reverting", "reverted"):
        message = approval_message(report, task, accepted_count)
        if (report.get("approval") or {}).get("correction") and memory_saved:
            message = f"{message} {MEMORY_SAVED}"
        return message
    if status == "rejected":
        return f"{REJECTED} {MEMORY_SAVED}" if memory_saved else REJECTED
    blocked = [d for d in decisions if d.get("kind") == rd.DECIDE_KIND and d.get("outcome") == "blocked"]
    if status == "pending" and blocked:
        return NOT_DECIDED.format(reason=rd.failure_reason(blocked[-1]).rstrip("."))
    return None


def _memory_tags(report: dict[str, Any]) -> dict[str, Any]:
    """`tags.assay` from the report (its first name mention); `tags.claim_kind`: the request has
    no claim kind field, so a report on a trial with no posted results is tagged
    `outcome_claim_without_results` (M1, V22) and any other `reviewer_correction`."""
    mentions = (report.get("discovery") or {}).get("mentions") or []
    has_results = (report.get("discovery") or {}).get("has_results")
    return {
        "assay": mentions[0].get("name") if mentions else None,
        "claim_kind": "outcome_claim_without_results" if has_results is False else "reviewer_correction",
    }


async def _create_memory(report: dict[str, Any], text: str, reviewer: m.Principal) -> tuple[m.Memory | None, Any]:
    """memory.create() for a reject or a correction, at most once per report (V46)."""
    decision_id = report.get("decision_id") or (report.get("approval") or {}).get("decision_id")
    grant = await rd.reviewer_grant(reviewer.id)
    grant_id = (grant or {}).get("grant_id") or rd.REVIEWER_GRANT
    version = (grant or {}).get("version") or 1
    ctx = m.RunContext(
        principal=reviewer,
        stamp=m.Stamp.model_validate(rd.reviewer_stamp(reviewer.id, grant_id, version)),
        grant_id=grant_id,
        grant_version=version,
        request_id=(report.get("approval") or {}).get("request_id") or rd.new_request_id(),
        cause=m.DecisionCause(report_id=report["_id"], origin_run_id=report.get("run_id")),
    )
    try:
        created, decision = await memory.create(
            report["team_id"],
            text,
            _memory_tags(report),
            m.MemorySource(decision_id=decision_id, report_id=report["_id"]),
            reviewer,
            ctx,
        )
    except Exception:
        log.exception("memory.create failed for report %s", report["_id"])
        return None, None
    if created is not None and getattr(decision, "outcome", "allowed") == "allowed":
        await rd.attach_memory(report["_id"], created.id)
    return created, decision


async def _memory_for(report: dict[str, Any]) -> m.Memory | None:
    memory_id = report.get("memory_id")
    if not memory_id:
        return None
    doc = await store.get_db()["memories"].find_one({"memory_id": memory_id}, sort=[("version", -1)])
    if doc is None:
        return None
    return m.Memory.model_validate({**doc, "id": doc.get("memory_id", memory_id)})


async def _accepted_count(report: dict[str, Any]) -> int:
    ids = list(report.get("proposal_ids") or [])
    if not ids:
        return 0
    return await store.get_db()["proposals"].count_documents({"_id": {"$in": ids}, "status": "applied"})


@router.post("/reports/{report_id}/decision", response_model=m.ReportDecisionResponse, tags=["reports"])
async def decide_report(report_id: str, body: m.ReportDecisionRequest, request: Request) -> m.ReportDecisionResponse:
    reviewer = await _caller(request)
    try:
        rd.require_note(body.action, body.note, body.correction)
    except rd.NoteRequired as exc:
        raise ApiError(400, "note_required", str(exc)) from exc

    await ledger.recover_applying()
    await rd.recover_accepting()
    await ta.recover_authorisations()

    try:
        _, decided = await rd.decide(report_id, body.action, body.note, body.correction, reviewer)
    except rd.ReportNotFound as exc:
        raise ApiError(404, "not_found", "Report not found.") from exc
    in_hand = [rd.as_doc(d) for d in decided]

    report = await rd.get_report(report_id)
    approval = report.get("approval") or {}
    if report.get("status") == "accepted" and approval.get("task_step") == "pending":
        if fault_hook is not None:
            fault_hook(report_id)
        try:
            task_model = await ta.authorise(report_id, reviewer)
            in_hand.append(rd.as_doc(await store.get_db()["decisions"].find_one(
                {"_id": task_model.authorised_by_decision_id})))
        except ta.TaskNotAuthorised as exc:
            in_hand.append(rd.as_doc(exc.decision))

    if feature_enabled(TASK_RUN_FLAG):
        await td.dispatch_next(request.app.state.start_run)

    report = await rd.get_report(report_id)
    created: m.Memory | None = None
    memory_text = None
    if report.get("status") == "rejected" and body.action == "reject":
        memory_text = report.get("note")
    elif report.get("status") in ("accepted",) and approval_for(report).get("correction"):
        memory_text = approval_for(report)["correction"]
    if memory_text and not report.get("memory_id"):
        created, memory_decision = await _create_memory(report, memory_text, reviewer)
        in_hand.append(rd.as_doc(memory_decision))
        report = await rd.get_report(report_id)
    memory_model = created or await _memory_for(report)

    decisions = rd.merge_decisions(await rd.decisions_for(report_id), *in_hand)
    task_doc = await store.get_db()["tasks"].find_one({"report_id": report_id})
    message = decision_message(report, task_doc, await _accepted_count(report), decisions, memory_model is not None)
    return m.ReportDecisionResponse(
        report=rd.report_model(report),
        decisions=[rd.decision_model(d) for d in decisions],
        task=ta.task_model(task_doc) if task_doc else None,
        memory=memory_model,
        message=message,
    )


def approval_for(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("approval") or {}


@router.get("/tasks", response_model=m.TaskList, tags=["tasks"])
async def list_tasks(request: Request, report_id: str | None = Query(default=None)) -> m.TaskList:
    await _caller(request)
    query = {"report_id": report_id} if report_id else {}
    docs = [d async for d in store.get_db()["tasks"].find(query)]
    docs.sort(key=lambda d: (d.get("created_at") is None, d.get("created_at")), reverse=True)
    return m.TaskList(items=[ta.task_model(d) for d in docs], next=None)


@router.get("/tasks/{task_id}", response_model=m.Task, tags=["tasks"])
async def get_task(task_id: str, request: Request) -> m.Task:
    await _caller(request)
    doc = await store.get_db()["tasks"].find_one({"_id": task_id})
    if doc is None:
        raise ApiError(404, "not_found", "Task not found.")
    return ta.task_model(doc)
