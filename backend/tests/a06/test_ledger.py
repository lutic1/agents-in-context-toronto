"""ledger.file, ledger.apply and ledger.recover_applying (Story 1.6, D13, D26 to D28, V35, V37, V43)."""

from __future__ import annotations

import asyncio
import importlib

import pytest

from dxp import ledger

from .world import ANCHOR, SCOPE_ID, derive, dx, normalise_name

apply_mod = importlib.import_module("dxp.ledger.apply")  # the package attribute "apply" is the function

GOOD = {"quote_found": True, "supported": True, "confidence": 0.9}
EVIDENCE = {"source_ref": ANCHOR, "version_id": "sv_anchor0000000001", "source": "clinicaltrials.gov",
            "quote": "ctDNA, tumor NGS"}


def scope_change():
    return {"field": "evidence_collection", "value": ANCHOR, "scope_id": SCOPE_ID, "evidence": EVIDENCE,
            "check": GOOD, "label": "early-stage plasma-plus-tissue profiling study"}


def mention_change(w):
    return {"field": "trials", "value": "NCT04712877", "diagnostic_id": w.dx_tissue, "evidence": EVIDENCE,
            "check": GOOD, "mention": {"name": "FoundationOne CDx", "resolved_diagnostic_id": w.dx_tissue}}


async def test_demo_path_allowed_scope_update_and_blocked_mention_link(world):
    w = world
    adm1, adm2 = await w.admit(), await w.admit()
    before_items = await w.db["source_items"].find_one({"_id": ANCHOR})
    [ok] = await ledger.file_detailed("f_anchor", scope_change(), "live", w.run_ctx(adm1, report_id="rep_a"))
    assert ok.status == "filed" and ok.diagnostic_id is None
    p = await w.db["proposals"].find_one({"_id": ok.proposal_id})
    assert p["status"] == "pending" and p["diagnostic_id"] is None and p["target"] == {"scope_id": SCOPE_ID}
    assert p["report_id"] == "rep_a" and p["action_id"] and p["decision_id"] == ok.decision_id
    assert p["stamp"]["run_id"] == w.run_id and "notification" not in p
    assert p["evidence"]["version_id"] == "sv_anchor0000000001"
    act = await w.db["actions"].find_one({"_id": p["action_id"]})
    assert act["status"] == "done" and act["result"]["proposal_ids"] == [ok.proposal_id]
    assert await w.count("events", {"type": "proposal_pending"}) == 1
    assert await w.db["source_items"].find_one({"_id": ANCHOR}) == before_items  # never applied in live mode
    dec = await w.db["decisions"].find_one({"_id": ok.decision_id})
    assert dec["target"]["diagnostic_id"] is None and dec["target"]["scope_id"] == SCOPE_ID

    before = await w.business_state()
    [blocked] = await ledger.file_detailed("f_anchor_f1", mention_change(w), "live", w.run_ctx(adm2, report_id="rep_a"))
    assert blocked.status == "blocked" and blocked.reason == "team_scope"
    detail = blocked.decision.checks[1].detail
    assert "'FoundationOne CDx'" in detail and w.dx_tissue in detail and SCOPE_ID in detail
    assert blocked.decision.inputs["mention"]["name"] == "FoundationOne CDx"
    assert await w.business_state() == before


async def test_creating_a_diagnostic_outside_scope_is_blocked_before_any_write(world):
    w = world
    adm = await w.admit()
    before = await w.business_state()
    [r] = await ledger.file_detailed("f_new", {"field": "trials", "value": "NCT1", "assay_name": "Brand New Assay",
                                      "evidence": EVIDENCE, "check": GOOD}, "live", w.run_ctx(adm))
    assert r.status == "blocked" and r.reason == "team_scope"
    assert await w.business_state() == before
    assert await w.db["diagnostics"].find_one({"_id": dx("Brand New Assay")}) is None


async def test_live_change_to_in_scope_diagnostic_is_pending_never_applied(world):
    w = world
    adm = await w.admit()
    [r] = await ledger.file_detailed("f_1", {"field": "biomarkers", "value": "EGFR", "diagnostic_id": w.dx_f1l,
                                    "evidence": EVIDENCE, "check": GOOD}, "live", w.run_ctx(adm))
    assert r.status == "filed"
    d = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    assert d["fields"] == {} and d["rev"] == 0 and d["applied_proposal_ids"] == []


async def test_filing_twice_and_concurrent_findings_leave_no_duplicates(world):
    w = world
    adm = await w.admit()
    change = {"field": "biomarkers", "value": "EGFR", "diagnostic_id": w.dx_f1l, "evidence": EVIDENCE, "check": GOOD}
    a = await ledger.file_detailed("f_1", change, "live", w.run_ctx(adm))
    b = await ledger.file_detailed("f_1", change, "live", w.run_ctx(adm))
    assert a[0].proposal_id == b[0].proposal_id
    assert await w.count("proposals") == 1 and await w.count("decisions") == 1 and await w.count("actions") == 1

    # two Findings creating the same new in-scope Diagnostic at once, under the seed grant
    name = "Guardant360 CDx"  # in scope; its alias exists, so ensure_diagnostic must find it
    n_dx = await w.count("diagnostics")
    r1, r2 = await asyncio.gather(
        ledger.file_detailed("f_a", {"field": "biomarkers", "value": "KRAS", "assay_name": name, "evidence": EVIDENCE,
                            "check": GOOD}, "baseline", w.seed_ctx()),
        ledger.file_detailed("f_b", {"field": "biomarkers", "value": "ALK", "assay_name": name, "evidence": EVIDENCE,
                            "check": GOOD}, "baseline", w.seed_ctx()),
    )
    assert await w.count("diagnostics") == n_dx
    brand_new = "Approach Assay"
    r3, r4 = await asyncio.gather(
        ledger.file_detailed("f_c", {"field": "biomarkers", "value": "KRAS", "assay_name": brand_new, "evidence": EVIDENCE,
                            "check": GOOD}, "baseline", w.seed_ctx()),
        ledger.file_detailed("f_d", {"field": "biomarkers", "value": "ALK", "assay_name": brand_new, "evidence": EVIDENCE,
                            "check": GOOD}, "baseline", w.seed_ctx()),
    )
    assert await w.count("diagnostics") == n_dx + 1
    assert await w.count("events", {"type": "diagnostic_created"}) == 1
    d = await w.db["diagnostics"].find_one({"_id": dx(brand_new)})
    assert sorted(e["value"] for e in d["fields"]["biomarkers"]) == ["ALK", "KRAS"]
    assert d["created_mode"] == "baseline"


async def test_equal_value_and_earlier_stage_are_not_filed(world):
    w = world
    await ledger.file_detailed("f_s", {"field": "biomarkers", "value": "EGFR", "diagnostic_id": w.dx_f1l,
                              "evidence": EVIDENCE, "check": GOOD}, "baseline", w.seed_ctx())
    adm = await w.admit()
    [r] = await ledger.file_detailed("f_2", {"field": "biomarkers", "value": "EGFR", "diagnostic_id": w.dx_f1l,
                                    "evidence": EVIDENCE, "check": GOOD}, "live", w.run_ctx(adm))
    assert r.status == "not_filed" and "current" in r.reason
    [r] = await ledger.file_detailed("f_3", {"field": "lifecycle_stage", "value": "discovery", "diagnostic_id": w.dx_f1l,
                                    "evidence": EVIDENCE, "check": GOOD}, "live", w.run_ctx(adm))
    assert r.status == "not_filed" and "not later" in r.reason


async def test_seed_values_are_applied_at_once_unreviewed(world):
    w = world
    [r] = await ledger.file_detailed("f_seed", {"field": "biomarkers", "value": "EGFR", "diagnostic_id": w.dx_tissue,
                                       "evidence": EVIDENCE, "check": GOOD}, "baseline", w.seed_ctx())
    assert r.status == "applied"
    d = await w.db["diagnostics"].find_one({"_id": w.dx_tissue})
    [entry] = d["fields"]["biomarkers"]
    assert entry["review"] == "unreviewed" and entry["state"] == "current" and entry["proposal_id"] == r.proposal_id
    assert d["applied_proposal_ids"] == [r.proposal_id] and d["rev"] == 1 and d["facets"]["biomarkers"] == ["EGFR"]
    assert r.decision.agent == "seed"
    act = await w.db["actions"].find_one({"_id": r.decision.action_id})
    assert act["status"] == "done" and act["result"]["value_ids"] == [entry["value_id"]]


async def test_modes_and_contexts_are_enforced(world):
    w = world
    with pytest.raises(ValueError):
        await ledger.file_detailed("f", scope_change(), "baseline", w.run_ctx(None))
    with pytest.raises(ValueError):
        await ledger.file_detailed("f", scope_change(), "live", w.seed_ctx())
    with pytest.raises(ValueError):
        await ledger.file_detailed("f", scope_change(), "dry_run", w.run_ctx(None))


async def _pending_diag(w, finding="f_1", value="EGFR", run_ctx=None):
    adm = await w.admit()
    [r] = await ledger.file_detailed(finding, {"field": "biomarkers", "value": value, "diagnostic_id": w.dx_f1l,
                                      "evidence": EVIDENCE, "check": GOOD}, "live", run_ctx or w.run_ctx(adm))
    return r.proposal_id


async def test_apply_writes_entry_edges_event_once(world):
    w = world
    pid = await _pending_diag(w)
    p = await ledger.apply_with(pid, review="accepted", decided_by="sam")
    assert p.status == "applied"
    assert (await w.db["proposals"].find_one({"_id": pid}))["value_id"]
    d = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    assert d["applied_proposal_ids"] == [pid] and d["rev"] == 1
    assert d["fields"]["biomarkers"][0]["review"] == "accepted" and "EGFR" in d["search_text"]
    edge_id = derive("e_", f"diagnostic:{w.dx_f1l}", "biomarker:EGFR", "biomarkers")
    edge = await w.db["edges"].find_one({"_id": edge_id})
    assert edge["run_id"] == w.run_id and edge["proposal_id"] == pid and edge["status"] == "applied"
    assert await w.count("events", {"type": "value_applied"}) == 1
    again = await ledger.apply(pid)
    assert again.status == "applied"
    assert (await w.db["diagnostics"].find_one({"_id": w.dx_f1l}))["rev"] == 1


async def test_concurrent_applies_apply_once(world):
    w = world
    pid = await _pending_diag(w)
    results = await asyncio.gather(*(ledger.apply_with(pid, review="accepted") for _ in range(5)))
    assert all(r.status in ("applying", "applied") for r in results)
    d = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    assert d["applied_proposal_ids"] == [pid] and d["rev"] == 1 and len(d["fields"]["biomarkers"]) == 1
    assert await w.count("events", {"type": "value_applied"}) == 1
    assert (await w.db["proposals"].find_one({"_id": pid}))["status"] == "applied"


async def test_apply_interrupted_after_the_guarded_update_is_finished_by_recovery(world, monkeypatch):
    w = world
    pid = await _pending_diag(w)
    real = apply_mod._upsert_edges

    async def crash(p, session):
        raise RuntimeError("worker died")

    monkeypatch.setattr(apply_mod, "_upsert_edges", crash)
    with pytest.raises(RuntimeError):
        await ledger.apply_with(pid, review="accepted")
    assert (await w.db["proposals"].find_one({"_id": pid}))["status"] == "applying"
    assert (await w.db["diagnostics"].find_one({"_id": w.dx_f1l}))["applied_proposal_ids"] == [pid]
    assert await w.count("edges") == 0
    monkeypatch.setattr(apply_mod, "_upsert_edges", real)

    assert await apply_mod.recover_applying_ids() == [pid]
    assert await apply_mod.recover_applying_ids() == []  # idempotent
    assert (await w.db["proposals"].find_one({"_id": pid}))["status"] == "applied"
    d = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    assert d["rev"] == 1 and len(d["fields"]["biomarkers"]) == 1
    assert await w.count("edges") == 1 and await w.count("events", {"type": "value_applied"}) == 1


async def test_recovery_reruns_edges_and_event_whatever_the_guard_returns(world):
    w = world
    pid = await _pending_diag(w)
    await ledger.apply_with(pid, review="accepted")
    # simulate a crash that left the proposal in applying after everything else ran
    await w.db["proposals"].update_one({"_id": pid}, {"$set": {"status": "applying"}})
    await apply_mod.recover_applying_ids()
    await apply_mod.recover_applying_ids()
    assert await w.count("edges") == 1 and await w.count("events", {"type": "value_applied"}) == 1
    assert (await w.db["diagnostics"].find_one({"_id": w.dx_f1l}))["rev"] == 1


async def test_edges_keep_their_first_run_id(world):
    w = world
    first = await _pending_diag(w, finding="f_run1")
    await ledger.apply_with(first, review="accepted")
    edge_id = derive("e_", f"diagnostic:{w.dx_f1l}", "biomarker:EGFR", "biomarkers")
    # a later run re-proposes the same value after it was superseded off current
    await w.db["diagnostics"].update_one({"_id": w.dx_f1l}, {"$set": {"fields.biomarkers": []}})
    await w.db["runs"].insert_one({"_id": "run_test0002", "agent": "dxp-curator", "initiated_by": "sam",
                                   "grant_id": "lbdx", "grant_version": 1, "status": "running",
                                   "policy_set_version": w.policy_set_version})
    adm = await w.admit(run_id="run_test0002")
    ctx = w.run_ctx(adm, run_id="run_test0002")
    ctx["stamp"] = {**ctx["stamp"], "run_id": "run_test0002"}
    second = await _pending_diag(w, finding="f_run2", run_ctx=ctx)
    await ledger.apply_with(second, review="accepted")
    edge = await w.db["edges"].find_one({"_id": edge_id})
    assert edge["run_id"] == w.run_id and edge["proposal_id"] == first


async def test_scope_collection_apply_writes_no_diagnostic_or_edge(world):
    w = world
    adm = await w.admit()
    [r] = await ledger.file_detailed("f_anchor", scope_change(), "live", w.run_ctx(adm, report_id="rep_a"))
    before_dx = sorted([d async for d in w.db["diagnostics"].find({})], key=lambda d: d["_id"])
    p = await ledger.apply_with(r.proposal_id, review="accepted", decided_by="sam")
    assert p.status == "applied"
    assert (await w.db["proposals"].find_one({"_id": r.proposal_id}))["value_id"] is None
    item = await w.db["source_items"].find_one({"_id": ANCHOR})
    entry = item["collections"][SCOPE_ID]
    assert entry["status"] == "accepted" and entry["proposal_id"] == r.proposal_id
    assert entry["version_id"] == "sv_anchor0000000001"
    assert sorted([d async for d in w.db["diagnostics"].find({})], key=lambda d: d["_id"]) == before_dx
    assert await w.count("edges") == 0 and await w.count("events", {"type": "value_applied"}) == 1
    # the same update again is not filed
    adm2 = await w.admit()
    [again] = await ledger.file_detailed("f_anchor2", scope_change(), "live", w.run_ctx(adm2))
    assert again.status == "not_filed"


async def test_reverse_proposals_are_left_to_a26(world):
    w = world
    await w.db["proposals"].insert_one({"_id": "p_rev", "op": "remove", "reverts_proposal_id": "p_x",
                                        "status": "applying", "diagnostic_id": None})
    assert await apply_mod.recover_applying_ids() == []
    await w.db["proposals"].update_one({"_id": "p_rev"}, {"$set": {"status": "pending"}})
    with pytest.raises(ValueError):
        await ledger.apply("p_rev")
    assert (await w.db["proposals"].find_one({"_id": "p_rev"}))["status"] == "pending"


async def test_single_field_supersedes_on_reviewer_apply_and_is_held_for_baseline(world):
    w = world
    await ledger.file_detailed("f_m1", {"field": "modality", "value": "ngs", "diagnostic_id": w.dx_f1l,
                               "evidence": EVIDENCE, "check": GOOD}, "baseline", w.seed_ctx())
    [held] = await ledger.file_detailed("f_m2", {"field": "modality", "value": "pcr", "diagnostic_id": w.dx_f1l,
                                        "evidence": EVIDENCE, "check": GOOD}, "baseline", w.seed_ctx())
    p = await w.db["proposals"].find_one({"_id": held.proposal_id})
    assert p["status"] == "pending" and p["reason"] == "held_for_review"
    # holding never overwrites the stored value
    d = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    assert [(e["value"], e["state"]) for e in d["fields"]["modality"]] == [("ngs", "current")]
    assert d["rev"] == 1 and d["facets"]["modality"] == ["ngs"] and held.proposal_id not in d["applied_proposal_ids"]
    await ledger.apply_with(held.proposal_id, review="accepted", decided_by="sam")
    d = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    states = {e["value"]: e["state"] for e in d["fields"]["modality"]}
    assert states == {"ngs": "superseded", "pcr": "current"} and d["facets"]["modality"] == ["pcr"]


async def test_file_returns_one_decision_per_gated_change(world):
    from dxp.api.models import Decision

    w = world
    adm = await w.admit()
    out = await ledger.file("f_anchor", [scope_change(), mention_change(w)], "live", w.run_ctx(adm, report_id="rep_a"))
    assert [type(d) for d in out] == [Decision, Decision]
    assert [d.outcome for d in out] == ["allowed", "blocked"]


async def test_an_alias_created_in_a_live_run_never_resolves_as_an_fda_trade_name(world):
    """V34: only FDA trade names resolve; an alias a run creates is marked live."""
    from dxp.identity import resolve_exact
    from dxp.ledger import ensure_diagnostic

    w = world
    name = "Brand New Assay"
    dx_id = await ensure_diagnostic(name, w.run_ctx(None))
    alias = await w.db["aliases"].find_one({"_id": normalise_name(name)})
    assert alias["created_mode"] == "live" and alias["created_run_id"] == w.run_id
    assert await resolve_exact(name, aliases=w.db["aliases"]) is None
    assert (await w.db["diagnostics"].find_one({"_id": dx_id}))["created_mode"] == "live"
    # a seeded FDA trade name still resolves
    assert await resolve_exact("FoundationOne Liquid CDx", aliases=w.db["aliases"]) == w.dx_f1l


async def test_stage_not_later_at_apply_is_a_recorded_outcome(world):
    """AD-5: the stage moved on between filing and apply; apply records it, never raises."""
    w = world
    await w.db["diagnostics"].update_one({"_id": w.dx_f1l}, {"$set": {"lifecycle_stage": "discovery"}})
    adm = await w.admit()
    [r] = await ledger.file_detailed("f_stage", {"field": "lifecycle_stage", "value": "clinical_validation",
                                                 "diagnostic_id": w.dx_f1l, "evidence": EVIDENCE, "check": GOOD},
                                     "live", w.run_ctx(adm))
    assert r.status == "filed"
    await w.db["diagnostics"].update_one({"_id": w.dx_f1l}, {"$set": {"lifecycle_stage": "regulatory_approval"}})
    before = await w.db["diagnostics"].find_one({"_id": w.dx_f1l})
    p = await ledger.apply(r.proposal_id)
    assert p.status == "rejected" and p.reason == "stage_not_later"
    assert await w.db["diagnostics"].find_one({"_id": w.dx_f1l}) == before
    assert await w.count("events", {"type": "value_applied"}) == 0
    [unknown] = await ledger.file_detailed("f_stage2", {"field": "lifecycle_stage", "value": "warp_speed",
                                                        "diagnostic_id": w.dx_f1l, "evidence": EVIDENCE,
                                                        "check": GOOD}, "live", w.run_ctx(adm))
    assert unknown.status == "not_filed"


async def test_the_ledger_writes_no_finding(world):
    w = world
    adm = await w.admit()
    await ledger.file("f_anchor", scope_change(), "live", w.run_ctx(adm, report_id="rep_a"))
    await ledger.file("f_seed", {"field": "biomarkers", "value": "EGFR", "diagnostic_id": w.dx_tissue,
                                 "evidence": EVIDENCE, "check": GOOD}, "baseline", w.seed_ctx())
    assert await w.count("findings") == 0
