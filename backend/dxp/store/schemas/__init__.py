"""The `$jsonSchema` validators for every DxP collection that has one (A03, AD-18).

`store.ensure_indexes()` (A01) creates each collection with its validator,
`validationLevel: strict` and `validationAction: error`, so Atlas itself
rejects a malformed document, not only application code. Use
`collection_options(name)` at creation, or `apply(db)` to create the
collections that are missing and `collMod` the ones that exist.

Collections: grants, policies, policy_sets, research_scopes, runs, admissions,
decisions, actions, proposals (`op: add | remove`, V48), reports (relationships embedded as `related[]`), memories,
tasks, media and source_versions (V40).
"""

from __future__ import annotations

from typing import Any

from . import (
    actions,
    admissions,
    decisions,
    grants,
    media,
    memories,
    policies,
    policy_sets,
    proposals,
    reports,
    research_scopes,
    runs,
    source_versions,
    tasks,
)

VALIDATORS: dict[str, dict[str, Any]] = {
    "grants": grants.VALIDATOR,
    "policies": policies.VALIDATOR,
    "policy_sets": policy_sets.VALIDATOR,
    "research_scopes": research_scopes.VALIDATOR,
    "runs": runs.VALIDATOR,
    "admissions": admissions.VALIDATOR,
    "decisions": decisions.VALIDATOR,
    "actions": actions.VALIDATOR,
    "proposals": proposals.VALIDATOR,
    "reports": reports.VALIDATOR,
    "memories": memories.VALIDATOR,
    "tasks": tasks.VALIDATOR,
    "media": media.VALIDATOR,
    "source_versions": source_versions.VALIDATOR,
}

COLLECTIONS: tuple[str, ...] = tuple(VALIDATORS)

VALIDATION_LEVEL = "strict"
VALIDATION_ACTION = "error"


def validator(name: str) -> dict[str, Any]:
    """The full validator document (`$jsonSchema`, and `$expr` where one applies)."""
    return VALIDATORS[name]


def collection_options(name: str) -> dict[str, Any]:
    """Keyword arguments for `db.create_collection(name, **options)`."""
    return {
        "validator": VALIDATORS[name],
        "validationLevel": VALIDATION_LEVEL,
        "validationAction": VALIDATION_ACTION,
    }


async def apply(db: Any, names: tuple[str, ...] | list[str] | None = None) -> list[str]:
    """Create each missing collection with its validator; `collMod` existing ones.

    Idempotent. Returns the names it touched. `db` is a PyMongo async database.
    """
    wanted = list(names) if names is not None else list(COLLECTIONS)
    existing = set(await db.list_collection_names())
    for name in wanted:
        options = collection_options(name)
        if name in existing:
            await db.command({"collMod": name, **options})
        else:
            await db.create_collection(name, **options)
    return wanted
