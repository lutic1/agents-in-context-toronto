"""Cancel a report's follow-up task on revert (AD-31, V48). A26.

`cancel_for_report(report, decision)`, called by the revert route after `reports.revert()`:

- `authorised` or `queued` -> `cancelled` by a conditional update (`task_status_changed`), then
  `gate.grant_expiry.expire_task_grant()` inserts the task grant's next version, `expired`
  (check 1 then blocks every later step of the task). A retry finds the task `cancelled` and
  only makes sure the grant expiry was written (insert-if-absent).
- `running` (dispatch won the race): `runs.stop(task.run_id)`, the normal stop.
- `done`, `failed`, `blocked` or `stopped`: left as it is; its findings stay pending.

None when the report has no task. It changes no other task and no other grant.
"""

from __future__ import annotations

import importlib
from typing import Any

from pydantic import BaseModel

from dxp import runs, store
from dxp.api.models import Decision, Report, Task
from dxp.gate.grant_expiry import expire_task_grant

ta = importlib.import_module("dxp.tasks.authorise")

CANCELLABLE = ("authorised", "queued")


def _plain(value: Any) -> dict[str, Any]:
    data = value.model_dump() if isinstance(value, BaseModel) else dict(value or {})
    data.setdefault("_id", data.get("id"))
    data.setdefault("id", data.get("_id"))
    return data


async def cancel_for_report(report: Report, decision: Decision) -> Task | None:
    """authorised or queued -> cancelled (conditional) plus grant expiry; running -> runs.stop;
    done, failed, blocked or stopped left as they are. None when the report has no task."""
    report_doc = _plain(report)
    decision_doc = _plain(decision)
    tasks = store.get_db()["tasks"]
    task_id = report_doc.get("task_id") or ((report_doc.get("approval") or {}).get("task_id"))
    task = await tasks.find_one({"_id": task_id}) if task_id else None
    if task is None:
        task = await tasks.find_one({"report_id": report_doc["_id"]})
    if task is None:
        return None

    if task.get("status") in CANCELLABLE:
        res = await tasks.update_one(
            {"_id": task["_id"], "status": {"$in": list(CANCELLABLE)}},
            {"$set": {"status": "cancelled", "cancelled_at": ta.rd.now(),
                      "cancelled_by_decision_id": decision_doc["_id"]}},
        )
        task = await tasks.find_one({"_id": task["_id"]})
        if res.modified_count:
            await store.emit_event(
                {
                    "type": "task_status_changed",
                    "dedupe_key": f"task_status_changed|{task['_id']}|cancelled",
                    "mode": "live",
                    "run_id": None,
                    "stamp": decision_doc.get("stamp"),
                    "decision_id": decision_doc["_id"],
                    "report_id": task.get("report_id"),
                    "task_id": task["_id"],
                    "status": "cancelled",
                }
            )
    if task.get("status") == "cancelled":
        await expire_task_grant(ta.task_model(task), decision)
    elif task.get("status") == "running" and task.get("run_id"):
        await runs.stop(task["run_id"])
        task = await tasks.find_one({"_id": task["_id"]})
    return ta.task_model(task)
