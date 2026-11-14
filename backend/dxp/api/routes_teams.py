"""Teams (Story 1.2), finished by A13.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
`GET /teams` returns every Team in `teams`, sorted by name; the seed inserts three synthetic
Teams (`python -m dxp.ledger.seed`). It reads only: no Team is created or changed here.
Like every read route it needs a known `X-DxP-Key` and refuses the seed key (401 / 403,
build-day ruling, 14 Nov), through A03's `auth.require_principal`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request  # noqa: F401

from dxp.api import auth
from dxp.api import models as m

router = APIRouter()
OWNER = "A13"


def _teams() -> Any:
    """The `teams` collection (a seam for tests)."""
    from dxp import store

    return store.collection("teams")


def team_from_doc(doc: dict[str, Any]) -> m.Team:
    return m.Team(
        id=doc["_id"],
        name=doc["name"],
        profile={k: list(v) for k, v in (doc.get("profile") or {}).items()},
        last_seen_seq=doc.get("last_seen_seq"),
        last_seen_at=doc.get("last_seen_at"),
        synthetic=bool(doc.get("synthetic", False)),
    )


@router.get("/teams", response_model=m.TeamList, tags=["teams"])
async def list_teams(request: Request) -> m.TeamList:
    await auth.require_principal(request)
    docs = [doc async for doc in _teams().find({}).sort([("name", 1), ("_id", 1)])]
    return m.TeamList(items=[team_from_doc(d) for d in docs])
