"""The only Claude caller (AD-11). Stub from A01 (contract); finished by A08. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


async def extract(item: dict[str, Any], aliases: Sequence[str] | None = None) -> dict[str, Any]:
    """Extract a Finding from one source item version. aliases: the exact seeded trade names (V34)."""
    raise NotImplementedError("llm.extract (A08)")


async def check(finding: dict[str, Any], source_text: str) -> dict[str, Any]:
    """Check a Finding's quotes and support against its source text."""
    raise NotImplementedError("llm.check (A08)")


async def call_structured(model: str, schema: dict[str, Any], messages: list[dict[str, Any]]) -> dict[str, Any]:
    """One structured-output call (JSON schema), no sampling parameters."""
    raise NotImplementedError("llm.call_structured (A08)")
