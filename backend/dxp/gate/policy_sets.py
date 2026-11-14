"""Grant and policy-set selection: latest version first, then status (D6). Stub from A01 (contract); finished by A03. Frozen signature: change only through the contract keeper."""

from __future__ import annotations

from dxp.api.models import Grant, PolicySet


async def current_grant(grant_id: str) -> Grant:
    """The latest version of the grant, whatever its status (check 1 judges the status)."""
    raise NotImplementedError("gate.policy_sets.current_grant (A03)")


async def current_set() -> PolicySet:
    """The policies whose latest version is active; inserts the policy_sets document on first use."""
    raise NotImplementedError("gate.policy_sets.current_set (A03)")
