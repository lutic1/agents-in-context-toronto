"""The only starter of a task's run (V38). Stub from A01 (contract); finished by A24. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from dxp.api.models import Run

StartRun = Callable[[str], Awaitable[Any] | Any]


async def dispatch_next(start: StartRun) -> Run | None:
    """Start the oldest queued task if no run is running or stopping: runs.start on
    derive("run_", task_id), insert-if-absent; only the inserter calls start(run_id).
    No-op stub: does nothing while task_run is off (V38, V46) and until A24 merges."""
    return None


async def mark_abandoned(task_id: str) -> None:
    """running -> failed (error: abandoned), conditional; never restarted."""
    raise NotImplementedError("tasks.mark_abandoned (A24)")
