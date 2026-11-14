"""Fixtures for A07+A11 (runs, stop, sweep and the audit API).

- `authority`: replaces A03's `resolve_actor`, `current_grant` and `current_set` (not on main
  yet) with an in-memory map of keys and grants, so the frozen signatures are what is tested.
- `clean`: empties the collections these tests write, inside the session's test database
  (`dxp_test_<hex>`, never `dxp`), so the one-run rule starts from nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio

from dxp.api.errors import ApiError
from dxp.api.models import Grant, PolicySet, Principal
from dxp.identity import derive

SAM = Principal(id="sam", name="Sam", kind="person", actions=["decide_report"])
VLAD = Principal(id="vlad", name="Vlad", kind="person", actions=[])
AGENT = Principal(id="dxp-curator", name="dxp-curator", kind="agent", actions=["search_source"])
SEED = Principal(id="seed", name="seed", kind="seed", actions=["apply_value"])

KEYS = {"key-sam": SAM, "key-vlad": VLAD, "key-agent": AGENT, "key-seed": SEED}

PS_VERSION = derive("ps_", "claim_planned@v1", "evidence_quote@v1")
SCOPE_ID = "scope_plasma_ctdna_nsclc"
TEAM_ID = "team_lbdx"
TASK_ID = derive("task_", derive("rep_", "run_fixture", "clinicaltrials.gov:NCT04712877"))
TASK_GRANT_ID = "task-" + TASK_ID.removeprefix("task_")


def agent_grant(version: int = 1, status: str = "active", startable_by: list[str] | None = None,
                expires_in: timedelta = timedelta(hours=8)) -> Grant:
    return Grant(
        id=f"lbdx@v{version}", grant_id="lbdx", version=version, principal="dxp-curator", kind="agent",
        acting_for="Team Liquid Biopsy Dx", granted_by="luis", startable_by=startable_by or ["sam"],
        team_id=TEAM_ID, scope={"diagnostic_ids": [], "scope_id": SCOPE_ID},
        destinations=["source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"],
        actions=["search_source", "file_proposal", "notify_slack"],
        expires_at=datetime.now(UTC) + expires_in, status=status,
    )


def task_grant(task_id: str = TASK_ID) -> Grant:
    return Grant(
        id=f"task-{task_id.removeprefix('task_')}@v1", grant_id=f"task-{task_id.removeprefix('task_')}", version=1,
        principal="dxp-curator", kind="agent", acting_for="Team Liquid Biopsy Dx", granted_by="sam",
        startable_by=["sam"], team_id=TEAM_ID, scope={"diagnostic_ids": [], "scope_id": SCOPE_ID},
        destinations=["source:clinicaltrials.gov", "ledger"], actions=["search_source", "file_related_evidence"],
        limits={"max_results": 5}, task_id=task_id, expires_at=datetime.now(UTC) + timedelta(hours=1),
        status="active",
    )


@dataclass
class Authority:
    grants: dict[str, Grant] = field(default_factory=dict)
    keys: dict[str, Principal] = field(default_factory=lambda: dict(KEYS))
    policy_set: PolicySet = field(default_factory=lambda: PolicySet(id=PS_VERSION, members=["claim_planned@v1", "evidence_quote@v1"]))

    async def resolve_actor(self, api_key: str) -> Principal:
        principal = self.keys.get(api_key)
        if principal is None:
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return principal

    async def current_grant(self, grant_id: str) -> Grant | None:
        return self.grants.get(grant_id)

    async def current_set(self) -> PolicySet:
        return self.policy_set


@pytest.fixture
def authority(monkeypatch: pytest.MonkeyPatch) -> Authority:
    import dxp.api.auth
    import dxp.gate.policy_sets

    fake = Authority(grants={"lbdx": agent_grant(), TASK_GRANT_ID: task_grant()})
    monkeypatch.setattr(dxp.api.auth, "resolve_actor", fake.resolve_actor)
    monkeypatch.setattr(dxp.gate.policy_sets, "current_grant", fake.current_grant)
    monkeypatch.setattr(dxp.gate.policy_sets, "current_set", fake.current_set)
    return fake


TOUCHED = ("runs", "admissions", "decisions", "actions", "events", "reports", "proposals", "tasks",
           "policy_sets", "policies", "grants", "source_items")


@pytest_asyncio.fixture
async def clean(db: Any) -> Any:
    for name in TOUCHED:
        await db[name].delete_many({})
    return db
