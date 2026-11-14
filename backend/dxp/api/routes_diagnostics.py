"""Accepted knowledge of one Diagnostic (Story 1.1 read model). Stub from A01 (contract); finished by A14.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A14 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A14"


@router.get("/diagnostics/{dx_id}", response_model=m.Record, tags=["diagnostics"])
async def get_diagnostic(dx_id: str) -> m.Record:
    raise not_implemented("GET /diagnostics/<dx_id>", OWNER)
