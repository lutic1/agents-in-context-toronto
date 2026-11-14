"""Deterministic medical gate (V70, step A.i). It runs first, before any model call.

The rule is one sentence: a question that mentions a PERSON or a CLINICAL DECISION is refused, with the one
fixed refusal and no model call. When in doubt it refuses, because a refusal costs a rephrase and a missed
medical question costs far more.

This is not a list of phrasings. There are two small vocabularies and nothing else:

- person words: I, me, my, we, our, mum, mom, dad, family, friend, a patient, a doctor, an oncologist, someone, he,
  she, "a 60 year old" ...
- decision and clinical words: should, would you, what would, recommend, advise, treat*, therapy, drug, dose,
  diagnose, prognosis, biopsy, surgery, ...

plus a few frames that make any question hypothetical ("if a patient", "what if", "suppose", "imagine").
A question is read after Unicode folding, look-alike letters, spacing tricks and common typos are repaired, so
"sh0uld i", "s h o u l d" and "shoud i" are read as "should i". The same two vocabularies exist in French, Spanish,
German, Italian, Portuguese and Dutch (accents folded) and as a few words in Chinese, Japanese, Korean, Russian
and Arabic. A language that is not detected gets no answer either: the intent gate and the vocabulary guard
(`question.py`) refuse to answer anything they cannot map to the record, still without a model call.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["medical_advice_rule", "is_medical_advice", "normalise_question"]

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)
_DELEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
# Cyrillic and Greek letters that look like Latin ones. NFKC folds full-width letters, not these.
_CONFUSABLES = str.maketrans(
    {
        "а": "a", "в": "b", "е": "e", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p", "с": "c", "т": "t", "у": "y", "х": "x",
        "і": "i", "ї": "i", "ѕ": "s", "ј": "j", "ԁ": "d", "һ": "h", "ԛ": "q", "ԝ": "w", "ӏ": "l", "ё": "e",
        "α": "a", "β": "b", "γ": "y", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
        "ɑ": "a", "ɡ": "g", "ı": "i", "ɩ": "i", "ʜ": "h", "ᴅ": "d", "ɴ": "n", "ꜱ": "s",
    }
)
_SPACED_RUN = re.compile(r"(?<![a-z0-9])(?:[a-z0-9][\s.\-_*]){3,}[a-z0-9](?![a-z0-9])")


def normalise_question(question: str) -> str:
    """Lowercase, NFKC, no zero-width characters, look-alike letters mapped, quotes and dashes flattened, spacing collapsed."""
    text = unicodedata.normalize("NFKC", question).translate(_ZERO_WIDTH).lower().translate(_CONFUSABLES)
    text = text.replace("’", "'").replace("‘", "'").replace("‐", "-").replace("‑", "-")
    text = re.sub(r"[–—]", " ", text)
    # "s h o u l d  i" and "s.h.o.u.l.d" collapse into one word, so spacing tricks do not hide a word.
    text = _SPACED_RUN.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), text)
    return re.sub(r"\s+", " ", text).strip()


def _fold(question: str) -> str:
    """NFKC, lowercase, accents removed ("médecin" -> "medecin"). Look-alike letters are NOT mapped: this is the
    view in which another language is read as itself."""
    text = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", question).translate(_ZERO_WIDTH).lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


# --- typo repair --------------------------------------------------------------------------------------------

_TYPO_WORDS = {
    "shud": "should", "shld": "should", "shoud": "should", "shold": "should", "shuld": "should", "shuold": "should",
    "shoudl": "should", "shouldd": "should", "sould": "should", "shoul": "should", "shopuld": "should", "shoulld": "should",
    "wat": "what", "whta": "what", "wht": "what", "tke": "take", "taek": "take", "drgu": "drug", "durg": "drug",
    "pateint": "patient", "pateints": "patients", "dr": "doctor", "doc": "doctor", "docs": "doctor", "mom": "mum",
}
# Words the markers hinge on. A token within one edit (two for ten letters or more) is read as the word, unless it
# is itself an ordinary word of the record's questions.
_CANONICAL = (
    "should", "patient", "patients", "treatment", "treatments", "therapy", "medication", "medications", "prescribe",
    "diagnose", "diagnosis", "prognosis", "dosage", "oncologist", "oncologists", "chemotherapy", "immunotherapy",
    "recommend", "physician", "physicians", "surgery", "biopsy", "doctor", "doctors", "advise", "clinician",
)
_PROTECTED = frozenset(
    "would could describe described describes subscribe patent patents treat treated shoulder shoulders hold holds model models "
    "modal records record mention mentions entry entries diagnostic diagnostics diagnoses surgeon surgeons surgical dosage "
    "location locations design designed status statuses sponsor sponsors phase phases date dates condition conditions "
    "enrollment enrolment enrolled intervention interventions".split()
) | frozenset(_CANONICAL)


def _distance(a: str, b: str) -> int:
    """Optimal string alignment distance: an insertion, deletion, substitution or adjacent swap is one edit."""
    rows = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        rows[i][0] = i
    for j in range(len(b) + 1):
        rows[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            rows[i][j] = min(rows[i - 1][j] + 1, rows[i][j - 1] + 1, rows[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                rows[i][j] = min(rows[i][j], rows[i - 2][j - 2] + 1)
    return rows[len(a)][len(b)]


def _repair_token(token: str) -> str:
    if token in _TYPO_WORDS:
        return _TYPO_WORDS[token]
    if len(token) < 5 or token in _PROTECTED:
        return token
    for word in _CANONICAL:
        limit = 1
        if abs(len(token) - len(word)) <= limit and _distance(token, word) <= limit:
            return word
    return token


def _deleet(text: str) -> str:
    """Read "sh0uld", "m3" and "$hould" as letters. A token with no letter ("phase 1", "2021") is left alone."""
    out = []
    for token in text.split(" "):
        if any(ch.isalpha() for ch in token) and any(ch in "0134 57@$!".replace(" ", "") for ch in token):
            token = token.translate(_DELEET)
        out.append(token)
    return " ".join(out)


_TOKEN = re.compile(r"[a-z]+|[0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text)


def _views(question: str) -> list[list[str]]:
    plain = normalise_question(question)
    views = [_tokens(plain), _tokens(_deleet(plain))]
    views += [[_repair_token(t) for t in tokens] for tokens in list(views)]
    seen: list[list[str]] = []
    for tokens in views:
        if tokens and tokens not in seen:
            seen.append(tokens)
    return seen


# --- the two vocabularies ----------------------------------------------------------------------------------

# A person: the asker, the asker's people, a patient, a clinician, anyone.
_PERSON_WORDS = frozenset(
    """
    i im ive me my mine myself we us our ours ourselves
    mum mummy mom mommy mama dad daddy papa parent parents family families friend friends relative relatives cousin cousins
    aunt auntie uncle grandma grandmother grandpa grandfather son daughter child children kid kids baby wife husband partner
    spouse boyfriend girlfriend brother sister sibling siblings mother father neighbour neighbor colleague coworker boss
    he she him his her hers himself herself someone somebody anyone anybody person persons man men woman women lady guy girl boy
    elderly senior smoker smokers survivor survivors
    patient patients doctor doctors physician physicians oncologist oncologists clinician clinicians nurse nurses surgeon
    surgeons specialist specialists pharmacist pharmacists gp practitioner practitioners
    """.split()
)
# A decision or a clinical matter, as whole words and as prefixes.
_DECISION_WORDS = frozenset(
    """
    should shouldnt ought would suppose imagine pretend hypothetical hypothetically scenario theoretically
    advice advise advised advisable recommend recommended recommendation recommendations suggest suggested suggestion
    opinion opinions choose choice choices pick prefer preferred decide decision decisions
    dose doses dosage dosing drug drugs medicine medicines medication medications medic medical pill pills tablet tablets
    treat treated treating treatment treatments therapy therapies therapeutic chemo chemotherapy radiotherapy radiation
    immunotherapy surgery surgical operation regimen prescribe prescribed prescription
    diagnose diagnosed diagnosis diagnoses prognosis prognostic survive survival mortality cure cured curable
    biopsy biopsies symptom symptoms risk risks safe safely unsafe dangerous eligible eligibility qualify candidate
    """.split()
)
_PERSON_PREFIX = re.compile(r"^(?:patient|doctor|physician|oncolog|clinician|nurse|surgeon|pharmac)\w*$")
_DECISION_PREFIX = re.compile(
    r"^(?:recommend|advis|advice|suggest|prescri|treat|therap|diagnos(?:e|es|ed|ing|is)\b|prognos|biops|medic|surg|chemo|radiother|immunother|"
    r"symptom|surviv|cure|curab|dosag|dosing|decision|decid|should|eligib)\w*$"
)

# Frames that make a question hypothetical or personal, matched on the token string.
_PHRASES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(pattern))
    for name, pattern in (
        ("would_you", r"\b(?:would|do|could|will|can) you (?:recommend|advise|suggest|think|pick|choose|prefer|do|say|take|give|tell me what)\b"),
        ("what_would", r"\bwhat (?:would|could|might|if)\b"),
        ("if_you_were", r"\bif you (?:were|was|had)\b|\byou think\b|\byour (?:opinion|view|advice|recommendation)\b"),
        ("what_to_do", r"\bwhat to (?:do|take|give|use|choose|pick|order|prescribe|start|stop)\b"),
        ("if_frame", r"\bif (?:a|an|the|some\w*|one|any\w*|it|they|there|this|that|i|we|you|he|she)\b"),
        ("with_stage", r"\b(?:with|has|had|have|having|diagnosed with|diagnosed|at) stage\b|\bstage [a-z0-9]{1,4} (?:patient|disease|cancer|case)\b"),
        ("years_old", r"\b\d+ ?(?:year|yr|yrs|years) ?(?:old)?\b|\baged \d+\b|\b\d+ y o\b"),
        ("in_my_case", r"\bin (?:my|our|his|her|their) (?:case|situation|family)\b"),
        ("side_effects", r"\bside effects?\b|\badverse (?:events?|effects?|reactions?)\b|\btoxicit\w*\b"),
        ("for_example", r"\bfor (?:a|an) (?:friend|relative|family|colleague|patient|person)\b"),
    )
)

# A Roman numeral after "phase" or "stage" is not the first person.
_NUMERAL_CONTEXT = frozenset({"phase", "phases", "stage", "stages", "type", "grade"})


def _rule_for_tokens(tokens: list[str]) -> str | None:
    for index, token in enumerate(tokens):
        if token == "i" and index > 0 and tokens[index - 1] in _NUMERAL_CONTEXT:
            continue
        if token in _PERSON_WORDS or _PERSON_PREFIX.match(token):
            return f"person:{token}"
        if token in _DECISION_WORDS or _DECISION_PREFIX.match(token):
            return f"decision:{token}"
    joined = " ".join(tokens)
    for name, pattern in _PHRASES:
        if pattern.search(joined):
            return f"frame:{name}"
    return None


# --- other languages (accents folded) ---------------------------------------------------------------------

_FOREIGN_WORDS = frozenset(
    """
    paciente pacientes medico medica doctora tratamiento tratamientos tratar medicamento medicamentos medicina farmaco farmacos
    dosis diagnostico pronostico cirugia yo mi mis mio mia nosotros nuestro nuestra madre padre mama familia amigo amiga hermano hermana
    debo deberia debe puedo recomienda recomiendas recomendar aconseja consejo sintomas biopsia enfermo enferma hijo hija esposa esposo
    medecin docteur traitement traitements traiter medicament medicaments posologie pronostic chirurgie je moi mon ma mes nous notre nos
    ami amie mere pere maman famille dois devrais devrait puis recommande recommandez conseille conseillez symptomes biopsie malade
    arzt arztin aerztin behandlung behandeln medikament medikamente diagnose prognose operation ich mich mir mein meine meinen meiner
    wir unser unsere mutter vater familie freund freundin sollte soll empfehlen empfehlung empfiehlst symptome krank therapie
    dottore dottoressa cura curare trattamento farmaci diagnosi prognosi chirurgia io mia miei noi nostro nostra mamma famiglia amico
    devo dovrei posso consiglia raccomanda sintomi malato
    tratamento remedio cirurgia meu minha nos nosso nossa mae pai deveria recomenda sintomas doente
    dokter behandeling medicijn medicijnen operatie ik mij mijn wij ons onze moeder vader vriend vriendin moet zou aanbevelen symptomen ziek
    """.split()
)
# Scripts with no word spacing or a different alphabet: a substring is enough.
_FOREIGN_SUBSTRINGS = (
    "患者", "病人", "医生", "醫生", "医师", "治疗", "治療", "药", "藥", "我的", "我应该", "我該", "诊断", "診断", "处方", "手术", "手術",
    "医師", "薬", "患者さん", "私の", "私は", "환자", "의사", "치료", "약", "진단", "내가", "제가",
    "пациент", "врач", "лечени", "лекарств", "диагноз", "мой", "моя", "мне", "я ",
    "مريض", "طبيب", "علاج", "دواء", "أنا", "انا",
)


def _foreign_rule(question: str) -> str | None:
    folded = _fold(question)
    for token in re.findall(r"[a-z]+", folded):
        if token in _FOREIGN_WORDS:
            return f"foreign:{token}"
    padded = unicodedata.normalize("NFKC", question).lower() + " "
    for fragment in _FOREIGN_SUBSTRINGS:
        if fragment in padded:
            return "foreign:script"
    return None


def medical_advice_rule(question: str) -> str | None:
    """The name of the rule that makes this a medical question, or None. Case, spacing and simple character
    substitutions do not hide a word."""
    for tokens in _views(question):
        rule = _rule_for_tokens(tokens)
        if rule is not None:
            return rule
    return _foreign_rule(question)


def is_medical_advice(question: str) -> bool:
    return medical_advice_rule(question) is not None
