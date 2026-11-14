import pytest

import importlib

draft = importlib.import_module("dxp.reports.draft")

HEADLINE = ("This study investigates molecular profiling using blood (ctDNA) and tumour tissue in "
            "early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. "
            "No results posted.")
AMBIGUOUS = ("The trial's intervention field is ambiguous: it lists assay names as alternate names of "
             "a generic ctDNA and tumour NGS intervention, and does not say which assay was used for "
             "which sample.")
UNRESOLVED = ("The record names 'FoundationOne Liquid'. Whether this is the FDA-approved "
              "FoundationOne Liquid CDx is not stated.")
GAP = "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"
NAMES = ["FoundationOne CDx", "FoundationOne Liquid"]

M1 = {"memory_id": "mem_1", "version": 1, "author": "sam", "score": 0.71,
      "source": {"decision_id": "dec_1", "report_id": "rep_0"},
      "text": "Do not state an outcome when the trial has no posted results; say no results posted."}
M2 = {"memory_id": "mem_2", "version": 2, "author": "sam", "score": 0.4,
      "source": {"decision_id": "dec_2", "report_id": "rep_0"},
      "text": "Prefer the phrase tumour tissue over biopsy material."}

BEFORE = {"headline": "This study investigates profiling in early-stage lung cancer.",
          "discovery": {"summary": "The trial showed that blood profiling finds drivers. It is recruiting."},
          "uncertainties": ["Recruiting; no results posted."], "gap": GAP}
AFTER = {"headline": "This study investigates profiling in early-stage lung cancer.",
         "discovery": {"summary": "The trial investigates whether blood profiling finds drivers; "
                                  "no results posted. It is recruiting."},
         "uncertainties": ["Recruiting; no results posted."], "gap": GAP}


def test_split_sentences():
    assert draft.split_sentences("One. Two? Three!") == ["One.", "Two?", "Three!"]
    assert draft.split_sentences(UNRESOLVED) == [
        "The record names 'FoundationOne Liquid'.",
        "Whether this is the FDA-approved FoundationOne Liquid CDx is not stated."]
    assert draft.split_sentences(None) == [] and draft.split_sentences("") == []


def test_one_memory_gets_the_changed_sentence_before_and_after():
    uses = draft.memory_effects(BEFORE, AFTER, [M1])
    assert uses == [{
        "memory_id": "mem_1", "version": 1, "author": "sam", "score": 0.71,
        "source": {"decision_id": "dec_1", "report_id": "rep_0"},
        "effect": {"target": "sentence",
                   "before": "The trial showed that blood profiling finds drivers.",
                   "after": "The trial investigates whether blood profiling finds drivers; no results posted."},
    }]
    assert draft.effect_text(uses[0]).startswith("changed sentence: before ")


def test_identical_drafts_mean_retrieved_no_change():
    uses = draft.memory_effects(BEFORE, dict(BEFORE), [M1, M2])
    assert [u["effect"] for u in uses] == [None, None]
    assert draft.effect_text(uses[0]) == "retrieved, no change"


def test_each_change_goes_to_the_memory_it_matches_and_others_show_no_change():
    uses = draft.memory_effects(BEFORE, AFTER, [M2, M1])
    by_id = {u["memory_id"]: u["effect"] for u in uses}
    assert by_id["mem_2"] is None
    assert by_id["mem_1"]["after"].endswith("no results posted.")
    assert [u["memory_id"] for u in uses] == ["mem_2", "mem_1"]


def test_explicit_attribution_wins_only_when_it_names_a_real_change():
    after_sentence = "The trial investigates whether blood profiling finds drivers; no results posted."
    uses = draft.memory_effects(BEFORE, AFTER, [M1, M2], attribution={"mem_2": after_sentence})
    by_id = {u["memory_id"]: u["effect"] for u in uses}
    assert by_id["mem_2"]["after"] == after_sentence and by_id["mem_1"] is None
    ignored = draft.memory_effects(BEFORE, AFTER, [M1, M2], attribution={"mem_2": "It is recruiting."})
    by_id = {u["memory_id"]: u["effect"] for u in ignored}
    assert by_id["mem_2"] is None and by_id["mem_1"] is not None


def test_a_change_matching_no_memory_goes_to_the_best_ranked_one():
    before = {"headline": "Alpha beta."}
    after = {"headline": "Gamma delta."}
    uses = draft.memory_effects(before, after, [M2, M1])
    assert uses[0]["effect"] == {"target": "sentence", "before": "Alpha beta.", "after": "Gamma delta."}
    assert uses[1]["effect"] is None


def test_removed_and_added_sentences_are_changes():
    removed = draft.draft_changes({"headline": "A. B."}, {"headline": "A."})
    assert removed == [{"target": "sentence", "before": "B.", "after": ""}]
    added = draft.draft_changes({"headline": "A."}, {"headline": "A. C."})
    assert added == [{"target": "sentence", "before": "", "after": "C."}]


def test_a_changed_claim_kind_is_a_label_change():
    before = {"claims": [{"text": "Blood profiling finds drivers.", "claim_kind": "outcome_claim"}]}
    after = {"claims": [{"text": "Blood profiling finds drivers.", "claim_kind": "design_claim"}]}
    uses = draft.memory_effects(before, after, [M1])
    assert uses[0]["effect"] == {"target": "label", "before": "outcome_claim", "after": "design_claim"}


def test_no_memories_and_missing_drafts_are_handled():
    assert draft.memory_effects(BEFORE, AFTER, []) == []
    assert draft.memory_effects(None, None, [M1])[0]["effect"] is None


def test_memory_id_may_come_as_id():
    uses = draft.memory_effects(BEFORE, AFTER, [{"id": "mem_9", "text": "no results posted"}])
    assert uses[0]["memory_id"] == "mem_9" and uses[0]["effect"] is not None


@pytest.mark.parametrize("sentence,verb", [
    ("The trial uses FoundationOne CDx on tissue.", "uses"),
    ("Patients were tested using FoundationOne Liquid.", "uses"),
    ("FoundationOne CDx was used for tissue samples.", "uses"),
    ("This trial studies FoundationOne Liquid in early-stage disease.", "studies"),
    ("FoundationOne CDx is studied before surgery.", "studies"),
    ("FoundationOne Liquid showed high concordance.", "showed"),
    ("The trial shows that foundationone cdx finds drivers.", "showed"),
])
def test_uses_studies_showed_about_a_named_product_is_flagged(sentence, verb):
    flags = draft.wording_flags(sentence, NAMES)
    assert flags and flags[0]["verb"] == verb and flags[0]["sentence"] == sentence


@pytest.mark.parametrize("text", [
    HEADLINE, AMBIGUOUS, UNRESOLVED, GAP,
    "'FoundationOne CDx' is named in the record (otherNames of \"ctDNA, tumor NGS\").",
    "The record names FoundationOne CDx, which is not proof of use.",
    "The trial uses blood samples. The record names FoundationOne Liquid.",
])
def test_required_and_mention_wording_is_not_flagged(text):
    assert draft.wording_flags(text, NAMES) == []


def test_only_the_offending_sentence_and_name_are_reported():
    text = "The record names FoundationOne Liquid. The trial uses FoundationOne CDx."
    flags = draft.wording_flags(text, NAMES)
    assert flags == [{"name": "FoundationOne CDx", "verb": "uses",
                      "sentence": "The trial uses FoundationOne CDx."}]


def test_no_names_means_no_flags():
    assert draft.wording_flags("The trial uses FoundationOne CDx.", []) == []
    assert draft.wording_flags(None, NAMES) == []


def demo_report(**changes):
    base = {"headline": HEADLINE, "status_line": "Recruiting; no results posted", "gap": GAP,
            "discovery": {"summary": "An early-stage profiling study of blood and tumour tissue.",
                          "intervention_text": "ctDNA, tumor NGS",
                          "mentions": [{"name": n, "resolved_diagnostic_id": None} for n in NAMES]},
            "uncertainties": [AMBIGUOUS, UNRESOLVED],
            "related": [{"rationale": "The new trial moves blood-based profiling to an earlier stage."},
                        {"rationale": None}]}
    base.update(changes)
    return base


def test_the_demo_report_wording_is_clean():
    assert draft.mention_names(demo_report()) == NAMES
    assert draft.report_wording_flags(demo_report()) == []


def test_report_fields_are_all_scanned_with_the_field_named():
    r = demo_report(related=[{"rationale": "Both trials studied FoundationOne Liquid."}],
                    script="The trial showed FoundationOne CDx works.")
    flags = draft.report_wording_flags(r)
    assert {(f["field"], f["verb"], f["name"]) for f in flags} == {
        ("related.rationale", "studies", "FoundationOne Liquid"),
        ("script", "showed", "FoundationOne CDx")}
