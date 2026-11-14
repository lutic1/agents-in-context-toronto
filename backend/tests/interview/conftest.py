"""Fixtures of the interview lane: an accepted report, fake reads, a recording fake llm, a Reviewer context.

Nothing here reaches Atlas, Anthropic or any other service. The gate is `conftest.fake_gate` (A01).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

import pytest

from dxp.api import models as m

REPORT_ID = "rep_0123456789abcdef"
VERSION_ID = "sv_aaaaaaaaaaaaaaaa"
RELATED_VERSION_ID = "sv_bbbbbbbbbbbbbbbb"
PENDING_VERSION_ID = "sv_cccccccccccccccc"
SOURCE_REF = "clinicaltrials.gov:NCT04712877"
RELATED_REF = "clinicaltrials.gov:NCT05715229"

Q_PURPOSE = "This study investigates molecular profiling using blood (ctDNA) and tumor tissue in early-stage (IA2 to III) lung cancer."
Q_NAMES = "Other names: FoundationOne CDx, FoundationOne Liquid"
Q_STATUS = "Overall status: RECRUITING. No results posted."
Q_ENROL = "Estimated enrollment: 120 participants."
Q_RELATED_NEW = "Plasma ctDNA genotyping in early-stage disease."
Q_RELATED_OLD = "Plasma ctDNA genotyping in advanced NSCLC."
Q_PENDING = "A pending relationship quote about circulating tumor DNA."

RAW_TEXT = " ".join([Q_PURPOSE, Q_NAMES, Q_STATUS, Q_ENROL, Q_RELATED_NEW])
RELATED_RAW_TEXT = f"Brief summary. {Q_RELATED_OLD} Second line."
PENDING_RAW_TEXT = Q_PENDING


def make_report(**overrides: Any) -> dict[str, Any]:
    """An accepted report document as the store keeps it (`_id`, nested discovery and related)."""
    report: dict[str, Any] = {
        "_id": REPORT_ID,
        "run_id": "run_0123456789abcdef",
        "scope_id": "scope_plasma_ctdna_nsclc",
        "team_id": "team_liquid",
        "source_ref": SOURCE_REF,
        "version_id": VERSION_ID,
        "status": "accepted",
        "headline": "New trial signal worth investigating",
        "discovery": {
            "summary": "A trial record.",
            "trial_status": "RECRUITING",
            "has_results": False,
            "quotes": [
                {"text": Q_PURPOSE, "quote_found": True, "version_id": VERSION_ID},
                {"text": Q_NAMES, "quote_found": True, "version_id": VERSION_ID},
                {"text": Q_STATUS, "quote_found": True, "version_id": VERSION_ID},
                {"text": Q_ENROL, "quote_found": True, "version_id": VERSION_ID},
                {"text": "A quote that was never found.", "quote_found": False, "version_id": VERSION_ID},
            ],
            "mentions": [
                {"name": "FoundationOne CDx", "field": "otherNames", "resolved_diagnostic_id": None},
                {"name": "FoundationOne Liquid", "field": "otherNames", "resolved_diagnostic_id": None},
            ],
        },
        "related": [
            {
                "_id": "rel_0123456789abcdef",
                "related_ref": RELATED_REF,
                "label": "extends",
                "status": "accepted",
                "new_quote": {"source_ref": SOURCE_REF, "version_id": VERSION_ID, "text": Q_RELATED_NEW, "quote_found": True},
                "related_quote": {"source_ref": RELATED_REF, "version_id": RELATED_VERSION_ID, "text": Q_RELATED_OLD, "quote_found": True},
            },
            {
                "_id": "rel_fedcba9876543210",
                "related_ref": "clinicaltrials.gov:NCT00000001",
                "label": "supports",
                "status": "pending",
                "new_quote": {"source_ref": SOURCE_REF, "version_id": VERSION_ID, "text": Q_PENDING, "quote_found": True},
                "related_quote": {"source_ref": "clinicaltrials.gov:NCT00000001", "version_id": PENDING_VERSION_ID, "text": Q_PENDING, "quote_found": True},
            },
        ],
        "uncertainties": [],
        "gap": "Have early-stage studies posted results?",
    }
    for key, value in overrides.items():
        report[key] = value
    return report


@dataclass
class FakeLlm:
    """Stands in for `llm.call_structured`. It records every call; `ids` are what it will select."""

    ids: list[str] | None = None
    result: Any = None
    error: Exception | None = None
    calls: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = field(default_factory=list)
    chooser: Any = None  # optional callable(messages) -> result

    async def __call__(self, model: str, schema: dict[str, Any], messages: list[dict[str, Any]]) -> Any:
        self.calls.append((model, schema, messages))
        if self.error is not None:
            raise self.error
        if self.chooser is not None:
            return self.chooser(messages)
        if self.result is not None:
            return self.result
        return {"quote_ids": list(self.ids or [])}

    def prompt_text(self) -> str:
        return "\n".join(str(msg["content"]) for _, _, messages in self.calls for msg in messages)


def quote_id(text: str, source_ref: str = SOURCE_REF, version_id: str = VERSION_ID, field_name: str = "discovery") -> str:
    from dxp.interview.cards import quote_id_for

    return quote_id_for(source_ref, version_id, field_name, text)


@dataclass
class Store:
    reports: dict[str, dict[str, Any]]
    raw: dict[str, str]
    reads: list[str] = field(default_factory=list)


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> Store:
    """In-memory replacements for the lane's two reads."""
    from dxp.interview import repo

    fake = Store(
        reports={REPORT_ID: make_report()},
        raw={VERSION_ID: RAW_TEXT, RELATED_VERSION_ID: RELATED_RAW_TEXT, PENDING_VERSION_ID: PENDING_RAW_TEXT},
    )

    async def get_report(report_id: str) -> dict[str, Any] | None:
        fake.reads.append(report_id)
        found = fake.reports.get(report_id)
        return copy.deepcopy(found) if found else None

    async def get_raw_text(version_id: str) -> str | None:
        return fake.raw.get(version_id)

    monkeypatch.setattr(repo, "get_report", get_report)
    monkeypatch.setattr(repo, "get_raw_text", get_raw_text)
    return fake


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeLlm:
    import dxp.llm

    fake = FakeLlm()
    monkeypatch.setattr(dxp.llm, "call_structured", fake)
    return fake


def make_ctx(actions: list[str] | None = None) -> m.RunContext:
    granted = ["answer_question"] if actions is None else actions
    principal = m.Principal(id="sam", name="Sam", kind="person", actions=granted)  # type: ignore[arg-type]
    stamp = m.Stamp(kind="reviewer", principal="sam", initiated_by="sam", grant_id="sam", grant_version=2)
    return m.RunContext(
        run_id=None,
        principal=principal,
        stamp=stamp,
        grant_id="sam",
        grant_version=2,
        policy_set_version="ps_test",
        mode="live",
        request_id="req_test",
        cause=m.DecisionCause(report_id=REPORT_ID, origin_run_id="run_0123456789abcdef"),
    )


@pytest.fixture
def ctx() -> m.RunContext:
    return make_ctx()
