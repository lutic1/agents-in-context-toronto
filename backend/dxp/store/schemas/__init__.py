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

_MODULES = {
    "grants": grants,
    "policies": policies,
    "policy_sets": policy_sets,
    "research_scopes": research_scopes,
    "runs": runs,
    "admissions": admissions,
    "decisions": decisions,
    "actions": actions,
    "proposals": proposals,
    "reports": reports,
    "memories": memories,
    "tasks": tasks,
    "media": media,
    "source_versions": source_versions,
}

# The bare `$jsonSchema` documents, by collection: what A01's `store.ensure_indexes()`
# wraps as `{"$jsonSchema": ...}`.
VALIDATORS: dict[str, dict[str, Any]] = {name: module.JSON_SCHEMA for name, module in _MODULES.items()}

# Cross-field rules `$jsonSchema` cannot say (`_id` == `<id>@v<version>`, a task
# grant's one-hour expiry and its ID tied to its task). They apply only where the
# full `validator(name)` is used (`apply()`, and `ensure_indexes()` once it does).
EXPRESSIONS: dict[str, dict[str, Any]] = {
    name: module.VALIDATOR["$expr"] for name, module in _MODULES.items() if "$expr" in module.VALIDATOR
}

COLLECTIONS: tuple[str, ...] = tuple(VALIDATORS)

VALIDATION_LEVEL = "strict"
VALIDATION_ACTION = "error"


def validator(name: str) -> dict[str, Any]:
    """The full validator document (`$jsonSchema`, and `$expr` where one applies)."""
    return _MODULES[name].VALIDATOR


def collection_options(name: str) -> dict[str, Any]:
    """Keyword arguments for `db.create_collection(name, **options)`."""
    return {
        "validator": validator(name),
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
