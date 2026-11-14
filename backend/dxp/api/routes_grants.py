"""Identity, grants and policies (Story 9.2, A03, AD-14).

`GET /whoami`, `GET /grants`, `GET /grants/<grant_id>`, `GET /policies`. Paths,
parameters and response models are A01's frozen ones; `app.py` mounts the
router under `/api/v1` and installs the `{ error: { code, message } }` handlers
for `ApiError`.

Every route resolves the caller from `X-DxP-Key` server-side (`api.auth`).
Grants are returned at their latest version (`?version=` for an earlier one),
with `team_name`, so the Run console can label each grant with its Team (D18).
The key hash is never returned.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.gate import policy_sets

router = APIRouter()

POLICY_STATUSES = ("draft", "active", "retired")


async def _labels(db: Any) -> tuple[dict[str, str], dict[str, str]]:
    """Team names (from `teams`, A13) and research scope names, by ID."""
    teams = await db["teams"].find({}, {"name": 1}).to_list(length=None)
    scopes = await db["research_scopes"].find({}, {"name": 1}).to_list(length=None)
    return (
        {t["_id"]: t.get("name") for t in teams},
        {s["_id"]: s.get("name") for s in scopes},
    )


def grant_view(grant: dict[str, Any], team_names: dict[str, str], scope_names: dict[str, str]) -> m.Grant:
    """The AD-14 `Grant`. `team_name` comes from `teams` (A13), else from the grant.

    `scope_name` (the scope title the A03 card asks for) is passed along; it
    reaches the response once the contract's `Grant` carries that field.
    """
    data = {k: v for k, v in grant.items() if k != "key_hash"}
    data["id"] = grant["_id"]
    data["team_name"] = team_names.get(grant.get("team_id")) or grant.get("team_name")
    scope_id = (grant.get("scope") or {}).get("scope_id")
    data["scope_name"] = scope_names.get(scope_id) if scope_id else None
    return m.Grant.model_validate(data)


def policy_view(policy: dict[str, Any]) -> m.Policy:
    return m.Policy.model_validate({**policy, "id": policy["_id"]})


@router.get("/whoami", response_model=m.Principal, tags=["grants"])
async def whoami(request: Request) -> m.Principal:
    return await auth.require_principal(request)


@router.get("/grants", response_model=m.GrantList, tags=["grants"])
async def list_grants(request: Request) -> m.GrantList:
    await auth.require_principal(request)
    db = policy_sets.database()
    team_names, scope_names = await _labels(db)
    grants = await policy_sets.current_grants(db)
    return m.GrantList(items=[grant_view(g, team_names, scope_names) for g in grants], next=None)


@router.get("/grants/{grant_id}", response_model=m.Grant, tags=["grants"])
async def get_grant(request: Request, grant_id: str, version: int | None = Query(default=None)) -> m.Grant:
    await auth.require_principal(request)
    db = policy_sets.database()
    if version is not None:
        grant = await policy_sets.grant_version(grant_id, version, db)
    else:
        grant = await policy_sets.latest_grant(grant_id, db)
    if grant is None:
        label = f"{grant_id}@v{version}" if version is not None else grant_id
        raise ApiError(404, "grant_not_found", f"No grant {label}.")
    team_names, scope_names = await _labels(db)
    return grant_view(grant, team_names, scope_names)


@router.get("/policies", response_model=m.PolicyList, tags=["grants"])
async def list_policies(request: Request, status: str | None = Query(default=None)) -> m.PolicyList:
    """Without `status`, the members of the current policy set; with it, the
    policies whose latest version has that status. Always the current set's version."""
    await auth.require_principal(request)
    if status is not None and status not in POLICY_STATUSES:
        raise ApiError(400, "invalid_status", f"status must be one of {', '.join(POLICY_STATUSES)}.")
    db = policy_sets.database()
    current = await policy_sets.record_current_set(db)
    if status is None:
        policies = await policy_sets.policies_in_set(current["_id"], db)
    else:
        policies = [p for p in await policy_sets.latest_policies(db) if p.get("status") == status]
    return m.PolicyList(items=[policy_view(p) for p in policies], policy_set_version=current["_id"])
