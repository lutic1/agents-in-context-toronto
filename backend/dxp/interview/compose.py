"""Answer text (V70): fixed lead-ins plus verbatim quotes. Nothing else is ever in an answer.

A sentence is `<lead-in> "<quote>" [n]`, where n numbers the citation. Sentences are separated by a
blank line. The lead-in comes from a short fixed list, so DxP never says that a trial "uses" or
"studies" a product: a name in a quote is introduced as "<name> is named in the record:".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from dxp.interview import texts
from dxp.interview.cards import Card

__all__ = ["Sentence", "compose", "lead_in_for", "mentions_in", "render", "MARKER"]

MARKER = re.compile(r"\[\d+\]")


@dataclass(frozen=True)
class Sentence:
    lead_in: str
    card: Card


def mentions_in(text: str, names: list[str]) -> list[str]:
    """The record's names found in the quote, as the quote spells them, in the order they appear.
    A name that sits inside a longer name found at the same place is not listed twice."""
    lowered = text.lower()
    found: list[tuple[int, int, str]] = []
    for name in sorted({n for n in names if n.strip()}, key=len, reverse=True):
        start = lowered.find(name.lower())
        if start < 0:
            continue
        end = start + len(name)
        if any(s <= start and end <= e for s, e, _ in found):
            continue
        found.append((start, end, text[start:end]))
    return [spelled for _, _, spelled in sorted(found)]


def join_names(spelled: list[str]) -> str:
    if len(spelled) <= 2:
        return " and ".join(spelled)
    return ", ".join(spelled[:-1]) + " and " + spelled[-1]


def lead_in_for(card: Card, names: list[str]) -> str:
    """The one fixed lead-in for this quote. A name is "named in the record" (V37), nothing more."""
    spelled = mentions_in(card.text, names)
    if len(spelled) == 1:
        return texts.LEAD_MENTION.format(names=spelled[0], verb="is")
    if spelled:
        return texts.LEAD_MENTION.format(names=join_names(spelled), verb="are")
    return texts.LEAD_RELATED if card.field == "related" else texts.LEAD_DISCOVERY


def compose(cards: list[Card], names: list[str]) -> list[Sentence]:
    return [Sentence(lead_in_for(card, names), card) for card in cards]


def render(sentences: list[Sentence]) -> str:
    return "\n\n".join(f'{s.lead_in} "{s.card.text}" [{n}]' for n, s in enumerate(sentences, start=1))
