"""The five checks and their order (Story 9.3, AD-19): pure, no Atlas needed."""

from __future__ import annotations

from datetime import timedelta

import pytest

from dxp.gate.checks import CHECK_ORDER, GateAction, GateCtx, Loaded, run_checks

from .world import CLAIM_POLICY_IDS, NOW, SCOPE_ID, TEAM_ID, grant_doc, policy_doc

PLASMA_DX = ["dx_plasma1", "dx_plasma2"]
TISSUE_DX = "dx_tissue"


def lbdx(**kw):
    base = dict(principal="dxp-curator", kind="agent", startable_by=["sam"],
                scope={"scope_id": SCOPE_ID, "diagnostic_ids": PLASMA_DX},
                actions=["search_source", "file_proposal", "notify_slack"],
                destinations=["source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"])
    base.update(kw)
    version = base.pop("version", 1)
    return grant_doc("lbdx", version, **base)


def sam(**kw):
    return grant_doc("sam", principal="sam", kind="person", startable_by=[],
                     scope={"scope_id": SCOPE_ID, "diagnostic_ids": PLASMA_DX},
                     actions=["decide_report", "authorise_task", "create_memory", "review_value",
                              "resolve_notification", "revert_report"],
                     destinations=["ledger"], **kw)


POLICIES = [policy_doc("evidence_quote", ["file_proposal", "file_related_evidence"],
                       {"quote_found": True, "supported": True, "min_confidence": 0.6})] + [
    policy_doc(p, ["file_proposal"], {"claim_checks": [p]}) for p in CLAIM_POLICY_IDS]

GOOD_CHECK = {"quote_found": True, "supported": True, "confidence": 0.9}


def run_ctx(**kw):
    base = dict(kind="run", principal="dxp-curator", grant_id="lbdx", run_id="run_1", agent="dxp-curator",
                initiated_by="sam", run_grant_version=1, policy_set_version="ps_x", admission_id="adm_1")
    base.update(kw)
    return GateCtx(**base)


def loaded(grant=None, run_status="running", admission_status="admitted", **kw):
    return Loaded(grant=grant if grant is not None else lbdx(), policies=POLICIES, now=NOW,
                  run={"_id": "run_1", "status": run_status},
                  admission={"_id": "adm_1", "run_id": "run_1", "status": admission_status}, **kw)


def scope_change(**kw):
    a = dict(kind="file_proposal", destination="ledger",
             target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_1"}, checks=[GOOD_CHECK])
    a.update(kw)
    return GateAction(**a)


def outcome(ctx, action, ld):
    checks, failed, claims = run_checks(ctx, action, ld)
    assert [c["check"] for c in checks] == list(CHECK_ORDER)
    if failed is not None:
        n = CHECK_ORDER.index(failed)
        assert checks[n]["passed"] is False
        for c in checks[n + 1:]:
            assert c["passed"] == "n/a" and c["detail"] == f"not evaluated: check {n + 1} ({failed}) blocked"
    return checks, failed, claims


def test_allowed_scope_collection_update_passes_all_five():
    checks, failed, _ = outcome(run_ctx(), scope_change(), loaded())
    assert failed is None
    assert all(c["passed"] is True for c in checks)


@pytest.mark.parametrize("grant,expect", [
    (lbdx(status="revoked", version=2), "is revoked"),
    (lbdx(expires_at=NOW - timedelta(seconds=1)), "expired"),
])
def test_check1_blocks_on_its_own(grant, expect):
    checks, failed, _ = outcome(run_ctx(), scope_change(), loaded(grant=grant))
    assert failed == "grant_active" and expect in checks[0]["detail"]
    assert [c["passed"] for c in checks[1:]] == ["n/a"] * 4


def test_check1_reads_the_latest_version_so_an_expired_task_grant_v2_blocks():
    v2 = grant_doc("task-abc", version=2, status="expired", expires_at=NOW, principal="dxp-curator",
                   kind="agent", scope={"scope_id": SCOPE_ID, "diagnostic_ids": PLASMA_DX},
                   actions=["search_source", "file_related_evidence"],
                   destinations=["source:clinicaltrials.gov", "ledger"], limits={"max_results": 5})
    ctx = run_ctx(grant_id="task-abc")
    checks, failed, _ = outcome(ctx, scope_change(kind="file_related_evidence",
                                                   target={"task_id": "task_1", "source_ref": "x", "scope_id": SCOPE_ID}),
                                loaded(grant=v2))
    assert failed == "grant_active" and "task-abc@v2 is expired" in checks[0]["detail"]


def test_check1_missing_grant():
    _, failed, _ = outcome(run_ctx(), scope_change(), Loaded(grant=None, policies=POLICIES, now=NOW))
    assert failed == "grant_active"


def test_check2_blocks_a_mention_link_to_an_out_of_scope_diagnostic_and_cites_it():
    action = GateAction(kind="file_proposal", destination="ledger",
                        target={"diagnostic_id": TISSUE_DX, "proposal_id": "p_2", "field": "trials"},
                        checks=[GOOD_CHECK], mention={"name": "FoundationOne CDx", "resolved_diagnostic_id": TISSUE_DX})
    checks, failed, _ = outcome(run_ctx(), action, loaded())
    assert failed == "team_scope"
    detail = checks[1]["detail"]
    assert "'FoundationOne CDx'" in detail and TISSUE_DX in detail and SCOPE_ID in detail


def test_check2_blocks_creating_a_diagnostic_outside_scope():
    action = scope_change(target={"diagnostic_id": "dx_new", "proposal_id": "p_3"}, creates_diagnostic=True)
    checks, failed, _ = outcome(run_ctx(), action, loaded())
    assert failed == "team_scope" and "D28" in checks[1]["detail"]


def test_check2_blocks_another_scope():
    _, failed, _ = outcome(run_ctx(), scope_change(target={"diagnostic_id": None, "scope_id": "scope_other",
                                                            "proposal_id": "p_1"}), loaded())
    assert failed == "team_scope"


def test_check2_all_true_only_for_seed():
    bad = lbdx(scope={"all": True})
    _, failed, _ = outcome(run_ctx(), scope_change(), loaded(grant=bad))
    assert failed == "team_scope"


def test_check2_search_limits_and_terms():
    task = grant_doc("task-abc", principal="dxp-curator", kind="agent", limits={"max_results": 5},
                     scope={"scope_id": SCOPE_ID, "diagnostic_ids": PLASMA_DX},
                     actions=["search_source", "file_related_evidence"], destinations=["source:clinicaltrials.gov", "ledger"])
    scope = {"assays": ["Guardant360 CDx"], "aliases": ["ctDNA"], "condition": "non-small cell lung cancer"}
    ld = loaded(grant=task, scope=scope)
    ctx = run_ctx(grant_id="task-abc")
    ok = GateAction(kind="search_source", destination="source:clinicaltrials.gov",
                    target={"task_id": "task_1"}, query={"terms": ["ctDNA"], "condition": "non-small cell lung cancer"},
                    requested_count=5)
    assert outcome(ctx, ok, ld)[1] is None
    over = GateAction(kind="search_source", destination="source:clinicaltrials.gov", target={"task_id": "task_1"},
                      requested_count=6)
    assert outcome(ctx, over, ld)[1] == "team_scope"
    off = GateAction(kind="search_source", destination="source:clinicaltrials.gov", target={"task_id": "task_1"},
                     query={"terms": ["FoundationOne CDx"]})
    assert outcome(ctx, off, ld)[1] == "team_scope"
    sixth = GateAction(kind="file_related_evidence", destination="ledger",
                       target={"task_id": "task_1", "source_ref": "x"}, filed_count=5, item_scope_ids=[SCOPE_ID],
                       checks=[GOOD_CHECK])
    assert outcome(ctx, sixth, ld)[1] == "team_scope"


def test_check3_blocks_a_slack_post_to_another_channel():
    action = GateAction(kind="notify_slack", destination="slack:#general", target={"report_id": "rep_1"})
    checks, failed, _ = outcome(run_ctx(), action, loaded())
    assert failed == "destination_action"


def test_check3_blocks_a_kind_not_on_the_grant_and_unknown_or_superseded_kinds():
    for kind in ("apply_value", "decide_proposal", "launch_rocket"):
        _, failed, _ = outcome(run_ctx(), scope_change(kind=kind), loaded())
        assert failed == "destination_action", kind


def test_check3_knows_revert_report():
    ctx = GateCtx(kind="reviewer", principal="sam", grant_id="sam", initiated_by="sam", request_id="r1")
    action = GateAction(kind="revert_report", destination="ledger", target={"report_id": "rep_1", "scope_id": SCOPE_ID})
    checks, failed, _ = outcome(ctx, action, Loaded(grant=sam(), policies=POLICIES, now=NOW))
    assert failed is None
    assert checks[3]["passed"] == "n/a" and checks[4]["passed"] == "n/a"


def test_check4_blocks_on_evidence():
    for bad in ({"quote_found": False, "supported": True, "confidence": 0.9},
                {"quote_found": True, "supported": False, "confidence": 0.9},
                {"quote_found": True, "supported": True, "confidence": 0.2}):
        checks, failed, _ = outcome(run_ctx(), scope_change(checks=[bad]), loaded())
        assert failed == "evidence_checks", bad


def test_check4_claim_policy_blocks_report_level_file_proposal():
    action = GateAction(kind="file_proposal", destination="ledger",
                        target={"report_id": "rep_1", "draft": 1, "scope_id": SCOPE_ID},
                        claims=[{"claim_kind": "claim_performed_or_results", "text": "It showed EGFR detection."}],
                        source_fields={"overall_status": "RECRUITING", "has_results": False})
    checks, failed, claims = outcome(run_ctx(), action, loaded())
    assert failed == "evidence_checks"
    assert "claim_performed_or_results" in checks[3]["detail"] and "showed" in checks[3]["detail"]
    assert claims[0]["passed"] is False


def test_check4_na_for_search_seed_and_human_kinds():
    seed = grant_doc("seed", principal="seed", kind="seed", scope={"all": True}, actions=["apply_value"],
                     destinations=["ledger"])
    ctx = GateCtx(kind="seed", principal="seed", grant_id="seed")
    checks, failed, _ = outcome(ctx, scope_change(kind="apply_value", checks=[{"quote_found": False}],
                                                   target={"diagnostic_id": "dx_any", "proposal_id": "p"}),
                                Loaded(grant=seed, policies=POLICIES, now=NOW))
    assert failed is None and checks[3]["passed"] == "n/a" and checks[4]["passed"] == "n/a"
    rctx = GateCtx(kind="reviewer", principal="sam", grant_id="sam", initiated_by="sam", request_id="r")
    for kind in ("decide_report", "authorise_task", "resolve_notification", "review_value"):
        target = {"report_id": "rep_1", "task_id": "task_1", "action_id": "act_1", "value_id": "v_1"}
        checks, failed, _ = outcome(rctx, GateAction(kind=kind, destination="ledger", target=target),
                                    Loaded(grant=sam(), policies=POLICIES, now=NOW))
        assert failed is None and checks[3]["passed"] == "n/a", kind


def test_check4_slack_needs_a_report_filed_allowed():
    action = GateAction(kind="notify_slack", destination="slack:#all-mango-db-hackathon", target={"report_id": "rep_1"})
    assert outcome(run_ctx(), action, loaded())[1] == "evidence_checks"
    ld = loaded(report={"_id": "rep_1", "file_decision_id": "dec_1"},
                report_file_decision={"_id": "dec_1", "outcome": "blocked"})
    assert outcome(run_ctx(), action, ld)[1] == "evidence_checks"
    ld.report_file_decision = {"_id": "dec_1", "outcome": "allowed"}
    assert outcome(run_ctx(), action, ld)[1] is None


@pytest.mark.parametrize("run_status,adm_status,admission", [
    ("stopped", "admitted", True),
    ("running", "released", True),
    ("running", "abandoned", True),
    ("running", "admitted", False),
])
def test_check5_blocks_on_its_own(run_status, adm_status, admission):
    ld = loaded(run_status=run_status, admission_status=adm_status)
    if not admission:
        ld.admission = None
    checks, failed, _ = outcome(run_ctx(), scope_change(), ld)
    assert failed == "run_authorised"
    assert all(c["passed"] is True for c in checks[:4])


def test_check5_allows_an_admitted_action_while_stopping():
    assert outcome(run_ctx(), scope_change(), loaded(run_status="stopping"))[1] is None


def test_context_validation():
    with pytest.raises(ValueError):
        GateCtx(kind="run", principal="dxp-curator", grant_id="lbdx").validate()  # agent write without run_id
    with pytest.raises(ValueError):
        GateCtx(kind="reviewer", principal="sam", grant_id="sam").validate()  # no request_id


def test_team_id_rule_for_memory_kinds():
    rctx = GateCtx(kind="reviewer", principal="sam", grant_id="sam", initiated_by="sam", request_id="r")
    ok = GateAction(kind="create_memory", destination="ledger", target={"report_id": "rep_1"}, team_id=TEAM_ID)
    assert outcome(rctx, ok, Loaded(grant=sam(), policies=POLICIES, now=NOW))[1] is None
    bad = GateAction(kind="create_memory", destination="ledger", target={"report_id": "rep_1"}, team_id="team_other")
    assert outcome(rctx, bad, Loaded(grant=sam(), policies=POLICIES, now=NOW))[1] == "team_scope"


def test_check4_fails_closed_when_no_check_is_recorded():
    _, failed, _ = outcome(run_ctx(), scope_change(checks=[]), loaded())
    assert failed == "evidence_checks"
    checks, failed, _ = outcome(run_ctx(), GateAction(
        kind="file_proposal", destination="ledger", target={"report_id": "rep_1", "draft": 2, "scope_id": SCOPE_ID},
        claims=[{"claim_kind": "claim_planned", "text": "It is recruiting."}],
        source_fields={"overall_status": "RECRUITING", "has_results": False}), loaded())
    assert failed == "evidence_checks" and "no check recorded" in checks[3]["detail"]


def test_check2_judges_the_diagnostic_a_mention_resolves_to_whatever_the_target():
    """I1 must-show 3: the FoundationOne CDx mention linked to the plasma scope (scope-targeted)."""
    action = scope_change(target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_m",
                                  "field": "evidence_collection"},
                          mention={"name": "FoundationOne CDx", "resolved_diagnostic_id": TISSUE_DX})
    checks, failed, _ = outcome(run_ctx(), action, loaded())
    assert failed == "team_scope"
    assert "'FoundationOne CDx'" in checks[1]["detail"] and TISSUE_DX in checks[1]["detail"]
    # an in-scope mention is allowed
    ok = scope_change(mention={"name": "FoundationOne Liquid CDx", "resolved_diagnostic_id": PLASMA_DX[0]})
    assert outcome(run_ctx(), ok, loaded())[1] is None


def test_unknown_claim_kind_is_refused():
    action = GateAction(kind="file_proposal", destination="ledger", target={"report_id": "rep_1", "draft": 1},
                        claims=[{"claim_kind": "", "text": "It showed X."}])
    with pytest.raises(ValueError):
        action.validate()
