"""A09: the real httpx sender against a local HTTP fake on 127.0.0.1 (never Slack).

Proves the observed-outcome rules end to end through httpx, and that httpx's own request
logging never shows the webhook URL.
"""

from __future__ import annotations

import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from dxp import actions
from dxp.actions import records, slack

from .conftest import REPORT_ID, make_report, notify, run_ctx

pytestmark = pytest.mark.usefixtures("gate")

SECRET_PATH = "/services/T0LOCAL/B0LOCAL/localSECRETtoken"


class Script:
    def __init__(self) -> None:
        self.replies: list[tuple[int, str, dict[str, str], float]] = []
        self.bodies: list[bytes] = []


@pytest.fixture
def webhook(monkeypatch):
    script = Script()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            script.bodies.append(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            status, body, headers, delay = script.replies.pop(0) if script.replies else (200, "ok", {}, 0.0)
            if delay:
                time.sleep(delay)
            data = body.encode()
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", f"http://127.0.0.1:{server.server_address[1]}{SECRET_PATH}")
    yield script
    server.shutdown()
    server.server_close()


async def dispatch_one(mem, report_id: str = REPORT_ID):
    mem["reports"].docs.setdefault(report_id, make_report(_id=report_id, proposal_ids=[]))
    return await actions.dispatch(notify(report_id=report_id), run_ctx())


async def test_local_ok_is_delivered_and_the_url_never_logged(mem, webhook, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    action = await dispatch_one(mem)
    assert action.status == "delivered" and action.result.http_status == 200
    assert len(webhook.bodies) == 1 and b"New research report for review" in webhook.bodies[0]
    assert "localSECRETtoken" not in caplog.text
    assert "localSECRETtoken" not in str(mem["actions"].docs) + str(mem.events)


async def test_local_429_then_ok(mem, webhook, waits) -> None:
    webhook.replies.append((429, "rate_limited", {"Retry-After": "0"}, 0.0))
    action = await dispatch_one(mem)
    assert action.status == "delivered" and len(webhook.bodies) == 2 and waits == [0.0]


@pytest.mark.parametrize(("status", "expected"), [(404, "failed"), (400, "failed"), (500, "unknown")])
async def test_local_status_codes(mem, webhook, status, expected) -> None:
    webhook.replies.append((status, "no_service", {}, 0.0))
    action = await dispatch_one(mem)
    assert action.status == expected and len(webhook.bodies) == 1


async def test_local_timeout_is_unknown_and_not_retried(mem, webhook, monkeypatch, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(slack, "TIMEOUT_S", 0.2)
    webhook.replies.append((200, "ok", {}, 1.0))
    action = await dispatch_one(mem)
    assert action.status == "unknown" and action.result.http_status is None
    assert len(webhook.bodies) == 1
    assert (await records.get(action.id))["status"] == "unknown"
    assert "localSECRETtoken" not in caplog.text
