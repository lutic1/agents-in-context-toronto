"""A05 against the Atlas Sandbox, in the session's own test database (never dxp).

Skipped with the stated reason when MONGODB_URI is unset (tests/conftest.py)."""

from __future__ import annotations

import pytest

from dxp import discovery
from dxp.sources import ctgov, load

from .conftest import RUN_ID, FakeActions, ScanGate, run_doc, scan_mod, scope_doc, study

pytestmark = pytest.mark.atlas

A_SCOPE = "scope_a05_atlas_test"  # never the seeded scope, so other PRs' Atlas tests are untouched


async def _clean(db) -> None:
    refs = [f"clinicaltrials.gov:{n}" for n in ("NCT00000011", "NCT00000012", "NCT04712877")]
    await db["source_items"].delete_many({"_id": {"$in": refs}})
    await db["source_versions"].delete_many({"source_ref": {"$in": refs}})
    await db["research_scopes"].delete_many({"_id": A_SCOPE})
    await db["runs"].delete_many({"_id": RUN_ID})
    for name in ("actions", "decisions"):
        await db[name].delete_many({"run_id": RUN_ID})


async def test_versions_on_atlas(db) -> None:
    await _clean(db)
    a = await load.store_record(ctgov.parse_study(study("NCT00000011", "2026-10-01")), window="prior", set_name="prior")
    again = await load.store_record(ctgov.parse_study(study("NCT00000011", "2026-10-01")), window="prior", set_name="prior")
    assert again.version_id == a.version_id and not again.moved
    b = await load.store_record(ctgov.parse_study(study("NCT00000011", "2026-11-12", summary="Changed.")),
                                window="discovered", set_name="discover", scope_id=A_SCOPE)
    assert b.changed
    assert await db["source_versions"].count_documents({"source_ref": "clinicaltrials.gov:NCT00000011"}) == 2
    item = await db["source_items"].find_one({"_id": "clinicaltrials.gov:NCT00000011"})
    assert item["current_version_id"] == b.version_id
    first = await db["source_versions"].find_one({"_id": a.version_id})
    assert first["last_update_post_date"] == "2026-10-01" and first["previous_version_id"] is None


async def test_scan_on_atlas(db, monkeypatch, events, fake_runs, ctgov_fake) -> None:
    await _clean(db)
    await db["research_scopes"].insert_one(scope_doc(_id=A_SCOPE))
    await db["runs"].insert_one(run_doc())
    gate = ScanGate(db)
    monkeypatch.setattr(scan_mod.gate, "evaluate", gate.evaluate)
    acts = FakeActions(db)
    monkeypatch.setattr(scan_mod.actions, "record_source_result", acts.record_source_result, raising=False)
    ctgov_fake.pages = [[study("NCT04712877", "2026-11-12"), study("NCT00000012", "2026-11-03")]]
    from .conftest import run_ctx

    refs = await discovery.scan(A_SCOPE, run_ctx())
    assert refs[0] == "clinicaltrials.gov:NCT04712877"
    scope = await db["research_scopes"].find_one({"_id": A_SCOPE})
    assert scope["cursor"]["last_update_post_date"] == "2026-11-12" and scope["version"] == 2
    decision = await db["decisions"].find_one({"_id": {"$regex": "^dec_"}, "run_id": RUN_ID})
    assert decision["outcome"] == "allowed" and decision["action_id"] == gate.action_ids[0]
    action = await db["actions"].find_one({"_id": gate.action_ids[0]})
    assert action["status"] == "delivered" and action["result"]["count"] == 2
    assert fake_runs.scans[RUN_ID]["source_refs"] == refs


async def test_blocked_scan_on_atlas(db, monkeypatch, events, fake_runs, ctgov_fake) -> None:
    await _clean(db)
    await db["research_scopes"].insert_one(scope_doc(_id=A_SCOPE))
    await db["runs"].insert_one(run_doc())
    gate = ScanGate(db, blocked=True)
    monkeypatch.setattr(scan_mod.gate, "evaluate", gate.evaluate)
    from .conftest import run_ctx

    assert await discovery.scan(A_SCOPE, run_ctx()) == []
    assert ctgov_fake.requests == []
    assert await db["decisions"].count_documents({"run_id": RUN_ID, "outcome": "blocked"}) == 1
    assert await db["actions"].count_documents({"run_id": RUN_ID}) == 0
    scope = await db["research_scopes"].find_one({"_id": A_SCOPE})
    assert scope["cursor"]["last_update_post_date"] == "2026-11-11" and scope["version"] == 1
    await _clean(db)
