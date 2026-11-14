"""A small in-memory stand-in for the async PyMongo calls the pipeline makes (A10 tests only).

Supports: find_one (with an ignored projection), find (async iteration), update_one with
$set, $inc, $push and $setOnInsert (and upsert), insert_one and count_documents; filters on
equality (dotted paths), $in and $ne.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

_MISSING = object()


def _get(doc: dict[str, Any], path: str) -> Any:
    cur: Any = doc
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _MISSING
        cur = cur[part]
    return cur


def _set(doc: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur = doc
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


def matches(doc: dict[str, Any], flt: dict[str, Any]) -> bool:
    for key, cond in flt.items():
        value = _get(doc, key)
        if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
            for op, arg in cond.items():
                if op == "$in" and value not in arg:
                    return False
                if op == "$ne" and value == arg:
                    return False
        elif value is _MISSING or value != cond:
            return False
    return True


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int
    upserted_id: Any = None


class FakeCollection:
    def __init__(self) -> None:
        self.docs: dict[Any, dict[str, Any]] = {}

    async def find_one(self, flt: dict[str, Any], projection: Any = None, **_: Any) -> dict[str, Any] | None:
        for doc in self.docs.values():
            if matches(doc, flt):
                return copy.deepcopy(doc)
        return None

    def find(self, flt: dict[str, Any] | None = None, **_: Any):
        found = [copy.deepcopy(d) for d in self.docs.values() if matches(d, flt or {})]

        async def gen():
            for d in found:
                yield d

        return gen()

    async def insert_one(self, doc: dict[str, Any], **_: Any) -> None:
        if doc["_id"] in self.docs:
            raise KeyError(f"duplicate {doc['_id']}")
        self.docs[doc["_id"]] = copy.deepcopy(doc)

    async def update_one(self, flt: dict[str, Any], update: dict[str, Any], upsert: bool = False, **_: Any) -> UpdateResult:
        for doc in self.docs.values():
            if matches(doc, flt):
                self._apply(doc, update, inserting=False)
                return UpdateResult(1, 1)
        if upsert:
            doc = {k: v for k, v in flt.items() if not isinstance(v, dict)}
            self._apply(doc, update, inserting=True)
            self.docs[doc["_id"]] = doc
            return UpdateResult(0, 0, doc["_id"])
        return UpdateResult(0, 0)

    @staticmethod
    def _apply(doc: dict[str, Any], update: dict[str, Any], inserting: bool) -> None:
        for path, value in (update.get("$set") or {}).items():
            _set(doc, path, copy.deepcopy(value))
        if inserting:
            for path, value in (update.get("$setOnInsert") or {}).items():
                _set(doc, path, copy.deepcopy(value))
        for path, value in (update.get("$inc") or {}).items():
            current = _get(doc, path)
            _set(doc, path, (0 if current is _MISSING else current) + value)
        for path, value in (update.get("$push") or {}).items():
            current = _get(doc, path)
            _set(doc, path, ([] if current is _MISSING else current) + [copy.deepcopy(value)])

    async def count_documents(self, flt: dict[str, Any], **_: Any) -> int:
        return sum(1 for d in self.docs.values() if matches(d, flt))


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())
