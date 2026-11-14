import "server-only";

import { type NextRequest } from "next/server";

/**
 * The streaming proxy for a run's change stream (Story 9.12, V48, AD-23).
 *
 * `/api/stream/<run_id>` is forwarded to `<NEXT_PUBLIC_API_URL>/api/v1/runs/<run_id>/stream`
 * with the reviewer key from the server-only DXP_API_KEY added as `X-DxP-Key`, so the
 * browser never holds the key. The response body is passed through as it arrives, and
 * `Last-Event-ID` is passed on so a reconnect resumes where the stream left off. A
 * browser that cannot set that header on a fresh EventSource may send `?lastEventId=`
 * instead; it is turned into the header here.
 *
 * Anything but a 200 `text/event-stream` answer (a 404 with `live_stream` off in the
 * API, A01's 501 stub before A27 is merged, a 401, a network failure) is returned as a
 * plain JSON error with the API's status, which makes EventSource fail so the screen
 * falls back to polling.
 *
 * It does not use lib/server/upstream.ts: that helper puts a 30-second timeout on the
 * whole request, which would cut every stream. Here the timeout covers only the wait
 * for the first response, and the stream then runs until either side closes it.
 */

// Streams end themselves before the hosting limit (AD-23); this is the ceiling for the platform.
export const maxDuration = 300;

const RUN_ID = /^[A-Za-z0-9_-]{1,128}$/;
/** Resume tokens are opaque printable text. Anything else is not sent upstream. */
const EVENT_ID = /^[\x20-\x7e]{1,4096}$/;
const CONNECT_TIMEOUT_MS = 30_000;

type Ctx = { params: Promise<{ run_id: string }> };

function fail(status: number, error: string, message: string): Response {
  return Response.json({ error, message }, { status, headers: { "Cache-Control": "no-store" } });
}

export async function GET(request: NextRequest, ctx: Ctx): Promise<Response> {
  const { run_id: runId } = await ctx.params;
  if (!RUN_ID.test(runId)) {
    return fail(400, "bad_run_id", "That run ID is not allowed.");
  }

  const origin = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, "");
  const key = process.env.DXP_API_KEY?.trim();
  if (!origin || !key) {
    return fail(503, "not_configured", "API access is not configured on the web server.");
  }

  const headers: Record<string, string> = {
    "X-DxP-Key": key,
    Accept: "text/event-stream",
    "Cache-Control": "no-cache",
  };
  const lastEventId = request.headers.get("last-event-id") ?? request.nextUrl.searchParams.get("lastEventId");
  if (lastEventId && EVENT_ID.test(lastEventId)) headers["Last-Event-ID"] = lastEventId;

  // One controller ends the upstream request when the browser goes away or the connect wait runs out.
  const controller = new AbortController();
  const onClientAbort = () => controller.abort();
  request.signal.addEventListener("abort", onClientAbort, { once: true });
  const connectTimer = setTimeout(() => controller.abort(), CONNECT_TIMEOUT_MS);

  let upstream: Response;
  try {
    upstream = await fetch(`${origin}/api/v1/runs/${encodeURIComponent(runId)}/stream`, {
      method: "GET",
      headers,
      cache: "no-store",
      redirect: "manual",
      signal: controller.signal,
    });
  } catch {
    request.signal.removeEventListener("abort", onClientAbort);
    return fail(502, "api_unreachable", "Couldn't reach the API.");
  } finally {
    clearTimeout(connectTimer);
  }

  const type = upstream.headers.get("content-type") ?? "";
  if (upstream.status !== 200 || !type.toLowerCase().startsWith("text/event-stream") || !upstream.body) {
    request.signal.removeEventListener("abort", onClientAbort);
    await upstream.body?.cancel().catch(() => undefined);
    const status = upstream.status >= 400 ? upstream.status : 502;
    return fail(status, "stream_unavailable", "The live stream is not available.");
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-store, no-transform",
      // Ask proxies in front of this route not to buffer the stream.
      "X-Accel-Buffering": "no",
    },
  });
}
