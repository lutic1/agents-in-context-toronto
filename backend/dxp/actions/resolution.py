"""`actions.resolve(...)`: a Reviewer settles an `unknown` Slack alert by hand (S8, AD-20, D25).

The Reviewer checks `#all-mango-db-hackathon` for the action ID, then records what they
saw. The resolution is gated as kind `resolve_notification` under the Reviewer's grant
(destination `ledger`, `run_id: null`, a server-generated `request_id`, `cause { action_id,
origin_run_id }`), so it is audited as a Decision with the Reviewer's stamp. Allowed, one
conditional update moves the action from `unknown` and writes `resolution { outcome, note,
decision_id, by, at }`. It never posts.
"""

from __future__ import annotations

import logging
import secrets
from typing import Literal

import dxp.gate as gate
from dxp.actions import records
from dxp.actions.errors import ActionNotFound, NotResolvable, NoteRequired
from dxp.actions.views import action_model, decision_dict, decision_model
from dxp.api.models import Action, Decision, DecisionCause, ProposedAction, RunContext, Target

log = logging.getLogger("dxp.actions")

KIND = "resolve_notification"


async def resolve(action_id: str, outcome: Literal["delivered", "failed"], note: str, ctx: RunContext) -> tuple[Action, Decision]:
    """Gated resolve_notification: settle an unknown notification by hand; never posts (S8).

    Raises `NoteRequired` (no note, refused before the gate), `ActionNotFound`, or
    `NotResolvable` (the action is not an `unknown` notify_slack action: 409). A blocked
    resolution returns the unchanged action with the blocked Decision.
    """
    if outcome not in ("delivered", "failed"):
        raise ValueError(f"outcome must be delivered or failed, not {outcome!r}")
    note = (note or "").strip()
    if not note:
        raise NoteRequired("A resolution needs a note: what you saw in the channel.")

    doc = await records.get(action_id)
    if doc is None:
        raise ActionNotFound(action_id)
    if doc.get("kind") != "notify_slack" or doc.get("status") != "unknown":
        raise NotResolvable(action_id, doc.get("status"), doc.get("kind"))

    ctx = ctx.model_copy(
        update={
            "run_id": None,  # a Reviewer decision is outside any run (AD-17)
            "request_id": ctx.request_id or secrets.token_hex(8),
            "cause": DecisionCause(action_id=action_id, origin_run_id=doc.get("run_id")),
        }
    )
    target = doc.get("target") or {}
    proposed = ProposedAction(
        kind=KIND,
        destination="ledger",
        target=Target(report_id=target.get("report_id"), diagnostic_id=target.get("diagnostic_id"), scope_id=target.get("scope_id")),
        # D49: the ID target is the action_id. A01's `Target` has no action_id field, so it
        # travels in `inputs`, where A06's gate reads it into the target.
        inputs={"action_id": action_id, "outcome": outcome, "note": note},
    )
    decision = decision_dict(await gate.evaluate(ctx, proposed))
    if decision.get("outcome") != "allowed":
        log.info("resolve_notification on %s blocked by %s", action_id, decision.get("failed_check"))
        return action_model(doc), decision_model(decision)

    resolution = {
        "outcome": outcome,
        "note": note,
        "decision_id": decision["_id"],
        "by": ctx.stamp.initiated_by or ctx.stamp.principal,
        "at": records.now(),
    }
    if not await records.transition(action_id, "unknown", outcome, {"resolution": resolution}):
        current = await records.get(action_id) or doc
        raise NotResolvable(action_id, current.get("status"))
    # The resolve_notification action the gate queued is a DxP-state kind: it is done.
    if decision.get("action_id"):
        await records.transition(decision["action_id"], "queued", "done", {"observed_at": records.now()})
    return action_model(await records.get(action_id) or doc), decision_model(decision)
