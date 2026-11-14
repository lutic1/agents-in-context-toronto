"""ledger.apply and recovery (AD-1, D13, D26, D27). Stub from A01 (contract); finished by A06. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Proposal


async def apply(proposal_id: str) -> Proposal:
    """pending -> applying (claim) -> applied, with the guarded update."""
    raise NotImplementedError("ledger.apply (A06)")


async def recover_applying() -> None:
    """Finish proposals stuck in applying. No-op stub: the API start hook calls it before A06 merges."""
    return None
