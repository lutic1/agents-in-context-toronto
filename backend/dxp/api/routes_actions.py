"""Actions (Story 9.6). Finished by A07+A11; read only.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
`GET /actions/<action_id>` is for status and results; "who authorised" is read from the
Decision's `authorised_by` (D40). `reconciling` is returned in place of `dispatching` while the
background sweep settles an action, and is never stored (D24).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from dxp.api import models as m
from dxp.api.routes_runs import caller
from dxp.search import audit

router = APIRouter()
OWNER = "A07+A11"


@router.get("/actions", response_model=m.ActionList, tags=["actions"])
async def list_actions(
    request: Request, run_id: str | None = Query(default=None), status: str | None = Query(default=None)
) -> m.ActionList:
    await caller(request)
    return m.ActionList(items=await audit.list_actions(run_id=run_id, status=status), next=None)


@router.get("/actions/{action_id}", response_model=m.Action, tags=["actions"])
async def get_action(action_id: str, request: Request) -> m.Action:
    await caller(request)
    return await audit.action_detail(action_id)
