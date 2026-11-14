"""The ten-second ElevenLabs briefing (Story 10.11, AD-30, V12, V29, V41). Finished by B06.

`generate(report_id, ctx)` is called only from `POST /reports/<report_id>/briefing`, on demand,
for a Reviewer. The run, the pipeline, filing a report and the Slack alert never call it.

What it does, in order:

1. Reads the report's stored script (`report.script`, built at filing by `reports.script_for()`).
   It never builds or edits a script: the text sent to ElevenLabs is that string, unchanged.
   ctDNA, NSCLC, NGS and the other terms are pronounced through a pronunciation dictionary
   (alias rules) passed to ElevenLabs as a locator, so the words themselves stay as written.
2. Evaluates the gate as `generate_briefing` to `tts:elevenlabs` under the Reviewer's grant.
   Blocked: nothing is called and nothing is stored. Allowed: the gate has already inserted the
   `actions` document, `queued`.
3. Claims the action (`queued` to `dispatching`, conditional) and the cache entry in `audio`
   (one per report and script hash), so two presses never make two ElevenLabs calls.
4. Calls ElevenLabs once, or finds the cached audio and calls nothing. The whole generation
   (the dictionary step, the call and a 429 retry) shares one deadline of `OVERALL_DEADLINE_S`
   (about 25 s, inside AD-9's 30 s). It records exactly what it observed (AD-20): a failure
   before the call is made (the dictionary step, anything else that goes wrong first) is `failed`,
   because nothing was sent; a 4xx other than 429 is `failed`; a 429 is retried once after
   `Retry-After` while the claim is held and the deadline allows it, and a second 429 is
   `failed`; a timeout, a connection error or a 5xx is `unknown` and is not retried within the
   press; no key is `failed` with nothing sent. Every update is conditional on `dispatching`.

   Pressing the button again after an `unknown` outcome may retry automatically (V72, a
   double charge is accepted): the failed cache entry is claimed again by the next press, and the
   earlier action keeps its `unknown` status.

   Writing its own `actions` status (queued to dispatching to delivered, failed or unknown) is
   the V71 exception to V65, for the media kinds only. Every update is conditional on the status
   it expects.

   The voice is `ELEVENLABS_VOICE_ID` when set, else `DEFAULT_VOICE_ID`, ElevenLabs' default voice "Jessica".

A failure is recorded and returned as a briefing with status `failed` or `unavailable`; it never
raises into the caller, and nothing else (the report, Slack, the decision, the task) reads it.

`ELEVENLABS_API_KEY` is read here and nowhere else in the backend. It is never logged, stored,
returned or put in an event. Errors are recorded as a status code and a short machine code only.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import httpx
from pymongo.errors import DuplicateKeyError

from dxp import gate, store
from dxp.api.models import Briefing, Decision, ProposedAction, RunContext, Target
from dxp.identity import derive

log = logging.getLogger("dxp.briefing")

KIND = "generate_briefing"
DESTINATION = "tts:elevenlabs"
OUTPUT_FORMAT = "mp3_44100_128"
MIME = "audio/mpeg"
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_VOICE_ID = "cgSgspJ2msm6clMCkdW9"  # ElevenLabs default voice "Jessica", the same voice DxP's LiveAvatar uses

OVERALL_DEADLINE_S = 25.0  # one deadline for the whole generation, inside AD-9's 30 seconds
REQUEST_TIMEOUT_S = OVERALL_DEADLINE_S  # the client never waits longer than the deadline
DICTIONARY_BUDGET_S = 5.0  # the pronunciation dictionary is optional: past this, go without it
MIN_RETRY_BUDGET_S = 5.0  # a 429 is retried only if this much is left after the wait
RETRY_AFTER_CAP_S = 10.0
IN_FLIGHT_WAIT_S = 20.0  # how long a second press waits for the first one's call
STALE_AFTER = timedelta(seconds=90)  # a `generating` entry older than this is a dead worker's

# Spoken forms for the terms a ten-second briefing is likely to contain. They go to ElevenLabs as
# alias rules in a pronunciation dictionary; the text that is read stays `report.script`.
PRONUNCIATIONS: tuple[tuple[str, str], ...] = (
    ("ctDNA", "circulating tumor D N A"),
    ("cfDNA", "cell-free D N A"),
    ("NSCLC", "non-small cell lung cancer"),
    ("NGS", "N G S"),
    ("MRD", "M R D"),
    ("EGFR", "E G F R"),
    ("CDx", "C D x"),
)
DICTIONARY_NAME = "dxp-briefing-terms"

Phase = Literal["won", "ready", "busy"]


class ReportNotFound(LookupError):
    """No report has this ID."""


class ScriptMissing(ValueError):
    """The report carries no script (a report is always filed with one, V41)."""


# ---------------------------------------------------------------------------
# The ElevenLabs client: the one place the key is read. Tests replace `_client`.
# ---------------------------------------------------------------------------


async def _sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


def configured() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())


def _client() -> Any | None:
    """An `AsyncElevenLabs`, or `None` when there is no key (OD3)."""
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        return None
    from elevenlabs.client import AsyncElevenLabs

    return AsyncElevenLabs(api_key=key, timeout=REQUEST_TIMEOUT_S)


@dataclass
class Sent:
    """What one attempt observed: `ok`, `failed` (nothing to retry), `unknown` (ambiguous) or
    `unavailable` (no key, nothing was sent)."""

    outcome: Literal["ok", "failed", "unknown", "unavailable"]
    audio: bytes | None = None
    model_id: str | None = None
    voice_id: str | None = None
    pronunciation: Literal["dictionary", "none"] = "none"
    error: dict[str, Any] = field(default_factory=dict)


_SAFE_CODE = re.compile(r"^[a-z0-9_]{1,64}$")


def _safe_code(value: Any) -> str | None:
    return value if isinstance(value, str) and _SAFE_CODE.match(value) else None


def _error_detail(exc: BaseException) -> dict[str, Any]:
    """A status code and a short machine code, never the message (it could carry a key or a URL)."""
    status = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    detail = body.get("detail") if isinstance(body, dict) else None
    code = None
    if isinstance(detail, dict):
        code = _safe_code(detail.get("status")) or _safe_code(detail.get("code"))
    out: dict[str, Any] = {"type": type(exc).__name__}
    if isinstance(status, int):
        out["status_code"] = status
    if code:
        out["code"] = code
    return out


def _retry_after(exc: BaseException) -> float:
    headers = getattr(exc, "headers", None) or {}
    try:
        value = float(headers.get("retry-after") or headers.get("Retry-After") or 1.0)
    except (TypeError, ValueError):
        value = 1.0
    return max(0.0, min(value, RETRY_AFTER_CAP_S))


def _is_api_error(exc: BaseException) -> bool:
    from elevenlabs.core import ApiError

    return isinstance(exc, ApiError)


async def _pronunciation_locators(client: Any) -> list[Any]:
    """The pronunciation dictionary for `PRONUNCIATIONS`, created once and remembered in `audio`.

    A failure here never stops the briefing: it is made without the dictionary and the audio
    entry says `pronunciation: "none"`.
    """
    from elevenlabs import (
        BodyAddAPronunciationDictionaryV1PronunciationDictionariesAddFromRulesPostRulesItem_Alias as AliasRule,
    )
    from elevenlabs import PronunciationDictionaryVersionLocator

    rules_hash = hashlib.sha256(json.dumps(PRONUNCIATIONS).encode("utf-8")).hexdigest()[:16]
    entry_id = f"pronunciation_{rules_hash}"
    audio = store.collection("audio")
    try:
        found = await audio.find_one({"_id": entry_id})
        if found is None:
            created = await client.pronunciation_dictionaries.create_from_rules(
                name=f"{DICTIONARY_NAME}-{rules_hash}",
                rules=[
                    AliasRule(string_to_replace=term, alias=alias, case_sensitive=True, word_boundaries=True)
                    for term, alias in PRONUNCIATIONS
                ],
            )
            found = {"_id": entry_id, "kind": "pronunciation_dictionary", "dictionary_id": created.id,
                     "version_id": created.version_id, "created_at": _now()}
            try:
                await audio.insert_one(found)
            except DuplicateKeyError:
                found = await audio.find_one({"_id": entry_id}) or found
        return [PronunciationDictionaryVersionLocator(
            pronunciation_dictionary_id=found["dictionary_id"], version_id=found["version_id"])]
    except Exception as exc:  # noqa: BLE001 - never stops the briefing
        log.warning("briefing pronunciation dictionary unavailable: %s", _error_detail(exc))
        return []


def _voice_id() -> str:
    """`ELEVENLABS_VOICE_ID` when set, else DxP's chosen voice. No lookup, so nothing can fail here."""
    return os.environ.get("ELEVENLABS_VOICE_ID", "").strip() or DEFAULT_VOICE_ID


async def _attempt(client: Any, text: str, voice_id: str, model_id: str, locators: list[Any]) -> bytes:
    chunks = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        output_format=OUTPUT_FORMAT,
        pronunciation_dictionary_locators=locators or None,
    )
    return b"".join([chunk async for chunk in chunks if chunk])


async def _send(text: str) -> Sent:
    """One synthesis of `text`, exactly as given, inside one overall deadline. Classifies what
    happened (AD-20). Anything that goes wrong before the call is made is `failed`: nothing was sent."""
    client = _client()
    if client is None:
        return Sent("unavailable", error={"code": "no_key"})
    model_id = os.environ.get("ELEVENLABS_MODEL_ID", "").strip() or DEFAULT_MODEL_ID
    voice_id = _voice_id()
    sent = Sent("failed", model_id=model_id, voice_id=voice_id)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + OVERALL_DEADLINE_S
    attempted = False  # true once a synthesis request may have reached ElevenLabs
    try:
        try:
            locators = await asyncio.wait_for(
                _pronunciation_locators(client), max(0.1, min(DICTIONARY_BUDGET_S, deadline - loop.time())))
        except TimeoutError:  # optional step: go without the dictionary
            log.warning("briefing pronunciation dictionary timed out")
            locators = []
        sent.pronunciation = "dictionary" if locators else "none"
        for attempt in (1, 2):
            budget = deadline - loop.time()
            if budget <= 0:  # no time left to start a call: nothing was sent
                sent.outcome, sent.error = "failed", {"code": "deadline"}
                return sent
            attempted = True
            try:
                audio = await asyncio.wait_for(_attempt(client, text, voice_id, model_id, locators), budget)
            except Exception as exc:  # noqa: BLE001 - classified below
                status = getattr(exc, "status_code", None) if _is_api_error(exc) else None
                if status == 429:
                    wait = _retry_after(exc)
                    if attempt == 1 and deadline - loop.time() >= wait + MIN_RETRY_BUDGET_S:
                        attempted = False  # nothing was produced: retry once, holding the claim
                        await _sleep(wait)
                        continue
                    sent.outcome, sent.error = "failed", _error_detail(exc)
                    return sent
                if isinstance(status, int) and 400 <= status < 500:
                    sent.outcome, sent.error = "failed", _error_detail(exc)
                    return sent
                # 5xx, a timeout, a connection error or anything unexpected: ambiguous
                sent.outcome = "unknown"
                sent.error = _error_detail(exc) if _is_api_error(exc) else {
                    "type": type(exc).__name__,
                    "code": "timeout" if isinstance(exc, (TimeoutError, httpx.TimeoutException)) else "connection",
                }
                return sent
            if not audio:
                sent.outcome, sent.error = "failed", {"code": "empty_audio"}
                return sent
            sent.outcome, sent.audio = "ok", audio
            return sent
    except Exception as exc:  # noqa: BLE001 - unexpected; ambiguous only if a request may be out
        sent.outcome = "unknown" if attempted else "failed"
        sent.error = _error_detail(exc)
    return sent


# ---------------------------------------------------------------------------
# Storage: the report (read only), the `audio` cache, and the action's own status
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def audio_id_for(report_id: str, script_hash: str) -> str:
    """One cache entry per report state: the report and the hash of its script."""
    return derive("audio_", report_id, script_hash)


def audio_url_for(report_id: str) -> str:
    """Where the cached audio is served: the same route, asked for audio (`?audio=1`)."""
    return f"/api/v1/reports/{report_id}/briefing?audio=1"


async def report_for(report_id: str) -> dict[str, Any]:
    doc = await store.collection("reports").find_one(
        {"_id": report_id}, {"script": 1, "script_hash": 1, "run_id": 1})
    if doc is None:
        raise ReportNotFound(report_id)
    return doc


def _script_of(report: dict[str, Any]) -> tuple[str, str]:
    script = report.get("script")
    if not isinstance(script, str) or not script.strip():
        raise ScriptMissing(report["_id"])
    script_hash = report.get("script_hash") or hashlib.sha256(script.encode("utf-8")).hexdigest()
    return script, script_hash


def _view(report_id: str, script: str, script_hash: str | None, entry: dict[str, Any] | None) -> Briefing:
    """The Briefing a caller sees. The script is always in it, whatever the audio status."""
    if entry is not None and entry.get("status") == "ready":
        status: Literal["none", "ready", "failed", "unavailable"] = "ready"
    elif entry is not None and entry.get("status") in ("failed", "unavailable"):
        status = entry["status"]
    elif entry is None and not configured():
        status = "unavailable"  # no key (OD3): there is nothing to press
    else:
        status = "none"  # also while another press is still generating
    ready = status == "ready"
    return Briefing(
        report_id=report_id,
        script=script,
        script_hash=script_hash,
        status=status,
        audio_id=entry["_id"] if ready and entry else None,
        audio_url=audio_url_for(report_id) if ready else None,
    )


async def status(report_id: str) -> Briefing:
    """`GET /reports/<report_id>/briefing`: the script as text, plus the audio status and URL."""
    report = await report_for(report_id)
    script = report.get("script") if isinstance(report.get("script"), str) else ""
    script_hash = report.get("script_hash")
    entry = None
    if script and script_hash:
        entry = await store.collection("audio").find_one(
            {"_id": audio_id_for(report_id, script_hash)}, {"audio": 0})
    return _view(report_id, script, script_hash, entry)


async def audio_bytes(report_id: str) -> tuple[bytes, str] | None:
    """The cached audio for the report's current script, or `None` while none exists."""
    report = await report_for(report_id)
    script_hash = report.get("script_hash")
    if not script_hash:
        return None
    entry = await store.collection("audio").find_one(
        {"_id": audio_id_for(report_id, script_hash), "status": "ready"})
    if not entry or not entry.get("audio"):
        return None
    return bytes(entry["audio"]), entry.get("mime") or MIME


async def _claim_entry(audio_id: str, doc: dict[str, Any]) -> Phase:
    """Take the cache entry for this press: `won` (call ElevenLabs), `ready` (use the cache) or
    `busy` (another press is generating it)."""
    audio = store.collection("audio")
    try:
        await audio.insert_one(doc)
        return "won"
    except DuplicateKeyError:
        pass
    taken = {"status": "generating", "updated_at": _now(), "action_id": doc["action_id"],
             "decision_id": doc["decision_id"], "requested_by": doc["requested_by"], "error": None}
    again = await audio.update_one({"_id": audio_id, "status": {"$in": ["failed", "unavailable"]}}, {"$set": taken})
    if again.matched_count:
        return "won"
    stale = await audio.update_one(
        {"_id": audio_id, "status": "generating", "updated_at": {"$lt": _now() - STALE_AFTER}}, {"$set": taken})
    if stale.matched_count:
        return "won"
    existing = await audio.find_one({"_id": audio_id}, {"audio": 0})
    return "ready" if existing and existing.get("status") == "ready" else "busy"


async def _wait_for_entry(audio_id: str) -> dict[str, Any] | None:
    """Wait (bounded) for the press that is generating this entry; its result is ours too."""
    audio = store.collection("audio")
    waited = 0.0
    while waited < IN_FLIGHT_WAIT_S:
        entry = await audio.find_one({"_id": audio_id}, {"audio": 0})
        if entry is None or entry.get("status") != "generating":
            return entry
        await _sleep(0.5)
        waited += 0.5
    return await audio.find_one({"_id": audio_id}, {"audio": 0})


async def _emit(ctx: RunContext, action_id: str, report_id: str, decision_id: str, new_status: str) -> None:
    try:
        await store.emit_event(
            "action_status_changed",
            dedupe_key=f"{action_id}|{new_status}",
            stamp=ctx.stamp.model_dump(mode="json", exclude_none=True),
            action_id=action_id,
            decision_id=decision_id,
            report_id=report_id,
            status=new_status,
        )
    except Exception as exc:  # noqa: BLE001 - an event failure never fails the briefing
        log.warning("briefing event not recorded: %s", type(exc).__name__)


async def _claim_action(ctx: RunContext, action_id: str, report_id: str, decision_id: str) -> bool:
    """queued -> dispatching, conditional: only the caller whose update matched may send."""
    won = await store.collection("actions").update_one(
        {"_id": action_id, "status": "queued"}, {"$set": {"status": "dispatching", "claimed_at": _now()}})
    if won.matched_count:
        await _emit(ctx, action_id, report_id, decision_id, "dispatching")
    return bool(won.matched_count)


async def _settle_action(ctx: RunContext, action_id: str, report_id: str, decision_id: str,
                         new_status: Literal["delivered", "failed", "unknown"],
                         result: dict[str, Any] | None = None) -> None:
    """dispatching -> delivered | failed | unknown, conditional on `dispatching` (D24), so a slow
    worker never overwrites a swept action."""
    update: dict[str, Any] = {"status": new_status, "observed_at": _now()}
    if result is not None:
        update["result"] = result
    done = await store.collection("actions").update_one(
        {"_id": action_id, "status": "dispatching"}, {"$set": update})
    if done.matched_count:
        await _emit(ctx, action_id, report_id, decision_id, new_status)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


async def generate(report_id: str, ctx: RunContext) -> tuple[Briefing, Decision]:
    """Gated generate_briefing to tts:elevenlabs under sam@v1; called only by its own route.

    Returns the Briefing as it stands afterwards (status `ready`, `failed` or `unavailable`; the
    script is always in it) and the gate's Decision. Raises `ReportNotFound` or `ScriptMissing`
    before the gate when there is nothing to say; an ElevenLabs failure never raises.
    """
    report = await report_for(report_id)
    script, script_hash = _script_of(report)

    decision = await gate.evaluate(
        ctx,
        ProposedAction(
            kind=KIND,
            destination=DESTINATION,
            target=Target(report_id=report_id),
            inputs={"report_id": report_id, "script_hash": script_hash, "script": script},
        ),
    )
    if decision.outcome != "allowed":
        # A blocked action changes nothing and calls nothing (D5).
        return await status(report_id), decision
    action_id = decision.action_id
    if not action_id:
        raise RuntimeError("The gate allowed generate_briefing without an action; nothing was sent.")

    audio_id = audio_id_for(report_id, script_hash)
    requested_by = ctx.stamp.initiated_by or ctx.principal.id
    entry_doc = {
        "_id": audio_id,
        "report_id": report_id,
        "script_hash": script_hash,
        "status": "generating",
        "action_id": action_id,
        "decision_id": decision.id,
        "requested_by": requested_by,
        "error": None,
        "created_at": _now(),
        "updated_at": _now(),
    }

    if not await _claim_action(ctx, action_id, report_id, decision.id):
        # Not ours to send (another worker or the sweep holds this action): change nothing.
        return await status(report_id), decision

    may_have_sent = False  # True once an ElevenLabs request could be on the wire
    try:
        phase = await _claim_entry(audio_id, entry_doc)
        if phase == "busy":
            entry = await _wait_for_entry(audio_id)
            phase = "ready" if entry and entry.get("status") == "ready" else "busy"
        if phase == "ready":  # the cache: nothing is sent (generated once per report state)
            await _settle_action(ctx, action_id, report_id, decision.id, "delivered", {"audio_id": audio_id})
        elif phase == "busy":  # the other press did not finish: nothing of ours was sent
            await _settle_action(ctx, action_id, report_id, decision.id, "failed")
        else:
            may_have_sent = True
            await _generate_and_record(ctx, report_id, script, audio_id, action_id, decision.id)
    except BaseException:
        # Whatever went wrong after the claim, leave the action settled, not dispatching:
        # `failed` if nothing can have been sent (AD-20), `unknown` once a request may be out.
        outcome: Literal["failed", "unknown"] = "unknown" if may_have_sent else "failed"
        await _settle_action(ctx, action_id, report_id, decision.id, outcome)
        await _fail_entry(audio_id, action_id, outcome, {"code": "internal"})
        raise
    return await status(report_id), decision


async def _fail_entry(audio_id: str, action_id: str, outcome: str, error: dict[str, Any]) -> None:
    await store.collection("audio").update_one(
        {"_id": audio_id, "status": "generating", "action_id": action_id},
        {"$set": {"status": "failed", "outcome": outcome, "error": error, "updated_at": _now()}},
    )


async def _generate_and_record(ctx: RunContext, report_id: str, script: str, audio_id: str,
                               action_id: str, decision_id: str) -> None:
    sent = await _send(script)  # the report's script, unchanged
    audio = store.collection("audio")
    if sent.outcome == "ok":
        stored = await audio.update_one(
            {"_id": audio_id, "status": "generating", "action_id": action_id},
            {"$set": {
                "status": "ready",
                "audio": sent.audio,
                "mime": MIME,
                "output_format": OUTPUT_FORMAT,
                "model_id": sent.model_id,
                "voice_id": sent.voice_id,
                "pronunciation": sent.pronunciation,
                "characters": len(script),
                "bytes": len(sent.audio or b""),
                "outcome": "ok",
                "error": None,
                "updated_at": _now(),
            }},
        )
        if stored.matched_count:
            await _settle_action(ctx, action_id, report_id, decision_id, "delivered", {"audio_id": audio_id})
        return
    log.warning("briefing not generated: report=%s outcome=%s error=%s", report_id, sent.outcome, sent.error)
    # `unavailable` (no key) and `unknown` are shown to the person as "unavailable" / "failed";
    # none of them changes anything but this entry and this action.
    entry_status = "unavailable" if sent.outcome == "unavailable" else "failed"
    await audio.update_one(
        {"_id": audio_id, "status": "generating", "action_id": action_id},
        {"$set": {"status": entry_status, "outcome": sent.outcome, "error": sent.error,
                  "model_id": sent.model_id, "voice_id": sent.voice_id, "updated_at": _now()}},
    )
    action_status: Literal["failed", "unknown"] = "unknown" if sent.outcome == "unknown" else "failed"
    await _settle_action(ctx, action_id, report_id, decision_id, action_status)
