"""The documents A05 writes, and the fixtures its Atlas tests insert, pass A03's validators.

Checked locally with A03's `jsonschema_lite`, so a validator mismatch shows up without Atlas."""

from __future__ import annotations

import importlib

from dxp import discovery
from dxp.store import schemas

from .conftest import run_doc, scope_doc, setup_results_for

validate = importlib.import_module("tests.a03.jsonschema_lite").validate


def check(collection: str, doc: dict) -> None:
    assert validate(schemas.validator(collection), doc) == [], (collection, doc.get("_id"))


async def test_written_documents_validate(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    check("runs", run_doc())
    check("research_scopes", scope_doc())
    setup_results_for(ctgov_fake)
    await discovery.scan("scope_plasma_ctdna_nsclc", discover_run)
    for name in ("decisions", "actions", "source_versions", "research_scopes"):
        docs = list(fakedb[name].docs.values())
        assert docs, name
        for doc in docs:
            check(name, doc)


async def test_blocked_decision_validates(fakedb, events, fake_runs, fake_actions, scan_gate, ctgov_fake, discover_run) -> None:
    scan_gate.blocked = True
    await discovery.scan("scope_plasma_ctdna_nsclc", discover_run)
    (doc,) = fakedb["decisions"].docs.values()
    check("decisions", doc)
