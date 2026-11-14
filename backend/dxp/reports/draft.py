"""Report drafting: the pure helpers (AD-27, AD-28, Story 10.4).

memory_effects() compares the draft written without memories (draft 1) to the
draft written with them (draft 2, V21). wording_flags() finds "uses",
"studies" or "showed" wording about a named product (V37).
"""
from __future__ import annotations

import difflib
import inspect
import json
import logging
import re
from typing import Any

from dxp.api.models import Memory, Relationship

log = logging.getLogger("dxp.reports")

NO_CHANGE_TEXT = "retrieved, no change"
MODEL = "claude-sonnet-5-5"  # the stronger model (AD-11)
MAX_RECORD_CHARS = 24000
MAX_QUOTE_CHARS = 300
CLAIM_KINDS = ("claim_planned", "claim_performed_or_results", "claim_preclinical", "claim_design")
NAMED_IN_RECORD = "named in the record"
EVIDENCE_COLLECTION = "evidence_collection"
NO_RESULTS = "No results posted."
AMBIGUOUS_INTERVENTION = (
    "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic "
    "{plain} intervention, and does not say which assay was used for which sample."
)
UNRESOLVED_NAME = "The record names '{name}'. Whether this is the FDA-approved {candidate} is not stated."
UNRESOLVED_NAME_NO_MATCH = "The record names '{name}'. It matches no FDA-listed companion diagnostic name exactly."
MENTION_NOT_PROOF = "a name in the record is a mention, not proof of use (V37)"

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
    owned: dict[Any, list[tuple[int, dict]]] = {}
    for change in changes:
        owner = None
        changed = _words(change["before"]) ^ _words(change["after"])
        if not changed:
            changed = _words(change["before"]) | _words(change["after"])
        for memory in memories:
            named = attribution.get(_memory_id(memory))
            if named and named in (change["after"], change["before"]):
                owner = memory
                break
        if owner is None and memories:
            scored = [(len(changed & _words(m.get("text"))), -i, m) for i, m in enumerate(memories)]
            owner = max(scored, key=lambda entry: entry[:2])[2]
        if owner is not None:
            named = attribution.get(_memory_id(owner))
            is_named = bool(named) and named in (change["after"], change["before"])
            weight = len(changed & _words(owner.get("text"))) + (10**6 if is_named else 0)
            owned.setdefault(_memory_id(owner), []).append((weight, change))
    # A memory shows one effect: the difference closest to its own words, the earliest on a tie.
    effects = {key: max(found, key=lambda entry: entry[0])[1] for key, found in owned.items()}
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


# ------------------------------------------------------------ reports.draft

def _plain(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value or {})


def _clean(value: Any) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def _sentence(text: str) -> str:
    return text if not text or text[-1] in ".!?" else text + "."


def status_text(overall_status: Any) -> str:
    """"NOT_YET_RECRUITING" -> "Not yet recruiting": the record's status, in words."""
    return _clean(str(overall_status or "").replace("_", " ").replace(",", " ")).capitalize()


def status_line(overall_status: Any, has_results: Any) -> str | None:
    parts = [status_text(overall_status)] if overall_status else []
    if has_results is False:
        parts.append("no results posted")
    elif has_results is True:
        parts.append("results posted")
    line = "; ".join(parts)
    return (line[0].upper() + line[1:]) if line else None


def intervention_text(interventions: Any) -> str | None:
    """The record's intervention names, verbatim."""
    names = [i.get("name") for i in interventions or [] if isinstance(i, dict) and isinstance(i.get("name"), str)]
    return "; ".join(names) or None


def _other_names(intervention: dict[str, Any]) -> list[str]:
    names = intervention.get("otherNames") or intervention.get("other_names") or []
    return [name for name in names if isinstance(name, str) and name.strip()]


def collect_mentions(source: dict[str, Any], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every name the record gives, verbatim, once, with the field it came from (V37)."""
    mentions: dict[str, dict[str, Any]] = {}

    def add(name: Any, field: Any, resolved: Any) -> None:
        if not isinstance(name, str) or not name.strip():
            return
        kept = mentions.setdefault(name, {"name": name, "resolved_diagnostic_id": None, "field": None})
        kept["field"] = kept["field"] or field
        kept["resolved_diagnostic_id"] = kept["resolved_diagnostic_id"] or resolved

    for holder in [*findings, source]:
        for mention in holder.get("mentions") or []:
            mention = _plain(mention)
            add(mention.get("name"), mention.get("field"), mention.get("resolved_diagnostic_id"))
    for intervention in source.get("interventions") or []:
        if isinstance(intervention, dict):
            for name in _other_names(intervention):
                add(name, "otherNames", None)
    return list(mentions.values())


def _is_other_name(mention: dict[str, Any]) -> bool:
    return "othername" in str(mention.get("field") or "").lower().replace("_", "")


def approved_candidates(name: str, seeded_names: list[str]) -> list[str]:
    """Seeded trade names that begin with the unresolved name, word for word. Never a match (V34)."""
    from dxp import identity

    key = identity.normalise_name(name)
    if not key:
        return []
    return [s for s in seeded_names if isinstance(s, str) and identity.normalise_name(s).startswith(key + " ")]


def build_uncertainties(source: dict[str, Any], mentions: list[dict[str, Any]], plain: str, seeded_names: list[str]) -> list[str]:
    """What the source does not settle: status and results, an ambiguous intervention field
    (V37) and every name that matched no seeded name exactly (V34)."""
    out: list[str] = []
    line = status_line(source.get("overall_status"), source.get("has_results"))
    if line and source.get("has_results") is not True:
        out.append(_sentence(line))
    if any(_is_other_name(m) for m in mentions):
        out.append(AMBIGUOUS_INTERVENTION.format(plain=plain))
    for mention in mentions:
        if mention.get("resolved_diagnostic_id"):
            continue
        candidates = approved_candidates(mention["name"], seeded_names)
        if candidates:
            out.append(UNRESOLVED_NAME.format(name=mention["name"], candidate=" or ".join(candidates)))
        else:
            out.append(UNRESOLVED_NAME_NO_MATCH.format(name=mention["name"]))
    return out


def build_updates(source: dict[str, Any], findings: list[dict[str, Any]], mentions: list[dict[str, Any]],
                  quotes: list[dict[str, Any]], label: str, quote_found) -> list[dict[str, Any]]:
    """The Proposed changes the ledger would file: `[{ finding_id, change }]`.

    One update adds the record to the scope's evidence collection (V35). A mention that
    resolves exactly to a Diagnostic is proposed as a link carrying `mention`, with
    `supported: false`: a name in the record is never proof of use (V37), so the gate
    decides. The checked values of a resolved Diagnostic's Finding follow.
    """
    from dxp import identity

    source_ref, version_id = source.get("source_ref"), source.get("version_id")
    record_finding = next((f for f in findings if not f.get("diagnostic_id")), None)
    record_finding_id = (record_finding or {}).get("id") or (record_finding or {}).get("_id") or identity.derive(
        "f_", version_id or "-", "-")
    updates: list[dict[str, Any]] = []

    def evidence(quote: Any) -> dict[str, Any]:
        return {"source_ref": source_ref, "version_id": version_id, "quote": quote}

    if source.get("scope_id"):
        passing = [v for v in (record_finding or {}).get("values") or []
                   if (v.get("check") or {}).get("quote_found") and (v.get("check") or {}).get("supported")]
        best = max(passing, key=lambda v: (v.get("check") or {}).get("confidence") or 0, default=None)
        if best:
            quote, check = best.get("quote"), dict(best.get("check") or {})
        else:
            quote = next((q["text"] for q in quotes if q.get("quote_found")), None)
            check = {"quote_found": quote is not None, "supported": False, "confidence": 0.0,
                     "detail": "no checked value of the record backs this update"}
        updates.append({"finding_id": record_finding_id, "change": {
            "field": EVIDENCE_COLLECTION, "value": source_ref, "label": label, "diagnostic_id": None,
            "scope_id": source["scope_id"], "evidence": evidence(quote), "check": check, "trigger": "discovery",
        }})
    by_dx = {f.get("diagnostic_id"): f for f in findings if f.get("diagnostic_id")}
    for mention in mentions:
        dx_id = mention.get("resolved_diagnostic_id")
        if not dx_id:
            continue
        finding = by_dx.get(dx_id) or {}
        finding_id = finding.get("id") or finding.get("_id") or record_finding_id
        updates.append({"finding_id": finding_id, "change": {
            "field": "trials", "value": source.get("nct_id") or source_ref, "label": NAMED_IN_RECORD,
            "diagnostic_id": dx_id, "diagnostic_name": mention["name"],
            "mention": {"name": mention["name"], "field": mention.get("field")},
            "evidence": evidence(mention["name"]),
            "check": {"quote_found": quote_found(mention["name"]), "supported": False, "confidence": 0.0,
                      "detail": MENTION_NOT_PROOF},
            "trigger": "discovery",
        }})
        for value in finding.get("values") or []:
            check = value.get("check") or {}
            if value.get("value") is None or not (check.get("quote_found") and check.get("supported")):
                continue
            updates.append({"finding_id": finding_id, "change": {
                "field": value.get("field"), "value": value.get("value"), "label": value.get("label"),
                "diagnostic_id": dx_id, "diagnostic_name": mention["name"],
                "evidence": evidence(value.get("quote")), "check": dict(check), "trigger": "discovery",
            }})
    return updates


def compose(number: int, output: Any, base: dict[str, Any], quote_found) -> dict[str, Any]:
    """One draft from the model's answer. Whatever the answer lacks or gets wrong about a
    named product (V37) is replaced from the record's own fields; nothing else is changed,
    so an unsupported claim still reaches the gate (V21)."""
    output = output if isinstance(output, dict) else {}
    names = base["names"]

    def usable(text: Any, limit: int = 600) -> str:
        text = _clean(text)
        return text if text and len(text) <= limit and not wording_flags(text, names) else ""

    headline = usable(output.get("headline")) or base["headline"]
    if base["has_results"] is False and "no results posted" not in headline.lower():
        headline = _sentence(headline) + " " + NO_RESULTS
    kept = [s for s in split_sentences(_clean(output.get("summary"))) if not wording_flags(s, names)]
    summary = " ".join(kept) or base["summary"]
    claims, quotes = [], []
    for claim in output.get("claims") or []:
        claim = claim if isinstance(claim, dict) else {}
        text = usable(claim.get("text"))
        if not text:
            continue
        quote = _clean(claim.get("quote")) if isinstance(claim.get("quote"), str) else ""
        quote = claim["quote"] if quote and len(claim["quote"]) <= MAX_QUOTE_CHARS else ""
        found = bool(quote) and quote_found(quote)
        kind = claim.get("claim_kind") if claim.get("claim_kind") in CLAIM_KINDS else "claim_design"
        claims.append({"text": text, "claim_kind": kind, "quote": quote, "quote_found": found})
        if quote and quote not in [q["text"] for q in quotes]:
            quotes.append({"text": quote, "quote_found": found, "version_id": base["version_id"]})
    gap = _clean(output.get("gap"))
    gap = gap[:gap.index("?") + 1] if "?" in gap else ""
    if not gap or wording_flags(gap, names):
        gap = base["gap"]
    task = output.get("task") if isinstance(output.get("task"), dict) else {}
    testing = [t for t in (_clean(x) for x in task.get("testing") or []) if t and not _has_name(t, names)][:5]
    plain = _clean(output.get("intervention_plain"))
    if not plain or len(plain) > 80 or _has_name(plain, names):
        plain = base["intervention_plain"]
    label = _clean(output.get("collection_label"))
    if not label or len(label) > 120 or _has_name(label, names):
        label = "trial record"
    return {
        "draft": number, "headline": headline, "summary": summary, "claims": claims, "quotes": quotes,
        "gap": gap, "intervention_plain": plain, "collection_label": label,
        "task": {"condition": _clean(task.get("condition")) or base["condition"],
                 "stage": _clean(task.get("stage")) or "early", "testing": testing,
                 "has_results": True, "max": 5},
    }


def _has_name(text: str, names: list[str]) -> bool:
    lowered = text.lower()
    return any(name.lower() in lowered for name in names)


def gate_claims(one_draft: dict[str, Any]) -> list[dict[str, Any]]:
    """Every sentence the draft states, for check 4: the tagged claims, then the headline
    and summary sentences not already among them."""
    claims = [{k: c[k] for k in ("claim_kind", "text", "quote") if c.get(k)} for c in one_draft.get("claims") or []]
    seen = {c["text"] for c in claims}
    for sentence in split_sentences(one_draft.get("headline")) + split_sentences(one_draft.get("summary")):
        if sentence not in seen:
            seen.add(sentence)
            claims.append({"claim_kind": "claim_design", "text": sentence})
    return claims


async def _load_source(item: Any) -> dict[str, Any]:
    from dxp import store
    from dxp.reports.relate import load_item

    source = await load_item(item)
    missing = [k for k in ("overall_status", "has_results", "interventions", "evidence_text") if source.get(k) is None]
    if missing and source.get("version_id"):
        try:
            version = await store.db()["source_versions"].find_one({"_id": source["version_id"]}) or {}
            for key in missing:
                source[key] = version.get(key)
        except Exception as exc:
            log.warning("reports.draft: could not load the source version: %s", type(exc).__name__)
    if not source.get("scope_id") and source.get("scope_ids"):
        source["scope_id"] = source["scope_ids"][0]
    return source


async def _seeded_names(source: dict[str, Any]) -> list[str]:
    if source.get("seeded_names"):
        return list(source["seeded_names"])
    try:
        from dxp import store

        docs = await store.db()["diagnostics"].find({}, {"name": 1}).to_list(length=None)
        return sorted({d["name"] for d in docs if isinstance(d.get("name"), str)})
    except Exception as exc:
        log.warning("reports.draft: could not read the seeded names: %s", type(exc).__name__)
        return []


async def _resolve(mentions: list[dict[str, Any]]) -> None:
    from dxp import identity

    for mention in mentions:
        if mention.get("resolved_diagnostic_id"):
            continue
        try:
            found = identity.resolve_exact(mention["name"])
            mention["resolved_diagnostic_id"] = await found if inspect.isawaitable(found) else found
        except Exception as exc:
            log.warning("reports.draft: could not resolve a name: %s", type(exc).__name__)


async def _ask(source: dict[str, Any], names: list[str], related: list[dict[str, Any]], memories: list[dict[str, Any]]) -> Any:
    from dxp import llm
    from dxp.llm.prompts import report as prompt

    guidance = ""
    if memories:
        guidance = prompt.GUIDANCE.format(memories="\n".join(f"{i}. {m.get('text')}" for i, m in enumerate(memories, 1)))
    lines = [f"- {r.get('label')}: {r.get('related_title') or r.get('related_ref')}" for r in related] or ["- none"]
    try:
        return await llm.call_structured(MODEL, prompt.SCHEMA, [
            {"role": "system", "content": prompt.SYSTEM},
            {"role": "user", "content": prompt.USER.format(
                source_ref=source.get("source_ref"),
                record=(source.get("raw_text") or source.get("evidence_text") or "")[:MAX_RECORD_CHARS],
                overall_status=source.get("overall_status"),
                has_results=source.get("has_results"),
                interventions=json.dumps(source.get("interventions") or [], ensure_ascii=False),
                names=json.dumps(names, ensure_ascii=False),
                related="\n".join(lines),
                guidance=guidance,
            )},
        ])
    except Exception as exc:
        log.warning("reports.draft: model call failed: %s", type(exc).__name__)
        return None


async def draft(item: dict[str, Any], findings: list[dict[str, Any]], related: list[Relationship], memories: list[Memory]) -> dict[str, Any]:
    """Draft the report fields (headline, discovery and mentions, uncertainties, gap, recommended task,
    updates); drafts with and without the memories so each memory's before-and-after effect is known."""
    from dxp import evidence

    source = await _load_source(item)
    findings = [_plain(f) for f in findings or []]
    related_dicts = [_plain(r) for r in related or []]
    memory_dicts = [_plain(m) for m in memories or []]
    for finding in findings:
        if source.get("overall_status") is None:
            source["overall_status"] = finding.get("trial_status")
        if source.get("has_results") is None:
            source["has_results"] = finding.get("has_results")
    raw_text = source.get("raw_text")
    checker = getattr(evidence, "quote_in_source", None)

    def quote_found(quote: Any) -> bool:
        try:
            return checker is not None and isinstance(raw_text, str) and checker(quote, raw_text) is True
        except Exception:
            return False

    mentions = collect_mentions(source, findings)
    await _resolve(mentions)
    names = [m["name"] for m in mentions]
    seeded = await _seeded_names(source)
    verbatim = intervention_text(source.get("interventions"))
    title = _clean(source.get("title") or source.get("brief_title")).rstrip(".")
    conditions = source.get("conditions") or []
    condition = _clean(conditions[0]) if conditions and isinstance(conditions[0], str) else "lung cancer"
    headline = f"New trial signal: {title}." if title else f"New trial signal in {condition}."
    if wording_flags(headline, names):
        headline = f"New trial signal in {condition}."
    record_summary = next((_clean(f.get("summary")) for f in findings if not f.get("diagnostic_id") and f.get("summary")), "")
    base = {
        "names": names, "version_id": source.get("version_id"), "has_results": source.get("has_results"),
        "headline": headline, "condition": condition,
        "summary": record_summary if record_summary and not wording_flags(record_summary, names) else headline,
        "gap": f"Have other {condition} studies with a similar design posted results?",
        "intervention_plain": f'"{verbatim}"' if verbatim else "unnamed",
    }

    drafts = [compose(1, await _ask(source, names, related_dicts, []), base, quote_found)]
    if memory_dicts:
        answer = await _ask(source, names, related_dicts, memory_dicts)
        if isinstance(answer, dict):
            drafts.append(compose(2, answer, base, quote_found))
        else:  # the second call failed: draft 2 is draft 1, so every memory shows "retrieved, no change"
            drafts.append({**drafts[0], "draft": 2})
    for one in drafts:
        one["uncertainties"] = build_uncertainties(source, mentions, one["intervention_plain"], seeded)
    final = drafts[-1]
    effects = memory_effects(drafts[0], final, memory_dicts) if memory_dicts else []
    for use, memory in zip(effects, memory_dicts):
        use["source"] = use["source"] or {"decision_id": None, "report_id": None}
        use["version"] = use["version"] if use["version"] is not None else 1
        use["author"] = use["author"] or ""

    retrieval = source.get("retrieval")
    return {
        "draft": final["draft"],
        "run_id": source.get("run_id"),
        "scope_id": source.get("scope_id"),
        "team_id": source.get("team_id"),
        "source_ref": source.get("source_ref"),
        "version_id": source.get("version_id"),
        "nct_id": source.get("nct_id"),
        "headline": final["headline"],
        "status_line": status_line(source.get("overall_status"), source.get("has_results")),
        "discovery": {
            "summary": final["summary"],
            "quotes": final["quotes"],
            "trial_status": source.get("overall_status"),
            "has_results": source.get("has_results"),
            "intervention_text": verbatim,
            "mentions": mentions,
        },
        "claims": final["claims"],
        "name_mentions": [{**m, "description": NAMED_IN_RECORD} for m in mentions],
        "related": related_dicts,
        "uncertainties": final["uncertainties"],
        "gap": final["gap"],
        "retrieval": _plain(retrieval) if retrieval else None,
        "memories_used": effects,
        "recommended_task": {"kind": "search_related", "params": final["task"]},
        "updates": build_updates(source, findings, mentions, final["quotes"], final["collection_label"], quote_found),
        "source_fields": {"overall_status": source.get("overall_status"), "has_results": source.get("has_results")},
        "drafts": drafts,
    }
