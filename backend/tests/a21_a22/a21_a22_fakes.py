"""Hand-written test doubles for A21+A22: an in-memory database and a recording gate.

No network and no Atlas: `install()` replaces `dxp.store.collection` and
`dxp.store.emit_event` for one test.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from dxp import identity
from dxp.api.models import DecisionCause, Grant, Principal, RunContext, Stamp
from pymongo.errors import DuplicateKeyError

TEAM = "team_lbdx"
OTHER_TEAM = "team_other"
CLAIM = "outcome_claim_without_results"
M1_TEXT = "Terminated trial with no posted results: describe its status; do not state outcomes"


def dec(name: str) -> str:
    """A decision ID in the stored form, `dec_<16 hex>` (A03's validators)."""
    return identity.derive("dec_", "a21_a22", name)


def rep(name: str) -> str:
    """A report ID in the stored form, `rep_<16 hex>`."""
    return identity.derive("rep_", "a21_a22", name)


def install_hex_gate(fake_gate: Any, monkeypatch: Any) -> None:
    """A01's fake gate, with each Decision given an ID the validators accept (`dec_<16 hex>`),
    derived from the kind and the request ID so a retry is a new Decision."""
    import dxp.gate

    evaluate = fake_gate.evaluate

    async def hex_ids(ctx: Any, action: Any) -> Any:
        decision = await evaluate(ctx, action)
        return decision.model_copy(update={"id": identity.derive("dec_", action.kind, ctx.request_id or "-")})

    monkeypatch.setattr(dxp.gate, "evaluate", hex_ids)


def _value(document: dict[str, Any], dotted: str) -> Any:
    value: Any = document
    for part in dotted.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, wanted in query.items():
        value = _value(document, key)
        if isinstance(wanted, dict) and "$in" in wanted:
            if value not in wanted["$in"]:
                return False
        elif value != wanted:
            return False
    return True


@dataclass
class Changed:
    matched_count: int
    modified_count: int


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return self._documents


class FakeCollection:
    """The few calls the memory code makes, with `_id` and extra unique keys enforced."""

    def __init__(self, name: str, unique: tuple[tuple[str, ...], ...] = ()) -> None:
        self.name = name
        self.unique = unique
        self.documents: list[dict[str, Any]] = []
        self.writes: list[tuple[str, Any]] = []
        self.fail_next_insert: Exception | None = None

    def find(self, query: dict[str, Any] | None = None, *args: Any, **kwargs: Any) -> FakeCursor:
        return FakeCursor([copy.deepcopy(d) for d in self.documents if _matches(d, query or {})])

    async def find_one(self, query: dict[str, Any] | None = None, *args: Any, **kwargs: Any) -> dict[str, Any] | None:
        found = await self.find(query).to_list()
        return found[0] if found else None

    async def insert_one(self, document: dict[str, Any], **kwargs: Any) -> None:
        if self.fail_next_insert is not None:
            error, self.fail_next_insert = self.fail_next_insert, None
            raise error
        for held in self.documents:
            if held["_id"] == document["_id"] or any(
                all(held.get(k) == document.get(k) for k in keys) for keys in self.unique
            ):
                raise DuplicateKeyError("duplicate key")
        self.documents.append(copy.deepcopy(document))
        self.writes.append(("insert_one", document["_id"]))

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], **kwargs: Any) -> Changed:
        for held in self.documents:
            if _matches(held, query):
                held.update(copy.deepcopy(update["$set"]))
                self.writes.append(("update_one", held["_id"]))
                return Changed(1, 1)
        return Changed(0, 0)


@dataclass
class FakeDatabase:
    collections: dict[str, FakeCollection] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)

    def collection(self, name: str) -> FakeCollection:
        self.opened.append(name)
        if name not in self.collections:
            unique = (("memory_id", "version"),) if name == "memories" else ()
            self.collections[name] = FakeCollection(name, unique)
        return self.collections[name]

    async def emit_event(self, event: str, *, session: Any = None, dedupe_key: str | None = None,
                         stamp: dict[str, Any] | None = None, **fields: Any) -> int:
        assert dedupe_key, "emit_event needs a dedupe_key"
        for seq, held in enumerate(self.events, start=1):
            if held["dedupe_key"] == dedupe_key:
                return seq
        self.events.append({"type": event, "dedupe_key": dedupe_key, "stamp": stamp, **fields})
        return len(self.events)

    @property
    def memories(self) -> list[dict[str, Any]]:
        return self.collection("memories").documents

    def memory(self, version_id: str) -> dict[str, Any]:
        return next(d for d in self.memories if d["_id"] == version_id)

    def snapshot(self, *names: str) -> dict[str, list[dict[str, Any]]]:
        return {name: copy.deepcopy(self.collections[name].documents) for name in names}


def install(monkeypatch: Any) -> FakeDatabase:
    import dxp.store

    database = FakeDatabase()
    monkeypatch.setattr(dxp.store, "collection", database.collection)
    monkeypatch.setattr(dxp.store, "emit_event", database.emit_event)
    return database


def sam() -> Principal:
    return Principal(id="sam", name="Sam", kind="person",
                     actions=["decide_report", "create_memory", "correct_memory", "revoke_memory"])


def sam_grant(team_id: str = TEAM) -> Grant:
    return Grant(id="sam@v1", grant_id="sam", version=1, principal="sam", kind="person", team_id=team_id,
                 scope={"diagnostic_ids": [], "scope_id": "scope_plasma"}, destinations=["ledger"],
                 actions=["decide_report", "create_memory", "correct_memory", "revoke_memory"], status="active")


def reviewer_ctx(*, request_id: str | None = "req_1", report_id: str | None = "rep_setup",
                 memory_id: str | None = None, origin_run_id: str | None = "run_setup") -> RunContext:
    return RunContext(
        run_id=None,
        principal=sam(),
        stamp=Stamp(kind="reviewer", initiated_by="sam", principal="sam", grant_id="sam", grant_version=1),
        grant_id="sam",
        grant_version=1,
        request_id=request_id,
        cause=DecisionCause(report_id=report_id, memory_id=memory_id, origin_run_id=origin_run_id),
    )
