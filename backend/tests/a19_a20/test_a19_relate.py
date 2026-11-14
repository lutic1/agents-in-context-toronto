import pytest

import importlib

relate = importlib.import_module("dxp.reports.relate")

NEW = {
    "source_ref": "ctgov:NCT04712877",
    "version_id": "sv_new",
    "raw_text": "Molecular profiling using blood (ctDNA) and tumour tissue in early-stage lung cancer.",
}
RELATED = {
    "ref": "ctgov:NCT00000001",
    "source_ref": "ctgov:NCT00000001",
    "version_id": "sv_old",
    "kind": "source_item",
    "title": "Plasma ctDNA genotyping in advanced NSCLC",
    "raw_text": "Plasma ctDNA genotyping guided therapy in advanced non-small cell lung cancer.",
}
GOOD = {
    "label": "extends",
    "rationale": "The new trial moves blood-based profiling to an earlier-stage setting.",
    "new_quote": "tumour tissue in early-stage lung cancer",
    "related_quote": "Plasma ctDNA genotyping guided therapy",
}


def exact(quote, raw_text):
    return quote in raw_text


def build(output, check=exact, **kwargs):
    return relate.build_relationship(output, NEW, RELATED, check, **kwargs)


@pytest.mark.parametrize("label", ["supports", "contradicts", "extends", "new_question"])
def test_the_four_labels_are_valid(label):
    assert relate.valid_label(label)
    assert build(dict(GOOD, label=label))["label"] == label


@pytest.mark.parametrize("label", ["related_unestablished", "Supports", "refutes", "", None, 3])
def test_other_labels_are_not_valid(label):
    assert not relate.valid_label(label)
    assert build(dict(GOOD, label=label))["label"] == "related_unestablished"


def test_two_checked_quotes_establish_the_label_in_the_contract_shape():
    rel = build(GOOD, similarity=0.83, retrieval_method="vector_search")
    assert set(rel) == {"id", "related_ref", "related_kind", "related_title", "label", "rationale",
                        "new_quote", "related_quote", "similarity", "retrieval_method", "origin",
                        "status", "filed_by_decision_id"}
    assert rel["label"] == "extends"
    assert rel["rationale"] == GOOD["rationale"]
    assert rel["new_quote"] == {"source_ref": "ctgov:NCT04712877", "version_id": "sv_new",
                                "text": GOOD["new_quote"], "quote_found": True}
    assert rel["related_quote"] == {"source_ref": "ctgov:NCT00000001", "version_id": "sv_old",
                                    "text": GOOD["related_quote"], "quote_found": True}
    assert rel["related_ref"] == "ctgov:NCT00000001"
    assert rel["related_kind"] == "source_item"
    assert rel["related_title"] == RELATED["title"]
    assert (rel["similarity"], rel["retrieval_method"]) == (0.83, "vector_search")
    assert (rel["origin"], rel["status"], rel["filed_by_decision_id"]) == ("discovery", "pending", None)
    assert relate.is_established(rel)


def test_high_similarity_with_one_unchecked_quote_gets_no_label():
    rel = build(dict(GOOD, related_quote="Plasma ctDNA genotyping improved survival"),
                similarity=0.99, retrieval_method="vector_search")
    assert rel["label"] == "related_unestablished"
    assert relate.label_text(rel["label"]) == "related (no relationship established)"
    assert rel["rationale"] is None
    assert rel["new_quote"]["quote_found"] is True
    assert rel["related_quote"]["quote_found"] is False
    assert rel["similarity"] == 0.99
    assert not relate.is_established(rel)


def test_unchecked_new_side_quote_also_downgrades():
    rel = build(dict(GOOD, new_quote="the trial showed benefit"))
    assert rel["label"] == "related_unestablished"
    assert rel["new_quote"]["quote_found"] is False


def test_similarity_never_changes_the_label():
    assert build(GOOD, similarity=0.01)["label"] == "extends"
    assert build(GOOD, similarity=None)["label"] == "extends"


def test_each_quote_is_checked_against_its_own_side():
    calls = []

    def recording(quote, raw_text):
        calls.append((quote, raw_text))
        return True

    build(GOOD, recording)
    assert calls == [(GOOD["new_quote"], NEW["raw_text"]), (GOOD["related_quote"], RELATED["raw_text"])]


def test_a_quote_found_only_on_the_other_side_is_unchecked():
    rel = build(dict(GOOD, new_quote=GOOD["related_quote"]))
    assert rel["label"] == "related_unestablished"


def test_quote_of_300_characters_is_allowed_and_301_is_malformed():
    long_text = "a" * 301
    new = dict(NEW, raw_text=long_text)
    ok = relate.build_relationship(dict(GOOD, new_quote="a" * 300), new, RELATED, exact)
    assert ok["label"] == "extends"
    too_long = relate.build_relationship(dict(GOOD, new_quote=long_text), new, RELATED, exact)
    assert too_long["label"] == "related_unestablished"
    assert too_long["new_quote"]["text"] == ""
    assert relate.parse_proposal(dict(GOOD, new_quote=long_text)) is None


@pytest.mark.parametrize("output", [
    None, "extends", [], {}, {"label": "extends"},
    dict(GOOD, rationale=""), dict(GOOD, rationale=None),
    dict(GOOD, new_quote=""), dict(GOOD, new_quote="   "), dict(GOOD, related_quote=None),
    dict(GOOD, new_quote=["tumour tissue", "early-stage"]),
    {k: v for k, v in GOOD.items() if k != "related_quote"},
])
def test_malformed_model_output_is_unestablished_and_never_raises(output):
    rel = build(output, similarity=0.9)
    assert rel["label"] == "related_unestablished"
    assert rel["rationale"] is None
    assert rel["new_quote"]["quote_found"] is False
    assert rel["related_quote"]["quote_found"] is False
    assert rel["new_quote"]["version_id"] == "sv_new"
    assert rel["related_ref"] == "ctgov:NCT00000001"
    assert rel["similarity"] == 0.9


def test_quotes_given_as_objects_with_text_are_accepted():
    out = dict(GOOD, new_quote={"text": GOOD["new_quote"]}, related_quote={"text": GOOD["related_quote"]})
    assert build(out)["label"] == "extends"


def test_a_failing_quote_check_downgrades_instead_of_raising():
    def broken(quote, raw_text):
        raise RuntimeError("checker down")

    assert build(GOOD, broken)["label"] == "related_unestablished"


@pytest.mark.parametrize("answer", [1, "yes", {"found": True}, (True,), None])
def test_only_a_true_check_result_counts(answer):
    assert build(GOOD, lambda quote, raw_text: answer)["label"] == "related_unestablished"


def test_missing_raw_text_means_unchecked_without_calling_the_checker():
    called = []
    rel = relate.build_relationship(GOOD, NEW, dict(RELATED, raw_text=None),
                                    lambda q, t: called.append(q) or True)
    assert rel["label"] == "related_unestablished"
    assert called == [GOOD["new_quote"]]


def test_origin_and_id_are_carried_and_finding_kind_is_kept():
    finding = dict(RELATED, ref="f_abc", kind="finding")
    rel = relate.build_relationship(GOOD, NEW, finding, exact, origin="task:task_1", rel_id="rel_1")
    assert (rel["id"], rel["origin"]) == ("rel_1", "task:task_1")
    assert (rel["related_ref"], rel["related_kind"]) == ("f_abc", "finding")
    assert rel["related_quote"]["source_ref"] == "ctgov:NCT00000001"
