"""Interview this evidence (V70, interview flag). Stub from A01 (contract); finished by the interview lane.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Returns 501 in the error shape until the interview lane finishes it (then 404 when `interview` is off).
"""

from __future__ import annotations

from fastapi import APIRouter

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "Interview"


@router.post("/reports/{report_id}/interview", response_model=m.InterviewResponse, tags=["reports"])
async def interview_report(report_id: str, body: m.InterviewRequest) -> m.InterviewResponse:
    raise not_implemented("POST /reports/<report_id>/interview", OWNER)
