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


def test_check_report_pins_the_version_and_keeps_the_report_fields() -> None:
    drafted = item.check_report({"updates": [{"finding_id": "f", "change": {}}], "drafts": [{"draft": 1}, {"draft": 2}]}, "sv_1")
    assert drafted["version_id"] == "sv_1" and len(drafted["updates"]) == 1 and len(drafted["drafts"]) == 2
    with pytest.raises(item.ItemFailed):
        item.check_report({"version_id": "sv_other"}, "sv_1")
    with pytest.raises(item.ItemFailed):
        item.check_report("not a report", "sv_1")


def test_draft_targets_match_a19_gate_target() -> None:
    drafted = {"drafts": [{"draft": 1}, {"draft": 2}]}
    assert [t for _, t in item.draft_targets(drafted, "rep_x")] == ["rep_x|draft1", "rep_x|draft2"]
    assert [t for _, t in item.draft_targets({**drafted, "attempt": 1}, "rep_x")] == ["rep_x|draft1.r1", "rep_x|draft2.r1"]
    assert [t for _, t in item.draft_targets({"draft": 1, "drafts": None}, "rep_x")] == ["rep_x|draft1"]


def test_change_target_follows_ad3() -> None:
    assert item.change_target("f_1", {"proposal_id": "p_1"}) == "p_1"
    derived = item.change_target("f_1", {"field": "evidence_collection", "value": "x"})
    assert derived.startswith("p_") and len(derived) == 18
    assert item.change_target(None, {"field": "f", "value": "v"}) == "f|v"
