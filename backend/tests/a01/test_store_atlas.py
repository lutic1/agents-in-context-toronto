"""A01 store on the Atlas Sandbox (skipped without MONGODB_URI): indexes, validators hook, emit_event."""

from __future__ import annotations

import pytest
from pymongo.errors import DuplicateKeyError

pytestmark = [pytest.mark.atlas, pytest.mark.asyncio(loop_scope="session")]


async def test_ensure_indexes_creates_every_collection_and_is_repeatable(db) -> None:
    from dxp import store

    await store.ensure_indexes()  # a second run changes nothing
    names = set(await db.list_collection_names())
    assert set(store.COLLECTIONS) <= names
    admissions = await db["admissions"].index_information()
    assert admissions["run_item"]["unique"] and admissions["run_item"]["key"] == [("run_id", 1), ("item_key", 1)]
    memories = await db["memories"].index_information()
    assert memories["memory_version"]["unique"]
    assert "status" in await db["runs"].index_information()


async def test_admissions_unique_on_run_and_item(db) -> None:
    doc = {"run_id": "run_t", "item_key": "k|file_proposal|-|-", "status": "admitted"}
    await db["admissions"].insert_one({"_id": "adm_t1", **doc})
    with pytest.raises(DuplicateKeyError):
        await db["admissions"].insert_one({"_id": "adm_t2", **doc})


async def test_emit_event_assigns_increasing_seq_and_dedupes(db) -> None:
    from dxp.store import emit_event

    stamp = {"kind": "run", "principal": "dxp-curator", "run_id": "run_t"}
    first = await emit_event("action_allowed", dedupe_key="t:1", stamp=stamp, run_id="run_t", decision_id="dec_1")
    second = await emit_event("action_blocked", dedupe_key="t:2", stamp=stamp, run_id="run_t", decision_id="dec_2")
    again = await emit_event("action_allowed", dedupe_key="t:1", stamp=stamp, run_id="run_t", decision_id="dec_1")
    assert second == first + 1 and again == first
    stored = await db["events"].find_one({"_id": first})
    assert stored["type"] == "action_allowed" and stored["stamp"] == stamp


async def test_validators_from_store_schemas_are_applied(db, monkeypatch) -> None:
    from dxp import store
    from dxp.store import schemas

    monkeypatch.setattr(schemas, "VALIDATORS", {"policy_sets": {"bsonType": "object", "required": ["members"]}})
    await store.ensure_indexes()
    info = await db.command({"listCollections": 1, "filter": {"name": "policy_sets"}})
    options = info["cursor"]["firstBatch"][0]["options"]
    assert options["validator"]["$jsonSchema"]["required"] == ["members"]
    assert options["validationLevel"] == "strict" and options["validationAction"] == "error"


async def test_emit_event_accepts_an_event_document(db) -> None:
    from dxp import store

    seq = await store.emit_event({"type": "report_filed", "dedupe_key": "t:doc", "stamp": {"kind": "run", "principal": "dxp-curator"}, "report_id": "rep_t"})
    again = await store.emit_event({"type": "report_filed", "dedupe_key": "t:doc", "stamp": None})
    assert again == seq
    assert (await store.collection("events").find_one({"_id": seq}))["report_id"] == "rep_t"
    assert store.db().name == db.name
