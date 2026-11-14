"""Memory retrieval (AD-28, V22). A21+A22.

The signature of retrieve is frozen by A01: change it only through the contract keeper.
The similarity search belongs to `retrieval.memories` (A19+A20). A score only orders memories
and is shown beside them: it never enters a check, a label or a claim, and no memory is read
into a grant, a policy or the gate.
"""

from __future__ import annotations

from typing import Any

from dxp.api.models import Memory, Retrieval

ACTIVE = "active"
DEFAULT_TOP_K = 3


# ---------------------------------------------------------------------------
# Filtering and ranking (pure, over memory version documents)
# ---------------------------------------------------------------------------


def search_tags(tags: dict[str, Any] | None) -> dict[str, Any] | None:
    """The tags a memory search may filter on: `claim_kind` only, or None when none is given.

    The assay tag is recorded and shown, never required to match (V22).
    """
    claim_kind = (tags or {}).get("claim_kind")
    return {"claim_kind": claim_kind} if _is_text(claim_kind) else None


def memory_id_of(ref: Any) -> str | None:
    """The memory ID in a retrieval ref: `mem_x` or `mem_x@v2` both give `mem_x`."""
    if not _is_text(ref):
        return None
    return ref.split("@v", 1)[0]


def latest_versions(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The highest version of each memory, in first-seen order."""
    latest: dict[str, dict[str, Any]] = {}
    for memory in memories:
        held = latest.get(memory["memory_id"])
        if held is None or memory["version"] > held["version"]:
            latest[memory["memory_id"]] = memory
    return list(latest.values())


def is_eligible(memory: dict[str, Any], team_id: str, tags: dict[str, Any] | None) -> bool:
    """True for an `active` version of this Team; with a claim kind asked for, the same one."""
    if not _is_text(team_id):
        return False
    if memory.get("team_id") != team_id or memory.get("status") != ACTIVE:
        return False
    wanted = search_tags(tags)
    return wanted is None or (memory.get("tags") or {}).get("claim_kind") == wanted["claim_kind"]


def eligible(memories: list[dict[str, Any]], team_id: str, tags: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The latest version of each memory, where that version is eligible."""
    return [memory for memory in latest_versions(memories) if is_eligible(memory, team_id, tags)]


def rank(memories: list[dict[str, Any]], items: list[dict[str, Any]], team_id: str, tags: dict[str, Any] | None,
         k: int = DEFAULT_TOP_K) -> list[tuple[dict[str, Any], float]]:
    """The memories to use, best first, each with its score.

    `memories` are memory version documents; `items` are the `Retrieval.items` returned by
    `retrieval.memories`. A memory is kept only if its latest version is eligible and the
    search returned it. Order: score, highest first; then `memory_id`; then the search's own
    order. At most `k` are returned.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        return []
    scored = _scores(items or [])
    found = []
    for memory in eligible(memories, team_id, tags):
        hit = scored.get(memory["_id"]) or scored.get(memory["memory_id"])
        if hit is not None:
            position, score = hit
            found.append((-score, memory["memory_id"], position, memory, score))
    found.sort(key=lambda entry: entry[:3])
    return [(memory, score) for *_, memory, score in found[:k]]


def _scores(items: list[dict[str, Any]]) -> dict[str, tuple[int, float]]:
    """`ref -> (position, score)`, keeping the first entry for each ref.

    A ref is a version (`mem_x@v2`) or a memory (`mem_x`); a version ref only ever scores
    that version, so a stale hit on an earlier version is not used.
    """
    scored: dict[str, tuple[int, float]] = {}
    for position, item in enumerate(items):
        ref = item.get("ref")
        score = item.get("score")
        if not _is_text(ref) or ref in scored or not _is_number(score):
            continue
        scored[ref] = (position, score)
    return scored


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value == value and value not in (float("inf"), float("-inf"))


# ---------------------------------------------------------------------------
# Retrieval (frozen signature)
# ---------------------------------------------------------------------------


async def retrieve(team_id: str, text: str, tags: dict[str, Any] | None) -> tuple[list[Memory], Retrieval]:
    """Only active versions of the Team, ranked by retrieval.memories."""
    raise NotImplementedError("memory.retrieve (A21+A22)")
