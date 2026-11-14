"""Selection (latest version first, then status) and policy sets (AD-18, D6)."""

from __future__ import annotations

import asyncio
import copy
from datetime import timedelta

from dxp import identity
from dxp.gate import policy_sets, seed

from .examples import NOW, seed_data_dir, task_grant


def run(coro):
    return asyncio.run(coro)


def seeded_db(fake_db, tmp_path, keys):
    run(seed.seed(fake_db, keys, seed_data_dir(tmp_path)))
    return fake_db


def test_a_newer_revoked_grant_version_blocks(fake_db, tmp_path, keys):
    db = seeded_db(fake_db, tmp_path, keys)
    assert policy_sets.grant_is_active(run(policy_sets.current_grant("lbdx", db)))
    run(seed.new_grant_version(db, "lbdx", "revoked", keys))
    latest = run(policy_sets.current_grant("lbdx", db))
    assert latest["_id"] == "lbdx@v2" and latest["status"] == "revoked"
    assert not policy_sets.grant_is_active(latest)
    # The older active version is still there, and it does not count.
    assert run(policy_sets.grant_version("lbdx", 1, db))["status"] == "active"


def test_an_expired_or_past_expiry_grant_is_not_active(fake_db, tmp_path, keys):
    db = seeded_db(fake_db, tmp_path, keys)
    lbdx = run(policy_sets.current_grant("lbdx", db))
    assert not policy_sets.grant_is_active(lbdx, at=lbdx["expires_at"] + timedelta(seconds=1))
    run(seed.new_grant_version(db, "sam", "expired", keys))
    assert not policy_sets.grant_is_active(run(policy_sets.current_grant("sam", db)))


def test_task_grant_early_expiry_is_its_v2(fake_db, tmp_path, keys):
    db = seeded_db(fake_db, tmp_path, keys)
    lbdx = run(policy_sets.current_grant("lbdx", db))
    v1 = task_grant(lbdx, expires_at=policy_sets.now() + timedelta(minutes=30), created_at=policy_sets.now())
    run(db["grants"].insert_one(v1))
    assert policy_sets.grant_is_active(run(policy_sets.current_grant(v1["grant_id"], db)))
    v2 = {
        **copy.deepcopy(v1),
        "_id": v1["grant_id"] + "@v2",
        "version": 2,
        "status": "expired",
        "expires_at": NOW,
        "created_at": NOW,
    }
    run(db["grants"].insert_one(v2))  # validates (V48)
    assert not policy_sets.grant_is_active(run(policy_sets.current_grant(v1["grant_id"], db)))


def test_the_three_claim_policies_are_in_the_current_set(fake_db, tmp_path, keys):
    db = seeded_db(fake_db, tmp_path, keys)
    current = run(policy_sets.current_set(db))
    assert {"claim_performed_or_results@v1", "claim_planned@v1", "claim_preclinical@v1"} <= set(current["members"])
    assert current["members"] == sorted(current["members"])
    assert current["_id"] == identity.derive("ps_", *current["members"])
    assert run(db["policy_sets"].find_one({"_id": current["_id"]})) is not None


def test_policy_set_is_inserted_once_and_rebuildable(fake_db, tmp_path, keys):
    db = seeded_db(fake_db, tmp_path, keys)
    first = run(policy_sets.current_set(db))
    again = run(policy_sets.current_set(db))
    assert first["_id"] == again["_id"]
    assert len(db["policy_sets"].docs) == 1
    members = [p["_id"] for p in run(policy_sets.policies_in_set(first["_id"], db))]
    assert members == first["members"]


def test_latest_policy_version_first_then_status(fake_db, tmp_path, keys):
    db = seeded_db(fake_db, tmp_path, keys)
    before = run(policy_sets.current_set(db))
    v1 = run(db["policies"].find_one({"_id": "claim_planned@v1"}))
    retired = {
        **copy.deepcopy(v1),
        "_id": "claim_planned@v2",
        "version": 2,
        "status": "retired",
        "created_at": policy_sets.now(),
    }
    run(db["policies"].insert_one(retired))
    after = run(policy_sets.current_set(db))
    assert "claim_planned@v1" not in after["members"] and "claim_planned@v2" not in after["members"]
    assert after["_id"] != before["_id"]
    # The earlier set is still recorded, so a decision made under it can be rebuilt.
    assert run(policy_sets.policy_set(before["_id"], db))["members"] == before["members"]
    active_again = {**copy.deepcopy(v1), "_id": "claim_planned@v3", "version": 3, "created_at": policy_sets.now()}
    run(db["policies"].insert_one(active_again))
    assert "claim_planned@v3" in run(policy_sets.current_set(db))["members"]


def test_display_policy_set():
    assert policy_sets.display_policy_set("ps_ab12cd34ef56ab78", 4) == "ps_ab12… (4 policies)"
