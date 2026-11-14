"""ClinicalTrials.gov API v2 client (A05, Story 10.1 and Story 1.4, AD-15, AD-25, V37, V40).

The one place that talks to ClinicalTrials.gov:

- `fetch_study(nct_id)`: `GET /api/v2/studies/<nct_id>`, one record by NCT ID.
- `search(term, cond, cursor)`: `GET /api/v2/studies` with `query.term`, `query.cond` and
  `filter.advanced = AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]`, reading every page up to a
  fixed cap. `complete` is False when the cap stopped it, so the scan never advances the cursor
  past records it did not read.
- `parse_study(study)`: the fields DxP keeps: `overall_status`, `has_results`,
  `last_update_post_date`, the interventions verbatim (name, type, `otherNames` and the rest as
  the API returns them; a name in the record is a mention, never proof of use, V37), the text
  fields as `raw_text` and the shorter `evidence_text` (AD-15).

Nothing here touches the database. PubMed is deferred (V18) and never fetched here.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx

BASE_URL = "https://clinicaltrials.gov/api/v2"
STUDY_URL = "https://clinicaltrials.gov/study/{nct_id}"
SOURCE = "clinicaltrials.gov"
TIMEOUT_S = 30.0
PAGE_SIZE = 100
MAX_PAGES = 10  # the fixed cap (AD-25): at most 1,000 records per scan
USER_AGENT = "dxp/0.1 (research prototype)"

NCT_RE = re.compile(r"^NCT\d{8}$")
_WS = re.compile(r"\s+")


class CtgovError(Exception):
    """A request without a usable answer. `http_status` is None when no response arrived."""

    def __init__(self, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status


class StudyNotFound(CtgovError):
    """HTTP 404 for an NCT ID."""


@dataclass
class SearchResult:
    studies: list[dict[str, Any]] = field(default_factory=list)
    http_status: int | None = None
    pages: int = 0
    complete: bool = True
    params: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# References and query building
# ---------------------------------------------------------------------------


def source_ref(nct_id: str) -> str:
    return f"{SOURCE}:{nct_id}"


def nct_from_ref(ref: str) -> str:
    return ref.split(":", 1)[1] if ref.startswith(SOURCE + ":") else ref


def check_nct(nct_id: str) -> str:
    nct = (nct_id or "").strip().upper()
    if not NCT_RE.match(nct):
        raise ValueError(f"not an NCT ID: {nct_id!r}")
    return nct


def quote_term(term: str) -> str:
    """One quoted phrase; inner double quotes are dropped (they would end the phrase)."""
    return '"' + _WS.sub(" ", term.replace('"', " ")).strip() + '"'


def or_terms(terms: Iterable[str]) -> str:
    """Terms quoted and OR-joined, in order, without duplicates (AD-25)."""
    kept: list[str] = []
    for t in terms:
        if isinstance(t, str) and t.strip() and t.strip() not in kept:
            kept.append(t.strip())
    return " OR ".join(quote_term(t) for t in kept)


def last_update_filter(cursor: str) -> str:
    """`AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]` (V2); inclusive of the cursor day."""
    return f"AREA[LastUpdatePostDate]RANGE[{cursor},MAX]"


def search_params(term: str, cond: str | None, cursor: str | None, page_size: int = PAGE_SIZE) -> dict[str, Any]:
    params: dict[str, Any] = {"format": "json", "pageSize": page_size, "countTotal": "true"}
    if term:
        params["query.term"] = term
    if cond:
        params["query.cond"] = cond
    if cursor:
        params["filter.advanced"] = last_update_filter(cursor)
    return params


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE_URL, timeout=TIMEOUT_S, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )


async def _get(client: httpx.AsyncClient, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
    """One GET. A 429 or 5xx is retried once after a short wait (a read, so a retry is safe);
    no response after the retry raises CtgovError with no status."""
    for attempt in (1, 2):
        try:
            resp = await client.get(path, params=params)
        except httpx.HTTPError as exc:
            if attempt == 2:
                raise CtgovError(f"no response from ClinicalTrials.gov ({type(exc).__name__})") from exc
            await asyncio.sleep(1.0)
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt == 2:
                raise CtgovError(f"ClinicalTrials.gov answered HTTP {resp.status_code}", resp.status_code)
            retry_after = resp.headers.get("Retry-After", "")
            await asyncio.sleep(min(float(retry_after), 10.0) if retry_after.isdigit() else 1.0)
            continue
        return resp
    raise CtgovError("unreachable")  # pragma: no cover


async def fetch_study(nct_id: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """`GET /api/v2/studies/<nct_id>`: the whole record as the API returns it."""
    nct = check_nct(nct_id)
    own = client is None
    client = client or make_client()
    try:
        resp = await _get(client, f"/studies/{nct}", {"format": "json"})
    finally:
        if own:
            await client.aclose()
    if resp.status_code == 404:
        raise StudyNotFound(f"{nct} not found", 404)
    if resp.status_code != 200:
        raise CtgovError(f"{nct}: HTTP {resp.status_code}", resp.status_code)
    return resp.json()


async def search(
    term: str,
    cond: str | None,
    cursor: str | None,
    *,
    page_size: int = PAGE_SIZE,
    max_pages: int | None = None,
    max_results: int | None = None,
    client: httpx.AsyncClient | None = None,
) -> SearchResult:
    """Every page of one query, up to `max_pages` pages (or `max_results` records).

    `complete` is True only when the last page read had no `nextPageToken`. A non-200 answer
    raises CtgovError, so a partial scan is never mistaken for a finished one.
    """
    max_pages = max_pages or MAX_PAGES
    size = min(page_size, max_results) if max_results else page_size
    params = search_params(term, cond, cursor, size)
    result = SearchResult(params=dict(params))
    own = client is None
    client = client or make_client()
    try:
        token: str | None = None
        while True:
            page_params = dict(params)
            if token:
                page_params["pageToken"] = token
            resp = await _get(client, "/studies", page_params)
            result.http_status = resp.status_code
            if resp.status_code != 200:
                raise CtgovError(f"search: HTTP {resp.status_code}", resp.status_code)
            body = resp.json()
            result.studies.extend(body.get("studies") or [])
            result.pages += 1
            token = body.get("nextPageToken")
            if max_results is not None and len(result.studies) >= max_results:
                result.complete = token is None and len(result.studies) == max_results
                result.studies = result.studies[:max_results]
                break
            if not token:
                result.complete = True
                break
            if result.pages >= max_pages:
                result.complete = False
                break
    finally:
        if own:
            await client.aclose()
    return result


# ---------------------------------------------------------------------------
# Parsing a study into the fields DxP keeps
# ---------------------------------------------------------------------------


def _module(study: dict[str, Any], name: str) -> dict[str, Any]:
    return (study.get("protocolSection") or {}).get(name) or {}


def _lines(label: str, value: Any) -> list[str]:
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value if v not in (None, ""))
    if value is None or value == "":
        return []
    return [f"{label}: {value}"]


def interventions_of(study: dict[str, Any]) -> list[dict[str, Any]]:
    """The interventions exactly as the API returns them (V37): every key kept, `otherNames` included."""
    return [dict(iv) for iv in (_module(study, "armsInterventionsModule").get("interventions") or [])]


def _intervention_line(iv: dict[str, Any], with_description: bool = True) -> str:
    text = str(iv.get("name", ""))
    if iv.get("type"):
        text += f" ({iv['type']})"
    other = [n for n in (iv.get("otherNames") or []) if isinstance(n, str)]
    if other:
        text += f"; other names: {', '.join(other)}"
    if with_description and iv.get("description"):
        text += f"; {iv['description']}"
    return text


def build_raw_text(study: dict[str, Any]) -> str:
    """The record's text fields, labelled, in a fixed order. Quotes are checked against this
    text, so every value is kept word for word."""
    ident = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    desc = _module(study, "descriptionModule")
    cond = _module(study, "conditionsModule")
    design = _module(study, "designModule")
    arms = _module(study, "armsInterventionsModule")
    outcomes = _module(study, "outcomesModule")
    elig = _module(study, "eligibilityModule")
    sponsor = _module(study, "sponsorCollaboratorsModule")

    lines: list[str] = []
    lines += _lines("NCT ID", ident.get("nctId"))
    lines += _lines("Title", ident.get("briefTitle"))
    lines += _lines("Official title", ident.get("officialTitle"))
    lines += _lines("Overall status", status.get("overallStatus"))
    lines += _lines("Has results", "yes" if study.get("hasResults") else "no")
    lines += _lines("Last update posted", (status.get("lastUpdatePostDateStruct") or {}).get("date"))
    lines += _lines("Lead sponsor", (sponsor.get("leadSponsor") or {}).get("name"))
    lines += _lines("Study type", design.get("studyType"))
    lines += _lines("Phases", design.get("phases"))
    lines += _lines("Conditions", cond.get("conditions"))
    lines += _lines("Keywords", cond.get("keywords"))
    for iv in arms.get("interventions") or []:
        lines += _lines("Intervention", _intervention_line(iv))
    for arm in arms.get("armGroups") or []:
        arm_text = str(arm.get("label", ""))
        if arm.get("description"):
            arm_text += f": {arm['description']}"
        lines += _lines("Arm", arm_text)
    lines += _lines("Brief summary", desc.get("briefSummary"))
    lines += _lines("Detailed description", desc.get("detailedDescription"))
    for label, key in (("Primary outcome", "primaryOutcomes"), ("Secondary outcome", "secondaryOutcomes")):
        for o in outcomes.get(key) or []:
            text = str(o.get("measure", ""))
            if o.get("description"):
                text += f": {o['description']}"
            if o.get("timeFrame"):
                text += f" (time frame: {o['timeFrame']})"
            lines += _lines(label, text)
    lines += _lines("Eligibility criteria", elig.get("eligibilityCriteria"))
    return "\n".join(lines)


def build_evidence_text(study: dict[str, Any]) -> str:
    """AD-15's embedding text: title, brief summary, conditions, interventions and status."""
    ident = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    desc = _module(study, "descriptionModule")
    cond = _module(study, "conditionsModule")
    lines: list[str] = []
    lines += _lines("Title", ident.get("briefTitle"))
    lines += _lines("Conditions", cond.get("conditions"))
    for iv in interventions_of(study):
        lines += _lines("Intervention", _intervention_line(iv, with_description=False))
    lines += _lines("Overall status", status.get("overallStatus"))
    lines += _lines("Has results", "yes" if study.get("hasResults") else "no")
    lines += _lines("Brief summary", desc.get("briefSummary"))
    return "\n".join(lines)


def normalise_text(text: str) -> str:
    """Whitespace collapsed and trimmed: the text the content hash is taken over (V40)."""
    return _WS.sub(" ", text or "").strip()


def content_hash(raw_text: str) -> str:
    """SHA-256 of the normalised `raw_text`, first 16 hex characters (the width of A03's
    `source_versions` validator and of AD-3 IDs)."""
    return hashlib.sha256(normalise_text(raw_text).encode("utf-8")).hexdigest()[:16]


def last_update_post_date(study: dict[str, Any]) -> str | None:
    return (_module(study, "statusModule").get("lastUpdatePostDateStruct") or {}).get("date")


def parse_study(study: dict[str, Any]) -> dict[str, Any]:
    """The fields DxP keeps from one record (Story 1.4, Story 10.1, V40)."""
    ident = _module(study, "identificationModule")
    status = _module(study, "statusModule")
    nct = ident.get("nctId")
    if not nct:
        raise ValueError("record has no NCT ID")
    raw_text = build_raw_text(study)
    return {
        "nct_id": nct,
        "source_ref": source_ref(nct),
        "source": SOURCE,
        "url": STUDY_URL.format(nct_id=nct),
        "title": ident.get("briefTitle"),
        "overall_status": status.get("overallStatus"),
        "has_results": bool(study.get("hasResults", False)),
        "last_update_post_date": last_update_post_date(study),
        "conditions": list(_module(study, "conditionsModule").get("conditions") or []),
        "interventions": interventions_of(study),
        "raw_text": raw_text,
        "evidence_text": build_evidence_text(study),
        "content_hash": content_hash(raw_text),
    }


def order_refs(records: Sequence[dict[str, Any]], priority: Sequence[str] = ()) -> list[str]:
    """The scope's `priority_refs` (NCT IDs or source refs) that were found, in their listed order,
    then the rest by `last_update_post_date`, newest first, ties by NCT ID."""
    ordered = sorted(records, key=lambda r: r.get("nct_id") or "")
    ordered = sorted(ordered, key=lambda r: r.get("last_update_post_date") or "", reverse=True)
    refs: list[str] = []
    for r in ordered:
        if r["source_ref"] not in refs:
            refs.append(r["source_ref"])
    first: list[str] = []
    for p in priority:
        ref = p if p.startswith(SOURCE + ":") else source_ref(p.strip().upper())
        if ref in refs and ref not in first:
            first.append(ref)
    return first + [r for r in refs if r not in first]
