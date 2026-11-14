"""Source versions (V40) and the prior collection (Story 1.4), on the in-memory store."""

from __future__ import annotations

import json

from dxp.sources import ctgov, load

from .conftest import SCOPE_ID, scope_doc, study


def rec(nct: str, lupd: str, summary: str = "A test summary.") -> dict:
    return ctgov.parse_study(study(nct, lupd, summary=summary))


async def test_first_fetch_writes_version_and_pointer(fakedb) -> None:
    s = await load.store_record(rec("NCT00000001", "2026-10-01"), window="prior", set_name="prior", scope_id=SCOPE_ID)
    assert s.new_version and s.moved and s.previous_version_id is None and not s.changed
    assert s.version_id == load.version_id_for("clinicaltrials.gov:NCT00000001", "2026-10-01", rec("NCT00000001", "2026-10-01")["content_hash"])
    item = fakedb["source_items"].docs["clinicaltrials.gov:NCT00000001"]
    assert item["current_version_id"] == s.version_id
    assert item["window"] == "prior" and item["sets"] == ["prior"] and item["scope_ids"] == [SCOPE_ID]
    assert item["source_date"] == "2026-10-01" and item["overall_status"] == "RECRUITING" and item["has_results"] is False
    v = fakedb["source_versions"].docs[s.version_id]
    assert v["raw_text"] == item["raw_text"] and v["previous_version_id"] is None


async def test_same_record_twice_changes_nothing(fakedb) -> None:
    r = rec("NCT00000001", "2026-10-01")
    first = await load.store_record(r, window="prior", set_name="prior", scope_id=SCOPE_ID)
    before = dict(fakedb["source_versions"].docs)
    second = await load.store_record(r, window="prior", set_name="prior", scope_id=SCOPE_ID)
    assert second.version_id == first.version_id and not second.new_version and not second.moved
    assert fakedb["source_versions"].docs == before
    assert fakedb["source_items"].docs["clinicaltrials.gov:NCT00000001"]["sets"] == ["prior"]


async def test_changed_record_writes_second_version_and_keeps_first(fakedb) -> None:
    first = await load.store_record(rec("NCT00000001", "2026-10-01"), window="prior", set_name="prior")
    first_doc = dict(fakedb["source_versions"].docs[first.version_id])
    second = await load.store_record(
        rec("NCT00000001", "2026-11-12", summary="Changed."), window="discovered", set_name="discover", scope_id=SCOPE_ID)
    assert second.version_id != first.version_id and second.changed
    assert fakedb["source_versions"].docs[first.version_id] == first_doc  # never overwritten
    assert fakedb["source_versions"].docs[second.version_id]["previous_version_id"] == first.version_id
    item = fakedb["source_items"].docs["clinicaltrials.gov:NCT00000001"]
    assert item["current_version_id"] == second.version_id and item["window"] == "discovered"
    assert set(item["sets"]) == {"prior", "discover"}


async def test_same_date_new_content_is_a_new_version(fakedb) -> None:
    a = await load.store_record(rec("NCT00000001", "2026-10-01"), window="prior", set_name="prior")
    b = await load.store_record(rec("NCT00000001", "2026-10-01", summary="Edited."), window="prior", set_name="prior")
    assert a.version_id != b.version_id and b.moved


async def test_older_fetch_never_moves_pointer_back(fakedb) -> None:
    new = await load.store_record(rec("NCT00000001", "2026-11-12", "New."), window="discovered", set_name="discover")
    old = await load.store_record(rec("NCT00000001", "2026-10-01", "Old."), window="discovered", set_name="discover")
    assert not old.moved
    assert fakedb["source_items"].docs["clinicaltrials.gov:NCT00000001"]["current_version_id"] == new.version_id
    assert old.version_id in fakedb["source_versions"].docs


def test_manifest_is_the_d30_list() -> None:
    data = load.manifest()
    assert len(data["nct_ids"]) == 20 and len(set(data["nct_ids"])) == 20
    assert data["nct_ids"][0] == "NCT04712877" and data["setup_item"] == "NCT05715229"
    assert "NCT05715229" in data["nct_ids"]
    raw = json.loads(load.MANIFEST.read_text())
    assert set(raw) == {"//", "setup_item", "nct_ids"}


async def test_prior_loads_only_before_cursor_and_reports_failures(fakedb, ctgov_fake) -> None:
    fakedb["research_scopes"].docs[SCOPE_ID] = scope_doc("2026-11-01")
    ids = ["NCT04712877", "NCT00000002", "NCT05715229", "NCT00000003", "NCT00000004"]
    ctgov_fake.studies = {
        "NCT04712877": study("NCT04712877", "2026-11-12"),  # after the cursor: left for the scan
        "NCT00000002": study("NCT00000002", "2026-10-31"),
        "NCT05715229": study("NCT05715229", "2025-01-01"),  # setup item: excluded
        "NCT00000003": study("NCT00000003", "2026-11-01"),  # on the cursor: left for the scan
    }  # NCT00000004 is missing: 404
    res = await load.load_prior(SCOPE_ID, nct_ids=ids)
    assert [s.source_ref for s in res.loaded] == ["clinicaltrials.gov:NCT00000002"]
    assert {n for n, _ in res.left_for_scan} == {"NCT04712877", "NCT00000003"}
    assert res.excluded == ["NCT05715229"]
    assert set(res.failed) == {"NCT00000004"}
    assert res.accounted == res.manifest_count == 5
    assert "5 of 5 in the manifest" in res.lines()[-1]
    assert list(fakedb["source_items"].docs) == ["clinicaltrials.gov:NCT00000002"]
    # no fetch for the setup item
    assert not any(r.url.path.endswith("NCT05715229") for r in ctgov_fake.requests)
    # twice: nothing new
    versions = dict(fakedb["source_versions"].docs)
    again = await load.load_prior(SCOPE_ID, nct_ids=ids)
    assert fakedb["source_versions"].docs == versions and not again.loaded[0].moved


async def test_setup_item_window(fakedb, ctgov_fake) -> None:
    ctgov_fake.studies = {"NCT05715229": study("NCT05715229", "2025-01-01", status="TERMINATED")}
    s = await load.load_nct("NCT05715229")
    item = fakedb["source_items"].docs[s.source_ref]
    assert item["window"] == "setup" and item["sets"] == ["nct:NCT05715229"] and item["overall_status"] == "TERMINATED"
