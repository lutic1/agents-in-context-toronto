"""The four races from Luis's review of PR #30 (comment 6881065120), reproduced without Atlas.

An in-memory MongoDB fake with transactions: a transaction's writes become visible at once but
are undone on abort, and a transactional write to a document that another transaction owns, or
that was committed after this transaction began, raises a write conflict that `with_transaction`
retries (as Atlas does). Every operation yields to the event loop first, and hooks pause a caller
at the exact point of each probe:

1. `settle`: a settle from a release counts 0 and pauses; an admit commits; stop; the settle
   resumes. The run must stay `stopping` with its live admission.
2. `finish`: the same gap. The run must stay `running` with its live admission.
3. Start: one start computes its time and pauses before its one-run check; a second start runs
   to completion; the first resumes. Exactly one run may be running.
4. `record_progress`: an older snapshot landing last must not rewind the counts, and writes for
   one run are serialised.
"""

from __future__ import annotations

import asyncio
import copy
import itertools
from typing import Any, Self

import pytest
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, OperationFailure

import dxp.runs.admissions
import dxp.store
from dxp import runs
from dxp.api.errors import ApiError

from .conftest import SAM


class WriteConflict(OperationFailure):
    def __init__(self) -> None:
        super().__init__("WriteConflict", code=112)


def _get(doc: dict[str, Any], path: str) -> Any:
    value: Any = doc
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


_OPS = {
    "$in": lambda have, want: have in want,
    "$ne": lambda have, want: have != want,
    "$gte": lambda have, want: have is not None and have >= want,
    "$gt": lambda have, want: have is not None and have > want,
    "$lt": lambda have, want: have is not None and have < want,
    "$lte": lambda have, want: have is not None and have <= want,
}


def _cmp(have: Any, op: str, want: Any) -> bool:
    assert op in _OPS, f"fake: unsupported operator {op}"
    return _OPS[op](have, want)


def matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, want in query.items():
        if key == "$or":
            if not any(matches(doc, q) for q in want):
                return False
            continue
        have = _get(doc, key)
        if isinstance(want, dict) and want and all(k.startswith("$") for k in want):
            if not all(_cmp(have, op, arg) for op, arg in want.items()):
                return False
        elif have != want:
            return False
    return True


def _set(doc: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    for part in parts[:-1]:
        doc = doc.setdefault(part, {})
    doc[parts[-1]] = value


def apply_update(doc: dict[str, Any], update: dict[str, Any], inserting: bool = False) -> None:
    for op, fields in update.items():
        for path, value in fields.items():
            if op == "$set" or (op == "$setOnInsert" and inserting):
                _set(doc, path, copy.deepcopy(value))
            elif op == "$inc":
                _set(doc, path, (_get(doc, path) or 0) + value)
            elif op == "$max":
                have = _get(doc, path)
                _set(doc, path, value if have is None else max(have, value))
            elif op == "$push":
                _set(doc, path, [*(_get(doc, path) or []), value])
            elif op != "$setOnInsert":
                raise AssertionError(f"fake: unsupported update {op}")


class Result:
    def __init__(self, matched: int = 0, modified: int = 0, deleted: int = 0) -> None:
        self.matched_count, self.modified_count, self.deleted_count = matched, modified, deleted


class FakeSession:
    def __init__(self, mongo: FakeMongo) -> None:
        self.mongo, self.start_clock, self.undo, self.owned = mongo, 0, [], set()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    def _rollback(self) -> None:
        for coll, key, before in reversed(self.undo):
            if before is None:
                coll.docs.pop(key, None)
            else:
                coll.docs[key] = before
        self._release()

    def _release(self) -> None:
        for owned in self.owned:
            self.mongo.owners.pop(owned, None)
        self.undo, self.owned = [], set()

    async def with_transaction(self, callback: Any) -> Any:
        for _ in range(200):
            self.start_clock = self.mongo.clock
            try:
                result = await callback(self)
            except WriteConflict:
                self._rollback()
                self.mongo.conflicts += 1
                await asyncio.sleep(0.001)
                continue
            except BaseException:
                self._rollback()
                raise
            self.mongo.clock += 1
            for owned in self.owned:
                self.mongo.versions[owned] = self.mongo.clock
            self._release()
            return result
        raise AssertionError("fake: transaction never committed")


class FakeCollection:
    def __init__(self, mongo: FakeMongo, name: str) -> None:
        self.mongo, self.name, self.docs = mongo, name, {}
        self.before_find_one: Any = None
        self.in_update = 0
        self.max_in_update = 0

    async def _write(self, key: Any, session: FakeSession | None) -> None:
        owned = (self.name, key)
        if session is None:
            self.mongo.clock += 1
            self.mongo.versions[owned] = self.mongo.clock
            return
        owner = self.mongo.owners.get(owned)
        if (owner is not None and owner is not session) or self.mongo.versions.get(owned, 0) > session.start_clock:
            raise WriteConflict()
        if owned not in session.owned:
            session.owned.add(owned)
            self.mongo.owners[owned] = session
        session.undo.append((self, key, copy.deepcopy(self.docs.get(key))))

    def _find(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        return [d for d in self.docs.values() if matches(d, query)]

    async def find_one(self, query: dict[str, Any], projection: Any = None, session: Any = None) -> dict | None:
        await asyncio.sleep(0)
        found = copy.deepcopy(self._find(query)[:1])
        if self.before_find_one is not None:
            await self.before_find_one(query)  # pauses after reading, as a snapshot read would
        return found[0] if found else None

    async def aggregate(self, pipeline: list[dict[str, Any]]) -> Any:
        async def rows() -> Any:  # the read-time counts are not under test here
            for row in ():
                yield row
        return rows()

    async def count_documents(self, query: dict[str, Any], session: Any = None, limit: int = 0) -> int:
        await asyncio.sleep(0)
        n = len(self._find(query))
        return min(n, limit) if limit else n

    async def insert_one(self, doc: dict[str, Any], session: Any = None) -> Result:
        await asyncio.sleep(0)
        if doc["_id"] in self.docs:
            raise DuplicateKeyError(f"duplicate _id {doc['_id']}")
        await self._write(doc["_id"], session)
        self.docs[doc["_id"]] = copy.deepcopy(doc)
        return Result(1, 1)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], session: Any = None,
                         upsert: bool = False) -> Result:
        self.in_update += 1
        self.max_in_update = max(self.max_in_update, self.in_update)
        try:
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            found = self._find(query)
            if not found:
                if not upsert:
                    return Result()
                doc = {k: v for k, v in query.items() if not k.startswith("$")}
                await self._write(doc["_id"], session)
                apply_update(doc, update, inserting=True)
                self.docs[doc["_id"]] = doc
                return Result()
            doc = found[0]
            await self._write(doc["_id"], session)
            apply_update(doc, update)
            return Result(1, 1)
        finally:
            self.in_update -= 1

    async def find_one_and_update(self, query: dict[str, Any], update: dict[str, Any], session: Any = None,
                                  return_document: Any = ReturnDocument.BEFORE) -> dict | None:
        await asyncio.sleep(0)
        found = self._find(query)
        if not found:
            return None
        doc = found[0]
        await self._write(doc["_id"], session)
        apply_update(doc, update)
        return copy.deepcopy(doc)

    async def delete_one(self, query: dict[str, Any], session: Any = None) -> Result:
        await asyncio.sleep(0)
        found = self._find(query)
        if not found:
            return Result()
        await self._write(found[0]["_id"], session)
        del self.docs[found[0]["_id"]]
        return Result(deleted=1)


class FakeMongo:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}
        self.clock = 0
        self.versions: dict[tuple, int] = {}
        self.owners: dict[tuple, FakeSession] = {}
        self.conflicts = 0
        self.events: list[dict[str, Any]] = []

    def collection(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection(self, name))

    def get_client(self) -> FakeMongo:
        return self

    def start_session(self) -> FakeSession:
        return FakeSession(self)

    async def emit_event(self, kind: str, **fields: Any) -> int:
        self.events.append({"kind": kind, **fields})
        return len(self.events)


@pytest.fixture
def mongo(monkeypatch: pytest.MonkeyPatch) -> FakeMongo:
    fake = FakeMongo()
    monkeypatch.setattr(dxp.store, "collection", fake.collection)
    monkeypatch.setattr(dxp.store, "get_client", fake.get_client)
    monkeypatch.setattr(dxp.store, "emit_event", fake.emit_event)
    return fake


def pause_first_count(monkeypatch: pytest.MonkeyPatch) -> tuple[asyncio.Event, asyncio.Event]:
    """The first `count_admitted` call returns its count only after `resume` is set; `paused` is
    set once it has counted."""
    paused, resume = asyncio.Event(), asyncio.Event()
    original = dxp.runs.admissions.count_admitted
    calls = itertools.count()

    async def count_admitted(run_id: str, session: Any = None) -> int:
        n = await original(run_id, session=session)
        if next(calls) == 0:
            paused.set()
            await resume.wait()
        return n

    monkeypatch.setattr(dxp.runs.admissions, "count_admitted", count_admitted)
    return paused, resume


async def live(mongo: FakeMongo, run_id: str) -> int:
    return await mongo.collection("admissions").count_documents({"run_id": run_id, "status": "admitted"})


# --- 1. settle ----------------------------------------------------------------------------------


async def test_1_settle_never_stops_a_run_with_a_live_admission(mongo, authority, monkeypatch) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    first = await runs.admit(run.id, "a|search_source|-|-")
    paused, resume = pause_first_count(monkeypatch)

    released = asyncio.create_task(runs.release(first.id))  # its settle counts 0, then pauses
    await paused.wait()
    assert await runs.admit(run.id, "b|file_proposal|-|-") is not None  # an admit commits
    await runs.stop(run.id)  # running -> stopping; stop's own settle sees the live admission
    resume.set()
    await released

    stored = await mongo.collection("runs").find_one({"_id": run.id})
    assert stored["status"] == "stopping" and await live(mongo, run.id) == 1  # was: stopped with 1 live


# --- 2. finish ----------------------------------------------------------------------------------


async def test_2_finish_never_ends_a_run_with_a_live_admission(mongo, authority, monkeypatch) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    first = await runs.admit(run.id, "a|search_source|-|-")
    await runs.release(first.id)  # running: its settle changes nothing
    paused, resume = pause_first_count(monkeypatch)

    finishing = asyncio.create_task(runs.finish(run.id))  # counts 0, then pauses
    await paused.wait()
    assert await runs.admit(run.id, "b|file_proposal|-|-") is not None
    resume.set()
    await finishing

    stored = await mongo.collection("runs").find_one({"_id": run.id})
    assert stored["status"] == "running" and await live(mongo, run.id) == 1  # was: done with 1 live


async def test_settle_and_finish_still_end_an_idle_run(mongo, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    adm = await runs.admit(run.id, "a|search_source|-|-")
    await runs.stop(run.id)
    assert (await mongo.collection("runs").find_one({"_id": run.id}))["status"] == "stopping"
    await runs.release(adm.id)
    assert (await mongo.collection("runs").find_one({"_id": run.id}))["status"] == "stopped"

    other = await runs.start(SAM, "lbdx", "discover")
    await runs.finish(other.id)
    assert (await mongo.collection("runs").find_one({"_id": other.id}))["status"] == "done"
    assert [e["status"] for e in mongo.events] == ["running", "stopping", "stopped", "running", "done"]


# --- 3. start -----------------------------------------------------------------------------------


async def test_3_two_concurrent_starts_leave_one_running_run(mongo, authority) -> None:
    runs_coll = mongo.collection("runs")
    first_checking, release_first = asyncio.Event(), asyncio.Event()
    calls = itertools.count()

    async def before_find_one(query: dict[str, Any]) -> None:
        # The first start's one-run check waits (its time is already taken) until the second
        # start has finished, so the first lands last with the earlier started_at.
        if "progress_at" in query and next(calls) == 0:
            first_checking.set()
            await release_first.wait()

    runs_coll.before_find_one = before_find_one
    first = asyncio.create_task(runs.start(SAM, "lbdx", "discover"))
    await first_checking.wait()
    await asyncio.sleep(0.003)  # the second start's clock is later than the first's
    second = await runs.start(SAM, "lbdx", "discover")
    release_first.set()
    outcome = await asyncio.gather(first, return_exceptions=True)

    assert isinstance(outcome[0], ApiError) and outcome[0].status_code == 409
    running = [d["_id"] for d in runs_coll.docs.values() if d["status"] == "running"]
    assert running == [second.id]  # was: 2 running runs
    assert mongo.conflicts >= 1  # serialised on the server lock, not on a client clock


async def test_3_many_concurrent_starts_leave_one_run(mongo, authority) -> None:
    results = await asyncio.gather(*(runs.start(SAM, "lbdx", "discover") for _ in range(6)), return_exceptions=True)
    started = [r for r in results if not isinstance(r, Exception)]
    refused = [r for r in results if isinstance(r, ApiError) and r.status_code == 409]
    assert len(started) == 1 and len(refused) == 5
    assert len(mongo.collection("runs").docs) == 1  # nothing inserted and withdrawn


# --- 4. record_progress --------------------------------------------------------------------------


async def test_4_an_older_snapshot_landing_last_never_rewinds_counts(mongo, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    assert await runs.record_progress(run.id, counts={"total": 9, "done": 5}, active_items=[], failure_lines=[])
    assert await runs.record_progress(run.id, counts={"total": 9, "done": 3}, active_items=[], failure_lines=[])
    stored = await mongo.collection("runs").find_one({"_id": run.id})
    assert stored["counts"]["done"] == 5 and stored["counts"]["total"] == 9  # was: rewound to 3


async def test_4_concurrent_snapshots_are_serialised_per_run(mongo, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    runs_coll = mongo.collection("runs")
    runs_coll.max_in_update = 0
    snapshots = [
        ({"done": n}, [{"source_ref": f"clinicaltrials.gov:NCT0000000{n}", "step": "draft"}]) for n in range(1, 7)
    ]
    results = await asyncio.gather(*(
        runs.record_progress(run.id, counts=counts, active_items=active, failure_lines=[])
        for counts, active in snapshots
    ))
    assert all(results)
    assert runs_coll.max_in_update == 1  # one write at a time for the run
    stored = await runs_coll.find_one({"_id": run.id})
    assert stored["counts"]["done"] == 6 and len(stored["active"]) == 1
