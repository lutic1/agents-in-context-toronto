"""A01: ensure_indexes takes A03's full validators when store.schemas.validator exists (no Atlas needed)."""

from __future__ import annotations

import pytest

from dxp.store import indexes, schemas


def test_full_validator_wins_and_keeps_extra_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    full = {"$jsonSchema": {"bsonType": "object"}, "$expr": {"$eq": ["$_id", {"$concat": ["$grant_id", "@v"]}]}}
    monkeypatch.setattr(schemas, "VALIDATORS", {"grants": {"bsonType": "object"}})
    monkeypatch.setattr(schemas, "validator", lambda name: full if name == "grants" else None, raising=False)
    validators = indexes._validators()
    assert validators["grants"] == full
    assert "runs" not in validators


def test_bare_json_schema_is_wrapped_without_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(schemas, "VALIDATORS", {"tasks": {"bsonType": "object"}})
    monkeypatch.delattr(schemas, "validator", raising=False)
    assert indexes._validators() == {"tasks": {"$jsonSchema": {"bsonType": "object"}}}
