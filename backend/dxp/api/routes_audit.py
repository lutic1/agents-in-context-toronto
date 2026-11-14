"""Run audit and decisions (Story 9.6). Stub from A01 (contract); finished by A07+A11.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A07+A11 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A07+A11"


@router.get("/runs/{run_id}/audit", response_model=m.Audit, tags=["audit"])
async def get_audit(run_id: str) -> m.Audit:
    raise not_implemented("GET /runs/<run_id>/audit", OWNER)


@router.get("/decisions/{decision_id}", response_model=m.Decision, tags=["audit"])
async def get_decision(decision_id: str) -> m.Decision:
    raise not_implemented("GET /decisions/<decision_id>", OWNER)
