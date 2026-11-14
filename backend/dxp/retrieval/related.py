"""Related evidence and memory retrieval, with an honest text-search fallback. Stub from A01 (contract); finished by A19+A20. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Retrieval


async def related(scope_id: str, text: str, k: int, exclude: list[str] | None = None) -> Retrieval:
    """Related source items and findings in the scope; scores are shown, never used as evidence."""
    raise NotImplementedError("retrieval.related (A19+A20)")


async def memories(team_id: str, text: str, tags: dict[str, Any] | None, k: int) -> Retrieval:
    """Team-scoped active memories (filter on claim_kind, V22)."""
    raise NotImplementedError("retrieval.memories (A19+A20)")
