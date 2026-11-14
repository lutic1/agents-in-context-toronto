"""GET /scopes and GET /scopes/<scope_id> (AD-14 Scope shape)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from dxp.api import auth
from dxp.api.errors import ApiError
from dxp.api.models import Principal

from .conftest import SCOPE_ID, scope_doc


@pytest.fixture
def keyed(monkeypatch: pytest.MonkeyPatch) -> None:
    async def resolve_actor(api_key: str) -> Principal:
        if api_key != "good":
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return Principal(id="sam", name="Sam", kind="person", actions=[])

    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)


def test_list_and_get(fakedb, keyed, api_client) -> None:
    doc = scope_doc()
    doc["cursor"]["set_at"] = datetime(2026, 11, 14, 10, 45, tzinfo=UTC)
    fakedb["research_scopes"].docs[SCOPE_ID] = doc
    r = api_client.get("/api/v1/scopes", headers={"X-DxP-Key": "good"})
    assert r.status_code == 200
    (item,) = r.json()["items"]
    assert item["id"] == SCOPE_ID and item["name"] == "Plasma ctDNA genotyping assays in NSCLC"
    assert item["assays"][2] == "Guardant360® Liquid CDx"
    assert item["cursor"]["last_update_post_date"] == "2026-11-11"
    assert item["condition_aliases"] == ["NSCLC"] and item["priority_refs"] == ["NCT04712877"]
    r = api_client.get(f"/api/v1/scopes/{SCOPE_ID}", headers={"X-DxP-Key": "good"})
    assert r.status_code == 200 and r.json()["condition"] == "non-small cell lung cancer"


def test_errors(fakedb, keyed, api_client) -> None:
    assert api_client.get("/api/v1/scopes").status_code == 401
    assert api_client.get("/api/v1/scopes", headers={"X-DxP-Key": "bad"}).status_code == 401
    r = api_client.get("/api/v1/scopes/scope_nope", headers={"X-DxP-Key": "good"})
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
