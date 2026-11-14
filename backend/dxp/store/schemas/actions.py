"""`actions` validator (AD-19, AD-20, D24, D44).

External kinds (`notify_slack`, `search_source`, `generate_briefing`,
`generate_avatar_video`) move `queued | dispatching | delivered | failed |
unknown`; DxP-state kinds move `queued | done | failed`. `reconciling` is a
read-time word only and is never stored. A blocked decision creates no action,
so every action points at an allowed `decision_id`.
"""

from __future__ import annotations

from ._common import (
    DATE,
    DESTINATIONS,
    DXP_STATE_KINDS,
    EXTERNAL_KINDS,
    STAMP,
    STRING,
    document,
    enum,
    nullable,
    pattern,
)

RESOLUTION = document(
    ["outcome", "note", "decision_id", "by", "at"],
    {
        "outcome": enum(["delivered", "failed"]),
        "note": STRING,
        "decision_id": pattern("^dec_[0-9a-f]{16}$"),
        "by": STRING,
        "at": DATE,
    },
)

EXTERNAL = document(
    ["kind", "status"],
    {
        "kind": enum(EXTERNAL_KINDS),
        "status": enum(["queued", "dispatching", "delivered", "failed", "unknown"]),
    },
)
DXP_STATE = document(
    ["kind", "status"],
    {"kind": enum(DXP_STATE_KINDS), "status": enum(["queued", "done", "failed"])},
)

JSON_SCHEMA = {
    **document(
        ["_id", "decision_id", "run_id", "kind", "destination", "status", "stamp", "proposed_at"],
        {
            "_id": pattern("^act_[0-9a-f]{16}$"),
            "decision_id": pattern("^dec_[0-9a-f]{16}$"),
            "admission_id": nullable(STRING),
            "run_id": nullable(STRING),
            "kind": STRING,
            "destination": enum(DESTINATIONS),
            "target": {"bsonType": ["object", "null"]},
            "stamp": STAMP,
            "error": nullable(enum(["abandoned_before_send", "abandoned_in_flight"])),
            "result": {"bsonType": ["object", "null"]},
            "resolution": nullable(RESOLUTION),
            "proposed_at": DATE,
            "decided_at": nullable(DATE),
            "claimed_at": nullable(DATE),
            "observed_at": nullable(DATE),
        },
    ),
    "oneOf": [EXTERNAL, DXP_STATE],
}

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
