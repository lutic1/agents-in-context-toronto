"""The report's grounded text script (AD-30, V41).

script_for() is a template over the report's own fields: the signal
(headline), its status and the gap. A model may only shorten that wording;
shortening_problems() rejects a result that carries a number, NCT ID, assay
name or status the template script does not.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from dxp.api.models import Report

from dxp.reports.draft import mention_names, wording_flags

GAP_LEAD = "Evidence gap: "
STATUS_LEAD = "Trial status: "
NO_RESULTS = "No results posted."
HAS_RESULTS = "Results posted."

# Longest first, so "not yet recruiting" is never read as "recruiting".
STATUS_PHRASES = sorted(
    (
        "active not recruiting", "not yet recruiting", "enrolling by invitation",
        "temporarily not available", "no longer available", "approved for marketing",
        "unknown status", "no results posted", "results not posted", "results posted",
        "posted results", "results available", "has results", "no results",
        "recruiting", "completed", "terminated", "suspended", "withdrawn",
        "approved", "cleared", "pending", "accepted", "rejected",
    ),
    key=len,
    reverse=True,
)
_STATUS_RE = re.compile(r"\b(%s)\b" % "|".join(re.escape(p) for p in STATUS_PHRASES))
_NUMBER_RE = re.compile(r"\b\w*\d\w*(?:[.,]\d+)*%?")
_NCT_RE = re.compile(r"\bNCT\d{8}\b", re.IGNORECASE)
_CDX_RE = re.compile(r"\b[\w-]*CDx\b", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z]+")
# "one" is left out: it is also an ordinary pronoun and part of product names.
NUMBER_WORDS = frozenset(
    "zero two three four five six seven eight nine ten eleven twelve twenty thirty "
    "forty fifty sixty seventy eighty ninety hundred thousand million dozen half "
    "double triple twice percent".split()
)


def _clean(value):
    return " ".join(value.split()) if isinstance(value, str) else ""


def _sentence(text):
    return text if text[-1:] in ".!?" else text + "."


def _normal(text):
    return " ".join(re.sub(r"[_,;:/()\-]", " ", text.lower()).split())


def _as_dict(report):
    if hasattr(report, "model_dump"):
        return report.model_dump()
    return dict(report or {})


def script_parts(report):
    """The script's sentences: the signal, its status, the gap."""
    report = _as_dict(report)
    discovery = report.get("discovery") or {}
    headline = _clean(report.get("headline"))
    if not headline:
        raise ValueError("a report script needs the report's headline")
    parts = [_sentence(headline)]

    def said(text):
        return _normal(text).rstrip(".") in _normal(" ".join(parts))

    status_line = _clean(report.get("status_line"))
    trial_status = _clean(discovery.get("trial_status"))
    if status_line:
        if not said(status_line):
            parts.append(_sentence(status_line))
    elif trial_status and not said(trial_status):
        parts.append(_sentence(STATUS_LEAD + trial_status))
    has_results = discovery.get("has_results")
    if has_results is False and not said(NO_RESULTS):
        parts.append(NO_RESULTS)
    elif has_results is True and not said(HAS_RESULTS):
        parts.append(HAS_RESULTS)
    gap = _clean(report.get("gap"))
    if gap:
        parts.append(_sentence(GAP_LEAD + gap))
    return parts


def script_for(report: Report | dict[str, Any]) -> str:
    """The grounded text script of a report, from its own fields only."""
    return " ".join(script_parts(report))


def script_hash(script: str) -> str:
    return hashlib.sha256(script.encode("utf-8")).hexdigest()


def _numbers(text):
    return {token.lower().rstrip(".,") for token in _NUMBER_RE.findall(text)} | (
        set(_WORD_RE.findall(text.lower())) & NUMBER_WORDS
    )


def _statuses(text):
    return set(_STATUS_RE.findall(_normal(text)))


def shortening_problems(candidate, report, assay_names=()):
    """Why a shortened script is rejected; an empty list means it may be used.

    The reference is the template script of the same report. `assay_names`
    are the known assay names (the scope's and the ledger's); the names the
    record mentions and anything ending in "CDx" are always checked too.
    """
    report = _as_dict(report)
    reference = script_for(report)
    if not isinstance(candidate, str) or not candidate.strip():
        return ["empty: the shortened script has no text"]
    candidate = _clean(candidate)
    problems = []
    if len(candidate) > len(reference):
        problems.append("longer: the result is longer than the template script")
    for number in sorted(_numbers(candidate) - _numbers(reference)):
        problems.append("number: %r is not in the report's script fields" % number)
    reference_ncts = {n.upper() for n in _NCT_RE.findall(reference)}
    for nct in sorted({n.upper() for n in _NCT_RE.findall(candidate)} - reference_ncts):
        problems.append("nct_id: %r is not in the report's script fields" % nct)
    names = []
    for name in list(assay_names or []) + mention_names(report) + _CDX_RE.findall(candidate):
        name = _clean(name)
        if name and name.lower() not in {n.lower() for n in names}:
            names.append(name)
    for name in names:
        if name.lower() in candidate.lower() and name.lower() not in reference.lower():
            problems.append("assay_name: %r is not in the report's script fields" % name)
    for status in sorted(_statuses(candidate) - _statuses(reference)):
        problems.append("status: %r is not in the report's script fields" % status)
    for flag in wording_flags(candidate, names):
        problems.append("wording: %r said about %r" % (flag["verb"], flag["name"]))
    return problems


def accept_shortened(candidate, report, assay_names=()):
    """The shortened script if it is grounded, else the template script."""
    if shortening_problems(candidate, report, assay_names):
        return script_for(report)
    return _clean(candidate)
