"""The seeded world for A06 tests (ledger, gate, claim checks).

Store tests run on two backends (see ``conftest.world``):

* ``fake``: the in-memory ``fakedb`` (always runs);
* ``atlas``: A01's session test database (``dxp_test_<hex>``, dropped at the end,
  never ``dxp``), emptied before each test; skipped by A01's conftest without
  ``MONGODB_URI``.

``identity`` and ``schema.registry`` are A02's real modules. On ``atlas`` the
store is A01's real ``store.db()`` and ``store.emit_event``; on ``fake`` an
in-memory database (behind the store's accessors) and an AD-10 emitter stand
in. ``gate.policy_sets`` is A03's real module on both.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

from dxp.gate.decisions import deps
from dxp.identity import derive, normalise_name

from .fakedb import FakeDB

NOW = datetime(2026, 11, 14, 13, 0, tzinfo=timezone.utc)

PLASMA = ["FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx", "Agilent Resolution ctDx FIRST assay"]
TISSUE = "FoundationOne CDx"
SCOPE_ID = "scope_plasma_ctdna_nsclc"
TEAM_ID = "team_liquid_biopsy_dx"
ANCHOR = "clinicaltrials.gov:NCT04712877"


# --- stand-in for the store's event writer on the fake backend ---------------


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
        from dxp.gate.policy_sets import current_set

        self.policy_set_version = (await current_set()).id
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

    async def evaluate(self, ctx: Any, action: Any) -> Raw:
        """gate.evaluate, checked to return the API Decision, then the stored document."""
        from dxp import gate
        from dxp.api.models import Decision

        d = await gate.evaluate(ctx, action)
        assert isinstance(d, Decision)
        return Raw(await self.db["decisions"].find_one({"_id": d.id}))

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


ATLAS_COLLECTIONS = (
    "grants", "policies", "policy_sets", "research_scopes", "aliases", "diagnostics", "source_items",
    "runs", "admissions", "decisions", "actions", "events", "proposals", "edges", "reports",
)


class Raw(dict):
    """A stored decision document with the accessors the tests read."""

    @property
    def decision_id(self) -> str:
        return self["_id"]

    @property
    def allowed(self) -> bool:
        return self.get("outcome") == "allowed"

    @property
    def blocked(self) -> bool:
        return self.get("outcome") == "blocked"

    @property
    def action_id(self) -> str | None:
        return self.get("action_id")

    @property
    def failed_check(self) -> str | None:
        return self.get("failed_check")


async def open_world(backend: str) -> tuple[World, Callable[[], Awaitable[None]]]:
    """Seed a world on ``fake`` (in memory) or ``atlas`` (A01's store and test database).

    A03's ``gate.policy_sets`` is used as it is on both: on ``fake`` the store's
    database accessors are pointed at the in-memory database for the test.
    """
    from dxp import store

    restore: dict[str, Any] = {}
    if backend == "fake":
        db = FakeDB()
        db["events"].unique.append(("dedupe_key",))
        for name in ("db", "get_db"):
            restore[name] = getattr(store, name)
            setattr(store, name, lambda _db=db: _db)
        restore["collection"] = store.collection
        store.collection = lambda name, _db=db: _db[name]
        # store.emit_event reads with a projection and a sort the fake does not model: AD-10 stand-in.
        deps.override(emit_event=Emitter(db))
    else:
        await store.ensure_indexes()
        db = store.db()
        for name in ATLAS_COLLECTIONS:
            await db[name].delete_many({})
    deps.override(now=lambda: NOW)
    w = World(db)
    await w.seed()

    async def close() -> None:
        deps.reset()
        for name, fn in restore.items():
            setattr(store, name, fn)

    return w, close
