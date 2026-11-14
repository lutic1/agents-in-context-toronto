"""A24 fixtures: a hand-written world (grants, scope, one filed report with one scope-collection
proposal) on an in-memory store, a gate double that persists Decisions with the AD-3 IDs and
judges check 1 and check 3 from the stored grants, and doubles for ledger.apply, runs.start,
memory.create and the caller's key. No file from data/ is read."""

from __future__ import annotations

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
    gate_calls: list[tuple[Any, Any]] = field(default_factory=list)
    run_starts: list[dict[str, Any]] = field(default_factory=list)
    spawned: list[str] = field(default_factory=list)
    memories: list[dict[str, Any]] = field(default_factory=list)
    memory_fails: int = 0
    refused_task_starts: int = 0

    def events(self, kind: str) -> list[dict[str, Any]]:
        return sorted((e for e in self.db.all("events") if e["type"] == kind), key=lambda e: e["_id"])

    @property
    def applied(self) -> list[str]:
        """Proposals the real ledger applied, from its deduplicated `value_applied` events."""
        return [e["proposal_id"] for e in self.events("value_applied")]

    @property
    def rejected_by_ledger(self) -> list[str]:
        return [e["proposal_id"] for e in self.events("proposal_rejected")]

    def report(self) -> dict[str, Any]:
        return self.db.data["reports"][REPORT_ID]

    def revoke_sam(self) -> None:
        self.db.data["grants"]["sam@v2"] = grant_doc("sam", 2, "sam", "person", SAM_ACTIONS,
                                                     ["ledger", "tts:elevenlabs", "video:heygen"],
                                                     status="revoked", name="Sam")

    def drop_from_sam(self, kind: str) -> None:
        """A new active version of sam's grant without `kind`: the real check 3 then blocks it."""
        latest = max(g["version"] for g in self.db.all("grants") if g["grant_id"] == "sam")
        actions = [a for a in SAM_ACTIONS if a != kind]
        doc = grant_doc("sam", latest + 1, "sam", "person", actions, ["ledger", "tts:elevenlabs", "video:heygen"],
                        name="Sam")
        doc["key_hash"] = hash_key(SAM_KEY)
        self.db.data["grants"][doc["_id"]] = doc

    def add_report(self, **overrides: Any) -> None:
        doc = report_doc(**overrides)
        self.db.data["reports"][doc["_id"]] = doc


def hash_key(key: str) -> str:
    import hashlib

    return hashlib.sha256(key.encode("utf-8")).hexdigest()


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> World:
    """The real merged gate (A06), ledger (A06), runs (A07+A11) and actor resolution (A03), over
    the in-memory store. Only memory.create is a double here (it needs embeddings)."""
    import dxp.gate
    import dxp.memory
    import dxp.runs
    import dxp.store
    import dxp.store.client
    import dxp.store.events
    from dxp.api.errors import ApiError

    db = FakeDB()
    w = World(db=db)
    for name in ("grants", "policies", "policy_sets", "reports", "proposals", "decisions", "tasks", "runs",
                 "run_locks", "events", "source_items", "research_scopes", "memories", "actions", "diagnostics",
                 "edges", "admissions"):
        db.data.setdefault(name, {})
    lbdx = grant_doc("lbdx", 1, "dxp-curator", "agent", ["search_source", "file_proposal", "notify_slack"],
                     ["source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"])
    lbdx["key_hash"] = hash_key(AGENT_KEY)
    sam = grant_doc("sam", 1, "sam", "person", SAM_ACTIONS, ["ledger", "tts:elevenlabs", "video:heygen"], name="Sam")
    sam["key_hash"] = hash_key(SAM_KEY)
    db.data["grants"]["lbdx@v1"] = lbdx
    db.data["grants"]["sam@v1"] = sam
    # One hand-written evidence policy, so the current policy set has a member (A03 derives its ID).
    db.data["policies"]["evidence_quote_supported@v1"] = {
        "_id": "evidence_quote_supported@v1", "policy_id": "evidence_quote_supported", "version": 1,
        "status": "active", "applies_to": ["file_proposal", "file_related_evidence"],
        "requires": {"quote_found": True, "supported": True}, "text": "A24 test policy.", "created_at": now(),
    }
    db.data["research_scopes"][SCOPE_ID] = {"_id": SCOPE_ID, "condition": "non-small cell lung cancer"}
    db.data["source_items"][SOURCE_REF] = {"_id": SOURCE_REF, "collections": {}}
    db.data["proposals"][PROPOSAL_ID] = proposal_doc()
    w.add_report()

    client = FakeClient(db)
    for module in (dxp.store, dxp.store.client):
        monkeypatch.setattr(module, "get_db", lambda: db)
        monkeypatch.setattr(module, "get_client", lambda: client)
    monkeypatch.setattr(dxp.store.events, "get_db", lambda: db)

    # Spies around the real functions: they record calls and delegate unchanged.
    real_evaluate, real_evaluate_in = dxp.gate.evaluate, dxp.gate.evaluate_in

    async def evaluate(ctx: Any, action: Any) -> m.Decision:
        w.gate_calls.append((ctx, action))
        return await real_evaluate(ctx, action)

    async def evaluate_in(ctx: Any, action: Any, session: Any) -> m.Decision:
        w.gate_calls.append((ctx, action))
        return await real_evaluate_in(ctx, action, session)

    monkeypatch.setattr(dxp.gate, "evaluate", evaluate)
    monkeypatch.setattr(dxp.gate, "evaluate_in", evaluate_in)

    real_start_if_absent = dxp.runs.start_if_absent

    async def start_if_absent(caller: m.Principal, grant_id: str, set: str,
                              run_id: str | None = None) -> tuple[m.Run, bool]:
        try:
            run, created = await real_start_if_absent(caller, grant_id, set, run_id)
        except ApiError as exc:
            if exc.code == "task_run_off":
                w.refused_task_starts += 1
            raise
        w.run_starts.append({"caller": caller.id, "grant_id": grant_id, "set": set, "run_id": run_id,
                             "created": created})
        return run, created

    monkeypatch.setattr(dxp.runs, "start_if_absent", start_if_absent)

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
