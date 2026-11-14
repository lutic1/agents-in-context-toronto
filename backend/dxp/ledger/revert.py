"""Reverse proposals (AD-31, V48). Stub from A01 (contract); finished by A26. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Decision, Proposal


async def revert_proposal(proposal_id: str, decision: Decision) -> Proposal:
    """File derive("p_", proposal_id, "revert") (op remove, reverts_proposal_id) insert-if-absent and
    apply it pending -> applying -> applied with a guarded unset; emits value_reverted."""
    raise NotImplementedError("ledger.revert_proposal (A26)")


async def recover_reverting() -> None:
    """Finish reverse proposals stuck in applying. No-op stub: the API start hook calls it before A26 merges."""
    return None
