"""`tasks` validator (AD-29, V26, V38, V42).

One task per report (`derive("task_", report_id)`), run under its own grant
`task-<hex>@v1`. Status `authorised | queued | running | done | failed | blocked |
stopped | cancelled` (`cancelled` only by a revert, V48). With `task_run` off a task is inserted `authorised` and never queued.
The result always carries the query, the number of records searched and the
limit (V42); `with_posted_results` may be empty.
"""

from __future__ import annotations

from ._common import DATE, STRING, array_of, document, enum, nullable, pattern

RESULT = document(
    ["answer", "with_posted_results", "query", "searched_count", "limit"],
    {
        "answer": STRING,
        "with_posted_results": array_of(pattern("^NCT[0-9]{8}$")),
        "query": {"bsonType": ["string", "object"]},
        "searched_count": {"bsonType": ["int", "long"], "minimum": 0},
        "limit": {"bsonType": ["int", "long"], "minimum": 1, "maximum": 5},
    },
)

JSON_SCHEMA = document(
    ["_id", "report_id", "kind", "question", "params", "grant_id", "status", "authorised_by_decision_id", "created_at"],
    {
        "_id": pattern("^task_[0-9a-f]{16}$"),
        "report_id": pattern("^rep_[0-9a-f]{16}$"),
        "kind": enum(["search_related"]),
        "question": STRING,
        "params": document(["max"], {"max": {"bsonType": ["int", "long"], "minimum": 1, "maximum": 5}}),
        "grant_id": pattern("^task-[0-9a-f]{16}$"),
        "grant_version": {"bsonType": ["int", "long"], "minimum": 1},
        "status": enum(["authorised", "queued", "running", "done", "failed", "blocked", "stopped", "cancelled"]),
        "error": nullable(enum(["abandoned"])),
        "queued_at": nullable(DATE),
        "run_id": nullable(pattern("^run_[0-9a-f]{16}$")),
        "authorised_by_decision_id": pattern("^dec_[0-9a-f]{16}$"),
        "result": nullable(RESULT),
        "created_at": DATE,
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
