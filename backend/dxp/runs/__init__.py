"""Runs and identity (AD-16, AD-17, AD-21), finished by A07+A11. Frozen signatures: change only
through the contract keeper.

- `start` creates a run under the latest version of a grant, for a caller in its
  `startable_by`, with two identities (`initiated_by` the caller, `agent` the grant's
  principal), the grant version and the policy set pinned. At most one run is `running` or
  `stopping` (409), unless it has stalled (no progress for 10 minutes, AD-16).
- A `task:` set needs the derived run ID, `derive("run_", task_id)`, and is inserted if absent;
  only `tasks.dispatch_next()` (A24) passes it (V38). `start_if_absent` also says whether this
  call inserted the run, so only the inserter starts the worker.
- `context` refuses a worker key that does not resolve to the run's agent; `stamp` is the only
  stamp maker for run writes; `stop` moves `running` to `stopping`, then settles.

runs imports nothing from actions or tasks (D43, V38), nor from memory, retrieval or reports (AD-28).
"""

from __future__ import annotations

import re
import secrets
from typing import Any

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from dxp import identity, store
from dxp.api import auth
from dxp.api.errors import ApiError
from dxp.api.models import Grant, Principal, Run, RunContext, RunCounts, Stamp
from dxp.gate import policy_sets
from dxp.runs.admissions import admit, finish, release, settle, sweep
from dxp.runs.common import (
    ACTIVE_STATUSES,
    STALL_WINDOW,
    aware,
    emit_status,
    load_run,
    now,
    run_model,
    runs_collection,
    stamp_of,
)
from dxp.runs.views import get_run, list_runs

__all__ = [
    "admit",
    "context",
    "fail",
    "finish",
    "get_run",
    "list_runs",
    "parse_set",
    "record_progress",
    "release",
    "settle",
    "stamp",
    "start",
    "start_if_absent",
    "stop",
    "sweep",
]

SET_PATTERN = re.compile(r"^(?:(?P<discover>discover)|nct:(?P<nct>NCT\d{8})|task:(?P<task>task_[0-9a-f]{16}))$")
SOURCE = "clinicaltrials.gov"


def parse_set(value: str) -> tuple[str, str | None, str | None]:
    """`(kind, nct_id, task_id)` for `discover`, `nct:<NCT ID>` or `task:<task_id>`; 400 otherwise."""
    match = SET_PATTERN.match(value or "")
    if match is None:
        raise ApiError(400, "invalid_set", "set must be discover, nct:<NCT ID> or task:<task_id>.")
    if match.group("discover"):
        return "discover", None, None
    if match.group("nct"):
        return "items", match.group("nct"), None
    return "task", None, match.group("task")


def _llm_identity() -> tuple[str | None, str | None]:
    """The model and prompt version from `llm` (A08), when it publishes them (AD-17)."""
    try:
        from dxp import llm
    except Exception:  # noqa: BLE001 - llm is optional for the run identity
        return None, None
    models = getattr(llm, "MODEL_IDS", None)
    model = models.get("strong") if isinstance(models, dict) else getattr(llm, "MODEL", None)
    return model, getattr(llm, "PROMPT_VERSION", None)


def _policy_set_id(policy_set: Any) -> str | None:
    """The `policy_set_version` from `current_set()` (A03: a PolicySet)."""
    if policy_set is None:
        return None
    if isinstance(policy_set, tuple):
        policy_set = policy_set[0]
    if isinstance(policy_set, str):
        return policy_set
    if isinstance(policy_set, dict):
        return policy_set.get("id") or policy_set.get("_id")
    return getattr(policy_set, "id", None)


def _grant_active(grant: Grant) -> bool:
    expires_at = aware(grant.expires_at)
    return grant.status == "active" and expires_at is not None and expires_at > now()


async def _checked_grant(caller: Principal, grant_id: str, kind: str, task_id: str | None) -> Grant:
    """AD-17 step 2: the latest version of the grant, active, unexpired, caller in startable_by."""
    grant = await policy_sets.current_grant(grant_id)
    if grant is None:
        raise ApiError(403, "grant_not_found", f"No grant {grant_id}; no run was created.")
    if not _grant_active(grant):
        raise ApiError(403, "grant_not_active", f"{grant.id} is {grant.status} or expired; no run was created.")
    if caller.id not in grant.startable_by:
        raise ApiError(403, "not_startable_by_caller", f"{caller.id} may not start runs under {grant.id}.")
    if kind == "task":
        if grant.task_id != task_id:
            raise ApiError(403, "not_the_task_grant", f"{grant.id} is not the grant of {task_id}.")
    elif grant.task_id is not None or grant.kind != "agent":
        raise ApiError(403, "not_an_agent_grant", f"{grant.id} cannot start a {kind} run.")
    if not grant.team_id:
        raise ApiError(403, "grant_has_no_team", f"{grant.id} names no Team.")
    return grant


def _active_filter(at: Any) -> dict[str, Any]:
    """Runs that count against the one-run rule: running or stopping, not stalled (AD-16)."""
    return {"status": {"$in": list(ACTIVE_STATUSES)}, "progress_at": {"$gte": at - STALL_WINDOW}}


async def _task_report_id(task_id: str) -> str | None:
    task = await store.collection("tasks").find_one({"_id": task_id}, {"report_id": 1})
    if task is None:
        raise ApiError(403, "task_not_found", f"No task {task_id}; no run was created.")
    return task.get("report_id")


async def start_if_absent(caller: Principal, grant_id: str, set: str, run_id: str | None = None) -> tuple[Run, bool]:
    """`start`, also saying whether this call inserted the run (True) or found the task's derived
    run already there (False). Only the inserter starts the worker (V38)."""
    kind, _, task_id = parse_set(set)
    if kind == "task":
        if run_id is None:
            raise ApiError(403, "task_set_refused", "A task's run starts only through tasks.dispatch_next() (V38).")
        if run_id != identity.derive("run_", task_id):
            raise ApiError(403, "task_run_id_mismatch", "A task's run ID is derive(\"run_\", task_id).")
        existing = await runs_collection().find_one({"_id": run_id})
        if existing is not None:
            return run_model(existing), False
    elif run_id is not None:
        raise ApiError(400, "run_id_not_allowed", "Only a task's run has a derived run ID.")

    grant = await _checked_grant(caller, grant_id, kind, task_id)
    report_id = await _task_report_id(task_id) if task_id else None
    policy_set_version = _policy_set_id(await policy_sets.current_set())
    model, prompt_version = _llm_identity()

    at = now()
    others = {**_active_filter(at), "_id": {"$ne": run_id}} if run_id else _active_filter(at)
    if await runs_collection().find_one(others, {"_id": 1}) is not None:
        raise ApiError(409, "run_active", "Another run is running or stopping.")

    scope_id = getattr(grant.scope, "scope_id", None)
    doc: dict[str, Any] = {
        "_id": run_id or f"run_{secrets.token_hex(8)}",
        "agent": grant.principal,
        "initiated_by": caller.id,
        "model": model,
        "prompt_version": prompt_version,
        "policy_set_version": policy_set_version,
        "acting_for": grant.acting_for,
        "grant_id": grant.grant_id,
        "grant_version": grant.version,
        "team_id": grant.team_id,
        "mode": "live",
        "source": SOURCE,
        "set": set,
        "kind": kind,
        "scope_id": scope_id,
        "task_id": task_id,
        "cause": {"task_id": task_id, "report_id": report_id} if task_id else None,
        "scan": None,
        "status": "running",
        "in_flight": 0,
        "admitting": 0,
        "counts": RunCounts().model_dump(),
        "active": [],
        "failures": [],
        "started_at": at,
        "progress_at": at,
        "stopping_at": None,
        "stopped_at": None,
        "finished_at": None,
    }
    try:
        await runs_collection().insert_one(doc)
    except DuplicateKeyError:
        if kind != "task":
            raise
        stored = await runs_collection().find_one({"_id": doc["_id"]})
        return run_model(stored), False

    # Two starts that both passed the check above: the earlier one (started_at, then _id) keeps
    # running and the later one is withdrawn before anything starts it (AD-16).
    earlier = {
        **_active_filter(at),
        "_id": {"$ne": doc["_id"]},
        "$or": [{"started_at": {"$lt": at}}, {"started_at": at, "_id": {"$lt": doc["_id"]}}],
    }
    if await runs_collection().find_one(earlier, {"_id": 1}) is not None:
        await runs_collection().delete_one({"_id": doc["_id"], "status": "running", "admitting": 0})
        raise ApiError(409, "run_active", "Another run is running or stopping.")

    await emit_status(doc, "running")
    return run_model(doc), True


async def start(caller: Principal, grant_id: str, set: str, run_id: str | None = None) -> Run:
    """Create a run under the latest version of the grant, checked against startable_by.

    set is discover, nct:<NCT ID> or task:<task_id>. run_id is passed only for a task's
    derived run ID, derive("run_", task_id), insert-if-absent (V38).
    """
    run, _ = await start_if_absent(caller, grant_id, set, run_id)
    return run


async def context(run_id: str, key: str) -> RunContext:
    """Resolve the worker key; refuse unless it resolves to the run's agent (AD-17)."""
    if not run_id:
        raise ApiError(403, "run_id_required", "Every agent write needs a run_id.")
    if not key:
        raise ApiError(401, "missing_key", "The worker key is required.")
    doc = await load_run(run_id)
    principal = await auth.resolve_actor(key)
    if principal.kind != "agent" or principal.id != doc.get("agent"):
        raise ApiError(403, "not_run_agent", f"The key does not resolve to the agent of {run_id}.")
    return RunContext(
        run_id=run_id,
        principal=principal,
        stamp=stamp_of(doc),
        grant_id=doc["grant_id"],
        grant_version=doc["grant_version"],
        run_grant_version=doc["grant_version"],
        policy_set_version=doc.get("policy_set_version"),
        mode=doc.get("mode", "live"),
    )


async def stop(run_id: str) -> Run:
    """running -> stopping (conditional), then settle. Any other status is returned unchanged."""
    at = now()
    doc = await runs_collection().find_one_and_update(
        {"_id": run_id, "status": "running"},
        {"$set": {"status": "stopping", "stopping_at": at, "progress_at": at}},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        await load_run(run_id)  # 404 for an unknown run; any other status is left as it is
    else:
        await emit_status(doc, "stopping")
    await settle(run_id)
    return await get_run(run_id)


#: The counts the pipeline (A10) owns; `not_admitted` is runs.admit's (AD-21).
PIPELINE_COUNTS = frozenset(RunCounts.model_fields) - {"not_admitted"}


async def record_progress(
    run_id: str,
    *,
    counts: dict[str, int],
    active_items: list[dict[str, str]],
    failure_lines: list[dict[str, str]],
) -> bool:
    """The pipeline's progress (A10), written only here (only Governance writes `runs`).

    Each call carries the full current values, so a repeat is harmless: `counts` keys from
    RunCounts except `not_admitted`, `active_items` [{ source_ref, step }] and `failure_lines`
    [{ source_ref, error }] (codes, never source text). Conditional on the run being `running`
    or `stopping`; returns False when it is neither (an ended run is never rewritten).
    """
    unknown = set(counts) - PIPELINE_COUNTS
    if unknown:
        raise ValueError(f"record_progress: counts not owned by the pipeline: {sorted(unknown)}")
    active = [{"source_ref": str(a["source_ref"]), "step": str(a["step"])} for a in active_items]
    failures = [{"source_ref": str(f["source_ref"]), "error": str(f["error"])} for f in failure_lines]
    update: dict[str, Any] = {f"counts.{key}": int(value) for key, value in counts.items()}
    update.update({"active": active, "failures": failures, "progress_at": now()})
    result = await runs_collection().update_one(
        {"_id": run_id, "status": {"$in": list(ACTIVE_STATUSES)}}, {"$set": update}
    )
    return result.matched_count == 1


async def fail(run_id: str, error: str) -> Run:
    """running or stopping -> failed (conditional), only for an error the pipeline cannot
    recover from (D23); emits run_status_changed. Any other status is returned unchanged."""
    at = now()
    doc = await runs_collection().find_one_and_update(
        {"_id": run_id, "status": {"$in": list(ACTIVE_STATUSES)}},
        {
            "$set": {"status": "failed", "finished_at": at, "progress_at": at},
            "$push": {"failures": {"source_ref": "-", "error": error}},
        },
        return_document=ReturnDocument.AFTER,
    )
    if doc is not None:
        await emit_status(doc, "failed")
    return await get_run(run_id)


async def stamp(run_id: str) -> Stamp:
    """The only stamp maker for run writes; kind run."""
    return stamp_of(await load_run(run_id))
