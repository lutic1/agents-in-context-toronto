"""Memory retrieval (AD-28, V22). Stub from A01 (contract); finished by A21+A22. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Memory, Retrieval


async def retrieve(team_id: str, text: str, tags: dict[str, Any] | None) -> tuple[list[Memory], Retrieval]:
    """Only active versions of the Team, ranked by retrieval.memories."""
    raise NotImplementedError("memory.retrieve (A21+A22)")
