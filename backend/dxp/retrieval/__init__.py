"""Retrieval (AD-15): the only embedding and $vectorSearch / $search caller."""

from __future__ import annotations

from dxp.retrieval.embed import embed
from dxp.retrieval.indexes import ensure_indexes
from dxp.retrieval.related import memories, related

__all__ = ["embed", "ensure_indexes", "memories", "related"]
