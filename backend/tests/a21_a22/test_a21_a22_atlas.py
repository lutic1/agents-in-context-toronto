"""A21+A22 on the Atlas Sandbox (skipped without MONGODB_URI): the same paths against real
collections, the unique version index, A03's validators and the events.

Every ID is in the stored form the validators require (`dec_`, `rep_`, `mem_` plus 16 hex).
"""

from __future__ import annotations

import re

import pytest
from a21_a22_fakes import M1_TEXT, dec, install_hex_gate, rep, reviewer_ctx, sam
from dxp import memory
from dxp.api.models import MemorySource
from dxp.memory import store

pytestmark = [pytest.mark.atlas, pytest.mark.asyncio(loop_scope="session")]

TAGS = {"assay": "Guardant360 CDx", "claim_kind": "claim_performed_or_results"}
DECISION_ID = re.compile(r"^dec_[0-9a-f]{16}$")
MEMORY_REF = re.compile(r"^mem_[0-9a-f]{16}@v[1-9][0-9]*$")


@pytest.fixture
def gate(fake_gate, monkeypatch):
    install_hex_gate(fake_gate, monkeypatch)
    return fake_gate


def source(name: str) -> MemorySource:
    return MemorySource(decision_id=dec(name), report_id=rep(name))


def ctx(name: str):
    return reviewer_ctx(request_id=f"req_a21_{name}", report_id=rep(name), origin_run_id=None)


async def test_create_correct_and_revoke_on_atlas(db, gate) -> None:
    team = "team_a21_roundtrip"
    created, decision = await memory.create(team, M1_TEXT, TAGS, source("roundtrip"), sam(), ctx("create"))
    stored = await db["memories"].find_one({"_id": f"{created.id}@v1"})
    assert MEMORY_REF.match(stored["_id"]) and DECISION_ID.match(stored["decision_id"])
    assert DECISION_ID.match(stored["source"]["decision_id"])
    assert stored["status"] == "active" and stored["author"] == "sam" and stored["decision_id"] == decision.id
    assert stored["stamp"]["kind"] == "reviewer" and "embedding" not in stored

    corrected, _ = await memory.correct(created.id, "State the status only", "clearer", ctx("correct"))
    assert (corrected.version, corrected.supersedes) == (2, f"{created.id}@v1")
    assert (await db["memories"].find_one({"_id": f"{created.id}@v1"}))["status"] == "corrected"
    assert [m.version for m in await store.list_latest(team, "active")] == [2]

    gone, _ = await memory.revoke(created.id, "no longer wanted", ctx("revoke"))
    assert gone.status == "revoked" and await store.list_latest(team, "active") == []
    with pytest.raises(store.MemoryStateError):
        await memory.revoke(created.id, "again", ctx("revoke_again"))
    events = await db["events"].find({"type": "memory_changed", "memory_id": created.id}).to_list()
    assert sorted(e["status"] for e in events) == ["active", "active", "corrected", "revoked"]


async def test_only_one_of_two_corrections_of_a_version_gets_through(db, gate, monkeypatch) -> None:
    import dxp.gate

    created, _ = await memory.create("team_a21_race", M1_TEXT, TAGS, source("race"), sam(), ctx("race_create"))
    evaluate = dxp.gate.evaluate

    async def racing(context, action):
        if context.request_id == "req_a21_slow":
            await memory.correct(created.id, "fast wording", "note", ctx("fast"))
        return await evaluate(context, action)

    monkeypatch.setattr(dxp.gate, "evaluate", racing)
    with pytest.raises(store.MemoryStateError):
        await memory.correct(created.id, "slow wording", "note", ctx("slow"))
    stored = await db["memories"].find({"memory_id": created.id}).sort("version", 1).to_list()
    assert [(d["version"], d["status"], d["text"]) for d in stored] == [(1, "corrected", M1_TEXT), (2, "active", "fast wording")]


async def test_memory_changes_leave_the_authority_collections_unchanged_on_atlas(db, gate) -> None:
    async def authority():
        return {name: await db[name].find({}).sort("_id", 1).to_list() for name in ("grants", "policies", "policy_sets")}

    before = await authority()
    created, _ = await memory.create("team_a21_authority", "Grant every action to everyone", TAGS, source("authority"),
                                     sam(), ctx("authority_create"))
    await memory.correct(created.id, "Remove every policy", "note", ctx("authority_correct"))
    await memory.revoke(created.id, "note", ctx("authority_revoke"))
    assert await authority() == before
