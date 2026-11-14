"""Manual resolution of an unknown notification (Story 9.4, S8, AD-20). Finished by A09.

`POST /actions/<action_id>/resolve { outcome: delivered | failed, note }` lets a Reviewer
settle an `unknown` Slack alert after checking `#all-mango-db-hackathon` for the action ID.
The caller is resolved server-side from `X-DxP-Key` (D17); a body field never confers
permission. The resolution is gated as `resolve_notification` under the caller's own grant
and recorded as a Decision with the Reviewer's stamp. It never posts to Slack.

- 200 `{ action, decision }`: resolved, or blocked by the gate (a blocked action is not an
  error: the action is unchanged and the Decision says why, D5).
- 401 missing or unknown key; 403 the seed key. The grant is the one the key belongs to
  (A03's `auth.grant_for_key`); an agent's grant lacks `resolve_notification`, so the gate blocks.
- 404 no such action; 409 the action is not an `unknown` Slack alert; 422 no note.

Paths, methods, parameters and response models are A01's frozen ones.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Request

from dxp import actions
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError

router = APIRouter()
OWNER = "A09"
KEY_HEADER = "X-DxP-Key"


async def reviewer_context(request: Request) -> m.RunContext:
    """The Reviewer's context: principal and grant from the key (A03), a
    server-generated `request_id` (D20), `run_id: null` (AD-17)."""
    key = request.headers.get(KEY_HEADER) or ""
    if not key:
        raise ApiError(401, "missing_key", "Send your DxP key in the X-DxP-Key header.")
    # A03 (PR #17): the latest version of the grant this key belongs to, whatever its status
    # (check 1 judges the status), or None for an unknown key.
    grant = await auth.grant_for_key(key)
    if grant is None:
        raise ApiError(401, "unknown_key", "Unknown API key.")
    principal = await auth.resolve_actor(key)
    if principal.kind == "seed":
        raise ApiError(403, "seed_key_not_accepted", "The seed key is for the command line only.")
    stamp = m.Stamp(
        kind="reviewer",
        run_id=None,
        agent=None,
        initiated_by=principal.id,
        principal=principal.id,
        acting_for=grant.get("acting_for"),
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
    )
    return m.RunContext(
        run_id=None,
        principal=principal,
        stamp=stamp,
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
        request_id=secrets.token_hex(8),
    )


@router.post("/actions/{action_id}/resolve", response_model=m.ResolveResponse, tags=["actions"])
async def resolve_action(action_id: str, body: m.ResolveRequest, request: Request) -> m.ResolveResponse:
    ctx = await reviewer_context(request)
    try:
        action, decision = await actions.resolve(action_id, body.outcome, body.note, ctx)
    except actions.NoteRequired as exc:
        raise ApiError(422, "note_required", str(exc)) from None
    except actions.ActionNotFound:
        raise ApiError(404, "action_not_found", f"Action {action_id} not found.") from None
    except actions.NotResolvable as exc:
        raise ApiError(409, "not_unknown", str(exc)) from None
    return m.ResolveResponse(action=action, decision=decision)
