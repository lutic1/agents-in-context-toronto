"""Voice input (V73): POST /reports/{id}/interview/transcribe, with a FAKE speech-to-text client.

Nothing here reaches ElevenLabs. The real gate runs on A06's seeded world in the last section."""

from __future__ import annotations

import hashlib
import json
import logging
import struct
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.gate import policy_sets
from dxp.interview import transcribe

from .conftest import REPORT_ID, Settled, make_ctx, make_report

URL = f"/api/v1/reports/{REPORT_ID}/interview/transcribe"
HEADERS = {"X-DxP-Key": "test-dxp-api-key", "Content-Type": "audio/webm"}
AUDIO = b"\x1aE\xdf\xa3 fake webm bytes, never a transcript"
TEST_KEY = "test-elevenlabs-key"


@dataclass
class FakeStt:
    """Stands in for the ElevenLabs call: records what it was sent; `text` or `error` is what it gives back."""

    text: str = "  Is the trial\n recruiting?  "
    error: Exception | None = None
    calls: list[tuple[bytes, str]] = field(default_factory=list)

    async def __call__(self, audio: bytes, mime: str) -> str:
        self.calls.append((audio, mime))
        if self.error is not None:
            raise self.error
        return self.text


@pytest.fixture
def stt(monkeypatch: pytest.MonkeyPatch) -> FakeStt:
    fake = FakeStt()
    monkeypatch.setattr(transcribe, "elevenlabs_stt", fake)
    return fake


@pytest.fixture(autouse=True)
def transitions(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, settled: Settled) -> list:
    """Records every AD-20 step `_transition(action_id, from, to, result)` (claim and settle), so no database is
    needed; each settle (anything but the claim) is also added to `settled.calls` as (action_id, status, result)."""
    calls: list = []
    if "world" in request.fixturenames:  # the real gate on A06's fake world moves the action for real
        return calls

    async def record(action_id, from_status, to_status, result=None):
        calls.append((action_id, from_status, to_status, result))
        if to_status != "dispatching":
            settled.calls.append((action_id, to_status, result))
        return True

    monkeypatch.setattr(transcribe, "_transition", record)
    return calls


@pytest.fixture
def delivered(transitions: list) -> list:
    """The success settles: (action_id, result) for each dispatching -> delivered step."""

    class _View(list):
        def __iter__(self):
            return iter([(a, r) for (a, f, s, r) in transitions if f == "dispatching" and s == "delivered"])

        def __len__(self):
            return len(list(iter(self)))

    return _View()


@pytest.fixture
def signed_in(monkeypatch: pytest.MonkeyPatch):
    state = {"actions": ["answer_question", "transcribe_question"], "grant": {"grant_id": "sam", "version": 3, "acting_for": "team_liquid"}}

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


def wav(seconds: float, rate: int = 16000) -> bytes:
    """A mono 16-bit PCM WAV header with `seconds` of (zero) samples."""
    data_len = int(seconds * rate * 2)
    header = b"RIFF" + struct.pack("<I", 36 + data_len) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
    return header + b"data" + struct.pack("<I", data_len) + b"\x00" * data_len


def post(client, body: bytes = AUDIO, headers: dict | None = None):
    return client.post(URL, content=body, headers=HEADERS if headers is None else headers)


# --- flags, caller, report, content type ---------------------------------------------------------------------------------


def test_flags_off_is_404(api_client, store, stt, fake_gate, signed_in) -> None:
    assert post(api_client).status_code == 404
    assert stt.calls == [] and fake_gate.calls == []


@pytest.mark.parametrize("flags", [("interview",), ("voice_input",), ("avatar", "briefing")])
def test_one_flag_alone_is_404(flags, api_client, features, store, stt, fake_gate, signed_in) -> None:
    features(*flags)
    response = post(api_client)
    assert response.status_code == 404 and response.json()["error"]["code"] == "not_found"
    assert stt.calls == [] and fake_gate.calls == []


def test_flags_off_is_404_before_the_key_is_looked_at(api_client, store, stt, fake_gate) -> None:
    assert api_client.post(URL, content=AUDIO, headers={"Content-Type": "audio/webm"}).status_code == 404


def test_no_key_is_401(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    assert api_client.post(URL, content=AUDIO, headers={"Content-Type": "audio/webm"}).status_code == 401


def test_an_agent_key_is_403_before_any_decision(monkeypatch, api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")

    async def agent_principal(request):
        return m.Principal(id="dxp-curator", name="dxp-curator", kind="agent", actions=["transcribe_question"])

    monkeypatch.setattr(auth, "require_principal", agent_principal)
    response = post(api_client)
    assert response.status_code == 403 and response.json()["error"]["code"] == "person_only"
    assert fake_gate.calls == [] and stt.calls == []


def test_unknown_report_is_404(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    response = api_client.post("/api/v1/reports/rep_ffffffffffffffff/interview/transcribe", content=AUDIO, headers=HEADERS)
    assert response.status_code == 404 and response.json()["error"]["code"] == "not_found"


def test_a_pending_report_can_be_transcribed(api_client, features, store, stt, fake_gate, signed_in) -> None:
    # V74: transcription runs before approval too, through the same gate.
    features("interview", "voice_input")
    store.reports[REPORT_ID] = make_report(status="pending")
    response = post(api_client)
    assert response.status_code == 200, response.text
    assert len(fake_gate.calls) == 1


@pytest.mark.parametrize("status", ["accepting", "rejected", "reverting", "reverted"])
def test_report_not_pending_or_accepted_is_409(status, api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    store.reports[REPORT_ID] = make_report(status=status)
    response = post(api_client)
    assert response.status_code == 409 and response.json()["error"]["code"] == "report_not_accepted"
    assert fake_gate.calls == [] and stt.calls == []


@pytest.mark.parametrize("content_type", ["application/json", "audio/mpeg", "audio/ogg", "text/plain", "audio/webmx", ""])
def test_a_wrong_content_type_is_415(content_type, api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    headers = {"X-DxP-Key": "test-dxp-api-key"}
    if content_type:
        headers["Content-Type"] = content_type
    response = post(api_client, headers=headers)
    assert response.status_code == 415 and response.json()["error"]["code"] == "unsupported_media_type"
    assert fake_gate.calls == [] and stt.calls == []


@pytest.mark.parametrize("content_type", ["audio/webm", "audio/webm;codecs=opus", "Audio/WebM; codecs=opus", "audio/wav", "audio/wav; rate=16000"])
def test_webm_and_wav_with_params_are_accepted(content_type, api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    response = post(api_client, headers={"X-DxP-Key": "test-dxp-api-key", "Content-Type": content_type})
    assert response.status_code == 200, response.text
    assert stt.calls[0][1] == content_type.split(";")[0].lower()


def test_an_empty_body_is_422(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    assert post(api_client, body=b"").status_code == 422
    assert fake_gate.calls == [] and stt.calls == []


# --- size and duration, before the gate ------------------------------------------------------------------------------------


def test_a_clip_over_the_size_cap_is_too_long_with_no_gate_call(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    response = post(api_client, body=b"\x00" * (transcribe.MAX_BYTES + 1))
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True and body["refusal_reason"] == "too_long" and body["text"] == ""
    assert fake_gate.calls == [] and stt.calls == []


def test_a_clip_at_the_size_cap_goes_to_the_gate(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    response = post(api_client, body=b"\x00" * transcribe.MAX_BYTES)
    assert response.json()["refused"] is False
    assert len(fake_gate.calls) == 1


def test_a_wav_over_thirty_seconds_is_too_long_with_no_gate_call(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    clip = wav(31, rate=8000)
    assert len(clip) < transcribe.MAX_BYTES
    response = post(api_client, body=clip, headers={"X-DxP-Key": "test-dxp-api-key", "Content-Type": "audio/wav"})
    assert response.json()["refusal_reason"] == "too_long"
    assert fake_gate.calls == [] and stt.calls == []


def test_a_wav_of_ten_seconds_is_sent(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    response = post(api_client, body=wav(10, rate=8000), headers={"X-DxP-Key": "test-dxp-api-key", "Content-Type": "audio/wav"})
    assert response.json()["refused"] is False
    assert fake_gate.calls[0][1].inputs["duration_ms"] == 10000


def test_wav_duration_reads_the_header() -> None:
    assert transcribe.wav_duration_ms(wav(2.5)) == 2500
    assert transcribe.wav_duration_ms(b"not a wav") is None
    assert transcribe.wav_duration_ms(AUDIO) is None


# --- the gate ---------------------------------------------------------------------------------------------------------------


def test_the_gate_gets_a_reviewer_context_and_metadata_only(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    post(api_client)
    ctx, action = fake_gate.calls[0]
    assert ctx.run_id is None and ctx.stamp.kind == "reviewer" and (ctx.grant_id, ctx.grant_version) == ("sam", 3)
    assert ctx.request_id.startswith("req_") and ctx.cause.report_id == REPORT_ID
    assert (action.kind, action.destination, action.target.report_id) == ("transcribe_question", "stt:elevenlabs", REPORT_ID)
    assert action.inputs == {
        "id_target": REPORT_ID,
        "mime": "audio/webm",
        "bytes": len(AUDIO),
        "sha256": hashlib.sha256(AUDIO).hexdigest(),
    }
    blob = action.model_dump_json()
    assert "fake webm" not in blob and "recruiting" not in blob


def test_blocked_is_a_200_refusal_with_no_vendor_call(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    fake_gate.block("transcribe_question", "destination_action")
    response = post(api_client)
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True and body["refusal_reason"] == "blocked" and body["text"] == ""
    assert body["decision_id"].startswith("dec_")
    assert stt.calls == []


def test_the_gate_not_on_main_is_501_in_the_error_shape(api_client, features, store, stt, signed_in, monkeypatch) -> None:
    import dxp.gate

    async def not_built(ctx, action):
        raise NotImplementedError("gate.evaluate (A06)")

    monkeypatch.setattr(dxp.gate, "evaluate", not_built)
    features("interview", "voice_input")
    response = post(api_client)
    assert response.status_code == 501 and response.json()["error"]["code"] == "not_implemented"
    assert stt.calls == []


# --- success and failure ----------------------------------------------------------------------------------------------------


def test_success_returns_the_stripped_text_and_settles_delivered(api_client, features, store, stt, fake_gate, signed_in, settled: Settled, delivered) -> None:
    features("interview", "voice_input")
    response = post(api_client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"text", "decision_id", "refused", "refusal_reason"}
    assert body["text"] == "Is the trial recruiting?" and body["refused"] is False and body["refusal_reason"] is None
    assert stt.calls == [(AUDIO, "audio/webm")]
    assert [s for (_, s, _) in settled.calls] == ["delivered"], "claimed, then delivered: never done (external kind)"
    [(action_id, result)] = list(delivered)
    assert action_id
    assert "recruiting" not in json.dumps(result), "the action's result never carries the transcript"


def test_the_text_is_cut_to_what_a_question_allows(api_client, features, store, stt, fake_gate, signed_in) -> None:
    features("interview", "voice_input")
    stt.text = "word " * 400
    text = post(api_client).json()["text"]
    assert 0 < len(text) <= 500 and text == text.strip()


def test_a_transcript_is_one_line_without_control_characters() -> None:
    assert transcribe.clean_text("a\x00b\r\n\tc") == "a b c"
    assert transcribe.clean_text(None) == ""


def test_nothing_is_stored_and_the_question_is_not_submitted(api_client, features, store, stt, fake_gate, signed_in, monkeypatch) -> None:
    import dxp.gate
    from dxp import store as dxp_store

    features("interview", "voice_input")
    writes: list[str] = []

    class Collection:
        def __getattr__(self, name):
            def record(*args, **kwargs):
                writes.append(name)
                raise AssertionError(f"a collection was used: {name}")

            return record

    class Db:
        def __getitem__(self, name):
            return Collection()

        def __getattr__(self, name):
            return Collection()

    monkeypatch.setattr(dxp_store, "get_db", lambda *a, **k: Db(), raising=False)

    async def no_interview(*args, **kwargs):
        raise AssertionError("the transcript was submitted as a question")

    monkeypatch.setattr("dxp.api.routes_interview.answer_question", no_interview)
    response = post(api_client)
    assert response.json()["text"] and writes == []
    # The only Decision is the gate's one `transcribe_question`; the settle call carried no transcript.
    assert [a.kind for _, a in fake_gate.calls] == ["transcribe_question"]
    assert dxp.gate.evaluate  # the fake stayed the only gate in play


def test_a_vendor_failure_is_unavailable_and_settles_failed(api_client, features, store, stt, fake_gate, signed_in, settled: Settled) -> None:
    features("interview", "voice_input")
    stt.error = transcribe.SttError("http_500")
    response = post(api_client)
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True and body["refusal_reason"] == "unavailable" and body["text"] == ""
    assert body["decision_id"].startswith("dec_")
    [(_, status, result)] = settled.calls
    assert status == "unknown" and result["error"] == "http_500", "a 5xx may have been processed: unknown, never re-sent"


def test_an_unexpected_vendor_exception_is_unavailable_not_a_500(api_client, features, store, stt, fake_gate, signed_in, settled: Settled) -> None:
    features("interview", "voice_input")
    stt.error = RuntimeError("secret detail from the vendor")
    response = post(api_client)
    assert response.status_code == 200 and response.json()["refusal_reason"] == "unavailable"
    assert "secret" not in response.text and settled.calls[0][1] == "unknown"


def test_a_slow_vendor_is_unavailable_at_the_deadline(api_client, features, store, fake_gate, signed_in, settled: Settled, monkeypatch) -> None:
    import asyncio

    async def slow(audio, mime):
        await asyncio.sleep(5)
        return "late"

    monkeypatch.setattr(transcribe, "elevenlabs_stt", slow)
    monkeypatch.setattr(transcribe, "DEADLINE_S", 0.05)
    features("interview", "voice_input")
    response = post(api_client)
    assert response.json()["refusal_reason"] == "unavailable" and settled.calls[0][1] == "unknown"


def test_a_failure_to_settle_never_changes_the_reply(api_client, features, store, stt, fake_gate, signed_in, monkeypatch) -> None:
    import dxp.gate

    async def broken(*args, **kwargs):
        raise RuntimeError("db down")

    claims = {"n": 0}

    async def claim_then_break(action_id, from_status, to_status, result=None):
        if to_status == "dispatching":
            claims["n"] += 1
            return True
        raise RuntimeError("db down")

    monkeypatch.setattr(transcribe, "_transition", claim_then_break)
    features("interview", "voice_input")
    assert post(api_client).json()["text"] == "Is the trial recruiting?" and claims["n"] == 1


# --- the real vendor client (httpx faked), the key ----------------------------------------------------------------------------


class VendorApiError(Exception):
    """Shaped like the SDK's ApiError (a status code), with a message that carries the credential on purpose."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"headers: {{'xi-api-key': '{TEST_KEY}'}}, status_code: {status_code}")
        self.status_code = status_code


@pytest.fixture
def vendor(monkeypatch: pytest.MonkeyPatch):
    """The real `elevenlabs_stt` against a fake of B06's SDK client: records the convert() call, answers `state`."""
    from dxp.briefing import audio as briefing_audio

    state: dict = {"text": "hello ctDNA", "raise": None, "response": None, "calls": []}

    class Stt:
        async def convert(self, **kwargs):
            state["calls"].append(kwargs)
            if state["raise"] is not None:
                raise state["raise"]
            return state["response"] if state["response"] is not None else SimpleNamespace(text=state["text"])

    monkeypatch.setattr(briefing_audio, "_client", lambda: SimpleNamespace(speech_to_text=Stt()))
    return state


def test_the_vendor_request_is_the_documented_one(api_client, features, store, fake_gate, signed_in, vendor) -> None:
    features("interview", "voice_input")
    assert post(api_client).json()["text"] == "hello ctDNA"
    [call] = vendor["calls"]
    assert call["model_id"] == "scribe_v2" and call["language_code"] == "en" and call["tag_audio_events"] is False
    assert call["file"] == ("question.webm", AUDIO, "audio/webm")
    assert call["request_options"] == {"max_retries": 0}, "no SDK retries: one recording, one request"
    assert set(call) == {"model_id", "file", "language_code", "tag_audio_events", "request_options"}


def test_a_missing_key_is_unavailable_and_settles_failed(api_client, features, store, fake_gate, signed_in, settled: Settled, monkeypatch) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY")  # the real `_client()` answers None: nothing is sent
    features("interview", "voice_input")
    response = post(api_client)
    assert response.status_code == 200 and response.json()["refusal_reason"] == "unavailable"
    assert settled.calls[0][1] == "failed" and settled.calls[0][2]["error"] == "no_key"


@pytest.mark.parametrize(
    ("failure", "status"),
    [
        ({"raise": VendorApiError(401)}, "failed"),
        ({"raise": VendorApiError(429)}, "failed"),
        ({"raise": VendorApiError(500)}, "unknown"),
        ({"raise": ConnectionError("boom")}, "unknown"),
        ({"raise": TimeoutError("slow")}, "unknown"),
        ({"response": SimpleNamespace(text=5)}, "unknown"),
        ({"response": SimpleNamespace(transcripts=[])}, "unknown"),
    ],
)
def test_every_vendor_failure_is_unavailable(failure, status, api_client, features, store, fake_gate, signed_in, vendor, settled: Settled) -> None:
    """V71/AD-20: `failed` only when nothing can have been processed (a 4xx refusal); otherwise `unknown`."""
    vendor.update(failure)
    features("interview", "voice_input")
    response = post(api_client)
    assert response.status_code == 200 and response.json()["refusal_reason"] == "unavailable"
    assert settled.calls[0][1] == status


def test_the_key_never_appears_in_logs_results_or_replies(api_client, features, store, fake_gate, signed_in, vendor, settled: Settled, caplog) -> None:
    features("interview", "voice_input")
    caplog.set_level(logging.DEBUG)
    vendor["raise"] = VendorApiError(500)  # its message carries the key
    failed = post(api_client)
    vendor["raise"] = None
    ok = post(api_client)
    everything = caplog.text + failed.text + ok.text + json.dumps(settled.calls) + json.dumps([str(c) for c in fake_gate.calls])
    assert TEST_KEY not in everything
    assert "http_500" in json.dumps(settled.calls)


def test_the_lane_never_reads_the_credential() -> None:
    import pathlib

    source = pathlib.Path(transcribe.__file__).read_text()
    assert "API_KEY" not in source and "environ" not in source and "getenv" not in source


# --- the real gate on A06's seeded world -------------------------------------------------------------------------------------

a06 = pytest.importorskip("a06.conftest", reason="A06's seeded world is on main, not on this branch")
world = a06.world  # the fixture


def reviewer_ctx(w, grant_version: int = 3, request_id: str = "req_real_t1") -> m.RunContext:
    ctx = make_ctx(["transcribe_question"])
    return ctx.model_copy(
        update={
            "policy_set_version": w.policy_set_version,
            "grant_version": grant_version,
            "request_id": request_id,
            "cause": m.DecisionCause(report_id=REPORT_ID, origin_run_id=w.run_id),
        }
    )


async def test_real_gate_allows_sam_v3_and_settles_delivered(world, store) -> None:
    fake = FakeStt()
    response = await transcribe.transcribe(REPORT_ID, AUDIO, "audio/webm", reviewer_ctx(world), report=make_report(), stt=fake)
    assert response.refused is False and response.text == "Is the trial recruiting?" and response.decision_id.startswith("dec_")
    decision = await world.db["decisions"].find_one({"_id": response.decision_id})
    action = await world.db["actions"].find_one({"decision_id": response.decision_id})
    assert decision["outcome"] == "allowed" and decision["kind"] == "transcribe_question" and decision["destination"] == "stt:elevenlabs"
    assert decision["stamp"]["kind"] == "reviewer" and decision["inputs"]["id_target"] == REPORT_ID
    assert decision["inputs"]["sha256"] == hashlib.sha256(AUDIO).hexdigest() and decision["inputs"]["bytes"] == len(AUDIO)
    assert action["status"] == "delivered" and action["result"]["outcome"] == "transcribed", action
    assert fake.calls == [(AUDIO, "audio/webm")]


async def test_real_gate_stores_no_audio_or_transcript_anywhere(world, store) -> None:
    await transcribe.transcribe(REPORT_ID, AUDIO, "audio/webm", reviewer_ctx(world), report=make_report(), stt=FakeStt(text="UNIQUE-TRANSCRIPT-TEXT"))
    seen = 0
    for name, collection in list(world.db.collections.items()):
        async for doc in collection.find({}):
            seen += 1
            blob = json.dumps(doc, default=str)
            assert "UNIQUE-TRANSCRIPT" not in blob and "fake webm" not in blob, name
    assert seen > 0


async def test_real_gate_vendor_failure_settles_failed(world, store) -> None:
    fake = FakeStt(error=transcribe.SttError("http_503"))
    response = await transcribe.transcribe(REPORT_ID, AUDIO, "audio/webm", reviewer_ctx(world), report=make_report(), stt=fake)
    assert response.refused is True and response.refusal_reason == "unavailable"
    action = await world.db["actions"].find_one({"decision_id": response.decision_id})
    assert action["status"] == "unknown" and action["result"]["error"] == "http_503", action


async def test_real_gate_blocks_a_grant_without_the_action(world, store) -> None:
    # lbdx (a team grant) has no transcribe_question: the gate blocks and nothing is sent.
    fake = FakeStt()
    ctx = reviewer_ctx(world).model_copy(update={"grant_id": "lbdx", "grant_version": 1})
    response = await transcribe.transcribe(REPORT_ID, AUDIO, "audio/webm", ctx, report=make_report(), stt=fake)
    assert response.refused is True and response.refusal_reason == "blocked" and fake.calls == []


async def test_real_gate_blocks_a_revoked_grant(world, store) -> None:
    await world.new_grant_version("sam", "revoked")
    fake = FakeStt()
    response = await transcribe.transcribe(REPORT_ID, AUDIO, "audio/webm", reviewer_ctx(world, grant_version=4), report=make_report(), stt=fake)
    assert response.refusal_reason == "blocked" and fake.calls == []


def test_an_unclaimed_action_is_never_sent(api_client, features, store, stt, fake_gate, signed_in, monkeypatch) -> None:
    """Another worker holds it or it is already settled: the conditional claim fails and nothing is sent (AD-20)."""

    async def not_claimed(action_id, from_status, to_status, result=None):
        return False

    monkeypatch.setattr(transcribe, "_transition", not_claimed)
    features("interview", "voice_input")
    body = post(api_client).json()
    assert body["refused"] is True and body["refusal_reason"] == "unavailable" and stt.calls == []


def test_the_vendor_call_turns_the_sdk_retries_off(monkeypatch) -> None:
    """One recording, one request: the ElevenLabs SDK would retry 5xx/429 twice and could bill it three times."""
    import asyncio

    from dxp.briefing import audio as vendor_module

    seen: dict = {}

    class _Stt:
        async def convert(self, **kwargs):
            seen.update(kwargs)
            return SimpleNamespace(text="hello")

    monkeypatch.setattr(vendor_module, "_client", lambda: SimpleNamespace(speech_to_text=_Stt()))
    assert asyncio.run(transcribe.elevenlabs_stt(b"x", "audio/webm")) == "hello"
    assert seen["request_options"] == {"max_retries": 0}
