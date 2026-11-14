"""Run configuration (AD-12, D33): concurrency, demo pacing and the agent key.

- `MAX_CONCURRENCY`: how many Source items one run processes at once. AD-12 caps it at 16;
  the run keeps it low so it stays inside the model rate limit.
- `DXP_DEMO_PACE`: when set, one item at a time and a pause after each, so the anchor is
  first and a stop lands mid-run. A number is the pause in seconds; any other non-empty
  value ("1", "true", "on") means the default pause.
- `DXP_AGENT_KEY`: the worker acts with the agent's key (AD-17). Its value is never logged.
"""

from __future__ import annotations

import os

MAX_CONCURRENCY_CAP = 16
MAX_CONCURRENCY = 4
DEFAULT_PACE_SECONDS = 4.0
OFF_VALUES = {"", "0", "false", "off", "no"}

# Top-k for related evidence (AD-15). The report shows each score; none enters a check.
RELATED_K = 5

# The only Slack destination an agent grant names (S1, S2).
SLACK_DESTINATION = "slack:#all-mango-db-hackathon"


def concurrency() -> int:
    """1 with DXP_DEMO_PACE set, else MAX_CONCURRENCY, never above 16."""
    if pace_seconds() is not None:
        return 1
    return max(1, min(MAX_CONCURRENCY, MAX_CONCURRENCY_CAP))


def pace_seconds() -> float | None:
    """The pause after each item, or None when DXP_DEMO_PACE is unset or off."""
    raw = os.environ.get("DXP_DEMO_PACE", "").strip()
    if raw.lower() in OFF_VALUES:
        return None
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_PACE_SECONDS
    # "1" reads as "on" (a one-second pause is too short to see); larger numbers are seconds.
    return value if value > 1 else DEFAULT_PACE_SECONDS


def agent_key() -> str:
    key = os.environ.get("DXP_AGENT_KEY", "").strip()
    if not key:
        raise RuntimeError("DXP_AGENT_KEY is not set.")
    return key
