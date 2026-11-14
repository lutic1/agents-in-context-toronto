"""A13 on the Atlas Sandbox (skipped without MONGODB_URI), in the session's test database
(`dxp_test_<hex>`, dropped afterwards), never `dxp` or `dxp_smoke`.

- The FDA rows and the seed (through the fake ledger and fake gate) are idempotent on Atlas.
- GET /teams reads the seeded Teams.
- reset_demo.py snapshots a throwaway database with mongodump and restores it into another
  throwaway database with mongorestore, validators and indexes intact (skipped when the
  MongoDB Database Tools are not installed: OD6).
"""

from __future__ import annotations

import os
import secrets
import shutil
from datetime import UTC, datetime

import pytest

from dxp.ledger import seed as seed_mod
from dxp.sources import fda_cdx

pytestmark = [pytest.mark.atlas, pytest.mark.asyncio(loop_scope="session")]

FETCHED = datetime(2026, 11, 14, 13, 0, tzinfo=UTC)


async def _counts(db, names) -> dict[str, int]:
    return {n: await db[n].count_documents({}) for n in names}


async def test_fda_rows_and_seed_are_idempotent_on_atlas(db, fda_page, fake_gate) -> None:
    from .conftest import FakeLedger

    rows = fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page))
    assert (await fda_cdx.store_rows(db, rows, fetched_at=FETCHED))["inserted"] == len(rows)
    ledger = FakeLedger(db)
    first = await seed_mod.seed(db, file=ledger.file)
    names = ("source_items", "source_versions", "aliases", "diagnostics", "proposals", "decisions", "teams")
    before = await _counts(db, names)
    assert first.filed > 0 and before["teams"] == 3

    await fda_cdx.store_rows(db, rows, fetched_at=datetime(2026, 11, 15, tzinfo=UTC))
    second = await seed_mod.seed(db, file=ledger.file)
    assert second.filed == 0 and await _counts(db, names) == before

    from dxp.api import routes_teams

    teams = await routes_teams.list_teams()
    assert {t.name for t in teams.items} == {t["name"] for t in seed_mod.TEAMS}
    assert all(t.synthetic for t in teams.items)


@pytest.mark.skipif(
    not (shutil.which("mongodump") and shutil.which("mongorestore")),
    reason="mongodump/mongorestore are not installed: the reset round trip is skipped (OD6)",
)
def test_reset_round_trip_keeps_validators_and_indexes(reset_demo, tmp_path) -> None:
    from pymongo import MongoClient

    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri, tz_aware=True)
    src, dst = f"dxp_test_a13_{secrets.token_hex(4)}", f"dxp_test_a13_{secrets.token_hex(4)}"
    assert {src, dst}.isdisjoint({"dxp", "dxp_smoke"})
    validator = {"$jsonSchema": {"bsonType": "object", "required": ["name"]}}
    try:
        for name in (src, dst):
            db = client[name]
            db.create_collection("teams", validator=validator, validationLevel="strict", validationAction="error")
            db["teams"].create_index("name", name="name")
            db.create_collection("memories")
        client[src]["teams"].insert_many([{"_id": "team_a", "name": "A"}, {"_id": "team_b", "name": "B"}])
        client[src]["memories"].insert_one({"_id": "mem_1@v1", "status": "active"})
        client[dst]["teams"].insert_one({"_id": "stale", "name": "Stale"})

        snap = tmp_path / "snap"
        reset_demo.snapshot(client, src, snap, uri=uri)
        restored = reset_demo.restore(client, dst, snap, uri=uri)
        assert restored["teams"] == 2 and restored["memories"] == 1
        target = client[dst]
        assert sorted(d["_id"] for d in target["teams"].find()) == ["team_a", "team_b"]
        info = target.command("listCollections", filter={"name": "teams"})["cursor"]["firstBatch"][0]
        assert info["options"]["validator"] == validator  # kept: emptied with delete_many, never dropped
        assert "name" in target["teams"].index_information()
        assert sorted(d["_id"] for d in client[src]["teams"].find()) == ["team_a", "team_b"]  # source untouched
    finally:
        client.drop_database(src)
        client.drop_database(dst)
        client.close()
