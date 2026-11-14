"""`policy_sets` validator (AD-18, D6).

`{ _id: policy_set_version, members: ["<policy_id>@v<n>", ...], created_at }`,
inserted if absent the first time a set is used; `policy_set_version` is
`derive("ps_", *sorted members)`.
"""

from __future__ import annotations

from ._common import DATE, HEX16, array_of, document, pattern

JSON_SCHEMA = document(
    ["_id", "members", "created_at"],
    {
        "_id": pattern(f"^ps_{HEX16}$"),
        "members": array_of(pattern("^[a-z0-9][a-z0-9_-]*@v[1-9][0-9]*$"), unique=True),
        "created_at": DATE,
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
