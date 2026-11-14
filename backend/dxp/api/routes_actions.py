"""Actions (Story 9.6). Stub from A01 (contract); finished by A07+A11.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A07+A11 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A07+A11"


@router.get("/actions", response_model=m.ActionList, tags=["actions"])
async def list_actions(run_id: str | None = Query(default=None), status: str | None = Query(default=None)) -> m.ActionList:
    raise not_implemented("GET /actions", OWNER)


@router.get("/actions/{action_id}", response_model=m.Action, tags=["actions"])
async def get_action(action_id: str) -> m.Action:
    raise not_implemented("GET /actions/<action_id>", OWNER)
