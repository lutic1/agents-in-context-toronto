"""Grant and policy selection, and policy sets (A03, AD-18, D6).

Selection works the same way for grants and policies: for each ID take the
latest version first, then look at its status. Only a latest version that is
`active` (and unexpired, for a grant) counts, so a newer `revoked` or
`expired` version blocks even when an older version is `active`.

A policy set is the list of current policy members, `"<policy_id>@v<n>"`,
sorted; its version is `derive("ps_", *members)`. The `policy_sets` document is
inserted if absent the first time the set is used, so any decision's set can be
rebuilt later. A run pins the set at start; a Reviewer decision uses the
current set.

Frozen signatures (A01): `current_grant(grant_id) -> Grant` and
`current_set() -> PolicySet`. The document-level helpers below take an
optional `db` so tests and the seed can pass their own database.

Nothing here reads `memories`: a memory never changes authority (V6, AD-28).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from dxp.api.models import Grant, PolicySet

GRANTS = "grants"
POLICIES = "policies"
POLICY_SETS = "policy_sets"


def database(db: Any = None) -> Any:
    """The database to use: the one given, else the store's (`DXP_DB`)."""
    if db is not None:
        return db
    from dxp import store

    return store.get_db()


def utc(value: datetime | None) -> datetime | None:
    """Datetimes as aware UTC (the store's client is tz-aware; plain clients are not)."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def now() -> datetime:
    return datetime.now(UTC)


def latest_by(docs: list[dict[str, Any]], id_field: str) -> dict[str, dict[str, Any]]:
    """For each ID, the document with the highest `version`."""
    latest: dict[str, dict[str, Any]] = {}
    for doc in docs:
        key = doc[id_field]
        if key not in latest or doc["version"] > latest[key]["version"]:
            latest[key] = doc
    return latest


# --- Grants -----------------------------------------------------------------


def _field(grant: Any, name: str) -> Any:
    return grant.get(name) if isinstance(grant, dict) else getattr(grant, name, None)


def grant_is_active(grant: Grant | dict[str, Any] | None, at: datetime | None = None) -> bool:
    """`active` and `expires_at` in the future (check 1's test, AD-19). Takes a `Grant` or a document."""
    if not grant or _field(grant, "status") != "active":
        return False
    expires_at = utc(_field(grant, "expires_at"))
    return expires_at is not None and expires_at > (at or now())


def grant_model(doc: dict[str, Any]) -> Grant:
    """The AD-14 `Grant` from a stored version (the key hash is not part of it)."""
    return Grant.model_validate({**doc, "id": doc["_id"]})


async def latest_grant(grant_id: str, db: Any = None) -> dict[str, Any] | None:
    """The latest stored version of `grant_id`, whatever its status, or `None`."""
    cursor = database(db)[GRANTS].find({"grant_id": grant_id}).sort("version", -1).limit(1)
    found = await cursor.to_list(length=1)
    return found[0] if found else None


async def current_grant(grant_id: str) -> Grant | None:
    """Frozen (A01): the latest version of the grant, whatever its status, or `None` if unknown.

    Check 1 judges the status with `grant_is_active()` and records the version
    it evaluated beside the run's pinned version.
    """
    doc = await latest_grant(grant_id)
    return grant_model(doc) if doc else None


async def grant_version(grant_id: str, version: int, db: Any = None) -> dict[str, Any] | None:
    """One stored version, `<grant_id>@v<version>` (for `?version=` and audits)."""
    return await database(db)[GRANTS].find_one({"_id": f"{grant_id}@v{int(version)}"})


async def current_grants(db: Any = None) -> list[dict[str, Any]]:
    """The latest version of every grant, ordered by `grant_id`."""
    docs = await database(db)[GRANTS].find({}).to_list(length=None)
    return [doc for _, doc in sorted(latest_by(docs, "grant_id").items())]


# --- Policies and policy sets -----------------------------------------------


async def latest_policies(db: Any = None) -> list[dict[str, Any]]:
    """The latest version of every policy, whatever its status, by `policy_id`."""
    docs = await database(db)[POLICIES].find({}).to_list(length=None)
    return [doc for _, doc in sorted(latest_by(docs, "policy_id").items())]


async def current_policies(db: Any = None) -> list[dict[str, Any]]:
    """Policies whose latest version is `active`: the members of the current set."""
    return [doc for doc in await latest_policies(db) if doc.get("status") == "active"]


def members_of(policies: list[dict[str, Any]]) -> list[str]:
    return sorted(f"{p['policy_id']}@v{p['version']}" for p in policies)


def policy_set_version(members: list[str]) -> str:
    """`derive("ps_", *sorted members)` (AD-18)."""
    from dxp import (
        identity,  # A02; imported here so the API starts even before A02 merges
    )

    return identity.derive("ps_", *sorted(members))


async def record_current_set(db: Any = None) -> dict[str, Any]:
    """The current policy set as its `policy_sets` document, inserted if absent.

    Returns `{ _id: policy_set_version, members, created_at }`.
    """
    database_ = database(db)
    members = members_of(await current_policies(database_))
    version = policy_set_version(members)
    existing = await database_[POLICY_SETS].find_one({"_id": version})
    if existing:
        return existing
    doc = {"_id": version, "members": members, "created_at": now()}
    try:
        await database_[POLICY_SETS].insert_one(doc)
    except DuplicateKeyError:  # another caller used the same set first
        return await database_[POLICY_SETS].find_one({"_id": version})
    return doc


async def current_set() -> PolicySet:
    """Frozen (A01): the current policy set; inserts its `policy_sets` document on first use.

    The member documents are `policies_in_set(policy_set.id)`.
    """
    doc = await record_current_set()
    return PolicySet(id=doc["_id"], members=list(doc["members"]), created_at=doc.get("created_at"))


async def policy_set(version: str, db: Any = None) -> dict[str, Any] | None:
    """A recorded policy set by its version (a run's pinned set, an audit)."""
    return await database(db)[POLICY_SETS].find_one({"_id": version})


async def policies_in_set(version: str, db: Any = None) -> list[dict[str, Any]]:
    """The policy documents of a recorded set, in member order (the gate reads these)."""
    database_ = database(db)
    recorded = await policy_set(version, database_)
    if not recorded:
        return []
    members = list(recorded["members"])
    docs = await database_[POLICIES].find({"_id": {"$in": members}}).to_list(length=None)
    by_id = {doc["_id"]: doc for doc in docs}
    return [by_id[m] for m in members if m in by_id]


def display_policy_set(version: str, count: int) -> str:
    """D40 display form: `ps_ab12… (N policies)`."""
    return f"{version[:7]}… ({count} {'policy' if count == 1 else 'policies'})"
