"""tasks.run (Story 10.9): claim, gated search and filing, the limit, stop, and the flag."""

from __future__ import annotations

from dxp import tasks

from .conftest import TaskWorld, ref, run_mod


async def test_no_results_answers_with_query_count_and_limit(tw: TaskWorld) -> None:
    tw.add_items({ref(1): False, ref(2): False, ref(3): False})
    task = await tasks.run(tw.task_id)
    assert task.status == "done"
    result = tw.task()["result"]
    assert result["answer"] == "No matching results found among the records searched"
    assert result["with_posted_results"] == []
    assert result["searched_count"] == 3 and result["limit"] == 5
    assert result["query"]["query.cond"] == "NSCLC" and result["query"]["params"]["stage"] == "early"
    assert tw.searches == [("scope_plasma_ctdna_nsclc", 5)]
    assert [e["status"] for e in tw.events("task_status_changed")] == ["running", "done"]
    assert tw.db["reports"].docs[tw.report_id]["related"] == []


async def test_second_worker_exits_without_acting(tw: TaskWorld) -> None:
    tw.add_items({ref(1): True})
    tw.task()["status"] = "running"  # the first worker owns it
    task = await tasks.run(tw.task_id)
    assert task.status == "running"
    assert tw.searches == [] and tw.events("task_status_changed") == []
    assert tw.db["decisions"].docs == {} and tw.task()["result"] is None


async def test_findings_are_pending_and_the_sixth_is_blocked_by_the_real_gate(tw: TaskWorld, quote_checks) -> None:
    found = {ref(n): True for n in range(1, 7)}
    found[ref(7)] = False
    tw.add_items(found)
    task = await tasks.run(tw.task_id)
    assert task.status == "blocked"
    result = tw.task()["result"]
    assert result["with_posted_results"] == [f"NCT{n:08d}" for n in range(1, 6)]
    assert result["searched_count"] == 7 and result["limit"] == 5
    (blocked,) = result["blocked"]
    assert blocked["source_ref"] == ref(6) and blocked["failed_check"] == "team_scope"
    decisions = sorted(tw.db["decisions"].docs.values(), key=lambda d: d["inputs"]["source_ref"])
    assert [d["outcome"] for d in decisions] == ["allowed"] * 5 + ["blocked"]
    assert all(d["kind"] == "file_related_evidence" and d["grant_id"] == tw.grant_id for d in decisions)
    # pending related evidence on the report, never accepted knowledge
    related = tw.db["reports"].docs[tw.report_id]["related"]
    assert len(related) == 5 and {r["status"] for r in related} == {"pending"}
    assert {r["origin"] for r in related} == {f"task:{tw.task_id}"}
    assert tw.db["proposals"].docs == {} and tw.db["reports"].docs[tw.report_id]["status"] == "accepted"
    # allowed actions settled through gate.mark_action; every admission released
    assert {a["status"] for a in tw.db["actions"].docs.values()} == {"done"}
    assert {a["status"] for a in tw.db["admissions"].docs.values()} == {"released"}


async def test_add_related_without_checks_is_blocked(tw: TaskWorld) -> None:
    """Without the A19+A20 fix the real gate blocks every filing (evidence_checks): the task ends
    blocked, records why, and files nothing (fails closed)."""
    tw.add_items({ref(1): True})
    task = await tasks.run(tw.task_id)
    assert task.status == "blocked"
    (blocked,) = tw.task()["result"]["blocked"]
    assert blocked["failed_check"] == "evidence_checks"
    assert tw.db["reports"].docs[tw.report_id]["related"] == []


async def test_out_of_scope_finding_is_blocked_and_recorded(tw: TaskWorld, quote_checks) -> None:
    tw.add_items({ref(1): True}, scope_ids=["scope_other"])
    task = await tasks.run(tw.task_id)
    assert task.status == "blocked"
    (blocked,) = tw.task()["result"]["blocked"]
    assert blocked["source_ref"] == ref(1) and blocked["failed_check"] == "team_scope"
    assert tw.db["reports"].docs[tw.report_id]["related"] == []


async def test_stop_on_the_task_run_ends_stopped(tw: TaskWorld) -> None:
    tw.add_items({ref(1): True, ref(2): True})

    def stop() -> None:  # runs.stop: running -> stopping, while the search is in flight
        tw.run_doc()["status"] = "stopping"

    tw.on_search = stop
    task = await tasks.run(tw.task_id)
    assert task.status == "stopped"
    assert tw.db["reports"].docs[tw.report_id]["related"] == []
    assert tw.db["admissions"].docs == {}
    assert [e["status"] for e in tw.events("task_status_changed")] == ["running", "stopped"]


async def test_stopped_before_start_does_not_search(tw: TaskWorld) -> None:
    tw.run_doc()["status"] = "stopped"
    task = await tasks.run(tw.task_id)
    assert task.status == "stopped" and tw.searches == []


async def test_blocked_search_ends_blocked(tw: TaskWorld) -> None:
    tw.outcome.status = "blocked"
    tw.outcome.decision_id = "dec_0000000000000001"
    task = await tasks.run(tw.task_id)
    assert task.status == "blocked"
    result = tw.task()["result"]
    assert result["searched_count"] == 0 and result["limit"] == 5
    assert result["blocked"] == [{"step": "search_source", "decision_id": "dec_0000000000000001"}]


async def test_search_error_ends_failed(tw: TaskWorld) -> None:
    def boom() -> None:
        raise RuntimeError("network")

    tw.on_search = boom
    task = await tasks.run(tw.task_id)
    assert task.status == "failed"


async def test_flag_off_does_nothing(tw: TaskWorld, monkeypatch) -> None:
    monkeypatch.setenv("DXP_FEATURES", "")
    tw.add_items({ref(1): True})
    task = await tasks.run(tw.task_id)
    assert task.status == "queued" and tw.task()["status"] == "queued"
    assert tw.searches == [] and tw.events("task_status_changed") == []


def test_limit_never_exceeds_five() -> None:
    assert run_mod.limit_of({"params": {"max": 9}}) == 5
    assert run_mod.limit_of({"params": {"max": 3}}) == 3
    assert run_mod.limit_of({}) == 5
