"""Reviewer memory (Stories 10.5, 10.6). Stub from A01 (contract); finished by A21+A22.

Paths, methods, parameters and response models are frozen (AD-14): only the bodies change.
Every route here returns 501 in the error shape until A21+A22 finishes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Query  # noqa: F401

from dxp.api import models as m
from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A21+A22"


@router.get("/memories", response_model=m.MemoryList, tags=["memories"])
async def list_memories(team_id: str | None = Query(default=None), status: str | None = Query(default=None)) -> m.MemoryList:
    raise not_implemented("GET /memories", OWNER)


@router.get("/memories/{memory_id}", response_model=m.Memory, tags=["memories"])
async def get_memory(memory_id: str, version: int | None = Query(default=None)) -> m.Memory:
    raise not_implemented("GET /memories/<memory_id>", OWNER)


@router.post("/memories/{memory_id}/correct", response_model=m.MemoryChangeResponse, tags=["memories"])
async def correct_memory(memory_id: str, body: m.MemoryCorrectRequest) -> m.MemoryChangeResponse:
    raise not_implemented("POST /memories/<memory_id>/correct", OWNER)


@router.post("/memories/{memory_id}/revoke", response_model=m.MemoryChangeResponse, tags=["memories"])
async def revoke_memory(memory_id: str, body: m.MemoryRevokeRequest) -> m.MemoryChangeResponse:
    raise not_implemented("POST /memories/<memory_id>/revoke", OWNER)
