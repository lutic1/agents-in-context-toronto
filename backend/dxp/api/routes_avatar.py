"""Avatar session token, on demand (Story 10.12, avatar flag, V29, V70). Finished by B08.

Paths, methods and parameters are the frozen AD-14 ones. `POST` mints a short-lived LiveAvatar FULL
session token for the interview page and returns it only in `AvatarResponse.session_token`.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dxp import feature_enabled
from dxp.api import models as m
from dxp.api.auth import KEY_HEADER, require_principal
from dxp.api.errors import ApiError
from dxp.briefing import avatar as avatar_module

router = APIRouter()
OWNER = "B08"


def _require_flag() -> None:
    if not feature_enabled("avatar"):
        raise ApiError(404, "not_found", "Not found.")


@router.post("/reports/{report_id}/avatar", response_model=m.AvatarResponse, tags=["media"])
async def render_avatar(report_id: str, request: Request) -> JSONResponse:
    """Reviewer only, with the `avatar` flag on (else 404). Gated as `generate_avatar_video` under
    `sam@v1`; mints one token after an allowed Decision, only for an accepted report (else 409). A blocked
    request is a 200 with the blocked Decision (D5), never an error."""
    _require_flag()
    principal = await require_principal(request)
    report = await avatar_module.get_report(report_id)
    if report is None:
        raise ApiError(404, "not_found", "Report not found.")
    ctx = await avatar_module.reviewer_context(principal, request.headers.get(KEY_HEADER) or "", report)
    outcome = await avatar_module.start_avatar_session(report_id, ctx)
    body = m.AvatarResponse(
        media=outcome.media,
        decision=outcome.decision,
        session_token=outcome.session_token,
        session_expires_at=outcome.session_expires_at,
    )
    # The token is secret: never cached by the browser or a proxy.
    return JSONResponse(body.model_dump(mode="json"), headers={"Cache-Control": "no-store"})


@router.get("/reports/{report_id}/avatar", response_model=m.Media, tags=["media"])
async def get_avatar(report_id: str, request: Request) -> m.Media:
    """The latest avatar status for the report; 404 when none was requested. Never returns a token."""
    _require_flag()
    await require_principal(request)
    media = await avatar_module.avatar_status(report_id)
    if media is None:
        raise ApiError(404, "not_found", "No avatar was requested for this report.")
    return media
