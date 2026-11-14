"""ledger.file (AD-1, AD-4, D46). Stub from A01 (contract); finished by A06. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Decision, Mode, RunContext


async def file(finding_id: str, changes: list[dict[str, Any]], mode: Mode, ctx: RunContext) -> list[Decision]:
    """Gate each change once, then file it (live: a pending proposal; baseline: applied at once).
    Returns one Decision per change, allowed or blocked."""
    raise NotImplementedError("ledger.file (A06)")
