"""The LiveAvatar session token minter (Story 10.12, B08; V29, V70; AD-30).

V70: the live avatar belongs to the interview page, not the report page. This module and
`api/routes_avatar.py` are only the server side of it: a token minter for `POST /reports/{id}/avatar`.

What the backend does, and no more:

1. The report must exist and be ACCEPTED. Any other status is a 409 before the gate and before any
   provider call.
2. The request is gated as `generate_avatar_video` to `video:heygen` under the Reviewer's grant
   (`sam@v1`), before any call to LiveAvatar. The Decision is recorded allowed or blocked; a blocked
   Decision makes no call.
3. Once allowed, it reads `LIVEAVATAR_API_KEY` (server side only) and mints one short-lived FULL-mode
   session token with `POST https://api.liveavatar.com/v1/sessions/token` (header `X-API-KEY`).
4. The token goes back only in `AvatarResponse.session_token` (with `session_expires_at`), the contract
   from A01. It is never stored, logged, traced, or put in `Media` or any document.
5. It records a `media` document `{ report_id, status, decision_id, provider, ... }` without the token.
6. AD-20 lifecycle (V71: `generate_avatar_video` writes its own `actions` status, conditionally). The
   action the gate inserted `queued` is claimed `queued -> dispatching` by a conditional update, and only
   the worker whose update matched calls LiveAvatar. It is then settled, each step conditional on
   `dispatching`: `delivered` with `result { media_id, provider_video_id = session_id }` (never the
   token); `failed` for a missing key or a definite provider rejection (4xx); `unknown` for a timeout,
   a network error, a 5xx or an unreadable answer, never retried.

Nothing here runs unless a Reviewer asks (V29), and nothing waits on it. A missing key or a provider
failure leaves the media `unavailable` and the response without a token.

Docs: https://docs.liveavatar.com/api-reference/full-mode/sessions/create-session-token.md
      https://docs.liveavatar.com/docs/full-mode/overview.md
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol

import httpx
from dxp import gate
from dxp.api import auth
from dxp.api.errors import ApiError
from dxp.api.models import (
    Decision,
    DecisionCause,
    EvidenceRef,
    Media,
    ProposedAction,
    Principal,
    RunContext,
    Stamp,
    Target,
)
from dxp.identity import derive

log = logging.getLogger("dxp.briefing.avatar")

LIVEAVATAR_API_URL = "https://api.liveavatar.com"
TOKEN_PATH = "/v1/sessions/token"
KEY_ENV = "LIVEAVATAR_API_KEY"  # the only secret; read here only, never logged or returned
AVATAR_ID_ENV = "LIVEAVATAR_AVATAR_ID"  # not secret: overrides which LiveAvatar avatar speaks (a UUID)
SANDBOX_ENV = "LIVEAVATAR_SANDBOX"  # "true" asks for sandbox mode, which consumes no credits
MAX_SECONDS_ENV = "LIVEAVATAR_MAX_SECONDS"
VOICE_ID_ENV = "LIVEAVATAR_VOICE_ID"  # not secret: overrides the LiveAvatar voice record (a UUID)

# DxP's chosen stock avatar and voice (Vlad, 14 Nov). Identifiers, not secrets; env vars override them.
# The avatar is LiveAvatar's public "Lily (Friendly)". The voice is a LiveAvatar voice record ("Jessica"),
# an ElevenLabs voice imported into LiveAvatar, so FULL mode speaks with it via avatar_persona.voice_id.
# It is not a raw ElevenLabs voice ID (B06 uses ELEVENLABS_VOICE_ID for that).
DXP_AVATAR_ID = "eb961787-3605-49e9-b703-3402c12ccdb4"
DXP_VOICE_ID = "4d175bd2-b678-46f6-bb01-38b2270147fa"
# Verified against the sandbox on 14 Nov: sandbox sessions accept only this free avatar.
SANDBOX_AVATAR_ID = "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a"


def voice_id() -> str:
    """The LiveAvatar voice the avatar speaks with (LIVEAVATAR_VOICE_ID, else DxP's chosen voice)."""
    return os.environ.get(VOICE_ID_ENV, "").strip() or DXP_VOICE_ID

# A short ceiling: FULL mode costs 2 credits a minute, so one session is capped at 6 credits.
DEFAULT_MAX_SESSION_SECONDS = 180
REQUEST_TIMEOUT_SECONDS = 15.0

UnavailableReason = Literal["blocked", "no_key", "provider_error", "not_claimed"]



# ---------------------------------------------------------------------------
# The LiveAvatar client (the one place that holds the key)
# ---------------------------------------------------------------------------


class LiveAvatarError(Exception):
    """A LiveAvatar call failed. Carries a status code only, never a body, a header or the key."""

    def __init__(self, status: int | None = None) -> None:
        super().__init__(f"LiveAvatar session token request failed (status {status})" if status else "LiveAvatar could not be reached")
        self.status = status


@dataclass(frozen=True)
class SessionToken:
    session_id: str
    session_token: str


class LiveAvatarClient(Protocol):
    async def create_session_token(self, *, avatar_id: str, max_session_duration: int, is_sandbox: bool) -> SessionToken: ...


class HttpLiveAvatarClient:
    """`POST /v1/sessions/token` in FULL mode. Never called from a test."""

    def __init__(self, api_key: str, base_url: str = LIVEAVATAR_API_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def create_session_token(self, *, avatar_id: str, max_session_duration: int, is_sandbox: bool) -> SessionToken:
        # FULL mode needs exactly one of avatar_persona or voice_agent, otherwise 422.
        body: dict[str, Any] = {
            "mode": "FULL",
            "avatar_id": avatar_id,
            "is_sandbox": is_sandbox,
            # LiveAvatar has only CONVERSATIONAL and PUSH_TO_TALK; neither is a no-listening mode. In
            # PUSH_TO_TALK, voice detection and speech recognition stay off until the app sends
            # `user.start_push_to_talk`. Nothing in DxP ever sends it or starts listening (Luis, V70:
            # no voice input today), and the app's Permissions-Policy (#45) blocks the microphone.
            # The avatar only speaks what the page gives it with `repeat(text)`.
            "interactivity_type": "PUSH_TO_TALK",
            "max_session_duration": max_session_duration,
            # DxP's voice outside sandbox; sandbox sessions keep the sandbox avatar's own voice.
            "avatar_persona": {"language": "en"} if is_sandbox else {"language": "en", "voice_id": voice_id()},
        }
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as http:
                response = await http.post(
                    self._base_url + TOKEN_PATH,
                    json=body,
                    headers={"X-API-KEY": self._api_key, "Content-Type": "application/json"},
                )
        except httpx.HTTPError:
            raise LiveAvatarError(None) from None  # httpx error text can carry the URL: keep none of it
        if response.status_code != 200:
            raise LiveAvatarError(response.status_code)
        try:
            data = response.json()["data"]
            session_id, token = data["session_id"], data["session_token"]
        except (ValueError, KeyError, TypeError):
            raise LiveAvatarError(response.status_code) from None
        if not isinstance(session_id, str) or not isinstance(token, str) or not session_id or not token:
            raise LiveAvatarError(response.status_code)
        return SessionToken(session_id=session_id, session_token=token)


_client_override: LiveAvatarClient | None = None


def set_client(client: LiveAvatarClient | None) -> None:
    """Install a fake client (tests) or clear it. Production uses `HttpLiveAvatarClient`."""
    global _client_override
    _client_override = client


def _client(api_key: str) -> LiveAvatarClient:
    return _client_override or HttpLiveAvatarClient(api_key)


# ---------------------------------------------------------------------------
# Storage seam: reports (read) and media (B08 is its only writer)
# ---------------------------------------------------------------------------


class AvatarStore(Protocol):
    async def get_report(self, report_id: str) -> dict[str, Any] | None: ...
    async def insert_media(self, doc: dict[str, Any]) -> None: ...
    async def latest_media(self, report_id: str) -> dict[str, Any] | None: ...
    async def claim_action(self, action_id: str) -> bool: ...
    async def settle_action(self, action_id: str, status: str, result: dict[str, Any] | None = None) -> bool: ...


class MongoAvatarStore:
    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        from dxp import store

        return await store.collection("reports").find_one({"_id": report_id})

    async def insert_media(self, doc: dict[str, Any]) -> None:
        from pymongo.errors import DuplicateKeyError

        from dxp import store

        try:
            await store.collection("media").insert_one(doc)
        except DuplicateKeyError:
            pass  # the same Decision already recorded its media: insert-if-absent

    async def latest_media(self, report_id: str) -> dict[str, Any] | None:
        from dxp import store

        found = await store.collection("media").find({"report_id": report_id}).sort("created_at", -1).limit(1).to_list(length=1)
        return found[0] if found else None

    # The gate's `mark_action` settles DxP-state actions only (queued to done or failed), so these two
    # conditional updates are B08's own (V71, an exception to V65): AD-20 claim and settle.

    async def claim_action(self, action_id: str) -> bool:
        """`queued` to `dispatching`, conditional: only the worker whose update matched calls LiveAvatar."""
        from dxp import store

        res = await store.collection("actions").update_one(
            {"_id": action_id, "status": "queued"}, {"$set": {"status": "dispatching", "claimed_at": _now()}}
        )
        if not res.modified_count:
            return False
        await self._emit(action_id, "dispatching")
        return True

    async def settle_action(self, action_id: str, status: str, result: dict[str, Any] | None = None) -> bool:
        """`dispatching` to `delivered`, `failed` or `unknown`, conditional on `dispatching`."""
        from dxp import store

        res = await store.collection("actions").update_one(
            {"_id": action_id, "status": "dispatching"},
            {"$set": {"status": status, "result": result, "observed_at": _now()}},
        )
        if not res.modified_count:
            return False
        await self._emit(action_id, status)
        return True

    async def _emit(self, action_id: str, status: str) -> None:
        from dxp import store

        act = await store.collection("actions").find_one({"_id": action_id}) or {}
        await store.emit_event(
            {
                "type": "action_status_changed",
                "dedupe_key": f"action_status_changed|{action_id}|{status}",
                "mode": act.get("mode"),
                "run_id": act.get("run_id"),
                "stamp": act.get("stamp"),
                "decision_id": act.get("decision_id"),
                "action_id": action_id,
                "status": status,
            }
        )


_store_override: AvatarStore | None = None


def set_store(store: AvatarStore | None) -> None:
    """Install an in-memory store (tests) or clear it."""
    global _store_override
    _store_override = store


def _store() -> AvatarStore:
    return _store_override or MongoAvatarStore()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class AvatarOutcome:
    """The token and its expiry live only here, in memory, until the route puts them in AvatarResponse."""

    media: Media
    decision: Decision
    session_token: str | None = None
    session_expires_at: datetime | None = None
    reason: UnavailableReason | None = None


def media_model(doc: dict[str, Any]) -> Media:
    return Media.model_validate({**doc, "id": doc.get("id") or doc["_id"]})


def _now() -> datetime:
    return datetime.now(UTC)


def _max_seconds() -> int:
    raw = os.environ.get(MAX_SECONDS_ENV, "").strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MAX_SESSION_SECONDS
    return value if 10 <= value <= 600 else DEFAULT_MAX_SESSION_SECONDS


# ---------------------------------------------------------------------------
# The Reviewer's context (a Reviewer route builds it, AD-17, D19)
# ---------------------------------------------------------------------------


async def reviewer_context(principal: Principal, api_key: str, report: dict[str, Any]) -> RunContext:
    """A Reviewer decision carries no run: `run_id` and `agent` are null, the stamp is the Reviewer's,
    with a server-made request id and the report as its cause (D19, D20). The caller is resolved from
    the key, never from the request body."""
    grant = await auth.grant_for_key(api_key)
    if grant is None:
        raise ApiError(401, "unknown_key", "Unknown API key.")
    stamp = Stamp(
        kind="reviewer",
        run_id=None,
        agent=None,
        initiated_by=principal.id,
        principal=principal.id,
        acting_for=grant.get("acting_for"),
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
    )
    return RunContext(
        run_id=None,
        principal=principal,
        stamp=stamp,
        grant_id=grant["grant_id"],
        grant_version=grant["version"],
        request_id="req_" + uuid.uuid4().hex[:16],
        cause=DecisionCause(report_id=report["_id"], origin_run_id=report.get("run_id")),
    )


# ---------------------------------------------------------------------------
# start_avatar_session, render_avatar, avatar_status
# ---------------------------------------------------------------------------


def _transient_media(report_id: str, decision: Decision, script_hash: str | None) -> Media:
    """A blocked request records no media: this is the unsaved answer the route returns with the Decision."""
    return Media(
        id=derive("media_", decision.id),
        report_id=report_id,
        status="unavailable",
        script_hash=script_hash,
        decision_id=decision.id,
        created_at=_now(),
    )


async def start_avatar_session(report_id: str, ctx: RunContext) -> AvatarOutcome:
    """Gate, then mint one live session token. Called only from `POST /reports/<report_id>/avatar`."""
    store = _store()
    report = await store.get_report(report_id)
    if report is None:
        raise ApiError(404, "not_found", "Report not found.")
    if report.get("status") != "accepted":
        # Before the gate and before any provider call: only an accepted report is interviewed (V70).
        raise ApiError(409, "report_not_accepted", "The avatar is available only for an accepted report.")
    script_hash = report.get("script_hash")

    # 1. The gate, before any call to LiveAvatar. The Decision is recorded allowed or blocked.
    decision = await gate.evaluate(
        ctx,
        ProposedAction(
            kind="generate_avatar_video",
            destination="video:heygen",
            target=Target(report_id=report_id),
            inputs={"provider": "liveavatar", "mode": "FULL"},
            evidence_ref=EvidenceRef(report_id=report_id),
        ),
    )
    if decision.outcome != "allowed":
        return AvatarOutcome(_transient_media(report_id, decision, script_hash), decision, reason="blocked")

    # 2. Allowed: claim the action (AD-20), then mint the token and settle what was observed.
    action_id = decision.action_id
    if action_id:
        try:
            claimed = await store.claim_action(action_id)
        except Exception:  # noqa: BLE001 - not claimed means nothing is sent
            log.warning("Could not claim the avatar action for %s", report_id)
            claimed = False
        if not claimed:
            # Another worker holds it or it is already settled: never sent twice.
            return AvatarOutcome(_transient_media(report_id, decision, script_hash), decision, reason="not_claimed")

    token: SessionToken | None = None
    expires_at: datetime | None = None
    reason: UnavailableReason | None = None
    settle_as: str | None = None  # "failed" (definite) or "unknown" (ambiguous); None once delivered
    api_key = os.environ.get(KEY_ENV, "").strip()
    is_sandbox = os.environ.get(SANDBOX_ENV, "").strip().lower() in {"1", "true", "yes", "on"}
    # Sandbox accepts only its own free avatar; otherwise DxP's avatar unless the env overrides it.
    avatar_id = SANDBOX_AVATAR_ID if is_sandbox else (os.environ.get(AVATAR_ID_ENV, "").strip() or DXP_AVATAR_ID)
    max_seconds = _max_seconds()
    if not api_key:
        reason, settle_as = "no_key", "failed"  # nothing was sent
    else:
        try:
            minted_at = _now()
            token = await _client(api_key).create_session_token(
                avatar_id=avatar_id, max_session_duration=max_seconds, is_sandbox=is_sandbox
            )
            # The token cannot outlive the session it opens, so the session ceiling bounds its expiry.
            expires_at = minted_at + timedelta(seconds=max_seconds)
        except LiveAvatarError as exc:
            # The status only: never the response body, the headers or the key.
            log.warning("LiveAvatar did not issue a session token (status %s)", exc.status)
            reason = "provider_error"
            # A 4xx is a definite rejection. A timeout, a network error, a 5xx or an unreadable 200 may
            # have created a session: ambiguous, so `unknown`, never retried.
            settle_as = "failed" if exc.status is not None and 400 <= exc.status < 500 else "unknown"
        except Exception:  # noqa: BLE001 - a provider failure never reaches the report or the loop
            log.warning("LiveAvatar session token request failed unexpectedly")
            reason, settle_as = "provider_error", "unknown"

    # 3. Record the media: report_id, status, decision_id, provider. The token is not stored.
    doc: dict[str, Any] = {
        "_id": derive("media_", decision.id),
        "report_id": report_id,
        "kind": "avatar_video",
        "provider": "heygen",  # Media.provider is Literal["heygen"] (A01); a contract change, see the B08 report
        "provider_video_id": token.session_id if token else None,
        "status": "ready" if token else "unavailable",
        "video_url": None,
        "script_hash": script_hash,
        "decision_id": decision.id,
        "created_at": _now(),
        "checked_at": None,
    }
    try:
        await store.insert_media(doc)
    except Exception:  # noqa: BLE001 - failing to record must not lose a minted token or break the report
        log.warning("Could not record the avatar media for %s", report_id)

    # 4. Settle the action, conditional on `dispatching`. The result never carries the token.
    if action_id:
        try:
            if token is not None:
                await store.settle_action(action_id, "delivered", {"media_id": doc["_id"], "provider_video_id": token.session_id})
            else:
                await store.settle_action(action_id, settle_as or "unknown")
        except Exception:  # noqa: BLE001 - a settle failure must not lose a minted token
            log.warning("Could not settle the avatar action for %s", report_id)
    return AvatarOutcome(media_model(doc), decision, token.session_token if token else None, expires_at, reason)


async def render_avatar(report_id: str, ctx: RunContext) -> tuple[Media, Decision]:
    """Frozen signature (A01). Gated `generate_avatar_video` to `video:heygen` under `sam@v1`; returns
    at once. The route calls `start_avatar_session`, which also hands back the session token; this
    wrapper keeps the frozen shape and drops it."""
    outcome = await start_avatar_session(report_id, ctx)
    return outcome.media, outcome.decision


async def get_report(report_id: str) -> dict[str, Any] | None:
    """The stored report document (read only), for the route's 404 and the Reviewer context's cause."""
    return await _store().get_report(report_id)


async def avatar_status(report_id: str) -> Media | None:
    """Frozen signature (A01). The latest Media for the report, or None. A live session has nothing
    to check with LiveAvatar in the background; `ready` means a session token was issued."""
    doc = await _store().latest_media(report_id)
    return media_model(doc) if doc else None
