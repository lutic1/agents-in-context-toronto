"""X-DxP-Key -> principal by key_hash across all grant versions (AD-18, D17). Stub from A01 (contract); finished by A03. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Principal


async def resolve_actor(api_key: str) -> Principal:
    """401 (ApiError) only for an unknown key; a revoked or expired grant still resolves."""
    raise NotImplementedError("api.auth.resolve_actor (A03)")
