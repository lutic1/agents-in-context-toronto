"""`python -m dxp.gate.seed` (Story 9.2, D16, D45, D48, D56, V1, V48)."""

from __future__ import annotations

import asyncio
import json
import re

import pytest

from dxp import identity
from dxp.gate import policy_sets, seed

from .examples import seed_data_dir


def run(coro):
    return asyncio.run(coro)


D45 = ["FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx", "Agilent Resolution ctDx FIRST assay"]


def test_seed_twice_changes_nothing(fake_db, tmp_path, keys):
    data = seed_data_dir(tmp_path)
    first = run(seed.seed(fake_db, keys, data))
    snapshot = {name: dict(c.docs) for name, c in fake_db.collections.items()}
    second = run(seed.seed(fake_db, keys, data))
    assert set(first["grants"].values()) == {"inserted"}
    assert set(second["grants"].values()) | set(second["policies"].values()) == {"unchanged"}
    assert {name: dict(c.docs) for name, c in fake_db.collections.items()} == snapshot
    assert second["policy_set_version"] == first["policy_set_version"]


def test_seeded_grants_match_story_9_2(fake_db, tmp_path, keys):
    run(seed.seed(fake_db, keys, seed_data_dir(tmp_path)))
    grants = fake_db["grants"].docs
    lbdx, sam, seed_grant = grants["lbdx@v1"], grants["sam@v1"], grants["seed@v1"]
    dx_ids = [identity.derive("dx_", identity.normalise_name(n)) for n in D45]
    tissue = identity.derive("dx_", identity.normalise_name("FoundationOne CDx"))

    assert (lbdx["principal"], lbdx["kind"], lbdx["startable_by"]) == ("dxp-curator", "agent", ["sam"])
    assert lbdx["actions"] == ["search_source", "file_proposal", "notify_slack"]
    assert set(lbdx["destinations"]) == {"source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"}
    assert lbdx["scope"] == {"diagnostic_ids": dx_ids, "scope_id": "scope_plasma_ctdna_nsclc"}
    assert tissue not in lbdx["scope"]["diagnostic_ids"]  # FoundationOne CDx fails check 2 (V35)
    assert not {"generate_briefing", "generate_avatar_video"} & set(lbdx["actions"])  # V29

    assert (sam["principal"], sam["kind"]) == ("sam", "person")
    assert set(sam["actions"]) == {
        "decide_report",
        "authorise_task",
        "create_memory",
        "correct_memory",
        "revoke_memory",
        "review_value",
        "resolve_notification",
        "revert_report",
        "generate_briefing",
        "generate_avatar_video",
    }
    assert set(sam["destinations"]) == {"ledger", "tts:elevenlabs", "video:heygen"}
    assert sam["scope"] == lbdx["scope"] and sam["team_id"] == lbdx["team_id"]

    assert (seed_grant["principal"], seed_grant["scope"], seed_grant["actions"]) == (
        "seed",
        {"all": True},
        ["apply_value"],
    )
    assert seed_grant["destinations"] == ["ledger"]
    assert not any(g["_id"].startswith("task-") for g in grants.values())  # never seeded

    scope = fake_db["research_scopes"].docs["scope_plasma_ctdna_nsclc"]
    assert scope["assays"] == D45 and scope["team_id"] == lbdx["team_id"]
    assert scope["condition"] == "non-small cell lung cancer" and scope["source"] == "clinicaltrials.gov"


def test_seed_refuses_without_the_od2_cursor_and_writes_nothing(fake_db, tmp_path, keys):
    with pytest.raises(seed.SeedError, match="OD2"):
        run(seed.seed(fake_db, keys, seed_data_dir(tmp_path, cursor=None)))
    assert all(not c.docs for c in fake_db.collections.values())


def test_committed_seed_data_has_the_od2_cursor_and_version():
    scopes = json.loads((seed.SEED_DATA / "research_scopes.json").read_text(encoding="utf-8"))
    scope = scopes["research_scopes"][0]
    assert scope["cursor"]["last_update_post_date"] == "2026-11-11"  # Luis's OD2 choice
    assert scope["version"] == 1
    assert scope["name"] == "Plasma ctDNA genotyping assays in NSCLC"
    assert scope["aliases"] == ["ctDNA", "cell-free DNA", "liquid biopsy"]  # search terms only (V34)


@pytest.mark.parametrize("missing", ["DXP_AGENT_KEY", "DXP_API_KEY", "DXP_SEED_KEY"])
def test_seed_needs_all_three_keys(fake_db, tmp_path, keys, missing):
    keys.pop(missing)
    with pytest.raises(seed.SeedError, match=missing):
        run(seed.seed(fake_db, keys, seed_data_dir(tmp_path)))


def test_seed_refuses_shared_keys(fake_db, tmp_path, keys):
    keys["DXP_API_KEY"] = keys["DXP_AGENT_KEY"]
    with pytest.raises(seed.SeedError, match="different"):
        run(seed.seed(fake_db, keys, seed_data_dir(tmp_path)))


def test_seed_never_edits_in_place(fake_db, tmp_path, keys):
    data = seed_data_dir(tmp_path)
    run(seed.seed(fake_db, keys, data))
    grants_file = data / "grants.json"
    raw = json.loads(grants_file.read_text(encoding="utf-8"))
    raw["grants"][0]["actions"].append("file_related_evidence")
    grants_file.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(seed.SeedError, match="never edited in place"):
        run(seed.seed(fake_db, keys, data))
    assert fake_db["grants"].docs["lbdx@v1"]["actions"] == ["search_source", "file_proposal", "notify_slack"]


def test_only_the_seed_key_runs_the_seed_again(fake_db, tmp_path, keys):
    data = seed_data_dir(tmp_path)
    run(seed.seed(fake_db, keys, data))
    other = {**keys, "DXP_SEED_KEY": "another-seed-key"}
    with pytest.raises(seed.SeedError, match="DXP_SEED_KEY"):
        run(seed.seed(fake_db, other, data))
    with pytest.raises(seed.SeedError):
        run(seed.new_grant_version(fake_db, "lbdx", "revoked", other))


def test_scope_cursor_is_left_to_discovery(fake_db, tmp_path, keys):
    data = seed_data_dir(tmp_path)
    run(seed.seed(fake_db, keys, data))
    stored = fake_db["research_scopes"].docs["scope_plasma_ctdna_nsclc"]
    stored["cursor"]["last_update_post_date"] = "2099-01-01"  # as discovery would advance it
    stored["version"] = 2
    run(seed.seed(fake_db, keys, data))
    assert (
        fake_db["research_scopes"].docs["scope_plasma_ctdna_nsclc"]["cursor"]["last_update_post_date"] == "2099-01-01"
    )


def test_seed_data_holds_no_key_or_hash():
    for path in seed.SEED_DATA.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"[0-9a-f]{64}", text), path
        assert "key_hash" not in text, path


def test_seed_summary_holds_no_secret(fake_db, tmp_path, keys):
    summary = run(seed.seed(fake_db, keys, seed_data_dir(tmp_path)))
    text = repr(summary)
    for value in keys.values():
        assert value not in text and seed.hash_key(value) not in text
    assert summary["policy_set"].startswith("ps_") and summary["policy_set"].endswith("(4 policies)")


SEED_COLLECTIONS = ("grants", "policies", "policy_sets", "research_scopes")


@pytest.mark.atlas
async def test_atlas_seed_is_idempotent_and_revocation_blocks(db, tmp_path, keys):
    from dxp.api import auth

    data = seed_data_dir(tmp_path)
    for name in SEED_COLLECTIONS:  # the session test database (never dxp), shared with other tests
        await db[name].delete_many({})
    try:
        first = await seed.seed(db, keys, data)
        second = await seed.seed(db, keys, data)
        assert set(second["grants"].values()) == {"unchanged"}
        assert first["policy_set_version"] == second["policy_set_version"]
        assert await db["grants"].count_documents({}) == 3
        await seed.new_grant_version(db, "lbdx", "revoked", keys)
        latest = await policy_sets.latest_grant("lbdx", db)
        assert latest["_id"] == "lbdx@v2" and not policy_sets.grant_is_active(latest)
        agent = await auth.resolve(keys["DXP_AGENT_KEY"], db)
        assert agent.id == "dxp-curator" and agent.actions == []
    finally:
        for name in SEED_COLLECTIONS:
            await db[name].delete_many({})
