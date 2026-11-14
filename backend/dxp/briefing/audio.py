"""ElevenLabs briefing from report.script (V41). Stub from A01 (contract); finished by B06. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Briefing, Decision, RunContext


async def generate(report_id: str, ctx: RunContext) -> tuple[Briefing, Decision]:
    """Gated generate_briefing to tts:elevenlabs under sam@v1; called only by its own route."""
    raise NotImplementedError("briefing.generate (B06)")
