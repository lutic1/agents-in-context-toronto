"""A26: revert an approval (Story 10.13, AD-31, V48) through the route, on A24's in-memory world
with the real gate (Decision IDs derived by the gate itself), the real ledger and real runs."""

from __future__ import annotations

import asyncio

from a24.conftest import PROPOSAL_ID, REPORT_ID, SAM_KEY, SCOPE_ID, SOURCE_REF, decide

from dxp import gate
from dxp.identity import derive

TASK_ID = derive("task_", REPORT_ID)
TASK_GRANT = "task-" + TASK_ID[len("task_"):]
REVERT_DEC = derive("dec_", "-", "revert_report", "-", REPORT_ID)
REVERSE_ID = derive("p_", PROPOSAL_ID, "revert")
NOTE = "Approved by mistake: the intervention field is ambiguous."


def revert(client, note: str | None = NOTE, report_id: str = REPORT_ID, key: str = SAM_KEY):
    body = {} if note is None else {"note": note}
    return client.post(f"/api/v1/reports/{report_id}/revert", json=body, headers={"X-DxP-Key": key})


def kinds(world, kind):
    return [d for d in world.db.all("decisions") if d["kind"] == kind]


def grant_versions(world, grant_id):
    return sorted((g for g in world.db.all("grants") if g["grant_id"] == grant_id), key=lambda g: g["version"])


def approve(client, world):
    res = decide(client)
    assert res.status_code == 200, res.text
    assert world.report()["status"] == "accepted"
    assert world.db.data["source_items"][SOURCE_REF]["collections"][SCOPE_ID]["proposal_id"] == PROPOSAL_ID


def snapshot(world):
    return {name: sorted(map(repr, world.db.all(name))) for name in
            ("reports", "proposals", "decisions", "tasks", "grants", "source_items", "events", "runs")}


# --- request handling ------------------------------------------------------------------------


def test_flag_off_is_404(world, client, features) -> None:
    features()
    approve(client, world)
    res = revert(client)
    assert res.status_code == 404
    assert world.report()["status"] == "accepted" and kinds(world, "revert_report") == []


def test_blank_note_is_400_before_the_gate(world, client, features) -> None:
    features("revert")
    approve(client, world)
    calls = len(world.gate_calls)
    res = revert(client, note="   ")
    assert res.status_code == 400 and res.json()["error"]["code"] == "note_required"
    assert len(world.gate_calls) == calls and kinds(world, "revert_report") == []


def test_missing_note_is_refused_before_the_gate(world, client, features) -> None:
    # The frozen ReportRevertRequest makes `note` required, so FastAPI refuses it (422).
    features("revert")
    approve(client, world)
    calls = len(world.gate_calls)
    assert revert(client, note=None).status_code in (400, 422)
    assert len(world.gate_calls) == calls


def test_pending_report_is_409_without_a_decision(world, client, features) -> None:
    features("revert")
    res = revert(client)
    assert res.status_code == 409, res.text
    assert "pending" in res.json()["error"]["message"]
    assert kinds(world, "revert_report") == [] and world.report()["status"] == "pending"


def test_unknown_report_is_404(world, client, features) -> None:
    features("revert")
    assert revert(client, report_id="rep_0000000000000000").status_code == 404


# --- the core path ---------------------------------------------------------------------------


def test_revert_after_approval(world, client, features) -> None:
    features("revert")
    approve(client, world)
    approval_dec = world.report()["approval"]["decision_id"]

    res = revert(client)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["removed"] == 1
    assert body["decision"]["id"] == REVERT_DEC and body["decision"]["outcome"] == "allowed"
    assert body["report"]["status"] == "reverted"
    assert body["task"]["status"] == "cancelled"

    # The gate's Decision: Reviewer stamp, run_id null, request_id, cause, report and scope.
    (dec,) = kinds(world, "revert_report")
    assert dec["_id"] == REVERT_DEC and dec["run_id"] is None and dec["request_id"].startswith("req_")
    assert dec["stamp"]["kind"] == "reviewer" and dec["stamp"]["principal"] == "sam"
    assert dec["destination"] == "ledger" and dec["grant_id"] == "sam"
    assert dec["cause"]["report_id"] == REPORT_ID and dec["target"]["scope_id"] == SCOPE_ID

    report = world.report()
    assert report["status"] == "reverted" and report["reverted_by"] == "sam" and report["reverted_at"]
    assert report["revert"]["step"] == "done" and report["revert"]["note"] == NOTE
    assert report["revert"]["decision_id"] == REVERT_DEC
    assert all(rel["status"] != "accepted" for rel in report["related"])

    # The ledger: a new reverse proposal; the original and its Decision stay.
    reverse = world.db.data["proposals"][REVERSE_ID]
    assert reverse["op"] == "remove" and reverse["reverts_proposal_id"] == PROPOSAL_ID
    assert reverse["status"] == "applied" and reverse["decision_id"] == REVERT_DEC
    assert world.db.data["proposals"][PROPOSAL_ID]["status"] == "applied"
    assert SCOPE_ID not in world.db.data["source_items"][SOURCE_REF]["collections"]
    assert world.db.data["decisions"][approval_dec]["outcome"] == "allowed"
    assert [e["proposal_id"] for e in world.events("value_reverted")] == [REVERSE_ID]
    assert len(world.events("report_reverted")) == 1

    # Audit reconstruction: both decisions are on record, nothing removed.
    on_report = {d["kind"] for d in world.db.all("decisions") if (d.get("target") or {}).get("report_id") == REPORT_ID}
    assert {"decide_report", "revert_report"} <= on_report

    # The task grant: v1 untouched, v2 expired.
    v1, v2 = grant_versions(world, TASK_GRANT)
    assert v1["status"] == "active" and v2["version"] == 2 and v2["status"] == "expired"
    # The revert's action is settled through the gate.
    assert world.db.data["actions"][dec["action_id"]]["status"] == "done"


def test_double_revert_changes_nothing(world, client, features) -> None:
    features("revert")
    approve(client, world)
    first = revert(client)
    assert first.status_code == 200
    before = snapshot(world)
    second = revert(client)
    assert second.status_code == 200, second.text
    assert second.json()["decision"]["id"] == REVERT_DEC and second.json()["removed"] == 1
    assert len(kinds(world, "revert_report")) == 1
    assert len([p for p in world.db.all("proposals") if p.get("op") == "remove"]) == 1
    assert snapshot(world) == before


def test_concurrent_reverts_apply_once(world, client, features) -> None:
    features("revert")
    approve(client, world)
    from dxp.api import models as m
    from dxp.reports.revert import revert as do_revert

    sam = m.Principal(id="sam", name="Sam", kind="person", grant_id="sam", actions=["revert_report"])

    async def both():
        return await asyncio.gather(do_revert(REPORT_ID, NOTE, sam), do_revert(REPORT_ID, NOTE, sam))

    results = asyncio.run(both())
    assert {r[1].id for r in results} == {REVERT_DEC}
    assert len(kinds(world, "revert_report")) == 1
    assert len([p for p in world.db.all("proposals") if p.get("op") == "remove"]) == 1
    assert len(world.events("value_reverted")) == 1 and len(world.events("report_reverted")) == 1


def test_revert_with_a_queued_task(world, client, features) -> None:
    features("revert")
    approve(client, world)
    # The task as dispatch would leave it with task_run on, before a worker picks it up.
    world.db.data["tasks"][TASK_ID]["status"] = "queued"

    res = revert(client)
    assert res.status_code == 200, res.text
    task = world.db.data["tasks"][TASK_ID]
    assert task["status"] == "cancelled" and task["cancelled_by_decision_id"] == REVERT_DEC
    assert [e["status"] for e in world.events("task_status_changed") if e["task_id"] == TASK_ID][-1] == "cancelled"
    versions = grant_versions(world, TASK_GRANT)
    assert [(g["version"], g["status"]) for g in versions] == [(1, "active"), (2, "expired")]

    # A later step of the task, under its grant, is blocked by check 1 (grant_active).
    run_id = derive("run_", TASK_ID)
    ctx = {
        "kind": "run", "principal": "dxp-curator", "grant_id": TASK_GRANT, "run_id": run_id,
        "agent": "dxp-curator", "initiated_by": "sam", "run_grant_version": 1, "mode": "live",
        "stamp": {"kind": "run", "run_id": run_id, "agent": "dxp-curator", "initiated_by": "sam",
                  "principal": "dxp-curator", "grant_id": TASK_GRANT, "grant_version": 1},
    }
    action = {"kind": "search_source", "destination": "source:clinicaltrials.gov",
              "target": {"task_id": TASK_ID, "scope_id": SCOPE_ID}, "query": {"scope_id": SCOPE_ID}}
    decision = asyncio.run(gate.evaluate(ctx, action))
    assert decision.outcome == "blocked" and decision.failed_check == "grant_active"


def test_done_task_is_left_as_it_is(world, client, features) -> None:
    features("revert")
    approve(client, world)
    world.db.data["tasks"][TASK_ID]["status"] = "done"
    res = revert(client)
    assert res.status_code == 200 and res.json()["task"]["status"] == "done"
    assert len(grant_versions(world, TASK_GRANT)) == 1


def test_blocked_revert_changes_nothing_and_is_final(world, client, features) -> None:
    features("revert")
    approve(client, world)
    world.drop_from_sam("revert_report")
    before = snapshot(world)

    res = revert(client)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["decision"]["id"] == REVERT_DEC and body["decision"]["outcome"] == "blocked"
    assert body["report"]["status"] == "accepted" and body["removed"] == 0
    assert body["task"]["status"] == "authorised"
    (dec,) = kinds(world, "revert_report")
    assert dec["outcome"] == "blocked"

    after = snapshot(world)
    for name in ("reports", "proposals", "tasks", "grants", "source_items", "runs"):
        assert after[name] == before[name], name
    new_decisions = set(after["decisions"]) - set(before["decisions"])
    assert len(new_decisions) == 1

    # Final: restoring the grant does not let a second revert through (same Decision ID).
    again = revert(client)
    assert again.json()["decision"]["outcome"] == "blocked" and len(kinds(world, "revert_report")) == 1
    assert world.report()["status"] == "accepted"


def test_recover_reverting_finishes_an_interrupted_revert(world, client, features) -> None:
    features("revert")
    approve(client, world)
    # Interrupt: the claim was written, nothing else.
    import importlib

    rv = importlib.import_module("dxp.reports.revert")

    async def claim_only():
        real = rv.finish_reverting

        async def crash(report_id):
            raise RuntimeError("crash after the claim")

        rv.finish_reverting = crash
        try:
            from dxp.api import models as m
            sam = m.Principal(id="sam", name="Sam", kind="person", grant_id="sam", actions=["revert_report"])
            try:
                await rv.revert(REPORT_ID, NOTE, sam)
            except RuntimeError:
                pass
        finally:
            rv.finish_reverting = real

    asyncio.run(claim_only())
    assert world.report()["status"] == "reverting"
    asyncio.run(rv.recover_reverting())
    assert world.report()["status"] == "reverted" and world.report()["revert"]["step"] == "done"
    assert world.db.data["proposals"][REVERSE_ID]["status"] == "applied"
