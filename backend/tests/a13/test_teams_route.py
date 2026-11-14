"""A13: GET /teams returns the seeded Teams in the AD-14 shape."""

from __future__ import annotations

from dxp.api import routes_teams
from dxp.ledger import seed as seed_mod


async def test_get_teams(api_client, fake_db, monkeypatch) -> None:
    await seed_mod.seed_teams(fake_db)
    monkeypatch.setattr(routes_teams, "_teams", lambda: fake_db["teams"])
    response = api_client.get("/api/v1/teams")
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [t["name"] for t in items] == sorted(t["name"] for t in seed_mod.TEAMS)
    lbdx = next(t for t in items if t["name"] == "Team Liquid Biopsy Dx")
    assert lbdx["id"] == seed_mod.team_id("Team Liquid Biopsy Dx")
    assert lbdx["synthetic"] is True and lbdx["last_seen_seq"] is None
    assert set(lbdx["profile"]) == {"modalities", "biomarkers", "linked_drugs"}


async def test_get_teams_empty(api_client, fake_db, monkeypatch) -> None:
    monkeypatch.setattr(routes_teams, "_teams", lambda: fake_db["teams"])
    response = api_client.get("/api/v1/teams")
    assert response.status_code == 200 and response.json() == {"items": []}
