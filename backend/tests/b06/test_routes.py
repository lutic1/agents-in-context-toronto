"""POST and GET /reports/<report_id>/briefing, and "nothing generates a briefing automatically"."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import dxp
from dxp.api import auth, routes_briefing
from dxp.api import models as m
from dxp.api.errors import ApiError, install_error_handlers
from dxp.gate import policy_sets

from .conftest import REPORT_ID, SCRIPT, api_error

SAM = m.Principal(id="sam", name="Sam", kind="person", actions=["generate_briefing"])
AGENT = m.Principal(id="dxp-curator", name="dxp-curator", kind="agent", actions=["search_source"])
KEYS = {"sam-key": SAM, "agent-key": AGENT}


@pytest.fixture
def client(fake_db, gate, monkeypatch):
    async def require_principal(request):
        principal = KEYS.get(request.headers.get(auth.KEY_HEADER) or "")
        if principal is None:
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return principal

    async def grant_for_key(key, db=None):
        return {"grant_id": "sam", "version": 1, "acting_for": "team_x"} if key == "sam-key" else None

    async def current_set():
        return m.PolicySet(id="ps_test", members=[])

    monkeypatch.setattr(auth, "require_principal", require_principal)
    monkeypatch.setattr(auth, "grant_for_key", grant_for_key)
    monkeypatch.setattr(policy_sets, "current_set", current_set)
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(routes_briefing.router, prefix="/api/v1")
    return TestClient(app)


def sam():
    return {"X-DxP-Key": "sam-key"}


URL = f"/api/v1/reports/{REPORT_ID}/briefing"


def test_post_generates_and_returns_briefing_and_decision(client, gate, eleven):
    res = client.post(URL, headers=sam())

    assert res.status_code == 200
    body = res.json()
    assert body["briefing"]["status"] == "ready" and body["briefing"]["script"] == SCRIPT
    assert body["decision"]["kind"] == "generate_briefing" and body["decision"]["outcome"] == "allowed"
    assert body["decision"]["destination"] == "tts:elevenlabs"
    ctx = gate.calls[0][0]
    assert (ctx.run_id, ctx.stamp.kind, ctx.stamp.initiated_by, ctx.grant_id) == (None, "reviewer", "sam", "sam")
    assert ctx.cause.report_id == REPORT_ID and ctx.cause.origin_run_id == "run_abc"
    assert ctx.request_id.startswith("req_")  # server generated; the body is never read
    assert eleven.convert_calls[0]["text"] == SCRIPT


def test_each_press_gets_its_own_request_id(client, gate, eleven):
    client.post(URL, headers=sam())
    client.post(URL, headers=sam())
    assert gate.calls[0][0].request_id != gate.calls[1][0].request_id


def test_a_blocked_request_is_200_with_the_decision_and_makes_no_call(client, gate, eleven):
    gate.blocked = True
    res = client.post(URL, headers=sam())

    assert res.status_code == 200
    assert res.json()["decision"]["outcome"] == "blocked" and res.json()["briefing"]["status"] == "none"
    assert eleven.convert_calls == []


def test_a_failure_is_503_in_the_error_shape_and_the_script_stays_on_get(client, eleven):
    eleven.queue.append(api_error(500))
    res = client.post(URL, headers=sam())

    assert res.status_code == 503
    assert res.json() == {"error": {"code": "briefing_unavailable",
                                    "message": "Briefing unavailable. The script is shown on the report."}}
    after = client.get(URL, headers=sam()).json()
    assert after["status"] == "failed" and after["script"] == SCRIPT


def test_without_a_key_post_is_503_and_get_says_unavailable_with_the_script(client, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY")  # no fake client: the real one finds no key

    before = client.get(URL, headers=sam()).json()
    assert (before["status"], before["script"]) == ("unavailable", SCRIPT)  # nothing to press
    res = client.post(URL, headers=sam())
    assert res.status_code == 503 and res.json()["error"]["code"] == "briefing_unavailable"
    after = client.get(URL, headers=sam()).json()
    assert (after["status"], after["script"]) == ("unavailable", SCRIPT)


def test_an_agent_key_cannot_generate(client, gate, eleven):
    res = client.post(URL, headers={"X-DxP-Key": "agent-key"})
    assert res.status_code == 403 and res.json()["error"]["code"] == "reviewer_only"
    assert gate.calls == [] and eleven.convert_calls == []


def test_an_unknown_key_is_401_on_both(client):
    assert client.post(URL, headers={"X-DxP-Key": "nope"}).status_code == 401
    assert client.get(URL, headers={"X-DxP-Key": "nope"}).status_code == 401


def test_an_unknown_report_is_404_on_both_with_the_error_shape(client):
    missing = "/api/v1/reports/rep_missing/briefing"
    for res in (client.post(missing, headers=sam()), client.get(missing, headers=sam())):
        assert res.status_code == 404 and res.json()["error"]["code"] == "report_not_found"


def test_get_returns_the_script_whatever_the_audio_status(client):
    res = client.get(URL, headers=sam())
    assert res.status_code == 200
    assert res.json() == {"report_id": REPORT_ID, "script": SCRIPT, "script_hash": "h" * 16,
                          "status": "none", "audio_id": None, "audio_url": None}


def test_get_audio_is_404_while_none_exists_then_serves_the_cached_mp3(client, eleven):
    assert client.get(URL + "?audio=1", headers=sam()).status_code == 404
    client.post(URL, headers=sam())

    by_query = client.get(URL + "?audio=1", headers=sam())
    by_accept = client.get(URL, headers={**sam(), "Accept": "audio/mpeg"})
    assert by_query.status_code == by_accept.status_code == 200
    assert by_query.headers["content-type"] == "audio/mpeg" and by_query.content == b"ID3-fake-audio"
    assert by_accept.content == b"ID3-fake-audio"
    assert client.get(URL, headers=sam()).json()["audio_url"] == URL + "?audio=1"


def test_a_pending_report_changes_nothing_when_a_briefing_is_made(client, fake_db, eleven):
    before = dict(fake_db.collection("reports").docs[REPORT_ID])
    client.post(URL, headers=sam())
    assert fake_db.collection("reports").docs[REPORT_ID] == before


# --- nothing generates a briefing automatically (V29) ----------------------------------------

BACKEND = Path(dxp.__file__).parent


def imports_of(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            found.add(base)
            found |= {f"{base}.{a.name}" for a in node.names}
    return found


def test_only_the_briefing_route_reaches_the_briefing_generator():
    """Filing a report, the pipeline, the Slack alert, the decision and the tasks make no ElevenLabs
    call, because none of them imports `briefing` or the ElevenLabs SDK."""
    allowed = {"briefing", "api/routes_briefing.py", "api/routes_avatar.py"}  # avatar: B08's own route
    offenders = []
    for path in BACKEND.rglob("*.py"):
        rel = path.relative_to(BACKEND).as_posix()
        if any(rel == a or rel.startswith(a + "/") for a in allowed):
            continue
        for name in imports_of(path):
            if name.split(".")[0] == "elevenlabs" or name.startswith(("dxp.briefing", ".briefing", "..briefing")):
                offenders.append((rel, name))
    assert offenders == []


def test_the_key_is_read_only_in_the_briefing_module():
    users = [p.relative_to(BACKEND).as_posix() for p in BACKEND.rglob("*.py") if "ELEVENLABS_API_KEY" in p.read_text()]
    assert users == ["briefing/audio.py"]
