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


CHANGED_BEFORE = "The trial showed that blood profiling finds drivers."
CHANGED_AFTER = "The trial investigates whether blood profiling finds drivers; no results posted."
CITED = [{"memory_id": "mem_1", "before": CHANGED_BEFORE, "after": CHANGED_AFTER}]


def test_a_cited_real_difference_is_the_memorys_effect():
    uses = draft.memory_effects(BEFORE, AFTER, [M1], CITED)
    assert uses == [{
        "memory_id": "mem_1", "version": 1, "author": "sam", "score": 0.71,
        "source": {"decision_id": "dec_1", "report_id": "rep_0"},
        "effect": {"target": "sentence", "before": CHANGED_BEFORE, "after": CHANGED_AFTER},
    }]
    assert draft.effect_text(uses[0]).startswith("changed sentence: before ")


def test_a_difference_nobody_cites_is_attributed_to_no_memory():
    uses = draft.memory_effects(BEFORE, AFTER, [M1, M2])
    assert [u["effect"] for u in uses] == [None, None]
    assert draft.effect_text(uses[0]) == "retrieved, no change"


def test_identical_drafts_mean_retrieved_no_change_even_when_cited():
    uses = draft.memory_effects(BEFORE, dict(BEFORE), [M1, M2], CITED)
    assert [u["effect"] for u in uses] == [None, None]


def test_a_citation_must_match_a_real_difference_exactly():
    wrong = [{"memory_id": "mem_1", "before": "It is recruiting.", "after": CHANGED_AFTER},
             {"memory_id": "mem_2", "before": CHANGED_BEFORE, "after": "Something else."}]
    assert [u["effect"] for u in draft.memory_effects(BEFORE, AFTER, [M1, M2], wrong)] == [None, None]


def test_only_the_named_memory_gets_the_effect_and_unknown_ids_are_ignored():
    cited = [{"memory_id": "mem_404", "before": CHANGED_BEFORE, "after": CHANGED_AFTER}, dict(CITED[0], memory_id="mem_2")]
    uses = draft.memory_effects(BEFORE, AFTER, [M1, M2], cited)
    by_id = {u["memory_id"]: u["effect"] for u in uses}
    assert by_id["mem_1"] is None and by_id["mem_2"]["after"] == CHANGED_AFTER


def test_apply_citations_keeps_draft_one_except_for_the_cited_change():
    one = {"draft": 1, "headline": "Alpha one. Beta.", "summary": "Gamma. Delta.", "gap": "Why?",
           "claims": [{"text": "Gamma.", "claim_kind": "claim_planned", "quote": "g"}]}
    candidate = {"draft": 2, "headline": "Alpha two. Beta.", "summary": "Gamma changed. Delta moved.", "gap": "Why?",
                 "claims": [{"text": "Gamma changed.", "claim_kind": "claim_planned", "quote": "g2"}]}
    cited = [{"memory_id": "mem_1", "before": "Gamma.", "after": "Gamma changed."}]
    accepted = draft.verified_citations(one, candidate, cited, ["mem_1"])
    two = draft.apply_citations(one, candidate, accepted)
    assert two["headline"] == "Alpha one. Beta." and two["summary"] == "Gamma changed. Delta."
    assert two["claims"] == [{"text": "Gamma changed.", "claim_kind": "claim_planned", "quote": "g2"}]
    assert {(c["before"], c["after"]) for c in draft.draft_changes(one, two)} == {("Gamma.", "Gamma changed.")}
    assert two["draft"] == 2 and one["summary"] == "Gamma. Delta."


def test_removed_and_added_sentences_are_changes():
    removed = draft.draft_changes({"headline": "A. B."}, {"headline": "A."})
    assert removed == [{"target": "sentence", "before": "B.", "after": ""}]
    added = draft.draft_changes({"headline": "A."}, {"headline": "A. C."})
    assert added == [{"target": "sentence", "before": "", "after": "C."}]


def test_a_changed_claim_kind_is_a_label_change():
    before = {"claims": [{"text": "Blood profiling finds drivers.", "claim_kind": "claim_performed_or_results"}]}
    after = {"claims": [{"text": "Blood profiling finds drivers.", "claim_kind": "claim_planned"}]}
    assert draft.draft_changes(before, after) == [
        {"target": "label", "before": "claim_performed_or_results", "after": "claim_planned"}]
    cited = [{"memory_id": "mem_1", "before": "claim_performed_or_results", "after": "claim_planned"}]
    assert draft.memory_effects(before, after, [M1], cited)[0]["effect"]["target"] == "label"


def test_no_memories_and_missing_drafts_are_handled():
    assert draft.memory_effects(BEFORE, AFTER, [], CITED) == []
    assert draft.memory_effects(None, None, [M1], CITED)[0]["effect"] is None


def test_memory_id_may_come_as_id():
    uses = draft.memory_effects(BEFORE, AFTER, [{"id": "mem_9", "text": "no results posted"}],
                                [dict(CITED[0], memory_id="mem_9")])
    assert uses[0]["memory_id"] == "mem_9" and uses[0]["effect"] is not None


@pytest.mark.parametrize("sentence,verb", [
    ("The trial uses FoundationOne CDx on tissue.", "uses"),
    ("Patients were tested using FoundationOne Liquid.", "uses"),
    ("FoundationOne CDx was used for tissue samples.", "uses"),
    ("This trial studies FoundationOne Liquid in early-stage disease.", "studies"),
    ("FoundationOne CDx is studied before surgery.", "studies"),
    ("FoundationOne Liquid showed high concordance.", "showed"),
    ("The trial shows that foundationone cdx finds drivers.", "showed"),
    ("The trial will use FoundationOne CDx on tissue.", "uses"),
    ("The trial aims to study FoundationOne Liquid.", "studies"),
    ("Results show FoundationOne CDx finds drivers.", "showed"),
    ("The trial tests FoundationOne CDx.", "tests"),
    ("The trial will evaluate FoundationOne Liquid in plasma.", "evaluates"),
    ("Investigators assess FoundationOne CDx before surgery.", "assesses"),
    ("The sponsor utilises FoundationOne Liquid.", "uses"),
    ("FoundationOne CDx has been evaluated in tissue.", "evaluates"),
    ("The study demonstrates that FoundationOne CDx works.", "showed"),
])
def test_uses_studies_showed_about_a_named_product_is_flagged(sentence, verb):
    flags = draft.wording_flags(sentence, NAMES)
    assert verb in [f["verb"] for f in flags] and all(f["sentence"] == sentence for f in flags)


@pytest.mark.parametrize("text", [
    HEADLINE, AMBIGUOUS, UNRESOLVED, GAP,
    "'FoundationOne CDx' is named in the record (otherNames of \"ctDNA, tumor NGS\").",
    "The record names FoundationOne CDx, which is not proof of use.",
    "The trial uses blood samples. The record names FoundationOne Liquid.",
    "This study names FoundationOne CDx among its other names.",
    "FoundationOne CDx is a tissue test; FoundationOne Liquid is named separately.",
    "The record lists FoundationOne CDx, and a blood test is used for plasma samples.",
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
