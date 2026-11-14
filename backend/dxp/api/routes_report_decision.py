"""The report decision and tasks (Story 10.8). No route starts a task (V38). Stub from A01 (contract); finished by A24.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A24 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A24"


@router.post("/reports/{report_id}/decision", response_model=m.ReportDecisionResponse, tags=["reports"])
async def decide_report(report_id: str, body: m.ReportDecisionRequest) -> m.ReportDecisionResponse:
    raise not_implemented("POST /reports/<report_id>/decision", OWNER)


@router.get("/tasks", response_model=m.TaskList, tags=["tasks"])
async def list_tasks(report_id: str | None = Query(default=None)) -> m.TaskList:
    raise not_implemented("GET /tasks", OWNER)


@router.get("/tasks/{task_id}", response_model=m.Task, tags=["tasks"])
async def get_task(task_id: str) -> m.Task:
    raise not_implemented("GET /tasks/<task_id>", OWNER)
