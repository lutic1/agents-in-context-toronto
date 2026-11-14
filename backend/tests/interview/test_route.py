"""POST /reports/{report_id}/interview behind the `interview` flag (404 when off), with the auth and grant
reads faked (no Atlas) and the gate and llm faked."""

from __future__ import annotations

import pytest

from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.gate import policy_sets

from .conftest import Q_STATUS, REPORT_ID, FakeLlm, make_report, quote_id

URL = f"/api/v1/reports/{REPORT_ID}/interview"
HEADERS = {"X-DxP-Key": "test-dxp-api-key"}


@pytest.fixture
def signed_in(monkeypatch: pytest.MonkeyPatch):
    """A Reviewer with the grant: sam@v2 carries answer_question."""
    state = {"actions": ["answer_question"], "grant": {"grant_id": "sam", "version": 2, "acting_for": "team_liquid"}}

    async def require_principal(request):
        if not request.headers.get("X-DxP-Key"):
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return m.Principal(id="sam", name="Sam", kind="person", actions=state["actions"])

    async def grant_for_key(api_key, db=None):
        return state["grant"]

    async def current_set():
        return m.PolicySet(id="ps_abcd", members=["p@v1"])

    monkeypatch.setattr(auth, "require_principal", require_principal)
    monkeypatch.setattr(auth, "grant_for_key", grant_for_key)
    monkeypatch.setattr(policy_sets, "current_set", current_set)
    return state


def test_flag_off_is_404_even_with_a_valid_key(api_client, store, fake_llm, fake_gate, signed_in) -> None:
    response = api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert fake_llm.calls == [] and fake_gate.calls == []


def test_flag_off_is_404_before_the_key_is_looked_at(api_client, store, fake_llm, fake_gate) -> None:
    assert api_client.post(URL, json={"question": "Is the trial recruiting?"}).status_code == 404


def test_other_flags_do_not_turn_interview_on(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("avatar", "briefing", "revert")
    assert api_client.post(URL, json={"question": "x"}, headers=HEADERS).status_code == 404


def test_answers_with_the_flag_on(api_client, features, store, fake_llm: FakeLlm, fake_gate, signed_in) -> None:
    features("interview")
    fake_llm.ids = [quote_id(Q_STATUS)]
    response = api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"answer", "citations", "refused", "refusal_reason", "decision_id"}
    assert body["answer"] == f'The accepted record says: "{Q_STATUS}" [1]'
    assert body["citations"][0]["quote"] == Q_STATUS
    assert body["refused"] is False and body["refusal_reason"] is None
    assert body["decision_id"].startswith("dec_")


def test_the_gate_gets_a_reviewer_context(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    fake_llm.ids = []
    api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    ctx, action = fake_gate.calls[0]
    assert ctx.run_id is None and ctx.stamp.kind == "reviewer" and ctx.stamp.agent is None
    assert (ctx.grant_id, ctx.grant_version) == ("sam", 2)
    assert ctx.policy_set_version == "ps_abcd"
    assert ctx.request_id.startswith("req_")
    assert ctx.cause.report_id == REPORT_ID and ctx.cause.origin_run_id == "run_0123456789abcdef"
    assert action.kind == "answer_question"


def test_every_question_gets_its_own_request_id(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    fake_llm.ids = []
    for _ in range(2):
        api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert fake_gate.calls[0][0].request_id != fake_gate.calls[1][0].request_id


def test_medical_advice_over_http_makes_no_model_call(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    response = api_client.post(URL, json={"question": "Should I or my patient start therapy?"}, headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True and body["refusal_reason"] == "medical_advice" and body["citations"] == []
    assert fake_llm.calls == []


def test_blocked_is_a_200_not_an_error(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    fake_gate.block("answer_question", "destination_action")
    fake_llm.ids = [quote_id(Q_STATUS)]
    response = api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["refusal_reason"] == "blocked" and response.json()["refused"] is True


def test_a_caller_without_the_grant_gets_a_blocked_decision(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    signed_in["actions"] = ["decide_report"]
    fake_llm.ids = [quote_id(Q_STATUS)]
    response = api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert response.json()["refusal_reason"] == "blocked"
    assert fake_llm.calls == []


def test_no_key_is_401(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    response = api_client.post(URL, json={"question": "x"})
    assert response.status_code == 401


def test_unknown_report_is_404(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    response = api_client.post("/api/v1/reports/rep_ffffffffffffffff/interview", json={"question": "x"}, headers=HEADERS)
    assert response.status_code == 404 and response.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("status", ["pending", "rejected", "reverted"])
def test_report_not_accepted_is_409(status, api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    store.reports[REPORT_ID] = make_report(status=status)
    response = api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "report_not_accepted"
    assert fake_llm.calls == [] and fake_gate.calls == []


@pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "x" * 501}, {"question": 5}])
def test_a_bad_question_is_422(body, api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    assert api_client.post(URL, json=body, headers=HEADERS).status_code == 422


def test_a_500_character_question_is_accepted(api_client, features, store, fake_llm, fake_gate, signed_in) -> None:
    features("interview")
    fake_llm.ids = []
    response = api_client.post(URL, json={"question": "Is it recruiting? " + "a" * 482}, headers=HEADERS)
    assert response.status_code == 200
    assert len(fake_gate.calls[0][1].inputs["question"]) <= 200


def test_the_gate_not_on_main_is_501_in_the_error_shape(api_client, features, store, fake_llm, signed_in, monkeypatch) -> None:
    import dxp.gate

    async def not_built(ctx, action):
        raise NotImplementedError("gate.evaluate (A06)")

    monkeypatch.setattr(dxp.gate, "evaluate", not_built)
    features("interview")
    fake_llm.ids = []
    response = api_client.post(URL, json={"question": "Is the trial recruiting?"}, headers=HEADERS)
    assert response.status_code == 501 and response.json()["error"]["code"] == "not_implemented"


def test_the_route_matches_the_published_contract() -> None:
    from dxp.api.app import create_app

    spec = create_app().openapi()
    operation = spec["paths"]["/api/v1/reports/{report_id}/interview"]["post"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/InterviewResponse")
