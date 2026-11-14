"""One interview question, start to finish (V70).

Order, and why:

1. The report must exist and be `accepted` (404, 409). Nothing is read from anything but the report.
2. A medical-advice question gets the one fixed refusal. No model call is made, here or later.
3. Otherwise the model selects quote IDs from the report's own cards (`llm`, one call). DxP builds the
   text from fixed lead-ins and the verbatim quotes, then verifies it. Any failure ends in the exact
   reply "The accepted record doesn't answer that".
4. One `gate.evaluate` call records the `answer_question` Decision (question truncated, cited quote IDs
   with their version_id, outcome) and carries the claim tags for check 4. A blocked Decision means a
   refused response with reason `blocked` and no answer. This lane writes nothing else.

A caller without `answer_question` in its grant costs no model call: the gate still records the
blocked attempt.
"""

from __future__ import annotations

import logging
from typing import Any

from dxp import gate
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.interview import cards as cards_module
from dxp.interview import compose as compose_module
from dxp.interview import medical, repo, texts
from dxp.interview.select import LlmCall, select_cards
from dxp.interview.verify import QuoteCheck, claim_guard_blocks, verify_answer

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
    """Cards, selection, composition and verification. Never raises for a model or verification failure."""
    all_cards = cards_module.load_cards(report)
    if not all_cards:
        return _not_in_record(reason="no_quotes_on_report")
    try:
        selected = await select_cards(question, all_cards, llm_call)
    except Exception as exc:  # noqa: BLE001 - llm's own errors vary; never echo them (AD-20)
        log.warning("interview selection failed (%s)", type(exc).__name__)
        return _not_in_record(reason="selection_failed")
    usable = [c for c in selected if not claim_guard_blocks(c, report)]
    if not usable:
        return _not_in_record(reason="nothing_selected" if not selected else "claim_guard")
    names = cards_module.mention_names(report)
    sentences = compose_module.compose(usable, names)
    answer = compose_module.render(sentences)
    raw = await _raw_texts({s.card.version_id for s in sentences})
    verdict = await verify_answer(answer, sentences, names, raw, quote_check)
    if not verdict.ok:
        return _not_in_record(reason="verification_failed", problems=verdict.problems[:5])
    draft = _Draft(OUTCOME_ANSWERED, answer)
    draft.cards = [s.card for s in sentences]
    draft.claims = verdict.claims
    return draft


def _action(report_id: str, report: dict[str, Any], question: str, draft: _Draft, rule: str | None) -> m.ProposedAction:
    inputs: dict[str, Any] = {
        "question": _truncate(question),
        "outcome": draft.outcome,
        "report_version_id": report.get("version_id"),
        "cited": [{"quote_id": c.quote_id, "version_id": c.version_id} for c in draft.cards],
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
