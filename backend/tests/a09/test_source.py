"""A09: record_source_result for A05's search_source action (D24, AD-19, Luis's ruling)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dxp import actions
from dxp.actions import records

RESULT = {"http_status": 200, "cursor_from": "2026-11-11", "cursor_to": "2026-11-12",
          "source_refs": ["ctgov:NCT04712877"], "count": 1}


def put(mem, status: str, kind: str = "search_source", action_id: str = "act_00000000000000e1") -> str:
    mem["actions"].docs[action_id] = {"_id": action_id, "kind": kind, "status": status, "run_id": "run_x",
                                      "decision_id": "dec_00000000000000e1", "target": {"scope_id": "s"}}
    return action_id


async def test_claim_then_delivered(mem) -> None:
    action_id = put(mem, "queued")
    assert await actions.record_source_result(action_id, status="dispatching", result=None) is True
    assert await actions.record_source_result(action_id, status="dispatching", result=None) is False  # claimed once
    assert await actions.record_source_result(action_id, status="delivered", result=RESULT) is True
    doc = await records.get(action_id)
    assert doc["status"] == "delivered" and doc["result"] == RESULT
    assert doc["claimed_at"] and doc["observed_at"]
    assert [e["status"] for e in mem.events] == ["dispatching", "delivered"]
    assert all(e["action_id"] == action_id and e["decision_id"] == "dec_00000000000000e1" for e in mem.events)


async def test_failed_from_dispatching(mem) -> None:
    action_id = put(mem, "dispatching")
    failed = {**RESULT, "http_status": None, "cursor_to": "2026-11-11", "source_refs": [], "count": 0}
    assert await actions.record_source_result(action_id, status="failed", result=failed) is True
    assert (await records.get(action_id))["status"] == "failed"


@pytest.mark.parametrize("current", ["queued", "delivered", "failed", "unknown"])
async def test_settling_is_conditional_on_dispatching(mem, current) -> None:
    action_id = put(mem, current)
    assert await actions.record_source_result(action_id, status="delivered", result=RESULT) is False
    assert (await records.get(action_id))["status"] == current


async def test_only_search_source_actions(mem) -> None:
    action_id = put(mem, "queued", kind="notify_slack")
    assert await actions.record_source_result(action_id, status="dispatching", result=None) is False
    assert (await records.get(action_id))["status"] == "queued"


async def test_arguments_are_checked(mem) -> None:
    action_id = put(mem, "dispatching")
    with pytest.raises(ValueError):
        await actions.record_source_result(action_id, status="unknown", result=RESULT)
    with pytest.raises(ValueError):
        await actions.record_source_result(action_id, status="delivered", result=None)
    with pytest.raises(ValueError):
        await actions.record_source_result(put(mem, "queued", action_id="act_00000000000000e2"), status="dispatching", result=RESULT)
    with pytest.raises(ValidationError):
        await actions.record_source_result(action_id, status="delivered", result={**RESULT, "extra": 1})
    assert (await records.get(action_id))["status"] == "dispatching"
