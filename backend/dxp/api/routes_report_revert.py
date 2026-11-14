"""Revert one approval (Story 10.13, revert flag, AD-31, V48). A26.

`POST /reports/<report_id>/revert { note }`:

1. 404 when `revert` is not in `DXP_FEATURES` (the route then does not exist for the caller).
2. The caller from `X-DxP-Key` (D17). A blank note is 400 before the gate.
3. Recovery first: `ledger.recover_reverting()`, `reports.recover_reverting()`.
4. `reports.revert()` (gated `revert_report`). A report that is not `accepted`, `reverting`
   or `reverted` is 409 with its current status and no Decision.
5. Only once the report is `reverted`: `tasks.cancel_for_report()`. A blocked revert changes
   nothing, so the task is only read.

`reports` imports nothing from `tasks`: this route orchestrates. No A24 file is edited.
The response is `{ report, decision, task, removed }`; the frozen shape has no message field,
so the sentence "Approval reverted by Sam at {time}: ..." is left to the web app.
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Request

from dxp import feature_enabled, ledger, store
from dxp.api import models as m
from dxp.api.errors import ApiError

rd = importlib.import_module("dxp.reports.decide")
rv = importlib.import_module("dxp.reports.revert")
tc = importlib.import_module("dxp.tasks.cancel")
ta = importlib.import_module("dxp.tasks.authorise")
decision_route = importlib.import_module("dxp.api.routes_report_decision")

router = APIRouter()
OWNER = "A26"
REVERT_FLAG = "revert"


async def _task_for(report: m.Report) -> m.Task | None:
    doc = await store.get_db()["tasks"].find_one({"report_id": report.id})
    return ta.task_model(doc) if doc else None


@router.post("/reports/{report_id}/revert", response_model=m.ReportRevertResponse, tags=["reports"])
async def revert_report(report_id: str, body: m.ReportRevertRequest, request: Request) -> m.ReportRevertResponse:
    if not feature_enabled(REVERT_FLAG):
        raise ApiError(404, "not_found", "Not found.")
    reviewer = await decision_route._caller(request)
    # Only a person reverts. The revert Decision ID does not depend on the request and a blocked
    # revert is final, so an agent key reaching the gate would lock Sam out of this report for good.
    if reviewer.kind != "person":
        raise ApiError(403, "person_only", "Only a person can revert an approval.")
    if not (body.note or "").strip():
        raise ApiError(400, "note_required", "A revert needs a note.")

    await ledger.recover_reverting()
    await rv.recover_reverting()

    try:
        report, decision, removed = await rv.revert(report_id, body.note, reviewer)
    except rd.ReportNotFound as exc:
        raise ApiError(404, "not_found", "Report not found.") from exc
    except rv.NotReversible as exc:
        raise ApiError(409, "not_reversible", "This report has updates that cannot be reverted here.") from exc
    except rv.NotRevertable as exc:
        raise ApiError(409, "not_revertable",
                       f"Report is {exc.status}; only an accepted report can be reverted.") from exc

    if report.status == "reverted":
        task = await tc.cancel_for_report(report, decision)
    else:
        task = await _task_for(report)
    return m.ReportRevertResponse(report=report, decision=decision, task=task, removed=removed)
