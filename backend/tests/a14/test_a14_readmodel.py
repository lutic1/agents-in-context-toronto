"""A14, Story 1.1 read model and the accepted knowledge route `GET /diagnostics/<dx_id>`."""

from __future__ import annotations

from tests.a14.conftest import DX_ID, HEADERS, SEED_KEY, diagnostic_doc, proposal_doc


def _seed(fake_db, doc=None):
    fake_db["diagnostics"].docs[DX_ID] = doc or diagnostic_doc()


def _values(body, field):
    return {v["value_id"]: v for v in body["fields"][field]["values"]}


def test_passed_values_are_returned_with_provenance(api_client, fake_db, principals):
    _seed(fake_db)
    response = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == DX_ID and body["name"] == "FoundationOne Liquid CDx"
    assert body["lifecycle_stage"] == "regulatory_approval" and body["early_research"] is False
    modality = _values(body, "modality")["v_modality"]
    assert modality["review"] == "unreviewed"
    assert modality["proposal_id"] == "p_modality"
    assert modality["stamp"]["kind"] == "seed" and modality["stamp"]["principal"] == "seed"
    assert "action_id" in modality
    assert modality["evidence"]["source"] == "FDA list of cleared or approved companion diagnostic devices"
    assert modality["evidence"]["data_as_of"] == "2026-11-14"
    # The Record links each value to the write that made it.
    assert "p_modality" in body["applied_proposal_ids"]
    trial = _values(body, "trials")["v_trial"]
    assert trial["stamp"]["run_id"] == "run_a14"
    assert trial["evidence"]["source"] == "ClinicalTrials.gov"
    assert trial["evidence"]["source_url"] == "https://clinicaltrials.gov/study/NCT05715229"


def test_failed_value_is_never_returned(api_client, fake_db, principals):
    _seed(fake_db)
    body = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    assert "v_failed" not in _values(body, "trials")
    assert "NCT00000001" not in str(body)


def test_pending_or_unapplied_value_is_never_returned_as_accepted(api_client, fake_db, principals):
    _seed(fake_db)
    fake_db["proposals"].docs["p_pending"] = proposal_doc("p_pending")
    body = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    trials = _values(body, "trials")
    assert set(trials) == {"v_trial"}
    for value in ("NCT00000002", "NCT00000003", "NCT04712877"):
        assert value not in str(body)


def test_pending_report_is_listed_as_pending_beside_accepted_knowledge(api_client, fake_db, principals):
    _seed(fake_db)
    fake_db["proposals"].docs["p_pending"] = proposal_doc("p_pending")
    fake_db["proposals"].docs["p_done"] = proposal_doc("p_done", status="applied", value="NCT05715229")
    response = api_client.get(
        "/api/v1/proposals", params={"diagnostic_id": DX_ID, "status": "pending"}, headers=HEADERS
    )
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [(p["id"], p["status"], p["report_id"]) for p in items] == [("p_pending", "pending", "rep_a14")]


def test_empty_field_has_no_data(api_client, fake_db, principals):
    _seed(fake_db)
    body = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    assert body["fields"]["biomarkers"] == {"values": [], "no_data": True}
    assert body["fields"]["modality"]["no_data"] is False


def test_unknown_diagnostic_is_404_in_the_error_shape(api_client, fake_db, principals):
    response = api_client.get("/api/v1/diagnostics/dx_unknown", headers=HEADERS)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_raw_text_is_never_returned(api_client, fake_db, principals):
    _seed(fake_db)
    response = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS)
    assert "raw_text" not in response.text and "NEVER RETURNED" not in response.text


def test_stage_not_determined_and_synthetic_pass_through(api_client, fake_db, principals):
    doc = diagnostic_doc()
    doc.pop("lifecycle_stage")
    doc["fields"].pop("lifecycle_stage")
    doc["synthetic"] = True
    _seed(fake_db, doc)
    body = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    assert body["lifecycle_stage"] == "not_determined" and body["early_research"] is False
    assert body["synthetic"] is True


def test_early_research_label_comes_from_the_registry(api_client, fake_db, principals):
    doc = diagnostic_doc()
    doc["lifecycle_stage"] = "assay_development"
    _seed(fake_db, doc)
    assert api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()["early_research"] is True


def test_manual_value_is_returned_without_a_check(api_client, fake_db, principals):
    doc = diagnostic_doc()
    doc["fields"]["provider"] = [
        {
            "value_id": "v_manual",
            "value": "foundation medicine",
            "label": "Foundation Medicine",
            "state": "current",
            "review": "manual",
            "evidence": {"manual": True, "submitter": "sam", "note": "typed by hand"},
            "check": None,
            "proposal_id": None,
            "stamp": {"kind": "reviewer", "principal": "sam"},
        }
    ]
    _seed(fake_db, doc)
    body = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    manual = body["fields"]["provider"]["values"][0]
    assert manual["review"] == "manual" and manual["evidence"]["manual"] is True


def test_evidence_follows_the_pinned_version_never_the_current_pointer(api_client, fake_db, principals):
    """V40: moving source_items.current_version_id never changes accepted evidence."""
    _seed(fake_db)
    fake_db["source_versions"].docs["sv_trial_v1"] = {
        "_id": "sv_trial_v1",
        "source_ref": "clinicaltrials.gov:NCT05715229",
        "last_update_post_date": "2026-10-01",
        "raw_text": "VERSION 1 RAW TEXT",
    }
    fake_db["source_items"].docs["clinicaltrials.gov:NCT05715229"] = {
        "_id": "clinicaltrials.gov:NCT05715229",
        "current_version_id": "sv_trial_v1",
    }
    before = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    trial = _values(before, "trials")["v_trial"]
    assert trial["evidence"]["version_id"] == "sv_trial_v1"
    assert trial["evidence"]["data_as_of"] == "2026-10-01"  # read from the pinned version

    fake_db["source_versions"].docs["sv_trial_v2"] = {
        "_id": "sv_trial_v2",
        "source_ref": "clinicaltrials.gov:NCT05715229",
        "last_update_post_date": "2026-11-13",
        "raw_text": "VERSION 2 RAW TEXT",
    }
    fake_db["source_items"].docs["clinicaltrials.gov:NCT05715229"]["current_version_id"] = "sv_trial_v2"
    after = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers=HEADERS).json()
    assert after == before
    assert "RAW TEXT" not in str(after)


def test_reads_need_a_known_key_and_refuse_the_seed_key(api_client, fake_db, principals):
    _seed(fake_db)
    assert api_client.get(f"/api/v1/diagnostics/{DX_ID}").status_code == 401
    unknown = api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers={"X-DxP-Key": "nope"})
    assert unknown.status_code == 401 and unknown.json()["error"]["code"] == "unknown_key"
    assert api_client.get(f"/api/v1/diagnostics/{DX_ID}", headers={"X-DxP-Key": SEED_KEY}).status_code == 403


def test_diagnostics_list_stays_deferred(api_client):
    response = api_client.get("/api/v1/diagnostics", headers=HEADERS)
    assert response.status_code == 501 and response.json()["error"]["code"] == "not_implemented"
