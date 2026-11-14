"""`mark_unknown` and `mark_failed`: settling the actions of abandoned admissions (D24, D43).

Called by the sweep's background task in `api/routes_runs.py` (A07+A11) for each action
`runs.sweep` returns. Both are conditional updates: they change nothing (and return False)
when the action has moved on, so a slow sweep never overwrites a recorded outcome or a
Reviewer's resolution. Neither ever posts to Slack.
"""

from __future__ import annotations

from typing import Literal

from dxp.actions import records


async def mark_unknown(action_id: str, error: Literal["abandoned_in_flight"]) -> bool:
    """dispatching -> unknown, conditional; never re-sent (D43). Its post may or may not have
    reached Slack, so a Reviewer resolves it in DxP (S8)."""
    if error != "abandoned_in_flight":
        raise ValueError(f"mark_unknown records abandoned_in_flight, not {error!r}")
    return await records.transition(action_id, "dispatching", "unknown", {"error": error, "observed_at": records.now()})


async def mark_failed(action_id: str, error: Literal["abandoned_before_send"]) -> bool:
    """queued -> failed, conditional; it was never sent (D24)."""
    if error != "abandoned_before_send":
        raise ValueError(f"mark_failed records abandoned_before_send, not {error!r}")
    return await records.transition(action_id, "queued", "failed", {"error": error, "observed_at": records.now()})
