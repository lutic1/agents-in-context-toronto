"""Admissions (AD-21, D22, D23, D43). Stub from A01 (contract); finished by A07+A11. Frozen signature: change only through the contract keeper.

Re-exported from runs as runs.admit, runs.release, runs.sweep, runs.settle, runs.finish.
"""

from __future__ import annotations

from dxp.api.models import Admission


async def admit(run_id: str, item_key: str) -> Admission | None:
    """In one transaction: guard the run on status running and insert the admission.
    Not admitted: None. item_key = "<source_ref or scope_id or task_id>|<kind>|<diagnostic_id or '-'>|<target>"."""
    raise NotImplementedError("runs.admit (A07+A11)")


async def release(admission_id: str) -> None:
    """admitted -> released, conditional; a second release does nothing."""
    raise NotImplementedError("runs.release (A07+A11)")


async def sweep(run_id: str) -> list[dict[str, str]]:
    """Mark expired admitted admissions abandoned; return [{ action_id, status }] they held.
    Changes no action (D43)."""
    raise NotImplementedError("runs.sweep (A07+A11)")


async def settle(run_id: str) -> None:
    """Only stops (D23): stopping -> stopped once no admitted admission remains."""
    raise NotImplementedError("runs.settle (A07+A11)")


async def finish(run_id: str) -> None:
    """running -> done once no admitted admission remains; called by the pipeline after the last item."""
    raise NotImplementedError("runs.finish (A07+A11)")
