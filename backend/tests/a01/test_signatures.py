"""A01: the frozen signatures exist, stubs raise NotImplementedError, the start-hook ones are no-ops."""

from __future__ import annotations

import importlib
import inspect

import pytest

# (module, function, parameter names) as frozen in "Contracts come first" (development-plan.md).
FROZEN = [
    ("dxp.api.auth", "resolve_actor", ["api_key"]),
    ("dxp.gate.policy_sets", "current_grant", ["grant_id"]),
    ("dxp.gate.policy_sets", "current_set", []),
    ("dxp.runs", "start", ["caller", "grant_id", "set", "run_id"]),
    ("dxp.runs", "context", ["run_id", "key"]),
    ("dxp.runs", "admit", ["run_id", "item_key"]),
    ("dxp.runs", "release", ["admission_id"]),
    ("dxp.runs", "sweep", ["run_id"]),
    ("dxp.runs", "settle", ["run_id"]),
    ("dxp.runs", "finish", ["run_id"]),
    ("dxp.runs", "stop", ["run_id"]),
    ("dxp.runs", "stamp", ["run_id"]),
    ("dxp.gate", "evaluate", ["ctx", "action"]),
    ("dxp.ledger", "file", ["finding_id", "changes", "mode", "ctx"]),
    ("dxp.ledger", "apply", ["proposal_id"]),
    ("dxp.ledger", "recover_applying", []),
    ("dxp.llm", "extract", ["item", "aliases"]),
    ("dxp.llm", "check", ["finding", "source_text"]),
    ("dxp.llm", "call_structured", ["model", "schema", "messages"]),
    ("dxp.discovery", "scan", ["scope_id", "ctx"]),
    ("dxp.retrieval", "ensure_indexes", []),
    ("dxp.retrieval", "embed", ["texts"]),
    ("dxp.retrieval", "related", ["scope_id", "text", "k", "exclude"]),
    ("dxp.retrieval", "memories", ["team_id", "text", "tags", "k"]),
    ("dxp.reports", "relate", ["new_item", "related_item"]),
    ("dxp.reports", "draft", ["item", "findings", "related", "memories"]),
    ("dxp.reports", "file", ["draft", "ctx"]),
    ("dxp.reports", "add_related", ["report_id", "refs", "ctx"]),
    ("dxp.reports", "script_for", ["report"]),
    ("dxp.reports", "decide", ["report_id", "action", "note", "correction", "reviewer"]),
    ("dxp.reports", "recover_accepting", []),
    ("dxp.memory", "create", ["team_id", "text", "tags", "source", "reviewer", "ctx"]),
    ("dxp.memory", "correct", ["memory_id", "text", "note", "ctx"]),
    ("dxp.memory", "revoke", ["memory_id", "note", "ctx"]),
    ("dxp.memory", "retrieve", ["team_id", "text", "tags"]),
    ("dxp.tasks", "authorise", ["report_id", "reviewer"]),
    ("dxp.tasks", "dispatch_next", ["start"]),
    ("dxp.tasks", "mark_abandoned", ["task_id"]),
    ("dxp.tasks", "recover_authorisations", []),
    ("dxp.tasks", "run", ["task_id"]),
    ("dxp.gate.grants", "issue_task_grant", ["task", "decision", "session"]),
    ("dxp.actions", "dispatch", ["action", "ctx"]),
    ("dxp.actions", "mark_unknown", ["action_id", "error"]),
    ("dxp.actions", "mark_failed", ["action_id", "error"]),
    ("dxp.actions", "resolve", ["action_id", "outcome", "note", "ctx"]),
    ("dxp.pipeline", "run", ["run_id"]),
    ("dxp.briefing", "generate", ["report_id", "ctx"]),
    ("dxp.briefing", "render_avatar", ["report_id", "ctx"]),
    ("dxp.briefing", "avatar_status", ["report_id"]),
    ("dxp.search.readmodel", "get_diagnostic", ["dx_id"]),
    # V48
    ("dxp.reports", "revert", ["report_id", "note", "reviewer"]),
    ("dxp.reports", "recover_reverting", []),
    ("dxp.ledger", "revert_proposal", ["proposal_id", "decision"]),
    ("dxp.ledger", "recover_reverting", []),
    ("dxp.tasks", "cancel_for_report", ["report", "decision"]),
    ("dxp.gate.grant_expiry", "expire_task_grant", ["task", "decision"]),
    ("dxp.search.stream", "run_events", ["run_id", "resume_after"]),
]

# The start hook calls these before their owners merge: no-op stubs (dispatch_next does nothing
# while task_run is off).
NO_OPS = {
    ("dxp.ledger", "recover_applying"), ("dxp.retrieval", "ensure_indexes"), ("dxp.reports", "recover_accepting"),
    ("dxp.tasks", "recover_authorisations"), ("dxp.tasks", "dispatch_next"),
    ("dxp.ledger", "recover_reverting"), ("dxp.reports", "recover_reverting"),
}


def resolve(module: str, name: str):
    return getattr(importlib.import_module(module), name)


@pytest.mark.parametrize(("module", "name", "params"), FROZEN)
def test_signature_is_frozen(module: str, name: str, params: list[str]) -> None:
    function = resolve(module, name)
    assert list(inspect.signature(function).parameters) == params
    hints = inspect.get_annotations(function, eval_str=True)
    assert "return" in hints, f"{module}.{name} has no typed result"
    assert all(p in hints for p in params), f"{module}.{name} has an untyped argument"


def still_stub(function, marker: str) -> bool:
    """True while the function is still A01's stub. Once its owner finishes it, the stub
    assertions no longer apply (the frozen signature still does)."""
    try:
        return marker in inspect.getsource(function)
    except (OSError, TypeError):
        return False


@pytest.mark.parametrize(("module", "name"), sorted(NO_OPS))
async def test_start_hook_stubs_are_no_ops(module: str, name: str) -> None:
    function = resolve(module, name)
    if not still_stub(function, "No-op stub"):
        pytest.skip(f"{module}.{name} is finished by its owner")
    args = [lambda run_id: None] if name == "dispatch_next" else []
    assert await function(*args) is None


def _dummy_args(function) -> list[object]:
    return [None] * len(inspect.signature(function).parameters)


@pytest.mark.parametrize(("module", "name"), [(m, n) for m, n, _ in FROZEN if (m, n) not in NO_OPS])
async def test_unfinished_stubs_raise_not_implemented(module: str, name: str) -> None:
    function = resolve(module, name)
    if not still_stub(function, "raise NotImplementedError("):
        pytest.skip(f"{module}.{name} is finished by its owner")
    with pytest.raises(NotImplementedError):
        result = function(*_dummy_args(function))
        if inspect.isawaitable(result):
            await result


def test_store_names_the_drafts_use() -> None:
    from dxp import store

    assert callable(store.db) and callable(store.collection)
    params = inspect.signature(store.emit_event).parameters
    assert list(params)[0] == "event" and params["session"].kind is inspect.Parameter.KEYWORD_ONLY


async def test_emit_event_requires_a_dedupe_key() -> None:
    from dxp import store

    with pytest.raises(ValueError):
        await store.emit_event({"type": "report_filed"})


def test_decision_model_validates_an_ad14_dict() -> None:
    from dxp.api.models import Decision

    decision = Decision.model_validate({
        "id": "dec_1", "stamp": {"kind": "seed", "principal": "seed"}, "kind": "apply_value",
        "destination": "ledger", "grant_id": "seed", "grant_version": 1, "outcome": "allowed",
    })
    assert decision.outcome == "allowed" and decision.run_id is None
