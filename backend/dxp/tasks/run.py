"""Follow-up task execution (Story 10.9, stretch, V9, V26, V27, V33, V38, V39, V42). A25.

`tasks.run(task_id)` is reached only through the task's own `task:` run, which
`tasks.dispatch_next()` (A24) started on `derive("run_", task_id)`; A10 hands that run here.
Nothing runs while the backend flag `task_run` is off. Frozen signature (A01).

1. **Claim.** `queued` -> `running` by a conditional update on the task. No match means another
   worker owns it (or it was cancelled): exit without acting.
2. **Search.** `discovery.run_scan` on the report's research scope, under the run's context (the
   task grant), capped at the task's `params.max` (at most 5) and never moving the discover
   cursor. The scan holds its own admission and passes its own `search_source` gate.
3. **Answer.** The trials among the records searched that have posted results answer the task's
   `question`. A capped search cannot prove that none exists, so an empty answer is "No matching
   results found among the records searched". The result always carries the query, the number of
   records searched and the limit (V42).
4. **File.** Each finding goes through `reports.add_related()` as pending related evidence on the
   report, never accepted knowledge (V27), one admission per finding and its own
   `file_related_evidence` gate (grant, scope, destination, limit, run authorisation). A sixth
   finding or one outside the scope is blocked by the gate and recorded in `result.blocked`. An
   allowed filing's action is settled only through `gate.mark_action` (V65).
5. **End.** `running` -> `done | failed | blocked | stopped`, by a conditional update on
   `running`. A stop of the task's run (`runs.stop`) is seen before each step: the next
   admission is refused and the task ends `stopped`.

The `tasks` module is the only writer of `tasks`; this file writes nothing in `runs`, `actions`
or `reports` itself.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from dxp import feature_enabled, gate, runs, store
from dxp.api.models import Task
from dxp.identity import derive

log = logging.getLogger("dxp.tasks.run")

TASK_RUN_FLAG = "task_run"
MAX_RESULTS = 5
NO_RESULTS = "No matching results found among the records searched"
FILE_KIND = "file_related_evidence"
SOURCE_PREFIX = "clinicaltrials.gov:"
TERMINAL = ("done", "failed", "blocked", "stopped")


def _now() -> datetime:
    return datetime.now(UTC)


def _model(doc: dict[str, Any]) -> Task:
    return Task.model_validate({**doc, "id": doc["_id"]})


def nct_of(ref: str) -> str:
    """`clinicaltrials.gov:NCT01234567` -> `NCT01234567`."""
    return ref.split(":", 1)[1] if ":" in ref else ref


def limit_of(task: dict[str, Any]) -> int:
    """The task's own limit, never above the task grant's 5."""
    try:
        wanted = int((task.get("params") or {}).get("max") or MAX_RESULTS)
    except (TypeError, ValueError):
        wanted = MAX_RESULTS
    return max(1, min(wanted, MAX_RESULTS))


def answer_for(question: str, with_results: list[str], searched: int) -> str:
    if not with_results:
        return NO_RESULTS
    names = ", ".join(with_results)
    return f"{len(with_results)} of the {searched} records searched have posted results: {names}."


def file_item_key(task_id: str, ref: str) -> str:
    """One admission per finding (D22): `<source_ref>|file_related_evidence|-|<task_id>|<ref>`."""
    return f"{ref}|{FILE_KIND}|-|{task_id}|{ref}"


# ---------------------------------------------------------------------------
# Steps (module functions, so tests replace the network-facing ones)
# ---------------------------------------------------------------------------


async def _context(run_id: str) -> Any:
    """The run's context under the worker key (AD-17): the task grant is the run's grant."""
    return await runs.context(run_id, os.environ.get("DXP_AGENT_KEY", "").strip())


async def _search(scope_id: str, ctx: Any, limit: int) -> Any:
    """Gated search_source through discovery (A05): capped, the discover cursor never moves."""
    from dxp import discovery

    return await discovery.run_scan(scope_id, ctx, max_results=limit, advance_cursor=False)


async def _file(report_id: str, ref: str, ctx: Any) -> list[Any]:
    """Gated file_related_evidence through reports (A19+A20): pending, never accepted."""
    from dxp import reports

    return await reports.add_related(report_id, [ref], ctx)


async def _run_status(run_id: str) -> str | None:
    doc = await store.get_db()["runs"].find_one({"_id": run_id}, {"status": 1})
    return (doc or {}).get("status")


async def _emit_status(task: dict[str, Any], status: str, ctx: Any = None) -> None:
    stamp = ctx.stamp.model_dump() if ctx is not None else {
        "kind": "run", "principal": "dxp-curator", "run_id": task.get("run_id"),
    }
    await store.emit_event(
        {
            "type": "task_status_changed",
            "dedupe_key": f"task_status_changed|{task['_id']}|{status}",
            "mode": getattr(ctx, "mode", None) or "live",
            "run_id": task.get("run_id"),
            "stamp": stamp,
            "decision_id": task.get("authorised_by_decision_id"),
            "report_id": task.get("report_id"),
            "task_id": task["_id"],
            "status": status,
        }
    )


async def _end(task: dict[str, Any], status: str, result: dict[str, Any] | None, ctx: Any) -> dict[str, Any]:
    """`running` -> a terminal status, conditional on `running` (a stop or revert in between wins)."""
    tasks = store.get_db()["tasks"]
    fields: dict[str, Any] = {"status": status, "finished_at": _now()}
    if result is not None:
        fields["result"] = result
    res = await tasks.update_one({"_id": task["_id"], "status": "running"}, {"$set": fields})
    if res.modified_count:
        await _emit_status(task, status, ctx)
    return await tasks.find_one({"_id": task["_id"]}) or {**task, **fields}


# ---------------------------------------------------------------------------
# The task
# ---------------------------------------------------------------------------


async def run(task_id: str) -> Task:
    """queued -> running (conditional), gated search_source, file_related_evidence, at most 5."""
    tasks = store.get_db()["tasks"]
    task = await tasks.find_one({"_id": task_id})
    if task is None:
        raise LookupError(f"task {task_id} not found")
    if not feature_enabled(TASK_RUN_FLAG):
        return _model(task)  # V38, V46: nothing runs while task_run is off

    run_id = task.get("run_id") or derive("run_", task_id)
    claimed = await tasks.update_one(
        {"_id": task_id, "status": "queued"},
        {"$set": {"status": "running", "run_id": run_id, "started_at": _now()}},
    )
    if not claimed.modified_count:
        return _model(await tasks.find_one({"_id": task_id}) or task)  # another worker owns it
    task = await tasks.find_one({"_id": task_id}) or {**task, "status": "running", "run_id": run_id}

    ctx = None
    try:
        ctx = await _context(run_id)
        await _emit_status(task, "running", ctx)
        task = await _execute(task, run_id, ctx)
    except Exception as exc:
        log.exception("task %s failed: %s", task_id, type(exc).__name__)
        task = await _end(task, "failed", None, ctx)
    return _model(task)


async def _execute(task: dict[str, Any], run_id: str, ctx: Any) -> dict[str, Any]:
    db = store.get_db()
    task_id = task["_id"]
    limit = limit_of(task)
    report = await db["reports"].find_one({"_id": task["report_id"]}, {"scope_id": 1}) or {}
    scope_id = report.get("scope_id")
    if not scope_id:
        raise LookupError(f"report {task['report_id']} names no research scope")

    if await _run_status(run_id) != "running":
        return await _end(task, "stopped", None, ctx)

    outcome = await _search(scope_id, ctx, limit)
    query = dict(outcome.query or {})
    query.update({"question": task.get("question"), "params": task.get("params") or {}})
    refs = list(outcome.source_refs or [])
    base = {"query": query, "searched_count": len(refs), "limit": limit}

    if outcome.status == "blocked":
        result = {**base, "answer": "The search was blocked by the gate; nothing was searched.",
                  "with_posted_results": [], "searched_count": 0,
                  "blocked": [{"step": "search_source", "decision_id": outcome.decision_id}]}
        return await _end(task, "blocked", result, ctx)
    if outcome.status != "done":  # not admitted: the run is stopping or stopped
        status = "stopped" if await _run_status(run_id) != "running" else "failed"
        return await _end(task, status, None, ctx)

    items = {d["_id"]: d async for d in db["source_items"].find({"_id": {"$in": refs}})}
    found = [r for r in refs if (items.get(r) or {}).get("has_results") is True]

    filed: list[str] = []
    blocked: list[dict[str, Any]] = []
    stopped = False
    for ref in found:  # never cut here: a finding past the limit is the gate's to block
        if await _run_status(run_id) != "running":
            stopped = True
            break
        admission = await runs.admit(run_id, file_item_key(task_id, ref))
        if admission is None:
            stopped = await _run_status(run_id) != "running"
            blocked.append({"step": FILE_KIND, "source_ref": ref, "reason": "not admitted"})
            if stopped:
                break
            continue
        try:
            actx = ctx.model_copy(update={"admission_id": admission.id})
            for decision in await _file(task["report_id"], ref, actx):
                if decision.outcome == "allowed":
                    filed.append(ref)
                    if decision.action_id:
                        await gate.mark_action(decision.action_id, "done", {"report_id": task["report_id"], "source_ref": ref})
                else:
                    blocked.append({"step": FILE_KIND, "source_ref": ref, "decision_id": decision.id,
                                    "failed_check": getattr(decision, "failed_check", None)})
        finally:
            await runs.release(admission.id)

    with_results = [nct_of(r) for r in filed]
    result = {
        **base,
        "answer": answer_for(task.get("question") or "", with_results, len(refs)),
        "with_posted_results": with_results,
        "found_with_posted_results": [nct_of(r) for r in found],
        "blocked": blocked,
    }
    if stopped:
        return await _end(task, "stopped", result, ctx)
    return await _end(task, "blocked" if blocked else "done", result, ctx)
