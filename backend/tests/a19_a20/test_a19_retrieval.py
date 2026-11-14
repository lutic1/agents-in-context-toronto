import importlib

import pytest

related_module = importlib.import_module("dxp.retrieval.related")
embed_module = importlib.import_module("dxp.retrieval.embed")
from dxp import retrieval

SCOPE = "scope_plasma"
ANCHOR = "ctgov:NCT04712877"
S1 = {"_id": "ctgov:NCT00000001", "source_ref": "ctgov:NCT00000001", "scope_ids": [SCOPE],
      "current_version_id": "sv_1111111111111111", "evidence_text": "plasma ctDNA genotyping"}
S2 = {"_id": "ctgov:NCT00000002", "source_ref": "ctgov:NCT00000002", "scope_ids": [SCOPE],
      "current_version_id": "sv_2222222222222222", "evidence_text": "liquid biopsy"}
SELF = {"_id": ANCHOR, "source_ref": ANCHOR, "scope_ids": [SCOPE], "current_version_id": "sv_aaaaaaaaaaaaaaaa"}
OTHER = {"_id": "ctgov:NCT00000009", "source_ref": "ctgov:NCT00000009", "scope_ids": ["scope_other"],
         "current_version_id": "sv_9999999999999999"}
F1 = {"_id": "f_1111111111111111", "source_ref": "ctgov:NCT00000001", "version_id": "sv_1111111111111111"}
F9 = {"_id": "f_9999999999999999", "source_ref": "ctgov:NCT00000009", "version_id": "sv_9999999999999999"}


def scored(*pairs):
    return lambda pipeline: [dict(doc, score=score) for doc, score in pairs]


def stage(collection, name):
    return [p[0][name] for p in collection.pipelines if name in p[0]]


@pytest.fixture
def seeded(mongo):
    mongo["source_items"].add(S1, S2, SELF, OTHER)
    mongo["findings"].add(F1, F9)
    return mongo


async def test_auto_mode_runs_vector_search_filtered_to_the_scope(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")
    seeded["source_items"].on_aggregate = scored((SELF, 0.99), (S1, 0.9), (S2, 0.5))
    seeded["findings"].on_aggregate = scored((F1, 0.7), (F9, 0.95))
    result = await retrieval.related(SCOPE, "early-stage profiling", 3, [ANCHOR])
    assert result.method == "vector_search"
    assert result.index == "vs_source_items+vs_findings"
    assert result.top_k == 3 and result.filter.scope_id == SCOPE
    assert [(i.ref, i.version_id, i.score) for i in result.items] == [
        ("ctgov:NCT00000001", "sv_1111111111111111", 0.9),
        ("f_1111111111111111", "sv_1111111111111111", 0.7),
        ("ctgov:NCT00000002", "sv_2222222222222222", 0.5),
    ]
    search = stage(seeded["source_items"], "$vectorSearch")[0]
    assert search["index"] == "vs_source_items" and search["path"] == "evidence_text"
    assert search["query"] == {"text": "early-stage profiling"} and "queryVector" not in search
    assert search["filter"] == {"$and": [{"scope_ids": {"$eq": SCOPE}}]}
    assert stage(seeded["findings"], "$vectorSearch")[0]["path"] == "summary"


async def test_the_item_itself_and_other_scopes_are_never_returned(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")
    seeded["source_items"].on_aggregate = scored((SELF, 0.99), (S1, 0.9))
    seeded["findings"].on_aggregate = scored((F9, 0.95), (dict(F1, _id="f_self", source_ref=ANCHOR), 0.9))
    result = await retrieval.related(SCOPE, "text", 5, [ANCHOR])
    assert [i.ref for i in result.items] == ["ctgov:NCT00000001"]


async def test_voyage_mode_queries_the_embedding_path_with_a_query_vector(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "voyage")

    async def fake_query(text):
        return [0.1, 0.2]

    monkeypatch.setattr(related_module, "embed_query", fake_query)
    seeded["source_items"].on_aggregate = scored((S1, 0.8))
    seeded["findings"].on_aggregate = scored()
    result = await retrieval.related(SCOPE, "text", 2)
    assert result.method == "vector_search"
    search = stage(seeded["source_items"], "$vectorSearch")[0]
    assert search["path"] == "embedding" and search["queryVector"] == [0.1, 0.2] and "query" not in search


async def test_none_mode_never_runs_vector_search_and_says_text_search(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "none")
    seeded["source_items"].on_aggregate = scored((S1, 3.2))
    seeded["findings"].on_aggregate = scored((F1, 1.1))
    result = await retrieval.related(SCOPE, "text", 5, [ANCHOR])
    assert result.method == "text_search" and result.index == "ts_source_items+ts_findings"
    assert [i.ref for i in result.items] == ["ctgov:NCT00000001", "f_1111111111111111"]
    assert not stage(seeded["source_items"], "$vectorSearch")
    search = stage(seeded["source_items"], "$search")[0]
    assert search["index"] == "ts_source_items"
    assert search["compound"]["filter"] == [{"equals": {"path": "scope_ids", "value": SCOPE}}]


async def test_a_failed_vector_query_falls_back_to_text_search(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")

    def handler(pipeline):
        if "$vectorSearch" in pipeline[0]:
            raise RuntimeError("index not found")
        return [dict(S2, score=2.0)]

    seeded["source_items"].on_aggregate = handler
    seeded["findings"].on_aggregate = lambda pipeline: []
    result = await retrieval.related(SCOPE, "text", 5)
    assert result.method == "text_search"
    assert [i.ref for i in result.items] == ["ctgov:NCT00000002"]


async def test_an_empty_vector_result_also_falls_back(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")
    seeded["source_items"].on_aggregate = lambda p: [] if "$vectorSearch" in p[0] else [dict(S1, score=1.5)]
    seeded["findings"].on_aggregate = lambda p: []
    result = await retrieval.related(SCOPE, "text", 5)
    assert (result.method, [i.ref for i in result.items]) == ("text_search", ["ctgov:NCT00000001"])


async def test_without_any_search_index_the_regular_text_index_answers(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "voyage")

    async def no_key(text):
        raise RuntimeError("VOYAGE_API_KEY is not set.")

    monkeypatch.setattr(related_module, "embed_query", no_key)
    seeded["source_items"].on_text = lambda query: [dict(S1, score=1.2), dict(OTHER, score=9.0), dict(SELF, score=5.0)]
    seeded["findings"].on_text = lambda query: []
    result = await retrieval.related(SCOPE, "plasma ctDNA", 5, [ANCHOR])
    assert result.method == "text_search" and result.index == "tx_source_items+tx_findings"
    assert [i.ref for i in result.items] == ["ctgov:NCT00000001"]
    assert seeded["source_items"].text_queries[0]["$text"] == {"$search": "plasma ctDNA"}


async def test_when_nothing_can_be_searched_the_result_is_empty_and_never_raises(mongo, monkeypatch):
    for mode, method in (("auto", "text_search"), ("none", "text_search")):
        monkeypatch.setenv("DXP_EMBEDDING", mode)
        result = await retrieval.related(SCOPE, "text", 5)
        assert result.items == [] and result.method == method and result.index is None


async def test_an_all_empty_search_reports_the_first_method_that_ran(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")
    seeded["source_items"].on_aggregate = lambda p: []
    seeded["findings"].on_aggregate = lambda p: []
    result = await retrieval.related(SCOPE, "text", 5)
    assert result.items == [] and result.method == "vector_search"


async def test_blank_text_or_zero_k_runs_no_query(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "none")
    assert (await retrieval.related(SCOPE, "  ", 5)).items == []
    assert (await retrieval.related(SCOPE, "text", 0)).items == []
    assert seeded["source_items"].pipelines == []


async def test_a_bad_embedding_setting_is_treated_as_none(seeded, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "openai")
    seeded["source_items"].on_aggregate = scored((S1, 1.0))
    seeded["findings"].on_aggregate = scored()
    assert (await retrieval.related(SCOPE, "text", 5)).method == "text_search"


M1 = {"_id": "mem_1111111111111111@v1", "memory_id": "mem_1111111111111111", "version": 1, "team_id": "team_lb",
      "status": "active", "tags": {"assay": "Guardant360 CDx", "claim_kind": "outcome_claim_without_results"},
      "text": "Do not state an outcome when no results are posted."}


async def test_memories_filter_on_team_active_and_claim_kind_never_on_assay(mongo, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "auto")
    mongo["memories"].on_aggregate = scored((M1, 0.77))
    tags = {"assay": "FoundationOne Liquid CDx", "claim_kind": "outcome_claim_without_results"}
    result = await retrieval.memories("team_lb", "early-stage profiling", tags, 3)
    assert result.method == "vector_search" and result.index == "vs_memories" and result.top_k == 3
    assert [(i.ref, i.score) for i in result.items] == [("mem_1111111111111111", 0.77)]
    assert result.filter.model_dump() == {"scope_id": None, "team_id": "team_lb", "status": "active",
                                          "tags": {"claim_kind": "outcome_claim_without_results"}}
    search = stage(mongo["memories"], "$vectorSearch")[0]
    assert search["filter"] == {"$and": [{"team_id": {"$eq": "team_lb"}}, {"status": {"$eq": "active"}},
                                         {"tags.claim_kind": {"$eq": "outcome_claim_without_results"}}]}
    assert "assay" not in str(search["filter"])


async def test_memories_in_none_mode_use_text_search_with_the_same_filter(mongo, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "none")
    mongo["memories"].on_aggregate = scored((M1, 4.0))
    result = await retrieval.memories("team_lb", "text", {"assay": "X", "claim_kind": "k"}, 3)
    assert result.method == "text_search" and result.index == "ts_memories"
    filters = stage(mongo["memories"], "$search")[0]["compound"]["filter"]
    assert [f["equals"]["path"] for f in filters] == ["team_id", "status", "tags.claim_kind"]


async def test_memories_without_tags_filter_on_team_and_status_only(mongo, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "none")
    mongo["memories"].on_text = lambda query: [dict(M1, score=1.0), dict(M1, _id="x", memory_id="mem_other", team_id="team_b", score=5.0)]
    result = await retrieval.memories("team_lb", "text", None, 3)
    assert [i.ref for i in result.items] == ["mem_1111111111111111"] and result.filter.tags is None
    assert result.index == "tx_memories"


async def test_voyage_mode_embeds_a_new_memory_before_searching(mongo, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "voyage")
    mongo["memories"].add(M1)
    calls = []

    async def fake_embed(texts):
        calls.append(list(texts))
        return [[0.5, 0.5] for _ in texts]

    async def fake_query(text):
        return [0.5, 0.5]

    monkeypatch.setattr(embed_module, "embed", fake_embed)
    monkeypatch.setattr(related_module, "embed_query", fake_query)
    mongo["memories"].on_aggregate = scored((M1, 0.9))
    await retrieval.memories("team_lb", "text", {"claim_kind": "k"}, 3)
    assert calls == [[M1["text"]]]
    assert mongo["memories"].docs[0]["embedding"] == [0.5, 0.5]


class FakeVoyage:
    def __init__(self):
        self.calls = []

    async def embed(self, texts, model, input_type, output_dimension):
        self.calls.append((list(texts), model, input_type, output_dimension))

        class Result:
            embeddings = [[float(len(t))] for t in texts]

        return Result()


async def test_embed_is_the_voyage_path_only(monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "none")
    with pytest.raises(RuntimeError):
        await retrieval.embed(["text"])
    monkeypatch.setenv("DXP_EMBEDDING", "voyage")
    client = FakeVoyage()
    monkeypatch.setattr(embed_module, "_client", lambda: client)
    assert await retrieval.embed(["ab", "abc"]) == [[2.0], [3.0]]
    assert await embed_module.embed_query("abcd") == [4.0]
    assert [(c[2], c[3]) for c in client.calls] == [("document", 1024), ("query", 1024)]
    assert await retrieval.embed([]) == []


async def test_embed_refuses_without_a_key_and_never_echoes_it(monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "voyage")
    monkeypatch.setenv("VOYAGE_API_KEY", "")
    with pytest.raises(RuntimeError) as error:
        await retrieval.embed(["text"])
    assert str(error.value) == "VOYAGE_API_KEY is not set."


async def test_embed_missing_embeds_only_documents_without_an_embedding(mongo, monkeypatch):
    monkeypatch.setenv("DXP_EMBEDDING", "voyage")
    client = FakeVoyage()
    monkeypatch.setattr(embed_module, "_client", lambda: client)
    mongo["source_items"].add(dict(S1), dict(S2, embedding=[9.0]), dict(SELF))
    mongo["findings"].add(dict(F1, summary="abc"))
    assert await embed_module.embed_missing(mongo) == 2
    assert mongo["source_items"].docs[0]["embedding"] == [float(len(S1["evidence_text"]))]
    assert mongo["source_items"].docs[1]["embedding"] == [9.0]
    assert "embedding" not in mongo["source_items"].docs[2]
    assert mongo["findings"].docs[0]["embedding"] == [3.0]
