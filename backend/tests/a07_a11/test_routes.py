"""Route behaviour without Atlas: authority, the task-set refusal, start and spawn, stop authority
and the background sweep being started (Stories 9.1, 9.5; V38)."""

from __future__ import annotations

from typing import Any

import pytest

import dxp.ledger
import dxp.runs
from dxp.api import models as m
from dxp.api import routes_runs

from .conftest import TASK_ID

H = {"X-DxP-Key": "key-sam"}


def a_run(**overrides: Any) -> m.Run:
    data = dict(id="run_0123456789abcdef", agent="dxp-curator", initiated_by="sam", grant_id="lbdx",
                grant_version=1, team_id="team_lbdx", set="discover", kind="discover", status="running")
    data.update(overrides)
    return m.Run(**data)


@pytest.fixture
def started(monkeypatch: pytest.MonkeyPatch) -> list[tuple]:
    """Fakes runs.start / runs.get_run / ledger.recover_applying and records the calls."""
    calls: list[tuple] = []

    async def start(caller, grant_id, set, run_id=None):
        calls.append(("start", caller.id, grant_id, set, run_id))
        return a_run(set=set)

    async def get_run(run_id):
        calls.append(("get_run", run_id))
        return a_run(id=run_id)

    async def recover_applying():
        calls.append(("recover_applying",))

    async def fail(run_id, error):
        calls.append(("fail", run_id, error))
        return a_run(id=run_id, status="failed")

    monkeypatch.setattr(dxp.runs, "start", start)
    monkeypatch.setattr(dxp.runs, "get_run", get_run)
    monkeypatch.setattr(dxp.runs, "fail", fail)
    monkeypatch.setattr(dxp.ledger, "recover_applying", recover_applying)
    return calls


@pytest.fixture
def no_sweep(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    swept: list[str] = []

    async def sweep(run_id, start, *, recover=True):
        swept.append(run_id)

    async def sweep_many(run_ids, start):
        swept.extend(run_ids)

    monkeypatch.setattr(routes_runs, "sweep_in_background", sweep)
    monkeypatch.setattr(routes_runs, "sweep_runs_in_background", sweep_many)
    return swept


def test_missing_key_is_401(api_client, authority) -> None:
    response = api_client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "discover"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "missing_key"


def test_unknown_key_is_401_and_creates_nothing(api_client, authority, started) -> None:
    response = api_client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "discover"},
                               headers={"X-DxP-Key": "nope"})
    assert response.status_code == 401
    assert set(response.json()) == {"error"}
    assert not [c for c in started if c[0] == "start"]


def test_seed_key_is_refused_on_every_route(api_client, authority, started) -> None:
    seed = {"X-DxP-Key": "key-seed"}
    for method, path, body in (("POST", "/runs", {"grant_id": "lbdx", "set": "discover"}),
                               ("GET", "/runs", None), ("GET", "/runs/run_x", None),
                               ("POST", "/runs/run_x/stop", None), ("GET", "/runs/run_x/audit", None),
                               ("GET", "/decisions/dec_x", None), ("GET", "/actions", None),
                               ("GET", "/actions/act_x", None)):
        response = api_client.request(method, "/api/v1" + path, json=body, headers=seed)
        assert response.status_code == 403, (method, path, response.text)
        assert response.json()["error"]["code"] == "seed_key_not_accepted"


def test_client_task_set_is_refused_with_403_and_no_run(api_client, authority, started, fake_run_function) -> None:
    response = api_client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": f"task:{TASK_ID}"}, headers=H)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "task_set_refused"
    assert started == []  # runs.start never called: no run, nothing spawned (V38)
    assert fake_run_function.spawned == []


def test_task_set_is_refused_even_under_its_own_task_grant(api_client, authority, started, fake_run_function) -> None:
    grant_id = "task-" + TASK_ID.removeprefix("task_")
    response = api_client.post("/api/v1/runs", json={"grant_id": grant_id, "set": f"task:{TASK_ID}"}, headers=H)
    assert response.status_code == 403
    assert started == [] and fake_run_function.spawned == []


def test_invalid_set_is_400(api_client, authority, started) -> None:
    response = api_client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "nct:12345"}, headers=H)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_set"
    assert started == []


def test_identity_never_comes_from_the_body(api_client, authority, started) -> None:
    body = {"grant_id": "lbdx", "set": "discover", "initiated_by": "luis", "agent": "someone", "team_id": "t"}
    response = api_client.post("/api/v1/runs", json=body, headers=H)
    assert response.status_code == 200, response.text
    start = next(c for c in started if c[0] == "start")
    assert start == ("start", "sam", "lbdx", "discover", None)  # caller from the key only


def test_post_runs_starts_the_run_function_after_recovery(api_client, authority, started, fake_run_function) -> None:
    response = api_client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "nct:NCT05715229"}, headers=H)
    assert response.status_code == 200, response.text
    assert [c[0] for c in started] == ["recover_applying", "start", "get_run"]
    assert fake_run_function.spawned == ["run_0123456789abcdef"]
    assert response.json()["agent"] == "dxp-curator" and response.json()["initiated_by"] == "sam"


def test_a_run_whose_worker_cannot_start_is_marked_failed(api_client, authority, started, monkeypatch) -> None:
    def broken(run_id: str) -> None:
        raise RuntimeError("modal unavailable")

    api_client.app.state.start_run = broken
    response = api_client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "discover"}, headers=H)
    assert response.status_code == 503
    assert ("fail", "run_0123456789abcdef", "the run function could not be started") in started


def test_get_run_returns_current_state_and_starts_the_sweep(api_client, authority, started, no_sweep, monkeypatch) -> None:
    import dxp.actions

    async def must_not_send(*args, **kwargs):  # GET never calls Slack (D24)
        raise AssertionError("dispatch called inside a request")

    monkeypatch.setattr(dxp.actions, "dispatch", must_not_send)
    response = api_client.get("/api/v1/runs/run_0123456789abcdef", headers=H)
    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert no_sweep == ["run_0123456789abcdef"]


def test_list_runs_sweeps_only_active_runs(api_client, authority, no_sweep, monkeypatch) -> None:
    async def list_runs(limit: int = 50):
        return [a_run(id="run_a"), a_run(id="run_b", status="done"), a_run(id="run_c", status="stopping")]

    monkeypatch.setattr(dxp.runs, "list_runs", list_runs)
    response = api_client.get("/api/v1/runs", headers=H)
    assert response.status_code == 200
    assert [r["id"] for r in response.json()["items"]] == ["run_a", "run_b", "run_c"]
    assert no_sweep == ["run_a", "run_c"]


def test_stop_by_someone_not_allowed_is_403(api_client, authority, no_sweep, monkeypatch) -> None:
    async def load_run(run_id):
        return {"_id": run_id, "initiated_by": "sam", "grant_id": "lbdx"}

    stopped: list[str] = []

    async def stop(run_id):
        stopped.append(run_id)
        return a_run(id=run_id, status="stopping")

    monkeypatch.setattr(routes_runs, "load_run", load_run)
    monkeypatch.setattr(dxp.runs, "stop", stop)
    refused = api_client.post("/api/v1/runs/run_a/stop", headers={"X-DxP-Key": "key-vlad"})
    assert refused.status_code == 403 and stopped == []
    allowed = api_client.post("/api/v1/runs/run_a/stop", headers=H)
    assert allowed.status_code == 200 and allowed.json()["status"] == "stopping"
    assert stopped == ["run_a"] and no_sweep == ["run_a"]
