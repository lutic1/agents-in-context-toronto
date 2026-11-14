"""memory.create, memory.correct and memory.revoke against an in-memory database and a fake gate."""

from __future__ import annotations

import pytest
from a21_a22_fakes import CLAIM, M1_TEXT, TEAM, install, reviewer_ctx, sam
from dxp import identity, memory
from dxp.api.models import Memory, MemorySource
from dxp.memory import store

SOURCE = MemorySource(decision_id="dec_reject", report_id="rep_setup")
TAGS = {"assay": "Guardant360 CDx", "claim_kind": CLAIM}


@pytest.fixture
def database(monkeypatch):
    return install(monkeypatch)


async def create_m1(ctx=None, **changes):
    fields = dict(team_id=TEAM, text=M1_TEXT, tags=TAGS, source=SOURCE, reviewer=sam(), ctx=ctx or reviewer_ctx())
    fields.update(changes)
    return await memory.create(**fields)


# --- create ---------------------------------------------------------------


async def test_create_is_gated_and_writes_version_one(database, fake_gate):
    created, decision = await create_m1()
    assert isinstance(created, Memory)
    ctx, action = fake_gate.calls[0]
    assert len(fake_gate.calls) == 1
    assert (action.kind, action.destination) == ("create_memory", "ledger")
    assert action.target.report_id == "rep_setup" and action.target.memory_id == created.id
    assert action.inputs["team_id"] == TEAM
    assert ctx.run_id is None and ctx.request_id == "req_1" and ctx.stamp.kind == "reviewer"
    assert decision.outcome == "allowed" and decision.kind == "create_memory" and decision.request_id == "req_1"
    assert created.id == identity.derive("mem_", TEAM, "dec_reject") and created.id.startswith("mem_")
    document = database.memory(f"{created.id}@v1")
    assert set(document) == {"_id", "memory_id", "version", "team_id", "author", "source", "text", "tags",
                             "status", "supersedes", "decision_id", "stamp", "created_at"}
    assert (document["version"], document["status"], document["supersedes"]) == (1, "active", None)
    assert document["team_id"] == TEAM and document["text"] == M1_TEXT and document["tags"] == TAGS
    assert document["source"] == {"decision_id": "dec_reject", "report_id": "rep_setup"}
    assert document["decision_id"] == decision.id
    assert document["stamp"]["kind"] == "reviewer" and document["stamp"]["run_id"] is None
    assert document["stamp"]["principal"] == "sam" and document["stamp"]["grant_id"] == "sam"
    assert created.created_at is not None and created.created_at.tzinfo is not None


async def test_the_author_is_the_keys_principal(database, fake_gate):
    created, _ = await create_m1()
    assert created.author == "sam"
    other = sam().model_copy(update={"id": "mallory"})
    with pytest.raises(ValueError):
        await create_m1(reviewer=other)
    assert fake_gate.calls[1:] == [] and len(database.memories) == 1


async def test_a_blocked_create_writes_nothing_and_returns_the_decision(database, fake_gate):
    fake_gate.block("create_memory", "destination_action")
    created, decision = await create_m1()
    assert created is None
    assert decision.outcome == "blocked" and decision.failed_check == "destination_action"
    assert database.memories == [] and database.events == []


async def test_create_emits_memory_changed_with_the_reviewer_stamp(database, fake_gate):
    created, decision = await create_m1()
    assert database.events == [{
        "type": "memory_changed",
        "dedupe_key": f"memory_changed|{created.id}@v1|active",
        "stamp": database.memory(f"{created.id}@v1")["stamp"],
        "memory_id": created.id,
        "decision_id": decision.id,
        "status": "active",
        "report_id": "rep_setup",
    }]


async def test_a_repeat_for_the_same_source_decision_finds_the_stored_memory(database, fake_gate):
    first, _ = await create_m1()
    again, second_decision = await create_m1(ctx=reviewer_ctx(request_id="req_2"), text="other words")
    assert again.id == first.id and again.text == M1_TEXT and again.decision_id == first.decision_id
    assert second_decision.request_id == "req_2"
    assert len(database.memories) == 1 and len(database.events) == 1


async def test_a_missing_request_id_is_generated_before_the_gate(database, fake_gate):
    _, decision = await create_m1(ctx=reviewer_ctx(request_id=None))
    assert decision.request_id and fake_gate.calls[0][0].request_id == decision.request_id


async def test_without_a_source_decision_the_id_comes_from_the_gate_decision(database, fake_gate):
    created, decision = await create_m1(source=MemorySource(report_id="rep_setup"))
    assert created.id == identity.derive("mem_", TEAM, decision.id)
    assert fake_gate.calls[0][1].target.memory_id is None


async def test_tags_keep_only_assay_and_claim_kind_and_either_may_be_missing(database, fake_gate):
    created, _ = await create_m1(tags={"assay": None, "claim_kind": CLAIM, "grant": "lbdx"})
    assert created.tags.model_dump() == {"assay": None, "claim_kind": CLAIM}
    untagged, _ = await create_m1(tags=None, source=MemorySource(decision_id="dec_other", report_id="rep_2"))
    assert untagged.tags.model_dump() == {"assay": None, "claim_kind": None}


@pytest.mark.parametrize("changes", [{"text": ""}, {"text": "  "}, {"team_id": ""}])
async def test_create_needs_a_team_and_a_text(database, fake_gate, changes):
    with pytest.raises(ValueError):
        await create_m1(**changes)
    assert fake_gate.calls == [] and database.memories == []


async def test_an_allowed_action_is_set_done_with_its_result(database, fake_gate, monkeypatch):
    evaluate = fake_gate.evaluate

    async def with_action(ctx, action):
        decision = await evaluate(ctx, action)
        await database.collection("actions").insert_one({"_id": "act_1", "decision_id": decision.id, "status": "queued"})
        return decision.model_copy(update={"action_id": "act_1"})

    import dxp.gate
    monkeypatch.setattr(dxp.gate, "evaluate", with_action)
    created, _ = await create_m1()
    action = database.collection("actions").documents[0]
    assert action["status"] == "done"
    assert action["result"] == {"proposal_ids": [], "value_ids": [], "report_id": "rep_setup",
                                "memory_id": created.id, "task_id": None}


# --- correct --------------------------------------------------------------


async def test_correct_writes_a_successor_and_marks_the_old_version_corrected(database, fake_gate):
    m1, _ = await create_m1()
    ctx = reviewer_ctx(request_id="req_c", report_id=None, memory_id=m1.id)
    changed, decision = await memory.correct(m1.id, "new wording", "clearer", ctx)
    _, action = fake_gate.calls[-1]
    assert (action.kind, action.destination, action.target.memory_id) == ("correct_memory", "ledger", m1.id)
    assert action.inputs["memory_version"] == f"{m1.id}@v1" and action.inputs["note"] == "clearer"
    assert decision.kind == "correct_memory" and decision.request_id == "req_c" and decision.cause.memory_id == m1.id
    assert (changed.version, changed.status, changed.text) == (2, "active", "new wording")
    assert changed.supersedes == f"{m1.id}@v1" and changed.decision_id == decision.id and changed.author == "sam"
    assert changed.team_id == TEAM and changed.source == m1.source and changed.tags == m1.tags
    old = database.memory(f"{m1.id}@v1")
    assert old["status"] == "corrected" and old["text"] == M1_TEXT and old["decision_id"] == m1.decision_id
    assert [(e["dedupe_key"].split("|", 1)[1], e["decision_id"]) for e in database.events[1:]] == [
        (f"{m1.id}@v1|corrected", decision.id), (f"{m1.id}@v2|active", decision.id)]
    assert (await store.get(m1.id)).version == 2
    assert (await store.get(m1.id, 1)).status == "corrected"


async def test_a_blocked_correction_changes_nothing(database, fake_gate):
    m1, _ = await create_m1()
    fake_gate.block("correct_memory", "grant_active")
    before = database.snapshot("memories")
    unchanged, decision = await memory.correct(m1.id, "new wording", "note", reviewer_ctx(memory_id=m1.id))
    assert decision.outcome == "blocked" and decision.failed_check == "grant_active"
    assert unchanged == m1 and database.snapshot("memories") == before and len(database.events) == 1


async def test_correct_and_revoke_need_a_note_before_the_gate(database, fake_gate):
    m1, _ = await create_m1()
    for call in (lambda: memory.correct(m1.id, "new wording", " ", reviewer_ctx()),
                 lambda: memory.correct(m1.id, "", "note", reviewer_ctx()),
                 lambda: memory.revoke(m1.id, "", reviewer_ctx())):
        with pytest.raises(ValueError):
            await call()
    assert len(fake_gate.calls) == 1


async def test_only_the_active_latest_version_can_be_changed(database, fake_gate):
    m1, _ = await create_m1()
    await memory.correct(m1.id, "second", "note", reviewer_ctx(request_id="req_2"))
    await memory.revoke(m1.id, "note", reviewer_ctx(request_id="req_3"))
    gate_calls = len(fake_gate.calls)
    with pytest.raises(store.MemoryStateError):
        await memory.correct(m1.id, "third", "note", reviewer_ctx(request_id="req_4"))
    with pytest.raises(store.MemoryStateError):
        await memory.revoke(m1.id, "note", reviewer_ctx(request_id="req_5"))
    assert len(fake_gate.calls) == gate_calls
    assert [(d["version"], d["status"]) for d in database.memories] == [(1, "corrected"), (2, "revoked")]


async def test_an_unknown_memory_is_not_found(database, fake_gate):
    with pytest.raises(store.MemoryNotFound):
        await memory.correct("mem_nope", "text", "note", reviewer_ctx())
    with pytest.raises(store.MemoryNotFound):
        await memory.revoke("mem_nope", "note", reviewer_ctx())
    with pytest.raises(store.MemoryNotFound):
        await store.get("mem_nope")
    assert fake_gate.calls == []


async def test_two_corrections_of_one_version_only_one_wins(database, fake_gate, monkeypatch):
    m1, _ = await create_m1()
    evaluate = fake_gate.evaluate

    async def racing(ctx, action):
        # Another request corrects the same version while this one waits for the gate.
        if action.kind == "correct_memory" and ctx.request_id == "req_slow":
            await memory.correct(m1.id, "fast wording", "note", reviewer_ctx(request_id="req_fast"))
        return await evaluate(ctx, action)

    import dxp.gate
    monkeypatch.setattr(dxp.gate, "evaluate", racing)
    with pytest.raises(store.MemoryStateError):
        await memory.correct(m1.id, "slow wording", "note", reviewer_ctx(request_id="req_slow"))
    assert [(d["version"], d["status"], d["text"]) for d in database.memories] == [
        (1, "corrected", M1_TEXT), (2, "active", "fast wording")]


async def test_a_revocation_that_races_a_correction_stands(database, fake_gate, monkeypatch):
    m1, _ = await create_m1()
    evaluate = fake_gate.evaluate

    async def racing(ctx, action):
        if action.kind == "correct_memory":
            await memory.revoke(m1.id, "note", reviewer_ctx(request_id="req_revoke"))
        return await evaluate(ctx, action)

    import dxp.gate
    monkeypatch.setattr(dxp.gate, "evaluate", racing)
    with pytest.raises(store.MemoryStateError):
        await memory.correct(m1.id, "new wording", "note", reviewer_ctx(request_id="req_correct"))
    assert all(d["status"] != "active" for d in database.memories)
    assert (await store.get(m1.id)).status == "revoked"


# --- revoke ---------------------------------------------------------------


async def test_revoke_marks_the_latest_version_revoked(database, fake_gate):
    m1, _ = await create_m1()
    gone, decision = await memory.revoke(m1.id, "no longer true", reviewer_ctx(request_id="req_r", memory_id=m1.id))
    _, action = fake_gate.calls[-1]
    assert (action.kind, action.target.memory_id, action.inputs["memory_version"]) == ("revoke_memory", m1.id, f"{m1.id}@v1")
    assert decision.kind == "revoke_memory" and decision.request_id == "req_r"
    assert (gone.id, gone.version, gone.status, gone.text) == (m1.id, 1, "revoked", M1_TEXT)
    assert len(database.memories) == 1 and database.memory(f"{m1.id}@v1")["status"] == "revoked"
    assert database.events[-1]["dedupe_key"] == f"memory_changed|{m1.id}@v1|revoked"
    assert database.events[-1]["decision_id"] == decision.id


async def test_a_blocked_revocation_changes_nothing(database, fake_gate):
    m1, _ = await create_m1()
    fake_gate.block("revoke_memory", "team_scope")
    unchanged, decision = await memory.revoke(m1.id, "note", reviewer_ctx(memory_id=m1.id))
    assert decision.outcome == "blocked" and unchanged == m1
    assert database.memory(f"{m1.id}@v1")["status"] == "active" and len(database.events) == 1


async def test_a_retried_reviewer_decision_is_a_new_evaluation(database, fake_gate):
    m1, _ = await create_m1()
    fake_gate.block("revoke_memory")
    _, blocked = await memory.revoke(m1.id, "note", reviewer_ctx(request_id="req_a"))
    fake_gate.blocked.clear()
    _, allowed = await memory.revoke(m1.id, "note", reviewer_ctx(request_id="req_b"))
    assert (blocked.outcome, allowed.outcome) == ("blocked", "allowed")
    assert blocked.request_id != allowed.request_id and blocked.id != allowed.id


# --- reads ----------------------------------------------------------------


async def test_list_latest_is_one_entry_per_memory_for_the_team_only(database, fake_gate):
    m1, _ = await create_m1()
    await memory.correct(m1.id, "second", "note", reviewer_ctx(request_id="req_2"))
    m2, _ = await create_m1(source=MemorySource(decision_id="dec_two", report_id="rep_2"))
    await memory.revoke(m2.id, "note", reviewer_ctx(request_id="req_3"))
    await create_m1(team_id="team_other", source=MemorySource(decision_id="dec_three", report_id="rep_3"))
    listed = await store.list_latest(TEAM)
    assert {(item.id, item.version, item.status) for item in listed} == {(m1.id, 2, "active"), (m2.id, 1, "revoked")}
    assert [(item.id, item.version) for item in await store.list_latest(TEAM, "active")] == [(m1.id, 2)]
    assert [item.id for item in await store.list_latest(TEAM, "revoked")] == [m2.id]
    assert await store.list_latest(TEAM, "corrected") == []
    assert all(item.team_id == TEAM for item in listed)
