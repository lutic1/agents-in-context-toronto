"""Regular indexes for every collection, plus A03's validators (AD-18, AD-21, AD-28).

Search and vector indexes are not here: they are `retrieval.ensure_indexes()` (A19+A20).
"""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import CollectionInvalid

from dxp.store.client import get_db

# (name, keys, options). Index names are explicit so a second run is a no-op.
INDEXES: dict[str, list[IndexModel]] = {
    "grants": [
        IndexModel([("grant_id", ASCENDING), ("version", DESCENDING)], name="grant_version", unique=True),
        IndexModel([("key_hash", ASCENDING)], name="key_hash"),
        IndexModel([("task_id", ASCENDING)], name="task_id"),
    ],
    "policies": [
        IndexModel([("policy_id", ASCENDING), ("version", DESCENDING)], name="policy_version", unique=True),
        IndexModel([("status", ASCENDING)], name="status"),
    ],
    "policy_sets": [IndexModel([("created_at", DESCENDING)], name="created_at")],
    "research_scopes": [IndexModel([("team_id", ASCENDING)], name="team_id")],
    "runs": [
        IndexModel([("status", ASCENDING)], name="status"),
        IndexModel([("started_at", DESCENDING)], name="started_at"),
        IndexModel([("task_id", ASCENDING)], name="task_id"),
    ],
    "admissions": [
        IndexModel([("run_id", ASCENDING), ("item_key", ASCENDING)], name="run_item", unique=True),
        IndexModel([("run_id", ASCENDING), ("status", ASCENDING)], name="run_status"),
        IndexModel([("status", ASCENDING), ("expires_at", ASCENDING)], name="status_expires"),
    ],
    "decisions": [
        IndexModel([("run_id", ASCENDING), ("seq", ASCENDING)], name="run_seq"),
        IndexModel([("cause.origin_run_id", ASCENDING)], name="origin_run"),
        IndexModel([("target.report_id", ASCENDING)], name="target_report"),
        IndexModel([("kind", ASCENDING)], name="kind"),
    ],
    "actions": [
        IndexModel([("run_id", ASCENDING), ("status", ASCENDING)], name="run_status"),
        IndexModel([("decision_id", ASCENDING)], name="decision_id"),
        IndexModel([("status", ASCENDING)], name="status"),
        IndexModel([("target.report_id", ASCENDING), ("kind", ASCENDING)], name="report_kind"),
    ],
    "reports": [
        IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="status_created"),
        IndexModel([("run_id", ASCENDING)], name="run_id"),
        IndexModel([("scope_id", ASCENDING)], name="scope_id"),
        IndexModel([("approval.task_step", ASCENDING)], name="task_step"),
    ],
    "memories": [
        IndexModel([("memory_id", ASCENDING), ("version", ASCENDING)], name="memory_version", unique=True),
        IndexModel([("team_id", ASCENDING), ("status", ASCENDING)], name="team_status"),
    ],
    "tasks": [
        IndexModel([("report_id", ASCENDING)], name="report_id"),
        IndexModel([("status", ASCENDING), ("queued_at", ASCENDING)], name="status_queued"),
        IndexModel([("run_id", ASCENDING)], name="run_id"),
    ],
    "media": [IndexModel([("report_id", ASCENDING), ("created_at", DESCENDING)], name="report_created")],
    "audio": [IndexModel([("report_id", ASCENDING)], name="report_id")],
    "source_versions": [
        IndexModel([("source_ref", ASCENDING), ("last_update_post_date", DESCENDING)], name="source_date"),
    ],
    "source_items": [
        IndexModel([("scope_ids", ASCENDING)], name="scope_ids"),
        IndexModel([("window", ASCENDING)], name="window"),
        IndexModel([("current_version_id", ASCENDING)], name="current_version"),
    ],
    "findings": [
        IndexModel([("source_ref", ASCENDING)], name="source_ref"),
        IndexModel([("version_id", ASCENDING)], name="version_id"),
        IndexModel([("run_id", ASCENDING)], name="run_id"),
    ],
    "proposals": [
        IndexModel([("status", ASCENDING)], name="status"),
        IndexModel([("report_id", ASCENDING)], name="report_id"),
        IndexModel([("diagnostic_id", ASCENDING), ("status", ASCENDING)], name="diagnostic_status"),
        IndexModel([("run_id", ASCENDING)], name="run_id"),
    ],
    "diagnostics": [IndexModel([("applied_proposal_ids", ASCENDING)], name="applied_proposals")],
    "aliases": [IndexModel([("diagnostic_id", ASCENDING)], name="diagnostic_id")],
    "edges": [
        IndexModel([("proposal_id", ASCENDING)], name="proposal_id"),
        IndexModel([("run_id", ASCENDING)], name="run_id"),
    ],
    "events": [
        IndexModel([("dedupe_key", ASCENDING)], name="dedupe_key", unique=True),
        IndexModel([("run_id", ASCENDING), ("_id", ASCENDING)], name="run_seq"),
        IndexModel([("decision_id", ASCENDING)], name="decision_id"),
    ],
    "teams": [IndexModel([("name", ASCENDING)], name="name")],
}

COLLECTIONS: tuple[str, ...] = tuple(INDEXES)


def _validators() -> dict[str, dict]:
    """A03's `$jsonSchema` documents, keyed by collection name (store/schemas/)."""
    from dxp.store import schemas

    return dict(getattr(schemas, "VALIDATORS", {}) or {})


async def ensure_indexes() -> None:
    db = get_db()
    validators = _validators()
    existing = set(await db.list_collection_names())
    for name in sorted(set(COLLECTIONS) | set(validators)):
        schema = validators.get(name)
        options = {}
        if schema is not None:
            options = {"validator": {"$jsonSchema": schema}, "validationLevel": "strict", "validationAction": "error"}
        if name not in existing:
            try:
                await db.create_collection(name, **options)
            except CollectionInvalid:
                existing.add(name)  # created concurrently: apply below
        if name in existing and schema is not None:
            await db.command({"collMod": name, **options})
        models = INDEXES.get(name)
        if models:
            await db[name].create_indexes(models)
