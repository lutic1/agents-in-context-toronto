"""Run audit and decisions (Story 9.6, AD-22, V14). Finished by A07+A11; A11's part only reads.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
"Who authorised" is always the Decision's `authorised_by` (D40).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request  # noqa: F401

from dxp.api import models as m
from dxp.api.routes_runs import caller
from dxp.search import audit

router = APIRouter()
OWNER = "A07+A11"


@router.get("/runs/{run_id}/audit", response_model=m.Audit, tags=["audit"])
async def get_audit(run_id: str, request: Request) -> m.Audit:
    await caller(request)
    return await audit.run_audit(run_id)


@router.get("/decisions/{decision_id}", response_model=m.Decision, tags=["audit"])
async def get_decision(decision_id: str, request: Request) -> m.Decision:
    await caller(request)
    return await audit.decision_detail(decision_id)
