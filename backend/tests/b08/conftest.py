"""B08 test setup: a fake LiveAvatar client, an in-memory report and media store, and a Reviewer.

Nothing here reaches LiveAvatar, Atlas or the real gate. The fake gate is the shared `fake_gate`
fixture (tests/conftest.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from dxp.api.models import Principal
from dxp.briefing import avatar
from dxp.briefing.avatar import LiveAvatarError, SessionToken

REPORT_ID = "rep_0123456789abcdef"
SCRIPT = "A new trial signal worth investigating. Status: terminated. No results posted."
SECRET_TOKEN = "fake-session-token-do-not-leak"
FAKE_KEY = "fake-liveavatar-key-do-not-leak"
AVATAR_ID = "11111111-2222-3333-4444-555555555555"


@dataclass
class FakeLiveAvatar:
    """Records every token request. Queue an error with `fail(status)`."""

    calls: list[dict[str, Any]] = field(default_factory=list)
    next_error: LiveAvatarError | None = None

    def fail(self, status: int | None = 500) -> None:
        self.next_error = LiveAvatarError(status)

    async def create_session_token(self, *, avatar_id: str, max_session_duration: int, is_sandbox: bool) -> SessionToken:
        self.calls.append({"avatar_id": avatar_id, "max_session_duration": max_session_duration, "is_sandbox": is_sandbox})
        if self.next_error is not None:
            error, self.next_error = self.next_error, None
            raise error
        return SessionToken(session_id="sess_fake_1", session_token=SECRET_TOKEN)


class MemoryStore:
    """In-memory reports and media."""

    def __init__(self) -> None:
        self.reports: dict[str, dict[str, Any]] = {}
        self.media: list[dict[str, Any]] = []
        self.actions: dict[str, dict[str, Any]] = {}
        self.history: list[tuple[str, str]] = []  # (action_id, status) in order

    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        return self.reports.get(report_id)

    async def insert_media(self, doc: dict[str, Any]) -> None:
        if not any(d["_id"] == doc["_id"] for d in self.media):
            self.media.append(dict(doc))

    async def claim_action(self, action_id: str) -> bool:
        action = self.actions.get(action_id)
        if action is None or action["status"] != "queued":
            return False
        action["status"] = "dispatching"
        self.history.append((action_id, "dispatching"))
        return True

    async def settle_action(self, action_id: str, status: str, result: dict[str, Any] | None = None) -> bool:
        action = self.actions.get(action_id)
        if action is None or action["status"] != "dispatching":
            return False
        action.update(status=status, result=result)
        self.history.append((action_id, status))
        return True

    async def latest_media(self, report_id: str) -> dict[str, Any] | None:
        found = [d for d in self.media if d["report_id"] == report_id]
        return max(found, key=lambda d: d["created_at"]) if found else None


@pytest.fixture
def live() -> FakeLiveAvatar:
    return FakeLiveAvatar()


@pytest.fixture
def media_store() -> MemoryStore:
    store = MemoryStore()
    store.reports[REPORT_ID] = {
        "_id": REPORT_ID,
        "run_id": "run_0123456789abcdef",
        "script": SCRIPT,
        "script_hash": "hash_fake",
        "status": "accepted",
    }
    return store


@pytest.fixture(autouse=True)
def avatar_env(monkeypatch: pytest.MonkeyPatch, live: FakeLiveAvatar, media_store: MemoryStore):
    """The avatar module with fakes installed, the key and avatar id set, sandbox off."""
    monkeypatch.setenv("LIVEAVATAR_API_KEY", FAKE_KEY)
    monkeypatch.setenv("LIVEAVATAR_AVATAR_ID", AVATAR_ID)
    monkeypatch.delenv("LIVEAVATAR_SANDBOX", raising=False)
    monkeypatch.delenv("LIVEAVATAR_MAX_SECONDS", raising=False)
    monkeypatch.setenv("DXP_FEATURES", "avatar")
    avatar.set_client(live)
    avatar.set_store(media_store)
    yield
    avatar.set_client(None)
    avatar.set_store(None)


SAM = Principal(id="sam", name="Sam", kind="person", actions=["generate_avatar_video"])


ACTION_ID = "act_0000000000000b08"


@pytest.fixture
def fake_gate(fake_gate, media_store: MemoryStore, monkeypatch: pytest.MonkeyPatch):
    """The shared fake gate, plus what the real one does on an allowed Decision: insert the action
    `queued` (insert-if-absent, AD-20) and point the Decision at it."""
    inner = fake_gate.evaluate

    async def evaluate(ctx: Any, action: Any) -> Any:
        decision = await inner(ctx, action)
        if decision.outcome != "allowed":
            return decision
        media_store.actions.setdefault(ACTION_ID, {"_id": ACTION_ID, "kind": action.kind, "status": "queued", "result": None})
        return decision.model_copy(update={"action_id": ACTION_ID})

    fake_gate.evaluate = evaluate  # type: ignore[method-assign]
    import dxp.gate

    monkeypatch.setattr(dxp.gate, "evaluate", evaluate)
    return fake_gate


@pytest.fixture
def reviewer(monkeypatch: pytest.MonkeyPatch):
    """Sam's key resolves to sam@v1 (no database)."""
    from dxp.api import auth

    async def resolve_actor(api_key: str) -> Principal:
        return SAM

    async def grant_for_key(api_key: str | None, db: Any = None) -> dict[str, Any] | None:
        return {"grant_id": "sam", "version": 1, "principal": "sam", "kind": "person"}

    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)
    monkeypatch.setattr(auth, "grant_for_key", grant_for_key)
    return SAM
