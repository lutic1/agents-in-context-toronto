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


# ---------------------------------------------------------------- reports.relate (mocked llm)

from dxp import reports
from dxp.api.models import Relationship, RetrievalItem

V_NEW, V_OLD = "sv_aaaaaaaaaaaaaaaa", "sv_bbbbbbbbbbbbbbbb"
NEW_ITEM = dict(NEW, version_id=V_NEW, mentions=[{"name": "FoundationOne CDx"}, {"name": "FoundationOne Liquid"}])
RELATED_ITEM = dict(RELATED, version_id=V_OLD, score=0.83, retrieval_method="vector_search")


@pytest.fixture
def model(monkeypatch):
    """Replaces llm.call_structured and evidence.quote_in_source; no model is called."""
    import dxp.evidence
    import dxp.llm

    class Model:
        answer = dict(GOOD)
        calls = []

        async def call_structured(self, model, schema, messages):
            self.calls.append((model, schema, messages))
            if isinstance(self.answer, Exception):
                raise self.answer
            return self.answer

    fake = Model()
    fake.calls = []
    monkeypatch.setattr(dxp.llm, "call_structured", fake.call_structured)
    monkeypatch.setattr(dxp.evidence, "quote_in_source", exact, raising=False)
    return fake


async def test_relate_returns_the_frozen_relationship_with_both_quotes_pinned(model, mongo):
    rel = await reports.relate(NEW_ITEM, RELATED_ITEM)
    assert isinstance(rel, Relationship)
    assert rel.label == "extends" and rel.rationale == GOOD["rationale"]
    assert rel.id.startswith("rel_") and len(rel.id) == 20
    assert (rel.new_quote.version_id, rel.related_quote.version_id) == (V_NEW, V_OLD)
    assert rel.new_quote.quote_found and rel.related_quote.quote_found
    assert (rel.similarity, rel.retrieval_method) == (0.83, "vector_search")
    assert (rel.origin, rel.status, rel.related_kind) == ("discovery", "pending", "source_item")
    model_id, schema, messages = model.calls[0]
    assert model_id == "claude-sonnet-5-5"
    assert schema["properties"]["label"]["enum"] == list(relate.LABELS)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert NEW["raw_text"] in messages[1]["content"] and RELATED["raw_text"] in messages[1]["content"]


async def test_relate_high_similarity_with_one_unchecked_quote_gets_no_label(model, mongo):
    model.answer = dict(GOOD, related_quote="Plasma ctDNA genotyping improved survival")
    rel = await reports.relate(NEW_ITEM, dict(RELATED_ITEM, score=0.99))
    assert rel.label == "related_unestablished" and rel.rationale is None
    assert rel.similarity == 0.99 and rel.related_quote.quote_found is False


@pytest.mark.parametrize("answer", [RuntimeError("overloaded"), None, "refused", {"label": "extends"}])
async def test_relate_model_error_or_refusal_is_unestablished_and_never_fails_the_item(model, mongo, answer):
    model.answer = answer
    rel = await reports.relate(NEW_ITEM, RELATED_ITEM)
    assert rel.label == "related_unestablished"
    assert rel.new_quote.text == "" and rel.new_quote.version_id == V_NEW
    assert rel.similarity == 0.83


async def test_relate_failure_object_from_the_client_is_unestablished(model, mongo):
    class Failure:
        kind = "failure"

    model.answer = Failure()
    assert (await reports.relate(NEW_ITEM, RELATED_ITEM)).label == "related_unestablished"


async def test_relate_drops_a_rationale_that_says_a_trial_uses_a_named_product(model, mongo):
    model.answer = dict(GOOD, rationale="The new trial uses FoundationOne CDx in an earlier stage.")
    rel = await reports.relate(NEW_ITEM, RELATED_ITEM)
    assert rel.label == "related_unestablished" and rel.rationale is None


async def test_relate_reads_the_exact_version_named_not_the_current_pointer(model, mongo):
    mongo["source_items"].add({"_id": "ctgov:NCT00000001", "current_version_id": "sv_cccccccccccccccc",
                               "title": "Plasma ctDNA genotyping in advanced NSCLC"})
    mongo["source_versions"].add(
        {"_id": V_OLD, "source_ref": "ctgov:NCT00000001", "raw_text": RELATED["raw_text"]},
        {"_id": "sv_cccccccccccccccc", "source_ref": "ctgov:NCT00000001", "raw_text": "A rewritten record."})
    item = RetrievalItem(ref="ctgov:NCT00000001", version_id=V_OLD, score=0.6)
    rel = await reports.relate(NEW_ITEM, item)
    assert rel.label == "extends" and rel.related_quote.version_id == V_OLD
    assert rel.related_title == "Plasma ctDNA genotyping in advanced NSCLC" and rel.similarity == 0.6
    assert "A rewritten record." not in model.calls[0][2][1]["content"]


async def test_relate_a_finding_is_checked_against_its_own_source_version(model, mongo):
    mongo["findings"].add({"_id": "f_1111111111111111", "source_ref": "ctgov:NCT00000001", "version_id": V_OLD,
                           "summary": "Plasma genotyping study"})
    mongo["source_versions"].add({"_id": V_OLD, "raw_text": RELATED["raw_text"]})
    rel = await reports.relate(NEW_ITEM, {"ref": "f_1111111111111111", "score": 0.5})
    assert (rel.related_kind, rel.related_ref) == ("finding", "f_1111111111111111")
    assert rel.label == "extends" and rel.related_quote.source_ref == "ctgov:NCT00000001"


async def test_relate_without_source_text_asks_no_model(model, mongo):
    rel = await reports.relate(NEW_ITEM, {"ref": "ctgov:NCT00000404", "score": 0.4})
    assert rel.label == "related_unestablished" and model.calls == []
    assert rel.related_quote.source_ref == "ctgov:NCT00000404"


async def test_relationship_id_is_derived_from_report_source_and_related_ref(model, mongo):
    from dxp import identity

    rel = await reports.relate(dict(NEW_ITEM, report_id="rep_1"), RELATED_ITEM)
    assert rel.id == identity.derive("rel_", "rep_1", NEW["source_ref"], RELATED["ref"])
    assert rel.id == relate.relationship_id("rep_1", NEW["source_ref"], RELATED["ref"])


async def test_relate_never_takes_a_version_from_the_current_pointer(model, mongo):
    """V40: an item that names no version stays unpinned, so it gets no label."""
    mongo["source_items"].add({"_id": "ctgov:NCT00000001", "current_version_id": "sv_cccccccccccccccc",
                               "title": "Plasma ctDNA genotyping in advanced NSCLC"})
    mongo["source_versions"].add({"_id": "sv_cccccccccccccccc", "source_ref": "ctgov:NCT00000001",
                                  "raw_text": RELATED["raw_text"]})
    rel = await reports.relate(NEW_ITEM, {"ref": "ctgov:NCT00000001", "score": 0.9})
    assert rel.related_quote.version_id is None and rel.label == "related_unestablished"
    assert rel.related_title == "Plasma ctDNA genotyping in advanced NSCLC"


async def test_relate_takes_the_model_id_from_llm_when_it_names_one(model, mongo, monkeypatch):
    import dxp.llm

    monkeypatch.setattr(dxp.llm, "MODEL_IDS", {"strong": "model-from-llm"}, raising=False)
    mongo["source_versions"].add({"_id": V_OLD, "source_ref": "ctgov:NCT00000001", "raw_text": RELATED["raw_text"]})
    await reports.relate(NEW_ITEM, RELATED_ITEM)
    assert [c[0] for c in model.calls] == ["model-from-llm"]
