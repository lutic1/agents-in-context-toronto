"""Review of an unreviewed value (A14; Story 2.3, D16), and the caller helpers A14's routes share.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.

The caller is resolved server-side from `X-DxP-Key` (AD-18, D17); no name in the body is read.
A blocked review is not an error: it returns 200 with the unchanged Record and the blocked
Decision (D5).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request  # noqa: F401

from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.ledger import review as ledger_review
from dxp.search import readmodel

router = APIRouter()
OWNER = "A14"
KEY_HEADER = "X-DxP-Key"


def _key(request: Request) -> str:
    return request.headers.get(KEY_HEADER) or ""


async def caller(request: Request) -> m.Principal:
    """The calling principal (A03's `require_principal`): 401 for a missing or unknown key, 403 for
    the seed key, which is command line only (AD-17)."""
    return await auth.require_principal(request)


async def caller_grant(request: Request) -> m.Grant:
    """The latest version of the grant that carries the caller's key, whatever its status:
    check 1 of the gate judges the status (D17)."""
    doc = await auth.grant_for_key(_key(request))  # A03
    if doc is None:
        raise ApiError(401, "unknown_key", "Unknown API key.")
    return m.Grant.model_validate({**doc, "id": doc["_id"]})


async def reviewer_context(request: Request) -> m.RunContext:
    """A Reviewer decision's context: no run, a reviewer stamp and a server-generated request_id (D19, D20)."""
    principal = await caller(request)
    grant = await caller_grant(request)
    stamp = m.Stamp(
        kind="reviewer",
        run_id=None,
        agent=None,
        initiated_by=principal.id,
        principal=principal.id,
        acting_for=grant.acting_for,
        grant_id=grant.grant_id,
        grant_version=grant.version,
    )
    return m.RunContext(
        run_id=None,
        principal=principal,
        stamp=stamp,
        grant_id=grant.grant_id,
        grant_version=grant.version,
        request_id=ledger_review.new_request_id(),
    )


@router.post("/diagnostics/{dx_id}/values/{value_id}/review", response_model=m.ValueReviewResponse, tags=["diagnostics"])
async def review_value(dx_id: str, value_id: str, body: m.ValueReviewRequest, request: Request) -> m.ValueReviewResponse:
    try:
        ctx = await reviewer_context(request)  # the caller first: 401 or 403 before any input rule
        ledger_review.validate_request(body.action, body.value, body.reason)
        outcome = await ledger_review.review_value(dx_id, value_id, body.action, body.value, body.reason, ctx)
    except ledger_review.ReviewRefused as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    record = await readmodel.get_diagnostic(dx_id)
    if record is None:
        raise ApiError(404, "not_found", f"Diagnostic {dx_id} not found.")
    return m.ValueReviewResponse(record=record, decision=outcome.decision)
