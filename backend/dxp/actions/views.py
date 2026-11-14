"""Stored documents to AD-14 shapes. The gate may return its own dict-like Decision (A06) or
the `Decision` model (A01's contract, the fake gate): both are handled."""

from __future__ import annotations

from typing import Any

from dxp.api.models import Action, Decision


def decision_dict(decision: Any) -> dict[str, Any]:
    """A Decision as a stored-shape dict with `_id`."""
    if hasattr(decision, "model_dump"):
        data = decision.model_dump(mode="python")
        data["_id"] = data.pop("id")
        return data
    data = dict(decision)
    if "_id" not in data and "id" in data:
        data["_id"] = data["id"]
    return data


def decision_model(decision: Any) -> Decision:
    if isinstance(decision, Decision):
        return decision
    data = decision_dict(decision)
    return Decision.model_validate({**data, "id": data["_id"]})


def action_model(doc: dict[str, Any]) -> Action:
    data = {k: v for k, v in doc.items() if k != "_id"}
    return Action.model_validate({**data, "id": doc["_id"]})
