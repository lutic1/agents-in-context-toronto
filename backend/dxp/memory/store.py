"""create, correct, revoke: gated create_memory, correct_memory, revoke_memory (AD-28). A21+A22.

The signatures of create, correct and revoke are frozen by A01: change them only through the
contract keeper. The document helpers below are pure functions over plain dicts.
Nothing here reads or writes a grant, a policy or a policy set.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from dxp.api.models import Decision, Memory, MemorySource, Principal, RunContext

ACTIVE = "active"
CORRECTED = "corrected"
REVOKED = "revoked"
STATUSES = (ACTIVE, CORRECTED, REVOKED)

# A corrected or revoked version is final.
ALLOWED_TRANSITIONS = {
    ACTIVE: frozenset({CORRECTED, REVOKED}),
    CORRECTED: frozenset(),
    REVOKED: frozenset(),
}

API_FIELDS = ("version", "team_id", "author", "source", "text", "tags", "status", "supersedes", "decision_id", "created_at")


class MemoryNotFound(LookupError):
    """No such memory, or no such version of it."""


class MemoryStateError(ValueError):
    """The memory version is not in a status that allows the change."""


# ---------------------------------------------------------------------------
# Documents (pure)
# ---------------------------------------------------------------------------


def version_key(memory_id: str, version: int) -> str:
    """The `_id` of one memory version: `<memory_id>@v<version>`."""
    _require_text(memory_id, "memory_id")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("version must be a whole number from 1")
    return f"{memory_id}@v{version}"


def can_transition(current_status: Any, new_status: Any) -> bool:
    return new_status in ALLOWED_TRANSITIONS.get(current_status, frozenset())


def new_memory(memory_id: str, team_id: str, author: str, source: dict[str, Any], text: str, tags: dict[str, Any] | None,
               decision_id: str, stamp: dict[str, Any] | None, created_at: Any) -> dict[str, Any]:
    """Version 1 of a memory, `active`."""
    return _version_document(memory_id, 1, team_id, author, source, text, tags, None, decision_id, stamp, created_at)


def corrected_successor(current: dict[str, Any], text: str, author: str, decision_id: str, stamp: dict[str, Any] | None,
                        created_at: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Correct an active version.

    Returns `(successor, superseded)`: the new `active` version n+1 that `supersedes` the
    current one, and a copy of the current version marked `corrected`. The current version's
    text is never changed.
    """
    superseded = with_status(current, CORRECTED)
    successor = _version_document(current["memory_id"], current["version"] + 1, current["team_id"], author,
                                  current["source"], text, current["tags"], current["_id"], decision_id, stamp, created_at)
    return successor, superseded


def revoked(current: dict[str, Any]) -> dict[str, Any]:
    """A copy of an active version marked `revoked`."""
    return with_status(current, REVOKED)


def with_status(current: dict[str, Any], new_status: str) -> dict[str, Any]:
    """A copy of `current` in `new_status`, if the transition is allowed."""
    status = current.get("status")
    if not can_transition(status, new_status):
        raise MemoryStateError(f"memory {current.get('_id')} is {status}; it cannot become {new_status}")
    changed = deepcopy(current)
    changed["status"] = new_status
    return changed


def to_api(document: dict[str, Any]) -> dict[str, Any]:
    """The `Memory` response shape (AD-14): no `_id`, stamp or embedding."""
    memory = {"id": document["memory_id"]}
    for field in API_FIELDS:
        memory[field] = deepcopy(document.get(field))
    return memory


def to_model(document: dict[str, Any]) -> Memory:
    return Memory.model_validate(to_api(document))


def _version_document(memory_id: str, version: int, team_id: str, author: str, source: dict[str, Any], text: str,
                      tags: dict[str, Any] | None, supersedes: str | None, decision_id: str,
                      stamp: dict[str, Any] | None, created_at: Any) -> dict[str, Any]:
    _require_text(team_id, "team_id")
    _require_text(author, "author")
    _require_text(text, "text")
    _require_text(decision_id, "decision_id")
    source = source or {}
    tags = tags or {}
    return {
        "_id": version_key(memory_id, version),
        "memory_id": memory_id,
        "version": version,
        "team_id": team_id,
        "author": author,
        "source": {"decision_id": source.get("decision_id"), "report_id": source.get("report_id")},
        "text": text,
        "tags": {"assay": tags.get("assay"), "claim_kind": tags.get("claim_kind")},
        "status": ACTIVE,
        "supersedes": supersedes,
        "decision_id": decision_id,
        "stamp": deepcopy(stamp),
        "created_at": created_at,
    }


def _require_text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


# ---------------------------------------------------------------------------
# Gated writes (frozen signatures)
# ---------------------------------------------------------------------------


async def create(team_id: str, text: str, tags: dict[str, Any], source: MemorySource, reviewer: Principal, ctx: RunContext) -> tuple[Memory, Decision]:
    raise NotImplementedError("memory.create (A21+A22)")


async def correct(memory_id: str, text: str, note: str, ctx: RunContext) -> tuple[Memory, Decision]:
    """New version with supersedes; the old one corrected, conditional on its status."""
    raise NotImplementedError("memory.correct (A21+A22)")


async def revoke(memory_id: str, note: str, ctx: RunContext) -> tuple[Memory, Decision]:
    raise NotImplementedError("memory.revoke (A21+A22)")
