"""Report filing (AD-27): the report is the pending proposal.

`file(draft, ctx, final=...)` gates one draft as a report-level
`file_proposal` (target `<report_id>|draft<n>`, its own Decision, V21). The
caller (A10) calls it once per draft, in order, with `final=False` for every
draft but the last (Luis's ruling, 14 Nov):

- `final=False` only asks the gate. The Decision is recorded by the gate;
  nothing is written here, no update is filed and no alert is created. An
  allowed gate-only action is settled `done` with `report_id: None` through
  `gate.mark_action` (V65). A non-final draft carries no `updates`.
- `final=True` (the default), when allowed, writes the `reports` document
  (`pending`, with its script, V41), one `ledger.file()` per update (each
  change keeps its own `admission_id`, D22) and the `report_filed` event.

`file()` never creates or sends `notify_slack`: the run (A10) dispatches the
report's one alert after the final `file()` succeeds. A blocked draft writes
nothing here: the gate has recorded its Decision and event.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError, WriteError

from dxp.api.models import Decision, EvidenceRef, ProposedAction, Report, RunContext, Target

log = logging.getLogger("dxp.reports")

UNPINNED_RELATED = "{count} related item(s) could not be pinned to a source version and are not listed."


class ReportNotFiled(RuntimeError):
    """An allowed report could not be written. The message names the report only."""


def gate_target(report_id: str, number: int, attempt: int = 0) -> str:
    """The gate target of one draft: `<report_id>|draft<n>`, or `<report_id>|draft<n>.r<k>` on
    redraft attempt k, so a redraft after a block is a new evaluation with its own Decision."""
    suffix = f".r{attempt}" if attempt else ""
    return f"{report_id}|draft{number}{suffix}"


def _pinned(relationship: dict[str, Any]) -> bool:
    """Both quotes name the source version they were checked against (V40)."""
    return all(
        isinstance(relationship.get(side), dict) and relationship[side].get("version_id") and relationship[side].get("source_ref")
        for side in ("new_quote", "related_quote")
    )


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
    attempt = int(draft.get("attempt") or 0)
    return ProposedAction(
        kind="file_proposal",
        destination="ledger",
        target=Target(report_id=report_id, scope_id=draft.get("scope_id")),
        inputs={
            "draft": number,
            "attempt": attempt,
            "id_target": gate_target(report_id, number, attempt),
            "source_ref": draft.get("source_ref"),
            "headline": one.get("headline"),
            "gap": one.get("gap"),
            "claims": gate_claims(one),
            "source_fields": dict(draft.get("source_fields") or {}),
            "checked_quotes": [dict(q) for q in one.get("quotes") or []],
        },
        evidence_ref=EvidenceRef(source_ref=draft.get("source_ref"), version_id=draft.get("version_id"), report_id=report_id),
        retrieval=draft.get("retrieval") or None,
        memories_used=(one.get("memories_used") or []) if number > 1 else [],
    )


def report_document(report_id: str, draft: dict[str, Any], ctx: RunContext, decision: Decision | None,
                    blocked_draft_decision_id: str | None) -> dict[str, Any]:
    """The `reports` document, validated against the frozen `Report` shape, with its script.
    `decision` is None for the check made before the gate is asked."""
    from dxp.reports.relate import relationship_id
    from dxp.reports.script import script_for, script_hash

    source_ref = draft["source_ref"]
    related = []
    for relationship in draft.get("related") or []:
        relationship = _plain(relationship)
        if not _pinned(relationship):
            continue
        relationship["id"] = relationship_id(report_id, source_ref, relationship.get("related_ref"))
        related.append(relationship)
    uncertainties = list(draft.get("uncertainties") or [])
    omitted = len(draft.get("related") or []) - len(related)
    if omitted:
        log.warning("reports.file: %s related item(s) of %s have no source version and are left out", omitted, report_id)
        uncertainties.append(UNPINNED_RELATED.format(count=omitted))
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
        "uncertainties": uncertainties,
        "gap": draft.get("gap"),
        "retrieval": draft.get("retrieval") or None,
        "memories_used": draft.get("memories_used") or [],
        "proposal_ids": [],
        "diagnostic_ids": [],
        "recommended_task": draft.get("recommended_task"),
        "draft": int(draft.get("draft") or 1),
        "blocked_draft_decision_id": blocked_draft_decision_id,
        "stamp": ctx.stamp,
        "file_decision_id": decision.id if decision else None,
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


async def _settle(decision: Decision, status: str, result: dict[str, Any] | None) -> None:
    """Settle a report-level action through Governance, the only writer of `actions` (V65).
    Without a Governance function for it the action is left as the gate wrote it."""
    from dxp import gate

    mark_action = getattr(gate, "mark_action", None)
    if mark_action is None or not decision.action_id:
        return
    try:
        await mark_action(decision.action_id, status, result)
    except Exception as exc:
        log.warning("reports.file: action %s not settled: %s", decision.action_id, type(exc).__name__)


def _check_shape(draft: dict[str, Any], final: bool) -> None:
    """One draft per call. Raised before the gate is asked, so a wrong call records nothing."""
    nested = draft.get("drafts") or []
    if len(nested) > 1:
        raise ValueError("reports.file takes one draft per call: pass each of drafted['drafts'] in order, "
                         "with final=False for every draft but the last")
    if not final and draft.get("updates"):
        raise ValueError("a non-final draft carries no updates; only the final draft files them")


async def file(draft: dict[str, Any], ctx: RunContext, final: bool = True) -> Decision:
    """Gate one draft as a report-level file_proposal and return its Decision.

    `final=False`: gate only, nothing written. `final=True` and allowed: store the report pending
    with its script (V41) and ledger.file each update. The alert is the run's (A10), never sent here.
    On the final draft, `blocked_draft_decision_id` (the Decision of an earlier blocked draft, set by
    the caller) is recorded on the report so the memory's effect is visible."""
    from dxp import gate, ledger, store
    from dxp.reports.draft import team_for_scope

    _check_shape(draft, final)
    if not draft.get("team_id"):
        draft = {**draft, "team_id": await team_for_scope(draft.get("scope_id"))}
    report_id = report_id_for(ctx.run_id or draft.get("run_id"), draft["source_ref"])
    try:  # everything the report needs is checked before the gate is asked, never after
        report_document(report_id, draft, ctx, None, None)
    except Exception as exc:
        missing = [k for k in ("scope_id", "team_id", "version_id", "headline", "gap") if not draft.get(k)]
        raise ValueError(
            f"report {report_id} cannot be filed: " + (f"missing {', '.join(missing)}" if missing else type(exc).__name__)
        ) from None

    decision = await gate.evaluate(ctx, report_action(report_id, draft, draft))
    if not final:
        if decision.outcome == "allowed":  # gate-only: this draft is never written
            await _settle(decision, "done", {"report_id": None})
        return decision
    if decision.outcome != "allowed":
        return decision

    document = report_document(report_id, draft, ctx, decision, draft.get("blocked_draft_decision_id"))
    db = store.db()
    try:
        try:
            await db["reports"].insert_one(document)
        except DuplicateKeyError:
            document = await db["reports"].find_one({"_id": report_id}) or document  # a retry: finish the same report
        except WriteError as exc:
            raise ReportNotFiled(f"report {report_id} was allowed but could not be stored ({type(exc).__name__})") from None

        for update in draft.get("updates") or []:
            change = {**update["change"], "report_id": report_id}  # keeps the caller's admission_id (D22)
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
    except Exception:
        await _settle(decision, "failed", None)
        raise
    stored = await db["reports"].find_one({"_id": report_id}) or document
    await _settle(decision, "done", {"proposal_ids": list(stored.get("proposal_ids") or []), "report_id": report_id})
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
        # The version the task found is pinned here, explicitly, and recorded on the relationship (V40).
        pinned = {"ref": ref, "version_id": source.get("current_version_id"), "retrieval_method": None}
        relationship = await relate(new_item, pinned)
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
