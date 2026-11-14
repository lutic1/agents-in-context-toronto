"""A13: GET /teams returns the seeded Teams in the AD-14 shape, to a known non-seed key only."""

from __future__ import annotations

import pytest

from dxp.api import auth, routes_teams
from dxp.api.errors import ApiError
from dxp.api.models import Principal
from dxp.ledger import seed as seed_mod

KEYS = {
    "reviewer-key": Principal(id="sam", name="Sam", kind="person", actions=["decide_report"]),
    "seed-key": Principal(id="seed", name="seed", kind="seed", actions=["apply_value"]),
}


@pytest.fixture
def teams_api(api_client, fake_db, monkeypatch):
    async def resolve_actor(api_key: str) -> Principal:
        if api_key not in KEYS:
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return KEYS[api_key]

    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)
    monkeypatch.setattr(routes_teams, "_teams", lambda: fake_db["teams"])
    return api_client


async def test_get_teams(teams_api, fake_db) -> None:
    await seed_mod.seed_teams(fake_db)
    response = teams_api.get("/api/v1/teams", headers={"X-DxP-Key": "reviewer-key"})
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [t["name"] for t in items] == sorted(t["name"] for t in seed_mod.TEAMS)
    lbdx = next(t for t in items if t["name"] == "Team Liquid Biopsy Dx")
    assert lbdx["id"] == seed_mod.team_id("Team Liquid Biopsy Dx")
    assert lbdx["synthetic"] is True and lbdx["last_seen_seq"] is None
    assert set(lbdx["profile"]) == {"modalities", "biomarkers", "linked_drugs"}


async def test_get_teams_empty(teams_api) -> None:
    response = teams_api.get("/api/v1/teams", headers={"X-DxP-Key": "reviewer-key"})
    assert response.status_code == 200 and response.json() == {"items": []}


async def test_get_teams_needs_a_known_non_seed_key(teams_api, fake_db) -> None:
    await seed_mod.seed_teams(fake_db)
    assert teams_api.get("/api/v1/teams").status_code == 401
    assert teams_api.get("/api/v1/teams", headers={"X-DxP-Key": "nope"}).status_code == 401
    refused = teams_api.get("/api/v1/teams", headers={"X-DxP-Key": "seed-key"})
    assert refused.status_code == 403 and refused.json()["error"]["code"] == "seed_key_not_accepted"
