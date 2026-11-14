"""A02: schema/registry.py (AD-2, AD-5, Story 1.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from dxp.identity import normalise_name
from dxp.schema import registry
from dxp.schema.registry import (
    EARLY_RESEARCH_STAGES,
    FIELDS,
    LOW_CONFIDENCE_THRESHOLD,
    NOT_DETERMINED,
    STAGE_ORDER,
    CanonicalError,
    canonical,
    describe,
    is_early_research,
    is_later_stage,
    is_low_confidence,
    stage_rank,
)

AD2_CARDINALITY = {
    "modality": "single",
    "regulatory_status": "single",
    "lifecycle_stage": "single",
    "provider": "single",
    "clinical_uses": "list",
    "sample_types": "list",
    "tumour_stage_or_line": "list",
    "biomarkers": "list",
    "tumour_types": "list",
    "trials": "list",
    "linked_drugs": "list",
    "study_results": "list",
}


def test_fields_and_cardinality_match_ad2():
    assert {k: f.cardinality for k, f in FIELDS.items()} == AD2_CARDINALITY


def test_the_ten_agreed_fields_plus_regulatory_status_and_stage_are_present():
    agreed = {  # brief, "Extraction fields", agreed with Medical
        "modality", "biomarkers", "tumour_types", "tumour_stage_or_line",
        "sample_types", "clinical_uses", "study_results", "provider",
        "trials", "linked_drugs",
    }
    assert len(agreed) == 10
    assert agreed | {"regulatory_status", "lifecycle_stage"} == set(FIELDS)


def test_every_field_has_a_label():
    assert all(f.label for f in FIELDS.values())


def test_enum_fields_have_options_and_free_fields_do_not():
    for key in ("modality", "regulatory_status", "lifecycle_stage", "clinical_uses",
                "sample_types", "tumour_stage_or_line", "biomarkers", "tumour_types"):
        assert FIELDS[key].enum, key
    for key in ("provider", "trials", "linked_drugs", "study_results"):
        assert FIELDS[key].enum is None, key


def test_unknown_field_is_a_key_error():
    with pytest.raises(KeyError):
        canonical("sensitivity", "90%")


# --- Lifecycle stage (AD-5) ---------------------------------------------------------


def test_stage_order_is_the_nine_glossary_stages():
    assert STAGE_ORDER == (
        "discovery", "assay_development", "analytical_validation",
        "clinical_validation", "clinical_utility", "regulatory_approval",
        "guideline_inclusion", "reimbursement", "adoption",
    )


def test_lifecycle_enum_is_the_stage_order_plus_not_determined():
    assert FIELDS["lifecycle_stage"].enum == (*STAGE_ORDER, NOT_DETERMINED)


def test_stage_rank_and_is_later_stage():
    assert stage_rank("discovery") < stage_rank("regulatory_approval") < stage_rank("adoption")
    assert stage_rank(NOT_DETERMINED) < stage_rank("discovery")
    assert is_later_stage("clinical_validation", "assay_development")
    assert not is_later_stage("assay_development", "clinical_validation")
    assert not is_later_stage("regulatory_approval", "regulatory_approval")
    assert is_later_stage("discovery", None)
    assert is_later_stage("discovery", NOT_DETERMINED)
    with pytest.raises(ValueError):
        stage_rank("phase_3")


@pytest.mark.parametrize("stage", STAGE_ORDER + (NOT_DETERMINED, None))
def test_is_early_research_only_for_discovery_and_assay_development(stage):
    assert is_early_research(stage) is (stage in {"discovery", "assay_development"})


def test_early_research_stages_constant():
    assert EARLY_RESEARCH_STAGES == {"discovery", "assay_development"}


def test_fda_rows_canonicalise_to_regulatory_approval():
    assert canonical("lifecycle_stage", "Regulatory approval") == "regulatory_approval"
    assert canonical("lifecycle_stage", "regulatory_approval") == "regulatory_approval"


# --- Confidence threshold ---------------------------------------------------------------


def test_low_confidence_threshold():
    assert 0 < LOW_CONFIDENCE_THRESHOLD < 1
    assert is_low_confidence(LOW_CONFIDENCE_THRESHOLD - 0.01)
    assert not is_low_confidence(LOW_CONFIDENCE_THRESHOLD)
    assert is_low_confidence(None)


# --- canonical() ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field, raw, expected",
    [
        ("modality", "Next-generation sequencing", "ngs"),
        ("modality", "NGS", "ngs"),
        ("modality", "droplet digital PCR", "pcr"),
        ("modality", "Immunohistochemistry", "ihc"),
        ("regulatory_status", "PMA", "fda_approved"),
        ("regulatory_status", "510(k)", "fda_cleared"),
        ("regulatory_status", "fda_approved", "fda_approved"),
        ("clinical_uses", "Companion diagnostic", "treatment_selection"),
        ("clinical_uses", "MRD", "mrd"),
        ("clinical_uses", "molecular residual disease", "mrd"),
        ("sample_types", "Plasma", "plasma"),
        ("sample_types", "cfDNA", "plasma"),
        ("sample_types", "FFPE tissue", "tissue"),
        ("sample_types", "tumor tissue", "tissue"),
        ("sample_types", "Whole blood", "blood"),
        ("tumour_stage_or_line", "Stage IIIA", "stage_iii"),
        ("tumour_stage_or_line", "first-line", "first_line"),
        ("tumour_stage_or_line", "Neoadjuvant", "neoadjuvant"),
        ("tumour_stage_or_line", "advanced or metastatic", "metastatic"),
        ("biomarkers", "EGFR", "EGFR"),
        ("biomarkers", "egfr exon 19 deletion", "EGFR"),
        ("biomarkers", "KRAS G12C", "KRAS"),
        ("biomarkers", "HER2", "ERBB2"),
        ("biomarkers", "PD-L1", "CD274"),
        ("biomarkers", "PD-L1 expression", "CD274"),
        ("biomarkers", "c-MET", "MET"),
        ("biomarkers", "MET exon 14 skipping", "MET"),
        ("biomarkers", "ROS1 fusion", "ROS1"),
        ("biomarkers", "Tumor mutational burden", "tmb"),
        ("tumour_types", "Non-small cell lung cancer", "NSCLC"),
        ("tumour_types", "NSCLC", "NSCLC"),
        ("tumour_types", "lung adenocarcinoma", "LUAD"),
        ("tumour_types", "Small Cell Lung Carcinoma", "SCLC"),
        ("trials", "nct04712877", "NCT04712877"),
        ("trials", " NCT05715229 ", "NCT05715229"),
        ("provider", "Foundation Medicine, Inc.", "foundation medicine inc"),
        ("provider", "Guardant Health®", "guardant health"),
        ("linked_drugs", "  Osimertinib ", "osimertinib"),
        ("linked_drugs", "Amivantamab-vmjw", "amivantamab-vmjw"),
        ("study_results", "  ORR  was\n 64%  ", "ORR was 64%"),
    ],
)
def test_canonical(field, raw, expected):
    assert canonical(field, raw) == expected


@pytest.mark.parametrize(
    "field, raw",
    [
        ("modality", "mass spectrometry imaging"),
        ("sample_types", "saliva"),
        ("biomarkers", "XYZ123"),
        ("biomarkers", "exon 19 deletion EGFR"),  # marker must lead
        ("tumour_types", "breast cancer"),
        ("trials", "NCT123"),
        ("trials", "ISRCTN12345678"),
        ("regulatory_status", "approved in Narnia"),
        ("lifecycle_stage", "phase 3"),
        ("modality", ""),
        ("study_results", "   "),
        ("provider", "®"),
    ],
)
def test_canonical_refuses_values_it_cannot_place(field, raw):
    with pytest.raises(CanonicalError):
        canonical(field, raw)


def test_canonical_refuses_non_strings():
    with pytest.raises(CanonicalError):
        canonical("trials", None)


def test_canonical_is_idempotent():
    samples = {
        "modality": "Next-generation sequencing",
        "biomarkers": "PD-L1 expression",
        "tumour_types": "lung adenocarcinoma",
        "trials": "nct04712877",
        "provider": "Guardant Health®",
        "linked_drugs": "Osimertinib",
        "sample_types": "cfDNA",
    }
    for field, raw in samples.items():
        once = canonical(field, raw)
        assert canonical(field, once) == once, field


def test_provider_uses_identity_normalise_name():
    assert canonical("provider", "Agilent Technologies") == normalise_name("Agilent Technologies")


def test_canonical_enum_values_are_registry_values():
    for key, f in FIELDS.items():
        if f.enum:
            for opt in f.options:
                assert canonical(key, opt.value) == opt.value
                assert canonical(key, opt.label) == opt.value


def test_hgnc_symbols_are_upper_case_and_analytes_lower_case():
    for opt in FIELDS["biomarkers"].options:
        assert opt.value.isupper() or opt.value.islower()


def test_registry_canonicalises_values_never_diagnostic_names():
    # The registry is not a back door for the removed aliases (V34).
    for name in ("FoundationOne Liquid", "Guardant360", "FoundationOne"):
        for key in FIELDS:
            if FIELDS[key].enum:
                with pytest.raises(CanonicalError):
                    canonical(key, name)


# --- describe() for GET /schema --------------------------------------------------------------


def test_describe_is_json_and_carries_fields_enums_stage_order_and_threshold():
    out = describe()
    json.dumps(out)  # plain JSON
    assert [f["key"] for f in out["fields"]] == list(FIELDS)
    by_key = {f["key"]: f for f in out["fields"]}
    assert by_key["sample_types"]["cardinality"] == "list"
    assert {"value": "plasma", "label": "Plasma (cell-free DNA)"} in by_key["sample_types"]["enum"]
    assert by_key["trials"]["enum"] is None
    assert out["stage_order"] == list(STAGE_ORDER)
    assert out["early_research_stages"] == ["discovery", "assay_development"]
    assert out["not_determined_stage"] == NOT_DETERMINED
    assert out["low_confidence_threshold"] == LOW_CONFIDENCE_THRESHOLD


def test_registry_reads_no_file_under_data():
    src = Path(registry.__file__).read_text(encoding="utf-8")
    assert "open(" not in src and "read_text" not in src and "json.load" not in src
