import copy
import importlib

import pytest
from dxp.memory import store

# dxp.memory.retrieve is the frozen function; the module of the same name is fetched by path.
retrieve = importlib.import_module("dxp.memory.retrieve")

STAMP = {"kind": "reviewer", "run_id": None, "agent": None, "principal": "sam"}
M1_TEXT = "Terminated trial with no posted results: describe its status; do not state outcomes"

DOCUMENT_KEYS = {
    "_id", "memory_id", "version", "team_id", "author", "source", "text", "tags",
    "status", "supersedes", "decision_id", "stamp", "created_at",
}
API_KEYS = {
    "id", "version", "team_id", "author", "source", "text", "tags",
    "status", "supersedes", "decision_id", "created_at",
}


def m1(**changes):
    fields = dict(
        memory_id="mem_m1",
        team_id="team_lbdx",
        author="sam",
        source={"decision_id": "dec_reject", "report_id": "rep_setup"},
        text=M1_TEXT,
        tags={"assay": "Guardant360 CDx", "claim_kind": "claim_performed_or_results"},
        decision_id="dec_create",
        stamp=STAMP,
        created_at="2026-11-14T14:10:00Z",
    )
    fields.update(changes)
    return store.new_memory(**fields)


def correct(current, text="Say the trial was terminated; state no outcomes"):
    return store.corrected_successor(
        current, text, "sam", "dec_correct", STAMP, "2026-11-14T15:00:00Z"
    )


def test_version_one_document_follows_the_spine_shape():
    assert m1() == {
        "_id": "mem_m1@v1",
        "memory_id": "mem_m1",
        "version": 1,
        "team_id": "team_lbdx",
        "author": "sam",
        "source": {"decision_id": "dec_reject", "report_id": "rep_setup"},
        "text": M1_TEXT,
        "tags": {"assay": "Guardant360 CDx", "claim_kind": "claim_performed_or_results"},
        "status": "active",
        "supersedes": None,
        "decision_id": "dec_create",
        "stamp": STAMP,
        "created_at": "2026-11-14T14:10:00Z",
    }
    assert set(m1()) == DOCUMENT_KEYS


def test_only_the_named_source_and_tag_fields_are_kept():
    memory = m1(
        source={"decision_id": "d", "report_id": "r", "name": "someone"},
        tags={"assay": "A", "claim_kind": "k", "grant": "lbdx"},
    )
    assert memory["source"] == {"decision_id": "d", "report_id": "r"}
    assert memory["tags"] == {"assay": "A", "claim_kind": "k"}


def test_either_tag_may_be_missing():
    assert m1(tags={"claim_kind": "k"})["tags"] == {"assay": None, "claim_kind": "k"}
    assert m1(tags={"assay": "A"})["tags"] == {"assay": "A", "claim_kind": None}
    assert m1(tags=None)["tags"] == {"assay": None, "claim_kind": None}


@pytest.mark.parametrize("field", ["memory_id", "team_id", "author", "text", "decision_id"])
@pytest.mark.parametrize("value", ["", "   ", None])
def test_required_text_fields(field, value):
    with pytest.raises(ValueError):
        m1(**{field: value})


def test_the_document_does_not_share_the_callers_dicts():
    source = {"decision_id": "d", "report_id": "r"}
    tags = {"assay": "A", "claim_kind": "k"}
    stamp = dict(STAMP)
    memory = m1(source=source, tags=tags, stamp=stamp)
    source["report_id"] = "changed"
    tags["claim_kind"] = "changed"
    stamp["principal"] = "changed"
    assert memory["source"]["report_id"] == "r"
    assert memory["tags"]["claim_kind"] == "k"
    assert memory["stamp"]["principal"] == "sam"


def test_version_key():
    assert store.version_key("mem_m1", 3) == "mem_m1@v3"
    for version in (0, -1, "1", 1.0, True, None):
        with pytest.raises(ValueError):
            store.version_key("mem_m1", version)


def test_correction_writes_a_successor_and_marks_the_old_version_corrected():
    v1 = m1()
    before = copy.deepcopy(v1)
    v2, old = correct(v1, "new wording")
    assert v1 == before
    assert old == {**before, "status": "corrected"}
    assert old["text"] == M1_TEXT
    assert v2 == {
        "_id": "mem_m1@v2",
        "memory_id": "mem_m1",
        "version": 2,
        "team_id": "team_lbdx",
        "author": "sam",
        "source": {"decision_id": "dec_reject", "report_id": "rep_setup"},
        "text": "new wording",
        "tags": {"assay": "Guardant360 CDx", "claim_kind": "claim_performed_or_results"},
        "status": "active",
        "supersedes": "mem_m1@v1",
        "decision_id": "dec_correct",
        "stamp": STAMP,
        "created_at": "2026-11-14T15:00:00Z",
    }


def test_a_second_correction_chains_from_the_latest_version():
    v2, _ = correct(m1())
    v3, v2_old = correct(v2, "third wording")
    assert (v3["_id"], v3["version"], v3["supersedes"]) == ("mem_m1@v3", 3, "mem_m1@v2")
    assert v2_old["status"] == "corrected"


def test_correction_needs_a_text():
    for text in ("", "  ", None):
        with pytest.raises(ValueError):
            correct(m1(), text)


def test_revoke_marks_the_version_revoked_and_changes_nothing_else():
    v1 = m1()
    before = copy.deepcopy(v1)
    gone = store.revoked(v1)
    assert v1 == before
    assert gone == {**before, "status": "revoked"}


def test_allowed_transitions():
    allowed = {("active", "corrected"), ("active", "revoked")}
    for current in store.STATUSES:
        for new in store.STATUSES:
            assert store.can_transition(current, new) == ((current, new) in allowed)
    assert not store.can_transition("unknown", "active")
    assert not store.can_transition(None, "revoked")
    assert not store.can_transition("active", "deleted")


def test_nothing_follows_corrected_or_revoked():
    v1 = m1()
    _, old = correct(v1)
    gone = store.revoked(v1)
    for final in (old, gone):
        with pytest.raises(store.MemoryStateError):
            correct(final)
        with pytest.raises(store.MemoryStateError):
            store.revoked(final)
        for status in store.STATUSES:
            with pytest.raises(store.MemoryStateError):
                store.with_status(final, status)


def test_an_active_version_cannot_be_set_active_again():
    with pytest.raises(store.MemoryStateError):
        store.with_status(m1(), "active")


def test_api_shape_has_no_embedding_stamp_or_document_id():
    document = m1()
    document["embedding"] = [0.1, 0.2]
    memory = store.to_api(document)
    assert set(memory) == API_KEYS
    assert memory["id"] == "mem_m1"
    assert memory["supersedes"] is None
    v2, _ = correct(m1())
    assert store.to_api(v2)["supersedes"] == "mem_m1@v1"
    memory["tags"]["claim_kind"] = "changed"
    assert document["tags"]["claim_kind"] == "claim_performed_or_results"


def test_api_shape_validates_as_the_frozen_memory_model():
    from dxp.api.models import Memory

    v2, _ = correct(m1())
    memory = store.to_model(v2)
    assert isinstance(memory, Memory)
    assert (memory.id, memory.version, memory.status, memory.supersedes) == ("mem_m1", 2, "active", "mem_m1@v1")
    assert set(Memory.model_fields) == API_KEYS


def test_statuses_agree_between_store_and_retrieve():
    assert retrieve.ACTIVE == store.ACTIVE == "active"
