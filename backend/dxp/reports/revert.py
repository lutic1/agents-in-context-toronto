"""Revert one approval (AD-31, V48, supporting, revert flag). Stub from A01 (contract); finished by A26. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Decision, Principal, Report


async def revert(report_id: str, note: str, reviewer: Principal) -> tuple[Report, Decision, int]:
    """Gated revert_report under sam@v1; claim accepted -> reverting with the revert record;
    ledger.revert_proposal per applied proposal; report and relationships reverted.
    Returns the report, the Decision and the number of accepted updates removed."""
    raise NotImplementedError("reports.revert (A26)")


async def recover_reverting() -> None:
    """Finish a report left in reverting. No-op stub: the API start hook calls it before A26 merges."""
    return None
