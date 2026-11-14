> Reference only. Do not copy this code into the project; it was written before the event.

# Modal reference for DxP

Checked 12 November 2026 against `modal` 1.6.4. Sources are listed in `../SKILL.md`.

## Renamed, deprecated and removed APIs

Anything in the left column is wrong today. Most blog posts and older model training data use it.

| Old | Use instead | Status |
| --- | --- | --- |
| `modal.Stub` | `modal.App` | Error since 1.0.0 |
| `@modal.web_endpoint` | `@modal.fastapi_endpoint` | Renamed in 0.73.82 |
| `keep_warm=` | `min_containers=` | Old name removed in 1.4.0 |
| `concurrency_limit=` | `max_containers=` | Old name removed in 1.4.0 |
| `container_idle_timeout=` | `scaledown_window=` | Old name removed in 1.4.0 |
| `allow_concurrent_inputs=N` | `@modal.concurrent(max_inputs=N)` under `@app.function()` | Replaced in 0.73.148 |
| `max_inputs=` on `@app.function` | `single_use_containers=True` | Deprecated |
| `modal.Mount`, `mount=`, `Image.copy_mount` | `Image.add_local_dir`, `Image.add_local_file`, `Image.add_local_python_source` | Removed in 1.0.0 |
| `Image.copy_local_dir`, `Image.copy_local_file` | `Image.add_local_dir`, `Image.add_local_file` (`copy=True` to bake into a layer) | Deprecated |
| Automatic inclusion of imported local modules ("automounting") | `Image.add_local_python_source("pkg")`; only the file defining the App is still included automatically | Enforced in 1.0.0 |
| `Function.lookup(...)`, `Secret.lookup(...)` and other `.lookup` | `.from_name(...)` (lazy); call `.hydrate()` if metadata is needed at once | Deprecated |
| `modal.Function.from_name("app", "Cls.method")` | `modal.Cls.from_name("app", "Cls")().method` | Removed in 1.4.0 |
| `Function.update_autoscaler(...)` | `Function.autoscaler.update(...)` | Deprecated in 1.6.2 |
| Custom `__init__` on an `@app.cls()` class | `modal.parameter()` fields and `@modal.enter()` | Removed in 1.6.0 |
| `@modal.build` | `Image.run_function` or a `modal.Volume` | Deprecated |
| `modal.gpu.H100()` objects | Strings: `gpu="H100"` | Deprecated |
| `modal.functions.gather` | `modal.FunctionCall.gather` | Replaced in 0.73.69 |
| `modal deploy pkg.module` | `modal deploy -m pkg.module` | `-m` required since 1.4.0 |
| `modal app logs` following by default | `modal app logs <app> -f` | Changed in 1.4.0 |
| `wrap_returned_exceptions=` on `.map` | Nothing: exceptions from `.map` are no longer wrapped in `UserCodeException` | Changed in 1.4.0 |
| `Image.pip_install` as the default | `Image.uv_pip_install` (added 1.1.0); `pip_install` remains as the fallback | Current docs prefer uv |

New in the last year and not needed for DxP: `@app.server()` and `modal.Server` (1.5.1, low-latency HTTP, authenticated by proxy token by default), `modal endpoint` (LLM inference endpoints), named Images, `routing_region=`, `startup_timeout=` (1.1.4), `modal skills`.

## Invocation methods

| | Synchronous (caller waits) | Asynchronous (durable) |
| --- | --- | --- |
| One input | `f.remote(x)` | `f.spawn(x)` returns `modal.FunctionCall` |
| Many inputs | `f.map(xs)`, `f.starmap(tuples)` | `f.spawn_map(xs)` |

- `map(*input_iterators, kwargs={}, order_outputs=True, return_exceptions=False)`: one iterable per positional parameter.
- `starmap(input_iterator, *, kwargs={}, order_outputs=True, return_exceptions=False)`: an iterable of argument tuples.
- `for_each(*input_iterators, kwargs={}, ignore_exceptions=False)`: run for side effects, discard results.
- `FunctionCall.get(timeout=None)`: blocks; `timeout=0` polls and raises `TimeoutError` if not finished; `modal.exception.OutputExpiredError` after 7 days.
- `FunctionCall.from_id(call_id)`, `FunctionCall.cancel()`, `FunctionCall.gather(*calls)` (raises on the first failure).
- Async variants: append `.aio`, for example `await f.remote.aio(x)`, `async for r in f.map.aio(xs)`. Inside an `async def` web handler use these or the event loop blocks.
- `f.local(x)`: runs the plain Python function in the calling process with no Modal configuration.
- `map(evaluate, inputs)` with Python's builtin `map` runs in sequence. `f.map(inputs)` is the parallel one.

## Platform limits

| Limit | Value |
| --- | --- |
| Function timeout | default 300 s; 1 s to 24 h; per attempt |
| HTTP request to a web function | 150 s, then 303 redirect (up to about 20 in a browser; does not work with CORS) |
| Scale-down idle window | default 60 s; `scaledown_window` 2 s to 20 min |
| Containers, Starter plan | 100 concurrent (Team: 5,000) |
| Containers per function | hard limit 4,000 |
| `.map` concurrency | 1,000 inputs running per call |
| Synchronous inputs | 2,000 queued, 25,000 in the system, 200 per second |
| Asynchronous inputs | 1,000,000 queued, 1,500 per second |
| Web function rate limit | 200 requests per second per function (bursts of 15 s worth), 2,000 per workspace; excess gets 429 |
| `.spawn` result retention | 7 days |
| Payload size | 100 MB gRPC limit (`413 Content Too Large`) |
| Secrets | key up to 16,384 characters, value up to 32,768 |
| WebSocket message | 2 MiB |
| Deployed crons, Starter | 5 |
| Deployed apps, Starter | 200 |
| Log retention, Starter | 1 day |
| Seats, Starter | 3 |
| Static IP proxy, custom domains, rollbacks | Team and Enterprise only |
| `modal.Dict` | 100 MiB per object, entries expire after 7 days without reads or writes |

Exceeding the input limits raises `modal.exception.ResourceExhaustedError`. A timeout after retries raises `modal.exception.FunctionTimeoutError`.

## Prices and the batch estimate

List prices on 12 November 2026:

- CPU: $0.0000131 per physical core per second (one core is two vCPUs). Minimum request 0.125 core.
- Memory: $0.00000222 per GiB per second. Minimum request 128 MiB.
- Billed on the higher of the request and actual use, during container start-up, while handling inputs and during the idle window before scale-down.
- Region pinning (`region=`): 1.15x for a broad region such as `"us"`, 1.75x for a narrow one such as `"us-east"`. Non-preemptible: 3x.
- Starter: $0 per month plus compute, $30 of compute included each month, 1 TiB network egress included.

Arithmetic, not measurement:

- One container using 0.5 core and 0.5 GiB costs 0.5 x 0.0000131 + 0.5 x 0.00000222 = $0.0000077 per second, about $0.028 per hour.
- Batch of 500 items, 60 s each, 50 in flight (5 containers x 10 inputs): 500 x 60 / 50 = 600 s of wall time. 5 containers x 600 s x $0.0000077 = about $0.023. With 20 containers and 20 minutes it is still about $0.19.
- One warm API container for 24 hours at the minimum request: 86,400 x (0.125 x 0.0000131 + 0.125 x 0.00000222) = about $0.17. At 0.25 core and 0.5 GiB of real use: about $0.38.

The limit that matters for a run of this size is the Claude API rate limit, then the MongoDB tier, not Modal.

## Atlas from Modal

- Atlas accepts client connections only from entries in the project's IP access list. Modal containers start anywhere in Modal's fleet across AWS, GCP and OCI, so their addresses vary.
- On Starter the only workable entry is `0.0.0.0/0`. Atlas documents that this "allows access from anywhere" and emails an alert to project users. Protect the cluster with a strong database user password and remove the entry after the event.
- With a Team plan: create a Proxy in workspace Settings, add its static IPs (up to five) to the Atlas access list, and attach it with `@app.function(proxy=modal.Proxy.from_name("<proxy-name>"))`. Proxies are Beta and add WireGuard latency.
- To cut latency to Atlas, `region="us"` (or the narrow region of the cluster) on the functions costs the multiplier above. Not needed for the demo.
- Create one `MongoClient` per container and reuse it across inputs (see `db()` in SKILL.md). PyMongo is thread-safe and each client is a connection pool with `maxPoolSize` 100 by default. Do not create a client per input and do not pass a client to a forked process.
- Connection budget: containers x `maxPoolSize` x cluster members, plus monitoring connections. Atlas M0 allows 500 connections and 100 operations per second.

## Optional server-sent-events route

Add inside `api()` in SKILL.md, with `import json`, `import time` and `from fastapi.responses import StreamingResponse`. A sync generator runs on its own thread, so `time.sleep` is safe here. `text/event-stream` is what makes Modal send each event at once instead of buffering. Whether a stream that is already sending is cut at the 150 s request limit is UNVERIFIED, so this one ends itself at 120 s and the browser reconnects.

```python
    @web.get("/batches/{batch_id}/events")
    def batch_events(batch_id: str):
        def stream():
            deadline = time.monotonic() + 120  # end before the 150 s HTTP limit
            while time.monotonic() < deadline:
                doc = db()["batch_runs"].find_one({"_id": batch_id}) or {"status": "unknown"}
                yield f"data: {json.dumps(doc, default=str)}\n\n".encode()
                if doc["status"] in ("done", "unknown"):
                    return
                time.sleep(1)

        return StreamingResponse(stream(), media_type="text/event-stream")
```

## Front end (Next.js, TypeScript)

`fetch`, `EventSource` and the `NEXT_PUBLIC_` prefix are standard browser and Next.js features that were not re-checked in this session; the Modal side of each call was.


Polling, the default:

```ts
const API = process.env.NEXT_PUBLIC_DXP_API_URL!; // https://<workspace>--dxp-api.modal.run

export type BatchRun = {
  _id: string;
  status: "queued" | "running" | "done" | "unknown";
  total: number;
  processed: number;
  failed: number;
  early_research: number;
};

export async function startBatch(itemIds: string[]): Promise<string> {
  const res = await fetch(`${API}/batches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_ids: itemIds }),
  });
  if (!res.ok) throw new Error(`start failed: ${res.status}`);
  return (await res.json()).batch_id;
}

export async function pollBatch(batchId: string, onUpdate: (run: BatchRun) => void) {
  for (;;) {
    const run: BatchRun = await (await fetch(`${API}/batches/${batchId}`)).json();
    onUpdate(run);
    if (run.status === "done" || run.status === "unknown") return;
    await new Promise((r) => setTimeout(r, 1000));
  }
}
```

Server-sent events, optional. The server ends each stream after 120 s and the browser reconnects by itself, so close on completion:

```ts
export function streamBatch(batchId: string, onUpdate: (run: BatchRun) => void) {
  const source = new EventSource(`${API}/batches/${batchId}/events`);
  source.onmessage = (event) => {
    const run: BatchRun = JSON.parse(event.data);
    onUpdate(run);
    if (run.status === "done" || run.status === "unknown") source.close();
  };
  return () => source.close();
}
```

The front end can also read `batch_runs` straight from MongoDB in a Next.js route handler and skip Modal for progress entirely; Modal is then only called to start a batch. Modal has JavaScript and Go SDKs (Beta) that can call deployed functions with `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`; DxP does not need them.

## Keeping the demo warm

- `min_containers=1` on `api` keeps one container up at all times (in SKILL.md already).
- Workers scale from zero, so the first items of a batch wait for containers to start and import their packages. Before recording: `modal.Function.from_name("dxp", "process_item").autoscaler.update(min_containers=2)`. The next `modal deploy` resets it to the decorator's values.
- A container counts as warm only after module-level code and any `@modal.enter()` methods finish. Heavy imports at the top of a function body run on the first input instead, so the first item in each container is slower.
- `buffer_containers=N` keeps N spare containers while the function is active; useful if the demo starts several batches in a row.
