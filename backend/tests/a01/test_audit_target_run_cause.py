"""A01: AuditEntry.target and Run.cause are optional, additive, and match what is stored."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dxp.api import models as m

_AUDIT_BASE = {
    "decision_id": "dec_1",
    "outcome": "allowed",
    "kind": "file_proposal",
    "destination": "ledger",
    "grant_id": "grant_curator",
    "grant_version": 1,
}

_RUN_BASE = {
    "id": "run_1",
    "agent": "dxp-curator",
    "initiated_by": "reviewer_1",
    "grant_id": "grant_curator",
    "grant_version": 1,
    "set": "discover",
    "kind": "discover",
    "status": "running",
}


def test_audit_entry_target_is_optional() -> None:
    entry = m.AuditEntry(**_AUDIT_BASE)
    assert entry.target is None
    assert "target" in m.AuditEntry.model_fields
    assert not m.AuditEntry.model_fields["target"].is_required()


def test_audit_entry_target_carries_a_scope_target_for_a_v43_update() -> None:
    decision_target = {
        "diagnostic_id": None,
        "proposal_id": "p_1",
        "scope_id": "scope_plasma_ctdna_nsclc",
    }
    entry = m.AuditEntry(**_AUDIT_BASE, target=decision_target)
    assert isinstance(entry.target, m.Target)
    assert entry.target.diagnostic_id is None
    assert entry.target.scope_id == "scope_plasma_ctdna_nsclc"
    assert entry.model_dump()["target"]["scope_id"] == "scope_plasma_ctdna_nsclc"


def test_run_cause_is_optional_and_null_on_non_task_runs() -> None:
    run = m.Run(**_RUN_BASE, cause=None)
    assert run.cause is None
    assert not m.Run.model_fields["cause"].is_required()
    assert m.Run(**_RUN_BASE).cause is None


def test_run_cause_validates_the_stored_task_run_shape() -> None:
    # The exact dict runs.start_if_absent stores: {"task_id": task_id, "report_id": report_id}.
    stored = {"task_id": "task_1", "report_id": "rep_1"}
    run = m.Run(
        **{**_RUN_BASE, "set": "task:task_1", "kind": "task", "task_id": "task_1"},
        cause=stored,
    )
    assert isinstance(run.cause, m.RunCause)
    assert run.cause.model_dump() == stored
    no_report = m.Run(
        **{**_RUN_BASE, "set": "task:task_1", "kind": "task"},
        cause={"task_id": "task_1", "report_id": None},
    )
    assert no_report.cause is not None and no_report.cause.report_id is None


def test_run_cause_needs_a_task_id() -> None:
    with pytest.raises(ValidationError):
        m.RunCause(report_id="rep_1")


def test_run_model_keeps_a_stored_cause() -> None:
    from dxp.runs.common import run_model

    doc = {
        **{k: v for k, v in _RUN_BASE.items() if k != "id"},
        "_id": "run_1",
        "kind": "task",
        "set": "task:task_1",
        "task_id": "task_1",
        "cause": {"task_id": "task_1", "report_id": "rep_1"},
    }
    assert run_model(doc).cause == m.RunCause(task_id="task_1", report_id="rep_1")


def test_openapi_publishes_audit_target_and_run_cause(api_client) -> None:
    schemas = api_client.get("/openapi.json").json()["components"]["schemas"]
    # Output shapes list every key as present (Shape config); both values may be null.
    assert schemas["AuditEntry"]["properties"]["target"]["anyOf"] == [
        {"$ref": "#/components/schemas/Target"},
        {"type": "null"},
    ]
    assert schemas["Run"]["properties"]["cause"]["anyOf"] == [
        {"$ref": "#/components/schemas/RunCause"},
        {"type": "null"},
    ]
    assert set(schemas["RunCause"]["properties"]) == {"task_id", "report_id"}
    assert schemas["RunCause"]["properties"]["task_id"]["type"] == "string"
