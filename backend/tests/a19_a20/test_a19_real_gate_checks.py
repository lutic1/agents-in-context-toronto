"""The report-level file_proposal and file_related_evidence carry the AD-6 checks that the seeded
evidence policy reads, judged by the real gate's own code (A06), not a fake. Without them the gate
fails closed and blocks every report draft and every related-evidence filing (found at I1)."""

import importlib
import json
from pathlib import Path

import pytest

from dxp.api.models import Relationship
from dxp.gate import checks as gate_checks

file_module = importlib.import_module("dxp.reports.file")
POLICIES = json.loads((Path(gate_checks.__file__).parent / "seed_data" / "policies.json").read_text())
POLICIES = POLICIES if isinstance(POLICIES, list) else POLICIES.get("policies", POLICIES.get("items", []))
DRAFT = {"source_ref": "ctgov:NCT04712877", "version_id": "sv_aaaaaaaaaaaaaaaa", "scope_id": "scope_x",
         "headline": "H.", "gap": "G?", "summary": "S.", "draft": 1, "source_fields": {},
         "claims": [{"text": "S.", "claim_kind": "claim_planned", "quote": "q", "quote_found": True}]}


def failures(action):
    gate_action = gate_checks.GateAction.coerce(action)
    return gate_checks._requires_failures(gate_checks._policies_for(gate_action.kind, POLICIES), gate_action.checks)


def test_the_evidence_policy_applies_to_both_kinds():
    assert gate_checks._policies_for("file_proposal", POLICIES)
    assert gate_checks._policies_for("file_related_evidence", POLICIES)


def test_a_report_draft_with_found_quotes_meets_the_evidence_policy():
    draft = {**DRAFT, "quotes": [{"text": "q", "quote_found": True, "version_id": "sv_aaaaaaaaaaaaaaaa"}]}
    action = file_module.report_action("rep_1", draft, draft)
    assert action.inputs["checks"] == [{"quote_found": True, "supported": True}]
    assert failures(action) == []


@pytest.mark.parametrize("quotes", [[], [{"text": "q", "quote_found": False, "version_id": "sv_aaaaaaaaaaaaaaaa"}]])
def test_a_report_draft_without_a_found_quote_is_still_blocked(quotes):
    draft = {**DRAFT, "quotes": quotes}
    assert failures(file_module.report_action("rep_1", draft, draft)) != []


def _relationship(found_new, found_related):
    return Relationship.model_validate({
        "id": "rel_1", "related_ref": "ctgov:NCT00000001", "related_kind": "source_item",
        "label": "supports" if found_new and found_related else "related_unestablished",
        "new_quote": {"source_ref": "ctgov:NCT04712877", "version_id": "sv_a", "text": "a", "quote_found": found_new},
        "related_quote": {"source_ref": "ctgov:NCT00000001", "version_id": "sv_b", "text": "b",
                          "quote_found": found_related},
        "origin": "task:t_1", "status": "pending"})


def test_related_evidence_checks_need_both_quotes_found():
    both = file_module.quote_checks([_relationship(True, True).new_quote, _relationship(True, True).related_quote])
    assert both == [{"quote_found": True, "supported": True}] * 2
    one = file_module.quote_checks([_relationship(True, False).new_quote, _relationship(True, False).related_quote])
    assert gate_checks._requires_failures(gate_checks._policies_for("file_related_evidence", POLICIES), both) == []
    assert gate_checks._requires_failures(gate_checks._policies_for("file_related_evidence", POLICIES), one) != []
