"""The only starter of a task's run: the start rule and its recovery (Story 10.8, AD-29, V38). A24.

`dispatch_next(start)`:

- does nothing while the backend flag `task_run` is off (V38, V46): nothing is queued then;
- takes the oldest `queued` task (by `queued_at`);
- leaves it `queued` while any other run is `running` or `stopping` (AD-16: at most one run);
- claims it by a conditional update on the task itself (`dispatched_at` unset, or unchanged
  since a dispatch older than the 10-minute stall window), so of two callers only one goes on;
- creates its run through `runs.start(<authorising Reviewer>, "task-<hex>", "task:<task_id>",
  run_id=derive("run_", task_id))`, insert-if-absent on the derived run ID;
- and only that caller calls `start(run_id)` (the API's `.spawn()` of the run function, or a
  direct call from `pipeline.run`'s `finally`).

A derived run that exists while its task is still `queued` past the stall window is started
again on the same ID; A25's conditional `queued` -> `running` lets one worker win.

Callers: the decision route after its transaction, `pipeline.run`'s `finally` (the run-finish
path), the background sweep after `runs.settle()` and the API start hook.

`mark_abandoned(task_id)` sets a task whose run's admissions were abandoned `failed`
(`error: abandoned`), conditional on `running`; it is never restarted.

Nothing here imports `tasks/run.py` (A25) and `runs` imports nothing from `tasks`.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from dxp import feature_enabled, runs, store
from dxp.api.models import Principal, Run
from dxp.identity import derive

log = logging.getLogger("dxp.tasks.dispatch")

StartRun = Callable[[str], Awaitable[Any] | Any]

TASK_RUN_FLAG = "task_run"
STALL_WINDOW = timedelta(minutes=10)  # AD-16
ACTIVE_RUN_STATUSES = ["running", "stopping"]


def run_id_for(task_id: str) -> str:
    """The one derived run ID (V38)."""
    return derive("run_", task_id)


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def _caller(task: dict[str, Any]) -> Principal:
    """The Reviewer whose approval authorised the task: the run's `initiated_by` (V38)."""
    who = task.get("authorised_by")
    database = store.get_db()
    if not who and task.get("authorised_by_decision_id"):
        decision = await database["decisions"].find_one({"_id": task["authorised_by_decision_id"]})
        who = (decision or {}).get("initiated_by")
    who = who or "sam"
    grant = await database["grants"].find_one({"principal": who, "kind": "person"}, sort=[("version", -1)])
    return Principal(
        id=who,
        name=(grant or {}).get("principal_name") or who,
        kind="person",
        actions=list((grant or {}).get("actions") or []),
    )


async def dispatch_next(start: StartRun) -> Run | None:
    """Start the oldest queued task if no run is running or stopping: runs.start on
    derive("run_", task_id), insert-if-absent; only the inserter calls start(run_id).
    Does nothing while task_run is off (V38, V46)."""
    if not feature_enabled(TASK_RUN_FLAG):
        return None
    database = store.get_db()
    task = await database["tasks"].find_one(
        {"status": "queued"}, sort=[("queued_at", 1), ("created_at", 1), ("_id", 1)]
    )
    if task is None:
        return None
    task_id = task["_id"]
    run_id = run_id_for(task_id)
    now = datetime.now(UTC)

    dispatched_at = _aware(task.get("dispatched_at"))
    stalled = dispatched_at is not None and dispatched_at <= now - STALL_WINDOW
    if dispatched_at is not None and not stalled:
        return None  # its worker is starting; A25 moves it to running

    active = await database["runs"].find_one({"status": {"$in": ACTIVE_RUN_STATUSES}}, {"_id": 1})
    # The task's own derived run may be active without a worker (stalled, or a start that failed
    # after its run was inserted): start the worker again on the same run ID.
    if active is not None and active["_id"] != run_id:
        return None  # another run is active: the task stays queued (AD-16)

    claim = {"_id": task_id, "status": "queued", "dispatched_at": task.get("dispatched_at")}
    res = await database["tasks"].update_one(
        claim, {"$set": {"run_id": run_id, "dispatched_at": now}, "$inc": {"dispatch_count": 1}}
    )
    if not res.modified_count:
        return None  # another caller claimed it

    try:
        run = await runs.start(await _caller(task), task["grant_id"], f"task:{task_id}", run_id=run_id)
        started = start(run_id)
        if inspect.isawaitable(started):
            await started
    except Exception:
        log.exception("could not start the run of task %s", task_id)
        await database["tasks"].update_one(
            {"_id": task_id, "status": "queued", "dispatched_at": now},
            {"$set": {"dispatched_at": dispatched_at}},
        )
        return None
    return run


async def mark_abandoned(task_id: str) -> None:
    """running -> failed (error: abandoned), conditional; never restarted."""
    database = store.get_db()
    now = datetime.now(UTC)
    res = await database["tasks"].update_one(
        {"_id": task_id, "status": "running"},
        {"$set": {"status": "failed", "error": "abandoned", "finished_at": now}},
    )
    if not res.modified_count:
        return
    task = await database["tasks"].find_one({"_id": task_id})
    await store.emit_event(
        {
            "type": "task_status_changed",
            "dedupe_key": f"task_status_changed|{task_id}|failed",
            "mode": "live",
            "run_id": (task or {}).get("run_id"),
            "stamp": {"kind": "run", "principal": "dxp-curator", "run_id": (task or {}).get("run_id")},
            "report_id": (task or {}).get("report_id"),
            "task_id": task_id,
            "status": "failed",
        }
    )
