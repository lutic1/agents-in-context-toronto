"""One interview question, start to finish (V70).

Order, and why. Every step before the ranking is deterministic, and none of them calls a model:

1. The report must exist and be `accepted` (404, 409). Nothing is read from anything but the report.
2. MEDICAL: a question that mentions a person or a clinical decision gets the one fixed refusal.
3. INTENT: the question must map to exactly one answerable intent (status, dates, conditions, phase, design,
   interventions, sponsor, location, enrollment, results). Otherwise: "The accepted record doesn't answer that."
4. OFF-TOPIC: every content word of the question must be a word of the record. Otherwise the same reply.
5. CARDS: the intent may use only cards of its own fields, with no claim-like wording. None: the same reply.
6. RANKING: only now may a model be asked, and only to put those eligible cards in order (`select.py`). It never
   writes text. DxP composes the answer from allowlisted framing and the verbatim quotes, then verifies it. Any
   failure ends in the exact reply "The accepted record doesn't answer that."
7. One `gate.evaluate` call records the `answer_question` Decision (question truncated, intent, cited quote IDs
   with their version_id, outcome) and carries the claim checks. A blocked Decision means a refused response with
   reason `blocked` and no answer. This lane writes nothing else.

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
from dxp.interview.select import LlmCall, rank_cards
from dxp.interview.verify import QuoteCheck, verify_answer

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


def _not_in_record(**detail: Any) -> _Draft:
    draft = _Draft(OUTCOME_NOT_IN_RECORD, texts.NOT_IN_RECORD, texts.REASON_NOT_IN_RECORD)
    draft.detail = detail
    return draft


async def build_answer(
    report: dict[str, Any], question: str, *, llm_call: LlmCall | None = None, quote_check: QuoteCheck | None = None
) -> _Draft:
    """Intent, off-topic guard, eligible cards, ranking, composition and verification. Never raises for a model or
    verification failure. The model is reached only after every deterministic step has passed."""
    verdict = question_gate.classify_intent(question)
    if verdict.intent is None:
        return _not_in_record(reason=verdict.reason)
    intent = verdict.intent

    raw = await _raw_texts(cards_module.discovery_versions(report))
    all_cards = cards_module.load_cards(report, raw)
    if not all_cards:
        return _not_in_record(reason="no_quotes_on_report", intent=intent.name)
    outside = question_gate.off_topic_words(question, question_gate.vocabulary(report, all_cards))
    if outside:
        return _not_in_record(reason=question_gate.REASON_OFF_TOPIC, intent=intent.name, outside_words=len(outside))
    eligible = intents.eligible_cards(intent, all_cards, cards_module.mention_names(report))
    if not eligible:
        return _not_in_record(reason="no_eligible_cards", intent=intent.name)

    ranked = await rank_cards(question, intent.name, eligible, llm_call)
    answer = compose_module.render(ranked)
    verdict_ok = await verify_answer(answer, ranked, raw, quote_check)
    if not verdict_ok.ok:
        return _not_in_record(reason="verification_failed", intent=intent.name, problems=verdict_ok.problems[:5])
    draft = _Draft(OUTCOME_ANSWERED, answer)
    draft.cards = ranked
    draft.claims = verdict_ok.claims
    draft.detail = {"intent": intent.name}
    return draft


def _action(report_id: str, report: dict[str, Any], question: str, draft: _Draft, rule: str | None) -> m.ProposedAction:
    discovery = report.get("discovery") or {}
    inputs: dict[str, Any] = {
        "question": _truncate(question),
        "outcome": draft.outcome,
        "report_version_id": report.get("version_id"),
        "cited": [{"quote_id": c.quote_id, "version_id": c.version_id} for c in draft.cards],
        # What A06's GateAction.coerce reads for the claim checks (the report's own fields, never the model's).
        "source_fields": {"overall_status": discovery.get("trial_status"), "has_results": discovery.get("has_results")},
        "checked_quotes": [{"text": c.text, "quote_found": True} for c in draft.cards],
    }
    if rule:
        inputs["rule"] = rule
    inputs.update(draft.detail)
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
        draft = await build_answer(report, question, llm_call=llm_call, quote_check=quote_check)

    try:
        decision = await gate.evaluate(ctx, _action(report_id, report, question, draft, rule))
    except NotImplementedError as exc:
        raise ApiError(501, "not_implemented", "The policy gate is not on main yet (A06).") from exc

    if decision.outcome == "blocked" or draft.outcome == OUTCOME_NOT_PERMITTED:
        return m.InterviewResponse(answer=texts.BLOCKED, citations=[], refused=True, refusal_reason=texts.REASON_BLOCKED, decision_id=decision.id)
    return m.InterviewResponse(
        answer=draft.answer,
        citations=_citations(draft.cards),
        refused=draft.refused,
        refusal_reason=draft.refusal_reason,
        decision_id=decision.id,
    )
