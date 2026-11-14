"""The one Claude client (AD-11).

Only `backend/dxp/llm` calls Claude, through `langchain-anthropic` with the
JSON-schema structured-output method and no sampling parameters. Every call is
async. An ingest run holds at most 16 calls at once (lane `ingest`); every
other caller shares 4 (lane `shared`). Rate-limit, overload, server and
connection errors back off and retry here; a model error, a refusal, a
truncated or unparseable answer returns an `LLMFailure` and never raises.

A19+A20's `relate` and `draft` call `call_structured()`; nothing else in DxP
imports `langchain_anthropic` or `anthropic`.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from dxp.llm.types import LLMFailure

log = logging.getLogger("dxp.llm")

#: The two models (AD-11). The run reads these into its identity (AD-17).
MODEL_IDS: dict[str, str] = {
    "fast": "claude-haiku-5-5",  # triage
    "strong": "claude-sonnet-5-5",  # extraction, checks, relate, draft
}

LANE_LIMITS: dict[str, int] = {"ingest": 16, "shared": 4}

MAX_ATTEMPTS = 4
BASE_DELAY_S = 1.0
MAX_DELAY_S = 30.0
MAX_TOKENS = 16000
TIMEOUT_S = 180.0

T = TypeVar("T", bound=BaseModel)

# Replaced in tests.
_sleep = asyncio.sleep

_semaphores: dict[tuple[int, str], asyncio.Semaphore] = {}


def resolve_model(model: str) -> str | None:
    """`fast`/`strong`, or one of the two model IDs; anything else is None."""
    if model in MODEL_IDS:
        return MODEL_IDS[model]
    if model in MODEL_IDS.values():
        return model
    return None


def _semaphore(lane: str) -> asyncio.Semaphore:
    loop = asyncio.get_running_loop()
    key = (id(loop), lane)
    sem = _semaphores.get(key)
    if sem is None:
        sem = asyncio.Semaphore(LANE_LIMITS[lane])
        _semaphores[key] = sem
    return sem


def _make_runnable(model_id: str, schema: type[BaseModel]) -> Any:
    """A langchain runnable returning {raw, parsed, parsing_error}.

    Retries are ours (`max_retries=0`); no temperature, top_p or top_k.
    """
    from langchain_anthropic import ChatAnthropic

    chat = ChatAnthropic(
        model=model_id,
        max_tokens=MAX_TOKENS,
        max_retries=0,
        timeout=TIMEOUT_S,
    )
    return chat.with_structured_output(schema, method="json_schema", include_raw=True)


def _to_messages(messages: Sequence[Any]) -> list[Any]:
    out: list[Any] = []
    for m in messages:
        if isinstance(m, dict):
            out.append((m["role"], m["content"]))
        else:
            out.append(m)
    return out


def _classify(exc: BaseException) -> tuple[bool, str, int | None]:
    """(retryable, code, http_status) for an exception from the client."""
    try:
        import anthropic
    except ImportError:  # pragma: no cover - anthropic ships with langchain-anthropic
        return False, "unexpected_error", None

    status = getattr(exc, "status_code", None)
    if isinstance(exc, anthropic.RateLimitError):
        return True, "rate_limited", status
    if isinstance(exc, anthropic.InternalServerError):  # 5xx, including 529 overloaded
        code = "overloaded" if status == 529 or isinstance(exc, anthropic.OverloadedError) else "server_error"
        return True, code, status
    if isinstance(exc, anthropic.APITimeoutError):
        return True, "timeout", None
    if isinstance(exc, anthropic.APIConnectionError):
        return True, "connection_error", None
    if isinstance(exc, anthropic.APIStatusError):
        return False, "api_error", status
    return False, "unexpected_error", status


def _retry_after(exc: BaseException) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after")
    try:
        return max(0.0, float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _delay(attempt: int, exc: BaseException) -> float:
    hinted = _retry_after(exc)
    if hinted is not None:
        return min(hinted, MAX_DELAY_S)
    backoff = BASE_DELAY_S * (2 ** (attempt - 1))
    return min(backoff + random.uniform(0, backoff / 2), MAX_DELAY_S)


def _stop_reason(raw: Any) -> str | None:
    meta = getattr(raw, "response_metadata", None) or {}
    return meta.get("stop_reason")


async def call_structured(
    model: str,
    schema: type[T],
    messages: Sequence[Any],
    *,
    lane: str = "shared",
    step: str = "call",
) -> T | LLMFailure:
    """Ask Claude for one object of `schema`. Returns it, or an `LLMFailure`.

    `model` is `fast`, `strong` or one of their IDs. `messages` are
    `(role, content)` tuples, `{"role", "content"}` dicts or langchain
    messages; `system` is allowed as the first role. Never raises, except
    `asyncio.CancelledError`, so a stopped run still stops.
    """
    model_id = resolve_model(model)
    if model_id is None:
        return LLMFailure(code="unknown_model", step=step)
    if lane not in LANE_LIMITS:
        return LLMFailure(code="unknown_lane", step=step, model=model_id)

    try:
        runnable = _make_runnable(model_id, schema)
        payload = _to_messages(messages)
    except Exception as exc:  # noqa: BLE001 - a filter never raises (AD spine)
        failure = LLMFailure(
            code="client_setup_error", step=step, model=model_id, error_type=type(exc).__name__
        )
        log.warning("llm failure %s", failure.line())
        return failure

    attempt = 0
    while True:
        attempt += 1
        try:
            async with _semaphore(lane):
                result = await runnable.ainvoke(payload)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            retryable, code, status = _classify(exc)
            if retryable and attempt < MAX_ATTEMPTS:
                delay = _delay(attempt, exc)
                log.info(
                    "llm retry step=%s code=%s model=%s attempt=%d delay=%.1fs",
                    step, code, model_id, attempt, delay,
                )
                await _sleep(delay)
                continue
            failure = LLMFailure(
                code=code if not retryable else f"{code}_exhausted",
                step=step,
                model=model_id,
                attempts=attempt,
                error_type=type(exc).__name__,
                http_status=status,
            )
            log.warning("llm failure %s", failure.line())
            return failure
        break

    return _parse_result(result, schema, model_id, step, attempt)


def _parse_result(result: Any, schema: type[T], model_id: str, step: str, attempts: int) -> T | LLMFailure:
    raw = result.get("raw") if isinstance(result, dict) else None
    parsed = result.get("parsed") if isinstance(result, dict) else result
    parsing_error = result.get("parsing_error") if isinstance(result, dict) else None

    stop = _stop_reason(raw)
    code: str | None = None
    if stop == "refusal":
        code = "refusal"
    elif stop == "max_tokens":
        code = "truncated"
    elif parsing_error is not None:
        code = "parse_error"
    elif parsed is None:
        code = "no_output"
    elif not isinstance(parsed, schema):
        try:
            parsed = schema.model_validate(parsed)
        except Exception:  # noqa: BLE001
            code = "parse_error"

    if code is not None:
        failure = LLMFailure(
            code=code,
            step=step,
            model=model_id,
            attempts=attempts,
            error_type=type(parsing_error).__name__ if parsing_error is not None else None,
        )
        log.warning("llm failure %s", failure.line())
        return failure
    return parsed
