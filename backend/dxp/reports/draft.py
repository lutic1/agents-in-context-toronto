"""Report drafting, with and without memories (V5, V21). Stub from A01 (contract); finished by A19+A20. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Memory, Relationship


async def draft(item: dict[str, Any], findings: list[dict[str, Any]], related: list[Relationship], memories: list[Memory]) -> dict[str, Any]:
    """Draft the report fields (headline, discovery and mentions, uncertainties, gap, recommended task,
    updates); drafts with and without the memories so each memory's before-and-after effect is known."""
    raise NotImplementedError("reports.draft (A19+A20)")
