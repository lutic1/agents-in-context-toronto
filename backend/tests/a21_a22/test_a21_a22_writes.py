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


@pytest.mark.parametrize("source", [
    MemorySource(report_id="rep_setup"), MemorySource(decision_id="dec_reject"), MemorySource(),
    MemorySource(decision_id=" ", report_id="rep_setup"), None,
])
async def test_create_needs_the_source_decision_and_report_before_the_gate(database, fake_gate, source):
    with pytest.raises(ValueError, match="source"):
        await create_m1(source=source)
    assert fake_gate.calls == [] and database.memories == [] and database.events == []


async def test_tags_keep_only_assay_and_claim_kind_and_either_may_be_missing(database, fake_gate):
    created, _ = await create_m1(tags={"assay": None, "claim_kind": CLAIM, "grant": "lbdx"})
    assert created.tags.model_dump() == {"assay": None, "claim_kind": CLAIM}


async def test_a_correction_that_names_no_claim_kind_is_tagged_reviewer_correction(database, fake_gate):
    for n, tags in enumerate((None, {}, {"assay": "A"}, {"assay": "A", "claim_kind": None})):
        untagged, _ = await create_m1(tags=tags, source=MemorySource(decision_id=f"dec_{n}", report_id="rep_2"))
        assert untagged.tags.claim_kind == "reviewer_correction"


@pytest.mark.parametrize("claim_kind", ["claim_performed_or_results", "claim_planned", "claim_preclinical", "reviewer_correction"])
async def test_the_claim_kind_is_one_of_the_gates_kinds_or_reviewer_correction(database, fake_gate, claim_kind):
    created, _ = await create_m1(tags={"assay": None, "claim_kind": claim_kind})
    assert created.tags.claim_kind == claim_kind


@pytest.mark.parametrize("claim_kind", ["outcome_claim_without_results", "Claim_Planned", "anything"])
async def test_any_other_claim_kind_is_refused_before_the_gate(database, fake_gate, claim_kind):
    with pytest.raises(ValueError, match="claim_kind"):
        await create_m1(tags={"assay": None, "claim_kind": claim_kind})
    assert fake_gate.calls == [] and database.memories == []


@pytest.mark.parametrize("changes", [{"text": ""}, {"text": "  "}, {"team_id": ""}])
async def test_create_needs_a_team_and_a_text(database, fake_gate, changes):
    with pytest.raises(ValueError):
        await create_m1(**changes)
    assert fake_gate.calls == [] and database.memories == []


def gate_with_actions(database, fake_gate, monkeypatch):
    """The fake gate as Governance: it inserts the queued action an allowed Decision gets
    (AD-19) and offers A06's `gate.mark_action(action_id, status, result=None, *, session=None)`,
    the only way an action is settled (V65)."""
    import dxp.gate

    evaluate = fake_gate.evaluate
    actions = FakeActions()

    async def mark_action(action_id, status, result=None, *, session=None):
        action = next(a for a in actions if a["_id"] == action_id)
        if action["status"] != "queued":
            return False
        action.update(status=status, result=result)
        return True

    monkeypatch.setattr(dxp.gate, "mark_action", mark_action, raising=False)

    async def with_action(ctx, action):
        decision = await evaluate(ctx, action)
        if decision.outcome != "allowed":
            return decision
        action_id = f"act_{len(fake_gate.calls)}"
        actions.append({"_id": action_id, "decision_id": decision.id, "status": "queued", "result": None})
        return decision.model_copy(update={"action_id": action_id})

    monkeypatch.setattr(dxp.gate, "evaluate", with_action)
    return actions


class FakeActions(list):
    """Governance's own actions, held outside the database the memory code can reach."""


class WriteFailed(Exception):
    """Stands in for a pymongo WriteError (a validator rejection) or a lost connection."""


async def test_an_allowed_action_is_set_done_with_its_result(database, fake_gate, monkeypatch):
    actions = gate_with_actions(database, fake_gate, monkeypatch)
    created, _ = await create_m1()
    action = actions[0]
    assert action["status"] == "done" and "actions" not in database.opened
    assert action["result"] == {"proposal_ids": [], "value_ids": [], "report_id": "rep_setup",
                                "memory_id": created.id, "task_id": None}


async def test_the_memory_code_never_writes_actions_or_runs_itself(database, fake_gate, monkeypatch):
    """V65: with or without Governance's helper, memory opens only `memories`."""
    import dxp.gate

    async def with_action_id(ctx, action, evaluate=fake_gate.evaluate):
        return (await evaluate(ctx, action)).model_copy(update={"action_id": "act_1"})

    monkeypatch.setattr(dxp.gate, "evaluate", with_action_id)
    monkeypatch.delattr(dxp.gate, "mark_action", raising=False)  # as on main before A06 merges
    created, _ = await create_m1()
    await memory.correct(created.id, "new wording", "note", reviewer_ctx(request_id="req_2"))
    await memory.revoke(created.id, "note", reviewer_ctx(request_id="req_3"))
    assert set(database.opened) == {"memories"}
    gate_with_actions(database, fake_gate, monkeypatch)
    other, _ = await create_m1(source=MemorySource(decision_id="dec_two", report_id="rep_2"))
    await memory.revoke(other.id, "note", reviewer_ctx(request_id="req_4"))
    assert set(database.opened) == {"memories"}


async def test_a_failed_write_after_an_allowed_create_marks_the_action_failed(database, fake_gate, monkeypatch):
    actions = gate_with_actions(database, fake_gate, monkeypatch)
    database.collection("memories").fail_next_insert = WriteFailed("Document failed validation")
    with pytest.raises(WriteFailed):
        await create_m1()
    assert [a["status"] for a in actions] == ["failed"]
    assert database.memories == [] and database.events == []


# --- correct --------------------------------------------------------------


async def test_correct_writes_a_successor_and_marks_the_old_version_corrected(database, fake_gate):
    m1, _ = await create_m1()
    ctx = reviewer_ctx(request_id="req_c", report_id=None, memory_id=m1.id)
    changed, decision = await memory.correct(m1.id, "new wording", "clearer", ctx)
    _, action = fake_gate.calls[-1]
    assert (action.kind, action.destination, action.target.memory_id) == ("correct_memory", "ledger", m1.id)
    assert action.inputs["memory_version"] == 1 and action.inputs["team_id"] == TEAM and action.inputs["note"] == "clearer"
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
    # The correction wrote nothing: no successor exists and the revocation stands.
    assert [(d["version"], d["status"]) for d in database.memories] == [(1, "revoked")]
    assert (await store.get(m1.id)).status == "revoked"
    assert [e["status"] for e in database.events] == ["active", "revoked"]


async def test_the_old_version_is_marked_corrected_before_the_successor_is_written(database, fake_gate, monkeypatch):
    m1, _ = await create_m1()
    memories = database.collection("memories")
    seen = []
    insert_one = memories.insert_one

    async def watching(document, **kwargs):
        seen.append([(d["version"], d["status"]) for d in memories.documents])
        # A revocation arriving now finds no active version and is refused.
        with pytest.raises(store.MemoryStateError):
            await memory.revoke(m1.id, "note", reviewer_ctx(request_id="req_revoke"))
        await insert_one(document, **kwargs)

    monkeypatch.setattr(memories, "insert_one", watching)
    changed, _ = await memory.correct(m1.id, "new wording", "note", reviewer_ctx(request_id="req_c"))
    assert seen == [[(1, "corrected")]]
    assert [(d["version"], d["status"]) for d in database.memories] == [(1, "corrected"), (2, "active")]
    assert changed.version == 2


async def test_a_failed_successor_insert_restores_the_old_version_and_fails_the_action(database, fake_gate, monkeypatch):
    m1, _ = await create_m1()
    actions = gate_with_actions(database, fake_gate, monkeypatch)
    database.collection("memories").fail_next_insert = WriteFailed("Document failed validation")
    with pytest.raises(WriteFailed):
        await memory.correct(m1.id, "new wording", "note", reviewer_ctx(request_id="req_c"))
    assert [(d["version"], d["status"], d["text"]) for d in database.memories] == [(1, "active", M1_TEXT)]
    assert [a["status"] for a in actions] == ["failed"] and len(database.events) == 1
    # The memory can still be corrected afterwards.
    changed, _ = await memory.correct(m1.id, "new wording", "note", reviewer_ctx(request_id="req_d"))
    assert (changed.version, changed.status) == (2, "active")


async def test_a_lost_race_marks_the_action_failed(database, fake_gate, monkeypatch):
    m1, _ = await create_m1()
    actions = gate_with_actions(database, fake_gate, monkeypatch)
    memories = database.collection("memories")
    update_one = memories.update_one

    async def revoked_first(query, update, **kwargs):
        # Another request revokes the version between the gate and the guard.
        next(d for d in memories.documents if d["_id"] == query["_id"])["status"] = "revoked"
        monkeypatch.setattr(memories, "update_one", update_one)
        return await update_one(query, update, **kwargs)

    monkeypatch.setattr(memories, "update_one", revoked_first)
    with pytest.raises(store.MemoryStateError):
        await memory.correct(m1.id, "new wording", "note", reviewer_ctx(request_id="req_c"))
    assert [(d["version"], d["status"]) for d in database.memories] == [(1, "revoked")]
    assert [a["status"] for a in actions] == ["failed"]


# --- revoke ---------------------------------------------------------------


async def test_revoke_marks_the_latest_version_revoked(database, fake_gate):
    m1, _ = await create_m1()
    gone, decision = await memory.revoke(m1.id, "no longer true", reviewer_ctx(request_id="req_r", memory_id=m1.id))
    _, action = fake_gate.calls[-1]
    assert (action.kind, action.target.memory_id, action.inputs["memory_version"]) == ("revoke_memory", m1.id, 1)
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


# --- stored form ----------------------------------------------------------


async def test_stored_versions_have_the_ids_and_types_the_memories_validator_requires(database, fake_gate, monkeypatch):
    """The patterns of A03's `memories` validator, checked without Atlas."""
    import re
    from datetime import datetime

    from a21_a22_fakes import dec, install_hex_gate, rep

    install_hex_gate(fake_gate, monkeypatch)
    source = MemorySource(decision_id=dec("reject"), report_id=rep("setup"))
    created, _ = await create_m1(source=source)
    await memory.correct(created.id, "new wording", "note", reviewer_ctx(request_id="req_2"))
    await memory.revoke(created.id, "note", reviewer_ctx(request_id="req_3"))
    decision_id, memory_ref = re.compile(r"^dec_[0-9a-f]{16}$"), re.compile(r"^mem_[0-9a-f]{16}@v[1-9][0-9]*$")
    assert len(database.memories) == 2
    for document in database.memories:
        assert memory_ref.match(document["_id"]) and re.match(r"^mem_[0-9a-f]{16}$", document["memory_id"])
        assert document["_id"] == f"{document['memory_id']}@v{document['version']}"
        assert decision_id.match(document["decision_id"]) and decision_id.match(document["source"]["decision_id"])
        assert isinstance(document["created_at"], datetime) and "embedding" not in document
        assert all(document[key] for key in ("team_id", "author", "text"))
        assert set(document["tags"]) == {"assay", "claim_kind"}
    first, second = database.memories
    assert first["supersedes"] is None and second["supersedes"] == first["_id"]
    # The same documents against A03's own schema: every required key, every pattern.
    from dxp.store.schemas.memories import JSON_SCHEMA

    def check(schema, value, path):
        for key in schema.get("required", []):
            assert key in value, f"{path}.{key} is required"
        for key, rule in schema.get("properties", {}).items():
            if key not in value:
                continue
            if "pattern" in rule:
                assert isinstance(value[key], str) and re.search(rule["pattern"], value[key]), f"{path}.{key}"
            if rule.get("bsonType") == "object":
                check(rule, value[key], f"{path}.{key}")
            if "enum" in rule and rule.get("bsonType") == "string":
                assert value[key] in rule["enum"], f"{path}.{key}"

    for document in database.memories:
        check(JSON_SCHEMA, document, document["_id"])
