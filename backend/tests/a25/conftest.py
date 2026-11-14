"""A25 fixtures: A06's seeded world (in memory) with the REAL gate, a task, its grant and its run.

Only the network-facing search step, the worker context and the runs admissions (which need an
Atlas transaction) are replaced; filing goes through the real `reports.add_related` and the real
`gate.evaluate`. Hand-written test data only (D1)."""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import pytest
import pytest_asyncio
from a06.world import ANCHOR, NOW, SCOPE_ID, SV_ANCHOR, Emitter, World, open_world

from dxp import runs, store
from dxp.api.models import Admission, Principal, RunContext, Stamp
from dxp.gate import grants
from dxp.identity import derive

run_mod = importlib.import_module("dxp.tasks.run")
relate_mod = importlib.import_module("dxp.reports.relate")

ANCHOR_TEXT = "Brief title: Blood ctDNA and tumour tissue profiling in early-stage lung cancer before surgery."
RELATED_TEXT = "Brief title: Plasma testing with tissue profiling in resectable NSCLC. Results posted."


def ref(n: int) -> str:
    return f"clinicaltrials.gov:NCT{n:08d}"


@dataclass
class FakeOutcome:
    status: str = "done"
    source_refs: list[str] = field(default_factory=list)
    query: dict[str, Any] = field(default_factory=lambda: {"query.term": '"ctDNA" OR "plasma"', "query.cond": "NSCLC"})
    decision_id: str | None = None


@dataclass
class TaskWorld:
    world: World
    task_id: str
    run_id: str
    report_id: str
    grant_id: str
    searches: list[tuple[str, int]] = field(default_factory=list)
    outcome: FakeOutcome = field(default_factory=FakeOutcome)
    on_search: Any = None

    @property
    def db(self) -> Any:
        return self.world.db

    def task(self) -> dict[str, Any]:
        return self.db["tasks"].docs[self.task_id]

    def run_doc(self) -> dict[str, Any]:
        return self.db["runs"].docs[self.run_id]

    def add_items(self, refs_with_results: dict[str, bool], scope_ids: list[str] | None = None) -> None:
        for r, has in refs_with_results.items():
            version_id = derive("sv_", r, "1")
            self.db["source_versions"].docs[version_id] = {"_id": version_id, "source_ref": r, "raw_text": RELATED_TEXT}
            self.db["source_items"].docs[r] = {
                "_id": r, "source": "clinicaltrials.gov", "current_version_id": version_id,
                "has_results": has, "scope_ids": list(scope_ids or [SCOPE_ID]), "window": "discovered",
            }
        self.outcome.source_refs = list(refs_with_results)

    def events(self, type_: str) -> list[dict[str, Any]]:
        return [e for e in self.db["events"].docs.values() if e.get("type") == type_]


@pytest_asyncio.fixture
async def tw(monkeypatch: pytest.MonkeyPatch, features) -> AsyncIterator[TaskWorld]:
    world, close = await open_world("fake")
    db = world.db
    report_id = world.report_id
    task_id = derive("task_", report_id)
    run_id = derive("run_", task_id)
    decision_id = derive("dec_", "approval", "authorise_task")
    task = {
        "_id": task_id, "report_id": report_id, "kind": "search_related",
        "question": "Have early-stage NSCLC studies combining ctDNA or plasma testing with tissue profiling posted results?",
        "params": {"condition": "non-small cell lung cancer", "stage": "early",
                   "testing": ["ctDNA or plasma", "tissue profiling"], "has_results": True, "max": 5},
        "grant_id": grants.task_grant_id(task_id), "grant_version": 1, "status": "queued", "error": None,
        "queued_at": NOW, "run_id": run_id, "authorised_by_decision_id": decision_id,
        "authorised_by": "sam", "result": None, "created_at": NOW,
    }
    db["tasks"].docs[task_id] = task
    grant = grants.build_task_grant(task, {"_id": decision_id, "initiated_by": "sam"}, world.grants["lbdx"], NOW)
    await db["grants"].insert_one(grant)
    db["runs"].docs[run_id] = {
        "_id": run_id, "agent": "dxp-curator", "initiated_by": "sam", "grant_id": grant["grant_id"],
        "grant_version": 1, "policy_set_version": world.policy_set_version, "team_id": world.team_id,
        "set": f"task:{task_id}", "kind": "task", "scope_id": None, "task_id": task_id,
        "status": "running", "in_flight": 0, "mode": "live", "started_at": NOW,
    }
    db["reports"].docs[report_id] = {
        "_id": report_id, "source_ref": ANCHOR, "version_id": SV_ANCHOR, "scope_id": SCOPE_ID,
        "status": "accepted", "related": [], "discovery": {"mentions": []},
        "run_id": world.run_id, "team_id": world.team_id, "created_at": NOW,
        "stamp": {"kind": "run", "run_id": world.run_id, "agent": "dxp-curator", "initiated_by": "sam",
                  "principal": "dxp-curator", "grant_id": "lbdx", "grant_version": 1},
    }
    db["source_versions"].docs[SV_ANCHOR] = {"_id": SV_ANCHOR, "source_ref": ANCHOR, "raw_text": ANCHOR_TEXT}
    t = TaskWorld(world, task_id, run_id, report_id, grant["grant_id"])

    async def ask(new: dict[str, Any], related: dict[str, Any]) -> dict[str, Any]:  # the model, faked
        return {"label": "supports", "rationale": "Both records profile plasma and tissue in early disease.",
                "new_quote": "Blood ctDNA and tumour tissue profiling",
                "related_quote": "Plasma testing with tissue profiling"}

    monkeypatch.setattr(relate_mod, "_ask", ask)

    monkeypatch.setattr(store, "emit_event", Emitter(db))

    async def admit(rid: str, item_key: str) -> Admission | None:
        if (db["runs"].docs.get(rid) or {}).get("status") != "running":
            return None
        adm_id = await world.admit(key=item_key, run_id=rid)
        return Admission(id=adm_id, run_id=rid, item_key=item_key, status="admitted",
                         admitted_at=NOW, expires_at=NOW + timedelta(minutes=10))

    async def release(adm_id: str) -> None:
        doc = db["admissions"].docs.get(adm_id)
        if doc and doc["status"] == "admitted":
            doc["status"] = "released"

    monkeypatch.setattr(runs, "admit", admit)
    monkeypatch.setattr(runs, "release", release)

    async def context(rid: str) -> RunContext:
        stamp = Stamp(kind="run", run_id=rid, agent="dxp-curator", initiated_by="sam", principal="dxp-curator",
                      grant_id=t.grant_id, grant_version=1, policy_set_version=world.policy_set_version)
        return RunContext(run_id=rid, principal=Principal(id="dxp-curator", name="dxp-curator", kind="agent"),
                          stamp=stamp, grant_id=t.grant_id, grant_version=1, run_grant_version=1,
                          policy_set_version=world.policy_set_version)

    async def search(scope_id: str, ctx: RunContext, limit: int) -> FakeOutcome:  # no network
        t.searches.append((scope_id, limit))
        if t.on_search is not None:
            t.on_search()
        return t.outcome

    monkeypatch.setattr(run_mod, "_context", context)
    monkeypatch.setattr(run_mod, "_search", search)
    features("task_run")
    try:
        yield t
    finally:
        await close()


@pytest.fixture
def quote_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shim for a gap outside A25: `reports.add_related` sends `inputs.checked_quotes` but no
    `inputs.checks`, and the seeded `evidence_quote_supported@v1` policy reads `checks`, so the real
    gate blocks every related filing (see `test_add_related_without_checks_is_blocked`). Here the
    checked quotes are passed on as checks before the REAL gate evaluates, which is what the A19+A20
    fix would send; every other check (grant, scope, limit, admission) is the gate's own."""
    from dxp import gate

    real = gate.evaluate

    async def evaluate(ctx: Any, action: Any, *args: Any, **kwargs: Any) -> Any:
        if getattr(action, "kind", None) == "file_related_evidence" and "checks" not in action.inputs:
            quotes = action.inputs.get("checked_quotes") or []
            checks = [{"quote_found": q.get("quote_found") is True, "supported": q.get("quote_found") is True}
                      for q in quotes]
            action = action.model_copy(update={"inputs": {**action.inputs, "checks": checks}})
        return await real(ctx, action, *args, **kwargs)

    monkeypatch.setattr(gate, "evaluate", evaluate)
