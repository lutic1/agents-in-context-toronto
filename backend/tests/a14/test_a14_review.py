"""A14, Story 2.3: `POST /diagnostics/<dx_id>/values/<value_id>/review` (D16), through the gate."""

from __future__ import annotations

import pytest

from tests.a14.conftest import (
    DX_ID,
    HEADERS,
    SEED_KEY,
    diagnostic_doc,
)

URL = f"/api/v1/diagnostics/{DX_ID}/values/{{value_id}}/review"


@pytest.fixture
def gate(fake_gate, fake_db, monkeypatch):
    """The conftest fake gate, plus what A06's gate stores: the Decision and, when allowed, a
    queued action pointing back to it."""
    import dxp.gate

    async def evaluate(ctx, action):
        decision = await fake_gate.evaluate(ctx, action)
        if decision.outcome == "allowed":
            decision = decision.model_copy(update={"action_id": f"act_{decision.id}"})
            await fake_db["actions"].insert_one({"_id": decision.action_id, "decision_id": decision.id, "status": "queued"})
        await fake_db["decisions"].insert_one({**decision.model_dump(), "_id": decision.id})
        return decision

    async def evaluate_in(ctx, action, session):
        return await evaluate(ctx, action)

    calls = fake_gate.mark_action_calls = []

    async def mark_action(action_id, status, result=None, *, session=None):
        """A06's gate.mark_action: queued -> done or failed, with the deduplicated event."""
        calls.append((action_id, status))
        res = await fake_db["actions"].update_one(
            {"_id": action_id, "status": "queued"}, {"$set": {"status": status, "result": result}}
        )
        if res.modified_count:
            decision = fake_db["decisions"].docs[fake_db["actions"].docs[action_id]["decision_id"]]
            await dxp.store.emit_event(
                "action_status_changed",
                dedupe_key=f"action_status_changed|{action_id}|{status}",
                stamp=decision["stamp"],
                action_id=action_id,
                status=status,
            )
        return bool(res.modified_count)

    import dxp.store

    monkeypatch.setattr(dxp.gate, "evaluate", evaluate)
    # A06's transaction and action functions; on main once PR #15 merges.
    monkeypatch.setattr(dxp.gate, "evaluate_in", evaluate_in, raising=False)
    monkeypatch.setattr(dxp.gate, "mark_action", mark_action, raising=False)
    return fake_gate


@pytest.fixture
def seeded(fake_db, principals, recoveries):
    fake_db["diagnostics"].docs[DX_ID] = diagnostic_doc()
    return fake_db


def _post(api_client, value_id, **body):
    return api_client.post(URL.format(value_id=value_id), json=body, headers=HEADERS)


def _entries(fake_db, field):
    return {e["value_id"]: e for e in fake_db["diagnostics"].docs[DX_ID]["fields"][field]}


def test_accept(api_client, seeded, gate, recoveries):
    response = _post(api_client, "v_modality", action="accept")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"]["kind"] == "review_value" and body["decision"]["outcome"] == "allowed"
    value = body["record"]["fields"]["modality"]["values"][0]
    assert value["review"] == "accepted" and value["decided_by"] == "sam" and value["decided_at"]
    assert seeded["diagnostics"].docs[DX_ID]["rev"] == 6
    assert recoveries == ["recover_applying"]  # apply recovery ran on the decision call (D26)
    assert gate.mark_action_calls == [(body["decision"]["action_id"], "done")]  # through the gate (V65)
    action = seeded["actions"].docs[body["decision"]["action_id"]]
    assert action["status"] == "done" and action["result"]["value_ids"] == ["v_modality"]
    event = next(e for e in seeded["events"].docs.values() if e["type"] == "action_status_changed")
    assert event["stamp"]["kind"] == "reviewer" and event["stamp"]["principal"] == "sam"


def test_gate_sees_a_reviewer_decision(api_client, seeded, gate):
    _post(api_client, "v_modality", action="accept")
    ((ctx, action),) = gate.calls
    assert action.kind == "review_value" and action.destination == "ledger"
    assert action.target.diagnostic_id == DX_ID and action.target.value_id == "v_modality"
    assert ctx.run_id is None and ctx.request_id.startswith("req_")
    assert ctx.stamp.kind == "reviewer" and ctx.stamp.agent is None and ctx.stamp.initiated_by == "sam"
    assert ctx.grant_id == "sam"
    assert ctx.cause.proposal_id == "p_modality" and ctx.cause.origin_run_id is None  # a seed value


def test_edit_keeps_history(api_client, seeded, gate):
    response = _post(api_client, "v_modality", action="edit", value="digital PCR", reason="the FDA row says ddPCR")
    assert response.status_code == 200, response.text
    values = {v["value_id"]: v for v in response.json()["record"]["fields"]["modality"]["values"]}
    old = values["v_modality"]
    assert old["state"] == "superseded" and old["reason"] == "the FDA row says ddPCR" and old["decided_by"] == "sam"
    (new,) = [v for k, v in values.items() if k != "v_modality"]
    assert new["value"] == "pcr" and new["label"] == "digital PCR"
    assert new["state"] == "current" and new["review"] == "edited"
    assert new["evidence"]["version_id"] == old["evidence"]["version_id"]  # the pinned version stays (V40)
    assert new["stamp"]["kind"] == "reviewer"
    assert seeded["diagnostics"].docs[DX_ID]["facets"]["modality"] == ["pcr"]


def test_edit_of_lifecycle_stage_moves_the_stage(api_client, seeded, gate):
    response = _post(api_client, "v_stage", action="edit", value="clinical_utility", reason="not yet approved here")
    assert response.status_code == 200, response.text
    assert response.json()["record"]["lifecycle_stage"] == "clinical_utility"


def test_reject(api_client, seeded, gate):
    response = _post(api_client, "v_plasma", action="reject", reason="the row names tissue")
    assert response.status_code == 200, response.text
    (value,) = response.json()["record"]["fields"]["sample_types"]["values"]
    assert value["state"] == "rejected" and value["reason"] == "the row names tissue"
    assert value["evidence"]["quote"]  # nothing is deleted


@pytest.mark.parametrize("action", ["edit", "reject"])
def test_edit_and_reject_need_a_reason(api_client, seeded, gate, action):
    response = _post(api_client, "v_modality", action=action, value="pcr", reason="  ")
    assert response.status_code == 400 and response.json()["error"]["code"] == "reason_required"
    assert gate.calls == []  # refused before the gate
    assert seeded["diagnostics"].docs[DX_ID]["rev"] == 5


def test_edit_outside_the_allowed_values_is_400(api_client, seeded, gate):
    response = _post(api_client, "v_modality", action="edit", value="tea leaves", reason="x")
    assert response.status_code == 400 and response.json()["error"]["code"] == "invalid_value"
    assert gate.calls == []


def test_unknown_value_and_diagnostic_are_404(api_client, seeded, gate):
    assert _post(api_client, "v_nope", action="accept").status_code == 404
    response = api_client.post("/api/v1/diagnostics/dx_nope/values/v_modality/review", json={"action": "accept"}, headers=HEADERS)
    assert response.status_code == 404


def test_only_unreviewed_values(api_client, seeded, gate):
    response = _post(api_client, "v_trial", action="accept")  # accepted through its report
    assert response.status_code == 409 and response.json()["error"]["code"] == "not_unreviewed"
    assert gate.calls == []


def test_blocked_review_changes_nothing(api_client, seeded, gate):
    gate.block("review_value", "team_scope")
    before = seeded["diagnostics"].docs[DX_ID]
    response = _post(api_client, "v_modality", action="accept")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"]["outcome"] == "blocked" and body["decision"]["failed_check"] == "team_scope"
    assert body["record"]["fields"]["modality"]["values"][0]["review"] == "unreviewed"
    assert seeded["diagnostics"].docs[DX_ID] == before
    assert seeded["actions"].docs == {}


def test_second_review_returns_the_current_state(api_client, seeded, gate):
    first = _post(api_client, "v_modality", action="accept").json()
    second = _post(api_client, "v_modality", action="reject", reason="changed my mind")
    assert second.status_code == 200, second.text
    assert second.json()["decision"]["id"] == first["decision"]["id"]
    assert second.json()["record"] == first["record"]
    assert len(gate.calls) == 1
    assert seeded["diagnostics"].docs[DX_ID]["rev"] == 6


def test_caller_comes_from_the_key(api_client, seeded, gate):
    assert api_client.post(URL.format(value_id="v_modality"), json={"action": "accept"}).status_code == 401
    seed = api_client.post(URL.format(value_id="v_modality"), json={"action": "accept"}, headers={"X-DxP-Key": SEED_KEY})
    assert seed.status_code == 403
    # A name in the body confers nothing.
    response = api_client.post(
        URL.format(value_id="v_modality"), json={"action": "accept", "actor": "someone"}, headers=HEADERS
    )
    assert response.json()["record"]["fields"]["modality"]["values"][0]["decided_by"] == "sam"


def test_rejecting_the_only_value_leaves_no_data(api_client, seeded, gate):
    response = _post(api_client, "v_plasma", action="reject", reason="the row names tissue")
    field = response.json()["record"]["fields"]["sample_types"]
    assert field["no_data"] is True and field["values"][0]["state"] == "rejected"  # history kept


def test_caller_is_checked_before_the_input(api_client, seeded, gate):
    response = api_client.post(URL.format(value_id="v_modality"), json={"action": "reject"})
    assert response.status_code == 401
