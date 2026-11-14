"""Task grants (AD-18, AD-29, V8, V38). A24.

`issue_task_grant()` is the only runtime grant writer. After an allowed `authorise_task`
Decision, inside `tasks.authorise()`'s one transaction, it inserts `task-<hex>@v1`:

- kind `agent`, principal `dxp-curator`, `key_hash: null`, `granted_by` the authorising Reviewer,
  `acting_for`, `team_id` and `scope` (`scope_id`, `diagnostic_ids`) copied from the agent
  grant `lbdx` (latest version), `startable_by` the Reviewer;
- actions `search_source` and `file_related_evidence` only, destinations
  `source:clinicaltrials.gov` and `ledger` only, `limits.max_results: 5`;
- `task_id`, `expires_at` exactly one hour after `created_at`, `status: active`.

It is inserted if absent (`_id` `task-<hex>@v1`), so a retry or a recovery writes nothing new.
A grant is never edited in place (AD-18); the early expiry on a revert is A26's next version.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from dxp import store
from dxp.api.models import Decision, Grant, Task

AGENT_GRANT = "lbdx"
TASK_PRINCIPAL = "dxp-curator"
TASK_GRANT_KIND = "agent"  # AD-18, ruled by Luis: the task grant authorises the agent dxp-curator
TASK_ACTIONS = ["search_source", "file_related_evidence"]
TASK_DESTINATIONS = ["source:clinicaltrials.gov", "ledger"]
TASK_MAX_RESULTS = 5
TASK_GRANT_LIFETIME = timedelta(hours=1)


def task_grant_id(task_id: str) -> str:
    """`task-<the 16 hex characters of task_id>` (AD-3)."""
    if not task_id.startswith("task_"):
        raise ValueError(f"not a task ID: {task_id!r}")
    return "task-" + task_id[len("task_") :]


def _plain(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        data = value.model_dump()
    else:
        data = dict(value)
    data.setdefault("_id", data.get("id"))
    return data


def build_task_grant(
    task: dict[str, Any], decision: dict[str, Any], template: dict[str, Any] | None, created_at: datetime
) -> dict[str, Any]:
    """The `task-<hex>@v1` document (pure; AD-18)."""
    template = template or {}
    scope = template.get("scope") or {}
    granted_by = decision.get("initiated_by") or (decision.get("stamp") or {}).get("principal")
    grant_id = task_grant_id(task["_id"])
    created_at = created_at.replace(microsecond=(created_at.microsecond // 1000) * 1000)
    return {
        "_id": f"{grant_id}@v1",
        "grant_id": grant_id,
        "version": 1,
        "principal": template.get("principal") or TASK_PRINCIPAL,
        "principal_name": template.get("principal_name") or TASK_PRINCIPAL,
        "kind": TASK_GRANT_KIND,
        "key_hash": None,
        "acting_for": template.get("acting_for"),
        "granted_by": granted_by,
        "startable_by": [granted_by] if granted_by else [],
        "team_id": template.get("team_id"),
        "team_name": template.get("team_name"),
        "scope": {"diagnostic_ids": list(scope.get("diagnostic_ids") or []), "scope_id": scope.get("scope_id")},
        "destinations": list(TASK_DESTINATIONS),
        "actions": list(TASK_ACTIONS),
        "limits": {"max_results": TASK_MAX_RESULTS},
        "task_id": task["_id"],
        "report_id": task.get("report_id"),
        "decision_id": decision["_id"],
        "expires_at": created_at + TASK_GRANT_LIFETIME,
        "status": "active",
        "created_at": created_at,
    }


def grant_model(doc: dict[str, Any]) -> Grant:
    return Grant.model_validate({**doc, "id": doc["_id"]})


async def issue_task_grant(task: Task, decision: Decision, session: Any | None = None) -> Grant:
    """The only runtime grant writer: task-<hex>@v1 after an allowed authorise_task,
    inside tasks.authorise()'s one transaction (V38)."""
    task_doc = _plain(task)
    decision_doc = _plain(decision)
    if decision_doc.get("kind") != "authorise_task" or decision_doc.get("outcome") != "allowed":
        raise ValueError("a task grant is issued only after an allowed authorise_task Decision")
    grants = store.get_db()["grants"]
    template = await grants.find_one({"grant_id": AGENT_GRANT}, sort=[("version", -1)], session=session)
    if template is None:
        # The agent grant is seeded (A03); without it, copy the Reviewer grant's Team and scope.
        template = await grants.find_one(
            {"grant_id": decision_doc.get("grant_id")}, sort=[("version", -1)], session=session
        )
        template = {**(template or {}), "principal": TASK_PRINCIPAL, "principal_name": TASK_PRINCIPAL}
    doc = build_task_grant(task_doc, decision_doc, template, datetime.now(UTC))
    # Look first: inside a transaction a duplicate-key error would abort the whole transaction.
    stored = await grants.find_one({"_id": doc["_id"]}, session=session)
    if stored is not None:
        return grant_model(stored)
    try:
        await grants.insert_one(doc, session=session)
    except DuplicateKeyError:
        stored = await grants.find_one({"_id": doc["_id"]}, session=session)
        return grant_model(stored)
    return grant_model(doc)
