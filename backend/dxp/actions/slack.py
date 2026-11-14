"""The only module that posts to Slack (AD-20): one incoming webhook to `#all-mango-db-hackathon`.

- Configuration (S3): `SLACK_WEBHOOK_URL` is a credential, read from the environment only
  and never logged, stored, returned or shown; `DXP_BASE_URL` builds the links back to DxP.
  `require_config()` refuses to start without either (no link is ever built from an empty
  base URL).
- The message (S5, V11, V33, V37, V43): one Block Kit alert per report. Links only, no
  interactive elements (S4): Slack sends nothing back, and approval happens only in DxP.
- The sender: `post(url, payload)` returns what was observed. Tests and smoke runs install
  a recording sender with `use_sender()` (A01's `fake_slack`), so nothing reaches Slack.
- The observed outcome (S7): HTTP 200 with body `ok` is `delivered`; 429 is retried once by
  the dispatcher; another 4xx is `failed`; a timeout, a connection error, a 5xx or any other
  answer is `unknown`, never retried.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

import httpx

log = logging.getLogger("dxp.actions.slack")

DESTINATION = "slack:#all-mango-db-hackathon"
CHANNEL = "#all-mango-db-hackathon"
WEBHOOK_ENV = "SLACK_WEBHOOK_URL"
BASE_URL_ENV = "DXP_BASE_URL"

TIMEOUT_S = 10.0
MAX_BODY_CHARS = 2000
QUOTE_CHARS = 300  # AD-6: a quote in the alert is at most 300 characters

HEADER = "New research report for review"
CONTEXT_LINE = "Approve or reject in DxP. Slack only notifies."
REVIEW_LABEL = "Review in DxP"
DIAGNOSTIC_LABEL = "Open diagnostic"

# Relationship labels in words (EXPERIENCE.md, "Relationship label").
LABEL_WORDS = {
    "supports": "Supports",
    "contradicts": "Contradicts",
    "extends": "Extends",
    "new_question": "New question",
    "related_unestablished": "Related (no relationship established)",
}
LABEL_ORDER = ["supports", "contradicts", "extends", "new_question", "related_unestablished"]


class NotSent(Exception):
    """The request was refused before anything went on the wire (a malformed URL, a payload
    that cannot be encoded): nothing was sent, so the outcome is `failed`, not `unknown`."""


class SenderNotConfigured(RuntimeError):
    """`SLACK_WEBHOOK_URL` or `DXP_BASE_URL` is missing: the sender refuses to start (S3, D37).
    The message names the variable, never its value."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    webhook_url: str = field(repr=False)  # a credential: never in a repr, a log or a document
    base_url: str


def require_config() -> Config:
    """Both variables, or `SenderNotConfigured`. The base URL must be an absolute http(s) URL."""
    webhook = os.environ.get(WEBHOOK_ENV, "").strip()
    base = os.environ.get(BASE_URL_ENV, "").strip().rstrip("/")
    missing = [name for name, value in ((WEBHOOK_ENV, webhook), (BASE_URL_ENV, base)) if not value]
    if missing:
        raise SenderNotConfigured(f"The Slack sender refuses to start: {', '.join(missing)} is not set.")
    if not base.startswith(("https://", "http://")):
        raise SenderNotConfigured(f"The Slack sender refuses to start: {BASE_URL_ENV} must be an http(s) URL.")
    if not webhook_url_is_valid(webhook):
        # The message names the variable, never its value.
        raise SenderNotConfigured(f"The Slack sender refuses to start: {WEBHOOK_ENV} must be an https URL with a host.")
    return Config(webhook_url=webhook, base_url=base)


LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def webhook_url_is_valid(value: str) -> bool:
    """An https URL with a host and a path. Plain http is accepted only for a local fake on
    this machine (tests), never for a remote host."""
    try:
        url = httpx.URL(value)
    except Exception:  # noqa: BLE001 - any parse error means not valid
        return False
    if not url.host or url.path in ("", "/"):
        return False
    return url.scheme == "https" or (url.scheme == "http" and url.host in LOCAL_HOSTS)


# ---------------------------------------------------------------------------
# The webhook URL never reaches a log (AD-20)
# ---------------------------------------------------------------------------


class _RedactWebhook(logging.Filter):
    """httpx logs every request line with its URL at INFO, on the `httpx` logger itself.
    Replace the webhook URL (and any Slack hooks URL) in such records before any handler sees
    them. A logger filter applies only to records logged on that exact logger (not to records
    propagated from its children), so the filter is attached to each logger named below; no
    other logger is known to log the URL (httpcore logs only the host)."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a broken record is left to logging itself
            return True
        webhook = os.environ.get(WEBHOOK_ENV, "").strip()
        redacted = message
        if webhook and webhook in redacted:
            redacted = redacted.replace(webhook, "[slack webhook]")
        if "hooks.slack.com" in redacted:
            redacted = "[a Slack webhook request; URL withheld]"
        if redacted != message:
            record.msg, record.args = redacted, ()
        return True


_REDACT = _RedactWebhook()
for _name in ("httpx", "httpcore", "httpcore.connection", "httpcore.http11", "dxp.actions", "dxp.actions.slack"):
    _logger = logging.getLogger(_name)
    if not any(isinstance(f, _RedactWebhook) for f in _logger.filters):
        _logger.addFilter(_REDACT)


# ---------------------------------------------------------------------------
# Links and the message
# ---------------------------------------------------------------------------


def link_urls(base_url: str, report_id: str, diagnostic_id: str | None) -> dict[str, str | None]:
    """`result.link_urls` (D44): "Review in DxP" always; "Open diagnostic" only for a resolved
    in-scope Diagnostic, else null (V43)."""
    base = base_url.rstrip("/")
    if not base:
        raise SenderNotConfigured(f"The Slack sender refuses to start: {BASE_URL_ENV} is not set.")
    return {
        "report_url": f"{base}/reports/{quote(report_id, safe='')}",
        "diagnostic_url": f"{base}/diagnostics/{quote(diagnostic_id, safe='')}" if diagnostic_id else None,
    }


def _esc(text: Any) -> str:
    """Slack mrkdwn escaping: only &, < and > are control characters."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cut(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _words(status: str | None) -> str | None:
    if not status:
        return None
    return status.replace("_", " ").strip().capitalize()


def ctgov_url(nct_id: str) -> str:
    return f"https://clinicaltrials.gov/study/{quote(nct_id, safe='')}"


def relationship_summary(related: list[dict[str, Any]]) -> str:
    """Counts by label, in words: "Extends 1, Related (no relationship established) 2"."""
    counts: dict[str, int] = {}
    for rel in related or []:
        label = rel.get("label") or "related_unestablished"
        counts[label] = counts.get(label, 0) + 1
    if not counts:
        return "No related evidence in the scope"
    ordered = [lab for lab in LABEL_ORDER if lab in counts] + sorted(set(counts) - set(LABEL_ORDER))
    return ", ".join(f"{LABEL_WORDS.get(lab, lab)} {counts[lab]}" for lab in ordered)


def strongest_relationship(related: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The established relationship (both quotes found, AD-26) with the highest similarity.
    Display only: similarity picks which one the alert shows, never a label or a claim (AD-15)."""
    established = [
        r
        for r in related or []
        if r.get("label") not in (None, "related_unestablished")
        and (r.get("new_quote") or {}).get("quote_found")
        and (r.get("related_quote") or {}).get("quote_found")
    ]
    if not established:
        return None
    return max(established, key=lambda r: r.get("similarity") or 0.0)


def describe_update(proposal: dict[str, Any], nct_id: str | None) -> str:
    """One pending update in words. A scope-collection update names no Diagnostic (V35, V43)."""
    if proposal.get("diagnostic_id") is None and proposal.get("field") == "evidence_collection":
        subject = f"trial {nct_id}" if nct_id else (proposal.get("value") or "the discovery")
        return f"Add {subject} to the scope's evidence collection"
    who = proposal.get("diagnostic_name") or proposal.get("diagnostic_id") or "the scope"
    verb = "Remove" if proposal.get("op") == "remove" else "Add"
    return f"{verb} {proposal.get('field')} \"{proposal.get('value')}\" for {who}"


@dataclass
class Actor:
    """Who acted (S5): the agent, the run, the grant and the policy set."""

    agent: str | None
    run_id: str | None
    grant: str | None
    policy_set_version: str | None


def build_message(
    *,
    action_id: str,
    report: dict[str, Any],
    proposals: list[dict[str, Any]],
    links: dict[str, str | None],
    actor: Actor,
) -> dict[str, Any]:
    """The Block Kit payload. Built only from the report's own fields (AD-30): its headline,
    which the gate already checked (V33, V37), its discovery, gap and relationships. The
    wording added here never says a trial "uses" or "studies" a named product."""
    discovery = report.get("discovery") or {}
    nct_id = report.get("nct_id")
    headline = _cut(report.get("headline") or "New trial signal", 600)
    header = _cut(f"{HEADER} ({action_id})", 150)

    blocks: list[dict[str, Any]] = [
        {"type": "header", "text": {"type": "plain_text", "text": header, "emoji": False}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{_esc(headline)}*"}},
    ]

    facts: list[str] = []
    if nct_id:
        facts.append(f"*Discovery:* <{ctgov_url(nct_id)}|{_esc(nct_id)}> on ClinicalTrials.gov")
    status = _words(discovery.get("trial_status"))
    if status:
        facts.append(f"*Status:* {_esc(status)}")
    if discovery.get("has_results") is False:
        facts.append("*Results:* No results posted")
    if facts:
        blocks.append({"type": "section", "fields": [{"type": "mrkdwn", "text": f} for f in facts]})

    quotes = [q for q in discovery.get("quotes") or [] if q.get("quote_found") and q.get("text")]
    if quotes:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Evidence:* \"{_esc(_cut(quotes[0]['text'], QUOTE_CHARS))}\""}}
        )

    related = report.get("related") or []
    rel_text = f"*Related evidence:* {_esc(relationship_summary(related))}"
    strongest = strongest_relationship(related)
    if strongest:
        title = strongest.get("related_title") or strongest.get("related_ref")
        quote_text = (strongest.get("related_quote") or {}).get("text") or ""
        rel_text += f"\nStrongest: {LABEL_WORDS.get(strongest['label'], strongest['label'])} {_esc(title)}"
        if quote_text:
            rel_text += f": \"{_esc(_cut(quote_text, QUOTE_CHARS))}\""
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": _cut(rel_text, 2900)}})

    if report.get("gap"):
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Evidence gap:* {_esc(_cut(report['gap'], 600))}"}})

    if proposals:
        lines = [describe_update(p, nct_id) for p in proposals[:5]]
        more = len(proposals) - len(lines)
        text = "*Proposed update, pending review:* " + "; ".join(_esc(line) for line in lines)
        if more > 0:
            text += f"; and {more} more"
    else:
        count = len(report.get("proposal_ids") or [])
        text = f"*Proposed updates, pending review:* {count}"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": _cut(text, 2900)}})

    who = [
        f"agent `{_esc(actor.agent)}`" if actor.agent else None,
        f"run `{_esc(actor.run_id)}`" if actor.run_id else None,
        f"grant `{_esc(actor.grant)}`" if actor.grant else None,
        f"policy set `{_esc(actor.policy_set_version)}`" if actor.policy_set_version else None,
    ]
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Who acted:* " + " · ".join(w for w in who if w)}})

    link_line = f"<{links['report_url']}|{REVIEW_LABEL}>"
    if links.get("diagnostic_url"):
        link_line += f"   ·   <{links['diagnostic_url']}|{DIAGNOSTIC_LABEL}>"
    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": link_line}})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": CONTEXT_LINE}]})

    return {
        "text": _cut(f"{HEADER} ({action_id}): {headline}. {CONTEXT_LINE}", 1000),
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False,
    }


# ---------------------------------------------------------------------------
# The sender
# ---------------------------------------------------------------------------


@dataclass
class Observed:
    """What one post observed: the HTTP status, the body and the headers (no URL)."""

    status: int
    body: str
    headers: dict[str, str] = field(default_factory=dict)


Sender = Callable[..., Awaitable[Any]]


async def http_post(url: str, payload: dict[str, Any], *, timeout: float) -> Observed:
    """The real sender: one POST to the webhook, no redirects followed, nothing retried here."""
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        try:
            request = client.build_request("POST", url, json=payload)
        except (httpx.InvalidURL, TypeError, ValueError) as exc:
            raise NotSent(type(exc).__name__) from None
        try:
            response = await client.send(request)
        except (httpx.UnsupportedProtocol, httpx.InvalidURL) as exc:
            # Raised by the transport before any connection is made.
            raise NotSent(type(exc).__name__) from None
        return Observed(response.status_code, response.text, dict(response.headers))


_sender: Sender = http_post


@contextmanager
def use_sender(sender: Sender) -> Iterator[None]:
    """Install a sender (for example A01's `fake_slack`) for the duration of a block."""
    global _sender
    previous, _sender = _sender, sender
    try:
        yield
    finally:
        _sender = previous


async def post(webhook_url: str, payload: dict[str, Any]) -> Observed:
    """One post through the installed sender. Raises on a timeout or connection error."""
    reply = await _sender(webhook_url, payload, timeout=TIMEOUT_S)
    status = int(getattr(reply, "status", None) or getattr(reply, "status_code"))
    body = getattr(reply, "body", None)
    if body is None:
        body = getattr(reply, "text", "")
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    headers = {str(k).lower(): str(v) for k, v in (getattr(reply, "headers", None) or {}).items()}
    return Observed(status, str(body)[:MAX_BODY_CHARS], headers)


def classify(observed: Observed) -> str:
    """S7: `delivered`, `failed`, `rate_limited` (429) or `unknown`."""
    if observed.status == 200 and observed.body.strip() == "ok":
        return "delivered"
    if observed.status == 429:
        return "rate_limited"
    if 400 <= observed.status < 500:
        return "failed"
    # 5xx, a 2xx that is not `ok`, a redirect: whether it posted is not known.
    return "unknown"


def retry_after_seconds(observed: Observed, default: float = 1.0, cap: float = 30.0) -> float:
    """Slack's `Retry-After` in seconds, capped so the claim's lease is never at risk."""
    raw = observed.headers.get("retry-after")
    try:
        value = float(raw) if raw is not None else default
    except ValueError:
        value = default
    return max(0.0, min(value, cap))
