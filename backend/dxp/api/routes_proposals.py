"""Proposals (Story 2.2). Stub from A01 (contract); finished by A14.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A14 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A14"


@router.get("/proposals", response_model=m.ProposalList, tags=["proposals"])
async def list_proposals(
    status: str | None = Query(default=None),
    field: str | None = Query(default=None),
    diagnostic_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    report_id: str | None = Query(default=None),
) -> m.ProposalList:
    raise not_implemented("GET /proposals", OWNER)


@router.get("/proposals/{p_id}", response_model=m.Proposal, tags=["proposals"])
async def get_proposal(p_id: str) -> m.Proposal:
    raise not_implemented("GET /proposals/<p_id>", OWNER)
