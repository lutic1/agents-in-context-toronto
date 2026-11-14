"""Admissions (AD-21, D22, D23, D43), finished by A07+A11. Frozen signatures: change only
through the contract keeper.

Re-exported from runs as runs.admit, runs.release, runs.sweep, runs.settle, runs.finish.

- One admission per action, unique on (run_id, item_key), with a 10-minute lease.
- `admit` guards the run on `status: running` and inserts the admission in one transaction:
  the write on the run (`$inc admitting`) conflicts with a concurrent stop, so nothing is
  admitted after the stop.
- `release` is conditional on `admitted`, so a second release does nothing.
- `sweep` marks expired admissions `abandoned` and returns the actions they held; it changes
  no action (the background task in api/routes_runs.py settles them, D43).
- `settle` only stops; `finish` only finishes (D23).

runs imports nothing from actions or tasks (D43, V38).
"""

from __future__ import annotations

from typing import Any

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from dxp import identity, store
from dxp.api.models import Admission
from dxp.runs.common import LEASE, admissions_collection, count_admitted, emit_status, now, runs_collection


def _admission(doc: dict[str, Any]) -> Admission:
    data = {key: value for key, value in doc.items() if key != "_id"}
    return Admission.model_validate({**data, "id": doc["_id"]})


def admission_id(run_id: str, item_key: str) -> str:
    """derive("adm_", run_id, item_key) (AD-21)."""
    return identity.derive("adm_", run_id, item_key)


async def admit(run_id: str, item_key: str) -> Admission | None:
    """In one transaction: guard the run on status running and insert the admission.
    Not admitted: None. item_key = "<source_ref or scope_id or task_id>|<kind>|<diagnostic_id or '-'>|<target>"."""
    if not run_id or not item_key:
        return None
    adm_id = admission_id(run_id, item_key)
    admissions = admissions_collection()

    existing = await admissions.find_one({"_id": adm_id})
    if existing is not None:
        # One admission per action (D22): a repeat finds it while it is still admitted.
        return _admission(existing) if existing.get("status") == "admitted" else None

    at = now()
    doc = {
        "_id": adm_id,
        "run_id": run_id,
        "item_key": item_key,
        "status": "admitted",
        "admitted_at": at,
        "expires_at": at + LEASE,
        "released_at": None,
    }

    async def guarded_insert(session: Any) -> bool:
        guard = await runs_collection().update_one(
            {"_id": run_id, "status": "running"},
            {"$inc": {"admitting": 1}, "$set": {"progress_at": at}},
            session=session,
        )
        if guard.matched_count == 0:
            return False
        await admissions.insert_one(dict(doc), session=session)
        return True

    try:
        async with store.get_client().start_session() as session:
            admitted = await session.with_transaction(guarded_insert)
    except DuplicateKeyError:
        stored = await admissions.find_one({"_id": adm_id})
        return _admission(stored) if stored and stored.get("status") == "admitted" else None

    if not admitted:
        await runs_collection().update_one({"_id": run_id}, {"$inc": {"counts.not_admitted": 1}})
        return None
    return _admission(doc)


async def release(admission_id: str) -> None:
    """admitted -> released, conditional; a second release does nothing. Then settle."""
    at = now()
    doc = await admissions_collection().find_one_and_update(
        {"_id": admission_id, "status": "admitted"},
        {"$set": {"status": "released", "released_at": at}},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        return
    await runs_collection().update_one({"_id": doc["run_id"]}, {"$set": {"progress_at": at}})
    await settle(doc["run_id"])
    return


async def sweep(run_id: str) -> list[dict[str, str]]:
    """Mark expired admitted admissions abandoned; return [{ action_id, status }] they held.
    Changes no action (D43)."""
    at = now()
    admissions = admissions_collection()
    expired = await admissions.find(
        {"run_id": run_id, "status": "admitted", "expires_at": {"$lt": at}}, {"_id": 1}
    ).to_list(length=None)
    held: list[dict[str, str]] = []
    for adm in expired:
        changed = await admissions.update_one(
            {"_id": adm["_id"], "status": "admitted"},
            {"$set": {"status": "abandoned", "abandoned_at": at}},
        )
        if changed.modified_count != 1:
            continue  # released or swept by another worker in the meantime
        async for action in store.collection("actions").find({"admission_id": adm["_id"]}, {"status": 1}):
            held.append({"action_id": action["_id"], "status": action["status"], "admission_id": adm["_id"]})
    return held


async def settle(run_id: str) -> None:
    """Only stops (D23): stopping -> stopped once no admitted admission remains."""
    if await count_admitted(run_id):
        return
    doc = await runs_collection().find_one_and_update(
        {"_id": run_id, "status": "stopping"},
        {"$set": {"status": "stopped", "stopped_at": now()}},
        return_document=ReturnDocument.AFTER,
    )
    if doc is not None:
        await emit_status(doc, "stopped")
    return


async def finish(run_id: str) -> None:
    """running -> done once no admitted admission remains; called by the pipeline after the last item."""
    if await count_admitted(run_id):
        return
    at = now()
    doc = await runs_collection().find_one_and_update(
        {"_id": run_id, "status": "running"},
        {"$set": {"status": "done", "finished_at": at, "progress_at": at}},
        return_document=ReturnDocument.AFTER,
    )
    if doc is not None:
        await emit_status(doc, "done")
        return
    # Stopped while the last item finished: settle applies instead (AD-21).
    await settle(run_id)
    return
