"""Embeddings on the `voyage` path (AD-15, OD1). The only holder of VOYAGE_API_KEY.

`DXP_EMBEDDING=auto` embeds inside Atlas and `none` embeds nothing, so this
module is called only when the mode is `voyage`. The key is read here, at call
time, and is never logged or returned.
"""

from __future__ import annotations

import os

from dxp.retrieval.indexes import EMBEDDING_PATH, TEXT_FIELDS, VOYAGE_DIMENSIONS, embedding_mode

VOYAGE_MODEL = "voyage-4"
BATCH = 64


def _client():
    import voyageai

    key = os.environ.get("VOYAGE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("VOYAGE_API_KEY is not set.")
    return voyageai.AsyncClient(api_key=key)


async def _embed(texts: list[str], input_type: str) -> list[list[float]]:
    if embedding_mode() != "voyage":
        raise RuntimeError("retrieval.embed is used only when DXP_EMBEDDING is voyage.")
    texts = [text if isinstance(text, str) else "" for text in texts]
    if not texts:
        return []
    client = _client()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH):
        result = await client.embed(
            texts[start:start + BATCH],
            model=VOYAGE_MODEL,
            input_type=input_type,
            output_dimension=VOYAGE_DIMENSIONS,
        )
        vectors.extend([list(vector) for vector in result.embeddings])
    return vectors


async def embed(texts: list[str]) -> list[list[float]]:
    """One vector per text, as stored documents (the `voyage` path only)."""
    return await _embed(texts, "document")


async def embed_query(text: str) -> list[float]:
    """The vector of one query text."""
    return (await _embed([text], "query"))[0]


async def embed_missing(db, match: dict | None = None, collections: tuple[str, ...] | None = None) -> int:
    """Write `embedding` on every document that has its text field and no embedding yet.

    Returns the number of documents embedded. `match` narrows the documents
    (for example one Team's memories).
    """
    done = 0
    for collection in collections or tuple(TEXT_FIELDS):
        field = TEXT_FIELDS[collection]
        query = {**(match or {}), EMBEDDING_PATH: {"$exists": False}, field: {"$type": "string"}}
        documents = await db[collection].find(query, {field: 1}).to_list(length=None)
        documents = [doc for doc in documents if doc.get(field, "").strip()]
        if not documents:
            continue
        vectors = await embed([doc[field] for doc in documents])
        for doc, vector in zip(documents, vectors):
            await db[collection].update_one({"_id": doc["_id"]}, {"$set": {EMBEDDING_PATH: vector}})
            done += 1
    return done
