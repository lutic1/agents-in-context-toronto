"""A10: pacing and concurrency (AD-12, D33) and the draft shapes the run accepts (V21)."""

from __future__ import annotations

import pytest

from dxp.pipeline import config, item


@pytest.mark.parametrize(("raw", "expected"), [("", None), ("0", None), ("off", None), ("1", 4.0), ("true", 4.0), ("6", 6.0), ("2.5", 2.5)])
def test_demo_pace(monkeypatch: pytest.MonkeyPatch, raw: str, expected: float | None) -> None:
    monkeypatch.setenv("DXP_DEMO_PACE", raw)
    assert config.pace_seconds() == expected


def test_concurrency_is_one_with_pace_and_never_above_16(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DXP_DEMO_PACE", "")
    assert 1 <= config.concurrency() <= 16
    monkeypatch.setattr(config, "MAX_CONCURRENCY", 64)
    assert config.concurrency() == 16
    monkeypatch.setenv("DXP_DEMO_PACE", "3")
    assert config.concurrency() == 1


def test_agent_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DXP_AGENT_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        config.agent_key()
    assert "DXP_AGENT_KEY" in str(exc.value)


def test_split_drafts_accepts_the_three_shapes() -> None:
    assert [d["draft"] for d in item.split_drafts({"drafts": [{"a": 1}, {"a": 2}]})] == [1, 2]
    assert [d["draft"] for d in item.split_drafts({"draft1": {}, "draft2": {}})] == [1, 2]
    assert [d["draft"] for d in item.split_drafts({"headline": "x"})] == [1]
    with pytest.raises(item.ItemFailed):
        item.split_drafts("not a draft")


def test_change_target_follows_ad3() -> None:
    assert item.change_target({"proposal_id": "p_1"}) == "p_1"
    derived = item.change_target({"finding_id": "f_1", "field": "evidence_collection", "value": "x"})
    assert derived.startswith("p_") and len(derived) == 18
    assert item.change_target({"field": "f", "value": "v"}) == "f|v"
