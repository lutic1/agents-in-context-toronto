import pytest

from dxp.retrieval import indexes


def by_name(mode):
    return {spec["name"]: spec for spec in indexes.index_definitions(mode)}


def test_auto_mode_defines_three_auto_embed_vector_indexes():
    specs = by_name("auto")
    for name, path in (("vs_source_items", "evidence_text"), ("vs_findings", "summary"),
                       ("vs_memories", "text")):
        spec = specs[name]
        assert spec["type"] == "vectorSearch"
        first = spec["definition"]["fields"][0]
        assert first["type"] == "autoEmbed"
        assert first["path"] == path
        assert first["modality"] == "text"
        assert "numDimensions" not in first


def test_voyage_mode_defines_plain_vector_fields_on_embedding():
    specs = by_name("voyage")
    for name in ("vs_source_items", "vs_findings", "vs_memories"):
        first = specs[name]["definition"]["fields"][0]
        assert first == {"type": "vector", "path": "embedding", "numDimensions": 1024,
                         "similarity": "cosine"}


@pytest.mark.parametrize("mode", ["auto", "voyage"])
def test_every_vector_index_has_the_five_filter_fields(mode):
    for spec in indexes.index_definitions(mode):
        if spec["type"] != "vectorSearch":
            continue
        filters = [f["path"] for f in spec["definition"]["fields"] if f["type"] == "filter"]
        assert filters == ["scope_ids", "team_id", "status", "tags.assay", "tags.claim_kind"]
        assert len(spec["definition"]["fields"]) == 6


def test_none_mode_has_text_indexes_only():
    specs = indexes.index_definitions("none")
    assert not [s for s in specs if s["type"] == "vectorSearch"]
    assert {s["name"] for s in specs if s["type"] == "search"} == {
        "ts_source_items", "ts_findings", "ts_memories"}


@pytest.mark.parametrize("mode", ["auto", "voyage", "none"])
def test_text_fallback_indexes_exist_in_every_mode(mode):
    specs = by_name(mode)
    for collection, path in indexes.TEXT_FIELDS.items():
        search = specs["ts_" + collection]
        fields = search["definition"]["mappings"]["fields"]
        assert search["collection"] == collection
        assert fields[path] == {"type": "string"}
        assert fields["scope_ids"] == {"type": "token"}
        assert fields["tags"]["fields"]["claim_kind"] == {"type": "token"}
        regular = specs["tx_" + collection]
        assert regular["type"] == "text" and regular["keys"] == [(path, "text")]


def test_text_index_never_indexes_the_embedding_or_raw_text():
    for collection in indexes.TEXT_FIELDS:
        fields = indexes.text_index(collection)["definition"]["mappings"]["fields"]
        assert "embedding" not in fields and "raw_text" not in fields
        assert indexes.text_index(collection)["definition"]["mappings"]["dynamic"] is False


def test_embedding_mode_reads_the_environment_and_defaults_to_none(monkeypatch):
    monkeypatch.delenv("DXP_EMBEDDING", raising=False)
    assert indexes.embedding_mode() == "none"
    monkeypatch.setenv("DXP_EMBEDDING", "Voyage")
    assert indexes.embedding_mode() == "voyage"
    assert indexes.embedding_mode("auto") == "auto"


def test_unknown_mode_is_refused():
    with pytest.raises(ValueError):
        indexes.index_definitions("openai")
    with pytest.raises(ValueError):
        indexes.vector_index("findings", "none")


def test_definitions_are_fresh_objects():
    first = indexes.index_definitions("auto")
    first[0]["definition"]["fields"].append("x")
    assert "x" not in indexes.index_definitions("auto")[0]["definition"]["fields"]


class Cursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for doc in self.docs:
            yield doc


class FakeCollection:
    def __init__(self, existing, fail=False):
        self.existing = list(existing)
        self.created = []
        self.regular = []
        self.fail = fail

    async def list_search_indexes(self):
        return Cursor({"name": name, "queryable": True} for name in self.existing)

    async def create_search_index(self, model):
        if self.fail:
            raise RuntimeError("search is not available on this cluster")
        self.created.append(model)
        self.existing.append(model["name"])

    async def create_index(self, keys, name=None):
        self.regular.append((keys, name))


class FakeDb:
    def __init__(self, existing=(), fail=False):
        self.collections = {}
        self.existing = existing
        self.fail = fail

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = FakeCollection(
                [n for n in self.existing if n.endswith("_" + name)], self.fail)
        return self.collections[name]

    def created(self):
        return [m["name"] for c in self.collections.values() for m in c.created]


@pytest.fixture
def fake_db(monkeypatch):
    from dxp import store

    def install(db, mode):
        monkeypatch.setattr(store, "db", lambda: db)
        monkeypatch.setenv("DXP_EMBEDDING", mode)
        return db

    return install


async def test_ensure_indexes_creates_what_is_missing(fake_db):
    db = fake_db(FakeDb(), "auto")
    assert await indexes.ensure_indexes() is None
    assert db.created() == ["vs_source_items", "ts_source_items", "vs_findings", "ts_findings",
                            "vs_memories", "ts_memories"]
    model = db["memories"].created[0]
    assert set(model) == {"name", "type", "definition"}
    assert model["name"] == "vs_memories" and model["type"] == "vectorSearch"
    assert db["memories"].regular == [([("text", "text")], "tx_memories")]


async def test_ensure_indexes_skips_existing_and_makes_no_vector_index_in_none_mode(fake_db):
    db = fake_db(FakeDb(existing=("ts_findings",)), "none")
    await indexes.ensure_indexes()
    assert sorted(db.created()) == ["ts_memories", "ts_source_items"]
    assert all(m["type"] == "search" for c in db.collections.values() for m in c.created)


async def test_ensure_indexes_is_safe_to_run_twice(fake_db):
    db = fake_db(FakeDb(), "auto")
    await indexes.ensure_indexes()
    await indexes.ensure_indexes()
    assert len(db.created()) == 6


async def test_ensure_indexes_never_raises_when_an_index_cannot_be_built(fake_db):
    db = fake_db(FakeDb(fail=True), "auto")
    assert await indexes.ensure_indexes() is None
    assert db["findings"].regular == [([("summary", "text")], "tx_findings")]


async def test_ensure_indexes_never_raises_without_a_database(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    assert await indexes.ensure_indexes() is None


async def test_index_status_reports_queryable(fake_db):
    fake_db(FakeDb(existing=("ts_findings",)), "none")
    assert await indexes.index_status() == {"ts_source_items": False, "ts_findings": True,
                                            "ts_memories": False}
    assert await indexes.wait_until_queryable(timeout_s=0, poll_s=0) is False


async def test_ensure_indexes_in_voyage_mode_never_embeds_memories(fake_db, monkeypatch):
    """Only `memory` writes `memories` (AD-28); setup embeds the other collections."""
    import importlib

    embed_module = importlib.import_module("dxp.retrieval.embed")
    seen = []

    async def embed_missing(db, match=None, collections=None):
        seen.append(collections)
        return 0

    monkeypatch.setattr(embed_module, "embed_missing", embed_missing)
    fake_db(FakeDb(), "voyage")
    await indexes.ensure_indexes()
    assert len(seen) == 1 and "memories" not in seen[0] and set(seen[0]) == set(indexes.TEXT_FIELDS) - {"memories"}
