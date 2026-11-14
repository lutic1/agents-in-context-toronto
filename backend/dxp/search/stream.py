"""A run's events from an Atlas change stream on events (AD-23, V48, live_stream flag). Stub from A01 (contract); finished by A27. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any


def run_events(run_id: str, resume_after: Any | None = None) -> AsyncIterator[tuple[Any, dict[str, Any]]]:
    """Yield (resume_token, event) for each new event of the run, via store; resume_after is the
    last SSE id (Last-Event-ID)."""
    raise NotImplementedError("search.stream.run_events (A27)")
