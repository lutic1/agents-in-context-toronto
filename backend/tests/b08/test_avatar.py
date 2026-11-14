"""B08: the LiveAvatar token minter, gated, on demand, never blocking (Story 10.12, V29, V70)."""

from __future__ import annotations

import json
import logging
import pathlib

import httpx
import pytest

from dxp.api.models import AvatarResponse, RunContext
from dxp.briefing import avatar
from dxp.briefing.avatar import HttpLiveAvatarClient, LiveAvatarError

from dxp.briefing.avatar import DXP_AVATAR_ID, DXP_VOICE_ID, SANDBOX_AVATAR_ID, voice_id

from .conftest import ACTION_ID, AVATAR_ID, FAKE_KEY, REPORT_ID, SECRET_TOKEN

KEY_HEADERS = {"X-DxP-Key": "test-dxp-api-key"}
URL = f"/api/v1/reports/{REPORT_ID}/avatar"


def post(api_client):
    # No `with`: the startup hook needs Atlas, and these tests do not.
    return api_client.post(URL, headers=KEY_HEADERS)


# --- the flag --------------------------------------------------------------------


def test_flag_off_is_404_and_nothing_runs(api_client, reviewer, fake_gate, live, media_store, monkeypatch) -> None:
    monkeypatch.setenv("DXP_FEATURES", "")
    response = post(api_client)
    assert response.status_code == 404
    assert api_client.get(URL, headers=KEY_HEADERS).status_code == 404
    assert fake_gate.calls == [] and live.calls == [] and media_store.media == []


# --- reviewer only ---------------------------------------------------------------


def test_an_agent_principal_gets_403_and_records_nothing(api_client, monkeypatch, fake_gate, live, media_store) -> None:
    from dxp.api import auth
    from dxp.api.models import Principal

    agent = Principal(id="agent_1", name="Agent", kind="agent", actions=["generate_avatar_video"])

    async def resolve_actor(api_key: str) -> Principal:
        return agent

    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)
    response = post(api_client)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert fake_gate.calls == [] and live.calls == [] and media_store.media == []
    assert media_store.actions == {}  # no Decision, so no action either


# --- not accepted ----------------------------------------------------------------


@pytest.mark.parametrize("status", ["pending", "accepting", "rejected", "reverting", "reverted"])
def test_a_report_that_is_not_accepted_is_409_with_no_gate_and_no_provider_call(
    api_client, reviewer, fake_gate, live, media_store, status
) -> None:
    media_store.reports[REPORT_ID]["status"] = status
    response = post(api_client)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "report_not_accepted"
    assert fake_gate.calls == [] and live.calls == [] and media_store.media == []


# --- allowed -------------------------------------------------------------------


def test_allowed_returns_the_token_only_in_the_response_field(api_client, reviewer, fake_gate, live, media_store, caplog) -> None:
    with caplog.at_level(logging.DEBUG):
        response = post(api_client)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["decision"]["outcome"] == "allowed"
    assert body["session_token"] == SECRET_TOKEN
    assert body["session_expires_at"] is not None
    assert set(body) == {"media", "decision", "session_token", "session_expires_at"}
    assert body["media"]["status"] == "ready"
    assert body["media"]["video_url"] is None
    assert body["media"]["provider_video_id"] == "sess_fake_1"
    assert FAKE_KEY not in response.text
    # exactly one provider call, with a short max duration and the configured avatar
    assert live.calls == [{"avatar_id": AVATAR_ID, "max_session_duration": 180, "is_sandbox": False}]
    # the token is nowhere else: not in the media response, the stored media, any document or the logs
    assert SECRET_TOKEN not in json.dumps(body["media"]) and SECRET_TOKEN not in json.dumps(body["decision"])
    assert len(media_store.media) == 1
    assert SECRET_TOKEN not in json.dumps(media_store.media, default=str)
    assert SECRET_TOKEN not in json.dumps(media_store.reports, default=str)
    assert SECRET_TOKEN not in caplog.text and FAKE_KEY not in caplog.text
    assert media_store.media[0]["decision_id"] == body["decision"]["id"]
    assert media_store.media[0]["report_id"] == REPORT_ID and media_store.media[0]["status"] == "ready"
    # nothing the gate saw carries the token either (it records documents)
    assert SECRET_TOKEN not in repr(fake_gate.calls)
    # the response is the contract model, nothing else
    AvatarResponse.model_validate(body)


def test_the_gate_is_asked_first_as_a_reviewer(api_client, reviewer, fake_gate) -> None:
    post(api_client)
    (ctx, action), = fake_gate.calls
    assert action.kind == "generate_avatar_video"
    assert action.destination == "video:heygen"
    assert action.target.report_id == REPORT_ID
    assert isinstance(ctx, RunContext)
    assert ctx.run_id is None and ctx.stamp.kind == "reviewer" and ctx.stamp.agent is None
    assert ctx.stamp.initiated_by == "sam" and ctx.grant_id == "sam"
    assert ctx.cause is not None and ctx.cause.report_id == REPORT_ID
    assert ctx.request_id and ctx.request_id.startswith("req_")


def test_sandbox_and_duration_come_from_the_environment(api_client, reviewer, fake_gate, live, monkeypatch) -> None:
    monkeypatch.setenv("LIVEAVATAR_SANDBOX", "true")
    monkeypatch.setenv("LIVEAVATAR_MAX_SECONDS", "60")
    post(api_client)
    assert live.calls[0]["is_sandbox"] is True and live.calls[0]["max_session_duration"] == 60
    # Sandbox sessions accept only the free sandbox avatar, whatever LIVEAVATAR_AVATAR_ID says.
    assert live.calls[0]["avatar_id"] == SANDBOX_AVATAR_ID


def test_an_unset_avatar_id_uses_dxp_avatar_outside_sandbox(api_client, reviewer, fake_gate, live, monkeypatch) -> None:
    monkeypatch.delenv("LIVEAVATAR_AVATAR_ID")
    body = post(api_client).json()
    assert body["session_token"] == SECRET_TOKEN
    assert live.calls == [{"avatar_id": DXP_AVATAR_ID, "max_session_duration": 180, "is_sandbox": False}]
    assert DXP_AVATAR_ID == "eb961787-3605-49e9-b703-3402c12ccdb4"
    assert SANDBOX_AVATAR_ID == "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a"


def test_voice_id_defaults_to_dxp_voice_and_env_overrides(monkeypatch) -> None:
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    assert voice_id() == DXP_VOICE_ID == "4d175bd2-b678-46f6-bb01-38b2270147fa"
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice-override")
    assert voice_id() == "voice-override"


# --- blocked -------------------------------------------------------------------


def test_blocked_records_a_decision_and_makes_no_provider_call(api_client, reviewer, fake_gate, live, media_store) -> None:
    fake_gate.block("generate_avatar_video", "destination_action")
    response = post(api_client)
    assert response.status_code == 200  # a blocked action is not an error (D5)
    body = response.json()
    assert body["decision"]["outcome"] == "blocked"
    assert body["decision"]["failed_check"] == "destination_action"
    assert body["decision"]["id"]
    assert len(fake_gate.calls) == 1  # the gate recorded the Decision
    assert body["session_token"] is None and body["session_expires_at"] is None
    assert body["media"]["status"] == "unavailable"
    assert live.calls == []
    assert media_store.media == []
    assert SECRET_TOKEN not in response.text


# --- unavailable ---------------------------------------------------------------


@pytest.mark.parametrize("status", [401, 402, 429, 500, None])
def test_provider_failure_is_unavailable_and_leaks_nothing(api_client, reviewer, fake_gate, live, media_store, caplog, status) -> None:
    live.fail(status)
    with caplog.at_level(logging.DEBUG):
        response = post(api_client)
    assert response.status_code == 200
    body = response.json()
    assert body["session_token"] is None and body["session_expires_at"] is None
    assert body["media"]["status"] == "unavailable"
    assert body["decision"]["outcome"] == "allowed"
    assert media_store.media[0]["status"] == "unavailable" and media_store.media[0]["provider_video_id"] is None
    assert FAKE_KEY not in response.text and FAKE_KEY not in caplog.text


def test_an_unexpected_provider_exception_is_handled(api_client, reviewer, fake_gate, live, media_store, monkeypatch) -> None:
    async def boom(**kwargs):
        raise RuntimeError("socket exploded with " + FAKE_KEY)

    monkeypatch.setattr(live, "create_session_token", boom)
    response = post(api_client)
    assert response.status_code == 200 and response.json()["media"]["status"] == "unavailable"
    assert FAKE_KEY not in response.text


def test_no_key_is_unavailable_and_makes_no_call(api_client, reviewer, fake_gate, live, media_store, monkeypatch) -> None:
    monkeypatch.delenv("LIVEAVATAR_API_KEY")
    body = post(api_client).json()
    assert body["session_token"] is None
    assert body["media"]["status"] == "unavailable"
    assert body["decision"]["outcome"] == "allowed"
    assert live.calls == []
    assert media_store.media[0]["status"] == "unavailable"


def test_blank_key_counts_as_no_key(api_client, reviewer, fake_gate, live, monkeypatch) -> None:
    monkeypatch.setenv("LIVEAVATAR_API_KEY", "   ")
    assert post(api_client).json()["media"]["status"] == "unavailable"
    assert live.calls == []


def test_the_heygen_key_name_is_no_longer_read(api_client, reviewer, fake_gate, live, monkeypatch) -> None:
    monkeypatch.delenv("LIVEAVATAR_API_KEY")
    monkeypatch.setenv("HEYGEN_API_KEY", "fallback-key")  # tests/conftest.py sets one by default
    body = post(api_client).json()
    assert body["session_token"] is None and live.calls == []


# --- report errors -------------------------------------------------------------


def test_unknown_report_is_404_in_the_error_shape_and_never_reaches_the_gate(api_client, reviewer, fake_gate, live) -> None:
    response = api_client.post("/api/v1/reports/rep_ffffffffffffffff/avatar", headers=KEY_HEADERS)
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Report not found."}}
    assert fake_gate.calls == [] and live.calls == []


def test_the_seed_key_and_unknown_keys_are_refused(api_client, monkeypatch, fake_gate, live) -> None:
    from dxp.api import auth
    from dxp.api.errors import ApiError

    async def refuse(api_key: str):
        raise ApiError(401, "unknown_key", "Unknown API key.")

    monkeypatch.setattr(auth, "resolve_actor", refuse)
    assert api_client.post(URL, headers={"X-DxP-Key": "nope"}).status_code == 401
    assert api_client.get(URL, headers={"X-DxP-Key": "nope"}).status_code == 401
    assert fake_gate.calls == [] and live.calls == []


# --- GET -----------------------------------------------------------------------


def test_get_is_404_before_any_request_then_returns_the_status_without_a_token(api_client, reviewer, fake_gate) -> None:
    assert api_client.get(URL, headers=KEY_HEADERS).status_code == 404
    api_client.post(URL, headers=KEY_HEADERS)
    got = api_client.get(URL, headers=KEY_HEADERS)
    assert got.status_code == 200
    media = got.json()
    assert media["status"] == "ready" and media["report_id"] == REPORT_ID and media["provider"] == "heygen"
    assert SECRET_TOKEN not in got.text and "session_token" not in media


# --- the frozen signatures -----------------------------------------------------


async def test_render_avatar_keeps_its_frozen_shape_and_drops_the_token(reviewer, fake_gate) -> None:
    ctx = await avatar.reviewer_context(reviewer, "k", {"_id": REPORT_ID, "run_id": None})
    media, decision = await avatar.render_avatar(REPORT_ID, ctx)
    assert media.status == "ready" and decision.outcome == "allowed"
    assert (await avatar.avatar_status(REPORT_ID)).id == media.id
    assert await avatar.avatar_status("rep_ffffffffffffffff") is None


# --- the HTTP client, against a mock transport (LiveAvatar is never called) -----


def _http_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    real = httpx.AsyncClient

    def factory(**kwargs):
        return real(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(avatar.httpx, "AsyncClient", factory)


async def test_http_client_sends_the_documented_full_mode_request(monkeypatch) -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(url=str(request.url), key=request.headers.get("X-API-KEY"), body=json.loads(request.content))
        return httpx.Response(200, json={"code": 1000, "data": {"session_id": "s-1", "session_token": "tok-1"}})

    _http_client(monkeypatch, handler)
    token = await HttpLiveAvatarClient(FAKE_KEY).create_session_token(avatar_id=AVATAR_ID, max_session_duration=120, is_sandbox=False)
    assert (token.session_id, token.session_token) == ("s-1", "tok-1")
    assert seen["url"] == "https://api.liveavatar.com/v1/sessions/token"
    assert seen["key"] == FAKE_KEY
    assert seen["body"] == {
        "mode": "FULL",
        "avatar_id": AVATAR_ID,
        "is_sandbox": False,
        "interactivity_type": "PUSH_TO_TALK",
        "max_session_duration": 120,
        "avatar_persona": {"language": "en"},
    }


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(401, json={"message": "bad key FAKE"}),
        httpx.Response(400, text="nope"),
        httpx.Response(200, json={"data": None}),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"data": {"session_id": "s", "session_token": ""}}),
    ],
)
async def test_http_client_failures_carry_no_body_and_no_key(monkeypatch, response) -> None:
    _http_client(monkeypatch, lambda request: response)
    with pytest.raises(LiveAvatarError) as caught:
        await HttpLiveAvatarClient(FAKE_KEY).create_session_token(avatar_id=AVATAR_ID, max_session_duration=120, is_sandbox=True)
    assert FAKE_KEY not in str(caught.value) and "FAKE" not in str(caught.value)


async def test_http_client_network_failure_is_a_liveavatar_error(monkeypatch) -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("could not connect to https://api.liveavatar.com with key " + FAKE_KEY)

    _http_client(monkeypatch, boom)
    with pytest.raises(LiveAvatarError) as caught:
        await HttpLiveAvatarClient(FAKE_KEY).create_session_token(avatar_id=AVATAR_ID, max_session_duration=120, is_sandbox=False)
    assert FAKE_KEY not in str(caught.value) and caught.value.status is None


# --- filing makes no LiveAvatar call -------------------------------------------


def test_nothing_in_the_loop_imports_the_avatar_or_reads_its_key() -> None:
    """V29: only B08's own route calls `briefing.avatar`; filing, Slack, the decision and the run never do."""
    root = pathlib.Path(avatar.__file__).resolve().parents[1]
    allowed = {"briefing/avatar.py", "briefing/__init__.py", "api/routes_avatar.py"}
    offenders = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel in allowed:
            continue
        text = path.read_text()
        if "LIVEAVATAR" in text or "briefing.avatar" in text or "render_avatar" in text or "start_avatar_session" in text:
            offenders.append(rel)
    # the app registers the router and the contract tests name the route; neither calls the avatar
    assert [o for o in offenders if o not in {"api/app.py"}] == []


# --- no voice input (Luis, V70) -------------------------------------------------


def test_no_web_code_starts_listening_or_uses_push_to_talk() -> None:
    """LiveAvatar has no non-listening mode, so PUSH_TO_TALK stays and nothing may ever signal it."""
    import re

    repo = pathlib.Path(__file__).resolve().parents[3]
    web = repo / "web"
    pattern = re.compile(r"push.?to.?talk|startListening|start_listening|start_push", re.IGNORECASE)
    skip = {"node_modules", ".next", ".git"}
    offenders = []
    for path in web.rglob("*"):
        if skip & set(path.relative_to(web).parts) or not path.is_file():
            continue
        if path.suffix not in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".html"} or path.name == "package-lock.json":
            continue
        if pattern.search(path.read_text(errors="ignore")):
            offenders.append(path.relative_to(repo).as_posix())
    assert offenders == []
    # the mic is blocked for every page (#45)
    assert "microphone=()" in (web / "next.config.ts").read_text()


# --- the AD-20 lifecycle (V71) --------------------------------------------------


def test_allowed_goes_queued_dispatching_delivered_with_no_token_in_the_action(
    api_client, reviewer, fake_gate, live, media_store, caplog
) -> None:
    with caplog.at_level(logging.DEBUG):
        response = post(api_client)
    body = response.json()
    assert body["session_token"] == SECRET_TOKEN
    assert media_store.history == [(ACTION_ID, "dispatching"), (ACTION_ID, "delivered")]
    action = media_store.actions[ACTION_ID]
    assert action["status"] == "delivered"
    assert action["result"] == {"media_id": body["media"]["id"], "provider_video_id": "sess_fake_1"}
    assert SECRET_TOKEN not in json.dumps(action, default=str) and FAKE_KEY not in json.dumps(action, default=str)
    assert len(live.calls) == 1


def test_the_settled_result_fits_the_contract_shape(media_store) -> None:
    from dxp.api.models import AvatarResult

    AvatarResult.model_validate({"media_id": "media_x", "provider_video_id": "sess_fake_1"})


@pytest.mark.parametrize("status", [400, 401, 402, 403, 422, 429])
def test_a_provider_4xx_settles_failed(api_client, reviewer, fake_gate, live, media_store, status) -> None:
    live.fail(status)
    body = post(api_client).json()
    assert body["session_token"] is None and body["media"]["status"] == "unavailable"
    assert media_store.history == [(ACTION_ID, "dispatching"), (ACTION_ID, "failed")]
    assert media_store.actions[ACTION_ID]["status"] == "failed"
    assert len(live.calls) == 1


@pytest.mark.parametrize("status", [None, 500, 502, 503, 200])
def test_a_timeout_network_error_or_5xx_settles_unknown_and_is_never_retried(
    api_client, reviewer, fake_gate, live, media_store, status
) -> None:
    live.fail(status)  # None: a timeout or network error; 200: an unreadable answer
    body = post(api_client).json()
    assert body["session_token"] is None and body["media"]["status"] == "unavailable"
    assert media_store.history == [(ACTION_ID, "dispatching"), (ACTION_ID, "unknown")]
    assert media_store.actions[ACTION_ID]["status"] == "unknown"
    assert len(live.calls) == 1  # no retry
    # asking again never re-sends an unknown action
    post(api_client)
    assert len(live.calls) == 1 and media_store.actions[ACTION_ID]["status"] == "unknown"


def test_an_unexpected_exception_settles_unknown(api_client, reviewer, fake_gate, live, media_store, monkeypatch) -> None:
    async def boom(**kwargs):
        raise RuntimeError("socket exploded")

    monkeypatch.setattr(live, "create_session_token", boom)
    post(api_client)
    assert media_store.actions[ACTION_ID]["status"] == "unknown"


def test_a_missing_key_settles_failed_and_makes_no_call(api_client, reviewer, fake_gate, live, media_store, monkeypatch) -> None:
    monkeypatch.delenv("LIVEAVATAR_API_KEY")
    body = post(api_client).json()
    assert body["media"]["status"] == "unavailable" and body["session_token"] is None
    assert live.calls == []
    assert media_store.history == [(ACTION_ID, "dispatching"), (ACTION_ID, "failed")]


def test_a_blocked_request_creates_and_settles_no_action(api_client, reviewer, fake_gate, live, media_store) -> None:
    fake_gate.block("generate_avatar_video", "destination_action")
    post(api_client)
    assert media_store.actions == {} and media_store.history == []


def test_a_second_request_cannot_claim_a_claimed_action(api_client, reviewer, fake_gate, live, media_store) -> None:
    media_store.actions[ACTION_ID] = {"_id": ACTION_ID, "kind": "generate_avatar_video", "status": "dispatching", "result": None}
    body = post(api_client).json()
    assert body["session_token"] is None and body["media"]["status"] == "unavailable"
    assert live.calls == [] and media_store.media == []  # the other worker owns it: nothing is sent
    assert media_store.actions[ACTION_ID]["status"] == "dispatching"  # and it is not touched


def test_a_repeat_after_delivered_never_calls_the_provider_again(api_client, reviewer, fake_gate, live, media_store) -> None:
    assert post(api_client).json()["session_token"] == SECRET_TOKEN
    again = post(api_client).json()
    assert again["session_token"] is None
    assert len(live.calls) == 1


async def test_the_claim_and_settle_are_conditional_on_the_previous_status(media_store) -> None:
    media_store.actions[ACTION_ID] = {"_id": ACTION_ID, "status": "queued", "result": None}
    assert await media_store.settle_action(ACTION_ID, "delivered") is False  # not claimed yet
    assert await media_store.claim_action(ACTION_ID) is True
    assert await media_store.claim_action(ACTION_ID) is False  # a second worker cannot claim it
    assert await media_store.settle_action(ACTION_ID, "unknown") is True
    assert await media_store.settle_action(ACTION_ID, "delivered") is False  # settled once
    assert media_store.actions[ACTION_ID]["status"] == "unknown"


async def test_the_mongo_store_claim_is_a_conditional_update(monkeypatch) -> None:
    """The real store's claim and settle, against an in-memory stand-in for the `actions` collection."""
    from dxp import store as dxp_store

    docs: dict[str, dict] = {"act_x": {"_id": "act_x", "status": "queued", "stamp": None}}
    events: list[dict] = []

    class Res:
        def __init__(self, n: int) -> None:
            self.modified_count = n

    class Coll:
        async def update_one(self, flt, update):
            doc = docs.get(flt["_id"])
            if doc is None or doc["status"] != flt["status"]:
                return Res(0)
            doc.update(update["$set"])
            return Res(1)

        async def find_one(self, flt):
            return docs.get(flt["_id"])

    async def emit(event, **kw):
        events.append(event)
        return 1

    monkeypatch.setattr(dxp_store, "collection", lambda name: Coll())
    monkeypatch.setattr(dxp_store, "emit_event", emit)
    real = avatar.MongoAvatarStore()
    assert await real.claim_action("act_x") is True
    assert await real.claim_action("act_x") is False
    assert docs["act_x"]["claimed_at"] is not None
    assert await real.settle_action("act_x", "delivered", {"media_id": "m", "provider_video_id": "s"}) is True
    assert await real.settle_action("act_x", "failed") is False
    assert docs["act_x"]["status"] == "delivered" and docs["act_x"]["observed_at"] is not None
    assert [e["status"] for e in events] == ["dispatching", "delivered"]
