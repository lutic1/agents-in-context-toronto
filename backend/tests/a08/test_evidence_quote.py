"""evidence.quote_in_source(): the only quote check (AD-6). No model, no network."""

from dxp.evidence import MAX_QUOTE_CHARS, quote_in_source

SOURCE = (
    "Testing Tumor Tissue and Blood to Help Select Personalized Treatments\n"
    "Interventions:   DIAGNOSTIC_TEST: ctDNA, tumor NGS\n"
    "The patient’s sample – plasma – is tested."
)


def test_exact_quote_is_found():
    assert quote_in_source("ctDNA, tumor NGS", SOURCE)


def test_whitespace_and_line_breaks_are_tolerated():
    assert quote_in_source("Personalized Treatments Interventions: DIAGNOSTIC_TEST", SOURCE)


def test_typographic_quotes_and_dashes_are_tolerated():
    assert quote_in_source("The patient's sample - plasma - is tested.", SOURCE)


def test_case_matters():
    assert not quote_in_source("CTDNA, TUMOR NGS", SOURCE)


def test_paraphrase_is_not_found():
    assert not quote_in_source("ctDNA and tumor NGS", SOURCE)


def test_ellipsis_is_not_found():
    assert not quote_in_source("Testing Tumor Tissue ... Personalized Treatments", SOURCE)


def test_empty_or_missing_inputs_are_not_found():
    assert not quote_in_source("", SOURCE)
    assert not quote_in_source("   ", SOURCE)
    assert not quote_in_source(None, SOURCE)
    assert not quote_in_source("ctDNA", "")
    assert not quote_in_source("ctDNA", None)


def test_quote_over_300_characters_is_not_found():
    long_source = "word " * 200
    quote = ("word " * 70).strip()
    assert len(quote) > MAX_QUOTE_CHARS
    assert not quote_in_source(quote, long_source)
    assert quote_in_source(quote[:MAX_QUOTE_CHARS].strip(), long_source)


def test_a_name_not_in_the_record_is_not_found():
    assert not quote_in_source("FoundationOne Liquid CDx", "other names: FoundationOne CDx, FoundationOne Liquid")
