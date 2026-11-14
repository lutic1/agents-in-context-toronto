"""Opt-in checks against the live ClinicalTrials.gov API v2 (set DXP_LIVE_CTGOV=1).

They check fields and IDs only; no record text is asserted or written to any file."""

from __future__ import annotations

import os

import pytest

from dxp.discovery.scan import build_query
from dxp.sources import ctgov

from .conftest import scope_doc

pytestmark = pytest.mark.skipif(os.environ.get("DXP_LIVE_CTGOV") != "1", reason="DXP_LIVE_CTGOV=1 not set: live API checks skipped")

CURSOR = os.environ.get("DXP_LIVE_CURSOR", "2026-11-11")


async def test_fetch_anchor_keeps_other_names_verbatim() -> None:
    rec = ctgov.parse_study(await ctgov.fetch_study("NCT04712877"))
    names = [n for iv in rec["interventions"] for n in iv.get("otherNames", [])]
    assert "FoundationOne CDx" in names and "FoundationOne Liquid" in names
    assert rec["overall_status"] and rec["last_update_post_date"] and isinstance(rec["has_results"], bool)


async def test_scan_query_with_condition_alias_finds_anchor() -> None:
    q = build_query(scope_doc(CURSOR, condition_aliases=["NSCLC"]), CURSOR)
    res = await ctgov.search(q["query.term"], q["query.cond"], CURSOR)
    ids = {s["protocolSection"]["identificationModule"]["nctId"] for s in res.studies}
    assert res.complete and "NCT04712877" in ids


async def test_scan_query_without_condition_alias_misses_anchor() -> None:
    """Review item (b): with `condition_aliases=[]` the plain condition does not find the anchor,
    which lists its condition only as "NSCLC" (V51)."""
    q = build_query(scope_doc(CURSOR, condition_aliases=[]), CURSOR)
    assert "NSCLC" not in q["query.cond"]
    res = await ctgov.search(q["query.term"], q["query.cond"], CURSOR)
    ids = {s["protocolSection"]["identificationModule"]["nctId"] for s in res.studies}
    assert res.complete and "NCT04712877" not in ids
