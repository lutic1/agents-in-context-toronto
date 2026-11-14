"""A14 fixtures: an in-memory stand-in for the async MongoDB API, the caller, and seed documents.

`fake_db` replaces `store.get_db()` (and the event writer's) with `FakeDB`, a small async
collection fake that supports what the read model and the review path use: find_one, find
(sort, to_list, async iteration), insert_one and update_one with $set, $inc, $push, and the
filter operators $in, $ne, $exists, $or and $elemMatch. Atlas-backed tests use the real session
database (`db` from tests/conftest.py) and skip without MONGODB_URI.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pymongo.errors import DuplicateKeyError

from dxp.api import models as m

_MISSING = object()


def _get(doc: Any, path: str) -> Any:
    current = doc
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def _equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, list) and not isinstance(expected, list):
        return expected in actual
    return actual == expected


def _matches_value(actual: Any, condition: Any) -> bool:
    if isinstance(condition, dict) and condition and all(k.startswith("$") for k in condition):
        for op, arg in condition.items():
            if op == "$in":
                if not any(_equal(actual, a) for a in arg):
                    return False
            elif op == "$ne":
                if actual is not _MISSING and _equal(actual, arg):
                    return False
            elif op == "$exists":
                if (actual is not _MISSING) != bool(arg):
                    return False
            elif op == "$elemMatch":
                if not isinstance(actual, list) or not any(matches(e, arg) for e in actual):
                    return False
            else:
                raise NotImplementedError(op)
        return True
    if actual is _MISSING:
        return condition is None
    return _equal(actual, condition)


def matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, condition in query.items():
        if key == "$or":
            if not any(matches(doc, q) for q in condition):
                return False
        elif not _matches_value(_get(doc, key), condition):
            return False
    return True


def _set_path(doc: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    for part in parts[:-1]:
        doc = doc.setdefault(part, {})
    doc[parts[-1]] = value


@dataclass
class UpdateResult:
    matched_count: int
    modified_count: int


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs

    def sort(self, key: Any, direction: int = 1) -> FakeCursor:
        keys = key if isinstance(key, list) else [(key, direction)]
        for name, order in reversed(keys):
            self.docs.sort(key=lambda d: (_get(d, name) is _MISSING, _get(d, name)), reverse=order < 0)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return self.docs[:length] if length else list(self.docs)

    def __aiter__(self):
        self._iter = iter(self.docs)
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


class FakeCollection:
    def __init__(self) -> None:
        self.docs: dict[Any, dict[str, Any]] = {}

    def _find(self, query: dict[str, Any] | None) -> list[dict[str, Any]]:
        return [copy.deepcopy(d) for d in self.docs.values() if matches(d, query or {})]

    async def find_one(self, query=None, projection=None, sort=None, session=None):
        found = FakeCursor(self._find(query))
        if sort:
            found.sort(sort)
        return found.docs[0] if found.docs else None

    def find(self, query=None, projection=None, session=None) -> FakeCursor:
        return FakeCursor(self._find(query))

    async def insert_one(self, doc, session=None):
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("duplicate _id")
        self.docs[doc["_id"]] = copy.deepcopy(doc)

    async def update_one(self, query, update, upsert=False, session=None) -> UpdateResult:
        for doc in self.docs.values():
            if matches(doc, query):
                before = copy.deepcopy(doc)
                for path, value in (update.get("$set") or {}).items():
                    _set_path(doc, path, copy.deepcopy(value))
                for path, value in (update.get("$inc") or {}).items():
                    current = _get(doc, path)
                    _set_path(doc, path, (0 if current is _MISSING else current) + value)
                for path, value in (update.get("$push") or {}).items():
                    current = _get(doc, path)
                    _set_path(doc, path, ([] if current is _MISSING else current) + [value])
                return UpdateResult(1, int(before != doc))
        return UpdateResult(0, 0)


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDB:
    import dxp.store
    import dxp.store.events

    database = FakeDB()
    monkeypatch.setattr(dxp.store, "get_db", lambda: database)
    monkeypatch.setattr(dxp.store, "db", lambda: database)  # A06's gate reads dxp.store.db
    monkeypatch.setattr(dxp.store.events, "get_db", lambda: database)

    import dxp.ledger.review

    async def no_transaction(body):
        return await body(None)  # the fake has no sessions; Atlas tests run the real transaction

    monkeypatch.setattr(dxp.ledger.review, "in_transaction", no_transaction)
    return database


# ---------------------------------------------------------------------------
# The caller: Sam's key resolves to the Reviewer (A03's resolve_actor and current_grant faked)
# ---------------------------------------------------------------------------

SAM_KEY = "test-dxp-api-key"
SEED_KEY = "test-dxp-seed-key"
HEADERS = {"X-DxP-Key": SAM_KEY}


def grant_doc(grant_id: str, principal: str, kind: str, key: str, actions: list[str]) -> dict[str, Any]:
    import hashlib

    return {
        "_id": f"{grant_id}@v1",
        "grant_id": grant_id,
        "version": 1,
        "principal": principal,
        "kind": kind,
        "key_hash": hashlib.sha256(key.encode()).hexdigest(),
        "acting_for": "Team Liquid Biopsy Dx",
        "scope": {"all": True} if kind == "seed" else {"diagnostic_ids": [DX_ID], "scope_id": SCOPE_ID},
        "destinations": ["ledger"],
        "actions": actions,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "status": "active",
    }


@pytest.fixture
def principals(monkeypatch: pytest.MonkeyPatch) -> dict[str, m.Principal]:
    """Fake A03 (resolve_actor, grant_for_key): SAM_KEY resolves to sam, SEED_KEY to seed, anything else is a 401."""
    import dxp.api.auth
    from dxp.api.errors import ApiError

    people = {
        SAM_KEY: m.Principal(id="sam", name="Sam", kind="person", actions=["review_value"]),
        SEED_KEY: m.Principal(id="seed", name="seed", kind="seed", actions=["apply_value"]),
    }
    grants = {
        "sam": grant_doc("sam", "sam", "person", SAM_KEY, ["review_value"]),
        "seed": grant_doc("seed", "seed", "seed", SEED_KEY, ["apply_value"]),
    }

    async def resolve_actor(api_key: str) -> m.Principal:
        if api_key not in people:
            raise ApiError(401, "unknown_key", "Unknown API key.")
        return people[api_key]

    async def grant_for_key(api_key: str | None, db=None) -> dict[str, Any] | None:
        person = people.get(api_key or "")
        return grants[person.id] if person else None

    monkeypatch.setattr(dxp.api.auth, "resolve_actor", resolve_actor)
    # A03's grant_for_key is on main once PR #17 merges; until then it is added here.
    monkeypatch.setattr(dxp.api.auth, "grant_for_key", grant_for_key, raising=False)
    return people


@pytest.fixture
def recoveries(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Records each call of ledger.recover_applying (A06's; a no-op here)."""
    import dxp.ledger.review

    calls: list[str] = []

    async def recover_applying() -> None:
        calls.append("recover_applying")

    monkeypatch.setattr(dxp.ledger.review, "recover_applying", recover_applying)
    return calls


# ---------------------------------------------------------------------------
# Seed documents
# ---------------------------------------------------------------------------

DX_ID = "dx_f1liquidcdx0001"
SCOPE_ID = "scope_plasma_ctdna_nsclc"
SEED_STAMP = {"kind": "seed", "principal": "seed", "run_id": None}
RUN_STAMP = {"kind": "run", "run_id": "run_a14", "agent": "dxp-curator", "initiated_by": "sam", "principal": "dxp-curator"}
PASSED = {"quote_found": True, "supported": True, "confidence": 0.95, "flags": []}
FAILED = {"quote_found": False, "supported": False, "confidence": 0.4, "flags": []}


def fda_evidence(quote: str = "FoundationOne Liquid CDx ... companion diagnostic") -> dict[str, Any]:
    return {
        "source_ref": "fda_cdx_list:P190032:1a2b3c4d",
        "version_id": "sv_fda0000000000001",
        "source": "FDA list of cleared or approved companion diagnostic devices",
        "source_url": "https://www.fda.gov/cdx",
        "source_date": "2026-11-14",
        "quote": quote,
        "raw_text": "THE WHOLE FDA ROW, NEVER RETURNED",
    }


def entry(
    value_id: str,
    value: str,
    *,
    state: str = "current",
    review: str = "unreviewed",
    check: dict[str, Any] | None = None,
    proposal_id: str | None = None,
    evidence: dict[str, Any] | None = None,
    stamp: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "value_id": value_id,
        "value": value,
        "label": value,
        "detail": None,
        "state": state,
        "review": review,
        "evidence": evidence or fda_evidence(),
        "check": PASSED if check is None else check,
        "proposal_id": proposal_id,
        "action_id": None,
        "stamp": stamp or SEED_STAMP,
        "decided_by": None,
        "decided_at": None,
        "reason": None,
    }


def diagnostic_doc() -> dict[str, Any]:
    """FoundationOne Liquid CDx as the seed leaves it, plus one accepted trial and one failed value."""
    return {
        "_id": DX_ID,
        "name": "FoundationOne Liquid CDx",
        "lifecycle_stage": "regulatory_approval",
        "created_mode": "baseline",
        "rev": 5,
        "synthetic": False,
        "applied_proposal_ids": ["p_modality", "p_stage", "p_status", "p_samples", "p_trial", "p_failed"],
        "fields": {
            "modality": [entry("v_modality", "ngs", proposal_id="p_modality")],
            "lifecycle_stage": [entry("v_stage", "regulatory_approval", proposal_id="p_stage")],
            "regulatory_status": [entry("v_status", "fda_approved", proposal_id="p_status")],
            "sample_types": [entry("v_plasma", "plasma", proposal_id="p_samples")],
            "trials": [
                entry(
                    "v_trial",
                    "NCT05715229",
                    review="accepted",
                    proposal_id="p_trial",
                    stamp=RUN_STAMP,
                    evidence={
                        "source_ref": "clinicaltrials.gov:NCT05715229",
                        "version_id": "sv_trial_v1",
                        "quote": "plasma ctDNA genotyping",
                        "raw_text": "THE WHOLE TRIAL RECORD, NEVER RETURNED",
                    },
                ),
                entry("v_failed", "NCT00000001", check=FAILED, proposal_id="p_failed"),
                # Defensive: an entry the Diagnostic has not applied is never accepted knowledge.
                entry("v_unapplied", "NCT00000002", proposal_id="p_unapplied"),
                entry("v_pending_state", "NCT00000003", state="pending", proposal_id="p_trial"),
            ],
        },
        "search_text": "FoundationOne Liquid CDx",
        "facets": {},
    }


def proposal_doc(
    p_id: str,
    *,
    status: str = "pending",
    diagnostic_id: str | None = DX_ID,
    field: str = "trials",
    value: str = "NCT04712877",
    report_id: str | None = "rep_a14",
    confidence: float = 0.9,
    created_at: datetime | None = None,
    scope_id: str | None = None,
) -> dict[str, Any]:
    return {
        "_id": p_id,
        "finding_id": "f_a14",
        "diagnostic_id": diagnostic_id,
        "diagnostic_name": None,
        "target": {"scope_id": scope_id} if scope_id else None,
        "field": field,
        "value": value,
        "label": value,
        "detail": None,
        "current_value": None,
        "evidence": {
            "source_ref": f"clinicaltrials.gov:{value}" if value.startswith("NCT") else value,
            "version_id": "sv_anchor_v1",
            "source_date": "2026-11-12",
            "quote": "molecular profiling using blood (ctDNA) and tumour tissue",
            "raw_text": "THE WHOLE TRIAL RECORD, NEVER RETURNED",
        },
        "check": {"quote_found": True, "supported": True, "confidence": confidence, "flags": []},
        "mention": None,
        "op": "add",
        "reverts_proposal_id": None,
        "status": status,
        "mode": "live",
        "trigger": "discovery",
        "run_id": "run_a14",
        "report_id": report_id,
        "action_id": f"act_{p_id}",
        "decision_id": f"dec_{p_id}",
        "stamp": RUN_STAMP,
        "decided_by": None,
        "decided_at": None,
        "reason": None,
        "created_at": created_at or datetime(2026, 11, 14, 13, 0, tzinfo=UTC),
    }
