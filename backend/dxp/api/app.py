"""`create_app(run_function)`: the FastAPI app and every route of AD-14, registered once (A01).

- Every route lives under `/api/v1`. The routers of the other PRs are included here, so no
  later PR edits this file; each owner finishes the bodies in its own `routes_*.py`.
- Superseded, cut and deferred routes are registered here and stay 501.
- `GET /schema` is the only route A01 finishes: it serialises A02's `schema/registry.py`.
- Allowed CORS origins come from `DXP_ALLOWED_ORIGINS` (comma-separated); no other PR edits CORS.
- The startup hook runs `store.ensure_indexes()`, then the recovery hooks (no-op stubs until
  A06, A19+A20 and A24 finish them), then `tasks.dispatch_next()`, which does nothing while the
  backend flag `task_run` is off (V38, V46). V48 adds `ledger.recover_reverting()` and
  `reports.recover_reverting()` (no-op stubs until A26).
"""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from dxp.api import (
    routes_actions,
    routes_audit,
    routes_avatar,
    routes_briefing,
    routes_diagnostics,
    routes_grants,
    routes_memories,
    routes_proposals,
    routes_report_decision,
    routes_report_revert,
    routes_reports,
    routes_resolve,
    routes_review,
    routes_run_stream,
    routes_runs,
    routes_scopes,
    routes_teams,
)
from dxp.api import models as m
from dxp.api.errors import ERROR_RESPONSES, ApiError, install_error_handlers, not_implemented

log = logging.getLogger("dxp.api")

API_PREFIX = "/api/v1"

# Documents the header every request carries (AD-14, AD-18). It confers nothing by itself:
# the principal is resolved server-side by api.auth (A03).
dxp_key = APIKeyHeader(name="X-DxP-Key", auto_error=False, description="Resolved server-side to the calling principal.")

# Routers finished by other PRs, in the order of the AD-14 table.
OWNED_ROUTERS = (
    routes_grants.router,  # A03
    routes_runs.router,  # A07+A11
    routes_run_stream.router,  # A27 (V48)
    routes_audit.router,  # A07+A11
    routes_actions.router,  # A07+A11
    routes_resolve.router,  # A09
    routes_scopes.router,  # A05
    routes_reports.router,  # A19+A20
    routes_report_decision.router,  # A24
    routes_report_revert.router,  # A26 (V48)
    routes_briefing.router,  # B06
    routes_avatar.router,  # B08
    routes_memories.router,  # A21+A22
    routes_teams.router,  # A13
    routes_diagnostics.router,  # A14
    routes_review.router,  # A14
    routes_proposals.router,  # A14
)


def allowed_origins() -> list[str]:
    raw = os.environ.get("DXP_ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# ---------------------------------------------------------------------------
# GET /schema (AD-2): the registry's fields, enums and stage order
# ---------------------------------------------------------------------------

REGISTRY_MODULE = "dxp.schema.registry"


def _field_list(raw: Any) -> list[m.SchemaField]:
    items = raw.items() if isinstance(raw, dict) else ((None, spec) for spec in raw)
    fields = []
    for key, spec in items:
        spec = dict(spec) if isinstance(spec, dict) else dict(vars(spec))
        fields.append(
            m.SchemaField(
                key=spec.get("key", key),
                label=spec.get("label", spec.get("key", key)),
                cardinality=spec["cardinality"],
                enum=spec.get("enum"),
            )
        )
    return fields


def schema_from_registry(registry: Any) -> m.SchemaResponse:
    """Serialise the registry. A02's `schema/registry.py` exposes either `describe()` returning
    the SchemaResponse fields, or the module constants FIELDS, ENUMS, STAGE_ORDER and
    CONFIDENCE_THRESHOLD."""
    describe = getattr(registry, "describe", None)
    if callable(describe):
        return m.SchemaResponse.model_validate(describe())
    return m.SchemaResponse(
        fields=_field_list(registry.FIELDS),
        enums={name: list(values) for name, values in dict(registry.ENUMS).items()},
        stage_order=list(registry.STAGE_ORDER),
        confidence_threshold=getattr(registry, "CONFIDENCE_THRESHOLD", None),
    )


def _load_registry() -> Any:
    try:
        return importlib.import_module(REGISTRY_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != REGISTRY_MODULE:
            raise
        raise ApiError(503, "registry_unavailable", "The field registry is not on main yet (A02).") from exc


def _contract_router() -> APIRouter:
    router = APIRouter()

    @router.get("/schema", response_model=m.SchemaResponse, tags=["schema"])
    async def get_schema() -> m.SchemaResponse:
        return schema_from_registry(_load_registry())

    # Superseded, cut and deferred routes: registered once, left 501 (AD-14, D40).
    def stub(method: str, path: str, status: str, response_model: Any = None, body: Any = None) -> None:
        label = f"{method} {path.replace('{', '<').replace('}', '>')}"

        if body is None:
            async def endpoint() -> Any:
                raise not_implemented(label, status)
        else:
            async def endpoint(payload) -> Any:
                raise not_implemented(label, status)

            endpoint.__annotations__ = {"payload": body, "return": Any}

        router.add_api_route(
            path,
            endpoint,
            methods=[method],
            response_model=response_model,
            tags=["not built"],
            summary=f"{label} ({status})",
            name=f"{method.lower()}_{path}",
        )

    stub("GET", "/runs/{run_id}/audit/audio", "superseded by the report briefing, V12")
    stub("POST", "/policies/{policy_id}/approve", "cut, 9.11", m.Policy, m.PolicyApproveRequest)
    stub("POST", "/jobs", "superseded by /runs")
    stub("GET", "/jobs", "superseded by /runs")
    stub("GET", "/jobs/{job_id}", "superseded by /runs")
    stub("GET", "/teams/{team_id}", "deferred, 6.3", m.Team)
    stub("POST", "/teams/{team_id}/seen", "deferred, 5.1", m.Team, m.TeamSeenRequest)
    stub("GET", "/diagnostics", "deferred, D40", m.RecordList)
    stub("POST", "/diagnostics/{dx_id}/values", "deferred, 4.7", m.Proposal, m.ValueAddRequest)
    stub("POST", "/query", "deferred, 4.2", m.QueryResponse, m.QueryRequest)
    stub("POST", "/proposals/{p_id}/decision", "superseded by the report decision, V8", m.ProposalDecisionResponse, m.ProposalDecisionRequest)
    stub("GET", "/rules", "deferred, 2.6")
    stub("POST", "/rules/{rule_id}/status", "deferred, 2.6", m.Rule)
    stub("GET", "/alerts", "deferred, 3.1")
    stub("POST", "/alerts/{alert_id}/dismiss", "deferred, 3.1", m.Alert)
    stub("GET", "/alerts/{alert_id}/audio", "deferred, 3.4")
    stub("GET", "/changes", "cut, 9.9", m.ChangesResponse)
    stub("GET", "/graph", "cut, 5.1", m.GraphResponse)
    stub("GET", "/digest", "deferred, 3.3", m.DigestResponse)
    stub("GET", "/terms", "deferred, 4.8")
    stub("POST", "/shortlists", "deferred, 4.4", m.Shortlist, m.ShortlistCreate)
    stub("GET", "/shortlists", "deferred, 4.4")
    return router


# ---------------------------------------------------------------------------
# Startup hook
# ---------------------------------------------------------------------------


async def run_startup(run_function: Any = None) -> None:
    """Indexes and validators, then recovery, then start a queued task if any (V38, V45)."""
    from dxp import ledger, reports, retrieval, store, tasks

    await store.ensure_indexes()
    await ledger.recover_applying()
    await retrieval.ensure_indexes()
    await reports.recover_accepting()
    await tasks.recover_authorisations()
    await ledger.recover_reverting()
    await reports.recover_reverting()
    await tasks.dispatch_next(start_function(run_function))


def start_function(run_function: Any):
    """How the API starts a run: `.spawn()` on the run function modal_app passed in (AD-16),
    never `modal.Function.from_name`, and never inside a request."""

    def start(run_id: str) -> Any:
        if run_function is None:
            raise RuntimeError("No run function was passed to create_app().")
        return run_function.spawn(run_id)

    return start


# Shapes no route returns directly, published in /openapi.json so web/lib/types.ts has them.
EXTRA_SHAPES = (m.Admission, m.PolicySet, m.SourceVersion, m.Event, m.Stamp)  # Event: also the stream's message (V48)


def _install_openapi(app: FastAPI) -> None:
    from fastapi.openapi.utils import get_openapi
    from pydantic.json_schema import models_json_schema

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            spec = get_openapi(title=app.title, version=app.version, routes=app.routes, description=app.description)
            schemas = spec.setdefault("components", {}).setdefault("schemas", {})
            _, extra = models_json_schema(
                [(shape, "serialization") for shape in EXTRA_SHAPES],
                ref_template="#/components/schemas/{model}",
            )
            for name, schema in extra.get("$defs", {}).items():
                schemas.setdefault(name, schema)
            app.openapi_schema = spec
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]


def create_app(run_function: Any = None) -> FastAPI:
    """Build the API. `run_function` is the Modal run function from modal_app (A04); routes reach
    it as `request.app.state.run_function` and the start hook as `request.app.state.start_run`."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await run_startup(run_function)
        yield
        from dxp import store

        await store.close()

    app = FastAPI(
        title="DxP API",
        version="1",
        lifespan=lifespan,
        responses=ERROR_RESPONSES,
    )
    app.state.run_function = run_function
    app.state.start_run = start_function(run_function)
    install_error_handlers(app)

    origins = allowed_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["X-DxP-Key", "Content-Type"],
        )

    api = APIRouter(prefix=API_PREFIX, dependencies=[Depends(dxp_key)])
    api.include_router(_contract_router())
    for router in OWNED_ROUTERS:
        api.include_router(router)
    app.include_router(api)
    _install_openapi(app)
    return app
