"""A09 as its callers on main use it: A10's notify step (`pipeline/item.py`) and A05's scan
claim and settle (`discovery/scan.py`). Fakes only: memory store, fake gate, fake Slack."""

from __future__ import annotations

import importlib

import pytest

from dxp import actions
from dxp.actions import records, slack
from dxp.api.models import EvidenceRef, ProposedAction, Target
from dxp.identity import derive
from dxp.pipeline import config, item

from .conftest import REPORT_ID, RUN_ID, SCOPE_ID, make_report, run_ctx

pytestmark = pytest.mark.usefixtures("gate")

# `dxp.discovery.scan` is also the re-exported function; take the module itself.
scan = importlib.import_module("dxp.discovery.scan")

SOURCE_REF = "ctgov:NCT04712877"


def a10_action(report: dict) -> ProposedAction:
    """Built exactly as `pipeline.item.notify` builds it."""
    diagnostic_ids = [d for d in report.get("diagnostic_ids") or [] if d]
    dx = diagnostic_ids[0] if diagnostic_ids else None
    return ProposedAction(
        kind="notify_slack",
        destination=config.SLACK_DESTINATION,
        target=Target(report_id=report["_id"], diagnostic_id=dx, scope_id=SCOPE_ID),
        inputs={
            "report_id": report["_id"],
            "source_ref": SOURCE_REF,
            "version_id": report["version_id"],
            "diagnostic_ids": diagnostic_ids,
            "script_hash": report.get("script_hash"),
            "headline": report.get("headline"),
        },
        evidence_ref=EvidenceRef(source_ref=SOURCE_REF, version_id=report["version_id"], report_id=report["_id"]),
    )


async def test_a10_call_delivers_with_its_admission(seeded, sent, gate) -> None:
    adm = derive("adm_", RUN_ID, item.item_key(SOURCE_REF, "notify_slack", None, REPORT_ID))
    action = await actions.dispatch(a10_action(make_report()), item.with_admission(run_ctx(), adm))
    assert action.status == "delivered" and action.admission_id == adm
    assert action.id == derive("act_", RUN_ID, "notify_slack", "-", REPORT_ID)
    assert len(sent.sent) == 1
    assert gate.calls[0][0].admission_id == adm


async def test_a10_matches_the_blocked_and_not_sent_errors(seeded, sent, gate, monkeypatch) -> None:
    gate.block("notify_slack", "evidence_checks")
    with pytest.raises(Exception) as err:
        await actions.dispatch(a10_action(make_report()), item.with_admission(run_ctx(), "adm_x"))
    assert item.is_action_blocked(err.value)
    assert err.value.decision_id == err.value.decision["_id"]  # what A10 records

    gate.blocked.clear()
    monkeypatch.setenv("DXP_BASE_URL", "")
    with pytest.raises(Exception) as err:
        await actions.dispatch(a10_action(make_report()), item.with_admission(run_ctx(), "adm_x"))
    assert next(n for n in item.NOTIFY_NOT_SENT if item.is_a09(err.value, n)) == "SenderNotConfigured"

    with pytest.raises(Exception) as err:
        await actions.dispatch(a10_action(make_report(_id="rep_missing0000001")), run_ctx())
    assert item.is_a09(err.value, "ReportNotFound")
    assert sent.sent == []


async def test_the_diagnostic_always_comes_from_the_report(seeded, sent) -> None:
    proposed = a10_action(make_report())
    proposed = proposed.model_copy(update={"target": Target(report_id=REPORT_ID, diagnostic_id="dx_callerchosen0001")})
    action = await actions.dispatch(proposed, run_ctx())
    assert action.id == derive("act_", RUN_ID, "notify_slack", "-", REPORT_ID)
    assert action.result.link_urls.diagnostic_url is None


@pytest.mark.parametrize("broken", ["build_message", "get_proposals"])
async def test_a_message_that_cannot_be_built_is_never_dispatching(seeded, sent, monkeypatch, broken) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("cannot build")

    async def aboom(*args, **kwargs):
        raise RuntimeError("transient read error")

    if broken == "build_message":
        monkeypatch.setattr(slack, "build_message", boom)
    else:
        monkeypatch.setattr(records, "get_proposals", aboom)
    action = await actions.dispatch(a10_action(make_report()), run_ctx())
    assert action.status == "failed" and action.claimed_at is None
    assert action.result.http_status is None and action.result.posted_at is None
    assert sent.sent == []
    assert [e["status"] for e in seeded.events] == ["failed"]  # never dispatching


# --- A05's scan ---------------------------------------------------------------


@pytest.fixture
def scan_db(mem, monkeypatch):
    monkeypatch.setattr(scan, "_db", lambda: mem)
    return mem


def put_search(mem, action_id: str = "act_00000000000000f1") -> str:
    mem["actions"].docs[action_id] = {"_id": action_id, "kind": "search_source", "status": "queued", "run_id": RUN_ID,
                                      "decision_id": "dec_00000000000000f1", "target": {"scope_id": SCOPE_ID}}
    return action_id


async def test_a05_claim_and_settle_delivered(scan_db) -> None:
    action_id = put_search(scan_db)
    assert await scan._claim(action_id) is None  # claimed by this worker
    again = await scan._claim(action_id)
    assert again["status"] == "dispatching"  # a repeat reads the existing action
    result = {"http_status": 200, "cursor_from": "2026-11-11", "cursor_to": "2026-11-12",
              "source_refs": [SOURCE_REF], "count": 1}
    assert await scan._settle(action_id, "delivered", result) is True
    assert await scan._settle(action_id, "delivered", result) is False
    doc = await records.get(action_id)
    assert doc["status"] == "delivered" and doc["result"] == result


async def test_a05_failed_fetch_with_no_http_status(scan_db) -> None:
    action_id = put_search(scan_db)
    assert await scan._claim(action_id) is None
    failed = {"http_status": None, "cursor_from": "2026-11-11", "cursor_to": "2026-11-11", "source_refs": [], "count": 0}
    assert await scan._settle(action_id, "failed", failed) is True
    assert (await records.get(action_id))["status"] == "failed"
    assert await scan._settle(None, "failed", failed) is True  # no action: nothing to settle
