"""Task authorisation (AD-29, V38, V45). Stub from A01 (contract); finished by A24. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Principal, Task


async def authorise(report_id: str, reviewer: Principal) -> Task:
    """Gated authorise_task: the Decision, the task (queued with task_run on, else authorised),
    its grant and the queue entry in one transaction."""
    raise NotImplementedError("tasks.authorise (A24)")


async def recover_authorisations() -> None:
    """Complete accepted reports with approval.task_step "pending" (V45).
    No-op stub: the API start hook calls it before A24 merges."""
    return None
