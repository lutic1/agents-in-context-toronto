"""Report drafting: the pure helpers (AD-27, AD-28, Story 10.4).

memory_effects() compares the draft written without memories (draft 1) to the
draft written with them (draft 2, V21). wording_flags() finds "uses",
"studies" or "showed" wording about a named product (V37).
"""
from __future__ import annotations

import difflib
import re
from typing import Any

from dxp.api.models import Memory, Relationship

NO_CHANGE_TEXT = "retrieved, no change"

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|(?<=[.!?][\"')\]])\s+")
_WORD = re.compile(r"[a-z0-9]+")

# Verb forms only: the nouns "study" and "use" are left out on purpose.
WORDING_VERBS = {
    "uses": ("uses", "used", "using", "utilises", "utilised", "utilising",
             "utilizes", "utilized", "utilizing"),
    "studies": ("studies", "studied", "studying"),
    "showed": ("shows", "showed", "shown", "showing", "demonstrates",
               "demonstrated", "demonstrating"),
}
_VERB_FAMILY = {form: family for family, forms in WORDING_VERBS.items() for form in forms}
_VERB_RE = re.compile(r"\b(%s)\b" % "|".join(sorted(_VERB_FAMILY, key=len, reverse=True)),
                      re.IGNORECASE)


def split_sentences(text):
    if not isinstance(text, str):
        return []
    return [part.strip() for part in _SENTENCE_END.split(text) if part.strip()]


# ---------------------------------------------------------------- memory effect

def draft_sentences(draft):
    """Every sentence of a draft, in reading order."""
    draft = draft or {}
    discovery = draft.get("discovery") or {}
    sentences = []
    for text in (draft.get("headline"), discovery.get("summary"), draft.get("summary")):
        sentences += split_sentences(text)
    for claim in draft.get("claims") or []:
        sentences += split_sentences(claim.get("text") if isinstance(claim, dict) else claim)
    for text in draft.get("uncertainties") or []:
        sentences += split_sentences(text)
    sentences += split_sentences(draft.get("gap"))
    return sentences


def _claim_kinds(draft):
    kinds = {}
    for claim in (draft or {}).get("claims") or []:
        if isinstance(claim, dict) and claim.get("text"):
            kinds[claim["text"]] = claim.get("claim_kind")
    return kinds


def draft_changes(draft_without, draft_with):
    """What differs between the two drafts: [{ target, before, after }].

    target is "sentence" (changed, removed with after "", or added with
    before "") or "label" (a claim with the same text and another claim_kind).
    """
    before = draft_sentences(draft_without)
    after = draft_sentences(draft_with)
    changes = []
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old, new = before[i1:i2], after[j1:j2]
        for index in range(max(len(old), len(new))):
            changes.append({
                "target": "sentence",
                "before": old[index] if index < len(old) else "",
                "after": new[index] if index < len(new) else "",
            })
    kinds_before, kinds_after = _claim_kinds(draft_without), _claim_kinds(draft_with)
    for text, kind in kinds_before.items():
        if text in kinds_after and kinds_after[text] != kind:
            changes.append({"target": "label", "before": kind, "after": kinds_after[text]})
    return changes


def _words(text):
    return set(_WORD.findall(str(text or "").lower()))


def _memory_id(memory):
    return memory.get("memory_id") or memory.get("id")


def memory_effects(draft_without, draft_with, memories, attribution=None):
    """MemoryUse[] (AD-14): each retrieved memory with the change it made.

    A memory's effect is one real difference between the two drafts
    ({ target, before, after }) or None ("retrieved, no change"). Each
    difference goes to one memory: the one `attribution` names for it
    ({ memory_id: the changed text in draft 2 }), else the memory sharing the
    most words with the changed text, else the first (best ranked) memory.
    An attribution that names text the drafts do not differ on is ignored.
    """
    memories = list(memories or [])
    changes = draft_changes(draft_without, draft_with)
    attribution = attribution or {}
    effects = {}
    for change in changes:
        owner = None
        for memory in memories:
            named = attribution.get(_memory_id(memory))
            if named and named in (change["after"], change["before"]):
                owner = memory
                break
        if owner is None and memories:
            changed = _words(change["before"]) ^ _words(change["after"])
            if not changed:
                changed = _words(change["before"]) | _words(change["after"])
            scored = [(len(changed & _words(m.get("text"))), -i, m) for i, m in enumerate(memories)]
            owner = max(scored, key=lambda entry: entry[:2])[2]
        if owner is not None:
            effects.setdefault(_memory_id(owner), change)
    return [
        {
            "memory_id": _memory_id(memory),
            "version": memory.get("version"),
            "author": memory.get("author"),
            "source": memory.get("source"),
            "score": memory.get("score"),
            "effect": effects.get(_memory_id(memory)),
        }
        for memory in memories
    ]


def effect_text(memory_use):
    """One line for a screen or the audit."""
    effect = (memory_use or {}).get("effect")
    if not effect:
        return NO_CHANGE_TEXT
    return "changed %s: before %r, after %r" % (effect["target"], effect["before"], effect["after"])


# --------------------------------------------------------------- wording (V37)

def wording_flags(text, names):
    """Sentences that say "uses", "studies" or "showed" about a named product.

    Returns [{ name, verb, sentence }]; verb is the family: "uses", "studies"
    or "showed". A name alone, or a verb in a sentence that names no product,
    is not flagged.
    """
    names = [name for name in (names or []) if isinstance(name, str) and name.strip()]
    flags = []
    for sentence in split_sentences(text):
        lowered = sentence.lower()
        present = [name for name in names if name.strip().lower() in lowered]
        if not present:
            continue
        families = []
        for match in _VERB_RE.finditer(sentence):
            family = _VERB_FAMILY[match.group(1).lower()]
            if family not in families:
                families.append(family)
        for name in present:
            for family in families:
                flags.append({"name": name, "verb": family, "sentence": sentence})
    return flags


def mention_names(report):
    discovery = (report or {}).get("discovery") or {}
    names = []
    for mention in list(discovery.get("mentions") or []) + list((report or {}).get("name_mentions") or []):
        name = mention.get("name") if isinstance(mention, dict) else mention
        if isinstance(name, str) and name.strip() and name not in names:
            names.append(name)
    return names


def report_wording_flags(report, names=None):
    """wording_flags() over every sentence a report shows, with its field."""
    report = report or {}
    if names is None:
        names = mention_names(report)
    discovery = report.get("discovery") or {}
    texts = [("headline", report.get("headline")), ("status_line", report.get("status_line")),
             ("discovery.summary", discovery.get("summary")), ("gap", report.get("gap")),
             ("script", report.get("script"))]
    texts += [("uncertainties", text) for text in report.get("uncertainties") or []]
    texts += [("claims", c.get("text") if isinstance(c, dict) else c) for c in report.get("claims") or []]
    texts += [("related.rationale", r.get("rationale")) for r in report.get("related") or []
              if isinstance(r, dict)]
    flags = []
    for field, text in texts:
        for flag in wording_flags(text, names):
            flags.append(dict(flag, field=field))
    return flags


async def draft(item: dict[str, Any], findings: list[dict[str, Any]], related: list[Relationship], memories: list[Memory]) -> dict[str, Any]:
    """Draft the report fields (headline, discovery and mentions, uncertainties, gap, recommended task,
    updates); drafts with and without the memories so each memory's before-and-after effect is known."""
    raise NotImplementedError("reports.draft (A19+A20)")
