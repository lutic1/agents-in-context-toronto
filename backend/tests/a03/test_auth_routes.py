"""Server-side actor resolution and the A03 routes (D17, D53, AD-14, AD-18)."""

from __future__ import annotations

import asyncio
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dxp.api import auth, routes_grants
from dxp.api.errors import ApiError, install_error_handlers
from dxp.gate import policy_sets, seed

from .examples import seed_data_dir


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def seeded_db(fake_db, tmp_path, keys, monkeypatch):
    run(seed.seed(fake_db, keys, seed_data_dir(tmp_path)))
    monkeypatch.setattr(policy_sets, "database", lambda given=None: given if given is not None else fake_db)
    return fake_db


@pytest.fixture
def client(seeded_db):
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(routes_grants.router, prefix="/api/v1")  # A01's app.py does this once
    return TestClient(app)


def get(client, path, key):
    return client.get(f"/api/v1{path}", headers={"X-DxP-Key": key} if key is not None else {})


# --- resolve_actor -------------------------------------------------------------------


def test_each_key_resolves_to_its_principal(seeded_db, keys):
    agent = run(auth.resolve(keys["DXP_AGENT_KEY"], seeded_db))
    sam = run(auth.resolve(keys["DXP_API_KEY"], seeded_db))
    seed_principal = run(auth.resolve(keys["DXP_SEED_KEY"], seeded_db))
    assert (agent.id, agent.kind, agent.actions) == (
        "dxp-curator",
        "agent",
        ["search_source", "file_proposal", "notify_slack"],
    )
    assert (sam.id, sam.name, sam.kind) == ("sam", "Sam", "person")
    assert "revert_report" in sam.actions and "decide_proposal" not in sam.actions
    assert (seed_principal.id, seed_principal.kind, seed_principal.actions) == ("seed", "seed", ["apply_value"])


@pytest.mark.parametrize("key", [None, "", "not-a-known-key"])
def test_only_an_unknown_key_is_401(seeded_db, key):
    with pytest.raises(ApiError) as caught:
        run(auth.resolve(key, seeded_db))
    assert caught.value.status_code == 401


def test_a_revoked_key_still_resolves_and_has_no_current_actions(seeded_db, keys):
    run(seed.new_grant_version(seeded_db, "sam", "revoked", keys))
    sam = run(auth.resolve(keys["DXP_API_KEY"], seeded_db))
    assert sam.id == "sam" and sam.actions == []  # check 1 blocks whatever it tries (A06)


def test_raw_key_is_never_stored(seeded_db, keys):
    stored = repr([doc for c in seeded_db.collections.values() for doc in c.docs.values()])
    for value in keys.values():
        assert value not in stored
    hashes = {g["key_hash"] for g in seeded_db["grants"].docs.values() if g["key_hash"]}
    assert hashes == {auth.hash_key(v) for v in keys.values()}


# --- Routes ----------------------------------------------------------------------------


def test_whoami(client, keys):
    response = get(client, "/whoami", keys["DXP_API_KEY"])
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "sam" and body["kind"] == "person" and "resolve_notification" in body["actions"]
    assert "answer_question" in body["actions"]  # sam@v2 (V70): the interview page's gated action


def test_whoami_unknown_key_uses_the_error_shape(client):
    response = get(client, "/whoami", "nope")
    assert response.status_code == 401
    assert response.json() == {"error": {"code": "unknown_key", "message": "Unknown API key."}}
    assert get(client, "/whoami", None).status_code == 401


def test_no_route_accepts_the_seed_key(client, keys):
    for path in ("/whoami", "/grants", "/grants/lbdx", "/policies"):
        response = get(client, path, keys["DXP_SEED_KEY"])
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "seed_key_not_accepted"


def test_a_body_or_query_name_never_changes_the_caller(client, keys):
    response = client.get("/api/v1/whoami?principal=sam", headers={"X-DxP-Key": keys["DXP_AGENT_KEY"]})
    assert response.json()["id"] == "dxp-curator"


def test_list_grants(client, keys):
    response = get(client, "/grants", keys["DXP_API_KEY"])
    assert response.status_code == 200
    items = {g["id"]: g for g in response.json()["items"]}
    assert set(items) == {"lbdx@v1", "sam@v2", "seed@v1"}  # the latest version of each grant (sam@v2, V70)
    lbdx = items["lbdx@v1"]
    assert lbdx["team_name"] == "Team Liquid Biopsy Dx"
    assert lbdx["scope_name"] == "Plasma ctDNA genotyping assays in NSCLC"
    assert lbdx["startable_by"] == ["sam"]
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z", lbdx["expires_at"])
    for grant in items.values():
        assert "key_hash" not in grant and "_id" not in grant


def test_grant_latest_and_by_version(client, seeded_db, keys):
    run(seed.new_grant_version(seeded_db, "lbdx", "revoked", keys))
    latest = get(client, "/grants/lbdx", keys["DXP_API_KEY"]).json()
    assert (latest["id"], latest["status"]) == ("lbdx@v2", "revoked")
    first = get(client, "/grants/lbdx?version=1", keys["DXP_API_KEY"]).json()
    assert (first["id"], first["status"]) == ("lbdx@v1", "active")
    missing = get(client, "/grants/nobody", keys["DXP_API_KEY"])
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "grant_not_found"


def test_policies(client, keys):
    body = get(client, "/policies", keys["DXP_API_KEY"]).json()
    ids = {p["id"] for p in body["items"]}
    assert {"claim_performed_or_results@v1", "claim_planned@v1", "claim_preclinical@v1"} <= ids
    assert body["policy_set_version"].startswith("ps_")
    assert get(client, "/policies?status=retired", keys["DXP_API_KEY"]).json()["items"] == []
    bad = get(client, "/policies?status=bogus", keys["DXP_API_KEY"])
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_status"
