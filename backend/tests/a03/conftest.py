"""A03 test setup.

* `FakeDB`: a tiny in-memory async database that enforces each collection's
  `$jsonSchema` on insert (not `$expr`), for tests that need no Atlas.
* Atlas tests use A01's session `db` fixture (`tests/conftest.py`): a fresh
  `dxp_test_<hex>` database with `store.ensure_indexes()` applied, skipped with
  its stated reason when `MONGODB_URI` is unset.
"""

from __future__ import annotations

from typing import Any

import pytest

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

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        doc = await self.find_one(query)
        if doc is None:
            return
        doc.update(update["$set"])
        validator = self.db.validators.get(self.name)
        if validator is not None:
            problems = jsonschema_lite.validate(validator, doc)
            if problems:
                raise WriteError("Document failed validation: " + "; ".join(problems), 121)
        self.docs[doc["_id"]] = doc

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
