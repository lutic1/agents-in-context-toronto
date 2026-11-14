"""Manual resolution of an unknown notification (Story 9.4, S8). Stub from A01 (contract); finished by A09.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A09 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A09"


@router.post("/actions/{action_id}/resolve", response_model=m.ResolveResponse, tags=["actions"])
async def resolve_action(action_id: str, body: m.ResolveRequest) -> m.ResolveResponse:
    raise not_implemented("POST /actions/<action_id>/resolve", OWNER)
