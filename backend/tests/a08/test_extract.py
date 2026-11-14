"""llm.extract(): Story 1.5 and card A08 over fake Claude and fake A02 functions."""

import asyncio
import re

import anthropic
import httpx

from dxp.llm import Extraction
from dxp.llm import extract_item as extract
from dxp.llm.types import AssayOut, CheckOut, ExtractOut, FieldOut, StageOut, TriageOut, VerdictOut

from .conftest import NCT04712877_TITLE, SEEDED, SEEDED_NAMES

USE_OR_STUDY = re.compile(r"\b(uses?|used|using|stud(y|ies|ied)|evaluat\w*)\b", re.IGNORECASE)
OUTCOME = re.compile(r"\b(showed|demonstrat\w*|results show|detected|sensitivity|specificity)\b", re.IGNORECASE)


PRODUCTS = ("FoundationOne CDx", "FoundationOne Liquid", "FoundationOne")


def claims_use_of_a_product(text):
    """A sentence that names a product and says the trial uses or studies it."""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if any(p in sentence for p in PRODUCTS) and USE_OR_STUDY.search(sentence):
            return True
    return False


def run(coro):
    return asyncio.run(coro)


def relevant():
    return TriageOut(concerns_lung_cancer_diagnostic=True, reason="Molecular profiling in lung cancer.")


def all_supported(n=20):
    return CheckOut(verdicts=[VerdictOut(index=i, supported=True) for i in range(n)])


def anchor_extraction(**overrides):
    base = dict(
        summary="This study investigates molecular profiling using blood (ctDNA) and tumour tissue in lung cancer.",
        record_fields=[
            FieldOut(field="sample_types", raw_value="blood", quote="Tumor Tissue and Blood", confidence=0.9),
            FieldOut(field="trials", raw_value="NCT04712877", quote="Patients With Suspected Lung Cancers", confidence=0.6),
        ],
        stage_evidence=None,
        assays=[
            AssayOut(name_as_written="FoundationOne CDx", seeded_name="FoundationOne CDx"),
            AssayOut(name_as_written="FoundationOne Liquid", seeded_name="unresolved"),
        ],
    )
    base.update(overrides)
    return ExtractOut(**base)


# --------------------------------------------------------------------------
# NCT04712877: mentions, exact matching only (V34, V37)
# --------------------------------------------------------------------------


def test_anchor_mentions_and_findings(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction())
    fake_llm.script("CheckOut", all_supported(), all_supported())

    result = run(extract(item_nct04712877, SEEDED_NAMES))

    assert isinstance(result, Extraction)
    assert result.status == "extracted"
    assert result.version_id == "sv_test04712877aaaa"
    assert result.intervention_texts == ["ctDNA, tumor NGS"]

    by_name = {m.name: m for m in result.mentions}
    f1 = by_name["FoundationOne CDx"]
    assert f1.resolution == "exact" and f1.resolved_diagnostic_id == SEEDED["FoundationOne CDx"]
    assert f1.intervention_name == "ctDNA, tumor NGS"
    liquid = by_name["FoundationOne Liquid"]
    assert liquid.resolution == "unresolved" and liquid.resolved_diagnostic_id is None
    assert result.unresolved_names == ["FoundationOne Liquid"]

    plasma = SEEDED["FoundationOne Liquid CDx"]
    assert all(m.resolved_diagnostic_id != plasma for m in result.mentions)
    assert all(f.diagnostic_id != plasma for f in result.findings)
    assert "new" not in {m.resolution for m in result.mentions}

    record, *dx = result.findings
    assert record.diagnostic_id is None and record.target == "scope_collection"
    assert [f.diagnostic_id for f in dx] == [SEEDED["FoundationOne CDx"]]
    assert dx[0].target == "diagnostic"
    assert [m.name for m in dx[0].mentions] == ["FoundationOne CDx"]

    for f in result.findings:
        assert not claims_use_of_a_product(f.summary), f.summary
        assert "FoundationOne Liquid CDx" not in f.summary
        assert f.version_id == "sv_test04712877aaaa"
    assert "no results posted" in record.summary
    assert "recruiting" in record.summary


def test_every_passing_value_has_a_found_quote(fake_registry, fake_llm, item_nct04712877):
    bad_quote = FieldOut(field="biomarkers", raw_value="EGFR", quote="EGFR mutations were detected", confidence=0.9)
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction(record_fields=anchor_extraction().record_fields + [bad_quote]))
    fake_llm.script("CheckOut", all_supported(), all_supported())

    result = run(extract(item_nct04712877, SEEDED_NAMES))
    record = result.findings[0]
    egfr = next(v for v in record.values if v.field == "biomarkers")
    assert not egfr.check.quote_found and not egfr.check.supported and not egfr.passed
    for v in record.values:
        if v.passed:
            assert v.check.quote_found and v.check.supported
    # Only found quotes were sent to the check call.
    check_prompt = fake_llm.calls_for("CheckOut")[0]["messages"][1][1]
    assert "EGFR mutations were detected" not in check_prompt


def test_model_mapping_a_partial_name_is_rejected(fake_registry, fake_llm, item_nct04712877):
    """'FoundationOne Liquid' claimed as 'FoundationOne Liquid CDx' stays unresolved (V34)."""
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        anchor_extraction(
            assays=[AssayOut(name_as_written="FoundationOne Liquid", seeded_name="FoundationOne Liquid CDx")]
        ),
    )
    fake_llm.script("CheckOut", all_supported(), all_supported())

    result = run(extract(item_nct04712877, SEEDED_NAMES))
    assert "model_mapped_unmatched_name" in [f.code for f in result.failures]
    assert result.unresolved_names == ["FoundationOne Liquid"]
    plasma = SEEDED["FoundationOne Liquid CDx"]
    assert all(f.diagnostic_id != plasma for f in result.findings)


def test_seeded_name_outside_the_list_is_a_failure_record(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        anchor_extraction(assays=[AssayOut(name_as_written="FoundationOne CDx", seeded_name="Foundation Medicine")]),
    )
    fake_llm.script("CheckOut", all_supported(), all_supported())

    result = run(extract(item_nct04712877, SEEDED_NAMES))
    assert "seeded_name_not_allowed" in [f.code for f in result.failures]
    # The structured otherNames mention still resolves exactly.
    assert SEEDED["FoundationOne CDx"] in [f.diagnostic_id for f in result.findings]


def test_assay_name_not_in_the_record_is_rejected(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        anchor_extraction(assays=[AssayOut(name_as_written="Guardant360 CDx", seeded_name="Guardant360 CDx")]),
    )
    fake_llm.script("CheckOut", all_supported(), all_supported())

    result = run(extract(item_nct04712877, SEEDED_NAMES))
    assert "assay_name_not_in_source" in [f.code for f in result.failures]
    assert SEEDED["Guardant360 CDx"] not in [f.diagnostic_id for f in result.findings]


def test_summary_naming_or_claiming_use_is_replaced(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        anchor_extraction(summary="The trial uses FoundationOne Liquid and showed EGFR detection in 40% of patients."),
    )
    fake_llm.script("CheckOut", all_supported(), all_supported())

    record = run(extract(item_nct04712877, SEEDED_NAMES)).findings[0]
    assert "FoundationOne" not in record.summary
    assert not OUTCOME.search(record.summary)
    assert record.summary.startswith(NCT04712877_TITLE)


def test_stage_evidence_is_at_most_one_and_checked(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        anchor_extraction(stage_evidence=StageOut(stage="clinical validation", quote="ctDNA, tumor NGS", confidence=0.5)),
    )
    fake_llm.script("CheckOut", all_supported(), all_supported())

    record = run(extract(item_nct04712877, SEEDED_NAMES)).findings[0]
    assert record.stage_evidence is not None
    assert record.stage_evidence.stage == "clinical_validation"
    assert record.stage_evidence.check.quote_found and record.stage_evidence.check.supported


def test_unknown_field_is_a_failure_record(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        anchor_extraction(record_fields=[FieldOut(field="regulatory_status", raw_value="approved", quote="ctDNA", confidence=1)]),
    )
    fake_llm.script("CheckOut", all_supported(), all_supported())

    result = run(extract(item_nct04712877, SEEDED_NAMES))
    assert "field_not_allowed" in [f.code for f in result.findings[0].failures]
    assert result.findings[0].values == []


# --------------------------------------------------------------------------
# NCT05715229: status without outcomes; triage; failures
# --------------------------------------------------------------------------


def test_terminated_trial_states_status_not_outcomes(fake_registry, fake_llm, item_nct05715229):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script(
        "ExtractOut",
        ExtractOut(
            summary="The trial showed that ctDNA fraction predicted response to immunotherapy.",
            record_fields=[],
            stage_evidence=None,
            assays=[],
        ),
    )
    result = run(extract(item_nct05715229, SEEDED_NAMES))
    assert result.status == "extracted"
    record = result.findings[0]
    assert "terminated" in record.summary and "no results posted" in record.summary
    assert not OUTCOME.search(record.summary)
    # A drug's brand name is not an unresolved assay name.
    assert result.unresolved_names == []
    assert result.intervention_texts == ["Nivolumab"]


def test_item_rejected_at_triage_is_done_with_no_finding(fake_registry, fake_llm, item_nct05715229):
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=False, reason="Not a diagnostic."))
    result = run(extract(item_nct05715229, SEEDED_NAMES))
    assert result.status == "not_relevant"
    assert result.findings == [] and result.failures == []
    assert fake_llm.calls_for("ExtractOut") == []
    assert fake_llm.calls[0]["model"] == "claude-haiku-5-5"


def test_extraction_and_check_use_the_strong_model(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction())
    fake_llm.script("CheckOut", all_supported(), all_supported())
    run(extract(item_nct04712877, SEEDED_NAMES))
    assert {c["model"] for c in fake_llm.calls_for("ExtractOut")} == {"claude-sonnet-5-5"}
    assert {c["model"] for c in fake_llm.calls_for("CheckOut")} == {"claude-sonnet-5-5"}


def test_extraction_prompt_is_given_the_seeded_names(fake_registry, fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction())
    fake_llm.script("CheckOut", all_supported(), all_supported())
    run(extract(item_nct04712877, SEEDED_NAMES))
    system = fake_llm.calls_for("ExtractOut")[0]["messages"][0][1]
    for name in SEEDED_NAMES:
        assert f"- {name}" in system


def test_model_error_returns_a_failure_record_without_source_text(fake_registry, fake_llm, item_nct04712877, caplog):
    caplog.set_level("DEBUG", logger="dxp.llm")
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    err = anthropic.BadRequestError(item_nct04712877["raw_text"], response=httpx.Response(400, request=request), body=None)
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", err)

    result = run(extract(item_nct04712877, SEEDED_NAMES))
    assert result.status == "failed"
    assert [f.code for f in result.failures] == ["api_error"]
    dumped = result.model_dump_json(exclude={"mentions", "intervention_texts", "unresolved_names"})
    assert NCT04712877_TITLE not in dumped
    assert NCT04712877_TITLE not in caplog.text
    # Mentions are still reported from the structured record.
    assert result.unresolved_names == ["FoundationOne Liquid"]


def test_invalid_item_never_raises(fake_registry, fake_llm):
    result = run(extract({"source_ref": "clinicaltrials.gov:NCT00000000", "raw_text": "x"}))
    assert result.status == "failed"
    assert result.failures[0].code == "invalid_item_version_id"
    assert fake_llm.calls == []


def test_resolver_crash_is_recorded_not_raised(fake_registry, fake_llm, item_nct04712877, monkeypatch):
    from dxp.llm import _deps

    async def boom(name):
        raise RuntimeError("db down")

    monkeypatch.setattr(_deps, "resolve_exact", boom)
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=False, reason="x"))
    result = run(extract(item_nct04712877, SEEDED_NAMES))
    assert "resolve_error" in [f.code for f in result.failures]
    assert all(m.resolved_diagnostic_id is None for m in result.mentions)


def test_finding_ids_derive_from_the_pinned_version(fake_registry, fake_llm, item_nct04712877):
    from .conftest import fake_derive

    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction())
    fake_llm.script("CheckOut", all_supported(), all_supported())
    result = run(extract(item_nct04712877, SEEDED_NAMES))
    record, dx = result.findings
    assert record.id == fake_derive("f_", "sv_test04712877aaaa", "-")
    assert dx.id == fake_derive("f_", "sv_test04712877aaaa", SEEDED["FoundationOne CDx"])


def test_a_mentioned_product_carries_no_values(fake_registry, fake_llm, item_nct04712877):
    """V37: the FoundationOne CDx Finding records the mention only; the record's
    values (e.g. sample type blood) stay on the record-level Finding."""
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction())
    fake_llm.script("CheckOut", all_supported(), all_supported())
    result = run(extract(item_nct04712877, SEEDED_NAMES))
    record, dx = result.findings
    assert dx.diagnostic_id == SEEDED["FoundationOne CDx"]
    assert dx.values == [] and dx.stage_evidence is None
    assert [v.field for v in record.values] == ["sample_types", "trials"]
    assert "fields" not in AssayOut.model_fields


def test_fallback_title_naming_a_product_is_not_used(fake_registry, fake_llm, item_nct04712877):
    item = dict(item_nct04712877, title="FoundationOne CDx in lung cancer")
    fake_llm.script("TriageOut", relevant())
    fake_llm.script("ExtractOut", anchor_extraction(summary="The trial uses FoundationOne CDx."))
    fake_llm.script("CheckOut", all_supported(), all_supported())
    record = run(extract(item, SEEDED_NAMES)).findings[0]
    assert "FoundationOne" not in record.summary
    assert record.summary.startswith("Clinical trial record.")


def test_unresolved_test_name_is_kept_for_uncertainties(fake_registry, fake_llm, item_nct04712877):
    item = dict(item_nct04712877, interventions=[{"type": "DIAGNOSTIC_TEST", "name": "Guardant360", "otherNames": []}])
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=False, reason="x"))
    result = run(extract(item, SEEDED_NAMES))
    assert result.unresolved_names == ["Guardant360"]
