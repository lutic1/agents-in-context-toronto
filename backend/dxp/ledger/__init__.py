"""The ledger: the only writer of Records and proposals (AD-1).

``ledger.file(finding_id, changes, mode, ctx)`` gates and files each change;
``ledger.apply(proposal_id)`` and ``ledger.recover_applying()`` apply a pending
proposal exactly once and finish an interrupted apply (A06). ``review.py``
(``review_value``, the only writer of reviewed values, AD-1) belongs to A14
and ``revert.py`` to A26. ``ledger`` imports ``gate`` and nothing from ``reports``,
``memory`` or ``retrieval``.
"""

from __future__ import annotations

from dxp.ledger.apply import (
    apply,
    apply_with,
    recover_applying,
    reject_report_proposals,
)
from dxp.ledger.file import ensure_diagnostic, file, file_detailed
from dxp.ledger.revert import recover_reverting, revert_proposal
from dxp.ledger.types import Change, Filed, LedgerCtx

__all__ = [
    "Change",
    "Filed",
    "LedgerCtx",
    "apply",
    "apply_with",
    "ensure_diagnostic",
    "file",
    "file_detailed",
    "recover_applying",
    "reject_report_proposals",
    "recover_reverting",
    "review_value",
    "revert_proposal",
]


def __getattr__(name: str):
    # ledger.review_value is A14's (PR #28). The stub on main does not define it yet,
    # so it is resolved on first use instead of at import.
    if name == "review_value":
        from dxp.ledger.review import review_value

        return review_value
    raise AttributeError(f"module 'dxp.ledger' has no attribute {name!r}")
