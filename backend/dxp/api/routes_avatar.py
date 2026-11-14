"""Avatar, on demand (Story 10.12, avatar flag, V29). Stub from A01 (contract); finished by B08.

Paths, methods and parameters are the frozen AD-14 ones. The avatar is now a HeyGen LiveAvatar, a live
session (pending Luis's approval as V70), so `POST` also returns the session token the browser needs.
`m.AvatarResponse` (`{ media, decision }`) has no field for it, and B08 may not edit A01's models, so the
route keeps `response_model=m.AvatarResponse` (the published contract) and answers with the local
`AvatarStartResponse`, which is `AvatarResponse` plus `session` and `unavailable_reason`. The proposed
contract change is in the B08 report.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dxp.api import models as m
from dxp.api.auth import KEY_HEADER, require_principal
from dxp.api.errors import ApiError
from dxp.briefing import avatar as avatar_module
from dxp.briefing.avatar import AvatarSession

router = APIRouter()
OWNER = "B08"


class AvatarStartResponse(m.AvatarResponse):
    """`AvatarResponse` plus the live session. `session` is null when the avatar is unavailable
    (blocked, no key, no avatar id, provider failure) and `unavailable_reason` says which."""

    session: AvatarSession | None = None
    unavailable_reason: Literal["blocked", "no_key", "no_avatar", "provider_error"] | None = None


@router.post("/reports/{report_id}/avatar", response_model=m.AvatarResponse, tags=["media"])
async def render_avatar(report_id: str, request: Request) -> JSONResponse:
    """Reviewer only. Gated as `generate_avatar_video` under `sam@v1`; mints one session token after
    an allowed Decision. A blocked request is a 200 with the blocked Decision (D5), never an error."""
    principal = await require_principal(request)
    report = await avatar_module.get_report(report_id)
    if report is None:
        raise ApiError(404, "not_found", "Report not found.")
    ctx = await avatar_module.reviewer_context(principal, request.headers.get(KEY_HEADER) or "", report)
    outcome = await avatar_module.start_avatar_session(report_id, ctx)
    body = AvatarStartResponse(
        media=outcome.media,
        decision=outcome.decision,
        session=outcome.session,
        unavailable_reason=outcome.reason,
    )
    # The token is single use and secret: never cached, and not part of the published schema.
    return JSONResponse(body.model_dump(mode="json"), headers={"Cache-Control": "no-store"})


@router.get("/reports/{report_id}/avatar", response_model=m.Media, tags=["media"])
async def get_avatar(report_id: str, request: Request) -> m.Media:
    """The latest avatar status for the report; 404 when none was requested. Never returns a token."""
    await require_principal(request)
    media = await avatar_module.avatar_status(report_id)
    if media is None:
        raise ApiError(404, "not_found", "No avatar was requested for this report.")
    return media
