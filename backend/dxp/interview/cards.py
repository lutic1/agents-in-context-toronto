"""Quote cards from an accepted report (V70, V40).

A card is ONE verbatim quote stored on the report, with the record field it sits in. The only source is
the discovery's quotes, each pinned to its `version_id`. Nothing is retrieved and nothing is taken from
outside the report. A related record's quote is never a card: its field is not this record's.

Only the discovery's quotes pinned to the REPORT'S OWN `version_id` are cards (`pinned_version`): a quote pinned to any
other version would be cited under this report's `source_ref` while coming from somewhere else. Related-evidence quotes
(a related record's quote, or the new quote of a relationship) are never used. This is a deviation from V70, which allows them;
it is deliberate, because their field cannot be shown to be this record's.

A quote with a format (Cf) character (zero-width, right-to-left override, tag characters), one that talks to a model or a
reader, or one that recommends or advises (`advises`) is not a card either, in any field.

Fail closed, in this order (a card that fails any step is not a card):

1. The quote is whitespace-normalised: every run of whitespace, a blank line included, becomes one space.
   The normalised text is what is shown, composed, hashed into the quote ID and checked against the
   pinned version. A quote with a blank line therefore cannot split an answer on the page.
2. The quote carries its FIELD (status, dates, conditions, ...). The field is read from the pinned version's own
   labelled section that holds the quote (and from the quote's own leading label, which must agree). A quote with
   no known label, or one that spans two fields, has the field "other", and no intent uses "other".
3. A quote with a claim-like construction (a comparison, a performance or result verb, a percentage, a figure next
   to a performance noun) is excluded from every intent, whatever its field (`claim_like`). That net is the
   SECOND line: the first is a strict shape per field (`shape_ok`), so a quote is offered only if it is in a form
   the record's own fields have:
   - structured fields (status, dates, conditions, phase, design, sponsor, location, enrollment, results): one or more
     `Label: value` segments of that field, the value being an enumerated value, a date, a number or a list of names;
   - interventions: the value is a list made only of the names the record gives (`mention_names`);
   - narrative (brief summary, description): every word is in a small closed vocabulary of design words.
   Free text after a label ("Intervention: X outclasses Y") has no such shape and is excluded. Fail closed.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from bisect import bisect_right
from dataclasses import dataclass
from typing import Any

from dxp.interview.textfold import skeleton

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
    "advises",
    "has_format_character",
    "narrative_unsafe",
    "normalise_text",
    "pinned_version",
    "says_what_was_done",
    "shape_ok",
    "STRUCTURED_FIELDS",
]

MAX_CARDS = 60
MAX_QUOTE_CHARS = 600
FIELD_OTHER = "other"
NARRATIVE_FIELDS = frozenset({"summary", "description"})
STRUCTURED_FIELDS = frozenset({"status", "dates", "conditions", "phase", "design", "interventions", "sponsor", "location", "enrollment", "results"})

# A quote that talks to a model never answers a question, even though it may be verbatim. It is matched on the
# skeleton of the quote (no format characters, accents folded, look-alike letters mapped, lower case), so
# "Ign<ZWSP>ore" and a Cyrillic "о" in "ignоre" are read as the English word. The net is wide on purpose: a quote it
# catches is only left out.
_INSTRUCTION = re.compile(
    r"\bignore\b|\bdisregard\b|\bforget\s+(?:all|any|everything|the|your|previous|prior|above|earlier)\b|\boverrid(?:e|es|ing)\b|"
    r"\b(?:tell|inform|notify|instruct|ask|advise|warn|command|order|direct)\s+(?:the\s+|each\s+|every\s+|this\s+|that\s+)?"
    r"(?:user|users|reader|readers|assistant|model|ai|llm|agent|bot|human|client|customer)s?\b|"
    r"\b(?:assistant|chatbot|language\s+model|llm|large\s+language|openai|anthropic|claude|chatgpt|gpt)\b|"
    r"\b(?:system|developer|assistant|user|human|ai|bot)\s*:|</?\s*[a-z_ ]{0,24}\s*>|\[\s*/?\s*(?:system|inst|assistant|user|quotes?)\s*\]|"
    r"\brank\s+(?:this|these|it|the|that|first|higher|highest|top)\b|\b(?:select|choose|pick|return|output|answer|respond|reply)\s+(?:only\s+|just\s+)?(?:this|these|the\s+quote|with|qt_|quote)|"
    r"\bimportant\s+(?:note|notice|message|instruction)s?\b|\bnote\s+to\b|\bnew\s+instructions?\b|\binstructions?\b|"
    r"system\s+prompt|developer\s+message|you\s+are\s+now\b|\byou\s+(?:must|should|will|shall|need\s+to|have\s+to)\b|\bact\s+as\b|"
    r"\bdo\s+not\s+follow\b|pretend\s+(?:to\s+be|you)|reveal\s+(?:your|the)\s+(?:prompt|instructions?)|"
    r"\bqt_[0-9a-f]{4,}|as\s+an\s+ai\b|jailbreak|\bprompt\s+injection\b|\bbegin\s+(?:system|instructions?)\b",
    re.IGNORECASE,
)
# The recommendation vocabulary (V37, V70): a quote that advises, recommends or says what must or should be done is
# never a card, in any field.
_ADVICE = re.compile(
    r"\b(?:recommend\w*|advis\w*|advice|suggest\w*|should|shouldn't|ought|must|urge\w*|encourag\w*|prescrib\w*|prescription|"
    r"consider\w*|best\s+(?:option|choice|practice|test|assay)|first[\s-]?line|preferred|indicated|appropriate|"
    r"necessary|essential|critical|vital|crucial|proven|approved|cleared|endorse\w*|guideline\w*)\b",
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


def has_format_character(text: str) -> bool:
    """True when the text has a format (Cf) character: a zero-width character, a bidirectional control (right-to-left
    override), a tag character. None of them belongs in a quote about a trial, and they hide words from a check."""
    return any(unicodedata.category(ch) == "Cf" for ch in text)


def looks_like_instruction(text: str) -> bool:
    """True when the quote talks to a model or a reader. The format characters are stripped (and a quote that has any
    is refused by `has_format_character`) before the words are matched."""
    return bool(_INSTRUCTION.search(skeleton(text)) or _INSTRUCTION.search(text))


def advises(text: str) -> bool:
    """True when the quote recommends or advises (the recommendation vocabulary)."""
    return bool(_ADVICE.search(skeleton(text)))


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


# A second, wider net (red team 2): figures as fractions or folds, number words, regulatory and sales wording, verbs
# of effect. It only ever leaves a quote OUT. The first line of defence is the shape of the quote (`shape_ok`).
_CLAIM_EXTRA = re.compile(
    r"outclass\w*|outshin\w*|\bmatch(?:es|ed|ing)?\b|\bon\s+par\b|\bpar\s+with\b|gold\s+standard|standard\s+of\s+care|\bhalv\w*|\bhalf\b|"
    r"\bdoubl\w*|\btripl\w*|\d+\s*-?\s*fold|\bfold\b|\bcuts?\b|\b\d+\s*/\s*\d+\b|"
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"half|third|quarter|dozen)\b(?:\s+\w+)?\s+(?:of|in|out\s+of)\b|"
    r"\bapprov\w*|\bclear(?:ed|ance)\b|\bfda\b|\bsafe\w*|\bsav(?:e|es|ed|ing)\b|\bcur(?:e|es|ed|ing)\b|\btreat(?:s|ed|ing)?\b|\bguid(?:e|es|ed|ing)\b|"
    r"\benabl\w*|\bwork(?:s|ed|ing)?\b|\bexcellent\b|\brobust\b|\bbreakthrough\b|\bahead\b|\bleads\b|\bleading\b|\bwins?\b|\bpass(?:es|ed)?\b|"
    r"\brarely\b|\balways\b|\bnever\b|\bnearly\b|\balmost\b|\btrusted\b|\brecommend\w*|\brival\w*|\buseful\b|\bwell\b|\bgood\b|\bgreat\b|"
    r"\bmore\b|\bturnaround\b|\bfaster\b|\bquick\w*|\bcheap\w*|\bcost\w*|\bhelp\w*|\bimpro\w*|\bboost\w*|\bcut\b|\bgain\w*",
    re.IGNORECASE,
)


def comparison_like(text: str) -> bool:
    """A comparison or a percentage only. Used on a question, where the performance verbs of `claim_like` would
    also catch ordinary words ("responsible", "specific")."""
    return bool(_COMPARATIVE.search(text) or _PERCENT.search(text))


def claim_like(text: str) -> bool:
    """True when the text has a claim-like construction. It fails closed: it is a net, not a definition, and a
    quote it catches is only left out of the answer. The record's own plain fields never match. It is run on the
    text as it is and on its skeleton (no format characters, look-alike letters mapped), and it includes the
    recommendation vocabulary and the verbs of use (used, underwent, approved, recommended) for EVERY field."""
    return _claim_like(text) or (skeleton(text) != text.lower() and _claim_like(skeleton(text))) or advises(text)


def _claim_like(text: str) -> bool:
    return bool(
        _COMPARATIVE.search(text)
        or _PERFORMANCE_VERB.search(text)
        or _PERCENT.search(text)
        or _CLAIM_EXTRA.search(text)
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


# --- the shape of a quote ----------------------------------------------------------------------------------
#
# A quote is offered only if it has the shape of its field. The shapes are small closed grammars, not word lists
# of what is forbidden: a quote that is anything else (free text after a label, a clause with a verb) has no
# shape and is excluded, whatever it says. See the module docstring.

_SEGMENT_SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z][A-Za-z ()/'-]{1,48}:\s)")
_SEGMENT = re.compile(r"^([A-Za-z][A-Za-z ()/'-]{1,48}?)\s*:\s+(.+?)\.?$")
_QUALIFIER = r"(?: \((?:estimated|estimate|actual|anticipated)\))?"
_STATUS_VALUES = frozenset(
    "recruiting|not yet recruiting|active not recruiting|active|completed|terminated|withdrawn|suspended|enrolling by invitation|unknown|"
    "unknown status|available|no longer available|temporarily not available|approved for marketing|withheld".split("|")
)
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_VALUE = re.compile(rf"^(?:\d{{4}}(?:-\d{{2}}(?:-\d{{2}})?)?|{_MONTH} (?:\d{{1,2}}, )?\d{{4}}){_QUALIFIER}$", re.IGNORECASE)
_ROMAN_OR_ARABIC = r"(?:1|2|3|4|i|ii|iii|iv)"
_PHASE_VALUE = re.compile(
    rf"^(?:not applicable|n/a|na|early phase {_ROMAN_OR_ARABIC}|phase ?{_ROMAN_OR_ARABIC}(?: ?(?:/|,|and) ?(?:phase ?)?{_ROMAN_OR_ARABIC})?)$", re.IGNORECASE
)
_ENROLL_VALUE = re.compile(rf"^(?:\d{{1,7}}(?: (?:participants|subjects|people|patients))?{_QUALIFIER}|estimated|actual|anticipated)$", re.IGNORECASE)
_RESULTS_VALUE = re.compile(r"^(?:yes|no|true|false|posted|not posted)$", re.IGNORECASE)
_NAME_TOKEN = re.compile(r"^\(?[A-Z0-9][A-Za-z0-9'\-]*\)?$|^\([A-Za-z0-9'\-]+\)?$")
_CONNECTORS = frozenset("of and or the de la du van von der non in at st".split())
_MAX_VALUE_CHARS = 160
_MAX_NAME_WORDS = 8

# The labels whose value is a status, a date, ... (the others of a field take a list of names).
_STATUS_LABELS = re.compile(r"^(?:overall status|status|recruitment status)$")
_RESULTS_LABELS = re.compile(r"^(?:results posted|has results|results)$")
_ENROLL_LABELS = re.compile(r"^(?:estimated enrollment|enrollment|enrolment|enrollment type)$")


def _name_list_ok(value: str) -> bool:
    """A list of names: items split on , or ;, each of 1 to 8 words that are capitalised, numbers, or one of a few
    connectors (of, and, in, ...). A lower-case word that is not a connector ("outclasses", "is") is a clause, not a name."""
    if not value or len(value) > _MAX_VALUE_CHARS or not re.fullmatch(r"[A-Za-z0-9 ,;()/'&+\-]+", value):
        return False
    items = [item.strip() for item in re.split(r"[,;]", value)]
    if any(not item for item in items):
        return False
    for item in items:
        words = item.split()
        if not words or len(words) > _MAX_NAME_WORDS:
            return False
        for index, word in enumerate(words):
            if _NAME_TOKEN.match(word):
                continue
            if word.lower() in _CONNECTORS and 0 < index < len(words) - 1:
                continue
            return False
    return not claim_like(value)


def _names_only(value: str, names: list[str]) -> bool:
    known = {re.sub(r"\s+", " ", n).strip().lower() for n in names if n.strip()}
    if not known or not value or len(value) > _MAX_VALUE_CHARS:
        return False
    items = [re.sub(r"\s+", " ", item).strip().lower() for item in re.split(r"[,;]", value)]
    return all(item in known for item in items)


def _value_ok(field: str, label: str, value: str, names: list[str]) -> bool:
    value = value.strip()
    if field == "status":
        return bool(_STATUS_LABELS.match(label)) and re.sub(r"[_\s]+", " ", value).replace(",", "").strip().lower() in _STATUS_VALUES
    if field == "dates":
        return bool(_DATE_VALUE.match(value))
    if field == "phase":
        return bool(_PHASE_VALUE.match(re.sub(r"[_\s]+", " ", value).strip()))
    if field == "enrollment":
        return bool(_ENROLL_LABELS.match(label)) and bool(_ENROLL_VALUE.match(value))
    if field == "results":
        return bool(_RESULTS_LABELS.match(label)) and bool(_RESULTS_VALUE.match(value))
    if field == "interventions":
        return _names_only(value, names)
    if field in {"conditions", "design", "sponsor", "location"}:
        return _name_list_ok(value)
    return False


def structured_ok(field: str, text: str, names: list[str]) -> bool:
    """True when the quote is one or more `Label: value` segments of this field and every value has the field's shape."""
    if field not in STRUCTURED_FIELDS or not text or "\n" in text:
        return False
    segments = _SEGMENT_SPLIT.split(normalise_text(text))
    for segment in segments:
        match = _SEGMENT.match(segment.strip())
        if match is None:
            return False
        label = re.sub(r"\s+", " ", match.group(1)).strip().lower()
        if field_for_label(label) != field:
            return False
        if not _value_ok(field, label, match.group(2), names):
            return False
    return True


# Narrative (brief summary, description) is prose. It is offered only if EVERY word is in this closed list of
# plain design words (record names, which are stripped first, aside). No digit, no verb of effect, no adjective of
# quality is in it, so a narrative quote can describe a design and nothing else. A word that is not here excludes the quote.
_NARRATIVE_WORDS = frozenset(
    """
    a an the of in on at to for with and or is are was were be been this that these those it its as by from there here which who where when
    observational interventional cohort cohorts study studies trial adult adults participants participant patients samples sample sampling
    collected collection baseline blood plasma tissue specimens specimen prospective retrospective single multicenter multicentre multi-center
    multi-centre center centre site sites open-label randomized randomised non-randomized non-randomised arm arms group groups design
    population populations lung cancer early-stage stage time point points timepoints follow-up listed named mentioned given
    """.split()
)
_NARRATIVE_WORD = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")


def narrative_ok(text: str, names: list[str]) -> bool:
    """A narrative quote made only of plain design words (and the record's own names). Fail closed."""
    stripped = text
    for name in sorted((n for n in names if n.strip()), key=len, reverse=True):
        stripped = re.sub(re.escape(name), " ", stripped, flags=re.IGNORECASE)
    if re.search(r"[0-9%]", stripped) or re.search(r"[^A-Za-z\s.,;()\-]", stripped):
        return False
    words = _NARRATIVE_WORD.findall(stripped)
    return bool(words) and all(word.lower() in _NARRATIVE_WORDS for word in words) and not claim_like(text) and not narrative_unsafe(text, names)


# What was done with, or to, something: a verb of use, of a procedure undergone, of approval or of recommendation. A name
# in the record is "named in the record", never used, undergone, approved or recommended (V37), so a quote with one of
# these words is not a card in ANY field, whatever its label says.
_USED_NET = re.compile(
    r"\b(?:use[sd]?|using|usage|utili[sz]\w*|employ\w*|appl(?:y|ies|ied|ying)|underw\w+|undergo\w*|undergon\w*|receiv\w*|"
    r"administer\w*|perform\w*|conduct(?:s|ed|ing)?|carried|approv\w*|clear(?:ed|ance)|authori[sz]\w*|licen[sc]\w*|"
    r"recommend\w*|endorse\w*|adopt\w*|implement\w*)\b",
    re.IGNORECASE,
)


def says_what_was_done(text: str) -> bool:
    return bool(_USED_NET.search(text) or _USED_NET.search(skeleton(text)))


def shape_ok(field: str, text: str, names: list[str]) -> bool:
    """The one test every intent applies to a card: the shape of its field. No shape, no answer. The verbs of use,
    procedure, approval and recommendation (`says_what_was_done`) are a net over EVERY field."""
    if says_what_was_done(text):
        return False
    if field in NARRATIVE_FIELDS:
        return narrative_ok(text, names)
    return structured_ok(field, text, names)


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


def pinned_version(report: dict[str, Any]) -> str | None:
    """The version the report is pinned to. A quote pinned to any other version is not a card: it would be cited under
    this report's `source_ref` while coming from another version of the source, or from another source."""
    version = report.get("version_id")
    return version if isinstance(version, str) and version else None


def discovery_versions(report: dict[str, Any]) -> set[str]:
    """The version IDs the discovery quotes are pinned to, so the caller can read their raw text once."""
    versions: set[str] = set()
    pinned = pinned_version(report)
    for quote in (report.get("discovery") or {}).get("quotes") or []:
        if isinstance(quote, dict):
            version = _quote_version(report, quote)
            if isinstance(version, str) and version and version == pinned:
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
        and not has_format_character(text)
        and not looks_like_instruction(text)
        and not advises(text)
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
        if pinned_version(report) is None or version_id != pinned_version(report):
            continue
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
