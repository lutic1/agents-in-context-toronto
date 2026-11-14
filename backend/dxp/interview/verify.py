"""Verification of an answer before it is returned (V70, V33, V37, AD-6, AD-19).

Every check fails closed. The answer is returned only if all of these hold:

1. the answer is exactly the rendering of its cited cards: allowlisted framing, then one `"<quote>" [n]` block
   per card, then allowlisted framing (so nothing else, in any form, is in it);
2. every framing block is on the allowlist AND passes the mechanical no-facts check;
3. each cited quote is found in the raw text of the exact source version it names (V40), compared on the
   whitespace-normalised form;
4. no card is claim-like, no card is of the "other" field and every card has the shape of its field (a second net under
   the cards' own rules);
5. no digit appears outside a cited quote;
6. `gate.claims.evaluate_claims` is run, with the three claim policies, on every cited quote as that quote's own claim
   (`card_claims`), against the report's own structured fields (`overall_status`, `has_results`). One failed policy
   fails the answer (it becomes "not in the record"). The real results are recorded on the `answer_question` Decision
   (in its inputs); no placeholder claim is sent, because the lane states no claim of its own (AD-19);
7. a status or results quote must say what the report's own structured field says ("Overall status: COMPLETED" on a
   RECRUITING report is refused, whatever the claim policies make of it).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from typing import Any

from dxp.gate import claims as gate_claims
from dxp.interview import framing
from dxp.interview.cards import FIELD_OTHER, Card, claim_like, normalise_text, shape_ok
from dxp.interview.compose import render, split_blocks

__all__ = ["QuoteCheck", "Verification", "card_claims", "card_passes", "default_quote_check", "source_problem", "verify_answer"]

QuoteCheck = Callable[[str, str], "bool | Awaitable[bool]"]
_DIGITS = re.compile(r"\d")
_QUOTE_BLOCK = re.compile(r'^"[^\n]*" \[\d+\]$')


@dataclass
class Verification:
    ok: bool
    problems: list[str] = field(default_factory=list)
    claim_checks: list[dict[str, Any]] = field(default_factory=list)  # one {quote_id, passed, detail} per cited quote


def default_quote_check(quote: str, raw_text: str) -> bool | Awaitable[bool]:
    """`evidence.quote_in_source(quote, raw_text)` (AD-6, A08) when it is on main. Until then, a
    whitespace- and case-insensitive substring test, which can only be stricter than word for word
    on content and never accepts a quote that is not in the text."""
    from dxp import evidence

    real = getattr(evidence, "quote_in_source", None)
    if callable(real):
        return real(quote, raw_text)
    return normalise_text(quote).lower() in normalise_text(raw_text).lower()


_STATUS_SEGMENT = re.compile(r"(?:overall status|status|recruitment status)\s*:\s*([A-Za-z_ ,]+?)(?:\.|;|$)", re.IGNORECASE)
_RESULTS_SEGMENT = re.compile(r"(?:results posted|has results|results)\s*:\s*([A-Za-z_ ]+?)(?:\.|;|$)", re.IGNORECASE)
_YES = frozenset({"yes", "true", "posted"})
_NO = frozenset({"no", "false", "not posted"})


def _norm_status(value: str) -> str:
    return re.sub(r"[_\s,]+", "_", value.strip()).strip("_").upper()


def source_problem(card: Card, source_fields: dict[str, Any] | None) -> str | None:
    """None when the card agrees with the report's own structured fields, else why not. A status or results card must say
    what `overall_status` / `has_results` say; with no such field on the report it cannot be checked, so it is refused."""
    fields = source_fields or {}
    if card.field == "status":
        reported = fields.get("overall_status")
        values = [_norm_status(v) for v in _STATUS_SEGMENT.findall(card.text)]
        if not isinstance(reported, str) or not reported.strip() or not values:
            return "the status cannot be checked against the report's overall_status"
        if any(value != _norm_status(reported) for value in values):
            return "the quoted status is not the report's overall_status"
    if card.field == "results":
        reported = fields.get("has_results")
        values = [v.strip().lower() for v in _RESULTS_SEGMENT.findall(card.text)]
        if not isinstance(reported, bool) or not values:
            return "the results line cannot be checked against the report's has_results"
        if any((value in _YES) != reported or (value not in _YES and value not in _NO) for value in values):
            return "the quoted results line is not the report's has_results"
    return None


def card_claims(card: Card, source_fields: dict[str, Any] | None, *, quote_found: bool = True) -> dict[str, Any]:
    """The card as one claim of its own, judged by `gate.claims.evaluate_claims` under every claim policy, against the
    report's own fields, with the card as its own checked quote. The claim has no kind of its own, so each policy applies
    when the quote's words fall under it ("Overall status: COMPLETED" on a RECRUITING report fails `claim_planned`).
    Returns `{quote_id, passed, detail}`. If the claim module cannot run, the card fails (fail closed)."""
    label = f"{card.quote_id}, field {card.field}"
    claim = {"claim_kind": "", "text": card.text, "quote": card.text}
    try:
        results = gate_claims.evaluate_claims(
            [claim], dict(source_fields or {}), [{"text": card.text, "quote_found": quote_found}], gate_claims.CLAIM_POLICIES
        )
    except Exception as exc:  # noqa: BLE001 - any failure of the claim module refuses the quote
        return {"quote_id": card.quote_id, "passed": False, "detail": f"{label}: claim checks did not run ({type(exc).__name__})"}
    result = results[0] if results else {}
    passed = bool(result.get("passed") is True and not result.get("failed_policies"))
    detail = str(result.get("detail") or "no result from the claim checks")[:500]
    return {"quote_id": card.quote_id, "passed": passed, "detail": f"{label}: {detail}"}


def card_passes(card: Card, source_fields: dict[str, Any] | None) -> bool:
    """True when the card agrees with the report's own fields and passes every claim policy. The service drops a card
    that does not, before the question's vocabulary and the ranking see it."""
    return source_problem(card, source_fields) is None and card_claims(card, source_fields)["passed"]


async def verify_answer(
    answer: str,
    cards: list[Card],
    raw_texts: dict[str, str | None],
    quote_check: QuoteCheck | None = None,
    names: list[str] | None = None,
    source_fields: dict[str, Any] | None = None,
) -> Verification:
    """`raw_texts` maps a version_id to that version's raw text (None when unknown). `names` are the names the
    record gives, which an interventions card may list (none given: no interventions card can pass). `source_fields` are
    the report's own `overall_status` and `has_results`, which the claim checks judge each quote against."""
    check = quote_check or default_quote_check
    problems: list[str] = []
    claim_checks: list[dict[str, Any]] = []
    if not cards:
        return Verification(False, ["no cards"])

    for number, card in enumerate(cards, start=1):
        label = f"quote {number}"
        raw = raw_texts.get(card.version_id)
        quote_found = False
        if raw is None:
            problems.append(f"{label}: source version {card.version_id} is not available")
        else:
            found = check(card.text, raw)
            if inspect.isawaitable(found):
                found = await found
            quote_found = found is True
            if not quote_found:
                problems.append(f"{label}: quote not found in version {card.version_id}")
        if card.field == FIELD_OTHER:
            problems.append(f"{label}: no known field")
        if claim_like(card.text):
            problems.append(f"{label}: claim-like wording")
        if not shape_ok(card.field, card.text, names or []):
            problems.append(f"{label}: not in the shape of its field")
        if "\n" in card.text or card.text != normalise_text(card.text):
            problems.append(f"{label}: quote is not whitespace-normalised")
        mismatch = source_problem(card, source_fields)
        if mismatch:
            problems.append(f"{label}: {mismatch}")
        checked = card_claims(card, source_fields, quote_found=quote_found)
        claim_checks.append(checked)
        if not checked["passed"]:
            problems.append(f"{label}: failed a claim policy")

    if answer != render(cards):
        problems.append("answer text is not the rendering of its cited quotes")
    quote_blocks = {f'"{card.text}" [{n}]' for n, card in enumerate(cards, start=1)}
    outside_quotes: list[str] = []
    for block in split_blocks(answer):
        if block in quote_blocks and _QUOTE_BLOCK.match(block):
            continue
        outside_quotes.append(block)
        if not framing.allowed_framing([block]):
            problems.append("a block is neither an allowlisted framing sentence nor a cited quote")
    if _DIGITS.search(" ".join(outside_quotes)):
        problems.append("a number appears outside every cited quote")
    return Verification(not problems, problems, claim_checks)
