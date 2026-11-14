"""`runs` validator (AD-17, D4, D23, V38).

Two identities (`agent`, `initiated_by`), the grant pinned at start, the policy
set pinned at start, and the run status. A task run carries its `task_id`.
"""

from __future__ import annotations

from ._common import DATE, STRING, document, enum, nullable, pattern

JSON_SCHEMA = document(
    [
        "_id",
        "agent",
        "initiated_by",
        "grant_id",
        "grant_version",
        "policy_set_version",
        "team_id",
        "set",
        "kind",
        "status",
        "started_at",
    ],
    {
        "_id": pattern("^run_[A-Za-z0-9_-]+$"),
        "agent": STRING,
        "initiated_by": STRING,
        "grant_id": STRING,
        "grant_version": {"bsonType": ["int", "long"], "minimum": 1},
        "policy_set_version": pattern("^ps_[0-9a-f]{16}$"),
        "team_id": STRING,
        "set": pattern("^(discover|nct:NCT[0-9]{8}|task:task_[0-9a-f]{16})$"),
        "kind": enum(["discover", "items", "task"]),
        "scope_id": nullable(STRING),
        "task_id": nullable(pattern("^task_[0-9a-f]{16}$")),
        "status": enum(["running", "stopping", "stopped", "done", "failed"]),
        "in_flight": {"bsonType": ["int", "long"], "minimum": 0},
        "counts": {"bsonType": "object"},
        "started_at": DATE,
        "stopping_at": nullable(DATE),
        "stopped_at": nullable(DATE),
        "finished_at": nullable(DATE),
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
