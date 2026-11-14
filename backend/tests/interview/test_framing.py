"""Framing (V70 amendment): an allowlist plus a mechanical no-facts check, and the persona."""

from __future__ import annotations

import pytest

from dxp.interview import compose, framing, texts

from .conftest import Q_STATUS, VERSION_ID, RAW_TEXT
from dxp.interview.cards import load_cards


def test_the_allowlist_is_the_four_sentences_of_the_ruling() -> None:
    assert framing.ALLOWLIST == (
        "Here's what the accepted record says.",
        "I can only answer from this record.",
        "The accepted record doesn't answer that.",
        "These are the quotes it rests on.",
    )


@pytest.mark.parametrize("sentence", framing.ALLOWLIST)
def test_every_allowlisted_sentence_passes_the_no_facts_check(sentence) -> None:
    assert framing.facts_in(sentence) == []
    assert framing.is_clean_framing(sentence)
    assert framing.allowed_framing([sentence]) == [sentence]


BAD = [
    ("FoundationOne CDx is better than FoundationOne Liquid.", "result_word"),
    ("Here's what FoundationOne says.", "inner_capital_name"),
    ("Here's what Tagrisso does.", "capitalised_name"),
    ("The trial NCT04712877 is recruiting.", "nct_id"),
    ("The trial is NCT 04712877.", "nct_id"),
    ("The accepted record lists 120 participants.", "digit"),
    ("Here's what the record says in 2024.", "digit"),
    ("The assay was 92% sensitive.", "digit"),
    ("The test showed a positive result.", "result_word"),
    ("The accepted record says the assay is better.", "assay_or_product_word"),
    ("The ctDNA panel is named.", "assay_or_product_word"),
    ("It performed well.", "result_word"),
    ("The results are in.", "result_word"),
    ("Sensitivity was high.", "unlisted_first_word"),
    ("I'm FoundationOne CDx.", "persona_claim"),
    ("I'm the trial.", "persona_claim"),
    ("I am the evidence guide for Dr Smith.", "persona_claim"),
    ("Here's what NSCLC means.", "all_caps_name"),
    ("Here's what Dr Smith found.", "capitalised_name"),
    ("Toronto is the location.", "unlisted_first_word"),
    ("The sponsor is Example University.", "assay_or_product_word"),
    ("These quotes show it is more effective.", "result_word"),
]


@pytest.mark.parametrize(("sentence", "kind"), BAD)
def test_a_framing_string_with_a_fact_fails_the_check(sentence, kind) -> None:
    assert kind in framing.facts_in(sentence), framing.facts_in(sentence)
    assert not framing.is_clean_framing(sentence)


@pytest.mark.parametrize("sentence", [s for s, _ in BAD])
def test_a_bad_string_is_dropped_by_the_allowlist(sentence) -> None:
    assert framing.allowed_framing([sentence]) == []


def test_a_clean_sentence_that_is_not_on_the_allowlist_is_dropped() -> None:
    clean = "Here is what the accepted record says."
    assert framing.facts_in(clean) == []
    assert framing.allowed_framing([clean]) == []
    assert framing.allowed_framing(["here's what the accepted record says."]) == []
    assert framing.allowed_framing([" " + framing.FRAME_INTRO]) == []


def test_allowed_framing_keeps_order_and_drops_the_rest() -> None:
    mixed = [framing.FRAME_QUOTES, "Something else.", framing.FRAME_INTRO, "I'm FoundationOne."]
    assert framing.allowed_framing(mixed) == [framing.FRAME_QUOTES, framing.FRAME_INTRO]


def test_the_persona_is_dxps_evidence_guide_and_never_im_something() -> None:
    assert framing.PERSONA == "DxP's evidence guide"
    assert framing.PERSONA in texts.VOICE_LABEL
    for sentence in (*framing.ALLOWLIST, texts.MEDICAL_REFUSAL, texts.BLOCKED, texts.VOICE_LABEL):
        assert "I'm" not in sentence and "I am" not in sentence


def test_the_composed_answer_has_only_allowlisted_framing_around_quotes() -> None:
    card = next(c for c in load_cards(_report(), {VERSION_ID: RAW_TEXT}) if c.text == Q_STATUS)
    blocks = compose.compose([card])
    assert blocks == [framing.FRAME_INTRO, f'"{Q_STATUS}" [1]', framing.FRAME_QUOTES]
    assert compose.render([card]) == "\n\n".join(blocks)


def _report():
    from .conftest import make_report

    return make_report()
