"""A run's events as server-sent events (Story 9.12, `live_stream` flag, AD-23, V48). Finished by A27;
the read logic is in search/stream.py.

The path is frozen (AD-14). With `live_stream` not in `DXP_FEATURES` it answers 404, and nothing
needs it: the screens poll, and the audit stays the source. With the flag on:

- the caller is resolved from `X-DxP-Key` like every read route (the browser never holds the key;
  B02's streaming proxy adds it server-side);
- each new event of the run is one SSE message: `id:` is the change stream's resume token and
  `data:` is one `Event` (AD-14) as JSON. No `event:` name, so it arrives as a plain message;
- `Last-Event-ID` (header, or `?lastEventId=`) resumes after that token, so a reconnect repeats
  nothing and misses nothing; a token that cannot be resumed sends `event: reset` and ends, and the
  client reads the run again and reconnects without a token;
- a heartbeat comment every 15 s keeps proxies from closing an idle stream;
- the stream ends itself after `DXP_STREAM_MAX_SECONDS` (default 50 s) so it never meets the
  hosting request limit; EventSource reconnects with Last-Event-ID and resumes.

OD5 (not yet measured): whether `watch()` works on the Sandbox tier and where Modal's and the
Vercel streaming proxy's limits cut a long response. OD5 must set `DXP_STREAM_MAX_SECONDS` safely
below the smallest measured limit; the default of 50 s is a guess on the cautious side.
`seq` stays the only ordering source (AD-10). It writes nothing.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import math
import os
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from dxp import feature_enabled
from dxp.api.errors import ApiError
from dxp.api.routes_runs import caller
from dxp.search import stream as run_stream

router = APIRouter()
OWNER = "A27"

FLAG = "live_stream"
MAX_SECONDS_ENV = "DXP_STREAM_MAX_SECONDS"
DEFAULT_MAX_SECONDS = 50.0
HEARTBEAT_SECONDS = 15.0
# How long EventSource waits before it reconnects after the stream ends (ms).
RETRY_MS = 1000

_DONE = object()


def max_seconds() -> float:
    """The stream's lifetime: DXP_STREAM_MAX_SECONDS when it is a positive number, else 50 s."""
    raw = os.environ.get(MAX_SECONDS_ENV, "").strip()
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_MAX_SECONDS
    return value if math.isfinite(value) and value > 0 else DEFAULT_MAX_SECONDS


def sse_message(token: str, event: dict[str, Any]) -> str:
    data = json.dumps(event, separators=(",", ":"), default=str)
    return f"id: {token}\ndata: {data}\n\n"


def sse_reset() -> str:
    data = json.dumps({"reset": True, "reason": "resume_token_lost"})
    return f"event: reset\ndata: {data}\n\n"


async def _pump(run_id: str, resume_after: str | None, queue: asyncio.Queue) -> None:
    """Move the change stream into the queue; its end or failure is the last item."""
    try:
        async for token, event in run_stream.run_events(run_id, resume_after):
            await queue.put((token, event))
        await queue.put(_DONE)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - the stream ends; the client reconnects or polls
        await queue.put(exc)


async def event_stream(run_id: str, resume_after: str | None) -> AsyncIterator[str]:
    """The SSE body: messages, heartbeats, `reset`, and the end at the time limit."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_seconds()
    yield f"retry: {RETRY_MS}\n: open\n\n"
    queue: asyncio.Queue = asyncio.Queue()
    pump = asyncio.create_task(_pump(run_id, resume_after, queue))
    try:
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return  # end before the hosting limit; the client resumes from its last id
            try:
                item = await asyncio.wait_for(queue.get(), timeout=min(HEARTBEAT_SECONDS, remaining))
            except TimeoutError:
                if deadline - loop.time() > 0:
                    yield ": heartbeat\n\n"
                continue
            if item is _DONE:
                return
            if isinstance(item, run_stream.ResumeTokenLost):
                yield sse_reset()
                return
            if isinstance(item, Exception):
                return  # a failed watch ends the stream; EventSource reconnects, the screen polls meanwhile
            token, event = item
            yield sse_message(token, event)
    finally:
        pump.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await pump


@router.get(
    "/runs/{run_id}/stream",
    tags=["runs"],
    response_class=StreamingResponse,
    responses={200: {"description": "text/event-stream of Event", "content": {"text/event-stream": {}}}},
)
async def stream_run(run_id: str, request: Request):
    if not feature_enabled(FLAG):
        raise ApiError(404, "not_found", "Not found.")
    await caller(request)
    resume_after = request.headers.get("last-event-id") or request.query_params.get("lastEventId") or None
    return StreamingResponse(
        event_stream(run_id, resume_after),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-store, no-transform", "X-Accel-Buffering": "no"},
    )
