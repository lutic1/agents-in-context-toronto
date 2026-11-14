"""Research reports (Story 10.4). Stub from A01 (contract); finished by A19+A20.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A19+A20 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A19+A20"


@router.get("/reports", response_model=m.ReportList, tags=["reports"])
async def list_reports(status: str | None = Query(default=None), run_id: str | None = Query(default=None)) -> m.ReportList:
    raise not_implemented("GET /reports", OWNER)


@router.get("/reports/{report_id}", response_model=m.Report, tags=["reports"])
async def get_report(report_id: str) -> m.Report:
    """Whatever its status; 404 for an unknown ID."""
    raise not_implemented("GET /reports/<report_id>", OWNER)
