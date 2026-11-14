"""Task grants (AD-18, AD-29). Stub from A01 (contract); finished by A24. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Decision, Grant, Task


async def issue_task_grant(task: Task, decision: Decision, session: Any | None = None) -> Grant:
    """The only runtime grant writer: task-<hex>@v1 after an allowed authorise_task,
    inside tasks.authorise()'s one transaction (V38)."""
    raise NotImplementedError("gate.grants.issue_task_grant (A24)")
