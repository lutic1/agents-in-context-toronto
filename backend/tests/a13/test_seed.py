"""A13: the FDA seed through a fake ledger and the fake gate, and the synthetic Teams (D38)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest

from dxp.identity import derive, diagnostic_id, normalise_name, resolve_exact
from dxp.ledger import seed as seed_mod
from dxp.sources import fda_cdx

from .conftest import SCOPE_ASSAYS

FETCHED = datetime(2026, 11, 14, 13, 0, tzinfo=UTC)


async def _stored(fake_db, fda_page: str) -> None:
    rows = fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page))
    await fda_cdx.store_rows(fake_db, rows, fetched_at=FETCHED, list_date="2026-11-03")


def _items(fake_db) -> list[dict]:
    return list(fake_db["source_items"].docs.values())


async def test_plan_is_rule_based_and_separates_the_two_foundationone_tests(fake_db, fda_page) -> None:
    await _stored(fake_db, fda_page)
    plan = seed_mod.plan_changes(_items(fake_db))
    by_dx: dict[str, dict[str, set[str]]] = {}
    for p in plan:
        by_dx.setdefault(p.change["diagnostic_name"], {}).setdefault(p.field, set()).add(p.value)

    tissue, plasma = by_dx["FoundationOne CDx"], by_dx["FoundationOne Liquid CDx"]
    assert diagnostic_id("FoundationOne CDx") != diagnostic_id("FoundationOne Liquid CDx")
    assert tissue["sample_types"] == {"tissue"} and plasma["sample_types"] == {"plasma"}
    assert tissue["biomarkers"] == {"EGFR", "ALK"} and tissue["linked_drugs"] == {"osimertinib", "alectinib"}
    for fields in by_dx.values():
        assert fields["lifecycle_stage"] == {"regulatory_approval"}  # by rule, every Diagnostic
        assert fields["regulatory_status"] == {"fda_approved"}  # P numbers: PMA
        assert fields["clinical_uses"] == {"treatment_selection"}
        assert fields["tumour_types"] == {"NSCLC"}
    assert by_dx["cobas EGFR Mutation Test v2"]["sample_types"] == {"tissue", "plasma"}
    assert by_dx["Guardant360® Liquid CDx"]["provider"] == {"guardant health inc"}
    assert set(by_dx) == {
        "FoundationOne CDx", "FoundationOne Liquid CDx", "Guardant360® Liquid CDx", "Guardant360 CDx",
        "Agilent Resolution ctDx FIRST assay", "cobas EGFR Mutation Test v2", "VENTANA MET (SP44) RxDx Assay",
    }


async def test_plan_ids_follow_ad3(fake_db, fda_page) -> None:
    await _stored(fake_db, fda_page)
    items = {d["_id"]: d for d in _items(fake_db)}
    plan = seed_mod.plan_changes(items.values())
    keys = [(p.diagnostic_id, p.field, p.value) for p in plan]
    assert len(keys) == len(set(keys))  # each value once per Diagnostic
    for p in plan:
        ev = p.change["evidence"]
        item = items[ev["source_ref"]]
        assert p.diagnostic_id == derive("dx_", normalise_name(p.change["assay_name"]))
        assert p.finding_id == derive("f_", item["current_version_id"], p.diagnostic_id)
        assert p.proposal_id == derive("p_", p.finding_id, p.field, p.value)
        assert ev["version_id"] == item["current_version_id"] and ev["source"] == "fda_cdx_list"
        assert ev["quote"] in item["raw_text"] and len(ev["quote"]) <= 300
        assert ev["source_date"] == "2026-11-14" and ev["data_as_of"] == "2026-11-03"
    # the plan does not depend on the order rows are read in
    assert [p.proposal_id for p in seed_mod.plan_changes(reversed(list(items.values())))] == [p.proposal_id for p in plan]


async def test_seed_files_every_value_through_the_ledger_in_baseline_mode(fake_db, fda_page, fake_ledger, fake_gate) -> None:
    await _stored(fake_db, fda_page)
    report = await seed_mod.seed(fake_db, file=fake_ledger.file)
    plan = seed_mod.plan_changes(_items(fake_db))
    assert report.filed == len(plan) and not report.blocked and report.skipped_existing == 0
    assert len(fake_ledger.calls) == len(plan) == len(fake_gate.calls)  # one gate evaluation per change (D46)
    for finding_id, changes, mode, ctx in fake_ledger.calls:
        assert mode == "baseline" and len(changes) == 1
        assert ctx["stamp"] == {"kind": "seed", "principal": "seed", "run_id": None}
        assert ctx["run_id"] is None and ctx["agent"] == "seed" and ctx["initiated_by"] == "seed"
        assert ctx["grant_id"] == "seed" and ctx["grant_version"] == 1
    for _, action in fake_gate.calls:
        assert action.kind == "apply_value" and action.destination == "ledger"
    # the ledger was handed exact trade names, so the aliases it wrote resolve exactly (V34)
    aliases = fake_db["aliases"]
    sync = _SyncAliases(aliases)
    for assay in (*SCOPE_ASSAYS, "FoundationOne CDx"):
        assert resolve_exact(assay, aliases=sync) == diagnostic_id(assay)
    for name in ("FoundationOne Liquid", "Guardant360", "FoundationOne"):
        assert resolve_exact(name, aliases=sync) is None
    assert set(aliases.docs) == {normalise_name(n) for n in report.diagnostics}  # no other alias


async def test_seed_twice_creates_and_changes_nothing(fake_db, fda_page, fake_ledger) -> None:
    await _stored(fake_db, fda_page)
    await seed_mod.seed(fake_db, file=fake_ledger.file)
    before = fake_db.snapshot()
    calls = len(fake_ledger.calls)
    again = await seed_mod.seed(fake_db, file=fake_ledger.file)
    assert fake_db.snapshot() == before
    assert len(fake_ledger.calls) == calls  # nothing re-filed, so no new Decision either
    assert again.filed == 0 and again.skipped_existing == len(seed_mod.plan_changes(_items(fake_db)))
    assert again.teams == {"inserted": 0, "existing": 3}


async def test_a_blocked_change_is_reported_and_writes_nothing(fake_db, fda_page, fake_ledger, fake_gate) -> None:
    await _stored(fake_db, fda_page)
    fake_gate.block("apply_value", "grant_active")
    report = await seed_mod.seed_diagnostics(fake_db, file=fake_ledger.file)
    assert report.filed == 0 and len(report.blocked) == len(fake_ledger.calls)
    assert not fake_db["aliases"].docs and not fake_db["diagnostics"].docs and not fake_db["proposals"].docs


async def test_seed_refuses_without_rows(fake_db, fake_ledger) -> None:
    with pytest.raises(seed_mod.SeedError):
        await seed_mod.seed(fake_db, file=fake_ledger.file)


async def test_teams(fake_db) -> None:
    assert await seed_mod.seed_teams(fake_db) == {"inserted": 3, "existing": 0}
    teams = fake_db["teams"].docs
    lbdx = derive("team_", "Team Liquid Biopsy Dx")  # the ID A03's grants act for
    assert lbdx in teams and teams[lbdx]["name"] == "Team Liquid Biopsy Dx"
    assert seed_mod.team_id("Team Liquid Biopsy Dx") == lbdx
    for doc in teams.values():
        assert doc["synthetic"] is True
        assert set(doc["profile"]) == {"modalities", "biomarkers", "linked_drugs"}
        assert all(doc["profile"][k] for k in doc["profile"])
    assert len({d["name"] for d in teams.values()}) == 3


async def test_seed_key_check(fake_db) -> None:
    key = "test-dxp-seed-key"
    with pytest.raises(seed_mod.SeedError, match="not set"):
        await seed_mod.check_seed_key(fake_db, {})
    with pytest.raises(seed_mod.SeedError, match="no seed grant"):
        await seed_mod.check_seed_key(fake_db, {"DXP_SEED_KEY": key})
    await fake_db["grants"].insert_one({
        "_id": "seed@v1", "grant_id": "seed", "version": 1, "status": "active",
        "key_hash": hashlib.sha256(key.encode()).hexdigest(),
    })
    await seed_mod.check_seed_key(fake_db, {"DXP_SEED_KEY": key})
    with pytest.raises(seed_mod.SeedError, match="does not match"):
        await seed_mod.check_seed_key(fake_db, {"DXP_SEED_KEY": "test-dxp-agent-key"})


class _SyncAliases:
    """A02's resolver takes a sync collection: read the fake's documents directly."""

    def __init__(self, coll) -> None:
        self._docs = coll.docs

    def find_one(self, flt, *args, **kwargs):
        return self._docs.get(flt["_id"])
