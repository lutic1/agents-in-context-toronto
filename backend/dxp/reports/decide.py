"""The report decision and its recovery (AD-29, V45). Stub from A01 (contract); finished by A24. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Literal

from dxp.api.models import Decision, Principal, Report


async def decide(report_id: str, action: Literal["approve", "reject"], note: str | None, correction: str | None, reviewer: Principal) -> tuple[Report, list[Decision]]:
    """Gated decide_report; the claim pending -> accepting stores the approval record (V45);
    ledger.apply per proposal, all or nothing."""
    raise NotImplementedError("reports.decide (A24)")


async def recover_accepting() -> None:
    """Finish an interrupted acceptance. No-op stub: the API start hook calls it before A24 merges."""
    return None
