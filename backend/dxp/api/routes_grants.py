"""Identity, grants and policies (Story 9.2). Stub from A01 (contract); finished by A03.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A03 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A03"


@router.get("/whoami", response_model=m.Principal, tags=["grants"])
async def whoami() -> m.Principal:
    raise not_implemented("GET /whoami", OWNER)


@router.get("/grants", response_model=m.GrantList, tags=["grants"])
async def list_grants() -> m.GrantList:
    raise not_implemented("GET /grants", OWNER)


@router.get("/grants/{grant_id}", response_model=m.Grant, tags=["grants"])
async def get_grant(grant_id: str, version: int | None = Query(default=None)) -> m.Grant:
    raise not_implemented("GET /grants/<grant_id>", OWNER)


@router.get("/policies", response_model=m.PolicyList, tags=["grants"])
async def list_policies(status: str | None = Query(default=None)) -> m.PolicyList:
    raise not_implemented("GET /policies", OWNER)
