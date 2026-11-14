"""Status, results and "what is this about" answer from the pinned version's own labelled lines (V70).

The drafting model rarely quotes the status or results line, so a pending report with no such quote must still
answer verbatim from its raw text, under the same checks. A medical question still gets the fixed refusal.
"""

from __future__ import annotations

import pytest

from dxp.interview import service, texts
from tests.interview.conftest import REPORT_ID, VERSION_ID, make_report

# The raw text as `sources.ctgov.build_raw_text` writes it: one labelled line each, single newlines.
CTGOV_RAW = "\n".join(
    [
        "NCT ID: NCT04712877",
        "Title: Plasma ctDNA genotyping in early-stage lung cancer",
        "Overall status: RECRUITING",
        "Has results: no",
        "Last update posted: 2026-01-10",
        "Lead sponsor: Example University Hospital",
        "Study type: OBSERVATIONAL",
        "Phases: NA",
        "Conditions: Lung Cancer; Non-Small Cell Lung Cancer",
        "Brief summary: This study investigates molecular profiling using blood (ctDNA) in lung cancer.",
    ]
)
CLAIM_QUOTE = "This study investigates molecular profiling using blood (ctDNA) in lung cancer."


@pytest.fixture
def pending_store(store):
    report = make_report(status="pending")
    report["discovery"]["quotes"] = [{"text": CLAIM_QUOTE, "quote_found": True, "version_id": VERSION_ID}]
    store.reports[REPORT_ID] = report
    store.raw[VERSION_ID] = CTGOV_RAW
    return store


async def _ask(store, question: str):
    return await service.plan_answer(store.reports[REPORT_ID], question)


async def test_results_question_answers_verbatim(pending_store) -> None:
    draft = await _ask(pending_store, "Has this trial posted any results?")
    assert draft.outcome == service.OUTCOME_ANSWERED, draft.detail
    assert [c.text for c in draft.cards] == ["Has results: no"]
    assert draft.cards[0].field == "results" and draft.cards[0].version_id == VERSION_ID
    assert '"Has results: no" [1]' in draft.answer


async def test_status_question_answers_verbatim(pending_store) -> None:
    draft = await _ask(pending_store, "What is the trial's recruitment status?")
    assert draft.outcome == service.OUTCOME_ANSWERED, draft.detail
    assert [c.text for c in draft.cards] == ["Overall status: RECRUITING"]


async def test_status_line_that_disagrees_with_the_report_is_not_used(pending_store) -> None:
    pending_store.raw[VERSION_ID] = CTGOV_RAW.replace("RECRUITING", "COMPLETED")
    draft = await _ask(pending_store, "What is the trial's recruitment status?")
    assert draft.outcome == service.OUTCOME_NOT_IN_RECORD


@pytest.mark.parametrize("question", ["What is this report about?", "whats this report about?", "what's this about", "Summarise"])
async def test_what_is_this_about_answers(pending_store, question: str) -> None:
    draft = await _ask(pending_store, question)
    assert draft.outcome == service.OUTCOME_ANSWERED, draft.detail
    shown = [c.text for c in draft.cards]
    assert shown[0] == "Conditions: Lung Cancer; Non-Small Cell Lung Cancer"
    assert all(text in CTGOV_RAW for text in shown)


async def test_ask_about_status_answers(pending_store) -> None:
    draft = await _ask(pending_store, "Ask about this record's status")
    assert draft.outcome == service.OUTCOME_ANSWERED, draft.detail


async def test_greeting_gets_the_help_line(pending_store) -> None:
    draft = await _ask(pending_store, "hello")
    assert draft.outcome == service.OUTCOME_NOT_IN_RECORD
    assert draft.answer == texts.NO_INTENT_HELP


async def test_medical_question_still_refuses(pending_store, ctx, fake_llm, fake_gate) -> None:
    response = await service.answer_question(REPORT_ID, "Should my father get this test for his lung cancer?", ctx)
    assert response.refused and response.answer == texts.MEDICAL_REFUSAL
    assert fake_llm.calls == []


async def test_design_question_answers_from_the_study_type_line(pending_store) -> None:
    draft = await _ask(pending_store, "What is the study design?")
    assert draft.outcome == service.OUTCOME_ANSWERED, draft.detail
    assert [c.text for c in draft.cards] == ["Study type: OBSERVATIONAL"]
