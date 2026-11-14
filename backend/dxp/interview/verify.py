"""Verification of an answer before it is returned (V70, V33, V37, AD-6, AD-19).

Every check fails closed. The answer is returned only if all of these hold:

1. every sentence cites exactly one card that is on the report;
2. the cited quote is found in the raw text of the exact source version it names (V40);
3. a number appears only inside its cited quote (the lead-in has none of its own);
4. the lead-in is one of the fixed ones, and says nothing like "uses", "studies" or "showed":
   a name is "named in the record" (V37);
5. the answer text holds nothing but lead-ins, verbatim quotes and citation markers;
6. the claim wording in a quote is tagged for the gate's claim checks, which decide it (AD-19).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from dxp.api.models import ClaimCheck
from dxp.interview.cards import Card
from dxp.interview.compose import MARKER, Sentence, lead_in_for, render

__all__ = ["Verification", "claim_guard_blocks", "claim_tags", "default_quote_check", "verify_answer"]

QuoteCheck = Callable[[str, str], "bool | Awaitable[bool]"]

# What a lead-in may never say about a name or a trial (V33, V37) or about a result.
_FORBIDDEN_WORDING = re.compile(
    r"\b(?:use[sd]?|using|usage|stud(?:y|ies|ied|ying)|investigat\w*|test(?:s|ed|ing)?|evaluat\w*|show(?:s|ed|n)?|demonstrat\w*|"
    r"prov(?:e|es|ed|en)|confirm\w*|validat\w*|perform(?:s|ed|ance)?|detect\w*|measur\w*|outperform\w*)\b",
    re.IGNORECASE,
)
_DIGITS = re.compile(r"\d+")

# Claim wording in a quote. The gate's claim checks decide; these only tag what to send.
_NEGATED_RESULTS = re.compile(r"\b(?:no|not|without|none|yet\s+to|awaiting|pending)\b[^.;:]{0,40}\b(?:results?|data)\b", re.IGNORECASE)
_PERFORMED = re.compile(
    r"\b(?:performed|perform\w*|detected|detects?|detection|showed|shows?|shown|demonstrat\w+|results?|sensitiv\w*|specific\w*|concordance|"
    r"accura\w*|agreement|outperform\w*|yielded|positive\s+percent|negative\s+percent|limit\s+of\s+detection|"
    r"identif\w*|classif\w*|achiev\w*|auc|ppv|npv|predict\w*|valid\w*|recover\w*|observed|response|responses|survival|improv\w*|"
    r"caught|found|genotyp\w*\s+(?:the|a|all)|was\s+used|were\s+used|uses?|stud(?:y|ies)\s+(?:the|a|an)|evaluated|measured|reliab\w*|"
    r"correctly|missed|false\s+(?:positive|negative)s?|true\s+(?:positive|negative)s?|prevalence|reduc\w*|increas\w*|outcomes?\s+(?:was|were))\b"
    # A percentage or a ratio ("12 of 14") is a figure from a result, whatever verb is around it.
    r"|\d+(?:\.\d+)?\s*(?:%|percent\b)|\b\d+\s+of\s+(?:the\s+)?\d+\b",
    re.IGNORECASE,
)
# A record name with a verb that says what was done with it: "used", "studied", "tested" (V37).
_NAME_VERB = re.compile(r"\b(?:use[sd]?|using|stud(?:y|ies|ied|ying)|evaluat\w*|test(?:s|ed|ing)?|measur\w*|assess\w*|analy[sz]\w*|profil\w*)\b", re.IGNORECASE)
_PLANNED = re.compile(
    r"\b(?:planned|plans?|will|anticipated|expected|estimated|not\s+yet\s+recruiting|recruit\w*|enrol\w*|ongoing|completed|terminated|withdrawn)\b",
    re.IGNORECASE,
)
_PRECLINICAL = re.compile(
    r"\b(?:cell[\s-]lines?|xenografts?|mouse|mice|murine|rats?|animals?|in\s+vitro|in\s+vivo|preclinical|zebrafish|organoids?|pdx)\b",
    re.IGNORECASE,
)


@dataclass
class Verification:
    ok: bool
    problems: list[str] = field(default_factory=list)
    claims: list[ClaimCheck] = field(default_factory=list)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def default_quote_check(quote: str, raw_text: str) -> bool | Awaitable[bool]:
    """`evidence.quote_in_source(quote, raw_text)` (AD-6, A08) when it is on main. Until then, a
    whitespace- and case-insensitive substring test, which can only be stricter than word for word
    on content and never accepts a quote that is not in the text."""
    from dxp import evidence

    real = getattr(evidence, "quote_in_source", None)
    if callable(real):
        return real(quote, raw_text)
    return _normalise(quote) in _normalise(raw_text)


def claim_tags(text: str, names: list[str] | None = None) -> list[str]:
    """Which claim kinds a quote's wording touches. It fails closed: any performance or result wording,
    any figure that is a percentage or a ratio, and any record name next to a verb that says what was
    done with it is tagged claim_performed_or_results. A negated "no results" is not a claim."""
    kinds: list[str] = []
    performed = _PERFORMED.search(_NEGATED_RESULTS.sub(" ", text)) is not None
    if not performed and names:
        performed = any(
            name.lower() in text.lower() and _NAME_VERB.search(re.sub(re.escape(name), " ", text, flags=re.IGNORECASE)) for name in names
        )
    if performed:
        kinds.append("claim_performed_or_results")
    if _PLANNED.search(text):
        kinds.append("claim_planned")
    if _PRECLINICAL.search(text):
        kinds.append("claim_preclinical")
    return kinds


def claim_guard_blocks(card: Card, report: dict[str, Any]) -> bool:
    """A local floor under the gate's claim check (V7, AD-19): a quote that states a performance or a
    result is not used unless the report's discovery has posted results (`has_results` true), whatever
    the trial status. A related record's own results are not on the report, so a related quote with
    that wording is never used here. The gate still decides everything that passes."""
    from dxp.interview.cards import mention_names

    if "claim_performed_or_results" not in claim_tags(card.text, mention_names(report)):
        return False
    if card.field != "discovery":
        return True
    return (report.get("discovery") or {}).get("has_results") is not True


def _lead_in_ok(sentence: Sentence, names: list[str]) -> str | None:
    """The lead-in must be exactly the fixed one for this quote, and say nothing a name is not (V37)."""
    if sentence.lead_in != lead_in_for(sentence.card, names):
        return "lead-in is not the fixed lead-in for this quote"
    if not _only_inside_name(sentence.lead_in, names):
        return "lead-in has forbidden wording"
    return None


def _only_inside_name(lead: str, names: list[str]) -> bool:
    """A record name may itself contain a word like "Test" (a product name); that is the record's, not DxP's."""
    stripped = lead
    for name in names:
        stripped = re.sub(re.escape(name), " ", stripped, flags=re.IGNORECASE)
    return _FORBIDDEN_WORDING.search(stripped) is None


def _residue(answer: str, sentences: list[Sentence]) -> str:
    rest = MARKER.sub("", answer)
    for sentence in sentences:
        rest = rest.replace(sentence.card.text, "", 1).replace(sentence.lead_in, "", 1)
    return re.sub(r'[\s"]+', "", rest)


async def verify_answer(
    answer: str,
    sentences: list[Sentence],
    names: list[str],
    raw_texts: dict[str, str | None],
    quote_check: QuoteCheck | None = None,
) -> Verification:
    """`raw_texts` maps a version_id to that version's raw text (None when unknown)."""
    check = quote_check or default_quote_check
    problems: list[str] = []
    claims: list[ClaimCheck] = []
    if not sentences:
        return Verification(False, ["no sentences"])

    for number, sentence in enumerate(sentences, start=1):
        card = sentence.card
        label = f"sentence {number}"
        raw = raw_texts.get(card.version_id)
        if raw is None:
            problems.append(f"{label}: source version {card.version_id} is not available")
        else:
            found = check(card.text, raw)
            if inspect.isawaitable(found):
                found = await found
            if found is not True:
                problems.append(f"{label}: quote not found in version {card.version_id}")
        extra = set(_DIGITS.findall(sentence.lead_in)) - set(_DIGITS.findall(card.text))
        if extra:
            problems.append(f"{label}: number {sorted(extra)[0]} is not inside its cited quote")
        problem = _lead_in_ok(sentence, names)
        if problem:
            problems.append(f"{label}: {problem}")
        for kind in claim_tags(card.text, names):
            claims.append(
                ClaimCheck(claim_kind=kind, text=card.text[:300], passed=False, detail=f"{label}, {card.quote_id}: tagged by the interview lane; the gate decides")
            )

    if answer != render(sentences):
        problems.append("answer text is not the rendering of its cited sentences")
    if _residue(answer, sentences):
        problems.append("answer holds text that is not a fixed lead-in, a cited quote or a citation marker")
    cited_numbers = {n for s in sentences for n in _DIGITS.findall(s.card.text)}
    stray = set(_DIGITS.findall(MARKER.sub("", answer))) - cited_numbers
    if stray:
        problems.append(f"number {sorted(stray)[0]} appears outside every cited quote")
    return Verification(not problems, problems, claims)
