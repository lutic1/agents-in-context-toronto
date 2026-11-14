"""The grounded text script (V41, AD-30). Stub from A01 (contract); finished by A19+A20. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Report


def script_for(report: Report | dict[str, Any]) -> str:
    """About ten seconds of text from the report's own fields only; adds no fact."""
    raise NotImplementedError("reports.script_for (A19+A20)")
