"""A10 on the Atlas Sandbox: the pipeline's own writes (processed marker, Findings) in a fresh test database.

Runs only with MONGODB_URI set (a `dxp_test_<hex>` database, never `dxp`); skipped otherwise.
Run progress goes through A07+A11's runs functions; the modules the run calls are proved in I1.
"""

from __future__ import annotations

from typing import Any

import pytest

from dxp.pipeline import progress

pytestmark = pytest.mark.atlas


async def test_processed_marker_and_finding_insert_if_absent(db: Any) -> None:
    ref = "clinicaltrials.gov:NCT0A10ATL"
    await db["source_items"].delete_many({"_id": ref})
    await db["source_items"].insert_one({"_id": ref, "current_version_id": "sv_a10"})
    item = await db["source_items"].find_one({"_id": ref})
    assert not progress.processed(item, "scope_x", "sv_a10")
    await progress.mark_processed(ref, "scope_x", "sv_a10", "run_a10atlas0001")
    item = await db["source_items"].find_one({"_id": ref})
    assert progress.processed(item, "scope_x", "sv_a10") and not progress.processed(item, "scope_x", "sv_other")
    assert item["processed"]["scope_x"]["sv_a10"].tzinfo is not None  # processed_at, a timestamp
    finding = {"id": "f_a10atlas", "version_id": "sv_a10", "summary": "first"}
    await progress.save_finding(finding, "run_a10atlas0001", None)
    await progress.save_finding({**finding, "summary": "second"}, "run_a10atlas0002", None)
    stored = await db["findings"].find_one({"_id": "f_a10atlas"})
    assert stored["summary"] == "first" and stored["run_id"] == "run_a10atlas0001"
