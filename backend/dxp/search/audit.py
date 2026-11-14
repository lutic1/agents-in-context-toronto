"""The run audit with the V14 sections (AD-22), reconstructed from stored documents alone.
Finished by A07+A11. No signature is frozen here; no model call is made.

Sources: `decisions`, `actions`, `events` (through `Decision.seq`), `runs`, `policy_sets`,
`policies`, `grants` (at the version a decision recorded), `reports` (with `related[]`),
`proposals` and `tasks`, plus `source_items` for the sources fetched. Nothing is recomputed from
current grants or policies: "who authorised" is the Decision's `authorised_by`, and a missing one
is rebuilt from the grant at the decision's evaluated version. `proposal_review` and
`report_review` are read live at request time. No `raw_text` is ever returned.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from dxp import store
from dxp.api.errors import ApiError
from dxp.api.models import Action, Audit, AuditEntry, Decision, LinkedRun, Policy, Run
from dxp.runs.common import aware
from dxp.runs.views import view as run_view

#: Keys never returned from a stored document (V40: source raw text stays in Atlas).
HIDDEN_KEYS = frozenset({"raw_text"})


def scrub(value: Any) -> Any:
    """Drop `raw_text` at any depth."""
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items() if key not in HIDDEN_KEYS}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def _api_doc(doc: dict[str, Any]) -> dict[str, Any]:
    data = scrub({key: value for key, value in doc.items() if key != "_id"})
    data["id"] = doc["_id"]
    return data


def _order(doc: dict[str, Any]) -> tuple[int, datetime, str]:
    """Decision order (D21): by seq; a decision without one yet goes last, by time."""
    seq = doc.get("seq")
    decided = aware(doc.get("decided_at")) or datetime.max.replace(tzinfo=UTC)
    return (seq if isinstance(seq, int) else 2**62, decided, doc["_id"])


async def _by_id(collection: str, ids: list[str]) -> dict[str, dict[str, Any]]:
    wanted = sorted({i for i in ids if i})
    if not wanted:
        return {}
    docs = await store.collection(collection).find({"_id": {"$in": wanted}}).to_list(length=None)
    return {doc["_id"]: doc for doc in docs}


# ---------------------------------------------------------------------------
# "Who authorised" (AD-22)
# ---------------------------------------------------------------------------


async def authorised_by(decision: dict[str, Any]) -> dict[str, Any] | None:
    """The Decision's stored `authorised_by`; if absent, rebuilt from the grant at the version the
    decision evaluated and its policy-set version, never from the current grant."""
    stored = decision.get("authorised_by")
    if stored:
        return stored
    grant_id, version = decision.get("grant_id"), decision.get("grant_version")
    grant = None
    if grant_id and version:
        grant = await store.collection("grants").find_one({"_id": f"{grant_id}@v{int(version)}"})
    if not grant_id or not version:
        return None
    stamp = decision.get("stamp") or {}
    return {
        "principal": stamp.get("principal") or (grant or {}).get("principal") or decision.get("initiated_by"),
        "initiated_by": decision.get("initiated_by"),
        "acting_for": (grant or {}).get("acting_for"),
        "granted_by": (grant or {}).get("granted_by"),
        "grant_id": grant_id,
        "grant_version": int(version),
        "expires_at": (grant or {}).get("expires_at"),
        "policy_set_version": decision.get("policy_set_version"),
    }


# ---------------------------------------------------------------------------
# Decisions and actions
# ---------------------------------------------------------------------------


async def decision_detail(decision_id: str) -> Decision:
    """`GET /decisions/<decision_id>`: any decision, allowed or blocked, with `authorised_by`."""
    doc = await store.collection("decisions").find_one({"_id": decision_id})
    if doc is None:
        raise ApiError(404, "decision_not_found", f"No decision {decision_id}.")
    data = _api_doc(doc)
    data["authorised_by"] = await authorised_by(doc)
    return Decision.model_validate(data)


async def _reconciling(actions: list[dict[str, Any]], at: datetime | None = None) -> set[str]:
    """Dispatching actions the sweep is settling: their admission is abandoned, or admitted
    past its lease (D24). `reconciling` is never stored."""
    dispatching = [a for a in actions if a.get("status") == "dispatching" and a.get("admission_id")]
    if not dispatching:
        return set()
    at = at or datetime.now(UTC)
    admissions = await _by_id("admissions", [a["admission_id"] for a in dispatching])
    settling: set[str] = set()
    for action in dispatching:
        adm = admissions.get(action["admission_id"])
        if adm is None:
            continue
        expired = adm.get("status") == "admitted" and (aware(adm.get("expires_at")) or at) < at
        if adm.get("status") == "abandoned" or expired:
            settling.add(action["_id"])
    return settling


async def _action_models(docs: list[dict[str, Any]]) -> list[Action]:
    settling = await _reconciling(docs)
    missing = [d["decision_id"] for d in docs if not d.get("authorised_by") and d.get("decision_id")]
    decisions = await _by_id("decisions", missing)
    models = []
    for doc in docs:
        data = _api_doc(doc)
        if doc["_id"] in settling:
            data["status"] = "reconciling"
        if not data.get("authorised_by") and doc.get("decision_id") in decisions:
            data["authorised_by"] = await authorised_by(decisions[doc["decision_id"]])
        models.append(Action.model_validate(data))
    return models


async def action_detail(action_id: str) -> Action:
    doc = await store.collection("actions").find_one({"_id": action_id})
    if doc is None:
        raise ApiError(404, "action_not_found", f"No action {action_id}.")
    return (await _action_models([doc]))[0]


async def list_actions(run_id: str | None = None, status: str | None = None, limit: int = 500) -> list[Action]:
    """`GET /actions?run_id=&status=`; `status=reconciling` lists dispatching actions the sweep is settling."""
    query: dict[str, Any] = {}
    if run_id:
        query["run_id"] = run_id
    if status:
        query["status"] = "dispatching" if status == "reconciling" else status
    docs = (
        await store.collection("actions")
        .find(query)
        .sort([("proposed_at", 1), ("_id", 1)])
        .limit(limit)
        .to_list(length=limit)
    )
    models = await _action_models(docs)
    if status == "dispatching":
        models = [a for a in models if a.status == "dispatching"]
    elif status == "reconciling":
        models = [a for a in models if a.status == "reconciling"]
    return models


# ---------------------------------------------------------------------------
# The run audit
# ---------------------------------------------------------------------------


def _review(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None or not doc.get("status"):
        return None
    return {"status": doc["status"], "decided_by": doc.get("decided_by"), "decided_at": doc.get("decided_at")}


def _report_id(decision: dict[str, Any], action: dict[str, Any] | None) -> str | None:
    target = decision.get("target") or {}
    evidence = decision.get("evidence_ref") or {}
    cause = decision.get("cause") or {}
    result = (action or {}).get("result") or {}
    return target.get("report_id") or evidence.get("report_id") or cause.get("report_id") or result.get("report_id")


def _relationships(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    related = []
    for rel in (report or {}).get("related") or []:
        item = scrub(dict(rel))
        if "id" not in item and "_id" in item:
            item["id"] = item.pop("_id")
        related.append(item)
    return related


def _scan(decision: dict[str, Any], action: dict[str, Any] | None, run: dict[str, Any]) -> dict[str, Any] | None:
    """search_source entries: the cursor before and after and the refs fetched (V14)."""
    if decision.get("kind") != "search_source":
        return None
    result = (action or {}).get("result") or {}
    if any(key in result for key in ("cursor_from", "cursor_to", "source_refs")):
        return {
            "cursor_from": result.get("cursor_from"),
            "cursor_to": result.get("cursor_to"),
            "source_refs": list(result.get("source_refs") or []),
        }
    scan = run.get("scan")
    if scan:
        return {
            "cursor_from": scan.get("cursor_from"),
            "cursor_to": scan.get("cursor_to"),
            "source_refs": list(scan.get("source_refs") or []),
        }
    inputs = decision.get("inputs") or {}
    if "cursor" in inputs:
        return {"cursor_from": inputs.get("cursor"), "cursor_to": None, "source_refs": []}
    return None


def _entry(
    decision: dict[str, Any],
    authorised: dict[str, Any] | None,
    action: dict[str, Any] | None,
    reconciling: bool,
    proposals: dict[str, dict[str, Any]],
    reports: dict[str, dict[str, Any]],
    run: dict[str, Any],
) -> AuditEntry:
    target = decision.get("target") or {}
    evidence = decision.get("evidence_ref") or {}
    report_id = _report_id(decision, action)
    report = reports.get(report_id) if report_id else None
    proposal_id = target.get("proposal_id") or evidence.get("proposal_id")
    report_level = decision.get("kind") == "file_proposal" and report_id and not target.get("proposal_id")
    status = (action or {}).get("status")
    if reconciling and status == "dispatching":
        status = "reconciling"
    entry = {
        "seq": decision.get("seq"),
        "decision_id": decision["_id"],
        "outcome": decision["outcome"],
        "failed_check": decision.get("failed_check"),
        "checks": decision.get("checks") or [],
        "kind": decision["kind"],
        "destination": decision.get("destination"),
        "inputs": scrub(decision.get("inputs") or {}),
        "evidence_ref": scrub(evidence) if evidence else None,
        "stamp": decision.get("stamp"),
        "cause": decision.get("cause"),
        "grant_id": decision.get("grant_id"),
        "grant_version": decision.get("grant_version") or decision.get("run_grant_version") or 0,
        "policy_set_version": decision.get("policy_set_version"),
        "action_id": decision.get("action_id") or (action or {}).get("_id"),
        "status": status,
        "result": scrub((action or {}).get("result")) if action else None,
        "resolution": (action or {}).get("resolution"),
        "decided_at": decision.get("decided_at"),
        "claimed_at": (action or {}).get("claimed_at"),
        "observed_at": (action or {}).get("observed_at"),
        "authorised_by": authorised,
        "proposal_review": _review(proposals.get(proposal_id)) if proposal_id else None,
        "report_id": report_id,
        "task_id": target.get("task_id") or (decision.get("cause") or {}).get("task_id"),
        "memory_id": target.get("memory_id") or (decision.get("cause") or {}).get("memory_id"),
        "claims": decision.get("claims") or [],
        "scan": _scan(decision, action, run),
        "retrieval": decision.get("retrieval"),
        "memories_used": decision.get("memories_used") or [],
        "relationships": _relationships(report) if report_level and decision["outcome"] == "allowed" else [],
        "report_review": _review(report) if report is not None else None,
    }
    return AuditEntry.model_validate(entry)


async def _entries(decisions: list[dict[str, Any]], run: dict[str, Any]) -> list[AuditEntry]:
    decisions = sorted(decisions, key=_order)
    actions = await _by_id("actions", [d.get("action_id") for d in decisions])
    settling = await _reconciling(list(actions.values()))
    proposal_ids, report_ids = [], []
    for d in decisions:
        target, evidence = d.get("target") or {}, d.get("evidence_ref") or {}
        proposal_ids += [target.get("proposal_id"), evidence.get("proposal_id")]
        report_ids.append(_report_id(d, actions.get(d.get("action_id"))))
    proposals = await _by_id("proposals", proposal_ids)
    reports = await _by_id("reports", report_ids)
    entries = []
    for d in decisions:
        action = actions.get(d.get("action_id"))
        entries.append(
            _entry(d, await authorised_by(d), action, bool(action and action["_id"] in settling), proposals, reports, run)
        )
    return entries


async def _policies(policy_set_version: str | None) -> list[Policy]:
    """The run's pinned policies, rebuilt from `policy_sets` (AD-18, AD-22)."""
    if not policy_set_version:
        return []
    policy_set = await store.collection("policy_sets").find_one({"_id": policy_set_version})
    members = list((policy_set or {}).get("members") or [])
    stored = await _by_id("policies", members)
    return [Policy.model_validate(_api_doc(stored[m])) for m in members if m in stored]


def _date_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


async def _sources(run: dict[str, Any], decisions: list[dict[str, Any]], actions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """The sources fetched (V14): the scan's refs, then each search's refs, then the setup item,
    then the items the run reported on, in that order, each once."""
    refs: list[str] = []
    refs += list((run.get("scan") or {}).get("source_refs") or [])
    for d in sorted(decisions, key=_order):
        if d.get("kind") == "search_source":
            refs += list((((actions.get(d.get("action_id")) or {}).get("result")) or {}).get("source_refs") or [])
    set_value = run.get("set") or ""
    if set_value.startswith("nct:"):
        refs.append(f"clinicaltrials.gov:{set_value.removeprefix('nct:')}")
    reports = await store.collection("reports").find({"run_id": run["_id"]}, {"source_ref": 1}).to_list(length=None)
    refs += [r["source_ref"] for r in reports if r.get("source_ref")]
    ordered = list(dict.fromkeys(r for r in refs if r))
    if not ordered:
        return []
    items = await store.collection("source_items").find(
        {"$or": [{"_id": {"$in": ordered}}, {"source_ref": {"$in": ordered}}]},
        {"_id": 1, "source_ref": 1, "window": 1, "source_date": 1, "last_update_posted": 1},
    ).to_list(length=None)
    by_ref = {item.get("source_ref") or item["_id"]: item for item in items}
    sources = []
    for ref in ordered:
        item = by_ref.get(ref) or {}
        sources.append({
            "source_ref": ref,
            "window": item.get("window"),
            "source_date": _date_text(item.get("source_date") or item.get("last_update_posted")),
        })
    return sources


async def _linked_runs(run_id: str) -> list[LinkedRun]:
    """Task runs authorised from this run's reports (V14, V38)."""
    report_ids = await store.collection("reports").distinct("_id", {"run_id": run_id})
    if not report_ids:
        return []
    task_ids = await store.collection("tasks").distinct("_id", {"report_id": {"$in": report_ids}})
    if not task_ids:
        return []
    runs = await store.collection("runs").find({"task_id": {"$in": task_ids}}).sort("started_at", 1).to_list(length=None)
    return [LinkedRun(run_id=r["_id"], task_id=r["task_id"], status=r["status"]) for r in runs]


async def run_audit(run_id: str) -> Audit:
    """`GET /runs/<run_id>/audit`: the run, its pinned policies, the sources fetched, every
    decision of the run in seq order, then "After the run" and the linked task runs."""
    run = await store.collection("runs").find_one({"_id": run_id})
    if run is None:
        raise ApiError(404, "run_not_found", f"No run {run_id}.")
    decisions = await store.collection("decisions").find({"run_id": run_id}).to_list(length=None)
    after = await store.collection("decisions").find(
        {"cause.origin_run_id": run_id, "run_id": {"$ne": run_id}}
    ).to_list(length=None)
    actions = await _by_id("actions", [d.get("action_id") for d in decisions])
    run_model: Run = await run_view(run)
    return Audit(
        run=run_model,
        policies=await _policies(run.get("policy_set_version")),
        sources=await _sources(run, decisions, actions),
        entries=await _entries(decisions, run),
        after_run=await _entries(after, run),
        linked_runs=await _linked_runs(run_id),
    )
