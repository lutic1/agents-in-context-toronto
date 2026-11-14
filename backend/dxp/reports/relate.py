"""Relationship labels with two checked quotes (AD-26). Stub from A01 (contract); finished by A19+A20. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Relationship


async def relate(new_item: dict[str, Any], related_item: dict[str, Any]) -> Relationship:
    """supports | contradicts | extends | new_question, or related_unestablished without two found quotes."""
    raise NotImplementedError("reports.relate (A19+A20)")
