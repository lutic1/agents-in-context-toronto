"""A24 on the Atlas Sandbox (a fresh `dxp_test_<hex>` database, never `dxp`): the approval in one
transaction, the retried approval, and the V45 crash test with its revoked-`sam@v1` variant,
through the real store, the real gate (A06), the real `ledger.apply_with` (A06) and the real
grant selection (A03).

Skipped without MONGODB_URI (conftest), and skipped with a stated reason while the gate,
ledger or grant selection on this branch is still A01's stub (A06 and A03 not merged).
Only `runs.start` and `memory.create` are doubles here (A07+A11 and A21+A22 are not merged).
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import pytest

from dxp.api import models as m
from dxp.identity import derive

from .conftest import (
    SAM_ACTIONS,
    SCOPE_ID,
    SOURCE_REF,
    grant_doc,
    proposal_doc,
    report_doc,
)

pytestmark = pytest.mark.atlas


def _stub(module: str, name: str) -> bool:
    fn = getattr(importlib.import_module(module), name, None)
    if fn is None:
        return True
    try:
        return "raise NotImplementedError(" in inspect.getsource(fn)
    except (OSError, TypeError):
        return False


def _require_real_modules() -> None:
    missing = [label for label, stub in (
        ("gate.evaluate (A06)", _stub("dxp.gate", "evaluate")),
        ("ledger.apply_with (A06)", _stub("dxp.ledger", "apply_with")),
        ("gate.policy_sets.current_grant (A03)", _stub("dxp.gate.policy_sets", "current_grant")),
    ) if stub]
    if missing:
        pytest.skip("still A01 stubs on this branch: " + ", ".join(missing))


@pytest.fixture
async def atlas_world(db, monkeypatch: pytest.MonkeyPatch) -> Any:
    _require_real_modules()
    import dxp.memory
    import dxp.runs

    suffix = derive("t", str(id(monkeypatch)))[1:9]
    report = report_doc()
    report_id = derive("rep_", "atlas", suffix)
    report.update({"_id": report_id, "proposal_ids": [derive("p_", "atlas", suffix)]})
    for rel in report["related"]:
        rel["_id"] = rel["id"] = derive("rel_", report_id, suffix)
    proposal = proposal_doc()
    proposal.update({"_id": report["proposal_ids"][0], "report_id": report_id})
    source_ref = f"{SOURCE_REF}#{suffix}"
    proposal["evidence"]["source_ref"] = source_ref
    proposal["value"] = source_ref
    report["source_ref"] = source_ref

    await db["grants"].delete_many({})
    await db["grants"].insert_many([
        grant_doc("lbdx", 1, "dxp-curator", "agent", ["search_source", "file_proposal", "notify_slack"],
                  ["source:clinicaltrials.gov", "ledger", "slack:#all-mango-db-hackathon"]),
        grant_doc("sam", 1, "sam", "person", SAM_ACTIONS, ["ledger", "tts:elevenlabs", "video:heygen"], name="Sam"),
    ])
    await db["research_scopes"].update_one({"_id": SCOPE_ID}, {"$set": {"condition": "non-small cell lung cancer"}},
                                           upsert=True)
    await db["source_items"].insert_one({"_id": source_ref, "collections": {}})
    await db["proposals"].insert_one(proposal)
    await db["reports"].insert_one(report)

    starts: list[str] = []

    async def runs_start(caller, grant_id, set, run_id=None):
        starts.append(run_id)
        return m.Run(id=run_id, agent="dxp-curator", initiated_by=caller.id, grant_id=grant_id, grant_version=1,
                     set=set, kind="task", status="running")

    async def memory_create(*args, **kwargs):
        raise NotImplementedError("memory.create (A21+A22)")

    monkeypatch.setattr(dxp.runs, "start", runs_start)
    monkeypatch.setattr(dxp.memory, "create", memory_create)
    return {"db": db, "report_id": report_id, "proposal_id": proposal["_id"], "source_ref": source_ref,
            "starts": starts}


SAM = m.Principal(id="sam", name="Sam", kind="person")


async def _restart() -> None:
    await importlib.import_module("dxp.reports.decide").recover_accepting()
    await importlib.import_module("dxp.tasks.authorise").recover_authorisations()
    await importlib.import_module("dxp.tasks.dispatch").dispatch_next(lambda run_id: None)


async def test_atlas_approval_promotes_and_authorises_in_one_transaction(atlas_world) -> None:
    rd = importlib.import_module("dxp.reports.decide")
    ta = importlib.import_module("dxp.tasks.authorise")
    db, report_id = atlas_world["db"], atlas_world["report_id"]

    report, decisions = await rd.decide(report_id, "approve", None, None, SAM)
    assert report.status == "accepted" and decisions[0].kind == "decide_report"
    task = await ta.authorise(report_id, SAM)
    assert task.status == "authorised" and task.question == report.gap

    item = await db["source_items"].find_one({"_id": atlas_world["source_ref"]})
    assert item["collections"][SCOPE_ID]["proposal_id"] == atlas_world["proposal_id"]
    assert await db["diagnostics"].count_documents({}) == 0
    grant = await db["grants"].find_one({"_id": f"{task.grant_id}@v1"})
    assert grant is not None and grant["actions"] == ["search_source", "file_related_evidence"]
    auth = await db["decisions"].find_one({"_id": task.authorised_by_decision_id})
    assert auth["outcome"] == "allowed" and auth["kind"] == "authorise_task"
    stored = await db["reports"].find_one({"_id": report_id})
    assert stored["approval"]["task_step"] == "done"
    assert atlas_world["starts"] == []

    # retried: the same decision and task, nothing new
    _, decisions_again = await rd.decide(report_id, "approve", None, None, SAM)
    assert [d.id for d in decisions_again] == [d.id for d in decisions] + [auth["_id"]]
    assert (await ta.authorise(report_id, SAM)).id == task.id
    assert await db["tasks"].count_documents({"report_id": report_id}) == 1


async def test_atlas_crash_between_acceptance_and_authorisation(atlas_world) -> None:
    rd = importlib.import_module("dxp.reports.decide")
    db, report_id = atlas_world["db"], atlas_world["report_id"]

    await rd.decide(report_id, "approve", None, None, SAM)  # accepted; the "crash": authorise never runs
    await _restart()
    await _restart()
    stored = await db["reports"].find_one({"_id": report_id})
    assert stored["approval"]["task_step"] == "done"
    auths = await db["decisions"].find({"kind": "authorise_task", "target.report_id": report_id}).to_list(None)
    assert len(auths) == 1 and auths[0]["cause"]["approval_decision_id"] == stored["approval"]["decision_id"]
    assert await db["tasks"].count_documents({"report_id": report_id}) == 1
    assert await db["grants"].count_documents({"task_id": derive("task_", report_id)}) == 1


async def test_atlas_crash_then_revoked_sam_blocks_the_task_step(atlas_world) -> None:
    rd = importlib.import_module("dxp.reports.decide")
    db, report_id = atlas_world["db"], atlas_world["report_id"]

    await rd.decide(report_id, "approve", None, None, SAM)
    await db["grants"].insert_one(grant_doc("sam", 2, "sam", "person", SAM_ACTIONS,
                                            ["ledger", "tts:elevenlabs", "video:heygen"], status="revoked", name="Sam"))
    await _restart()
    await _restart()
    stored = await db["reports"].find_one({"_id": report_id})
    assert stored["status"] == "accepted" and stored["approval"]["task_step"] == "blocked"
    assert stored["approval"]["message"].startswith("Follow-up task not authorised")
    auths = await db["decisions"].find({"kind": "authorise_task", "target.report_id": report_id}).to_list(None)
    assert len(auths) == 1 and auths[0]["outcome"] == "blocked"
    assert await db["tasks"].count_documents({"report_id": report_id}) == 0
