"""Cancel a report's follow-up task on revert (AD-31, V48). Stub from A01 (contract); finished by A26. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Decision, Report, Task


async def cancel_for_report(report: Report, decision: Decision) -> Task | None:
    """authorised or queued -> cancelled (conditional) plus grant expiry; running -> runs.stop;
    done, failed, blocked or stopped left as they are. None when the report has no task."""
    raise NotImplementedError("tasks.cancel_for_report (A26)")
