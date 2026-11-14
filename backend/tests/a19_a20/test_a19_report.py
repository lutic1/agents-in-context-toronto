"""reports.draft, reports.file, reports.add_related and the report routes, on a fixture of
NCT04712877 written for these tests. The model, the gate, the ledger and the Slack dispatch
are fakes; nothing here reaches a network or a database."""

import importlib

import pytest

from dxp import identity, reports
from dxp.api.models import Action, Memory, Principal, ProposedAction, RunContext, Stamp, Target

draft_module = importlib.import_module("dxp.reports.draft")
file_module = importlib.import_module("dxp.reports.file")
script_module = importlib.import_module("dxp.reports.script")

RUN = "run_demo"
SCOPE = "scope_plasma_ctdna"
TEAM = "team_lbdx"
REF = "ctgov:NCT04712877"
VERSION = "sv_aaaaaaaaaaaaaaaa"
DX_TISSUE = "dx_1111111111111111"
HEADLINE = ("This study investigates molecular profiling using blood (ctDNA) and tumour tissue in "
            "early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. "
            "No results posted.")
GAP = "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"
AMBIGUOUS = ("The trial's intervention field is ambiguous: it lists assay names as alternate names of "
             "a generic ctDNA and tumour NGS intervention, and does not say which assay was used for "
             "which sample.")
UNRESOLVED = ("The record names 'FoundationOne Liquid'. Whether this is the FDA-approved "
              "FoundationOne Liquid CDx is not stated.")
RAW = ("Brief title: Molecular profiling in early-stage lung cancer before surgery. "
       "Patients with stage IA2 to III non-small cell lung cancer have blood and tumour tissue "
       "collected for molecular profiling before surgery. Overall status: RECRUITING. "
       "Intervention: ctDNA, tumor NGS. Other names: FoundationOne CDx; FoundationOne Liquid.")
Q_DESIGN = "have blood and tumour tissue collected for molecular profiling before surgery"
Q_STAGE = "stage IA2 to III non-small cell lung cancer"


def item(**changes):
    base = {
        "source_ref": REF, "version_id": VERSION, "nct_id": "NCT04712877", "run_id": RUN,
        "scope_id": SCOPE, "team_id": TEAM, "raw_text": RAW,
        "title": "Molecular profiling in early-stage lung cancer before surgery",
        "overall_status": "RECRUITING", "has_results": False,
        "conditions": ["non-small cell lung cancer"],
        "interventions": [{"type": "DIAGNOSTIC_TEST", "name": "ctDNA, tumor NGS",
                           "otherNames": ["FoundationOne CDx", "FoundationOne Liquid"]}],
        "seeded_names": ["FoundationOne CDx", "FoundationOne Liquid CDx", "Guardant360 CDx", "Agilent Resolution ctDx FIRST"],
        "retrieval": {"method": "vector_search", "index": "vs_source_items+vs_findings", "top_k": 5,
                      "filter": {"scope_id": SCOPE},
                      "items": [{"ref": "ctgov:NCT00000001", "version_id": "sv_bbbbbbbbbbbbbbbb", "score": 0.83}]},
    }
    base.update(changes)
    return base


def findings():
    mentions = [
        {"name": "FoundationOne CDx", "field": "interventions[0].otherNames[0]", "resolved_diagnostic_id": DX_TISSUE},
        {"name": "FoundationOne Liquid", "field": "interventions[0].otherNames[1]", "resolved_diagnostic_id": None},
    ]
    return [
        {"id": "f_aaaaaaaaaaaaaaaa", "source_ref": REF, "version_id": VERSION, "diagnostic_id": None,
         "target": "scope_collection", "mentions": mentions, "trial_status": "RECRUITING", "has_results": False,
         "summary": "A study of blood and tumour tissue profiling before surgery in early-stage lung cancer.",
         "values": [{"field": "tumour_types", "raw": "non-small cell lung cancer", "value": "nsclc",
                     "label": "NSCLC", "quote": Q_STAGE,
                     "check": {"quote_found": True, "supported": True, "confidence": 0.9}}]},
        {"id": "f_bbbbbbbbbbbbbbbb", "source_ref": REF, "version_id": VERSION, "diagnostic_id": DX_TISSUE,
         "target": "diagnostic", "mentions": [mentions[0]], "summary": "", "values": []},
    ]


def related():
    return [{
        "id": "rel_0000000000000000", "related_ref": "ctgov:NCT00000001", "related_kind": "source_item",
        "related_title": "Plasma ctDNA genotyping in advanced NSCLC", "label": "extends",
        "rationale": "The new trial moves blood-based profiling to an earlier-stage setting.",
        "new_quote": {"source_ref": REF, "version_id": VERSION, "text": Q_STAGE, "quote_found": True},
        "related_quote": {"source_ref": "ctgov:NCT00000001", "version_id": "sv_bbbbbbbbbbbbbbbb",
                          "text": "advanced non-small cell lung cancer", "quote_found": True},
        "similarity": 0.83, "retrieval_method": "vector_search", "origin": "discovery", "status": "pending",
    }]


M1 = Memory(id="mem_1111111111111111", version=1, team_id=TEAM, author="sam",
            source={"decision_id": "dec_0000000000000001", "report_id": "rep_0000000000000001"},
            text="Do not state an outcome when the trial has no posted results; say that no results are posted.",
            tags={"assay": "Guardant360 CDx", "claim_kind": "outcome_claim_without_results"}, status="active")

TASK = {"condition": "non-small cell lung cancer", "stage": "early", "testing": ["ctDNA or plasma", "tissue profiling"]}
SHOWED = "The trial showed that blood profiling finds actionable drivers."
INVESTIGATES = "The trial investigates whether blood and tissue profiling find actionable drivers; no results posted."
ANSWER_1 = {
    "headline": "This study investigates blood and tumour tissue profiling in early-stage lung cancer.",
    "summary": SHOWED + " It is recruiting.",
    "claims": [{"text": SHOWED, "claim_kind": "claim_performed_or_results", "quote": Q_DESIGN},
               {"text": "It is recruiting.", "claim_kind": "claim_planned", "quote": "Overall status: RECRUITING"}],
    "gap": GAP, "task": TASK, "intervention_plain": "ctDNA and tumour NGS",
    "collection_label": "early-stage plasma-plus-tissue profiling study",
}
ANSWER_2 = {
    "headline": HEADLINE,
    "summary": INVESTIGATES + " It is recruiting.",
    "claims": [{"text": INVESTIGATES, "claim_kind": "claim_planned", "quote": Q_DESIGN},
               {"text": "It is recruiting.", "claim_kind": "claim_planned", "quote": "Overall status: RECRUITING"}],
    "gap": GAP, "task": TASK, "intervention_plain": "ctDNA and tumour NGS",
    "collection_label": "early-stage plasma-plus-tissue profiling study",
}


def context(run_id=RUN):
    return RunContext(
        run_id=run_id, principal=Principal(id="dxp-curator", name="DxP curator", kind="agent"),
        stamp=Stamp(kind="run", run_id=run_id, principal="dxp-curator", agent="dxp-curator", initiated_by="sam",
                    grant_id="lbdx", grant_version=1),
        grant_id="lbdx", grant_version=1,
    )


@pytest.fixture
def world(monkeypatch, mongo, fake_gate):
    """The model, quote check, gate rules, ledger and Slack dispatch, all in memory."""
    import dxp.actions
    import dxp.evidence
    import dxp.gate
    import dxp.ledger
    import dxp.llm

    class World:
        answers = [ANSWER_1, ANSWER_2]
        llm_calls = []
        ledger_calls = []
        dispatched = []
        dispatch_error = None
        block_showed = True

    w = World()
    w.llm_calls, w.ledger_calls, w.dispatched = [], [], []
    w.mongo, w.gate = mongo, fake_gate

    async def call_structured(model, schema, messages):
        w.llm_calls.append(messages)
        answer = w.answers[min(len(w.llm_calls), len(w.answers)) - 1]
        if isinstance(answer, Exception):
            raise answer
        return answer

    plain_evaluate = fake_gate.evaluate

    async def evaluate(ctx, action):
        """Stands in for the gate's checks: a claim that says "showed" with no posted results
        fails check 4; a Diagnostic outside the scope fails check 2."""
        fake_gate.blocked = {}
        texts = " ".join(c.get("text", "") for c in action.inputs.get("claims") or [])
        if w.block_showed and "showed" in texts and not (action.inputs.get("source_fields") or {}).get("has_results"):
            fake_gate.blocked = {action.kind: "evidence_checks"}
        if action.target.diagnostic_id == DX_TISSUE:
            fake_gate.blocked = {action.kind: "team_scope"}
        if action.inputs.get("item_scope_ids") == []:
            fake_gate.blocked = {action.kind: "team_scope"}
        return await plain_evaluate(ctx, action)

    async def ledger_file(finding_id, changes, mode, ctx):
        decisions = []
        for change in changes:
            w.ledger_calls.append((finding_id, change, mode))
            decision = await dxp.gate.evaluate(ctx, ProposedAction(
                kind="file_proposal", destination="ledger",
                target=Target(diagnostic_id=change.get("diagnostic_id"), scope_id=change.get("scope_id")),
                inputs={"mention": change.get("mention"), "field": change["field"], "value": change["value"]}))
            decisions.append(decision)
            if decision.outcome == "allowed":
                proposal_id = identity.derive("p_", finding_id, change["field"], change["value"])
                if not await mongo["proposals"].find_one({"_id": proposal_id}):
                    await mongo["proposals"].insert_one({
                        "_id": proposal_id, "report_id": change["report_id"], "status": "pending",
                        "diagnostic_id": change.get("diagnostic_id"), "field": change["field"],
                        "value": change["value"], "evidence": change["evidence"]})
        return decisions

    async def dispatch(action, ctx):
        w.dispatched.append(action)
        if w.dispatch_error:
            raise w.dispatch_error
        action_id = f"act_{len(w.dispatched):016d}"
        await mongo["actions"].insert_one({
            "_id": action_id, "kind": action.kind, "status": "delivered",
            "target": {"report_id": action.target.report_id}, "result": {"http_status": 200}})
        return Action(id=action_id, decision_id="dec_x", kind=action.kind, destination=action.destination,
                      stamp=ctx.stamp, status="delivered")

    monkeypatch.setattr(dxp.llm, "call_structured", call_structured)
    monkeypatch.setattr(dxp.evidence, "quote_in_source", lambda quote, raw_text: quote in raw_text, raising=False)
    monkeypatch.setattr(dxp.gate, "evaluate", evaluate)
    monkeypatch.setattr(dxp.ledger, "file", ledger_file)
    monkeypatch.setattr(dxp.actions, "dispatch", dispatch)
    return w


async def demo_draft(world, memories=(M1,)):
    return await reports.draft(item(), findings(), related(), list(memories))


# ----------------------------------------------------------------------- reports.draft

async def test_draft_writes_two_drafts_and_returns_the_report_fields(world):
    d = await demo_draft(world)
    assert d["draft"] == 2 and [x["draft"] for x in d["drafts"]] == [1, 2]
    assert len(world.llm_calls) == 2
    assert "Reviewer guidance" not in world.llm_calls[0][1]["content"]
    assert M1.text in world.llm_calls[1][1]["content"]
    assert d["headline"] == HEADLINE
    assert d["gap"] == GAP
    assert d["status_line"] == "Recruiting; no results posted"
    assert (d["source_ref"], d["version_id"], d["nct_id"], d["scope_id"], d["team_id"]) == (
        REF, VERSION, "NCT04712877", SCOPE, TEAM)
    assert d["discovery"]["trial_status"] == "RECRUITING" and d["discovery"]["has_results"] is False
    assert d["retrieval"]["method"] == "vector_search"


async def test_draft_keeps_the_intervention_wording_verbatim_and_lists_names_as_mentions(world):
    d = await demo_draft(world)
    assert d["discovery"]["intervention_text"] == "ctDNA, tumor NGS"
    assert d["discovery"]["mentions"] == [
        {"name": "FoundationOne CDx", "resolved_diagnostic_id": DX_TISSUE, "field": "interventions[0].otherNames[0]"},
        {"name": "FoundationOne Liquid", "resolved_diagnostic_id": None, "field": "interventions[0].otherNames[1]"},
    ]
    assert [m["description"] for m in d["name_mentions"]] == ["named in the record"] * 2
    assert "FoundationOne Liquid CDx" not in [m["name"] for m in d["discovery"]["mentions"]]


async def test_draft_lists_the_two_uncertainties_and_the_status(world):
    d = await demo_draft(world)
    assert d["uncertainties"] == ["Recruiting; no results posted.", AMBIGUOUS, UNRESOLVED]


async def test_draft_names_one_gap_and_the_task_that_answers_it(world):
    d = await demo_draft(world)
    assert d["gap"].count("?") == 1
    assert d["recommended_task"] == {"kind": "search_related", "params": {
        "condition": "non-small cell lung cancer", "stage": "early",
        "testing": ["ctDNA or plasma", "tissue profiling"], "has_results": True, "max": 5}}


async def test_draft_proposes_the_collection_update_and_the_mention_link(world):
    d = await demo_draft(world)
    collection, link = d["updates"]
    assert collection["finding_id"] == "f_aaaaaaaaaaaaaaaa"
    assert collection["change"] == {
        "field": "evidence_collection", "value": REF, "label": "early-stage plasma-plus-tissue profiling study",
        "diagnostic_id": None, "scope_id": SCOPE, "trigger": "discovery",
        "evidence": {"source_ref": REF, "version_id": VERSION, "quote": Q_STAGE},
        "check": {"quote_found": True, "supported": True, "confidence": 0.9}}
    assert link["finding_id"] == "f_bbbbbbbbbbbbbbbb"
    assert link["change"]["diagnostic_id"] == DX_TISSUE
    assert link["change"]["mention"] == {"name": "FoundationOne CDx", "field": "interventions[0].otherNames[0]"}
    assert link["change"]["label"] == "named in the record"
    assert link["change"]["check"]["supported"] is False  # a mention is never proof of use
    assert link["change"]["evidence"]["version_id"] == VERSION


async def test_draft_records_each_memory_effect_from_the_two_real_drafts(world):
    d = await demo_draft(world)
    assert d["memories_used"] == [{
        "memory_id": "mem_1111111111111111", "version": 1, "author": "sam", "score": None,
        "source": {"decision_id": "dec_0000000000000001", "report_id": "rep_0000000000000001"},
        "effect": {"target": "sentence", "before": SHOWED, "after": INVESTIGATES},
    }]


async def test_a_memory_that_changes_nothing_is_retrieved_no_change(world):
    world.answers = [ANSWER_2, ANSWER_2]
    d = await demo_draft(world)
    assert d["memories_used"][0]["effect"] is None


async def test_without_memories_there_is_one_draft_and_one_model_call(world):
    world.answers = [ANSWER_2]
    d = await demo_draft(world, memories=())
    assert d["draft"] == 1 and len(d["drafts"]) == 1 and len(world.llm_calls) == 1
    assert d["memories_used"] == []


async def test_draft_quotes_are_checked_against_the_version_and_pinned(world):
    world.answers = [ANSWER_2, dict(ANSWER_2, claims=[
        {"text": INVESTIGATES, "claim_kind": "claim_planned", "quote": "a passage the record does not contain"}])]
    d = await demo_draft(world)
    assert d["discovery"]["quotes"] == [
        {"text": "a passage the record does not contain", "quote_found": False, "version_id": VERSION}]


async def test_draft_never_says_uses_studies_or_showed_about_a_name(world):
    bad = dict(ANSWER_2,
               headline="This study uses FoundationOne CDx in early-stage lung cancer.",
               summary="The trial studies FoundationOne Liquid. It is recruiting.",
               claims=[{"text": "FoundationOne CDx showed high concordance.", "claim_kind": "claim_design", "quote": Q_DESIGN}],
               gap="Have studies using FoundationOne CDx posted results?",
               intervention_plain="FoundationOne CDx testing", collection_label="FoundationOne CDx study")
    world.answers = [bad, bad]
    d = await demo_draft(world)
    assert draft_module.report_wording_flags(d) == []
    assert d["headline"] == "New trial signal: Molecular profiling in early-stage lung cancer before surgery. No results posted."
    assert d["discovery"]["summary"] == "It is recruiting."
    assert d["claims"] == []
    assert "FoundationOne" not in d["gap"] and "FoundationOne" not in d["updates"][0]["change"]["label"]
    assert 'a generic "ctDNA, tumor NGS" intervention' in d["uncertainties"][1]


@pytest.mark.parametrize("answer", [RuntimeError("overloaded"), None, "refused"])
async def test_a_model_failure_still_yields_a_draft_from_the_records_own_fields(world, answer):
    world.answers = [answer, answer]
    d = await demo_draft(world)
    assert d["headline"].endswith("No results posted.") and d["gap"].endswith("?")
    assert d["discovery"]["summary"] == findings()[0]["summary"]
    assert d["uncertainties"][0] == "Recruiting; no results posted." and UNRESOLVED in d["uncertainties"]
    assert d["memories_used"][0]["effect"] is None
    assert d["updates"][0]["change"]["field"] == "evidence_collection"


async def test_an_unresolved_name_with_no_seeded_candidate_is_still_an_uncertainty(world):
    d = await reports.draft(item(seeded_names=["Guardant360 CDx"]), findings(), [], [])
    assert "The record names 'FoundationOne Liquid'. It matches no FDA-listed companion diagnostic name exactly." in d["uncertainties"]


async def test_draft_reads_the_pinned_source_version_when_the_item_has_no_text(world):
    world.mongo["source_versions"].add({"_id": VERSION, "source_ref": REF, "raw_text": RAW, "overall_status": "RECRUITING",
                                        "has_results": False, "interventions": item()["interventions"]})
    bare = {k: v for k, v in item().items() if k not in ("raw_text", "overall_status", "has_results", "interventions")}
    d = await reports.draft(bare, findings(), related(), [M1])
    assert d["discovery"]["intervention_text"] == "ctDNA, tumor NGS"
    assert d["discovery"]["quotes"][0]["quote_found"] is True


# ------------------------------------------------------------------------ reports.file

REPORT_ID = identity.derive("rep_", RUN, REF)


async def filed(world, **kwargs):
    d = await demo_draft(world, **kwargs)
    decision = await reports.file(d, context())
    return d, decision, await world.mongo["reports"].find_one({"_id": REPORT_ID})


async def test_file_gates_both_drafts_and_files_draft_two_as_pending(world):
    d, decision, doc = await filed(world)
    report_level = [(a.inputs["id_target"], a.kind) for _, a in world.gate.calls if a.target.report_id and "draft" in a.inputs]
    assert report_level == [(f"{REPORT_ID}|draft1", "file_proposal"), (f"{REPORT_ID}|draft2", "file_proposal")]
    assert decision.outcome == "allowed"
    assert doc["status"] == "pending" and doc["draft"] == 2
    assert doc["run_id"] == RUN and doc["_id"] == REPORT_ID
    assert doc["file_decision_id"] == decision.id
    assert doc["blocked_draft_decision_id"] == "dec_fake000000000001"
    assert doc["stamp"]["kind"] == "run" and doc["stamp"]["principal"] == "dxp-curator"
    assert doc["created_at"] is not None
    assert doc["headline"] == HEADLINE and doc["gap"] == GAP
    assert doc["uncertainties"] == ["Recruiting; no results posted.", AMBIGUOUS, UNRESOLVED]
    assert doc["memories_used"][0]["effect"] == {"target": "sentence", "before": SHOWED, "after": INVESTIGATES}


async def test_the_gate_sees_claims_source_fields_retrieval_and_memories(world):
    await filed(world)
    first, second = [a for _, a in world.gate.calls if "draft" in a.inputs]
    assert first.destination == "ledger" and first.target.scope_id == SCOPE and first.target.diagnostic_id is None
    assert {"claim_kind": "claim_performed_or_results", "text": SHOWED, "quote": Q_DESIGN} in first.inputs["claims"]
    assert first.inputs["source_fields"] == {"overall_status": "RECRUITING", "has_results": False}
    assert first.evidence_ref.version_id == VERSION and first.evidence_ref.source_ref == REF
    assert first.memories_used == [] and first.retrieval.method == "vector_search"
    assert second.memories_used[0].memory_id == "mem_1111111111111111"
    assert HEADLINE.split(". ")[0] + "." in [c["text"] for c in second.inputs["claims"]]
    assert all(q["version_id"] == VERSION for q in second.inputs["checked_quotes"])


async def test_only_the_evidence_collection_update_is_filed_and_the_mention_link_is_blocked(world):
    _, _, doc = await filed(world)
    assert [(f, c["field"], c["report_id"], m) for f, c, m in world.ledger_calls] == [
        ("f_aaaaaaaaaaaaaaaa", "evidence_collection", REPORT_ID, "live"),
        ("f_bbbbbbbbbbbbbbbb", "trials", REPORT_ID, "live")]
    proposals = world.mongo["proposals"].docs
    assert [(p["field"], p["status"], p["diagnostic_id"]) for p in proposals] == [("evidence_collection", "pending", None)]
    assert doc["proposal_ids"] == [proposals[0]["_id"]]
    assert doc["diagnostic_ids"] == []
    blocked = [(c, a) for c, a in world.gate.calls if a.target.diagnostic_id == DX_TISSUE]
    assert len(blocked) == 1 and blocked[0][1].inputs["mention"]["name"] == "FoundationOne CDx"


async def test_an_allowed_report_gets_exactly_one_notify_slack_action_and_one_event(world):
    _, decision, doc = await filed(world)
    assert len(world.dispatched) == 1
    action = world.dispatched[0]
    assert action.kind == "notify_slack" and action.destination == "slack:#all-mango-db-hackathon"
    assert action.target.report_id == REPORT_ID and action.inputs["script_hash"] == doc["script_hash"]
    assert [(e["type"], e["report_id"], e["decision_id"], e["run_id"]) for e in world.mongo.events] == [
        ("report_filed", REPORT_ID, decision.id, RUN)]


async def test_a_report_with_two_updates_files_two_pending_proposals_and_one_notification(world):
    d = await demo_draft(world)
    extra = {"finding_id": "f_cccccccccccccccc", "change": {
        "field": "sample_types", "value": "plasma", "label": "Plasma", "diagnostic_id": "dx_2222222222222222",
        "evidence": {"source_ref": REF, "version_id": VERSION, "quote": Q_DESIGN},
        "check": {"quote_found": True, "supported": True, "confidence": 0.9}}}
    d["updates"] = [d["updates"][0], extra]
    await reports.file(d, context())
    doc = await world.mongo["reports"].find_one({"_id": REPORT_ID})
    assert [p["status"] for p in world.mongo["proposals"].docs] == ["pending", "pending"]
    assert len(doc["proposal_ids"]) == 2 and doc["diagnostic_ids"] == ["dx_2222222222222222"]
    assert all(p["evidence"]["version_id"] == VERSION for p in world.mongo["proposals"].docs)
    assert len(world.dispatched) == 1


async def test_every_filed_report_carries_a_script_holding_only_its_own_facts(world):
    _, _, doc = await filed(world)
    assert doc["script"] == HEADLINE + " Recruiting; no results posted. Evidence gap: " + GAP
    assert doc["script_hash"] == script_module.script_hash(doc["script"])
    assert doc["script"] == reports.script_for(doc)
    for absent in ("FoundationOne", "CDx", "NCT04712877", "tumor NGS"):
        assert absent not in doc["script"]
    assert script_module.shortening_problems(doc["script"], doc) == []


async def test_the_filed_report_has_no_uses_studies_or_showed_wording_about_either_name(world):
    _, _, doc = await filed(world)
    assert draft_module.report_wording_flags(doc) == []
    assert doc["discovery"]["intervention_text"] == "ctDNA, tumor NGS"
    assert [m["name"] for m in doc["discovery"]["mentions"]] == ["FoundationOne CDx", "FoundationOne Liquid"]


async def test_the_report_pins_its_version_on_quotes_relationships_and_retrieval(world):
    _, _, doc = await filed(world)
    assert doc["version_id"] == VERSION
    assert all(q["version_id"] == VERSION for q in doc["discovery"]["quotes"])
    relationship = doc["related"][0]
    assert relationship["new_quote"]["version_id"] == VERSION
    assert relationship["related_quote"]["version_id"] == "sv_bbbbbbbbbbbbbbbb"
    assert relationship["_id"] == relationship["id"] == identity.derive("rel_", REPORT_ID, REF, "ctgov:NCT00000001")
    assert (relationship["label"], relationship["similarity"], relationship["status"]) == ("extends", 0.83, "pending")
    assert doc["retrieval"]["items"][0]["version_id"] == "sv_bbbbbbbbbbbbbbbb"
    assert "raw_text" not in str(doc)


async def test_a_blocked_report_writes_nothing_but_its_decision(world):
    world.answers = [ANSWER_1, ANSWER_1]  # the unsupported claim survives into draft 2
    d = await demo_draft(world)
    decision = await reports.file(d, context())
    assert decision.outcome == "blocked" and decision.failed_check == "evidence_checks"
    assert len(world.gate.calls) == 2  # one Decision per draft; no change was gated
    assert world.mongo["reports"].docs == [] and world.mongo["proposals"].docs == []
    assert world.ledger_calls == [] and world.dispatched == [] and world.mongo.events == []


async def test_an_allowed_first_draft_leaves_no_blocked_draft_decision(world):
    world.block_showed = False
    _, _, doc = await filed(world)
    assert doc["draft"] == 2 and doc["blocked_draft_decision_id"] is None


async def test_a_single_draft_is_filed_as_draft_one(world):
    world.answers = [ANSWER_2]
    _, decision, doc = await filed(world, memories=())
    assert decision.outcome == "allowed" and doc["draft"] == 1 and doc["memories_used"] == []
    assert len([a for _, a in world.gate.calls if "draft" in a.inputs]) == 1


async def test_filing_again_keeps_one_report_one_proposal_and_one_notification(world):
    d, _, _ = await filed(world)
    await reports.file(d, context())
    assert len(world.mongo["reports"].docs) == 1 and len(world.mongo["proposals"].docs) == 1
    assert len(world.dispatched) == 1 and len(world.mongo.events) == 1


async def test_a_failed_slack_dispatch_never_blocks_the_report(world):
    world.dispatch_error = TimeoutError("slack timed out")
    _, decision, doc = await filed(world)
    assert decision.outcome == "allowed" and doc["status"] == "pending"
    assert len(world.mongo["proposals"].docs) == 1


async def test_the_report_validates_against_the_frozen_shape(world):
    from dxp.api.models import Report

    _, _, doc = await filed(world)
    report = Report.model_validate({**doc, "id": doc["_id"]})
    assert report.recommended_task.params.max == 5 and report.discovery.mentions[0].field.endswith("otherNames[0]")


# ------------------------------------------------------------------ reports.add_related

TASK_ID = "task_1111111111111111"
TASK_RUN = identity.derive("run_", TASK_ID)
NEW_REF = "ctgov:NCT00000007"


async def task_world(world):
    await filed(world)
    world.mongo["tasks"].add({"_id": TASK_ID, "report_id": REPORT_ID, "run_id": TASK_RUN})
    world.mongo["source_versions"].add(
        {"_id": VERSION, "source_ref": REF, "raw_text": RAW},
        {"_id": "sv_7777777777777777", "source_ref": NEW_REF, "raw_text": "Plasma ctDNA with tissue profiling in resectable NSCLC."})
    world.mongo["source_items"].add({"_id": NEW_REF, "scope_ids": [SCOPE], "current_version_id": "sv_7777777777777777",
                                     "title": "Plasma and tissue profiling in resectable NSCLC"})
    world.answers = [{"label": "supports", "rationale": "Both combine blood and tissue profiling before surgery.",
                      "new_quote": Q_DESIGN, "related_quote": "Plasma ctDNA with tissue profiling"}]
    world.llm_calls.clear()


async def test_add_related_appends_pending_related_evidence_under_the_task(world):
    await task_world(world)
    decisions = await reports.add_related(REPORT_ID, [NEW_REF], context(TASK_RUN))
    assert [d.outcome for d in decisions] == ["allowed"]
    doc = await world.mongo["reports"].find_one({"_id": REPORT_ID})
    added = doc["related"][-1]
    assert len(doc["related"]) == 2 and doc["status"] == "pending"
    assert (added["related_ref"], added["origin"], added["status"], added["label"]) == (
        NEW_REF, f"task:{TASK_ID}", "pending", "supports")
    assert added["filed_by_decision_id"] == decisions[0].id
    assert added["related_quote"]["version_id"] == "sv_7777777777777777" and added["new_quote"]["version_id"] == VERSION
    assert added["_id"] == identity.derive("rel_", REPORT_ID, REF, NEW_REF)
    action = world.gate.calls[-1][1]
    assert action.kind == "file_related_evidence" and action.target.task_id == TASK_ID
    assert action.inputs["id_target"] == f"{TASK_ID}|{NEW_REF}" and action.inputs["filed_count"] == 0
    assert action.inputs["item_scope_ids"] == [SCOPE]
    assert world.mongo.events[-1]["type"] == "related_evidence_filed"
    assert world.mongo["proposals"].docs[0]["status"] == "pending"  # nothing became accepted knowledge


async def test_add_related_blocked_item_writes_nothing(world):
    await task_world(world)
    decisions = await reports.add_related(REPORT_ID, ["ctgov:NCT00000404"], context(TASK_RUN))
    assert [d.outcome for d in decisions] == ["blocked"]
    doc = await world.mongo["reports"].find_one({"_id": REPORT_ID})
    assert len(doc["related"]) == 1 and len(world.mongo.events) == 1


async def test_add_related_twice_adds_the_item_once(world):
    await task_world(world)
    await reports.add_related(REPORT_ID, [NEW_REF], context(TASK_RUN))
    await reports.add_related(REPORT_ID, [NEW_REF], context(TASK_RUN))
    doc = await world.mongo["reports"].find_one({"_id": REPORT_ID})
    assert len(doc["related"]) == 2
    assert world.gate.calls[-1][1].inputs["filed_count"] == 1


async def test_add_related_to_an_unknown_report_is_refused(world):
    with pytest.raises(LookupError):
        await reports.add_related("rep_0000000000000000", [NEW_REF], context(TASK_RUN))


# ------------------------------------------------------------------------------ routes

async def test_get_reports_lists_by_status_and_run(world, api_client):
    await filed(world)
    listing = api_client.get("/api/v1/reports", params={"status": "pending"}).json()
    assert [r["id"] for r in listing["items"]] == [REPORT_ID] and listing["next"] is None
    report = listing["items"][0]
    assert report["headline"] == HEADLINE and len(report["related"]) == 1 and len(report["memories_used"]) == 1
    assert api_client.get("/api/v1/reports", params={"status": "accepted"}).json()["items"] == []
    assert len(api_client.get("/api/v1/reports", params={"run_id": RUN}).json()["items"]) == 1
    assert api_client.get("/api/v1/reports", params={"run_id": "run_other"}).json()["items"] == []


async def test_get_report_returns_the_report_with_its_script_and_never_raw_text(world, api_client):
    _, _, doc = await filed(world)
    await world.mongo["reports"].update_one({"_id": REPORT_ID}, {"$set": {"raw_text": RAW, "status": "accepted"}})
    response = api_client.get(f"/api/v1/reports/{REPORT_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == REPORT_ID and body["status"] == "accepted" and "_id" not in body
    assert body["script"] == doc["script"] and body["script_hash"] == doc["script_hash"]
    assert body["related"][0]["id"].startswith("rel_") and "_id" not in body["related"][0]
    assert body["related"][0]["new_quote"]["text"] == Q_STAGE
    assert body["proposal_ids"] == doc["proposal_ids"] and body["version_id"] == VERSION
    assert body["notification"] == {"action_id": "act_0000000000000001", "status": "delivered", "posted_at": None}
    assert "raw_text" not in response.text and RAW not in response.text


def test_get_report_unknown_id_is_404_in_the_error_shape(mongo, api_client):
    response = api_client.get("/api/v1/reports/rep_0000000000000000")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Report rep_0000000000000000 not found."}}
