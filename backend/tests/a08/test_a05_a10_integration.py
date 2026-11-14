"""A08 with A05's real source documents and A10's real calls (main).

- A `source_versions` document built exactly as A05's `store_record` writes it
  (from `ctgov.parse_study` of a minimal API v2 study: a title, a status and
  the intervention names only) goes straight into `extract_item`.
- A10's item step (`pipeline.item.extract`) and the prior collection
  (`pipeline.prior.is_trial_level` / `changes_for`) consume what `llm.extract`
  and `llm.check` return.
Claude is faked; A02's real `identity` and `registry` run over in-memory aliases.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from dxp import identity, llm
from dxp.llm import extract_item
from dxp.llm.types import AssayOut, CheckOut, ExtractOut, FieldOut, TriageOut, VerdictOut
from dxp.pipeline import item as pipeline_item
from dxp.pipeline import prior
from dxp.sources import ctgov
from dxp.sources import load as source_load

from .conftest import NCT04712877_TITLE, SEEDED_NAMES
from .test_a02_wiring import SeededAliases

STUDY = {
    "protocolSection": {
        "identificationModule": {"nctId": "NCT04712877", "briefTitle": NCT04712877_TITLE},
        "statusModule": {"overallStatus": "RECRUITING", "lastUpdatePostDateStruct": {"date": "2026-11-12"}},
        "conditionsModule": {"conditions": ["Lung Cancer"]},
        "armsInterventionsModule": {
            "interventions": [
                {"type": "DIAGNOSTIC_TEST", "name": "ctDNA, tumor NGS",
                 "otherNames": ["FoundationOne CDx", "FoundationOne Liquid"]}
            ]
        },
    },
    "hasResults": False,
}


def source_version_doc(study=STUDY, window="discovered"):
    """What A05's `store_record` inserts into `source_versions` for this study."""
    record = ctgov.parse_study(study)
    vid = source_load.version_id_for(record["source_ref"], record.get("last_update_post_date"), record["content_hash"])
    return {
        "_id": vid,
        "source_ref": record["source_ref"],
        **{k: record.get(k) for k in source_load._COPIED},
        "window": window,
        "previous_version_id": None,
        "run_id": None,
        "fetched_at": datetime.now(UTC),
    }


def source_item_doc(version):
    """The `source_items` document pointing at it (A05)."""
    return {
        "_id": version["source_ref"],
        **{k: version.get(k) for k in source_load._COPIED},
        "current_version_id": version["_id"],
        "window": "discovered",
        "sets": ["discover"],
        "scope_ids": ["scope_plasma"],
    }


def a10_item(version):
    """`pipeline.item.load()`'s merge of the item and its pinned version."""
    src = source_item_doc(version)
    item = {k: v for k, v in src.items() if k not in ("_id", "processed", "embedding")}
    item.update({k: v for k, v in version.items() if k not in ("_id", "embedding")})
    item.update({"source_ref": version["source_ref"], "version_id": version["_id"]})
    return item


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def aliases():
    identity.use_aliases(SeededAliases(SEEDED_NAMES))
    yield
    identity.use_aliases(None)


def script_anchor(fake_llm):
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=True, reason="x"))
    fake_llm.script(
        "ExtractOut",
        ExtractOut(
            summary="This study investigates molecular profiling using blood and tumour tissue in lung cancer.",
            record_fields=[
                FieldOut(field="sample_types", raw_value="blood", quote="Tumor Tissue and Blood", confidence=0.9),
                FieldOut(field="trials", raw_value="NCT04712877", quote="NCT ID: NCT04712877", confidence=0.9),
            ],
            stage_evidence=None,
            assays=[AssayOut(name_as_written="FoundationOne Liquid", seeded_name="unresolved")],
        ),
    )
    fake_llm.script("CheckOut", CheckOut(verdicts=[VerdictOut(index=i, supported=True) for i in range(2)]))


def test_a05_source_version_into_extract_item(fake_llm, aliases):
    version = source_version_doc()
    assert "ctDNA, tumor NGS (DIAGNOSTIC_TEST); other names: FoundationOne CDx, FoundationOne Liquid" in version["raw_text"]
    script_anchor(fake_llm)

    result = run(extract_item(version, SEEDED_NAMES))
    assert result.status == "extracted"
    assert result.source_ref == "clinicaltrials.gov:NCT04712877"
    assert result.version_id == version["_id"] and result.nct_id == "NCT04712877"
    assert result.intervention_texts == ["ctDNA, tumor NGS"]
    assert result.unresolved_names == ["FoundationOne Liquid"]
    record, dx = result.findings
    assert dx.diagnostic_id == identity.diagnostic_id("FoundationOne CDx") and dx.values == []
    assert record.trial_status == "RECRUITING" and record.has_results is False
    assert all(v.passed for v in record.values), [v.check for v in record.values]


def test_a10_item_step_calls_llm_as_on_main(fake_llm, aliases):
    version = source_version_doc()
    item = a10_item(version)
    script_anchor(fake_llm)

    findings = run(pipeline_item.extract(item, SimpleNamespace(seeded_names=SEEDED_NAMES)))

    assert isinstance(findings, list) and all(isinstance(f, dict) for f in findings)
    assert [f["diagnostic_id"] for f in findings] == [None, identity.diagnostic_id("FoundationOne CDx")]
    assert all(f["version_id"] == version["_id"] for f in findings)
    values = findings[0]["values"]
    assert {v["field"] for v in values} == {"sample_types", "trials"}
    assert all(v["check"]["quote_found"] and v["check"]["supported"] for v in values)
    assert item["extraction"]["unresolved_names"] == ["FoundationOne Liquid"]
    assert item["extraction"]["intervention_texts"] == ["ctDNA, tumor NGS"]
    assert {m["name"] for m in item["extraction"]["mentions"]} == {"FoundationOne CDx", "FoundationOne Liquid"}
    # A10 calls llm.check again on each Finding: the verdicts given against the
    # same text are reused, so the support check is asked once, not twice.
    assert len(fake_llm.calls_for("CheckOut")) == 1


def test_a10_not_relevant_and_failed(fake_llm, aliases):
    item = a10_item(source_version_doc())
    info = SimpleNamespace(seeded_names=SEEDED_NAMES)
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=False, reason="x"))
    assert run(pipeline_item.extract(dict(item), info)) is None

    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_llm.script("TriageOut", anthropic.BadRequestError("x", response=httpx.Response(400, request=request), body=None))
    with pytest.raises(pipeline_item.ItemFailed) as err:
        run(pipeline_item.extract(dict(item), info))
    assert err.value.code == "extract_failed:api_error"


def test_llm_check_on_a_changed_text_asks_again(fake_llm, aliases):
    """Reuse is only for the same text: a different source text gets a new verdict."""
    version = source_version_doc()
    script_anchor(fake_llm)
    finding = run(llm.extract(version, SEEDED_NAMES))["findings"][0]
    fake_llm.script("CheckOut", CheckOut(verdicts=[VerdictOut(index=0, supported=False), VerdictOut(index=1, supported=False)]))
    checked = run(llm.check(finding, version["raw_text"] + "\nAn added line."))
    assert len(fake_llm.calls_for("CheckOut")) == 2
    assert not any(v["check"]["supported"] for v in checked["values"])


def test_prior_collection_reads_the_extraction(fake_llm, aliases):
    version = source_version_doc(window="prior")
    script_anchor(fake_llm)
    extraction = run(llm.extract({**version, "version_id": version["_id"]}, SEEDED_NAMES))
    assert extraction["status"] == "extracted"
    trial_level = [f for f in extraction["findings"] if prior.is_trial_level(f)]
    assert len(trial_level) == 1
    changes = prior.changes_for(trial_level[0], "2026-11-12", "scope_plasma")
    assert changes[0]["value"] == "clinicaltrials.gov:NCT04712877"
    assert changes[0]["evidence"]["version_id"] == version["_id"]
    assert changes[0]["evidence"]["finding_id"] == trial_level[0]["id"]
    dx = [f for f in extraction["findings"] if not prior.is_trial_level(f)]
    assert prior.changes_for(dx[0], "2026-11-12", "scope_plasma") == []
