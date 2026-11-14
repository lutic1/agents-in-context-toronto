"""`proposals` validator (AD-1, AD-4, AD-27, AD-31, V43, V48).

A proposed change, filed only by the ledger after an allowed gate decision.
`op: add` is every ordinary proposal; `op: remove` is only a reverse proposal
filed by a revert (`derive("p_", proposal_id, "revert")`), and it must name
`reverts_proposal_id`. A scope-collection update has `diagnostic_id: null` and
`target.scope_id` (V43).
"""

from __future__ import annotations

from ._common import STAMP, STRING, document, enum, nullable, pattern

PROPOSAL_ID = "^p_[0-9a-f]{16}$"

ADD = document(
    ["op"],
    {"op": enum(["add"]), "reverts_proposal_id": {"bsonType": "null"}},
)
REMOVE = document(
    ["op", "reverts_proposal_id"],
    {"op": enum(["remove"]), "reverts_proposal_id": pattern(PROPOSAL_ID)},
)

JSON_SCHEMA = {
    **document(
        ["_id", "op", "status", "mode", "decision_id", "stamp"],
        {
            "_id": pattern(PROPOSAL_ID),
            "op": enum(["add", "remove"]),
            "reverts_proposal_id": nullable(pattern(PROPOSAL_ID)),
            "diagnostic_id": nullable(pattern("^dx_[0-9a-f]{16}$")),
            "target": {"bsonType": ["object", "null"]},
            "field": STRING,
            "status": enum(["pending", "applying", "applied", "rejected"]),
            "mode": enum(["live", "baseline"]),
            "run_id": nullable(STRING),
            "report_id": nullable(pattern("^rep_[0-9a-f]{16}$")),
            "action_id": nullable(pattern("^act_[0-9a-f]{16}$")),
            "decision_id": pattern("^dec_[0-9a-f]{16}$"),
            "stamp": STAMP,
            "evidence": {"bsonType": ["object", "null"]},
            "check": {"bsonType": ["object", "null"]},
        },
    ),
    "oneOf": [ADD, REMOVE],
}

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
