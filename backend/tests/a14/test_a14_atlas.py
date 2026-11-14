"""A14 against the Atlas Sandbox, in the session's fresh test database (never `dxp`).

Skipped without MONGODB_URI (tests/conftest.py). The value review runs its real transaction here;
the gate is the conftest fake gate, so no grant or policy seed is needed.
"""

from __future__ import annotations

import uuid

import pytest

from dxp.api import models as m
from dxp.ledger import review
from dxp.search import readmodel
from tests.a14.conftest import diagnostic_doc, proposal_doc

pytestmark = pytest.mark.atlas


def _ids() -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:8]
    return f"dx_a14_{suffix}", f"rep_a14_{suffix}"


def _reviewer_ctx() -> m.RunContext:
    principal = m.Principal(id="sam", name="Sam", kind="person", actions=["review_value"])
    stamp = m.Stamp(kind="reviewer", principal="sam", initiated_by="sam", grant_id="sam", grant_version=1)
    return m.RunContext(principal=principal, stamp=stamp, grant_id="sam", grant_version=1, request_id=review.new_request_id())


async def test_accepted_knowledge_and_pending_proposals(db):
    dx_id, report_id = _ids()
    doc = diagnostic_doc()
    doc["_id"] = dx_id
    await db["diagnostics"].insert_one(doc)
    pending = proposal_doc(f"p_pending_{dx_id}", diagnostic_id=dx_id, report_id=report_id)
    await db["proposals"].insert_one(pending)

    record = await readmodel.get_diagnostic(dx_id)
    trials = {v.value_id for v in record.fields["trials"].values}
    assert trials == {"v_trial"}  # failed, unapplied and pending-state entries are left out
    assert record.fields["biomarkers"].no_data is True
    assert "raw_text" not in record.model_dump_json()

    items = await readmodel.list_proposals(diagnostic_id=dx_id, status="pending")
    assert [(p.id, p.report_id) for p in items] == [(pending["_id"], report_id)]
    assert await readmodel.get_diagnostic(f"{dx_id}_missing") is None


async def test_value_review_in_a_transaction(db, fake_gate, monkeypatch):
    import dxp.gate

    monkeypatch.setattr(dxp.gate, "evaluate_in", lambda ctx, action, session: fake_gate.evaluate(ctx, action), raising=False)
    dx_id, _ = _ids()
    doc = diagnostic_doc()
    doc["_id"] = dx_id
    await db["diagnostics"].insert_one(doc)

    outcome = await review.review_value(dx_id, "v_plasma", "reject", None, "the row names tissue", _reviewer_ctx())
    assert outcome.changed and outcome.decision.outcome == "allowed"
    stored = await db["diagnostics"].find_one({"_id": dx_id})
    (plasma,) = stored["fields"]["sample_types"]
    assert plasma["state"] == "rejected" and plasma["reason"] == "the row names tissue" and plasma["decided_by"] == "sam"
    assert stored["rev"] == doc["rev"] + 1

    fake_gate.block("review_value")
    blocked = await review.review_value(dx_id, "v_modality", "accept", None, None, _reviewer_ctx())
    assert not blocked.changed and blocked.decision.outcome == "blocked"
    assert (await db["diagnostics"].find_one({"_id": dx_id}))["rev"] == doc["rev"] + 1
