"""A08 against A02's real functions on main: derive, resolve_exact, canonical.

`resolve_exact` reads an `aliases` collection; here it gets an in-memory one
(A02's `identity.use_aliases()`), holding only seeded trade names, so no Atlas
is needed. The Atlas path itself is A02's test.
"""

import asyncio

from dxp import identity
from dxp.llm import _deps, extract_item
from dxp.llm.types import CheckOut, ExtractOut, FieldOut, TriageOut, VerdictOut
from dxp.schema import registry

from .conftest import SEEDED_NAMES


class SeededAliases:
    """A sync stand-in for the `aliases` collection: `_id` = normalise_name(trade name)."""

    def __init__(self, trade_names):
        self.docs = {
            identity.normalise_name(n): {"_id": identity.normalise_name(n), "created_mode": "baseline"}
            for n in trade_names
        }

    def find_one(self, filter, *args, **kwargs):
        return self.docs.get(filter.get("_id"))


def run(coro):
    return asyncio.run(coro)


def with_aliases(fn):
    identity.use_aliases(SeededAliases(SEEDED_NAMES))
    try:
        return fn()
    finally:
        identity.use_aliases(None)


def test_real_resolve_exact_matches_exact_names_only():
    def go():
        tissue = run(_deps.resolve_exact("FoundationOne CDx"))
        plasma = run(_deps.resolve_exact("FoundationOne Liquid CDx"))
        assert tissue and plasma and tissue != plasma
        assert tissue == identity.diagnostic_id("FoundationOne CDx")
        for name in ("FoundationOne Liquid", "FoundationOne", "Guardant360"):
            assert run(_deps.resolve_exact(name)) is None
        assert run(_deps.resolve_exact("Guardant360® Liquid CDx")) is not None

    with_aliases(go)


def test_real_derive_and_canonical():
    assert _deps.derive("f_", "sv_1", "-") == identity.derive("f_", "sv_1", "-")
    assert _deps.canonical("trials", "nct04712877") == registry.canonical("trials", "nct04712877")
    assert "discovery" in _deps.stage_names() and registry.NOT_DETERMINED not in _deps.stage_names()


def test_extract_with_real_a02(fake_llm, item_nct04712877):
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=True, reason="x"))
    fake_llm.script(
        "ExtractOut",
        ExtractOut(
            summary="This study investigates molecular profiling using blood and tumour tissue in lung cancer.",
            record_fields=[
                FieldOut(field="trials", raw_value="NCT04712877", quote="ctDNA, tumor NGS", confidence=0.6),
                FieldOut(field="biomarkers", raw_value="not-a-biomarker-xyz", quote="ctDNA", confidence=0.6),
            ],
            stage_evidence=None,
            assays=[],
        ),
    )
    fake_llm.script("CheckOut", CheckOut(verdicts=[VerdictOut(index=0, supported=True)]), CheckOut())

    result = with_aliases(lambda: run(extract_item(item_nct04712877, SEEDED_NAMES)))
    assert result.status == "extracted"
    tissue = identity.diagnostic_id("FoundationOne CDx")
    assert [f.diagnostic_id for f in result.findings] == [None, tissue]
    assert result.unresolved_names == ["FoundationOne Liquid"]
    record = result.findings[0]
    assert record.id == identity.derive("f_", "sv_test04712877aaaa", "-")
    trials = next(v for v in record.values if v.field == "trials")
    assert trials.value == "NCT04712877"
    # A value with no canonical form fails and goes no further.
    bad = next(v for v in record.values if v.field == "biomarkers")
    assert bad.value is None and not bad.passed
    assert "canonical_error" in [f.code for f in record.failures]


def test_unreachable_aliases_is_a_resolve_error_not_unresolved(fake_llm, item_nct04712877, monkeypatch):
    def unavailable(name, **kw):
        raise identity.ResolverUnavailable("no store")

    monkeypatch.setattr(identity, "resolve_exact", unavailable)
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=False, reason="x"))
    result = run(extract_item(item_nct04712877, SEEDED_NAMES))
    assert "resolve_error" in [f.code for f in result.failures]
    assert result.unresolved_names == []


def test_frozen_wrappers_return_dicts(fake_llm, fake_registry, item_nct04712877):
    from dxp import llm

    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=False, reason="x"))
    out = run(llm.extract(item_nct04712877, SEEDED_NAMES))
    assert isinstance(out, dict) and out["status"] == "not_relevant"

    finding = {
        "id": "f_1", "source_ref": "s", "version_id": "sv_1", "target": "scope_collection",
        "summary": "s", "prompt_version": "p",
        "values": [{"field": "trials", "raw": "x", "value": "x", "label": "x", "quote": "absent quote"}],
    }
    checked = run(llm.check(finding, "source text"))
    assert isinstance(checked, dict) and checked["values"][0]["check"]["quote_found"] is False

    fake_llm.script("dict_schema", {"raw": None, "parsed": {"a": 1}, "parsing_error": None})
    schema = {"title": "dict_schema", "type": "object", "properties": {"a": {"type": "integer"}}}
    assert run(llm.call_structured("fast", schema, [{"role": "user", "content": "hi"}])) == {"a": 1}


def test_prompt_lists_registry_values_and_answers_pass_real_canonical(fake_llm, item_nct04712877):
    """The prompt gives each enum field's registry values; answers in those
    values pass the real registry.canonical(), a natural phrase does not."""
    modality = registry.get_field("modality").enum
    uses = registry.get_field("clinical_uses").enum
    stages = registry.get_field("tumour_stage_or_line").enum
    fake_llm.script("TriageOut", TriageOut(concerns_lung_cancer_diagnostic=True, reason="x"))
    fake_llm.script(
        "ExtractOut",
        ExtractOut(
            summary="This study investigates molecular profiling in lung cancer.",
            record_fields=[
                FieldOut(field="modality", raw_value=modality[0], quote="ctDNA, tumor NGS", confidence=0.7),
                FieldOut(field="clinical_uses", raw_value=uses[0], quote="ctDNA, tumor NGS", confidence=0.7),
                FieldOut(field="tumour_stage_or_line", raw_value=stages[0], quote="ctDNA, tumor NGS", confidence=0.7),
                FieldOut(field="modality", raw_value="ctDNA", quote="ctDNA, tumor NGS", confidence=0.7),
            ],
            stage_evidence=None,
            assays=[],
        ),
    )
    fake_llm.script("CheckOut", CheckOut(verdicts=[VerdictOut(index=i, supported=True) for i in range(3)]), CheckOut())

    result = with_aliases(lambda: run(extract_item(item_nct04712877, SEEDED_NAMES)))
    system = fake_llm.calls_for("ExtractOut")[0]["messages"][0][1]
    assert f"- modality: one of {', '.join(modality)}" in system
    assert f"- clinical_uses: one of {', '.join(uses)}" in system
    assert f"- tumour_stage_or_line: one of {', '.join(stages)}" in system
    assert "- trials: an NCT ID" in system

    record = result.findings[0]
    good = [v for v in record.values if v.value is not None]
    assert [(v.field, v.value) for v in good] == [
        ("modality", modality[0]), ("clinical_uses", uses[0]), ("tumour_stage_or_line", stages[0])
    ]
    assert all(v.passed for v in good)
    bad = [v for v in record.values if v.value is None]
    assert [v.raw for v in bad] == ["ctDNA"] and not bad[0].passed


def test_check_with_a_malformed_finding_returns_a_failure(fake_llm):
    from dxp import llm

    out = run(llm.check({"id": "f_1"}, "text"))
    assert out["failures"][0]["code"] == "invalid_finding"
    assert fake_llm.calls == []
