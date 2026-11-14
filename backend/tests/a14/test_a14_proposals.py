"""A14, Story 2.2: `GET /proposals` and `GET /proposals/<p_id>` (D42, D47, V43)."""

from __future__ import annotations

from datetime import UTC, datetime

from tests.a14.conftest import DX_ID, HEADERS, SCOPE_ID, diagnostic_doc, proposal_doc


def _ids(response):
    assert response.status_code == 200, response.text
    return [p["id"] for p in response.json()["items"]]


def test_filters(api_client, fake_db, principals):
    proposals = fake_db["proposals"].docs
    proposals["p_a"] = proposal_doc("p_a")
    proposals["p_b"] = proposal_doc("p_b", status="applied", report_id="rep_other")
    proposals["p_c"] = proposal_doc("p_c", field="biomarkers", value="EGFR")
    get = lambda **params: _ids(api_client.get("/api/v1/proposals", params=params, headers=HEADERS))
    assert set(get()) == {"p_a", "p_b", "p_c"}
    assert set(get(status="pending")) == {"p_a", "p_c"}
    assert get(report_id="rep_other") == ["p_b"]
    assert get(field="biomarkers") == ["p_c"]
    assert set(get(diagnostic_id=DX_ID, run_id="run_a14")) == {"p_a", "p_b", "p_c"}
    assert get(run_id="run_none") == []


def test_low_confidence_first_then_newest(api_client, fake_db, principals):
    proposals = fake_db["proposals"].docs
    proposals["p_old"] = proposal_doc("p_old", created_at=datetime(2026, 11, 14, 12, tzinfo=UTC))
    proposals["p_new"] = proposal_doc("p_new", created_at=datetime(2026, 11, 14, 14, tzinfo=UTC))
    proposals["p_low"] = proposal_doc("p_low", confidence=0.3, created_at=datetime(2026, 11, 14, 11, tzinfo=UTC))
    assert _ids(api_client.get("/api/v1/proposals", headers=HEADERS)) == ["p_low", "p_new", "p_old"]


def test_shape_with_read_time_notification(api_client, fake_db, principals):
    fake_db["diagnostics"].docs[DX_ID] = diagnostic_doc()
    fake_db["proposals"].docs["p_a"] = proposal_doc("p_a")
    posted = datetime(2026, 11, 14, 13, 5, tzinfo=UTC)
    fake_db["actions"].docs["act_slack"] = {
        "_id": "act_slack",
        "kind": "notify_slack",
        "target": {"report_id": "rep_a14"},
        "status": "delivered",
        "result": {"http_status": 200, "response_body": "ok", "posted_at": posted},
    }
    body = api_client.get("/api/v1/proposals/p_a", headers=HEADERS).json()
    assert body["diagnostic_name"] == "FoundationOne Liquid CDx"
    assert body["current_value"] == ["NCT05715229"]  # the list field's current values, read now
    assert body["evidence"]["quote"] and body["evidence"]["version_id"] == "sv_anchor_v1"
    assert body["check"]["confidence"] == 0.9
    for key in ("mode", "run_id", "report_id", "action_id", "decision_id", "stamp"):
        assert body[key] is not None, key
    assert body["notification"] == {"action_id": "act_slack", "status": "delivered", "posted_at": "2026-11-14T13:05:00Z"}
    # Read time only: nothing is written to the proposal document (D47).
    assert "notification" not in fake_db["proposals"].docs["p_a"]


def test_notification_is_null_until_the_action_exists(api_client, fake_db, principals):
    fake_db["proposals"].docs["p_a"] = proposal_doc("p_a")
    assert api_client.get("/api/v1/proposals/p_a", headers=HEADERS).json()["notification"] is None


def test_one_proposal_whatever_its_status_and_404(api_client, fake_db, principals):
    fake_db["proposals"].docs["p_rej"] = proposal_doc("p_rej", status="rejected")
    assert api_client.get("/api/v1/proposals/p_rej", headers=HEADERS).json()["status"] == "rejected"
    missing = api_client.get("/api/v1/proposals/p_missing", headers=HEADERS)
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"


def test_scope_collection_proposal_has_no_diagnostic(api_client, fake_db, principals):
    """V43: diagnostic_id null, target.scope_id, current value from the scope collection."""
    ref = "clinicaltrials.gov:NCT04712877"
    fake_db["proposals"].docs["p_scope"] = proposal_doc(
        "p_scope", diagnostic_id=None, field="evidence_collection", value=ref, scope_id=SCOPE_ID
    )
    fake_db["source_items"].docs[ref] = {"_id": ref, "collections": {}}
    body = api_client.get("/api/v1/proposals/p_scope", headers=HEADERS).json()
    assert body["diagnostic_id"] is None and body["diagnostic_name"] is None
    assert body["target"] == {"scope_id": SCOPE_ID}
    assert body["current_value"] is None
    fake_db["source_items"].docs[ref]["collections"][SCOPE_ID] = {"status": "accepted", "proposal_id": "p_x"}
    assert api_client.get("/api/v1/proposals/p_scope", headers=HEADERS).json()["current_value"] == "accepted"


def test_quotes_only_never_raw_text(api_client, fake_db, principals):
    fake_db["proposals"].docs["p_a"] = proposal_doc("p_a")
    response = api_client.get("/api/v1/proposals", headers=HEADERS)
    assert "raw_text" not in response.text and "NEVER RETURNED" not in response.text


def test_unknown_status_is_400(api_client, fake_db, principals):
    response = api_client.get("/api/v1/proposals", params={"status": "maybe"}, headers=HEADERS)
    assert response.status_code == 400 and response.json()["error"]["code"] == "bad_request"


def test_reads_need_a_key(api_client, fake_db, principals):
    assert api_client.get("/api/v1/proposals").status_code == 401
    assert api_client.get("/api/v1/proposals/p_a").status_code == 401


def test_per_proposal_decision_stays_superseded(api_client):
    response = api_client.post("/api/v1/proposals/p_a/decision", json={"action": "accept"}, headers=HEADERS)
    assert response.status_code == 501 and response.json()["error"]["code"] == "not_implemented"


def test_proposal_data_date_comes_from_the_pinned_version(api_client, fake_db, principals):
    doc = proposal_doc("p_a")
    doc["evidence"].pop("source_date")
    fake_db["proposals"].docs["p_a"] = doc
    fake_db["source_versions"].docs["sv_anchor_v1"] = {"_id": "sv_anchor_v1", "last_update_post_date": "2026-11-12"}
    fake_db["source_versions"].docs["sv_anchor_v2"] = {"_id": "sv_anchor_v2", "last_update_post_date": "2026-11-13"}
    evidence = api_client.get("/api/v1/proposals/p_a", headers=HEADERS).json()["evidence"]
    assert evidence["data_as_of"] == "2026-11-12" and evidence["version_id"] == "sv_anchor_v1"
