# Live updates in the browser (FR-27, FR-13, FR-4)

Checked 12 November 2026. TypeScript type-checked against `@types/react` 19.3.0; not run in a browser. The Python is a sketch of the contract; the working Modal code is in the `dxp-modal` skill.

## Design

- The Python API on Modal serves `GET /events` as server-sent events (`text/event-stream`).
- A Client Component opens it with `EventSource`, directly from the browser to Modal. Vercel is not in the path, so its duration limit does not apply.
- An event is a nudge, not the data. On every event, and on every reconnect, the client refetches the JSON it shows. Nothing is lost if an event is missed.
- The server ends each stream after about 120 s, because Modal caps an HTTP request at 150 s. `EventSource` reconnects by itself.

## Event contract

One frame per event, a blank line after it. Lines starting with `:` are comments and keep the connection alive.

```
retry: 2000

data: {"type":"change","summary":"Regulatory status updated for Example ctDNA assay","node_ids":["diagnostic:d1"],"link_keys":["diagnostic:d1->trial:NCT00000000"],"at":"2026-11-14T15:02:11Z"}

: keep-alive

data: {"type":"alert","summary":"Example ctDNA assay moved to clinical validation. Matches your profile: EGFR","node_ids":["diagnostic:d1"],"link_keys":[],"at":"2026-11-14T15:02:12Z"}

```

`type` is `"change"` (an accepted Proposed change, FR-27) or `"alert"` (FR-13). The TypeScript type is `DxpEvent` in `lib/types.ts`. Events have no `event:` field, so they arrive on `onmessage`.

## API side (Python, FastAPI on Modal)

```python
import json
import time

from fastapi.responses import StreamingResponse


@web.get("/events")
def events():
    def stream():
        deadline = time.monotonic() + 120  # end before Modal's 150 s request limit; the browser reconnects
        cursor = now_iso()                  # your helper: current time as an ISO string
        yield b"retry: 2000\n\n"            # reconnect two seconds after the stream ends
        while time.monotonic() < deadline:
            for event in events_since(cursor):  # your query: changes and Alerts newer than the cursor
                cursor = event["at"]
                yield f"data: {json.dumps(event)}\n\n".encode()
            yield b": keep-alive\n\n"
            time.sleep(2)

    return StreamingResponse(stream(), media_type="text/event-stream")
```

`events_since` can poll a collection or read a MongoDB change stream (see `dxp-mongodb-atlas`). FastAPI 0.135.0 and later also has `fastapi.sse.EventSourceResponse`, which adds the keep-alive comment and the no-cache headers for you. CORS must allow the front end's origin (see SKILL.md).

## `lib/useDxpEvents.ts`

```ts
"use client";

import { useEffect, useRef, useState } from "react";
import { API_URL } from "@/lib/api";
import type { DxpEvent } from "@/lib/types";

export type StreamStatus = "connecting" | "open" | "reconnecting";

// Subscribes to the backend's server-sent events. EventSource reconnects by itself when the
// connection drops or the server ends the response, so a server that closes every ~120 s is fine.
export function useDxpEvents(onEvent: (event: DxpEvent) => void, path = "/events"): StreamStatus {
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const handler = useRef(onEvent);

  useEffect(() => {
    handler.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const source = new EventSource(`${API_URL}${path}`);
    source.onopen = () => setStatus("open");
    source.onerror = () => setStatus("reconnecting"); // do not close here: the browser retries
    source.onmessage = (message: MessageEvent<string>) => {
      try {
        handler.current(JSON.parse(message.data) as DxpEvent);
      } catch {
        // ignore a malformed frame rather than break the stream
      }
    };
    return () => source.close();
  }, [path]);

  return status;
}
```

Usage in the Graph view is in [graph-view.md](graph-view.md). For batch progress (FR-4), pass the batch path, for example `useDxpEvents(onProgress, "/batches/" + id + "/events")`, with your own event type. That stream has a final message: close the `EventSource` when it arrives, or poll instead.

## `components/LiveAlerts.tsx`

```tsx
"use client";

import { useCallback, useState } from "react";
import type { DxpEvent } from "@/lib/types";
import { useDxpEvents } from "@/lib/useDxpEvents";

// Put <LiveAlerts /> in app/layout.tsx to show Alerts (FR-13) on every page as they arrive.
export function LiveAlerts() {
  const [alerts, setAlerts] = useState<DxpEvent[]>([]);
  const onEvent = useCallback((event: DxpEvent) => {
    if (event.type === "alert") setAlerts((current) => [event, ...current].slice(0, 5));
  }, []);
  useDxpEvents(onEvent);

  if (alerts.length === 0) return null;
  return (
    <ul aria-live="polite" className="fixed bottom-4 right-4 w-80 space-y-2 text-sm">
      {alerts.map((alert) => (
        <li key={`${alert.at}-${alert.summary}`} className="rounded border bg-white p-3 shadow">
          {alert.summary}
        </li>
      ))}
    </ul>
  );
}
```

## Fallback: `lib/usePolling.ts`

```ts
"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

// Fallback for any live view: refetch a JSON endpoint every few seconds.
export function usePolling<T>(path: string, intervalMs = 3000): T | undefined {
  const [data, setData] = useState<T>();

  useEffect(() => {
    let stopped = false;
    const tick = async () => {
      try {
        const next = await api<T>(path);
        if (!stopped) setData(next);
      } catch {
        // keep the last good value
      }
    };
    void tick();
    const timer = setInterval(tick, intervalMs);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [path, intervalMs]);

  return data;
}
```

`const graph = usePolling<GraphPayload>("/graph", 3000)` gives the same result as the stream with a delay of a few seconds. Vercel's own guidance is to poll when updates are infrequent and a few seconds of staleness is acceptable. For a three-minute demo that is good enough, and it has no moving parts.

## Optional: same-origin proxy through Vercel

Only if the browser cannot reach Modal directly (CORS you cannot change, or a token you must hide). It puts Vercel's limits back in the path.

```ts
// app/api/events/route.ts
import { API_URL } from "@/lib/api";

export const maxDuration = 300; // Hobby ceiling in seconds; the stream is cut here and EventSource reconnects

export async function GET() {
  const upstream = await fetch(`${API_URL}/events`, {
    headers: { Accept: "text/event-stream" },
    cache: "no-store",
  });
  if (!upstream.ok || !upstream.body) return new Response("upstream unavailable", { status: 502 });
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
```

Then open `new EventSource("/api/events")`.

## Limits on streaming

| Where | Limit | Effect |
|---|---|---|
| Modal web endpoint | 150 s per HTTP request; the redirect for longer requests does not work with CORS | end streams at about 120 s; keep every browser call short |
| Vercel Function (only when proxying) | duration counts the whole streamed response: 300 s on Hobby; Pro 300 s default, 800 s maximum | the stream is cut and `EventSource` reconnects |
| Vercel Function body | 4.5 MB request or response; streamed responses are exempt | |
| Vercel external rewrite (`rewrites` to another host) | upstream must respond within 120 s, else `ROUTER_EXTERNAL_TARGET_ERROR` | do not rely on a rewrite for long streams; whether a rewrite passes a long-lived event stream is UNVERIFIED |
| Edge runtime | must start responding within 25 s; deprecated in Next.js 16 | use the default Node.js runtime |
| Browser | 6 open `EventSource` connections per browser and domain over HTTP/1.1 | one or two streams per page; close on unmount (the hook does) |
| Safari | buffers a response until 1024 bytes arrive | the first tiny event can look delayed |

WebSockets on Vercel Functions are in public beta and close at the same duration limit. DxP does not need them.

`EventSource` cannot set request headers. If the stream needs a secret, use the proxy above and add the header in the Route Handler's `fetch`.

Whether a cross-origin `EventSource` resends `Last-Event-ID` without extra CORS configuration is UNVERIFIED, which is why this design refetches on reconnect and does not depend on resuming.

Sources: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events , https://vercel.com/kb/guide/publish-and-subscribe-to-realtime-data-on-vercel , https://vercel.com/docs/functions/limitations , https://vercel.com/docs/functions/streaming-functions , https://vercel.com/docs/limits , https://nextjs.org/docs/app/guides/streaming , https://modal.com/docs/guide/webhook-timeouts , https://modal.com/docs/guide/streaming-endpoints , https://fastapi.tiangolo.com/tutorial/server-sent-events/
