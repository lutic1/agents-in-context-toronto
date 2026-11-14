"""Related evidence and memory retrieval, with an honest text-search fallback (AD-15).

Order of attempts: `$vectorSearch` (only when DXP_EMBEDDING is `auto` or
`voyage`), then Atlas Search `$search`, then a `$text` query on the regular
text index. The first attempt that returns items wins and names its method;
an attempt that fails or finds nothing hands over to the next. A text result
always says `text_search`. A score is returned beside each item and is never
read here or anywhere else as evidence.
"""

from __future__ import annotations

import logging
from typing import Any

from dxp.api.models import Retrieval, RetrievalFilter, RetrievalItem
from dxp.retrieval.embed import embed_query
from dxp.retrieval.indexes import (
    EMBEDDING_PATH,
    REGULAR_TEXT_INDEX_NAMES,
    TEXT_FIELDS,
    TEXT_INDEX_NAMES,
    VECTOR_INDEX_NAMES,
    embedding_mode,
)

log = logging.getLogger("dxp.retrieval")

VECTOR = "vector_search"
TEXT = "text_search"
MAX_QUERY_CHARS = 4000
_SOURCE_FIELDS = {"source_ref": 1, "current_version_id": 1, "version_id": 1}
_FINDING_FIELDS = {"source_ref": 1, "version_id": 1}
_MEMORY_FIELDS = {"memory_id": 1, "version": 1}


def _mode() -> str:
    try:
        return embedding_mode()
    except ValueError:
        return "none"


def _db():
    from dxp import store

    return store.db()


# ------------------------------------------------------------------ one query

async def _vector(db, collection: str, text: str, limit: int, filters: dict[str, Any], fields: dict, mode: str) -> list[dict]:
    stage: dict[str, Any] = {
        "index": VECTOR_INDEX_NAMES[collection],
        "numCandidates": max(100, limit * 20),
        "limit": limit,
    }
    if mode == "auto":
        stage.update(path=TEXT_FIELDS[collection], query={"text": text})
    else:
        stage.update(path=EMBEDDING_PATH, queryVector=await embed_query(text))
    if filters:
        stage["filter"] = {"$and": [{path: {"$eq": value}} for path, value in filters.items()]}
    cursor = await db[collection].aggregate([
        {"$vectorSearch": stage},
        {"$project": {**fields, "score": {"$meta": "vectorSearchScore"}}},
    ])
    return await cursor.to_list(length=limit)


async def _search(db, collection: str, text: str, limit: int, filters: dict[str, Any], fields: dict, mode: str) -> list[dict]:
    compound: dict[str, Any] = {"must": [{"text": {"query": text, "path": TEXT_FIELDS[collection]}}]}
    if filters:
        compound["filter"] = [{"equals": {"path": path, "value": value}} for path, value in filters.items()]
    cursor = await db[collection].aggregate([
        {"$search": {"index": TEXT_INDEX_NAMES[collection], "compound": compound}},
        {"$limit": limit},
        {"$project": {**fields, "score": {"$meta": "searchScore"}}},
    ])
    return await cursor.to_list(length=limit)


async def _text(db, collection: str, text: str, limit: int, filters: dict[str, Any], fields: dict, mode: str) -> list[dict]:
    score = {"$meta": "textScore"}
    cursor = db[collection].find({"$text": {"$search": text}, **filters}, {**fields, "score": score})
    return await cursor.sort([("score", score)]).limit(limit).to_list(length=limit)


def _attempts(mode: str) -> list[tuple[str, Any, dict[str, str]]]:
    attempts = []
    if mode in ("auto", "voyage"):
        attempts.append((VECTOR, _vector, VECTOR_INDEX_NAMES))
    attempts.append((TEXT, _search, TEXT_INDEX_NAMES))
    attempts.append((TEXT, _text, REGULAR_TEXT_INDEX_NAMES))
    return attempts


def _item(ref: Any, version_id: Any, score: Any) -> RetrievalItem:
    return RetrievalItem(ref=str(ref), version_id=version_id, score=float(score or 0.0))


def _ranked(items: list[RetrievalItem], k: int) -> list[RetrievalItem]:
    best: dict[str, RetrievalItem] = {}
    for item in items:
        if item.ref not in best or item.score > best[item.ref].score:
            best[item.ref] = item
    return sorted(best.values(), key=lambda item: (-item.score, item.ref))[:k]


async def _run(attempts, search, top_k: int, filter: RetrievalFilter, collections: list[str]) -> Retrieval:
    """Try each method in turn; `search(query_fn)` returns the items of one method."""
    first: Retrieval | None = None
    for method, query_fn, names in attempts:
        try:
            items = await search(query_fn)
        except Exception as exc:
            log.warning("retrieval: %s on %s failed: %s", method, names[collections[0]], type(exc).__name__)
            continue
        result = Retrieval(
            method=method,
            index="+".join(names[c] for c in collections),
            top_k=top_k,
            filter=filter,
            items=items,
        )
        if items:
            return result
        first = first or result
    return first or Retrieval(method=TEXT, index=None, top_k=top_k, filter=filter, items=[])


# ---------------------------------------------------------------- public calls

async def related(scope_id: str, text: str, k: int, exclude: list[str] | None = None) -> Retrieval:
    """Related source items and findings in the scope; scores are shown, never used as evidence."""
    k = max(int(k or 0), 0)
    excluded = set(exclude or [])
    flt = RetrievalFilter(scope_id=scope_id)
    query = (text or "").strip()[:MAX_QUERY_CHARS]
    mode = _mode()
    if not query or not k:
        return Retrieval(method=TEXT, index=None, top_k=k, filter=flt, items=[])  # nothing was searched
    db = _db()
    wide = k + len(excluded)

    async def search(query_fn) -> list[RetrievalItem]:
        items: list[RetrievalItem] = []
        sources = await query_fn(db, "source_items", query, wide, {"scope_ids": scope_id}, _SOURCE_FIELDS, mode)
        for doc in sources:
            ref = doc.get("source_ref") or doc.get("_id")
            if ref in excluded:
                continue
            items.append(_item(ref, doc.get("current_version_id") or doc.get("version_id"), doc.get("score")))
        try:
            # Findings carry no scope: keep those whose source item is in the scope.
            findings = await query_fn(db, "findings", query, wide * 4, {}, _FINDING_FIELDS, mode)
            findings = [doc for doc in findings if doc.get("source_ref") not in excluded]
            refs = sorted({doc.get("source_ref") for doc in findings if doc.get("source_ref")})
            in_scope = set()
            if refs:
                found = await db["source_items"].find({"_id": {"$in": refs}, "scope_ids": scope_id}, {"_id": 1}).to_list(length=None)
                in_scope = {doc["_id"] for doc in found}
            for doc in findings:
                if doc.get("source_ref") in in_scope:
                    items.append(_item(doc["_id"], doc.get("version_id"), doc.get("score")))
        except Exception as exc:
            if not sources:
                raise
            log.warning("retrieval: findings query failed: %s", type(exc).__name__)
        return _ranked(items, k)

    return await _run(_attempts(mode), search, k, flt, ["source_items", "findings"])


async def memories(team_id: str, text: str, tags: dict[str, Any] | None, k: int) -> Retrieval:
    """Team-scoped active memories (filter on claim_kind, V22)."""
    k = max(int(k or 0), 0)
    claim_kind = (tags or {}).get("claim_kind")
    # V22: the assay tag is recorded and shown, never required to match.
    filters: dict[str, Any] = {"team_id": team_id, "status": "active"}
    if claim_kind:
        filters["tags.claim_kind"] = claim_kind
    flt = RetrievalFilter(team_id=team_id, status="active", tags={"claim_kind": claim_kind} if claim_kind else None)
    query = (text or "").strip()[:MAX_QUERY_CHARS]
    mode = _mode()
    if not query or not k:
        return Retrieval(method=TEXT, index=None, top_k=k, filter=flt, items=[])  # nothing was searched
    db = _db()
    # Read-only (AD-28): in voyage mode `memory.create`/`correct` write each version's embedding.

    async def search(query_fn) -> list[RetrievalItem]:
        docs = await query_fn(db, "memories", query, k, filters, _MEMORY_FIELDS, mode)
        return _ranked([_item(doc.get("memory_id") or doc.get("_id"), None, doc.get("score")) for doc in docs], k)

    return await _run(_attempts(mode), search, k, flt, ["memories"])
