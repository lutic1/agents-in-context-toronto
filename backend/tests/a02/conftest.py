"""Fixtures and test doubles for A02. Hand-written test data only; nothing
from data/."""

from __future__ import annotations

from typing import Any

import pytest
from dxp.identity import derive, normalise_name

# Exact trade-name strings as an FDA lung row would carry them (D45). This is
# a stand-in for the aliases A13's seed writes through the ledger; the real
# list is fetched during the event and is never read from data/.
SEEDED_TRADE_NAMES: tuple[str, ...] = (
    "FoundationOne CDx",  # tissue
    "FoundationOne Liquid CDx",  # plasma cfDNA
    "Guardant360 CDx",
    "Guardant360® Liquid CDx",
    "Agilent Resolution ctDx FIRST assay",
    "cobas EGFR Mutation Test v2",
    "therascreen EGFR RGQ PCR Kit",
)


def make_alias_doc(trade_name: str, *, created_mode: str = "baseline") -> dict[str, Any]:
    """The alias a seeded Diagnostic is found through (AD-3): ``_id`` is the
    normalised trade name; the Diagnostic ID is derived from it."""
    key = normalise_name(trade_name)
    return {
        "_id": key,
        "diagnostic_id": derive("dx_", key),
        "name": trade_name,
        "source": "fda_cdx_list",
        "created_mode": created_mode,
    }


class FakeAliases:
    """Supports only ``find_one({"_id": ...})`` and records every call, so a
    test can prove the resolver reads by exact key and never writes."""

    def __init__(self, docs: list[dict[str, Any]] | None = None) -> None:
        self._docs = {d["_id"]: dict(d) for d in (docs or [])}
        self.calls: list[tuple[str, Any]] = []

    def find_one(self, filter: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        self.calls.append(("find_one", filter))
        if set(filter) != {"_id"} or not isinstance(filter["_id"], str):
            raise AssertionError(f"resolver must look up by exact _id only, got {filter!r}")
        doc = self._docs.get(filter["_id"])
        return dict(doc) if doc is not None else None

    def __getattr__(self, name: str) -> Any:  # any write or scan is a failure
        raise AssertionError(f"resolver called aliases.{name}()")


def seeded_aliases() -> FakeAliases:
    return FakeAliases([make_alias_doc(t) for t in SEEDED_TRADE_NAMES])


@pytest.fixture
def aliases() -> FakeAliases:
    """The aliases collection as the FDA seed leaves it (exact trade names)."""
    return seeded_aliases()


@pytest.fixture
def seeded_trade_names() -> tuple[str, ...]:
    return SEEDED_TRADE_NAMES


@pytest.fixture
def alias_doc():
    return make_alias_doc


@pytest.fixture
def make_aliases():
    def _make(*docs: dict[str, Any]) -> FakeAliases:
        return FakeAliases(list(docs))

    return _make


@pytest.fixture(autouse=True)
def _no_global_aliases():
    """Every test starts and ends with no use_aliases() override."""
    from dxp.identity import use_aliases

    use_aliases(None)
    yield
    use_aliases(None)
