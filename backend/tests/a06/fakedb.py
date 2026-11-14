"""A small in-memory stand-in for the async PyMongo collection API (tests only).

It covers what the gate and the ledger use: ``insert_one`` (with
``DuplicateKeyError``), ``find_one``, ``find`` (async iteration), ``update_one``
(``$set``, ``$setOnInsert``, ``$push``, ``$inc``, ``$addToSet``, ``$unset``,
``upsert``) and ``count_documents``, with the filter operators ``$ne``,
``$in``, ``$nin``, ``$exists``, ``$gt``, ``$gte``, ``$lt`` and ``$lte`` on
dotted paths. Every call yields to the event loop first, so concurrent tasks
interleave the way they would against Atlas.
"""

from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from typing import Any

from pymongo.errors import DuplicateKeyError

_MISSING = object()


def _get_path(doc: Any, path: str) -> Any:
    cur = doc
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


def _set_path(doc: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    cur = doc
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _unset_path(doc: dict, path: str) -> None:
    parts = path.split(".")
    cur = doc
    for part in parts[:-1]:
        cur = cur.get(part)
        if not isinstance(cur, dict):
            return
    cur.pop(parts[-1], None)


def _eq(actual: Any, expected: Any) -> bool:
    if actual is _MISSING:
        return expected is None
    if isinstance(actual, list) and not isinstance(expected, list):
        return expected in actual
    return actual == expected


def _match_value(actual: Any, cond: Any) -> bool:
    if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
        for op, arg in cond.items():
            if op == "$ne" and _eq(actual, arg):
                return False
            if op == "$eq" and not _eq(actual, arg):
                return False
            if op == "$in" and not any(_eq(actual, a) for a in arg):
                return False
            if op == "$nin" and any(_eq(actual, a) for a in arg):
                return False
            if op == "$exists" and (actual is not _MISSING) != bool(arg):
                return False
            if op in ("$gt", "$gte", "$lt", "$lte"):
                if actual is _MISSING or actual is None:
                    return False
                if op == "$gt" and not actual > arg:
                    return False
                if op == "$gte" and not actual >= arg:
                    return False
                if op == "$lt" and not actual < arg:
                    return False
                if op == "$lte" and not actual <= arg:
                    return False
        return True
    return _eq(actual, cond)


def matches(doc: dict, flt: dict) -> bool:
    return all(_match_value(_get_path(doc, k), v) for k, v in (flt or {}).items())


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int
    upserted_id: Any = None


@dataclass
class InsertResult:
    inserted_id: Any


class FakeCursor:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def sort(self, key: str, direction: int = 1) -> "FakeCursor":
        self._docs.sort(key=lambda d: (_get_path(d, key) is _MISSING, _get_path(d, key)), reverse=direction < 0)
        return self

    def limit(self, n: int) -> "FakeCursor":
        self._docs = self._docs[:n] if n else self._docs
        return self

    def __aiter__(self):
        self._it = iter(self._docs)
        return self

    async def __anext__(self) -> dict:
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration

    async def to_list(self, length: int | None = None) -> list[dict]:
        return list(self._docs if length is None else self._docs[:length])


class FakeWriteError(Exception):
    """A document the collection's validator rejects (Atlas raises WriteError, code 121)."""


class FakeCollection:
    def __init__(self, name: str, check: Any = None):
        self.name = name
        self.docs: dict[Any, dict] = {}
        self.unique: list[tuple[str, ...]] = []
        self.check = check  # doc -> list of validator errors, or None

    def _validate(self, doc: dict) -> None:
        if self.check is not None:
            problems = self.check(doc)
            if problems:
                raise FakeWriteError(f"{self.name} {doc.get('_id')}: {problems}")

    def _violates_unique(self, doc: dict, skip_id: Any = _MISSING) -> bool:
        for keys in self.unique:
            vals = tuple(_get_path(doc, k) for k in keys)
            for other_id, other in self.docs.items():
                if other_id == skip_id:
                    continue
                if tuple(_get_path(other, k) for k in keys) == vals:
                    return True
        return False

    async def insert_one(self, doc: dict, session: Any = None) -> InsertResult:
        await asyncio.sleep(0)
        if doc["_id"] in self.docs or self._violates_unique(doc):
            raise DuplicateKeyError(f"E11000 duplicate key {self.name} {doc['_id']}")
        self._validate(doc)
        self.docs[doc["_id"]] = copy.deepcopy(doc)
        return InsertResult(doc["_id"])

    async def find_one(self, flt: dict | None = None, session: Any = None, **_: Any) -> dict | None:
        await asyncio.sleep(0)
        for d in self.docs.values():
            if matches(d, flt or {}):
                return copy.deepcopy(d)
        return None

    def find(self, flt: dict | None = None, session: Any = None, **_: Any) -> FakeCursor:
        return FakeCursor([copy.deepcopy(d) for d in self.docs.values() if matches(d, flt or {})])

    async def count_documents(self, flt: dict | None = None, session: Any = None) -> int:
        await asyncio.sleep(0)
        return sum(1 for d in self.docs.values() if matches(d, flt or {}))

    def _apply(self, doc: dict, update: dict, inserting: bool) -> None:
        for op, fields in update.items():
            for path, value in fields.items():
                if op == "$set":
                    _set_path(doc, path, copy.deepcopy(value))
                elif op == "$setOnInsert":
                    if inserting:
                        _set_path(doc, path, copy.deepcopy(value))
                elif op == "$unset":
                    _unset_path(doc, path)
                elif op == "$inc":
                    cur = _get_path(doc, path)
                    _set_path(doc, path, (0 if cur is _MISSING else cur) + value)
                elif op == "$push":
                    cur = _get_path(doc, path)
                    cur = [] if cur is _MISSING else list(cur)
                    cur.append(copy.deepcopy(value))
                    _set_path(doc, path, cur)
                elif op == "$addToSet":
                    cur = _get_path(doc, path)
                    cur = [] if cur is _MISSING else list(cur)
                    if value not in cur:
                        cur.append(copy.deepcopy(value))
                    _set_path(doc, path, cur)
                else:
                    raise NotImplementedError(op)

    async def update_one(self, flt: dict, update: dict, upsert: bool = False, session: Any = None) -> UpdateResult:
        await asyncio.sleep(0)
        for _id, d in self.docs.items():
            if matches(d, flt):
                new = copy.deepcopy(d)
                self._apply(new, update, inserting=False)
                if self._violates_unique(new, skip_id=_id):
                    raise DuplicateKeyError(f"E11000 duplicate key {self.name}")
                self._validate(new)
                changed = new != d
                self.docs[_id] = new
                return UpdateResult(1, 1 if changed else 0)
        if not upsert:
            return UpdateResult(0, 0)
        new = {k: copy.deepcopy(v) for k, v in flt.items() if not k.startswith("$") and not isinstance(v, dict)}
        self._apply(new, update, inserting=True)
        if new.get("_id") in self.docs or self._violates_unique(new):
            raise DuplicateKeyError(f"E11000 duplicate key {self.name}")
        self._validate(new)
        self.docs[new["_id"]] = new
        return UpdateResult(0, 0, new["_id"])

    async def update_many(self, flt: dict, update: dict, session: Any = None) -> UpdateResult:
        await asyncio.sleep(0)
        n = 0
        for _id, d in list(self.docs.items()):
            if matches(d, flt):
                new = copy.deepcopy(d)
                self._apply(new, update, inserting=False)
                self._validate(new)
                self.docs[_id] = new
                n += 1
        return UpdateResult(n, n)


class FakeDB:
    """``validators`` maps a collection name to a checker (doc -> errors), applied on every write,
    as Atlas applies A03's ``$jsonSchema`` validators with ``validationAction: error``."""

    def __init__(self, validators: dict[str, Any] | None = None) -> None:
        self.collections: dict[str, FakeCollection] = {}
        self.validators = validators or {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection(name, self.validators.get(name))
        return self.collections[name]

    def snapshot(self) -> dict[str, dict]:
        return {n: copy.deepcopy(c.docs) for n, c in self.collections.items()}
