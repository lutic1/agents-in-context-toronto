"""`media` validator (AD-30, V29): the on-demand HeyGen avatar video of a report."""

from __future__ import annotations

from ._common import DATE, STRING, document, enum, nullable, pattern

JSON_SCHEMA = document(
    ["_id", "report_id", "kind", "provider", "status", "decision_id", "created_at"],
    {
        "_id": pattern("^media_[0-9a-f]{16}$"),
        "report_id": pattern("^rep_[0-9a-f]{16}$"),
        "kind": enum(["avatar_video"]),
        "provider": enum(["heygen"]),
        "provider_video_id": nullable(STRING),
        "status": enum(["rendering", "ready", "unavailable"]),
        "video_url": nullable(STRING),
        "script_hash": nullable(STRING),
        "decision_id": pattern("^dec_[0-9a-f]{16}$"),
        "created_at": DATE,
        "checked_at": nullable(DATE),
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
