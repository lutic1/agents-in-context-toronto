"""ledger.review_value: gated review of an unreviewed value (A14; Story 2.3, AD-4, D16).

A Reviewer accepts, edits or rejects one `unreviewed` value entry on a Diagnostic (on Saturday
only seed values are unreviewed). In order:

1. Refused before the gate (`ReviewRefused`): `edit` or `reject` without a reason (400), an
   `edit` value with no canonical form in the field (400), an unknown Diagnostic or value (404),
   a value that is not unreviewed and was not reviewed here (409).
2. Apply recovery runs first, as on every decision call (D26).
3. In one transaction: `gate.evaluate_in(ctx, action, session)` as kind `review_value`,
   destination `ledger`, target the Diagnostic and the `value_id`, under the caller's grant
   (`sam@v1`); check 4 and check 5 record `n/a`. A blocked review writes nothing but its
   Decision (D5).
4. Allowed, in the same transaction: one guarded update of the Diagnostic on its `rev`, so two
   reviews never both apply:
   - accept: `review: accepted`;
   - edit: the entry becomes `superseded` with the reason, and a new `current` entry with the
     canonical value, `review: edited`, the same Evidence (its pinned `version_id`, V40) and the
     Reviewer's stamp is added;
   - reject: `state: rejected` with the reason.
   Every decided entry keeps its Evidence and gains `decided_by`, `decided_at`, `reason` and the
   `review_decision_id`; nothing is deleted. `lifecycle_stage`, `rev`, `search_text` and `facets`
   follow the change. The Decision's action is then set `done` (or `failed` if another review
   won the race) through `gate.mark_action`, which emits the event with the Reviewer's stamp;
   the ledger never writes `actions` itself (V65).
5. A second review of a value already reviewed here does nothing and returns its stored Decision.

The ledger is the only writer of Records (AD-1): this module is the ledger's review path. It
does not call `ledger.apply_with`: an unreviewed value is already applied (its proposal is
`applied`), so a review changes the entry in place and files no new proposal.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from dxp import gate, store
from dxp.api.models import Decision, DecisionCause, ProposedAction, RunContext, Target
from dxp.identity import derive
from dxp.ledger.apply import recover_applying
from dxp.schema import registry

ACTIONS = ("accept", "edit", "reject")
KIND = "review_value"
DESTINATION = "ledger"

# Fields indexed as facets on the Diagnostic (AD-15), recomputed after a review.
FACET_FIELDS = (
    "modality",
    "regulatory_status",
    "lifecycle_stage",
    "provider",
    "clinical_uses",
    "sample_types",
    "tumour_stage_or_line",
    "biomarkers",
    "tumour_types",
    "linked_drugs",
)


class ReviewRefused(Exception):
    """A review refused before (or instead of) the gate; the route answers with the error shape."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass
class ReviewOutcome:
    decision: Decision
    changed: bool  # False when blocked, or when the value had already been reviewed


def new_request_id() -> str:
    """Server-generated, so a blocked Reviewer decision can be retried and gets a new Decision (D20)."""
    return f"req_{uuid.uuid4().hex}"


def _now() -> datetime:
    return datetime.now(UTC)


def as_decision(value: Any) -> Decision:
    """The gate returns the AD-14 Decision; a stored `decisions` document maps `_id` to `id`."""
    if isinstance(value, Decision):
        return value
    data = dict(value)
    if "id" not in data and "_id" in data:
        data["id"] = data.pop("_id")
    return Decision.model_validate(data)


def find_entry(doc: dict[str, Any], value_id: str) -> tuple[str, int, dict[str, Any]] | None:
    for field, entries in (doc.get("fields") or {}).items():
        for index, entry in enumerate(entries or []):
            if entry.get("value_id") == value_id:
                return field, index, entry
    return None


def validate_request(action: str, value: str | None, reason: str | None) -> str | None:
    """Input rules checked before anything is read (D16). Returns the cleaned reason."""
    if action not in ACTIONS:
        raise ReviewRefused(400, "invalid_action", "action must be accept, edit or reject.")
    reason = (reason or "").strip() or None
    if action in ("edit", "reject") and reason is None:
        raise ReviewRefused(400, "reason_required", f"A reason is required to {action} a value.")
    if action == "edit" and not (value or "").strip():
        raise ReviewRefused(400, "value_required", "An edit needs the new value.")
    return reason


def canonical_edit(field: str, value: str) -> str:
    try:
        return registry.canonical(field, value)
    except (registry.CanonicalError, KeyError) as exc:
        raise ReviewRefused(400, "invalid_value", f"{value!r} is not an allowed value for {field}.") from exc


async def _stored_decision(decision_id: str, session: Any = None) -> Decision:
    doc = await store.get_db()["decisions"].find_one({"_id": decision_id}, session=session)
    if doc is None:
        raise ReviewRefused(409, "conflict", "The value was reviewed, but its Decision is missing.")
    return as_decision(doc)


def _search_text(name: str | None, fields: dict[str, list[dict[str, Any]]]) -> str:
    parts = [name or ""]
    for key in sorted(fields):
        parts.extend(str(e.get("label") or e.get("value")) for e in fields[key] if e.get("state") == "current")
    return " ".join(p for p in parts if p).strip()


def _facets(fields: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    facets = {}
    for key in FACET_FIELDS:
        values = sorted({e["value"] for e in fields.get(key, []) if e.get("state") == "current"})
        if values:
            facets[key] = values
    return facets


def _reviewed_entries(
    entries: list[dict[str, Any]],
    index: int,
    action: str,
    edited_value: str | None,
    edited_label: str | None,
    reason: str | None,
    decision: Decision,
    ctx: RunContext,
    now: datetime,
) -> list[dict[str, Any]]:
    entries = [dict(e) for e in entries]
    entry = entries[index]
    decided = {
        "decided_by": ctx.principal.id,
        "decided_at": now,
        "reason": reason,
        "review_decision_id": decision.id,
    }
    if action == "accept":
        entry.update(decided, review="accepted")
    elif action == "reject":
        entry.update(decided, state="rejected")
    else:
        entry.update(decided, state="superseded")
        entries.append(
            {
                "value_id": derive("v_", entry["value_id"], "edit", decision.id),
                "value": edited_value,
                "label": edited_label,
                "detail": entry.get("detail"),
                "state": "current",
                "review": "edited",
                "evidence": entry.get("evidence"),
                "check": entry.get("check"),
                "proposal_id": entry.get("proposal_id"),
                "action_id": decision.action_id,
                "stamp": ctx.stamp.model_dump(mode="python"),
                "edited_from_value_id": entry["value_id"],
                **decided,
            }
        )
    entries[index] = entry
    return entries


def _stage_after(field: str, entries: list[dict[str, Any]], stored: str | None) -> str | None:
    """`lifecycle_stage` follows the review of its field (AD-5): the current entry's stage, or not determined."""
    if field != "lifecycle_stage":
        return stored
    current = [e["value"] for e in entries if e.get("state") == "current"]
    return current[-1] if current else registry.NOT_DETERMINED


async def _settle_action(decision: Decision, status: str, value_ids: list[str], session: Any) -> None:
    """Set the review's DxP-state action done or failed through the gate (`gate.mark_action`, V65):
    only Governance writes `actions`; it emits the deduplicated `action_status_changed` event."""
    if not decision.action_id:
        return
    result = {"proposal_ids": [], "value_ids": value_ids, "report_id": None, "memory_id": None, "task_id": None}
    await gate.mark_action(decision.action_id, status, result if status == "done" else None, session=session)


async def _evaluate(ctx: RunContext, proposed: ProposedAction, session: Any) -> Decision:
    """The gate inside the review's transaction (A06's `gate.evaluate_in`); no fallback outside it."""
    return as_decision(await gate.evaluate_in(ctx, proposed, session))


async def in_transaction(body: Callable[[Any], Awaitable[ReviewOutcome]]) -> ReviewOutcome:
    """Run the gate and the write in one transaction, so an allowed Decision never stands
    without its write; a transient conflict retries the whole body (pymongo `with_transaction`)."""
    async with store.get_client().start_session() as session:
        return await session.with_transaction(body)


async def review_value(
    dx_id: str,
    value_id: str,
    action: str,
    value: str | None,
    reason: str | None,
    ctx: RunContext,
) -> ReviewOutcome:
    """Accept, edit or reject one unreviewed value through the gate (kind `review_value`, D16)."""
    reason = validate_request(action, value, reason)
    db = store.get_db()

    doc = await db["diagnostics"].find_one({"_id": dx_id})
    if doc is None:
        raise ReviewRefused(404, "not_found", f"Diagnostic {dx_id} not found.")
    found = find_entry(doc, value_id)
    if found is None:
        raise ReviewRefused(404, "not_found", f"Value {value_id} not found on {dx_id}.")
    field, _, entry = found
    if entry.get("review_decision_id"):
        return ReviewOutcome(await _stored_decision(entry["review_decision_id"]), changed=False)
    if entry.get("review") != "unreviewed":
        raise ReviewRefused(409, "not_unreviewed", f"Value {value_id} is {entry.get('review')}, not unreviewed.")
    edited_value = canonical_edit(field, value or "") if action == "edit" else None
    edited_label = (value or "").strip() if action == "edit" else None

    # Apply recovery runs on every decision call, before the decision (D26).
    await recover_applying()

    origin_run_id = (entry.get("stamp") or {}).get("run_id")
    ctx = ctx.model_copy(
        update={
            "run_id": None,
            "request_id": ctx.request_id or new_request_id(),
            "cause": ctx.cause or DecisionCause(proposal_id=entry.get("proposal_id"), origin_run_id=origin_run_id),
        }
    )
    proposed = ProposedAction(
        kind=KIND,
        destination=DESTINATION,
        target=Target(diagnostic_id=dx_id, value_id=value_id),
        inputs={"action": action, "field": field, "value": value, "reason": reason},
    )

    async def body(session: Any) -> ReviewOutcome:
        decision = await _evaluate(ctx, proposed, session)
        if decision.outcome != "allowed":
            return ReviewOutcome(decision, changed=False)

        doc = await db["diagnostics"].find_one({"_id": dx_id}, session=session)
        found = find_entry(doc or {}, value_id)
        if doc is None or found is None:
            raise ReviewRefused(404, "not_found", f"Value {value_id} not found on {dx_id}.")
        field, index, entry = found
        if entry.get("review_decision_id"):
            # Another review won the race: this one changes nothing.
            await _settle_action(decision, "failed", [], session)
            return ReviewOutcome(await _stored_decision(entry["review_decision_id"], session), changed=False)
        if entry.get("review") != "unreviewed":
            raise ReviewRefused(409, "not_unreviewed", f"Value {value_id} is no longer unreviewed.")

        now = _now()
        fields = {key: [dict(e) for e in entries or []] for key, entries in (doc.get("fields") or {}).items()}
        fields[field] = _reviewed_entries(
            fields[field], index, action, edited_value, edited_label, reason, decision, ctx, now
        )
        stage = _stage_after(field, fields[field], doc.get("lifecycle_stage"))
        rev_guard = {"rev": doc["rev"]} if "rev" in doc else {"rev": {"$exists": False}}
        res = await db["diagnostics"].update_one(
            {"_id": dx_id, **rev_guard},
            {
                "$set": {
                    f"fields.{field}": fields[field],
                    "lifecycle_stage": stage,
                    "search_text": _search_text(doc.get("name"), fields),
                    "facets": _facets(fields),
                    "updated_at": now,
                },
                "$inc": {"rev": 1},
            },
            session=session,
        )
        if not res.matched_count:
            raise ReviewRefused(409, "conflict", f"Diagnostic {dx_id} changed during the review; try again.")
        value_ids = [value_id] + ([fields[field][-1]["value_id"]] if action == "edit" else [])
        await _settle_action(decision, "done", value_ids, session)
        return ReviewOutcome(decision, changed=True)

    return await in_transaction(body)
