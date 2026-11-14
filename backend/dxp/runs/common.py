"""Shared helpers of the runs package (A07+A11): clock, collections, the run stamp and the
`run_status_changed` event.

runs imports nothing from actions, tasks, memory, retrieval or reports (D43, V38, AD-28).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from dxp import store
from dxp.api.errors import ApiError
from dxp.api.models import Run, Stamp

RUNS = "runs"
ADMISSIONS = "admissions"

#: The admission lease (AD-21) and the stall window (AD-16): both 10 minutes.
LEASE = timedelta(minutes=10)
STALL_WINDOW = timedelta(minutes=10)

ACTIVE_STATUSES = ("running", "stopping")


def now() -> datetime:
    """UTC, truncated to the millisecond MongoDB stores, so a time compared with a stored one
    means the same instant on both sides (the one-run rule orders starts by started_at)."""
    at = datetime.now(UTC)
    return at.replace(microsecond=at.microsecond - at.microsecond % 1000)


def aware(value: datetime | None) -> datetime | None:
    """Stored dates as aware UTC, whatever client read them."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def runs_collection() -> Any:
    return store.collection(RUNS)


def admissions_collection() -> Any:
    return store.collection(ADMISSIONS)


async def load_run(run_id: str, session: Any = None) -> dict[str, Any]:
    """The stored run document, or 404 in the error shape."""
    doc = await runs_collection().find_one({"_id": run_id}, session=session)
    if doc is None:
        raise ApiError(404, "run_not_found", f"No run {run_id}.")
    return doc


def stamp_of(doc: dict[str, Any]) -> Stamp:
    """AD-17 stamp of a run write: kind run, principal = the run's agent."""
    return Stamp(
        kind="run",
        run_id=doc["_id"],
        agent=doc.get("agent"),
        initiated_by=doc.get("initiated_by"),
        principal=doc.get("agent") or "unknown",
        acting_for=doc.get("acting_for"),
        grant_id=doc.get("grant_id"),
        grant_version=doc.get("grant_version"),
        model=doc.get("model"),
        prompt_version=doc.get("prompt_version"),
        policy_set_version=doc.get("policy_set_version"),
    )


def run_model(doc: dict[str, Any], in_flight: int | None = None, counts: dict[str, int] | None = None) -> Run:
    """The AD-14 Run from a stored document; `in_flight` and read-time counts when given."""
    data = {key: value for key, value in doc.items() if key != "_id"}
    data["id"] = doc["_id"]
    if in_flight is not None:
        data["in_flight"] = in_flight
    if counts:
        data["counts"] = {**(doc.get("counts") or {}), **counts}
    return Run.model_validate(data)


async def emit_status(doc: dict[str, Any], status: str, session: Any = None) -> int:
    """One `run_status_changed` event per status a run reaches, stamped with the run (AD-21)."""
    return await store.emit_event(
        "run_status_changed",
        session=session,
        dedupe_key=f"run_status_changed|{doc['_id']}|{status}",
        stamp=stamp_of(doc).model_dump(),
        run_id=doc["_id"],
        status=status,
        mode=doc.get("mode", "live"),
        task_id=doc.get("task_id"),
    )


async def count_admitted(run_id: str, session: Any = None) -> int:
    return await admissions_collection().count_documents({"run_id": run_id, "status": "admitted"}, session=session)
