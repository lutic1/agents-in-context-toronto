"""A run's events from an Atlas change stream on `events` (Story 9.12, AD-23, V48, `live_stream` flag).

`run_events(run_id, resume_after)` opens `events.watch()` through `store` with a pipeline that keeps
only inserts of this run's events, and yields `(resume_token, event)` for each one:

- `resume_token` is the change's opaque resume token as text (its `_data`), used as the SSE `id`;
- `event` is the inserted document in the AD-14 `Event` shape (JSON-ready), `seq` taken from `_id`.

While no event of the run arrives, the change stream's own resume token still advances (its
post-batch token). It is yielded as `(resume_token, None)` whenever it moves, so the route can hand
it to the client on a heartbeat or before closing and a quiet stream still resumes from now, not
from where it opened.

`resume_after` is the last SSE id the client saw (`Last-Event-ID`). A token that is malformed or that
the server can no longer resume from raises `ResumeTokenLost`; the route turns that into
`event: reset`. Ordering stays `seq` (AD-10): the stream is only a wake-up mirror of `events`, and
the audit stays the source. Nothing here writes. The frozen signature is in tests/a01.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from typing import Any

from pydantic import ValidationError
from pymongo.errors import OperationFailure

from dxp import store
from dxp.api import models as m

# Resume tokens are hex text (`_data`). Anything else cannot be resumed from.
_TOKEN = re.compile(r"^[0-9A-Fa-f]{2,4096}$")
# Server errors that mean "this resume token is no longer usable".
RESUME_ERROR_CODES = frozenset({
    9,  # FailedToParse (a malformed token)
    260,  # InvalidResumeToken
    280,  # ChangeStreamFatalError
    286,  # ChangeStreamHistoryLost (the oplog has rolled past it)
})
_EVENT_FIELDS = tuple(m.Event.model_fields)
MAX_AWAIT_MS = 1000  # how long one idle getMore waits on the server


class ResumeTokenLost(Exception):
    """The client's Last-Event-ID cannot be resumed from: it must reset and read the run again."""


def _events() -> Any:
    """The `events` collection, through store (the only client)."""
    return store.collection("events")


def pipeline(run_id: str) -> list[dict[str, Any]]:
    """Only inserts, only this run's events."""
    return [{"$match": {"operationType": "insert", "fullDocument.run_id": run_id}}]


def decode_token(token: Any) -> dict[str, Any] | None:
    """The resume document for a Last-Event-ID, None for none; ResumeTokenLost when malformed."""
    if token is None or token == "":
        return None
    if isinstance(token, dict) and isinstance(token.get("_data"), str):
        token = token["_data"]
    if not isinstance(token, str) or not _TOKEN.match(token):
        raise ResumeTokenLost("The resume token is not one this stream issued.")
    return {"_data": token}


def encode_token(resume: Any) -> str | None:
    if isinstance(resume, dict) and isinstance(resume.get("_data"), str):
        return resume["_data"]
    return None


def to_event(doc: dict[str, Any]) -> dict[str, Any]:
    """One `events` document in the AD-14 Event shape (JSON-ready); `seq` is the document's `_id`."""
    data = {k: doc[k] for k in _EVENT_FIELDS if k in doc}
    data["seq"] = int(doc.get("seq", doc.get("_id", 0)))
    try:
        return m.Event.model_validate(data).model_dump(mode="json")
    except ValidationError:
        # A type this build does not know still wakes the screen; it rereads the audit anyway.
        return {"seq": data["seq"], "type": str(doc.get("type", "")), "run_id": doc.get("run_id")}


async def run_events(run_id: str, resume_after: Any | None = None) -> AsyncIterator[tuple[Any, dict[str, Any]]]:
    """Yield (resume_token, event) for each new event of the run, via store; resume_after is the
    last SSE id (Last-Event-ID). While idle, (resume_token, None) when the stream's token moves."""
    resume = decode_token(resume_after)
    kwargs: dict[str, Any] = {"max_await_time_ms": MAX_AWAIT_MS}
    if resume is not None:
        kwargs["resume_after"] = resume
    try:
        change_stream = await _events().watch(pipeline(run_id), **kwargs)
    except OperationFailure as exc:
        if resume is not None and (exc.code in RESUME_ERROR_CODES or "resume" in str(exc).lower()):
            raise ResumeTokenLost(str(exc)) from exc
        raise
    async with change_stream as changes:
        last_idle: str | None = None
        try:
            while True:
                change = await changes.try_next()
                if change is None:
                    token = encode_token(getattr(changes, "resume_token", None))
                    if token is not None and token != last_idle:
                        last_idle = token
                        yield token, None
                    await asyncio.sleep(0)  # the server's await already paced this loop
                    continue
                doc = change.get("fullDocument") or {}
                if change.get("operationType") != "insert" or doc.get("run_id") != run_id:
                    continue  # the pipeline already filters; this never lets another run through
                token = encode_token(change.get("_id"))
                if token is None:
                    continue
                yield token, to_event(doc)
        except OperationFailure as exc:
            # The server checks a resume token on the first getMore, not always on open.
            if resume is not None and exc.code in RESUME_ERROR_CODES:
                raise ResumeTokenLost(str(exc)) from exc
            raise
