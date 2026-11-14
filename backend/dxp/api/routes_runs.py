"""Runs and stop (Stories 9.1, 9.5). The background sweep lives here (D43, V38, V45). Finished by A07+A11.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.

- The caller is resolved server-side from `X-DxP-Key` (D17): 401 for a missing or unknown key;
  the seed key is refused (command line only, AD-17). No body field confers permission.
- `POST /runs` refuses any `task:` set with 403 and creates nothing: a task's run starts only
  through `tasks.dispatch_next()` (V38).
- `GET /runs`, `GET /runs/<run_id>` and `POST /runs/<run_id>/stop` never call Slack: they start
  the sweep in the background and return current state (D24).
- The background sweep: `runs.sweep`, then `actions.mark_unknown` for a held `dispatching`
  action and `actions.mark_failed` for a held `queued` one, then `tasks.mark_abandoned` for a
  task's run, then `runs.settle`, then `tasks.recover_authorisations()` and finally
  `tasks.dispatch_next()` (D43, V38, V45).
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query, Request  # noqa: F401

from dxp import actions, ledger, runs, tasks
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.runs.common import ACTIVE_STATUSES, load_run

log = logging.getLogger("dxp.api.runs")

router = APIRouter()
OWNER = "A07+A11"
KEY_HEADER = "X-DxP-Key"


async def caller(request: Request) -> m.Principal:
    """The calling principal, from `X-DxP-Key` only (AD-18, D17)."""
    key = request.headers.get(KEY_HEADER)
    if not key:
        raise ApiError(401, "missing_key", f"{KEY_HEADER} is required.")
    principal = await auth.resolve_actor(key)
    if principal.kind == "seed":
        raise ApiError(403, "seed_key_not_accepted", "The seed key is for the command line only.")
    return principal


def _start_function(request: Request) -> Callable[[str], Any]:
    start = getattr(request.app.state, "start_run", None)
    if start is None:
        def refuse(run_id: str) -> Any:
            raise RuntimeError("No run function was passed to create_app().")

        return refuse
    return start


async def _call_start(start: Callable[[str], Any], run_id: str) -> None:
    """`.spawn()` may block (Modal): run it off the event loop; await it if it is async."""
    result = await asyncio.to_thread(start, run_id)
    if inspect.isawaitable(result):
        await result


async def _quietly(label: str, call: Callable[[], Awaitable[Any]]) -> Any:
    """One step of the background sweep: a failing step is logged and the next one still runs."""
    try:
        return await call()
    except NotImplementedError:
        log.info("sweep: %s is not on main yet; skipped", label)
    except Exception:
        log.exception("sweep: %s failed", label)
    return None


async def sweep_in_background(run_id: str, start: Callable[[str], Any], *, recover: bool = True) -> None:
    """The AD-21 background sweep for one run, in the order D43, V38 and V45 set."""
    held = await _quietly("runs.sweep", lambda: runs.sweep(run_id)) or []
    for item in held:
        action_id, status = item["action_id"], item["status"]
        if status == "dispatching":
            await _quietly("actions.mark_unknown", lambda a=action_id: actions.mark_unknown(a, "abandoned_in_flight"))
        elif status == "queued":
            await _quietly("actions.mark_failed", lambda a=action_id: actions.mark_failed(a, "abandoned_before_send"))
    run = await _quietly("load run", lambda: load_run(run_id))
    task_id = (run or {}).get("task_id")
    if task_id and (held or await _quietly("runs.has_abandoned", lambda: runs.has_abandoned(run_id))):
        # The abandoned-task rule (V38, D43): a task run with any abandoned admission, even one
        # whose worker died before its action existed, sets the task failed (error: abandoned),
        # conditional on running and never restarted.
        await _quietly("tasks.mark_abandoned", lambda: tasks.mark_abandoned(task_id))
    await _quietly("runs.settle", lambda: runs.settle(run_id))
    if recover:
        await recover_and_dispatch(start)


async def recover_and_dispatch(start: Callable[[str], Any]) -> None:
    """After settle: complete an interrupted authorisation (V45), then start a queued task (V38)."""
    await _quietly("tasks.recover_authorisations", tasks.recover_authorisations)
    await _quietly("tasks.dispatch_next", lambda: tasks.dispatch_next(start))


async def sweep_runs_in_background(run_ids: list[str], start: Callable[[str], Any]) -> None:
    for run_id in run_ids:
        await sweep_in_background(run_id, start, recover=False)
    await recover_and_dispatch(start)


@router.post("/runs", response_model=m.Run, tags=["runs"])
async def create_run(body: m.RunCreate, request: Request) -> m.Run:
    """set is discover or nct:<NCT ID>; a task: set is refused with 403 (V38). 409 while a run is
    running or stopping."""
    principal = await caller(request)
    if body.set.startswith("task:"):
        raise ApiError(403, "task_set_refused", "A task's run starts only through tasks.dispatch_next() (V38); no run was created.")
    runs.parse_set(body.set)  # 400 before anything else is read
    await ledger.recover_applying()  # at every run start (AD-1, D26)
    run = await runs.start(principal, body.grant_id, body.set)
    try:
        await _call_start(_start_function(request), run.id)
    except Exception:
        log.exception("POST /runs: the run function did not start %s", run.id)
        await runs.fail(run.id, "the run function could not be started")
        raise ApiError(503, "run_not_started", f"{run.id} could not be started; it is marked failed.") from None
    return await runs.get_run(run.id)


@router.get("/runs", response_model=m.RunList, tags=["runs"])
async def list_runs(request: Request, background: BackgroundTasks) -> m.RunList:
    await caller(request)
    items = await runs.list_runs()
    active = [run.id for run in items if run.status in ACTIVE_STATUSES]
    background.add_task(sweep_runs_in_background, active, _start_function(request))
    return m.RunList(items=items, next=None)


@router.get("/runs/{run_id}", response_model=m.Run, tags=["runs"])
async def get_run(run_id: str, request: Request, background: BackgroundTasks) -> m.Run:
    await caller(request)
    run = await runs.get_run(run_id)
    background.add_task(sweep_in_background, run_id, _start_function(request))
    return run


@router.post("/runs/{run_id}/stop", response_model=m.Run, tags=["runs"])
async def stop_run(run_id: str, request: Request, background: BackgroundTasks) -> m.Run:
    principal = await caller(request)
    doc = await load_run(run_id)
    if principal.id != doc.get("initiated_by"):
        from dxp.gate import policy_sets

        grant = await policy_sets.current_grant(doc["grant_id"])
        if grant is None or principal.id not in grant.startable_by:
            raise ApiError(403, "not_allowed_to_stop", f"{principal.id} may not stop {run_id}.")
    run = await runs.stop(run_id)
    background.add_task(sweep_in_background, run_id, _start_function(request))
    return run
