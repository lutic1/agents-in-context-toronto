"""Relationship classification: the pure parts (AD-26, Story 10.3).

A label stands only when the model output is well formed and both quotes are
found in the source version each names. Anything else is
"related (no relationship established)". The similarity score is carried
through and never read.
"""
from __future__ import annotations

from typing import Any

from dxp.api.models import Relationship

LABELS = ("supports", "contradicts", "extends", "new_question")
UNESTABLISHED = "related_unestablished"
UNESTABLISHED_TEXT = "related (no relationship established)"
MAX_QUOTE_CHARS = 300


def valid_label(label):
    return isinstance(label, str) and label in LABELS


def label_text(label):
    """What a screen shows for a label."""
    return UNESTABLISHED_TEXT if label == UNESTABLISHED else label


def _quote_text(value):
    """A quote as the model gave it, or None if it is not a usable quote."""
    if isinstance(value, dict):
        value = value.get("text")
    if not isinstance(value, str):
        return None
    if not value.strip() or len(value) > MAX_QUOTE_CHARS:
        return None
    return value


def parse_proposal(output):
    """Validate the model's proposed relationship.

    Returns { label, rationale, new_quote, related_quote } or None when the
    output is malformed: not a mapping, a label outside LABELS, no rationale,
    or a quote that is missing, empty or longer than MAX_QUOTE_CHARS.
    """
    if not isinstance(output, dict):
        return None
    label = output.get("label")
    rationale = output.get("rationale")
    new_quote = _quote_text(output.get("new_quote"))
    related_quote = _quote_text(output.get("related_quote"))
    if not valid_label(label):
        return None
    if not isinstance(rationale, str) or not rationale.strip():
        return None
    if new_quote is None or related_quote is None:
        return None
    return {
        "label": label,
        "rationale": rationale.strip(),
        "new_quote": new_quote,
        "related_quote": related_quote,
    }


def check_quote(quote, item, quote_in_source):
    """True only if the injected check finds the quote in the item's raw_text."""
    raw_text = (item or {}).get("raw_text")
    if not isinstance(quote, str) or not quote or not isinstance(raw_text, str) or not raw_text:
        return False
    try:
        return quote_in_source(quote, raw_text) is True
    except Exception:
        return False


def _quote(item, text, found):
    item = item or {}
    return {
        "source_ref": item.get("source_ref"),
        "version_id": item.get("version_id"),
        "text": text,
        "quote_found": found,
    }


def build_relationship(
    output,
    new_item,
    related_item,
    quote_in_source,
    *,
    similarity=None,
    retrieval_method=None,
    origin="discovery",
    rel_id=None,
):
    """The Relationship (AD-14) for one related item, from the model output.

    `output` is the model's structured answer, or None after a model error or
    refusal. Never raises on bad model output or a failing quote check.
    """
    proposal = parse_proposal(output)
    if proposal is None:
        label, rationale = UNESTABLISHED, None
        new_quote = _quote(new_item, "", False)
        related_quote = _quote(related_item, "", False)
    else:
        new_found = check_quote(proposal["new_quote"], new_item, quote_in_source)
        related_found = check_quote(proposal["related_quote"], related_item, quote_in_source)
        new_quote = _quote(new_item, proposal["new_quote"], new_found)
        related_quote = _quote(related_item, proposal["related_quote"], related_found)
        if new_found and related_found:
            label, rationale = proposal["label"], proposal["rationale"]
        else:
            label, rationale = UNESTABLISHED, None
    related_item = related_item or {}
    return {
        "id": rel_id,
        "related_ref": related_item.get("ref") or related_item.get("source_ref"),
        "related_kind": related_item.get("kind") or "source_item",
        "related_title": related_item.get("title"),
        "label": label,
        "rationale": rationale,
        "new_quote": new_quote,
        "related_quote": related_quote,
        "similarity": similarity,
        "retrieval_method": retrieval_method,
        "origin": origin,
        "status": "pending",
        "filed_by_decision_id": None,
    }


def is_established(relationship):
    return (
        valid_label(relationship.get("label"))
        and relationship.get("new_quote", {}).get("quote_found") is True
        and relationship.get("related_quote", {}).get("quote_found") is True
    )


async def relate(new_item: dict[str, Any], related_item: dict[str, Any]) -> Relationship:
    """supports | contradicts | extends | new_question, or related_unestablished without two found quotes."""
    raise NotImplementedError("reports.relate (A19+A20)")
