"""`GET /whoami`, `GET /grants`, `GET /grants/<grant_id>`, `GET /policies` (A03, AD-14).

Every route resolves the caller from `X-DxP-Key` server-side (`api.auth`).
`app.py` (A01) registers this router once, under `/api/v1`. Failures use the
one error shape, `{ error: { code, message } }`.

Grants are returned at their latest version (`?version=` for an earlier one),
with `id` (`<grant_id>@v<version>`), `team_name` and `scope_name`, so the Run
console can label each grant with its Team and research scope (D18). The key
hash is never returned.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dxp.api import auth
from dxp.gate import policy_sets

router = APIRouter()

POLICY_STATUSES = ("draft", "active", "retired")
HIDDEN_FIELDS = {"_id", "key_hash"}


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _json(value: Any) -> Any:
    """Datetimes as ISO 8601 UTC with `Z` (Consistency Conventions)."""
    if isinstance(value, datetime):
        return policy_sets.utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json(v) for v in value]
    return value


async def _labels(db: Any) -> tuple[dict[str, str], dict[str, str]]:
    """Team names (from `teams`, A13) and research scope names, by ID."""
    teams = await db["teams"].find({}, {"name": 1}).to_list(length=None)
    scopes = await db["research_scopes"].find({}, {"name": 1}).to_list(length=None)
    return (
        {t["_id"]: t.get("name") for t in teams},
        {s["_id"]: s.get("name") for s in scopes},
    )


def grant_view(grant: dict[str, Any], team_names: dict[str, str], scope_names: dict[str, str]) -> dict[str, Any]:
    """The AD-14 `Grant` shape, plus `scope_name`, without the key hash."""
    view = {"id": grant["_id"], **{k: v for k, v in grant.items() if k not in HIDDEN_FIELDS}}
    team_id = grant.get("team_id")
    view["team_name"] = team_names.get(team_id) or grant.get("team_name")
    scope_id = (grant.get("scope") or {}).get("scope_id")
    view["scope_name"] = scope_names.get(scope_id) if scope_id else None
    view.setdefault("limits", None)
    view.setdefault("task_id", None)
    return _json(view)


def policy_view(policy: dict[str, Any]) -> dict[str, Any]:
    return _json({"id": policy["_id"], **{k: v for k, v in policy.items() if k != "_id"}})


async def _caller(request: Request, db: Any) -> Any:
    return await auth.require_principal(request, db)


@router.get("/whoami")
async def whoami(request: Request) -> Any:
    db = policy_sets.database()
    try:
        principal = await _caller(request, db)
    except auth.AuthError as exc:
        return exc.response()
    return principal.model_dump(mode="json")


@router.get("/grants")
async def list_grants(request: Request) -> Any:
    db = policy_sets.database()
    try:
        await _caller(request, db)
    except auth.AuthError as exc:
        return exc.response()
    team_names, scope_names = await _labels(db)
    grants = await policy_sets.current_grants(db)
    return {"items": [grant_view(g, team_names, scope_names) for g in grants], "next": None}


@router.get("/grants/{grant_id}")
async def get_grant(request: Request, grant_id: str, version: int | None = None) -> Any:
    db = policy_sets.database()
    try:
        await _caller(request, db)
    except auth.AuthError as exc:
        return exc.response()
    if version is not None:
        grant = await policy_sets.grant_version(grant_id, version, db)
    else:
        grant = await policy_sets.current_grant(grant_id, db)
    if grant is None:
        label = f"{grant_id}@v{version}" if version is not None else grant_id
        return _error(404, "grant_not_found", f"No grant {label}.")
    team_names, scope_names = await _labels(db)
    return grant_view(grant, team_names, scope_names)


@router.get("/policies")
async def list_policies(request: Request, status: str | None = None) -> Any:
    """Without `status`, the members of the current policy set; with it, the
    policies whose latest version has that status. Always the current set's version."""
    db = policy_sets.database()
    try:
        await _caller(request, db)
    except auth.AuthError as exc:
        return exc.response()
    if status is not None and status not in POLICY_STATUSES:
        return _error(400, "invalid_status", f"status must be one of {', '.join(POLICY_STATUSES)}.")
    current = await policy_sets.current_set(db)
    if status is None:
        policies = await policy_sets.current_policies(db)
    else:
        policies = [p for p in await policy_sets.latest_policies(db) if p.get("status") == status]
    return {"items": [policy_view(p) for p in policies], "policy_set_version": current["_id"]}
