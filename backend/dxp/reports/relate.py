"""Relationship classification: the pure parts (AD-26, Story 10.3).

A label stands only when the model output is well formed and both quotes are
found in the source version each names. Anything else is
"related (no relationship established)". The similarity score is carried
through and never read.
"""
from __future__ import annotations

import logging
from typing import Any

from dxp.api.models import Relationship

log = logging.getLogger("dxp.reports")

MODEL_FALLBACK = "claude-sonnet-5-5"  # used only until llm.MODEL_IDS exists (A08)
MAX_RECORD_CHARS = 24000

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


# ------------------------------------------------------------ the frozen call

def _plain(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return dict(item or {})


def _names(*items: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in items:
        for mention in item.get("mentions") or item.get("name_mentions") or []:
            name = mention.get("name") if isinstance(mention, dict) else getattr(mention, "name", mention)
            if isinstance(name, str) and name.strip() and name not in names:
                names.append(name)
    return names


async def load_item(item: Any) -> dict[str, Any]:
    """An item with what a relationship needs: ref, kind, source_ref, version_id, title, raw_text.

    Accepts a source item, a Finding or a `Retrieval` item (`{ ref, version_id, score }`).
    Whatever is missing is read from the store, and the text is always the `raw_text` of
    the exact version the item names (V40). The current pointer is never read for a version: an
    item that names none stays unpinned, so its relationship cannot be labelled or listed.
    """
    from dxp import store

    out = _plain(item)
    ref = out.get("ref") or out.get("finding_id") or out.get("source_ref") or out.get("id") or out.get("_id")
    out["ref"] = ref
    out.setdefault("kind", "finding" if isinstance(ref, str) and ref.startswith("f_") else "source_item")
    try:
        db = store.db()
        if out["kind"] == "finding" and not (out.get("source_ref") and out.get("version_id")):
            finding = await db["findings"].find_one({"_id": ref}) or {}
            out["source_ref"] = out.get("source_ref") or finding.get("source_ref")
            out["version_id"] = out.get("version_id") or finding.get("version_id")
            out["title"] = out.get("title") or finding.get("summary")
        out["source_ref"] = out.get("source_ref") or ref
        if not out.get("title"):
            source = await db["source_items"].find_one({"_id": out["source_ref"]}) or {}
            out["title"] = source.get("title") or source.get("brief_title")
        if not out.get("raw_text") and out.get("version_id"):
            version = await db["source_versions"].find_one({"_id": out["version_id"]}) or {}
            out["raw_text"] = version.get("raw_text")
            out["title"] = out.get("title") or version.get("title")
    except Exception as exc:
        log.warning("reports.relate: could not load %s: %s", out.get("kind"), type(exc).__name__)
        out["source_ref"] = out.get("source_ref") or ref
    return out


async def _ask(new: dict[str, Any], related: dict[str, Any]) -> dict[str, Any] | None:
    """The model's proposal, or None on any error, refusal or non-object answer."""
    from dxp import llm
    from dxp.llm.prompts import relate as prompt

    try:
        model = (getattr(llm, "MODEL_IDS", None) or {}).get("strong", MODEL_FALLBACK)  # AD-11
        output = await llm.call_structured(model, prompt.SCHEMA, [
            {"role": "system", "content": prompt.SYSTEM},
            {"role": "user", "content": prompt.USER.format(
                new_ref=new.get("source_ref"),
                new_text=new["raw_text"][:MAX_RECORD_CHARS],
                related_ref=related.get("ref"),
                related_text=related["raw_text"][:MAX_RECORD_CHARS],
            )},
        ])
    except Exception as exc:
        log.warning("reports.relate: model call failed: %s", type(exc).__name__)
        return None
    return output if isinstance(output, dict) else None


def relationship_id(report_id: str | None, source_ref: str | None, related_ref: str | None) -> str:
    """derive("rel_", report_id, source_ref, related_ref) (AD-3); "-" stands for a part not known yet."""
    from dxp import identity

    return identity.derive("rel_", report_id or "-", source_ref or "-", related_ref or "-")


async def relate(new_item: dict[str, Any], related_item: dict[str, Any]) -> Relationship:
    """supports | contradicts | extends | new_question, or related_unestablished without two found quotes."""
    from dxp import evidence
    from dxp.reports.draft import wording_flags

    new = await load_item(new_item)
    related = await load_item(related_item)
    output = None
    if isinstance(new.get("raw_text"), str) and isinstance(related.get("raw_text"), str):
        output = await _ask(new, related)
    checker = getattr(evidence, "quote_in_source", None) or (lambda quote, raw_text: False)
    built = build_relationship(
        output,
        new,
        related,
        checker,
        similarity=related.get("similarity", related.get("score")),
        retrieval_method=related.get("retrieval_method") or related.get("method"),
        origin=new.get("origin") or "discovery",
    )
    if built["rationale"] and wording_flags(built["rationale"], _names(new, related)):
        # V37: a rationale that says a trial uses or studies a named product is not kept.
        built["label"], built["rationale"] = UNESTABLISHED, None
    built["related_ref"] = str(built["related_ref"] or "")
    for side, item in (("new_quote", new), ("related_quote", related)):
        built[side]["source_ref"] = str(built[side]["source_ref"] or item.get("ref") or "")
    built["id"] = relationship_id(new.get("report_id"), new.get("source_ref"), built["related_ref"])
    return Relationship.model_validate(built)
