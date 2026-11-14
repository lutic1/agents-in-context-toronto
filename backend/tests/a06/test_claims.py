"""Claim checks (Story 10.7, V7, V21): pure, no Atlas needed."""

from __future__ import annotations

from dxp.gate import claims as c

ALL = c.CLAIM_POLICIES
RECRUITING = {"overall_status": "RECRUITING", "has_results": False}


def judge(claims, source=RECRUITING, quotes=(), policies=ALL):
    return c.evaluate_claims(claims, source, list(quotes), policies)


def test_showed_on_recruiting_trial_without_results_is_blocked_and_redraft_allowed():
    draft1 = [{"claim_kind": "claim_performed_or_results",
               "text": "NCT04712877 showed blood profiling detecting actionable drivers."}]
    out = judge(draft1)
    assert out[0]["passed"] is False
    assert "claim_performed_or_results" in out[0]["failed_policies"]

    draft2 = [{"claim_kind": "claim_planned", "text": "NCT04712877 is recruiting; no results posted."}]
    out = judge(draft2)
    assert out[0]["passed"] is True, out


def test_demo_signal_wording_passes():
    text = ("This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage "
            "(IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted.")
    assert judge([{"claim_kind": "claim_planned", "text": text}])[0]["passed"] is True


def test_performed_claim_passes_with_posted_results():
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "The assay detected EGFR mutations."}],
                source={"overall_status": "COMPLETED", "has_results": True})
    assert out[0]["passed"] is True


def test_performed_claim_passes_with_its_own_checked_quote_saying_it_was_performed_with_results():
    quote = "ctDNA genotyping detected EGFR mutations in 40 of 52 patients"
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "Plasma genotyping detected EGFR mutations.",
                  "quote": quote}],
                source={"overall_status": "COMPLETED", "has_results": False},
                quotes=[{"text": quote, "quote_found": True}])
    assert out[0]["passed"] is True


def test_only_the_claims_own_quote_may_support_a_performance_claim():
    background = {"text": "Guardant360 detects EGFR mutations in plasma.", "quote_found": True}
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "NCT04712877 showed X."}],
                source={"overall_status": "COMPLETED", "has_results": False}, quotes=[background])
    assert out[0]["passed"] is False
    # its own quote, but present tense background wording: not "performed with results"
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "NCT04712877 showed X.",
                  "quote": background["text"]}],
                source={"overall_status": "COMPLETED", "has_results": False}, quotes=[background])
    assert out[0]["passed"] is False


def test_redraft_tagged_performed_or_results_without_a_performance_statement_passes():
    """DEMO-CRITICAL (V21): draft 2 passes whichever claim kind the drafter gave it."""
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "NCT04712877 is recruiting; no results posted."}])
    assert out[0]["passed"] is True and "no performance or results statement" in out[0]["detail"]


def test_an_unchecked_quote_does_not_support_a_performed_claim():
    quote = {"text": "ctDNA genotyping detected EGFR mutations", "quote_found": False}
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "Plasma genotyping detected EGFR."}],
                source={"overall_status": "COMPLETED", "has_results": False}, quotes=[quote])
    assert out[0]["passed"] is False


def test_mis_tagged_performance_claim_is_still_caught():
    out = judge([{"claim_kind": "other", "text": "The trial demonstrated high concordance."}],
                policies=["claim_performed_or_results"])
    assert out[0]["failed_policies"] == ["claim_performed_or_results"]


def test_infinitives_and_negations_are_not_performance_claims():
    for text in ("The study aims to detect actionable drivers.", "No results posted.", "It is detecting nothing yet"):
        assert not c.states_performed_or_results(text), text


def test_claim_planned_blocks_on_its_own():
    out = judge([{"claim_kind": "claim_planned", "text": "The trial has completed enrolment."}],
                policies=["claim_planned"])
    assert out[0]["failed_policies"] == ["claim_planned"]
    out = judge([{"claim_kind": "claim_planned", "text": "The trial is about lung cancer."}],
                policies=["claim_planned"])
    assert out[0]["passed"] is False  # not described as planned or ongoing
    out = judge([{"claim_kind": "claim_planned", "text": "The trial is ongoing."}],
                source={"overall_status": "NOT_YET_RECRUITING", "has_results": False}, policies=["claim_planned"])
    assert out[0]["passed"] is True


def test_claim_planned_does_not_apply_to_a_completed_trial():
    out = judge([{"claim_kind": "claim_planned", "text": "The trial has completed enrolment."}],
                source={"overall_status": "COMPLETED", "has_results": False}, policies=["claim_planned"])
    assert out[0]["passed"] is True


def test_claim_preclinical_blocks_on_its_own():
    out = judge([{"claim_kind": "claim_preclinical", "text": "The assay finds KRAS in mice."}],
                policies=["claim_preclinical"])
    assert out[0]["failed_policies"] == ["claim_preclinical"]
    out = judge([{"claim_kind": "claim_preclinical", "text": "In preclinical work in mice, the assay finds KRAS."}],
                policies=["claim_preclinical"])
    assert out[0]["passed"] is True


def test_preclinical_evidence_in_the_quote_needs_the_label():
    out = judge([{"claim_kind": "other", "text": "The assay finds KRAS.", "quote": "xenograft models carried KRAS"}],
                policies=["claim_preclinical"])
    assert out[0]["failed_policies"] == ["claim_preclinical"]


def test_a_policy_not_in_the_set_does_not_judge():
    out = judge([{"claim_kind": "claim_performed_or_results", "text": "It showed results."}],
                policies=["claim_preclinical"])
    assert out[0]["passed"] is True


def test_failed_claim_policies_in_policy_order():
    out = judge([
        {"claim_kind": "claim_preclinical", "text": "Cell lines responded."},
        {"claim_kind": "claim_performed_or_results", "text": "The assay showed results."},
    ])
    assert c.failed_claim_policies(out) == ["claim_performed_or_results", "claim_planned", "claim_preclinical"]


def test_item5_an_eligibility_sentence_is_not_a_result():
    """Review item 5 (Luis, 6881072627): the probe. "Tumor NGS was performed" is not supported
    by an eligibility sentence; the quote must state a result, otherwise has_results: true."""
    quote = "Inclusion: patients in whom tumor NGS was performed within 90 days are eligible"
    claim = {"claim_kind": "claim_performed_or_results", "text": "Tumor NGS was performed.", "quote": quote}
    found = [{"text": quote, "quote_found": True}]
    out = judge([claim], source={"overall_status": "RECRUITING", "has_results": False}, quotes=found)
    assert out[0]["passed"] is False and out[0]["failed_policies"][0] == "claim_performed_or_results"
    assert "states no result" in out[0]["detail"]
    # a bare "was performed" outside any eligibility wording is not a result either
    bare = "Tumor NGS was performed on resected specimens"
    out = judge([{**claim, "quote": bare}], source={"overall_status": "COMPLETED", "has_results": False},
                quotes=[{"text": bare, "quote_found": True}])
    assert out[0]["passed"] is False
    # has_results: true still supports the same claim
    out = judge([claim], source={"overall_status": "COMPLETED", "has_results": True}, quotes=found)
    assert out[0]["passed"] is True
    # a quote that states a result supports it
    result = "Tumor NGS identified actionable drivers in 31 of 60 resected tumours"
    out = judge([{**claim, "quote": result}], source={"overall_status": "COMPLETED", "has_results": False},
                quotes=[{"text": result, "quote_found": True}])
    assert out[0]["passed"] is True, out
    # the redraft still passes under either claim kind
    for kind in ("claim_performed_or_results", "claim_planned"):
        out = judge([{"claim_kind": kind, "text": "NCT04712877 is recruiting; no results posted."}])
        assert out[0]["passed"] is True, out
