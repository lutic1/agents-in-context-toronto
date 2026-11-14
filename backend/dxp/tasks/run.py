"""Follow-up task execution (stretch, V39). Stub from A01 (contract); finished by A25. Frozen signature: change only through the contract keeper.

Nothing calls it while the backend flag task_run is off.
"""

from __future__ import annotations

from dxp.api.models import Task


async def run(task_id: str) -> Task:
    """queued -> running (conditional), gated search_source, file_related_evidence, at most 5."""
    raise NotImplementedError("tasks.run (A25)")
