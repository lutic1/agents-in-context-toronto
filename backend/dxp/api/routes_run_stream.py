"""A run's events as server-sent events (Story 9.12, live_stream flag, AD-23, V48).
Stub from A01 (contract); finished by A27, with the read logic in search/stream.py.

The path is frozen (AD-14). Returns 501 in the error shape until A27 finishes it
(then 404 when `live_stream` is off). Each message's data is one `Event`.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from dxp.api.errors import not_implemented

router = APIRouter()
OWNER = "A27"


@router.get(
    "/runs/{run_id}/stream",
    tags=["runs"],
    response_class=StreamingResponse,
    responses={200: {"description": "text/event-stream of Event", "content": {"text/event-stream": {}}}},
)
async def stream_run(run_id: str):
    raise not_implemented("GET /runs/<run_id>/stream", OWNER)
