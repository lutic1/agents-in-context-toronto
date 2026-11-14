"""Proposals read routes (A14; Story 2.2, D42, D47).

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.

Proposals are decided through their report (`POST /reports/<report_id>/decision`, A24); the
per-proposal decision route is superseded (V8) and stays 501 in app.py. These routes read only.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.api.routes_review import caller
from dxp.search import readmodel

router = APIRouter()
OWNER = "A14"


@router.get("/proposals", response_model=m.ProposalList, tags=["proposals"])
async def list_proposals(
    request: Request,
    status: str | None = Query(default=None),
    field: str | None = Query(default=None),
    diagnostic_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    report_id: str | None = Query(default=None),
) -> m.ProposalList:
    await caller(request)
    try:
        items = await readmodel.list_proposals(
            status=status, field=field, diagnostic_id=diagnostic_id, run_id=run_id, report_id=report_id
        )
    except ValueError as exc:
        raise ApiError(400, "bad_request", str(exc)) from exc
    return m.ProposalList(items=items, next=None)


@router.get("/proposals/{p_id}", response_model=m.Proposal, tags=["proposals"])
async def get_proposal(p_id: str, request: Request) -> m.Proposal:
    await caller(request)
    proposal = await readmodel.get_proposal(p_id)
    if proposal is None:
        raise ApiError(404, "not_found", f"Proposal {p_id} not found.")
    return proposal
