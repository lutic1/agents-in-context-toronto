"""Deterministic medical-advice detector (V70). It runs first, before any model call.

A banned category: a question that asks for a diagnosis, a treatment, a dose, a prognosis, a choice
of test or drug, or "should I or my patient ...", gets one fixed refusal and no model call. The
detector is a list of named patterns over a normalised question. It errs toward refusing: a
refusal costs a rephrase, a missed medical question costs far more. Questions about what the record
says (status, names, quotes, sources, related evidence) must still pass; the tests hold both lists.

Not covered: questions in another language than English. They are not refused here and reach the
quote-only answer path, which cannot give advice either (it only quotes the record).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["medical_advice_rule", "is_medical_advice", "normalise_question"]

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
_SPACED_RUN = re.compile(r"(?<![a-z0-9])(?:[a-z0-9][\s.\-_*]){3,}[a-z0-9](?![a-z0-9])")


def normalise_question(question: str) -> str:
    """Lowercase, NFKC, no zero-width characters, quotes and dashes flattened, spacing collapsed."""
    text = unicodedata.normalize("NFKC", question).translate(_ZERO_WIDTH).lower()
    text = text.replace("’", "'").replace("‘", "'").replace("‐", "-").replace("‑", "-")
    text = re.sub(r"[–—]", " ", text)
    # "s h o u l d  i" and "s.h.o.u.l.d" collapse into one word, so spacing tricks do not hide a pattern.
    text = _SPACED_RUN.sub(lambda m: re.sub(r"[\s.\-_*]", "", m.group(0)), text)
    return re.sub(r"\s+", " ", text).strip()


def _variants(question: str) -> list[str]:
    plain = normalise_question(question)
    no_apostrophes = plain.replace("'", "")
    leet = no_apostrophes.translate(_LEET)
    punctuation_free = re.sub(r"[^a-z0-9' ]+", " ", plain)
    punctuation_free = re.sub(r"\s+", " ", punctuation_free).strip()
    seen: list[str] = []
    for text in (plain, no_apostrophes, punctuation_free, re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", leet)).strip(), leet):
        if text and text not in seen:
            seen.append(text)
    return seen


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
    return None


def is_medical_advice(question: str) -> bool:
    return medical_advice_rule(question) is not None
