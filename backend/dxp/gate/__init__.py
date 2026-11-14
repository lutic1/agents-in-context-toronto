"""The policy gate (AD-19). Stub from A01 (contract); finished by A06. Frozen signature: change only through the contract keeper.

gate imports nothing from memory, retrieval or reports (AD-28).
"""

from __future__ import annotations

from dxp.api.models import Decision, ProposedAction, RunContext

__all__ = ["evaluate"]


async def evaluate(ctx: RunContext, action: ProposedAction) -> Decision:
    """The only policy check: the five checks in order (check 4 includes the claim checks, V7).
    Inserts one decisions document, allowed or blocked, and one action_allowed or action_blocked event."""
    raise NotImplementedError("gate.evaluate (A06)")
