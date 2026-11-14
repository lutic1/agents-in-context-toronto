"""Runs and identity (AD-16, AD-17, AD-21). Stub from A01 (contract); finished by A07+A11. Frozen signature: change only through the contract keeper.

runs imports nothing from actions or tasks (D43, V38).
"""

from __future__ import annotations

from dxp.api.models import Principal, Run, RunContext, Stamp
from dxp.runs.admissions import admit, finish, release, settle, sweep

__all__ = ["admit", "context", "finish", "release", "settle", "start", "stamp", "stop", "sweep"]


async def start(caller: Principal, grant_id: str, set: str, run_id: str | None = None) -> Run:
    """Create a run under the latest version of the grant, checked against startable_by.

    set is discover, nct:<NCT ID> or task:<task_id>. run_id is passed only for a task's
    derived run ID, derive("run_", task_id), insert-if-absent (V38).
    """
    raise NotImplementedError("runs.start (A07+A11)")


async def context(run_id: str, key: str) -> RunContext:
    """Resolve the worker key; refuse unless it resolves to the run's agent (AD-17)."""
    raise NotImplementedError("runs.context (A07+A11)")


async def stop(run_id: str) -> Run:
    """running -> stopping (conditional), then settle. Any other status is returned unchanged."""
    raise NotImplementedError("runs.stop (A07+A11)")


async def stamp(run_id: str) -> Stamp:
    """The only stamp maker for run writes; kind run."""
    raise NotImplementedError("runs.stamp (A07+A11)")
