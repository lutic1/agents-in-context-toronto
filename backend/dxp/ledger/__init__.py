"""The ledger: the only writer of Records and proposals (AD-1).

``ledger.file(finding_id, changes, mode, ctx)`` gates and files each change;
``ledger.apply(proposal_id)`` and ``ledger.recover_applying()`` apply a pending
proposal exactly once and finish an interrupted apply (A06). ``revert.py``
belongs to A26. ``ledger`` imports ``gate`` and nothing from ``reports``,
``memory`` or ``retrieval``.
"""

from __future__ import annotations

from dxp.ledger.apply import apply, apply_with, recover_applying
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
    "recover_reverting",
    "revert_proposal",
]
