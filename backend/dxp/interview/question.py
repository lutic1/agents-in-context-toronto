"""The question gate (V70, steps A.ii and A.iii). Deterministic; no model is involved.

Step A.i (medical) is `medical.py` and runs before this. This module decides, from the question and the record
alone, whether the question may be answered at all:

- INTENT ALLOWLIST: the question must map to exactly one fixed intent (`intents.py`). None, or two with the
  same score, is "not in the record".
- OFF-TOPIC GUARD: every content word of the question (not a stopword, not an intent keyword) must be a word of
  the record's vocabulary: the text of its cards plus the report title. One word outside the record, and the
  question is about something else, so it is "not in the record". "What is the status of the Moon landing?" has
  the intent "status" and two words the record does not have.

The vocabulary is built from cards that are not claim-like, so a comparison the record happens to contain
("better than") never makes a question about comparing available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dxp.interview import intents
from dxp.interview.cards import Card, claim_like, comparison_like

__all__ = ["Verdict", "classify_intent", "off_topic_words", "vocabulary"]

REASON_NO_INTENT = "no_intent"
REASON_AMBIGUOUS = "ambiguous_intent"
REASON_OFF_TOPIC = "off_topic"
REASON_CLAIM = "claim_question"


@dataclass(frozen=True)
class Verdict:
    intent: intents.Intent | None
    reason: str  # "ok", or why there is no intent


def classify_intent(question: str) -> Verdict:
    """The one intent of the question. A question that itself asks for a comparison or a performance ("better than",
    "more sensitive", a percentage) has none: the record's fields are not a place to look that up."""
    if comparison_like(question):
        return Verdict(None, REASON_CLAIM)
    intent, reason = intents.match_intent(question)
    return Verdict(intent, reason)


def vocabulary(report: dict[str, Any], cards: list[Card]) -> frozenset[str]:
    """The record's words, stemmed: its title, its source reference and the text of every card that is not claim-like."""
    title = report.get("title") or report.get("headline") or ""
    texts = [title if isinstance(title, str) else "", str(report.get("source_ref") or "")]
    texts += [card.text for card in cards if not claim_like(card.text)]
    return frozenset(intents.stem(token) for text in texts for token in intents.tokenise(text))


def off_topic_words(question: str, record_words: frozenset[str]) -> list[str]:
    """The content words of the question that are neither stopwords, nor an intent keyword, nor in the record."""
    every_keyword: set[str] = set()
    for candidate in intents.INTENTS:
        every_keyword |= intents.keyword_stems(candidate)
    outside: list[str] = []
    for token in intents.tokenise(question):
        if len(token) == 1 and token.isalpha():  # the "s" of "record's"
            continue
        word = intents.stem(token)
        if word in intents.STOPWORDS or word in every_keyword or word in record_words:
            continue
        outside.append(token)
    return outside
