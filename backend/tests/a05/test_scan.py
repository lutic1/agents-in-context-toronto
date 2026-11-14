"""discovery.scan (Story 10.1, AD-25): gate before request, versions, cursor, audit fields."""

from __future__ import annotations

import pytest

from dxp import discovery

from .conftest import RUN_ID, SCOPE_ID, scan_mod, scope_doc, study


def setup_results(ctgov_fake) -> None:
    ctgov_fake.pages = [[
        study("NCT00000002", "2026-11-13"),
        study("NCT04712877", "2026-11-12", interventions=[
            {"type": "DIAGNOSTIC_TEST", "name": "ctDNA, tumor NGS", "otherNames": ["FoundationOne CDx", "FoundationOne Liquid"]}]),
        study("NCT00000003", "2026-11-11"),
    ]]


async def test_allowed_scan_queries_stores_and_advances(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run, monkeypatch) -> None:
    monkeypatch.setenv("DXP_DEMO_ANCHOR", "NCT04712877")
    setup_results(ctgov_fake)
    refs = await discovery.scan(SCOPE_ID, discover_run)

    # anchor first, then newest first
    assert refs == ["clinicaltrials.gov:NCT04712877", "clinicaltrials.gov:NCT00000002", "clinicaltrials.gov:NCT00000003"]
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
    assert req.url.params["query.cond"] == "non-small cell lung cancer"
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
    action_doc = fakedb["actions"].docs["act_test000000000001"]
    assert action_doc["status"] == "delivered"
    assert action_doc["result"] == {"http_status": 200, "cursor_from": "2026-11-11", "cursor_to": "2026-11-13",
                                    "source_refs": refs, "count": 3}
    scan = fakedb["runs"].docs[RUN_ID]["scan"]
    assert scan["cursor_from"] == "2026-11-11" and scan["cursor_to"] == "2026-11-13" and scan["source_refs"] == refs
    (fin,) = events.of("scan_finished")
    assert fin["cursor_from"] == "2026-11-11" and fin["cursor_to"] == "2026-11-13" and fin["cursor_advanced"]
    assert [e["status"] for e in events.of("action_status_changed")] == ["dispatching", "delivered"]


async def test_blocked_scan_makes_no_request(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
    scan_gate.blocked = True
    setup_results(ctgov_fake)
    assert await discovery.scan(SCOPE_ID, discover_run) == []
    assert ctgov_fake.requests == []
    assert len(scan_gate.calls) == 1 and len(fakedb["decisions"].docs) == 1
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    assert fakedb["source_items"].docs == {} and fakedb["actions"].docs == {}
    assert events.of("scan_finished") == []
    assert fake_runs.released == ["adm_0001"]


async def test_not_admitted_does_nothing(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
    fake_runs.admitting = False
    assert await discovery.scan(SCOPE_ID, discover_run) == []
    assert scan_gate.calls == [] and ctgov_fake.requests == []


async def test_failed_scan_leaves_cursor(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
    ctgov_fake.status = 500
    with pytest.raises(scan_mod.ScanError):
        await discovery.scan(SCOPE_ID, discover_run)
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    action = fakedb["actions"].docs["act_test000000000001"]
    assert action["status"] == "failed" and action["result"]["http_status"] == 500
    assert fake_runs.released == ["adm_0001"]


async def test_stopped_run_leaves_cursor(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
    setup_results(ctgov_fake)
    fakedb["runs"].docs[RUN_ID]["status"] = "stopping"
    refs = await discovery.scan(SCOPE_ID, discover_run)
    assert len(refs) == 3
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"
    assert fakedb["actions"].docs["act_test000000000001"]["result"]["cursor_to"] == "2026-11-11"


async def test_incomplete_scan_leaves_cursor(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run, monkeypatch) -> None:
    ctgov_fake.pages = [[study("NCT00000002", "2026-11-13")], [study("NCT00000003", "2026-11-11")]]
    monkeypatch.setattr(scan_mod.ctgov, "MAX_PAGES", 1)
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert not outcome.complete and not outcome.cursor_advanced
    assert fakedb["research_scopes"].docs[SCOPE_ID]["cursor"]["last_update_post_date"] == "2026-11-11"


async def test_cursor_update_is_conditional_on_version(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
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


async def test_changed_known_trial_is_a_new_version(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
    from dxp.sources import ctgov, load

    first = await load.store_record(ctgov.parse_study(study("NCT04712877", "2026-10-01")), window="prior", set_name="prior")
    first_doc = dict(fakedb["source_versions"].docs[first.version_id])
    setup_results(ctgov_fake)
    outcome = await scan_mod.run_scan(SCOPE_ID, discover_run)
    assert outcome.changed_refs == ["clinicaltrials.gov:NCT04712877"]
    item = fakedb["source_items"].docs["clinicaltrials.gov:NCT04712877"]
    assert item["current_version_id"] != first.version_id
    assert fakedb["source_versions"].docs[first.version_id] == first_doc


async def test_repeat_of_the_same_step_does_not_query_again(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run, monkeypatch) -> None:
    setup_results(ctgov_fake)
    refs = await discovery.scan(SCOPE_ID, discover_run)

    async def same_decision(ctx, action):
        d = await type(scan_gate).evaluate(scan_gate, ctx, action)
        return d.model_copy(update={"action_id": "act_test000000000001"})

    monkeypatch.setattr(scan_mod.gate, "evaluate", same_decision)
    before = len(ctgov_fake.requests)
    assert await discovery.scan(SCOPE_ID, discover_run) == refs
    assert len(ctgov_fake.requests) == before


async def test_condition_aliases_widen_the_condition(fakedb, events, fake_runs, scan_gate, ctgov_fake, discover_run) -> None:
    fakedb["research_scopes"].docs[SCOPE_ID] = scope_doc(condition_aliases=["NSCLC"])
    setup_results(ctgov_fake)
    await discovery.scan(SCOPE_ID, discover_run)
    assert ctgov_fake.searches[0].url.params["query.cond"] == '"non-small cell lung cancer" OR "NSCLC"'
    assert scan_gate.calls[0][1].inputs["query"]["condition"] == "non-small cell lung cancer"


async def test_scan_needs_a_run(fakedb, discover_run) -> None:
    with pytest.raises(ValueError):
        await discovery.scan(SCOPE_ID, discover_run.model_copy(update={"run_id": None}))
