"""Research scopes (Story 10.1, AD-25): `GET /scopes`, `GET /scopes/<scope_id>`. Owned by A05.

Paths, methods, parameters and response models are frozen (AD-14). The caller is resolved from
`X-DxP-Key` server-side (D17): no key or an unknown key is 401. Read only: the scope is seeded by
`python -m dxp.gate.seed` (A03) and only `discovery` moves its cursor.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from dxp import store
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.sources.load import cursor_text

router = APIRouter()
OWNER = "A05"
_LIMIT = 100


async def _caller(request: Request) -> m.Principal:
    key = request.headers.get("X-DxP-Key")
    if not key:
        raise ApiError(401, "unknown_key", "Missing X-DxP-Key.")
    return await auth.resolve_actor(key)


def scope_from_doc(doc: dict[str, Any]) -> m.Scope:
    """The AD-14 `Scope` from a `research_scopes` document (A03's seed shape)."""
    cursor = doc.get("cursor") or {}
    return m.Scope(
        id=doc["_id"],
        name=doc.get("name") or doc["_id"],
        team_id=doc.get("team_id") or "",
        assays=list(doc.get("assays") or []),
        aliases=list(doc.get("aliases") or []),
        condition=doc.get("condition") or "",
        source=doc.get("source") or "clinicaltrials.gov",
        cursor=m.ScopeCursor(
            last_update_post_date=cursor_text(cursor.get("last_update_post_date")),
            set_at=cursor.get("set_at"),
            set_by_run_id=cursor.get("set_by_run_id"),
        ),
    )


@router.get("/scopes", response_model=m.ScopeList, tags=["scopes"])
async def list_scopes(request: Request) -> m.ScopeList:
    await _caller(request)
    docs = await store.get_db()["research_scopes"].find({}).sort("_id", 1).to_list(length=_LIMIT)
    return m.ScopeList(items=[scope_from_doc(d) for d in docs], next=None)


@router.get("/scopes/{scope_id}", response_model=m.Scope, tags=["scopes"])
async def get_scope(scope_id: str, request: Request) -> m.Scope:
    await _caller(request)
    doc = await store.get_db()["research_scopes"].find_one({"_id": scope_id})
    if doc is None:
        raise ApiError(404, "not_found", f"Scope {scope_id} not found.")
    return scope_from_doc(doc)
