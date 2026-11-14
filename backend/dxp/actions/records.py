"""The `actions` documents A09 writes, and the conditional updates that move them (AD-20, D24).

Every status change is one `update_one` conditional on the current status, so a slow
worker never overwrites a later state (a swept `unknown` or a Reviewer's resolution), and
each change that matched emits one `action_status_changed` event (AD-10).

A09 writes only `actions` (and, through the gate, `decisions`). It reads `reports`,
`proposals` and `grants` to build a message or a Reviewer context, and never writes them.
Nothing here imports `memory`, `retrieval` or `reports` (AD-28).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

ACTIONS = "actions"
REPORTS = "reports"
PROPOSALS = "proposals"
GRANTS = "grants"


def get_db() -> Any:
    """The one database (`DXP_DB`). Tests replace this with an in-memory fake."""
    from dxp import store

    return store.get_db()


async def emit_event(event: dict[str, Any]) -> int:
    """Through `store.emit_event`, the only writer of `events`. Tests replace this."""
    from dxp import store

    return await store.emit_event(event)


def now() -> datetime:
    return datetime.now(UTC)


async def get(action_id: str) -> dict[str, Any] | None:
    return await get_db()[ACTIONS].find_one({"_id": action_id})


async def insert_if_absent(doc: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Save the action before anything is sent. A repeat finds the stored document."""
    try:
        await get_db()[ACTIONS].insert_one(doc)
        return doc, True
    except DuplicateKeyError:
        stored = await get(doc["_id"])
        if stored is None:  # pragma: no cover - a duplicate key means it exists
            raise
        return stored, False


async def transition(action_id: str, from_status: str, to_status: str, fields: dict[str, Any] | None = None) -> bool:
    """`from_status` -> `to_status`, conditional on the current status; emits on a change."""
    update = {"status": to_status, **(fields or {})}
    result = await get_db()[ACTIONS].update_one({"_id": action_id, "status": from_status}, {"$set": update})
    if not result.modified_count:
        return False
    doc = await get(action_id) or {}
    await emit_event(
        {
            "type": "action_status_changed",
            # One event per status an action reaches: a repeat emits nothing new.
            "dedupe_key": f"action_status_changed|{action_id}|{to_status}",
            "mode": doc.get("mode"),
            "run_id": doc.get("run_id"),
            "stamp": doc.get("stamp"),
            "decision_id": doc.get("decision_id"),
            "action_id": action_id,
            "status": to_status,
            "report_id": (doc.get("target") or {}).get("report_id"),
            "diagnostic_id": (doc.get("target") or {}).get("diagnostic_id"),
        }
    )
    return True


async def get_report(report_id: str) -> dict[str, Any] | None:
    return await get_db()[REPORTS].find_one({"_id": report_id})


async def get_proposals(proposal_ids: list[str]) -> list[dict[str, Any]]:
    if not proposal_ids:
        return []
    found = await get_db()[PROPOSALS].find({"_id": {"$in": list(proposal_ids)}}).to_list(length=None)
    order = {pid: i for i, pid in enumerate(proposal_ids)}
    return sorted(found, key=lambda p: order.get(p["_id"], len(order)))


async def latest_grant_of(principal_id: str) -> dict[str, Any] | None:
    """The latest version of the person grant held by `principal_id`, whatever its status
    (check 1 judges the status)."""
    cursor = get_db()[GRANTS].find({"principal": principal_id, "kind": "person"}).sort("version", -1).limit(1)
    found = await cursor.to_list(length=1)
    return found[0] if found else None
