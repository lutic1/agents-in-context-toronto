"""`reports` validator (AD-26, AD-27, AD-29, AD-31, V26, V37, V40, V41, V45, V48).

V48: a revert moves `accepted` -> `reverting` -> `reverted` and stores `revert`;
its accepted relationships become `reverted`.

A report is the pending proposal, kept apart from accepted knowledge. Its
relationships are embedded in `related[]` (no separate collection). AD-26 is
enforced here too: a relationship label other than `related_unestablished`
needs both quotes found.
"""

from __future__ import annotations

from ._common import DATE, STAMP, STRING, array_of, document, enum, nullable, pattern

LABELS = ["supports", "contradicts", "extends", "new_question", "related_unestablished"]

QUOTE = document(
    ["source_ref", "version_id", "text", "quote_found"],
    {
        "source_ref": STRING,
        "version_id": pattern("^sv_[0-9a-f]{16}$"),
        "text": {"bsonType": "string"},
        "quote_found": {"bsonType": "bool"},
    },
)
FOUND_QUOTE = document(["quote_found"], {"quote_found": {"bsonType": "bool", "enum": [True]}})

RELATIONSHIP = {
    **document(
        ["_id", "related_ref", "label", "new_quote", "related_quote", "origin", "status"],
        {
            "_id": pattern("^rel_[0-9a-f]{16}$"),
            "related_ref": STRING,
            "related_kind": enum(["source_item", "finding"]),
            "label": enum(LABELS),
            "new_quote": QUOTE,
            "related_quote": QUOTE,
            "similarity": nullable({"bsonType": "number"}),
            "origin": pattern("^(discovery|task:task_[0-9a-f]{16})$"),
            "status": enum(["pending", "accepted", "reverted"]),
        },
    ),
    "anyOf": [
        document(["label"], {"label": enum(["related_unestablished"])}),
        document(["new_quote", "related_quote"], {"new_quote": FOUND_QUOTE, "related_quote": FOUND_QUOTE}),
    ],
}

APPROVAL = document(
    ["decision_id", "task_id", "task_step"],
    {
        "decision_id": pattern("^dec_[0-9a-f]{16}$"),
        "task_id": pattern("^task_[0-9a-f]{16}$"),
        "task_step": enum(["pending", "done", "blocked"]),
    },
)

REVERT = document(
    ["decision_id", "step"],
    {
        "decision_id": pattern("^dec_[0-9a-f]{16}$"),
        "note": STRING,
        "step": enum(["pending", "done"]),
    },
)

JSON_SCHEMA = document(
    ["_id", "run_id", "scope_id", "team_id", "source_ref", "version_id", "status", "stamp", "created_at"],
    {
        "_id": pattern("^rep_[0-9a-f]{16}$"),
        "run_id": STRING,
        "scope_id": STRING,
        "team_id": STRING,
        "source_ref": STRING,
        "version_id": pattern("^sv_[0-9a-f]{16}$"),
        "status": enum(["pending", "accepting", "accepted", "rejected", "reverting", "reverted"]),
        "revert": nullable(REVERT),
        "related": array_of(RELATIONSHIP),
        "uncertainties": array_of({"bsonType": "string"}),
        "gap": nullable({"bsonType": "string"}),
        "diagnostic_ids": array_of(STRING),
        "proposal_ids": array_of(STRING),
        "draft": {"bsonType": ["int", "long"], "enum": [1, 2]},
        "approval": nullable(APPROVAL),
        "task_id": nullable(pattern("^task_[0-9a-f]{16}$")),
        "memory_id": nullable(STRING),
        "script": nullable({"bsonType": "string"}),
        "script_hash": nullable({"bsonType": "string"}),
        "stamp": STAMP,
        "created_at": DATE,
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
