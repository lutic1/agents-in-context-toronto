"""The four memory routes, with a fake key resolver, grant lookup, gate and database."""

from __future__ import annotations

import pytest
from a21_a22_fakes import CLAIM, M1_TEXT, OTHER_TEAM, TEAM, install, reviewer_ctx, sam, sam_grant
from dxp import memory
from dxp.api.errors import ApiError
from dxp.api.models import MemorySource, Principal

KEY = {"X-DxP-Key": "test-dxp-api-key"}
API = "/api/v1"


@pytest.fixture
def database(monkeypatch):
    return install(monkeypatch)


GRANTS = {
    "test-dxp-api-key": {**sam_grant().model_dump(exclude={"id"}), "_id": "sam@v1"},
    "test-dxp-agent-key": {"_id": "lbdx@v1", "grant_id": "lbdx", "version": 1, "principal": "dxp-curator", "kind": "agent",
                           "team_id": TEAM, "scope": {"diagnostic_ids": [], "scope_id": "scope_plasma"},
                           "destinations": ["ledger"], "actions": ["file_proposal"], "status": "active"},
    "test-dxp-seed-key": {"_id": "seed@v1", "grant_id": "seed", "version": 1, "principal": "seed", "kind": "seed",
                          "team_id": None, "scope": {"all": True}, "destinations": ["ledger"],
                          "actions": ["apply_value"], "status": "active"},
}
AGENT = {"X-DxP-Key": "test-dxp-agent-key"}
SEED = {"X-DxP-Key": "test-dxp-seed-key"}


@pytest.fixture
def client(api_client, database, fake_gate, monkeypatch):
    """The API with A03's key lookup faked: each key resolves to the latest version of its own
    grant, as `auth.grant_for_key` and `auth.resolve_actor` do against the stored grants."""
    from dxp.api import auth

    async def grant_for_key(api_key, db=None):
        return GRANTS.get(api_key)

    async def resolve_actor(api_key):
        grant = GRANTS.get(api_key)
        if grant is None:
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return Principal(id=grant["principal"], name=grant["principal"], kind=grant["kind"], actions=grant["actions"])

    monkeypatch.setattr(auth, "grant_for_key", grant_for_key)
    monkeypatch.setattr(auth, "resolve_actor", resolve_actor)
    return api_client


async def make(decision_id="dec_reject", team_id=TEAM, run_id="run_setup"):
    created, _ = await memory.create(team_id, M1_TEXT, {"assay": "Guardant360 CDx", "claim_kind": CLAIM},
                                     MemorySource(decision_id=decision_id, report_id=f"rep_{decision_id}"),
                                     sam(), reviewer_ctx(request_id=f"req_{decision_id}"))
    return created


async def test_list_returns_the_teams_memories_with_author_source_and_status(client, database):
    m1 = await make()
    await make("dec_theirs", team_id=OTHER_TEAM)
    response = client.get(f"{API}/memories", params={"team_id": TEAM}, headers=KEY)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["next"] is None and [item["id"] for item in body["items"]] == [m1.id]
    item = body["items"][0]
    assert set(item) == {"id", "version", "team_id", "author", "source", "text", "tags", "status",
                         "supersedes", "decision_id", "created_at"}
    assert item["author"] == "sam" and item["status"] == "active" and item["team_id"] == TEAM
    assert item["source"] == {"decision_id": "dec_reject", "report_id": "rep_dec_reject"}
    assert item["tags"] == {"assay": "Guardant360 CDx", "claim_kind": CLAIM}
    assert client.get(f"{API}/memories", headers=KEY).json() == body  # the grant's Team by default


async def test_list_filters_on_the_latest_versions_status(client, database):
    m1, m2 = await make(), await make("dec_two")
    client.post(f"{API}/memories/{m2.id}/revoke", json={"note": "n"}, headers=KEY)
    active = client.get(f"{API}/memories", params={"status": "active"}, headers=KEY).json()["items"]
    revoked = client.get(f"{API}/memories", params={"status": "revoked"}, headers=KEY).json()["items"]
    assert [i["id"] for i in active] == [m1.id] and [i["id"] for i in revoked] == [m2.id]
    bad = client.get(f"{API}/memories", params={"status": "deleted"}, headers=KEY)
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_request"


async def test_another_teams_memories_cannot_be_listed_read_or_changed(client, database, fake_gate):
    theirs = await make("dec_theirs", team_id=OTHER_TEAM)
    calls = len(fake_gate.calls)
    assert client.get(f"{API}/memories", params={"team_id": OTHER_TEAM}, headers=KEY).status_code == 403
    assert client.get(f"{API}/memories/{theirs.id}", headers=KEY).status_code == 404
    assert client.post(f"{API}/memories/{theirs.id}/correct", json={"text": "t", "note": "n"}, headers=KEY).status_code == 404
    assert client.post(f"{API}/memories/{theirs.id}/revoke", json={"note": "n"}, headers=KEY).status_code == 404
    assert len(fake_gate.calls) == calls and database.memory(f"{theirs.id}@v1")["status"] == "active"


async def test_get_returns_the_latest_version_or_the_one_asked_for(client, database):
    m1 = await make()
    client.post(f"{API}/memories/{m1.id}/correct", json={"text": "new wording", "note": "n"}, headers=KEY)
    latest = client.get(f"{API}/memories/{m1.id}", headers=KEY).json()
    first = client.get(f"{API}/memories/{m1.id}", params={"version": 1}, headers=KEY).json()
    assert (latest["version"], latest["status"], latest["text"], latest["supersedes"]) == (2, "active", "new wording", f"{m1.id}@v1")
    assert (first["version"], first["status"], first["text"]) == (1, "corrected", M1_TEXT)
    for path in (f"/memories/{m1.id}?version=9", "/memories/mem_nope"):
        missing = client.get(API + path, headers=KEY)
        assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"


async def test_correct_answers_with_the_new_version_and_its_decision(client, database, fake_gate):
    database.collection("reports").documents.append({"_id": "rep_dec_reject", "run_id": "run_setup"})
    m1 = await make()
    response = client.post(f"{API}/memories/{m1.id}/correct",
                           json={"text": " new wording ", "note": "clearer", "author": "mallory"}, headers=KEY)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"memory", "decision"}
    assert (body["memory"]["version"], body["memory"]["text"], body["memory"]["author"]) == (2, "new wording", "sam")
    assert body["memory"]["supersedes"] == f"{m1.id}@v1" and body["memory"]["decision_id"] == body["decision"]["id"]
    decision = body["decision"]
    assert (decision["kind"], decision["outcome"], decision["run_id"]) == ("correct_memory", "allowed", None)
    assert decision["request_id"] and decision["cause"]["memory_id"] == m1.id
    assert decision["cause"]["origin_run_id"] == "run_setup"
    ctx, _ = fake_gate.calls[-1]
    assert ctx.principal.id == "sam" and (ctx.grant_id, ctx.grant_version) == ("sam", 1)
    assert ctx.stamp.model_dump(exclude_none=True) == {
        "kind": "reviewer", "initiated_by": "sam", "principal": "sam", "grant_id": "sam", "grant_version": 1}


async def test_revoke_answers_with_the_revoked_version_and_its_decision(client, database, fake_gate):
    m1 = await make()
    body = client.post(f"{API}/memories/{m1.id}/revoke", json={"note": "no longer true"}, headers=KEY).json()
    assert (body["memory"]["version"], body["memory"]["status"]) == (1, "revoked")
    assert (body["decision"]["kind"], body["decision"]["outcome"]) == ("revoke_memory", "allowed")
    assert body["decision"]["cause"] == {"proposal_id": None, "report_id": None, "memory_id": m1.id,
                                         "action_id": None, "origin_run_id": None}
    assert fake_gate.calls[-1][1].inputs["note"] == "no longer true"


async def test_each_request_gets_its_own_request_id(client, database, fake_gate):
    m1 = await make()
    fake_gate.block("revoke_memory")
    first = client.post(f"{API}/memories/{m1.id}/revoke", json={"note": "n"}, headers=KEY).json()["decision"]
    second = client.post(f"{API}/memories/{m1.id}/revoke", json={"note": "n"}, headers=KEY).json()["decision"]
    assert first["request_id"] and second["request_id"] and first["request_id"] != second["request_id"]


async def test_a_blocked_change_is_200_with_the_decision_and_the_unchanged_memory(client, database, fake_gate):
    m1 = await make()
    fake_gate.block("correct_memory", "destination_action")
    response = client.post(f"{API}/memories/{m1.id}/correct", json={"text": "t", "note": "n"}, headers=KEY)
    assert response.status_code == 200
    body = response.json()
    assert (body["decision"]["outcome"], body["decision"]["failed_check"]) == ("blocked", "destination_action")
    assert (body["memory"]["version"], body["memory"]["status"], body["memory"]["text"]) == (1, "active", M1_TEXT)
    assert len(database.memories) == 1


async def test_a_change_to_a_memory_that_is_not_active_is_a_conflict(client, database, fake_gate):
    m1 = await make()
    client.post(f"{API}/memories/{m1.id}/revoke", json={"note": "n"}, headers=KEY)
    calls = len(fake_gate.calls)
    for path, body in ((f"/memories/{m1.id}/revoke", {"note": "n"}), (f"/memories/{m1.id}/correct", {"text": "t", "note": "n"})):
        response = client.post(API + path, json=body, headers=KEY)
        assert response.status_code == 409 and response.json()["error"]["code"] == "conflict"
    assert len(fake_gate.calls) == calls


@pytest.mark.parametrize(("path", "body"), [
    ("correct", {"text": "t", "note": " "}), ("correct", {"text": "", "note": "n"}),
    ("correct", {"text": "t"}), ("revoke", {"note": ""}), ("revoke", {}),
])
async def test_a_note_is_required_before_the_gate(client, database, fake_gate, path, body):
    m1 = await make()
    calls = len(fake_gate.calls)
    response = client.post(f"{API}/memories/{m1.id}/{path}", json=body, headers=KEY)
    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_request"
    assert len(fake_gate.calls) == calls and database.memory(f"{m1.id}@v1")["status"] == "active"


ROUTES = [
    ("GET", "/memories", None), ("GET", "/memories/mem_x", None),
    ("POST", "/memories/mem_x/correct", {"text": "t", "note": "n"}), ("POST", "/memories/mem_x/revoke", {"note": "n"}),
]


@pytest.mark.parametrize(("method", "path", "body"), ROUTES)
async def test_every_route_needs_a_known_key_and_refuses_the_seed_key(client, database, fake_gate, method, path, body):
    """V67: 401 for a missing or unknown key, 403 for the seed key, on reads and changes alike."""
    missing = client.request(method, API + path, json=body)
    unknown = client.request(method, API + path, json=body, headers={"X-DxP-Key": "nope"})
    seed = client.request(method, API + path, json=body, headers=SEED)
    assert (missing.status_code, unknown.status_code, seed.status_code) == (401, 401, 403)
    assert missing.json()["error"]["code"] == "unknown_key"
    assert seed.json()["error"]["code"] == "seed_key_not_accepted"
    assert fake_gate.calls == []


async def test_the_agents_key_reads_its_own_teams_memories_but_changes_none(client, database, fake_gate):
    m1 = await make()
    theirs = await make("dec_theirs", team_id=OTHER_TEAM)
    calls = len(fake_gate.calls)
    listed = client.get(f"{API}/memories", headers=AGENT)
    assert listed.status_code == 200 and [item["id"] for item in listed.json()["items"]] == [m1.id]
    assert client.get(f"{API}/memories/{m1.id}", headers=AGENT).status_code == 200
    assert client.get(f"{API}/memories/{theirs.id}", headers=AGENT).status_code == 404
    for path, body in ((f"/memories/{m1.id}/correct", {"text": "t", "note": "n"}), (f"/memories/{m1.id}/revoke", {"note": "n"})):
        refused = client.post(API + path, json=body, headers=AGENT)
        assert refused.status_code == 403 and refused.json()["error"]["code"] == "forbidden"
    assert len(fake_gate.calls) == calls and database.memory(f"{m1.id}@v1")["status"] == "active"


@pytest.mark.parametrize(("method", "path", "body"), ROUTES)
async def test_a_key_with_no_grant_for_a_team_is_forbidden_not_a_server_error(client, database, fake_gate, monkeypatch, method, path, body):
    from dxp.api import auth

    for stored in (None, {**GRANTS["test-dxp-api-key"], "team_id": None}):
        async def no_team(api_key, db=None, stored=stored):
            return stored

        monkeypatch.setattr(auth, "grant_for_key", no_team)
        response = client.request(method, API + path, json=body, headers=KEY)
        assert response.status_code == 403, response.text
        assert set(response.json()) == {"error"} and response.json()["error"]["code"] == "forbidden"
    assert fake_gate.calls == []


def test_the_frozen_route_contract_is_unchanged():
    from dxp.api.app import create_app

    paths = create_app().openapi()["paths"]
    listing = paths["/api/v1/memories"]["get"]
    assert [(p["name"], p["in"]) for p in listing["parameters"]] == [("team_id", "query"), ("status", "query")]
    assert [(p["name"], p["in"]) for p in paths["/api/v1/memories/{memory_id}"]["get"]["parameters"]] == [
        ("memory_id", "path"), ("version", "query")]
    for path, model in (("correct", "MemoryCorrectRequest"), ("revoke", "MemoryRevokeRequest")):
        op = paths[f"/api/v1/memories/{{memory_id}}/{path}"]["post"]
        assert op["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(model)
        assert op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("MemoryChangeResponse")


@pytest.mark.parametrize(("path", "body"), [("correct", {"text": "", "note": ""}), ("revoke", {"note": ""})])
async def test_an_invalid_change_from_an_unknown_or_agent_key_is_refused_before_it_is_validated(
        client, database, fake_gate, path, body):
    """Authentication comes first: 401/403, never a 422 that tells a stranger what is missing."""
    m1 = await make()
    assert client.post(f"{API}/memories/{m1.id}/{path}", json=body).status_code == 401
    assert client.post(f"{API}/memories/{m1.id}/{path}", json=body, headers=SEED).status_code == 403
    assert client.post(f"{API}/memories/{m1.id}/{path}", json=body, headers=AGENT).status_code == 403
