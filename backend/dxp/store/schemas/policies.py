"""`policies` validator (AD-18, NFR15, V7).

A policy document: `{ _id: "<policy_id>@v<version>", policy_id, version, status:
draft | active | retired, applies_to: [action kind], requires: { quote_found,
supported, min_confidence, claim_checks }, text, author, approved_by, created_at }`.

`requires` accepts only those four keys (AD-18); `text` is a description and is
never executed. A claim policy (`claim_performed_or_results`, `claim_planned`,
`claim_preclinical`) names its claim check in `requires.claim_checks`.
"""

from __future__ import annotations

from ._common import (
    ALL_KINDS,
    ANY_STRING,
    CLAIM_KINDS,
    DATE,
    POLICY_STATUSES,
    PRINCIPAL_PATTERN,
    STRING,
    array_of,
    document,
    enum,
    nullable,
    pattern,
    versioned_id_expr,
)

REQUIRES = document(
    [],
    {
        "quote_found": {"bsonType": "bool"},
        "supported": {"bsonType": "bool"},
        "min_confidence": {"bsonType": "number", "minimum": 0, "maximum": 1},
        "claim_checks": array_of(enum(CLAIM_KINDS), min_items=1, unique=True),
    },
    closed=True,
)
REQUIRES["minProperties"] = 1

JSON_SCHEMA = document(
    ["_id", "policy_id", "version", "status", "applies_to", "requires", "text", "author", "created_at"],
    {
        "_id": pattern("^[a-z0-9][a-z0-9_-]*@v[1-9][0-9]*$"),
        "policy_id": pattern(PRINCIPAL_PATTERN),
        "version": {"bsonType": ["int", "long"], "minimum": 1},
        "status": enum(POLICY_STATUSES),
        "applies_to": array_of(enum(ALL_KINDS), min_items=1, unique=True),
        "requires": REQUIRES,
        "text": STRING,
        "author": STRING,
        "approved_by": nullable(ANY_STRING),
        "created_at": DATE,
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA, "$expr": versioned_id_expr("policy_id")}
