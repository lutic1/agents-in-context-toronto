"""Revert one approval (Story 10.13, revert flag, AD-31, V48). Stub from A01 (contract); finished by A26.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Returns 501 in the error shape until A26 finishes it (then 404 when `revert` is off).
"""

from __future__ import annotations

from fastapi import APIRouter

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A26"


@router.post("/reports/{report_id}/revert", response_model=m.ReportRevertResponse, tags=["reports"])
async def revert_report(report_id: str, body: m.ReportRevertRequest) -> m.ReportRevertResponse:
    raise not_implemented("POST /reports/<report_id>/revert", OWNER)
