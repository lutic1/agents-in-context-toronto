"""Task grant expiry on revert (AD-18, AD-31, V48). Stub from A01 (contract); finished by A26. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Decision, Grant, Task


async def expire_task_grant(task: Task, decision: Decision) -> Grant:
    """Insert the task grant's next version, status expired, expires_at now; never edits in place."""
    raise NotImplementedError("gate.grant_expiry.expire_task_grant (A26)")
