"""A13 against the live FDA page (network). Runs only with DXP_LIVE_FDA=1; nothing is stored.

Done-when of the card: "the FDA fetch parses the live list".
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from dxp.ledger import seed as seed_mod
from dxp.sources import fda_cdx

from .conftest import SCOPE_ASSAYS

pytestmark = pytest.mark.skipif(
    os.environ.get("DXP_LIVE_FDA") != "1",
    reason="DXP_LIVE_FDA is not 1: the live FDA fetch is skipped",
)


async def test_live_list_parses_and_names_the_scope_assays() -> None:
    page = await fda_cdx.fetch_page()
    rows = fda_cdx.lung_rows(fda_cdx.parse_rows(page))
    names = {r.trade_name for r in rows}
    assert len(rows) >= 40
    for assay in (*SCOPE_ASSAYS, "FoundationOne CDx"):
        assert assay in names, assay
    assert fda_cdx.parse_list_date(page) is not None
    items = [fda_cdx.source_documents(r, fetched_at=datetime.now(UTC), list_date=None)[0] for r in rows]
    plan = seed_mod.plan_changes(items)
    planned = {p.change["diagnostic_name"] for p in plan}
    assert planned == names
    assert all(any(p.field == "lifecycle_stage" and p.change["diagnostic_name"] == n for p in plan) for n in names)
