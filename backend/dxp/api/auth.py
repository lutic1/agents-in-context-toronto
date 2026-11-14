"""Server-side actor resolution from `X-DxP-Key` (A03, AD-18, D17, D53).

The API hashes the key with SHA-256 and finds the principal by `key_hash`
across every grant version that carries one, whatever its status. 401 means
only an unknown key: a key whose grant is revoked or expired still resolves,
and the gate's check 1 blocks what it tries (recorded as a blocked Decision).
The raw key is never stored, logged or traced; only its hash is compared.

A body field never confers permission: routes take the actor from here only.
No API route accepts the seed key (AD-17); `require_principal` refuses it.
"""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from dxp.api import models
from dxp.gate import policy_sets

KEY_HEADER = "X-DxP-Key"


class AuthError(Exception):
    """A refused caller. `response()` gives the AD-14 error shape."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message

    def response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={"error": {"code": self.code, "message": self.message}},
        )


def hash_key(api_key: str) -> str:
    """SHA-256 hex of the key, as stored in `grants.key_hash`."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


async def grant_for_key(api_key: str | None, db: Any = None) -> dict[str, Any] | None:
    """The latest version of the grant whose key this is, or `None` if unknown.

    The match may be on any version (an older `active` one, or a newer
    `revoked` one); the principal comes from the latest version (AD-18).
    """
    if not api_key:
        return None
    database = policy_sets.database(db)
    matches = (
        await database[policy_sets.GRANTS]
        .find({"key_hash": hash_key(api_key)}, {"grant_id": 1, "version": 1})
        .sort("version", -1)
        .to_list(length=None)
    )
    grant_ids = sorted({m["grant_id"] for m in matches})
    if not grant_ids:
        return None
    if len(grant_ids) > 1:
        # One key maps to one principal (AD-18). The seed refuses to write this,
        # so it means hand-edited data; refuse rather than guess.
        raise AuthError(500, "ambiguous_key", "This key matches more than one grant.")
    return await policy_sets.current_grant(grant_ids[0], database)


def principal_from_grant(grant: dict[str, Any]) -> Any:
    """`Principal { id, name, kind, actions }` (D53).

    `actions` are the actions of the caller's current grant: the latest
    version's actions while it is active and unexpired, otherwise none.
    """
    actions = list(grant.get("actions", [])) if policy_sets.grant_is_active(grant) else []
    return models.Principal(
        id=grant["principal"],
        name=grant.get("principal_name") or grant["principal"],
        kind=grant["kind"],
        actions=actions,
    )


async def resolve_actor(api_key: str | None, db: Any = None) -> Any:
    """Frozen signature (A03): the `Principal` behind a key, or `AuthError` 401."""
    grant = await grant_for_key(api_key, db)
    if grant is None:
        raise AuthError(401, "unknown_key", "Unknown API key.")
    return principal_from_grant(grant)


async def require_principal(request: Request, db: Any = None) -> Any:
    """The caller of an API request. 401 for a missing or unknown key; 403 for the seed key."""
    principal = await resolve_actor(request.headers.get(KEY_HEADER), db)
    if principal.kind == "seed":
        raise AuthError(403, "seed_key_not_accepted", "The seed key is for the command line only.")
    return principal
