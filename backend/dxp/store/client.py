"""One AsyncMongoClient per process, reading MONGODB_URI and DXP_DB."""

from __future__ import annotations

import os

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

_client: AsyncMongoClient | None = None


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        # The value itself is never echoed: MONGODB_URI holds a credential.
        raise RuntimeError(f"{name} is not set.")
    return value


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(_require("MONGODB_URI"), tz_aware=True, appname="dxp")
    return _client


def get_db() -> AsyncDatabase:
    """The one database, named by DXP_DB (never defaulted, so a test never lands in `dxp`)."""
    return get_client()[_require("DXP_DB")]


async def close() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
