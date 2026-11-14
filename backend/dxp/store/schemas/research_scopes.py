"""`research_scopes` validator (AD-25, V1, V25, V34).

`{ _id: "scope_<slug>", name, team_id, assays: [the four exact D45 strings],
aliases (search terms only, never used to resolve a name, V34), condition,
source: "clinicaltrials.gov", cursor: { last_update_post_date, set_at,
set_by_run_id } }`. The cursor date is the ClinicalTrials.gov `YYYY-MM-DD`
text used in `AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]`; a parsed BSON date
is also accepted.

`condition_aliases` (search terms only: they widen the API condition query; the
gate and the report judge the plain `condition`) and `priority_refs` (the
explicit order the scan uses, so it shows in the audit) are optional,
seed-owned scan config. Only `discovery` (A05) moves the cursor after the seed, by a
conditional update on `version` that also increments it (seeded as 1).
"""

from __future__ import annotations

from ._common import DATE, DATE_TEXT, STRING, array_of, document, enum, nullable, pattern

CURSOR = document(
    ["last_update_post_date", "set_at", "set_by_run_id"],
    {
        "last_update_post_date": {"anyOf": [pattern(DATE_TEXT), DATE]},
        "set_at": nullable(DATE),
        "set_by_run_id": nullable(STRING),
    },
)

JSON_SCHEMA = document(
    ["_id", "name", "team_id", "assays", "condition", "source", "cursor", "version"],
    {
        "_id": pattern("^scope_[a-z0-9_]+$"),
        "name": STRING,
        "team_id": STRING,
        "assays": array_of(STRING, min_items=1, unique=True),
        "aliases": array_of(STRING, unique=True),
        "condition_aliases": array_of(STRING, unique=True),
        "priority_refs": array_of(pattern("^NCT[0-9]{8}$"), unique=True),
        "condition": STRING,
        "source": enum(["clinicaltrials.gov"]),
        "cursor": CURSOR,
        "version": {"bsonType": ["int", "long"], "minimum": 1},
        "created_at": DATE,
    },
)

VALIDATOR = {"$jsonSchema": JSON_SCHEMA}
