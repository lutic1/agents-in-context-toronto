"""Reverse proposals (AD-31, V48). A26.

``ledger.revert_proposal(proposal_id, decision)`` undoes one applied proposal without editing
history: it files a new reverse proposal ``derive("p_", proposal_id, "revert")`` (``op: remove``,
``reverts_proposal_id``), inserted if absent, and applies it ``pending`` -> ``applying`` ->
``applied`` with the A06 helpers (``claim``, ``mark_applied``, ``emit_ledger_event``):

1. Claim the reverse proposal (conditional on ``pending``; no match, no work).
2. A guarded ``$unset`` of ``source_items.collections.<scope_id>`` that matches only while the
   entry still names the original ``proposal_id``, so a later acceptance is never removed and
   a retry is a no-op.
3. Emit ``value_reverted`` (``dedupe_key = "value_reverted|<reverse p_id>"``).
4. Mark the reverse proposal ``applied``.

The original proposal, its Decision and the source version are left exactly as they are. The
ledger stays the only writer of ``proposals`` and ``source_items.collections`` (AD-1, V65).

Only scope evidence-collection proposals (``diagnostic_id: null``, V43) are reversible here;
reverting a Diagnostic value entry is not built (the demo report has none) and is refused
before anything is filed.

``recover_reverting()`` finishes every reverse proposal left in ``applying``.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from dxp.api.models import Decision, Proposal
from dxp.gate.decisions import deps, to_api
from dxp.ledger.apply import REMOVE, claim, emit_ledger_event, mark_applied

log = logging.getLogger(__name__)


class NotReversible(ValueError):
    """The proposal is not an applied scope evidence-collection proposal."""


def reverse_id(proposal_id: str) -> str:
    return deps.derive("p_", proposal_id, "revert")


def _plain(value: Any) -> dict[str, Any]:
    data = value.model_dump() if isinstance(value, BaseModel) else dict(value or {})
    data.setdefault("_id", data.get("id"))
    data.setdefault("id", data.get("_id"))
    return data


def build_reverse(original: dict[str, Any], decision: dict[str, Any], now: Any) -> dict[str, Any]:
    """The reverse proposal document (pure)."""
    return {
        "_id": reverse_id(original["_id"]),
        "op": REMOVE,
        "reverts_proposal_id": original["_id"],
        "diagnostic_id": None,
        "target": dict(original.get("target") or {}),
        "field": original.get("field"),
        "value": original.get("value"),
        "evidence": dict(original.get("evidence") or {}),
        "status": "pending",
        "mode": "live",
        "run_id": None,
        "report_id": original.get("report_id"),
        "decision_id": decision.get("_id"),
        "action_id": decision.get("action_id"),
        "stamp": decision.get("stamp"),
        "decided_by": decision.get("initiated_by") or (decision.get("stamp") or {}).get("principal"),
        "created_at": now,
    }


async def _file_reverse(original: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    proposals = deps.db()["proposals"]
    doc = build_reverse(original, decision, deps.now())
    stored = await proposals.find_one({"_id": doc["_id"]})
    if stored is not None:
        return stored
    try:
        await proposals.insert_one(doc)
    except DuplicateKeyError:
        return await proposals.find_one({"_id": doc["_id"]})
    return doc


async def _complete_reverse(p: dict[str, Any]) -> dict[str, Any]:
    """Steps 2 to 4 for a reverse proposal in ``applying``. Idempotent."""
    db = deps.db()
    scope_id = (p.get("target") or {}).get("scope_id")
    source_ref = (p.get("evidence") or {}).get("source_ref") or p.get("value")
    if not scope_id or not source_ref:
        raise NotReversible(f"reverse proposal {p['_id']} names no scope or source item")
    await db["source_items"].update_one(
        {"_id": source_ref, f"collections.{scope_id}.proposal_id": p["reverts_proposal_id"]},
        {"$unset": {f"collections.{scope_id}": ""}},
    )
    await emit_ledger_event("value_reverted", p)
    await mark_applied(p["_id"])
    return await db["proposals"].find_one({"_id": p["_id"]})


async def revert_proposal(proposal_id: str, decision: Decision) -> Proposal:
    """File derive("p_", proposal_id, "revert") (op remove, reverts_proposal_id) insert-if-absent and
    apply it pending -> applying -> applied with a guarded unset; emits value_reverted."""
    db = deps.db()
    rid = reverse_id(proposal_id)
    existing = await db["proposals"].find_one({"_id": rid})
    if existing is None:
        original = await db["proposals"].find_one({"_id": proposal_id})
        if original is None:
            raise LookupError(f"proposal {proposal_id} not found")
        if original.get("op") == REMOVE:
            raise NotReversible(f"{proposal_id} is itself a reverse proposal")
        if original.get("status") != "applied":
            raise NotReversible(f"{proposal_id} is {original.get('status')}, not applied")
        if original.get("diagnostic_id") is not None:
            raise NotReversible(f"{proposal_id} writes a Diagnostic; only scope collections are reversible (A26)")
        existing = await _file_reverse(original, _plain(decision))
    if existing.get("status") == "pending":
        claimed = await claim(rid)
        if claimed is not None:
            existing = await _complete_reverse(claimed)
        else:
            existing = await db["proposals"].find_one({"_id": rid})
    elif existing.get("status") == "applying":
        existing = await _complete_reverse(existing)
    return Proposal.model_validate(to_api(existing))


async def recover_reverting() -> None:
    """Finish reverse proposals stuck in applying (AD-31). Each one that cannot be finished is
    logged and left in applying; it never blocks the others."""
    db = deps.db()
    stuck = [p async for p in db["proposals"].find({"status": "applying", "op": REMOVE})]
    for p in stuck:
        try:
            await _complete_reverse(p)
        except Exception:
            log.exception("recover_reverting: could not finish reverse proposal %s", p.get("_id"))
