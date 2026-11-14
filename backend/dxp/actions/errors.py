"""Errors `actions` raises to its callers (A10's run, A07+A11's sweep task, the resolve route)."""

from __future__ import annotations

from typing import Any

from dxp.actions.slack import SenderNotConfigured

__all__ = ["ActionBlocked", "ActionNotFound", "NotResolvable", "NoteRequired", "ReportNotFound", "SenderNotConfigured"]


class ActionBlocked(Exception):
    """The gate blocked the action: the Decision is recorded, and nothing else happened (D5)."""

    def __init__(self, decision: dict[str, Any]) -> None:
        super().__init__(f"blocked by {decision.get('failed_check')} (decision {decision.get('_id')})")
        self.decision = decision
        self.decision_id = decision.get("_id")


class ReportNotFound(LookupError):
    """A notify_slack action names a report that is not in `reports`."""


class ActionNotFound(LookupError):
    """No action has this ID (404)."""


class NotResolvable(Exception):
    """Only an `unknown` notify_slack action can be resolved by hand (409, S8)."""

    def __init__(self, action_id: str, status: str | None, kind: str | None = None) -> None:
        reason = f"is {kind}, not notify_slack" if kind and kind != "notify_slack" else f"is {status}, not unknown"
        super().__init__(f"Action {action_id} {reason}: only an unknown Slack alert can be resolved.")
        self.status = status


class NoteRequired(ValueError):
    """A resolution without a note is refused before the gate (D16)."""
