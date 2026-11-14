"""Report filing (AD-27). Stub from A01 (contract); finished by A19+A20. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Decision, RunContext


async def file(draft: dict[str, Any], ctx: RunContext) -> Decision:
    """Gate the report as a report-level file_proposal; allowed: store the report pending with its
    script (V41), ledger.file each update, one notify_slack action. Returns the Decision."""
    raise NotImplementedError("reports.file (A19+A20)")


async def add_related(report_id: str, refs: list[str], ctx: RunContext) -> list[Decision]:
    """file_related_evidence for a task run: pending related evidence, never accepted knowledge."""
    raise NotImplementedError("reports.add_related (A19+A20)")
