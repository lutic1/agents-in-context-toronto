"""Evidence checks (AD-6). Owned by A08 (D36).

`quote_in_source()` is the only quote check in DxP. Every quote that reaches a
Finding, a report or a relationship passes through it, against the `raw_text`
of the exact source version the quote is drawn from (V40), never the current
pointer.

A quote is word for word: the only differences tolerated are runs of
whitespace and typographic variants of quotes, apostrophes and dashes, and
Unicode compatibility forms (NFKC). Case, words, punctuation and order must
match. An ellipsis, a paraphrase or a stitched quote is not found.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["MAX_QUOTE_CHARS", "normalise_for_quote", "quote_in_source"]

#: A quote is at most 300 characters (AD-6).
MAX_QUOTE_CHARS = 300

_TYPOGRAPHIC = str.maketrans(
    {
        "‘": "'",  # left single quotation mark
        "’": "'",  # right single quotation mark
        "‚": "'",
        "‛": "'",
        "′": "'",  # prime
        "“": '"',  # left double quotation mark
        "”": '"',  # right double quotation mark
        "„": '"',
        "″": '"',
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen
        "‒": "-",  # figure dash
        "–": "-",  # en dash
        "—": "-",  # em dash
        "−": "-",  # minus sign
        "­": None,  # soft hyphen
    }
)

_WHITESPACE = re.compile(r"\s+")


def normalise_for_quote(text: str) -> str:
    """Normalise text for a word-for-word comparison.

    NFKC, typographic quotes and dashes folded to ASCII, every run of
    whitespace collapsed to one space, trimmed. Case is kept.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_TYPOGRAPHIC)
    return _WHITESPACE.sub(" ", text).strip()


def quote_in_source(quote: str | None, raw_text: str | None) -> bool:
    """Return True only if `quote` appears word for word in `raw_text`.

    False for an empty quote, an empty source, or a quote longer than
    `MAX_QUOTE_CHARS` (after normalisation). Never raises.
    """
    if not isinstance(quote, str) or not isinstance(raw_text, str):
        return False
    needle = normalise_for_quote(quote)
    if not needle or len(needle) > MAX_QUOTE_CHARS:
        return False
    haystack = normalise_for_quote(raw_text)
    if not haystack:
        return False
    return needle in haystack
