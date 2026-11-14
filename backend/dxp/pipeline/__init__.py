"""The run function (Story 1.7, AD-12, AD-16, AD-21, V38, V45). Owned by A10.

`pipeline.run(run_id)` is what `modal_app` wraps (3600-second timeout) and what the API
starts with `.spawn()`. In order:

1. `runs.context(run_id, DXP_AGENT_KEY)`: the worker acts with the agent's key and is refused
   unless it resolves to the run's agent (AD-17).
2. `ledger.recover_applying()` (AD-1, D26).
3. One LangGraph run (`pipeline.graph`): the items of the run's `set`, each through
   `pipeline.item.process` (extract, check, retrieve, remember, relate, draft, gate, file,
   notify). A `task:` set is handed to `tasks.run` (A25), only with the backend flag
   `task_run` on.
4. `runs.finish(run_id)` after the last item (`running` -> `done` once no admission is
   held), then `runs.settle(run_id)` (`stopping` -> `stopped` after a stop). The run is
   `failed` only on an error the pipeline cannot recover from (D23); an item's error is a
   failure line and the run goes on.
5. `finally`, after every run however it ended: `tasks.recover_authorisations()` (V45), then
   `tasks.dispatch_next(start)` (V38), which does nothing while `task_run` is off; when it
   starts a queued task, `start` runs it next in this same call.

The run never generates a briefing or renders an avatar (V29).
"""

from __future__ import annotations

import logging
from typing import Any

from dxp import discovery, feature_enabled, ledger, runs, tasks
from dxp.pipeline import config, graph, item, progress

__all__ = ["run"]

log = logging.getLogger("dxp.pipeline")

SOURCE = "clinicaltrials.gov"


class RunFailed(Exception):
    """An error the run cannot recover from (D23). The message is a code."""


def source_ref_for(nct_id: str) -> str:
    return f"{SOURCE}:{nct_id}"


async def _list_items(run_doc: dict[str, Any], info: item.RunInfo) -> list[str]:
    set_ = str(run_doc.get("set") or "")
    if set_ == "discover":
        if not info.scope_id:
            raise RunFailed("discover_without_scope")
        refs = list(await discovery.scan(info.scope_id, info.ctx))
    elif set_.startswith("nct:"):
        refs = [source_ref_for(set_.split(":", 1)[1])]
    elif set_.startswith("task:"):
        await _hand_off_task(run_doc, set_.split(":", 1)[1], info)
        refs = []
    else:
        raise RunFailed("unknown_set")
    seen: set[str] = set()
    ordered = [r for r in refs if not (r in seen or seen.add(r))]  # the scan's order, anchor first
    await info.tracker.total(len(ordered))
    return ordered


async def _hand_off_task(run_doc: dict[str, Any], task_id: str, info: item.RunInfo) -> None:
    """A task's run is executed by A25's `tasks.run`, never while `task_run` is off (V38)."""
    task_id = run_doc.get("task_id") or task_id
    if not feature_enabled("task_run"):
        await info.tracker.item_failed(f"task:{task_id}", "task_run is off")
        return
    await tasks.run(task_id)


async def _start_next(run_id: str) -> None:
    """How `tasks.dispatch_next` starts a queued task at the end of a run: in this same call."""
    await run(run_id)


async def run(run_id: str) -> None:
    """Scan, extract, retrieve, relate, remember, draft, gate, file, notify; runs.finish after the
    last item; hands a task: run to tasks.run; calls tasks.dispatch_next in its finally."""
    tracker = progress.Progress(run_id)
    ctx = None
    try:
        ctx = await runs.context(run_id, config.agent_key())
        await ledger.recover_applying()
        run_doc = await progress.load_run(run_id)
        if run_doc is None:
            raise RunFailed("run_missing")
        info = item.RunInfo(
            run_id=run_id,
            ctx=ctx,
            scope_id=run_doc.get("scope_id"),
            team_id=run_doc.get("team_id"),
            seeded_names=await progress.seeded_names(),
            tracker=tracker,
        )

        async def list_items() -> list[str]:
            return await _list_items(run_doc, info)

        async def process_item(ref: str) -> dict[str, Any]:
            return (await item.process(ref, info)).as_dict()

        await graph.invoke(run_id, list_items, process_item)
        await tracker.recount()
        await runs.finish(run_id)
        await runs.settle(run_id)
    except Exception as exc:  # noqa: BLE001 - D23: an unrecoverable error fails the run
        code = str(exc) if isinstance(exc, RunFailed) else type(exc).__name__
        log.error("run failed run=%s error=%s", run_id, code)
        try:
            await tracker.mark_failed(code, getattr(ctx, "stamp", None))
        except Exception:  # noqa: BLE001
            log.error("could not mark run %s failed", run_id)
    finally:
        try:
            await tasks.recover_authorisations()
        except Exception as exc:  # noqa: BLE001
            log.error("recover_authorisations failed after run=%s error=%s", run_id, type(exc).__name__)
        try:
            await tasks.dispatch_next(_start_next)
        except Exception as exc:  # noqa: BLE001
            log.error("dispatch_next failed after run=%s error=%s", run_id, type(exc).__name__)
