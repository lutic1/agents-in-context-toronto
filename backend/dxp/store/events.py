"""`emit_event()`: the only writer of `events` (AD-10).

The event `_id` is `seq`, the next integer, assigned by inserting and retrying on a
duplicate key, so a higher seq is never visible before a lower one. Each event has a
unique `dedupe_key`: a retry emits nothing new and returns the stored event's seq.
Every event carries the AD-17 stamp.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from dxp.store.client import get_db

_MAX_ATTEMPTS = 50


async def emit_event(
    event: str | dict[str, Any],
    *,
    session: Any | None = None,
    dedupe_key: str | None = None,
    stamp: dict[str, Any] | None = None,
    **fields: Any,
) -> int:
    """Insert one event and return its seq; an existing `dedupe_key` returns the stored seq.

    Two call forms, same result:
    - emit_event({"type": ..., "dedupe_key": ..., "stamp": ..., <Event fields>}, session=s)
    - emit_event("action_allowed", dedupe_key=..., stamp=..., session=s, <Event fields>)
    `_id` and `seq` are assigned here and ignored if passed.
    """
    if isinstance(event, dict):
        fields = {**event, **fields}
        event_type = fields.pop("type")
        dedupe_key = dedupe_key or fields.pop("dedupe_key", None)
        stamp = stamp if stamp is not None else fields.pop("stamp", None)
    else:
        event_type = event
    fields.pop("_id", None)
    fields.pop("seq", None)
    if not dedupe_key:
        raise ValueError("emit_event needs a dedupe_key (AD-10).")
    events = get_db()["events"]
    for _ in range(_MAX_ATTEMPTS):
        found = await events.find_one({"dedupe_key": dedupe_key}, {"_id": 1}, session=session)
        if found is not None:
            return int(found["_id"])
        last = await events.find_one({}, {"_id": 1}, sort=[("_id", DESCENDING)], session=session)
        seq = int(last["_id"]) + 1 if last else 1
        doc = {**fields, "_id": seq, "type": event_type, "dedupe_key": dedupe_key, "stamp": stamp,
               "at": fields.get("at") or datetime.now(UTC)}
        try:
            await events.insert_one(doc, session=session)
            return seq
        except DuplicateKeyError:
            continue  # seq taken or the same dedupe_key raced in: look again
    raise RuntimeError("emit_event: could not assign a seq.")
