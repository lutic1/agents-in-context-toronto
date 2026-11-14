"""External actions (AD-20): the Slack notifier (A09, Story 9.4).

Frozen signatures (A01): `dispatch(action, ctx)`, `mark_unknown(action_id, error)`,
`mark_failed(action_id, error)`, `resolve(action_id, outcome, note, ctx)`.

- `dispatcher.py`: gate first, save the action ID, claim it once, post once, record exactly
  what was observed (S7).
- `slack.py`: the only module that posts to Slack; configuration, the message, the sender.
- `marks.py`: `mark_unknown` and `mark_failed`, for the sweep (D24, D43).
- `resolution.py`: the Reviewer's manual resolution of an `unknown` alert (S8).
- `records.py`: the conditional updates on `actions`; A09 writes nothing else.

actions imports nothing from memory, retrieval or reports (AD-28).
"""

from __future__ import annotations

from dxp.actions.dispatcher import dispatch
from dxp.actions.errors import ActionBlocked, ActionNotFound, NotResolvable, NoteRequired, ReportNotFound, SenderNotConfigured
from dxp.actions.marks import mark_failed, mark_unknown
from dxp.actions.resolution import resolve

__all__ = [
    "ActionBlocked",
    "ActionNotFound",
    "NotResolvable",
    "NoteRequired",
    "ReportNotFound",
    "SenderNotConfigured",
    "dispatch",
    "mark_failed",
    "mark_unknown",
    "resolve",
]
