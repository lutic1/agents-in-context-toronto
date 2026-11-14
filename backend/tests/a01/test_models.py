"""A01: the shapes behave as AD-14 says."""

from __future__ import annotations

from dxp.api import models as m


def test_action_result_variants_keep_their_fields() -> None:
    slack = {"http_status": 200, "response_body": "ok", "posted_at": "2026-11-14T14:30:00Z",
             "link_urls": {"report_url": "https://dxp.test/reports/rep_1", "diagnostic_url": None}}
    ledger = {"proposal_ids": ["p_1"], "value_ids": [], "report_id": "rep_1", "memory_id": None, "task_id": None}
    scan = {"http_status": 200, "cursor_from": "2026-11-01", "cursor_to": "2026-11-12", "source_refs": ["clinicaltrials.gov:NCT04712877"], "count": 1}
    base = {"id": "act_1", "decision_id": "dec_1", "kind": "notify_slack", "destination": "slack:#all-mango-db-hackathon",
            "stamp": {"kind": "run", "principal": "dxp-curator"}, "status": "delivered"}
    assert isinstance(m.Action(**base, result=slack).result, m.SlackResult)
    assert isinstance(m.Action(**{**base, "kind": "file_proposal", "destination": "ledger", "status": "done"}, result=ledger).result, m.LedgerResult)
    assert isinstance(m.Action(**{**base, "kind": "search_source", "destination": "source:clinicaltrials.gov"}, result=scan).result, m.SearchSourceResult)


def test_source_version_never_returns_raw_text() -> None:
    sv = m.SourceVersion(id="sv_1", source_ref="clinicaltrials.gov:NCT1", content_hash="abc", raw_text="secret text")
    assert "raw_text" not in sv.model_dump()


def test_scope_collection_update_has_no_diagnostic() -> None:
    proposal = m.Proposal(id="p_1", target={"scope_id": "scope_plasma_ctdna_nsclc"}, field="trials", value="NCT04712877",
                          status="pending", mode="live")
    assert proposal.diagnostic_id is None and proposal.op == "add" and proposal.reverts_proposal_id is None


def test_kinds_include_revert_report_and_statuses_include_v48() -> None:
    assert "revert_report" in m.ActionKind.__args__
    assert "cancelled" in m.TaskStatus.__args__
    assert {"reverting", "reverted"} <= set(m.ReportStatus.__args__)
