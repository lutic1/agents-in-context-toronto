"""A24: the queue entry, the start rule, recovery and the V45 crash test (Story 10.8, V38, V45).

`task_run` is turned on only inside the tests that need it (the `features` fixture); it is
never a default (V46)."""

from __future__ import annotations

import ast
import asyncio
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from dxp.identity import derive

from .conftest import REPORT_ID, decide

TASK_ID = derive("task_", REPORT_ID)
RUN_ID = derive("run_", TASK_ID)
PENDING_REVIEW = "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review."
NOT_RUN = "Approved: 1 update accepted. Follow-up task authorised; not run."


def td():
    return importlib.import_module("dxp.tasks.dispatch")


def ta():
    return importlib.import_module("dxp.tasks.authorise")


def rd():
    return importlib.import_module("dxp.reports.decide")


class SimulatedCrash(Exception):
    """Stops the request like a killed process: nothing after it in the request runs."""


async def restart(spawned: list[str]) -> None:
    """The API start hook's recovery steps, in order (A01's run_startup, without the index work)."""
    await rd().recover_accepting()
    await ta().recover_authorisations()
    await td().dispatch_next(spawned.append)


# --- task_run on ----------------------------------------------------------------------------


def test_flag_on_queues_the_task_and_starts_its_run_once(world, client, features) -> None:
    features("task_run")
    body = decide(client).json()
    assert body["message"] == PENDING_REVIEW
    (task,) = world.db.all("tasks")
    assert task["status"] == "queued" and task["queued_at"] is not None and task["run_id"] == RUN_ID
    assert world.run_starts == [{"caller": "sam", "grant_id": "task-" + TASK_ID[5:], "set": f"task:{TASK_ID}",
                                 "run_id": RUN_ID}]
    assert client.spawner.spawned == [RUN_ID]
    # a retried approval returns the same decision, task and run and starts nothing
    again = decide(client).json()
    assert again["task"]["run_id"] == RUN_ID and client.spawner.spawned == [RUN_ID]
    assert len(world.run_starts) == 1 and len(world.db.all("runs")) == 1


def test_flag_on_with_another_run_active_stays_queued(world, client, features) -> None:
    features("task_run")
    world.db.data["runs"]["run_other"] = {"_id": "run_other", "status": "running"}
    decide(client)
    (task,) = world.db.all("tasks")
    assert task["status"] == "queued" and task.get("dispatched_at") is None
    assert world.run_starts == [] and client.spawner.spawned == []
    # the run ends; the run-finish path calls dispatch_next
    world.db.data["runs"]["run_other"]["status"] = "done"
    spawned: list[str] = []
    asyncio.run(td().dispatch_next(spawned.append))
    assert spawned == [RUN_ID]


async def test_two_concurrent_dispatches_start_one_run(world, features) -> None:
    features("task_run")
    from dxp.api.models import Principal

    sam = Principal(id="sam", name="Sam", kind="person")
    await rd().decide(REPORT_ID, "approve", None, None, sam)
    await ta().authorise(REPORT_ID, sam)
    spawned: list[str] = []
    results = await asyncio.gather(td().dispatch_next(spawned.append), td().dispatch_next(spawned.append))
    assert spawned == [RUN_ID] and len([r for r in results if r is not None]) == 1
    assert len(world.db.all("runs")) == 1


async def test_a_stalled_queued_task_is_started_again_on_the_same_run(world, features) -> None:
    features("task_run")
    from dxp.api.models import Principal

    sam = Principal(id="sam", name="Sam", kind="person")
    await rd().decide(REPORT_ID, "approve", None, None, sam)
    await ta().authorise(REPORT_ID, sam)
    first: list[str] = []
    await td().dispatch_next(first.append)
    # within the stall window nothing happens
    second: list[str] = []
    await td().dispatch_next(second.append)
    assert first == [RUN_ID] and second == []
    # past the 10-minute window, still queued: started again on the same ID
    world.db.data["tasks"][TASK_ID]["dispatched_at"] = datetime.now(UTC) - timedelta(minutes=11)
    third: list[str] = []
    await td().dispatch_next(third.append)
    assert third == [RUN_ID] and len(world.db.all("runs")) == 1


async def test_an_existing_run_is_not_started_again_by_a_fresh_claim(world, features) -> None:
    """start_if_absent reports the run was not created by this call: no second worker."""
    features("task_run")
    from dxp.api.models import Principal

    sam = Principal(id="sam", name="Sam", kind="person")
    await rd().decide(REPORT_ID, "approve", None, None, sam)
    await ta().authorise(REPORT_ID, sam)
    world.db.data["runs"][RUN_ID] = {"_id": RUN_ID, "status": "done", "agent": "dxp-curator",
                                     "initiated_by": "sam", "grant_id": "g", "grant_version": 1,
                                     "set": f"task:{TASK_ID}", "kind": "task"}
    spawned: list[str] = []
    run = await td().dispatch_next(spawned.append)
    assert run is not None and run.id == RUN_ID and spawned == []


async def test_dispatch_does_nothing_with_task_run_off(world) -> None:
    world.db.data["tasks"]["task_x"] = {"_id": "task_x", "status": "queued", "grant_id": "task-x"}
    spawned: list[str] = []
    assert await td().dispatch_next(spawned.append) is None and spawned == []


async def test_mark_abandoned_fails_a_running_task_once(world) -> None:
    world.db.data["tasks"][TASK_ID] = {"_id": TASK_ID, "status": "running", "report_id": REPORT_ID, "run_id": RUN_ID}
    await td().mark_abandoned(TASK_ID)
    task = world.db.data["tasks"][TASK_ID]
    assert task["status"] == "failed" and task["error"] == "abandoned"
    await td().mark_abandoned(TASK_ID)  # conditional on running: nothing more
    assert len([e for e in world.db.all("events") if e["type"] == "task_status_changed"]) == 1


# --- the V45 crash test ---------------------------------------------------------------------


@pytest.mark.parametrize("flag", [False, True], ids=["task_run_off", "task_run_on"])
def test_crash_after_acceptance_is_completed_by_the_start_hook(world, client, features, monkeypatch, flag) -> None:
    if flag:
        features("task_run")
    routes = importlib.import_module("dxp.api.routes_report_decision")

    def crash(report_id: str) -> None:
        raise SimulatedCrash(report_id)

    monkeypatch.setattr(routes, "fault_hook", crash)
    with pytest.raises(SimulatedCrash):
        decide(client)
    report = world.report()
    assert report["status"] == "accepted" and report["approval"]["task_step"] == "pending"
    assert world.db.all("tasks") == []

    # restart, no second click
    spawned: list[str] = []
    asyncio.run(restart(spawned))
    asyncio.run(restart(spawned))  # safe to repeat

    report = world.report()
    decide_dec = [d for d in world.db.all("decisions") if d["kind"] == "decide_report"]
    auth = [d for d in world.db.all("decisions") if d["kind"] == "authorise_task"]
    assert len(decide_dec) == 1 and len(auth) == 1
    assert auth[0]["cause"]["approval_decision_id"] == decide_dec[0]["_id"] and auth[0]["origin"] == "recovery"
    assert auth[0]["request_id"] == report["approval"]["request_id"]
    (task,) = world.db.all("tasks")
    assert task["status"] == ("queued" if flag else "authorised")
    assert [g["_id"] for g in world.db.all("grants") if g["grant_id"].startswith("task-")] == [f"task-{TASK_ID[5:]}@v1"]
    assert report["approval"]["task_step"] == "done"
    assert len(world.db.all("runs")) == (1 if flag else 0)
    assert spawned == ([RUN_ID] if flag else [])


def test_crash_then_revoked_reviewer_grant_records_a_blocked_step(world, client, monkeypatch) -> None:
    routes = importlib.import_module("dxp.api.routes_report_decision")
    monkeypatch.setattr(routes, "fault_hook", lambda report_id: (_ for _ in ()).throw(SimulatedCrash(report_id)))
    with pytest.raises(SimulatedCrash):
        decide(client)
    world.revoke_sam()

    spawned: list[str] = []
    asyncio.run(restart(spawned))
    asyncio.run(restart(spawned))

    report = world.report()
    auth = [d for d in world.db.all("decisions") if d["kind"] == "authorise_task"]
    assert len(auth) == 1 and auth[0]["outcome"] == "blocked" and auth[0]["failed_check"] == "grant_active"
    assert world.db.all("tasks") == [] and report["approval"]["task_step"] == "blocked"
    assert report["status"] == "accepted"
    assert report["approval"]["reason"].startswith("Follow-up task not authorised")
    assert spawned == []
    # a retried decision reports it and never reopens the step
    monkeypatch.setattr(routes, "fault_hook", None)
    body = decide(client).json()
    assert "Follow-up task not authorised" in body["message"] and body["task"] is None
    assert len([d for d in world.db.all("decisions") if d["kind"] == "authorise_task"]) == 1


def test_crash_before_the_report_is_accepted_is_finished_by_recover_accepting(world, client, monkeypatch) -> None:
    decide_mod = rd()
    original = decide_mod.finish_accepting

    async def crash(report_id: str):
        raise SimulatedCrash(report_id)

    monkeypatch.setattr(decide_mod, "finish_accepting", crash)
    with pytest.raises(SimulatedCrash):
        decide(client)
    assert world.report()["status"] == "accepting" and world.report()["approval"]["task_step"] == "pending"
    monkeypatch.setattr(decide_mod, "finish_accepting", original)
    asyncio.run(restart([]))
    assert world.report()["status"] == "accepted" and world.report()["approval"]["task_step"] == "done"
    assert len(world.applied) == 1 and len(world.db.all("tasks")) == 1


# --- the import rule ------------------------------------------------------------------------

A24_FILES = ["dxp/reports/decide.py", "dxp/tasks/authorise.py", "dxp/tasks/dispatch.py", "dxp/gate/grants.py",
             "dxp/api/routes_report_decision.py"]


@pytest.mark.parametrize("path", A24_FILES)
def test_nothing_in_a24_imports_tasks_run(path: str) -> None:
    source = (Path(__file__).resolve().parents[2] / path).read_text()
    assert "dxp.tasks.run" not in source and "tasks.run(" not in source
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module == "dxp.tasks" and any(a.name == "run" for a in node.names))


def test_reports_imports_nothing_from_tasks() -> None:
    source = (Path(__file__).resolve().parents[2] / "dxp/reports/decide.py").read_text()
    assert "dxp.tasks" not in source and "from dxp import" in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "dxp":
            assert "tasks" not in {a.name for a in node.names}


def test_gate_grants_imports_nothing_from_memory_retrieval_or_reports() -> None:
    source = (Path(__file__).resolve().parents[2] / "dxp/gate/grants.py").read_text()
    for name in ("dxp.memory", "dxp.retrieval", "dxp.reports"):
        assert name not in source
