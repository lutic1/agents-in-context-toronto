"""`grants` validator (AD-18, D16, Story 9.2).

A grant document: `{ _id: "<grant_id>@v<version>", grant_id, version, principal,
kind, key_hash | null, acting_for, granted_by, startable_by, team_id, scope,
destinations, actions, limits | null, task_id | null, expires_at, status,
created_at }`.

Exactly one of four shapes must match:

* seed grant: principal `seed`, kind `seed`, scope `{ all: true }`, action
  `apply_value`, destination `ledger` (D16). `scope.all` is accepted nowhere else.
* agent grant (`lbdx@v1`): kind `agent`, only machine kinds, a Diagnostic scope.
* person grant (`sam@v1`): kind `person`, only human kinds plus the two on-demand
  media kinds (V29), a Diagnostic scope.
* task grant (`task-<hex>@v1`, AD-29): written only by `gate.grants.issue_task_grant()`
  (A24), never seeded; `key_hash: null`, actions within `search_source` and
  `file_related_evidence`, destinations within `source:clinicaltrials.gov` and
  `ledger`, `limits.max_results` at most 5, and (in `$expr`) an expiry no later
  than one hour after `created_at`. Its early expiry (V48, A26) is the next
  version, `task-<hex>@v2`, `status: expired`, `expires_at` = now, which validates. AD-18 writes its kind as `agent`; the plan's
  contract list says `task`, so both are accepted for a task grant, and only for one.

`$expr` also ties `_id` to `grant_id@v<version>`.
"""

from __future__ import annotations

from ._common import (
    AGENT_GRANT_KINDS,
    ALL_KINDS,
    DATE,
    DESTINATIONS,
    GRANT_STATUSES,
    HEX16,
    PERSON_GRANT_KINDS,
    PRINCIPAL_PATTERN,
    SEED_KINDS,
    SHA256_HEX,
    STRING,
    TASK_GRANT_DESTINATIONS,
    TASK_GRANT_KINDS,
    array_of,
    document,
    enum,
    nullable,
    pattern,
    versioned_id_expr,
)

TASK_GRANT_MAX_SECONDS = 3600
TASK_GRANT_MAX_RESULTS = 5

NOT_TASK_ID = "^(?!task-)[a-z0-9][a-z0-9_-]*$"

DIAGNOSTIC_SCOPE = document(
    ["diagnostic_ids", "scope_id"],
    {
        "diagnostic_ids": array_of(pattern(f"^dx_{HEX16}$"), min_items=1, unique=True),
        "scope_id": pattern("^scope_[a-z0-9_]+$"),
    },
    closed=True,  # so `{ all: true }` (or anything else) cannot ride along
)

ALL_SCOPE = document(["all"], {"all": {"bsonType": "bool", "enum": [True]}}, closed=True)


def _actions(kinds: list[str]) -> dict:
    return array_of(enum(kinds), min_items=1, unique=True)


def _destinations(values: list[str]) -> dict:
    return array_of(enum(values), min_items=1, unique=True)


SEED_GRANT = document(
    ["principal", "kind", "scope", "actions", "destinations"],
    {
        "grant_id": pattern(NOT_TASK_ID),
        "principal": enum(["seed"]),
        "kind": enum(["seed"]),
        "scope": ALL_SCOPE,
        "actions": _actions(SEED_KINDS),
        "destinations": _destinations(["ledger"]),
        "task_id": {"bsonType": "null"},
    },
)

AGENT_GRANT = document(
    ["kind", "scope", "actions", "team_id"],
    {
        "grant_id": pattern(NOT_TASK_ID),
        "kind": enum(["agent"]),
        "scope": DIAGNOSTIC_SCOPE,
        "actions": _actions(AGENT_GRANT_KINDS),
        "team_id": STRING,
        "task_id": {"bsonType": "null"},
    },
)

PERSON_GRANT = document(
    ["kind", "scope", "actions", "team_id"],
    {
        "grant_id": pattern(NOT_TASK_ID),
        "kind": enum(["person"]),
        "scope": DIAGNOSTIC_SCOPE,
        "actions": _actions(PERSON_GRANT_KINDS),
        "team_id": STRING,
        "task_id": {"bsonType": "null"},
    },
)

TASK_GRANT = document(
    ["kind", "scope", "actions", "destinations", "team_id", "task_id", "limits", "key_hash", "granted_by"],
    {
        "_id": pattern(f"^task-{HEX16}@v[1-9][0-9]*$"),
        "grant_id": pattern(f"^task-{HEX16}$"),
        "kind": enum(["agent", "task"]),
        "key_hash": {"bsonType": "null"},
        "scope": DIAGNOSTIC_SCOPE,
        "actions": _actions(TASK_GRANT_KINDS),
        "destinations": _destinations(TASK_GRANT_DESTINATIONS),
        "team_id": STRING,
        "task_id": pattern(f"^task_{HEX16}$"),
        "granted_by": STRING,
        "limits": document(
            ["max_results"],
            {"max_results": {"bsonType": ["int", "long"], "minimum": 1, "maximum": TASK_GRANT_MAX_RESULTS}},
            closed=True,
        ),
    },
)

JSON_SCHEMA = {
    "bsonType": "object",
    "required": [
        "_id",
        "grant_id",
        "version",
        "principal",
        "kind",
        "key_hash",
        "startable_by",
        "team_id",
        "scope",
        "destinations",
        "actions",
        "expires_at",
        "status",
        "created_at",
    ],
    "properties": {
        "_id": pattern("^[a-z0-9][a-z0-9_-]*@v[1-9][0-9]*$"),
        "grant_id": pattern(PRINCIPAL_PATTERN),
        "version": {"bsonType": ["int", "long"], "minimum": 1},
        "principal": pattern(PRINCIPAL_PATTERN),
        "principal_name": nullable(STRING),
        "kind": enum(["agent", "person", "seed", "task"]),
        "key_hash": nullable(pattern(SHA256_HEX)),
        "acting_for": nullable(STRING),
        "granted_by": nullable(STRING),
        "startable_by": array_of(pattern(PRINCIPAL_PATTERN), unique=True),
        "team_id": nullable(STRING),
        "team_name": nullable(STRING),
        "scope": {"bsonType": "object"},
        "destinations": _destinations(DESTINATIONS),
        "actions": _actions(ALL_KINDS),
        "limits": nullable(document(["max_results"], {"max_results": {"bsonType": ["int", "long"], "minimum": 1}})),
        "task_id": nullable(STRING),
        "expires_at": DATE,
        "status": enum(GRANT_STATUSES),
        "created_at": DATE,
    },
    "oneOf": [SEED_GRANT, AGENT_GRANT, PERSON_GRANT, TASK_GRANT],
}

EXPR = {
    "$and": [
        versioned_id_expr("grant_id"),
        {
            "$or": [
                {"$ne": [{"$substrCP": ["$grant_id", 0, 5]}, "task-"]},
                {
                    "$and": [
                        {"$gte": ["$expires_at", "$created_at"]},
                        {
                            "$lte": [
                                {"$subtract": ["$expires_at", "$created_at"]},
                                TASK_GRANT_MAX_SECONDS * 1000,
                            ]
                        },
                        {"$eq": ["$grant_id", {"$concat": ["task-", {"$substrCP": ["$task_id", 5, 16]}]}]},
                    ]
                },
            ]
        },
    ]
}

VALIDATOR = {"$jsonSchema": JSON_SCHEMA, "$expr": EXPR}
