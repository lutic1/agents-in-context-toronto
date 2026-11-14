"""briefing.generate (Story 10.11, AD-30): gated, from report.script unchanged, cached once,
observed outcomes recorded, failures never raising, no key means unavailable."""

from __future__ import annotations

import asyncio
import logging

import httpx
import pytest

from dxp.briefing import audio

from .conftest import FAKE_KEY, REPORT_ID, SCRIPT, SCRIPT_HASH, api_error


def action_doc(db, n: int = 1) -> dict:
    return db.collection("actions").docs[f"act_{n:016x}"]


def entry_of(db) -> dict:
    return db.collection("audio").docs[audio.audio_id_for(REPORT_ID, SCRIPT_HASH)]


async def test_the_audio_is_made_from_report_script_unchanged(fake_db, gate, eleven, ctx):
    briefing, decision = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 1
    call = eleven.convert_calls[0]
    assert call["text"] == SCRIPT  # byte for byte: not rewritten, shortened or respelled
    assert call["voice_id"] == "voice_test"
    assert call["output_format"] == "mp3_44100_128"
    assert briefing.script == SCRIPT
    assert briefing.status == "ready"
    assert briefing.audio_url == f"/api/v1/reports/{REPORT_ID}/briefing?audio=1"
    assert decision.outcome == "allowed"


async def test_ctdna_nsclc_and_ngs_are_pronounced_by_a_dictionary_not_by_respelling(fake_db, gate, eleven, ctx):
    await audio.generate(REPORT_ID, ctx)

    rules = {r.string_to_replace: r.alias for r in eleven.dictionary_calls[0]["rules"]}
    assert {"ctDNA", "NSCLC", "NGS"} <= set(rules)
    assert rules["ctDNA"] == "circulating tumor D N A"
    locators = eleven.convert_calls[0]["pronunciation_dictionary_locators"]
    assert [(loc.pronunciation_dictionary_id, loc.version_id) for loc in locators] == [("dict_fake", "ver_fake")]
    assert entry_of(fake_db)["pronunciation"] == "dictionary"
    # one dictionary is made, then remembered: a second report state reuses it
    fake_db.collection("reports").docs[REPORT_ID].update(script_hash="other", script=SCRIPT + " More.")
    await audio.generate(REPORT_ID, ctx)
    assert len(eleven.dictionary_calls) == 1


async def test_a_dictionary_failure_still_makes_the_briefing_without_it(fake_db, gate, eleven, ctx, monkeypatch):
    async def boom(**_):
        raise api_error(500)

    monkeypatch.setattr(eleven.pronunciation_dictionaries, "create_from_rules", boom)
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert briefing.status == "ready"
    assert eleven.convert_calls[0]["text"] == SCRIPT
    assert eleven.convert_calls[0]["pronunciation_dictionary_locators"] is None
    assert entry_of(fake_db)["pronunciation"] == "none"


async def test_it_is_gated_as_generate_briefing_to_tts_elevenlabs_under_the_reviewer(fake_db, gate, eleven, ctx):
    await audio.generate(REPORT_ID, ctx)

    (seen_ctx, action), = gate.calls
    assert (action.kind, action.destination, action.target.report_id) == (
        "generate_briefing", "tts:elevenlabs", REPORT_ID)
    assert seen_ctx.run_id is None and seen_ctx.stamp.kind == "reviewer"
    assert seen_ctx.cause.report_id == REPORT_ID and seen_ctx.cause.origin_run_id == "run_abc"
    assert action.inputs["script"] == SCRIPT and action.inputs["script_hash"] == SCRIPT_HASH
    entry = entry_of(fake_db)
    assert entry["requested_by"] == "sam"  # who requested it
    assert entry["decision_id"] == f"dec_{1:016x}"


async def test_a_blocked_request_calls_nothing_and_stores_nothing(fake_db, gate, eleven, ctx):
    gate.blocked = True
    briefing, decision = await audio.generate(REPORT_ID, ctx)

    assert decision.outcome == "blocked"
    assert eleven.convert_calls == [] and eleven.dictionary_calls == []
    assert fake_db.collection("audio").docs == {}
    assert fake_db.collection("actions").docs == {}
    assert briefing.status == "none" and briefing.script == SCRIPT  # the script is still there


async def test_the_action_goes_queued_dispatching_delivered_with_the_audio_id(fake_db, gate, eleven, ctx):
    await audio.generate(REPORT_ID, ctx)

    act = action_doc(fake_db)
    assert act["status"] == "delivered"
    assert act["result"] == {"audio_id": audio.audio_id_for(REPORT_ID, SCRIPT_HASH)}
    assert act["claimed_at"] and act["observed_at"]
    assert [(e["type"], e["status"]) for e in fake_db.events] == [
        ("action_status_changed", "dispatching"), ("action_status_changed", "delivered")]
    assert fake_db.events[0]["report_id"] == REPORT_ID


async def test_audio_is_generated_once_per_report_state_and_served_from_the_cache(fake_db, gate, eleven, ctx):
    first, _ = await audio.generate(REPORT_ID, ctx)
    second, decision = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 1  # the second press called nothing
    assert second.status == first.status == "ready" and second.audio_id == first.audio_id
    assert decision.id == f"dec_{2:016x}"  # but it is still a gated, audited request
    assert action_doc(fake_db, 2)["status"] == "delivered"
    found = await audio.audio_bytes(REPORT_ID)
    assert found == (b"ID3-fake-audio", "audio/mpeg")


async def test_a_changed_script_is_a_new_report_state_and_new_audio(fake_db, gate, eleven, ctx):
    await audio.generate(REPORT_ID, ctx)
    fake_db.collection("reports").docs[REPORT_ID].update(script="A revised script.", script_hash="rev2")
    await audio.generate(REPORT_ID, ctx)

    assert [c["text"] for c in eleven.convert_calls] == [SCRIPT, "A revised script."]


async def test_two_presses_at_once_make_one_call(fake_db, gate, eleven, ctx):
    (a, _), (b, _) = await asyncio.gather(audio.generate(REPORT_ID, ctx), audio.generate(REPORT_ID, ctx))

    assert len(eleven.convert_calls) == 1
    assert a.status == b.status == "ready"
    assert {action_doc(fake_db, 1)["status"], action_doc(fake_db, 2)["status"]} == {"delivered"}


async def test_without_a_key_it_is_unavailable_nothing_is_sent_and_the_script_stays(fake_db, gate, ctx, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY")  # the real _client, which finds no key
    briefing, decision = await audio.generate(REPORT_ID, ctx)

    assert briefing.status == "unavailable" and briefing.script == SCRIPT
    assert decision.outcome == "allowed"
    assert action_doc(fake_db)["status"] == "failed" and "result" not in action_doc(fake_db)
    assert entry_of(fake_db)["error"] == {"code": "no_key"}


async def test_status_without_a_key_and_without_a_press_is_unavailable(fake_db, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY")
    briefing = await audio.status(REPORT_ID)
    assert (briefing.status, briefing.script, briefing.audio_url) == ("unavailable", SCRIPT, None)


async def test_status_with_a_key_before_a_press_is_none_and_carries_the_script(fake_db, eleven):
    briefing = await audio.status(REPORT_ID)
    assert (briefing.status, briefing.script, briefing.script_hash) == ("none", SCRIPT, SCRIPT_HASH)
    assert await audio.audio_bytes(REPORT_ID) is None


@pytest.mark.parametrize("status", [400, 401, 402, 403, 422])
async def test_a_4xx_is_failed_and_never_retried(fake_db, gate, eleven, ctx, status):
    eleven.queue.append(api_error(status, body={"detail": {"status": "quota_exceeded", "message": "secret words"}}))
    briefing, decision = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 1
    assert briefing.status == "failed" and decision.outcome == "allowed"
    assert action_doc(fake_db)["status"] == "failed"
    assert entry_of(fake_db)["error"] == {"type": "ApiError", "status_code": status, "code": "quota_exceeded"}
    assert "secret words" not in str(fake_db.collection("audio").docs)  # the message is never stored


@pytest.mark.parametrize("failure", [
    api_error(500), api_error(503), httpx.ConnectError("no route"), httpx.ReadTimeout("slow"), TimeoutError()])
async def test_a_5xx_timeout_or_connection_error_is_unknown_and_never_retried(fake_db, gate, eleven, ctx, failure):
    eleven.queue.append(failure)
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 1
    assert action_doc(fake_db)["status"] == "unknown"
    assert briefing.status == "failed" and entry_of(fake_db)["outcome"] == "unknown"


async def test_a_429_is_retried_once_after_retry_after_while_holding_the_claim(fake_db, gate, eleven, ctx, instant_retry):
    eleven.queue.append(api_error(429, headers={"retry-after": "3"}))
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 2 and instant_retry == [3.0]
    assert briefing.status == "ready" and action_doc(fake_db)["status"] == "delivered"
    assert [e["status"] for e in fake_db.events] == ["dispatching", "delivered"]  # one claim, no re-queue


async def test_a_second_429_is_failed(fake_db, gate, eleven, ctx, instant_retry):
    eleven.queue.extend([api_error(429), api_error(429)])
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 2
    assert briefing.status == "failed" and action_doc(fake_db)["status"] == "failed"


async def test_pressing_again_after_a_failure_tries_once_more(fake_db, gate, eleven, ctx):
    eleven.queue.append(api_error(500))
    first, _ = await audio.generate(REPORT_ID, ctx)
    second, _ = await audio.generate(REPORT_ID, ctx)

    assert (first.status, second.status) == ("failed", "ready")
    assert len(eleven.convert_calls) == 2
    assert action_doc(fake_db, 1)["status"] == "unknown"  # the first is not rewritten
    assert action_doc(fake_db, 2)["status"] == "delivered"


async def test_a_stale_generating_entry_is_taken_over(fake_db, gate, eleven, ctx):
    from datetime import UTC, datetime, timedelta

    fake_db.collection("audio").docs[audio.audio_id_for(REPORT_ID, SCRIPT_HASH)] = {
        "_id": audio.audio_id_for(REPORT_ID, SCRIPT_HASH), "report_id": REPORT_ID, "status": "generating",
        "action_id": "act_dead", "updated_at": datetime.now(UTC) - timedelta(minutes=10)}
    briefing, _ = await audio.generate(REPORT_ID, ctx)
    assert briefing.status == "ready" and len(eleven.convert_calls) == 1


async def test_a_failure_never_raises_and_changes_nothing_but_its_own_records(fake_db, gate, eleven, ctx):
    before = dict(fake_db.collection("reports").docs[REPORT_ID])
    eleven.queue.append(api_error(500))
    await audio.generate(REPORT_ID, ctx)

    assert fake_db.collection("reports").docs[REPORT_ID] == before
    assert set(fake_db.collections) <= {"reports", "actions", "audio"}


async def test_an_unexpected_error_after_the_claim_settles_the_action(fake_db, gate, eleven, ctx, monkeypatch):
    async def boom(*_, **__):
        raise RuntimeError("bug")

    monkeypatch.setattr(audio, "_generate_and_record", boom)
    with pytest.raises(RuntimeError):
        await audio.generate(REPORT_ID, ctx)
    assert action_doc(fake_db)["status"] == "unknown"  # not left dispatching
    assert entry_of(fake_db)["status"] == "failed"


async def test_an_unknown_report_and_a_report_without_a_script(fake_db, gate, eleven, ctx):
    with pytest.raises(audio.ReportNotFound):
        await audio.generate("rep_missing", ctx)
    fake_db.collection("reports").docs[REPORT_ID]["script"] = ""
    with pytest.raises(audio.ScriptMissing):
        await audio.generate(REPORT_ID, ctx)
    assert gate.calls == [] and eleven.convert_calls == []  # nothing was gated or sent


async def test_the_voice_is_the_configured_one_else_dxps_chosen_voice(fake_db, gate, eleven, ctx, monkeypatch):
    await audio.generate(REPORT_ID, ctx)
    assert eleven.convert_calls[0]["voice_id"] == "voice_test"  # ELEVENLABS_VOICE_ID overrides

    monkeypatch.delenv("ELEVENLABS_VOICE_ID")
    fake_db.collection("audio").docs.clear()
    await audio.generate(REPORT_ID, ctx)
    assert eleven.convert_calls[1]["voice_id"] == "4d175bd2-b678-46f6-bb01-38b2270147fa"
    assert entry_of(fake_db)["voice_id"] == audio.DEFAULT_VOICE_ID

    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "  ")  # blank is not a choice
    fake_db.collection("audio").docs.clear()
    await audio.generate(REPORT_ID, ctx)
    assert eleven.convert_calls[2]["voice_id"] == audio.DEFAULT_VOICE_ID


async def test_a_failure_before_the_call_is_failed_not_unknown_and_nothing_is_sent(
        fake_db, gate, eleven, ctx, monkeypatch):
    async def boom(client):
        raise RuntimeError("before the call")

    monkeypatch.setattr(audio, "_pronunciation_locators", boom)
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert eleven.convert_calls == []
    assert briefing.status == "failed"
    assert action_doc(fake_db)["status"] == "failed"
    assert entry_of(fake_db)["outcome"] == "failed"


async def test_a_dictionary_that_hangs_is_given_up_on_and_the_briefing_is_made_without_it(
        fake_db, gate, eleven, ctx, monkeypatch):
    async def hang(**_):
        await asyncio.sleep(60)

    monkeypatch.setattr(eleven.pronunciation_dictionaries, "create_from_rules", hang)
    monkeypatch.setattr(audio, "DICTIONARY_BUDGET_S", 0.05)
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert briefing.status == "ready" and entry_of(fake_db)["pronunciation"] == "none"
    assert len(eleven.convert_calls) == 1


async def test_the_whole_generation_shares_one_deadline(fake_db, gate, eleven, ctx, monkeypatch):
    async def slow(**_):
        await asyncio.sleep(60)
        yield b"never"

    monkeypatch.setattr(eleven.text_to_speech, "convert", slow)
    monkeypatch.setattr(audio, "OVERALL_DEADLINE_S", 0.3)
    started = asyncio.get_running_loop().time()
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert asyncio.get_running_loop().time() - started < 2  # one deadline, not one per step
    assert briefing.status == "failed" and action_doc(fake_db)["status"] == "unknown"  # a call was out
    assert entry_of(fake_db)["error"]["code"] == "timeout"


def test_the_real_deadline_is_about_25_seconds_inside_ad_9s_30():
    assert 20 <= audio.OVERALL_DEADLINE_S <= 25
    assert audio.REQUEST_TIMEOUT_S <= audio.OVERALL_DEADLINE_S


async def test_a_429_is_not_retried_when_the_deadline_cannot_cover_the_wait(
        fake_db, gate, eleven, ctx, instant_retry, monkeypatch):
    monkeypatch.setattr(audio, "OVERALL_DEADLINE_S", 8.0)
    eleven.queue.append(api_error(429, headers={"retry-after": "10"}))
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert len(eleven.convert_calls) == 1 and instant_retry == []
    assert briefing.status == "failed" and action_doc(fake_db)["status"] == "failed"


async def test_the_audio_is_made_from_the_script_the_real_filing_path_builds(fake_db, gate, eleven, ctx):
    """`report.script` as A19+A20's `reports.file` makes it, not a string written for the test."""
    from dxp.reports.file import report_document
    from dxp.reports.script import script_for, script_hash

    draft = {
        "source_ref": "src_nct04712877", "version_id": "sv_0123456789abcdef", "nct_id": "NCT04712877",
        "scope_id": "scope_lung", "team_id": "team_x", "run_id": "run_abc",
        "headline": "This study investigates molecular profiling using blood (ctDNA) and tumour tissue.",
        "status_line": "Recruiting; no results posted",
        "gap": "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?",
        "discovery": {"summary": "A lung cancer study.", "trial_status": "RECRUITING", "has_results": False,
                      "intervention_text": "ctDNA, tumor NGS", "mentions": []},
    }
    doc = report_document("rep_real0123456789a", draft, ctx, None, None)
    assert doc["script"] == script_for(doc) and doc["script_hash"] == script_hash(doc["script"])
    fake_db.collection("reports").docs["rep_real0123456789a"] = doc

    briefing, _ = await audio.generate("rep_real0123456789a", ctx)

    assert eleven.convert_calls[0]["text"] == doc["script"]  # byte for byte
    assert gate.calls[0][1].inputs["script_hash"] == doc["script_hash"]
    assert briefing.status == "ready" and briefing.script == doc["script"]


async def test_the_key_is_never_stored_logged_or_returned(fake_db, gate, eleven, ctx, caplog):
    caplog.set_level(logging.DEBUG)
    eleven.queue.append(api_error(401, body={"detail": {"status": "invalid_api_key", "message": FAKE_KEY}}))
    briefing, decision = await audio.generate(REPORT_ID, ctx)

    everything = " ".join([
        repr(fake_db.collections["audio"].docs), repr(fake_db.collections["actions"].docs),
        repr(fake_db.events), briefing.model_dump_json(), decision.model_dump_json(), caplog.text])
    assert FAKE_KEY not in everything


async def test_a_press_that_finds_another_generating_waits_for_it_and_sends_nothing(fake_db, gate, eleven, ctx, monkeypatch):
    from datetime import UTC, datetime

    entry_id = audio.audio_id_for(REPORT_ID, SCRIPT_HASH)
    entries = fake_db.collection("audio")
    entries.docs[entry_id] = {"_id": entry_id, "report_id": REPORT_ID, "status": "generating",
                              "action_id": "act_other", "updated_at": datetime.now(UTC)}

    async def other_press_finishes(_: float) -> None:
        entries.docs[entry_id].update(status="ready", audio=b"ID3-theirs", mime="audio/mpeg")

    monkeypatch.setattr(audio, "_sleep", other_press_finishes)
    briefing, _ = await audio.generate(REPORT_ID, ctx)

    assert eleven.convert_calls == []  # their call is ours too
    assert briefing.status == "ready" and action_doc(fake_db)["status"] == "delivered"


async def test_a_press_whose_neighbour_never_finishes_fails_without_sending(fake_db, gate, eleven, ctx, monkeypatch):
    from datetime import UTC, datetime

    entry_id = audio.audio_id_for(REPORT_ID, SCRIPT_HASH)
    fake_db.collection("audio").docs[entry_id] = {"_id": entry_id, "status": "generating",
                                                  "action_id": "act_other", "updated_at": datetime.now(UTC)}
    monkeypatch.setattr(audio, "IN_FLIGHT_WAIT_S", 1.0)

    async def tick(_: float) -> None:
        return None

    monkeypatch.setattr(audio, "_sleep", tick)
    briefing, _ = await audio.generate(REPORT_ID, ctx)
    assert eleven.convert_calls == [] and briefing.status == "none"
    assert action_doc(fake_db)["status"] == "failed"
