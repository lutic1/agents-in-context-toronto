"""A02 against Atlas: exact resolution over a real ``aliases`` collection.

Runs only when MONGODB_URI is set, in a throwaway database named
``dxp_test_a02_<hex>`` that is dropped afterwards; it never touches ``dxp``
or ``DXP_DB``. Until A01's store and conftest are on main this test opens its
own client; after the rebase it should use A01's sandbox fixture.
"""

from __future__ import annotations

import os
import uuid

import pytest
from dxp.identity import diagnostic_id, resolve_exact

MONGODB_URI = os.environ.get("MONGODB_URI")

pytestmark = pytest.mark.skipif(
    not MONGODB_URI,
    reason="MONGODB_URI is not set: the Atlas Sandbox test of exact resolution is skipped",
)


@pytest.fixture
def atlas_aliases(alias_doc, seeded_trade_names):
    pymongo = pytest.importorskip("pymongo", reason="pymongo is not installed")
    client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10_000)
    name = f"dxp_test_a02_{uuid.uuid4().hex[:12]}"
    assert name not in ("dxp", os.environ.get("DXP_DB")), "never run in the demo database"
    db = client[name]
    try:
        coll = db["aliases"]
        coll.insert_many([alias_doc(t) for t in seeded_trade_names])
        yield coll
    finally:
        client.drop_database(name)
        client.close()


def test_atlas_exact_resolution(atlas_aliases):
    assert resolve_exact("FoundationOne CDx", aliases=atlas_aliases) == diagnostic_id(
        "FoundationOne CDx"
    )
    assert resolve_exact("FoundationOne Liquid CDx", aliases=atlas_aliases) == diagnostic_id(
        "FoundationOne Liquid CDx"
    )
    assert resolve_exact("Guardant360 Liquid CDx", aliases=atlas_aliases) == diagnostic_id(
        "Guardant360® Liquid CDx"
    )
    for name in ("FoundationOne Liquid", "Guardant360", "FoundationOne"):
        assert resolve_exact(name, aliases=atlas_aliases) is None
