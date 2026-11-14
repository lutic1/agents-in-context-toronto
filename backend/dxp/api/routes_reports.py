"""Research reports (Story 10.4): GET /reports and GET /reports/<report_id> (A19+A20).

Paths, methods, parameters and response models are frozen (AD-14). Both routes
read the `reports` collection; quotes only, never `raw_text` (V40).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from dxp.api import models as m
from dxp.api.errors import ApiError

router = APIRouter()
OWNER = "A19+A20"
MAX_REPORTS = 200


def _relationship(stored: dict[str, Any]) -> dict[str, Any]:
    out = dict(stored)
    out["id"] = out.get("id") or out.pop("_id", None)
    out.pop("_id", None)
    return out


async def _notification(db, report_id: str) -> m.ProposalNotification | None:
    """Read time only: built from the report's notify_slack action (V11, D47)."""
    action = await db["actions"].find_one({"target.report_id": report_id, "kind": "notify_slack"})
    if not action:
        return None
    result = action.get("result") or {}
    return m.ProposalNotification(
        action_id=str(action.get("_id") or action.get("id")),
        status=action.get("status"),
        posted_at=result.get("posted_at") if isinstance(result, dict) else None,
    )


async def _report(db, document: dict[str, Any]) -> m.Report:
    fields = dict(document)
    fields["id"] = str(fields.pop("_id"))
    fields["related"] = [_relationship(r) for r in fields.get("related") or []]
    fields["script"] = fields.get("script") or ""
    fields["script_hash"] = fields.get("script_hash") or ""
    fields["gap"] = fields.get("gap") or ""
    try:
        fields["notification"] = await _notification(db, fields["id"])
    except Exception:
        fields["notification"] = None  # the alert's state is shown when it can be read; the report always is
    return m.Report.model_validate(fields)


@router.get("/reports", response_model=m.ReportList, tags=["reports"])
async def list_reports(status: str | None = Query(default=None), run_id: str | None = Query(default=None)) -> m.ReportList:
    from dxp import store

    db = store.db()
    query: dict[str, Any] = {}
    if status:
        query["status"] = status
    if run_id:
        query["run_id"] = run_id
    documents = await db["reports"].find(query).sort("created_at", -1).limit(MAX_REPORTS).to_list(length=MAX_REPORTS)
    return m.ReportList(items=[await _report(db, document) for document in documents])


@router.get("/reports/{report_id}", response_model=m.Report, tags=["reports"])
async def get_report(report_id: str) -> m.Report:
    """Whatever its status; 404 for an unknown ID."""
    from dxp import store

    db = store.db()
    document = await db["reports"].find_one({"_id": report_id})
    if document is None:
        raise ApiError(404, "not_found", f"Report {report_id} not found.")
    return await _report(db, document)
