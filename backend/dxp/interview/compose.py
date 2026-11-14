"""Answer text (V70): allowlisted framing plus verbatim quotes. Nothing else is ever in an answer.

An answer is, in blocks separated by one blank line:

    Here's what the accepted record says.        <- framing, from the fixed allowlist
    "<quote>" [1]                                <- one cited verbatim quote per block, numbered
    "<quote>" [2]
    These are the quotes it rests on.            <- framing, from the fixed allowlist

A quote never holds a line break (cards normalise them away), so a block is always one quote and the page can
tell a quote from a framing sentence by its shape. DxP states no fact in its own words, ever.
"""

from __future__ import annotations

import re

from dxp.interview import framing
from dxp.interview.cards import Card

__all__ = ["MARKER", "compose", "quote_block", "render", "split_blocks"]

MARKER = re.compile(r"\[\d+\]")


def quote_block(card: Card, number: int) -> str:
    return f'"{card.text}" [{number}]'


def compose(cards: list[Card]) -> list[str]:
    """The blocks of an answer, framing first and last. The framing is filtered through the allowlist and the
    no-facts check, so a string that is not allowed could never get in."""
    intro = framing.allowed_framing([framing.FRAME_INTRO])
    outro = framing.allowed_framing([framing.FRAME_QUOTES])
    return [*intro, *(quote_block(card, n) for n, card in enumerate(cards, start=1)), *outro]


def render(cards: list[Card]) -> str:
    return "\n\n".join(compose(cards))


def split_blocks(answer: str) -> list[str]:
    return [block for block in answer.split("\n\n")]
