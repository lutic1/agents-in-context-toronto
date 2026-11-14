"""memory.retrieve over a fake retrieval.memories (A19+A20's frozen signature), and the Done-when cases."""

from __future__ import annotations

import importlib

import pytest
from a21_a22_fakes import CLAIM, M1_TEXT, OTHER_TEAM, TEAM, install, reviewer_ctx, sam
from dxp import memory
from dxp.api.models import Memory, MemorySource, MemoryUse, Retrieval, RetrievalFilter, RetrievalItem

retrieve_module = importlib.import_module("dxp.memory.retrieve")

ANCHOR_TEXT = "NCT04712877: FoundationOne Liquid CDx plasma profiling, recruiting, no results posted"
ANCHOR_TAGS = {"assay": "FoundationOne Liquid CDx", "claim_kind": CLAIM}


class FakeSearch:
    """Stands in for retrieval.memories: honours the Team, `active` and claim_kind filters the way
    the index does, scores from a table, and records every call."""

    def __init__(self, database, scores=None, method="vector_search", stale=()):
        self.database = database
        self.scores = scores or {}
        self.method = method
        self.stale = list(stale)  # items a lagging index still returns
        self.calls = []

    async def __call__(self, team_id, text, tags, k):
        self.calls.append({"team_id": team_id, "text": text, "tags": tags, "k": k})
        hits = [d for d in self.database.memories if d["team_id"] == team_id and d["status"] == "active"
                and (not tags or d["tags"]["claim_kind"] == tags.get("claim_kind"))]
        items = [RetrievalItem(ref=d["_id"], score=self.scores.get(d["memory_id"], 0.5)) for d in hits]
        items += [RetrievalItem(ref=ref, score=score) for ref, score in self.stale]
        items.sort(key=lambda item: -item.score)
        index = "vs_memories" if self.method == "vector_search" else "ts_memories"
        return Retrieval(method=self.method, index=index, top_k=k,
                         filter=RetrievalFilter(team_id=team_id, status="active", tags=tags), items=items[:k + len(self.stale)])


@pytest.fixture
def database(monkeypatch):
    return install(monkeypatch)


@pytest.fixture
def search(database, monkeypatch):
    import dxp.retrieval

    fake = FakeSearch(database)
    monkeypatch.setattr(dxp.retrieval, "memories", fake)
    return fake


async def create(decision_id, *, team_id=TEAM, text=M1_TEXT, assay="Guardant360 CDx", claim_kind=CLAIM):
    created, _ = await memory.create(team_id, text, {"assay": assay, "claim_kind": claim_kind},
                                     MemorySource(decision_id=decision_id, report_id=f"rep_{decision_id}"),
                                     sam(), reviewer_ctx(request_id=f"req_{decision_id}"))
    return created


async def test_v22_m1_from_the_setup_trial_is_retrieved_for_the_anchor_with_no_assay_in_common(database, fake_gate, search):
    m1 = await create("dec_reject")  # written on NCT05715229, a Guardant360 CDx trial
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [type(item) for item in found] == [Memory]
    assert (found[0].id, found[0].version, found[0].text, found[0].author) == (m1.id, 1, M1_TEXT, "sam")
    assert found[0].tags.assay == "Guardant360 CDx" and found[0].source.report_id == "rep_dec_reject"
    assert retrieval.items == [RetrievalItem(ref=m1.id, score=0.5)]
    assert retrieval.method == "vector_search" and retrieval.index == "vs_memories"


async def test_the_search_is_never_asked_to_filter_on_the_assay(database, fake_gate, search):
    await create("dec_reject")
    for tags in (ANCHOR_TAGS, {"assay": "anything"}, None):
        _, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, tags)
        assert "assay" not in (search.calls[-1]["tags"] or {})
        assert "assay" not in (retrieval.filter.tags or {})
    assert search.calls[0] == {"team_id": TEAM, "text": ANCHOR_TEXT, "tags": {"claim_kind": CLAIM}, "k": 3}
    assert search.calls[1]["tags"] is None and search.calls[2]["tags"] is None


async def test_the_returned_retrieval_states_the_filter_used(database, fake_gate, search):
    await create("dec_reject")
    _, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert retrieval.filter == RetrievalFilter(team_id=TEAM, status="active", tags={"claim_kind": CLAIM})
    assert retrieval.top_k == 3


async def test_retrieved_for_a_discovery_that_names_no_assay(database, fake_gate, search):
    m1 = await create("dec_reject")
    found, _ = await memory.retrieve(TEAM, ANCHOR_TEXT, {"assay": None, "claim_kind": CLAIM})
    assert [item.id for item in found] == [m1.id]


async def test_another_claim_kind_is_not_retrieved(database, fake_gate, search):
    await create("dec_reject", claim_kind="claim_planned")
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert found == [] and retrieval.items == []


async def test_another_teams_memory_is_never_returned(database, fake_gate, search):
    theirs = await create("dec_theirs", team_id=OTHER_TEAM)
    mine = await create("dec_mine")
    # Even if the search returned the other Team's memory, it is dropped.
    search.stale = [(f"{theirs.id}@v1", 0.99), (theirs.id, 0.98)]
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [item.id for item in found] == [mine.id]
    assert [item.ref for item in retrieval.items] == [mine.id]
    assert all(item.team_id == TEAM for item in found)
    other, _ = await memory.retrieve(OTHER_TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [item.id for item in other] == [theirs.id]


async def test_revoking_m1_removes_it_from_the_next_report(database, fake_gate, search):
    m1 = await create("dec_reject")
    before, _ = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    await memory.revoke(m1.id, "no longer wanted", reviewer_ctx(request_id="req_revoke", memory_id=m1.id))
    # A lagging index may still return the revoked version: it is never used.
    search.stale = [(f"{m1.id}@v1", 0.99)]
    after, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [item.id for item in before] == [m1.id]
    assert after == [] and retrieval.items == []
    assert retrieve_module.memory_uses(after, retrieval) == []


async def test_a_corrected_version_is_replaced_by_its_successor(database, fake_gate, search):
    m1 = await create("dec_reject")
    await memory.correct(m1.id, "State the trial status only", "clearer", reviewer_ctx(request_id="req_c", memory_id=m1.id))
    search.stale = [(f"{m1.id}@v1", 0.99)]
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [(item.id, item.version, item.text) for item in found] == [(m1.id, 2, "State the trial status only")]
    assert retrieval.items == [RetrievalItem(ref=m1.id, score=0.5)]


async def test_ranked_by_the_search_score_and_cut_to_three(database, fake_gate, search):
    created = [await create(f"dec_{n}") for n in range(5)]
    search.scores = {m.id: score for m, score in zip(created, (0.1, 0.9, 0.5, 0.7, 0.3))}
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [item.id for item in found] == [created[1].id, created[3].id, created[2].id]
    assert [(item.ref, item.score) for item in retrieval.items] == [
        (created[1].id, 0.9), (created[3].id, 0.7), (created[2].id, 0.5)]


async def test_the_text_search_fallback_is_passed_through_with_its_honest_label(database, fake_gate, search):
    m1 = await create("dec_reject")
    search.method = "text_search"
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert [item.id for item in found] == [m1.id]
    assert retrieval.method == "text_search" and retrieval.index == "ts_memories"


async def test_no_memories_is_an_empty_result(database, fake_gate, search):
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert found == [] and retrieval.items == [] and retrieval.top_k == 3


async def test_memory_uses_carry_author_source_version_and_score_with_no_effect_yet(database, fake_gate, search):
    m1 = await create("dec_reject")
    search.scores = {m1.id: 0.81}
    found, retrieval = await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
    assert retrieve_module.memory_uses(found, retrieval) == [MemoryUse(
        memory_id=m1.id, version=1, author="sam",
        source=MemorySource(decision_id="dec_reject", report_id="rep_dec_reject"), score=0.81, effect=None)]


async def test_until_a19_a20_merges_the_frozen_stub_says_so(database, fake_gate):
    import inspect

    import dxp.retrieval

    if "raise NotImplementedError(" not in inspect.getsource(dxp.retrieval.memories):
        pytest.skip("retrieval.memories is finished by its owner")
    with pytest.raises(NotImplementedError):
        await memory.retrieve(TEAM, ANCHOR_TEXT, ANCHOR_TAGS)
