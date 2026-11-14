"""An in-memory stand-in for the subset of the async PyMongo API A24 uses (A24 tests only).

It is not MongoDB: it exists so A24's logic (claims, conditional updates, one transaction,
recovery) can be exercised without an Atlas URI. A transaction snapshots every collection
and restores the snapshot if the callback raises, so "all of it or none of it" is observable.
The Atlas-backed tests in test_a24_atlas.py run the same flows on the real sandbox.
"""

from __future__ import annotations

import copy
from typing import Any

from pymongo.errors import DuplicateKeyError

_MISSING = object()


def _get(doc: Any, path: str) -> Any:
    cur = doc
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


def _match_value(value: Any, cond: Any) -> bool:
    if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
        for op, arg in cond.items():
            v = None if value is _MISSING else value
            if op == "$in":
                if isinstance(v, list):
                    if not any(x in arg for x in v):
                        return False
                elif v not in arg:
                    return False
            elif op == "$nin":
                if v in arg:
                    return False
            elif op == "$ne":
                if v == arg:
                    return False
            elif op == "$exists":
                if (value is not _MISSING) != bool(arg):
                    return False
            elif op == "$lt":
                if v is None or not v < arg:
                    return False
            elif op == "$lte":
                if v is None or not v <= arg:
                    return False
            elif op == "$gt":
                if v is None or not v > arg:
                    return False
            elif op == "$gte":
                if v is None or not v >= arg:
                    return False
            else:
                raise NotImplementedError(op)
        return True
    if cond is None:
        return value is _MISSING or value is None
    if value is _MISSING:
        return False
    if isinstance(value, list) and not isinstance(cond, list):
        return cond in value
    return value == cond


def matches(doc: dict[str, Any], flt: dict[str, Any]) -> bool:
    for key, cond in (flt or {}).items():
        if key == "$or":
            if not any(matches(doc, sub) for sub in cond):
                return False
            continue
        if not _match_value(_get(doc, key), cond):
            return False
    return True


def _set(doc: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur = doc
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _unset(doc: dict[str, Any], path: str) -> None:
    parts = path.split(".")
    cur = doc
    for part in parts[:-1]:
        cur = cur.get(part)
        if not isinstance(cur, dict):
            return
    cur.pop(parts[-1], None)


class Result:
    def __init__(self, matched: int = 0, modified: int = 0, upserted_id: Any = None) -> None:
        self.matched_count = matched
        self.modified_count = modified
        self.upserted_id = upserted_id


class Cursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def sort(self, key: Any, direction: int | None = None) -> Cursor:
        keys = [(key, direction or 1)] if isinstance(key, str) else list(key)
        for k, d in reversed(keys):
            self._docs.sort(key=lambda doc, k=k: _sort_key(_get(doc, k)), reverse=d < 0)
        return self

    def limit(self, n: int) -> Cursor:
        self._docs = self._docs[:n] if n else self._docs
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return list(self._docs)

    def __aiter__(self) -> Cursor:
        self._iter = iter(self._docs)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


def _sort_key(value: Any) -> tuple[int, Any]:
    if value is _MISSING or value is None:
        return (0, 0)
    return (1, value)


class Collection:
    def __init__(self, db: FakeDB, name: str) -> None:
        self.db = db
        self.name = name

    @property
    def docs(self) -> dict[Any, dict[str, Any]]:
        return self.db.data.setdefault(self.name, {})

    def _find(self, flt: dict[str, Any] | None) -> list[dict[str, Any]]:
        return [d for d in self.docs.values() if matches(d, flt or {})]

    async def find_one(self, flt: dict[str, Any] | None = None, projection: Any = None, *, sort: Any = None,
                       session: Any = None) -> dict[str, Any] | None:
        found = self._find(flt)
        if sort:
            found = Cursor(found).sort(sort)._docs
        return copy.deepcopy(found[0]) if found else None

    def find(self, flt: dict[str, Any] | None = None, projection: Any = None, *, sort: Any = None,
             session: Any = None) -> Cursor:
        cursor = Cursor([copy.deepcopy(d) for d in self._find(flt)])
        return cursor.sort(sort) if sort else cursor

    async def count_documents(self, flt: dict[str, Any], session: Any = None) -> int:
        return len(self._find(flt))

    async def insert_one(self, doc: dict[str, Any], session: Any = None) -> Result:
        if doc["_id"] in self.docs:
            raise DuplicateKeyError(f"E11000 duplicate key {self.name} {doc['_id']}")
        self.docs[doc["_id"]] = copy.deepcopy(doc)
        self.db.writes.append((self.name, "insert", doc["_id"]))
        return Result(1, 1)

    async def update_one(self, flt: dict[str, Any], update: dict[str, Any], *, upsert: bool = False,
                         session: Any = None, **_: Any) -> Result:
        found = self._find(flt)
        inserted = False
        if not found:
            if not upsert:
                return Result(0, 0)
            doc = {k: copy.deepcopy(v) for k, v in flt.items() if not k.startswith("$") and not isinstance(v, dict)}
            self.docs[doc["_id"]] = doc
            found, inserted = [doc], True
        doc = found[0]
        before = copy.deepcopy(doc)
        for op, fields in update.items():
            for path, value in fields.items():
                if op == "$setOnInsert":
                    if inserted:
                        _set(doc, path, copy.deepcopy(value))
                elif op == "$max":
                    current = _get(doc, path)
                    if current is _MISSING or current is None or value > current:
                        _set(doc, path, value)
                elif op == "$set":
                    _set(doc, path, copy.deepcopy(value))
                elif op == "$inc":
                    current = _get(doc, path)
                    _set(doc, path, (0 if current is _MISSING else current) + value)
                elif op == "$unset":
                    _unset(doc, path)
                elif op == "$push":
                    current = _get(doc, path)
                    _set(doc, path, ([] if current is _MISSING else current) + [value])
                else:
                    raise NotImplementedError(op)
        modified = int(doc != before) and not inserted
        if modified:
            self.db.writes.append((self.name, "update", doc["_id"]))
        return Result(0 if inserted else 1, modified, doc["_id"] if inserted else None)

    async def find_one_and_update(self, flt: dict[str, Any], update: dict[str, Any], *, upsert: bool = False,
                                  return_document: Any = False, projection: Any = None, sort: Any = None,
                                  session: Any = None) -> dict[str, Any] | None:
        candidates = self._find(flt)
        if sort and candidates:
            candidates = Cursor(candidates).sort(sort)._docs
        before = copy.deepcopy(candidates[0]) if candidates else None
        if before is None and not upsert:
            return None
        target = {"_id": before["_id"]} if before is not None else flt
        await self.update_one(target, update, upsert=upsert, session=session)
        after = self.docs.get(before["_id"] if before is not None else flt.get("_id"))
        return copy.deepcopy(after if return_document else before)


class FakeDB:
    def __init__(self) -> None:
        self.data: dict[str, dict[Any, dict[str, Any]]] = {}
        self.writes: list[tuple[str, str, Any]] = []
        self.transactions = 0

    def __getitem__(self, name: str) -> Collection:
        return Collection(self, name)

    def all(self, name: str) -> list[dict[str, Any]]:
        return [copy.deepcopy(d) for d in self.data.get(name, {}).values()]


class FakeSession:
    def __init__(self, db: FakeDB) -> None:
        self.db = db

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def with_transaction(self, callback: Any) -> Any:
        snapshot = copy.deepcopy(self.db.data)
        self.db.transactions += 1
        try:
            return await callback(self)
        except BaseException:
            self.db.data = snapshot
            raise


class FakeClient:
    def __init__(self, db: FakeDB) -> None:
        self.db = db

    def start_session(self) -> FakeSession:
        return FakeSession(self.db)
