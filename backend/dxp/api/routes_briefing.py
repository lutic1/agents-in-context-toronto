"""Report briefing, on demand (Story 10.11, briefing flag, V29). Stub from A01 (contract); finished by B06.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until B06 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "B06"


@router.post("/reports/{report_id}/briefing", response_model=m.BriefingResponse, tags=["media"])
async def generate_briefing(report_id: str) -> m.BriefingResponse:
    raise not_implemented("POST /reports/<report_id>/briefing", OWNER)


@router.get("/reports/{report_id}/briefing", response_model=m.Briefing, tags=["media"])
async def get_briefing(report_id: str) -> m.Briefing:
    """The script as text always, plus the audio status and URL (V41)."""
    raise not_implemented("GET /reports/<report_id>/briefing", OWNER)
