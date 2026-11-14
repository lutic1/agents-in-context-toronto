"""Report filing (AD-27): the report is the pending proposal.

`file()` gates each draft as a report-level `file_proposal` (target
`<report_id>|draft<n>`, each its own Decision, V21). Only when the last draft
is allowed is anything written: the `reports` document (`pending`, with its
script, V41), one `ledger.file()` per knowledge update, the `report_filed`
event and the report's one `notify_slack` action. A blocked report writes
nothing here: the gate has recorded its Decision and event.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from dxp.api.models import Decision, EvidenceRef, ProposedAction, Report, RunContext, Target

log = logging.getLogger("dxp.reports")

SLACK_DESTINATION = "slack:#all-mango-db-hackathon"


def report_id_for(run_id: str | None, source_ref: str) -> str:
    """derive("rep_", run_id, source_ref): one report per discovered Source item per run (AD-3)."""
    from dxp import identity

    return identity.derive("rep_", run_id or "-", source_ref)


def _plain(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value or {})


def report_action(report_id: str, draft: dict[str, Any], one: dict[str, Any]) -> ProposedAction:
    """The report-level file_proposal for one draft. The claims, the source's own status
    fields and the checked quotes travel in `inputs` for check 4; the retrieval and the
    memories used are recorded on the Decision (V14)."""
    from dxp.reports.draft import gate_claims

    number = int(one.get("draft") or 1)
    return ProposedAction(
        kind="file_proposal",
        destination="ledger",
        target=Target(report_id=report_id, scope_id=draft.get("scope_id")),
        inputs={
            "draft": number,
            "id_target": f"{report_id}|draft{number}",
            "source_ref": draft.get("source_ref"),
            "headline": one.get("headline"),
            "gap": one.get("gap"),
            "claims": gate_claims(one),
            "source_fields": dict(draft.get("source_fields") or {}),
            "checked_quotes": [dict(q) for q in one.get("quotes") or []],
        },
        evidence_ref=EvidenceRef(source_ref=draft.get("source_ref"), version_id=draft.get("version_id"), report_id=report_id),
        retrieval=draft.get("retrieval") or None,
        memories_used=(draft.get("memories_used") or []) if number > 1 else [],
    )


def report_document(report_id: str, draft: dict[str, Any], ctx: RunContext, decision: Decision,
                    blocked_draft_decision_id: str | None) -> dict[str, Any]:
    """The `reports` document, validated against the frozen `Report` shape, with its script."""
    from dxp.reports.relate import relationship_id
    from dxp.reports.script import script_for, script_hash

    source_ref = draft["source_ref"]
    related = []
    for relationship in draft.get("related") or []:
        relationship = _plain(relationship)
        relationship["id"] = relationship_id(report_id, source_ref, relationship.get("related_ref"))
        related.append(relationship)
    fields = {
        "id": report_id,
        "run_id": ctx.run_id or draft.get("run_id"),
        "scope_id": draft.get("scope_id"),
        "team_id": draft.get("team_id"),
        "source_ref": source_ref,
        "version_id": draft.get("version_id"),
        "nct_id": draft.get("nct_id"),
        "headline": draft.get("headline"),
        "status_line": draft.get("status_line"),
        "discovery": draft.get("discovery"),
        "related": related,
        "uncertainties": draft.get("uncertainties") or [],
        "gap": draft.get("gap"),
        "retrieval": draft.get("retrieval") or None,
        "memories_used": draft.get("memories_used") or [],
        "proposal_ids": [],
        "diagnostic_ids": [],
        "recommended_task": draft.get("recommended_task"),
        "draft": int(draft.get("draft") or 1),
        "blocked_draft_decision_id": blocked_draft_decision_id,
        "stamp": ctx.stamp,
        "file_decision_id": decision.id,
        "status": "pending",
        "created_at": datetime.now(UTC),
    }
    script = script_for(fields)
    report = Report.model_validate({**fields, "script": script, "script_hash": script_hash(script)})
    document = report.model_dump()
    document["_id"] = document.pop("id")
    for relationship in document["related"]:
        relationship["_id"] = relationship["id"]  # the stored key of an embedded relationship
    return document


async def _refresh_proposals(reports, proposals, report_id: str) -> None:
    filed = await proposals.find({"report_id": report_id}).to_list(length=None)
    proposal_ids = sorted(str(p["_id"]) for p in filed)
    diagnostic_ids = sorted({p["diagnostic_id"] for p in filed if p.get("diagnostic_id")})
    await reports.update_one(
        {"_id": report_id}, {"$set": {"proposal_ids": proposal_ids, "diagnostic_ids": diagnostic_ids}}
    )


async def _notify(db, report_id: str, document: dict[str, Any], ctx: RunContext) -> None:
    """The report's one notify_slack action (V11). Its result is recorded by actions.dispatch;
    a failure here never undoes or blocks the report."""
    from dxp import actions

    try:
        if await db["actions"].find_one({"target.report_id": report_id, "kind": "notify_slack"}):
            return
        await actions.dispatch(
            ProposedAction(
                kind="notify_slack",
                destination=SLACK_DESTINATION,
                target=Target(report_id=report_id, scope_id=document.get("scope_id")),
                inputs={
                    "script_hash": document["script_hash"],
                    "headline": document["headline"],
                    "status_line": document.get("status_line"),
                    "source_ref": document["source_ref"],
                },
                evidence_ref=EvidenceRef(
                    source_ref=document["source_ref"], version_id=document["version_id"], report_id=report_id
                ),
            ),
            ctx,
        )
    except Exception as exc:
        log.warning("reports.file: notify_slack for %s not dispatched: %s", report_id, type(exc).__name__)


async def file(draft: dict[str, Any], ctx: RunContext) -> Decision:
    """Gate the report as a report-level file_proposal; allowed: store the report pending with its
    script (V41), ledger.file each update, one notify_slack action. Returns the Decision."""
    from dxp import gate, ledger, store

    report_id = report_id_for(ctx.run_id or draft.get("run_id"), draft["source_ref"])
    drafts = draft.get("drafts") or [draft]
    decisions: list[Decision] = []
    for one in drafts:
        decisions.append(await gate.evaluate(ctx, report_action(report_id, draft, one)))
    decision = decisions[-1]
    if decision.outcome != "allowed":
        return decision

    blocked_earlier = next((d.id for d in decisions[:-1] if d.outcome == "blocked"), None)
    document = report_document(report_id, draft, ctx, decision, blocked_earlier)
    db = store.db()
    try:
        await db["reports"].insert_one(document)
    except DuplicateKeyError:
        document = await db["reports"].find_one({"_id": report_id}) or document  # a retry: finish the same report

    for update in draft.get("updates") or []:
        change = {**update["change"], "report_id": report_id}
        await ledger.file(update["finding_id"], [change], ctx.mode, ctx)
    await _refresh_proposals(db["reports"], db["proposals"], report_id)

    await store.emit_event({
        "type": "report_filed",
        "dedupe_key": f"report_filed|{report_id}",
        "stamp": ctx.stamp.model_dump(),
        "mode": ctx.mode,
        "run_id": ctx.run_id,
        "decision_id": decision.id,
        "report_id": report_id,
        "outcome": "allowed",
        "status": "pending",
    })
    await _notify(db, report_id, document, ctx)
    return decision


async def _task_id(db, ctx: RunContext) -> str | None:
    task = await db["tasks"].find_one({"run_id": ctx.run_id}) if ctx.run_id else None
    if task:
        return str(task["_id"])
    run = await db["runs"].find_one({"_id": ctx.run_id}) if ctx.run_id else None
    return (run or {}).get("task_id")


async def add_related(report_id: str, refs: list[str], ctx: RunContext) -> list[Decision]:
    """file_related_evidence for a task run: pending related evidence, never accepted knowledge."""
    from dxp import gate, store
    from dxp.reports.relate import relate

    db = store.db()
    report = await db["reports"].find_one({"_id": report_id})
    if report is None:
        raise LookupError(f"report {report_id} not found")
    task_id = await _task_id(db, ctx)
    origin = f"task:{task_id}" if task_id else "discovery"
    new_item = {
        "source_ref": report["source_ref"], "version_id": report["version_id"], "report_id": report_id,
        "origin": origin, "mentions": (report.get("discovery") or {}).get("mentions") or [],
    }
    decisions: list[Decision] = []
    for ref in refs:
        related = report.get("related") or []
        source = await db["source_items"].find_one({"_id": ref}) or {}
        relationship = await relate(new_item, {"ref": ref, "retrieval_method": None})
        action = ProposedAction(
            kind="file_related_evidence",
            destination="ledger",
            target=Target(report_id=report_id, task_id=task_id, scope_id=report.get("scope_id")),
            inputs={
                "source_ref": ref,
                "id_target": f"{task_id}|{ref}",
                "label": relationship.label,
                "filed_count": sum(1 for r in related if r.get("origin") == origin),
                "item_scope_ids": list(source.get("scope_ids") or []),
                "checked_quotes": [
                    {"text": q.text, "quote_found": q.quote_found, "version_id": q.version_id}
                    for q in (relationship.new_quote, relationship.related_quote) if q is not None
                ],
            },
            evidence_ref=EvidenceRef(
                source_ref=ref,
                version_id=relationship.related_quote.version_id if relationship.related_quote else None,
                report_id=report_id,
            ),
        )
        decision = await gate.evaluate(ctx, action)
        decisions.append(decision)
        if decision.outcome != "allowed":
            continue
        stored = relationship.model_dump()
        stored["_id"] = stored["id"]
        stored["filed_by_decision_id"] = decision.id
        result = await db["reports"].update_one(
            {"_id": report_id, "related._id": {"$ne": stored["_id"]}}, {"$push": {"related": stored}}
        )
        if result.matched_count:
            await store.emit_event({
                "type": "related_evidence_filed",
                "dedupe_key": f"related_evidence_filed|{stored['_id']}",
                "stamp": ctx.stamp.model_dump(),
                "mode": ctx.mode,
                "run_id": ctx.run_id,
                "decision_id": decision.id,
                "report_id": report_id,
                "task_id": task_id,
                "outcome": "allowed",
            })
        report = await db["reports"].find_one({"_id": report_id}) or report
    return decisions
