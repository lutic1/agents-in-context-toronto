"""Deterministic medical-advice detector (V70). It runs first, before any model call.

A banned category: a question that asks for a diagnosis, a treatment, a dose, a prognosis, a choice
of test or drug, or "should I or my patient ...", gets one fixed refusal and no model call. The
detector is a list of named patterns over a normalised question. It errs toward refusing: a
refusal costs a rephrase, a missed medical question costs far more. Questions about what the record
says (status, names, quotes, sources, related evidence) must still pass; the tests hold both lists.

Other languages: a question that is not plain English (a letter outside basic Latin, or Latin text
with non-English function words) cannot be read by these patterns, so it gets the same fixed refusal
and no model call (rule "non_english"). Typos and look-alike letters are repaired before matching.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["medical_advice_rule", "is_medical_advice", "normalise_question", "NON_ENGLISH_RULE"]

NON_ENGLISH_RULE = "non_english"

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
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
    """Lowercase, NFKC, no zero-width characters, quotes and dashes flattened, spacing collapsed."""
    text = unicodedata.normalize("NFKC", question).translate(_ZERO_WIDTH).lower().translate(_CONFUSABLES)
    text = text.replace("’", "'").replace("‘", "'").replace("‐", "-").replace("‑", "-")
    text = re.sub(r"[–—]", " ", text)
    # "s h o u l d  i" and "s.h.o.u.l.d" collapse into one word, so spacing tricks do not hide a pattern.
    text = _SPACED_RUN.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), text)
    return re.sub(r"\s+", " ", text).strip()


# Misspellings of short words the patterns hinge on ("shud i", "shld i", "wat").
_TYPO_WORDS = {
    "shud": "should", "shld": "should", "shoud": "should", "shold": "should", "shuld": "should", "shuold": "should",
    "shoudl": "should", "shouldd": "should", "sould": "should", "shoul": "should", "shopuld": "should", "shoulld": "should",
    "wat": "what", "whta": "what", "wht": "what", "whihc": "which", "wich": "which", "whch": "which", "whcih": "which",
    "tke": "take", "taek": "take", "drgu": "drug", "durg": "drug", "pateint": "patient", "pateints": "patients",
}
# Longer words the patterns hinge on. A token within one edit (two for words of ten letters or more) of one of these is
# read as that word, unless it is itself an ordinary word of the record's questions.
_CANONICAL = (
    "should", "patient", "patients", "treatment", "treatments", "therapy", "medication", "medications", "prescribe",
    "diagnose", "diagnosis", "dosage", "oncologist", "oncologists", "chemotherapy", "immunotherapy", "recommend",
    "physician", "physicians", "surgery", "biopsy",
)
_PROTECTED = frozenset(
    "would could describe described describes subscribe patent patents therapy treat treated shoulder shoulders hold holds model models modal records record "
    "mention mentions entry entries diagnostic diagnostics diagnoses surgeon surgeons surgical dosage".split()
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
        limit = 1 if len(word) < 10 else 2
        if abs(len(token) - len(word)) <= limit and _distance(token, word) <= limit:
            return word
    return token


def _repair_typos(text: str) -> str:
    return " ".join(_repair_token(token) for token in text.split())


def _variants(question: str) -> list[str]:
    plain = normalise_question(question)
    no_apostrophes = plain.replace("'", "")
    leet = no_apostrophes.translate(_LEET)
    punctuation_free = re.sub(r"[^a-z0-9' ]+", " ", plain)
    punctuation_free = re.sub(r"\s+", " ", punctuation_free).strip()
    leet_free = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", leet)).strip()
    seen: list[str] = []
    for text in (plain, no_apostrophes, punctuation_free, leet_free, leet, _repair_typos(punctuation_free), _repair_typos(leet_free)):
        if text and text not in seen:
            seen.append(text)
    return seen


# Function words that mark Latin-script text as French, Spanish, German, Italian, Portuguese or Dutch.
# One strong word is enough; the weak ones are also English-looking and need two.
_FOREIGN_STRONG = frozenset(
    "ik ich je moet soll sollte devo dois debo debe deberia debería mijn mein meine meinen est sont les des une pour dans "
    "una unos unas por este esta estos estas cette ces dieses diese dieser dit niet nicht und ist kann kunnen puedo posso "
    "voglio quiero tengo ho hai suis sont avec sans medicamento farmaco medikament medicijn paciente paziente patiente "
    "arzt medico medecin docteur dokter".split()
)
_FOREIGN_WEAK = frozenset(
    "el la le lo los las de du un en con che di della del der die das ein eine het een wat que qui pas vous il sus uma".split()
)


def _not_plain_english(question: str) -> bool:
    """True when the question has a letter outside basic Latin, or reads as another Latin-script language."""
    text = unicodedata.normalize("NFKC", question).translate(_ZERO_WIDTH)
    if any(ch.isalpha() and ord(ch) > 127 for ch in text):
        return True
    tokens = re.findall(r"[a-z]+", text.lower())
    if any(t in _FOREIGN_STRONG for t in tokens):
        return True
    return sum(1 for t in tokens if t in _FOREIGN_WEAK) >= 2


_RELATIVE = r"(?:mother|mom|mum|father|dad|wife|husband|partner|spouse|son|daughter|child|children|brother|sister|friend|grandmother|grandfather|grandma|grandpa|aunt|uncle|relative|family member|loved one|boyfriend|girlfriend|neighbou?r|colleague|client)"
_CLINICIAN = r"(?:clinicians?|doctors?|oncologists?|physicians?|surgeons?|nurses?|pathologists?|radiologists?|gps?|practitioners?)"
_MED_VERB = (
    r"(?:take|start|stop|begin|use|get|order|try|choose|pick|switch|change|receive|undergo|have|treat|test|screen|biopsy|"
    r"prescribe|give|avoid|skip|continue|discontinue|enrol|enroll|join|worry|see|go|combine|add|drop|rely|adopt|"
    r"be\s+(?:treated|tested|given|put|started|switched|screened|offered|cured|operated))"
)
_THING = r"(?:treatment|therapy|therapies|drug|drugs|medication|medications|medicine|medicines|regimen|chemo|chemotherapy|immunotherapy|radiotherapy|radiation|surgery|operation|pill|pills|tablet|tablets|inhibitor|inhibitors)"

# (name, pattern). The first match wins; the name is only for the Decision's inputs.
_RULES: list[tuple[str, re.Pattern[str]]] = [
    (name, re.compile(pattern))
    for name, pattern in [
        # Indirect, third-party, hypothetical and misspelled ways of asking the same things.
        ("modal_typo", r"\bsh(?:ou|uo|o|u)?l?d\s+(?:i|we)\b"),
        ("should_filler_patient", r"\bshould\s+(?:\w+\s+){0,6}(?:patients?|women|woman|men|man|people|persons?|adults?|smokers?|children|child|kids?|someone|girl|boy|lady)\b"),
        ("advice_near_person", r"\b(?:suggest\w*|advis\w*|recommend\w*|appropriate|advisable|worth|indicated|warranted)\b(?:\s+\w+){0,6}\s+(?:i|me|my|we|us|our|patients?|friend|her|him|she|he|someone|them|persons?)\b|\b(?:i|me|my|we|us|our|patients?|friend|her|him|someone|them)\b(?:\s+\w+){0,6}\s+(?:suggest\w*|advis\w*|recommend\w*|appropriate|advisable|indicated|warranted)\b"),
        ("need_treatment", r"\bneed\w*\s+(?:a\s+|an\s+|any\s+|some\s+)?(?:\w+\s+){0,2}(?:chemo\w*|treatments?|surgery|therapy|medications?|drugs?|radiation|operation|immunotherapy|biopsy|biopsies)\b"),
        ("right_call", r"\b(?:right|good|best|better|wise|correct|safe|sensible|smart)\s+(?:call|choice|option|approach|move|decision|idea|course|step)\b|\bgood\s+options?\b"),
        ("clinician_would", rf"\b(?:would|will|does|do|did|should|could|can)\s+(?:the\s+|a\s+|my\s+)?(?:\w+\s+)?{_CLINICIAN}\s+(?:\w+\s+){{0,2}}(?:advis|recommend|suggest|prescrib|order|treat|perform|choose|pick|offer|give|start|stop|do)\w*"),
        ("advisable", r"\badvisable\b|\b(?:appropriate|recommended|indicated)\s+(?:for|to)\b|\bworth\s+(?:getting|taking|doing|having|trying)\b"),
        ("next_step", r"\bnext\s+steps?\b(?:\s+\w+){0,8}\s+(?:patients?|symptoms?|me|my|i|someone|person|him|her)\b|\b(?:patients?|symptoms?|my|someone|person|him|her)\b(?:\s+\w+){0,8}\s+next\s+steps?\b|\bwhat\s+(?:now|next)\b"),
        ("dose_word", r"\b(?:dose|doses|dosage|dosages|dosing)\b"),
        ("how_much", r"\bhow\s+much\s+(?:\w+\s+)?(?:should|to\s+(?:give|take|use|administer)|can\s+(?:i|we|a|the)|do\s+(?:i|we))\b|\bshould\s+(?:\w+\s+){0,2}(?:be\s+)?(?:given|administered|taken|prescribed|started|stopped)\b"),
        ("what_to_do", r"\bwhat\s+to\s+(?:do|take|give|use|choose|pick|order|prescribe|start|stop)\b|\bwhat\s+(?:do|can|could|should)\s+(?:i|we)\s+do\b"),
        ("how_do_i_enrol", r"\bhow\s+(?:do|can|could|would|should)\s+(?:i|we)\s+(?:enrol|enroll|join|sign|apply|participate|qualify|take|start|stop|treat)\b"),
        ("third_party", rf"\b(?:a|my|our|his|her|their)\s+(?:\w+\s+)?(?:mother|mom|mum|father|dad|wife|husband|spouse|son|daughter|child|children|brother|sister|friend|grandmother|grandfather|grandma|grandpa|aunt|uncle|relative|family member|loved one|boyfriend|girlfriend|neighbou?r)\b|\bapplies?\s+to\s+(?:her|him|them|me|my)\b|\b(?:he|she)\s+(?:has|have|was\s+told|was\s+diagnosed|is\s+(?:sick|ill|dying))\b|\bsomeone\s+(?:had|has|have|got)\b"),
        ("hypothetical_frame", r"(?=.*\b(?:hypothetical\w*|educational\s+purposes?|for\s+(?:a|my)\s+friend|asking\s+for|just\s+curious|theoretically|in\s+theory|research\s+purposes?|academic\w*|roleplay|role\s+play|pretend|imagine|suppose)\b)(?=.*\b(?:diagnos\w*|treat\w*|cure\w*|recommend\w*|advis\w*|should|therapy|drug|dose|prescrib\w*|patients?|cancer|nsclc|tumou?r|surgery|chemo\w*)\b)"),
        ("how_treated", r"\bhow\s+(?:do|does|would|should|can|could|is|are|did|will)\s+(?:\w+\s+){0,4}(?:treat|treated|treating|managed|manage|diagnosed|diagnose|cured|cure|handled|handle)\b"),
        ("clinicians_do", rf"\bwhat\s+(?:do|does|would|should|can|could|will)\s+(?:the\s+)?(?:{_CLINICIAN}|patients?|people|persons?)\s+(?:\w+\s+){{0,2}}(?:do|take|give|order|prescribe|use|advise|recommend|start|offer|suggest|tell)\b"),
        ("treatment_for_disease", r"\b(?:treatments?|therapy|therapies|cure|medications?|drugs?)\s+(?:for|of|against)\s+(?:\w+\s+){0,3}(?:cancer|nsclc|sclc|disease|tumou?rs?|carcinoma|lung|malignan\w*|adenocarcinoma|mutation)\b"),
        ("prognosis_word", r"\bprognos\w*\b|\bsurvival\s+(?:rates?|chances?|odds|times?|probabilit\w*|likelihood)\b|(?<!overall\s)(?<!free\s)\bsurvival\b|\bmortality\b"),
        ("will_survive", r"\bwill\s+(?:the\s+|this\s+|a\s+|my\s+)?(?:\w+\s+){0,2}(?:patient|person|he|she|they)\s+(?:survive|live|die|relapse|recover)\b|\bwill\s+(?:it|he|she|they)\s+(?:come\s+back|spread|relapse)\b"),
        ("benefit", r"\b(?:would|will|could|can|does|do)\s+(?:\w+\s+){0,3}(?:patients?|persons?|people|someone|i|we)\s+(?:\w+\s+){0,2}(?:benefit|respond|qualify|survive|live|die|relapse|recover|improve|get\s+better)\b"),
        ("tell_whether", r"\btell\s+(?:me|us)\s+(?:whether|if)\s+(?:to|i|we|he|she|they|a\s+patient|the\s+patient)\b|\btell\s+(?:the\s+patient|them|him|her)\s+(?:what|whether|which|how|if)\b|\bwhether\s+to\s+(?:get|take|start|stop|have|do|use|order|undergo|treat|test|biopsy|operate|screen|skip|continue|switch)\b"),
        ("ok_to_ignore", r"\b(?:ok|okay|safe|fine|alright)\s+to\s+(?:ignore|skip|stop|delay|wait|defer|postpone)\b"),
        ("skip_treatment", r"\b(?:skip|ignore|delay|avoid|refuse|forgo|postpone|defer|decline)\s+(?:a\s+|an\s+|the\s+|any\s+)?(?:\w+\s+){0,3}(?:surgery|treatments?|chemo\w*|therapy|medications?|biops(?:y|ies)|results?|tests?|testing|screening|follow\s*up)\b|\bstop\s+(?:a\s+|an\s+|the\s+)?(?:\w+\s+){0,2}(?:treatments?|chemo\w*|therapy|medications?)\b"),
        ("diagnose_word", r"\bdiagnose\b|\bdiagnosing\b"),
        ("cure_word", r"\bcures?\b|\bcurable\b|\bcured\b"),
        ("do_they_have", r"\b(?:do|does|did|will|would)\s+(?:they|he|she|you|we)\s+(?:have|get)\s+(?:\w+\s+){0,2}(?:cancer|disease|tumou?rs?|nsclc|carcinoma|lung|infection|condition|illness|mutation)\b"),
        ("my_situation", r"\bmy\s+(?:\w+\s+)?(?:situation|case|family|history|nodules?|lumps?|masses|lesions?|growths?|cysts?|polyps?)\b"),
        # Asking what to do ("should I or my patient ...").
        ("should_i", r"\bshould\s+(?:i|we)\s+(?:or|and)\s+(?:my|our|the|a)\b"),
        ("should_i_any", r"\bshould\s*i\b"),
        ("should_we_medical", rf"\bshould\s+(?:we|you|he|she|they|one|someone)\s+(?:\w+\s+){{0,2}}{_MED_VERB}\b"),
        ("should_patient", rf"\bshould\s+(?:\w+\s+){{0,2}}(?:patients?|{_CLINICIAN}|{_RELATIVE})\b"),
        ("should_my", rf"\bshould\s+(?:my|our)\s+(?:\w+\s+){{0,2}}{_MED_VERB}\b"),
        ("who_should", rf"\bwho\s+should\s+(?:\w+\s+){{0,2}}{_MED_VERB}\b"),
        ("what_should_do", rf"\bwhat\s+(?:\w+\s+)?should\s+(?:i|we|you|they|he|she|a\s+patient|the\s+patient|patients|{_CLINICIAN})\s+(?:\w+\s+)?(?:do|take|ask|order|choose|pick|use|prescribe|give|try|start|stop|get|test|treat|expect|know)\b"),
        ("what_would_you_do", r"\b(?:what\s+would\s+you\s+do|if\s+you\s+were\s+(?:me|him|her|in\s+my)|what\s+would\s+you\s+(?:take|choose|pick|recommend))\b"),
        ("would_you_recommend", r"\b(?:would|do|can|could|will)\s+you\s+(?:recommend|advise|suggest|prescribe|give|choose|pick|order|start|stop|treat|test|tell\s+me\s+(?:what|which|whether))\b"),
        ("advise_on", r"\badvise\s+(?:on|me|us|my|the|him|her|them|about)\b|\btell\s+(?:me|my\s+\w+|us)\s+what\s+to\s+(?:do|take|give|use|choose)\b"),
        ("i_should", r"\bi\s+should\b|\bshould\s+(?:he|she|they)\b"),
        ("patient_decision", rf"\b(?:a|the|this|that|one|each|every|my|our|per)\s+(?:\w+\s+){{0,2}}patient\b.*\b(?:right|best|better|need|needs|recommend\w*|should|give|take|treat\w*|diagnos\w*|cure\w*|eligible|candidate|safe|effective|suitable|worry|advice|advise|options|next|drug|therapy|dose|dosage|biopsy|surgery|chemo\w*|immunotherapy|prescri\w*)\b|\b(?:right|best|better|recommend\w*|should|give|take|treat\w*|diagnos\w*|cure\w*|safe|effective|suitable|prescri\w*|need|needs)\b.*\b(?:a|the|this|that|one|each|every|my|our)\s+(?:\w+\s+){{0,2}}patient\b"),
        ("patients_need", r"\bpatients\s+(?:\w+\s+){0,2}(?:need|needs|must|should)\b|\b(?:do|does|should|must)\s+patients\b"),
        ("like_me", r"\b(?:like\s+me|someone\s+(?:with|who|newly|recently|like)|a\s+person\s+with|people\s+like|patients\s+like|for\s+(?:a|an)\s+(?:\d+|\w+)[\s-]year[\s-]old)\b"),
        ("what_do_i_take", r"\b(?:what|which)\s+(?:\w+\s+){0,3}(?:do|can|could|would|will)\s+(?:i|we|he|she|they)\s+(?:take|use|get|try|give|need|do)\b|\bif\s+i\s+(?:skip|stop|miss|delay|refuse|don'?t|do\s+not)\b|\bwhat\s+happens\s+if\s+(?:i|he|she|they)\b"),
        ("recommend_me", r"\b(?:recommend|advise|suggest|prescribe)\s+(?:me|us|him|her|them|my|a\s+(?:treatment|therapy|drug|test|dose|medication)|what|which|something)\b"),
        ("advice_words", r"\b(?:medical|clinical|treatment|health|diagnostic)\s+(?:advice|recommendations?|guidance|opinions?)\b|\bsecond\s+opinion\b|\bgive\s+me\s+(?:some\s+)?advice\b|\bneed\s+advice\b"),
        # Personal medical context: me, my patient, my relatives.
        ("my_patient", rf"\bmy\s+(?:\w+\s+)?(?:patients?|{_RELATIVE}|doctors?|oncologists?|physicians?|clinicians?|nurses?)\b"),
        ("my_medical_noun", r"\bmy\s+(?:\w+\s+)?(?:tumou?rs?|cancers?|diagnos\w+|biops(?:y|ies)|scans?|symptoms?|treatments?|therapy|medications?|prescriptions?|blood\s?work|mutations?|conditions?|illness|disease|lab\s+results?|test\s+results?|results?|ctdna|cfdna|genes?|lung|lungs|chest|cough|pain|options|chances|risk|odds|health|prognosis|stage)\b"),
        ("first_person_clinical", r"\bi\s+(?:was\s+diagnosed|was\s+told\s+i|think\s+i\s+have|might\s+have|may\s+have|am\s+(?:sick|ill|dying|diagnosed|pregnant|worried\s+about|scared|a\s+patient)|feel\s+(?:sick|ill|pain|dizzy|tired|weak)|have\s+(?:a\s+)?(?:cough|pain|fever|symptoms?|cancer|tumou?r|nodule|mass|lump|shortness|diagnos\w+|stage\s+\w+|nsclc|sclc|egfr|alk|kras|mutation|lung))\b"),
        ("do_i_have", r"\b(?:do|did|will|would|could|might|may)\s+i\s+(?:have|need|get|die|survive|live|qualify|be\s+(?:cured|ok|okay|fine|sick|ill))\b"),
        ("am_i", r"\bam\s+i\s+(?:sick|ill|dying|cured|at\s+risk|eligible|a\s+candidate|suitable|a\s+good\s+fit|safe|ok|okay|healthy|going\s+to)\b"),
        ("can_i_medical", rf"\b(?:can|could|may|might)\s+i\s+(?:safely\s+)?(?:take|stop|start|get|have|receive|skip|combine|mix|drink|eat|drive|exercise|travel|enrol|enroll|join|qualify|participate|undergo|order|try|switch|be\s+(?:treated|tested|cured))\b"),
        ("eligibility", rf"\bis\s+(?:he|she|they|my\s+\w+|the\s+patient|this\s+patient|a\s+patient|{_RELATIVE})\s+(?:eligible|a\s+candidate|suitable|a\s+good\s+fit)\b"),
        # Diagnosis, treatment, dose, prognosis.
        ("diagnose_someone", r"\bdiagnos(?:e|ing)\s+(?:me|him|her|them|my|a|the|this|that|someone|myself)\b|\bwhat(?:'?s|\s+is)\s+(?:wrong|the\s+matter)\s+with\b|\bwhat\s+(?:disease|condition|illness|cancer)\s+(?:do|does|have|has)\s+(?:i|he|she|they)\b"),
        ("treat_someone", rf"\b(?:treat(?:ing)?|cure|curing|medicat(?:e|ing)|operate\s+on|heal)\s+(?:\w+\s+){{0,2}}(?:me|him|her|them|my|his|their|myself|someone|a\s+patient|the\s+patient|this\s+patient|a\s+person)\b"),
        ("how_to_treat", r"\bhow\s+(?:to|do\s+(?:i|we|you)|can\s+(?:i|we|you)|should\s+(?:i|we|you))\s+(?:treat|cure|manage|prevent|diagnose|heal|fix|get\s+rid\s+of|beat|survive)\b"),
        ("can_be_cured", r"\b(?:can|could|will)\s+(?:it|this|that|[\w\-]+(?:\s+[\w\-]+)?)\s+be\s+(?:cured|treated|healed|prevented|reversed)\b|\bis\s+(?:it|this|that|[\w\-]+(?:\s+[\w\-]+)?)\s+(?:curable|treatable|survivable)\b"),
        ("prescribe", r"\bprescri(?:be|bes|bed|bing|ption|ptions)\b"),
        ("dose", rf"\b(?:dose|doses|dosage|dosing)\b.*\b(?:should|take|give|recommend|safe|right|best|use|per\s+day|daily)\b|\bhow\s+(?:much|many)\s+(?:\w+\s+)?(?:mg|milligrams?|pills?|tablets?|doses?|{_THING})\b|\bwhat\s+(?:dose|dosage)\b"),
        ("best_treatment", rf"\b(?:best|better|safest|safer|right|optimal|ideal|recommended|appropriate|suitable|preferred|most\s+effective|first[\s-]line|second[\s-]line)\s+(?:\w+\s+){{0,2}}{_THING}\b"),
        ("what_to_give", rf"\b(?:what|which)\s+(?:\w+\s+){{0,2}}(?:{_THING}|test|assay)\s+to\s+(?:give|take|use|prescribe|choose|pick|try|order|offer|start)\b"),
        ("treatment_options", rf"\b(?:treatment|therapy)\s+(?:options|plan|choices|regimen|approach|pathway)\b|\brecommended\s+(?:workup|work-up|screening|approach|course|protocol|management|pathway|schedule|guidelines?)\b|\bstandard\s+of\s+care\b"),
        ("is_thing_recommended", rf"\bis\s+(?:\w+\s+){{0,2}}(?:{_THING}|biopsy|biopsies)\s+(?:recommended|advised|necessary|needed|required|appropriate|indicated|warranted|better|worth)\b"),
        ("best_way", r"\b(?:best|right|safest|proper|correct)\s+way\s+to\s+(?:treat|cure|manage|diagnose|detect|test|screen|prevent)\b"),
        ("comparison", rf"\b(?:better|best|safer|safest|more\s+effective|preferable|superior)\b.*\b{_THING}\b|\b{_THING}\b.*\b(?:better|best|safer|safest|more\s+effective|preferable|superior)\b"),
        ("rule_out", r"\b(?:rule|rules|ruled)\s+out\s+(?:\w+\s+){0,2}(?:cancer|disease|tumou?r|malignancy|lung)\b"),
        ("dosage_chart", r"\b(?:dosage|dosing)\s+(?:chart|guide|table|schedule|recommendations?|instructions?)\b|\b(?:give|tell)\s+me\s+(?:a\s+|the\s+)?(?:dose|dosage)\b"),
        ("which_treatment", rf"\b(?:what|which)\s+(?:\w+\s+){{0,2}}{_THING}\b.*\b(?:should|recommend\w*|best|better|right|choose|pick|prescribe|safest|safer|preferred|appropriate|suitable)\b"),
        ("best_test", r"\b(?:best|better|right|recommended|appropriate|suitable|preferred)\s+(?:\w+\s+){0,2}(?:test|assay|biomarker|panel|scan)\s+(?:for|to)\s+(?:diagnos|detect|screen|identify|choose|guide|decide|treat|monitor)\w*"),
        ("which_test_to_order", rf"\bwhich\s+(?:\w+\s+){{0,2}}(?:test|assay|panel|scan)s?\s+(?:should|to|do\s+i|would\s+you)\b"),
        ("order_test", rf"\b(?:should|do)\s+(?:\w+\s+){{0,3}}(?:order|run|request|get)\s+(?:a\s+|an\s+|the\s+)?(?:\w+\s+){{0,3}}(?:test|assay|panel|scan|biopsy)\b"),
        ("safe_for", r"\b(?:safe|unsafe|dangerous|harmful)\s+(?:for|to)\s+(?:me|us|him|her|them|my\s+\w+|a\s+patient|the\s+patient|someone|pregnant|children|kids|the\s+elderly|take|use|give|combine|mix|drink|eat)\b"),
        ("is_it_ok_to", r"\bis\s+it\s+(?:ok|okay|fine|wise|advisable|a\s+good\s+idea|worth(?:\s+it)?|recommended|necessary)\s+(?:for\s+\w+\s+)?to\s+(?:take|use|stop|start|skip|get|order|test|treat|switch)\b"),
        ("side_effects_for_me", r"\b(?:side\s+effects?|risks?|interactions?)\b.*\b(?:for\s+me|for\s+my|for\s+him|for\s+her|if\s+i|when\s+i)\b"),
        ("prognosis", r"\b(?:my|his|her|their|the\s+patient'?s?)\s+(?:prognosis|survival|life\s+expectancy|chances|odds)\b|\blife\s+expectancy\b|\bhow\s+long\s+(?:will|do|does|can|would)\s+(?:i|he|she|they|a\s+patient|the\s+patient|my\s+\w+)\s+(?:live|survive|have\s+left|last)\b|\bchances?\s+of\s+(?:survival|surviving|dying|recovery|recovering|cure|remission)\b"),
        ("interpret_results", r"\binterpret\s+(?:my|his|her|their|these|this|the)\s+(?:\w+\s+){0,2}(?:results?|scan|biopsy|labs?|ctdna|mutation|genomic|blood)\b"),
        ("clinical_decision", rf"\b(?:should|must|ought\s+to)\s+(?:\w+\s+){{0,3}}(?:{_CLINICIAN}|patients?)\s+(?:\w+\s+){{0,3}}{_MED_VERB}\b"),
    ]
]


def medical_advice_rule(question: str) -> str | None:
    """The name of the first pattern the question trips, or None. Case, spacing and simple
    character substitutions do not hide a pattern."""
    for text in _variants(question):
        for name, pattern in _RULES:
            if pattern.search(text):
                return name
    if _not_plain_english(question):
        return NON_ENGLISH_RULE
    return None


def is_medical_advice(question: str) -> bool:
    return medical_advice_rule(question) is not None
