"""``ledger.file`` and ``ledger.ensure_diagnostic`` (AD-1, AD-3, AD-4, Story 1.6).

Every value enters through ``file(finding_id, changes, mode, ctx)``, called
once per admitted change (D46). For each change the gate is evaluated first,
before any write, including ``ensure_diagnostic`` (AD-19); blocked means no
write but the Decision and its ``action_blocked`` event.

* ``live`` (agent, inside a run): an allowed change is filed as a ``pending``
  Proposed change. It is never applied here (D8, D28); only a Reviewer's
  report decision applies it, through ``ledger.apply``.
* ``baseline`` (seed and prior collection, under ``seed@v1``): an allowed
  change is filed and applied at once as ``unreviewed`` (AD-4).
"""

from __future__ import annotations

import dataclasses
from typing import Any, Iterable

from dxp import gate
from dxp.gate.checks import GateAction
from dxp.gate.decisions import deps, insert_if_absent
from dxp.ledger.types import EVIDENCE_COLLECTION, Change, Filed, LedgerCtx

MODES = ("live", "baseline")


def alias_id(name: str) -> str:
    """The ``aliases`` key for a name (AD-3): the approach alias as is, else ``normalise_name``."""
    if name.startswith("approach:"):
        return name
    return deps.normalise_name(name)


def diagnostic_id_for(name: str) -> str:
    return deps.derive("dx_", alias_id(name))


async def ensure_diagnostic(name: str, ctx: Any, *, display_name: str | None = None) -> str:
    """Match a Diagnostic through ``aliases`` and create it only on a miss (AD-3).

    Call only after the gate allowed the change (check 2 blocks a Diagnostic
    outside the grant's scope, including one this would create, D28). A
    duplicate key means it already exists, so it is read. Returns the ``dx_`` ID.
    """
    ctx = LedgerCtx.coerce(ctx)
    db = deps.db()
    s = ctx.session
    key = alias_id(name)
    dx_id = deps.derive("dx_", key)
    now = deps.now()
    alias, _ = await insert_if_absent(
        db["aliases"], {"_id": key, "diagnostic_id": dx_id, "name": name, "created_at": now}, session=s
    )
    dx_id = alias["diagnostic_id"]
    _, created = await insert_if_absent(
        db["diagnostics"],
        {
            "_id": dx_id,
            "name": display_name or name,
            "id_alias": key,
            "aliases": [key],
            "lifecycle_stage": "not_determined",
            "fields": {},
            "rev": 0,
            "applied_proposal_ids": [],
            "search_text": display_name or name,
            "facets": {},
            "created_run_id": ctx.run_id,
            "created_mode": ctx.mode,
            "stamp": ctx.stamp,
            "created_at": now,
        },
        session=s,
    )
    if created:
        await deps.emit_event(
            {
                "type": "diagnostic_created",
                "dedupe_key": f"diagnostic_created|{dx_id}",
                "mode": ctx.mode,
                "run_id": ctx.run_id,
                "stamp": ctx.stamp,
                "diagnostic_id": dx_id,
            },
            session=s,
        )
    return dx_id


def _current_entries(diagnostic: dict[str, Any] | None, field: str) -> list[dict[str, Any]]:
    entries = ((diagnostic or {}).get("fields") or {}).get(field) or []
    if isinstance(entries, dict):  # tolerate { values: [...] }
        entries = entries.get("values") or []
    return [e for e in entries if e.get("state") == "current"]


def stage_is_later(new: str, stored: str | None) -> bool:
    """True when ``new`` is later than ``stored`` in the registry's stage order (AD-5)."""
    order = deps.stage_order()
    if new not in order:
        raise ValueError(f"unknown lifecycle stage {new!r}")
    stored_index = order.index(stored) if stored in order else -1
    return order.index(new) > stored_index


async def _not_filed_reason(change: Change, dx_id: str | None, diagnostic: dict[str, Any] | None, source_item: dict[str, Any] | None) -> str | None:
    if change.field == EVIDENCE_COLLECTION and dx_id is None:
        entry = ((source_item or {}).get("collections") or {}).get(change.scope_id) or {}
        if entry.get("status") == "accepted":
            return f"already accepted in the evidence collection of {change.scope_id}"
        return None
    if diagnostic is None:
        return None
    if any(e.get("value") == change.value for e in _current_entries(diagnostic, change.field)):
        return f"equal to a current value of {change.field}"
    if change.field == "lifecycle_stage" and not stage_is_later(change.value, diagnostic.get("lifecycle_stage")):
        return f"stage {change.value!r} is not later than {diagnostic.get('lifecycle_stage')!r}"
    return None


def _ctx_for(ctx: LedgerCtx, change: Change, mode: str) -> LedgerCtx:
    updates: dict[str, Any] = {"mode": mode}
    if change.admission_id:
        updates["admission_id"] = change.admission_id
    return dataclasses.replace(ctx, **updates)


async def _file_one(finding_id: str, change: Change, mode: str, ctx: LedgerCtx) -> Filed:
    db = deps.db()
    s = ctx.session
    if change.field == EVIDENCE_COLLECTION and change.diagnostic_id is None and not change.scope_id:
        raise ValueError("an evidence-collection change names its scope_id (V35)")

    alias = change.creates_alias
    dx_id = change.diagnostic_id or (diagnostic_id_for(alias) if alias else None)
    diagnostic = await db["diagnostics"].find_one({"_id": dx_id}, session=s) if dx_id else None
    source_ref = change.evidence.get("source_ref")
    source_item = None
    if dx_id is None and source_ref:
        source_item = await db["source_items"].find_one({"_id": source_ref}, session=s)

    reason = await _not_filed_reason(change, dx_id, diagnostic, source_item)
    if reason:
        return Filed(status="not_filed", diagnostic_id=dx_id, reason=reason)

    proposal_id = deps.derive("p_", finding_id, change.field, change.value)
    report_id = ctx.report_id
    target: dict[str, Any] = {
        "diagnostic_id": dx_id,
        "proposal_id": proposal_id,
        "report_id": report_id,
        "field": change.field,
        "value": change.value,
    }
    if dx_id is None:
        target["scope_id"] = change.scope_id
    evidence_ref = {
        "source_ref": source_ref,
        "version_id": change.evidence.get("version_id"),
        "finding_id": finding_id,
        "proposal_id": proposal_id,
        "report_id": report_id,
        "quote": change.evidence.get("quote"),
        "check": change.check,
    }
    action = GateAction(
        kind="file_proposal" if mode == "live" else "apply_value",
        destination="ledger",
        target=target,
        inputs={
            "finding_id": finding_id,
            "field": change.field,
            "value": change.value,
            "label": change.label,
            "mode": mode,
        },
        evidence_ref=evidence_ref,
        checks=[change.check] if change.check else [],
        mention=change.mention,
        creates_diagnostic=bool(alias) and diagnostic is None,
    )
    decision = await gate.evaluate(ctx, action)
    if not decision.allowed:
        return Filed(status="blocked", proposal_id=None, diagnostic_id=dx_id, decision=decision,
                     reason=decision.failed_check)

    action_id = decision.action_id
    try:
        diagnostic_name = change.diagnostic_name
        if alias and diagnostic is None:
            dx_id = await ensure_diagnostic(alias, ctx, display_name=change.diagnostic_name or alias)
        if dx_id and diagnostic_name is None:
            d = diagnostic or await db["diagnostics"].find_one({"_id": dx_id}, session=s)
            diagnostic_name = (d or {}).get("name")
        current = _current_entries(diagnostic, change.field)
        proposal = {
            "_id": proposal_id,
            "finding_id": finding_id,
            "diagnostic_id": dx_id,
            "diagnostic_name": diagnostic_name,
            "target": {"scope_id": change.scope_id} if dx_id is None else None,
            "field": change.field,
            "value": change.value,
            "label": change.label if change.label is not None else change.value,
            "detail": change.detail,
            "current_value": current[0].get("value") if current else None,
            "evidence": change.evidence,
            "check": change.check,
            "mention": change.mention,
            "op": "add",  # A26's reverse proposals carry op: remove (V48)
            "reverts_proposal_id": None,
            "status": "pending",
            "mode": mode,
            "trigger": change.trigger,
            "run_id": ctx.run_id,
            "report_id": report_id,
            "action_id": action_id,
            "decision_id": decision.decision_id,
            "stamp": ctx.stamp,
            "decided_by": None,
            "decided_at": None,
            "reason": None,
            "created_at": deps.now(),
        }
        await insert_if_absent(db["proposals"], proposal, session=s)
        value_ids: list[str] = []
        if mode == "live":
            await deps.emit_event(
                {
                    "type": "proposal_pending",
                    "dedupe_key": f"proposal_pending|{proposal_id}",
                    "mode": mode,
                    "run_id": ctx.run_id,
                    "stamp": ctx.stamp,
                    "decision_id": decision.decision_id,
                    "action_id": action_id,
                    "diagnostic_id": dx_id,
                    "proposal_id": proposal_id,
                    "report_id": report_id,
                    "field": change.field,
                },
                session=s,
            )
            status = "filed"
        else:
            from dxp.ledger.apply import apply

            applied = await apply(proposal_id, review="unreviewed", session=s)
            if applied and applied.get("value_id"):
                value_ids.append(applied["value_id"])
            status = "applied" if (applied or {}).get("status") == "applied" else (applied or {}).get("status", "filed")
        await gate.mark_action(
            action_id, "done", {"proposal_ids": [proposal_id], "value_ids": value_ids, "report_id": report_id},
            session=s,
        )
    except Exception:
        await gate.mark_action(action_id, "failed", None, session=s)
        raise
    return Filed(status=status, proposal_id=proposal_id, diagnostic_id=dx_id, decision=decision)


async def file(finding_id: str, changes: Any, mode: str, ctx: Any) -> list[Filed]:
    """File each change of one Finding, gating each one first (AD-1, D46).

    ``changes`` is one change or a list; each is judged on its own and gets
    its own Decision. ``ctx`` is the run context (``live``) or the seed
    context (``baseline``); ``ctx.report_id`` links each proposal to its
    research report (AD-27).
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    base = LedgerCtx.coerce(ctx)
    if mode == "live" and base.kind != "run":
        raise ValueError("live filing is an agent write and needs a run context (AD-17)")
    if mode == "baseline" and base.kind != "seed":
        raise ValueError("baseline mode runs only under the seed grant (AD-4)")
    if isinstance(changes, (dict, Change)) or not isinstance(changes, Iterable):
        changes = [changes]
    out: list[Filed] = []
    for raw in changes:
        change = Change.coerce(raw)
        out.append(await _file_one(finding_id, change, mode, _ctx_for(base, change, mode)))
    return out
