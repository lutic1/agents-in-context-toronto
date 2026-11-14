"""Task grant expiry on revert (AD-18, AD-31, V48). A26.

`expire_task_grant(task, decision)` inserts the task grant's next version with
`status: expired` and `expires_at` now. The earlier version is never edited (AD-18); check 1
reads the latest version, so every later step of the task is blocked.

Idempotent: if the latest version is already not `active` (expired by this revert, or revoked),
it is returned unchanged and nothing is written; the version `_id` is insert-if-absent, so two
concurrent calls write one version.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from dxp import store
from dxp.api.models import Decision, Grant, Task


def _plain(value: Any) -> dict[str, Any]:
    data = value.model_dump() if isinstance(value, BaseModel) else dict(value or {})
    data.setdefault("_id", data.get("id"))
    return data


def _model(doc: dict[str, Any]) -> Grant:
    return Grant.model_validate({**doc, "id": doc["_id"]})


def build_expired_version(latest: dict[str, Any], decision: dict[str, Any], at: datetime) -> dict[str, Any]:
    """The next version of a task grant, expired now (pure)."""
    version = int(latest["version"]) + 1
    at = at.replace(microsecond=(at.microsecond // 1000) * 1000)
    return {
        **{k: v for k, v in latest.items() if k != "_id"},
        "_id": f"{latest['grant_id']}@v{version}",
        "version": version,
        "status": "expired",
        "expires_at": at,
        "created_at": at,
        "expired_by_decision_id": decision.get("_id"),
    }


async def expire_task_grant(task: Task, decision: Decision) -> Grant:
    """Insert the task grant's next version, status expired, expires_at now; never edits in place."""
    task_doc = _plain(task)
    decision_doc = _plain(decision)
    grant_id = task_doc.get("grant_id")
    if not grant_id:
        raise ValueError(f"task {task_doc.get('_id')} names no grant")
    grants = store.get_db()["grants"]
    latest = await grants.find_one({"grant_id": grant_id}, sort=[("version", -1)])
    if latest is None:
        raise LookupError(f"task grant {grant_id} not found")
    if latest.get("status") != "active":
        return _model(latest)
    doc = build_expired_version(latest, decision_doc, datetime.now(UTC))
    try:
        await grants.insert_one(doc)
    except DuplicateKeyError:
        return _model(await grants.find_one({"_id": doc["_id"]}))
    return _model(doc)
