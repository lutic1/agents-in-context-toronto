"""Claim-accuracy checks for check 4 (V7, Story 10.7, AD-19; A23 folded into A06).

Every claim the drafter wrote is judged against the source's own structured
fields (``overall_status``, ``has_results``) and the quotes that were checked
word for word against the source version. Nothing here calls a model: the
outcome is decided by the source fields, the checked quotes and plain text
patterns, so the same draft always gets the same answer.

The three claim policies:

* ``claim_performed_or_results``: a sentence stating that an assay was
  performed, detected something, showed or produced results needs
  ``has_results: true`` or its own checked quote stating a result. An
  eligibility, enrolment, cohort-definition or design sentence states no
  result, nor does a bare "was performed" or a result verb used as a
  participle that defines a population ("patients with ctDNA detected at
  baseline"). A claim of this kind that makes no such statement passes.
* ``claim_planned``: when the trial is NOT_YET_RECRUITING or RECRUITING (or
  otherwise planned), it must be described as planned or ongoing.
* ``claim_preclinical``: cell-line or animal evidence must be labelled
  preclinical.

A policy judges the claims the drafter tagged with its kind, and also any
claim whose own words fall under it, so a mis-tagged claim cannot slip past.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

CLAIM_PERFORMED_OR_RESULTS = "claim_performed_or_results"
CLAIM_PLANNED = "claim_planned"
CLAIM_PRECLINICAL = "claim_preclinical"
CLAIM_POLICIES = (CLAIM_PERFORMED_OR_RESULTS, CLAIM_PLANNED, CLAIM_PRECLINICAL)

# Statuses under which a trial is planned or under way, not finished.
PLANNED_STATUSES = frozenset({"NOT_YET_RECRUITING", "RECRUITING", "ENROLLING_BY_INVITATION"})

# A statement that something was performed or produced a result. Only finite
# past or present forms: "to detect", "detecting" and "no results posted" do not
# match, while "showed", "detected" and "demonstrates" do.
_PERFORMED = re.compile(
    r"\b("
    r"showed|shows|shown|demonstrated|demonstrates|detected|detects|"
    r"found that|finds that|produced|produces|yielded|yields|achieved|achieves|"
    r"revealed|reveals|confirmed|confirms|proved|proves|"
    r"was performed|were performed|has been performed|have been performed|"
    r"resulted in|results showed|results show|reported (?:a|an|that)|"
    r"sensitivity of|specificity of|concordance of"
    r")\b",
    re.IGNORECASE,
)

# Eligibility, enrolment, cohort, design or plan wording: a quote like this describes who
# may take part or what will be done, never a result ("patients in whom tumor NGS was
# performed within 90 days are eligible", "patients with an EGFR mutation detected by tumor
# NGS are enrolled", "Cohort B: patients with ctDNA detected at baseline").
_NOT_A_RESULT = re.compile(
    r"\b("
    r"inclusion|exclusion|eligible|eligibility|criteria|criterion|must have|must be|required to|"
    r"will be|will undergo|to be performed|primary outcome|secondary outcome|outcome measures?|"
    r"enrol\w*|enroll\w*|recruit\w*|randomi[sz]\w*|allocat\w*|assigned to|stratified|"
    r"cohorts?|arms?|may|can|should|qualif\w*"
    r")\b",
    re.IGNORECASE,
)

# Past-tense RESULT wording is what a quote must say to support a performance claim. A quote
# that only says an assay "was performed" states no result (review item 5), so the bare
# performance verbs are not here.
#
# The single result verbs. Each is also a past participle, so on its own it
# can describe a population ("patients with ALK fusions identified by tissue NGS") instead of
# reporting a finding. It counts as a result only when it is used as a finite verb.
_RESULT_VERB = re.compile(
    r"\b(showed|demonstrated|detected|yielded|achieved|revealed|identified)\b", re.IGNORECASE
)
# Result phrases that are finite by construction.
_RESULT_PHRASE = re.compile(
    r"\b("
    r"found that|resulted in|results showed|results demonstrated|reported (?:a|an|that)|"
    r"(?:sensitivity|specificity|concordance|accuracy|detection rate) (?:was|were|of)"
    r")\b",
    re.IGNORECASE,
)
_AUXILIARY_BEFORE = re.compile(r"\b(?:was|were|is|are|has been|have been|had been)\s+$", re.IGNORECASE)
# A participle that modifies a noun is followed by its agent or circumstance ("detected by
# tumor NGS", "identified at baseline", "detected within 90 days"), or ends the sentence.
_PARTICIPLE_AFTER = re.compile(
    r"^\s*(?:$|[.;:,)]|(?:by|at|within|on|via|using|through|from|with|during|after|before|"
    r"prior|among|across|per|under|for|in)\b)",
    re.IGNORECASE,
)


def _finite_result_verb(quote: str) -> bool:
    """True when one of the single result verbs is used finitely: after an auxiliary
    ("EGFR mutations were detected in 42%") or with a direct object ("Tumor NGS detected EGFR
    mutations"), not as a participle modifying a noun ("an EGFR mutation detected by NGS")."""
    for m in _RESULT_VERB.finditer(quote):
        if _AUXILIARY_BEFORE.search(quote[: m.start()]):
            return True
        if not _PARTICIPLE_AFTER.match(quote[m.end():]):
            return True
    return False


def quote_states_a_result(quote: str) -> bool:
    """True when a quote reports a result.

    A positive test, not only a blocklist: the quote must use result wording as a finite
    statement (a result phrase such as "sensitivity was", or a result verb used finitely), and
    it must not contain eligibility, enrolment, cohort, design or plan wording. A result verb
    used as a participle that defines a population ("patients with ctDNA detected at
    baseline") states no result.
    """
    q = quote or ""
    if _NOT_A_RESULT.search(q):
        return False
    return bool(_RESULT_PHRASE.search(q)) or _finite_result_verb(q)

# Wording that describes a trial as planned or still running.
_PLANNED_WORDS = re.compile(
    r"\b("
    r"planned|plans|plan to|will|is recruiting|are recruiting|recruiting|"
    r"not yet recruiting|enrolling|ongoing|under way|underway|in progress|"
    r"is investigating|investigates|aims to|is designed to|is evaluating|evaluates|"
    r"is studying|is assessing|assesses|no results posted|no results yet"
    r")\b",
    re.IGNORECASE,
)

# Wording that describes a trial as finished.
_FINISHED_WORDS = re.compile(
    r"\b(completed|has completed|finished|concluded|was terminated)\b",
    re.IGNORECASE,
)

# Cell-line or animal evidence.
_PRECLINICAL_EVIDENCE = re.compile(
    r"\b("
    r"cell[- ]lines?|in vitro|xenografts?|mice|mouse|murine|rats?|"
    r"animal (?:models?|stud(?:y|ies))|organoids?|patient-derived xenografts?"
    r")\b",
    re.IGNORECASE,
)
_PRECLINICAL_LABEL = re.compile(r"\bpre-?clinical\b", re.IGNORECASE)


def states_performed_or_results(text: str) -> bool:
    """True when the text states that something was performed or produced a result."""
    return bool(_PERFORMED.search(text or ""))


def mentions_preclinical_evidence(text: str) -> bool:
    return bool(_PRECLINICAL_EVIDENCE.search(text or ""))


def is_planned_status(overall_status: str | None) -> bool:
    return (overall_status or "").upper() in PLANNED_STATUSES


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _checked_quotes(quotes: Iterable[Any] | None) -> list[str]:
    """The quotes that were found word for word in the source version."""
    out = []
    for q in quotes or []:
        if _get(q, "quote_found") is True and _get(q, "text"):
            out.append(str(_get(q, "text")))
    return out


def _policy_applies(policy: str, claim_kind: str, text: str, quote: str) -> bool:
    if claim_kind == policy:
        return True
    if policy == CLAIM_PERFORMED_OR_RESULTS:
        return states_performed_or_results(text)
    if policy == CLAIM_PLANNED:
        # Any claim that calls the trial finished or reports its outcome is a
        # statement about its status.
        return bool(_FINISHED_WORDS.search(text)) or states_performed_or_results(text)
    if policy == CLAIM_PRECLINICAL:
        return mentions_preclinical_evidence(text) or mentions_preclinical_evidence(quote)
    return False


def _judge(policy: str, text: str, quote: str, source: Mapping[str, Any], quotes: list[str]) -> tuple[bool, str]:
    """Judge one claim under one policy. Returns (passed, detail)."""
    if policy == CLAIM_PERFORMED_OR_RESULTS:
        if not states_performed_or_results(text):
            return True, "no performance or results statement"
        if source.get("has_results") is True:
            return True, "the source has posted results (has_results: true)"
        # Only the claim's own quote, found word for word, may support it, and only when it
        # states a result; otherwise has_results: true is required.
        if quote and quote in quotes and quote_states_a_result(quote):
            return True, f"the claim's own checked quote states a result: {quote[:300]!r}"
        why = "has no checked quote of its own" if not (quote and quote in quotes) else "has a checked quote that states no result"
        return False, (
            "states that something was performed or produced results, but the source has "
            f"has_results: {source.get('has_results')!r} and the claim {why}"
        )
    if policy == CLAIM_PLANNED:
        status = (source.get("overall_status") or "").upper()
        if status not in PLANNED_STATUSES:
            return True, f"status {status or 'unknown'} is not planned or recruiting"
        if states_performed_or_results(text) or _FINISHED_WORDS.search(text):
            return False, (
                f"the trial is {status}, but the claim describes it as finished or reports an outcome"
            )
        if _PLANNED_WORDS.search(text):
            return True, f"the trial is {status} and the claim describes it as planned or ongoing"
        return False, f"the trial is {status}, but the claim does not describe it as planned or ongoing"
    if policy == CLAIM_PRECLINICAL:
        if not (mentions_preclinical_evidence(text) or mentions_preclinical_evidence(quote)):
            return True, "no cell-line or animal evidence"
        if _PRECLINICAL_LABEL.search(text):
            return True, "cell-line or animal evidence is labelled preclinical"
        return False, "cell-line or animal evidence is not labelled preclinical"
    return True, "not a claim policy"


def evaluate_claims(
    claims: Iterable[Any],
    source_fields: Mapping[str, Any] | None,
    checked_quotes: Iterable[Any] | None,
    policies: Iterable[str],
) -> list[dict[str, Any]]:
    """Judge every claim under every active claim policy.

    ``claims`` are ``{claim_kind, text, quote?}`` as tagged by the drafter.
    ``source_fields`` carries ``overall_status`` and ``has_results`` of the exact
    source version used. ``checked_quotes`` are ``{text, quote_found}``.
    ``policies`` are the claim policies of the pinned policy set that apply to
    the action kind.

    Returns one ``Decision.claims`` entry per claim:
    ``{claim_kind, text, passed, detail, failed_policies}``.
    """
    source = dict(source_fields or {})
    quotes = _checked_quotes(checked_quotes)
    active = [p for p in CLAIM_POLICIES if p in set(policies)]
    results = []
    for claim in claims or []:
        kind = str(_get(claim, "claim_kind") or "")
        text = str(_get(claim, "text") or "")
        quote = str(_get(claim, "quote") or "")
        failed: list[str] = []
        details: list[str] = []
        for policy in active:
            if not _policy_applies(policy, kind, text, quote):
                continue
            ok, detail = _judge(policy, text, quote, source, quotes)
            details.append(f"{policy}: {detail}")
            if not ok:
                failed.append(policy)
        results.append(
            {
                "claim_kind": kind,
                "text": text,
                "passed": not failed,
                "detail": "; ".join(details) if details else "no claim policy applies",
                "failed_policies": failed,
            }
        )
    return results


def failed_claim_policies(results: Iterable[Mapping[str, Any]]) -> list[str]:
    """The claim policies that failed, in policy order, without repeats."""
    failed = {p for r in results for p in r.get("failed_policies", [])}
    return [p for p in CLAIM_POLICIES if p in failed]
