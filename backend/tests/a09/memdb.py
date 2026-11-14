"""An in-memory stand-in for the few async collection calls `dxp.actions.records` makes
(A09 tests only): insert_one with DuplicateKeyError, find_one, update_one with `$set`,
and find(...).sort(...).limit(...).to_list(...). Filters are equality on dotted paths and
`$in`. Each call yields to the event loop first, so concurrent tasks interleave; each
update is applied without a further yield, so a conditional update is atomic, as in Atlas.
"""

from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from typing import Any

from pymongo.errors import DuplicateKeyError

_ABSENT = object()


def _value(doc: dict[str, Any], path: str) -> Any:
    current: Any = doc
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return _ABSENT
        current = current[part]
    return current


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for path, expected in query.items():
        actual = _value(doc, path)
        if isinstance(expected, dict) and "$in" in expected:
            if actual is _ABSENT or actual not in expected["$in"]:
                return False
        elif actual is _ABSENT:
            if expected is not None:
                return False
        elif actual != expected:
            return False
    return True


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int


class Cursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs

    def sort(self, key: str, direction: int = 1) -> "Cursor":
        self.docs.sort(key=lambda d: _value(d, key), reverse=direction < 0)
        return self

    def limit(self, n: int) -> "Cursor":
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        await asyncio.sleep(0)
        return [copy.deepcopy(d) for d in (self.docs if length is None else self.docs[:length])]


class Collection:
    def __init__(self) -> None:
        self.docs: dict[Any, dict[str, Any]] = {}

    async def insert_one(self, doc: dict[str, Any], **_: Any) -> None:
        await asyncio.sleep(0)
        if doc["_id"] in self.docs:
            raise DuplicateKeyError(f"duplicate _id {doc['_id']}")
        self.docs[doc["_id"]] = copy.deepcopy(doc)

    async def find_one(self, query: dict[str, Any], *_: Any, **__: Any) -> dict[str, Any] | None:
        await asyncio.sleep(0)
        for doc in self.docs.values():
            if _matches(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query: dict[str, Any] | None = None, *_: Any, **__: Any) -> Cursor:
        return Cursor([d for d in self.docs.values() if _matches(d, query or {})])

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], **_: Any) -> UpdateResult:
        await asyncio.sleep(0)
        for doc in self.docs.values():
            if _matches(doc, query):
                for path, value in update.get("$set", {}).items():
                    target = doc
                    *parents, last = path.split(".")
                    for part in parents:
                        target = target.setdefault(part, {})
                    target[last] = copy.deepcopy(value)
                return UpdateResult(1, 1)
        return UpdateResult(0, 0)


class MemDB:
    def __init__(self) -> None:
        self.collections: dict[str, Collection] = {}
        self.events: list[dict[str, Any]] = []

    def __getitem__(self, name: str) -> Collection:
        return self.collections.setdefault(name, Collection())

    async def emit_event(self, event: dict[str, Any]) -> int:
        if any(e["dedupe_key"] == event["dedupe_key"] for e in self.events):
            return next(i for i, e in enumerate(self.events, 1) if e["dedupe_key"] == event["dedupe_key"])
        self.events.append(copy.deepcopy(event))
        return len(self.events)
