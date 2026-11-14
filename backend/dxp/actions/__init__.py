"""External actions (AD-20). Stub from A01 (contract); finished by A09. Frozen signature: change only through the contract keeper.

actions imports nothing from memory, retrieval or reports (AD-28).
"""

from __future__ import annotations

from typing import Literal

from dxp.api.models import Action, Decision, ProposedAction, RunContext


async def dispatch(action: ProposedAction, ctx: RunContext) -> Action:
    """Gate, persist, claim queued -> dispatching, send, record exactly what was observed."""
    raise NotImplementedError("actions.dispatch (A09)")


async def mark_unknown(action_id: str, error: Literal["abandoned_in_flight"]) -> bool:
    """dispatching -> unknown, conditional; never re-sent (D43)."""
    raise NotImplementedError("actions.mark_unknown (A09)")


async def mark_failed(action_id: str, error: Literal["abandoned_before_send"]) -> bool:
    """queued -> failed, conditional; it was never sent (D24)."""
    raise NotImplementedError("actions.mark_failed (A09)")


async def resolve(action_id: str, outcome: Literal["delivered", "failed"], note: str, ctx: RunContext) -> tuple[Action, Decision]:
    """Gated resolve_notification: settle an unknown notification by hand; never posts (S8)."""
    raise NotImplementedError("actions.resolve (A09)")
