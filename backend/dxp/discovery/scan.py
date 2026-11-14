"""discovery.scan (AD-25). Stub from A01 (contract); finished by A05. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import RunContext


async def scan(scope_id: str, ctx: RunContext) -> list[str]:
    """Gated search_source to source:clinicaltrials.gov; returns the source_refs updated since the
    scope's cursor; the cursor advances only after the scan finishes."""
    raise NotImplementedError("discovery.scan (A05)")
