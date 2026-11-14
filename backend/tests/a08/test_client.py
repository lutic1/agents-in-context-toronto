"""llm.call_structured(): retries, refusals and failure records (AD-11). Fake Claude."""

import asyncio

import anthropic
import httpx
import pytest

from dxp.llm import LLMFailure, client
from dxp.llm.client import call_structured
from dxp.llm.types import TriageOut

from .conftest import FakeRaw

SECRET_TEXT = "PRIVATE SOURCE SENTENCE 7f3a"
MESSAGES = [("system", "s"), ("human", SECRET_TEXT)]


def _status_error(cls, status, headers=None):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status, request=request, headers=headers or {})
    return cls(f"error echoing {SECRET_TEXT}", response=response, body=None)


def _ok():
    return TriageOut(concerns_lung_cancer_diagnostic=True, reason="ok")


def run(coro):
    return asyncio.run(coro)


def test_returns_parsed_object(fake_llm):
    fake_llm.script("TriageOut", _ok())
    out = run(call_structured("fast", TriageOut, MESSAGES))
    assert isinstance(out, TriageOut)
    assert fake_llm.calls[0]["model"] == "claude-haiku-5-5"


def test_model_ids_are_the_two_spine_models():
    assert client.MODEL_IDS == {"fast": "claude-haiku-5-5", "strong": "claude-sonnet-5-5"}
    assert client.resolve_model("claude-sonnet-5-5") == "claude-sonnet-5-5"
    assert client.resolve_model("claude-opus-5-5") is None


def test_unknown_model_is_a_failure_not_a_call(fake_llm):
    out = run(call_structured("gpt", TriageOut, MESSAGES))
    assert isinstance(out, LLMFailure) and out.code == "unknown_model"
    assert fake_llm.calls == []


def test_rate_limit_backs_off_honours_retry_after_and_retries(fake_llm):
    fake_llm.script("TriageOut", _status_error(anthropic.RateLimitError, 429, {"retry-after": "3"}), _ok())
    out = run(call_structured("fast", TriageOut, MESSAGES))
    assert isinstance(out, TriageOut)
    assert fake_llm.sleeps == [3.0]
    assert len(fake_llm.calls) == 2


def test_overload_is_retried_then_exhausted_without_raising(fake_llm):
    errors = [_status_error(anthropic.OverloadedError, 529) for _ in range(client.MAX_ATTEMPTS)]
    fake_llm.script("TriageOut", *errors)
    out = run(call_structured("strong", TriageOut, MESSAGES, step="extract"))
    assert isinstance(out, LLMFailure)
    assert out.code == "overloaded_exhausted"
    assert out.attempts == client.MAX_ATTEMPTS
    assert len(fake_llm.sleeps) == client.MAX_ATTEMPTS - 1


def test_bad_request_is_not_retried(fake_llm):
    fake_llm.script("TriageOut", _status_error(anthropic.BadRequestError, 400))
    out = run(call_structured("fast", TriageOut, MESSAGES))
    assert isinstance(out, LLMFailure) and out.code == "api_error" and out.http_status == 400
    assert len(fake_llm.calls) == 1 and fake_llm.sleeps == []


def test_refusal_is_a_failure_record(fake_llm):
    fake_llm.script("TriageOut", {"raw": FakeRaw("refusal"), "parsed": None, "parsing_error": None})
    out = run(call_structured("fast", TriageOut, MESSAGES))
    assert isinstance(out, LLMFailure) and out.code == "refusal"


def test_truncated_and_unparseable_answers_are_failure_records(fake_llm):
    fake_llm.script(
        "TriageOut",
        {"raw": FakeRaw("max_tokens"), "parsed": None, "parsing_error": None},
        {"raw": FakeRaw(), "parsed": None, "parsing_error": ValueError(SECRET_TEXT)},
    )
    assert run(call_structured("fast", TriageOut, MESSAGES)).code == "truncated"
    assert run(call_structured("fast", TriageOut, MESSAGES)).code == "parse_error"


def test_unexpected_exception_never_raises(fake_llm):
    fake_llm.script("TriageOut", RuntimeError(SECRET_TEXT))
    out = run(call_structured("fast", TriageOut, MESSAGES))
    assert isinstance(out, LLMFailure) and out.code == "unexpected_error"


def test_failure_records_and_log_lines_carry_no_source_text(fake_llm, caplog):
    caplog.set_level("DEBUG", logger="dxp.llm")
    fake_llm.script("TriageOut", _status_error(anthropic.BadRequestError, 400), RuntimeError(SECRET_TEXT))
    a = run(call_structured("fast", TriageOut, MESSAGES))
    b = run(call_structured("fast", TriageOut, MESSAGES))
    for failure in (a, b):
        assert SECRET_TEXT not in failure.model_dump_json()
        assert SECRET_TEXT not in failure.line()
    assert SECRET_TEXT not in caplog.text


def test_cancellation_propagates(fake_llm):
    fake_llm.script("TriageOut", asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        run(call_structured("fast", TriageOut, MESSAGES))


def test_shared_lane_holds_at_most_four_calls(fake_llm):
    async def go():
        fake_llm.gate = asyncio.Event()
        fake_llm.script("TriageOut", *[_ok() for _ in range(10)])
        tasks = [asyncio.create_task(call_structured("fast", TriageOut, MESSAGES)) for _ in range(10)]
        for _ in range(20):
            await asyncio.sleep(0)
        held = fake_llm.max_active
        fake_llm.gate.set()
        results = await asyncio.gather(*tasks)
        return held, results

    held, results = run(go())
    assert held == client.LANE_LIMITS["shared"] == 4
    assert all(isinstance(r, TriageOut) for r in results)


def test_ingest_lane_allows_sixteen(fake_llm):
    async def go():
        fake_llm.gate = asyncio.Event()
        fake_llm.script("TriageOut", *[_ok() for _ in range(20)])
        tasks = [asyncio.create_task(call_structured("fast", TriageOut, MESSAGES, lane="ingest")) for _ in range(20)]
        for _ in range(40):
            await asyncio.sleep(0)
        held = fake_llm.max_active
        fake_llm.gate.set()
        await asyncio.gather(*tasks)
        return held

    assert run(go()) == 16


def test_no_sampling_parameters_and_json_schema_method(monkeypatch):
    """The real runnable: no temperature/top_p/top_k, our own retries, JSON schema."""
    pytest.importorskip("langchain_anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    runnable = client._make_runnable("claude-sonnet-5-5", TriageOut)
    chat = runnable.steps[0].steps__["raw"].bound if hasattr(runnable, "steps") else None
    if chat is None:
        pytest.skip("langchain runnable layout changed; covered by the live test")
    assert chat.temperature is None and chat.top_p is None and chat.top_k is None
    assert chat.max_retries == 0
    bound_kwargs = runnable.steps[0].steps__["raw"].kwargs
    assert bound_kwargs["output_config"]["format"]["type"] == "json_schema"
