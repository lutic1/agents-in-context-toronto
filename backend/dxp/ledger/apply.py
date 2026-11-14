"""``ledger.apply`` and ``ledger.recover_applying`` (AD-1, D13, D26, D27, V43).

A proposal goes ``pending`` -> ``applying`` -> ``applied``:

1. Claim: a conditional update from ``pending`` to ``applying``; no match, no work.
2. One guarded update, a no-op once done:
   * a Diagnostic proposal writes the value entry, adds the proposal ID to
     ``applied_proposal_ids``, increments ``rev`` and rewrites
     ``search_text`` and ``facets``, matching only while the proposal ID is
     absent (and ``rev`` unchanged, so the rewrite is computed from the
     version it replaces);
   * a scope evidence-collection proposal (``diagnostic_id: null``) sets
     ``source_items.collections.<scope_id>`` while its ``proposal_id`` differs,
     and writes no Diagnostic, edge or search field (V43).
3. Upsert the derived edges; ``run_id``, ``seq`` and ``proposal_id`` are set
   on insert only, so a later run never takes over an earlier run's edge.
4. Emit ``value_applied`` with ``dedupe_key = "value_applied|<p_id>"``.
5. Mark the proposal ``applied``.

Outcomes of step 2 that are recorded, never raised:

* ``stage_not_later`` (AD-5: a ``lifecycle_stage`` applies only when the stored
  stage is earlier): the proposal is set ``rejected`` with ``reason:
  "stage_not_later"``; the Diagnostic is not written; ``proposal_rejected`` is
  emitted with ``status: "stage_not_later"`` for the audit.
* ``held`` (AD-2: a ``baseline`` value for a ``single`` field that already has
  a current value): the proposal goes back to ``pending`` with ``reason:
  "held_for_review"``; the stored value is never overwritten; ``proposal_pending``
  is emitted with ``status: "held_for_review"`` for the audit.

IDs: a value entry's ``value_id`` is ``derive("v_", proposal_id)``, so the
``v_`` prefix joins the AD-3 list (``dx_``, ``f_``, ``p_``, ``e_``, ``dec_``,
``act_``, ``adm_``, ``ps_``, ...); one value entry per applied proposal.

``recover_applying()`` reruns steps 2 to 5 for every proposal stuck in
``applying``; each step is idempotent, so it is safe to run any number of
times. A proposal it cannot finish is logged and skipped, never raised. It runs at API start, at the start of every run and on every decision
call (D26).
"""

from __future__ import annotations

import logging
from typing import Any

from dxp.api.models import Proposal
from dxp.gate.decisions import deps, to_api
from dxp.ledger.types import EDGE_NODE_TYPES, FACET_FIELDS

log = logging.getLogger(__name__)

MAX_RETRIES = 20

# A reverse proposal (V48, AD-31): filed and applied by A26's ledger/revert.py,
# which reuses claim(), mark_applied() and emit_ledger_event() below.
REMOVE = "remove"


def value_id_for(proposal_id: str) -> str:
    return deps.derive("v_", proposal_id)


def _entries(diagnostic: dict[str, Any], field: str) -> list[dict[str, Any]]:
    entries = (diagnostic.get("fields") or {}).get(field) or []
    return [dict(e) for e in entries]


def _search_text(name: str | None, fields: dict[str, list[dict[str, Any]]]) -> str:
    parts = [name or ""]
    for field in sorted(fields):
        for e in fields[field]:
            if e.get("state") == "current":
                parts.append(str(e.get("label") or e.get("value")))
    return " ".join(p for p in parts if p).strip()


def _facets(fields: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    facets: dict[str, list[str]] = {}
    for field in FACET_FIELDS:
        values = [e["value"] for e in fields.get(field, []) if e.get("state") == "current"]
        if values:
            facets[field] = sorted(set(values))
    return facets


def _entry(p: dict[str, Any], review: str, now: Any) -> dict[str, Any]:
    return {
        "value_id": value_id_for(p["_id"]),
        "value": p["value"],
        "label": p.get("label") if p.get("label") is not None else p["value"],
        "detail": p.get("detail"),
        "state": "current",
        "review": review,
        "evidence": p.get("evidence"),
        "check": p.get("check"),
        "proposal_id": p["_id"],
        "action_id": p.get("action_id"),
        "stamp": p.get("stamp"),
        "decided_by": p.get("decided_by"),
        "decided_at": p.get("decided_at") or (now if review != "unreviewed" else None),
        "reason": None,
    }


async def _guarded_diagnostic_update(p: dict[str, Any], review: str, session: Any) -> str:
    """Step 2 for a Diagnostic. Returns ``written``, ``already``, ``stage_not_later`` or ``held``."""
    db = deps.db()
    dx_id = p["diagnostic_id"]
    field = p["field"]
    for _ in range(MAX_RETRIES):
        d = await db["diagnostics"].find_one({"_id": dx_id}, session=session)
        if d is None:
            raise LookupError(f"Diagnostic {dx_id} of proposal {p['_id']} does not exist")
        if p["_id"] in (d.get("applied_proposal_ids") or []):
            return "already"
        now = deps.now()
        fields = {f: _entries(d, f) for f in (d.get("fields") or {})}
        current = [e for e in fields.get(field, []) if e.get("state") == "current"]
        extra_set: dict[str, Any] = {}
        if field == "lifecycle_stage":
            order = deps.stage_order()
            stored = d.get("lifecycle_stage")
            stored_index = order.index(stored) if stored in order else -1
            # AD-5: apply only when the stored stage is earlier; an unknown stage is never later.
            if p["value"] not in order or order.index(p["value"]) <= stored_index:
                return "stage_not_later"
            extra_set["lifecycle_stage"] = p["value"]
        elif deps.cardinality(field) == "single" and current and review == "unreviewed":
            # AD-2: applied without review, a single field with a current entry is not superseded.
            return "held"
        entries = fields.get(field, [])
        if deps.cardinality(field) == "single" or field == "lifecycle_stage":
            for e in entries:
                if e.get("state") == "current":
                    e["state"] = "superseded"
        entries.append(_entry(p, review, now))
        fields[field] = entries
        res = await db["diagnostics"].update_one(
            {"_id": dx_id, "rev": d.get("rev", 0), "applied_proposal_ids": {"$ne": p["_id"]}},
            {
                "$set": {
                    f"fields.{field}": entries,
                    "search_text": _search_text(d.get("name"), fields),
                    "facets": _facets(fields),
                    "updated_at": now,
                    **extra_set,
                },
                "$push": {"applied_proposal_ids": p["_id"]},
                "$inc": {"rev": 1},
            },
            session=session,
        )
        if res.matched_count:
            return "written"
    raise RuntimeError(f"could not apply {p['_id']}: Diagnostic {dx_id} kept changing")


async def _guarded_scope_update(p: dict[str, Any], session: Any) -> str:
    """Step 2 for a scope evidence-collection proposal (V35, V43)."""
    db = deps.db()
    scope_id = (p.get("target") or {}).get("scope_id")
    source_ref = (p.get("evidence") or {}).get("source_ref") or p["value"]
    if not scope_id:
        raise ValueError(f"proposal {p['_id']} has no diagnostic_id and no target.scope_id")
    res = await db["source_items"].update_one(
        {"_id": source_ref, f"collections.{scope_id}.proposal_id": {"$ne": p["_id"]}},
        {
            "$set": {
                f"collections.{scope_id}": {
                    "status": "accepted",
                    "proposal_id": p["_id"],
                    "version_id": (p.get("evidence") or {}).get("version_id"),
                    "accepted_at": deps.now(),
                }
            }
        },
        session=session,
    )
    if res.matched_count:
        return "written"
    if await db["source_items"].find_one({"_id": source_ref}, session=session) is None:
        raise LookupError(f"source item {source_ref} of proposal {p['_id']} does not exist")
    return "already"


async def _upsert_edges(p: dict[str, Any], session: Any) -> None:
    """Step 3 (AD-13, D27): only ``status`` is ever overwritten."""
    if p.get("diagnostic_id") is None:
        return
    node_type = EDGE_NODE_TYPES.get(p["field"])
    if node_type is None:
        return
    db = deps.db()
    seq = None
    if p.get("decision_id"):
        dec = await db["decisions"].find_one({"_id": p["decision_id"]}, session=session)
        seq = (dec or {}).get("seq")
    src, dst, kind = f"diagnostic:{p['diagnostic_id']}", f"{node_type}:{p['value']}", p["field"]
    await db["edges"].update_one(
        {"_id": deps.derive("e_", src, dst, kind)},
        {
            "$setOnInsert": {
                "from": src,
                "to": dst,
                "kind": kind,
                "run_id": p.get("run_id"),
                "seq": seq,
                "proposal_id": p["_id"],
            },
            "$set": {"status": "applied"},
        },
        upsert=True,
        session=session,
    )


async def emit_ledger_event(event_type: str, p: dict[str, Any], *, session: Any = None) -> int:
    """Emit a ledger event for a proposal, deduplicated on ``"<type>|<p_id>"``.

    The convention A26 reuses for ``value_reverted`` (V48, AD-31).
    """
    return await deps.emit_event(
        {
            "type": event_type,
            "dedupe_key": f"{event_type}|{p['_id']}",
            "mode": p.get("mode"),
            "run_id": p.get("run_id"),
            "stamp": p.get("stamp"),
            "decision_id": p.get("decision_id"),
            "action_id": p.get("action_id"),
            "diagnostic_id": p.get("diagnostic_id"),
            "proposal_id": p["_id"],
            "report_id": p.get("report_id"),
            "field": p.get("field"),
        },
        session=session,
    )


async def _emit_outcome(event_type: str, status: str, p: dict[str, Any], session: Any) -> int:
    """The audit event of a recorded apply outcome (``stage_not_later``, ``held_for_review``),
    deduplicated on ``"<type>|<status>|<p_id>"``."""
    return await deps.emit_event(
        {
            "type": event_type,
            "dedupe_key": f"{event_type}|{status}|{p['_id']}",
            "mode": p.get("mode"),
            "run_id": p.get("run_id"),
            "stamp": p.get("stamp"),
            "decision_id": p.get("decision_id"),
            "action_id": p.get("action_id"),
            "diagnostic_id": p.get("diagnostic_id"),
            "proposal_id": p["_id"],
            "report_id": p.get("report_id"),
            "field": p.get("field"),
            "status": status,
        },
        session=session,
    )


async def _emit_applied(p: dict[str, Any], session: Any) -> None:
    """Step 4, deduplicated."""
    await emit_ledger_event("value_applied", p, session=session)


async def claim(proposal_id: str, extra: dict[str, Any] | None = None, *, session: Any = None) -> dict[str, Any] | None:
    """Step 1: ``pending`` -> ``applying`` by a conditional update.

    Returns the claimed proposal, or ``None`` when another caller holds it or it
    is no longer pending. Reused by A26's ``ledger.revert_proposal`` (V48).
    """
    db = deps.db()
    res = await db["proposals"].update_one(
        {"_id": proposal_id, "status": "pending"},
        {"$set": {"status": "applying", "applying_at": deps.now(), **(extra or {})}},
        session=session,
    )
    if not res.modified_count:
        return None
    return await db["proposals"].find_one({"_id": proposal_id}, session=session)


async def mark_applied(proposal_id: str, extra: dict[str, Any] | None = None, *, session: Any = None) -> bool:
    """Step 5: ``applying`` -> ``applied`` by a conditional update. Reused by A26."""
    res = await deps.db()["proposals"].update_one(
        {"_id": proposal_id, "status": "applying"},
        {"$set": {"status": "applied", "applied_at": deps.now(), **(extra or {})}},
        session=session,
    )
    return bool(res.modified_count)


async def _complete(p: dict[str, Any], review: str | None, session: Any) -> dict[str, Any]:
    """Steps 2 to 5 for a proposal in ``applying``. Idempotent."""
    db = deps.db()
    review = review or p.get("apply_review") or ("unreviewed" if p.get("mode") == "baseline" else "accepted")
    if p.get("diagnostic_id") is None:
        outcome = await _guarded_scope_update(p, session)
    else:
        outcome = await _guarded_diagnostic_update(p, review, session)

    if outcome == "stage_not_later":
        await db["proposals"].update_one(
            {"_id": p["_id"], "status": "applying"},
            {"$set": {"status": "rejected", "reason": "stage_not_later", "decided_at": deps.now()}},
            session=session,
        )
        # Recorded for the audit: proposal_rejected with status stage_not_later.
        await _emit_outcome("proposal_rejected", "stage_not_later", p, session)
        return await db["proposals"].find_one({"_id": p["_id"]}, session=session)
    if outcome == "held":
        await db["proposals"].update_one(
            {"_id": p["_id"], "status": "applying"},
            {"$set": {"status": "pending", "reason": "held_for_review"}},
            session=session,
        )
        # Recorded for the audit: proposal_pending with status held_for_review.
        await _emit_outcome("proposal_pending", "held_for_review", p, session)
        return await db["proposals"].find_one({"_id": p["_id"]}, session=session)

    await _upsert_edges(p, session)
    await _emit_applied(p, session)
    value_id = value_id_for(p["_id"]) if p.get("diagnostic_id") else None
    await mark_applied(p["_id"], {"value_id": value_id}, session=session)
    return await db["proposals"].find_one({"_id": p["_id"]}, session=session)


async def apply(proposal_id: str) -> Proposal:
    """Apply one pending proposal exactly once (AD-1, D13, D27); returns it as
    ``api.models.Proposal``. The value entry is ``unreviewed`` for a ``baseline``
    proposal and ``accepted`` otherwise. ``apply_with`` also records the Reviewer."""
    return await apply_with(proposal_id)


async def apply_with(
    proposal_id: str,
    *,
    review: str | None = None,
    decided_by: str | None = None,
    session: Any = None,
) -> Proposal:
    """``apply`` with the review state, the deciding Reviewer and a session."""
    doc = await apply_raw(proposal_id, review=review, decided_by=decided_by, session=session)
    if doc is None:
        raise LookupError(f"proposal {proposal_id} not found")
    return Proposal.model_validate(to_api(doc))


async def apply_raw(
    proposal_id: str,
    *,
    review: str | None = None,
    decided_by: str | None = None,
    session: Any = None,
) -> dict[str, Any] | None:
    """Apply one pending proposal, exactly once (AD-1, D13, D27).

    Called by the seed (``baseline``), by ``reports.decide`` (A24) and by value
    review (A14); never by an agent in ``live`` mode. ``review`` is the value
    entry's review state (``unreviewed`` for ``baseline``, ``accepted`` for a
    Reviewer). Two concurrent calls apply once: only the claim that matches
    does the work. Returns the proposal as it stands.
    """
    db = deps.db()
    current = await db["proposals"].find_one({"_id": proposal_id}, session=session)
    if current is None:
        return None
    if current.get("op") == REMOVE:
        raise ValueError(f"{proposal_id} is a reverse proposal; it is applied by ledger.revert_proposal (A26, AD-31)")
    extra: dict[str, Any] = {}
    if review:
        extra["apply_review"] = review
    if decided_by:
        extra["decided_by"] = decided_by
        extra["decided_at"] = deps.now()
    proposal = await claim(proposal_id, extra, session=session)
    if proposal is None:
        return await db["proposals"].find_one({"_id": proposal_id}, session=session)
    return await _complete(proposal, review, session)


async def reject_report_proposals(report_id: str, decision_id: str, note: str, session: Any) -> int:
    """Reject every ``pending`` proposal of a rejected report (AD-29; the ledger is the only
    writer of ``proposals``, AD-1). Returns how many it rejected.

    Called by A24 inside the report-decision transaction (``session``). Each move is a
    conditional update on ``status: "pending"``, so an ``applying`` or ``applied``
    proposal is never touched and a retry changes nothing and returns 0. Each rejection
    emits one ``proposal_rejected`` event (``dedupe_key = "proposal_rejected|<p_id>"``)
    with the rejecting decision's stamp.
    """
    db = deps.db()
    decision = await db["decisions"].find_one({"_id": decision_id}, session=session) or {}
    decided_by = decision.get("initiated_by") or (decision.get("stamp") or {}).get("principal")
    pending = [
        p async for p in db["proposals"].find({"report_id": report_id, "status": "pending"}, session=session)
    ]
    rejected = 0
    for p in pending:
        now = deps.now()
        res = await db["proposals"].update_one(
            {"_id": p["_id"], "report_id": report_id, "status": "pending"},
            {"$set": {"status": "rejected", "reason": note, "rejected_by_decision_id": decision_id,
                      "decided_by": decided_by, "decided_at": now}},
            session=session,
        )
        if not res.modified_count:
            continue
        rejected += 1
        await deps.emit_event(
            {
                "type": "proposal_rejected",
                "dedupe_key": f"proposal_rejected|{p['_id']}",
                "mode": p.get("mode"),
                "run_id": None,
                "stamp": decision.get("stamp") or p.get("stamp"),
                "decision_id": decision_id,
                "action_id": decision.get("action_id"),
                "diagnostic_id": p.get("diagnostic_id"),
                "proposal_id": p["_id"],
                "report_id": report_id,
                "field": p.get("field"),
            },
            session=session,
        )
    return rejected


async def recover_applying() -> None:
    """Finish every proposal stuck in ``applying`` (D26, D27). Runs at API start, at the
    start of every run and on every decision call."""
    await recover_applying_ids()


async def recover_applying_ids(*, session: Any = None) -> list[str]:
    """``recover_applying`` returning the IDs it finished."""
    db = deps.db()
    # Reverse proposals (op: remove) are finished by A26's ledger.recover_reverting (AD-31).
    stuck = [
        p async for p in db["proposals"].find({"status": "applying", "op": {"$ne": REMOVE}}, session=session)
    ]
    done: list[str] = []
    for p in stuck:
        # One proposal that cannot be finished never blocks the others, API start, run start
        # or a decision (review item 2): it is logged and left in applying.
        try:
            await _complete(p, None, session)
        except Exception:  # per proposal: logged and skipped
            log.exception("recover_applying: could not finish proposal %s; left in applying", p.get("_id"))
            continue
        done.append(p["_id"])
    return done
