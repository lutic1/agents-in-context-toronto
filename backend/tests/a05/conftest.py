"""A05 fixtures. Every study here is hand-written test data with only the fields a test needs;
no fetched record text and nothing from data/ (D1)."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from dxp.api.models import Admission, CheckResult, Decision, Principal, RunContext, Stamp

from .fakedb import FakeDB

SCOPE_ID = "scope_plasma_ctdna_nsclc"
RUN_ID = "run_test0001"
ASSAYS = ["FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx", "Agilent Resolution ctDx FIRST assay"]

scan_mod = importlib.import_module("dxp.discovery.scan")


def study(
    nct: str,
    lupd: str,
    *,
    status: str = "RECRUITING",
    has_results: bool = False,
    title: str = "Test trial",
    summary: str = "A test summary.",
    interventions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct, "briefTitle": title},
            "statusModule": {"overallStatus": status, "lastUpdatePostDateStruct": {"date": lupd}},
            "descriptionModule": {"briefSummary": summary},
            "conditionsModule": {"conditions": ["NSCLC"]},
            "armsInterventionsModule": {
                "interventions": interventions
                if interventions is not None
                else [{"type": "DIAGNOSTIC_TEST", "name": "test assay", "otherNames": ["Name A", "Name B"]}]
            },
        },
        "hasResults": has_results,
    }


def scope_doc(cursor: str = "2026-11-11", **extra: Any) -> dict[str, Any]:
    doc = {
        "_id": SCOPE_ID,
        "name": "Plasma ctDNA genotyping assays in NSCLC",
        "team_id": "team_test",
        "assays": list(ASSAYS),
        "aliases": ["ctDNA", "cell-free DNA", "liquid biopsy"],
        "condition": "non-small cell lung cancer",
        "source": "clinicaltrials.gov",
        "cursor": {"last_update_post_date": cursor, "set_at": None, "set_by_run_id": None},
        "version": 1,
    }
    doc.update(extra)
    return doc


@dataclass
class FakeCtgov:
    """A MockTransport for the ClinicalTrials.gov API: `studies` by NCT ID, `pages` for search."""

    studies: dict[str, dict[str, Any]] = field(default_factory=dict)
    pages: list[list[dict[str, Any]]] = field(default_factory=list)
    status: int = 200
    requests: list[httpx.Request] = field(default_factory=list)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.status != 200:
            return httpx.Response(self.status, json={"error": "test"})
        path = request.url.path
        if path.endswith("/studies"):
            token = request.url.params.get("pageToken")
            index = int(token) if token else 0
            body: dict[str, Any] = {"studies": self.pages[index] if index < len(self.pages) else []}
            if index + 1 < len(self.pages):
                body["nextPageToken"] = str(index + 1)
            return httpx.Response(200, json=body)
        nct = path.rsplit("/", 1)[-1]
        if nct in self.studies:
            return httpx.Response(200, content=json.dumps(self.studies[nct]))
        return httpx.Response(404, json={"error": "not found"})

    @property
    def searches(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.url.path.endswith("/studies")]


@pytest.fixture
def ctgov_fake(monkeypatch: pytest.MonkeyPatch) -> FakeCtgov:
    from dxp.sources import ctgov

    fake = FakeCtgov()

    def make_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=ctgov.BASE_URL, transport=httpx.MockTransport(fake.handler))

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(ctgov, "make_client", make_client)
    monkeypatch.setattr(ctgov.asyncio, "sleep", no_sleep)
    return fake


@dataclass
class Events:
    emitted: list[dict[str, Any]] = field(default_factory=list)

    async def emit(self, event: Any, *, session: Any = None, dedupe_key: str | None = None, stamp: Any = None, **fields: Any) -> int:
        if any(e["dedupe_key"] == dedupe_key for e in self.emitted):
            return 0
        self.emitted.append({"type": event, "dedupe_key": dedupe_key, "stamp": stamp, **fields})
        return len(self.emitted)

    def of(self, type_: str) -> list[dict[str, Any]]:
        return [e for e in self.emitted if e["type"] == type_]


@pytest.fixture
def fakedb(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    from dxp import store

    db = FakeDB()
    monkeypatch.setattr(store, "get_db", lambda: db)
    return db


@pytest.fixture
def events(monkeypatch: pytest.MonkeyPatch) -> Events:
    from dxp import store

    rec = Events()
    monkeypatch.setattr(store, "emit_event", rec.emit)
    return rec


@dataclass
class FakeRuns:
    """Stands in for runs.admit and runs.release (A07+A11): admits while `admitting` is True."""

    admitting: bool = True
    admitted: list[str] = field(default_factory=list)
    released: list[str] = field(default_factory=list)

    async def admit(self, run_id: str, item_key: str) -> Admission | None:
        if not self.admitting:
            return None
        self.admitted.append(item_key)
        return Admission(id=f"adm_{len(self.admitted):04d}", run_id=run_id, item_key=item_key, status="admitted")

    async def release(self, admission_id: str) -> None:
        self.released.append(admission_id)


@pytest.fixture
def fake_runs(monkeypatch: pytest.MonkeyPatch) -> FakeRuns:
    fake = FakeRuns()
    monkeypatch.setattr(scan_mod.runs, "admit", fake.admit)
    monkeypatch.setattr(scan_mod.runs, "release", fake.release)
    return fake


@dataclass
class ScanGate:
    """Stands in for gate.evaluate (A06): records the action and, when allowed, inserts the
    `queued` action document the real gate inserts (AD-19)."""

    db: FakeDB
    blocked: bool = False
    calls: list[tuple[Any, Any]] = field(default_factory=list)

    async def evaluate(self, ctx: Any, action: Any) -> Decision:
        self.calls.append((ctx, action))
        n = len(self.calls)
        action_id = None if self.blocked else f"act_test{n:012d}"
        if action_id:
            await self.db["actions"].insert_one(
                {"_id": action_id, "kind": action.kind, "status": "queued", "run_id": ctx.run_id}
            )
        await self.db["decisions"].insert_one({"_id": f"dec_test{n:012d}", "outcome": "blocked" if self.blocked else "allowed"})
        return Decision(
            id=f"dec_test{n:012d}", run_id=ctx.run_id, stamp=ctx.stamp, kind=action.kind, inputs=action.inputs,
            destination=action.destination, target=action.target,
            checks=[CheckResult(check="team_scope", passed=not self.blocked, detail="test")],
            failed_check="team_scope" if self.blocked else None, grant_id=ctx.grant_id,
            grant_version=ctx.grant_version, outcome="blocked" if self.blocked else "allowed", action_id=action_id,
            decided_at=datetime.now(UTC),
        )


@pytest.fixture
def scan_gate(monkeypatch: pytest.MonkeyPatch, fakedb: FakeDB) -> ScanGate:
    gate = ScanGate(fakedb)
    monkeypatch.setattr(scan_mod.gate, "evaluate", gate.evaluate)
    return gate


def run_ctx(run_id: str = RUN_ID) -> RunContext:
    return RunContext(
        run_id=run_id,
        principal=Principal(id="dxp-curator", name="dxp-curator", kind="agent", actions=["search_source"]),
        stamp=Stamp(kind="run", run_id=run_id, agent="dxp-curator", initiated_by="sam", principal="dxp-curator",
                    grant_id="lbdx", grant_version=1),
        grant_id="lbdx",
        grant_version=1,
        run_grant_version=1,
    )


@pytest.fixture
def discover_run(fakedb: FakeDB) -> RunContext:
    fakedb["runs"].docs[RUN_ID] = {"_id": RUN_ID, "status": "running", "kind": "discover"}
    fakedb["research_scopes"].docs[SCOPE_ID] = scope_doc()
    return run_ctx()
