"""The ledger: the only writer of Records (AD-1).

``ledger.file(finding_id, changes, mode, ctx)`` gates and files each change;
``ledger.apply(proposal_id)`` and ``ledger.recover_applying()`` apply a
pending proposal exactly once and finish an interrupted apply. ``ledger``
imports ``gate`` and nothing from ``reports``, ``memory`` or ``retrieval``.
"""

from dxp.ledger.apply import apply, recover_applying
from dxp.ledger.file import ensure_diagnostic, file
from dxp.ledger.types import Change, Filed, LedgerCtx

__all__ = ["Change", "Filed", "LedgerCtx", "apply", "ensure_diagnostic", "file", "recover_applying"]
