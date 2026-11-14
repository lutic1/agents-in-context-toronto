"""Runs and stop (Stories 9.1, 9.5). The background sweep lives here (D43, V38). Stub from A01 (contract); finished by A07+A11.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A07+A11 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A07+A11"


@router.post("/runs", response_model=m.Run, tags=["runs"])
async def create_run(body: m.RunCreate) -> m.Run:
    """set is discover or nct:<NCT ID>; a task: set is refused with 403 (V38). 409 while a run is
    running or stopping."""
    raise not_implemented("POST /runs", OWNER)


@router.get("/runs", response_model=m.RunList, tags=["runs"])
async def list_runs() -> m.RunList:
    raise not_implemented("GET /runs", OWNER)


@router.get("/runs/{run_id}", response_model=m.Run, tags=["runs"])
async def get_run(run_id: str) -> m.Run:
    raise not_implemented("GET /runs/<run_id>", OWNER)


@router.post("/runs/{run_id}/stop", response_model=m.Run, tags=["runs"])
async def stop_run(run_id: str) -> m.Run:
    raise not_implemented("POST /runs/<run_id>/stop", OWNER)
