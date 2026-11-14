"""A27 on the Atlas Sandbox (a fresh `dxp_test_<hex>` database): a real `events.watch()` sees an
event written by `store.emit_event`, and a resume after its token sees only the next one. This is
the OD5 `watch()` check in test form. Skipped without MONGODB_URI (conftest)."""

from __future__ import annotations

import asyncio
import secrets
from typing import Any

import pytest

from dxp import store
from dxp.search import stream

pytestmark = pytest.mark.atlas


async def _first(run_id: str, resume_after: Any = None) -> tuple[str, dict[str, Any]]:
    async for token, event in stream.run_events(run_id, resume_after):
        return token, event
    raise AssertionError("the change stream ended")


async def test_a_real_watch_sees_the_runs_insert_and_resumes(db: Any) -> None:
    run_id = f"run_a27_{secrets.token_hex(4)}"
    stamp = {"actor": "test", "kind": "agent"}

    first = asyncio.create_task(_first(run_id))
    await asyncio.sleep(1.5)  # let the watch open
    await store.emit_event("run_status_changed", dedupe_key=f"{run_id}:other", stamp=stamp,
                           run_id="run_other", status="running")
    seq = await store.emit_event("run_status_changed", dedupe_key=f"{run_id}:1", stamp=stamp,
                                 run_id=run_id, status="running")
    token, event = await asyncio.wait_for(first, timeout=15)
    assert event["seq"] == seq and event["run_id"] == run_id

    seq2 = await store.emit_event("run_status_changed", dedupe_key=f"{run_id}:2", stamp=stamp,
                                  run_id=run_id, status="stopping")
    token2, event2 = await asyncio.wait_for(_first(run_id, token), timeout=15)
    assert event2["seq"] == seq2 and token2 != token
