"""create, correct, revoke: gated create_memory, correct_memory, revoke_memory. Stub from A01 (contract); finished by A21+A22. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Decision, Memory, MemorySource, Principal, RunContext


async def create(team_id: str, text: str, tags: dict[str, Any], source: MemorySource, reviewer: Principal, ctx: RunContext) -> tuple[Memory, Decision]:
    raise NotImplementedError("memory.create (A21+A22)")


async def correct(memory_id: str, text: str, note: str, ctx: RunContext) -> tuple[Memory, Decision]:
    """New version with supersedes; the old one corrected, conditional on its status."""
    raise NotImplementedError("memory.correct (A21+A22)")


async def revoke(memory_id: str, note: str, ctx: RunContext) -> tuple[Memory, Decision]:
    raise NotImplementedError("memory.revoke (A21+A22)")
