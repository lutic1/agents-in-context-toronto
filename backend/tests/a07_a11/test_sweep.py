"""The background sweep's layering and order without Atlas (D43, V38, V45): runs.sweep changes no
action; the route's task marks held dispatching actions unknown and queued ones failed, sets an
abandoned task failed, settles, recovers authorisations, then dispatches the next queued task."""

from __future__ import annotations

import pytest

import dxp.actions
import dxp.runs
import dxp.tasks
from dxp.api import routes_runs

from .conftest import TASK_ID


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple] = []
    held: list[dict] = []
    run_doc: dict = {"_id": "run_t", "task_id": None}
    abandoned = {"any": False}

    async def sweep(run_id):
        calls.append(("runs.sweep", run_id))
        return list(held)

    async def mark_unknown(action_id, error):
        calls.append(("actions.mark_unknown", action_id, error))
        return True

    async def mark_failed(action_id, error):
        calls.append(("actions.mark_failed", action_id, error))
        return True

    async def mark_abandoned(task_id):
        calls.append(("tasks.mark_abandoned", task_id))

    async def settle(run_id):
        calls.append(("runs.settle", run_id))

    async def recover_authorisations():
        calls.append(("tasks.recover_authorisations",))

    async def dispatch_next(start):
        calls.append(("tasks.dispatch_next", start))

    async def load_run(run_id):
        return run_doc

    async def has_abandoned(run_id):
        calls.append(("runs.has_abandoned", run_id))
        return abandoned["any"]

    monkeypatch.setattr(dxp.runs, "sweep", sweep)
    monkeypatch.setattr(dxp.runs, "settle", settle)
    monkeypatch.setattr(dxp.runs, "has_abandoned", has_abandoned)
    monkeypatch.setattr(dxp.actions, "mark_unknown", mark_unknown)
    monkeypatch.setattr(dxp.actions, "mark_failed", mark_failed)
    monkeypatch.setattr(dxp.tasks, "mark_abandoned", mark_abandoned)
    monkeypatch.setattr(dxp.tasks, "recover_authorisations", recover_authorisations)
    monkeypatch.setattr(dxp.tasks, "dispatch_next", dispatch_next)
    monkeypatch.setattr(routes_runs, "load_run", load_run)
    return calls, held, run_doc, abandoned


def start(run_id: str) -> None:
    return None


async def test_sweep_settles_held_actions_then_settles_recovers_and_dispatches(recorder) -> None:
    calls, held, _, _ = recorder
    held += [
        {"action_id": "act_in_flight", "status": "dispatching"},
        {"action_id": "act_never_sent", "status": "queued"},
        {"action_id": "act_done", "status": "delivered"},
    ]
    await routes_runs.sweep_in_background("run_t", start)
    assert calls == [
        ("runs.sweep", "run_t"),
        ("actions.mark_unknown", "act_in_flight", "abandoned_in_flight"),
        ("actions.mark_failed", "act_never_sent", "abandoned_before_send"),
        ("runs.settle", "run_t"),
        ("tasks.recover_authorisations",),
        ("tasks.dispatch_next", start),
    ]


async def test_a_task_run_with_abandoned_admissions_fails_its_task(recorder) -> None:
    calls, held, run_doc, _ = recorder
    run_doc["task_id"] = TASK_ID
    held.append({"action_id": "act_search", "status": "dispatching"})
    await routes_runs.sweep_in_background("run_t", start)
    names = [c[0] for c in calls]
    assert names == ["runs.sweep", "actions.mark_unknown", "tasks.mark_abandoned", "runs.settle",
                     "tasks.recover_authorisations", "tasks.dispatch_next"]
    assert ("tasks.mark_abandoned", TASK_ID) in calls


async def test_nothing_abandoned_marks_no_task(recorder) -> None:
    calls, _, run_doc, _ = recorder
    run_doc["task_id"] = TASK_ID
    await routes_runs.sweep_in_background("run_t", start)
    assert [c[0] for c in calls] == ["runs.sweep", "runs.has_abandoned", "runs.settle",
                                     "tasks.recover_authorisations", "tasks.dispatch_next"]


async def test_a_worker_that_died_before_its_action_still_fails_the_task(recorder) -> None:
    # admitted, then the worker died before the gate inserted the action: the sweep abandons
    # the admission but holds no action; the task must still end failed (V38, D43).
    calls, _, run_doc, abandoned = recorder
    run_doc["task_id"] = TASK_ID
    abandoned["any"] = True
    await routes_runs.sweep_in_background("run_t", start)
    assert [c[0] for c in calls] == ["runs.sweep", "runs.has_abandoned", "tasks.mark_abandoned", "runs.settle",
                                     "tasks.recover_authorisations", "tasks.dispatch_next"]
    assert ("tasks.mark_abandoned", TASK_ID) in calls


async def test_a_step_not_on_main_yet_does_not_stop_the_rest(recorder, monkeypatch) -> None:
    calls, held, _, _ = recorder
    held.append({"action_id": "act_q", "status": "queued"})

    async def not_yet(action_id, error):
        raise NotImplementedError("actions.mark_failed (A09)")

    monkeypatch.setattr(dxp.actions, "mark_failed", not_yet)
    await routes_runs.sweep_in_background("run_t", start)
    assert [c[0] for c in calls] == ["runs.sweep", "runs.settle", "tasks.recover_authorisations", "tasks.dispatch_next"]


async def test_sweeping_many_runs_recovers_and_dispatches_once(recorder) -> None:
    calls, _, _, _ = recorder
    await routes_runs.sweep_runs_in_background(["run_a", "run_b"], start)
    assert [c[0] for c in calls] == ["runs.sweep", "runs.settle", "runs.sweep", "runs.settle",
                                     "tasks.recover_authorisations", "tasks.dispatch_next"]
