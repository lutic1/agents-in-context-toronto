"""Index definitions for retrieval (AD-15, Story 10.2).

Definitions are plain data built by pure functions; ensure_indexes() only
applies them. Nothing here connects to a database at import time.
"""
from __future__ import annotations

import asyncio
import logging
import os

log = logging.getLogger("dxp.retrieval")

EMBEDDING_MODES = ("auto", "voyage", "none")

FILTER_FIELDS = ("scope_ids", "team_id", "status", "tags.assay", "tags.claim_kind")

# collection -> the one text field retrieval embeds and searches (AD-15)
TEXT_FIELDS = {
    "source_items": "evidence_text",
    "findings": "summary",
    "memories": "text",
}

VECTOR_INDEX_NAMES = {c: "vs_" + c for c in TEXT_FIELDS}
TEXT_INDEX_NAMES = {c: "ts_" + c for c in TEXT_FIELDS}
REGULAR_TEXT_INDEX_NAMES = {c: "tx_" + c for c in TEXT_FIELDS}

EMBEDDING_PATH = "embedding"
VOYAGE_DIMENSIONS = 1024
SIMILARITY = "cosine"
AUTO_EMBED_MODEL = "voyage-4"


def embedding_mode(value=None):
    """The embedding path: the argument, else DXP_EMBEDDING, else "none"."""
    if value is None:
        value = os.environ.get("DXP_EMBEDDING") or "none"
    mode = str(value).strip().lower()
    if mode not in EMBEDDING_MODES:
        raise ValueError(
            "DXP_EMBEDDING must be one of %s, got %r" % (", ".join(EMBEDDING_MODES), value)
        )
    return mode


def _filter_fields():
    return [{"type": "filter", "path": path} for path in FILTER_FIELDS]


def vector_index(collection, mode, model=AUTO_EMBED_MODEL, dimensions=VOYAGE_DIMENSIONS):
    """The Vector Search index of one collection for "auto" or "voyage"."""
    text_field = TEXT_FIELDS[collection]
    if mode == "auto":
        embedded = {"type": "autoEmbed", "modality": "text", "path": text_field, "model": model}
    elif mode == "voyage":
        embedded = {
            "type": "vector",
            "path": EMBEDDING_PATH,
            "numDimensions": dimensions,
            "similarity": SIMILARITY,
        }
    else:
        raise ValueError("no vector index in embedding mode %r" % (mode,))
    return {
        "collection": collection,
        "name": VECTOR_INDEX_NAMES[collection],
        "type": "vectorSearch",
        "definition": {"fields": [embedded] + _filter_fields()},
    }


def text_index(collection):
    """The Atlas Search ($search) fallback index of one collection."""
    return {
        "collection": collection,
        "name": TEXT_INDEX_NAMES[collection],
        "type": "search",
        "definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    TEXT_FIELDS[collection]: {"type": "string"},
                    "scope_ids": {"type": "token"},
                    "team_id": {"type": "token"},
                    "status": {"type": "token"},
                    "tags": {
                        "type": "document",
                        "fields": {
                            "assay": {"type": "token"},
                            "claim_kind": {"type": "token"},
                        },
                    },
                },
            }
        },
    }


def regular_text_index(collection):
    """The last-resort regular text index ($text) of one collection."""
    return {
        "collection": collection,
        "name": REGULAR_TEXT_INDEX_NAMES[collection],
        "type": "text",
        "keys": [(TEXT_FIELDS[collection], "text")],
    }


def index_definitions(mode):
    """Every index for an embedding mode: vector first (if any), then text."""
    mode = embedding_mode(mode)
    definitions = []
    if mode != "none":
        definitions += [vector_index(c, mode) for c in TEXT_FIELDS]
    definitions += [text_index(c) for c in TEXT_FIELDS]
    definitions += [regular_text_index(c) for c in TEXT_FIELDS]
    return definitions


async def _search_indexes(collection):
    cursor = await collection.list_search_indexes()
    return {index.get("name"): index async for index in cursor}


async def _ensure_one(db, spec):
    collection = db[spec["collection"]]
    if spec["type"] == "text":
        await collection.create_index(spec["keys"], name=spec["name"])
        return
    if spec["name"] in await _search_indexes(collection):
        return
    await collection.create_search_index(
        {"name": spec["name"], "type": spec["type"], "definition": spec["definition"]}
    )


async def ensure_indexes() -> None:
    """Create the missing indexes for the DXP_EMBEDDING path. Never raises.

    An index that cannot be built is logged by name and error type only; the
    retrieval calls then fall back honestly (AD-15). In `voyage` mode the
    documents still lacking an embedding are embedded first.
    """
    try:
        from dxp import store

        mode = embedding_mode()
        db = store.db()
    except Exception as exc:  # no database or a bad DXP_EMBEDDING: nothing to build
        log.warning("retrieval.ensure_indexes skipped: %s", type(exc).__name__)
        return None
    if mode == "voyage":
        try:
            from dxp.retrieval.embed import embed_missing

            await embed_missing(db)
        except Exception as exc:
            log.warning("retrieval.ensure_indexes: embedding failed: %s", type(exc).__name__)
    for spec in index_definitions(mode):
        try:
            await _ensure_one(db, spec)
        except Exception as exc:
            log.warning("retrieval.ensure_indexes: %s not built: %s", spec["name"], type(exc).__name__)
    return None


async def index_status(mode=None):
    """{ index name: queryable } for every search and vector index of the mode."""
    from dxp import store

    db = store.db()
    status = {}
    for spec in index_definitions(mode):
        if spec["type"] == "text":
            continue
        try:
            found = (await _search_indexes(db[spec["collection"]])).get(spec["name"]) or {}
            status[spec["name"]] = bool(found.get("queryable"))
        except Exception:
            status[spec["name"]] = False
    return status


async def wait_until_queryable(timeout_s=900.0, poll_s=10.0, mode=None):
    """Setup helper (I1 step 1): True once every index is queryable, False on timeout."""
    waited = 0.0
    while True:
        status = await index_status(mode)
        if status and all(status.values()):
            return True
        if waited >= timeout_s:
            return False
        await asyncio.sleep(poll_s)
        waited += poll_s
