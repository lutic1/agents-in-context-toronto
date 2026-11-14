"""Reviewer memory (Stories 10.5, 10.6). A21+A22.

Paths, methods, parameters and response models are frozen by A01 (AD-14): only the bodies
change. Every route is for a Reviewer and stays inside the Team of the Reviewer's grant.
Correct and revoke are gated in `memory.store`; a blocked change answers 200 with its
Decision and the unchanged memory (D5). No route here writes a grant or a policy.
"""

from __future__ import annotations

import secrets
from typing import get_args

from fastapi import APIRouter, Query, Request

from dxp import store as database
from dxp.api import auth
from dxp.api import models as m
from dxp.api.errors import ApiError
from dxp.gate import policy_sets
from dxp.memory import store as memories

router = APIRouter()
OWNER = "A21+A22"
KEY_HEADER = "X-DxP-Key"


async def _reviewer(request: Request) -> tuple[m.Principal, m.Grant]:
    """The Reviewer the key resolves to, with the current version of their grant.

    The principal comes from the key only (AD-18): no name in a body or a query is read.
    """
    key = request.headers.get(KEY_HEADER)
    if not key:
        raise ApiError(401, "unauthorised", "X-DxP-Key is required.")
    reviewer = await auth.resolve_actor(key)
    if reviewer.kind != "person":
        raise ApiError(403, "forbidden", "Memories are for Reviewers only.")
    grant = await policy_sets.current_grant(reviewer.id)
    if grant is None or not grant.team_id:
        raise ApiError(403, "forbidden", "The Reviewer has no grant for a Team.")
    return reviewer, grant


async def _own(memory_id: str, grant: m.Grant, version: int | None = None) -> m.Memory:
    """The memory, if it belongs to the Reviewer's Team; another Team's memory is not found."""
    try:
        memory = await memories.get(memory_id, version)
    except memories.MemoryNotFound as exc:
        raise ApiError(404, "not_found", "Memory not found.") from exc
    if memory.team_id != grant.team_id:
        raise ApiError(404, "not_found", "Memory not found.")
    return memory


async def _context(reviewer: m.Principal, grant: m.Grant, memory: m.Memory) -> m.RunContext:
    """A Reviewer decision's context: no run, a Reviewer stamp, a new request ID, and the
    memory with the run of its source report as the cause (AD-17, D19, D20)."""
    origin_run_id = None
    if memory.source.report_id:
        report = await database.collection("reports").find_one({"_id": memory.source.report_id}, {"run_id": 1})
        origin_run_id = (report or {}).get("run_id")
    stamp = m.Stamp(kind="reviewer", run_id=None, agent=None, initiated_by=reviewer.id, principal=reviewer.id,
                    acting_for=grant.acting_for, grant_id=grant.grant_id, grant_version=grant.version)
    return m.RunContext(
        run_id=None,
        principal=reviewer,
        stamp=stamp,
        grant_id=grant.grant_id,
        grant_version=grant.version,
        request_id=secrets.token_hex(8),
        cause=m.DecisionCause(memory_id=memory.id, origin_run_id=origin_run_id),
    )


def _required(value: str, name: str) -> str:
    if not value or not value.strip():
        raise ApiError(422, "invalid_request", f"{name}: required.")
    return value.strip()


@router.get("/memories", response_model=m.MemoryList, tags=["memories"])
async def list_memories(request: Request, team_id: str | None = Query(default=None), status: str | None = Query(default=None)) -> m.MemoryList:
    """The latest version of each of the Team's memories, with author, source and status."""
    _, grant = await _reviewer(request)
    if team_id is not None and team_id != grant.team_id:
        raise ApiError(403, "forbidden", "Another Team's memories cannot be read.")
    if status is not None and status not in get_args(m.MemoryStatus):
        raise ApiError(422, "invalid_request", "status: one of active, corrected, revoked.")
    return m.MemoryList(items=await memories.list_latest(grant.team_id, status), next=None)


@router.get("/memories/{memory_id}", response_model=m.Memory, tags=["memories"])
async def get_memory(request: Request, memory_id: str, version: int | None = Query(default=None)) -> m.Memory:
    _, grant = await _reviewer(request)
    return await _own(memory_id, grant, version)


@router.post("/memories/{memory_id}/correct", response_model=m.MemoryChangeResponse, tags=["memories"])
async def correct_memory(request: Request, memory_id: str, body: m.MemoryCorrectRequest) -> m.MemoryChangeResponse:
    text, note = _required(body.text, "text"), _required(body.note, "note")
    reviewer, grant = await _reviewer(request)
    memory = await _own(memory_id, grant)
    ctx = await _context(reviewer, grant, memory)
    try:
        changed, decision = await memories.correct(memory_id, text, note, ctx)
    except memories.MemoryStateError as exc:
        raise ApiError(409, "conflict", str(exc)) from exc
    return m.MemoryChangeResponse(memory=changed, decision=decision)


@router.post("/memories/{memory_id}/revoke", response_model=m.MemoryChangeResponse, tags=["memories"])
async def revoke_memory(request: Request, memory_id: str, body: m.MemoryRevokeRequest) -> m.MemoryChangeResponse:
    note = _required(body.note, "note")
    reviewer, grant = await _reviewer(request)
    memory = await _own(memory_id, grant)
    ctx = await _context(reviewer, grant, memory)
    try:
        changed, decision = await memories.revoke(memory_id, note, ctx)
    except memories.MemoryStateError as exc:
        raise ApiError(409, "conflict", str(exc)) from exc
    return m.MemoryChangeResponse(memory=changed, decision=decision)
