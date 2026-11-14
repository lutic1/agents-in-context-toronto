"""Live checks on the two tuning trials (card A08 "Done when").

Run only when ANTHROPIC_API_KEY is set (and ClinicalTrials.gov is reachable);
otherwise skipped with the reason. Fetched text stays in memory: nothing is
written to a file. Resolution, IDs and canonical values use A02's real
`identity` and `registry` when they are importable and MONGODB_URI is set,
else the conftest fakes that follow their contracts.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import re

import pytest

from dxp.evidence import quote_in_source
from dxp.llm import _deps, extract
from dxp.llm.cli import fetch_item

from .conftest import SEEDED, SEEDED_NAMES, fake_canonical, fake_derive, fake_resolve_exact

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY is not set: live Claude extraction not run",
)

USE_OR_STUDY = re.compile(r"\b(uses?|used|using|stud(y|ies|ied)|evaluat\w*)\b", re.IGNORECASE)
OUTCOME = re.compile(r"\b(showed|demonstrat\w*|results show|was associated|improved)\b", re.IGNORECASE)


@pytest.fixture
def registry(monkeypatch):
    real = importlib.util.find_spec("dxp.identity") is not None and os.environ.get("MONGODB_URI")
    if real:
        return None
    async def resolve(name):
        return fake_resolve_exact(name)
    monkeypatch.setattr(_deps, "resolve_exact", resolve)
    monkeypatch.setattr(_deps, "derive", fake_derive)
    monkeypatch.setattr(_deps, "canonical", fake_canonical)
    return SEEDED


def _fetch(nct_id):
    try:
        return asyncio.run(fetch_item(nct_id))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"ClinicalTrials.gov not reachable ({type(exc).__name__})")


def _sentences_claiming_use(text, names):
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if any(n in s for n in names) and USE_OR_STUDY.search(s)]


def test_live_nct04712877(registry):
    item = _fetch("NCT04712877")
    result = asyncio.run(extract(item, SEEDED_NAMES))
    assert result.status == "extracted", [f.line() for f in result.failures]
    assert "ctDNA, tumor NGS" in result.intervention_texts
    by_name = {m.name: m for m in result.mentions}
    assert by_name["FoundationOne CDx"].resolution == "exact"
    assert by_name["FoundationOne CDx"].resolved_diagnostic_id is not None
    assert by_name["FoundationOne Liquid"].resolution == "unresolved"
    assert "FoundationOne Liquid" in result.unresolved_names
    tissue = by_name["FoundationOne CDx"].resolved_diagnostic_id
    assert tissue in [f.diagnostic_id for f in result.findings]
    names = ["FoundationOne CDx", "FoundationOne Liquid", "FoundationOne"]
    for f in result.findings:
        assert not _sentences_claiming_use(f.summary, names), f.summary
        for v in f.passing_values:
            assert quote_in_source(v.quote, item["raw_text"])


def test_live_nct05715229(registry):
    item = _fetch("NCT05715229")
    result = asyncio.run(extract(item, SEEDED_NAMES))
    assert result.status == "extracted", [f.line() for f in result.failures]
    record = result.findings[0]
    assert record.diagnostic_id is None
    assert "terminated" in record.summary.lower() and "no results posted" in record.summary
    assert not OUTCOME.search(record.summary), record.summary
    for f in result.findings:
        for v in f.passing_values:
            assert quote_in_source(v.quote, item["raw_text"])
