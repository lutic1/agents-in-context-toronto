"""A02: identity.derive(), normalise_name() and exact trade-name matching
(AD-3, D45, V34, V37)."""

from __future__ import annotations

import hashlib
import importlib
import inspect
from pathlib import Path

import pytest
from dxp import identity
from dxp.identity import (
    ResolverUnavailable,
    derive,
    diagnostic_id,
    normalise_name,
    resolve_exact,
    use_aliases,
)

TISSUE = derive("dx_", "foundationone cdx")  # FoundationOne CDx
PLASMA = derive("dx_", "foundationone liquid cdx")  # FoundationOne Liquid CDx

# --- derive() -------------------------------------------------------------------


def test_derive_is_prefix_plus_16_hex_of_sha256_over_pipe_joined_parts():
    expected = "p_" + hashlib.sha256(b"f_1|biomarkers|EGFR").hexdigest()[:16]
    assert derive("p_", "f_1", "biomarkers", "EGFR") == expected


def test_derive_is_deterministic_and_order_sensitive():
    assert derive("rep_", "run_a", "ct:1") == derive("rep_", "run_a", "ct:1")
    assert derive("rep_", "run_a", "ct:1") != derive("rep_", "ct:1", "run_a")
    assert derive("a_", "x") != derive("b_", "x")


def test_derive_writes_ints_in_decimal():
    assert derive("mem_", "team", 2) == derive("mem_", "team", "2")


@pytest.mark.parametrize("bad", [None, 1.5, b"x", True, ["x"]])
def test_derive_refuses_parts_that_would_hash_silently(bad):
    with pytest.raises(TypeError):
        derive("x_", "a", bad)


def test_derive_needs_a_prefix_and_a_part():
    with pytest.raises(TypeError):
        derive("", "a")
    with pytest.raises(ValueError):
        derive("x_")


def test_derived_run_id_of_a_task_is_stable():
    task_id = derive("task_", "rep_abc")
    assert derive("run_", task_id) == derive("run_", task_id)
    assert task_id.startswith("task_") and len(task_id) == len("task_") + 16


# --- normalise_name() ---------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Guardant360® Liquid CDx", "guardant360 liquid cdx"),
        ("FoundationOne CDx", "foundationone cdx"),
        ("FOUNDATIONONE   cdx ", "foundationone cdx"),
        ("Agilent Resolution ctDx FIRST assay", "agilent resolution ctdx first assay"),
        ("Foo™ Bar©", "foo bar"),
        ("cobas® EGFR Mutation Test v2", "cobas egfr mutation test v2"),
        ("therascreen_EGFR-RGQ/PCR (Kit)", "therascreen egfr rgq pcr kit"),
        ("ＦｏｕｎｄａｔｉｏｎＯｎｅ CDx", "foundationone cdx"),  # full width, NFKC
        ("", ""),
        ("®™©", ""),
    ],
)
def test_normalise_name(raw, expected):
    assert normalise_name(raw) == expected


def test_normalise_name_removes_trademark_before_nfkc():
    # NFKC alone would turn "™" into "TM" and leave "foo tm".
    assert normalise_name("Foo™") == "foo"


def test_normalise_name_is_idempotent():
    for name in ("Guardant360® Liquid CDx", "FoundationOne Liquid", "x--y__z"):
        once = normalise_name(name)
        assert normalise_name(once) == once


def test_normalise_name_refuses_non_strings():
    with pytest.raises(TypeError):
        normalise_name(None)  # type: ignore[arg-type]


def test_diagnostic_id_derives_from_the_id_alias():
    assert diagnostic_id("FoundationOne CDx") == TISSUE
    assert diagnostic_id("FoundationOne Liquid CDx") == PLASMA
    assert diagnostic_id("Guardant360® Liquid CDx") == derive("dx_", "guardant360 liquid cdx")
    with pytest.raises(ValueError):
        diagnostic_id("®")


def test_the_four_scope_trade_names_give_four_distinct_ids_and_exclude_the_tissue_test():
    scope = [
        "FoundationOne Liquid CDx",
        "Guardant360 CDx",
        "Guardant360® Liquid CDx",
        "Agilent Resolution ctDx FIRST assay",
    ]
    ids = {diagnostic_id(n) for n in scope}
    assert len(ids) == 4
    assert TISSUE not in ids
    assert PLASMA in ids


# --- resolve_exact(): the required behaviours (V34, V37) ---------------------------------


def test_foundationone_cdx_resolves_exactly_to_the_tissue_diagnostic(aliases):
    assert resolve_exact("FoundationOne CDx", aliases=aliases) == TISSUE


def test_foundationone_liquid_cdx_resolves_exactly_to_the_plasma_diagnostic(aliases):
    assert resolve_exact("FoundationOne Liquid CDx", aliases=aliases) == PLASMA


def test_tissue_and_plasma_tests_are_never_merged(aliases):
    assert TISSUE != PLASMA
    assert resolve_exact("FoundationOne CDx", aliases=aliases) != resolve_exact(
        "FoundationOne Liquid CDx", aliases=aliases
    )


@pytest.mark.parametrize("name", ["FoundationOne Liquid", "Guardant360", "FoundationOne"])
def test_former_hand_written_aliases_resolve_to_nothing(aliases, name):
    assert resolve_exact(name, aliases=aliases) is None


@pytest.mark.parametrize(
    "name",
    [
        "Foundation One CDx",  # different words
        "FoundationOne CDx assay",  # longer
        "FoundationOne Liquid CDx test",
        "foundationone",  # prefix
        "Liquid CDx",  # suffix
        "Guardant360 Liquid",
        "Guardant 360 CDx",
        "F1CDx",
        "F1LCDx",
        "ctDNA, tumor NGS",  # the generic intervention of NCT04712877
        "Resolution ctDx",
        "",
        "   ",
        "®",
    ],
)
def test_no_prefix_substring_or_fuzzy_match(aliases, name):
    assert resolve_exact(name, aliases=aliases) is None


@pytest.mark.parametrize(
    "name, trade_name",
    [
        ("Guardant360® Liquid CDx", "Guardant360® Liquid CDx"),
        ("Guardant360 Liquid CDx", "Guardant360® Liquid CDx"),  # ® removed
        ("FOUNDATIONONE CDX", "FoundationOne CDx"),  # case folded
        ("  FoundationOne   CDx. ", "FoundationOne CDx"),  # spacing and punctuation
        ("Guardant360 CDx", "Guardant360 CDx"),
        ("Agilent Resolution ctDx FIRST assay", "Agilent Resolution ctDx FIRST assay"),
    ],
)
def test_exact_match_is_after_normalise_name(aliases, name, trade_name):
    assert resolve_exact(name, aliases=aliases) == diagnostic_id(trade_name)


def test_guardant360_cdx_and_guardant360_liquid_cdx_are_different(aliases):
    assert resolve_exact("Guardant360 CDx", aliases=aliases) != resolve_exact(
        "Guardant360® Liquid CDx", aliases=aliases
    )


def test_the_nct04712877_mentions(aliases):
    """The record's otherNames: one resolves exactly, one stays as written."""
    mentions = ["FoundationOne CDx", "FoundationOne Liquid"]
    resolved = {m: resolve_exact(m, aliases=aliases) for m in mentions}
    assert resolved == {"FoundationOne CDx": TISSUE, "FoundationOne Liquid": None}


def test_none_resolves_to_nothing_without_a_lookup(make_aliases):
    fake = make_aliases()
    assert resolve_exact(None, aliases=fake) is None
    assert fake.calls == []


def test_non_string_name_is_refused(aliases):
    with pytest.raises(TypeError):
        resolve_exact(42, aliases=aliases)  # type: ignore[arg-type]


def test_lookup_is_one_find_one_by_exact_normalised_id_and_never_writes(aliases):
    resolve_exact("Guardant360® Liquid CDx", aliases=aliases)
    resolve_exact("FoundationOne Liquid", aliases=aliases)
    assert aliases.calls == [
        ("find_one", {"_id": "guardant360 liquid cdx"}),
        ("find_one", {"_id": "foundationone liquid"}),
    ]


def test_an_alias_created_by_a_live_run_is_not_a_seeded_trade_name(make_aliases, alias_doc):
    fake = make_aliases(alias_doc("FoundationOne Liquid", created_mode="live"))
    assert resolve_exact("FoundationOne Liquid", aliases=fake) is None


def test_resolves_to_the_alias_diagnostic_id_when_stored(make_aliases):
    fake = make_aliases({"_id": "foundationone cdx", "diagnostic_id": TISSUE})
    assert resolve_exact("FoundationOne CDx", aliases=fake) == TISSUE
    bare = make_aliases({"_id": "foundationone cdx"})
    assert resolve_exact("FoundationOne CDx", aliases=bare) == TISSUE


def test_nothing_seeded_means_nothing_resolves(make_aliases):
    empty = make_aliases()
    for name in ("FoundationOne CDx", "FoundationOne Liquid CDx"):
        assert resolve_exact(name, aliases=empty) is None


def test_frozen_call_shape_resolve_exact_name_uses_the_bound_collection(aliases):
    use_aliases(aliases)
    assert resolve_exact("FoundationOne CDx") == TISSUE
    assert resolve_exact("FoundationOne Liquid") is None


def test_without_a_store_or_binding_the_resolver_says_so(monkeypatch):
    """A missing database is never mistaken for "unresolved"."""
    import sys

    import dxp

    monkeypatch.setitem(sys.modules, "dxp.store", None)  # import fails
    # `from dxp import store` reads the package attribute first, so an earlier
    # import of dxp.store (by any other test) must be hidden too.
    monkeypatch.delattr(dxp, "store", raising=False)
    with pytest.raises(ResolverUnavailable):
        resolve_exact("FoundationOne CDx")


# --- No hand-written aliases (V34) -----------------------------------------------------


def test_there_is_no_identity_aliases_module():
    pkg_dir = Path(identity.__file__).parent
    assert not (pkg_dir / "aliases.py").exists()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("dxp.identity.aliases")


def test_identity_holds_no_name_mapping_table():
    """No module-level mapping or name list in identity: the only source of
    truth for what resolves is the seeded aliases collection."""
    from collections.abc import Mapping

    for mod_name in ("dxp.identity", "dxp.identity.core", "dxp.identity.resolve"):
        mod = importlib.import_module(mod_name)
        for attr, value in vars(mod).items():
            if attr.startswith("__"):
                continue
            if isinstance(value, Mapping):  # a str.maketrans table has int keys
                assert not any(isinstance(k, str) for k in value), f"{mod_name}.{attr} maps names"
            if isinstance(value, (list, tuple, set, frozenset)) and attr != "__all__":
                assert not any(
                    isinstance(v, str) and "cdx" in v.lower() for v in value
                ), f"{mod_name}.{attr} lists trade names"


def test_identity_exports_the_frozen_names():
    for name in ("derive", "normalise_name", "resolve_exact"):
        assert callable(getattr(identity, name))
    params = list(inspect.signature(resolve_exact).parameters.values())
    assert params[0].name == "name"
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in params[1:])
