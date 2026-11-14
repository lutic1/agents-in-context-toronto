"""One interview question, start to finish (V70).

Order, and why. Every step before the gate is deterministic, and none of them calls a model:

1. The report must exist and be `accepted` (404, 409). Nothing is read from anything but the report.
2. MEDICAL: a question that mentions a person or a clinical decision gets the one fixed refusal.
   A letter outside ASCII is refused here too (a language the gate cannot read gets the same fixed refusal).
3. INTENT: the question must map to exactly one answerable intent (status, dates, conditions, phase, design,
   interventions, sponsor, location, enrollment, results). Otherwise: "The accepted record doesn't answer that."
   A definition, a general-knowledge frame and a question typed one letter at a time have no intent.
4. CARDS: the intent may use only cards of its own fields, each with the shape of that field (cards.shape_ok) and no
   claim-like wording, pinned to the report's own version. None: the same reply. Each eligible card has also passed
   `gate.claims.evaluate_claims` under the claim policies, as its own quote, against the report's own `overall_status`
   and `has_results` (`verify.card_passes`).
5. OFF-TOPIC: every content word of the question must be a stopword, a keyword or a word of the title or of THOSE
   eligible cards (not of the whole report). Otherwise the same reply.
6. The cards shown are the first ones in report order (at most three): the same question always shows the same quotes.
   The answer is composed from allowlisted framing and the verbatim quotes and verified (`plan_answer`).
7. THE GATE, before any model: one `gate.evaluate` call records the `answer_question` Decision (question truncated,
   intent, cited quote IDs with their version_id, outcome, the claim checks). A blocked Decision means a refused
   response with reason `blocked`, no answer and NO model call.
8. RANKING: only now may a model be asked, and only to put those cards in order (`select.py`). It never writes text and
   never chooses which cards. DxP composes the answer again and verifies it. Any failure ends in the exact reply "The
   accepted record doesn't answer that."
9. The gate's action is settled (`gate.mark_action`: `done` with the outcome and the cited quote IDs, or `failed`).
   This lane writes nothing else.

A caller without `answer_question` in its grant costs no model call: the gate still records the blocked attempt.
"""

from __future__ import annotations

import logging
from typing import Any

from dxp import gate
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.interview import cards as cards_module
from dxp.interview import compose as compose_module
from dxp.interview import intents, medical, question as question_gate, repo, texts
from dxp.interview import select as select_module
from dxp.interview.select import LlmCall, rank_cards
from dxp.interview.verify import QuoteCheck, card_passes, verify_answer

log = logging.getLogger("dxp.interview")

QUESTION_LOG_CHARS = 200

OUTCOME_ANSWERED = "answered"
OUTCOME_MEDICAL = "refused_medical_advice"
OUTCOME_NOT_IN_RECORD = "not_in_record"
OUTCOME_NOT_PERMITTED = "not_attempted_no_grant"


def _truncate(question: str) -> str:
    return " ".join(question.split())[:QUESTION_LOG_CHARS]


async def _raw_texts(version_ids: set[str]) -> dict[str, str | None]:
    return {version_id: await repo.get_raw_text(version_id) for version_id in sorted(version_ids)}


def source_fields_of(report: dict[str, Any]) -> dict[str, Any]:
    """The report's own structured fields, which the claim checks judge each quote against (never the model's)."""
    discovery = report.get("discovery") or {}
    return {"overall_status": discovery.get("trial_status"), "has_results": discovery.get("has_results")}


class _Draft:
    """What the question produced before the gate: the text, its citations, the claim tags and why."""

    def __init__(self, outcome: str, answer: str, reason: str | None = None) -> None:
        self.outcome = outcome
        self.answer = answer
        self.refusal_reason = reason
        self.refused = outcome == OUTCOME_MEDICAL
        self.cards: list[cards_module.Card] = []
        self.claims: list[m.ClaimCheck] = []
        self.detail: dict[str, Any] = {}
        # Set by `plan_answer` for an answer that still has to be ordered by the model.
        self.raw: dict[str, str | None] = {}
        self.names: list[str] = []
        self.source_fields: dict[str, Any] = {}
        self.intent: str | None = None


def _not_in_record(**detail: Any) -> _Draft:
    draft = _Draft(OUTCOME_NOT_IN_RECORD, texts.NOT_IN_RECORD, texts.REASON_NOT_IN_RECORD)
    draft.detail = detail
    return draft


async def plan_answer(report: dict[str, Any], question: str, *, quote_check: QuoteCheck | None = None) -> _Draft:
    """Every deterministic step, and no model: intent, eligible cards, the off-topic guard, and the verification of the
    answer in report order. The cards shown are the first ones in report order (`select.MAX_SELECTED`), whatever a model
    says, so the Decision can name them before any model is asked. Never raises for a verification failure."""
    verdict = question_gate.classify_intent(question)
    if verdict.intent is None:
        return _not_in_record(reason=verdict.reason)
    intent = verdict.intent

    raw = await _raw_texts(cards_module.discovery_versions(report))
    all_cards = cards_module.load_cards(report, raw)
    if not all_cards:
        return _not_in_record(reason="no_quotes_on_report", intent=intent.name)
    source_fields = source_fields_of(report)
    eligible = [
        card
        for card in intents.eligible_cards(intent, all_cards, cards_module.mention_names(report))
        if card_passes(card, source_fields)
    ]
    if not eligible:
        return _not_in_record(reason="no_eligible_cards", intent=intent.name)
    outside = question_gate.off_topic_words(question, question_gate.vocabulary(report, eligible), intent)
    if outside:
        return _not_in_record(reason=question_gate.REASON_OFF_TOPIC, intent=intent.name, outside_words=len(outside))

    shown = eligible[: select_module.MAX_SELECTED]
    verdict_ok = await verify_answer(
        compose_module.render(shown), shown, raw, quote_check, names=cards_module.mention_names(report), source_fields=source_fields
    )
    if not verdict_ok.ok:
        return _not_in_record(reason="verification_failed", intent=intent.name, problems=verdict_ok.problems[:5])
    draft = _Draft(OUTCOME_ANSWERED, compose_module.render(shown))
    draft.cards = shown
    draft.detail = {"intent": intent.name, "claim_checks": verdict_ok.claim_checks}
    draft.raw = raw
    draft.names = cards_module.mention_names(report)
    draft.source_fields = source_fields
    draft.intent = intent.name
    return draft


async def finish_answer(draft: _Draft, question: str, *, llm_call: LlmCall | None = None, quote_check: QuoteCheck | None = None) -> _Draft:
    """The model step, run only after the gate allowed the question: it puts the cards in order (it never chooses
    which cards, and never writes text), DxP composes the answer and verifies it once more. Any failure is "not in the
    record"."""
    ranked = await rank_cards(question, draft.intent or "", draft.cards, llm_call)
    answer = compose_module.render(ranked)
    verdict_ok = await verify_answer(answer, ranked, draft.raw, quote_check, names=draft.names, source_fields=draft.source_fields)
    if not verdict_ok.ok:
        return _not_in_record(reason="verification_failed", intent=draft.intent, problems=verdict_ok.problems[:5])
    done = _Draft(OUTCOME_ANSWERED, answer)
    done.cards = ranked
    done.detail = dict(draft.detail)
    return done


async def build_answer(
    report: dict[str, Any], question: str, *, llm_call: LlmCall | None = None, quote_check: QuoteCheck | None = None
) -> _Draft:
    """`plan_answer` then `finish_answer`, with no gate between them (tests and tools; `answer_question` puts the gate
    between the two so a blocked question never costs a model call)."""
    draft = await plan_answer(report, question, quote_check=quote_check)
    if draft.outcome != OUTCOME_ANSWERED:
        return draft
    return await finish_answer(draft, question, llm_call=llm_call, quote_check=quote_check)


def _action(report_id: str, report: dict[str, Any], question: str, draft: _Draft, rule: str | None) -> m.ProposedAction:
    inputs: dict[str, Any] = {
        "question": _truncate(question),
        "outcome": draft.outcome,
        "report_version_id": report.get("version_id"),
        "cited": [{"quote_id": c.quote_id, "version_id": c.version_id} for c in draft.cards],
        # What A06's GateAction.coerce reads for the claim checks (the report's own fields, never the model's).
        "source_fields": source_fields_of(report),
        "checked_quotes": [{"text": c.text, "quote_found": True} for c in draft.cards],
    }
    if rule:
        inputs["rule"] = rule
    inputs.update(draft.detail)
    # The gate derives the Decision's ID from the kind and a target, and `answer_question` is not a report-target kind:
    # without this every question is a 500 on the real gate ("no target to derive an ID from"). The request ID, which the
    # gate adds for a Reviewer, keeps each question's Decision its own.
    inputs["id_target"] = report_id
    return m.ProposedAction(
        kind="answer_question",
        destination="ledger",
        target=m.Target(report_id=report_id),
        inputs=inputs,
        evidence_ref=m.EvidenceRef(source_ref=report.get("source_ref"), version_id=report.get("version_id"), report_id=report_id),
        claims=draft.claims,
    )


def _citations(cards: list[cards_module.Card]) -> list[m.InterviewCitation]:
    return [m.InterviewCitation(quote=c.text, source_ref=c.source_ref, version_id=c.version_id, field=c.field) for c in cards]


async def answer_question(
    report_id: str,
    question: str,
    ctx: m.RunContext,
    *,
    llm_call: LlmCall | None = None,
    quote_check: QuoteCheck | None = None,
    report: dict[str, Any] | None = None,
) -> m.InterviewResponse:
    """`report` is the document the caller already read; it is read again only when not passed."""
    if report is None:
        report = await repo.get_report(report_id)
    if report is None:
        raise ApiError(404, "not_found", "Report not found.")
    if not cards_module.is_accepted(report):
        raise ApiError(409, "report_not_accepted", "Only an accepted report can be interviewed.")
    question = question.strip()
    if not question:
        raise ApiError(422, "invalid_request", "Ask a question first.")

    rule = medical.medical_advice_rule(question)
    if rule is not None:
        draft = _Draft(OUTCOME_MEDICAL, texts.MEDICAL_REFUSAL, texts.REASON_MEDICAL)
    elif "answer_question" not in ctx.principal.actions:
        draft = _not_in_record(reason="no_grant")
        draft.outcome = OUTCOME_NOT_PERMITTED
    else:
        draft = await plan_answer(report, question, quote_check=quote_check)

    # The gate BEFORE the model: a question the gate blocks, for any reason, costs no model call.
    action = _action(report_id, report, question, draft, rule)
    try:
        decision = await gate.evaluate(ctx, action)
    except NotImplementedError as exc:
        raise ApiError(501, "not_implemented", "The policy gate is not on main yet (A06).") from exc

    if decision.outcome == "blocked" or draft.outcome == OUTCOME_NOT_PERMITTED:
        return m.InterviewResponse(answer=texts.BLOCKED, citations=[], refused=True, refusal_reason=texts.REASON_BLOCKED, decision_id=decision.id)

    status = "done"
    if draft.outcome == OUTCOME_ANSWERED:
        try:
            draft = await finish_answer(draft, question, llm_call=llm_call, quote_check=quote_check)
        except Exception as exc:  # noqa: BLE001 - fail closed: the Decision is settled as failed and the reply is "not in the record"
            log.warning("interview answer failed after the gate (%s)", type(exc).__name__)
            draft = _not_in_record(reason="finish_failed")
        if draft.outcome != OUTCOME_ANSWERED:
            status = "failed"
    await _settle(ctx, action, decision, status, draft)
    return m.InterviewResponse(
        answer=draft.answer,
        citations=_citations(draft.cards),
        refused=draft.refused,
        refusal_reason=draft.refusal_reason,
        decision_id=decision.id,
    )


async def _settle(ctx: m.RunContext, action: m.ProposedAction, decision: m.Decision, status: str, draft: _Draft) -> None:
    """End the gate's `queued` action: `done` with the outcome and the quotes cited, or `failed` when the model step or
    the last verification failed after the gate allowed the question. Best effort: a failure to settle never changes
    the reply (the Decision is already recorded) and is logged without the question."""
    mark = getattr(gate, "mark_action", None)
    if mark is None:
        return
    try:
        action_id = getattr(decision, "action_id", None)
        if not action_id:
            from dxp.gate import checks as gate_checks, decisions as gate_decisions

            action_id = gate_decisions.ids_for(gate_checks.GateCtx.coerce(ctx), gate_checks.GateAction.coerce(action))[1]
        result = {
            "outcome": draft.outcome,
            "cited": [{"quote_id": c.quote_id, "version_id": c.version_id} for c in draft.cards],
        }
        await mark(action_id, status, result)
    except Exception as exc:  # noqa: BLE001 - see the docstring
        log.warning("interview action not settled (%s)", type(exc).__name__)
