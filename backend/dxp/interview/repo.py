"""Reads for the interview lane. The lane writes nothing: its one write is the gate's Decision.

Two reads only, both from the store: the report document, and the `raw_text` of a pinned source
version (V40) so a quote can be checked again against the exact version it names. Tests replace
these two functions.
"""

from __future__ import annotations

from typing import Any

__all__ = ["get_raw_text", "get_report"]


async def get_report(report_id: str) -> dict[str, Any] | None:
    """The stored report document (`_id` is the report ID), whatever its status, or None."""
    from dxp import store

    return await store.collection("reports").find_one({"_id": report_id})


async def get_raw_text(version_id: str) -> str | None:
    """`raw_text` of one immutable source version, or None if the version is unknown."""
    from dxp import store

    doc = await store.collection("source_versions").find_one({"_id": version_id}, {"raw_text": 1})
    text = (doc or {}).get("raw_text")
    return text if isinstance(text, str) else None
