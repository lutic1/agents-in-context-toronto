"""`admissions` validator (AD-21, D7, D22). Unique on `(run_id, item_key)` (A01's index)."""

from __future__ import annotations

from ._common import DATE, STRING, document, enum, nullable, pattern

JSON_SCHEMA = document(
    ["_id", "run_id", "item_key", "status", "admitted_at", "expires_at"],
    {
        "_id": pattern("^adm_[0-9a-f]{16}$"),
        "run_id": STRING,
        "item_key": STRING,
        "status": enum(["admitted", "released", "abandoned"]),
        "admitted_at": DATE,
        "expires_at": DATE,
        "released_at": nullable(DATE),
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
