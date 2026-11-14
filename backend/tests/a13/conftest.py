"""A13 fixtures: a hand-written FDA page, an in-memory async store and a fake ledger.

Nothing here is read from data/ or scripts/data/. The page below is typed by hand in the
shape of the live FDA list (six-column main table, a four-column group-labeling table and the
"Content current as of" line); the live list itself is fetched only by the live test.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[3]


def _row(*cells: str) -> str:
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


FDA_PAGE = (
    "<html><body><h1>List of Cleared or Approved Companion Diagnostic Devices</h1>"
    '<table class="table"><thead><tr><th scope="col">Diagnostic Name (Manufacturer)</th>'
    "<th>Indication - Sample Type</th><th>Drug Trade Name (Generic) NDA / BLA</th>"
    "<th>Biomarker(s)</th><th>Biomarker(s) (Details)</th>"
    "<th>PMA / 510(k) /<br>513(f)(2) / HDE (Approval / Clearance / Grant Date)</th></tr></thead><tbody>"
    + _row(
        "FoundationOne CDx (Foundation Medicine, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Tissue",
        'Tagrisso (osimertinib) <a href="#">NDA 208065</a>',
        "EGFR (HER1)",
        "T790M",
        '<a href="#">P170019</a><br>(11/30/2017)',
    )
    + _row(
        "FoundationOne CDx (Foundation Medicine, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Tissue",
        "Alecensa (alectinib) NDA 208434",
        "ALK",
        "ALK rearrangements",
        "P170019 (11/30/2017)",
    )
    + _row(
        "FoundationOne Liquid CDx (Foundation Medicine, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Plasma",
        "Tabrecta (capmatinib) NDA 213591",
        "MET",
        "MET single nucleotide variants and indels that lead to MET exon 14 skipping",
        "P190032/S001 (07/15/2021)",
    )
    + _row(
        "Guardant360&reg; Liquid CDx (Guardant Health, Inc.)",
        "Non-small cell lung cancer (NSCLC) - Plasma",
        "LUMAKRAS&trade; (sotorasib) NDA 214665",
        "KRAS",
        "KRAS G12C",
        "P250027&nbsp; (05/19/2026)",
    )
    + _row(
        "Guardant360 CDx (Guardant Health, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Plasma",
        "Tagrisso (osimertinib) NDA 208065",
        "EGFR (HER1)",
        "EGFR exon 19 deletions, EGFR exon 21 L858R, and T790M",
        "P200010 (08/07/2020)",
    )
    + _row(
        "Agilent Resolution ctDx FIRST assay (Resolution Bioscience, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Plasma",
        "Krazati (adagrasib) NDA 216340",
        "KRAS",
        "KRAS G12C",
        "P210040 (12/12/2022)",
    )
    + _row(
        "cobas EGFR Mutation Test v2 (Roche Molecular Systems, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Tissue or Plasma",
        "Iressa (gefitinib) NDA 206995",
        "EGFR (HER1)",
        "Exon 19 deletion or exon 21 L858R substitution mutation",
        "P120019/S019 (08/22/0218)",
    )
    + _row(
        "VENTANA MET (SP44) RxDx Assay (Ventana Medical Systems, Inc. (Roche Tissue Diagnostics)",
        "Non-Small Cell Lung Cancer (NSCLC) - Tissue",
        "Emrelis (telisotuzumab vedotin-tllv) BLA 761384",
        "MET",
        "MET protein expression",
        "P240037 (05/14/2025)",
    )
    # an exact duplicate of the first row: same row ID, kept once
    + _row(
        "FoundationOne CDx (Foundation Medicine, Inc.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Tissue",
        "Tagrisso (osimertinib) NDA 208065",
        "EGFR (HER1)",
        "T790M",
        "P170019 (11/30/2017)",
    )
    # not lung
    + _row(
        "OncoMate MSI Dx Analysis System (Promega Corporation)",
        "Solid Tumors - Tissue",
        "Keytruda (pembrolizumab) BLA 125514",
        "MSI-High",
        "Microsatellite instability-High (MSI-H)",
        "P250046 (09/15/2026)",
    )
    # lung, but no PMA or 510(k) number: not kept
    + _row(
        "Example Lung Test (Example Co.)",
        "Non-Small Cell Lung Cancer (NSCLC) - Tissue",
        "Example (exampleinib)",
        "ALK",
        "ALK fusions",
        "pending",
    )
    + "</tbody></table>"
    "<h2>Group labeling</h2><table><tr><th>Diagnostic Name</th><th>Indication</th><th>PMA</th>"
    "<th>Labeling</th></tr>"
    "<tr><td>FoundationOne CDx (Foundation Medicine, Inc.)</td>"
    "<td>Non-Small Cell Lung Cancer (NSCLC) - Tissue</td><td>P170019/S033 (03/16/2022)</td>"
    "<td>Group labeling text</td></tr></table>"
    '<p>Content current as of:</p><p><time datetime="2026-11-03">11/03/2026</time></p>'
    "</body></html>"
)

SCOPE_ASSAYS = (
    "FoundationOne Liquid CDx",
    "Guardant360 CDx",
    "Guardant360® Liquid CDx",
    "Agilent Resolution ctDx FIRST assay",
)


@pytest.fixture
def fda_page() -> str:
    return FDA_PAGE


# ---------------------------------------------------------------------------
# An in-memory async store: just the calls A13's code makes
# ---------------------------------------------------------------------------


def _matches(doc: dict[str, Any], flt: dict[str, Any]) -> bool:
    for key, want in flt.items():
        if isinstance(want, dict) and "$ne" in want:
            if doc.get(key) == want["$ne"]:
                return False
        elif doc.get(key) != want:
            return False
    return True


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def sort(self, keys: Any, direction: int | None = None) -> FakeCursor:
        keys = [(keys, direction or 1)] if isinstance(keys, str) else list(keys)
        for key, d in reversed(keys):
            self._docs.sort(key=lambda doc: (doc.get(key) is None, doc.get(key)), reverse=d < 0)
        return self

    def __aiter__(self):
        async def gen():
            for doc in self._docs:
                yield copy.deepcopy(doc)

        return gen()


class FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self.docs: dict[Any, dict[str, Any]] = {}
        self.writes = 0

    async def update_one(self, flt: dict[str, Any], update: dict[str, Any], upsert: bool = False, **_: Any):
        assert set(update) == {"$setOnInsert"}, f"A13 writes insert-if-absent only, got {update}"
        found = next((d for d in self.docs.values() if _matches(d, flt)), None)
        if found is not None or not upsert:
            return SimpleNamespace(upserted_id=None, matched_count=int(found is not None))
        doc = copy.deepcopy(update["$setOnInsert"])
        doc.setdefault("_id", flt.get("_id"))
        self.docs[doc["_id"]] = doc
        self.writes += 1
        return SimpleNamespace(upserted_id=doc["_id"], matched_count=0)

    async def insert_one(self, doc: dict[str, Any], **_: Any):
        if doc["_id"] in self.docs:
            raise AssertionError(f"duplicate key {doc['_id']} in {self.name}")
        self.docs[doc["_id"]] = copy.deepcopy(doc)
        self.writes += 1
        return SimpleNamespace(inserted_id=doc["_id"])

    async def find_one(self, flt: dict[str, Any], projection: Any = None, sort: Any = None, **_: Any):
        docs = [d for d in self.docs.values() if _matches(d, flt)]
        if sort:
            for key, d in reversed(sort):
                docs.sort(key=lambda doc: doc.get(key), reverse=d < 0)
        return copy.deepcopy(docs[0]) if docs else None

    def find(self, flt: dict[str, Any] | None = None, *_: Any, **__: Any) -> FakeCursor:
        return FakeCursor([d for d in self.docs.values() if _matches(d, flt or {})])

    async def count_documents(self, flt: dict[str, Any]) -> int:
        return sum(1 for d in self.docs.values() if _matches(d, flt))


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection(name))

    def snapshot(self) -> dict[str, dict[Any, dict[str, Any]]]:
        return {name: copy.deepcopy(c.docs) for name, c in self.collections.items()}


@pytest.fixture
def fake_db() -> FakeDB:
    return FakeDB()


# ---------------------------------------------------------------------------
# A fake ledger: gate first (the conftest fake gate), then ensure_diagnostic, file, apply
# ---------------------------------------------------------------------------


@dataclass
class FakeLedger:
    """Stands in for A06's ledger.file in baseline mode, enough to prove the seed's contract:
    one gate evaluation per change before any write; a blocked change writes nothing; an
    allowed one creates the alias and Diagnostic on a miss and files and applies the proposal
    insert-if-absent, with the derived p_ ID."""

    db: Any
    calls: list[tuple[str, list[dict[str, Any]], str, Any]] = field(default_factory=list)

    async def file(self, finding_id: str, changes: list[dict[str, Any]], mode: str, ctx: dict[str, Any]):
        from dxp import gate
        from dxp.api.models import EvidenceRef, ProposedAction, Stamp, Target
        from dxp.identity import derive, normalise_name

        self.calls.append((finding_id, changes, mode, ctx))
        assert mode == "baseline"
        out = []
        for change in changes:
            alias = normalise_name(change["assay_name"])
            dx_id = derive("dx_", alias)
            p_id = derive("p_", finding_id, change["field"], change["value"])
            gate_ctx = SimpleNamespace(
                run_id=ctx["run_id"], stamp=Stamp(**ctx["stamp"]), grant_id=ctx["grant_id"],
                grant_version=ctx["grant_version"], cause=None, request_id=None, policy_set_version=None,
            )
            action = ProposedAction(
                kind="apply_value", destination="ledger",
                target=Target(diagnostic_id=dx_id, proposal_id=p_id),
                inputs={"finding_id": finding_id, "field": change["field"], "value": change["value"], "mode": mode},
                evidence_ref=EvidenceRef(
                    source_ref=change["evidence"]["source_ref"], version_id=change["evidence"]["version_id"],
                    finding_id=finding_id, proposal_id=p_id, quote=change["evidence"]["quote"],
                ),
            )
            decision = await gate.evaluate(gate_ctx, action)
            await self.db["decisions"].update_one(
                {"_id": decision.id},
                {"$setOnInsert": {**decision.model_dump(), "_id": decision.id, "agent": "seed", "initiated_by": "seed"}},
                upsert=True,
            )
            if decision.outcome == "blocked":
                out.append(SimpleNamespace(status="blocked", proposal_id=None))
                continue
            await self.db["aliases"].update_one(
                {"_id": alias},
                {"$setOnInsert": {"_id": alias, "diagnostic_id": dx_id, "created_mode": "baseline"}},
                upsert=True,
            )
            await self.db["diagnostics"].update_one(
                {"_id": dx_id},
                {"$setOnInsert": {"_id": dx_id, "name": change["diagnostic_name"], "created_mode": "baseline",
                                  "created_run_id": None, "stamp": ctx["stamp"]}},
                upsert=True,
            )
            await self.db["proposals"].update_one(
                {"_id": p_id},
                {"$setOnInsert": {"_id": p_id, "finding_id": finding_id, "diagnostic_id": dx_id,
                                  "field": change["field"], "value": change["value"], "status": "applied",
                                  "mode": mode, "run_id": None, "stamp": ctx["stamp"],
                                  "decision_id": decision.id, "evidence": change["evidence"]}},
                upsert=True,
            )
            out.append(SimpleNamespace(status="applied", proposal_id=p_id))
        return out


@pytest.fixture
def fake_ledger(fake_db: FakeDB, fake_gate) -> FakeLedger:
    return FakeLedger(fake_db)


# ---------------------------------------------------------------------------
# scripts/reset_demo.py, loaded by path (the backend imports nothing from scripts/)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def reset_demo():
    path = REPO / "scripts" / "reset_demo.py"
    spec = importlib.util.spec_from_file_location("reset_demo_a13", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
