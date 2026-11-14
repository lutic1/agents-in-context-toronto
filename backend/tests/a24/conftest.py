"""A24 fixtures: a hand-written world (grants, scope, one filed report with one scope-collection
proposal) on an in-memory store, a gate double that persists Decisions with the AD-3 IDs and
judges check 1 and check 3 from the stored grants, and doubles for ledger.apply, runs.start,
memory.create and the caller's key. No file from data/ is read."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from dxp.api import models as m
from dxp.identity import derive

from .fakedb import FakeClient, FakeDB

SCOPE_ID = "scope_plasma_ctdna_nsclc"
TEAM_ID = derive("team_", "Team Liquid Biopsy Dx")
DX_IDS = [derive("dx_", "guardant360 cdx"), derive("dx_", "foundationone liquid cdx")]
ORIGIN_RUN = "run_0123456789abcdef"
SOURCE_REF = "clinicaltrials.gov:NCT04712877"
VERSION_ID = derive("sv_", SOURCE_REF, "2026-11-01", "hash")
REPORT_ID = derive("rep_", ORIGIN_RUN, SOURCE_REF)
PROPOSAL_ID = derive("p_", "-", "collections", REPORT_ID)
REL_ID = derive("rel_", REPORT_ID, SOURCE_REF, "clinicaltrials.gov:NCT00000001")
GAP = "Which early-stage NSCLC trials combining ctDNA testing with tissue profiling have posted results?"
SAM_KEY = "test-dxp-api-key"
AGENT_KEY = "test-dxp-agent-key"


def now() -> datetime:
    return datetime.now(UTC)


def grant_doc(grant_id: str, version: int, principal: str, kind: str, actions: list[str], destinations: list[str],
              status: str = "active", name: str | None = None) -> dict[str, Any]:
    return {
        "_id": f"{grant_id}@v{version}", "grant_id": grant_id, "version": version, "principal": principal,
        "principal_name": name or principal, "kind": kind, "key_hash": None, "acting_for": TEAM_ID,
        "granted_by": "luis", "startable_by": ["sam"], "team_id": TEAM_ID, "team_name": "Team Liquid Biopsy Dx",
        "scope": {"scope_id": SCOPE_ID, "diagnostic_ids": list(DX_IDS)}, "destinations": destinations,
        "actions": actions, "limits": None, "task_id": None, "expires_at": now() + timedelta(days=2),
        "status": status, "created_at": now(),
    }


SAM_ACTIONS = ["decide_report", "authorise_task", "create_memory", "correct_memory", "revoke_memory",
               "review_value", "resolve_notification", "revert_report", "generate_briefing", "generate_avatar_video"]


def report_doc(**overrides: Any) -> dict[str, Any]:
    doc = {
        "_id": REPORT_ID, "run_id": ORIGIN_RUN, "scope_id": SCOPE_ID, "team_id": TEAM_ID, "source_ref": SOURCE_REF,
        "version_id": VERSION_ID, "nct_id": "NCT04712877",
        "headline": "Updated trial names blood (ctDNA) and tumour tissue profiling in early-stage lung cancer",
        "discovery": {
            "summary": "Molecular profiling using blood (ctDNA) and tumour tissue; no results posted.",
            "quotes": [{"text": "molecular profiling", "quote_found": True, "version_id": VERSION_ID}],
            "trial_status": "RECRUITING", "has_results": False, "intervention_text": "verbatim",
            "mentions": [{"name": "FoundationOne CDx", "resolved_diagnostic_id": None, "field": "otherNames"}],
        },
        "related": [{
            "_id": REL_ID, "id": REL_ID, "related_ref": "clinicaltrials.gov:NCT00000001",
            "related_kind": "source_item", "label": "related_unestablished", "origin": "discovery",
            "status": "pending",
            "new_quote": {"source_ref": SOURCE_REF, "version_id": VERSION_ID, "text": "ctDNA", "quote_found": True},
            "related_quote": {"source_ref": "clinicaltrials.gov:NCT00000001", "version_id": VERSION_ID,
                              "text": "plasma", "quote_found": False},
        }],
        "uncertainties": ["The intervention field is ambiguous."], "gap": GAP,
        "proposal_ids": [PROPOSAL_ID], "diagnostic_ids": [],
        "recommended_task": {"kind": "search_related", "params": {
            "condition": "non-small cell lung cancer", "stage": "early",
            "testing": ["ctDNA or plasma", "tissue profiling"], "has_results": True, "max": 5}},
        "draft": 2, "stamp": {"kind": "run", "principal": "dxp-curator", "run_id": ORIGIN_RUN},
        "file_decision_id": derive("dec_", "file"), "status": "pending", "approval": None, "task_id": None,
        "memory_id": None, "script": "A short grounded script.", "script_hash": "h", "created_at": now(),
    }
    doc.update(overrides)
    return doc


def proposal_doc() -> dict[str, Any]:
    return {
        "_id": PROPOSAL_ID, "diagnostic_id": None, "target": {"scope_id": SCOPE_ID}, "field": "collections",
        "value": SOURCE_REF, "status": "pending", "mode": "live", "run_id": ORIGIN_RUN, "report_id": REPORT_ID,
        "evidence": {"source_ref": SOURCE_REF, "version_id": VERSION_ID},
    }


@dataclass
class World:
    db: FakeDB
    gate_calls: list[tuple[dict[str, Any], dict[str, Any]]] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    run_starts: list[dict[str, Any]] = field(default_factory=list)
    spawned: list[str] = field(default_factory=list)
    memories: list[dict[str, Any]] = field(default_factory=list)
    memory_fails: int = 0
    gate_fail_kinds: dict[str, str] = field(default_factory=dict)

    def one(self, collection: str, **flt: Any) -> list[dict[str, Any]]:
        return [d for d in self.db.all(collection) if all(d.get(k) == v for k, v in flt.items())]

    def report(self) -> dict[str, Any]:
        return self.db.data["reports"][REPORT_ID]

    def revoke_sam(self) -> None:
        self.db.data["grants"]["sam@v2"] = grant_doc("sam", 2, "sam", "person", SAM_ACTIONS,
                                                     ["ledger", "tts:elevenlabs", "video:heygen"],
                                                     status="revoked", name="Sam")

    def add_report(self, **overrides: Any) -> None:
        doc = report_doc(**overrides)
        self.db.data["reports"][doc["_id"]] = doc


class PersistingGate:
    """Records one Decision per evaluation, insert-if-absent on the AD-3 ID, like A06's gate.
    Check 1: the latest version of the context's grant is active, unexpired and the caller's.
    Check 3: the kind and destination are on that grant."""

    def __init__(self, world: World) -> None:
        self.world = world

    async def evaluate(self, ctx: Any, action: Any, session: Any = None) -> m.Decision:
        from dxp.store import emit_event

        ctx = dict(ctx)
        action = dict(action)
        self.world.gate_calls.append((ctx, action))
        db = self.world.db
        target = action.get("target") or {}
        decision_id = action.get("decision_id") or (action.get("inputs") or {}).get("decision_id") or derive(
            "dec_", "-", action["kind"], "-", target.get("report_id") or target.get("memory_id"), ctx["request_id"])
        stored = await db["decisions"].find_one({"_id": decision_id})
        if stored is not None:
            return m.Decision.model_validate({**stored, "id": stored["_id"]})
        grant = await db["grants"].find_one({"grant_id": ctx["grant_id"]}, sort=[("version", -1)])
        failed, detail = None, "ok"
        if grant is None or grant["status"] != "active" or grant["expires_at"] <= now():
            failed, detail = "grant_active", f"latest version {ctx['grant_id']}@v{(grant or {}).get('version')} is {(grant or {}).get('status')}"
        elif grant["principal"] != ctx["principal"]:
            failed, detail = "grant_active", "not the caller's grant"
        elif action["kind"] not in grant["actions"]:
            failed, detail = "destination_action", f"action {action['kind']!r} is not on the grant"
        elif action["kind"] in self.world.gate_fail_kinds:
            failed = self.world.gate_fail_kinds[action["kind"]]
            detail = "forced by the test"
        doc = {
            "_id": decision_id, "run_id": None, "agent": None, "initiated_by": ctx["initiated_by"],
            "stamp": ctx["stamp"], "cause": ctx.get("cause"), "request_id": ctx["request_id"], "kind": action["kind"],
            "inputs": action.get("inputs") or {}, "evidence_ref": action.get("evidence_ref"),
            "destination": action["destination"], "target": target,
            "checks": [{"check": failed or "grant_active", "passed": failed is None, "detail": detail}],
            "failed_check": failed, "grant_id": ctx["grant_id"], "grant_version": (grant or {}).get("version") or 0,
            "outcome": "blocked" if failed else "allowed", "action_id": None, "decided_at": now(),
        }
        if ctx.get("origin"):
            doc["origin"] = ctx["origin"]
        await db["decisions"].insert_one(doc)
        seq = await emit_event({"type": "action_blocked" if failed else "action_allowed",
                                "dedupe_key": f"decision|{decision_id}", "decision_id": decision_id,
                                "stamp": ctx["stamp"]})
        await db["decisions"].update_one({"_id": decision_id}, {"$set": {"seq": seq}})
        doc["seq"] = seq
        return m.Decision.model_validate({**doc, "id": decision_id})

    async def evaluate_in(self, ctx: Any, action: Any, session: Any) -> m.Decision:
        return await self.evaluate(ctx, action, session)


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> World:
    import dxp.gate
    import dxp.ledger
    import dxp.memory
    import dxp.runs
    import dxp.store
    import dxp.store.events
    from dxp.api import auth

    db = FakeDB()
    w = World(db=db)
    for name in ("grants", "reports", "proposals", "decisions", "tasks", "runs", "events", "source_items",
                 "research_scopes", "memories", "actions", "diagnostics"):
        db.data.setdefault(name, {})
    db.data["grants"]["lbdx@v1"] = grant_doc("lbdx", 1, "dxp-curator", "agent",
                                             ["search_source", "file_proposal", "notify_slack"],
                                             ["source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"])
    db.data["grants"]["sam@v1"] = grant_doc("sam", 1, "sam", "person", SAM_ACTIONS,
                                            ["ledger", "tts:elevenlabs", "video:heygen"], name="Sam")
    db.data["research_scopes"][SCOPE_ID] = {"_id": SCOPE_ID, "condition": "non-small cell lung cancer"}
    db.data["source_items"][SOURCE_REF] = {"_id": SOURCE_REF, "collections": {}}
    db.data["proposals"][PROPOSAL_ID] = proposal_doc()
    w.add_report()

    monkeypatch.setattr(dxp.store, "get_db", lambda: db)
    monkeypatch.setattr(dxp.store, "get_client", lambda: FakeClient(db))
    monkeypatch.setattr(dxp.store.events, "get_db", lambda: db)

    gate = PersistingGate(w)
    monkeypatch.setattr(dxp.gate, "evaluate", gate.evaluate)
    monkeypatch.setattr(dxp.gate, "evaluate_in", gate.evaluate_in, raising=False)

    async def apply_with(proposal_id: str, *, review: str | None = None, decided_by: str | None = None,
                         session: Any = None) -> m.Proposal:
        from dxp.store import emit_event

        res = await db["proposals"].update_one({"_id": proposal_id, "status": "pending"},
                                               {"$set": {"status": "applying", "decided_by": decided_by}})
        p = await db["proposals"].find_one({"_id": proposal_id})
        if res.modified_count:
            await asyncio.sleep(0)  # let a concurrent caller interleave
            w.applied.append(proposal_id)
            scope = p["target"]["scope_id"]
            await db["source_items"].update_one(
                {"_id": p["evidence"]["source_ref"]},
                {"$set": {f"collections.{scope}": {"status": "accepted", "proposal_id": proposal_id,
                                                   "version_id": p["evidence"]["version_id"]}}})
            await emit_event({"type": "value_applied", "dedupe_key": f"value_applied|{proposal_id}"})
            await db["proposals"].update_one({"_id": proposal_id, "status": "applying"}, {"$set": {"status": "applied"}})
            p = await db["proposals"].find_one({"_id": proposal_id})
        return m.Proposal.model_validate({**p, "id": p["_id"]})

    async def recover_applying() -> None:
        return None

    monkeypatch.setattr(dxp.ledger, "apply_with", apply_with, raising=False)
    monkeypatch.setattr(dxp.ledger, "recover_applying", recover_applying)

    async def runs_start(caller: m.Principal, grant_id: str, set: str, run_id: str | None = None) -> m.Run:
        w.run_starts.append({"caller": caller.id, "grant_id": grant_id, "set": set, "run_id": run_id})
        doc = {"_id": run_id, "agent": "dxp-curator", "initiated_by": caller.id, "grant_id": grant_id,
               "grant_version": 1, "set": set, "kind": "task", "status": "running", "task_id": set[5:]}
        try:
            await db["runs"].insert_one(doc)
        except Exception:  # noqa: BLE001 - insert-if-absent
            doc = await db["runs"].find_one({"_id": run_id})
        return m.Run.model_validate({**doc, "id": doc["_id"]})

    monkeypatch.setattr(dxp.runs, "start", runs_start)

    async def memory_create(team_id, text, tags, source, reviewer, ctx):
        if w.memory_fails:
            w.memory_fails -= 1
            raise NotImplementedError("memory.create (A21+A22)")
        memory_id = derive("mem_", team_id, source.decision_id)
        w.memories.append({"memory_id": memory_id, "text": text, "tags": tags, "author": reviewer.id})
        doc = {"_id": f"{memory_id}@v1", "memory_id": memory_id, "version": 1, "team_id": team_id,
               "author": reviewer.id, "source": source.model_dump(), "text": text, "tags": tags,
               "status": "active", "decision_id": source.decision_id, "created_at": now()}
        await db["memories"].insert_one(doc)
        decision = m.Decision(id=derive("dec_", "mem", memory_id), stamp=ctx.stamp, kind="create_memory",
                              destination="ledger", grant_id="sam", grant_version=1, outcome="allowed",
                              target=m.Target(report_id=source.report_id, memory_id=memory_id))
        return m.Memory.model_validate({**doc, "id": memory_id}), decision

    monkeypatch.setattr(dxp.memory, "create", memory_create)

    async def resolve_actor(api_key: str) -> m.Principal:
        if api_key == SAM_KEY:
            return m.Principal(id="sam", name="Sam", kind="person", actions=SAM_ACTIONS)
        if api_key == AGENT_KEY:
            return m.Principal(id="dxp-curator", name="dxp-curator", kind="agent", actions=[])
        from dxp.api.errors import ApiError

        raise ApiError(401, "unknown_key", "Unknown API key.")

    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)
    return w


@dataclass
class Spawner:
    spawned: list[str] = field(default_factory=list)

    def spawn(self, run_id: str) -> None:
        self.spawned.append(run_id)


@pytest.fixture
def client(world: World):
    from fastapi.testclient import TestClient

    from dxp.api.app import create_app

    spawner = Spawner()
    app = create_app(spawner)
    test_client = TestClient(app, raise_server_exceptions=True)
    test_client.spawner = spawner  # type: ignore[attr-defined]
    return test_client


def decide(client: Any, action: str = "approve", key: str = SAM_KEY, **body: Any):
    return client.post(f"/api/v1/reports/{REPORT_ID}/decision", json={"action": action, **body},
                       headers={"X-DxP-Key": key})
