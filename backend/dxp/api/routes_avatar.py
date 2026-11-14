"""Avatar video, on demand (Story 10.12, avatar flag, V29). Stub from A01 (contract); finished by B08.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until B08 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "B08"


@router.post("/reports/{report_id}/avatar", response_model=m.AvatarResponse, tags=["media"])
async def render_avatar(report_id: str) -> m.AvatarResponse:
    raise not_implemented("POST /reports/<report_id>/avatar", OWNER)


@router.get("/reports/{report_id}/avatar", response_model=m.Media, tags=["media"])
async def get_avatar(report_id: str) -> m.Media:
    raise not_implemented("GET /reports/<report_id>/avatar", OWNER)
