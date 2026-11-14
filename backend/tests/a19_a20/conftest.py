"""Fixtures for A19+A20's own tests: an in-memory stand-in for the store, so no test
here opens a connection, and a recorder for store.emit_event."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pymongo.errors import DuplicateKeyError


def _get(doc: Any, path: str) -> Any:
    for part in path.split("."):
        if isinstance(doc, list):
            doc = [d.get(part) for d in doc if isinstance(d, dict) and part in d]
            continue
        if not isinstance(doc, dict) or part not in doc:
            return None
        doc = doc[part]
    return doc


def _matches(doc: dict, query: dict) -> bool:
    for key, want in query.items():
        if key == "$text":
            continue
        if key == "$and":
            if not all(_matches(doc, q) for q in want):
                return False
            continue
        have = _get(doc, key)
        if isinstance(want, dict) and any(k.startswith("$") for k in want):
            for op, value in want.items():
                if op == "$in" and not (have in value or (isinstance(have, list) and set(have) & set(value))):
                    return False
                if op == "$ne" and (have == value or (isinstance(have, list) and value in have)):
                    return False
                if op == "$exists" and (have is not None) != value:
                    return False
                if op == "$type" and not isinstance(have, str):
                    return False
                if op == "$eq" and not (have == value or (isinstance(have, list) and value in have)):
                    return False
        elif not (have == want or (isinstance(have, list) and want in have)):
            return False
    return True


class Cursor:
    def __init__(self, docs):
        self.docs = [copy.deepcopy(d) for d in docs]

    def sort(self, spec, direction=None):
        if isinstance(spec, str):
            spec = [(spec, direction or 1)]
        for key, order in reversed(spec):
            reverse = isinstance(order, dict) or order == -1
            self.docs.sort(key=lambda d: (d.get(key) is None, d.get(key)), reverse=reverse)
        return self

    def limit(self, n):
        self.docs = self.docs[:n] if n else self.docs
        return self

    async def to_list(self, length=None):
        return self.docs if length is None else self.docs[:length]

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for doc in self.docs:
            yield doc


class Result:
    def __init__(self, matched=0):
        self.matched_count = matched
        self.modified_count = matched


class Collection:
    def __init__(self, name):
        self.name = name
        self.docs: list[dict] = []
        self.pipelines: list[list[dict]] = []
        self.text_queries: list[dict] = []
        self.on_aggregate = None  # fn(pipeline) -> docs, or raises
        self.on_text = None       # fn(query) -> docs, or raises

    def add(self, *docs):
        self.docs.extend(copy.deepcopy(d) for d in docs)
        return self

    async def find_one(self, query=None, projection=None, **_):
        for doc in self.docs:
            if _matches(doc, query or {}):
                return copy.deepcopy(doc)
        return None

    def find(self, query=None, projection=None, **_):
        query = query or {}
        if "$text" in query:
            self.text_queries.append(query)
            if self.on_text is None:
                raise RuntimeError("no text index")
            return Cursor(d for d in self.on_text(query) if _matches(d, query))
        return Cursor(d for d in self.docs if _matches(d, query))

    async def insert_one(self, doc, **_):
        if any(d.get("_id") == doc.get("_id") for d in self.docs):
            raise DuplicateKeyError("duplicate _id")
        self.docs.append(copy.deepcopy(doc))
        return Result(1)

    async def update_one(self, query, update, **_):
        for doc in self.docs:
            if _matches(doc, query):
                for key, value in (update.get("$set") or {}).items():
                    doc[key] = copy.deepcopy(value)
                for key, value in (update.get("$push") or {}).items():
                    doc.setdefault(key, []).append(copy.deepcopy(value))
                return Result(1)
        return Result(0)

    async def aggregate(self, pipeline, **_):
        self.pipelines.append(pipeline)
        if self.on_aggregate is None:
            raise RuntimeError("no search index")
        return Cursor(self.on_aggregate(pipeline))


class Database:
    def __init__(self):
        self.collections: dict[str, Collection] = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, Collection(name))


@pytest.fixture
def mongo(monkeypatch):
    """store.db(), store.get_db() and store.collection() answer from memory;
    store.emit_event records into mongo.events."""
    from dxp import store

    database = Database()
    database.events = []

    async def emit_event(event, **fields):
        record = {**event, **fields} if isinstance(event, dict) else {"type": event, **fields}
        if not record.get("dedupe_key"):
            raise ValueError("emit_event needs a dedupe_key (AD-10).")
        if not any(e["dedupe_key"] == record["dedupe_key"] for e in database.events):
            database.events.append(record)
        return len(database.events)

    monkeypatch.setattr(store, "db", lambda: database)
    monkeypatch.setattr(store, "get_db", lambda: database)
    monkeypatch.setattr(store, "collection", lambda name: database[name])
    monkeypatch.setattr(store, "emit_event", emit_event)
    return database
