"""Quote cards from an accepted report (V70, V40).

A card is ONE verbatim quote stored on the report, with the record field it sits in. The only source is
the discovery's quotes, each pinned to its `version_id`. Nothing is retrieved and nothing is taken from
outside the report. A related record's quote is never a card: its field is not this record's.

Fail closed, in this order (a card that fails any step is not a card):

1. The quote is whitespace-normalised: every run of whitespace, a blank line included, becomes one space.
   The normalised text is what is shown, composed, hashed into the quote ID and checked against the
   pinned version. A quote with a blank line therefore cannot split an answer on the page.
2. The quote carries its FIELD (status, dates, conditions, ...). The field is read from the pinned version's own
   labelled section that holds the quote (and from the quote's own leading label, which must agree). A quote with
   no known label, or one that spans two fields, has the field "other", and no intent uses "other".
3. A quote with a claim-like construction (a comparison, a performance or result verb, a percentage, a figure next
   to a performance noun) is excluded from every intent, whatever its field (`claim_like`).
"""

from __future__ import annotations

import hashlib
import re
from bisect import bisect_right
from dataclasses import dataclass
from typing import Any

__all__ = [
    "Card",
    "FIELD_OTHER",
    "MAX_CARDS",
    "NARRATIVE_FIELDS",
    "claim_like",
    "comparison_like",
    "discovery_versions",
    "field_for_label",
    "is_accepted",
    "load_cards",
    "looks_like_instruction",
    "mention_names",
    "narrative_unsafe",
    "normalise_text",
]

MAX_CARDS = 60
MAX_QUOTE_CHARS = 600
FIELD_OTHER = "other"
NARRATIVE_FIELDS = frozenset({"summary", "description"})

# A quote that talks to a model never answers a question, even though it may be verbatim.
_INSTRUCTION = re.compile(
    r"ignore\s+(?:all\s+|any\s+|the\s+|your\s+|previous\s+|prior\s+|above\s+|earlier\s+)+(?:instructions?|prompts?|rules?|messages?)"
    r"|disregard\s+(?:all\s+|any\s+|the\s+|your\s+|previous\s+|prior\s+|above\s+)+(?:instructions?|prompts?|rules?)"
    r"|system\s+prompt|developer\s+message|you\s+are\s+now\b|act\s+as\s+(?:a|an|the)\b|new\s+instructions?"
    r"|do\s+not\s+follow|pretend\s+(?:to\s+be|you)|reveal\s+(?:your|the)\s+(?:prompt|instructions?)|</?\s*(?:system|assistant|user)\s*>"
    r"|\bselect\s+(?:quote\s+)?(?:id\s+)?qt_|as\s+an\s+ai\b|jailbreak",
    re.IGNORECASE,
)

# What the page and the composer use to tell one cited sentence from another: a quote may not look like a
# citation marker, and it never holds a line break (normalisation removes them).
_MARKER_LOOKALIKE = re.compile(r"\[\s*\d+\s*\]")


@dataclass(frozen=True)
class Card:
    quote_id: str
    text: str  # whitespace-normalised
    source_ref: str
    version_id: str
    field: str  # status, dates, conditions, phase, design, interventions, sponsor, location, enrollment, results, summary, description, other


def normalise_text(text: str) -> str:
    """Collapse every run of whitespace (blank lines included) to one space."""
    return re.sub(r"\s+", " ", text).strip()


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


# --- claim-like constructions -------------------------------------------------------------------------------

_COMPARATIVE = re.compile(
    r"\b(?:better|worse|superior|inferior|best|worst|more|less|most|least|higher|lower|greater|fewer|larger|smaller|faster|slower|"
    r"stronger|weaker|improv\w*|outperform\w*|exceed\w*|surpass\w*|beat|beats|beating|versus|vs|than|compar\w*|relative|"
    r"advantage\w*|benefit\w*|non-?inferior\w*|equivalen\w*|similar\w*|differ\w*|preferab\w*|prefer\w*)\b",
    re.IGNORECASE,
)
_PERFORMANCE_VERB = re.compile(
    r"\b(?:show(?:s|ed|n|ing)?|demonstrat\w*|achiev\w*|detect\w*|identif\w*|predict\w*|yield\w*|prove[sdn]?|proving|confirm\w*|"
    r"valid\w*|perform\w*|correlat\w*|associat\w*|agree\w*|concord\w*|accura\w*|sensitiv\w*|specific\w*|reliab\w*|effective\w*|"
    r"efficac\w*|effects?|respon(?:se|ses|d|ds|ded|ding|der|ders)|surviv\w*|reduc\w*|increas\w*|decreas\w*|elevat\w*|found|find(?:s|ing|ings)?|observed|observes?|observing|"
    r"conclud\w*|suggest\w*|indicat(?:e|es|ed|ing)|significan\w*|outcomes?|success\w*|fail\w*|catch\w*|captur\w*|miss\w*|"
    r"results?\s+(?:in|show\w*|were|was|indicat\w*|suggest\w*|demonstrat\w*)|"
    r"superior|accurate|call(?:s|ed)|rate[sd]?|false|true\s+(?:positive|negative))\b",
    re.IGNORECASE,
)
_PERCENT = re.compile(r"%|\bper\s*cent\b|\bpercent\w*\b", re.IGNORECASE)
_PERFORMANCE_NOUN = re.compile(
    r"^(?:sensitivity|specificity|accuracy|ppv|npv|auc|rate|rates|concordance|agreement|survival|response|responses|detection|"
    r"recall|precision|prevalence|incidence|performance|efficacy|yield|ratio|odds|hazard|score|scores)$",
    re.IGNORECASE,
)
_WORD = re.compile(r"[A-Za-z0-9]+")


def _digit_near_performance_noun(text: str, window: int = 4) -> bool:
    tokens = _WORD.findall(text)
    for index, token in enumerate(tokens):
        if not _PERFORMANCE_NOUN.match(token):
            continue
        low, high = max(0, index - window), min(len(tokens), index + window + 1)
        if any(any(ch.isdigit() for ch in other) for other in tokens[low:high]):
            return True
    return False


def comparison_like(text: str) -> bool:
    """A comparison or a percentage only. Used on a question, where the performance verbs of `claim_like` would
    also catch ordinary words ("responsible", "specific")."""
    return bool(_COMPARATIVE.search(text) or _PERCENT.search(text))


def claim_like(text: str) -> bool:
    """True when the text has a claim-like construction. It fails closed: it is a net, not a definition, and a
    quote it catches is only left out of the answer. The record's own plain fields never match."""
    return bool(
        _COMPARATIVE.search(text)
        or _PERFORMANCE_VERB.search(text)
        or _PERCENT.search(text)
        or _digit_near_performance_noun(text)
    )


# Narrative (brief summary, description) is free prose, so it gets a second, stricter net. A narrative quote is left
# out when it says what was done with, or to, something: a record name next to a verb of use, a plan, or an animal
# or cell-line study. These words are a net, not a definition: a gap leaves a quote out of the answer, never into it.
_USAGE_VERB = re.compile(
    r"\b(?:use[sd]?|using|usage|stud(?:y|ies|ied|ying)|investigat\w*|test(?:s|ed|ing)?|evaluat\w*|measur\w*|assess\w*|analy[sz]\w*|"
    r"profil\w*|call(?:s|ed|ing)?|captur\w*|catch\w*|caught|work(?:s|ed|ing)?|agree\w*|help(?:s|ed|ing)?|find\w*|reveal\w*|"
    r"ran|run|runs|running|appl(?:y|ies|ied|ying)|employ\w*|utili[sz]\w*|monitor\w*|undergo\w*|underwent|receiv\w*|sequenc\w*|"
    r"assay(?:s|ed)|flag\w*|inform\w*|genotyp\w*|screen\w*|administer\w*|deliver\w*|collect\w*|includ\w*|involv\w*|enrol\w*|"
    r"recruit\w*|designed|aims?|seeks?|intends?|verif\w*|check\w*|determin\w*|quantif\w*|track\w*|diagnos\w*)\b",
    re.IGNORECASE,
)
_FUTURE_OR_PRECLINICAL = re.compile(
    r"\b(?:will|would|planned|plans?|planning|anticipat\w*|expected|mice|mouse|murine|rats?|animals?|xenografts?|cell[\s-]lines?|"
    r"in\s+vitro|in\s+vivo|preclinical|organoids?|zebrafish|pdx)\b",
    re.IGNORECASE,
)


def narrative_unsafe(text: str, names: list[str]) -> bool:
    """True when a narrative quote must not be used: it has a plan or a preclinical study in it, or it holds one of the
    record's names together with a verb of use or a figure (V37: a name in a record is not proof of use)."""
    if _FUTURE_OR_PRECLINICAL.search(text):
        return True
    lowered = text.lower()
    if any(name.strip() and name.lower() in lowered for name in names):
        stripped = text
        for name in names:
            if name.strip():
                stripped = re.sub(re.escape(name), " ", stripped, flags=re.IGNORECASE)
        return bool(_USAGE_VERB.search(stripped) or re.search(r"\d", stripped))
    return False


# --- fields --------------------------------------------------------------------------------------------------

# A record label and the field it belongs to. Order matters: the first match wins.
_LABEL_FIELDS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern), field)
    for pattern, field in (
        (r"^brief summary$|^summary$", "summary"),
        (r"^detailed description$|^description$", "description"),
        (r"^(?:overall status|status|recruitment status|why stopped)$", "status"),
        (
            r"^(?:start date|study start|completion date|primary completion date|study completion|first posted|study first posted|"
            r"results first posted|last update posted|first submitted|last update submitted|dates?)$",
            "dates",
        ),
        (r"^conditions?$", "conditions"),
        (r"^phases?$", "phase"),
        (
            r"^(?:design|study design|study type|allocation|masking|intervention model|observational model|time perspective|"
            r"primary purpose|sampling method|study population|population|sample size|sample|specimen)$",
            "design",
        ),
        (r"^(?:interventions?|intervention \(.*\)|other names|arm group|arms?)$", "interventions"),
        (r"^(?:lead sponsor|sponsor|sponsors|collaborators?|responsible party|organi[sz]ation)$", "sponsor"),
        (r"^(?:locations?|facility|facilities|countries|country|sites?)$", "location"),
        (r"^(?:estimated enrollment|enrollment|enrolment|enrollment type)$", "enrollment"),
        (r"^(?:results posted|has results|results)$", "results"),
    )
)
_LABEL = re.compile(r"^\s*([A-Za-z][A-Za-z ()/'-]{1,48}?)\s*:(?:\s|$)")


def _label_of(paragraph: str) -> str | None:
    match = _LABEL.match(paragraph)
    return re.sub(r"\s+", " ", match.group(1)).strip().lower() if match else None


def field_for_label(label: str | None) -> str:
    if not label:
        return FIELD_OTHER
    for pattern, field in _LABEL_FIELDS:
        if pattern.match(label):
            return field
    return FIELD_OTHER


class _Sections:
    """The pinned version's text as labelled sections, each with the field of the label that opened it.
    A paragraph with no label of its own belongs to the section above it."""

    def __init__(self, raw_text: str) -> None:
        parts: list[str] = []
        self.starts: list[int] = []
        self.fields: list[str] = []
        current = FIELD_OTHER
        offset = 0
        for paragraph in re.split(r"\n\s*\n", raw_text):
            text = normalise_text(paragraph)
            if not text:
                continue
            label = _label_of(text)
            if label is not None:
                current = field_for_label(label)
            self.starts.append(offset)
            self.fields.append(current)
            parts.append(text)
            offset += len(text) + 1
        self.text = " ".join(parts).lower()

    def field_at(self, position: int) -> str:
        return self.fields[bisect_right(self.starts, position) - 1]

    def field_of(self, quote: str) -> str | None:
        """The field of the section holding the quote, or None when it is not there. A quote that starts in one
        field and ends in another is "other"."""
        needle = quote.lower()
        position = self.text.find(needle)
        if position < 0:
            return None
        first, last = self.field_at(position), self.field_at(position + len(needle) - 1)
        return first if first == last else FIELD_OTHER


def _own_label_field(text: str) -> str | None:
    """The field named by the quote's own leading label, or None when it has no label."""
    label = _label_of(text)
    return None if label is None else field_for_label(label)


def resolve_field(text: str, sections: _Sections | None) -> str:
    own = _own_label_field(text)
    if sections is None:
        return own or FIELD_OTHER
    found = sections.field_of(text)
    if found is None:
        return FIELD_OTHER
    if own is not None and own != found:
        return FIELD_OTHER
    return found


# --- loading -------------------------------------------------------------------------------------------------


def _quote_version(report: dict[str, Any], quote: dict[str, Any]) -> Any:
    return quote.get("version_id") or report.get("version_id")


def discovery_versions(report: dict[str, Any]) -> set[str]:
    """The version IDs the discovery quotes are pinned to, so the caller can read their raw text once."""
    versions: set[str] = set()
    for quote in (report.get("discovery") or {}).get("quotes") or []:
        if isinstance(quote, dict):
            version = _quote_version(report, quote)
            if isinstance(version, str) and version:
                versions.add(version)
    return versions


def _usable(text: Any, version_id: Any, source_ref: Any, found: Any) -> bool:
    return (
        found is True
        and isinstance(text, str)
        and bool(text.strip())
        and isinstance(version_id, str)
        and bool(version_id)
        and isinstance(source_ref, str)
        and bool(source_ref)
        and len(normalise_text(text)) <= MAX_QUOTE_CHARS
        and not looks_like_instruction(text)
        and _MARKER_LOOKALIKE.search(text) is None
    )


def load_cards(report: dict[str, Any], raw_texts: dict[str, str | None] | None = None) -> list[Card]:
    """One card per usable discovery quote, in report order, without duplicates.

    `raw_texts` maps a version_id to the raw text of that pinned version. With it, a quote's field is the
    labelled section of that version that holds it. Without it (or with None for a version) only the quote's own
    leading label counts, and a quote with none is "other"."""
    cards: list[Card] = []
    seen: set[tuple[str, str, str]] = set()
    sections: dict[str, _Sections] = {}

    def sections_for(version_id: str) -> _Sections | None:
        raw = (raw_texts or {}).get(version_id)
        if not isinstance(raw, str):
            return None
        if version_id not in sections:
            sections[version_id] = _Sections(raw)
        return sections[version_id]

    source_ref = report.get("source_ref")
    for quote in (report.get("discovery") or {}).get("quotes") or []:
        if not isinstance(quote, dict):
            continue
        text, version_id = quote.get("text"), _quote_version(report, quote)
        if not _usable(text, version_id, source_ref, quote.get("quote_found")):
            continue
        shown = normalise_text(text)
        key = (source_ref, version_id, shown)
        if key in seen:
            continue
        seen.add(key)
        field = resolve_field(shown, sections_for(version_id))
        cards.append(Card(quote_id_for(source_ref, version_id, field, shown), shown, source_ref, version_id, field))
    return cards[:MAX_CARDS]
