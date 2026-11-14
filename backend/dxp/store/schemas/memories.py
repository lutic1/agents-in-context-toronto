"""`memories` validator (AD-28, V6).

One document per version: `{ _id: "<memory_id>@v<version>", memory_id, version,
team_id, author, source: { decision_id, report_id }, text, tags, status: active |
corrected | revoked, supersedes, decision_id, created_at }`. Version 1 supersedes
nothing; a later version supersedes `<memory_id>@v<n>`. Text is never edited in
place: correcting inserts a new version.
"""

from __future__ import annotations

from ._common import DATE, STRING, document, enum, nullable, pattern, versioned_id_expr

MEMORY_REF = "^mem_[0-9a-f]{16}@v[1-9][0-9]*$"

FIRST = document(
    ["version", "supersedes"],
    {"version": {"bsonType": ["int", "long"], "enum": [1]}, "supersedes": {"bsonType": "null"}},
)
LATER = document(
    ["version", "supersedes"],
    {"version": {"bsonType": ["int", "long"], "minimum": 2}, "supersedes": pattern(MEMORY_REF)},
)

JSON_SCHEMA = {
    **document(
        [
            "_id",
            "memory_id",
            "version",
            "team_id",
            "author",
            "source",
            "text",
            "tags",
            "status",
            "supersedes",
            "decision_id",
            "created_at",
        ],
        {
            "_id": pattern(MEMORY_REF),
            "memory_id": pattern("^mem_[0-9a-f]{16}$"),
            "version": {"bsonType": ["int", "long"], "minimum": 1},
            "team_id": STRING,
            "author": STRING,
            "source": document(
                ["decision_id", "report_id"],
                {"decision_id": pattern("^dec_[0-9a-f]{16}$"), "report_id": nullable(STRING)},
            ),
            "text": STRING,
            "tags": document([], {"assay": nullable(STRING), "claim_kind": nullable(STRING)}),
            "status": enum(["active", "corrected", "revoked"]),
            "supersedes": nullable(pattern(MEMORY_REF)),
            "decision_id": pattern("^dec_[0-9a-f]{16}$"),
            "embedding": {"bsonType": "array"},
            "created_at": DATE,
        },
    ),
    "oneOf": [FIRST, LATER],
}

VALIDATOR = {"$jsonSchema": JSON_SCHEMA, "$expr": versioned_id_expr("memory_id")}
