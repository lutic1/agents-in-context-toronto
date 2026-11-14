"""The answer path (V70): composition, verification, the gate call, access and the lane's boundaries."""

from __future__ import annotations

import re

import pytest

from dxp.api.errors import ApiError
from dxp.interview import cards, compose, framing, service, texts
from dxp.interview.verify import verify_answer

from .conftest import (
    Q_CONDITIONS,
    Q_ENROL,
    Q_STATUS,
    RAW_TEXT,
    REPORT_ID,
    SOURCE_REF,
    VERSION_ID,
    FakeLlm,
    make_ctx,
    make_report,
    quote_id,
)


def card_of(text: str) -> cards.Card:
    return next(c for c in cards.load_cards(make_report(), {VERSION_ID: RAW_TEXT}) if c.text == text)


SOURCE_FIELDS = {"overall_status": "RECRUITING", "has_results": False}  # what conftest.make_report says


async def verify(answer_cards, answer=None, raw=None, check=None, source_fields=SOURCE_FIELDS):
    return await verify_answer(
        answer if answer is not None else compose.render(answer_cards),
        answer_cards,
        raw if raw is not None else {VERSION_ID: RAW_TEXT},
        check,
        source_fields=source_fields,
    )


# --- the happy path and the Decision ------------------------------------------------------------------------


async def test_answer_is_allowlisted_framing_plus_the_verbatim_quote(store, fake_llm: FakeLlm, fake_gate, ctx) -> None:
    response = await service.answer_question(REPORT_ID, "What is the status of this trial?", ctx)
    assert response.refused is False and response.refusal_reason is None
    assert response.answer == f"{framing.FRAME_INTRO}\n\n\"{Q_STATUS}\" [1]\n\n{framing.FRAME_QUOTES}"
    citation = response.citations[0]
    assert (citation.quote, citation.source_ref, citation.version_id, citation.field) == (Q_STATUS, SOURCE_REF, VERSION_ID, "status")
    assert response.decision_id.startswith("dec_")
    assert fake_llm.calls == []


async def test_one_gate_evaluation_records_the_question_the_intent_and_the_cited_quotes(store, fake_llm, fake_gate, ctx) -> None:
    long_question = "Is the trial recruiting? " + "x" * 400
    response = await service.answer_question(REPORT_ID, long_question[:500], ctx)
    # "xxxx..." is not in the record, so this one is not answered; ask again with a clean question.
    assert response.answer == texts.NOT_IN_RECORD
    fake_gate.calls.clear()
    response = await service.answer_question(REPORT_ID, "Is the trial recruiting?", ctx)
    assert len(fake_gate.calls) == 1
    gate_ctx, action = fake_gate.calls[0]
    assert gate_ctx is ctx
    assert (action.kind, action.destination, action.target.report_id) == ("answer_question", "ledger", REPORT_ID)
    assert action.inputs["outcome"] == "answered" and action.inputs["intent"] == "status"
    assert action.inputs["cited"] == [{"quote_id": quote_id(Q_STATUS), "version_id": VERSION_ID}]
    assert action.inputs["report_version_id"] == VERSION_ID
    assert action.evidence_ref.report_id == REPORT_ID and action.evidence_ref.version_id == VERSION_ID
    without_checked = {k: v for k, v in action.inputs.items() if k != "checked_quotes"}
    assert Q_STATUS not in str(without_checked), "quote text is only in checked_quotes, which A06's claim checks read"
    assert action.inputs["checked_quotes"] == [{"text": Q_STATUS, "quote_found": True}]
    assert action.inputs["source_fields"] == {"overall_status": "RECRUITING", "has_results": False}
    assert response.decision_id == "dec_fake000000000001"


async def test_the_question_is_truncated_in_the_decision(store, fake_llm, fake_gate, ctx) -> None:
    await service.answer_question(REPORT_ID, "Is the trial recruiting? " + "x" * 450, ctx)
    assert len(fake_gate.calls[0][1].inputs["question"]) <= 200


async def test_the_real_claim_results_are_recorded_and_no_placeholder_claim_is_sent(store, fake_llm, fake_gate, ctx) -> None:
    await service.answer_question(REPORT_ID, "What is the study design?", ctx)
    action = fake_gate.calls[0][1]
    assert action.claims == [], "the lane states no claim of its own; the old passed=False placeholders are gone"
    checks = action.inputs["claim_checks"]
    assert [c["quote_id"] for c in checks] == [c["quote_id"] for c in action.inputs["cited"]]
    assert all(c["passed"] is True and c["quote_id"] in c["detail"] for c in checks)


async def test_the_gate_blocking_a_claim_refuses_the_answer(store, fake_llm, fake_gate, ctx) -> None:
    fake_gate.block("answer_question", "claim_check")
    response = await service.answer_question(REPORT_ID, "What is the status?", ctx)
    assert response.refused is True and response.refusal_reason == "blocked" and response.citations == []


# --- verification --------------------------------------------------------------------------------------------


async def test_a_composed_answer_verifies() -> None:
    verdict = await verify([card_of(Q_STATUS)])
    assert verdict.ok, verdict.problems
    assert len(verdict.claim_checks) == 1 and verdict.claim_checks[0]["passed"] is True


async def test_a_quote_not_in_its_pinned_version_is_rejected() -> None:
    verdict = await verify([card_of(Q_STATUS)], raw={VERSION_ID: "something else entirely"})
    assert not verdict.ok and any("not found" in p for p in verdict.problems)


async def test_the_quote_is_checked_against_the_version_it_names_not_another() -> None:
    verdict = await verify([card_of(Q_STATUS)], raw={VERSION_ID: "nothing", "sv_bbbbbbbbbbbbbbbb": RAW_TEXT})
    assert not verdict.ok


async def test_an_unknown_version_is_rejected() -> None:
    verdict = await verify([card_of(Q_STATUS)], raw={})
    assert not verdict.ok and any("not available" in p for p in verdict.problems)


async def test_the_real_quote_check_is_used_when_it_exists(monkeypatch) -> None:
    import dxp.evidence

    seen = []

    async def fake_quote_in_source(quote, raw_text):
        seen.append((quote, raw_text))
        return False

    monkeypatch.setattr(dxp.evidence, "quote_in_source", fake_quote_in_source, raising=False)
    verdict = await verify([card_of(Q_STATUS)])
    assert seen == [(Q_STATUS, RAW_TEXT)] and not verdict.ok


async def test_an_injected_quote_check_decides() -> None:
    assert not (await verify([card_of(Q_STATUS)], check=lambda quote, raw: False)).ok
    assert (await verify([card_of(Q_STATUS)], check=lambda quote, raw: True)).ok


@pytest.mark.parametrize(
    "tamper",
    [
        lambda a: a.replace(framing.FRAME_INTRO, "Here is what the accepted record says."),
        lambda a: a.replace(framing.FRAME_INTRO, "FoundationOne CDx is better than FoundationOne Liquid."),
        lambda a: a.replace(framing.FRAME_INTRO, "I'm FoundationOne CDx."),
        lambda a: a.replace(framing.FRAME_QUOTES, "These are the 3 quotes it rests on."),
        lambda a: a + "\n\nThe trial worked.",
        lambda a: "The trial worked.\n\n" + a,
        lambda a: a.replace("RECRUITING", "COMPLETED"),
        lambda a: a.replace(' [1]', ' [2]'),
        lambda a: a.replace("\n\n", "\n"),
        lambda a: "",
    ],
)
async def test_any_text_outside_the_allowlist_and_the_cited_quotes_is_rejected(tamper) -> None:
    card = card_of(Q_STATUS)
    verdict = await verify([card], answer=tamper(compose.render([card])))
    assert not verdict.ok


async def test_an_empty_answer_is_rejected() -> None:
    assert not (await verify([])).ok


async def test_a_card_with_claim_like_wording_or_no_field_is_rejected_even_if_it_got_this_far() -> None:
    claim = cards.Card("qt_x", "Overall status: better than before.", SOURCE_REF, VERSION_ID, "status")
    other = cards.Card("qt_y", Q_ENROL, SOURCE_REF, VERSION_ID, "other")
    assert not (await verify([claim], raw={VERSION_ID: claim.text})).ok
    assert not (await verify([other])).ok


async def test_a_quote_with_a_line_break_is_rejected() -> None:
    broken = cards.Card("qt_x", "Overall status: RECRUITING.\n\nNo results posted.", SOURCE_REF, VERSION_ID, "status")
    assert not (await verify([broken], raw={VERSION_ID: broken.text})).ok


async def test_a_number_outside_a_quote_is_rejected() -> None:
    card = card_of(Q_ENROL)
    answer = compose.render([card]).replace(framing.FRAME_INTRO, "Here's what the accepted record says in 2024.")
    assert not (await verify([card], answer=answer)).ok


# --- the fallback never fails open --------------------------------------------------------------------------


async def test_a_failed_verification_ends_in_the_exact_reply(store, fake_llm, fake_gate, ctx) -> None:
    response = await service.answer_question(REPORT_ID, "What is the status?", ctx, quote_check=lambda quote, raw: False)
    assert response.answer == texts.NOT_IN_RECORD and response.citations == []
    assert fake_gate.calls[0][1].inputs["outcome"] == "not_in_record"
    assert fake_gate.calls[0][1].inputs["reason"] == "verification_failed"


async def test_a_pinned_version_that_no_longer_holds_the_quotes_gives_the_exact_reply(store, fake_llm, fake_gate, ctx) -> None:
    store.raw[VERSION_ID] = "the pinned text no longer holds the quotes"
    response = await service.answer_question(REPORT_ID, "What is the status?", ctx)
    assert response.answer == texts.NOT_IN_RECORD and response.citations == []


# --- who may ask, which report ------------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["pending", "accepting", "rejected", "reverting", "reverted"])
async def test_a_report_that_is_not_accepted_is_refused_with_409(status, store, fake_llm, fake_gate, ctx) -> None:
    store.reports[REPORT_ID] = make_report(status=status)
    with pytest.raises(ApiError) as caught:
        await service.answer_question(REPORT_ID, "Is the trial recruiting?", ctx)
    assert caught.value.status_code == 409 and caught.value.code == "report_not_accepted"
    assert fake_llm.calls == [] and fake_gate.calls == []


async def test_an_unknown_report_is_404(store, fake_llm, fake_gate, ctx) -> None:
    with pytest.raises(ApiError) as caught:
        await service.answer_question("rep_ffffffffffffffff", "Is the trial recruiting?", ctx)
    assert caught.value.status_code == 404
    assert fake_llm.calls == [] and fake_gate.calls == []


async def test_a_medical_question_on_a_pending_report_is_still_409(store, fake_llm, fake_gate, ctx) -> None:
    store.reports[REPORT_ID] = make_report(status="pending")
    with pytest.raises(ApiError) as caught:
        await service.answer_question(REPORT_ID, "Should I start my patient on it?", ctx)
    assert caught.value.status_code == 409


async def test_a_blocked_gate_returns_refused_blocked_with_the_decision(store, fake_llm, fake_gate, ctx) -> None:
    fake_gate.block("answer_question", "destination_action")
    response = await service.answer_question(REPORT_ID, "Is the trial recruiting?", ctx)
    assert response.refused is True and response.refusal_reason == "blocked"
    assert response.answer == texts.BLOCKED and response.citations == []
    assert response.decision_id == "dec_fake000000000001"


async def test_a_blocked_gate_also_blocks_a_medical_refusal_text(store, fake_llm, fake_gate, ctx) -> None:
    fake_gate.block("answer_question")
    response = await service.answer_question(REPORT_ID, "Should I start my patient on it?", ctx)
    assert response.refusal_reason == "blocked" and fake_llm.calls == []


async def test_a_caller_without_the_grant_costs_no_model_call_and_is_blocked(store, fake_llm, fake_gate) -> None:
    response = await service.answer_question(REPORT_ID, "What is the study design?", make_ctx(actions=[]))
    assert fake_llm.calls == []
    assert len(fake_gate.calls) == 1, "the attempt is still a logged Decision"
    assert response.refused is True and response.refusal_reason == "blocked"


async def test_the_gate_not_being_on_main_is_a_501(store, fake_llm, monkeypatch, ctx) -> None:
    import dxp.gate

    async def missing(ctx, action):
        raise NotImplementedError("gate.evaluate (A06)")

    monkeypatch.setattr(dxp.gate, "evaluate", missing)
    with pytest.raises(ApiError) as caught:
        await service.answer_question(REPORT_ID, "Is the trial recruiting?", ctx)
    assert caught.value.status_code == 501


async def test_a_blank_question_is_422(store, fake_llm, fake_gate, ctx) -> None:
    with pytest.raises(ApiError) as caught:
        await service.answer_question(REPORT_ID, "   ", ctx)
    assert caught.value.status_code == 422


async def test_one_decision_per_question_whatever_the_outcome(store, fake_llm, fake_gate, ctx) -> None:
    for text in ("Is the trial recruiting?", "Should I take it?", "What is the status of the Moon landing?", "Hello"):
        before = len(fake_gate.calls)
        await service.answer_question(REPORT_ID, text, ctx)
        assert len(fake_gate.calls) == before + 1
        assert fake_gate.calls[-1][1].kind == "answer_question"


# --- the lane writes nothing --------------------------------------------------------------------------------


async def test_the_lane_reads_two_things_and_writes_nothing(store, fake_llm, fake_gate, ctx, monkeypatch) -> None:
    import dxp.store

    def no_store(*args, **kwargs):
        raise AssertionError("the interview lane must not touch the store directly")

    monkeypatch.setattr(dxp.store, "collection", no_store)
    monkeypatch.setattr(dxp.store, "get_db", no_store)
    response = await service.answer_question(REPORT_ID, "Is the trial recruiting?", ctx)
    assert response.citations
    assert store.reads == [REPORT_ID]


def test_no_secret_names_in_the_lane() -> None:
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "dxp" / "interview"
    source = "\n".join(p.read_text() for p in root.glob("*.py"))
    assert not re.search(r"API_KEY|MONGODB_URI|os\.environ|getenv", source)


def test_the_conditions_quote_is_a_plain_card() -> None:
    assert card_of(Q_CONDITIONS).field == "conditions"


# --- red team 4: the gate runs before the model, the action is settled, the Decision has an ID target ------------------------------


async def test_the_decision_has_an_id_target_so_the_real_gate_can_derive_an_id(store, fake_llm, fake_gate, ctx) -> None:
    for question in ("What is the status?", "Should I join?", "What is the Moon?"):
        await service.answer_question(REPORT_ID, question, ctx)
    assert [call[1].inputs["id_target"] for call in fake_gate.calls] == [REPORT_ID] * 3


async def test_a_blocked_question_costs_no_model_call_for_any_reason(store, fake_llm, fake_gate, ctx) -> None:
    for check in ("team_scope", "policy_checks", "evidence_checks", "grant_expiry"):
        fake_gate.block("answer_question", check)
        response = await service.answer_question(REPORT_ID, "What is the study design?", ctx)
        assert response.refused is True and response.refusal_reason == "blocked" and response.citations == []
    assert fake_llm.calls == [], "the design intent has several cards, so an allowed question is ranked; a blocked one is not"


async def test_the_gate_is_evaluated_before_the_model_is_asked(store, fake_llm, fake_gate, ctx) -> None:
    order: list[str] = []
    real_evaluate = fake_gate.evaluate

    async def evaluate(c, action):
        order.append("gate")
        return await real_evaluate(c, action)

    original_call = fake_llm.__class__.__call__

    async def call(self, *args, **kwargs):
        order.append("model")
        return await original_call(self, *args, **kwargs)

    import dxp.gate

    dxp.gate.evaluate = evaluate  # restored by the fake_gate fixture's monkeypatch
    fake_llm.__class__.__call__ = call
    try:
        await service.answer_question(REPORT_ID, "What is the study design?", ctx)
    finally:
        fake_llm.__class__.__call__ = original_call
    assert order == ["gate", "model"]


async def test_the_decision_names_the_cited_quotes_before_the_model_orders_them(store, fake_llm, fake_gate, ctx) -> None:
    fake_llm.ids = []
    response = await service.answer_question(REPORT_ID, "What is the study design?", ctx)
    cited = fake_gate.calls[0][1].inputs["cited"]
    assert len(cited) == len(response.citations) > 1
    assert {c["version_id"] for c in cited} == {VERSION_ID}


async def test_the_action_is_settled_done_with_the_outcome_and_the_cited_quotes(store, fake_llm, fake_gate, ctx, settled) -> None:
    await service.answer_question(REPORT_ID, "What is the status?", ctx)
    [(action_id, status, result)] = settled.calls
    assert action_id.startswith("act_") and status == "done"
    assert result == {"outcome": "answered", "cited": [{"quote_id": quote_id(Q_STATUS), "version_id": VERSION_ID}]}


async def test_a_medical_refusal_and_a_not_in_record_reply_are_settled_done(store, fake_llm, fake_gate, ctx, settled) -> None:
    await service.answer_question(REPORT_ID, "Should I join?", ctx)
    await service.answer_question(REPORT_ID, "What is the Moon?", ctx)
    assert [(s, r["outcome"]) for _, s, r in settled.calls] == [("done", "refused_medical_advice"), ("done", "not_in_record")]


async def test_a_blocked_question_settles_nothing(store, fake_llm, fake_gate, ctx, settled) -> None:
    fake_gate.block("answer_question")
    await service.answer_question(REPORT_ID, "What is the status?", ctx)
    assert settled.calls == []


async def test_a_failure_after_the_gate_settles_the_action_failed_and_says_not_in_record(store, fake_llm, fake_gate, ctx, settled) -> None:
    seen = []

    def quote_check(quote, raw):
        seen.append(quote)
        return len(seen) <= 1  # true while the answer is planned, false once the model step verifies again

    response = await service.answer_question(REPORT_ID, "What is the status?", ctx, quote_check=quote_check)
    assert response.answer == texts.NOT_IN_RECORD and response.citations == []
    assert [(s, r["outcome"], r["cited"]) for _, s, r in settled.calls] == [("failed", "not_in_record", [])]


async def test_a_settle_that_fails_never_changes_the_reply(monkeypatch, store, fake_llm, fake_gate, ctx) -> None:
    import dxp.gate

    async def broken(*args, **kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(dxp.gate, "mark_action", broken)
    response = await service.answer_question(REPORT_ID, "What is the status?", ctx)
    assert response.refused is False and response.citations
