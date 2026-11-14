"""I1 defect: M1 asked the model to ADD a sentence. The model cited it at a coarser grain than the
sentence diff ("old sentence" -> "old sentence + new sentence"), the exact match failed, the change
was dropped from draft 2 and the memory's effect was empty. Coarse citations of real changes count;
invented ones still never do."""

from dxp.reports.draft import apply_citations, memory_effects, verified_citations

OLD = "The trial investigates blood and tissue profiling before surgery."
NEW = "This is a new trial signal worth investigating, not evidence about any assay."
FIRST = {"draft": 1, "headline": "New trial signal: LEADER.", "summary": OLD, "gap": "G?", "claims": []}
CANDIDATE = {**FIRST, "draft": 2, "summary": f"{OLD} {NEW}"}
MEM = [{"memory_id": "mem_1", "version": 2, "author": "sam", "source": {"report_id": "rep_s"}}]


def test_an_added_sentence_cited_with_its_neighbour_counts():
    cited = [{"memory_id": "mem_1", "changed": True, "before": OLD, "after": f"{OLD} {NEW}"}]
    accepted = verified_citations(FIRST, CANDIDATE, cited, ["mem_1"])
    assert [(m, c["before"], c["after"]) for m, c in accepted] == [("mem_1", "", NEW)]
    second = apply_citations(FIRST, CANDIDATE, accepted)
    assert NEW in second["summary"]
    effect = memory_effects(FIRST, second, MEM, cited)[0]["effect"]
    assert effect and effect["before"] == "" and effect["after"] == NEW


def test_an_added_sentence_cited_exactly_still_counts():
    cited = [{"memory_id": "mem_1", "changed": True, "before": "", "after": NEW}]
    assert [(c["before"], c["after"]) for _, c in verified_citations(FIRST, CANDIDATE, cited, ["mem_1"])] == [("", NEW)]


def test_a_citation_of_a_change_that_did_not_happen_never_counts():
    cited = [{"memory_id": "mem_1", "changed": True, "before": OLD, "after": f"{OLD} Invented sentence."}]
    assert verified_citations(FIRST, CANDIDATE, cited, ["mem_1"]) == []
    assert verified_citations(FIRST, FIRST, [{"memory_id": "mem_1", "before": OLD, "after": f"{OLD} {NEW}"}], ["mem_1"]) == []


def test_an_unknown_memory_never_counts():
    cited = [{"memory_id": "mem_other", "changed": True, "before": OLD, "after": f"{OLD} {NEW}"}]
    assert verified_citations(FIRST, CANDIDATE, cited, ["mem_1"]) == []
