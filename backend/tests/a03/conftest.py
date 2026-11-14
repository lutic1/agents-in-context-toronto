"""A03 test setup.

* Puts `backend/` on `sys.path` (A01's `conftest.py` and `pyproject.toml` do this
  once A01 is merged).
* Until A01 and A02 are on `main`, installs stand-ins for the frozen
  `dxp.identity` (A02) and `dxp.api.models.Principal` (A01) signatures, built to
  their written contracts (AD-3, AD-14). When the real modules exist they are used.
* `FakeDB`: a tiny in-memory async database that enforces each collection's
  `$jsonSchema` on insert (not `$expr`), for tests that need no Atlas.
* `atlas`: an Atlas-backed test database, used only when `MONGODB_URI` is set
  (skipped otherwise, with the reason). It is a fresh `dxp_test_a03_<random>`
  database, dropped afterwards; never `dxp`.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import os
import re
import sys
import types
import unicodedata
import uuid
from pathlib import Path
from typing import Any

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


if not _has("dxp.identity"):  # A02 not merged yet: its frozen signatures (AD-3)
    identity = types.ModuleType("dxp.identity")

    def derive(prefix: str, *parts: Any) -> str:
        return prefix + hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]

    def normalise_name(text: str) -> str:
        text = unicodedata.normalize("NFKC", text).lower()
        text = re.sub("[®™©]", "", text)
        return re.sub(r"[^0-9a-z]+", " ", text).strip()

    identity.derive = derive
    identity.normalise_name = normalise_name
    sys.modules["dxp.identity"] = identity

if not _has("dxp.api.models"):  # A01 not merged yet: the AD-14 Principal shape
    from pydantic import BaseModel

    class Principal(BaseModel):
        id: str
        name: str
        kind: str
        actions: list[str]

    models = types.ModuleType("dxp.api.models")
    models.Principal = Principal
    sys.modules["dxp.api.models"] = models


# --- In-memory database ---------------------------------------------------------

from pymongo.errors import DuplicateKeyError, WriteError

from dxp.store import schemas

from . import jsonschema_lite


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, want in query.items():
        have = doc
        for part in key.split("."):
            have = have.get(part) if isinstance(have, dict) else None
        if isinstance(want, dict) and "$in" in want:
            if have not in want["$in"]:
                return False
        elif have != want:
            return False
    return True


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self._docs = docs

    def sort(self, key: str, direction: int = 1) -> FakeCursor:
        self._docs.sort(key=lambda d: d.get(key), reverse=direction < 0)
        return self

    def limit(self, n: int) -> FakeCursor:
        self._docs = self._docs[:n] if n else self._docs
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return list(self._docs if length is None else self._docs[:length])


class FakeCollection:
    def __init__(self, db: FakeDB, name: str):
        self.db, self.name, self.docs = db, name, {}

    def find(self, query: dict[str, Any] | None = None, projection: Any = None) -> FakeCursor:
        return FakeCursor([dict(d) for d in self.docs.values() if _matches(d, query or {})])

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        found = await self.find(query).to_list(1)
        return found[0] if found else None

    async def insert_one(self, doc: dict[str, Any]) -> None:
        validator = self.db.validators.get(self.name)
        if validator is not None:
            problems = jsonschema_lite.validate(validator, doc)
            if problems:
                raise WriteError("Document failed validation: " + "; ".join(problems), 121)
        if doc["_id"] in self.docs:
            raise DuplicateKeyError(f"duplicate _id {doc['_id']}")
        self.docs[doc["_id"]] = dict(doc)


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}
        self.validators: dict[str, dict[str, Any]] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection(self, name))

    async def list_collection_names(self) -> list[str]:
        return list(self.collections)

    async def create_collection(self, name: str, **options: Any) -> FakeCollection:
        self.validators[name] = options["validator"]
        return self[name]

    async def command(self, command: dict[str, Any]) -> dict[str, Any]:
        if "collMod" in command:
            self.validators[command["collMod"]] = command["validator"]
        return {"ok": 1}


@pytest.fixture
def fake_db() -> FakeDB:
    db = FakeDB()
    for name in schemas.COLLECTIONS:
        db.validators[name] = schemas.validator(name)
    return db


TEST_KEYS = {
    "DXP_AGENT_KEY": "test-agent-key-not-a-secret",
    "DXP_API_KEY": "test-reviewer-key-not-a-secret",
    "DXP_SEED_KEY": "test-seed-key-not-a-secret",
}


@pytest.fixture
def keys() -> dict[str, str]:
    return dict(TEST_KEYS)


# --- Atlas -------------------------------------------------------------------------

ATLAS_SKIP_REASON = "MONGODB_URI is not set: Atlas-backed test skipped (run against the Atlas Sandbox to prove it)"


@pytest.fixture
def atlas():
    """An async context manager factory for a fresh Atlas test database."""
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        pytest.skip(ATLAS_SKIP_REASON)

    @contextlib.asynccontextmanager
    async def open_db():
        from pymongo import AsyncMongoClient

        name = f"dxp_test_a03_{uuid.uuid4().hex[:8]}"
        assert name != "dxp"
        client = AsyncMongoClient(uri, tz_aware=True)
        try:
            yield client[name]
        finally:
            await client.drop_database(name)
            await client.close()

    return open_db
