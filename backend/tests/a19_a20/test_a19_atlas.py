"""Atlas Sandbox tests for A19+A20 (marked `atlas`; skipped when MONGODB_URI is unset).

They need a cluster with MongoDB Search: the index test builds the real search and vector
indexes in the session's test database."""

import importlib

import pytest

from dxp import identity, reports, retrieval
from dxp.api.models import Principal, RunContext, Stamp

indexes = importlib.import_module("dxp.retrieval.indexes")
routes = importlib.import_module("dxp.api.routes_reports")

pytestmark = pytest.mark.atlas

RUN = "run_a19atlas"
REF = "ctgov:NCT04712877"
VERSION = "sv_aaaaaaaaaaaaaaaa"


async def test_ensure_indexes_builds_the_search_and_vector_indexes(db, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")
    await retrieval.ensure_indexes()
    await retrieval.ensure_indexes()  # safe to run again
    status = await indexes.index_status("auto")
    assert set(status) == {"vs_source_items", "ts_source_items", "vs_findings", "ts_findings",
                           "vs_memories", "ts_memories"}
    regular = await db["source_items"].index_information()
    assert "tx_source_items" in regular


async def test_related_never_raises_on_an_empty_scope_and_names_its_method(db, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "none")
    result = await retrieval.related("scope_a19_empty", "plasma ctDNA genotyping", 5, [REF])
    assert result.method == "text_search" and result.items == []


async def test_a_filed_report_passes_the_validator_and_reads_back(db, monkeypatch, fake_gate):
    import dxp.actions
    import dxp.evidence
    import dxp.ledger
    import dxp.llm

    answer = {
        "headline": "This study investigates blood and tumour tissue profiling in early-stage lung cancer.",
        "summary": "The trial investigates blood and tissue profiling before surgery.",
        "claims": [{"text": "The trial investigates blood and tissue profiling before surgery.",
                    "claim_kind": "claim_planned", "quote": "blood and tumour tissue"}],
        "gap": "Have early-stage studies that combine plasma ctDNA with tissue profiling posted results?",
        "task": {"condition": "non-small cell lung cancer", "stage": "early", "testing": ["ctDNA or plasma"]},
        "intervention_plain": "ctDNA and tumour NGS", "collection_label": "early-stage profiling study",
    }

    async def call_structured(model, schema, messages):
        return answer

    async def ledger_file(finding_id, changes, mode, ctx):
        return []

    async def dispatch(action, ctx):
        return None

    monkeypatch.setattr(dxp.llm, "call_structured", call_structured)
    monkeypatch.setattr(dxp.evidence, "quote_in_source", lambda quote, raw_text: quote in raw_text, raising=False)
    monkeypatch.setattr(dxp.ledger, "file", ledger_file)
    monkeypatch.setattr(dxp.actions, "dispatch", dispatch)

    item = {
        "source_ref": REF, "version_id": VERSION, "nct_id": "NCT04712877", "scope_id": "scope_a19", "team_id": "team_a19",
        "retrieval": {"method": "text_search", "index": "ts_source_items+ts_findings", "top_k": 5, "items": []},
        "raw_text": "Patients have blood and tumour tissue collected before surgery.", "overall_status": "RECRUITING",
        "has_results": False, "title": "Profiling before surgery", "seeded_names": ["FoundationOne Liquid CDx"],
        "interventions": [{"name": "ctDNA, tumor NGS", "otherNames": ["FoundationOne Liquid"]}],
    }
    draft = await reports.draft(item, [], [], [])
    ctx = RunContext(
        run_id=RUN, principal=Principal(id="dxp-curator", name="DxP curator", kind="agent"),
        stamp=Stamp(kind="run", run_id=RUN, principal="dxp-curator", agent="dxp-curator"),
        grant_id="lbdx", grant_version=1,
    )
    decision = await reports.file(draft, ctx)
    report_id = identity.derive("rep_", RUN, REF)
    stored = await db["reports"].find_one({"_id": report_id})
    assert decision.outcome == "allowed"
    assert stored["status"] == "pending" and stored["run_id"] == RUN and stored["script"]
    from dxp.api import auth

    async def reader(request):
        return Principal(id="sam", name="Sam", kind="person")

    monkeypatch.setattr(auth, "require_principal", reader)
    report = await routes.get_report(None, report_id)
    assert report.id == report_id and report.script_hash == stored["script_hash"]
    assert [r.id for r in (await routes.list_reports(None, status="pending", run_id=RUN)).items] == [report_id]
