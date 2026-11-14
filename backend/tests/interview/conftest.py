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
Q_CLAIM = "FoundationOne CDx is better than FoundationOne Liquid in sensitivity (92% vs 85%)."
Q_BLANK = "Observational cohort of adults.\n\nSamples are collected at baseline."
Q_BLANK_SHOWN = "Observational cohort of adults. Samples are collected at baseline."
Q_CONDITIONS = "Conditions: Lung Cancer, Non-Small Cell Lung Cancer"
Q_STATUS = "Overall status: RECRUITING."
Q_RESULTS = "Results posted: No."
Q_PHASE = "Phase: Not Applicable"
Q_DESIGN = "Study type: OBSERVATIONAL. Observational model: Cohort. Time perspective: Prospective."
Q_DATES = "Start date: 2021-03-01. Primary completion date: 2026-06-30 (estimated)."
Q_SPONSOR = "Lead sponsor: Example University Hospital. Collaborators: Open Network."
Q_LOCATION = "Locations: Toronto, Canada; Boston, United States."
Q_ENROL = "Estimated enrollment: 120 participants."
Q_INTERVENTION = "Intervention (DEVICE): FoundationOne Liquid."
Q_NAMES = "Other names: FoundationOne CDx, FoundationOne Liquid"
Q_RELATED_NEW = "Plasma ctDNA genotyping in early-stage disease."
Q_RELATED_OLD = "Plasma ctDNA genotyping in advanced NSCLC."
Q_PENDING = "A pending relationship quote about circulating tumor DNA."

DISCOVERY_QUOTES = [
    Q_PURPOSE, Q_CLAIM, Q_BLANK, Q_CONDITIONS, Q_STATUS, Q_RESULTS, Q_PHASE, Q_DESIGN, Q_DATES, Q_SPONSOR, Q_LOCATION,
    Q_ENROL, Q_INTERVENTION, Q_NAMES,
]

RAW_TEXT = "\n\n".join(
    [
        "Brief title: Plasma ctDNA genotyping in early-stage lung cancer",
        f"Brief summary: {Q_PURPOSE}",
        f"Detailed description: {Q_CLAIM}\n\n{Q_BLANK}",
        Q_CONDITIONS,
        Q_STATUS,
        Q_RESULTS,
        Q_PHASE,
        Q_DESIGN,
        Q_DATES,
        Q_SPONSOR,
        Q_LOCATION,
        Q_ENROL,
        Q_INTERVENTION,
        Q_NAMES,
        "Eligibility criteria: Adults with early-stage lung cancer.",
        Q_RELATED_NEW,
    ]
)
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
            "quotes": [{"text": text, "quote_found": True, "version_id": VERSION_ID} for text in DISCOVERY_QUOTES]
            + [{"text": "A quote that was never found.", "quote_found": False, "version_id": VERSION_ID}],
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


def quote_id(text: str, report: dict[str, Any] | None = None) -> str:
    """The quote ID of the card made from this quote (the fixture's pinned raw text decides its field)."""
    from dxp.interview import cards

    shown = cards.normalise_text(text)
    for card in cards.load_cards(report or make_report(), {VERSION_ID: RAW_TEXT}):
        if card.text == shown:
            return card.quote_id
    raise AssertionError(f"not a card: {text!r}")


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
