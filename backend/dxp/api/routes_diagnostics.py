"""Accepted knowledge of one Diagnostic (A14; Story 1.1 read model, Story 1.3 narrowed, V10).

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.

`GET /diagnostics/<dx_id>` returns the Record built by `search.readmodel`: accepted knowledge
only (passed or manual entries, with history), never a pending value. A Diagnostic's pending
proposals, each with its `report_id`, are read from `GET /proposals?diagnostic_id=<dx_id>&status=pending`.
`GET /diagnostics` (the list) is deferred and stays 501 in app.py (D40).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.api.routes_review import caller
from dxp.search import readmodel

router = APIRouter()
OWNER = "A14"


@router.get("/diagnostics/{dx_id}", response_model=m.Record, tags=["diagnostics"])
async def get_diagnostic(dx_id: str, request: Request) -> m.Record:
    await caller(request)
    record = await readmodel.get_diagnostic(dx_id)
    if record is None:
        raise ApiError(404, "not_found", f"Diagnostic {dx_id} not found.")
    return record
