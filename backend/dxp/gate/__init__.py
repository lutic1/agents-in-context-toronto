"""The policy gate: ``gate.evaluate(ctx, action) -> Decision`` (AD-19, Story 9.3).

The only policy check. Every write path and every external call evaluates it
first; it runs the five checks in order (``gate.checks``), with the claim
checks inside check 4 (``gate.claims``), and records every evaluation as a
Decision (``gate.decisions``).

Import rule (AD-28): nothing in ``gate`` imports ``memory``, ``retrieval`` or
``reports``. A memory may inform a draft; it never reaches a grant, a policy
or a check.
"""

from __future__ import annotations

from typing import Any

from dxp.api.models import Decision, ProposedAction, RunContext
from dxp.gate import checks, claims, decisions
from dxp.gate.checks import CHECK_ORDER, GateAction, GateCtx, Loaded, run_checks
from dxp.gate.decisions import api_decision, deps


async def _load_policies(ctx: GateCtx) -> tuple[str | None, list[dict[str, Any]]]:
    """The run's pinned policy set; outside a run (or unpinned), the current set (AD-18)."""
    if ctx.policy_set_version:
        if await deps.policy_set(ctx.policy_set_version) is None:
            raise LookupError(f"policy set {ctx.policy_set_version} not found")
        return ctx.policy_set_version, await deps.policies_in_set(ctx.policy_set_version)
    version, policies = await deps.current_set()
    return version, list(policies)


async def _load(ctx: GateCtx, action: GateAction) -> tuple[Loaded, str | None]:
    db = deps.db()
    s = ctx.session
    grant = await deps.current_grant(ctx.grant_id)
    policy_set_version, policies = await _load_policies(ctx)
    loaded = Loaded(grant=grant, policies=policies, now=deps.now())
    if ctx.kind == "run":
        loaded.run = await db["runs"].find_one({"_id": ctx.run_id}, session=s)
        if ctx.admission_id:
            loaded.admission = await db["admissions"].find_one({"_id": ctx.admission_id}, session=s)
    if action.kind == "search_source":
        scope_id = (action.query or {}).get("scope_id") or ((grant or {}).get("scope") or {}).get("scope_id")
        if scope_id:
            loaded.scope = await db["research_scopes"].find_one({"_id": scope_id}, session=s)
    if action.kind in checks.REPORT_DERIVED_KINDS and action.target.get("report_id"):
        loaded.report = await db["reports"].find_one({"_id": action.target["report_id"]}, session=s)
        file_decision_id = (loaded.report or {}).get("file_decision_id")
        if file_decision_id:
            loaded.report_file_decision = await db["decisions"].find_one({"_id": file_decision_id}, session=s)
    return loaded, policy_set_version


async def evaluate(ctx: RunContext, action: ProposedAction) -> Decision:
    """Evaluate one proposed action and record the Decision.

    ``ctx`` is the frozen ``RunContext`` (or a ``GateCtx`` or mapping with its
    fields); ``action`` is the frozen ``ProposedAction`` (or a ``GateAction`` or
    mapping). To evaluate inside a caller's transaction (``tasks.authorise``,
    V38), use ``evaluate_in(ctx, action, session)``. Returns
    ``api.models.Decision``.

    Allowed: the decision, a ``queued`` action pointing back to it, and
    ``action_allowed``. Blocked: the decision and ``action_blocked`` only. A
    repeat of the same run step returns the stored decision.
    """
    ctx = GateCtx.coerce(ctx)
    action = GateAction.coerce(action)
    ctx.validate()
    action.validate()

    decision_id, action_id = decisions.ids_for(ctx, action)
    stored = await deps.db()["decisions"].find_one({"_id": decision_id}, session=ctx.session)
    if stored is not None:
        return api_decision(await decisions.record(ctx, action, stored, action_id))

    loaded, policy_set_version = await _load(ctx, action)
    results, failed, claim_results = run_checks(ctx, action, loaded)
    doc = decisions.build_decision(
        ctx,
        action,
        decision_id=decision_id,
        grant=loaded.grant,
        policy_set_version=policy_set_version,
        checks=results,
        failed_check=failed,
        claims=claim_results,
        now=loaded.now,
    )
    return api_decision(await decisions.record(ctx, action, doc, action_id))


async def evaluate_in(ctx: Any, action: Any, session: Any) -> Decision:
    """``evaluate`` inside the caller's transaction: every read and write uses ``session``."""
    return await evaluate(GateCtx.coerce(ctx, session=session), action)


async def mark_action(action_id: str, status: str, result: dict[str, Any] | None = None, *, session: Any = None) -> bool:
    """Settle a DxP-state action (``queued`` to ``done`` or ``failed``), AD-19.

    Conditional on ``queued``, so a repeat changes nothing. Emits
    ``action_status_changed`` on the change.
    """
    if status not in ("done", "failed"):
        raise ValueError("a DxP-state action ends done or failed")
    db = deps.db()
    res = await db["actions"].update_one(
        {"_id": action_id, "status": "queued"},
        {"$set": {"status": status, "result": result, "observed_at": deps.now()}},
        session=session,
    )
    if res.modified_count:
        act = await db["actions"].find_one({"_id": action_id}, session=session)
        await deps.emit_event(
            {
                "type": "action_status_changed",
                "dedupe_key": f"action_status_changed|{action_id}|{status}",
                "mode": act.get("mode"),
                "run_id": act.get("run_id"),
                "stamp": act.get("stamp"),
                "decision_id": act.get("decision_id"),
                "action_id": action_id,
                "status": status,
            },
            session=session,
        )
        return True
    return False


__all__ = [
    "CHECK_ORDER",
    "Decision",
    "GateAction",
    "GateCtx",
    "claims",
    "checks",
    "decisions",
    "deps",
    "evaluate",
    "evaluate_in",
    "mark_action",
]
