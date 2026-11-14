"""Teams (Story 1.2). Stub from A01 (contract); finished by A13.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A13 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A13"


@router.get("/teams", response_model=m.TeamList, tags=["teams"])
async def list_teams() -> m.TeamList:
    raise not_implemented("GET /teams", OWNER)
