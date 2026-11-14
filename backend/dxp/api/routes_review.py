"""Review of an unreviewed value (Story 2.3, D16). Stub from A01 (contract); finished by A14.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A14 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A14"


@router.post("/diagnostics/{dx_id}/values/{value_id}/review", response_model=m.ValueReviewResponse, tags=["diagnostics"])
async def review_value(dx_id: str, value_id: str, body: m.ValueReviewRequest) -> m.ValueReviewResponse:
    raise not_implemented("POST /diagnostics/<dx_id>/values/<value_id>/review", OWNER)
