"""gate.evaluate against a database (Story 9.3, D5, D19, D20, D21).

Each test runs on the in-memory fake and, when ``MONGODB_URI`` is set, on a
throwaway Atlas Sandbox database.
"""

from __future__ import annotations

from conftest import ANCHOR, SCOPE_ID, TEAM_ID, derive, grant_doc

from dxp import gate

GOOD = {"quote_found": True, "supported": True, "confidence": 0.9}


def scope_action(**kw):
    a = {"kind": "file_proposal", "destination": "ledger",
         "target": {"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_scope1"},
         "evidence_ref": {"source_ref": ANCHOR, "version_id": "sv_anchor0000000001"}, "checks": [GOOD]}
    a.update(kw)
    return a


def test_allowed_writes_decision_action_and_event(world):
    async def body(w):
        adm = await w.admit()
        d = await gate.evaluate(w.run_ctx(adm), scope_action())
        assert d.allowed and d.action_id
        stored = await w.db["decisions"].find_one({"_id": d.decision_id})
        assert stored["action_id"] == d.action_id and stored["seq"] is not None
        assert stored["grant_id"] == "lbdx" and stored["grant_version"] == 1
        assert stored["policy_set_version"] == w.policy_set_version
        assert stored["agent"] == "dxp-curator" and stored["initiated_by"] == "sam"
        assert stored["authorised_by"]["grant_id"] == "lbdx" and stored["authorised_by"]["granted_by"] == "luis"
        assert stored["evidence_ref"]["version_id"] == "sv_anchor0000000001"
        assert [c["check"] for c in stored["checks"]] == list(gate.CHECK_ORDER)
        act = await w.db["actions"].find_one({"_id": d.action_id})
        assert act["status"] == "queued" and act["decision_id"] == d.decision_id and act["admission_id"] == adm
        ev = await w.db["events"].find_one({"_id": stored["seq"]})
        assert ev["type"] == "action_allowed" and ev["decision_id"] == d.decision_id
        assert ev["action_id"] == d.action_id
        # IDs follow D20: (run_id, kind, diagnostic_id or "-", target)
        assert d.decision_id == derive("dec_", w.run_id, "file_proposal", "-", "p_scope1")
        assert d.action_id == derive("act_", w.run_id, "file_proposal", "-", "p_scope1")
    world(body)


def test_blocked_writes_only_the_decision_and_one_event(world):
    async def body(w):
        adm = await w.admit()
        before = await w.business_state()
        events_before = await w.count("events")
        d = await gate.evaluate(w.run_ctx(adm), scope_action(checks=[{"quote_found": False}]))
        assert d.blocked and d.failed_check == "evidence_checks" and d.action_id is None
        assert await w.business_state() == before
        assert await w.count("events") == events_before + 1
        ev = await w.db["events"].find_one({"_id": d["seq"]})
        assert ev["type"] == "action_blocked" and ev["decision_id"] == d.decision_id
    world(body)


def test_each_check_blocks_on_its_own_and_leaves_records_and_slack_untouched(world):
    async def body(w):
        cases = {}
        # check 1: a newer revoked version of lbdx
        # (run last, since it blocks everything after it)
        adm = await w.admit()
        cases["team_scope"] = (w.run_ctx(adm), scope_action(
            target={"diagnostic_id": w.dx_tissue, "proposal_id": "p_t", "field": "trials"},
            mention={"name": "FoundationOne CDx", "resolved_diagnostic_id": w.dx_tissue}))
        adm = await w.admit()
        cases["destination_action"] = (w.run_ctx(adm), {"kind": "notify_slack", "destination": "slack:#random",
                                                         "target": {"report_id": "rep_1"}})
        adm = await w.admit()
        cases["evidence_checks"] = (w.run_ctx(adm), scope_action(
            target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_e"},
            checks=[{"quote_found": True, "supported": False, "confidence": 0.9}]))
        released = await w.admit(status="released")
        cases["run_authorised"] = (w.run_ctx(released), scope_action(
            target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_r"}))
        for expected, (ctx, action) in cases.items():
            before = await w.business_state()
            d = await gate.evaluate(ctx, action)
            assert d.failed_check == expected, (expected, d["checks"])
            assert await w.business_state() == before
            assert await w.count("actions", {"kind": "notify_slack"}) == 0

        await w.db["grants"].insert_one(grant_doc("lbdx", 2, status="revoked", principal="dxp-curator", kind="agent",
                                                  scope={}, actions=[], destinations=[]))
        adm = await w.admit()
        before = await w.business_state()
        d = await gate.evaluate(w.run_ctx(adm), scope_action(
            target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_g"}))
        assert d.failed_check == "grant_active" and d["grant_version"] == 2 and d["run_grant_version"] == 1
        assert await w.business_state() == before
    world(body)


def test_a_repeat_of_the_same_run_step_returns_the_stored_decision(world):
    async def body(w):
        adm = await w.admit()
        d1 = await gate.evaluate(w.run_ctx(adm), scope_action())
        n_events, n_actions = await w.count("events"), await w.count("actions")
        d2 = await gate.evaluate(w.run_ctx(adm), scope_action())
        assert d2.decision_id == d1.decision_id and d2["seq"] == d1["seq"] and d2.action_id == d1.action_id
        assert await w.count("events") == n_events and await w.count("actions") == n_actions
    world(body)


def test_reviewer_decisions_carry_reviewer_stamp_and_a_retry_gets_a_new_decision(world):
    async def body(w):
        action = {"kind": "decide_report", "destination": "ledger",
                  "target": {"report_id": "rep_1", "scope_id": SCOPE_ID}}
        await w.db["grants"].insert_one(grant_doc("sam", 2, status="revoked", principal="sam", kind="person",
                                                  scope={}, actions=[], destinations=[]))
        d1 = await gate.evaluate(w.reviewer_ctx(), action)
        assert d1.blocked and d1["run_id"] is None and d1["agent"] is None and d1["initiated_by"] == "sam"
        assert d1["request_id"] and d1["cause"]["report_id"] == "rep_x"
        assert d1["checks"][4]["passed"] == "not_run"
        await w.db["grants"].insert_one(grant_doc(
            "sam", 3, principal="sam", kind="person", scope={"scope_id": SCOPE_ID, "diagnostic_ids": w.dx_plasma},
            actions=["decide_report"], destinations=["ledger"]))
        d2 = await gate.evaluate(w.reviewer_ctx(), action)
        assert d2.allowed and d2.decision_id != d1.decision_id
        assert d2["checks"][3]["passed"] == "n/a" and d2["checks"][4]["passed"] == "n/a"
        assert d2["policy_set_version"] == w.policy_set_version
    world(body)


def test_revert_report_decision_id_is_derived_without_the_request_id(world):
    async def body(w):
        action = {"kind": "revert_report", "destination": "ledger",
                  "target": {"report_id": "rep_9", "scope_id": SCOPE_ID}}
        d1 = await gate.evaluate(w.reviewer_ctx(), action)
        d2 = await gate.evaluate(w.reviewer_ctx(), action)
        assert d1.allowed and d1.decision_id == d2.decision_id
        assert d1.decision_id == derive("dec_", "-", "revert_report", "-", "rep_9")
        assert await w.count("decisions", {"kind": "revert_report"}) == 1
    world(body)


def test_authorise_task_uses_its_explicit_derived_decision_id(world):
    async def body(w):
        dec_id = derive("dec_", "dec_approval", "authorise_task")
        d = await gate.evaluate(w.reviewer_ctx(), {"kind": "authorise_task", "destination": "ledger",
                                                   "target": {"task_id": "task_1", "report_id": "rep_1"},
                                                   "decision_id": dec_id})
        assert d.decision_id == dec_id and d.allowed
    world(body)


def test_seed_decision_stamps(world):
    async def body(w):
        d = await gate.evaluate(w.seed_ctx(), {"kind": "apply_value", "destination": "ledger",
                                               "target": {"diagnostic_id": w.dx_tissue, "proposal_id": "p_seed"}})
        assert d.allowed and d["agent"] == "seed" and d["initiated_by"] == "seed" and d["run_id"] is None
        assert d["checks"][3]["passed"] == "n/a" and d["checks"][4]["passed"] == "n/a"
    world(body)


def test_blocked_claim_on_report_draft_then_redraft_allowed(world):
    async def body(w):
        base = {"kind": "file_proposal", "destination": "ledger",
                "source_fields": {"overall_status": "RECRUITING", "has_results": False},
                "retrieval": {"method": "vector_search", "top_k": 5, "items": []},
                "memories_used": [{"memory_id": "mem_m1", "version": 1}]}
        adm1 = await w.admit()
        d1 = await gate.evaluate(w.run_ctx(adm1), {**base,
            "target": {"report_id": "rep_a", "draft": 1, "scope_id": SCOPE_ID},
            "claims": [{"claim_kind": "claim_performed_or_results",
                        "text": "NCT04712877 showed blood profiling detecting actionable drivers."}]})
        assert d1.blocked and d1.failed_check == "evidence_checks"
        assert "claim_performed_or_results" in d1["checks"][3]["detail"]
        assert d1["claims"][0]["failed_policies"] == ["claim_performed_or_results", "claim_planned"]
        assert d1.decision_id == derive("dec_", w.run_id, "file_proposal", "-", "rep_a|draft1")
        assert await w.count("actions") == 0 and await w.count("reports") == 0
        adm2 = await w.admit()
        d2 = await gate.evaluate(w.run_ctx(adm2), {**base,
            "target": {"report_id": "rep_a", "draft": 2, "scope_id": SCOPE_ID},
            "claims": [{"claim_kind": "claim_planned", "text": "NCT04712877 is recruiting; no results posted."}]})
        assert d2.allowed and d2.decision_id != d1.decision_id
        assert d2["memories_used"][0]["memory_id"] == "mem_m1" and d2["retrieval"]["method"] == "vector_search"
    world(body)


def test_mark_action_is_conditional(world):
    async def body(w):
        adm = await w.admit()
        d = await gate.evaluate(w.run_ctx(adm), scope_action())
        assert await gate.mark_action(d.action_id, "done", {"proposal_ids": ["p"]}) is True
        assert await gate.mark_action(d.action_id, "failed") is False
        assert (await w.db["actions"].find_one({"_id": d.action_id}))["status"] == "done"
    world(body)


def test_memory_kind_team_scope(world):
    async def body(w):
        d = await gate.evaluate(w.reviewer_ctx(), {"kind": "create_memory", "destination": "ledger",
                                                   "target": {"report_id": "rep_1"}, "team_id": TEAM_ID})
        assert d.allowed
    world(body)

