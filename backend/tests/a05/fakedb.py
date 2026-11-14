"""A small in-memory stand-in for the async pymongo calls A05 makes (tests without Atlas).

Supports equality filters on dotted keys (a None value also matches a missing key), and the
update operators $set, $setOnInsert, $addToSet and $inc. Unique `_id` raises DuplicateKeyError.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

from pymongo.errors import DuplicateKeyError

_MISSING = object()


def _get(doc: dict[str, Any], dotted: str) -> Any:
    cur: Any = doc
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def _set(doc: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = doc
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def matches(doc: dict[str, Any], flt: dict[str, Any]) -> bool:
    for key, want in flt.items():
        got = _get(doc, key)
        if want is None:
            if got is not _MISSING and got is not None:
                return False
        elif got is _MISSING or got != want:
            return False
    return True


class Cursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def sort(self, key: str, direction: int = 1) -> Cursor:
        self._docs.sort(key=lambda d: d.get(key), reverse=direction < 0)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return self._docs[:length] if length else list(self._docs)

    def __aiter__(self):
        self._it = iter(self._docs)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration from None


class Collection:
    def __init__(self, name: str) -> None:
        self.name = name
        self.docs: dict[Any, dict[str, Any]] = {}
        self.writes: list[tuple[str, Any]] = []

    async def find_one(self, flt: dict[str, Any] | None = None, projection: Any = None, **_: Any) -> dict[str, Any] | None:
        for doc in self.docs.values():
            if matches(doc, flt or {}):
                return copy.deepcopy(doc)
        return None

    def find(self, flt: dict[str, Any] | None = None, projection: Any = None, **_: Any) -> Cursor:
        return Cursor([copy.deepcopy(d) for d in self.docs.values() if matches(d, flt or {})])

    async def insert_one(self, doc: dict[str, Any], **_: Any) -> SimpleNamespace:
        if doc["_id"] in self.docs:
            raise DuplicateKeyError(f"duplicate _id {doc['_id']}")
        self.docs[doc["_id"]] = copy.deepcopy(doc)
        self.writes.append(("insert", doc["_id"]))
        return SimpleNamespace(inserted_id=doc["_id"])

    async def update_one(self, flt: dict[str, Any], update: dict[str, Any], upsert: bool = False, **_: Any) -> SimpleNamespace:
        for doc in self.docs.values():
            if matches(doc, flt):
                self._apply(doc, update, inserting=False)
                self.writes.append(("update", doc["_id"]))
                return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)
        if upsert:
            doc = {k: v for k, v in flt.items() if "." not in k and not isinstance(v, dict)}
            self._apply(doc, update, inserting=True)
            if doc["_id"] in self.docs:
                raise DuplicateKeyError(f"duplicate _id {doc['_id']}")
            self.docs[doc["_id"]] = doc
            self.writes.append(("upsert", doc["_id"]))
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=doc["_id"])
        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=None)

    @staticmethod
    def _apply(doc: dict[str, Any], update: dict[str, Any], *, inserting: bool) -> None:
        for op, fields in update.items():
            for key, value in fields.items():
                if op == "$set" or (op == "$setOnInsert" and inserting):
                    _set(doc, key, copy.deepcopy(value))
                elif op == "$addToSet":
                    current = _get(doc, key)
                    current = [] if current is _MISSING else current
                    if value not in current:
                        current = [*current, value]
                    _set(doc, key, current)
                elif op == "$inc":
                    current = _get(doc, key)
                    _set(doc, key, (0 if current is _MISSING else current) + value)
                elif op != "$setOnInsert":
                    raise NotImplementedError(op)


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, Collection] = {}

    def __getitem__(self, name: str) -> Collection:
        return self.collections.setdefault(name, Collection(name))
