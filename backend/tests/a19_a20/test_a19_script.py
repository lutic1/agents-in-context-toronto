import pytest

import importlib

script = importlib.import_module("dxp.reports.script")

HEADLINE = ("This study investigates molecular profiling using blood (ctDNA) and tumour tissue in "
            "early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. "
            "No results posted.")
GAP = "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"


def report(**changes):
    base = {
        "nct_id": "NCT04712877",
        "headline": HEADLINE,
        "status_line": "Recruiting; no results posted",
        "gap": GAP,
        "discovery": {
            "trial_status": "RECRUITING",
            "has_results": False,
            "intervention_text": "ctDNA, tumor NGS",
            "mentions": [{"name": "FoundationOne CDx", "resolved_diagnostic_id": None},
                         {"name": "FoundationOne Liquid", "resolved_diagnostic_id": None}],
        },
        "uncertainties": ["The record names 'FoundationOne Liquid'. Whether this is the "
                          "FDA-approved FoundationOne Liquid CDx is not stated."],
    }
    base.update(changes)
    return base


def test_script_is_the_signal_then_its_status_then_the_gap():
    text = script.script_for(report())
    assert text == HEADLINE + " Recruiting; no results posted. Evidence gap: " + GAP


def test_script_adds_nothing_from_outside_its_fields():
    text = script.script_for(report())
    for absent in ("NCT04712877", "FoundationOne", "CDx", "tumor NGS", "FDA"):
        assert absent not in text


def test_script_is_deterministic_and_hash_is_sha256_of_it():
    first, second = script.script_for(report()), script.script_for(report())
    assert first == second
    assert script.script_hash(first) == script.script_hash(second)
    assert len(script.script_hash(first)) == 64
    assert script.script_hash(first) != script.script_hash(first + " ")


def test_status_comes_from_trial_fields_when_there_is_no_status_line():
    r = report(status_line=None, headline="A new trial signal in early-stage lung cancer.")
    assert script.script_for(r) == ("A new trial signal in early-stage lung cancer. "
                                    "Trial status: RECRUITING. No results posted. Evidence gap: " + GAP)


def test_status_already_in_the_headline_is_not_repeated():
    r = report(status_line="No results posted.")
    assert script.script_for(r) == HEADLINE + " Evidence gap: " + GAP


def test_posted_results_are_stated_only_when_the_report_says_so():
    r = report(status_line=None, headline="A completed trial signal.",
               discovery={"trial_status": "COMPLETED", "has_results": True})
    assert "Results posted." in script.script_for(r)
    unknown = report(status_line=None, headline="A trial signal.", discovery={"trial_status": "COMPLETED"})
    assert "esults posted" not in script.script_for(unknown)


def test_a_report_without_a_headline_has_no_script():
    with pytest.raises(ValueError):
        script.script_for(report(headline="  "))


def test_a_report_without_a_gap_still_gets_a_script():
    assert script.script_for(report(gap=None)) == HEADLINE + " Recruiting; no results posted."


def test_the_template_script_passes_its_own_validator():
    r = report()
    assert script.shortening_problems(script.script_for(r), r) == []


SHORT = ("This study investigates blood (ctDNA) and tumour tissue profiling in early-stage "
         "(IA2 to III) lung cancer. No results posted. Evidence gap: have similar studies posted results?")


def test_a_shortening_with_only_the_reports_facts_is_accepted():
    r = report()
    assert script.shortening_problems(SHORT, r) == []
    assert script.accept_shortened(SHORT, r) == SHORT


@pytest.mark.parametrize("candidate,kind", [
    ("Profiling in 120 patients with early-stage lung cancer. No results posted.", "number"),
    ("Profiling in early-stage (IB to III) lung cancer in five centres. No results posted.", "number"),
    ("Profiling in stage IIIA lung cancer, 45% of cases. No results posted.", "number"),
    ("NCT04712877 investigates profiling in early-stage lung cancer. No results posted.", "nct_id"),
    ("This study investigates FoundationOne CDx in early-stage lung cancer.", "assay_name"),
    ("Blood profiling, named FoundationOne Liquid in the record. No results posted.", "assay_name"),
    ("Blood profiling with the Guardant360 CDx test. No results posted.", "assay_name"),
    ("This completed study investigates profiling in early-stage lung cancer.", "status"),
    ("This study investigates profiling in early-stage lung cancer. Results posted.", "status"),
    ("An approved blood test in early-stage lung cancer. No results posted.", "status"),
    ("Profiling in early-stage lung cancer. Not yet recruiting.", "status"),
])
def test_a_shortening_with_a_new_fact_is_rejected(candidate, kind):
    r = report()
    problems = script.shortening_problems(candidate, r)
    assert any(p.startswith(kind + ":") for p in problems), problems
    assert script.accept_shortened(candidate, r) == script.script_for(r)


def test_recruiting_is_not_accepted_on_the_strength_of_not_yet_recruiting():
    r = report(status_line="Not yet recruiting", headline="A trial signal in early-stage lung cancer.")
    problems = script.shortening_problems("A trial signal. Recruiting.", r)
    assert any(p.startswith("status:") for p in problems)
    assert script.shortening_problems("A trial signal. Not yet recruiting.", r) == []


def test_injected_assay_names_are_checked():
    r = report()
    candidate = "Blood profiling with Guardant360 in early-stage lung cancer. No results posted."
    assert any(p.startswith("assay_name:") for p in
               script.shortening_problems(candidate, r, assay_names=["Guardant360"]))


def test_an_assay_name_already_in_the_fields_may_stay_but_not_with_uses_wording():
    r = report(headline="The record names 'FoundationOne CDx' as another name of its intervention. "
                        "No results posted.")
    assert script.shortening_problems(
        "The record names 'FoundationOne CDx'. No results posted.", r) == []
    problems = script.shortening_problems("The trial uses FoundationOne CDx. No results posted.", r)
    assert problems and all(p.startswith("wording:") for p in problems)


@pytest.mark.parametrize("candidate", [None, "", "   ", 7])
def test_an_empty_or_non_text_result_falls_back_to_the_template(candidate):
    r = report()
    assert script.shortening_problems(candidate, r)
    assert script.accept_shortened(candidate, r) == script.script_for(r)


def test_a_longer_result_is_not_a_shortening():
    r = report()
    longer = script.script_for(r) + " This is worth investigating further."
    assert any(p.startswith("longer:") for p in script.shortening_problems(longer, r))
