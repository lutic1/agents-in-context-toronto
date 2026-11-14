"""`actions.dispatch(action, ctx)`: one Slack alert per report, exactly once (AD-20, S7, V11).

The order never changes:

1. Gate first: `gate.evaluate(ctx, action)` records the Decision. Blocked: nothing else
   happens (`ActionBlocked`, no action, no post).
2. Save the action ID first: the `actions` document is inserted if absent, `queued`, before
   anything is sent (the gate inserts it too; a repeat of the same step finds it).
3. Refuse to start without `SLACK_WEBHOOK_URL` or `DXP_BASE_URL`: the action stays `queued`.
4. Claim it with one conditional update, `queued` -> `dispatching`. Only the worker whose
   update matched posts; any other status is never posted again.
5. Post once and record exactly what was observed, conditional on `dispatching`: 200 `ok`
   `delivered`; another 4xx `failed`; 429 retried once after `Retry-After` while still
   holding the claim, a second 429 `failed`; timeout, connection error or 5xx `unknown`,
   never retried.

The action ID is `derive("act_", run_id or "-", "notify_slack", diagnostic_id or "-", report_id)`:
the target is the report, so a report with two proposals gets one alert (V11), and a report
with no resolved Diagnostic uses "-" (V43).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dxp.gate as gate
from dxp.actions import records, slack
from dxp.actions.errors import ActionBlocked, ReportNotFound
from dxp.actions.views import action_model, decision_dict
from dxp.api.models import Action, ProposedAction, RunContext, Target
from dxp.identity import derive

log = logging.getLogger("dxp.actions")

KIND = "notify_slack"
EXTERNAL_DONE = frozenset({"dispatching", "delivered", "failed", "unknown"})


def action_id_for(run_id: str | None, diagnostic_id: str | None, report_id: str) -> str:
    """AD-20, D20, V11, V43: the same parts as the Decision ID, with prefix `act_`."""
    return derive("act_", run_id or "-", KIND, diagnostic_id or "-", report_id)


def _dump(model: Any) -> Any:
    return model.model_dump(mode="python") if hasattr(model, "model_dump") else model


def _actor(ctx: RunContext) -> slack.Actor:
    stamp = ctx.stamp
    grant_version = ctx.grant_version or stamp.grant_version
    grant_id = ctx.grant_id or stamp.grant_id
    return slack.Actor(
        agent=stamp.agent or (ctx.principal.id if ctx.principal else None),
        run_id=ctx.run_id,
        grant=f"{grant_id}@v{grant_version}" if grant_id and grant_version else grant_id,
        policy_set_version=ctx.policy_set_version or stamp.policy_set_version,
    )


def _normalised(action: ProposedAction, report: dict[str, Any]) -> ProposedAction:
    """One alert per report: the target is the report (never a proposal), destination the one
    channel. The Diagnostic is the caller's, else the report's first in-scope one, else none."""
    if action.kind != KIND:
        raise ValueError(f"actions.dispatch sends notify_slack only, not {action.kind!r}")
    diagnostic_ids = report.get("diagnostic_ids") or []
    diagnostic_id = action.target.diagnostic_id or (diagnostic_ids[0] if diagnostic_ids else None)
    target = Target(report_id=report["_id"], diagnostic_id=diagnostic_id, scope_id=action.target.scope_id or report.get("scope_id"))
    inputs = {
        **action.inputs,
        "report_id": report["_id"],
        "nct_id": report.get("nct_id"),
        "headline": report.get("headline"),
        "relationship_summary": slack.relationship_summary(report.get("related") or []),
        "proposal_ids": list(report.get("proposal_ids") or []),
        "channel": slack.CHANNEL,
    }
    # A06's gate reads the extras A01's ProposedAction lacks from `inputs`: check 4 compares
    # `script_hash` with the filed report's, so an alert is built from that report version (AD-30).
    if report.get("script_hash") and "script_hash" not in inputs:
        inputs["script_hash"] = report["script_hash"]
    return action.model_copy(update={"target": target, "inputs": inputs})


def _new_action_doc(action_id: str, decision: dict[str, Any], action: ProposedAction, ctx: RunContext) -> dict[str, Any]:
    """The AD-14 `actions` document, `queued`, pointing back to its Decision (as the gate writes it)."""
    at = decision.get("decided_at") or records.now()
    return {
        "_id": action_id,
        "decision_id": decision["_id"],
        "admission_id": ctx.admission_id,
        "run_id": ctx.run_id,
        "mode": ctx.mode,
        "kind": KIND,
        "destination": action.destination,
        "target": _dump(action.target),
        "inputs": action.inputs,
        "evidence_ref": _dump(action.evidence_ref),
        "stamp": _dump(ctx.stamp),
        "error": None,
        "status": "queued",
        "result": None,
        "resolution": None,
        "proposed_at": at,
        "decided_at": at,
        "claimed_at": None,
        "observed_at": None,
        "authorised_by": decision.get("authorised_by"),
    }


async def dispatch(action: ProposedAction, ctx: RunContext) -> Action:
    """Gate, persist, claim `queued` -> `dispatching`, send, record exactly what was observed."""
    report_id = action.target.report_id
    if not report_id:
        raise ValueError("a notify_slack action targets its report: target.report_id is required (V11)")
    report = await records.get_report(report_id)
    if report is None:
        raise ReportNotFound(report_id)
    action = _normalised(action, report)
    action_id = action_id_for(ctx.run_id, action.target.diagnostic_id, report_id)

    doc = await records.get(action_id)
    if doc is None:
        # 1. Gate first: no action document, no post, without an allowed Decision.
        decision = decision_dict(await gate.evaluate(ctx, action))
        if decision.get("outcome") != "allowed":
            log.info("notify_slack blocked: decision %s (%s)", decision.get("_id"), decision.get("failed_check"))
            raise ActionBlocked(decision)
        if decision.get("action_id") and decision["action_id"] != action_id:
            # The gate inserted the action and owns its ID; follow it, and say so.
            log.warning("notify_slack: the gate's action ID %s differs from %s", decision["action_id"], action_id)
            action_id = decision["action_id"]
        # 2. Save the action ID first (insert if absent: the gate may already have done it).
        doc, _ = await records.insert_if_absent(_new_action_doc(action_id, decision, action, ctx))

    if doc["status"] != "queued":
        # Claimed, settled or resolved already: never posted again (one alert per report).
        return action_model(doc)

    # 3. Refuse to start without the configuration: the action stays queued.
    config = slack.require_config()

    # 4. Claim it atomically.
    claimed_at = records.now()
    if not await records.transition(action_id, "queued", "dispatching", {"claimed_at": claimed_at}):
        return action_model(await records.get(action_id) or doc)

    # 5. Post once; record what was observed.
    links = slack.link_urls(config.base_url, report_id, action.target.diagnostic_id)
    proposals = await records.get_proposals(list(report.get("proposal_ids") or []))
    payload = slack.build_message(action_id=action_id, report=report, proposals=proposals, links=links, actor=_actor(ctx))
    status, observed = await _post_once_with_one_429_retry(action_id, config.webhook_url, payload)

    result = {
        "http_status": observed.status if observed else None,
        "response_body": observed.body if observed else None,
        "posted_at": records.now() if status == "delivered" else None,
        "link_urls": links,
    }
    await records.transition(action_id, "dispatching", status, {"result": result, "observed_at": records.now()})
    log.info("notify_slack %s: %s (HTTP %s)", action_id, status, result["http_status"])
    return action_model(await records.get(action_id) or doc)


async def _post_once_with_one_429_retry(action_id: str, webhook_url: str, payload: dict[str, Any]) -> tuple[str, slack.Observed | None]:
    observed: slack.Observed | None = None
    for attempt in (1, 2):
        try:
            observed = await slack.post(webhook_url, payload)
        except Exception as exc:  # noqa: BLE001 - a timeout or connection error: ambiguous
            # The exception text is never logged or stored: it could carry the URL.
            log.warning("notify_slack %s: no answer from Slack (%s); outcome unknown, not retried", action_id, type(exc).__name__)
            return "unknown", None
        outcome = slack.classify(observed)
        if outcome != "rate_limited":
            return outcome, observed
        if attempt == 1:
            # Nothing was posted. Wait as asked, still holding the claim (status dispatching).
            await sleep(slack.retry_after_seconds(observed))
    return "failed", observed  # a second 429


async def sleep(seconds: float) -> None:
    """Patched in tests."""
    await asyncio.sleep(seconds)

