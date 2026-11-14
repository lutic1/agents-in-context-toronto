"""The read model: accepted knowledge of one Diagnostic, and proposals (A14; Stories 1.1, 2.2).

Every endpoint that returns Record data builds it here (AD-6); the web app applies no display
rule of its own.

Accepted knowledge (AD-27, V5, V10):
- A value entry is returned only when it passed the Evidence check (`quote_found` and
  `supported`) or is manually sourced. A failed entry is never returned.
- Only applied entries are accepted knowledge: an entry whose state is not `current`,
  `superseded` or `rejected`, or whose `proposal_id` the Diagnostic has not applied, is never
  returned. Pending proposals live in `proposals` and are never mixed in. Pending reports are
  a query on `reports` (`GET /reports?status=pending`, A19+A20), not a field of the Record.
- Superseded and rejected entries stay, labelled by `state`, with their reason and decider:
  history is never deleted (Story 2.3).
- Version pinning (V40): Evidence is read from the entry as it was reviewed or accepted. When a
  data date is missing it is read from the pinned `source_versions[version_id]`, never from
  `source_items.current_version_id`.
- `raw_text` is never returned (AD-6): the shapes carry quotes only.

Proposals (Story 2.2, D42, D47, V43): `notification` is built at read time from the
`notify_slack` action of the proposal's report and is never written to the proposal. A
scope-collection proposal has `diagnostic_id: null` and `target.scope_id`.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from dxp import store
from dxp.api.models import Proposal, ProposalNotification, Record, RecordField, Value
from dxp.schema import registry

log = logging.getLogger("dxp.search.readmodel")

ACCEPTED_STATES = frozenset({"current", "superseded", "rejected"})
PROPOSAL_STATUSES = frozenset({"pending", "applying", "applied", "rejected"})
PROPOSAL_LIMIT = 500

# Display names of the AD-3 `source` strings, used when an entry does not carry one.
SOURCE_NAMES = {
    "clinicaltrials.gov": "ClinicalTrials.gov",
    "fda_cdx_list": "FDA list of cleared or approved companion diagnostic devices",
    "pubmed": "PubMed",
    "openfda_device_pma": "openFDA device PMA",
}


# ---------------------------------------------------------------------------
# Accepted knowledge of one Diagnostic (Story 1.1, formerly A18)
# ---------------------------------------------------------------------------


def passed(entry: dict[str, Any]) -> bool:
    """True when the entry passed the Evidence check or is manually sourced (AD-6)."""
    if entry.get("review") == "manual" or (entry.get("evidence") or {}).get("manual") is True:
        return True
    check = entry.get("check") or {}
    return check.get("quote_found") is True and check.get("supported") is True


def accepted(entry: dict[str, Any], applied_proposal_ids: Iterable[str]) -> bool:
    """True when the entry is applied knowledge, never a pending value (V5)."""
    if entry.get("state") not in ACCEPTED_STATES:
        return False
    proposal_id = entry.get("proposal_id")
    return proposal_id is None or proposal_id in applied_proposal_ids


def source_name(source_ref: str | None) -> str | None:
    if not source_ref or ":" not in source_ref:
        return None
    prefix = source_ref.split(":", 1)[0]
    return SOURCE_NAMES.get(prefix, prefix)


def source_url(source_ref: str | None) -> str | None:
    if source_ref and source_ref.startswith("clinicaltrials.gov:"):
        return f"https://clinicaltrials.gov/study/{source_ref.split(':', 1)[1]}"
    return None


def _date_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


async def _pinned_dates(version_ids: set[str]) -> dict[str, str | None]:
    """The data date of each pinned source version (V40). raw_text is never read."""
    if not version_ids:
        return {}
    cursor = store.get_db()["source_versions"].find(
        {"_id": {"$in": sorted(version_ids)}}, {"last_update_post_date": 1, "fetched_at": 1}
    )
    dates: dict[str, str | None] = {}
    async for doc in cursor:
        dates[doc["_id"]] = _date_text(doc.get("last_update_post_date") or doc.get("fetched_at"))
    return dates


def _evidence(evidence: dict[str, Any], pinned_dates: dict[str, str | None]) -> dict[str, Any]:
    if evidence.get("manual") is True:
        return {"manual": True, "submitter": evidence.get("submitter"), "note": evidence.get("note")}
    source_ref = evidence.get("source_ref")
    source_date = _date_text(evidence.get("source_date"))
    if source_date is None and evidence.get("version_id"):
        source_date = pinned_dates.get(evidence["version_id"])
    return {
        "source_ref": source_ref,
        "version_id": evidence.get("version_id"),
        "source": evidence.get("source") or source_name(source_ref),
        "source_url": evidence.get("source_url") or source_url(source_ref),
        "source_date": source_date,
        "quote": evidence.get("quote"),
        "data_as_of": source_date,
    }


def _value(entry: dict[str, Any], pinned_dates: dict[str, str | None]) -> Value | None:
    data = {key: entry.get(key) for key in Value.model_fields if key in entry}
    data["evidence"] = _evidence(entry.get("evidence") or {}, pinned_dates)
    try:
        return Value.model_validate(data)
    except ValidationError as exc:
        # A malformed entry is left out rather than shown half-built.
        log.warning("value %s left out of the read model (%d errors)", entry.get("value_id"), exc.error_count())
        return None


def build_record(doc: dict[str, Any], pinned_dates: dict[str, str | None] | None = None) -> Record:
    """Build the accepted-knowledge Record from a `diagnostics` document."""
    pinned_dates = pinned_dates or {}
    applied = set(doc.get("applied_proposal_ids") or [])
    stored = doc.get("fields") or {}
    keys = list(registry.FIELD_KEYS) + sorted(k for k in stored if k not in registry.FIELDS)
    fields: dict[str, RecordField] = {}
    for key in keys:
        values = []
        for entry in stored.get(key) or []:
            if not (passed(entry) and accepted(entry, applied)):
                continue
            value = _value(entry, pinned_dates)
            if value is not None:
                values.append(value)
        # History stays in `values`; no_data means no current accepted value.
        fields[key] = RecordField(values=values, no_data=not any(v.state == "current" for v in values))
    stage = doc.get("lifecycle_stage") or registry.NOT_DETERMINED
    return Record(
        id=doc["_id"],
        name=doc.get("name") or doc["_id"],
        lifecycle_stage=stage,
        early_research=registry.is_early_research(stage),
        created_mode=doc.get("created_mode"),
        rev=doc.get("rev"),
        synthetic=bool(doc.get("synthetic", False)),
        applied_proposal_ids=list(doc.get("applied_proposal_ids") or []),
        fields=fields,
    )


def _versions_without_date(doc: dict[str, Any]) -> set[str]:
    versions = set()
    for entries in (doc.get("fields") or {}).values():
        for entry in entries or []:
            evidence = entry.get("evidence") or {}
            if evidence.get("version_id") and not evidence.get("source_date"):
                versions.add(evidence["version_id"])
    return versions


async def get_diagnostic(dx_id: str) -> Record | None:
    """Accepted knowledge only: passed or manual entries, no_data on empty fields, data_as_of. None if unknown."""
    doc = await store.get_db()["diagnostics"].find_one({"_id": dx_id})
    if doc is None:
        return None
    return build_record(doc, await _pinned_dates(_versions_without_date(doc)))


# ---------------------------------------------------------------------------
# Proposals (Story 2.2, D42, D47)
# ---------------------------------------------------------------------------


def _current_value(field: str, diagnostic: dict[str, Any] | None) -> Any:
    """The field's current accepted value(s) on the Diagnostic now: a string for a single field, a list for a list field."""
    if diagnostic is None:
        return None
    applied = set(diagnostic.get("applied_proposal_ids") or [])
    entries = [
        e
        for e in (diagnostic.get("fields") or {}).get(field) or []
        if e.get("state") == "current" and passed(e) and accepted(e, applied)
    ]
    values = [e.get("value") for e in entries]
    try:
        single = registry.get_field(field).cardinality == "single"
    except KeyError:
        single = len(values) <= 1
    if single:
        return values[0] if values else None
    return values


async def _by_id(collection: str, ids: set[str], projection: dict[str, int] | None = None) -> dict[str, dict]:
    if not ids:
        return {}
    cursor = store.get_db()[collection].find({"_id": {"$in": sorted(ids)}}, projection)
    return {doc["_id"]: doc async for doc in cursor}


async def _notifications(report_ids: set[str], proposal_ids: set[str]) -> dict[str, ProposalNotification]:
    """The `notify_slack` action of each report (one per report, V11), keyed by report ID; a
    proposal without a report falls back to an action targeting the proposal. Read time only (D47)."""
    clauses = []
    if report_ids:
        clauses.append({"target.report_id": {"$in": sorted(report_ids)}})
    if proposal_ids:
        clauses.append({"target.proposal_id": {"$in": sorted(proposal_ids)}})
    if not clauses:
        return {}
    query: dict[str, Any] = {"kind": "notify_slack"}
    if len(clauses) == 1:
        query.update(clauses[0])
    else:
        query["$or"] = clauses
    found: dict[str, ProposalNotification] = {}
    async for action in store.get_db()["actions"].find(query):
        target = action.get("target") or {}
        note = ProposalNotification(
            action_id=action["_id"],
            status=action.get("status") or "queued",
            posted_at=(action.get("result") or {}).get("posted_at"),
        )
        for key in (target.get("report_id"), target.get("proposal_id")):
            if key and key not in found:
                found[key] = note
    return found


def _collection_ref(doc: dict[str, Any]) -> str | None:
    return (doc.get("evidence") or {}).get("source_ref") or doc.get("value")


def _order(item: tuple[Proposal, datetime | None]) -> tuple[int, float]:
    """Low-confidence first, then newest first (Story 2.2)."""
    proposal, created = item
    confidence = proposal.check.confidence if proposal.check else None
    low = 0 if registry.is_low_confidence(confidence) else 1
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return low, -(created.timestamp() if created else 0.0)


async def build_proposals(docs: list[dict[str, Any]]) -> list[Proposal]:
    """Read-time Proposal shapes with diagnostic name, current value and notification (D29, D47)."""
    diagnostics = await _by_id(
        "diagnostics", {d["diagnostic_id"] for d in docs if d.get("diagnostic_id")}, {"name": 1, "fields": 1, "applied_proposal_ids": 1}
    )
    collection_refs = {
        _collection_ref(d) for d in docs if not d.get("diagnostic_id") and (d.get("target") or {}).get("scope_id")
    }
    source_items = await _by_id("source_items", {r for r in collection_refs if r}, {"collections": 1})
    pinned = await _pinned_dates(
        {
            (d.get("evidence") or {}).get("version_id")
            for d in docs
            if (d.get("evidence") or {}).get("version_id") and not (d.get("evidence") or {}).get("source_date")
        }
    )
    notifications = await _notifications(
        {d["report_id"] for d in docs if d.get("report_id")},
        {d["_id"] for d in docs if not d.get("report_id")},
    )

    built: list[tuple[Proposal, datetime | None]] = []
    for doc in docs:
        dx = diagnostics.get(doc.get("diagnostic_id") or "")
        scope_id = (doc.get("target") or {}).get("scope_id")
        data = {key: doc.get(key) for key in Proposal.model_fields if key in doc}
        data["id"] = doc["_id"]
        data["diagnostic_name"] = doc.get("diagnostic_name") or (dx or {}).get("name")
        data["target"] = {"scope_id": scope_id} if doc.get("diagnostic_id") is None and scope_id else None
        if doc.get("status") == "pending":
            if doc.get("diagnostic_id"):
                data["current_value"] = _current_value(doc.get("field", ""), dx)
            elif scope_id:
                entry = ((source_items.get(_collection_ref(doc)) or {}).get("collections") or {}).get(scope_id)
                data["current_value"] = (entry or {}).get("status")
        if doc.get("evidence") is not None:
            data["evidence"] = _evidence(doc["evidence"], pinned)
        data["notification"] = notifications.get(doc.get("report_id") or doc["_id"])
        try:
            proposal = Proposal.model_validate(data)
        except ValidationError as exc:
            log.warning("proposal %s left out of the read model (%d errors)", doc.get("_id"), exc.error_count())
            continue
        created = doc.get("created_at")
        built.append((proposal, created if isinstance(created, datetime) else None))

    built.sort(key=_order)
    return [proposal for proposal, _ in built]


async def list_proposals(
    status: str | None = None,
    field: str | None = None,
    diagnostic_id: str | None = None,
    run_id: str | None = None,
    report_id: str | None = None,
) -> list[Proposal]:
    """Proposals matching every filter given. Raises ValueError for an unknown status."""
    if status and status not in PROPOSAL_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(PROPOSAL_STATUSES))}.")
    filters = {
        "status": status,
        "field": field,
        "diagnostic_id": diagnostic_id,
        "run_id": run_id,
        "report_id": report_id,
    }
    query = {key: value for key, value in filters.items() if value}
    docs = await store.get_db()["proposals"].find(query).to_list(length=PROPOSAL_LIMIT)
    return await build_proposals(docs)


async def get_proposal(p_id: str) -> Proposal | None:
    """One proposal, whatever its status; None if unknown (D42)."""
    doc = await store.get_db()["proposals"].find_one({"_id": p_id})
    if doc is None:
        return None
    built = await build_proposals([doc])
    return built[0] if built else None
