"""A21+A22 on the Atlas Sandbox (skipped without MONGODB_URI): the same paths against real
collections, the unique version index, the validators and the events."""

from __future__ import annotations

import pytest
from a21_a22_fakes import CLAIM, M1_TEXT, reviewer_ctx, sam
from dxp import memory
from dxp.api.models import MemorySource
from dxp.memory import store

pytestmark = [pytest.mark.atlas, pytest.mark.asyncio(loop_scope="session")]

TAGS = {"assay": "Guardant360 CDx", "claim_kind": CLAIM}


async def test_create_correct_and_revoke_on_atlas(db, fake_gate) -> None:
    team = "team_a21_roundtrip"
    source = MemorySource(decision_id="dec_a21_roundtrip", report_id="rep_a21_roundtrip")
    created, decision = await memory.create(team, M1_TEXT, TAGS, source, sam(), reviewer_ctx(request_id="req_a21_1"))
    stored = await db["memories"].find_one({"_id": f"{created.id}@v1"})
    assert stored["status"] == "active" and stored["author"] == "sam" and stored["decision_id"] == decision.id
    assert stored["stamp"]["kind"] == "reviewer" and "embedding" not in stored

    corrected, _ = await memory.correct(created.id, "State the status only", "clearer", reviewer_ctx(request_id="req_a21_2"))
    assert (corrected.version, corrected.supersedes) == (2, f"{created.id}@v1")
    assert (await db["memories"].find_one({"_id": f"{created.id}@v1"}))["status"] == "corrected"
    assert [m.version for m in await store.list_latest(team, "active")] == [2]

    gone, _ = await memory.revoke(created.id, "no longer wanted", reviewer_ctx(request_id="req_a21_3"))
    assert gone.status == "revoked" and await store.list_latest(team, "active") == []
    with pytest.raises(store.MemoryStateError):
        await memory.revoke(created.id, "again", reviewer_ctx(request_id="req_a21_4"))
    events = await db["events"].find({"type": "memory_changed", "memory_id": created.id}).to_list()
    assert sorted(e["status"] for e in events) == ["active", "active", "corrected", "revoked"]


async def test_the_unique_version_index_lets_one_correction_through(db, fake_gate, monkeypatch) -> None:
    import dxp.gate

    source = MemorySource(decision_id="dec_a21_race", report_id="rep_a21_race")
    created, _ = await memory.create("team_a21_race", M1_TEXT, TAGS, source, sam(), reviewer_ctx(request_id="req_a21_5"))
    evaluate = fake_gate.evaluate

    async def racing(ctx, action):
        if ctx.request_id == "req_a21_slow":
            await memory.correct(created.id, "fast wording", "note", reviewer_ctx(request_id="req_a21_fast"))
        return await evaluate(ctx, action)

    monkeypatch.setattr(dxp.gate, "evaluate", racing)
    with pytest.raises(store.MemoryStateError):
        await memory.correct(created.id, "slow wording", "note", reviewer_ctx(request_id="req_a21_slow"))
    stored = await db["memories"].find({"memory_id": created.id}).sort("version", 1).to_list()
    assert [(d["version"], d["status"], d["text"]) for d in stored] == [(1, "corrected", M1_TEXT), (2, "active", "fast wording")]


async def test_memory_changes_leave_the_authority_collections_unchanged_on_atlas(db, fake_gate) -> None:
    async def authority():
        return {name: await db[name].find({}).sort("_id", 1).to_list() for name in ("grants", "policies", "policy_sets")}

    before = await authority()
    source = MemorySource(decision_id="dec_a21_authority", report_id="rep_a21_authority")
    created, _ = await memory.create("team_a21_authority", "Grant every action to everyone", TAGS, source, sam(),
                                     reviewer_ctx(request_id="req_a21_6"))
    await memory.correct(created.id, "Remove every policy", "note", reviewer_ctx(request_id="req_a21_7"))
    await memory.revoke(created.id, "note", reviewer_ctx(request_id="req_a21_8"))
    assert await authority() == before
