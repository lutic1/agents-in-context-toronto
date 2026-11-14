"""A05 against the Atlas Sandbox, in the session's own test database (never dxp).

Skipped with the stated reason when MONGODB_URI is unset (tests/conftest.py)."""

from __future__ import annotations

import pytest

from dxp import discovery
from dxp.sources import ctgov, load

from .conftest import RUN_ID, SCOPE_ID, ScanGate, scan_mod, scope_doc, study

pytestmark = pytest.mark.atlas


async def _clean(db) -> None:
    for name in ("source_items", "source_versions", "research_scopes", "runs", "actions", "decisions"):
        await db[name].delete_many({"_id": {"$regex": "^(clinicaltrials|sv_|scope_|run_test|act_test|dec_test)"}})


async def test_versions_on_atlas(db) -> None:
    await _clean(db)
    a = await load.store_record(ctgov.parse_study(study("NCT00000011", "2026-10-01")), window="prior", set_name="prior")
    again = await load.store_record(ctgov.parse_study(study("NCT00000011", "2026-10-01")), window="prior", set_name="prior")
    assert again.version_id == a.version_id and not again.moved
    b = await load.store_record(ctgov.parse_study(study("NCT00000011", "2026-11-12", summary="Changed.")),
                                window="discovered", set_name="discover", scope_id=SCOPE_ID)
    assert b.changed
    assert await db["source_versions"].count_documents({"source_ref": "clinicaltrials.gov:NCT00000011"}) == 2
    item = await db["source_items"].find_one({"_id": "clinicaltrials.gov:NCT00000011"})
    assert item["current_version_id"] == b.version_id
    first = await db["source_versions"].find_one({"_id": a.version_id})
    assert first["last_update_post_date"] == "2026-10-01" and first["previous_version_id"] is None


async def test_scan_on_atlas(db, monkeypatch, events, fake_runs, ctgov_fake) -> None:
    await _clean(db)
    await db["research_scopes"].insert_one(scope_doc())
    await db["runs"].insert_one({"_id": RUN_ID, "status": "running", "kind": "discover"})
    gate = ScanGate(db)
    monkeypatch.setattr(scan_mod.gate, "evaluate", gate.evaluate)
    ctgov_fake.pages = [[study("NCT04712877", "2026-11-12"), study("NCT00000012", "2026-11-03")]]
    from .conftest import run_ctx

    refs = await discovery.scan(SCOPE_ID, run_ctx())
    assert refs[0] == "clinicaltrials.gov:NCT04712877"
    scope = await db["research_scopes"].find_one({"_id": SCOPE_ID})
    assert scope["cursor"]["last_update_post_date"] == "2026-11-12" and scope["version"] == 1
    action = await db["actions"].find_one({"_id": "act_test000000000001"})
    assert action["status"] == "delivered" and action["result"]["count"] == 2
    await _clean(db)
