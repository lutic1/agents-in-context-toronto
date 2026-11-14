"""A09 against the Atlas Sandbox, in the session's own `dxp_test_<hex>` database (never `dxp`).

Skipped with the stated reason when MONGODB_URI is unset. Slack is A01's `fake_slack`.
"""

from __future__ import annotations

import asyncio

import pytest

from dxp import actions
from dxp.actions import records, slack

from .conftest import make_proposals, make_report, notify, reviewer_ctx, run_ctx

pytestmark = [pytest.mark.atlas, pytest.mark.usefixtures("gate")]


async def seed_report(db, report_id: str) -> None:
    # Test fixtures only: the report and proposals are A19+A20's documents, inserted here
    # without their validators; A09's own `actions` writes are validated.
    await db["reports"].insert_one(make_report(_id=report_id), bypass_document_validation=True)
    for p in make_proposals():
        await db["proposals"].update_one({"_id": p["_id"]}, {"$setOnInsert": p}, upsert=True, bypass_document_validation=True)


async def test_atlas_delivered_once_with_two_workers(db, fake_slack) -> None:
    report_id = "rep_a09atlas000001"
    await seed_report(db, report_id)

    async def slow(*args, **kwargs):
        await asyncio.sleep(0.05)
        return await fake_slack(*args, **kwargs)

    with slack.use_sender(slow):
        results = await asyncio.gather(*(actions.dispatch(notify(report_id=report_id), run_ctx()) for _ in range(4)))
    assert len(fake_slack.sent) == 1
    doc = await db["actions"].find_one({"_id": results[0].id})
    assert doc["status"] == "delivered" and doc["result"]["http_status"] == 200
    assert doc["result"]["link_urls"]["diagnostic_url"] is None
    assert await db["actions"].count_documents({"target.report_id": report_id, "kind": "notify_slack"}) == 1
    events = await db["events"].find({"action_id": doc["_id"], "type": "action_status_changed"}).to_list(None)
    assert sorted(e["status"] for e in events) == ["delivered", "dispatching"]


async def test_atlas_unknown_then_resolved_and_swept(db, fake_slack) -> None:
    report_id = "rep_a09atlas000002"
    await seed_report(db, report_id)
    fake_slack.fail()
    with slack.use_sender(fake_slack):
        action = await actions.dispatch(notify(report_id=report_id), run_ctx())
    assert action.status == "unknown"
    resolved, decision = await actions.resolve(action.id, "delivered", "seen in channel", reviewer_ctx())
    assert resolved.status == "delivered" and resolved.resolution.decision_id == decision.id
    assert await actions.mark_unknown(action.id, "abandoned_in_flight") is False
    assert (await records.get(action.id))["status"] == "delivered"
