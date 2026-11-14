"""A09: the Block Kit alert (S4, S5, V11, V33, V37, V43)."""

from __future__ import annotations

import json
import re

import pytest

from dxp.actions import slack

from .conftest import HEADLINE, NCT, POLICY_SET, REPORT_ID, RUN_ID, make_proposals, make_report

ACTION_ID = "act_0123456789abcdef"
ACTOR = slack.Actor(agent="dxp-curator", run_id=RUN_ID, grant="lbdx@v1", policy_set_version=POLICY_SET)


def build(report=None, proposals=None, diagnostic_id=None):
    report = report or make_report()
    links = slack.link_urls("https://dxp.test/", report["_id"], diagnostic_id)
    return slack.build_message(action_id=ACTION_ID, report=report, proposals=make_proposals() if proposals is None else proposals,
                               links=links, actor=ACTOR)


def texts(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def test_notify_only_no_interactive_elements() -> None:
    payload = build()
    kinds = {n.get("type") for n in walk(payload["blocks"])}
    assert "actions" not in kinds and "button" not in kinds
    assert not any("accessory" in n or "action_id" in n for n in walk(payload["blocks"]))


def test_header_carries_the_action_id() -> None:
    header = build()["blocks"][0]
    assert header["type"] == "header"
    assert header["text"]["text"] == f"New research report for review ({ACTION_ID})"
    assert ACTION_ID in build()["text"]


def test_body_headline_discovery_gap_relationships_who_and_context() -> None:
    payload = build()
    text = texts(payload)
    assert HEADLINE in text
    assert f"<https://clinicaltrials.gov/study/{NCT}|{NCT}>" in text
    assert "*Status:* Recruiting" in text and "No results posted" in text
    assert "Have early-stage NSCLC studies" in text
    assert "Extends 1, Related (no relationship established) 1" in text
    assert "Strongest: Extends A prior plasma genotyping study (test)" in text
    assert "agent `dxp-curator`" in text and f"run `{RUN_ID}`" in text
    assert "grant `lbdx@v1`" in text and f"policy set `{POLICY_SET}`" in text
    assert payload["blocks"][-1] == {"type": "context", "elements": [{"type": "mrkdwn", "text": "Approve or reject in DxP. Slack only notifies."}]}


def test_review_link_only_when_no_diagnostic_resolves() -> None:
    text = texts(build())
    assert f"<https://dxp.test/reports/{REPORT_ID}|Review in DxP>" in text
    assert "Open diagnostic" not in text and "/diagnostics/" not in text


def test_open_diagnostic_link_for_a_resolved_in_scope_diagnostic() -> None:
    text = texts(build(diagnostic_id="dx_00000000000000c1"))
    assert "<https://dxp.test/diagnostics/dx_00000000000000c1|Open diagnostic>" in text


def test_the_scope_collection_update_is_described_without_a_diagnostic() -> None:
    assert slack.describe_update(make_proposals()[0], NCT) == "Add trial NCT04712877 to the scope's evidence collection"
    assert "Proposed updates, pending review:* 2" in texts(build(proposals=[]))


def test_quotes_are_at_most_300_characters() -> None:
    long = "x" * 400
    report = make_report()
    report["discovery"]["quotes"][0]["text"] = long
    report["related"][0]["related_quote"]["text"] = long
    for match in re.findall(r'"(x+…?)"', texts(build(report)).replace('\\"', '"')):
        assert len(match) <= 300


def test_the_wording_added_never_claims_use_study_or_performance() -> None:
    """V37: the alert's own words never say a trial uses or studies a named product."""
    report = make_report(headline="H", gap="G", related=[], discovery={"summary": "s", "quotes": []})
    text = texts(build(report, proposals=make_proposals())).lower()
    for word in ("uses", "used", "studies", "studied", "showed", "detect", "performance", "accuracy"):
        assert not re.search(rf"\b{word}", text), word


def test_mrkdwn_is_escaped() -> None:
    text = texts(build(make_report(headline="a <b> & c")))
    assert "a &lt;b&gt; &amp; c" in text


@pytest.mark.parametrize(("status", "body", "expected"), [
    (200, "ok", "delivered"), (200, " ok\n", "delivered"), (200, "", "unknown"), (201, "ok", "unknown"),
    (400, "invalid_payload", "failed"), (404, "no_service", "failed"), (410, "channel_is_archived", "failed"),
    (429, "", "rate_limited"), (500, "", "unknown"), (504, "", "unknown"), (302, "", "unknown"),
])
def test_classify(status, body, expected) -> None:
    assert slack.classify(slack.Observed(status, body)) == expected


def test_retry_after() -> None:
    assert slack.retry_after_seconds(slack.Observed(429, "", {"retry-after": "7"})) == 7.0
    assert slack.retry_after_seconds(slack.Observed(429, "")) == 1.0
    assert slack.retry_after_seconds(slack.Observed(429, "", {"retry-after": "soon"})) == 1.0
    assert slack.retry_after_seconds(slack.Observed(429, "", {"retry-after": "9999"})) == 30.0


def test_config_repr_never_shows_the_webhook(monkeypatch) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.invalid/services/SECRET")
    assert "SECRET" not in repr(slack.require_config())


@pytest.mark.parametrize("bad", [
    "hooks.slack.com/services/x", "ftp://hooks.slack.invalid/services/x", "http://hooks.slack.invalid/services/x",
    "https://hooks.slack.invalid", "https:///services/x", "https://hooks.slack.invalid/", "not a url at all",
])
def test_a_malformed_webhook_url_is_refused_without_echoing_it(monkeypatch, bad) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", bad)
    with pytest.raises(slack.SenderNotConfigured) as err:
        slack.require_config()
    assert "SLACK_WEBHOOK_URL" in str(err.value) and bad not in str(err.value)


@pytest.mark.parametrize("good", ["https://hooks.slack.invalid/services/TEST", "http://127.0.0.1:8080/services/x"])
def test_valid_webhook_urls(monkeypatch, good) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", good)
    assert slack.require_config().webhook_url == good


async def test_http_post_raises_not_sent_before_the_wire() -> None:
    with pytest.raises(slack.NotSent):
        await slack.http_post("ftp://127.0.0.1/services/x", {"text": "t"}, timeout=1.0)
    with pytest.raises(slack.NotSent):
        await slack.http_post("http://127.0.0.1:9/services/x", {"bad": object()}, timeout=1.0)
