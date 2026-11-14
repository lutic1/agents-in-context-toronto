"""Verification of an answer before it is returned (V70, V33, V37, AD-6, AD-19).

Every check fails closed. The answer is returned only if all of these hold:

1. the answer is exactly the rendering of its cited cards: allowlisted framing, then one `"<quote>" [n]` block
   per card, then allowlisted framing (so nothing else, in any form, is in it);
2. every framing block is on the allowlist AND passes the mechanical no-facts check;
3. each cited quote is found in the raw text of the exact source version it names (V40), compared on the
   whitespace-normalised form;
4. no card is claim-like and no card is of the "other" field (a second net under the cards' own rules);
5. no digit appears outside a cited quote;
6. every claim kind is sent to the gate for every cited quote; the gate decides (AD-19).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from dxp.api.models import ClaimCheck
from dxp.interview import framing
from dxp.interview.cards import FIELD_OTHER, Card, claim_like, normalise_text
from dxp.interview.compose import render, split_blocks

__all__ = ["CLAIM_KINDS", "QuoteCheck", "Verification", "default_quote_check", "verify_answer"]

CLAIM_KINDS = ("claim_performed_or_results", "claim_planned", "claim_preclinical")
QuoteCheck = Callable[[str, str], "bool | Awaitable[bool]"]
_DIGITS = re.compile(r"\d")
_QUOTE_BLOCK = re.compile(r'^"[^\n]*" \[\d+\]$')


@dataclass
class Verification:
    ok: bool
    problems: list[str] = field(default_factory=list)
    claims: list[ClaimCheck] = field(default_factory=list)


def default_quote_check(quote: str, raw_text: str) -> bool | Awaitable[bool]:
    """`evidence.quote_in_source(quote, raw_text)` (AD-6, A08) when it is on main. Until then, a
    whitespace- and case-insensitive substring test, which can only be stricter than word for word
    on content and never accepts a quote that is not in the text."""
    from dxp import evidence

    real = getattr(evidence, "quote_in_source", None)
    if callable(real):
        return real(quote, raw_text)
    return normalise_text(quote).lower() in normalise_text(raw_text).lower()


async def verify_answer(
    answer: str,
    cards: list[Card],
    raw_texts: dict[str, str | None],
    quote_check: QuoteCheck | None = None,
) -> Verification:
    """`raw_texts` maps a version_id to that version's raw text (None when unknown)."""
    check = quote_check or default_quote_check
    problems: list[str] = []
    claims: list[ClaimCheck] = []
    if not cards:
        return Verification(False, ["no cards"])

    for number, card in enumerate(cards, start=1):
        label = f"quote {number}"
        raw = raw_texts.get(card.version_id)
        if raw is None:
            problems.append(f"{label}: source version {card.version_id} is not available")
        else:
            found = check(card.text, raw)
            if inspect.isawaitable(found):
                found = await found
            if found is not True:
                problems.append(f"{label}: quote not found in version {card.version_id}")
        if card.field == FIELD_OTHER:
            problems.append(f"{label}: no known field")
        if claim_like(card.text):
            problems.append(f"{label}: claim-like wording")
        if "\n" in card.text or card.text != normalise_text(card.text):
            problems.append(f"{label}: quote is not whitespace-normalised")
        for kind in CLAIM_KINDS:
            claims.append(
                ClaimCheck(
                    claim_kind=kind,
                    text=card.text[:300],
                    passed=False,
                    detail=f"{label}, {card.quote_id}, field {card.field}: sent to the gate; the lane's field and claim rules already applied",
                )
            )

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
    return Verification(not problems, problems, claims)
