"""A09: actions.dispatch, one Slack alert per report, exactly once (S7, V11, V43, AD-20).

Every test posts through A01's `fake_slack` (or nothing): no test reaches Slack.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from dxp import actions
from dxp.actions import dispatcher, records, slack
from dxp.identity import derive

from .conftest import REPORT_ID, RUN_ID, make_report, notify, run_ctx

pytestmark = pytest.mark.usefixtures("gate")

EXPECTED_ID = derive("act_", RUN_ID, "notify_slack", "-", REPORT_ID)


async def test_delivered_records_what_was_observed(seeded, sent, gate) -> None:
    action = await actions.dispatch(notify(), run_ctx())

    assert action.id == EXPECTED_ID  # "-" for the Diagnostic (V43)
    assert action.status == "delivered"
    assert action.kind == "notify_slack" and action.destination == "slack:#all-mango-db-hackathon"
    assert action.result.http_status == 200 and action.result.response_body == "ok"
    assert action.result.posted_at is not None
    assert action.result.link_urls.report_url == f"https://dxp.test/reports/{REPORT_ID}"
    assert action.result.link_urls.diagnostic_url is None
    assert action.claimed_at is not None and action.observed_at is not None
    assert action.decision_id.startswith("dec_")
    assert len(sent.sent) == 1
    # Gate first, once, for notify_slack to the one channel, targeting the report.
    assert len(gate.calls) == 1
    _, proposed = gate.calls[0]
    assert proposed.kind == "notify_slack" and proposed.target.report_id == REPORT_ID
    assert proposed.target.diagnostic_id is None
    assert proposed.inputs["script_hash"] == "h"
    statuses = [e["status"] for e in seeded.events if e["type"] == "action_status_changed"]
    assert statuses == ["dispatching", "delivered"]


async def test_one_report_with_two_proposals_gets_exactly_one_alert(seeded, sent) -> None:
    first = await actions.dispatch(notify(proposal_id="p_00000000000000b1"), run_ctx())
    second = await actions.dispatch(notify(proposal_id="p_00000000000000b2"), run_ctx())
    again = await actions.dispatch(notify(), run_ctx())

    assert first.id == second.id == again.id == EXPECTED_ID
    assert len(sent.sent) == 1
    assert len(seeded["actions"].docs) == 1
    text = str(sent.sent[0]["args"][1])
    assert "Add trial NCT04712877 to the scope's evidence collection" in text


@pytest.mark.parametrize(("status", "body"), [(400, "invalid_payload"), (403, "action_prohibited"), (404, "no_service"), (404, "channel_not_found")])
async def test_other_4xx_is_failed_and_never_retried(seeded, sent, waits, status, body) -> None:
    sent.respond(status, body)
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "failed"
    assert action.result.http_status == status and action.result.response_body == body
    assert action.result.posted_at is None
    assert len(sent.sent) == 1 and waits == []
    await actions.dispatch(notify(), run_ctx())
    assert len(sent.sent) == 1


async def test_429_is_retried_once_after_retry_after_while_holding_the_claim(seeded, sent, monkeypatch) -> None:
    sent.respond(429, "rate_limited", {"Retry-After": "3"})
    sent.respond(200, "ok")
    seen: list[tuple[float, str]] = []

    async def wait(seconds: float) -> None:
        seen.append((seconds, (await records.get(EXPECTED_ID))["status"]))

    monkeypatch.setattr(dispatcher, "sleep", wait)
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "delivered"
    assert seen == [(3.0, "dispatching")]
    assert len(sent.sent) == 2


async def test_a_second_429_is_failed(seeded, sent, waits) -> None:
    sent.respond(429, "rate_limited", {"Retry-After": "1"})
    sent.respond(429, "rate_limited", {"Retry-After": "1"})
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "failed" and action.result.http_status == 429
    assert len(sent.sent) == 2 and waits == [1.0]


async def test_timeout_is_unknown_and_never_retried(seeded, sent, waits) -> None:
    sent.fail()
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "unknown"
    assert action.result.http_status is None and action.result.response_body is None
    assert action.result.link_urls.report_url.endswith(REPORT_ID)
    await actions.dispatch(notify(), run_ctx())
    assert len(sent.sent) == 1 and waits == []


async def test_connection_error_is_unknown(seeded, sent) -> None:
    sent.fail(ConnectionError("refused"))
    assert (await actions.dispatch(notify(), run_ctx())).status == "unknown"


@pytest.mark.parametrize(("status", "body"), [(500, "internal"), (502, ""), (503, "x"), (200, "not ok")])
async def test_5xx_or_a_200_that_is_not_ok_is_unknown(seeded, sent, waits, status, body) -> None:
    sent.respond(status, body)
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "unknown" and action.result.http_status == status
    assert len(sent.sent) == 1 and waits == []


async def test_two_workers_at_once_post_once(seeded, fake_slack) -> None:
    async def slow(*args, **kwargs):
        await asyncio.sleep(0.01)
        return await fake_slack(*args, **kwargs)

    with slack.use_sender(slow):
        results = await asyncio.gather(*(actions.dispatch(notify(), run_ctx()) for _ in range(5)))
    assert len(fake_slack.sent) == 1
    assert {r.id for r in results} == {EXPECTED_ID}
    assert (await records.get(EXPECTED_ID))["status"] == "delivered"


async def test_a_slow_worker_never_overwrites_a_swept_action(seeded, fake_slack) -> None:
    async def swept_meanwhile(*args, **kwargs):
        assert await actions.mark_unknown(EXPECTED_ID, "abandoned_in_flight")
        return await fake_slack(*args, **kwargs)

    with slack.use_sender(swept_meanwhile):
        action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "unknown" and action.error == "abandoned_in_flight"
    assert action.result is None


@pytest.mark.parametrize("missing", ["DXP_BASE_URL", "SLACK_WEBHOOK_URL"])
async def test_refuses_to_start_without_configuration_and_stays_queued(seeded, sent, monkeypatch, missing) -> None:
    monkeypatch.setenv(missing, "")
    with pytest.raises(actions.SenderNotConfigured) as err:
        await actions.dispatch(notify(), run_ctx())
    assert missing in str(err.value) and "hooks" not in str(err.value)
    assert (await records.get(EXPECTED_ID))["status"] == "queued"
    assert sent.sent == []
    # Fixed: the same action is claimed and sent once.
    monkeypatch.setenv(missing, {"DXP_BASE_URL": "https://dxp.test", "SLACK_WEBHOOK_URL": "https://hooks.slack.invalid/services/TEST"}[missing])
    with slack.use_sender(sent):
        assert (await actions.dispatch(notify(), run_ctx())).status == "delivered"
    assert len(sent.sent) == 1


async def test_a_relative_base_url_is_refused(seeded, sent, monkeypatch) -> None:
    monkeypatch.setenv("DXP_BASE_URL", "dxp.test")
    with pytest.raises(actions.SenderNotConfigured):
        await actions.dispatch(notify(), run_ctx())
    assert sent.sent == []


async def test_blocked_creates_no_action_and_sends_nothing(seeded, sent, gate) -> None:
    gate.block("notify_slack", "evidence_checks")
    with pytest.raises(actions.ActionBlocked) as err:
        await actions.dispatch(notify(), run_ctx())
    assert err.value.decision["outcome"] == "blocked"
    assert seeded["actions"].docs == {} and sent.sent == []


async def test_a_resolved_in_scope_diagnostic_gets_the_open_diagnostic_link(mem, sent) -> None:
    mem["reports"].docs[REPORT_ID] = make_report(diagnostic_ids=["dx_00000000000000c1"], proposal_ids=[])
    action = await actions.dispatch(notify(), run_ctx())
    assert action.id == derive("act_", RUN_ID, "notify_slack", "dx_00000000000000c1", REPORT_ID)
    assert action.result.link_urls.diagnostic_url == "https://dxp.test/diagnostics/dx_00000000000000c1"
    assert "Open diagnostic" in str(sent.sent[0]["args"][1])


async def test_an_action_the_gate_already_saved_is_claimed_not_duplicated(seeded, sent, monkeypatch) -> None:
    """The real gate (A06) inserts the queued action itself and returns its ID."""
    import dxp.gate

    real_fake = dxp.gate.evaluate

    async def gate_that_saves(ctx, proposed):
        decision = await real_fake(ctx, proposed)
        decision = decision.model_copy(update={"action_id": EXPECTED_ID})
        doc = dispatcher._new_action_doc(EXPECTED_ID, {**decision.model_dump(), "_id": decision.id}, proposed, ctx)
        await records.get_db()["actions"].insert_one(doc)
        return decision

    monkeypatch.setattr(dxp.gate, "evaluate", gate_that_saves)
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "delivered" and len(seeded["actions"].docs) == 1 and len(sent.sent) == 1


async def test_needs_a_filed_report(mem, sent) -> None:
    with pytest.raises(actions.ReportNotFound):
        await actions.dispatch(notify(), run_ctx())
    with pytest.raises(ValueError):
        await actions.dispatch(notify(report_id=None), run_ctx())
    assert sent.sent == []


async def test_the_webhook_url_is_never_stored_logged_or_emitted(seeded, fake_slack, monkeypatch, caplog, waits) -> None:
    secret = "https://hooks.slack.com/services/T0SECRET/B0SECRET/xyzSECRETxyz"
    monkeypatch.setenv("SLACK_WEBHOOK_URL", secret)
    caplog.set_level(logging.DEBUG)
    for reply in ((200, "ok"),):
        fake_slack.respond(*reply)
    with slack.use_sender(fake_slack):
        await actions.dispatch(notify(), run_ctx())
        for i, outcome in enumerate(["timeout", 500, 404, 429]):
            report_id = f"rep_00000000000001{i:02d}"
            seeded["reports"].docs[report_id] = make_report(_id=report_id)
            if outcome == "timeout":
                fake_slack.fail()
            elif outcome == 429:
                fake_slack.respond(429, "rate_limited")
                fake_slack.respond(429, "rate_limited")
            else:
                fake_slack.respond(outcome, "err")
            await actions.dispatch(notify(report_id=report_id), run_ctx())
    logging.getLogger("httpx").info("HTTP Request: POST %s \"HTTP/1.1 200 OK\"", secret)
    stored = str(seeded["actions"].docs) + str(seeded.events)
    assert "SECRET" not in stored
    assert "SECRET" not in caplog.text
    assert fake_slack.sent[0]["args"][0] == secret  # only the sender ever sees it
