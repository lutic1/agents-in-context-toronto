"""A27 (Story 9.12): GET /runs/<run_id>/stream over a fake change stream. No network, no Atlas.

The fake `events` collection keeps an oplog of inserts with hex resume tokens, applies the
route's `$match` pipeline the way the server would, resumes after a token, and fails with
InvalidResumeToken for a token it never issued.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import OperationFailure

import dxp.api.auth
from dxp.api import models as m
from dxp.api import routes_run_stream
from dxp.search import stream as search_stream

KEY = "test-dxp-api-key"
RUN = "run_a27"
OTHER = "run_other"


# ---------------------------------------------------------------------------
# A fake change stream on `events`
# ---------------------------------------------------------------------------


def _matches(doc: dict[str, Any], pipeline: list[dict[str, Any]]) -> bool:
    for stage in pipeline:
        for path, want in stage.get("$match", {}).items():
            if path == "operationType":
                if want != "insert":
                    return False
                continue
            value: Any = {"fullDocument": doc}
            for part in path.split("."):
                value = value.get(part) if isinstance(value, dict) else None
            if value != want:
                return False
    return True


class FakeChangeStream:
    def __init__(self, coll: FakeEvents, pipeline: list[dict[str, Any]], start: int) -> None:
        self.coll, self.pipeline, self.pos = coll, pipeline, start
        self.closed = False

    async def __aenter__(self) -> FakeChangeStream:  # noqa: PYI034
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.closed = True

    def __aiter__(self) -> FakeChangeStream:
        return self

    async def __anext__(self) -> dict[str, Any]:
        while True:
            if self.pos < len(self.coll.oplog):
                token, doc = self.coll.oplog[self.pos]
                self.pos += 1
                if _matches(doc, self.pipeline):
                    return {"_id": {"_data": token}, "operationType": "insert", "fullDocument": doc}
                continue
            await asyncio.sleep(0.01)


class FakeEvents:
    def __init__(self) -> None:
        self.oplog: list[tuple[str, dict[str, Any]]] = []
        self.arrive_on_open: list[dict[str, Any]] = []  # inserted right after the next watch opens
        self.watches: list[dict[str, Any]] = []
        self.streams: list[FakeChangeStream] = []
        self.writes = 0

    def insert(self, doc: dict[str, Any]) -> str:
        token = f"82{len(self.oplog) + 1:08X}"
        self.oplog.append((token, doc))
        return token

    async def watch(self, pipeline: list[dict[str, Any]], resume_after: dict[str, Any] | None = None, **kw: Any):
        self.watches.append({"pipeline": pipeline, "resume_after": resume_after})
        if resume_after is None:
            start = len(self.oplog)
        else:
            tokens = [t for t, _ in self.oplog]
            if resume_after["_data"] not in tokens:
                raise OperationFailure("cannot resume stream; the resume token was not found", code=260)
            start = tokens.index(resume_after["_data"]) + 1
        for doc in self.arrive_on_open:
            self.insert(doc)
        self.arrive_on_open = []
        change_stream = FakeChangeStream(self, pipeline, start)
        self.streams.append(change_stream)
        return change_stream

    def __getattr__(self, name: str) -> Any:  # any write would be a bug: the stream writes nothing
        if name.startswith(("insert_", "update_", "delete_", "replace_", "find_one_and")):
            self.writes += 1
        raise AttributeError(name)


def event(seq: int, run_id: str = RUN, type_: str = "action_allowed") -> dict[str, Any]:
    return {"_id": seq, "type": type_, "run_id": run_id, "dedupe_key": f"k{seq}", "action_id": f"act_{seq}",
            "at": "2026-11-14T14:00:00Z", "stamp": None}


@pytest.fixture
def events(monkeypatch: pytest.MonkeyPatch) -> FakeEvents:
    fake = FakeEvents()
    monkeypatch.setattr(search_stream, "_events", lambda: fake)
    return fake


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, events: FakeEvents) -> TestClient:
    async def resolve_actor(api_key: str) -> m.Principal:
        if api_key != KEY:
            from dxp.api.errors import ApiError

            raise ApiError(401, "unknown_key", "Unknown API key.")
        return m.Principal(id="sam", name="Sam", kind="person", actions=[])

    monkeypatch.setattr(dxp.api.auth, "resolve_actor", resolve_actor)
    monkeypatch.setenv(routes_run_stream.MAX_SECONDS_ENV, "0.4")
    from dxp.api.app import create_app

    return TestClient(create_app(lambda run_id: None))


@pytest.fixture
def live(features) -> None:
    features("live_stream")


def get(client: TestClient, run_id: str = RUN, last_event_id: str | None = None, key: str | None = KEY):
    headers = {}
    if key:
        headers["X-DxP-Key"] = key
    if last_event_id is not None:
        headers["Last-Event-ID"] = last_event_id
    return client.get(f"/api/v1/runs/{run_id}/stream", headers=headers)


def parse(body: str) -> list[dict[str, Any]]:
    """SSE frames: each a dict of id / event / data / comments."""
    frames = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        frame: dict[str, Any] = {"comments": []}
        for line in block.split("\n"):
            if line.startswith(":"):
                frame["comments"].append(line[1:].strip())
            elif ":" in line:
                name, _, value = line.partition(":")
                frame[name] = value.removeprefix(" ")
        frames.append(frame)
    return frames


def messages(body: str) -> list[dict[str, Any]]:
    return [f for f in parse(body) if "data" in f and "event" not in f]


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------


def test_404_with_the_flag_off(client: TestClient, events: FakeEvents) -> None:
    response = get(client)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert events.watches == []  # nothing opened


def test_needs_a_key(client: TestClient, live: None, events: FakeEvents) -> None:
    assert get(client, key=None).status_code == 401
    assert get(client, key="wrong").status_code == 401
    assert events.watches == []


def test_an_event_reaches_the_stream(client: TestClient, live: None, events: FakeEvents) -> None:
    events.arrive_on_open = [event(7)]
    started = time.monotonic()
    response = get(client)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    [msg] = messages(response.text)
    data = json.loads(msg["data"])
    assert data["seq"] == 7 and data["type"] == "action_allowed" and data["run_id"] == RUN
    assert data["action_id"] == "act_7"
    assert set(data) <= set(m.Event.model_fields)  # the AD-14 Event shape, no _id or dedupe_key
    assert msg["id"] == events.oplog[0][0]  # the SSE id is the resume token
    assert time.monotonic() - started < 3
    assert events.watches[0]["pipeline"] == [{"$match": {"operationType": "insert", "fullDocument.run_id": RUN}}]
    assert events.watches[0]["resume_after"] is None
    assert all(s.closed for s in events.streams)
    assert events.writes == 0


def test_no_event_from_another_run(client: TestClient, live: None, events: FakeEvents) -> None:
    events.arrive_on_open = [event(1, OTHER), event(2), event(3, OTHER), event(4)]
    seqs = [json.loads(f["data"])["seq"] for f in messages(get(client).text)]
    assert seqs == [2, 4]


def test_reconnect_with_last_event_id_misses_and_repeats_nothing(
    client: TestClient, live: None, events: FakeEvents
) -> None:
    events.arrive_on_open = [event(1), event(2)]
    first = messages(get(client).text)
    assert [json.loads(f["data"])["seq"] for f in first] == [1, 2]
    last_id = first[-1]["id"]

    # While the client is away, two more events of the run (and one of another run) are written.
    events.insert(event(3))
    events.insert(event(4, OTHER))
    events.insert(event(5))
    events.arrive_on_open = [event(6)]

    second = messages(get(client, last_event_id=last_id).text)
    assert [json.loads(f["data"])["seq"] for f in second] == [3, 5, 6]
    assert events.watches[-1]["resume_after"] == {"_data": last_id}


def test_last_event_id_as_query_parameter(client: TestClient, live: None, events: FakeEvents) -> None:
    token = events.insert(event(1))
    events.insert(event(2))
    response = client.get(f"/api/v1/runs/{RUN}/stream", params={"lastEventId": token}, headers={"X-DxP-Key": KEY})
    assert [json.loads(f["data"])["seq"] for f in messages(response.text)] == [2]


@pytest.mark.parametrize("bad", ["82DEADBEEF", "not a token!"])
def test_reset_on_a_token_that_cannot_be_resumed(client: TestClient, live: None, events: FakeEvents, bad: str) -> None:
    events.insert(event(1))
    started = time.monotonic()
    response = get(client, last_event_id=bad)
    assert response.status_code == 200
    frames = parse(response.text)
    resets = [f for f in frames if f.get("event") == "reset"]
    assert len(resets) == 1 and json.loads(resets[0]["data"])["reset"] is True
    assert messages(response.text) == []
    assert time.monotonic() - started < 0.4  # ends at once, without waiting for the limit


def test_the_stream_ends_at_the_limit(client: TestClient, live: None, events: FakeEvents) -> None:
    started = time.monotonic()
    response = get(client)
    elapsed = time.monotonic() - started
    assert response.status_code == 200
    assert 0.35 <= elapsed < 2.5
    assert parse(response.text)[0].get("retry") == str(routes_run_stream.RETRY_MS)
    assert all(s.closed for s in events.streams)


def test_heartbeat_comments(client: TestClient, live: None, events: FakeEvents, monkeypatch) -> None:
    monkeypatch.setattr(routes_run_stream, "HEARTBEAT_SECONDS", 0.1)
    comments = [c for f in parse(get(client).text) for c in f["comments"]]
    assert comments.count("heartbeat") >= 2


def test_a_failed_watch_ends_the_stream_quietly(client: TestClient, live: None, monkeypatch) -> None:
    class Broken:
        async def watch(self, *args: Any, **kwargs: Any) -> Any:
            raise OperationFailure("The $changeStream stage is only supported on replica sets", code=40573)

    monkeypatch.setattr(search_stream, "_events", lambda: Broken())
    started = time.monotonic()
    response = get(client)
    assert response.status_code == 200
    assert messages(response.text) == []
    assert not [f for f in parse(response.text) if f.get("event") == "reset"]
    assert time.monotonic() - started < 0.4


@pytest.mark.parametrize(("raw", "expected"), [("", 50.0), ("abc", 50.0), ("-3", 50.0), ("inf", 50.0), ("20", 20.0)])
def test_max_seconds_default_and_env(monkeypatch, raw: str, expected: float) -> None:
    monkeypatch.setenv(routes_run_stream.MAX_SECONDS_ENV, raw)
    assert routes_run_stream.max_seconds() == expected


def test_unknown_event_type_still_wakes_the_screen() -> None:
    out = search_stream.to_event({"_id": 9, "type": "something_new", "run_id": RUN})
    assert out == {"seq": 9, "type": "something_new", "run_id": RUN}
