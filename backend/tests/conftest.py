"""Shared test fixtures (A01; D36). Each PR's own tests live in backend/tests/<id>/.

- Fake keys for every credential: tests never read .env and never reach Slack, ElevenLabs,
  HeyGen, Voyage or Anthropic with a real key.
- Backend flags all off (`DXP_FEATURES` empty): `task_run`, `revert` and `live_stream` stay off
  unless a test turns one on with `features`.
- Atlas: tests marked `atlas` (or using `db`) run against the Atlas Sandbox in a fresh database
  per session, `dxp_test_<hex>`, dropped at the end; never `dxp` or `dxp_smoke`. Without
  MONGODB_URI they are skipped with that reason.
- Fakes: `fake_gate` (patches `dxp.gate.evaluate`), `fake_slack`, `fake_elevenlabs`,
  `fake_heygen` (recording senders that each owner installs on its own client), `fake_run_function`.
"""

from __future__ import annotations

import os
import secrets
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Environment: fake keys, flags off, a session test database name
# ---------------------------------------------------------------------------

FAKE_ENV = {
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "DXP_API_KEY": "test-dxp-api-key",
    "DXP_AGENT_KEY": "test-dxp-agent-key",
    "DXP_SEED_KEY": "test-dxp-seed-key",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.invalid/services/TEST",
    "DXP_BASE_URL": "https://dxp.test",
    "DXP_ALLOWED_ORIGINS": "http://localhost:3000",
    "DXP_EMBEDDING": "none",
    "VOYAGE_API_KEY": "test-voyage-key",
    "ELEVENLABS_API_KEY": "test-elevenlabs-key",
    "HEYGEN_API_KEY": "test-heygen-key",
    "DXP_FEATURES": "",
    "LANGSMITH_TRACING": "false",
}
FORBIDDEN_DBS = {"dxp", "dxp_smoke"}
TEST_DB = f"dxp_test_{secrets.token_hex(4)}"
ATLAS_SKIP_REASON = "MONGODB_URI is not set: Atlas Sandbox tests skipped (set it to run them in a fresh test database)"


def pytest_configure(config: pytest.Config) -> None:
    os.environ.update(FAKE_ENV)
    os.environ.pop("LANGSMITH_API_KEY", None)
    os.environ["DXP_DB"] = TEST_DB


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("MONGODB_URI"):
        return
    skip = pytest.mark.skip(reason=ATLAS_SKIP_REASON)
    for item in items:
        if "atlas" in item.keywords or "db" in getattr(item, "fixturenames", ()):
            item.add_marker(skip)


@pytest.fixture
def features(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Turn backend flags on for one test: features("task_run")."""

    def set_flags(*names: str) -> None:
        monkeypatch.setenv("DXP_FEATURES", ",".join(names))

    return set_flags


# ---------------------------------------------------------------------------
# Atlas Sandbox: a fresh database per session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db() -> AsyncIterator[Any]:
    """The session's test database, with store.ensure_indexes() applied; dropped afterwards."""
    from dxp import store

    name = os.environ["DXP_DB"]
    assert name not in FORBIDDEN_DBS and name.startswith("dxp_test_"), name
    await store.ensure_indexes()
    database = store.get_db()
    try:
        yield database
    finally:
        await store.get_client().drop_database(name)
        await store.close()


# ---------------------------------------------------------------------------
# Fake gate
# ---------------------------------------------------------------------------


@dataclass
class FakeGate:
    """Replaces gate.evaluate. Allows everything unless `block(kind, check)` says otherwise;
    records every (ctx, action) it saw."""

    calls: list[tuple[Any, Any]] = field(default_factory=list)
    blocked: dict[str, str] = field(default_factory=dict)

    def block(self, kind: str, check: str = "team_scope") -> None:
        self.blocked[kind] = check

    async def evaluate(self, ctx: Any, action: Any) -> Any:
        from dxp.api.models import CheckResult, Decision, Stamp

        self.calls.append((ctx, action))
        failed = self.blocked.get(action.kind)
        stamp = getattr(ctx, "stamp", None) or Stamp(kind="run", principal="test")
        return Decision(
            id=f"dec_fake{len(self.calls):012d}",
            run_id=getattr(ctx, "run_id", None),
            agent=stamp.agent,
            initiated_by=stamp.initiated_by,
            stamp=stamp,
            cause=getattr(ctx, "cause", None),
            request_id=getattr(ctx, "request_id", None),
            kind=action.kind,
            inputs=action.inputs,
            evidence_ref=action.evidence_ref,
            destination=action.destination,
            target=action.target,
            claims=action.claims,
            checks=[CheckResult(check=failed or "fake_gate", passed=failed is None, detail="fake gate")],
            failed_check=failed,
            grant_id=getattr(ctx, "grant_id", "test"),
            grant_version=getattr(ctx, "grant_version", 1),
            policy_set_version=getattr(ctx, "policy_set_version", None),
            outcome="blocked" if failed else "allowed",
            decided_at=datetime.now(UTC),
        )


@pytest.fixture
def fake_gate(monkeypatch: pytest.MonkeyPatch) -> FakeGate:
    import dxp.gate

    gate = FakeGate()
    monkeypatch.setattr(dxp.gate, "evaluate", gate.evaluate)
    return gate


# ---------------------------------------------------------------------------
# Fake external senders (Slack, ElevenLabs, HeyGen)
# ---------------------------------------------------------------------------


class FakeTimeout(Exception):
    """Raised by a fake sender to simulate a timeout or connection error."""


@dataclass
class FakeResponse:
    status: int = 200
    body: Any = "ok"
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class FakeSender:
    """A recording sender. Queue responses with `respond(...)` or `fail()`; once the queue is
    empty it answers `default`. Each owner installs it on its own client with monkeypatch."""

    name: str
    default: FakeResponse = field(default_factory=FakeResponse)
    sent: list[dict[str, Any]] = field(default_factory=list)
    queue: list[FakeResponse | Exception] = field(default_factory=list)

    def respond(self, status: int = 200, body: Any = "ok", headers: dict[str, str] | None = None) -> None:
        self.queue.append(FakeResponse(status, body, headers or {}))

    def fail(self, exc: Exception | None = None) -> None:
        self.queue.append(exc or FakeTimeout(f"{self.name} timed out"))

    async def __call__(self, *args: Any, **kwargs: Any) -> FakeResponse:
        self.sent.append({"args": args, "kwargs": kwargs})
        reply = self.queue.pop(0) if self.queue else self.default
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def fake_slack() -> FakeSender:
    """HTTP 200 `ok` by default (delivered, S7)."""
    return FakeSender("slack")


@pytest.fixture
def fake_elevenlabs() -> FakeSender:
    return FakeSender("elevenlabs", default=FakeResponse(200, b"ID3-fake-audio"))


@pytest.fixture
def fake_heygen() -> FakeSender:
    return FakeSender("heygen", default=FakeResponse(200, {"data": {"video_id": "vid_fake", "status": "processing"}}))


# ---------------------------------------------------------------------------
# The run function and the API
# ---------------------------------------------------------------------------


@dataclass
class FakeRunFunction:
    """Stands in for the Modal run function: records `.spawn(run_id)` calls."""

    spawned: list[str] = field(default_factory=list)

    def spawn(self, run_id: str) -> None:
        self.spawned.append(run_id)


@pytest.fixture
def fake_run_function() -> FakeRunFunction:
    return FakeRunFunction()


@pytest.fixture
def api_client(fake_run_function: FakeRunFunction):
    """A TestClient without the startup hook (no Atlas needed). Use `with api_client:` to run it."""
    from fastapi.testclient import TestClient

    from dxp.api.app import create_app

    return TestClient(create_app(fake_run_function), raise_server_exceptions=False)
