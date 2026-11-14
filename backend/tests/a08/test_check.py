"""llm.check(): quote_found from quote_in_source, supported from the check call (AD-6)."""

import asyncio

import anthropic
import httpx

from dxp.llm import Finding, FindingValue, LLMFailure, ValueCheck
from dxp.llm import check_finding as check
from dxp.llm.types import CheckOut, StageEvidence, VerdictOut

SOURCE = "Overall status: TERMINATED. Sample: plasma ctDNA fraction measured before treatment."


def finding(*values, stage=None):
    return Finding(
        id="f_x",
        source_ref="clinicaltrials.gov:NCT05715229",
        version_id="sv_x",
        target="scope_collection",
        summary="s",
        values=list(values),
        stage_evidence=stage,
        prompt_version="t",
    )


def v(field, raw, quote, value="ok"):
    return FindingValue(field=field, raw=raw, value=value, label=raw, quote=quote, check=ValueCheck(confidence=0.8))


def run(coro):
    return asyncio.run(coro)


def test_pass_needs_both_quote_found_and_supported(fake_llm):
    fake_llm.script("CheckOut", CheckOut(verdicts=[VerdictOut(index=0, supported=True), VerdictOut(index=1, supported=False)]))
    f = finding(
        v("sample_types", "plasma", "plasma ctDNA fraction"),
        v("biomarkers", "ctDNA", "ctDNA fraction measured"),
        v("study_results", "response", "responded to treatment"),
    )
    out = run(check(f, SOURCE))
    a, b, c = out.values
    assert a.check.quote_found and a.check.supported and a.passed
    assert b.check.quote_found and not b.check.supported and not b.passed
    assert not c.check.quote_found and not c.check.supported and c.check.detail == "quote_not_found"
    assert a.check.confidence == 0.8
    # The input Finding is not mutated.
    assert not f.values[0].check.quote_found


def test_no_found_quote_means_no_model_call(fake_llm):
    out = run(check(finding(v("biomarkers", "EGFR", "EGFR positive")), SOURCE))
    assert fake_llm.calls == []
    assert not out.values[0].passed


def test_non_canonical_value_is_not_sent_and_fails(fake_llm):
    out = run(check(finding(v("biomarkers", "ctDNA", "plasma ctDNA", value=None)), SOURCE))
    assert fake_llm.calls == []
    assert out.values[0].check.detail == "not_canonical" and not out.values[0].passed


def test_missing_verdict_is_unsupported(fake_llm):
    fake_llm.script("CheckOut", CheckOut(verdicts=[]))
    out = run(check(finding(v("sample_types", "plasma", "plasma ctDNA")), SOURCE))
    assert out.values[0].check.detail == "no_verdict" and not out.values[0].passed


def test_stage_evidence_is_checked(fake_llm):
    fake_llm.script("CheckOut", CheckOut(verdicts=[VerdictOut(index=0, supported=True)]))
    stage = StageEvidence(stage="clinical_validation", raw="clinical validation", quote="Overall status: TERMINATED")
    out = run(check(finding(stage=stage), SOURCE))
    assert out.stage_evidence.passed


def test_model_failure_never_raises_and_fails_closed(fake_llm):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_llm.script("CheckOut", anthropic.PermissionDeniedError("no", response=httpx.Response(403, request=request), body=None))
    out = run(check(finding(v("sample_types", "plasma", "plasma ctDNA")), SOURCE))
    assert isinstance(out.failures[0], LLMFailure) and out.failures[0].step == "check"
    assert out.values[0].check.quote_found and not out.values[0].check.supported
    assert out.values[0].check.detail == "check_failed"
