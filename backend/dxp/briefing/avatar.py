"""HeyGen avatar video from report.script (V29, V41). Stub from A01 (contract); finished by B08. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Decision, Media, RunContext


async def render_avatar(report_id: str, ctx: RunContext) -> tuple[Media, Decision]:
    """Gated generate_avatar_video to video:heygen under sam@v1; returns at once."""
    raise NotImplementedError("briefing.render_avatar (B08)")


async def avatar_status(report_id: str) -> Media | None:
    """Current Media; checks a rendering video with HeyGen in the background, never waits."""
    raise NotImplementedError("briefing.avatar_status (B08)")
