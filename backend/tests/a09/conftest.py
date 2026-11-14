"""A09 fixtures: an in-memory `actions` store, the fake gate with hex decision IDs, A01's
`fake_slack` installed as the sender, and a report like the demo's (V33, V35, V43).

Nothing here reaches Slack: every test posts through `fake_slack` or a local HTTP fake.
Quotes and headlines are invented test text, not registry or PubMed text.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

import dxp.gate
from dxp.actions import dispatcher, records, slack
from dxp.api.models import Principal, ProposedAction, RunContext, Stamp, Target
from dxp.identity import derive

from .memdb import MemDB

RUN_ID = "run_0123456789abcdef"
REPORT_ID = "rep_00000000000000a1"
SCOPE_ID = "scope_plasma_ctdna_nsclc"
NCT = "NCT04712877"
POLICY_SET = "ps_00000000000000ff"
HEADLINE = (
    "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage "
    "(IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted."
)


def make_report(**overrides: Any) -> dict[str, Any]:
    report = {
        "_id": REPORT_ID,
        "run_id": RUN_ID,
        "scope_id": SCOPE_ID,
        "team_id": "team_test",
        "source_ref": f"ctgov:{NCT}",
        "version_id": "sv_0000000000000001",
        "nct_id": NCT,
        "headline": HEADLINE,
        "discovery": {
            "summary": "A new trial signal in the scope.",
            "quotes": [{"text": "Blood and tissue samples are collected before surgery (test text).", "quote_found": True}],
            "trial_status": "RECRUITING",
            "has_results": False,
            "intervention_text": "ctDNA, tumor NGS",
            "mentions": [{"name": "FoundationOne CDx", "resolved_diagnostic_id": None, "field": "otherNames"}],
        },
        "related": [
            {
                "id": "rel_1",
                "related_ref": "ctgov:NCT00000001",
                "related_kind": "source_item",
                "related_title": "A prior plasma genotyping study (test)",
                "label": "extends",
                "new_quote": {"source_ref": f"ctgov:{NCT}", "text": "Early-stage patients (test).", "quote_found": True},
                "related_quote": {"source_ref": "ctgov:NCT00000001", "text": "Advanced-stage patients (test).", "quote_found": True},
                "similarity": 0.82,
                "origin": "discovery",
                "status": "pending",
            },
            {
                "id": "rel_2",
                "related_ref": "ctgov:NCT00000002",
                "related_kind": "source_item",
                "label": "related_unestablished",
                "similarity": 0.61,
                "origin": "discovery",
                "status": "pending",
            },
        ],
        "uncertainties": [],
        "gap": "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?",
        "proposal_ids": ["p_00000000000000b1", "p_00000000000000b2"],
        "diagnostic_ids": [],
        "status": "pending",
        "script": "test script",
        "script_hash": "h",
    }
    report.update(overrides)
    return report


def make_proposals() -> list[dict[str, Any]]:
    return [
        {"_id": "p_00000000000000b1", "diagnostic_id": None, "target": {"scope_id": SCOPE_ID}, "field": "evidence_collection",
         "value": f"ctgov:{NCT}", "status": "pending", "report_id": REPORT_ID},
        {"_id": "p_00000000000000b2", "diagnostic_id": None, "target": {"scope_id": SCOPE_ID}, "field": "evidence_collection",
         "value": f"ctgov:{NCT}|note", "status": "pending", "report_id": REPORT_ID},
    ]


def run_ctx(run_id: str = RUN_ID) -> RunContext:
    stamp = Stamp(kind="run", run_id=run_id, agent="dxp-curator", initiated_by="sam", principal="dxp-curator",
                  grant_id="lbdx", grant_version=1, policy_set_version=POLICY_SET)
    return RunContext(run_id=run_id, principal=Principal(id="dxp-curator", name="dxp-curator", kind="agent"),
                      stamp=stamp, grant_id="lbdx", grant_version=1, run_grant_version=1,
                      policy_set_version=POLICY_SET, admission_id=derive("adm_", run_id, "k"))


def reviewer_ctx() -> RunContext:
    stamp = Stamp(kind="reviewer", principal="sam", initiated_by="sam", grant_id="sam", grant_version=1)
    return RunContext(principal=Principal(id="sam", name="Sam", kind="person"), stamp=stamp,
                      grant_id="sam", grant_version=1, request_id="req0000000000001")


def notify(report_id: str = REPORT_ID, **target: Any) -> ProposedAction:
    return ProposedAction(kind="notify_slack", destination=slack.DESTINATION, target=Target(report_id=report_id, **target))


@pytest.fixture
def mem(monkeypatch: pytest.MonkeyPatch) -> MemDB:
    db = MemDB()
    monkeypatch.setattr(records, "get_db", lambda: db)
    monkeypatch.setattr(records, "emit_event", db.emit_event)
    return db


@pytest.fixture
def seeded(mem: MemDB) -> MemDB:
    mem["reports"].docs[REPORT_ID] = make_report()
    for p in make_proposals():
        mem["proposals"].docs[p["_id"]] = p
    return mem


@pytest.fixture
def gate(fake_gate, monkeypatch: pytest.MonkeyPatch):
    """A01's fake gate, with decision IDs in the stored `dec_<16 hex>` form."""

    async def evaluate(ctx: Any, action: Any) -> Any:
        decision = await fake_gate.evaluate(ctx, action)
        return decision.model_copy(update={"id": derive("dec_", "a09-test", len(fake_gate.calls))})

    monkeypatch.setattr(dxp.gate, "evaluate", evaluate)
    return fake_gate


@pytest.fixture
def sent(fake_slack):
    """A01's fake Slack sender, installed as the only sender."""
    with slack.use_sender(fake_slack):
        yield fake_slack


@pytest.fixture
def waits(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retry-After waits, recorded instead of slept."""
    seen: list[float] = []

    async def no_sleep(seconds: float) -> None:
        seen.append(seconds)

    monkeypatch.setattr(dispatcher, "sleep", no_sleep)
    return seen


def now() -> datetime:
    return datetime.now(UTC)
