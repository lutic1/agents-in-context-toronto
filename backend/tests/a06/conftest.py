"""A06 fixture: one seeded world per test, on the in-memory fake and (with MONGODB_URI) Atlas."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from .world import World, open_world


@pytest_asyncio.fixture(params=["fake", pytest.param("atlas", marks=pytest.mark.atlas)])
async def world(request: pytest.FixtureRequest) -> AsyncIterator[World]:
    w, close = await open_world(request.param)
    try:
        yield w
    finally:
        await close()
