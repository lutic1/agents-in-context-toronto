"""`source_versions` validator (AD-25, V40).

Immutable: one document per fetched version, insert-if-absent on
`derive("sv_", source_ref, last_update_post_date, content_hash)`.
`raw_text` is stored but never returned by the API.
"""

from __future__ import annotations

from ._common import DATE, STRING, array_of, document, nullable, pattern

JSON_SCHEMA = document(
    ["_id", "source_ref", "last_update_post_date", "content_hash", "raw_text", "evidence_text", "fetched_at"],
    {
        "_id": pattern("^sv_[0-9a-f]{16}$"),
        "source_ref": pattern("^[a-z_.]+:.+$"),
        "last_update_post_date": nullable({"bsonType": ["string", "date"]}),
        "content_hash": pattern("^[0-9a-f]{16}$"),
        "raw_text": {"bsonType": "string"},
        "evidence_text": {"bsonType": "string"},
        "overall_status": nullable({"bsonType": "string"}),
        "has_results": nullable({"bsonType": "bool"}),
        "interventions": array_of({"bsonType": "object"}),
        "previous_version_id": nullable(pattern("^sv_[0-9a-f]{16}$")),
        "run_id": nullable(STRING),
        "fetched_at": DATE,
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
