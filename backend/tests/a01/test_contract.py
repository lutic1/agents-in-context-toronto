"""A01: every AD-14 route registered, 501 in the one error shape, GET /schema, CORS, the start hook."""

from __future__ import annotations

import ast
import inspect
import re
import types
from pathlib import Path

import pytest

from dxp.api import app as app_module
from dxp.api.app import create_app, run_startup

BACKEND = Path(__file__).resolve().parents[2]
REPO = BACKEND.parent

# Every route of the AD-14 table (and V48), as (method, path under /api/v1).
BUILT_ROUTES = [
    ("GET", "/whoami"), ("GET", "/grants"), ("GET", "/grants/{grant_id}"), ("GET", "/policies"),
    ("POST", "/runs"), ("GET", "/runs"), ("GET", "/runs/{run_id}"), ("POST", "/runs/{run_id}/stop"),
    ("GET", "/runs/{run_id}/audit"), ("GET", "/runs/{run_id}/stream"),
    ("GET", "/actions"), ("GET", "/actions/{action_id}"), ("POST", "/actions/{action_id}/resolve"),
    ("GET", "/decisions/{decision_id}"),
    ("GET", "/scopes"), ("GET", "/scopes/{scope_id}"),
    ("GET", "/reports"), ("GET", "/reports/{report_id}"), ("POST", "/reports/{report_id}/decision"),
    ("POST", "/reports/{report_id}/revert"),
    ("POST", "/reports/{report_id}/briefing"), ("GET", "/reports/{report_id}/briefing"),
    ("POST", "/reports/{report_id}/avatar"), ("GET", "/reports/{report_id}/avatar"),
    ("GET", "/memories"), ("GET", "/memories/{memory_id}"),
    ("POST", "/memories/{memory_id}/correct"), ("POST", "/memories/{memory_id}/revoke"),
    ("GET", "/tasks"), ("GET", "/tasks/{task_id}"),
    ("GET", "/teams"),
    ("GET", "/diagnostics/{dx_id}"), ("POST", "/diagnostics/{dx_id}/values/{value_id}/review"),
    ("GET", "/proposals"), ("GET", "/proposals/{p_id}"),
]
NOT_BUILT_ROUTES = [
    ("GET", "/runs/{run_id}/audit/audio"), ("POST", "/policies/{policy_id}/approve"),
    ("POST", "/jobs"), ("GET", "/jobs"), ("GET", "/jobs/{job_id}"),
    ("GET", "/teams/{team_id}"), ("POST", "/teams/{team_id}/seen"),
    ("GET", "/diagnostics"), ("POST", "/diagnostics/{dx_id}/values"), ("POST", "/query"),
    ("POST", "/proposals/{p_id}/decision"),
    ("GET", "/rules"), ("POST", "/rules/{rule_id}/status"),
    ("GET", "/alerts"), ("POST", "/alerts/{alert_id}/dismiss"), ("GET", "/alerts/{alert_id}/audio"),
    ("GET", "/changes"), ("GET", "/graph"), ("GET", "/digest"), ("GET", "/terms"),
    ("POST", "/shortlists"), ("GET", "/shortlists"),
]
ALL_STUBS = BUILT_ROUTES + NOT_BUILT_ROUTES

# Minimal valid bodies, so a stub answers 501 rather than 422.
BODIES = {
    "/runs": {"grant_id": "lbdx", "set": "discover"},
    "/actions/{action_id}/resolve": {"outcome": "delivered", "note": "seen in channel"},
    "/reports/{report_id}/decision": {"action": "approve"},
    "/reports/{report_id}/revert": {"note": "undo"},
    "/memories/{memory_id}/correct": {"text": "t", "note": "n"},
    "/memories/{memory_id}/revoke": {"note": "n"},
    "/diagnostics/{dx_id}/values/{value_id}/review": {"action": "accept"},
    "/policies/{policy_id}/approve": {"version": 1},
    "/teams/{team_id}/seen": {"seq": 1},
    "/diagnostics/{dx_id}/values": {"field": "trials", "value": "NCT00000000"},
    "/query": {"text": "q"},
    "/proposals/{p_id}/decision": {"action": "accept"},
    "/shortlists": {"team_id": "t", "intended_use": "u"},
}


def concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "x1", path)


def test_openapi_lists_every_route() -> None:
    spec = create_app().openapi()
    listed = {(method.upper(), path.removeprefix("/api/v1")) for path, ops in spec["paths"].items() for method in ops}
    missing = set(ALL_STUBS) - listed
    assert not missing, missing
    assert listed - set(ALL_STUBS) == {("GET", "/schema")}


def is_stub_route(method: str, path: str) -> bool:
    """True while the route's endpoint is still A01's stub (its body raises not_implemented).
    Once the owning PR finishes the route, the 501 assertion no longer applies to it."""
    routers = (*app_module.OWNED_ROUTERS, app_module._contract_router())
    for route in (r for router in routers for r in router.routes):
        if getattr(route, "path", None) == path and method in getattr(route, "methods", ()):
            try:
                source = inspect.getsource(route.endpoint)
            except (OSError, TypeError):
                return False
            return "raise not_implemented(" in source
    raise AssertionError(f"{method} {path} is not registered")


@pytest.mark.parametrize(("method", "path"), ALL_STUBS)
def test_stub_returns_501_in_the_error_shape(api_client, method: str, path: str) -> None:
    if not is_stub_route(method, path):
        pytest.skip(f"{method} {path} is finished by its owner; the stub contract no longer applies")
    response = api_client.request(method, "/api/v1" + concrete(path), json=BODIES.get(path))
    assert response.status_code == 501, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "not_implemented"
    assert isinstance(body["error"]["message"], str) and body["error"]["message"]


def test_other_errors_use_the_same_shape(api_client) -> None:
    unknown = api_client.get("/api/v1/nowhere")
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "not_found"
    # a deferred route (always A01's), so a finished owner route cannot change the answer
    invalid = api_client.post("/api/v1/query", json={"filters": {}})
    assert invalid.status_code == 422
    assert set(invalid.json()) == {"error"} and invalid.json()["error"]["code"] == "invalid_request"


def test_openapi_documents_the_error_shape_and_the_key_header() -> None:
    spec = create_app().openapi()
    op = spec["paths"]["/api/v1/reports/{report_id}"]["get"]
    assert op["responses"]["501"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")
    assert "X-DxP-Key" in str(spec["components"]["securitySchemes"])


def test_openapi_publishes_the_epic_10_and_v48_shapes() -> None:
    schemas = create_app().openapi()["components"]["schemas"]
    for name in ("Scope", "Report", "Relationship", "Retrieval", "MemoryUse", "Memory", "Task", "Media",
                 "SourceVersion", "Audit", "AuditEntry", "Decision", "Action", "Proposal", "Principal",
                 "Run", "Grant", "Stamp", "PolicySet", "Admission", "Event", "Record", "Value",
                 "Node", "Link", "Team", "ReportRevertResponse", "ErrorResponse"):
        assert name in schemas, name
    assert "raw_text" not in schemas["SourceVersion"]["properties"]
    task_status = schemas["Task"]["properties"]["status"]["enum"]
    assert task_status == ["authorised", "queued", "running", "done", "failed", "blocked", "stopped", "cancelled"]
    report = schemas["Report"]["properties"]
    for key in ("gap", "uncertainties", "discovery", "version_id", "script", "script_hash", "approval",
                "revert", "reverted_by", "reverted_at"):
        assert key in report, key
    assert "reverted" in schemas["Report"]["properties"]["status"]["enum"]
    assert "reverted" in schemas["Relationship"]["properties"]["status"]["enum"]
    assert {"op", "reverts_proposal_id"} <= set(schemas["Proposal"]["properties"])
    assert set(schemas["TaskResult"]["properties"]) >= {"answer", "with_posted_results", "query", "searched_count", "limit"}
    assert "claim_kind" in schemas["ReportDecisionRequest"]["properties"]
    assert "reason" in schemas["ReportApproval"]["properties"]
    assert {"condition_aliases", "priority_refs"} <= set(schemas["Scope"]["properties"])


def test_types_ts_is_generated_from_the_current_schema() -> None:
    types_ts = (REPO / "web" / "lib" / "types.ts").read_text()
    assert types_ts.startswith("// Generated by tools/gen_types.sh")
    schemas = create_app().openapi()["components"]["schemas"]
    for name in schemas:
        assert re.search(rf"^\s+{re.escape(name)}: {{", types_ts, re.M), f"{name} missing: run tools/gen_types.sh"


# ---------------------------------------------------------------------------
# GET /schema
# ---------------------------------------------------------------------------

FAKE_DESCRIBE = {
    "fields": [
        {"key": "lifecycle_stage", "label": "Lifecycle stage", "cardinality": "single", "canonical_form": "enum",
         "enum": [{"value": "discovery", "label": "Discovery"}, {"value": "regulatory_approval", "label": "Regulatory approval"}]},
        {"key": "trials", "label": "Trials", "cardinality": "list", "canonical_form": "nct_id", "enum": None},
    ],
    "stage_order": ["discovery", "regulatory_approval"],
    "not_determined_stage": "not_determined",
    "early_research_stages": ["discovery"],
    "low_confidence_threshold": 0.7,
}
FAKE_REGISTRY = types.SimpleNamespace(describe=lambda: FAKE_DESCRIBE)


def test_schema_serialises_describe_and_derives_enums(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_module, "_load_registry", lambda: FAKE_REGISTRY)
    response = api_client.get("/api/v1/schema")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["stage_order"] == ["discovery", "regulatory_approval"]
    assert body["enums"] == {"lifecycle_stage": ["discovery", "regulatory_approval"]}
    assert body["fields"][0]["enum"][1] == {"value": "regulatory_approval", "label": "Regulatory approval"}
    assert body["fields"][1]["enum"] is None
    assert body["low_confidence_threshold"] == 0.7 and body["early_research_stages"] == ["discovery"]


def test_schema_serves_the_real_registry(api_client) -> None:
    from dxp.schema import registry

    response = api_client.get("/api/v1/schema")
    assert response.status_code == 200, response.text
    body = response.json()
    described = registry.describe()
    assert [f["key"] for f in body["fields"]] == [f["key"] for f in described["fields"]]
    assert body["stage_order"] == list(described["stage_order"])
    assert body["enums"]["lifecycle_stage"] == [v["value"] for f in described["fields"] if f["key"] == "lifecycle_stage" for v in f["enum"]]


def test_schema_without_the_registry_is_an_error_not_a_crash(api_client, monkeypatch: pytest.MonkeyPatch) -> None:
    def missing():
        raise app_module.ApiError(503, "registry_unavailable", "not yet")

    monkeypatch.setattr(app_module, "_load_registry", missing)
    response = api_client.get("/api/v1/schema")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "registry_unavailable"


# ---------------------------------------------------------------------------
# CORS, the start hook and the flags
# ---------------------------------------------------------------------------


def test_cors_origins_come_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.setenv("DXP_ALLOWED_ORIGINS", "https://dxp.example, http://localhost:3000")
    client = TestClient(create_app())
    ok = client.options("/api/v1/reports", headers={"Origin": "https://dxp.example", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "https://dxp.example"
    other = client.options("/api/v1/reports", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert other.headers.get("access-control-allow-origin") is None


async def test_start_hook_order_and_no_task_start_while_task_run_is_off(monkeypatch: pytest.MonkeyPatch, fake_run_function) -> None:
    from dxp import store

    calls: list[str] = []

    async def fake_ensure_indexes() -> None:
        calls.append("store.ensure_indexes")

    monkeypatch.setattr(store, "ensure_indexes", fake_ensure_indexes)
    for module, name in (("dxp.ledger", "recover_applying"), ("dxp.retrieval", "ensure_indexes"),
                         ("dxp.reports", "recover_accepting"), ("dxp.tasks", "recover_authorisations"),
                         ("dxp.ledger", "recover_reverting"), ("dxp.reports", "recover_reverting")):
        # Record the order only: once an owner finishes one of these (A06's
        # recover_applying first), the real call needs Atlas, which this test does not.
        async def wrapped(_label=f"{module}.{name}"):
            calls.append(_label)
            return None

        monkeypatch.setattr(__import__(module, fromlist=[name]), name, wrapped)

    await run_startup(fake_run_function)
    assert calls == [
        "store.ensure_indexes", "dxp.ledger.recover_applying", "dxp.retrieval.ensure_indexes",
        "dxp.reports.recover_accepting", "dxp.tasks.recover_authorisations",
        "dxp.ledger.recover_reverting", "dxp.reports.recover_reverting",
    ]
    assert fake_run_function.spawned == []  # dispatch_next started nothing


def test_flags_are_off_by_default(features) -> None:
    from dxp import feature_enabled

    for flag in ("task_run", "revert", "live_stream"):
        assert not feature_enabled(flag)
    features("revert")
    assert feature_enabled("revert") and not feature_enabled("task_run")


def test_start_function_spawns_on_the_run_function(fake_run_function) -> None:
    app_module.start_function(fake_run_function)("run_abc")
    assert fake_run_function.spawned == ["run_abc"]


# ---------------------------------------------------------------------------
# Repository rules
# ---------------------------------------------------------------------------

ENV_NAMES = [
    "MONGODB_URI", "DXP_DB", "ANTHROPIC_API_KEY", "DXP_API_KEY", "DXP_AGENT_KEY", "DXP_SEED_KEY",
    "SLACK_WEBHOOK_URL", "DXP_BASE_URL", "DXP_ALLOWED_ORIGINS", "DXP_DEMO_PACE", "DXP_EMBEDDING",
    "VOYAGE_API_KEY", "ELEVENLABS_API_KEY", "HEYGEN_API_KEY", "DXP_FEATURES", "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_DXP_FEATURES", "LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT",
]


def test_env_example_names_every_variable_with_no_values() -> None:
    lines = [ln.strip() for ln in (REPO / ".env.example").read_text().splitlines()]
    assignments = dict(ln.split("=", 1) for ln in lines if ln and not ln.startswith("#"))
    assert set(ENV_NAMES) <= set(assignments), set(ENV_NAMES) - set(assignments)
    assert all(value == "" for value in assignments.values())
    assert "DXP_FEED" not in assignments


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("package", ["gate", "runs", "actions"])
def test_governance_imports_nothing_from_memory_retrieval_or_reports(package: str) -> None:
    for path in (BACKEND / "dxp" / package).rglob("*.py"):
        bad = {n for n in _imports(path) if n.split(".")[:2] in (["dxp", "memory"], ["dxp", "retrieval"], ["dxp", "reports"])}
        assert not bad, f"{path}: {bad} (AD-28)"


def test_runs_imports_nothing_from_actions_or_tasks() -> None:
    for path in (BACKEND / "dxp" / "runs").rglob("*.py"):
        bad = {n for n in _imports(path) if n.split(".")[:2] in (["dxp", "actions"], ["dxp", "tasks"])}
        assert not bad, f"{path}: {bad} (D43, V38)"


def test_reports_imports_nothing_from_tasks() -> None:
    for path in (BACKEND / "dxp" / "reports").rglob("*.py"):
        assert not {n for n in _imports(path) if n.startswith("dxp.tasks")}, path


def test_only_store_creates_a_mongo_client() -> None:
    for path in (BACKEND / "dxp").rglob("*.py"):
        if "store" in path.relative_to(BACKEND / "dxp").parts[:1]:
            continue
        assert "MongoClient" not in path.read_text(), path
