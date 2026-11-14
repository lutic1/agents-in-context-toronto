"""Audit reconstruction against the Atlas Sandbox (Story 9.6, AD-22, V14, V27, V40, V43).

A fixture discover run with a search, a blocked claim on draft 1, a blocked out-of-scope mention,
a filed report (retrieval, a memory used, relationships with both quotes), its scope-collection
proposal, a delivered Slack alert and an unknown one, then Sam's approval and task authorisation
under "After the run" and the task's own run. Documents other PRs write are inserted as fixtures
(bypassing validation, since their writers are not on main); this PR's own writes go through runs.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from dxp import runs
from dxp.api.app import create_app
from dxp.identity import derive
from dxp.search import audit

from .conftest import PS_VERSION, SAM, SCOPE_ID, task_grant

pytestmark = pytest.mark.atlas

T0 = datetime(2026, 11, 14, 14, 0, tzinfo=UTC)
NCT = "clinicaltrials.gov:NCT04712877"
SV = derive("sv_", NCT, "2026-10-01", "hash")
M1 = derive("mem_", "M1")
SAM_STAMP = {"kind": "reviewer", "principal": "sam", "run_id": None, "agent": None, "initiated_by": "sam",
             "grant_id": "sam", "grant_version": 1, "policy_set_version": PS_VERSION}


def at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def checks(failed: str | None = None) -> list[dict]:
    names = ["grant_active", "team_scope", "destination_action", "evidence_checks", "run_authorised"]
    out = []
    for name in names:
        out.append({"check": name, "passed": name != failed, "detail": None})
        if name == failed:
            break
    return out


def auth_by(principal: str, initiated_by: str, grant_id: str, granted_by: str = "luis") -> dict:
    return {"principal": principal, "initiated_by": initiated_by, "acting_for": "Team Liquid Biopsy Dx",
            "granted_by": granted_by, "grant_id": grant_id, "grant_version": 1, "expires_at": None,
            "policy_set_version": PS_VERSION}


def decision(run, kind, seq, target, *, outcome="allowed", failed=None, destination="ledger", action_id=None,
             minutes=0, **extra) -> dict:
    doc = {
        "_id": derive("dec_", run["_id"] if run else "-", kind, "-", str(seq)), "run_id": run["_id"] if run else None,
        "agent": run["agent"] if run else None, "initiated_by": run["initiated_by"] if run else "sam",
        "stamp": run["stamp"] if run else SAM_STAMP, "cause": None, "request_id": None, "kind": kind,
        "inputs": {}, "evidence_ref": None, "destination": destination,
        "target": {"diagnostic_id": None, "scope_id": SCOPE_ID, **target}, "claims": [], "retrieval": None,
        "memories_used": [], "checks": checks(failed), "failed_check": failed, "grant_id": run["grant_id"] if run else "sam",
        "grant_version": 1, "run_grant_version": 1 if run else None, "policy_set_version": PS_VERSION,
        "outcome": "blocked" if failed else outcome, "action_id": action_id, "seq": seq, "decided_at": at(minutes),
        "authorised_by": auth_by(run["agent"], run["initiated_by"], run["grant_id"]) if run
        else auth_by("sam", "sam", "sam"),
    }
    doc.update(extra)
    return doc


def action(dec, status, result=None, *, kind=None, destination=None, **extra) -> dict:
    return {
        "_id": derive("act_", dec["_id"]), "decision_id": dec["_id"], "admission_id": None, "run_id": dec["run_id"],
        "kind": kind or dec["kind"], "destination": destination or dec["destination"], "target": dec["target"],
        "inputs": {}, "evidence_ref": dec["evidence_ref"], "stamp": dec["stamp"], "error": None, "status": status,
        "result": result, "resolution": None, "proposed_at": dec["decided_at"], "decided_at": dec["decided_at"],
        "claimed_at": dec["decided_at"], "observed_at": dec["decided_at"], "authorised_by": dec["authorised_by"],
        **extra,
    }


@pytest.fixture
async def story(clean, authority):
    db = clean
    await db["policy_sets"].insert_one({"_id": PS_VERSION, "members": ["claim_planned@v1", "evidence_quote@v1"], "created_at": T0})
    await db["policies"].insert_many([
        {"_id": "claim_planned@v1", "policy_id": "claim_planned", "version": 1, "status": "active",
         "applies_to": ["file_proposal"], "requires": {"claim_checks": ["claim_planned"]}, "text": "Planned is planned.",
         "author": "luis", "created_at": T0},
        {"_id": "evidence_quote@v1", "policy_id": "evidence_quote", "version": 1, "status": "active",
         "applies_to": ["file_proposal"], "requires": {"quote_found": True}, "text": "Quotes must be found.",
         "author": "luis", "created_at": T0},
        {"_id": "evidence_quote@v2", "policy_id": "evidence_quote", "version": 2, "status": "retired",
         "applies_to": ["file_proposal"], "requires": {"quote_found": True}, "text": "Later version.",
         "author": "luis", "created_at": at(90)},
    ])
    await db["source_items"].insert_one({"_id": NCT, "window": "discovered", "source_date": "2026-10-01",
                                         "raw_text": "never returned", "current_version_id": SV})

    run_model = await runs.start(SAM, "lbdx", "discover")
    await db["runs"].update_one({"_id": run_model.id}, {"$set": {"scan": {
        "cursor_from": "2026-09-01", "cursor_to": "2026-11-14", "query": {"term": "ctDNA"}, "source_refs": [NCT]}}})
    run = await db["runs"].find_one({"_id": run_model.id})
    run["stamp"] = (await runs.stamp(run["_id"])).model_dump()
    report_id = derive("rep_", run["_id"], NCT)
    proposal_id = derive("p_", report_id, "scope")
    task_id = derive("task_", report_id)
    task_grant_id = "task-" + task_id.removeprefix("task_")
    authority.grants[task_grant_id] = task_grant(task_id)

    search = decision(run, "search_source", 1, {"scope_id": SCOPE_ID}, destination="source:clinicaltrials.gov",
                      inputs={"cursor": "2026-09-01", "max": 20})
    search["action_id"] = derive("act_", search["_id"])
    blocked_mention = decision(run, "file_proposal", 2, {"report_id": report_id}, failed="team_scope",
                               inputs={"mention": "FoundationOne CDx", "scope_rule": "plasma assays only"},
                               evidence_ref={"source_ref": NCT, "version_id": SV, "quote": "FoundationOne CDx"})
    blocked_draft = decision(run, "file_proposal", 3, {"report_id": report_id, "draft": 1}, failed="evidence_checks",
                             claims=[{"claim_kind": "claim_performed_or_results", "text": "The assay showed ctDNA.",
                                      "passed": False, "detail": "has_results is false"}],
                             evidence_ref={"source_ref": NCT, "version_id": SV, "raw_text": "never returned"})
    retrieval = {"method": "text_search", "index": "source_text", "top_k": 5, "filter": {"scope_id": SCOPE_ID},
                 "items": [{"ref": "clinicaltrials.gov:NCT03000000", "version_id": SV, "score": 0.81}]}
    memory_use = {"memory_id": M1, "version": 1, "author": "sam", "source": {"report_id": "rep_setup"}, "score": 0.9,
                  "effect": {"target": "status sentence", "before": "showed results", "after": "is recruiting; no results posted"}}
    filed = decision(run, "file_proposal", 4, {"report_id": report_id}, retrieval=retrieval, memories_used=[memory_use],
                     claims=[{"claim_kind": "claim_planned", "text": "is recruiting", "passed": True, "detail": None}],
                     evidence_ref={"source_ref": NCT, "version_id": SV, "report_id": report_id})
    filed["action_id"] = derive("act_", filed["_id"])
    change = decision(run, "file_proposal", 5, {"report_id": report_id, "proposal_id": proposal_id},
                      evidence_ref={"source_ref": NCT, "version_id": SV, "proposal_id": proposal_id, "quote": "Plasma ctDNA"})
    change["action_id"] = derive("act_", change["_id"])
    alert = decision(run, "notify_slack", 6, {"report_id": report_id}, destination="slack:#all-mango-db-hackathon")
    alert["action_id"] = derive("act_", alert["_id"])
    alert2 = decision(run, "notify_slack", 7, {"report_id": derive("rep_", "other")}, destination="slack:#all-mango-db-hackathon")
    alert2["action_id"] = derive("act_", alert2["_id"])
    # inserted out of order on purpose: the audit orders by seq (D21)
    await db["decisions"].insert_many([alert2, filed, search, blocked_draft, change, blocked_mention, alert],
                                      bypass_document_validation=True)
    link = {"report_url": f"https://dxp.test/reports/{report_id}", "diagnostic_url": None}
    await db["actions"].insert_many([
        action(search, "delivered", {"http_status": 200, "cursor_from": "2026-09-01", "cursor_to": "2026-11-14",
                                     "source_refs": [NCT], "count": 1}),
        action(filed, "done", {"proposal_ids": [proposal_id], "value_ids": [], "report_id": report_id}),
        action(change, "done", {"proposal_ids": [proposal_id], "value_ids": [], "report_id": report_id}),
        action(alert, "delivered", {"http_status": 200, "response_body": "ok", "posted_at": at(7), "link_urls": link}),
        action(alert2, "unknown", {"http_status": None, "response_body": None, "posted_at": None, "link_urls": link}),
    ], bypass_document_validation=True)

    related = [{"id": derive("rel_", report_id, "NCT03000000"), "related_ref": "clinicaltrials.gov:NCT03000000",
                "related_kind": "source_item", "label": "extends", "similarity": 0.81, "retrieval_method": "text_search",
                "new_quote": {"source_ref": NCT, "version_id": SV, "text": "plasma ctDNA", "quote_found": True},
                "related_quote": {"source_ref": "clinicaltrials.gov:NCT03000000", "version_id": SV,
                                  "text": "ctDNA genotyping", "quote_found": True},
                "origin": "discovery", "status": "accepted"}]
    await db["reports"].insert_one({
        "_id": report_id, "run_id": run["_id"], "scope_id": SCOPE_ID, "team_id": "team_lbdx", "source_ref": NCT,
        "version_id": SV, "status": "accepted", "decided_by": "sam", "decided_at": at(30), "related": related,
        "stamp": run["stamp"], "created_at": at(4), "task_id": task_id,
    }, bypass_document_validation=True)
    await db["proposals"].insert_one({"_id": proposal_id, "op": "add", "status": "applied", "mode": "live",
                                      "decision_id": change["_id"], "stamp": run["stamp"], "decided_by": "sam",
                                      "decided_at": at(30), "report_id": report_id, "diagnostic_id": None,
                                      "target": {"scope_id": SCOPE_ID}}, bypass_document_validation=True)

    cause = {"report_id": report_id, "origin_run_id": run["_id"]}
    decide = decision(None, "decide_report", 101, {"report_id": report_id}, minutes=30, cause=cause, request_id="req_1")
    authorise = decision(None, "authorise_task", 102, {"report_id": report_id, "task_id": task_id}, minutes=30,
                         cause={**cause, "task_id": task_id}, request_id="req_1")
    authorise.pop("authorised_by")  # rebuilt from the grant at its recorded version
    resolve = decision(None, "resolve_notification", 103, {"action_id": alert2["action_id"]}, minutes=40,
                       cause={"action_id": alert2["action_id"], "origin_run_id": run["_id"]}, request_id="req_2")
    await db["decisions"].insert_many([authorise, resolve, decide], bypass_document_validation=True)
    await db["grants"].insert_one({"_id": "sam@v1", "grant_id": "sam", "version": 1, "principal": "sam", "kind": "person",
                                   "acting_for": "Team Liquid Biopsy Dx", "granted_by": "luis", "status": "active"},
                                  bypass_document_validation=True)
    await db["grants"].insert_one({"_id": "sam@v2", "grant_id": "sam", "version": 2, "principal": "sam", "kind": "person",
                                   "acting_for": "SOMEONE ELSE", "granted_by": "luis", "status": "revoked"},
                                  bypass_document_validation=True)
    await db["tasks"].insert_one({"_id": task_id, "report_id": report_id, "kind": "search_related",
                                  "question": "Which early-stage trials posted results?", "params": {"max": 5},
                                  "grant_id": task_grant_id, "status": "running", "authorised_by_decision_id": authorise["_id"],
                                  "created_at": at(30)}, bypass_document_validation=True)

    # The task's own run, finished, so it carries its own audit.
    await runs.finish(run["_id"])
    task_run = await runs.start(SAM, task_grant_id, f"task:{task_id}", run_id=derive("run_", task_id))
    task_doc = await db["runs"].find_one({"_id": task_run.id})
    task_doc["stamp"] = (await runs.stamp(task_run.id)).model_dump()
    task_search = decision(task_doc, "search_source", 201, {"task_id": task_id}, destination="source:clinicaltrials.gov")
    await db["decisions"].insert_one(task_search, bypass_document_validation=True)
    return {"task_grant_id": task_grant_id, "run": run, "report_id": report_id, "task_id": task_id, "task_run_id": task_run.id,
            "proposal_id": proposal_id, "alert2": alert2, "decide": decide, "authorise": authorise}


async def test_the_discovery_run_reconstructs_in_order_with_every_v14_section(story) -> None:
    result = await audit.run_audit(story["run"]["_id"])
    assert result.run.agent == "dxp-curator" and result.run.initiated_by == "sam" and result.run.grant_version == 1
    assert [p.id for p in result.policies] == ["claim_planned@v1", "evidence_quote@v1"]  # pinned, not v2
    assert [s.source_ref for s in result.sources] == [NCT]
    assert result.sources[0].window == "discovered" and result.sources[0].source_date == "2026-10-01"

    entries = result.entries
    assert [e.seq for e in entries] == [1, 2, 3, 4, 5, 6, 7]
    search, mention, draft1, filed, change, alert, unknown = entries
    assert search.kind == "search_source" and search.scan.cursor_from == "2026-09-01" and search.scan.cursor_to == "2026-11-14"
    assert search.scan.source_refs == [NCT] and search.status == "delivered"
    assert mention.outcome == "blocked" and mention.failed_check == "team_scope"
    assert mention.inputs["mention"] == "FoundationOne CDx" and mention.action_id is None
    assert draft1.failed_check == "evidence_checks" and draft1.claims[0].claim_kind == "claim_performed_or_results"
    assert draft1.evidence_ref.version_id == SV
    assert filed.retrieval.method == "text_search" and filed.retrieval.items[0].score == 0.81
    assert filed.memories_used[0].author == "sam" and filed.memories_used[0].effect.after == "is recruiting; no results posted"
    rel = filed.relationships[0]
    assert rel.label == "extends" and rel.new_quote.quote_found and rel.related_quote.text == "ctDNA genotyping"
    assert filed.report_review.status == "accepted" and filed.report_review.decided_by == "sam"
    assert change.proposal_review.status == "applied" and change.proposal_review.decided_by == "sam"
    assert change.evidence_ref.version_id == SV
    assert alert.status == "delivered" and alert.result.http_status == 200
    assert alert.result.link_urls.diagnostic_url is None  # no resolved Diagnostic (V43)
    assert unknown.status == "unknown"  # listed, never hidden
    assert all(e.authorised_by and e.authorised_by.grant_id == "lbdx" for e in entries)

    assert [e.kind for e in result.after_run] == ["decide_report", "authorise_task", "resolve_notification"]
    decided, authorised, resolved = result.after_run
    assert decided.report_review.status == "accepted" and decided.stamp.kind == "reviewer"
    assert authorised.task_id == story["task_id"]
    assert authorised.authorised_by.principal == "sam" and authorised.authorised_by.acting_for == "Team Liquid Biopsy Dx"
    assert resolved.cause.action_id == story["alert2"]["action_id"]
    assert [(r.run_id, r.task_id) for r in result.linked_runs] == [(story["task_run_id"], story["task_id"])]

    text = result.model_dump_json()
    assert "raw_text" not in text and "never returned" not in text


async def test_the_task_run_has_its_own_audit_under_its_task_grant(story) -> None:
    result = await audit.run_audit(story["task_run_id"])
    assert result.run.kind == "task" and result.run.grant_id == story["task_grant_id"] and result.run.initiated_by == "sam"
    assert [e.kind for e in result.entries] == ["search_source"]
    assert result.entries[0].grant_id == story["task_grant_id"]


async def test_decision_detail_and_action_routes(story, fake_run_function) -> None:
    app = create_app(fake_run_function)
    h = {"X-DxP-Key": "key-sam"}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://dxp.test") as client:
        got = await client.get(f"/api/v1/runs/{story['run']['_id']}/audit", headers=h)
        assert got.status_code == 200 and len(got.json()["entries"]) == 7
        detail = await client.get(f"/api/v1/decisions/{story['authorise']['_id']}", headers=h)
        assert detail.status_code == 200
        body = detail.json()
        assert body["authorised_by"]["grant_version"] == 1 and body["run_id"] is None and body["agent"] is None
        assert (await client.get("/api/v1/decisions/dec_missing", headers=h)).status_code == 404
        unknown = await client.get(f"/api/v1/actions?run_id={story['run']['_id']}&status=unknown", headers=h)
        assert [a["id"] for a in unknown.json()["items"]] == [story["alert2"]["action_id"]]
        one = await client.get(f"/api/v1/actions/{story['alert2']['action_id']}", headers=h)
        assert one.json()["authorised_by"]["principal"] == "dxp-curator"
        assert (await client.get("/api/v1/runs/run_missing/audit", headers=h)).status_code == 404


async def test_an_action_whose_decision_lost_its_action_id_is_still_joined(story) -> None:
    from dxp import store

    db_decisions = store.collection("decisions")
    alert_id = story["alert2"]["_id"]
    await db_decisions.update_one({"_id": alert_id}, {"$set": {"action_id": None}})
    result = await audit.run_audit(story["run"]["_id"])
    entry = next(e for e in result.entries if e.decision_id == alert_id)
    assert entry.status == "unknown" and entry.action_id == story["alert2"]["action_id"]
