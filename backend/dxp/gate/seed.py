"""`python -m dxp.gate.seed`: grants, policies and the research scope (A03, Story 9.2).

Run from the command line only, with `DXP_SEED_KEY`, `DXP_AGENT_KEY` and
`DXP_API_KEY` in the environment (D48). It reads the hand-written documents in
`gate/seed_data/` and inserts, if absent:

* the grants `lbdx@v1` (agent `dxp-curator`), `sam@v1` (Reviewer) and `seed@v1`;
* the evidence policy and the three claim policies (V7);
* the research scope `scope_plasma_ctdna_nsclc` with the 10:45 cursor (OD2);
* the current policy set in `policy_sets`.

Each grant's `key_hash` is computed here from the environment at run time; no
key or hash is in `seed_data/`, and nothing key-related is printed or logged.
Running it twice changes nothing. A stored version that differs from the
hand-written one is never overwritten: the seed stops and asks for a new
version, because grants and policies are never edited in place (AD-18). The
scope's cursor is left alone once seeded: only discovery (A05) moves it.

`--revoke <grant_id>` / `--expire <grant_id>` insert the next version of a
grant with that status (a revocation is a new version, D6); check 1 then
blocks it while its key still resolves (D17).
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import inspect
import json
import os
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from pymongo.errors import DuplicateKeyError

from dxp import identity
from dxp.gate import policy_sets
from dxp.store import schemas

SEED_DATA = Path(__file__).with_name("seed_data")
KEY_VARS = ("DXP_AGENT_KEY", "DXP_API_KEY", "DXP_SEED_KEY")
SEED_KEY_VAR = "DXP_SEED_KEY"
SEED_COLLECTIONS = ("grants", "policies", "policy_sets", "research_scopes")


class SeedError(Exception):
    """The seed refuses to run; nothing has been written when this is raised before `seed()` writes."""


# --- Reading the hand-written documents --------------------------------------


def _strip_comments(value: Any) -> Any:
    """Drop the `"//"` comment keys, at any depth."""
    if isinstance(value, dict):
        return {k: _strip_comments(v) for k, v in value.items() if k != "//"}
    if isinstance(value, list):
        return [_strip_comments(v) for v in value]
    return value


def load_seed_data(data_dir: Path = SEED_DATA) -> dict[str, list[dict[str, Any]]]:
    data: dict[str, list[dict[str, Any]]] = {}
    for name in ("grants", "policies", "research_scopes"):
        raw = json.loads((data_dir / f"{name}.json").read_text(encoding="utf-8"))
        data[name] = _strip_comments(raw)[name]
    return data


def _parse_time(text: str) -> datetime:
    return policy_sets.utc(datetime.fromisoformat(text))


def team_id_for(team_name: str) -> str:
    """The Team's ID. A13 must seed the Team in `teams` under the same ID."""
    return identity.derive("team_", team_name)


def diagnostic_id_for(trade_name: str) -> str:
    """A seeded Diagnostic's ID from its exact FDA trade name (AD-3, D45)."""
    return identity.derive("dx_", identity.normalise_name(trade_name))


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def check_keys(env: Mapping[str, str]) -> None:
    missing = [name for name in KEY_VARS if not env.get(name)]
    if missing:
        raise SeedError(f"Missing in the environment: {', '.join(missing)} (D48).")
    if len({env[name] for name in KEY_VARS}) != len(KEY_VARS):
        raise SeedError("DXP_AGENT_KEY, DXP_API_KEY and DXP_SEED_KEY must be three different keys (AD-18).")


# --- Building the documents ---------------------------------------------------


def build_grant(raw: Mapping[str, Any], env: Mapping[str, str], created_at: datetime) -> dict[str, Any]:
    doc = copy.deepcopy(dict(raw))
    key_env = doc.pop("key_env", None)
    if not key_env or not env.get(key_env):
        raise SeedError(f"{doc.get('_id')}: no key in {key_env or 'key_env'}.")
    doc["key_hash"] = hash_key(env[key_env])
    team_name = doc.get("team_name")
    doc["team_id"] = team_id_for(team_name) if team_name else None
    doc.setdefault("acting_for", doc["team_id"])
    scope = doc.get("scope") or {}
    if "diagnostic_trade_names" in scope:
        names = scope.pop("diagnostic_trade_names")
        scope["diagnostic_ids"] = [diagnostic_id_for(name) for name in names]
        doc["scope"] = {"diagnostic_ids": scope["diagnostic_ids"], "scope_id": scope["scope_id"]}
    doc["expires_at"] = _parse_time(doc["expires_at"])
    doc["created_at"] = created_at
    return doc


def build_policy(raw: Mapping[str, Any], created_at: datetime) -> dict[str, Any]:
    doc = copy.deepcopy(dict(raw))
    doc["created_at"] = created_at
    return doc


def build_scope(raw: Mapping[str, Any], created_at: datetime) -> dict[str, Any]:
    doc = copy.deepcopy(dict(raw))
    cursor = doc.get("cursor") or {}
    if not cursor.get("last_update_post_date"):
        raise SeedError(
            f"{doc.get('_id')}: OD2 cursor not set. Write the YYYY-MM-DD cursor chosen at 10:45 "
            "into seed_data/research_scopes.json (cursor.last_update_post_date)."
        )
    doc["cursor"] = {
        "last_update_post_date": cursor["last_update_post_date"],
        "set_at": created_at,
        "set_by_run_id": cursor.get("set_by_run_id"),
    }
    doc["team_id"] = team_id_for(doc.pop("team_name"))
    doc["created_at"] = created_at
    return doc


def build_all(
    data: Mapping[str, list[dict[str, Any]]], env: Mapping[str, str], created_at: datetime
) -> dict[str, list[dict[str, Any]]]:
    """Every document, built and checked before anything is written."""
    check_keys(env)
    return {
        "grants": [build_grant(g, env, created_at) for g in data["grants"]],
        "policies": [build_policy(p, created_at) for p in data["policies"]],
        "research_scopes": [build_scope(s, created_at) for s in data["research_scopes"]],
    }


# --- Writing -------------------------------------------------------------------


def _comparable(doc: Mapping[str, Any], ignore: tuple[str, ...]) -> Any:
    def norm(value: Any) -> Any:
        if isinstance(value, datetime):
            return policy_sets.utc(value)
        if isinstance(value, dict):
            return {k: norm(v) for k, v in value.items()}
        if isinstance(value, list):
            return [norm(v) for v in value]
        return value

    return norm({k: v for k, v in doc.items() if k not in ignore})


async def _insert_if_absent(collection: Any, doc: dict[str, Any], ignore: tuple[str, ...]) -> str:
    """`inserted`, or `unchanged` when an identical document exists; `SeedError` when it differs."""
    existing = await collection.find_one({"_id": doc["_id"]})
    if existing is None:
        try:
            await collection.insert_one(doc)
            return "inserted"
        except DuplicateKeyError:
            existing = await collection.find_one({"_id": doc["_id"]})
    if _comparable(existing, ignore) != _comparable(doc, ignore):
        raise SeedError(
            f"{doc['_id']} already exists with different content. Documents are never edited in "
            "place: add a new version to seed_data/ (or check that the keys in the environment "
            "are the ones the grants were seeded with)."
        )
    return "unchanged"


async def check_seed_authority(db: Any, env: Mapping[str, str]) -> None:
    """Once `seed@v1` exists, only its own key may run the seed, and only while it is active."""
    seed_grant = await policy_sets.latest_grant("seed", db)
    if seed_grant is None:
        return  # first run: this run creates the seed grant
    key_hash = hash_key(env.get(SEED_KEY_VAR, ""))
    known = await db[policy_sets.GRANTS].find_one({"grant_id": "seed", "key_hash": key_hash})
    if known is None:
        raise SeedError("DXP_SEED_KEY does not match the seeded seed grant.")
    if not policy_sets.grant_is_active(seed_grant):
        raise SeedError(f"The seed grant {seed_grant['_id']} is {seed_grant['status']} or expired.")


async def seed(db: Any, env: Mapping[str, str] | None = None, data_dir: Path = SEED_DATA) -> dict[str, Any]:
    """Seed `db`. Returns a summary with no key or hash in it."""
    env = os.environ if env is None else env
    created_at = policy_sets.now()
    docs = build_all(load_seed_data(data_dir), env, created_at)
    await schemas.apply(db, SEED_COLLECTIONS)
    await check_seed_authority(db, env)

    summary: dict[str, Any] = {"grants": {}, "policies": {}, "research_scopes": {}}
    for grant in docs["grants"]:
        summary["grants"][grant["_id"]] = await _insert_if_absent(db["grants"], grant, ("created_at",))
    for policy in docs["policies"]:
        summary["policies"][policy["_id"]] = await _insert_if_absent(db["policies"], policy, ("created_at",))
    for scope in docs["research_scopes"]:
        # The cursor belongs to discovery once seeded (AD-25); compare the rest.
        summary["research_scopes"][scope["_id"]] = await _insert_if_absent(
            db["research_scopes"], scope, ("created_at", "cursor")
        )
    current = await policy_sets.record_current_set(db)
    summary["policy_set"] = policy_sets.display_policy_set(current["_id"], len(current["members"]))
    summary["policy_set_version"] = current["_id"]
    summary["members"] = list(current["members"])
    return summary


async def new_grant_version(
    db: Any, grant_id: str, status: str, env: Mapping[str, str] | None = None
) -> dict[str, Any]:
    """Insert the next version of `grant_id` with `status` `revoked` or `expired` (AD-18, D6).

    An expiry also sets `expires_at` to now. The key hash is kept, so the key
    still resolves to its principal (D17) and check 1 blocks it.
    """
    if status not in ("revoked", "expired"):
        raise SeedError("status must be revoked or expired.")
    env = os.environ if env is None else env
    await check_seed_authority(db, env)
    latest = await policy_sets.latest_grant(grant_id, db)
    if latest is None:
        raise SeedError(f"No grant {grant_id}.")
    at = policy_sets.now()
    doc = {k: v for k, v in latest.items()}
    doc["version"] = int(latest["version"]) + 1
    doc["_id"] = f"{grant_id}@v{doc['version']}"
    doc["status"] = status
    doc["created_at"] = at
    if status == "expired":
        doc["expires_at"] = at
    await db["grants"].insert_one(doc)
    return doc


# --- Command line ------------------------------------------------------------------


async def _ensure_store_indexes() -> None:
    from dxp import store  # A01: creates every collection with its validator

    result = store.ensure_indexes()
    if inspect.isawaitable(result):
        await result


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dxp.gate.seed", description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--revoke", metavar="GRANT_ID", help="insert the next version of a grant as revoked")
    group.add_argument("--expire", metavar="GRANT_ID", help="insert the next version of a grant as expired")
    args = parser.parse_args(argv)

    try:
        db = policy_sets.database()
        if args.revoke or args.expire:
            doc = await new_grant_version(db, args.revoke or args.expire, "revoked" if args.revoke else "expired")
            print(f"{doc['_id']}: {doc['status']}")
            return 0
        await _ensure_store_indexes()
        summary = await seed(db)
    except SeedError as exc:
        print(f"seed refused: {exc}", file=sys.stderr)
        return 1
    for section in ("grants", "policies", "research_scopes"):
        for doc_id, outcome in summary[section].items():
            print(f"{doc_id}: {outcome}")
    print(f"policy set {summary['policy_set']}: {', '.join(summary['members'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
