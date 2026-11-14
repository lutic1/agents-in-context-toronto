"""The live avatar session for a report's script (Story 10.12, B08; V29, V41; AD-30).

Vlad changed the avatar on 14 Nov from a pre-rendered HeyGen video to a HeyGen LiveAvatar, a live
and interactive avatar. The change is pending Luis's approval as a new ruling (to be numbered V70).
It is contained in this module and `api/routes_avatar.py`, and in `web/app/reports/[report_id]/avatar/`.

What the backend does, and no more:

1. The report must exist and carry its stored script (`report.script`, V41); this module never
   builds one.
2. The request is gated as `generate_avatar_video` to `video:heygen` under the Reviewer's grant
   (`sam@v1`), before any call to LiveAvatar. A blocked Decision makes no call.
3. Once allowed, it mints one FULL-mode session token on the server with
   `POST https://api.liveavatar.com/v1/sessions/token` (header `X-API-KEY`, from `LIVEAVATAR_API_KEY`),
   with a short `max_session_duration`, and returns only the session token and the session id.
4. It records a `media` document `{ report_id, status, provider_video_id = session id, ... }`.
   The token itself is never stored, logged, traced or returned anywhere else.

Nothing here runs unless a Reviewer asks (V29), and nothing waits on it: the report, the Slack alert,
the decision, the task and the rehearsal never call this module. A missing key, a missing avatar id
or a provider failure leaves the media `unavailable`; the script stays on the page as text.

Docs: https://docs.liveavatar.com/api-reference/full-mode/sessions/create-session-token.md
      https://docs.liveavatar.com/docs/full-mode/overview.md
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

import httpx
from pydantic import BaseModel

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
# The plan, .env.example and docs/deploy.md still name HEYGEN_API_KEY (OD7). Until those files
# are brought in step, it is read as a fallback so a deployment set up from them still works.
KEY_FALLBACK_ENV = "HEYGEN_API_KEY"
AVATAR_ID_ENV = "LIVEAVATAR_AVATAR_ID"  # not secret: which LiveAvatar avatar speaks (a UUID)
SANDBOX_ENV = "LIVEAVATAR_SANDBOX"  # "true" asks for sandbox mode, which consumes no credits
MAX_SECONDS_ENV = "LIVEAVATAR_MAX_SECONDS"

# About ten seconds of script, so a short ceiling: 2 credits a minute in FULL mode caps one
# session at 4 credits.
DEFAULT_MAX_SESSION_SECONDS = 120
REQUEST_TIMEOUT_SECONDS = 15.0

UnavailableReason = Literal["blocked", "no_key", "no_avatar", "provider_error"]


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
        body: dict[str, Any] = {
            "mode": "FULL",
            "avatar_id": avatar_id,
            "max_session_duration": max_session_duration,
            # The page keeps the microphone off and never calls startListening. Push to talk
            # makes the agent ignore audio outside a push window as well.
            "interactivity_type": "PUSH_TO_TALK",
        }
        if is_sandbox:
            body["is_sandbox"] = True
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


class AvatarSession(BaseModel):
    """What the browser needs to join the live session, and nothing else (the proposed contract
    change in the B08 report: `AvatarResponse.session`)."""

    session_id: str
    session_token: str
    max_session_duration: int
    provider: Literal["liveavatar"] = "liveavatar"


@dataclass
class AvatarOutcome:
    media: Media
    decision: Decision
    session: AvatarSession | None = None
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
    script = report.get("script")
    if not isinstance(script, str) or not script.strip():
        raise ApiError(409, "no_script", "This report has no stored script yet.")
    script_hash = report.get("script_hash")

    # 1. The gate, before any call to LiveAvatar. The Decision is recorded allowed or blocked.
    decision = await gate.evaluate(
        ctx,
        ProposedAction(
            kind="generate_avatar_video",
            destination="video:heygen",
            target=Target(report_id=report_id),
            # The exact text the avatar will speak (report.script, V41), so check 4 can compare it.
            inputs={"text": script, "script_hash": script_hash, "provider": "liveavatar", "mode": "FULL"},
            evidence_ref=EvidenceRef(report_id=report_id),
        ),
    )
    if decision.outcome != "allowed":
        return AvatarOutcome(_transient_media(report_id, decision, script_hash), decision, None, "blocked")

    # 2. Allowed: mint the token, or record why the avatar is unavailable.
    session: AvatarSession | None = None
    reason: UnavailableReason | None = None
    api_key = os.environ.get(KEY_ENV, "").strip() or os.environ.get(KEY_FALLBACK_ENV, "").strip()
    avatar_id = os.environ.get(AVATAR_ID_ENV, "").strip()
    max_seconds = _max_seconds()
    if not api_key:
        reason = "no_key"
    elif not avatar_id:
        reason = "no_avatar"
    else:
        try:
            token = await _client(api_key).create_session_token(
                avatar_id=avatar_id,
                max_session_duration=max_seconds,
                is_sandbox=os.environ.get(SANDBOX_ENV, "").strip().lower() in {"1", "true", "yes", "on"},
            )
            session = AvatarSession(session_id=token.session_id, session_token=token.session_token, max_session_duration=max_seconds)
        except LiveAvatarError as exc:
            # The status only: never the response body, the headers or the key.
            log.warning("LiveAvatar did not issue a session token (status %s)", exc.status)
            reason = "provider_error"
        except Exception:  # noqa: BLE001 - a provider failure never reaches the report or the loop
            log.warning("LiveAvatar session token request failed unexpectedly")
            reason = "provider_error"

    # 3. Record the media. The token is not stored.
    doc: dict[str, Any] = {
        "_id": derive("media_", decision.id),
        "report_id": report_id,
        "kind": "avatar_video",
        "provider": "heygen",
        "provider_video_id": session.session_id if session else None,
        "status": "ready" if session else "unavailable",
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
    return AvatarOutcome(media_model(doc), decision, session, reason)


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
