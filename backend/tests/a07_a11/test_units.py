"""Pure parts of runs and the audit, without Atlas."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dxp import runs
from dxp.api.errors import ApiError
from dxp.identity import derive
from dxp.search import audit

from .conftest import SAM, TASK_ID

BACKEND = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(("value", "parsed"), [
    ("discover", ("discover", None, None)),
    ("nct:NCT05715229", ("items", "NCT05715229", None)),
    (f"task:{TASK_ID}", ("task", None, TASK_ID)),
])
def test_parse_set(value, parsed) -> None:
    assert runs.parse_set(value) == parsed


@pytest.mark.parametrize("value", ["", "Discover", "nct:NCT1", "task:abc", "nct:NCT05715229 ", "items"])
def test_parse_set_refuses_anything_else(value) -> None:
    with pytest.raises(ApiError) as caught:
        runs.parse_set(value)
    assert caught.value.status_code == 400


async def test_a_task_set_without_the_derived_run_id_is_refused_before_any_read() -> None:
    # No database is configured for this test: the refusal happens before any read (V38).
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "task-x", f"task:{TASK_ID}")
    assert caught.value.status_code == 403 and caught.value.code == "task_set_refused"
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "task-x", f"task:{TASK_ID}", run_id="run_0000000000000000")
    assert caught.value.status_code == 403 and caught.value.code == "task_run_id_mismatch"


async def test_a_derived_run_id_on_a_discover_set_is_refused() -> None:
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "lbdx", "discover", run_id=derive("run_", TASK_ID))
    assert caught.value.status_code == 400


async def test_context_needs_a_run_id_and_a_key() -> None:
    with pytest.raises(ApiError) as caught:
        await runs.context("", "key-agent")
    assert caught.value.status_code == 403
    with pytest.raises(ApiError) as caught:
        await runs.context("run_x", "")
    assert caught.value.status_code == 401


def test_scrub_drops_raw_text_at_any_depth() -> None:
    doc = {"raw_text": "x", "a": {"raw_text": "y", "b": [{"raw_text": "z", "quote": "q"}]}}
    assert audit.scrub(doc) == {"a": {"b": [{"quote": "q"}]}}


def test_decision_order_is_seq_then_time() -> None:
    docs = [{"_id": "dec_b", "seq": 7}, {"_id": "dec_c", "seq": None}, {"_id": "dec_a", "seq": 3}]
    assert [d["_id"] for d in sorted(docs, key=audit._order)] == ["dec_a", "dec_b", "dec_c"]


def test_a_blocked_entry_keeps_its_failed_check_and_claims() -> None:
    decision = {
        "_id": "dec_0000000000000001", "seq": 4, "outcome": "blocked", "failed_check": "evidence_checks",
        "kind": "file_proposal", "destination": "ledger", "grant_id": "lbdx", "grant_version": 1,
        "policy_set_version": "ps_0000000000000000", "inputs": {"headline": "h", "raw_text": "never"},
        "target": {"report_id": "rep_1", "draft": 1, "diagnostic_id": None, "scope_id": "scope_x"},
        "checks": [{"check": "grant_active", "passed": True}, {"check": "evidence_checks", "passed": False}],
        "claims": [{"claim_kind": "claim_performed_or_results", "text": "showed", "passed": False,
                    "failed_policies": ["claim_performed_or_results@v1"]}],
        "stamp": {"kind": "run", "principal": "dxp-curator", "run_id": "run_x"},
    }
    entry = audit._entry(decision, None, None, False, {}, {}, {"_id": "run_x"})
    assert entry.outcome == "blocked" and entry.failed_check == "evidence_checks"
    assert entry.claims[0].claim_kind == "claim_performed_or_results" and entry.claims[0].passed is False
    assert entry.action_id is None and entry.status is None
    assert "raw_text" not in entry.inputs
    assert entry.relationships == []  # a blocked draft lists no relationships


def test_package_runs_imports_nothing_it_must_not() -> None:
    forbidden = (["dxp", "actions"], ["dxp", "tasks"], ["dxp", "memory"], ["dxp", "retrieval"], ["dxp", "reports"])
    for path in (BACKEND / "dxp" / "runs").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for name in names:
                assert name.split(".")[:2] not in forbidden, f"{path}: {name}"


async def test_record_progress_refuses_counts_the_pipeline_does_not_own() -> None:
    with pytest.raises(ValueError):
        await runs.record_progress("run_x", counts={"not_admitted": 3}, active_items=[], failure_lines=[])


async def test_record_scan_refuses_unknown_keys() -> None:
    with pytest.raises(ValueError):
        await runs.record_scan("run_x", {"cursor_from": "2026-09-01", "raw_text": "never"})
