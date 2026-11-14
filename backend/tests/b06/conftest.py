"""B06 test setup: an in-memory database, a gate that records its action, and a fake ElevenLabs.

Nothing here reaches ElevenLabs, Atlas or the gate for real, and no real key is read: the
session's fake `ELEVENLABS_API_KEY` comes from tests/conftest.py.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from pymongo.errors import DuplicateKeyError

from dxp.api import models as m
from dxp.briefing import audio

SCRIPT = (
    "New trial signal worth investigating: NCT04712877, recruiting, no results posted. "
    "It extends one related trial; evidence gap: ctDNA against tumour NGS."
)
SCRIPT_HASH = "h" * 16
REPORT_ID = "rep_0123456789abcdef"
FAKE_KEY = "test-elevenlabs-key"


# --- an in-memory database --------------------------------------------------------------


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, want in query.items():
        have: Any = doc
        for part in key.split("."):
            have = have.get(part) if isinstance(have, dict) else None
        if isinstance(want, dict) and any(k.startswith("$") for k in want):
            if "$in" in want and have not in want["$in"]:
                return False
            if "$lt" in want and not (have is not None and have < want["$lt"]):
                return False
        elif have != want:
            return False
    return True


class FakeCollection:
    def __init__(self) -> None:
        self.docs: dict[Any, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any], projection: Any = None) -> dict[str, Any] | None:
        await asyncio.sleep(0)
        for doc in self.docs.values():
            if _matches(doc, query):
                return dict(doc)
        return None

    async def insert_one(self, doc: dict[str, Any]) -> None:
        await asyncio.sleep(0)
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("duplicate _id")
        self.docs[doc["_id"]] = dict(doc)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> Any:
        await asyncio.sleep(0)
        for doc in self.docs.values():
            if _matches(doc, query):
                doc.update(update["$set"])
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}
        self.events: list[dict[str, Any]] = []

    def collection(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collection(name)


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    from dxp import store

    database = FakeDB()

    async def emit_event(event: str, **fields: Any) -> int:
        database.events.append({"type": event, **fields})
        return len(database.events)

    monkeypatch.setattr(store, "collection", database.collection)
    monkeypatch.setattr(store, "emit_event", emit_event)
    database.collection("reports").docs[REPORT_ID] = {
        "_id": REPORT_ID,
        "run_id": "run_abc",
        "script": SCRIPT,
        "script_hash": SCRIPT_HASH,
        "status": "pending",
    }
    return database


# --- the gate: records what it saw, inserts the queued action like A06 does ---------------


@dataclass
class RecordingGate:
    db: FakeDB
    blocked: bool = False
    calls: list[tuple[m.RunContext, m.ProposedAction]] = field(default_factory=list)

    async def evaluate(self, ctx: m.RunContext, action: m.ProposedAction) -> m.Decision:
        self.calls.append((ctx, action))
        n = len(self.calls)
        decision_id = f"dec_{n:016x}"
        action_id = None if self.blocked else f"act_{n:016x}"
        if action_id:
            self.db.collection("actions").docs[action_id] = {
                "_id": action_id,
                "decision_id": decision_id,
                "kind": action.kind,
                "destination": action.destination,
                "status": "queued",
                "proposed_at": datetime.now(UTC),
            }
        return m.Decision(
            id=decision_id,
            run_id=ctx.run_id,
            initiated_by=ctx.stamp.initiated_by,
            stamp=ctx.stamp,
            cause=ctx.cause,
            request_id=ctx.request_id,
            kind=action.kind,
            inputs=action.inputs,
            destination=action.destination,
            target=action.target,
            checks=[m.CheckResult(check="destination_action", passed=not self.blocked, detail="fake")],
            failed_check="destination_action" if self.blocked else None,
            grant_id=ctx.grant_id,
            grant_version=ctx.grant_version,
            outcome="blocked" if self.blocked else "allowed",
            action_id=action_id,
            decided_at=datetime.now(UTC),
        )


@pytest.fixture
def gate(fake_db: FakeDB, monkeypatch: pytest.MonkeyPatch) -> RecordingGate:
    import dxp.gate

    recording = RecordingGate(fake_db)
    monkeypatch.setattr(dxp.gate, "evaluate", recording.evaluate)
    return recording


# --- a fake ElevenLabs client -------------------------------------------------------------


def api_error(status: int, headers: dict[str, str] | None = None, body: Any = None) -> Exception:
    from elevenlabs.core import ApiError

    return ApiError(status_code=status, headers=headers, body=body)


class FakeTextToSpeech:
    def __init__(self, owner: FakeElevenLabs) -> None:
        self.owner = owner

    async def convert(self, **kwargs: Any):
        self.owner.convert_calls.append(kwargs)
        reply = self.owner.queue.pop(0) if self.owner.queue else b"ID3-fake-audio"
        if isinstance(reply, Exception):
            raise reply
        await asyncio.sleep(0)
        yield reply[:5]
        yield reply[5:]


class FakeDictionaries:
    def __init__(self, owner: FakeElevenLabs) -> None:
        self.owner = owner

    async def create_from_rules(self, **kwargs: Any) -> Any:
        self.owner.dictionary_calls.append(kwargs)
        return SimpleNamespace(id="dict_fake", version_id="ver_fake")


class FakeElevenLabs:
    """Records every call. Queue replies with `queue.append(b"...")` or an exception."""

    def __init__(self) -> None:
        self.convert_calls: list[dict[str, Any]] = []
        self.dictionary_calls: list[dict[str, Any]] = []
        self.queue: list[Any] = []
        self.text_to_speech = FakeTextToSpeech(self)
        self.pronunciation_dictionaries = FakeDictionaries(self)


@pytest.fixture
def eleven(monkeypatch: pytest.MonkeyPatch) -> FakeElevenLabs:
    fake = FakeElevenLabs()
    monkeypatch.setenv("ELEVENLABS_API_KEY", FAKE_KEY)
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice_test")
    monkeypatch.delenv("ELEVENLABS_MODEL_ID", raising=False)
    monkeypatch.setattr(audio, "_client", lambda: fake)
    return fake


@pytest.fixture
def instant_retry(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retry-After waits are recorded, not slept."""
    waits: list[float] = []

    async def sleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr(audio, "_sleep", sleep)
    return waits


@pytest.fixture
def ctx() -> m.RunContext:
    principal = m.Principal(id="sam", name="Sam", kind="person", actions=["generate_briefing"])
    stamp = m.Stamp(kind="reviewer", run_id=None, agent=None, initiated_by="sam", principal="sam",
                    grant_id="sam", grant_version=1, policy_set_version="ps_test")
    return m.RunContext(
        run_id=None, principal=principal, stamp=stamp, grant_id="sam", grant_version=1,
        policy_set_version="ps_test", request_id="req_test",
        cause=m.DecisionCause(report_id=REPORT_ID, origin_run_id="run_abc"),
    )
