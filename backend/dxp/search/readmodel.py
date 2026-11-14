"""The Record read model (Story 1.1). Stub from A01 (contract); finished by A14. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Record


async def get_diagnostic(dx_id: str) -> Record | None:
    """Accepted knowledge only: passed or manual entries, no_data on empty fields, data_as_of. None if unknown."""
    raise NotImplementedError("search.readmodel.get_diagnostic (A14)")
