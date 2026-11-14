"""A10: the run over fakes of every module it calls (Story 1.7, card A10 "Done when").

I1 proves the same flow against the real modules on the Atlas Sandbox.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from dxp import pipeline
from tests.a10.conftest import (
    ANCHOR,
    OUT_OF_SCOPE_DX,
    RUN_ID,
    SCOPE_ID,
    SECOND,
    TEAM_ID,
    World,
    add_source,
    version_id_for,
)


def released_once(w: World) -> bool:
    return bool(w.admitted) and all(w.releases[a] == 1 for a in w.admitted) and len(w.releases) == len(w.admitted)


async def test_demo_scenario_blocked_claim_redraft_report_and_one_alert(world: World) -> None:
    await pipeline.run(RUN_ID)
    w = world
    file_decisions = [d for d in w.decisions if d["kind"] == "file_proposal" and "|draft" in d["target"]]
    # one blocked claim (draft 1), one redraft (draft 2) allowed
    assert [(d["target"].rsplit("|", 1)[1], d["outcome"]) for d in file_decisions] == [("draft1", "blocked"), ("draft2", "allowed")]
    assert file_decisions[0]["failed_check"] == "evidence_checks:claim_performed_or_results"
    # one report, filed from draft 2, naming the blocked draft's decision
    reports = list(w.db["reports"].docs.values())
    assert len(reports) == 1 and reports[0]["draft"] == 2
    assert reports[0]["blocked_draft_decision_id"] == file_decisions[0]["id"]
    # its proposals: the scope update filed, the FoundationOne CDx mention link blocked by check 2
    assert len(w.db["proposals"].docs) == 1
    change_decisions = [d for d in w.decisions if d["target"] in ("evidence_collection", "trials")]
    assert [(d["target"], d["outcome"], d["failed_check"]) for d in change_decisions] == [
        ("evidence_collection", "allowed", None), ("trials", "blocked", "team_scope")]
    assert reports[0]["memories_used"][0]["memory_id"] == "mem_m1"  # the drafter's memories reach the report
    # one alert through the fake sender; no ElevenLabs or HeyGen call
    assert len(w.slack) == 1 and w.slack[0]["report_id"] == reports[0]["_id"]
    assert w.media == []
    # every admission released exactly once; the run ends done
    assert released_once(w)
    assert w.run["status"] == "done"
    counts = w.run["counts"]
    assert counts["total"] == 1 and counts["done"] == 1 and counts.get("failed", 0) == 0
    assert counts["reports"] == 1 and counts["filed"] == 1
    assert counts["blocked"] == 2 and counts["allowed"] == 3  # draft2, scope update, slack
    assert w.run["active"] == []


async def test_one_admission_per_action_with_the_d22_item_keys(world: World) -> None:
    await pipeline.run(RUN_ID)
    report_id = next(iter(world.db["reports"].docs))
    keys = list(world.admitted.values())
    assert keys[0] == f"{ANCHOR}|file_proposal|-|{report_id}|draft1"
    assert keys[1] == f"{ANCHOR}|file_proposal|-|{report_id}|draft2"
    assert keys[2].startswith(f"{ANCHOR}|file_proposal|-|p_")  # scope update: "-" for the Diagnostic (V43)
    assert keys[3].startswith(f"{ANCHOR}|file_proposal|{OUT_OF_SCOPE_DX}|p_")
    assert keys[4] == f"{ANCHOR}|notify_slack|-|{report_id}"  # A10's own alert admission
    assert keys[2] != keys[3] and len(keys) == len(set(keys)) == 5
    # each draft and each change was gated under its own admission
    by_target = {d["target"]: d["admission_id"] for d in world.decisions}
    assert world.admitted[by_target[f"{report_id}|draft1"]] == keys[0]
    assert world.admitted[by_target[f"{report_id}|draft2"]] == keys[1]
    assert world.admitted[by_target["evidence_collection"]] == keys[2]
    assert world.admitted[by_target["trials"]] == keys[3]


def file_calls(w: World) -> list[dict[str, Any]]:
    return w.args("reports.file")


async def test_item5_each_draft_is_filed_on_its_own_and_draft1_is_gate_only(world: World) -> None:
    """(5) Probe: draft 1 must not go through the full reports.file. Each draft is its own
    reports.file(draft, ctx, final) call under its own admission; draft 1 is final=False with no
    updates, and nothing is written until the final draft's call."""
    import dxp.reports

    real_file = dxp.reports.file
    reports_before_call: list[int] = []

    async def spy(d: dict[str, Any], ctx: Any, final: bool = True) -> Any:
        reports_before_call.append(len(world.db["reports"].docs) + len(world.db["proposals"].docs))
        return await real_file(d, ctx, final)

    dxp.reports.file = spy
    await pipeline.run(RUN_ID)
    calls = file_calls(world)
    report_id = next(iter(world.db["reports"].docs))
    assert [(c["draft"], c["final"]) for c in calls] == [(1, False), (2, True)]
    assert "drafts" not in calls[0] and "drafts" not in calls[1]  # one draft per call
    assert "updates" not in calls[0] and calls[0]["memories_used"] == []  # non-final drafts carry no updates
    assert len(calls[1]["updates"]) == 2
    assert reports_before_call == [0, 0]  # the gate-only call wrote nothing
    # each draft under its own admission, keyed on its own target
    assert world.admitted[calls[0]["admission_id"]] == f"{ANCHOR}|file_proposal|-|{report_id}|draft1"
    assert world.admitted[calls[1]["admission_id"]] == f"{ANCHOR}|file_proposal|-|{report_id}|draft2"
    # draft 1's Decision is recorded and named on the report filed from draft 2
    draft1 = next(d for d in world.decisions if d["target"] == f"{report_id}|draft1")
    assert draft1["outcome"] == "blocked" and calls[1]["blocked_draft_decision_id"] == draft1["id"]
    assert released_once(world)


async def test_item5_a_single_draft_is_filed_final(world: World) -> None:
    world.with_memories = False  # no memories: draft 1 is the only and final draft
    world.draft1_text = "This study is recruiting."
    await pipeline.run(RUN_ID)
    assert [(c["draft"], c["final"]) for c in file_calls(world)] == [(1, True)]
    assert len(world.db["reports"].docs) == 1 and len(world.slack) == 1


async def test_update_shape_is_finding_id_and_change_with_its_admission(world: World) -> None:
    """The agreed update shape (#19/#24): [{finding_id, change{field, value, diagnostic_id, ...,
    admission_id}}], read from the final draft; each change keeps its own admission (D22)."""
    await pipeline.run(RUN_ID)
    final = file_calls(world)[-1]
    vid = version_id_for(ANCHOR)
    assert [set(u) for u in final["updates"]] == [{"finding_id", "change"}, {"finding_id", "change"}]
    assert [u["finding_id"] for u in final["updates"]] == [f"f_{vid}_record", f"f_{vid}_f1cdx"]
    for update in final["updates"]:
        change = update["change"]
        assert {"field", "value", "diagnostic_id", "admission_id"} <= set(change)
        assert "|file_proposal|" in world.admitted[change["admission_id"]]
    assert len({u["change"]["admission_id"] for u in final["updates"]}) == 2


async def test_item7_a10_is_the_only_alert_sender(world: World) -> None:
    """(7) Probe: notify must not defer to an alert reports.file may have sent. reports.file
    sends none; A10 dispatches the one notify_slack, after the final reports.file returns."""
    from dxp import identity

    report_id = identity.derive("rep_", RUN_ID, ANCHOR)
    # an existing notify_slack action for the report no longer suppresses A10's dispatch;
    # A09's derived action ID keeps a repeat to one post.
    world.db["actions"].docs["act_old"] = {"_id": "act_old", "kind": "notify_slack", "target": {"report_id": report_id}}
    await pipeline.run(RUN_ID)
    assert len(world.args("actions.dispatch")) == 1 and len(world.slack) == 1
    assert world.admitted[world.slack[0]["admission_id"]] == f"{ANCHOR}|notify_slack|-|{report_id}"
    names = world.names()
    last_file = max(i for i, n in enumerate(names) if n == "reports.file")
    assert file_calls(world)[-1]["final"] is True and last_file < names.index("actions.dispatch")


async def test_item4_a_refused_change_admission_files_nothing(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    """(4) Probe: a stop lands after the draft admissions and before the change admissions.
    Every admission held is released, no draft is gated, no report is filed without its update,
    no alert is sent and the version stays unprocessed, so a resumed run retries the item."""
    import dxp.runs

    real_admit = dxp.runs.admit

    async def admit(run_id: str, key: str) -> Any:
        if "|p_" in key and world.run["status"] == "running":
            world.run["status"] = "stopping"  # POST /runs/<id>/stop between the admissions
        return await real_admit(run_id, key)

    monkeypatch.setattr(dxp.runs, "admit", admit)
    await pipeline.run(RUN_ID)
    assert world.refused and world.refused[0].startswith(f"{ANCHOR}|file_proposal|-|p_")
    assert "reports.file" not in world.names() and world.decisions == []
    assert world.db["reports"].docs == {} and world.db["proposals"].docs == {}
    assert world.slack == [] and "actions.dispatch" not in world.names()
    assert released_once(world) and len(world.admitted) == 2  # the two draft admissions, released once
    assert "processed" not in world.db["source_items"].docs[ANCHOR]
    assert world.run["status"] == "stopped"


async def test_item6_processed_only_after_the_alert_outcome(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    """(6) Probe: the alert raises. The version must stay unprocessed so a rerun sends it."""
    import dxp.actions

    real_dispatch = dxp.actions.dispatch
    attempts: list[int] = []

    async def dispatch(action: Any, ctx: Any) -> Any:
        attempts.append(1)
        if len(attempts) == 1:
            world.calls.append(("actions.dispatch", action))
            raise RuntimeError("slack down")
        return await real_dispatch(action, ctx)

    monkeypatch.setattr(dxp.actions, "dispatch", dispatch)
    await pipeline.run(RUN_ID)
    assert world.run["counts"]["failed"] == 1
    assert world.run["failures"] == [{"source_ref": ANCHOR, "error": "notify: RuntimeError"}]
    assert "processed" not in world.db["source_items"].docs[ANCHOR]
    assert released_once(world)

    # the rerun is not skipped: it sends the alert, then marks the version processed
    world.run["status"] = "running"
    await pipeline.run(RUN_ID)
    assert len(world.slack) == 1
    assert list(world.db["source_items"].docs[ANCHOR]["processed"][SCOPE_ID]) == [version_id_for(ANCHOR)]


async def test_item6_mark_processed_runs_after_the_alert(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    from dxp.pipeline import progress

    real_mark = progress.mark_processed

    async def mark(*args: Any) -> None:
        world.calls.append(("progress.mark_processed", args[0]))
        await real_mark(*args)

    monkeypatch.setattr(progress, "mark_processed", mark)
    await pipeline.run(RUN_ID)
    names = world.names()
    assert names.index("actions.dispatch") < names.index("progress.mark_processed")


async def test_the_alert_carries_the_report_and_no_diagnostic(world: World) -> None:
    await pipeline.run(RUN_ID)
    report_id = next(iter(world.db["reports"].docs))
    action = world.slack[0]["action"]
    assert action.kind == "notify_slack" and action.destination == "slack:#all-mango-db-hackathon"
    assert action.target.diagnostic_id is None and action.inputs["diagnostic_ids"] == []
    assert action.evidence_ref.version_id == version_id_for(ANCHOR)
    assert world.admitted[world.slack[0]["admission_id"]] == f"{ANCHOR}|notify_slack|-|{report_id}"
    assert released_once(world)


async def test_version_id_is_carried_through_every_step(world: World) -> None:
    await pipeline.run(RUN_ID)
    vid = version_id_for(ANCHOR)
    assert world.args("llm.extract")[0]["item"]["version_id"] == vid
    assert all(f["version_id"] == vid for f in world.db["findings"].docs.values())
    relate = world.args("reports.relate")[0]
    assert relate["new"]["version_id"] == vid and relate["related"]["version_id"] == "sv_prior"
    drafted = world.args("reports.draft")[0]
    assert drafted["item"]["version_id"] == vid and all(f["version_id"] == vid for f in drafted["findings"])
    assert all(d["version_id"] == vid for d in world.args("reports.file"))
    assert world.args("reports.draft")[0]["item"]["attempt"] == 0
    assert next(iter(world.db["reports"].docs.values()))["version_id"] == vid
    processed = world.db["source_items"].docs[ANCHOR]["processed"][SCOPE_ID]
    assert list(processed) == [vid] and isinstance(processed[vid], datetime)  # processed_at


async def test_order_of_steps_recovery_first_and_task_hooks_last(world: World) -> None:
    await pipeline.run(RUN_ID)
    names = world.names()
    assert names[0] == "runs.context" and world.args("runs.context")[0] == (RUN_ID, "test-dxp-agent-key")
    assert names[1] == "ledger.recover_applying"
    item_steps = ["discovery.scan", "llm.extract", "llm.check", "retrieval.related", "memory.retrieve",
                  "reports.relate", "reports.draft", "reports.file", "actions.dispatch", "runs.finish"]
    positions = [names.index(n) for n in item_steps]
    assert positions == sorted(positions)
    assert names[-2:] == ["tasks.recover_authorisations", "tasks.dispatch_next"]
    assert names.index("runs.finish") < names.index("tasks.dispatch_next")


async def test_extraction_gets_the_seeded_trade_names_only(world: World) -> None:
    await pipeline.run(RUN_ID)
    aliases = world.args("llm.extract")[0]["aliases"]
    assert aliases == ["FoundationOne CDx", "guardant360 cdx"]  # the live-created alias is left out


async def test_memories_are_asked_for_by_team_and_claim_kind(world: World) -> None:
    await pipeline.run(RUN_ID)
    assert world.args("memory.retrieve")[0] == {"team_id": TEAM_ID, "tags": {"claim_kind": "claim_performed_or_results"}}
    assert world.args("retrieval.related")[0] == {"scope_id": SCOPE_ID, "k": 5, "exclude": [ANCHOR]}
    assert world.args("reports.draft")[0]["memories"][0]["id"] == "mem_m1"


async def test_a_blocked_report_redrafts_once_then_files_nothing(world: World) -> None:
    world.draft2_text = "It showed detection of EGFR."
    await pipeline.run(RUN_ID)
    report_id_targets = [d["target"].split("|", 1)[1] for d in world.decisions if "|draft" in d["target"]]
    assert report_id_targets == ["draft1", "draft2", "draft1.r1", "draft2.r1"]
    assert [a["item"]["attempt"] for a in world.args("reports.draft")] == [0, 1]
    assert world.db["reports"].docs == {} and world.db["proposals"].docs == {}
    assert world.slack == [] and "actions.dispatch" not in world.names()
    assert released_once(world)
    assert world.run["status"] == "done" and world.run["counts"]["blocked"] == 4
    assert "processed" not in world.db["source_items"].docs[ANCHOR]


async def test_a_redraft_after_a_block_can_be_filed(world: World) -> None:
    world.draft2_text = "It showed detection of EGFR."
    world.redraft_text = "This study is recruiting; no results posted."
    await pipeline.run(RUN_ID)
    report = next(iter(world.db["reports"].docs.values()))
    filed = [d for d in world.decisions if d["target"].endswith("|draft2.r1")]
    assert filed and filed[0]["outcome"] == "allowed" and report["status"] == "pending"
    assert len(world.slack) == 1 and released_once(world)


async def test_draft_one_allowed_still_files_draft_two(world: World) -> None:
    world.draft1_text = "This study is recruiting."
    await pipeline.run(RUN_ID)
    report = next(iter(world.db["reports"].docs.values()))
    assert report["draft"] == 2 and report["blocked_draft_decision_id"] is None
    assert len(world.slack) == 1


async def test_a_forced_item_failure_fails_that_item_only(world: World) -> None:
    world.scan_refs = [ANCHOR, SECOND]
    world.extract_fail = {SECOND}
    await pipeline.run(RUN_ID)
    run = world.run
    assert run["status"] == "done"
    assert run["counts"]["done"] == 1 and run["counts"]["failed"] == 1 and run["counts"]["total"] == 2
    assert run["failures"] == [{"source_ref": SECOND, "error": "extract: RuntimeError"}]
    assert "model down" not in str(run["failures"])  # codes, never messages or source text
    assert len(world.slack) == 1
    assert released_once(world)


async def test_items_keep_the_scan_order_one_at_a_time_with_pace(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("dxp.pipeline.config.pace_seconds", lambda: 0.001)
    world.scan_refs = [ANCHOR, SECOND]
    await pipeline.run(RUN_ID)
    assert [a["item"]["source_ref"] for a in world.args("llm.extract")] == [ANCHOR, SECOND]
    # one at a time: the anchor's alert went out before the second item was extracted
    names = world.names()
    first_dispatch = names.index("actions.dispatch")
    second_extract = [i for i, n in enumerate(names) if n == "llm.extract"][1]
    assert first_dispatch < second_extract


async def test_stop_mid_run_drains_and_settles(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("dxp.pipeline.config.pace_seconds", lambda: 0.001)
    world.scan_refs = [ANCHOR, SECOND]
    world.stop_after = ANCHOR
    await pipeline.run(RUN_ID)
    assert [a["item"]["source_ref"] for a in world.args("llm.extract")] == [ANCHOR]
    assert world.run["status"] == "stopped"
    assert released_once(world)
    assert world.names()[-1] == "tasks.dispatch_next"


async def test_a_refused_admission_attempts_nothing(world: World) -> None:
    async def scan(scope_id: str, ctx: Any) -> list[str]:
        world.run["status"] = "stopping"  # stop lands right after the scan
        return [ANCHOR]

    import dxp.discovery

    dxp.discovery.scan = scan  # restored by the world fixture's monkeypatch
    await pipeline.run(RUN_ID)
    assert "reports.file" not in world.names() and world.slack == []
    assert world.run["status"] == "stopped"


async def test_admission_refused_at_filing_files_nothing(world: World) -> None:
    import dxp.reports

    real_draft = dxp.reports.draft

    async def draft(*args: Any) -> Any:
        out = await real_draft(*args)
        world.run["status"] = "stopping"
        return out

    dxp.reports.draft = draft
    await pipeline.run(RUN_ID)
    assert world.refused and "reports.file" not in world.names()
    assert world.run["counts"]["not_admitted"] == 1
    assert world.run["status"] == "stopped"


async def test_an_already_processed_version_is_skipped(world: World) -> None:
    add_source(world.db, ANCHOR, processed=True)
    await pipeline.run(RUN_ID)
    assert "llm.extract" not in world.names()
    assert world.run["status"] == "done" and world.run["counts"]["done"] == 1


async def test_a_not_relevant_item_is_done_with_nothing_filed(world: World) -> None:
    import dxp.llm

    async def extract(item: dict[str, Any], aliases: Any = None) -> dict[str, Any]:
        return {"status": "not_relevant", "findings": []}

    dxp.llm.extract = extract
    await pipeline.run(RUN_ID)
    assert world.run["counts"]["done"] == 1 and world.slack == [] and "reports.draft" not in world.names()


async def test_an_nct_set_processes_one_setup_item_without_a_scan(world: World) -> None:
    world.run["set"] = "nct:NCT00000002"
    await pipeline.run(RUN_ID)
    assert "discovery.scan" not in world.names()
    assert [a["item"]["source_ref"] for a in world.args("llm.extract")] == [SECOND]
    assert world.run["status"] == "done"


async def test_an_unrecoverable_error_fails_the_run_and_still_dispatches(world: World) -> None:
    world.scan_error = RuntimeError("source down")
    await pipeline.run(RUN_ID)
    assert world.run["status"] == "failed" and world.run["error"] == "RuntimeError"
    assert "runs.finish" not in world.names()
    assert world.names()[-2:] == ["tasks.recover_authorisations", "tasks.dispatch_next"]
    assert world.args("runs.fail") == [(RUN_ID, "RuntimeError")]
    assert world.events == []  # type: ignore[attr-defined]  # the pipeline writes no run event itself


async def test_a_task_run_with_task_run_off_fails_and_leaves_the_task_authorised(world: World) -> None:
    world.run["set"] = "task:task_0123456789abcdef"
    world.run["task_id"] = "task_0123456789abcdef"
    world.db["tasks"].docs["task_0123456789abcdef"] = {"_id": "task_0123456789abcdef", "status": "authorised"}
    await pipeline.run(RUN_ID)
    assert "tasks.run" not in world.names() and "llm.extract" not in world.names()
    assert "runs.finish" not in world.names()
    assert world.args("runs.fail") == [(RUN_ID, "task_run is off")]
    assert world.run["status"] == "failed" and world.run["error"] == "task_run is off"
    assert world.db["tasks"].docs["task_0123456789abcdef"]["status"] == "authorised"
    assert world.names()[-2:] == ["tasks.recover_authorisations", "tasks.dispatch_next"]


async def test_a_task_set_is_handed_to_tasks_run_with_task_run_on(world: World, features: Any) -> None:
    features("task_run")
    world.run["set"] = "task:task_0123456789abcdef"
    world.run["task_id"] = "task_0123456789abcdef"
    await pipeline.run(RUN_ID)
    assert world.args("tasks.run") == ["task_0123456789abcdef"]
    assert world.run["status"] == "done"


async def test_dispatch_next_starts_the_next_run_in_this_call(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    import dxp.tasks

    started: list[str] = []

    async def dispatch_next(start: Any) -> None:
        if not started:
            started.append("run_next")
            world.db["runs"].docs["run_next"] = {"_id": "run_next", "status": "running", "set": "nct:NCT00000002",
                                                 "scope_id": SCOPE_ID, "team_id": TEAM_ID, "counts": {}}
            await start("run_next")

    monkeypatch.setattr(dxp.tasks, "dispatch_next", dispatch_next)
    await pipeline.run(RUN_ID)
    assert world.db["runs"].docs["run_next"]["status"] == "done"
    assert [a[0] for a in world.args("runs.context")] == [RUN_ID, "run_next"]


async def test_hook_failures_never_mask_each_other(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    import dxp.tasks

    async def boom() -> None:
        raise RuntimeError("x")

    monkeypatch.setattr(dxp.tasks, "recover_authorisations", boom)
    await pipeline.run(RUN_ID)
    assert world.names()[-1] == "tasks.dispatch_next" and world.run["status"] == "done"


async def test_the_pipeline_never_writes_runs_directly(world: World) -> None:
    """Only Governance writes `runs` (spine layer table): progress goes through runs.record_progress."""
    import copy

    before = copy.deepcopy(world.db["runs"].docs)
    world.scan_refs = [ANCHOR, SECOND]
    world.extract_fail = {SECOND}
    calls: list[Any] = []
    real_update = world.db["runs"].update_one

    async def spy(*args: Any, **kwargs: Any) -> Any:
        calls.append(args)
        return await real_update(*args, **kwargs)

    world.db["runs"].update_one = spy  # type: ignore[method-assign]
    await pipeline.run(RUN_ID)
    assert calls == [] and before  # every change came through the faked runs functions
    assert "runs.record_progress" in world.names()


async def test_a_blocked_alert_is_a_blocked_step_not_a_failure(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    import dxp.actions

    class ActionBlocked(Exception):
        def __init__(self, decision: dict[str, Any]) -> None:
            super().__init__("blocked")
            self.decision = decision

    async def dispatch(action: Any, ctx: Any) -> Any:
        world.calls.append(("actions.dispatch", action))
        raise ActionBlocked({"_id": "dec_slack_blocked"})

    monkeypatch.setattr(dxp.actions, "dispatch", dispatch)
    monkeypatch.setattr(dxp.actions, "ActionBlocked", ActionBlocked, raising=False)
    from dxp.pipeline import item as item_module

    results: list[Any] = []
    real_process = item_module.process

    async def process(ref: str, info: Any) -> Any:
        out = await real_process(ref, info)
        results.append(out)
        return out

    monkeypatch.setattr(item_module, "process", process)
    await pipeline.run(RUN_ID)
    run = world.run
    assert run["status"] == "done" and run["counts"]["done"] == 1 and run["counts"].get("failed", 0) == 0
    assert run["failures"] == [] and world.slack == []
    assert results[0].alert == {"status": "blocked", "decision_id": "dec_slack_blocked"}
    assert len(world.db["reports"].docs) == 1  # the report stays filed and pending
    assert released_once(world)


@pytest.mark.parametrize("error", ["SenderNotConfigured", "ReportNotFound"])
async def test_an_unsent_alert_is_non_fatal_with_a_failure_line(world: World, monkeypatch: pytest.MonkeyPatch, error: str) -> None:
    import dxp.actions

    exc_class = type(error, (Exception,), {})

    async def dispatch(action: Any, ctx: Any) -> Any:
        world.calls.append(("actions.dispatch", action))
        raise exc_class("not sent")

    monkeypatch.setattr(dxp.actions, "dispatch", dispatch)
    monkeypatch.setattr(dxp.actions, error, exc_class, raising=False)
    await pipeline.run(RUN_ID)
    run = world.run
    assert run["status"] == "done" and run["counts"]["done"] == 1 and run["counts"].get("failed", 0) == 0
    assert run["failures"] == [{"source_ref": ANCHOR, "error": f"notify: {error}"}]
    assert len(world.db["reports"].docs) == 1 and released_once(world)
    # A10's dispatch came after reports.file returned (the report was committed first)
    names = world.names()
    assert names.index("reports.file") < max(i for i, n in enumerate(names) if n == "actions.dispatch")


async def test_an_alert_for_a_report_with_a_diagnostic_uses_it_in_the_admission_key(world: World) -> None:
    world.link_dx = "dx_g360"  # an in-scope link: filed, so the stored report names it
    await pipeline.run(RUN_ID)
    report = next(iter(world.db["reports"].docs.values()))
    assert report["diagnostic_ids"] == ["dx_g360"]
    assert list(world.admitted.values())[-1] == f"{ANCHOR}|notify_slack|dx_g360|{report['_id']}"
    assert world.slack[0]["action"].target.diagnostic_id == "dx_g360"
