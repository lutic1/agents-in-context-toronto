"""A09: manual resolution of an unknown alert, actions.resolve and its route (S8, D25, D49)."""

from __future__ import annotations

import pytest

from dxp import actions
from dxp.actions import records
from dxp.api.models import Principal

from .conftest import REPORT_ID, RUN_ID, notify, reviewer_ctx, run_ctx

pytestmark = pytest.mark.usefixtures("gate")


async def unknown_action(seeded, sent) -> str:
    sent.fail()
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "unknown"
    return action.id


@pytest.mark.parametrize("outcome", ["delivered", "failed"])
async def test_resolves_an_unknown_alert_through_the_gate(seeded, sent, gate, outcome) -> None:
    action_id = await unknown_action(seeded, sent)
    action, decision = await actions.resolve(action_id, outcome, "Seen in #all-mango-db-hackathon at 14:31", reviewer_ctx())

    assert action.status == outcome
    assert action.resolution.outcome == outcome and action.resolution.by == "sam"
    assert action.resolution.decision_id == decision.id and action.resolution.note.startswith("Seen")
    ctx, proposed = gate.calls[-1]
    assert proposed.kind == "resolve_notification" and proposed.destination == "ledger"
    assert proposed.inputs["action_id"] == action_id
    assert ctx.run_id is None and ctx.request_id
    assert ctx.cause.action_id == action_id and ctx.cause.origin_run_id == RUN_ID
    assert decision.outcome == "allowed"
    assert len(sent.sent) == 1  # never posts


async def test_only_an_unknown_alert_can_be_resolved(seeded, sent) -> None:
    action = await actions.dispatch(notify(), run_ctx())
    assert action.status == "delivered"
    with pytest.raises(actions.NotResolvable):
        await actions.resolve(action.id, "failed", "n", reviewer_ctx())
    assert (await records.get(action.id))["status"] == "delivered"


async def test_a_second_resolution_is_refused(seeded, sent) -> None:
    action_id = await unknown_action(seeded, sent)
    await actions.resolve(action_id, "delivered", "seen", reviewer_ctx())
    with pytest.raises(actions.NotResolvable):
        await actions.resolve(action_id, "failed", "again", reviewer_ctx())


async def test_missing_action_and_missing_note(seeded, sent, gate) -> None:
    with pytest.raises(actions.ActionNotFound):
        await actions.resolve("act_ffffffffffffffff", "delivered", "n", reviewer_ctx())
    action_id = await unknown_action(seeded, sent)
    calls = len(gate.calls)
    with pytest.raises(actions.NoteRequired):
        await actions.resolve(action_id, "delivered", "  ", reviewer_ctx())
    assert len(gate.calls) == calls  # refused before the gate (D16)


async def test_blocked_resolution_changes_nothing(seeded, sent, gate) -> None:
    action_id = await unknown_action(seeded, sent)
    gate.block("resolve_notification", "grant_active")
    action, decision = await actions.resolve(action_id, "delivered", "seen", reviewer_ctx())
    assert decision.outcome == "blocked" and action.status == "unknown" and action.resolution is None


# --- the route -----------------------------------------------------------------


@pytest.fixture
def reviewer(monkeypatch):
    from dxp.api import auth

    principals = {
        "sam-key": Principal(id="sam", name="Sam", kind="person", actions=["resolve_notification"]),
        "seed-key": Principal(id="seed", name="seed", kind="seed"),
    }

    async def resolve_actor(key: str) -> Principal:
        from dxp.api.errors import ApiError

        if key not in principals:
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return principals[key]

    async def latest_grant_of(principal_id: str):
        return {"grant_id": "sam", "version": 1, "principal": "sam", "kind": "person"} if principal_id == "sam" else None

    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)
    monkeypatch.setattr(records, "latest_grant_of", latest_grant_of)


def post(api_client, action_id: str, key: str | None = "sam-key", **body):
    headers = {"X-DxP-Key": key} if key else {}
    return api_client.post(f"/api/v1/actions/{action_id}/resolve", json={"outcome": "delivered", "note": "seen", **body}, headers=headers)


async def test_route_resolves(seeded, sent, reviewer, api_client) -> None:
    action_id = await unknown_action(seeded, sent)
    response = post(api_client, action_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action"]["status"] == "delivered"
    assert body["action"]["resolution"]["by"] == "sam"
    assert body["decision"]["kind"] == "resolve_notification" and body["decision"]["run_id"] is None
    assert body["action"]["target"]["report_id"] == REPORT_ID


async def test_route_errors(seeded, sent, reviewer, api_client) -> None:
    action_id = await unknown_action(seeded, sent)
    assert post(api_client, action_id, key=None).status_code == 401
    assert post(api_client, action_id, key="nope").status_code == 401
    assert post(api_client, action_id, key="seed-key").status_code == 403
    assert post(api_client, "act_ffffffffffffffff").json()["error"]["code"] == "action_not_found"
    missing_note = post(api_client, action_id, note=" ")
    assert missing_note.status_code == 422 and missing_note.json()["error"]["code"] == "note_required"
    assert post(api_client, action_id, outcome="maybe").status_code == 422
    assert post(api_client, action_id).status_code == 200
    conflict = post(api_client, action_id)
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "not_unknown"
