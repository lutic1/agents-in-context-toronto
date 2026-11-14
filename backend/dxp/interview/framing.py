"""Framing sentences (V70 amendment). The only words in an answer that are not a cited verbatim quote.

- ALLOWLIST: a framing sentence comes only from the fixed list below, in code. The model never writes one. A
  sentence outside the list is dropped (`allowed_framing`).
- NO FACTS: a framing sentence never holds a digit, an NCT ID, a capitalised proper name or product, an assay
  name, a result word, or a first-person claim to be a product, company, trial or person ("I'm ..."). This is
  checked mechanically (`facts_in`); a string that fails is dropped. The allowlist passes the check, and a unit
  test holds both.
- PERSONA: "DxP's evidence guide". It never says "I'm" plus anything.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

__all__ = [
    "ALLOWLIST",
    "FIXED_REPLY_SENTENCES",
    "BLOCKED_SENTENCES",
    "MEDICAL_SENTENCES",
    "is_fixed_reply",
    "FRAME_INTRO",
    "FRAME_NOT_IN_RECORD",
    "FRAME_ONLY_RECORD",
    "FRAME_QUOTES",
    "PERSONA",
    "allowed_framing",
    "facts_in",
    "is_clean_framing",
]

PERSONA = "DxP's evidence guide"

FRAME_INTRO = "Here's what the accepted record says."
FRAME_ONLY_RECORD = "I can only answer from this record."
FRAME_NOT_IN_RECORD = "The accepted record doesn't answer that."
FRAME_QUOTES = "These are the quotes it rests on."

ALLOWLIST: tuple[str, ...] = (FRAME_INTRO, FRAME_ONLY_RECORD, FRAME_NOT_IN_RECORD, FRAME_QUOTES)

# The two other fixed replies the page serves as an answer, each built only from sentences listed HERE, in code, and
# each passing the same mechanical no-facts check (`facts_in`). They are the one medical refusal (V70 ruling: the
# fixed medical-advice refusal) and the reply for a blocked Decision. No model writes them and none is built from a
# question. They are not framing around quotes, so they are not in `ALLOWLIST` (the four sentences of the ruling).
MEDICAL_SENTENCES: tuple[str, ...] = (
    "This page can't give medical advice, a diagnosis or a treatment recommendation.",
    "It only quotes the accepted record.",
    "That is a question for a qualified clinician.",
)
BLOCKED_SENTENCES: tuple[str, ...] = (
    "The policy gate blocked this question, so no answer was given.",
    "The record of this decision explains why.",
)
FIXED_REPLY_SENTENCES: tuple[str, ...] = (*MEDICAL_SENTENCES, *BLOCKED_SENTENCES)

# What a sentence of framing may start with. Any other first word, capitalised, would be a name.
_STARTERS = frozenset({"here's", "here", "i", "the", "these", "this", "that", "those", "it", "there"})

_DIGIT = re.compile(r"\d")
_NCT = re.compile(r"\bNCT\s*[-:]?\s*\d*", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
_ALL_CAPS = re.compile(r"^[A-Z]{2,}$")
_INNER_CAPITAL = re.compile(r"[a-z][A-Z]")
_FIRST_PERSON_CLAIM = re.compile(r"\bI(?:['’]?m|\s+am)\b|\bmy\s+name\b|\bwe\s+are\b", re.IGNORECASE)
_ASSAY = re.compile(
    r"\b(?:assays?|tests?|tested|testing|panels?|ctdna|dna|rna|pcr|ngs|sequenc\w*|biops\w*|cdx|liquid|foundation\w*|guardant\w*|"
    r"biomarkers?|genom\w*|kits?|devices?|platforms?|products?|compan(?:y|ies)|manufactur\w*|sponsors?|trials?)\b",
    re.IGNORECASE,
)
_RESULT = re.compile(
    r"\b(?:results?|findings?|found|show(?:s|ed|n|ing)?|demonstrat\w*|sensitiv\w*|specific\w*|accura\w*|perform\w*|outperform\w*|"
    r"better|worse|superior|inferior|higher|lower|more|less|positive|negative|detect\w*|concordan\w*|agree\w*|respon\w*|surviv\w*|"
    r"effective\w*|efficac\w*|significan\w*|improv\w*|reduc\w*|increas\w*|outcomes?|rates?|percent\w*|prov(?:e|es|ed|en)|"
    r"confirm\w*|valid\w*|success\w*|benefit\w*)\b|%",
    re.IGNORECASE,
)


def facts_in(sentence: str) -> list[str]:
    """What a framing sentence says that it may not: an empty list means it states no fact."""
    found: list[str] = []
    if _DIGIT.search(sentence):
        found.append("digit")
    if _NCT.search(sentence):
        found.append("nct_id")
    if _FIRST_PERSON_CLAIM.search(sentence):
        found.append("persona_claim")
    if _ASSAY.search(sentence):
        found.append("assay_or_product_word")
    if _RESULT.search(sentence):
        found.append("result_word")
    words = _WORD.findall(sentence)
    for index, word in enumerate(words):
        bare = word.strip("'’-")
        if _ALL_CAPS.match(bare) and bare != "I":
            found.append("all_caps_name")
        elif _INNER_CAPITAL.search(bare):
            found.append("inner_capital_name")
        elif index == 0 and bare.lower() not in _STARTERS:
            found.append("unlisted_first_word")
        elif index > 0 and bare[:1].isupper() and bare != "I" and not bare.startswith("I'"):
            found.append("capitalised_name")
    return sorted(set(found))


def is_clean_framing(sentence: str) -> bool:
    return not facts_in(sentence)


def is_fixed_reply(text: str, sentences: Iterable[str] = FIXED_REPLY_SENTENCES) -> bool:
    """True when `text` is made only of listed fixed-reply or framing sentences, each passing the no-facts check."""
    listed = {*sentences, *ALLOWLIST}
    parts = [part for part in re.split(r"(?<=\.)\s+", text.strip()) if part]
    return bool(parts) and all(part in listed and is_clean_framing(part) for part in parts)


def allowed_framing(candidates: Iterable[str]) -> list[str]:
    """Only sentences that are on the allowlist exactly and pass the no-facts check; everything else is dropped."""
    return [s for s in candidates if s in ALLOWLIST and is_clean_framing(s)]
