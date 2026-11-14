"""python -m dxp.pipeline.prior (Story 1.4): extraction and baseline filing, idempotent."""

from __future__ import annotations

import importlib

import pytest

from dxp.api.models import Principal, RunContext, Stamp

from .conftest import SCOPE_ID, scope_doc, study

prior = importlib.import_module("dxp.pipeline.prior")


def seed_ctx() -> RunContext:
    return RunContext(principal=Principal(id="seed", name="seed", kind="seed", actions=["apply_value"]),
                      stamp=Stamp(kind="seed", principal="seed"), grant_id="seed", grant_version=1, mode="baseline")


def finding(version_id: str, ref: str, dx: str | None) -> dict:
    values = [] if dx is None else [
        {"field": "sample_types", "raw": "plasma", "value": "plasma", "label": "Plasma", "quote": "plasma",
         "check": {"quote_found": True, "supported": True, "confidence": 0.9, "flags": []}},
        {"field": "biomarkers", "raw": "x", "value": "x", "label": "X", "quote": "x",
         "check": {"quote_found": False, "supported": False, "confidence": 0.2, "flags": []}},
    ]
    stage = None if dx is None else {"stage": "clinical_validation", "quote": "q",
                                     "check": {"quote_found": True, "supported": True, "confidence": 0.9, "flags": []}}
    return {"id": f"f_{dx or '-'}", "source_ref": ref, "version_id": version_id, "diagnostic_id": dx,
            "target": "diagnostic" if dx else "scope_collection", "summary": "s", "values": values,
            "stage_evidence": stage, "prompt_version": "test"}


@pytest.fixture
def pipeline_fakes(monkeypatch, fakedb, ctgov_fake):
    fakedb["research_scopes"].docs[SCOPE_ID] = scope_doc("2026-11-01")
    ctgov_fake.studies = {"NCT00000002": study("NCT00000002", "2026-10-31"), "NCT04712877": study("NCT04712877", "2026-11-12")}
    monkeypatch.setattr(prior.source_load, "manifest", lambda: {"setup_item": "NCT05715229", "nct_ids": ["NCT04712877", "NCT00000002", "NCT05715229"]})
    calls = {"extract": [], "file": []}

    async def extract(item, aliases=None):
        calls["extract"].append(item)
        assert "raw_text" in item and item["version_id"].startswith("sv_")
        return {"status": "extracted", "findings": [finding(item["version_id"], item["source_ref"], "dx_1"),
                                                     finding(item["version_id"], item["source_ref"], None)]}

    async def file(finding_id, changes, mode, ctx):
        assert mode == "baseline" and ctx.stamp.kind == "seed" and ctx.run_id is None and len(changes) == 1
        calls["file"].append((finding_id, changes[0]))
        return [{"outcome": "allowed"}]

    monkeypatch.setattr(prior.llm, "extract", extract)
    monkeypatch.setattr(prior.ledger, "file", file)
    return calls


async def test_prior_files_only_evidence_collection_entries(fakedb, pipeline_fakes) -> None:
    """V54 (R19): each trial-level Finding is filed once, as an entry in the scope's evidence
    collection, pinned to its version; nothing else is filed and nothing is filed twice."""
    run = await prior.file_prior(SCOPE_ID, ctx=seed_ctx())
    assert run.extracted == ["NCT00000002"] and run.findings == 1 and run.changes == 1
    assert run.diagnostic_skipped == 1
    files = pipeline_fakes["file"]
    vid = fakedb["source_items"].docs["clinicaltrials.gov:NCT00000002"]["current_version_id"]
    (fid, change), = files
    assert fid == "f_-" and change["field"] == "evidence_collection" and change["value"] == "clinicaltrials.gov:NCT00000002"
    assert change["diagnostic_id"] is None and change["scope_id"] == SCOPE_ID
    assert change["evidence"]["version_id"] == vid and change["evidence"]["source_date"] == "2026-10-31"
    assert set(fakedb["findings"].docs) == {"f_-"}
    # again: nothing is extracted or filed twice
    again = await prior.file_prior(SCOPE_ID, ctx=seed_ctx())
    assert again.already_filed == ["NCT00000002"] and len(pipeline_fakes["extract"]) == 1 and len(files) == 1


async def test_prior_load_files_no_diagnostic_value(fakedb, pipeline_fakes) -> None:
    """Review item (c), Luis's ruling V54 (R19), V37: the extraction returns a Diagnostic Finding with a
    checked value (sample_types) and a checked lifecycle stage; the prior load files neither, and
    stores no Diagnostic Finding."""
    await prior.file_prior(SCOPE_ID, ctx=seed_ctx())
    filed = pipeline_fakes["file"]
    assert filed, "the trial-level Finding is still filed"
    for _, change in filed:
        assert change["field"] == "evidence_collection" and change["diagnostic_id"] is None
        assert change["field"] not in {"sample_types", "biomarkers", "lifecycle_stage"} and "check" not in change
    assert not any(d.get("diagnostic_id") for d in fakedb["findings"].docs.values())
    # changes_for itself returns nothing for a Diagnostic Finding, whatever its checks say
    assert prior.changes_for(finding("sv_x", "clinicaltrials.gov:NCT00000002", "dx_1"), "2026-10-31", SCOPE_ID) == []


async def test_prior_refused_after_a_scan(fakedb, pipeline_fakes) -> None:
    """Review item (a) through the pipeline: once a scan has moved the cursor, nothing is extracted or filed."""
    fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["set_by_run_id"] = "run_x"
    with pytest.raises(prior.source_load.CursorMovedError):
        await prior.file_prior(SCOPE_ID, ctx=seed_ctx())
    assert pipeline_fakes["extract"] == [] and pipeline_fakes["file"] == []


async def test_seed_key_required(monkeypatch) -> None:
    monkeypatch.delenv("DXP_SEED_KEY", raising=False)
    with pytest.raises(PermissionError):
        await prior.seed_context()


async def test_non_seed_key_refused(monkeypatch) -> None:
    async def resolve_actor(key):
        return Principal(id="sam", name="Sam", kind="person")

    monkeypatch.setattr(prior.auth, "resolve_actor", resolve_actor)
    with pytest.raises(PermissionError):
        await prior.seed_context()
