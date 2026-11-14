"""Shared building blocks for the `$jsonSchema` validators (A03, AD-18).

Only the subset of JSON Schema that MongoDB's `$jsonSchema` supports is used:
`bsonType`, `enum`, `required`, `properties`, `additionalProperties`, `items`,
`minItems`, `maxItems`, `uniqueItems`, `pattern`, `minLength`, `minimum`,
`maximum`, `anyOf`, `oneOf`, `allOf` and `not`. There is no `const`, `$ref`
or `format` in MongoDB, so single values are written as one-item enums.

The enums here are the AD-14 action kinds, destinations and statuses. They are
the vocabulary the validators enforce; the gate (A06) judges the same words.
"""

from __future__ import annotations

from typing import Any

Schema = dict[str, Any]

# --- Action kinds (AD-14, AD-18). `decide_proposal` is superseded (V8) and
# granted to no one, so it is not in any list a grant may carry.
MACHINE_KINDS = [
    "search_source",
    "file_proposal",
    "file_related_evidence",
    "notify_slack",
    "generate_briefing",
    "generate_avatar_video",
]
SEED_KINDS = ["apply_value"]
HUMAN_KINDS = [
    "decide_report",
    "authorise_task",
    "create_memory",
    "correct_memory",
    "revoke_memory",
    "review_value",
    "resolve_notification",
    "revert_report",  # V48, AD-31: seeded on sam@v1 from the start
    "answer_question",  # V70: granted to sam by a new grant version (sam@v2), never in place
]
# The two media kinds are machine kinds that only the Reviewer requests, on
# demand, under `sam@v1` (V29).
MEDIA_KINDS = ["generate_briefing", "generate_avatar_video"]
AGENT_GRANT_KINDS = MACHINE_KINDS
PERSON_GRANT_KINDS = HUMAN_KINDS + MEDIA_KINDS
TASK_GRANT_KINDS = ["search_source", "file_related_evidence"]
ALL_KINDS = MACHINE_KINDS + SEED_KINDS + HUMAN_KINDS

# External kinds use the AD-20 statuses; DxP-state kinds use queued | done | failed.
EXTERNAL_KINDS = ["notify_slack", "search_source", "generate_briefing", "generate_avatar_video"]
DXP_STATE_KINDS = [k for k in ALL_KINDS if k not in EXTERNAL_KINDS]

DESTINATIONS = [
    "ledger",
    "slack:#all-mango-db-hackathon",
    "source:clinicaltrials.gov",
    "tts:elevenlabs",
    "video:heygen",
]
TASK_GRANT_DESTINATIONS = ["source:clinicaltrials.gov", "ledger"]

CHECKS = ["grant_active", "team_scope", "destination_action", "evidence_checks", "run_authorised"]
CLAIM_KINDS = ["claim_performed_or_results", "claim_planned", "claim_preclinical"]

GRANT_STATUSES = ["active", "revoked", "expired"]
POLICY_STATUSES = ["draft", "active", "retired"]

# --- Identifier patterns (AD-3, Consistency Conventions).
HEX16 = "[0-9a-f]{16}"
PRINCIPAL_PATTERN = "^[a-z0-9][a-z0-9_-]*$"
SHA256_HEX = "^[0-9a-f]{64}$"
DATE_TEXT = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"


def one_of_values(*values: Any) -> Schema:
    """A single allowed value (MongoDB has no `const`)."""
    return {"enum": list(values)}


def nullable(schema: Schema) -> Schema:
    """Allow `null` beside the given schema."""
    return {"anyOf": [{"bsonType": "null"}, schema]}


STRING: Schema = {"bsonType": "string", "minLength": 1}
ANY_STRING: Schema = {"bsonType": "string"}
INT: Schema = {"bsonType": ["int", "long"]}
NUMBER: Schema = {"bsonType": "number"}
BOOL: Schema = {"bsonType": "bool"}
DATE: Schema = {"bsonType": "date"}
OBJECT: Schema = {"bsonType": "object"}
ARRAY: Schema = {"bsonType": "array"}


def pattern(regex: str) -> Schema:
    return {"bsonType": "string", "pattern": regex}


def enum(values: list[str]) -> Schema:
    return {"bsonType": "string", "enum": list(values)}


def array_of(items: Schema, *, min_items: int | None = None, unique: bool = False) -> Schema:
    schema: Schema = {"bsonType": "array", "items": items}
    if min_items is not None:
        schema["minItems"] = min_items
    if unique:
        schema["uniqueItems"] = True
    return schema


def document(required: list[str], properties: dict[str, Schema], *, closed: bool = False) -> Schema:
    """An object schema. `closed=True` rejects keys not listed (AD-18 `requires`)."""
    schema: Schema = {"bsonType": "object", "required": list(required), "properties": dict(properties)}
    if closed:
        schema["additionalProperties"] = False
    return schema


# The AD-17 stamp. Only `kind` and `principal` are always present: a seed stamp
# is `{ kind: seed, principal: seed, run_id: null }` and nothing more (D19).
STAMP: Schema = document(
    ["kind", "principal"],
    {
        "kind": enum(["run", "reviewer", "seed"]),
        "principal": STRING,
        "run_id": nullable(STRING),
        "agent": nullable(STRING),
        "initiated_by": nullable(STRING),
        "grant_id": nullable(STRING),
        "grant_version": nullable(INT),
        "policy_set_version": nullable(STRING),
    },
)


def versioned_id_expr(id_field: str) -> dict[str, Any]:
    """`$expr`: `_id` equals `<id_field>@v<version>` (grants, policies, memories)."""
    return {"$eq": ["$_id", {"$concat": [f"${id_field}", "@v", {"$toString": "$version"}]}]}
