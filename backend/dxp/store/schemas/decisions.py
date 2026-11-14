"""`decisions` validator (AD-19, D5, D19, D21, V7, V14).

Every gate evaluation, allowed or blocked, is one decision. `kind` is free text
on purpose: an attempt at an unknown or superseded kind must still be recorded
as a blocked Decision (check 3), so the validator cannot refuse it. A blocked
decision names its `failed_check` and has no `action_id`.
"""

from __future__ import annotations

from ._common import CHECKS, CLAIM_KINDS, DATE, STAMP, STRING, array_of, document, enum, nullable, pattern

CHECK = document(
    ["check"],
    {
        "check": enum(CHECKS),
        "passed": {"anyOf": [{"bsonType": "bool"}, {"enum": ["n/a"]}]},
        "detail": nullable({"bsonType": ["string", "object"]}),
    },
)

CLAIM = document(
    ["claim_kind", "text", "passed"],
    {"claim_kind": enum(CLAIM_KINDS), "text": STRING, "passed": {"bsonType": "bool"}},
)

ALLOWED = document(["outcome"], {"outcome": enum(["allowed"]), "failed_check": {"bsonType": "null"}})
BLOCKED = document(
    ["outcome", "failed_check"],
    {"outcome": enum(["blocked"]), "failed_check": enum(CHECKS), "action_id": {"bsonType": "null"}},
)

JSON_SCHEMA = {
    **document(
        [
            "_id",
            "run_id",
            "agent",
            "initiated_by",
            "stamp",
            "kind",
            "destination",
            "checks",
            "grant_id",
            "grant_version",
            "policy_set_version",
            "outcome",
            "decided_at",
        ],
        {
            "_id": pattern("^dec_[0-9a-f]{16}$"),
            "run_id": nullable(STRING),
            "agent": nullable(STRING),
            "initiated_by": STRING,
            "stamp": STAMP,
            "cause": nullable({"bsonType": "object"}),
            "request_id": nullable(STRING),
            "kind": STRING,
            "inputs": {"bsonType": ["object", "null"]},
            "evidence_ref": {"bsonType": ["object", "null"]},
            "destination": nullable({"bsonType": "string"}),
            "target": {"bsonType": ["object", "null"]},
            "claims": array_of(CLAIM),
            "checks": array_of(CHECK, min_items=1),
            "failed_check": nullable(enum(CHECKS)),
            "grant_id": STRING,
            "grant_version": nullable({"bsonType": ["int", "long"], "minimum": 1}),
            "run_grant_version": nullable({"bsonType": ["int", "long"], "minimum": 1}),
            "policy_set_version": pattern("^ps_[0-9a-f]{16}$"),
            "outcome": enum(["allowed", "blocked"]),
            "action_id": nullable(pattern("^act_[0-9a-f]{16}$")),
            "seq": nullable({"bsonType": ["int", "long"]}),
            "decided_at": DATE,
            "authorised_by": {"bsonType": ["object", "null"]},
        },
    ),
    "oneOf": [ALLOWED, BLOCKED],
}

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
