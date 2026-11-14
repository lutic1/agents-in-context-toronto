"""Interview this evidence (V70, interview flag).

`POST /reports/<report_id>/interview { question }` returns `{ answer, citations[], refused, refusal_reason,
decision_id }`. Paths, methods, parameters and response models are A01's frozen ones (AD-14).

- Flag `interview` off: 404, as for every flagged route.
- The caller comes from `X-DxP-Key` (a body field never confers permission). The Reviewer context the gate
  needs is built here: no run, a Reviewer stamp, a server-generated request ID and the report as the cause.
- A blocked question is not an error: it is a 200 with `refused: true`, `refusal_reason: "blocked"` and the
  blocked Decision's ID (D5).
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Request

from dxp import feature_enabled
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.gate import policy_sets
from dxp.interview import answer_question, repo

router = APIRouter()
OWNER = "Interview"


async def reviewer_context(request: Request, principal: m.Principal, report: dict) -> m.RunContext:
    """The context of a Reviewer decision (D19, D20): `run_id` null, Reviewer stamp, request ID and cause set."""
    grant = await auth.grant_for_key(request.headers.get(auth.KEY_HEADER) or "")
    if grant is None:
        raise ApiError(401, "unknown_key", "Unknown API key.")
    current_set = await policy_sets.current_set()
    stamp = m.Stamp(
        kind="reviewer",
        run_id=None,
        agent=None,
        initiated_by=principal.id,
        principal=principal.id,
        acting_for=grant.get("acting_for"),
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
        policy_set_version=current_set.id,
    )
    return m.RunContext(
        run_id=None,
        principal=principal,
        stamp=stamp,
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
        policy_set_version=current_set.id,
        mode="live",
        request_id=f"req_{secrets.token_hex(8)}",
        cause=m.DecisionCause(report_id=report.get("_id") or report.get("id"), origin_run_id=report.get("run_id")),
    )


@router.post("/reports/{report_id}/interview", response_model=m.InterviewResponse, tags=["reports"])
async def interview_report(report_id: str, body: m.InterviewRequest, request: Request) -> m.InterviewResponse:
    if not feature_enabled("interview"):
        raise ApiError(404, "not_found", "Not found.")
    principal = await auth.require_principal(request)
    report = await repo.get_report(report_id)
    if report is None:
        raise ApiError(404, "not_found", "Report not found.")
    ctx = await reviewer_context(request, principal, report)
    return await answer_question(report_id, body.question, ctx, report=report)
