"""Report briefing, on demand (Story 10.11, briefing flag, V29). Finished by B06.

Paths, methods, parameters and response models are A01's frozen ones (AD-14); only the bodies are
new. `POST` is the only way a briefing is made: a Reviewer presses "Generate briefing". `GET`
returns the report's script as text always, plus the audio status and URL, and serves the cached
audio itself when asked for it (`?audio=1`, or `Accept: audio/mpeg`), 404 while none exists.
Both return 404 in the error shape when the `briefing` flag is off, before anything else is read.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Request, Response

from dxp import feature_enabled
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.briefing import audio
from dxp.gate import policy_sets

router = APIRouter()


def _not_found(report_id: str) -> ApiError:
    return ApiError(404, "report_not_found", f"No report has the ID {report_id}.")


def _require_enabled() -> None:
    """The `briefing` flag (DXP_FEATURES) is off unless named: then there is no briefing route."""
    if not feature_enabled("briefing"):
        raise ApiError(404, "not_found", "Not found.")


async def reviewer_context(request: Request, report_id: str, origin_run_id: str | None) -> m.RunContext:
    """The context of a Reviewer decision (AD-30): `run_id` null, the Reviewer's stamp, a
    server-generated `request_id`, and `cause { report_id, origin_run_id }`. The caller is resolved
    from `X-DxP-Key` only; nothing in the body or the URL says who is asking."""
    principal = await auth.require_principal(request)
    if principal.kind != "person":
        raise ApiError(403, "reviewer_only", "Only a Reviewer can generate a briefing.")
    grant = await auth.grant_for_key(request.headers.get(auth.KEY_HEADER))
    if grant is None:  # resolved a moment ago; only a race with a hand edit gets here
        raise ApiError(401, "unknown_key", "Unknown API key.")
    policy_set = await policy_sets.current_set()
    stamp = m.Stamp(
        kind="reviewer",
        run_id=None,
        agent=None,
        initiated_by=principal.id,
        principal=principal.id,
        acting_for=grant.get("acting_for"),
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
        policy_set_version=policy_set.id,
    )
    return m.RunContext(
        run_id=None,
        principal=principal,
        stamp=stamp,
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
        run_grant_version=None,
        policy_set_version=policy_set.id,
        mode="live",
        request_id="req_" + secrets.token_hex(8),
        cause=m.DecisionCause(report_id=report_id, origin_run_id=origin_run_id),
    )


@router.post("/reports/{report_id}/briefing", response_model=m.BriefingResponse, tags=["media"])
async def generate_briefing(request: Request, report_id: str) -> m.BriefingResponse:
    """Generate the briefing from `report.script`, gated as `generate_briefing` under the Reviewer's
    grant. A blocked request is not an error: 200 with the Decision, nothing called. A failed or
    unavailable ElevenLabs is the error shape with 503 (the Decision is in the audit); the report,
    the decision and everything else carry on. 404 when the `briefing` flag is off."""
    _require_enabled()
    try:
        report = await audio.report_for(report_id)
        ctx = await reviewer_context(request, report_id, report.get("run_id"))
        briefing, decision = await audio.generate(report_id, ctx)
    except audio.ReportNotFound:
        raise _not_found(report_id) from None
    except audio.ScriptMissing:
        raise ApiError(409, "no_script", "This report has no script to read.") from None
    if decision.outcome == "allowed" and briefing.status in ("failed", "unavailable"):
        raise ApiError(503, "briefing_unavailable", "Briefing unavailable. The script is shown on the report.")
    return m.BriefingResponse(briefing=briefing, decision=decision)


@router.get("/reports/{report_id}/briefing", response_model=m.Briefing, tags=["media"])
async def get_briefing(request: Request, report_id: str):
    """The script as text always (V41), plus the audio status and URL; or the audio itself.
    404 when the `briefing` flag is off."""
    _require_enabled()
    await auth.require_principal(request)
    wants_audio = request.query_params.get("audio") == "1" or "audio/mpeg" in request.headers.get("accept", "")
    try:
        if wants_audio:
            found = await audio.audio_bytes(report_id)
            if found is None:
                raise ApiError(404, "briefing_not_found", "No briefing has been generated for this report.")
            content, mime = found
            return Response(content=content, media_type=mime, headers={"Cache-Control": "private, max-age=3600"})
        return await audio.status(report_id)
    except audio.ReportNotFound:
        raise _not_found(report_id) from None
