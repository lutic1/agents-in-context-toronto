"""The answerable intents (V70, step A.ii): a small fixed set, each tied to report fields.

A question is answered only if it maps to exactly ONE intent here. An intent says which card fields it may use,
whether narrative cards (brief summary, description) may help, and what a card must hold to be offered. The
model never sees a card of another intent's field.

Keyword matching is on word stems, so "recruiting" and "recruit", or "sponsors" and "sponsored", are the same
word. Every word of a question that is an intent keyword is exempt from the vocabulary guard (`question.py`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from dxp.interview.cards import NARRATIVE_FIELDS, Card, claim_like, normalise_text, shape_ok

__all__ = ["INTENTS", "Intent", "STOPWORDS", "eligible_cards", "keyword_stems", "match_intent", "stem", "tokenise"]

_TOKEN = re.compile(r"[a-z]+|[0-9]+")


def tokenise(text: str) -> list[str]:
    return _TOKEN.findall(text.lower().replace("'", " "))


def stem(token: str) -> str:
    """A light stem, the same on both sides of every comparison: plural, -ing, -ed and a final e are removed."""
    word = token
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        word = word[:-1]
    for suffix in ("ing", "ed"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            word = word[: -len(suffix)]
            break
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


@dataclass(frozen=True)
class Intent:
    name: str
    fields: frozenset[str]  # card fields this intent may use
    words: frozenset[str]  # keyword words (stemmed on load)
    phrases: tuple[str, ...] = ()  # two-word keywords, worth two hits
    narrative: bool = False  # may brief summary / description cards help?
    must_hold: re.Pattern[str] | None = None  # every card offered must match this
    narrative_must_hold: re.Pattern[str] | None = None  # a narrative card offered must match this


def _words(text: str) -> frozenset[str]:
    return frozenset(stem(w) for w in text.split())


INTENTS: tuple[Intent, ...] = (
    Intent(
        "status",
        frozenset({"status"}),
        _words("status recruiting recruitment recruit active ongoing completed terminated withdrawn suspended stopped open closed"),
        ("still enrolling", "currently enrolling"),
    ),
    Intent(
        "dates",
        frozenset({"dates"}),
        _words("date dates when start started begin began begins end ended ends completion updated update posted submitted year month deadline timeline first last"),
        ("start date", "completion date", "first posted", "last updated", "primary completion"),
    ),
    Intent(
        "conditions",
        frozenset({"conditions"}),
        _words("condition conditions disease diseases cancer cancers nsclc sclc tumor tumors tumour tumours carcinoma illness disorder indication"),
    ),
    Intent("phase", frozenset({"phase"}), _words("phase phases")),
    Intent(
        "design",
        frozenset({"design"}),
        _words(
            "design designed allocation masking blinded blinding randomised randomized randomisation randomization arm arms cohort cohorts "
            "population sample samples sampling specimen specimens observational interventional purpose aim aims objective objectives "
            "summary overview description describe describes"
        ),
        ("study type", "study design"),
        narrative=True,
        narrative_must_hold=re.compile(
            r"\b(?:design\w*|random\w*|blind\w*|mask\w*|arms?|cohorts?|observational|interventional|prospective|retrospective|samples?|"
            r"sampling|specimens?|plasma|blood|tissue|population|allocation|open-label|purpose|aims?|objectives?)\b",
            re.IGNORECASE,
        ),
    ),
    Intent(
        "interventions",
        frozenset({"interventions"}),
        _words(
            "name names named naming mention mentions mentioned intervention interventions assay assays test tests product products device "
            "devices diagnostic diagnostics platform panel kit biomarker biomarkers technology"
        ),
        ("other names",),
        narrative=True,
    ),
    Intent(
        "sponsor",
        frozenset({"sponsor"}),
        _words("sponsor sponsors sponsored funder funded funding collaborator collaborators organisation organization institution university company runs conducting conducted responsible"),
    ),
    Intent(
        "location",
        frozenset({"location"}),
        _words("location locations site sites country countries city cities where facility facilities centre center centres centers place"),
    ),
    Intent(
        "enrollment",
        frozenset({"enrollment"}),
        _words("enrollment enrolment enrolled enrol enroll participants participant subjects volunteers size people"),
        ("sample size",),
    ),
    Intent(
        "results",
        frozenset({"results"}),
        _words("results result posted"),
        ("results posted", "posted results"),
        must_hold=re.compile(r"\bresults?\b", re.IGNORECASE),
    ),
)
_BY_NAME = {intent.name: intent for intent in INTENTS}

# Words that carry no content of their own. Anything else in a question must be an intent keyword or appear in
# the record (the vocabulary guard). The words about "the record" itself are here, so "the accepted record" never
# has to be in the record.
STOPWORDS = frozenset(
    stem(w)
    for w in """
    a an the of in on at to for is are was were be been being do does did what which who whom whose when where why how it its this that
    these those and or but with about from by as there has have had say says said tell tells give gives show shows list lists please can
    could will not no yes also some any all each every both only just one exactly overall main current currently still yet already now
    here then so if into out up over under between other another too very really much many long own same such record records report
    reports accepted trial trials study studies entry listing listed state states stated according per you your yours they them their
    theirs studied cover covers covered address addressed given give gives use used uses using located take takes place planned plan plans
    appear appears kind kinds sort type types number whether either regarding concerning related information info details detail know
    i ii iii iv know exactly actually get gets got make makes made
    """.split()
)


def keyword_stems(intent: Intent) -> frozenset[str]:
    return intent.words | frozenset(stem(w) for phrase in intent.phrases for w in phrase.split())


def match_intent(question: str) -> tuple[Intent | None, str]:
    """The ONE intent a question maps to, or (None, reason). Two intents with the same score are ambiguous and
    map to nothing."""
    stems = [stem(t) for t in tokenise(question)]
    pairs = {f"{a} {b}" for a, b in zip(stems, stems[1:], strict=False)}
    scored: list[tuple[int, Intent]] = []
    for intent in INTENTS:
        score = sum(1 for s in set(stems) if s in intent.words)
        score += 2 * sum(1 for phrase in intent.phrases if " ".join(stem(w) for w in phrase.split()) in pairs)
        if score:
            scored.append((score, intent))
    if not scored:
        return None, "no_intent"
    scored.sort(key=lambda pair: -pair[0])
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None, "ambiguous_intent"
    return scored[0][1], "ok"


def intent_named(name: str) -> Intent:
    return _BY_NAME[name]


def eligible_cards(intent: Intent, cards: list[Card], names: list[str]) -> list[Card]:
    """The cards this intent may use, in report order. Fail closed: a card of another field, a card that does not
    have the shape of its field (`cards.shape_ok`: no free text after a label, no prose outside the closed design
    vocabulary), a claim-like card, a narrative card the intent does not allow, or a card that does not hold what
    the intent needs is left out. Interventions are cards that list only the names the record gives, and those are preferred to narrative cards."""
    chosen: list[Card] = []
    for card in cards:
        if card.field not in intent.fields and not (intent.narrative and card.field in NARRATIVE_FIELDS):
            continue
        if claim_like(card.text) or not shape_ok(card.field, card.text, names):
            continue
        if intent.must_hold is not None and not intent.must_hold.search(card.text):
            continue
        if card.field in NARRATIVE_FIELDS and intent.narrative_must_hold is not None and not intent.narrative_must_hold.search(card.text):
            continue
        if card.field in NARRATIVE_FIELDS and intent.name == "interventions":
            # A narrative card helps "what the record names" only if it names one of the record's names.
            lowered_names = [n.lower() for n in names if n.strip()]
            if not any(name in normalise_text(card.text).lower() for name in lowered_names):
                continue
        chosen.append(card)
    if intent.name == "interventions":
        # "What does the record name?" is answered by the cards that list only names. A narrative card that happens to
        # hold a name helps only when no name-only card exists.
        name_only = [card for card in chosen if card.field not in NARRATIVE_FIELDS]
        if name_only:
            return name_only
    return chosen
