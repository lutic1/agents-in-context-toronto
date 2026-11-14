"""Report filing (AD-27). Stub from A01 (contract); finished by A19+A20. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Decision, RunContext


async def file(draft: dict[str, Any], ctx: RunContext, final: bool = True) -> Decision:
    """Gate one draft as a report-level file_proposal. `final=False` (every draft but the last):
    gate only, nothing written. `final=True` and allowed: store the report pending with its script
    (V41) and ledger.file each update, each keeping its own admission_id (D22). Never creates or
    sends notify_slack: the run (A10) dispatches the one alert after the final file succeeds
    (Luis's ruling, 14 Nov). Returns the Decision."""
    raise NotImplementedError("reports.file (A19+A20)")


async def add_related(report_id: str, refs: list[str], ctx: RunContext) -> list[Decision]:
    """file_related_evidence for a task run: pending related evidence, never accepted knowledge."""
    raise NotImplementedError("reports.add_related (A19+A20)")
