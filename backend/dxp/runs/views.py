"""Read-time Run views (AD-14, AD-21), A07+A11.

`in_flight` is the count of `admitted` admissions, and `counts.allowed`, `counts.blocked` and
`counts.unknown` are read from `decisions` and `actions` at request time, so they always agree
with the audit. The other counts are the pipeline's (A10).
"""

from __future__ import annotations

from typing import Any

from dxp import store
from dxp.api.models import Run
from dxp.runs.common import ADMISSIONS, load_run, run_model, runs_collection


async def _group_count(collection: str, match: dict[str, Any], key: Any = "$run_id") -> dict[Any, int]:
    """{ group key: count }; a compound key { run_id, outcome } becomes the tuple (run_id, outcome)."""
    pipeline = [{"$match": match}, {"$group": {"_id": key, "n": {"$sum": 1}}}]
    cursor = await store.collection(collection).aggregate(pipeline)
    counts: dict[Any, int] = {}
    async for row in cursor:
        group = row["_id"]
        if isinstance(group, dict):
            group = (group.get("run_id"), group.get("outcome"))
        counts[group] = int(row["n"])
    return counts


async def read_time_fields(run_ids: list[str]) -> dict[str, tuple[int, dict[str, int]]]:
    """{ run_id: (in_flight, { allowed, blocked, unknown }) } for the given runs."""
    if not run_ids:
        return {}
    in_flight = await _group_count(ADMISSIONS, {"run_id": {"$in": run_ids}, "status": "admitted"})
    outcomes = await _group_count(
        "decisions", {"run_id": {"$in": run_ids}}, key={"run_id": "$run_id", "outcome": "$outcome"}
    )
    unknown = await _group_count("actions", {"run_id": {"$in": run_ids}, "status": "unknown"})
    return {
        run_id: (
            in_flight.get(run_id, 0),
            {
                "allowed": outcomes.get((run_id, "allowed"), 0),
                "blocked": outcomes.get((run_id, "blocked"), 0),
                "unknown": unknown.get(run_id, 0),
            },
        )
        for run_id in run_ids
    }


async def view(doc: dict[str, Any]) -> Run:
    fields = await read_time_fields([doc["_id"]])
    in_flight, counts = fields.get(doc["_id"], (0, {}))
    return run_model(doc, in_flight=in_flight, counts=counts)


async def get_run(run_id: str) -> Run:
    """The run with its read-time fields; 404 in the error shape if unknown."""
    return await view(await load_run(run_id))


async def list_runs(limit: int = 50) -> list[Run]:
    """The most recent runs first."""
    docs = await runs_collection().find({}).sort([("started_at", -1), ("_id", -1)]).limit(limit).to_list(length=limit)
    fields = await read_time_fields([doc["_id"] for doc in docs])
    return [run_model(doc, *fields.get(doc["_id"], (0, {}))) for doc in docs]
