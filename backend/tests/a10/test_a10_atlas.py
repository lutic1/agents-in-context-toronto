"""A10 on the Atlas Sandbox: the run's own progress writes in a fresh test database.

Runs only with MONGODB_URI set (a `dxp_test_<hex>` database, never `dxp`); skipped otherwise.
The modules the run calls are proved against Atlas in I1.
"""

from __future__ import annotations

from typing import Any

import pytest

from dxp.pipeline import progress

pytestmark = pytest.mark.atlas


async def test_progress_writes_counts_failures_and_failed_status(db: Any) -> None:
    run_id = "run_a10atlas0001"
    await db["runs"].delete_many({"_id": run_id})
    await db["runs"].insert_one({"_id": run_id, "agent": "dxp-curator", "initiated_by": "sam", "grant_id": "lbdx",
                                 "grant_version": 1, "policy_set_version": "ps_0000000000000001", "team_id": "t",
                                 "set": "discover", "kind": "discover", "status": "running",
                                 "started_at": progress.now(), "counts": {}})
    tracker = progress.Progress(run_id)
    await tracker.total(2)
    await tracker.step("clinicaltrials.gov:NCT1", "extract")
    await tracker.item_done("clinicaltrials.gov:NCT1", early_research=True)
    await tracker.item_failed("clinicaltrials.gov:NCT2", "extract: RuntimeError")
    await tracker.recount()
    run = await db["runs"].find_one({"_id": run_id})
    assert run["counts"]["total"] == 2 and run["counts"]["done"] == 1 and run["counts"]["failed"] == 1
    assert run["counts"]["early_research"] == 1 and run["counts"]["reports"] == 0
    assert run["active"] == [] and run["failures"][0]["error"] == "extract: RuntimeError"
    assert await tracker.mark_failed("RuntimeError") is True
    assert await tracker.mark_failed("RuntimeError") is False  # conditional: once
    assert (await db["runs"].find_one({"_id": run_id}))["status"] == "failed"


async def test_processed_marker_and_finding_insert_if_absent(db: Any) -> None:
    ref = "clinicaltrials.gov:NCT0A10ATL"
    await db["source_items"].delete_many({"_id": ref})
    await db["source_items"].insert_one({"_id": ref, "current_version_id": "sv_a10"})
    item = await db["source_items"].find_one({"_id": ref})
    assert not progress.processed(item, "scope_x", "sv_a10")
    await progress.mark_processed(ref, "scope_x", "sv_a10", "run_a10atlas0001")
    item = await db["source_items"].find_one({"_id": ref})
    assert progress.processed(item, "scope_x", "sv_a10") and not progress.processed(item, "scope_x", "sv_other")
    finding = {"id": "f_a10atlas", "version_id": "sv_a10", "summary": "first"}
    await progress.save_finding(finding, "run_a10atlas0001", None)
    await progress.save_finding({**finding, "summary": "second"}, "run_a10atlas0002", None)
    stored = await db["findings"].find_one({"_id": "f_a10atlas"})
    assert stored["summary"] == "first" and stored["run_id"] == "run_a10atlas0001"
