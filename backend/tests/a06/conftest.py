"""Fixtures for A06 (ledger, gate, claim checks).

Store tests run on two backends:

* ``fake``: the in-memory ``fakedb`` (always runs);
* ``atlas``: a fresh database on the Atlas Sandbox, named ``dxp_test_a06_<hex>``
  and dropped afterwards, run only when ``MONGODB_URI`` is set. It never uses
  the ``dxp`` database.

Until A01, A02 and A03 are on main, the modules they own (``store``,
``identity``, ``gate.policy_sets``, ``schema.registry``) are not on this
branch, so ``gate.decisions.deps`` is pointed at the test stand-ins below,
each written to the rule it stands for (AD-3, AD-10, AD-18). After the A01
rebase, ``derive`` and ``normalise_name`` switch to A02's real functions.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sys
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fakedb import FakeDB  # noqa: E402

from dxp.gate.decisions import deps  # noqa: E402

NOW = datetime(2026, 11, 14, 13, 0, tzinfo=timezone.utc)

PLASMA = ["FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx", "Agilent Resolution ctDx FIRST assay"]
TISSUE = "FoundationOne CDx"
SCOPE_ID = "scope_plasma_ctdna_nsclc"
TEAM_ID = "team_liquid_biopsy_dx"
ANCHOR = "clinicaltrials.gov:NCT04712877"
STAGES = ["not_determined", "discovery", "assay_development", "clinical_validation", "regulatory_approval"]


# --- stand-ins for A02, A01 and A03 ----------------------------------------


def derive(prefix: str, *parts: Any) -> str:
    """AD-3: the prefix plus the first 16 hex characters of SHA-256 over the parts joined with ``|``."""
    return prefix + hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def normalise_name(text: str) -> str:
    """AD-3: NFKC, lower case, remove ®, ™ and ©, collapse non-alphanumerics to one space, trim."""
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub("[®™©]", "", t)
    return re.sub(r"[^0-9a-z]+", " ", t).strip()


def dx(name: str) -> str:
    return derive("dx_", normalise_name(name))


class Emitter:
    """AD-10: integer ``seq`` as ``_id``, inserted with retry; a repeated ``dedupe_key`` returns the stored ``seq``."""

    def __init__(self, db: Any):
        self.db = db

    async def __call__(self, event: dict[str, Any], *, session: Any = None) -> int:
        events = self.db["events"]
        for _ in range(50):
            found = await events.find_one({"dedupe_key": event["dedupe_key"]}, session=session)
            if found is not None:
                return found["_id"]
            last = await events.find({}, session=session).sort("_id", -1).to_list(1)
            seq = (last[0]["_id"] + 1) if last else 1
            try:
                await events.insert_one({"_id": seq, **event, "at": NOW}, session=session)
                return seq
            except Exception as exc:  # duplicate seq or dedupe_key: retry
                if type(exc).__name__ != "DuplicateKeyError":
                    raise
        raise RuntimeError("could not emit event")


class PolicySets:
    """AD-18 selection: latest version first, then status."""

    def __init__(self, db: Any):
        self.db = db

    async def current_grant(self, grant_id: str) -> dict | None:
        found = await self.db["grants"].find({"grant_id": grant_id}).sort("version", -1).to_list(1)
        return found[0] if found else None

    async def current_set(self) -> tuple[str, list[dict]]:
        latest: dict[str, dict] = {}
        async for p in self.db["policies"].find({}):
            if p["policy_id"] not in latest or p["version"] > latest[p["policy_id"]]["version"]:
                latest[p["policy_id"]] = p
        members = sorted(p["_id"] for p in latest.values() if p["status"] == "active")
        version = derive("ps_", *members)
        try:
            await self.db["policy_sets"].insert_one({"_id": version, "members": members, "created_at": NOW})
        except Exception as exc:
            if type(exc).__name__ != "DuplicateKeyError":
                raise
        return version, [latest[m.split("@")[0]] for m in members]


# --- the seeded world --------------------------------------------------------


def grant_doc(grant_id: str, version: int = 1, **kw: Any) -> dict:
    doc = {
        "_id": f"{grant_id}@v{version}",
        "grant_id": grant_id,
        "version": version,
        "status": "active",
        "expires_at": NOW + timedelta(days=1),
        "created_at": NOW,
        "acting_for": TEAM_ID,
        "granted_by": "luis",
        "team_id": TEAM_ID,
        "limits": None,
        "task_id": None,
    }
    doc.update(kw)
    return doc


def policy_doc(policy_id: str, applies_to: list[str], requires: dict, version: int = 1, status: str = "active") -> dict:
    return {
        "_id": f"{policy_id}@v{version}",
        "policy_id": policy_id,
        "version": version,
        "status": status,
        "applies_to": applies_to,
        "requires": requires,
        "text": policy_id,
        "author": "luis",
        "approved_by": "luis",
        "created_at": NOW,
    }


CLAIM_POLICY_IDS = ("claim_performed_or_results", "claim_planned", "claim_preclinical")


class World:
    def __init__(self, db: Any):
        self.db = db
        self.dx_plasma = [dx(n) for n in PLASMA]
        self.dx_tissue = dx(TISSUE)
        self.dx_f1l = self.dx_plasma[0]
        self.run_id = "run_test0001"
        self.policy_set_version: str | None = None
        self._adm = 0

    async def seed(self) -> None:
        db = self.db
        scope = {"scope_id": SCOPE_ID, "diagnostic_ids": self.dx_plasma}
        await db["grants"].insert_one(grant_doc(
            "lbdx", principal="dxp-curator", kind="agent", startable_by=["sam"], scope=scope,
            actions=["search_source", "file_proposal", "notify_slack"],
            destinations=["source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"],
        ))
        await db["grants"].insert_one(grant_doc(
            "sam", principal="sam", kind="person", startable_by=[], scope=scope,
            actions=["decide_report", "authorise_task", "create_memory", "correct_memory", "revoke_memory",
                     "review_value", "resolve_notification", "revert_report", "generate_briefing",
                     "generate_avatar_video"],
            destinations=["ledger", "tts:elevenlabs", "video:heygen"],
        ))
        await db["grants"].insert_one(grant_doc(
            "seed", principal="seed", kind="seed", startable_by=[], scope={"all": True},
            actions=["apply_value"], destinations=["ledger"], acting_for=None, team_id=None,
        ))
        await db["policies"].insert_one(policy_doc(
            "evidence_quote", ["file_proposal", "file_related_evidence"],
            {"quote_found": True, "supported": True, "min_confidence": 0.6},
        ))
        for pid in CLAIM_POLICY_IDS:
            await db["policies"].insert_one(policy_doc(pid, ["file_proposal"], {"claim_checks": [pid]}))
        await db["research_scopes"].insert_one({
            "_id": SCOPE_ID, "name": "Plasma ctDNA genotyping assays in NSCLC", "team_id": TEAM_ID,
            "assays": PLASMA, "aliases": ["ctDNA", "cell-free DNA", "liquid biopsy"],
            "condition": "non-small cell lung cancer", "source": "clinicaltrials.gov",
            "cursor": {"last_update_post_date": "2026-11-01", "set_at": NOW, "set_by_run_id": None},
        })
        for name in PLASMA + [TISSUE]:
            key = normalise_name(name)
            await db["aliases"].insert_one({"_id": key, "diagnostic_id": dx(name), "name": name})
            await db["diagnostics"].insert_one({
                "_id": dx(name), "name": name, "id_alias": key, "aliases": [key],
                "lifecycle_stage": "regulatory_approval", "fields": {}, "rev": 0,
                "applied_proposal_ids": [], "search_text": name, "facets": {},
                "created_run_id": None, "created_mode": "baseline",
            })
        await db["source_items"].insert_one({
            "_id": ANCHOR, "source": "clinicaltrials.gov", "current_version_id": "sv_anchor0000000001",
            "overall_status": "RECRUITING", "has_results": False, "scope_ids": [SCOPE_ID], "window": "discovered",
        })
        self.policy_set_version, _ = await PolicySets(db).current_set()
        await db["runs"].insert_one({
            "_id": self.run_id, "agent": "dxp-curator", "initiated_by": "sam", "grant_id": "lbdx",
            "grant_version": 1, "policy_set_version": self.policy_set_version, "status": "running",
            "mode": "live", "set": "discover", "scope_id": SCOPE_ID, "team_id": TEAM_ID,
        })

    async def admit(self, key: str | None = None, run_id: str | None = None, status: str = "admitted") -> str:
        self._adm += 1
        run_id = run_id or self.run_id
        item_key = key or f"item{self._adm}"
        adm_id = derive("adm_", run_id, item_key)
        await self.db["admissions"].insert_one({
            "_id": adm_id, "run_id": run_id, "item_key": item_key, "status": status,
            "admitted_at": NOW, "expires_at": NOW + timedelta(minutes=10),
        })
        return adm_id

    def run_ctx(self, admission_id: str | None, **kw: Any) -> dict:
        stamp = {
            "kind": "run", "run_id": self.run_id, "agent": "dxp-curator", "initiated_by": "sam",
            "principal": "dxp-curator", "grant_id": "lbdx", "grant_version": 1,
            "policy_set_version": self.policy_set_version,
        }
        ctx = {
            "kind": "run", "principal": "dxp-curator", "grant_id": "lbdx", "run_id": self.run_id,
            "agent": "dxp-curator", "initiated_by": "sam", "run_grant_version": 1,
            "policy_set_version": self.policy_set_version, "admission_id": admission_id, "stamp": stamp,
            "mode": "live",
        }
        ctx.update(kw)
        return ctx

    def reviewer_ctx(self, **kw: Any) -> dict:
        ctx = {
            "kind": "reviewer", "principal": "sam", "grant_id": "sam", "initiated_by": "sam",
            "request_id": uuid.uuid4().hex,
            "cause": {"report_id": "rep_x", "origin_run_id": self.run_id},
            "stamp": {"kind": "reviewer", "run_id": None, "principal": "sam", "agent": None,
                      "initiated_by": "sam", "grant_id": "sam", "grant_version": 1},
        }
        ctx.update(kw)
        return ctx

    def seed_ctx(self, **kw: Any) -> dict:
        ctx = {"kind": "seed", "principal": "seed", "grant_id": "seed", "mode": "baseline",
               "stamp": {"kind": "seed", "principal": "seed", "run_id": None}}
        ctx.update(kw)
        return ctx

    async def count(self, coll: str, flt: dict | None = None) -> int:
        return await self.db[coll].count_documents(flt or {})

    async def business_state(self) -> dict:
        """Everything a blocked action must leave untouched."""
        out = {}
        for coll in ("diagnostics", "aliases", "proposals", "actions", "reports", "edges", "source_items"):
            out[coll] = sorted(
                [d async for d in self.db[coll].find({})], key=lambda d: str(d["_id"])
            )
        return out


BACKENDS = ["fake", "atlas"]


@pytest.fixture(params=BACKENDS)
def world(request: pytest.FixtureRequest) -> Callable[[Callable[[World], Awaitable[Any]]], Any]:
    """``world(async_fn)`` runs ``async_fn(w)`` against a freshly seeded database."""
    backend = request.param
    uri = os.environ.get("MONGODB_URI")
    if backend == "atlas" and not uri:
        pytest.skip("MONGODB_URI is not set: Atlas Sandbox tests skipped (the fake backend ran)")

    def run(fn: Callable[[World], Awaitable[Any]]) -> Any:
        async def main() -> Any:
            client = None
            if backend == "fake":
                db = FakeDB()
                db["events"].unique.append(("dedupe_key",))
            else:
                from pymongo import AsyncMongoClient

                client = AsyncMongoClient(uri)
                name = f"dxp_test_a06_{uuid.uuid4().hex[:8]}"
                assert name != "dxp"
                db = client[name]
                await db["events"].create_index("dedupe_key", unique=True)
            ps = PolicySets(db)
            deps.override(
                db=lambda: db,
                emit_event=Emitter(db),
                derive=derive,
                normalise_name=normalise_name,
                current_grant=ps.current_grant,
                current_set=ps.current_set,
                stage_order=STAGES,
                now=lambda: NOW,
            )
            w = World(db)
            try:
                await w.seed()
                return await fn(w)
            finally:
                deps.reset()
                if client is not None:
                    await client.drop_database(db.name)
                    await client.close()

        return asyncio.run(main())

    return run
