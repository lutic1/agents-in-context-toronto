"""Runs, admissions, stop and sweep against the Atlas Sandbox (Stories 9.1, 9.5; AD-17, AD-21, V38).

Skipped with a stated reason when MONGODB_URI is unset (backend/tests/conftest.py). Runs in the
session's own `dxp_test_<hex>` database, never `dxp`.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from dxp import runs
from dxp.api.app import create_app
from dxp.api.errors import ApiError
from dxp.identity import derive

from .conftest import AGENT, PS_VERSION, SAM, SCOPE_ID, TASK_GRANT_ID, TASK_ID, TEAM_ID, VLAD, agent_grant

pytestmark = pytest.mark.atlas

TASK_RUN_ID = derive("run_", TASK_ID)
REPORT_ID = derive("rep_", "run_fixture", "clinicaltrials.gov:NCT04712877")


async def add_task(db, task_id: str = TASK_ID, status: str = "queued") -> None:
    await db["tasks"].insert_one({
        "_id": task_id, "report_id": REPORT_ID, "kind": "search_related", "question": "Which early-stage trials posted results?",
        "params": {"condition": "non-small cell lung cancer", "max": 5}, "grant_id": TASK_GRANT_ID, "grant_version": 1,
        "status": status, "authorised_by_decision_id": derive("dec_", "-", "authorise_task", "-", task_id),
        "created_at": datetime.now(UTC),
    }, bypass_document_validation=True)


# --- Story 9.1: start, identity, 403/409 -------------------------------------------------------


async def test_start_pins_identity_grant_and_policy_set(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    stored = await clean["runs"].find_one({"_id": run.id})
    assert run.id.startswith("run_") and run.status == "running"
    assert (run.agent, run.initiated_by) == ("dxp-curator", "sam")
    assert (run.grant_id, run.grant_version, run.policy_set_version) == ("lbdx", 1, PS_VERSION)
    assert (run.team_id, run.scope_id, run.kind, run.mode) == (TEAM_ID, SCOPE_ID, "discover", "live")
    assert stored["status"] == "running" and stored["started_at"] is not None
    event = await clean["events"].find_one({"type": "run_status_changed", "run_id": run.id, "status": "running"})
    assert event is not None and event["stamp"]["run_id"] == run.id and event["stamp"]["principal"] == "dxp-curator"


async def test_nct_set_is_an_items_run(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "nct:NCT05715229")
    assert run.kind == "items" and run.set == "nct:NCT05715229"


@pytest.mark.parametrize(("grant", "code"), [
    (agent_grant(version=2, status="revoked"), "grant_not_active"),
    (agent_grant(expires_in=timedelta(minutes=-1)), "grant_not_active"),
    (agent_grant(startable_by=["luis"]), "not_startable_by_caller"),
])
async def test_403_creates_no_run(clean, authority, grant, code) -> None:
    authority.grants["lbdx"] = grant
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "lbdx", "discover")
    assert caught.value.status_code == 403 and caught.value.code == code
    assert await clean["runs"].count_documents({}) == 0


async def test_unknown_grant_and_task_grant_on_discover_are_403(clean, authority) -> None:
    for grant_id in ("nope", TASK_GRANT_ID):
        with pytest.raises(ApiError) as caught:
            await runs.start(SAM, grant_id, "discover")
        assert caught.value.status_code == 403
    assert await clean["runs"].count_documents({}) == 0


async def test_409_while_a_run_is_running_or_stopping(clean, authority) -> None:
    first = await runs.start(SAM, "lbdx", "discover")
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "lbdx", "discover")
    assert caught.value.status_code == 409
    await runs.admit(first.id, "scope|search_source|-|x")
    await runs.stop(first.id)  # stopping while the admission is held
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "lbdx", "discover")
    assert caught.value.status_code == 409


async def test_a_stalled_run_does_not_block_a_new_start(clean, authority) -> None:
    first = await runs.start(SAM, "lbdx", "discover")
    await clean["runs"].update_one({"_id": first.id}, {"$set": {"progress_at": datetime.now(UTC) - timedelta(minutes=11)}})
    second = await runs.start(SAM, "lbdx", "discover")
    assert second.id != first.id


async def test_concurrent_discover_starts_leave_one_run(clean, authority) -> None:
    results = await asyncio.gather(*(runs.start(SAM, "lbdx", "discover") for _ in range(6)), return_exceptions=True)
    started = [r for r in results if not isinstance(r, Exception)]
    refused = [r for r in results if isinstance(r, ApiError) and r.status_code == 409]
    assert len(started) == 1 and len(refused) == 5
    assert await clean["runs"].count_documents({"status": "running"}) == 1


# --- V38: the task's derived run ------------------------------------------------------------------


async def test_task_run_is_insert_if_absent_on_its_derived_id(clean, authority) -> None:
    await add_task(clean)
    results = await asyncio.gather(*(
        runs.start_if_absent(SAM, TASK_GRANT_ID, f"task:{TASK_ID}", run_id=TASK_RUN_ID) for _ in range(5)
    ))
    assert sum(1 for _, inserted in results if inserted) == 1  # only one caller starts the worker
    assert {run.id for run, _ in results} == {TASK_RUN_ID}
    assert await clean["runs"].count_documents({}) == 1
    stored = await clean["runs"].find_one({"_id": TASK_RUN_ID})
    assert stored["kind"] == "task" and stored["task_id"] == TASK_ID
    assert stored["grant_id"] == TASK_GRANT_ID and stored["initiated_by"] == "sam" and stored["agent"] == "dxp-curator"
    assert stored["cause"] == {"task_id": TASK_ID, "report_id": REPORT_ID}
    again = await runs.start(SAM, TASK_GRANT_ID, f"task:{TASK_ID}", run_id=TASK_RUN_ID)
    assert again.id == TASK_RUN_ID


async def test_task_set_under_the_agent_grant_is_403(clean, authority) -> None:
    await add_task(clean)
    with pytest.raises(ApiError) as caught:
        await runs.start(SAM, "lbdx", f"task:{TASK_ID}", run_id=TASK_RUN_ID)
    assert caught.value.status_code == 403


# --- Story 9.5: admissions, stop, settle, finish, sweep ------------------------------------------


async def test_admit_release_settle_and_stop(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    adm = await runs.admit(run.id, "clinicaltrials.gov:NCT04712877|file_proposal|-|rep_1")
    assert adm is not None and adm.status == "admitted" and adm.id == derive("adm_", run.id, adm.item_key)
    assert adm.expires_at - adm.admitted_at == timedelta(minutes=10)
    assert (await runs.admit(run.id, adm.item_key)).id == adm.id  # one admission per action
    assert (await runs.get_run(run.id)).in_flight == 1

    stopping = await runs.stop(run.id)
    assert stopping.status == "stopping" and stopping.in_flight == 1  # in flight, still finishing
    assert await runs.admit(run.id, "x|search_source|-|-") is None  # nothing new after stop
    assert (await clean["runs"].find_one({"_id": run.id}))["counts"]["not_admitted"] == 1

    await runs.release(adm.id)
    stopped = await runs.get_run(run.id)
    assert stopped.status == "stopped" and stopped.in_flight == 0 and stopped.stopped_at is not None
    await runs.release(adm.id)  # a second release does nothing
    assert (await clean["admissions"].find_one({"_id": adm.id}))["status"] == "released"
    statuses = [e["status"] async for e in clean["events"].find({"run_id": run.id, "type": "run_status_changed"}).sort("_id", 1)]
    assert statuses == ["running", "stopping", "stopped"]


async def test_stop_of_a_finished_run_changes_nothing(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    await runs.finish(run.id)
    done = await runs.get_run(run.id)
    assert done.status == "done" and done.finished_at is not None
    again = await runs.stop(run.id)
    assert again.status == "done" and again.stopping_at is None
    with pytest.raises(ApiError) as caught:
        await runs.stop("run_missing")
    assert caught.value.status_code == 404


async def test_settle_never_ends_a_running_run_and_finish_waits(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    await runs.settle(run.id)
    assert (await runs.get_run(run.id)).status == "running"
    adm = await runs.admit(run.id, "a|search_source|-|-")
    await runs.finish(run.id)
    assert (await runs.get_run(run.id)).status == "running"  # an admission is still held
    await runs.release(adm.id)
    await runs.finish(run.id)
    assert (await runs.get_run(run.id)).status == "done"


async def test_finish_after_a_stop_settles_instead(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    adm = await runs.admit(run.id, "a|search_source|-|-")
    await runs.stop(run.id)
    await runs.release(adm.id)
    await runs.finish(run.id)
    assert (await runs.get_run(run.id)).status == "stopped"


async def test_concurrent_stop_and_admissions_never_admit_after_the_stop(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    keys = [f"item{i}|file_proposal|-|-" for i in range(30)]
    results = await asyncio.gather(runs.stop(run.id), *(runs.admit(run.id, k) for k in keys))
    admitted = [a for a in results[1:] if a is not None]
    assert await clean["admissions"].count_documents({"run_id": run.id}) == len(admitted)
    after = await asyncio.gather(*(runs.admit(run.id, f"late{i}|file_proposal|-|-") for i in range(10)))
    assert all(a is None for a in after)
    state = await runs.get_run(run.id)
    assert state.in_flight == len(admitted)
    assert state.status == ("stopping" if admitted else "stopped")
    for a in admitted:
        await runs.release(a.id)
    assert (await runs.get_run(run.id)).status == "stopped"


async def test_sweep_abandons_expired_admissions_and_changes_no_action(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    in_flight = await runs.admit(run.id, "rep_1|notify_slack|-|rep_1")
    never_sent = await runs.admit(run.id, "rep_2|notify_slack|-|rep_2")
    fresh = await runs.admit(run.id, "rep_3|notify_slack|-|rep_3")
    past = datetime.now(UTC) - timedelta(minutes=1)
    await clean["admissions"].update_many({"_id": {"$in": [in_flight.id, never_sent.id]}}, {"$set": {"expires_at": past}})
    stamp = (await runs.stamp(run.id)).model_dump()
    now = datetime.now(UTC)
    await clean["actions"].insert_many([
        {"_id": "act_0000000000000001", "decision_id": "dec_0000000000000001", "admission_id": in_flight.id,
         "run_id": run.id, "kind": "notify_slack", "destination": "slack:#all-mango-db-hackathon",
         "stamp": stamp, "status": "dispatching", "proposed_at": now},
        {"_id": "act_0000000000000002", "decision_id": "dec_0000000000000002", "admission_id": never_sent.id,
         "run_id": run.id, "kind": "notify_slack", "destination": "slack:#all-mango-db-hackathon",
         "stamp": stamp, "status": "queued", "proposed_at": now},
    ])
    held = await runs.sweep(run.id)
    assert {(h["action_id"], h["status"]) for h in held} == {("act_0000000000000001", "dispatching"),
                                                             ("act_0000000000000002", "queued")}
    assert {a["status"] async for a in clean["actions"].find({"run_id": run.id})} == {"dispatching", "queued"}
    assert (await clean["admissions"].find_one({"_id": in_flight.id}))["status"] == "abandoned"
    assert (await clean["admissions"].find_one({"_id": fresh.id}))["status"] == "admitted"
    assert await runs.sweep(run.id) == []  # a second sweep finds nothing


# --- AD-17: the worker key -------------------------------------------------------------------------


async def test_context_resolves_only_the_runs_agent(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    ctx = await runs.context(run.id, "key-agent")
    assert ctx.principal.id == AGENT.id and ctx.run_id == run.id
    assert ctx.stamp.kind == "run" and ctx.stamp.run_id == run.id and ctx.stamp.initiated_by == "sam"
    assert ctx.grant_version == ctx.run_grant_version == 1 and ctx.policy_set_version == PS_VERSION
    for key, status in (("key-sam", 403), ("nope", 401)):
        with pytest.raises(ApiError) as caught:
            await runs.context(run.id, key)
        assert caught.value.status_code == status


# --- the routes, in the same event loop as the database ------------------------------------------


@pytest.fixture
async def client(fake_run_function):
    app = create_app(fake_run_function)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://dxp.test") as http:
        http.spawned = fake_run_function.spawned  # type: ignore[attr-defined]
        yield http


H = {"X-DxP-Key": "key-sam"}


async def test_routes_start_get_list_and_stop(clean, authority, client) -> None:
    created = await client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "discover"}, headers=H)
    assert created.status_code == 200, created.text
    run_id = created.json()["id"]
    assert client.spawned == [run_id]
    conflict = await client.post("/api/v1/runs", json={"grant_id": "lbdx", "set": "discover"}, headers=H)
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "run_active"
    refused = await client.post("/api/v1/runs", json={"grant_id": TASK_GRANT_ID, "set": f"task:{TASK_ID}"}, headers=H)
    assert refused.status_code == 403
    assert await clean["runs"].count_documents({}) == 1

    got = await client.get(f"/api/v1/runs/{run_id}", headers=H)
    assert got.status_code == 200 and got.json()["status"] == "running"
    listed = await client.get("/api/v1/runs", headers=H)
    assert [r["id"] for r in listed.json()["items"]] == [run_id]
    assert (await client.get("/api/v1/runs/run_missing", headers=H)).status_code == 404

    vlad = await client.post(f"/api/v1/runs/{run_id}/stop", headers={"X-DxP-Key": "key-vlad"})
    assert vlad.status_code == 403
    stopped = await client.post(f"/api/v1/runs/{run_id}/stop", headers=H)
    assert stopped.status_code == 200 and stopped.json()["status"] == "stopped"


async def test_reconciling_is_read_time_only(clean, authority, client) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    adm = await runs.admit(run.id, "rep_1|notify_slack|-|rep_1")
    await clean["admissions"].update_one({"_id": adm.id}, {"$set": {"expires_at": datetime.now(UTC) - timedelta(minutes=1)}})
    await clean["actions"].insert_one({
        "_id": "act_0000000000000009", "decision_id": "dec_0000000000000009", "admission_id": adm.id, "run_id": run.id,
        "kind": "notify_slack", "destination": "slack:#all-mango-db-hackathon",
        "stamp": (await runs.stamp(run.id)).model_dump(), "status": "dispatching", "proposed_at": datetime.now(UTC),
    })
    listed = await client.get(f"/api/v1/actions?run_id={run.id}", headers=H)
    assert listed.status_code == 200
    assert [a["status"] for a in listed.json()["items"]] == ["reconciling"]
    assert (await clean["actions"].find_one({"_id": "act_0000000000000009"}))["status"] == "dispatching"
    assert (await client.get("/api/v1/actions/act_0000000000000009", headers=H)).json()["status"] == "reconciling"
    assert (await client.get("/api/v1/actions/act_missing", headers=H)).status_code == 404


async def test_vlad_is_not_startable(clean, authority) -> None:
    with pytest.raises(ApiError) as caught:
        await runs.start(VLAD, "lbdx", "discover")
    assert caught.value.status_code == 403


# --- A10's progress, written only through runs (spine layer table) --------------------------------


async def test_record_progress_writes_full_values_while_running_or_stopping(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    await runs.admit(run.id, "a|search_source|-|-")  # not_admitted stays runs.admit's
    ok = await runs.record_progress(
        run.id, counts={"total": 3, "done": 1, "failed": 1, "early_research": 1, "filed": 2, "reports": 1},
        active_items=[{"source_ref": "clinicaltrials.gov:NCT04712877", "step": "draft"}],
        failure_lines=[{"source_ref": "clinicaltrials.gov:NCT00000001", "error": "extract_failed"}],
    )
    assert ok
    again = await runs.record_progress(run.id, counts={"total": 3, "done": 2}, active_items=[], failure_lines=[])
    assert again
    stored = await clean["runs"].find_one({"_id": run.id})
    assert stored["counts"]["total"] == 3 and stored["counts"]["done"] == 2 and stored["counts"]["filed"] == 2
    assert stored["counts"]["not_admitted"] == 0
    assert stored["active"] == [] and stored["failures"] == []
    await runs.stop(run.id)
    assert await runs.record_progress(run.id, counts={"done": 3}, active_items=[], failure_lines=[])
    view = await runs.get_run(run.id)
    assert view.counts.done == 3 and view.status == "stopping"


async def test_record_progress_never_rewrites_an_ended_run(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    await runs.finish(run.id)
    assert not await runs.record_progress(run.id, counts={"done": 9}, active_items=[], failure_lines=[])
    assert (await clean["runs"].find_one({"_id": run.id}))["counts"]["done"] == 0


async def test_fail_is_conditional_and_emits_once(clean, authority) -> None:
    run = await runs.start(SAM, "lbdx", "discover")
    failed = await runs.fail(run.id, "pipeline_error")
    assert failed.status == "failed" and failed.finished_at is not None
    assert failed.failures[-1].error == "pipeline_error"
    again = await runs.fail(run.id, "second")
    assert again.status == "failed" and len(again.failures) == 1
    assert await clean["events"].count_documents({"run_id": run.id, "status": "failed"}) == 1
    done = await runs.start(SAM, "lbdx", "discover")
    await runs.finish(done.id)
    assert (await runs.fail(done.id, "late")).status == "done"
