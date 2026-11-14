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

The ledger takes a ``finding_id`` and never writes a Finding: ``findings``
belong to the ingest layer (A10's pipeline). The ledger writes Diagnostics and
aliases (``ensure_diagnostic``), proposals, value entries, edges and events.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Iterable

from dxp import gate
from dxp.api.models import Decision, Mode, RunContext
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
    """The ID a new Diagnostic for ``name`` gets (AD-3). Not its ID when an alias exists:
    use ``resolve_alias`` for that."""
    return deps.derive("dx_", alias_id(name))


async def resolve_alias(name: str, session: Any = None) -> str:
    """The Diagnostic ``name`` names: the ``aliases`` entry for ``alias_id(name)`` when there
    is one, else the ID ``ensure_diagnostic`` would create (review item 7, AD-3). An alias
    such as "F1 Liquid" for FoundationOne Liquid CDx resolves to that Diagnostic, so check 2
    judges the real one."""
    found = await deps.db()["aliases"].find_one({"_id": alias_id(name)}, session=session)
    if found and found.get("diagnostic_id"):
        return found["diagnostic_id"]
    return diagnostic_id_for(name)


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
        db["aliases"],
        # created_mode: A02's identity.resolve_exact treats an alias as an FDA trade name
        # unless it was created live, so a run's alias never resolves as one (V34).
        {"_id": key, "diagnostic_id": dx_id, "name": name, "created_mode": ctx.mode,
         "created_run_id": ctx.run_id, "created_at": now},
        session=s
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
    """True when ``new`` is later than ``stored`` in the registry's stage order (AD-5).
    An unknown stage is never later, so it is recorded as not filed, never raised."""
    order = deps.stage_order()
    if new not in order:
        return False
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
    if not change.diagnostic_id and not change.creates_alias and not (
        change.field == EVIDENCE_COLLECTION and change.scope_id
    ):
        # Review item 2: a change with no Diagnostic is only the scope's evidence collection
        # (V35, V43). Anything else would file, then wedge apply and recovery in applying.
        raise ValueError(
            f"change to {change.field!r} names no Diagnostic; only an {EVIDENCE_COLLECTION!r} change "
            "with a scope_id may have diagnostic_id null (V35, V43)"
        )
    if not (change.evidence or {}).get("version_id"):
        # V40: every proposal and value entry pins the exact source version it used.
        raise ValueError("a change's evidence names its source version_id (V40)")

    alias = change.creates_alias
    dx_id = change.diagnostic_id or (await resolve_alias(alias, s) if alias else None)
    diagnostic = await db["diagnostics"].find_one({"_id": dx_id}, session=s) if dx_id else None
    source_ref = change.evidence.get("source_ref")
    source_item = None
    if dx_id is None and source_ref:
        source_item = await db["source_items"].find_one({"_id": source_ref}, session=s)

    reason = await _not_filed_reason(change, dx_id, diagnostic, source_item)
    if reason:
        return Filed(status="not_filed", diagnostic_id=dx_id, reason=reason)

    proposal_id = deps.derive("p_", finding_id, change.field, change.value)
    report_id = change.report_id or ctx.report_id
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
    decision = await gate.evaluate(ctx, action)  # ctx carries the session
    if decision.outcome != "allowed":
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
            "decision_id": decision.id,
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
                    "decision_id": decision.id,
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
            from dxp.ledger.apply import apply_raw

            applied = await apply_raw(proposal_id, review="unreviewed", session=s) or {}
            if applied.get("value_id"):
                value_ids.append(applied["value_id"])
            status = "applied" if applied.get("status") == "applied" else applied.get("status", "filed")
        await gate.mark_action(
            action_id, "done", {"proposal_ids": [proposal_id], "value_ids": value_ids, "report_id": report_id},
            session=s,
        )
    except Exception:
        await gate.mark_action(action_id, "failed", None, session=s)
        raise
    return Filed(status=status, proposal_id=proposal_id, diagnostic_id=dx_id, decision=decision)


async def file_detailed(finding_id: str, changes: Any, mode: str, ctx: Any, *, session: Any = None) -> list[Filed]:
    """``file`` with the outcome of every change, including those not filed (equal to a
    current value, or a stage that is not later), which are never gated."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    base = LedgerCtx.coerce(ctx, session=session)
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


async def file(finding_id: str, changes: list[dict[str, Any]], mode: Mode, ctx: RunContext) -> list[Decision]:
    """Gate each change once, then file it (AD-1, D46): ``live`` files a pending proposal,
    ``baseline`` applies at once. Returns one Decision per gated change, allowed or
    blocked; a change equal to a current value (or a stage that is not later) is not
    filed and not gated, so it has no Decision. ``ctx.report_id``, or a change's own
    ``report_id``, links each proposal to its research report (AD-27)."""
    return [f.decision for f in await file_detailed(finding_id, changes, mode, ctx) if f.decision is not None]
