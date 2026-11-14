"""A24: the report decision route, promotion and task authorisation (Story 10.8), on the
in-memory store with the gate, ledger, runs and memory doubles of conftest.py."""

from __future__ import annotations

import asyncio
import importlib
from datetime import timedelta

import pytest

from dxp.identity import derive

from .conftest import (
    AGENT_KEY,
    GAP,
    PROPOSAL_ID,
    REPORT_ID,
    SCOPE_ID,
    SOURCE_REF,
    VERSION_ID,
    decide,
)

TASK_ID = derive("task_", REPORT_ID)
TASK_GRANT = "task-" + TASK_ID[len("task_"):]
NOT_RUN = "Approved: 1 update accepted. Follow-up task authorised; not run."
PENDING_REVIEW = "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review."


def decisions_of(world, kind):
    return [d for d in world.db.all("decisions") if d["kind"] == kind]


# --- request validation, before the gate ---------------------------------------------------


def test_reject_without_a_note_is_400_before_the_gate(world, client) -> None:
    res = decide(client, "reject")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "note_required"
    assert world.gate_calls == []
    assert world.report()["status"] == "pending"


def test_correction_without_a_note_is_400(world, client) -> None:
    res = decide(client, "approve", correction="say terminated")
    assert res.status_code == 400 and world.gate_calls == []


def test_missing_or_unknown_key_is_401(world, client) -> None:
    assert client.post(f"/api/v1/reports/{REPORT_ID}/decision", json={"action": "approve"}).status_code == 401
    assert decide(client, key="nope").status_code == 401


def test_unknown_report_is_404(world, client) -> None:
    res = client.post("/api/v1/reports/rep_0000000000000000/decision", json={"action": "approve"},
                      headers={"X-DxP-Key": "test-dxp-api-key"})
    assert res.status_code == 404 and res.json()["error"]["code"] == "not_found"


def test_edit_is_not_offered(world, client) -> None:
    assert decide(client, "edit").status_code == 422


# --- approve, task_run off (the base case) --------------------------------------------------


def test_approve_promotes_once_and_authorises_the_task_not_run(world, client) -> None:
    res = decide(client)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["message"] == NOT_RUN

    # decide_report: Reviewer stamp, run_id null, request_id, cause { report_id, origin_run_id }
    (dec,) = decisions_of(world, "decide_report")
    assert dec["outcome"] == "allowed" and dec["run_id"] is None and dec["request_id"].startswith("req_")
    assert dec["stamp"]["kind"] == "reviewer" and dec["stamp"]["principal"] == "sam"
    assert dec["cause"]["report_id"] == REPORT_ID and dec["cause"]["origin_run_id"] == world.report()["run_id"]
    # V43: the target is the report and its scope; no Diagnostic assumed
    assert dec["target"]["diagnostic_id"] is None and dec["target"]["scope_id"] == SCOPE_ID
    assert dec["evidence_ref"]["version_id"] == VERSION_ID

    # promotion: the one update applied once, into the scope's evidence collection
    assert world.applied == [PROPOSAL_ID]
    entry = world.db.data["source_items"][SOURCE_REF]["collections"][SCOPE_ID]
    assert entry["proposal_id"] == PROPOSAL_ID and entry["version_id"] == VERSION_ID
    assert world.db.all("diagnostics") == []
    report = world.report()
    assert report["status"] == "accepted" and report["decided_by"] == "sam"
    assert all(r["status"] == "accepted" for r in report["related"])
    assert report["approval"]["task_step"] == "done" and report["approval"]["task_id"] == TASK_ID

    # the task: authorised, never queued, the gap as its question
    (task,) = world.db.all("tasks")
    assert task["_id"] == TASK_ID and task["status"] == "authorised" and task["queued_at"] is None
    assert task["question"] == GAP and task["kind"] == "search_related" and task["result"] is None
    assert task["params"] == {"condition": "non-small cell lung cancer", "stage": "early",
                              "testing": ["ctDNA or plasma", "tissue profiling"], "has_results": True, "max": 5}
    assert task["grant_id"] == TASK_GRANT

    # authorise_task: derived ID from the approval decision, Reviewer authorised it
    (auth,) = decisions_of(world, "authorise_task")
    assert auth["_id"] == derive("dec_", dec["_id"], "authorise_task") == task["authorised_by_decision_id"]
    assert auth["outcome"] == "allowed" and auth["initiated_by"] == "sam"
    assert auth["cause"]["approval_decision_id"] == dec["_id"]
    # the audit's "After the run" reads the gap the task answers from the Decision's inputs
    assert auth["inputs"]["question"] == GAP == task["question"]

    # the task grant: narrow, one hour
    grant = world.db.data["grants"][f"{TASK_GRANT}@v1"]
    assert grant["actions"] == ["search_source", "file_related_evidence"]
    assert grant["destinations"] == ["source:clinicaltrials.gov", "ledger"]
    assert grant["limits"] == {"max_results": 5} and grant["key_hash"] is None
    assert grant["scope"]["scope_id"] == SCOPE_ID and grant["startable_by"] == ["sam"]
    assert grant["kind"] == "agent"
    assert grant["principal"] == "dxp-curator" and grant["granted_by"] == "sam" and grant["task_id"] == TASK_ID
    assert grant["expires_at"] - grant["created_at"] == timedelta(hours=1)

    # nothing started (V38 flag off)
    assert world.run_starts == [] and client.spawner.spawned == []

    # response
    assert body["report"]["status"] == "accepted"
    assert body["task"]["status"] == "authorised" and body["task"]["id"] == TASK_ID
    assert [d["kind"] for d in body["decisions"]] == ["decide_report", "authorise_task"]
    assert body["memory"] is None


def test_retried_approval_returns_the_same_decision_and_task(world, client) -> None:
    first = decide(client).json()
    second = decide(client).json()
    assert [d["id"] for d in second["decisions"]] == [d["id"] for d in first["decisions"]]
    assert second["task"]["id"] == first["task"]["id"] and second["message"] == NOT_RUN
    assert len(world.db.all("tasks")) == 1 and len(world.db.all("grants")) == 3
    assert len(decisions_of(world, "decide_report")) == 1 and world.applied == [PROPOSAL_ID]


async def test_concurrent_double_approval_applies_once(world) -> None:
    from dxp.api.models import Principal
    rd = importlib.import_module("dxp.reports.decide")

    sam = Principal(id="sam", name="Sam", kind="person")
    await asyncio.gather(rd.decide(REPORT_ID, "approve", None, None, sam),
                         rd.decide(REPORT_ID, "approve", None, None, sam))
    assert world.applied == [PROPOSAL_ID]
    assert world.report()["status"] == "accepted"
    assert len([e for e in world.db.all("events") if e["type"] == "report_decided"]) == 1


def test_blocked_decide_report_changes_nothing(world, client) -> None:
    world.add_report(scope_id="scope_other")  # the real check 2: outside sam@v1's scope
    body = decide(client).json()
    assert world.report()["status"] == "pending" and world.applied == [] and world.db.all("tasks") == []
    (dec,) = body["decisions"]
    assert dec["outcome"] == "blocked" and body["message"].startswith("Decision blocked: team_scope")


def test_the_agent_key_cannot_decide(world, client) -> None:
    body = decide(client, key=AGENT_KEY).json()
    assert body["decisions"][0]["outcome"] == "blocked" and world.report()["status"] == "pending"


def test_blocked_authorisation_keeps_the_evidence_accepted(world, client) -> None:
    world.drop_from_sam("authorise_task")  # the real check 3: the action is not on the grant
    body = decide(client).json()
    report = world.report()
    assert report["status"] == "accepted" and report["approval"]["task_step"] == "blocked"
    assert world.db.all("tasks") == []
    assert not [g for g in world.db.all("grants") if g["grant_id"].startswith("task-")]
    assert body["message"].startswith("Approved: 1 update accepted. Follow-up task not authorised: destination_action")
    assert report["approval"]["reason"].startswith("Follow-up task not authorised")
    # terminal: a retry never reopens it
    decide(client)
    assert len(decisions_of(world, "authorise_task")) == 1 and world.db.all("tasks") == []


# --- one transaction (V38) ------------------------------------------------------------------


async def test_authorisation_is_one_transaction(world, monkeypatch: pytest.MonkeyPatch) -> None:
    from dxp.api.models import Principal
    from dxp.gate import grants
    rd = importlib.import_module("dxp.reports.decide")
    ta = importlib.import_module("dxp.tasks.authorise")

    sam = Principal(id="sam", name="Sam", kind="person")
    await rd.decide(REPORT_ID, "approve", None, None, sam)

    async def broken(task, decision, session=None):
        raise RuntimeError("grant write failed")

    monkeypatch.setattr(grants, "issue_task_grant", broken)
    with pytest.raises(RuntimeError):
        await ta.authorise(REPORT_ID, sam)
    # none of it: no Decision, no task, no grant, the step still pending
    assert decisions_of(world, "authorise_task") == [] and world.db.all("tasks") == []
    assert world.report()["approval"]["task_step"] == "pending"


# --- reject and correction ------------------------------------------------------------------


def test_reject_creates_the_memory_and_promotes_nothing(world, client) -> None:
    note = "Terminated trial with no posted results: describe its status; do not state outcomes"
    body = decide(client, "reject", note=note).json()
    report = world.report()
    assert report["status"] == "rejected" and report["note"] == note
    assert world.db.data["proposals"][PROPOSAL_ID]["status"] == "rejected"
    assert world.rejected_by_ledger == [PROPOSAL_ID]  # through the ledger, not reports
    assert world.applied == [] and world.db.all("tasks") == []
    assert world.db.data["source_items"][SOURCE_REF]["collections"] == {}
    (mem,) = world.memories
    assert mem["text"] == note and mem["author"] == "sam"
    # no claim kind in the request: never inferred from the trial (it has no posted results here)
    assert mem["tags"]["claim_kind"] == "reviewer_correction"
    assert mem["tags"]["assay"] == "FoundationOne CDx"
    assert report["memory_id"] == mem["memory_id"]
    assert body["memory"]["id"] == mem["memory_id"]
    assert body["message"] == "Rejected: no update accepted; no task authorised. Memory saved."


def test_memory_failure_is_repaired_by_a_retry(world, client) -> None:
    world.memory_fails = 1
    body = decide(client, "reject", note="a note").json()
    assert body["memory"] is None and "Memory saved" not in body["message"]
    assert world.report()["status"] == "rejected"
    body = decide(client, "reject", note="a note").json()
    assert body["memory"] is not None and body["message"].endswith("Memory saved.")
    assert len(world.memories) == 1 and len(decisions_of(world, "decide_report")) == 1


def test_approve_with_correction_promotes_authorises_and_remembers(world, client) -> None:
    body = decide(client, "approve", note="wording", correction="Describe the status only").json()
    assert world.report()["status"] == "accepted" and len(world.db.all("tasks")) == 1
    assert world.memories[0]["text"] == "Describe the status only"
    assert body["message"] == f"{NOT_RUN} Memory saved."


# --- GET /tasks -----------------------------------------------------------------------------


def test_task_routes(world, client) -> None:
    decide(client)
    headers = {"X-DxP-Key": "test-dxp-api-key"}
    items = client.get(f"/api/v1/tasks?report_id={REPORT_ID}", headers=headers).json()["items"]
    assert [t["id"] for t in items] == [TASK_ID]
    assert client.get(f"/api/v1/tasks/{TASK_ID}", headers=headers).json()["status"] == "authorised"
    assert client.get("/api/v1/tasks/task_0000000000000000", headers=headers).status_code == 404
    assert client.get("/api/v1/tasks?report_id=rep_x", headers=headers).json()["items"] == []


def test_memory_claim_kind_is_the_reviewers_choice() -> None:
    routes = importlib.import_module("dxp.api.routes_report_decision")
    report = {"discovery": {"has_results": False, "mentions": []}}
    assert routes._memory_tags(report, "claim_performed_or_results") == {
        "assay": None, "claim_kind": "claim_performed_or_results"}
    assert routes._memory_tags(report, None)["claim_kind"] == "reviewer_correction"


def test_reports_decide_writes_no_proposal() -> None:
    from pathlib import Path

    source = (Path(__file__).resolve().parents[2] / "dxp/reports/decide.py").read_text()
    assert 'db()["proposals"].update' not in source and "reject_report_proposals" in source


def test_claim_kind_in_the_request_tags_the_memory(world, client) -> None:
    decide(client, "reject", note="Terminated trial", claim_kind="claim_performed_or_results")
    assert world.memories[0]["tags"]["claim_kind"] == "claim_performed_or_results"


def test_blocked_reason_is_returned_with_the_report(world, client) -> None:
    world.drop_from_sam("authorise_task")  # the real check 3: the action is not on the grant
    body = decide(client).json()
    stored = world.report()["approval"]["reason"]
    assert stored.startswith("Follow-up task not authorised: destination_action")
    assert body["report"]["approval"]["reason"] == stored


def test_the_approval_action_is_settled(world, client) -> None:
    decide(client)
    actions = {a["kind"]: a["status"] for a in world.db.all("actions")}
    assert actions == {"decide_report": "done", "authorise_task": "done"}


def test_a_report_with_no_gap_records_a_blocked_task_step(world, client) -> None:
    world.add_report(gap="")  # the model requires a string; the validator allows an empty one
    res = decide(client)
    assert res.status_code == 200, res.text
    report = world.report()
    assert report["status"] == "accepted" and report["approval"]["task_step"] == "blocked"
    assert report["approval"]["reason"] == "Follow-up task not authorised: the report names no gap for the task to answer"
    assert world.db.all("tasks") == [] and res.json()["message"].startswith(
        "Approved: 1 update accepted. Follow-up task not authorised: the report names no gap")
    assert decide(client).status_code == 200  # terminal; later decisions do not fail
