"""create, correct, revoke: gated create_memory, correct_memory, revoke_memory (AD-28). A21+A22.

The signatures of create, correct and revoke are frozen by A01: change them only through the
contract keeper. The document helpers below are pure functions over plain dicts.
Nothing here reads or writes a grant, a policy or a policy set.
"""

from __future__ import annotations

import secrets
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import DuplicateKeyError

from dxp import gate, identity
from dxp import store as database
from dxp.api.models import Decision, Memory, MemorySource, Principal, ProposedAction, RunContext, Target

COLLECTION = "memories"
DESTINATION = "ledger"

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
# Reads
# ---------------------------------------------------------------------------


async def versions(memory_id: str) -> list[dict[str, Any]]:
    """Every version document of one memory, oldest first."""
    found = await database.collection(COLLECTION).find({"memory_id": memory_id}).to_list()
    return sorted(found, key=lambda document: document["version"])


async def latest_document(memory_id: str) -> dict[str, Any]:
    found = await versions(memory_id)
    if not found:
        raise MemoryNotFound(f"memory {memory_id} was not found")
    return found[-1]


async def get(memory_id: str, version: int | None = None) -> Memory:
    """The latest version, or the one asked for."""
    if version is None:
        return to_model(await latest_document(memory_id))
    document = await database.collection(COLLECTION).find_one({"memory_id": memory_id, "version": version})
    if document is None:
        raise MemoryNotFound(f"memory {memory_id} has no version {version}")
    return to_model(document)


async def list_latest(team_id: str, status: str | None = None) -> list[Memory]:
    """The latest version of each of the Team's memories, newest first; `status` filters on it."""
    found = await database.collection(COLLECTION).find({"team_id": team_id}).to_list()
    latest: dict[str, dict[str, Any]] = {}
    for document in found:
        held = latest.get(document["memory_id"])
        if held is None or document["version"] > held["version"]:
            latest[document["memory_id"]] = document
    kept = [document for document in latest.values() if status is None or document["status"] == status]
    kept.sort(key=lambda document: document["memory_id"])
    kept.sort(key=lambda document: str(document.get("created_at") or ""), reverse=True)
    return [to_model(document) for document in kept]


# ---------------------------------------------------------------------------
# Gated writes (frozen signatures)
# ---------------------------------------------------------------------------


async def create(team_id: str, text: str, tags: dict[str, Any], source: MemorySource, reviewer: Principal, ctx: RunContext) -> tuple[Memory, Decision]:
    """Version 1 of a memory, gated as create_memory under the Reviewer's grant.

    The author is the Reviewer the key resolved to, never a name from a request body.
    Blocked: nothing is written and the result is `(None, decision)`.
    """
    _require_text(team_id, "team_id")
    _require_text(text, "text")
    if ctx.principal.id != reviewer.id:
        raise ValueError("the context's principal is not the Reviewer")
    source = MemorySource.model_validate(source or {})
    tags = {"assay": (tags or {}).get("assay"), "claim_kind": (tags or {}).get("claim_kind")}
    ctx = _with_request_id(ctx)
    # One memory per source decision: a repeat of the same step finds the stored memory.
    memory_id = identity.derive("mem_", team_id, source.decision_id) if source.decision_id else None
    decision = await gate.evaluate(ctx, ProposedAction(
        kind="create_memory",
        destination=DESTINATION,
        target=Target(report_id=source.report_id, memory_id=memory_id),
        inputs={"team_id": team_id, "text": text, "tags": tags, "source": source.model_dump()},
    ))
    if decision.outcome != "allowed":
        return None, decision  # type: ignore[return-value]
    memory_id = memory_id or identity.derive("mem_", team_id, decision.id)
    document = new_memory(memory_id, team_id, reviewer.id, source.model_dump(), text, tags, decision.id, _stamp(ctx), _now())
    try:
        await database.collection(COLLECTION).insert_one(document)
    except DuplicateKeyError:
        document = await latest_document(memory_id)
    else:
        await _emit(document, decision, ctx)
    await _finish_action(decision, document)
    return to_model(document), decision


async def correct(memory_id: str, text: str, note: str, ctx: RunContext) -> tuple[Memory, Decision]:
    """New version with supersedes; the old one corrected, conditional on its status.

    Gated as correct_memory. Blocked: nothing is written and the current version is returned.
    """
    _require_text(text, "text")
    _require_text(note, "note")
    current = await _active(memory_id)
    ctx = _with_request_id(ctx)
    decision = await gate.evaluate(ctx, _change("correct_memory", current, {"text": text, "note": note}))
    if decision.outcome != "allowed":
        return to_model(current), decision
    successor, superseded = corrected_successor(current, text, ctx.principal.id, decision.id, _stamp(ctx), _now())
    memories = database.collection(COLLECTION)
    try:
        # The unique (memory_id, version) index lets only one correction of a version through.
        await memories.insert_one(successor)
    except DuplicateKeyError as exc:
        await _fail_action(decision)
        raise MemoryStateError(f"memory {current['_id']} was changed by another request") from exc
    changed = await memories.update_one({"_id": current["_id"], "status": ACTIVE}, {"$set": {"status": CORRECTED}})
    if changed.matched_count == 0:
        # The old version was revoked meanwhile: the revocation stands for the memory.
        await memories.update_one({"_id": successor["_id"], "status": ACTIVE}, {"$set": {"status": REVOKED}})
        await _fail_action(decision)
        raise MemoryStateError(f"memory {current['_id']} was changed by another request")
    await _emit(superseded, decision, ctx)
    await _emit(successor, decision, ctx)
    await _finish_action(decision, successor)
    return to_model(successor), decision


async def revoke(memory_id: str, note: str, ctx: RunContext) -> tuple[Memory, Decision]:
    """The latest version revoked, conditional on its status. Gated as revoke_memory.

    Blocked: nothing is written and the current version is returned.
    """
    _require_text(note, "note")
    current = await _active(memory_id)
    ctx = _with_request_id(ctx)
    decision = await gate.evaluate(ctx, _change("revoke_memory", current, {"note": note}))
    if decision.outcome != "allowed":
        return to_model(current), decision
    gone = revoked(current)
    changed = await database.collection(COLLECTION).update_one(
        {"_id": current["_id"], "status": ACTIVE}, {"$set": {"status": REVOKED}})
    if changed.matched_count == 0:
        await _fail_action(decision)
        raise MemoryStateError(f"memory {current['_id']} was changed by another request")
    await _emit(gone, decision, ctx)
    await _finish_action(decision, gone)
    return to_model(gone), decision


async def _active(memory_id: str) -> dict[str, Any]:
    current = await latest_document(memory_id)
    if current["status"] != ACTIVE:
        raise MemoryStateError(f"memory {current['_id']} is {current['status']}; only an active memory can be changed")
    return current


def _change(kind: str, current: dict[str, Any], inputs: dict[str, Any]) -> ProposedAction:
    return ProposedAction(
        kind=kind,
        destination=DESTINATION,
        target=Target(memory_id=current["memory_id"]),
        inputs={"memory_version": current["_id"], "version": current["version"], "team_id": current["team_id"], **inputs},
    )


def _with_request_id(ctx: RunContext) -> RunContext:
    """Every Reviewer decision carries a server-generated request ID (D20)."""
    return ctx if ctx.request_id else ctx.model_copy(update={"request_id": secrets.token_hex(8)})


def _stamp(ctx: RunContext) -> dict[str, Any]:
    return ctx.stamp.model_dump()


def _now() -> datetime:
    return datetime.now(UTC)


async def _emit(document: dict[str, Any], decision: Decision, ctx: RunContext) -> None:
    await database.emit_event(
        "memory_changed",
        dedupe_key=f"memory_changed|{document['_id']}|{document['status']}",
        stamp=_stamp(ctx),
        memory_id=document["memory_id"],
        decision_id=decision.id,
        status=document["status"],
        report_id=document["source"].get("report_id"),
    )


async def _finish_action(decision: Decision, document: dict[str, Any]) -> None:
    """The owning module sets its DxP-state action done with its result (AD-19)."""
    if not decision.action_id:
        return
    result = {"proposal_ids": [], "value_ids": [], "report_id": document["source"].get("report_id"),
              "memory_id": document["memory_id"], "task_id": None}
    await database.collection("actions").update_one(
        {"_id": decision.action_id, "status": "queued"},
        {"$set": {"status": "done", "result": result, "observed_at": _now()}})


async def _fail_action(decision: Decision) -> None:
    if not decision.action_id:
        return
    await database.collection("actions").update_one(
        {"_id": decision.action_id, "status": "queued"}, {"$set": {"status": "failed", "observed_at": _now()}})
