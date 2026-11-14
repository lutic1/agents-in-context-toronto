import copy
import importlib

from dxp.memory import store

# dxp.memory.retrieve is the frozen function; the module of the same name is fetched by path.
retrieve = importlib.import_module("dxp.memory.retrieve")

TEAM = "team_lbdx"
OTHER_TEAM = "team_other"
CLAIM = "claim_performed_or_results"
STAMP = {"kind": "reviewer", "run_id": None, "principal": "sam"}


def make(memory_id, team_id=TEAM, assay="Guardant360 CDx", claim_kind=CLAIM, text="t"):
    return store.new_memory(
        memory_id=memory_id,
        team_id=team_id,
        author="sam",
        source={"decision_id": f"dec_{memory_id}", "report_id": f"rep_{memory_id}"},
        text=text,
        tags={"assay": assay, "claim_kind": claim_kind},
        decision_id=f"dec_gate_{memory_id}",
        stamp=STAMP,
        created_at="2026-11-14T14:10:00Z",
    )


def found(*pairs):
    """The `Retrieval.items` of a memory search."""
    return [{"ref": ref, "score": score} for ref, score in pairs]


def ids(ranked):
    return [memory["memory_id"] for memory, _ in ranked]


def scores(ranked):
    return [score for _, score in ranked]


def test_v22_memory_from_one_trial_is_retrieved_for_another_with_no_assay_in_common():
    m1 = make("mem_m1", assay="Guardant360 CDx")
    tags = {"assay": "FoundationOne Liquid CDx", "claim_kind": CLAIM}
    uses = retrieve.rank([m1], found(("mem_m1@v1", 0.81)), TEAM, tags)
    assert ids(uses) == ["mem_m1"]


def test_v22_retrieved_when_the_discovery_names_no_assay_at_all():
    m1 = make("mem_m1")
    for tags in ({"claim_kind": CLAIM}, {"assay": None, "claim_kind": CLAIM}):
        assert ids(retrieve.rank([m1], found(("mem_m1@v1", 0.5)), TEAM, tags)) == ["mem_m1"]


def test_v22_memory_recorded_with_no_assay_is_retrieved():
    m1 = make("mem_m1", assay=None)
    tags = {"assay": "FoundationOne Liquid CDx", "claim_kind": CLAIM}
    assert ids(retrieve.rank([m1], found(("mem_m1@v1", 0.5)), TEAM, tags)) == ["mem_m1"]


def test_search_tags_never_carry_the_assay():
    tags = {"assay": "FoundationOne Liquid CDx", "claim_kind": CLAIM}
    assert retrieve.search_tags(tags) == {"claim_kind": CLAIM}
    for none in (None, {}, {"assay": "Guardant360 CDx"}, {"claim_kind": ""}, {"claim_kind": None}):
        assert retrieve.search_tags(none) is None


def test_a_different_claim_kind_is_not_retrieved_even_with_the_same_assay():
    other = make("mem_other", claim_kind="claim_planned")
    tags = {"assay": "Guardant360 CDx", "claim_kind": CLAIM}
    assert retrieve.rank([other], found(("mem_other@v1", 0.99)), TEAM, tags) == []


def test_no_claim_kind_in_the_query_means_no_claim_kind_filter():
    memories = [make("mem_m1"), make("mem_other", claim_kind="claim_planned"), make("mem_none", claim_kind=None)]
    result = found(("mem_m1@v1", 0.9), ("mem_other@v1", 0.8), ("mem_none@v1", 0.7))
    for tags in (None, {}, {"claim_kind": ""}, {"assay": "Guardant360 CDx"}):
        assert ids(retrieve.rank(memories, result, TEAM, tags)) == ["mem_m1", "mem_other", "mem_none"]


def test_a_memory_with_no_claim_kind_is_not_matched_by_a_claim_kind_query():
    untagged = make("mem_none", claim_kind=None)
    assert retrieve.rank([untagged], found(("mem_none@v1", 0.9)), TEAM, {"claim_kind": CLAIM}) == []


def test_another_teams_memory_is_never_returned():
    theirs = make("mem_theirs", team_id=OTHER_TEAM)
    mine = make("mem_mine")
    result = found(("mem_theirs@v1", 0.99), ("mem_mine@v1", 0.2))
    uses = retrieve.rank([theirs, mine], result, TEAM, {"claim_kind": CLAIM})
    assert ids(uses) == ["mem_mine"]
    assert retrieve.rank([theirs], result, TEAM, {"claim_kind": CLAIM}) == []
    assert retrieve.rank([theirs, mine], result, "", {"claim_kind": CLAIM}) == []
    assert retrieve.rank([theirs, mine], result, None, {"claim_kind": CLAIM}) == []


def test_a_revoked_memory_is_never_returned():
    gone = store.revoked(make("mem_m1"))
    result = found(("mem_m1@v1", 0.99), ("mem_m1", 0.99))
    assert retrieve.rank([gone], result, TEAM, {"claim_kind": CLAIM}) == []
    assert retrieve.eligible([gone], TEAM, {"claim_kind": CLAIM}) == []


def test_a_corrected_version_is_replaced_by_its_successor():
    v1 = make("mem_m1", text="old wording")
    v2, v1_corrected = store.corrected_successor(
        v1, "new wording", "sam", "dec_correct", STAMP, "2026-11-14T15:00:00Z"
    )
    # A stale search result still names version 1 and scores it higher.
    result = found(("mem_m1@v1", 0.95), ("mem_m1@v2", 0.60))
    uses = retrieve.rank([v1_corrected, v2], result, TEAM, {"claim_kind": CLAIM})
    assert [(memory["memory_id"], memory["version"], score) for memory, score in uses] == [("mem_m1", 2, 0.60)]
    only_old = retrieve.rank([v1_corrected], found(("mem_m1@v1", 0.95)), TEAM, {"claim_kind": CLAIM})
    assert only_old == []


def test_revoking_the_successor_leaves_nothing_to_retrieve():
    v1 = make("mem_m1")
    v2, v1_corrected = store.corrected_successor(
        v1, "new wording", "sam", "dec_correct", STAMP, "2026-11-14T15:00:00Z"
    )
    result = found(("mem_m1@v1", 0.9), ("mem_m1@v2", 0.9))
    uses = retrieve.rank([v1_corrected, store.revoked(v2)], result, TEAM, {"claim_kind": CLAIM})
    assert uses == []


def test_ordered_by_score_highest_first():
    memories = [make("mem_a"), make("mem_b"), make("mem_c")]
    result = found(("mem_a@v1", 0.2), ("mem_b@v1", 0.9), ("mem_c@v1", 0.5))
    uses = retrieve.rank(memories, result, TEAM, {"claim_kind": CLAIM})
    assert ids(uses) == ["mem_b", "mem_c", "mem_a"]
    assert scores(uses) == [0.9, 0.5, 0.2]


def test_ties_break_by_memory_id_whatever_the_input_order():
    memories = [make("mem_c"), make("mem_a"), make("mem_b")]
    expected = ["mem_a", "mem_b", "mem_c"]
    one = found(("mem_c@v1", 0.7), ("mem_b@v1", 0.7), ("mem_a@v1", 0.7))
    two = found(("mem_a@v1", 0.7), ("mem_c@v1", 0.7), ("mem_b@v1", 0.7))
    assert ids(retrieve.rank(memories, one, TEAM, {"claim_kind": CLAIM})) == expected
    assert ids(retrieve.rank(list(reversed(memories)), two, TEAM, {"claim_kind": CLAIM})) == expected


def test_top_k_cut():
    memories = [make(f"mem_{n}") for n in range(5)]
    result = found(*[(f"mem_{n}@v1", n / 10) for n in range(5)])
    tags = {"claim_kind": CLAIM}
    assert ids(retrieve.rank(memories, result, TEAM, tags)) == ["mem_4", "mem_3", "mem_2"]
    assert ids(retrieve.rank(memories, result, TEAM, tags, k=1)) == ["mem_4"]
    assert len(retrieve.rank(memories, result, TEAM, tags, k=50)) == 5
    for k in (0, -1, None, True, 2.0):
        assert retrieve.rank(memories, result, TEAM, tags, k=k) == []


def test_a_memory_the_search_did_not_return_is_not_used():
    memories = [make("mem_a"), make("mem_b")]
    uses = retrieve.rank(memories, found(("mem_a@v1", 0.4)), TEAM, {"claim_kind": CLAIM})
    assert ids(uses) == ["mem_a"]
    assert retrieve.rank(memories, found(), TEAM, {"claim_kind": CLAIM}) == []
    assert retrieve.rank(memories, None, TEAM, {"claim_kind": CLAIM}) == []


def test_a_search_result_with_no_matching_document_is_ignored():
    uses = retrieve.rank([make("mem_a")], found(("mem_ghost@v1", 0.9), ("mem_a@v1", 0.1)), TEAM, {"claim_kind": CLAIM})
    assert ids(uses) == ["mem_a"]


def test_ref_may_be_the_memory_id_and_duplicates_keep_the_first_entry():
    memories = [make("mem_a"), make("mem_b")]
    result = found(("mem_a", 0.3), ("mem_b@v1", 0.6), ("mem_b@v1", 0.1))
    uses = retrieve.rank(memories, result, TEAM, {"claim_kind": CLAIM})
    assert list(zip(ids(uses), scores(uses))) == [("mem_b", 0.6), ("mem_a", 0.3)]


def test_items_without_a_usable_score_are_dropped():
    memories = [make("mem_a"), make("mem_b"), make("mem_c"), make("mem_d")]
    result = found(("mem_a@v1", None), ("mem_b@v1", "0.9"), ("mem_c@v1", float("nan")), ("mem_d@v1", 0))
    assert ids(retrieve.rank(memories, result, TEAM, {"claim_kind": CLAIM})) == ["mem_d"]


def test_text_search_scores_rank_the_same_way():
    memories = [make("mem_a"), make("mem_b")]
    result = found(("mem_a@v1", 3.5), ("mem_b@v1", 7))
    assert ids(retrieve.rank(memories, result, TEAM, {"claim_kind": CLAIM})) == ["mem_b", "mem_a"]


def test_a_stale_active_earlier_version_never_wins_over_the_latest():
    # An interrupted correction can leave version 1 active beside version 2: the latest wins.
    v1 = make("mem_m1", text="old wording")
    v2, _ = store.corrected_successor(v1, "new wording", "sam", "dec_correct", STAMP, "2026-11-14T15:00:00Z")
    ranked = retrieve.rank([v1, v2], found(("mem_m1@v1", 0.95), ("mem_m1@v2", 0.6)), TEAM, {"claim_kind": CLAIM})
    assert [(memory["version"], score) for memory, score in ranked] == [(2, 0.6)]
    assert retrieve.rank([v1, store.revoked(v2)], found(("mem_m1@v1", 0.95)), TEAM, {"claim_kind": CLAIM}) == []


def test_memory_id_of():
    assert retrieve.memory_id_of("mem_a@v12") == "mem_a"
    assert retrieve.memory_id_of("mem_a") == "mem_a"
    assert retrieve.memory_id_of(None) is None and retrieve.memory_id_of("") is None


def test_inputs_are_not_changed():
    memories = [make("mem_a"), store.revoked(make("mem_b")), make("mem_c", team_id=OTHER_TEAM)]
    result = found(("mem_a@v1", 0.4), ("mem_b@v1", 0.9), ("mem_c@v1", 0.8))
    tags = {"assay": "X", "claim_kind": CLAIM}
    before = copy.deepcopy((memories, result, tags))
    retrieve.rank(memories, result, TEAM, tags)
    assert (memories, result, tags) == before
