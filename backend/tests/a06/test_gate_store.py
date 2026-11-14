"""gate.evaluate against a database (Story 9.3, D5, D19, D20, D21).

Each test runs on the in-memory fake and, when ``MONGODB_URI`` is set, on a
throwaway Atlas Sandbox database.
"""

from __future__ import annotations

from dxp import gate
from dxp.api.models import Decision

from .world import ANCHOR, SCOPE_ID, SV_ANCHOR, derive

GOOD = {"quote_found": True, "supported": True, "confidence": 0.9}


def scope_action(**kw):
    a = {"kind": "file_proposal", "destination": "ledger",
         "target": {"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_scope1"},
         "evidence_ref": {"source_ref": ANCHOR, "version_id": SV_ANCHOR}, "checks": [GOOD]}
    a.update(kw)
    return a


async def test_allowed_writes_decision_action_and_event(world):
    w = world
    adm = await w.admit()
    d = await w.evaluate(w.run_ctx(adm), scope_action())
    assert d.allowed and d.action_id
    stored = await w.db["decisions"].find_one({"_id": d.decision_id})
    assert stored["action_id"] == d.action_id and stored["seq"] is not None
    assert stored["grant_id"] == "lbdx" and stored["grant_version"] == 1
    assert stored["policy_set_version"] == w.policy_set_version
    assert stored["agent"] == "dxp-curator" and stored["initiated_by"] == "sam"
    assert stored["authorised_by"]["grant_id"] == "lbdx" and stored["authorised_by"]["granted_by"] == "luis"
    assert stored["evidence_ref"]["version_id"] == SV_ANCHOR
    assert [c["check"] for c in stored["checks"]] == list(gate.CHECK_ORDER)
    act = await w.db["actions"].find_one({"_id": d.action_id})
    assert act["status"] == "queued" and act["decision_id"] == d.decision_id and act["admission_id"] == adm
    ev = await w.db["events"].find_one({"_id": stored["seq"]})
    assert ev["type"] == "action_allowed" and ev["decision_id"] == d.decision_id
    assert ev["action_id"] == d.action_id
    # IDs follow D20: (run_id, kind, diagnostic_id or "-", target)
    assert d.decision_id == derive("dec_", w.run_id, "file_proposal", "-", "p_scope1")
    assert d.action_id == derive("act_", w.run_id, "file_proposal", "-", "p_scope1")


async def test_blocked_writes_only_the_decision_and_one_event(world):
    w = world
    adm = await w.admit()
    before = await w.business_state()
    events_before = await w.count("events")
    d = await w.evaluate(w.run_ctx(adm), scope_action(checks=[{"quote_found": False}]))
    assert d.blocked and d.failed_check == "evidence_checks" and d.action_id is None
    assert await w.business_state() == before
    assert await w.count("events") == events_before + 1
    ev = await w.db["events"].find_one({"_id": d["seq"]})
    assert ev["type"] == "action_blocked" and ev["decision_id"] == d.decision_id


async def test_each_check_blocks_on_its_own_and_leaves_records_and_slack_untouched(world):
    w = world
    cases = {}
    # check 1: a newer revoked version of lbdx
    # (run last, since it blocks everything after it)
    adm = await w.admit()
    cases["team_scope"] = (w.run_ctx(adm), scope_action(
        target={"diagnostic_id": w.dx_tissue, "proposal_id": "p_t", "field": "trials"},
        mention={"name": "FoundationOne CDx", "resolved_diagnostic_id": w.dx_tissue}))
    adm = await w.admit()
    cases["destination_action"] = (w.run_ctx(adm), {"kind": "notify_slack", "destination": "ledger",
                                                     "target": {"report_id": w.rep("1")}})
    adm = await w.admit()
    cases["evidence_checks"] = (w.run_ctx(adm), scope_action(
        target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_e"},
        checks=[{"quote_found": True, "supported": False, "confidence": 0.9}]))
    released = await w.admit(status="released", tail="p_r")
    cases["run_authorised"] = (w.run_ctx(released), scope_action(
        target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_r"}))
    for expected, (ctx, action) in cases.items():
        before = await w.business_state()
        d = await w.evaluate(ctx, action)
        assert d.failed_check == expected, (expected, d["checks"])
        assert await w.business_state() == before
        assert await w.count("actions", {"kind": "notify_slack"}) == 0

    await w.new_grant_version("lbdx", "revoked")
    adm = await w.admit()
    before = await w.business_state()
    d = await w.evaluate(w.run_ctx(adm), scope_action(
        target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_g"}))
    assert d.failed_check == "grant_active" and d["grant_version"] == 2 and d["run_grant_version"] == 1
    assert await w.business_state() == before


async def test_a_repeat_of_the_same_run_step_returns_the_stored_decision(world):
    w = world
    adm = await w.admit()
    d1 = await w.evaluate(w.run_ctx(adm), scope_action())
    n_events, n_actions = await w.count("events"), await w.count("actions")
    d2 = await w.evaluate(w.run_ctx(adm), scope_action())
    assert d2.decision_id == d1.decision_id and d2["seq"] == d1["seq"] and d2.action_id == d1.action_id
    assert await w.count("events") == n_events and await w.count("actions") == n_actions


async def test_reviewer_decisions_carry_reviewer_stamp_and_a_retry_gets_a_new_decision(world):
    w = world
    action = {"kind": "decide_report", "destination": "ledger",
              "target": {"report_id": w.rep("1"), "scope_id": SCOPE_ID}}
    revoked = await w.new_grant_version("sam", "revoked")
    d1 = await w.evaluate(w.reviewer_ctx(), action)
    assert d1.blocked and d1["run_id"] is None and d1["agent"] is None and d1["initiated_by"] == "sam"
    assert d1["request_id"] and d1["cause"]["report_id"] == w.rep("cause")
    assert [c["passed"] for c in d1["checks"]] == [False, "n/a", "n/a", "n/a", "n/a"]
    # The next version after the revocation (sam@v2 is seeded since V70, so this is no longer v3).
    nxt = int(revoked["version"]) + 1
    reactivated = {**w.grants["sam"], "_id": f"sam@v{nxt}", "version": nxt, "status": "active"}
    await w.db["grants"].insert_one(reactivated)
    d2 = await w.evaluate(w.reviewer_ctx(), action)
    assert d2.allowed and d2.decision_id != d1.decision_id, (d2["checks"], d2["claims"])
    assert d2["checks"][3]["passed"] == "n/a" and d2["checks"][4]["passed"] == "n/a"
    assert d2["policy_set_version"] == w.policy_set_version


async def test_revert_report_decision_id_is_derived_without_the_request_id(world):
    w = world
    action = {"kind": "revert_report", "destination": "ledger",
              "target": {"report_id": w.rep("9"), "scope_id": SCOPE_ID}}
    d1 = await w.evaluate(w.reviewer_ctx(), action)
    d2 = await w.evaluate(w.reviewer_ctx(), action)
    assert d1.allowed and d1.decision_id == d2.decision_id
    assert d1.decision_id == derive("dec_", "-", "revert_report", "-", w.rep("9"))
    assert await w.count("decisions", {"kind": "revert_report"}) == 1


async def test_authorise_task_uses_its_explicit_derived_decision_id(world):
    w = world
    dec_id = derive("dec_", "dec_approval", "authorise_task")
    d = await w.evaluate(w.reviewer_ctx(), {"kind": "authorise_task", "destination": "ledger",
                                               "target": {"task_id": "task_1", "report_id": w.rep("1")},
                                               "decision_id": dec_id})
    assert d.decision_id == dec_id and d.allowed


async def test_seed_decision_stamps(world):
    w = world
    d = await w.evaluate(w.seed_ctx(), {"kind": "apply_value", "destination": "ledger",
                                           "target": {"diagnostic_id": w.dx_tissue, "proposal_id": "p_seed"}})
    assert d.allowed and d["agent"] == "seed" and d["initiated_by"] == "seed" and d["run_id"] is None
    assert d["checks"][3]["passed"] == "n/a" and d["checks"][4]["passed"] == "n/a"


async def test_blocked_claim_on_report_draft_then_redraft_allowed(world):
    w = world
    base = {"kind": "file_proposal", "destination": "ledger",
            "source_fields": {"overall_status": "RECRUITING", "has_results": False},
            "retrieval": {"method": "vector_search", "top_k": 5, "items": []},
            "checks": [GOOD],
            "memories_used": [{"memory_id": "mem_m1", "version": 1, "author": "sam",
                                   "source": {"decision_id": "dec_m1", "report_id": w.rep("m1")}}]}
    adm1 = await w.admit()
    d1 = await w.evaluate(w.run_ctx(adm1), {**base,
        "target": {"report_id": w.rep("a"), "draft": 1, "scope_id": SCOPE_ID},
        "claims": [{"claim_kind": "claim_performed_or_results",
                    "text": "NCT04712877 showed blood profiling detecting actionable drivers."}]})
    assert d1.blocked and d1.failed_check == "evidence_checks"
    assert "claim_performed_or_results" in d1["checks"][3]["detail"]
    assert d1["claims"][0]["failed_policies"] == ["claim_performed_or_results", "claim_planned"]
    assert d1.decision_id == derive("dec_", w.run_id, "file_proposal", "-", f"{w.rep('a')}|draft1")
    assert await w.count("actions") == 0 and await w.count("reports") == 0
    adm2 = await w.admit(head=SCOPE_ID, tail=f"{w.rep('a')}|draft2")
    d2 = await w.evaluate(w.run_ctx(adm2), {**base,
        "target": {"report_id": w.rep("a"), "draft": 2, "scope_id": SCOPE_ID},
        "claims": [{"claim_kind": "claim_performed_or_results",
                    "text": "NCT04712877 is recruiting; no results posted."},
                   {"claim_kind": "claim_planned", "text": "NCT04712877 is recruiting; no results posted."}]})
    assert d2.allowed and d2.decision_id != d1.decision_id, (d2["checks"], d2["claims"])
    assert d2["memories_used"][0]["memory_id"] == "mem_m1" and d2["retrieval"]["method"] == "vector_search"


async def test_mark_action_is_conditional(world):
    w = world
    adm = await w.admit()
    d = await w.evaluate(w.run_ctx(adm), scope_action())
    assert await gate.mark_action(d.action_id, "done", {"proposal_ids": ["p"]}) is True
    assert await gate.mark_action(d.action_id, "failed") is False
    assert (await w.db["actions"].find_one({"_id": d.action_id}))["status"] == "done"


async def test_memory_kind_team_scope(world):
    w = world
    d = await w.evaluate(w.reviewer_ctx(), {"kind": "create_memory", "destination": "ledger",
                                               "target": {"report_id": w.rep("1")}, "team_id": w.team_id})
    assert d.allowed



async def test_evaluate_takes_the_frozen_run_context_and_proposed_action(world):
    from dxp.api.models import Principal, ProposedAction, RunContext, Stamp

    w = world
    adm = await w.admit(head=SCOPE_ID)
    ctx = RunContext(
        run_id=w.run_id, principal=Principal(id="dxp-curator", name="dxp-curator", kind="agent"),
        stamp=Stamp(kind="run", run_id=w.run_id, agent="dxp-curator", initiated_by="sam", principal="dxp-curator",
                    grant_id="lbdx", grant_version=1, policy_set_version=w.policy_set_version),
        grant_id="lbdx", grant_version=1, policy_set_version=w.policy_set_version, admission_id=adm)
    action = ProposedAction(kind="file_proposal", destination="ledger",
                            target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_frozen"},
                            inputs={"checks": [GOOD]})
    d = await gate.evaluate(ctx, action)
    assert isinstance(d, Decision) and d.outcome == "allowed" and d.agent == "dxp-curator"
    assert d.run_grant_version == 1 and d.seq is not None and d.action_id
    blocked = await gate.evaluate(ctx, ProposedAction(
        kind="file_proposal", destination="ledger", target={"report_id": w.rep("f"), "scope_id": SCOPE_ID},
        inputs={"draft": 1, "source_fields": {"overall_status": "RECRUITING", "has_results": False}},
        claims=[{"claim_kind": "claim_performed_or_results", "text": "It showed EGFR detection.", "passed": False}]))
    assert blocked.outcome == "blocked" and blocked.failed_check == "evidence_checks"
    assert blocked.claims[0].passed is False


async def test_unknown_kinds_are_contract_errors_but_unknown_destinations_are_recorded_blocks(world):
    """Review item 3 (Luis, 6881072627): notify_slack to slack:#general reaches check 3 and
    records a blocked Decision (AD-19, S2); only an unknown kind is refused before any record."""
    import pytest

    w = world
    adm = await w.admit(kind="notify_slack", head=w.rep("1"))
    before = await w.business_state()
    d = await gate.evaluate(w.run_ctx(adm), {"kind": "notify_slack", "destination": "slack:#general",
                                             "target": {"report_id": w.rep("1")}})
    assert isinstance(d, Decision) and d.outcome == "blocked" and d.failed_check == "destination_action"
    assert d.destination == "slack:#general" and "unknown destination 'slack:#general'" in d.checks[2].detail
    stored = await w.db["decisions"].find_one({"_id": d.id})
    assert stored["destination"] == "slack:#general" and stored["outcome"] == "blocked"
    ev = await w.db["events"].find_one({"_id": stored["seq"]})
    assert ev["type"] == "action_blocked" and ev["decision_id"] == d.id
    assert await w.business_state() == before and await w.count("actions") == 0
    with pytest.raises(ValueError):
        await gate.evaluate(w.run_ctx(adm), scope_action(kind="launch_rocket"))
    assert await w.count("decisions") == 1


async def test_a_blocked_decision_always_lists_five_checks_in_order(world):
    """Blocked action (D5): every check with its result and detail, whichever check blocked."""
    w = world
    cases = [
        ("team_scope", scope_action(target={"diagnostic_id": w.dx_tissue, "proposal_id": "p_5a"})),
        ("destination_action", {"kind": "notify_slack", "destination": "ledger", "target": {"report_id": w.rep("5")}}),
        ("evidence_checks", scope_action(target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_5c"},
                                         checks=[{"quote_found": False}])),
    ]
    for expected, action in cases:
        adm = await w.admit()
        d = await gate.evaluate(w.run_ctx(adm), action)
        assert isinstance(d, Decision) and d.outcome == "blocked" and d.failed_check == expected
        assert [c.check for c in d.checks] == list(gate.CHECK_ORDER)
        n = gate.CHECK_ORDER.index(expected)
        assert all(c.passed is True for c in d.checks[:n]) and d.checks[n].passed is False
        assert all(c.passed == "n/a" and c.detail.startswith(f"not evaluated: check {n + 1}") for c in d.checks[n + 1:])
    released = await w.admit(status="released", tail="p_5d")
    d = await gate.evaluate(w.run_ctx(released), scope_action(
        target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_5d"}))
    assert d.failed_check == "run_authorised" and len(d.checks) == 5
    await w.new_grant_version("lbdx", "revoked")
    adm = await w.admit()
    d = await gate.evaluate(w.run_ctx(adm), scope_action(
        target={"diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_5e"}))
    assert d.failed_check == "grant_active" and [c.passed for c in d.checks] == [False] + ["n/a"] * 4


async def test_check4_with_no_check_recorded_blocks(world):
    w = world
    adm = await w.admit()
    d = await w.evaluate(w.run_ctx(adm), scope_action(checks=[]))
    assert d.blocked and d.failed_check == "evidence_checks" and "no check recorded" in d["checks"][3]["detail"]


def _grant_version_nullable() -> bool:
    from dxp.api.models import Decision

    return Decision.model_fields["grant_version"].is_required() is False or "None" in str(
        Decision.model_fields["grant_version"].annotation)


async def test_missing_grant_is_a_recorded_block_with_null_version(world):
    import pytest

    if not _grant_version_nullable():
        pytest.skip("needs PR #34 (A01): Decision.grant_version may be null; until then the API model requires an int")
    w = world
    ctx = w.reviewer_ctx(grant_id="nosuch")
    ctx["stamp"] = {**ctx["stamp"], "grant_id": "nosuch", "grant_version": None}
    d = await w.evaluate(ctx, {"kind": "decide_report", "destination": "ledger",
                               "target": {"report_id": w.report_id, "scope_id": SCOPE_ID}})
    assert d.failed_check == "grant_active" and d["grant_version"] is None
    assert d["authorised_by"]["grant_version"] is None


async def test_unknown_claim_kind_writes_no_decision(world):
    import pytest

    w = world
    adm = await w.admit()
    with pytest.raises(ValueError):
        await gate.evaluate(w.run_ctx(adm), {"kind": "file_proposal", "destination": "ledger",
                                             "target": {"report_id": w.report_id, "draft": 1, "scope_id": SCOPE_ID},
                                             "checks": [GOOD], "claims": [{"claim_kind": "other", "text": "x"}]})
    assert await w.count("decisions") == 0


async def test_missing_grant_is_recorded_with_null_version_in_the_store(world):
    """The stored Decision is valid under A03's validator (grant_version null), whatever the API model."""
    from dxp.gate import decisions
    from dxp.gate.checks import GateAction, GateCtx

    w = world
    ctx = GateCtx.coerce({**w.reviewer_ctx(grant_id="nosuch")})
    action = GateAction.coerce({"kind": "decide_report", "destination": "ledger",
                                "target": {"report_id": w.report_id, "scope_id": SCOPE_ID}})
    dec_id, act_id = decisions.ids_for(ctx, action)
    loaded, psv = await gate._load(ctx, action)
    results, failed, claims = gate.checks.run_checks(ctx, action, loaded)
    doc = decisions.build_decision(ctx, action, decision_id=dec_id, grant=loaded.grant, policy_set_version=psv,
                                   checks=results, failed_check=failed, claims=claims, now=loaded.now)
    stored = await decisions.record(ctx, action, doc, act_id)  # the fake applies A03's validator
    assert stored["failed_check"] == "grant_active" and stored["grant_version"] is None
    assert stored["authorised_by"]["grant_version"] is None


async def test_the_fake_backend_applies_a03_validators(world):
    """So the fake-backend runs also prove the documents pass A03's $jsonSchema validators."""
    import pytest

    from .fakedb import FakeDB, FakeWriteError

    w = world
    if not isinstance(w.db, FakeDB):
        pytest.skip("checks the in-memory backend only; Atlas applies the validators itself")
    with pytest.raises(FakeWriteError):
        await w.db["proposals"].insert_one({"_id": "p_bad", "op": "add", "status": "pending"})


async def test_item6_an_admission_for_another_item_does_not_authorise_the_action(world):
    """Review item 6 (Luis, 6881072627): the probe. An admission for NCT_OTHER does not authorise
    an action on this trial; check 5 blocks and nothing but the Decision is written."""
    w = world
    other = await w.admit(head="clinicaltrials.gov:NCT_OTHER")
    before = await w.business_state()
    d = await w.evaluate(w.run_ctx(other), scope_action())
    assert d.blocked and d.failed_check == "run_authorised"
    assert "is not for this action" in d["checks"][4]["detail"] and "NCT_OTHER" in d["checks"][4]["detail"]
    assert await w.business_state() == before
    this = await w.admit()
    assert (await w.evaluate(w.run_ctx(this), scope_action(target={
        "diagnostic_id": None, "scope_id": SCOPE_ID, "proposal_id": "p_this"}))).allowed


class _Txn:
    """A stand-in for a client session inside a transaction (fake backend only)."""

    in_transaction = True


async def test_insert_if_absent_in_a_transaction_reads_first_and_never_catches_a_duplicate(world):
    """Review risk: a caught duplicate-key error aborts an Atlas transaction, so inside one the
    insert is made only after a read finds nothing."""
    import pytest

    from dxp.gate.decisions import insert_if_absent

    from .fakedb import FakeDB

    w = world
    if not isinstance(w.db, FakeDB):
        pytest.skip("uses a stand-in session; the Atlas path is covered by evaluate_in in A24's tests")
    coll = w.db["aliases"]
    calls: list[str] = []
    real_insert = coll.insert_one

    async def counting_insert(doc, session=None):
        calls.append(doc["_id"])
        return await real_insert(doc, session=session)

    coll.insert_one = counting_insert
    doc = {"_id": "txn alias", "diagnostic_id": w.dx_f1l, "name": "txn alias", "created_mode": "live"}
    _, inserted = await insert_if_absent(coll, doc, session=_Txn())
    again, inserted_again = await insert_if_absent(coll, {**doc, "name": "other"}, session=_Txn())
    assert inserted is True and inserted_again is False and again["name"] == "txn alias"
    assert calls == ["txn alias"]  # the second call never attempted the insert


async def test_evaluate_in_reads_the_grant_and_pinned_policies_on_the_session(world, monkeypatch):
    """Review risk: inside a caller's transaction the grant and policy reads use its session."""
    import pytest

    from dxp.gate import policy_sets

    from .fakedb import FakeDB

    w = world
    if not isinstance(w.db, FakeDB):
        pytest.skip("uses a stand-in session")
    seen: list[tuple[str, object]] = []
    for name in ("grants", "policies", "policy_sets"):
        coll = w.db[name]
        real_find, real_find_one = coll.find, coll.find_one

        def find(flt=None, session=None, _n=name, _f=real_find, **kw):
            seen.append((_n, session))
            return _f(flt, session=session, **kw)

        async def find_one(flt=None, session=None, _n=name, _f=real_find_one, **kw):
            seen.append((_n, session))
            return await _f(flt, session=session, **kw)

        coll.find, coll.find_one = find, find_one

    async def not_on_the_session(*a, **k):
        raise AssertionError("read outside the session")

    monkeypatch.setattr(policy_sets, "current_grant", not_on_the_session)
    monkeypatch.setattr(policy_sets, "policy_set", not_on_the_session)
    monkeypatch.setattr(policy_sets, "policies_in_set", not_on_the_session)
    txn = _Txn()
    adm = await w.admit()
    d = await gate.evaluate_in(w.run_ctx(adm), scope_action(), txn)
    assert d.outcome == "allowed"
    assert {n for n, s in seen if s is txn} == {"grants", "policies", "policy_sets"}
