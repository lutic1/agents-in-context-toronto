"""Quote cards from an accepted report (V70, V40).

A card is one verbatim quote stored on the report with where it came from. The only sources are the
discovery's quotes and the accepted related evidence's two quotes per relationship, each pinned to
its `version_id`. Nothing is retrieved and nothing is taken from outside the report.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

__all__ = ["Card", "MAX_CARDS", "is_accepted", "load_cards", "looks_like_instruction", "mention_names"]

MAX_CARDS = 40
MAX_QUOTE_CHARS = 600

# A quote that talks to a model is not offered to it and never answers a question, even though it
# may be verbatim. A record has no reason to contain these phrases.
_INSTRUCTION = re.compile(
    r"ignore\s+(?:all\s+|any\s+|the\s+|your\s+|previous\s+|prior\s+|above\s+|earlier\s+)+(?:instructions?|prompts?|rules?|messages?)"
    r"|disregard\s+(?:all\s+|any\s+|the\s+|your\s+|previous\s+|prior\s+|above\s+)+(?:instructions?|prompts?|rules?)"
    r"|system\s+prompt|developer\s+message|you\s+are\s+now\b|act\s+as\s+(?:a|an|the)\b|new\s+instructions?"
    r"|do\s+not\s+follow|pretend\s+(?:to\s+be|you)|reveal\s+(?:your|the)\s+(?:prompt|instructions?)|</?\s*(?:system|assistant|user)\s*>"
    r"|\bselect\s+(?:quote\s+)?(?:id\s+)?qt_|as\s+an\s+ai\b|jailbreak",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Card:
    quote_id: str
    text: str
    source_ref: str
    version_id: str
    field: str  # "discovery" or "related"


def quote_id_for(source_ref: str, version_id: str, field: str, text: str) -> str:
    """A stable ID: the same quote on the same version always has the same ID."""
    digest = hashlib.sha256("\x1f".join((source_ref, version_id, field, text)).encode("utf-8")).hexdigest()
    return f"qt_{digest[:12]}"


def looks_like_instruction(text: str) -> bool:
    return bool(_INSTRUCTION.search(text))


def is_accepted(report: dict[str, Any]) -> bool:
    """Only an `accepted` report may be interviewed. Pending, rejected, reverting and reverted are not."""
    return report.get("status") == "accepted"


def mention_names(report: dict[str, Any]) -> list[str]:
    """The names the record gives verbatim (V37). A name is "named in the record", never used or studied."""
    mentions = (report.get("discovery") or {}).get("mentions") or []
    names = [m.get("name") for m in mentions if isinstance(m, dict) and isinstance(m.get("name"), str)]
    return [n for n in names if n.strip()]


def _usable(text: Any, version_id: Any, source_ref: Any, found: Any) -> bool:
    return (
        found is True
        and isinstance(text, str)
        and bool(text.strip())
        and len(text) <= MAX_QUOTE_CHARS
        and isinstance(version_id, str)
        and bool(version_id)
        and isinstance(source_ref, str)
        and bool(source_ref)
        and not looks_like_instruction(text)
    )


def load_cards(report: dict[str, Any]) -> list[Card]:
    """Every usable quote on the report, in report order, without duplicates.

    Discovery quotes carry the report's `source_ref` (and its `version_id` when they do not carry
    their own). Related evidence counts only when the relationship is `accepted`, and only a quote
    marked `quote_found` is used.
    """
    cards: list[Card] = []
    seen: set[tuple[str, str, str]] = set()

    def add(text: Any, source_ref: Any, version_id: Any, field: str, found: Any) -> None:
        if not _usable(text, version_id, source_ref, found):
            return
        key = (source_ref, version_id, text)
        if key in seen:
            return
        seen.add(key)
        cards.append(Card(quote_id_for(source_ref, version_id, field, text), text, source_ref, version_id, field))

    discovery = report.get("discovery") or {}
    for quote in discovery.get("quotes") or []:
        if isinstance(quote, dict):
            add(quote.get("text"), report.get("source_ref"), quote.get("version_id") or report.get("version_id"), "discovery", quote.get("quote_found"))

    for relationship in report.get("related") or []:
        if not isinstance(relationship, dict) or relationship.get("status") != "accepted":
            continue
        for key in ("new_quote", "related_quote"):
            quote = relationship.get(key)
            if isinstance(quote, dict):
                add(quote.get("text"), quote.get("source_ref"), quote.get("version_id"), "related", quote.get("quote_found"))

    return cards[:MAX_CARDS]
