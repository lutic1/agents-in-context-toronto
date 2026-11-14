"""Research scopes (Story 10.1). Stub from A01 (contract); finished by A05.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A05 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A05"


@router.get("/scopes", response_model=m.ScopeList, tags=["scopes"])
async def list_scopes() -> m.ScopeList:
    raise not_implemented("GET /scopes", OWNER)


@router.get("/scopes/{scope_id}", response_model=m.Scope, tags=["scopes"])
async def get_scope(scope_id: str) -> m.Scope:
    raise not_implemented("GET /scopes/<scope_id>", OWNER)
