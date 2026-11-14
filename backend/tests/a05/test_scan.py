"""discovery.scan (Story 10.1, AD-25): gate before request, versions, cursor, audit fields."""

from __future__ import annotations

import pytest

from dxp import discovery

from .conftest import RUN_ID, SCOPE_ID, scan_mod, scope_doc, study


def setup_results(ctgov_fake) -> None:
    ctgov_fake.pages = [[
        study("NCT02498613", "2026-11-13"),
        study("NCT04712877", "2026-11-12", interventions=[
            {"type": "DIAGNOSTIC_TEST", "name": "ctDNA, tumor NGS", "otherNames": ["FoundationOne CDx", "FoundationOne Liquid"]}]),
        study("NCT00000003", "2026-11-11"),
    ]]


async def test_allowed_scan_queries_stores_and_advances(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    setup_results(ctgov_fake)
    refs = await discovery.scan(SCOPE_ID, discover_run)

    # priority_refs first even though NCT02498613 is newer, then newest first
    assert refs == ["clinicaltrials.gov:NCT04712877", "clinicaltrials.gov:NCT02498613", "clinicaltrials.gov:NCT00000003"]
    # one admission, item key with the scan target
    assert fake_runs.admitted == [f"{SCOPE_ID}|search_source|-|{SCOPE_ID}|2026-11-11"]
    assert fake_runs.released == ["adm_0001"]
    # gate before the request, with the A06 inputs
    (ctx, action), = scan_gate.calls
    assert ctx.admission_id == "adm_0001"
    assert action.kind == "search_source" and action.destination == "source:clinicaltrials.gov"
    assert action.target.scope_id == SCOPE_ID and action.inputs["cursor"] == "2026-11-11"
    assert action.inputs["query"]["condition"] == "non-small cell lung cancer"
    assert action.inputs["query"]["terms"][:4] == scope_doc()["assays"]
    # the query (V2)
    (req,) = ctgov_fake.searches
    assert req.url.params["filter.advanced"] == "AREA[LastUpdatePostDate]RANGE[2026-11-11,MAX]"
    assert req.url.params["query.cond"] == '"non-small cell lung cancer" OR "NSCLC"'
    assert req.url.params["query.term"].startswith('"FoundationOne Liquid CDx" OR "Guardant360 CDx"')
    assert '"ctDNA"' in req.url.params["query.term"]
    # items: discovered, in scope, versioned, otherNames verbatim
    item = fakedb["source_items"].docs["clinicaltrials.gov:NCT04712877"]
    assert item["window"] == "discovered" and item["scope_ids"] == [SCOPE_ID]
    assert item["current_version_id"] in fakedb["source_versions"].docs
    assert item["interventions"][0]["otherNames"] == ["FoundationOne CDx", "FoundationOne Liquid"]
    assert item["source_date"] == "2026-11-12" and item["has_results"] is False
    # cursor advanced to the newest date seen, by the run
    cursor = fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]
    assert cursor["last_update_post_date"] == "2026-11-13" and cursor["set_by_run_id"] == RUN_ID
    assert fakedb["research_scopes"].docs[SCOPE_ID]["version"] == 2
    # action delivered with the result; run audit fields; scan_finished
    action_doc = fakedb["actions"].docs[scan_gate.action_ids[0]]
    assert action_doc["status"] == "delivered"
    assert action_doc["result"] == {"http_status": 200, "cursor_from": "2026-11-11", "cursor_to": "2026-11-13",
                                    "source_refs": refs, "count": 3}
    scan = fake_runs.scans[RUN_ID]  # through runs.record_scan, never a direct runs write
    assert scan["cursor_from"] == "2026-11-11" and scan["cursor_to"] == "2026-11-13" and scan["source_refs"] == refs
    assert scan["count"] == 3 and scan["complete"] and scan["cursor_advanced"]
    assert "scan" not in fakedb["runs"].docs[RUN_ID]
    assert [c[1] for c in fake_actions.calls] == ["dispatching", "delivered"]
    (fin,) = events.of("scan_finished")
    assert fin["cursor_from"] == "2026-11-11" and fin["cursor_to"] == "2026-11-13" and fin["cursor_advanced"]
    assert fin["source_refs"] == refs
    assert fin["order"] == {"rule": "priority_refs first, then last_update_post_date descending",
                            "priority_refs": ["NCT04712877"]}


async def test_blocked_scan_makes_no_request(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    scan_gate.blocked = True
    setup_results(ctgov_fake)
    assert await discovery.scan(SCOPE_ID, discover_run) == []
    assert ctgov_fake.requests == []
    assert len(scan_gate.calls) == 1 and len(fakedb["decisions"].docs) == 1
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    assert fakedb["source_items"].docs == {} and fakedb["actions"].docs == {}
    assert events.of("scan_finished") == []
    assert fake_runs.released == ["adm_0001"]


async def test_not_admitted_does_nothing(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    fake_runs.admitting = False
    assert await discovery.scan(SCOPE_ID, discover_run) == []
    assert scan_gate.calls == [] and ctgov_fake.requests == []


async def test_failed_scan_leaves_cursor(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    ctgov_fake.status = 500
    with pytest.raises(scan_mod.ScanError):
        await discovery.scan(SCOPE_ID, discover_run)
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    action = fakedb["actions"].docs[scan_gate.action_ids[0]]
    assert action["status"] == "failed" and action["result"]["http_status"] == 500
    assert fake_runs.released == ["adm_0001"]


async def test_stopped_run_leaves_cursor(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    setup_results(ctgov_fake)
    fakedb["runs"].docs[RUN_ID]["status"] = "stopping"
    refs = await discovery.scan(SCOPE_ID, discover_run)
    assert len(refs) == 3
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    assert fakedb["actions"].docs[scan_gate.action_ids[0]]["result"]["cursor_to"] == "2026-11-11"


async def test_incomplete_scan_leaves_cursor(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run, monkeypatch) -> None:
    ctgov_fake.pages = [[study("NCT02498613", "2026-11-13")], [study("NCT00000003", "2026-11-11")]]
    monkeypatch.setattr(scan_mod.ctgov, "MAX_PAGES", 1)
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert not outcome.complete and not outcome.cursor_advanced
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"


async def test_cursor_update_is_conditional_on_version(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    fakedb["research_scopes"].docs[SCOPE_ID] = scope_doc(version=3)
    setup_results(ctgov_fake)
    real_find = fakedb["research_scopes"].find_one

    async def find_then_race(*a, **k):
        doc = await real_find(*a, **k)
        fakedb["research_scopes"].docs[SCOPE_ID]["version"] = 4  # another writer moved it after our read
        return doc

    fakedb["research_scopes"].find_one = find_then_race
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert outcome.status == "done" and not outcome.cursor_advanced
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    assert fakedb["actions"].docs[scan_gate.action_ids[0]]["result"]["cursor_to"] == "2026-11-11"


async def test_changed_known_trial_is_a_new_version(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    from dxp.sources import ctgov, load

    first = await load.store_record(ctgov.parse_study(study("NCT04712877", "2026-10-01")), window="prior", set_name="prior")
    first_doc = dict(fakedb["source_versions"].docs[first.version_id])
    setup_results(ctgov_fake)
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert outcome.changed_refs == ["clinicaltrials.gov:NCT04712877"]
    item = fakedb["source_items"].docs["clinicaltrials.gov:NCT04712877"]
    assert item["current_version_id"] != first.version_id
    assert fakedb["source_versions"].docs[first.version_id] == first_doc


async def test_repeat_of_the_same_step_does_not_query_again(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run, monkeypatch) -> None:
    setup_results(ctgov_fake)
    refs = await discovery.scan(SCOPE_ID, discover_run)
    first_action = scan_gate.action_ids[0]

    async def same_decision(ctx, action):
        d = await type(scan_gate).evaluate(scan_gate, ctx, action)
        return d.model_copy(update={"action_id": first_action})

    monkeypatch.setattr(scan_mod.gate, "evaluate", same_decision)
    before = len(ctgov_fake.requests)
    assert await discovery.scan(SCOPE_ID, discover_run) == refs
    assert len(ctgov_fake.requests) == before


async def test_without_condition_aliases_the_condition_is_plain(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    doc = scope_doc()
    doc.pop("condition_aliases")
    fakedb["research_scopes"].docs[SCOPE_ID] = doc
    setup_results(ctgov_fake)
    await discovery.scan(SCOPE_ID, discover_run)
    assert ctgov_fake.searches[0].url.params["query.cond"] == "non-small cell lung cancer"


async def test_gate_judges_the_plain_condition(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    setup_results(ctgov_fake)
    await discovery.scan(SCOPE_ID, discover_run)
    assert scan_gate.calls[0][1].inputs["query"]["condition"] == "non-small cell lung cancer"


async def test_without_priority_refs_newest_first(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    doc = scope_doc()
    doc.pop("priority_refs")
    fakedb["research_scopes"].docs[SCOPE_ID] = doc
    setup_results(ctgov_fake)
    refs = await discovery.scan(SCOPE_ID, discover_run)
    assert refs[0] == "clinicaltrials.gov:NCT02498613"


async def test_scan_needs_a_run(fakedb, discover_run) -> None:
    with pytest.raises(ValueError):
        await discovery.scan(SCOPE_ID, discover_run.model_copy(update={"run_id": None}))


async def test_capped_search_never_moves_the_cursor(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    setup_results(ctgov_fake)
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run, max_results=5)
    assert outcome.complete and not outcome.cursor_advanced
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    assert scan_gate.calls[0][1].inputs["requested_count"] == 5


async def test_action_is_settled_before_the_cursor_moves(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    """Review item (e): the delivered settle happens before the cursor update."""
    setup_results(ctgov_fake)
    order: list[str] = []
    real_settle, real_update = fake_actions.record_source_result, fakedb["research_scopes"].update_one

    async def settle(action_id, *, status, result):
        order.append(f"settle:{status}")
        return await real_settle(action_id, status=status, result=result)

    async def update_one(*a, **k):
        order.append("cursor")
        return await real_update(*a, **k)

    scan_mod.actions.record_source_result = settle
    fakedb["research_scopes"].update_one = update_one
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert outcome.cursor_advanced
    assert order == ["settle:dispatching", "settle:delivered", "cursor"]


async def test_failed_settle_leaves_the_cursor(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    """Review item (e), Luis's probe: the settle fails; the cursor must not have moved while the
    action is still `dispatching`."""
    setup_results(ctgov_fake)
    real_settle = fake_actions.record_source_result

    async def settle(action_id, *, status, result):
        if status == "delivered":
            raise RuntimeError("settle failed")
        return await real_settle(action_id, status=status, result=result)

    scan_mod.actions.record_source_result = settle
    with pytest.raises(RuntimeError):
        await scan_mod.run_scan(SCOPE_ID, discover_run)
    scope = fakedb["research_scopes"].docs[SCOPE_ID]
    assert scope["cursor"]["last_update_post_date"] == "2026-11-11" and scope["version"] == 1
    assert fakedb["actions"].docs[scan_gate.action_ids[0]]["status"] == "dispatching"


async def test_unsettled_action_leaves_the_cursor(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    """Review item (e): the settle reports the action was not `dispatching` (False); no cursor move."""
    setup_results(ctgov_fake)
    real_settle = fake_actions.record_source_result

    async def settle(action_id, *, status, result):
        if status == "delivered":
            return False
        return await real_settle(action_id, status=status, result=result)

    scan_mod.actions.record_source_result = settle
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert not outcome.cursor_advanced
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
