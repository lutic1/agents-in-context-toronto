"""The question gate (V70, steps A.ii and A.iii). Deterministic; no model is involved.

Step A.i (medical) is `medical.py` and runs before this. This module decides, from the question and the record
alone, whether the question may be answered at all:

- INTENT ALLOWLIST: the question must map to exactly one fixed intent (`intents.py`). None, or two with the
  same score, is "not in the record".
- OFF-TOPIC GUARD: every content word of the question (not a stopword, not an intent keyword) must be a word of
  the record's vocabulary: the text of its cards plus the report title. One word outside the record, and the
  question is about something else, so it is "not in the record". "What is the status of the Moon landing?" has
  the intent "status" and two words the record does not have.

The vocabulary is the report title plus ONLY the eligible cards of the matched intent (service.build_answer passes
them), so a word that lives in another field ("Canada" in a location card, asked as a status) is off-topic.

Also refused here, before any intent: a letter outside ASCII (a language the gate cannot read), a run of three or
more single letters (a question typed one letter at a time), and definitional or general-knowledge frames ("what
is a cohort", "what does X mean", "what date is it").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from dxp.interview import intents
from dxp.interview.cards import Card, claim_like, comparison_like
from dxp.interview.textfold import has_non_latin_letter, strip_invisible

__all__ = ["Verdict", "classify_intent", "off_topic_words", "vocabulary"]

REASON_NO_INTENT = "no_intent"
REASON_AMBIGUOUS = "ambiguous_intent"
REASON_OFF_TOPIC = "off_topic"
REASON_CLAIM = "claim_question"
REASON_NON_LATIN = "non_latin"
REASON_GENERAL = "general_or_definition"
REASON_SPACED = "spaced_letters"

# Nouns that name a field of the record. "What is the status?" asks for a field; "What is a cohort?" or "What is
# RECRUITING?" asks for a definition, which the record does not give.
_FIELD_NOUNS = frozenset(
    """status date dates phase phases condition conditions design sponsor sponsors location locations enrollment enrolment size results result
    intervention interventions population purpose aim aims objective allocation masking timeline indication""".split()
)
_ONE_WORD_WHAT = re.compile(r"^\s*(?:what(?:'s|s| is| are)|define)\s+(?:an?\s+|the\s+)?([a-z]+)\s*[?.!]?\s*$")
_GENERAL = re.compile(
    r"\bmean(?:s|ing|t)?\b|\bdefin\w*|\bexplain\w*|\bwhat(?:'s| is| are| does)? (?:an?)\b|"
    r"\bwhat date is it\b|\bwhat(?:'s| is) (?:the )?(?:date|time|day) (?:today|now)\b|\bhow many (?:people|persons) live\b|"
    r"\bwhich (?:country|city|state|province|continent) is (?!the\b|this\b|it\b|that\b)\w+ (?:in|located)\b|\bwho (?:is|was) (?:the )?(?:president|king|queen|ceo)\b"
)


@dataclass(frozen=True)
class Verdict:
    intent: intents.Intent | None
    reason: str  # "ok", or why there is no intent


def classify_intent(question: str) -> Verdict:
    """The one intent of the question. A question that itself asks for a comparison or a performance ("better than",
    "more sensitive", a percentage) has none: the record's fields are not a place to look that up."""
    if has_non_latin_letter(question):
        return Verdict(None, REASON_NON_LATIN)
    question = strip_invisible(question)
    lowered = question.lower().replace("\u2019", "'")
    if spaced_letters(lowered):
        return Verdict(None, REASON_SPACED)
    if _GENERAL.search(lowered):
        return Verdict(None, REASON_GENERAL)
    one_word = _ONE_WORD_WHAT.match(lowered)
    if one_word and one_word.group(1) not in _FIELD_NOUNS and intents.stem(one_word.group(1)) not in {intents.stem(n) for n in _FIELD_NOUNS}:
        return Verdict(None, REASON_GENERAL)
    if comparison_like(question):
        return Verdict(None, REASON_CLAIM)
    intent, reason = intents.match_intent(question)
    return Verdict(intent, reason)


def spaced_letters(lowered: str) -> bool:
    """Three or more single letters in a row: a question typed one letter at a time ("w h a t d o s e")."""
    run = 0
    for token in re.findall(r"[a-z0-9']+", lowered):
        if len(token) == 1 and token.isalpha():
            run += 1
            if run >= 3:
                return True
        else:
            run = 0
    return False


def vocabulary(report: dict[str, Any], cards: list[Card]) -> frozenset[str]:
    """The record's words, stemmed: its title, its source reference and the text of the cards it is given (the eligible
    cards of the matched intent) that are not claim-like."""
    title = report.get("title") or report.get("headline") or ""
    texts = [title if isinstance(title, str) else "", str(report.get("source_ref") or "")]
    texts += [card.text for card in cards if not claim_like(card.text)]
    return frozenset(intents.stem(token) for text in texts for token in intents.tokenise(text))


def off_topic_words(question: str, record_words: frozenset[str], intent: intents.Intent | None = None) -> list[str]:
    """The content words of the question that are neither stopwords, nor a keyword of the MATCHED intent, nor in
    the record's vocabulary. A keyword of another intent ("cohort", asked as a date) is not exempt."""
    every_keyword: set[str] = set() if intent is None else set(intents.keyword_stems(intent))
    if intent is None:
        for candidate in intents.INTENTS:
            every_keyword |= intents.keyword_stems(candidate)
    outside: list[str] = []
    # No single-letter token is exempt. Only the English contractions are read as words: "n't" is "not", and "'s", "'re",
    # "'ve", "'ll", "'d", "'m" after a word are dropped. Any other one-letter token ("m", "e", "s") is a word like the
    # rest and must be a stopword, a keyword or in the record.
    cleaned = strip_invisible(question).lower().replace("\u2019", "'")
    cleaned = re.sub(r"n't\b", " not", cleaned)
    cleaned = re.sub(r"(?<=[a-z])'(?:s|re|ve|ll|d|m)\b", " ", cleaned)
    if spaced_letters(cleaned):
        return ["spaced letters"]
    for token in intents.tokenise(cleaned):
        word = intents.stem(token)
        if word in intents.STOPWORDS or word in every_keyword or word in record_words:
            continue
        outside.append(token)
    return outside
