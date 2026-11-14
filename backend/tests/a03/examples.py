"""Example documents for the A03 tests: one valid document per collection and
the seeded grants, policies and scope built by `gate.seed` with test keys.

`TEST_CURSOR` is a test-only value. The real cursor is Luis's 10:45 choice (OD2),
which is in `gate/seed_data/research_scopes.json` (2026-11-11).
"""

from __future__ import annotations

import copy
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from dxp import identity
from dxp.gate import seed

TEST_CURSOR = "2000-01-01"  # test-only placeholder, not the OD2 cursor
NOW = datetime(2026, 11, 14, 15, 0, tzinfo=UTC)


def h(prefix: str, *parts: str) -> str:
    return identity.derive(prefix, *parts)


def seed_data_dir(tmp_path: Path, cursor: str | None = TEST_CURSOR) -> Path:
    """A copy of `gate/seed_data/` with the test cursor filled in."""
    target = tmp_path / "seed_data"
    shutil.copytree(seed.SEED_DATA, target)
    scopes_file = target / "research_scopes.json"
    data = json.loads(scopes_file.read_text(encoding="utf-8"))
    data["research_scopes"][0]["cursor"]["last_update_post_date"] = cursor
    scopes_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return target


def seeded(tmp_path: Path, keys: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    return seed.build_all(seed.load_seed_data(seed_data_dir(tmp_path)), keys, NOW)


def by_id(docs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {d["_id"]: d for d in docs}


def task_grant(lbdx: dict[str, Any], version: int = 1, status: str = "active", **overrides: Any) -> dict[str, Any]:
    """A task grant as AD-18 describes it (A24 writes the real one)."""
    task_id = h("task_", h("rep_", "run_x", "clinicaltrials.gov:NCT04712877"))
    hexpart = task_id[len("task_") :]
    doc = {
        "_id": f"task-{hexpart}@v{version}",
        "grant_id": f"task-{hexpart}",
        "version": version,
        "principal": "dxp-curator",
        "kind": "agent",
        "key_hash": None,
        "acting_for": lbdx["acting_for"],
        "granted_by": "sam",
        "startable_by": ["sam"],
        "team_id": lbdx["team_id"],
        "scope": copy.deepcopy(lbdx["scope"]),
        "destinations": ["source:clinicaltrials.gov", "ledger"],
        "actions": ["search_source", "file_related_evidence"],
        "limits": {"max_results": 5},
        "task_id": task_id,
        "expires_at": NOW + timedelta(hours=1),
        "status": status,
        "created_at": NOW,
    }
    doc.update(overrides)
    return doc


STAMP_REVIEWER = {
    "kind": "reviewer",
    "principal": "sam",
    "run_id": None,
    "agent": None,
    "initiated_by": "sam",
    "grant_id": "sam",
    "grant_version": 1,
    "policy_set_version": "ps_" + "a" * 16,
}
STAMP_RUN = {
    "kind": "run",
    "principal": "dxp-curator",
    "run_id": "run_abc123",
    "agent": "dxp-curator",
    "initiated_by": "sam",
    "grant_id": "lbdx",
    "grant_version": 1,
    "policy_set_version": "ps_" + "a" * 16,
}

SV = "sv_" + "1" * 16
REP = "rep_" + "2" * 16
DEC = "dec_" + "3" * 16
ACT = "act_" + "4" * 16
TASK = "task_" + "5" * 16
MEM = "mem_" + "6" * 16
P = "p_" + "7" * 16


def quote(found: bool) -> dict[str, Any]:
    return {"source_ref": "clinicaltrials.gov:NCT04712877", "version_id": SV, "text": "ctDNA", "quote_found": found}


def valid_documents() -> dict[str, dict[str, Any]]:
    """One valid document for each collection with a validator (besides the seeded ones)."""
    return {
        "policy_sets": {"_id": "ps_" + "a" * 16, "members": ["claim_planned@v1"], "created_at": NOW},
        "runs": {
            "_id": "run_abc123",
            "agent": "dxp-curator",
            "initiated_by": "sam",
            "grant_id": "lbdx",
            "grant_version": 1,
            "policy_set_version": "ps_" + "a" * 16,
            "team_id": "team_" + "8" * 16,
            "set": "discover",
            "kind": "discover",
            "scope_id": "scope_plasma_ctdna_nsclc",
            "task_id": None,
            "status": "running",
            "in_flight": 0,
            "started_at": NOW,
        },
        "admissions": {
            "_id": "adm_" + "9" * 16,
            "run_id": "run_abc123",
            "item_key": "clinicaltrials.gov:NCT04712877",
            "status": "admitted",
            "admitted_at": NOW,
            "expires_at": NOW + timedelta(minutes=5),
            "released_at": None,
        },
        "decisions": {
            "_id": DEC,
            "run_id": None,
            "agent": None,
            "initiated_by": "sam",
            "stamp": STAMP_REVIEWER,
            "cause": {"report_id": REP, "origin_run_id": "run_abc123"},
            "request_id": "req_1",
            "kind": "revert_report",
            "destination": "ledger",
            "checks": [
                {"check": "grant_active", "passed": True, "detail": None},
                {"check": "evidence_checks", "passed": "n/a", "detail": None},
            ],
            "claims": [],
            "failed_check": None,
            "grant_id": "sam",
            "grant_version": 1,
            "policy_set_version": "ps_" + "a" * 16,
            "outcome": "allowed",
            "action_id": ACT,
            "seq": 7,
            "decided_at": NOW,
        },
        "actions": {
            "_id": ACT,
            "decision_id": DEC,
            "run_id": "run_abc123",
            "kind": "notify_slack",
            "destination": "slack:#all-mango-db-hackathon",
            "status": "unknown",
            "stamp": STAMP_RUN,
            "error": "abandoned_in_flight",
            "result": None,
            "resolution": None,
            "proposed_at": NOW,
        },
        "proposals": {
            "_id": P,
            "op": "add",
            "reverts_proposal_id": None,
            "diagnostic_id": None,
            "target": {"scope_id": "scope_plasma_ctdna_nsclc"},
            "field": "collections",
            "status": "pending",
            "mode": "live",
            "run_id": "run_abc123",
            "report_id": REP,
            "decision_id": DEC,
            "stamp": STAMP_RUN,
        },
        "reports": {
            "_id": REP,
            "run_id": "run_abc123",
            "scope_id": "scope_plasma_ctdna_nsclc",
            "team_id": "team_" + "8" * 16,
            "source_ref": "clinicaltrials.gov:NCT04712877",
            "version_id": SV,
            "status": "reverted",
            "revert": {"decision_id": DEC, "note": "wrong trial", "step": "done"},
            "related": [
                {
                    "_id": "rel_" + "a" * 16,
                    "related_ref": "clinicaltrials.gov:NCT00000001",
                    "related_kind": "source_item",
                    "label": "extends",
                    "new_quote": quote(True),
                    "related_quote": quote(True),
                    "origin": "discovery",
                    "status": "reverted",
                },
                {
                    "_id": "rel_" + "b" * 16,
                    "related_ref": "clinicaltrials.gov:NCT00000002",
                    "label": "related_unestablished",
                    "new_quote": quote(True),
                    "related_quote": quote(False),
                    "origin": f"task:{TASK}",
                    "status": "pending",
                },
            ],
            "uncertainties": ["The record names 'FoundationOne Liquid'."],
            "gap": "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?",
            "diagnostic_ids": [],
            "draft": 2,
            "approval": {"decision_id": DEC, "task_id": TASK, "task_step": "done"},
            "stamp": STAMP_RUN,
            "created_at": NOW,
        },
        "memories": {
            "_id": f"{MEM}@v2",
            "memory_id": MEM,
            "version": 2,
            "team_id": "team_" + "8" * 16,
            "author": "sam",
            "source": {"decision_id": DEC, "report_id": REP},
            "text": "Terminated trial with no posted results: describe its status; do not state outcomes",
            "tags": {"assay": None, "claim_kind": "claim_performed_or_results"},
            "status": "active",
            "supersedes": f"{MEM}@v1",
            "decision_id": DEC,
            "created_at": NOW,
        },
        "tasks": {
            "_id": TASK,
            "report_id": REP,
            "kind": "search_related",
            "question": "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?",
            "params": {"condition": "non-small cell lung cancer", "stage": "early", "has_results": True, "max": 5},
            "grant_id": "task-" + "5" * 16,
            "grant_version": 1,
            "status": "cancelled",
            "error": None,
            "run_id": None,
            "authorised_by_decision_id": DEC,
            "result": None,
            "created_at": NOW,
        },
        "media": {
            "_id": "media_" + "c" * 16,
            "report_id": REP,
            "kind": "avatar_video",
            "provider": "heygen",
            "status": "rendering",
            "video_url": None,
            "decision_id": DEC,
            "created_at": NOW,
        },
        "source_versions": {
            "_id": SV,
            "source_ref": "clinicaltrials.gov:NCT04712877",
            "last_update_post_date": "2026-11-12",
            "content_hash": "d" * 16,
            "raw_text": "test text",
            "evidence_text": "test text",
            "overall_status": "RECRUITING",
            "has_results": False,
            "interventions": [{"name": "ctDNA, tumor NGS", "other_names": ["FoundationOne CDx"]}],
            "previous_version_id": None,
            "fetched_at": NOW,
        },
    }


def _set(doc: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    doc = copy.deepcopy(doc)
    target = doc
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part] if not part.isdigit() else target[int(part)]
    last = parts[-1]
    if value is DELETE:
        del target[last]
    else:
        target[last] = value
    return doc


DELETE = object()

# (collection, path, bad value, why): each must be rejected.
BAD_CHANGES: list[tuple[str, str, Any, str]] = [
    ("policy_sets", "_id", "ps_short", "policy set version is not a ps_ hash"),
    ("runs", "status", "paused", "unknown run status"),
    ("runs", "agent", DELETE, "a run without its agent identity"),
    ("admissions", "status", "held", "unknown admission status"),
    ("decisions", "failed_check", "team_scope", "an allowed decision naming a failed check"),
    ("decisions", "outcome", "maybe", "unknown outcome"),
    ("actions", "status", "reconciling", "reconciling is read-time only, never stored"),
    ("actions", "status", "done", "an external kind cannot be done"),
    ("proposals", "op", "remove", "a remove proposal must name reverts_proposal_id"),
    ("proposals", "op", "replace", "unknown op"),
    ("reports", "status", "approved", "unknown report status"),
    ("reports", "related.0.related_quote", quote(False), "an established label needs both quotes found (AD-26)"),
    ("memories", "supersedes", None, "a later memory version must name what it supersedes"),
    ("memories", "status", "deleted", "unknown memory status"),
    ("tasks", "status", "paused", "unknown task status"),
    ("tasks", "params.max", 6, "a task may search at most 5 records"),
    ("media", "provider", "other", "unknown provider"),
    ("source_versions", "raw_text", DELETE, "a source version keeps its raw text"),
]


def bad_document(collection: str, path: str, value: Any) -> dict[str, Any]:
    return _set(valid_documents()[collection], path, value)
