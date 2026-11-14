"""Voice input for the interview page (V73, `voice_input` flag): transcription only.

`transcribe(report_id, audio, mime, ctx)` turns one short recording into text for the user to read and edit in the
question box. Nothing is submitted, answered or decided from it, and the typed path (`answer_question`) is unchanged.

Order, and why:

1. The size cap (`MAX_BYTES`) and, when the clip is a WAV, the duration cap (`MAX_DURATION_MS`) are checked BEFORE the
   gate: a clip that is too long is refused as `too_long` with no Decision and no vendor call (`decision_id` is "").
2. The gate: one `gate.evaluate` of `transcribe_question` to `stt:elevenlabs` under the Reviewer's grant. Its inputs are
   metadata only (`id_target`, MIME type, byte count, duration when known, SHA-256 of the audio). Never the audio and
   never the transcript. Blocked: `refused: true, refusal_reason: "blocked"` and no vendor call.
3. Allowed: one call to ElevenLabs speech-to-text under one overall deadline (`DEADLINE_S`). The action is settled:
   claimed `dispatching` before the call, then `delivered`, `failed` (no key, 4xx) or `unknown` (timeout, 5xx), as B06 does
   A failure is `unavailable` to the user, never a 500.
4. The text is stripped and cut to 500 characters (what `InterviewRequest` allows). The audio and the transcript are
   never stored: not in a collection, not in a Decision, not in the action's result, not in a log.

LiveAvatar never listens. The vendor credential is read in `briefing/audio.py` only (B06's client is reused) and never
reaches this lane; errors are logged as a status code or a short machine code, never a message.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import struct
from collections.abc import Awaitable, Callable
from typing import Any

from dxp import gate
from dxp.api import models as m

log = logging.getLogger("dxp.interview")

KIND = "transcribe_question"
DESTINATION = "stt:elevenlabs"
ALLOWED_MIMES = ("audio/webm", "audio/wav")
MAX_BYTES = 2 * 1024 * 1024
MAX_DURATION_MS = 30_000
MAX_TEXT_CHARS = 500  # InterviewRequest.question allows 500
DEADLINE_S = 20.0

# ElevenLabs' speech-to-text endpoint (POST /v1/speech-to-text, multipart). `scribe_v1` is deprecated; `scribe_v2` is
# the model the API reference examples use (`scribe_v3` is newer and not yet tried against DxP's account).
MODEL_ID = "scribe_v2"
LANGUAGE_CODE = "en"

REASON_BLOCKED = "blocked"
REASON_TOO_LONG = "too_long"
REASON_UNAVAILABLE = "unavailable"

_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")


class SttError(Exception):
    """The speech-to-text call did not give a transcript. `code` is a short machine code, never a message from the vendor."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


SttClient = Callable[[bytes, str], Awaitable[str]]


def normalise_mime(content_type: str | None) -> str | None:
    """`audio/webm;codecs=opus` -> `audio/webm`; anything that is not webm or wav -> None."""
    base = (content_type or "").split(";", 1)[0].strip().lower()
    return base if base in ALLOWED_MIMES else None


def wav_duration_ms(audio: bytes) -> int | None:
    """The length of a PCM WAV from its header, or None when it cannot be read (webm has no cheap header to read)."""
    if len(audio) < 12 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        return None
    byte_rate: int | None = None
    pos = 12
    while pos + 8 <= len(audio):
        chunk_id = audio[pos : pos + 4]
        (size,) = struct.unpack("<I", audio[pos + 4 : pos + 8])
        body = pos + 8
        if chunk_id == b"fmt " and body + 12 <= len(audio):
            (byte_rate,) = struct.unpack("<I", audio[body + 8 : body + 12])
        elif chunk_id == b"data":
            if not byte_rate:
                return None
            data_len = min(size, len(audio) - body)  # a streamed WAV may carry a 0 or 0xFFFFFFFF size
            return int(data_len * 1000 / byte_rate)
        pos = body + size + (size & 1)
    return None


def clean_text(raw: Any) -> str:
    """The transcript as the question box takes it: one line, stripped, at most 500 characters."""
    if not isinstance(raw, str):
        return ""
    return " ".join(_CONTROL.sub(" ", raw).split())[:MAX_TEXT_CHARS].rstrip()


async def elevenlabs_stt(audio: bytes, mime: str) -> str:
    """The one ElevenLabs speech-to-text call, through B06's client (`briefing.audio._client()`: the one place the vendor
    credential is read, so nothing in this lane touches it). No credential: `SttError("no_key")`, nothing is sent."""
    from dxp.briefing import audio as vendor

    client = vendor._client()
    if client is None:
        raise SttError("no_key")
    filename = "question.wav" if mime == "audio/wav" else "question.webm"
    try:
        response = await client.speech_to_text.convert(
            model_id=MODEL_ID,
            file=(filename, audio, mime),
            language_code=LANGUAGE_CODE,
            tag_audio_events=False,
            # One recording, one request: the SDK would otherwise retry 5xx/429/408/409 twice and could bill it
            # three times (Luis's review of #70). A failure is settled instead (failed or unknown, never re-sent).
            request_options={"max_retries": 0},
        )
    except SttError:
        raise
    except Exception as exc:  # noqa: BLE001 - only a status code or a short class name leaves this function
        status = getattr(exc, "status_code", None)
        if isinstance(status, int):
            raise SttError(f"http_{status}") from exc
        name = type(exc).__name__
        raise SttError("timeout" if "Timeout" in name else "connection") from exc
    text = getattr(response, "text", None)
    if not isinstance(text, str):
        raise SttError("bad_response")
    return text


def _action(report_id: str, report: dict[str, Any], audio: bytes, mime: str, duration_ms: int | None) -> m.ProposedAction:
    inputs: dict[str, Any] = {
        # The gate derives the Decision's ID from the kind and a target; the request ID keeps each recording its own.
        "id_target": report_id,
        "mime": mime,
        "bytes": len(audio),
        "sha256": hashlib.sha256(audio).hexdigest(),
    }
    if duration_ms is not None:
        inputs["duration_ms"] = duration_ms
    return m.ProposedAction(
        kind=KIND,
        destination=DESTINATION,
        target=m.Target(report_id=report_id),
        inputs=inputs,
        evidence_ref=m.EvidenceRef(source_ref=report.get("source_ref"), version_id=report.get("version_id"), report_id=report_id),
    )


async def _action_id(ctx: m.RunContext, action: m.ProposedAction, decision: m.Decision) -> str:
    action_id = getattr(decision, "action_id", None)
    if action_id:
        return action_id
    from dxp.gate import checks as gate_checks, decisions as gate_decisions

    return gate_decisions.ids_for(gate_checks.GateCtx.coerce(ctx), gate_checks.GateAction.coerce(action))[1]


async def _transition(action_id: str, from_status: str, to_status: str, result: dict[str, Any] | None = None) -> bool:
    """One AD-20 step for this external (media) kind (V71: it writes its own `actions` status, as B06 does): a
    conditional update on `from_status`, so two workers can never both move it, then the same `action_status_changed`
    event `gate.mark_action` emits. True when this call moved it."""
    db = gate.deps.db()
    fields: dict[str, Any] = {"status": to_status}
    if to_status == "dispatching":
        fields["claimed_at"] = gate.deps.now()
    else:
        fields.update({"result": result, "observed_at": gate.deps.now()})
    res = await db["actions"].update_one({"_id": action_id, "status": from_status}, {"$set": fields})
    if not res.modified_count:
        return False
    try:
        act = await db["actions"].find_one({"_id": action_id}) or {}
        await gate.deps.emit_event(
            {
                "type": "action_status_changed",
                "dedupe_key": f"action_status_changed|{action_id}|{to_status}",
                "mode": act.get("mode"),
                "run_id": act.get("run_id"),
                "stamp": act.get("stamp"),
                "decision_id": act.get("decision_id"),
                "action_id": action_id,
                "status": to_status,
            }
        )
    except Exception as exc:  # noqa: BLE001 - the action document is the record; the event is a notice
        log.warning("transcribe action event not emitted (%s)", type(exc).__name__)
    return True


async def _claim(ctx: m.RunContext, action: m.ProposedAction, decision: m.Decision) -> str | None:
    """`queued` to `dispatching` before the vendor call (AD-20). The action ID when this call claimed it, else None:
    then nothing is sent (another worker holds it, it is already settled, or the store failed)."""
    try:
        action_id = await _action_id(ctx, action, decision)
        return action_id if await _transition(action_id, "queued", "dispatching") else None
    except Exception as exc:  # noqa: BLE001 - not claimed means nothing is sent
        log.warning("transcribe action not claimed (%s)", type(exc).__name__)
        return None


async def _settle(action_id: str, status: str, result: dict[str, Any]) -> None:
    """End the claimed action, conditional on `dispatching`: `delivered` (the transcript came back), `failed` (nothing
    can have been processed: no key, or a 4xx refusal) or `unknown` (a timeout, connection error or 5xx: the request
    may have been processed; never re-sent). `result` is metadata only (never the transcript). Best effort: a failure
    to settle never changes the reply and is logged by type only."""
    try:
        await _transition(action_id, "dispatching", status, result)
    except Exception as exc:  # noqa: BLE001 - see the docstring
        log.warning("transcribe action not settled (%s)", type(exc).__name__)


def _failure_status(code: str) -> str:
    """`failed` only when nothing can have been processed: no credential (nothing was sent) or a 4xx refusal.
    Everything else (timeout, connection, 5xx, an unreadable answer, the deadline) is `unknown` (V71, AD-20)."""
    if code == "no_key":
        return "failed"
    if code.startswith("http_"):
        try:
            return "failed" if 400 <= int(code[5:]) < 500 else "unknown"
        except ValueError:
            return "unknown"
    return "unknown"


def too_long() -> m.TranscribeResponse:
    return m.TranscribeResponse(text="", decision_id="", refused=True, refusal_reason=REASON_TOO_LONG)


async def transcribe(
    report_id: str,
    audio: bytes,
    mime: str,
    ctx: m.RunContext,
    *,
    report: dict[str, Any],
    stt: SttClient | None = None,
) -> m.TranscribeResponse:
    """One recording to text. `report` is the pending or accepted report the caller already read (for the gate's evidence)."""
    duration_ms = wav_duration_ms(audio) if mime == "audio/wav" else None
    if len(audio) > MAX_BYTES or (duration_ms is not None and duration_ms > MAX_DURATION_MS):
        return too_long()

    action = _action(report_id, report, audio, mime, duration_ms)
    decision = await gate.evaluate(ctx, action)
    if decision.outcome == "blocked":
        return m.TranscribeResponse(text="", decision_id=decision.id, refused=True, refusal_reason=REASON_BLOCKED)

    action_id = await _claim(ctx, action, decision)
    if action_id is None:
        # Not ours to send (or the store is down): never call the vendor for an unclaimed action.
        return m.TranscribeResponse(text="", decision_id=decision.id, refused=True, refusal_reason=REASON_UNAVAILABLE)

    call = stt or elevenlabs_stt
    try:
        raw = await asyncio.wait_for(call(audio, mime), timeout=DEADLINE_S)
        text = clean_text(raw)
    except Exception as exc:  # noqa: BLE001 - a vendor failure is `unavailable`, never a 500
        code = exc.code if isinstance(exc, SttError) else ("timeout" if isinstance(exc, TimeoutError) else type(exc).__name__)
        log.warning("transcribe failed after the gate (%s)", code)
        await _settle(action_id, _failure_status(str(code)), {"outcome": "unavailable", "error": str(code)})
        return m.TranscribeResponse(text="", decision_id=decision.id, refused=True, refusal_reason=REASON_UNAVAILABLE)

    await _settle(action_id, "delivered", {"outcome": "transcribed", "chars": len(text), "bytes": len(audio)})
    return m.TranscribeResponse(text=text, decision_id=decision.id, refused=False, refusal_reason=None)
