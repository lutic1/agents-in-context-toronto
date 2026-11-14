"""A09: mark_unknown and mark_failed for the sweep (D24, D43): conditional, never posting."""

from __future__ import annotations

import pytest

from dxp import actions
from dxp.actions import records


def put(mem, status: str, action_id: str = "act_00000000000000d1") -> str:
    mem["actions"].docs[action_id] = {"_id": action_id, "kind": "notify_slack", "status": status, "run_id": "run_x", "target": {}}
    return action_id


async def test_mark_unknown_moves_only_dispatching(mem) -> None:
    action_id = put(mem, "dispatching")
    assert await actions.mark_unknown(action_id, "abandoned_in_flight") is True
    doc = await records.get(action_id)
    assert doc["status"] == "unknown" and doc["error"] == "abandoned_in_flight" and doc["observed_at"]
    assert await actions.mark_unknown(action_id, "abandoned_in_flight") is False
    assert [e["status"] for e in mem.events] == ["unknown"]


@pytest.mark.parametrize("status", ["queued", "delivered", "failed", "unknown"])
async def test_mark_unknown_never_overwrites(mem, status) -> None:
    action_id = put(mem, status)
    assert await actions.mark_unknown(action_id, "abandoned_in_flight") is False
    assert (await records.get(action_id))["status"] == status


async def test_mark_failed_moves_only_queued(mem) -> None:
    action_id = put(mem, "queued")
    assert await actions.mark_failed(action_id, "abandoned_before_send") is True
    doc = await records.get(action_id)
    assert doc["status"] == "failed" and doc["error"] == "abandoned_before_send"


@pytest.mark.parametrize("status", ["dispatching", "delivered", "unknown"])
async def test_mark_failed_never_overwrites(mem, status) -> None:
    action_id = put(mem, status)
    assert await actions.mark_failed(action_id, "abandoned_before_send") is False
    assert (await records.get(action_id))["status"] == status


async def test_wrong_reasons_are_refused(mem) -> None:
    with pytest.raises(ValueError):
        await actions.mark_unknown(put(mem, "dispatching"), "abandoned_before_send")
    with pytest.raises(ValueError):
        await actions.mark_failed(put(mem, "queued", "act_00000000000000d2"), "abandoned_in_flight")


async def test_unknown_action_is_a_no_op(mem) -> None:
    assert await actions.mark_unknown("act_missing", "abandoned_in_flight") is False
