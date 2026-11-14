"""The ClinicalTrials.gov client (A05): fields kept, query building, paging, errors."""

from __future__ import annotations

import pytest

from dxp.sources import ctgov

from .conftest import study


def test_parse_keeps_status_results_date_and_interventions_verbatim() -> None:
    ivs = [{"type": "DIAGNOSTIC_TEST", "name": "ctDNA, tumor NGS", "otherNames": ["FoundationOne CDx", "FoundationOne Liquid"]}]
    rec = ctgov.parse_study(study("NCT04712877", "2026-11-12", interventions=ivs))
    assert rec["source_ref"] == "clinicaltrials.gov:NCT04712877"
    assert rec["overall_status"] == "RECRUITING"
    assert rec["has_results"] is False
    assert rec["last_update_post_date"] == "2026-11-12"
    # V37: otherNames stored verbatim, as name mentions, every key kept
    assert rec["interventions"] == ivs
    assert "other names: FoundationOne CDx, FoundationOne Liquid" in rec["raw_text"]
    assert "ctDNA, tumor NGS" in rec["evidence_text"]
    assert "Overall status: RECRUITING" in rec["evidence_text"]


def test_content_hash_ignores_whitespace_only() -> None:
    assert ctgov.content_hash("a  b\n c") == ctgov.content_hash("a b c")
    assert ctgov.content_hash("a b c") != ctgov.content_hash("a b d")
    assert len(ctgov.content_hash("x")) == 16


def test_query_terms_are_quoted_and_or_joined() -> None:
    assert ctgov.or_terms(["Guardant360® Liquid CDx", "ctDNA", "ctDNA", ""]) == '"Guardant360® Liquid CDx" OR "ctDNA"'
    params = ctgov.search_params('"x"', "non-small cell lung cancer", "2026-11-01")
    assert params["filter.advanced"] == "AREA[LastUpdatePostDate]RANGE[2026-11-01,MAX]"
    assert params["query.cond"] == "non-small cell lung cancer"


def test_check_nct_rejects_bad_ids() -> None:
    assert ctgov.check_nct(" nct04712877 ") == "NCT04712877"
    with pytest.raises(ValueError):
        ctgov.check_nct("NCT123")


async def test_search_reads_every_page(ctgov_fake) -> None:
    ctgov_fake.pages = [[study("NCT00000001", "2026-11-02")], [study("NCT00000002", "2026-11-03")]]
    res = await ctgov.search('"ctDNA"', "nsclc", "2026-11-01")
    assert res.complete and res.pages == 2 and len(res.studies) == 2
    assert ctgov_fake.searches[1].url.params["pageToken"] == "1"


async def test_search_cap_marks_incomplete(ctgov_fake) -> None:
    ctgov_fake.pages = [[study("NCT00000001", "2026-11-02")], [study("NCT00000002", "2026-11-03")]]
    res = await ctgov.search('"ctDNA"', "nsclc", "2026-11-01", max_pages=1)
    assert not res.complete and len(res.studies) == 1


async def test_server_error_raises_after_one_retry(ctgov_fake) -> None:
    ctgov_fake.status = 503
    with pytest.raises(ctgov.CtgovError) as err:
        await ctgov.search('"ctDNA"', "nsclc", "2026-11-01")
    assert err.value.http_status == 503
    assert len(ctgov_fake.requests) == 2


async def test_fetch_study_404(ctgov_fake) -> None:
    with pytest.raises(ctgov.StudyNotFound):
        await ctgov.fetch_study("NCT00000009")


def test_order_newest_first_with_anchor_first() -> None:
    recs = [ctgov.parse_study(study(n, d)) for n, d in
            [("NCT00000001", "2026-11-02"), ("NCT00000002", "2026-11-13"), ("NCT04712877", "2026-11-12")]]
    assert ctgov.order_refs(recs) == [
        "clinicaltrials.gov:NCT00000002", "clinicaltrials.gov:NCT04712877", "clinicaltrials.gov:NCT00000001"]
    assert ctgov.order_refs(recs, "NCT04712877")[0] == "clinicaltrials.gov:NCT04712877"
