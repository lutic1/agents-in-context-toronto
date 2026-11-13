---
name: dxp-modal
description: Modal for DxP - hosting the Python agents, the parallel batch over 300 to 500 source items, the scheduled unattended scan and the HTTP API the Next.js front end calls. Load when a task touches `modal`, `modal.App`, `@app.function`, `modal deploy` / `modal run` / `modal serve`, `.map` / `.starmap` / `.spawn`, `modal.Cron`, `modal.Secret`, `@modal.asgi_app`, `@modal.fastapi_endpoint`, `@modal.concurrent`, cold starts, batch progress or `*.modal.run` URLs.
---

# Modal for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Read its Precedence paragraph before copying an example from here.

## Verified

Checked 12 November 2026 against the official docs and PyPI.

- `modal` Python SDK **1.6.4** (released 2026-11-11), requires Python `>=3.10,<3.16`. Python 3.10 images already warn and are dropped in SDK 1.7.0.
- Pages used (every page has a markdown twin: append `.md`; index at https://modal.com/llms.txt):
  guide pages `apps`, `images`, `scale`, `concurrent-inputs`, `batch-processing`, `job-queue`, `function-invocation-methods`, `cron`, `secrets`, `webhooks`, `streaming-endpoints`, `webhook-timeouts`, `webhook-urls`, `webhook-proxy-auth`, `cold-start`, `timeouts`, `retries`, `proxy-ips`, `lifecycle-functions`, `managing-deployments`, `trigger-deployed-functions`, `billing`, `resources`, `modal-1-0-migration` under https://modal.com/docs/guide/ ; SDK reference `App`, `Function`, `FunctionCall`, `Image`, `Secret`, `Cron`, `Period`, `Retries`, `concurrent`, `asgi_app`, `fastapi_endpoint` under https://modal.com/docs/sdk/py/latest/ ; release notes https://modal.com/docs/sdk/py/releases ; https://modal.com/pricing .
- Atlas network and M0 limits: https://www.mongodb.com/docs/atlas/security/ip-access-list/ and https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/ . PyMongo client reuse and pool options: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/connect/mongoclient/ .
- Only the names used below were checked for the neighbouring tools: LangGraph quickstart (`StateGraph`, `START`, `END`, `compile`, `invoke`), LangSmith (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`), Anthropic Python SDK (`ANTHROPIC_API_KEY`), FastAPI (`CORSMiddleware`). Their own DxP skills are authoritative for versions and model IDs.

## Read this first

1. **No fixed egress IP on the free plan.** Static IPs come only from Modal Proxies (Beta), which are Team and Enterprise only (Team is $250 per month). On Starter the Atlas IP access list must contain `0.0.0.0/0`, or every Modal container is refused. Atlas emails all project users an alert when a `/0` entry is added. Atlas's Vercel integration requires the same entry, so this is one decision for both.
2. **HTTP requests to Modal are capped at 150 seconds.** A longer request gets a 303 redirect, and Modal's docs say that redirect does not work for requests that need CORS, which is exactly a browser on Vercel calling `*.modal.run`. So never run the batch inside a request, and never hold one server-sent-events stream open for the whole run. Start the batch with `.spawn()`, write progress to MongoDB, and let the front end poll or use a stream that ends itself within about two minutes.
3. **Starter plan caps:** 100 concurrent containers, 5 deployed crons, log retention 1 day, 3 seats, $30 of compute per month. The pricing page lists "Scheduled and Web Functions (limited)" without a number, so use ONE ASGI app for all routes and ONE cron. The billing guide says a payment method must be on file to use Modal.
4. **Modal re-runs inputs.** A container crash or preemption makes Modal retry the inputs it was running, and `retries=` re-runs failures. `process_item` must be idempotent: FR-3 (no duplicates) has to be enforced in MongoDB (unique index on the match key plus upsert), not by the batch runner.
5. **Schedules are activated by deploying.** The docs give `modal deploy` as the only way to activate a schedule; do not expect the cron to fire under `modal run` or `modal serve` (their behaviour is not documented: UNVERIFIED). FR-1 needs `modal deploy`.
6. **The parallelism limit is not Modal.** Concurrency = `max_containers` x `max_inputs`. Size it to the Claude rate limit (PRD section 8) and, on an Atlas M0 cluster, to 500 connections and 100 operations per second.
7. Most code on the web predates SDK 1.0 and fails today: `modal.Stub`, `@modal.web_endpoint`, `keep_warm`, `concurrency_limit`, `container_idle_timeout`, `allow_concurrent_inputs`, `modal.Mount`, `.lookup()`. Replacements are in [references/reference.md](references/reference.md).

## What DxP uses it for

- **FR-1** Unattended scan: a `modal.Cron` function in the deployed App, plus a manual trigger route.
- **FR-4** Batch of 300 to 500 Source items in parallel with a live count of processed, failed and Early research.
- **FR-30** Baseline load and Held-back set: two calls of the same batch function with different item lists.
- **FR-3, FR-5, FR-15, FR-18** run inside `process_item` (the LangGraph graph); Modal only supplies the containers, secrets and retries.
- **PRD section 8, Unattended operation:** nothing here depends on a laptop staying open once deployed.

## Setup

```bash
pip install modal            # or: uv add modal
modal setup                  # browser login, writes ~/.modal.toml
modal token info             # confirm
```

Secrets (values come from the shell or a file the human supplies; never paste them into code or chat):

```bash
modal secret create dxp-secrets \
  MONGODB_URI="$MONGODB_URI" ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  TAVILY_API_KEY="$TAVILY_API_KEY" LANGSMITH_API_KEY="$LANGSMITH_API_KEY"
# or: modal secret create dxp-secrets --from-dotenv <path>   (add --force to overwrite)
modal secret list
```

Names the code expects in the container: `MONGODB_URI` (DxP convention), `ANTHROPIC_API_KEY` (read by the `anthropic` SDK by default), `TAVILY_API_KEY` (DxP convention, see dxp-tavily; pass it to the client explicitly), `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` (LangSmith). A LangSmith organisation created recently has an agent-based workspace and also needs `LANGSMITH_AGENT_ID` and `LANGSMITH_AGENT_ENVIRONMENT` in the secret, and must not set `LANGSMITH_PROJECT`, or no traces are sent; see dxp-langgraph-langsmith for which case applies. Local machine only: `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` override `~/.modal.toml`.

Both developers share one workspace (Starter allows 3 seats). Each sets `MODAL_DEV_SUFFIX` (for example their name) so that two `modal serve` sessions do not steal each other's URL. Only one person runs `modal deploy`.

Optional: `modal skills install --claude` installs Modal's own version-matched agent skill and docs.

## Core patterns

One file, for example `backend/modal_app.py`. Third-party imports go inside function bodies, because the file is also imported on the laptop where those packages may be missing.

### App, image, secrets, MongoDB client

```python
import os
import threading

import modal

app = modal.App("dxp")

image = (
    modal.Image.debian_slim(python_version="3.13")
    .uv_pip_install(  # pin versions from the other DxP skills
        "fastapi[standard]", "pymongo", "langgraph", "langchain-anthropic",
        "langsmith", "tavily-python",
    )
    .env({"LANGSMITH_TRACING": "true"})
    .add_local_python_source("dxp")  # local package with the pipeline; last step; omit until it exists
)

secrets = [
    modal.Secret.from_name(
        "dxp-secrets",
        required_keys=["MONGODB_URI", "ANTHROPIC_API_KEY", "TAVILY_API_KEY", "LANGSMITH_API_KEY"],
    )
]

MAX_CONTAINERS = 5        # x INPUTS_PER_CONTAINER = items in flight; size to the Claude rate limit
INPUTS_PER_CONTAINER = 10

_lock = threading.Lock()
_mongo = None


def db():
    """One MongoClient per container, reused by every input that container handles."""
    global _mongo
    with _lock:
        if _mongo is None:
            from pymongo import MongoClient

            _mongo = MongoClient(os.environ["MONGODB_URI"], maxPoolSize=10)
    return _mongo.get_database(os.environ.get("MONGODB_DB", "dxp"))
```

The file that defines the App is included automatically; every other local module needs `add_local_python_source`.

### Worker and batch runner (FR-4, FR-30)

```python
@app.function(
    image=image,
    secrets=secrets,
    timeout=600,  # per attempt; the default is 300 s
    retries=modal.Retries(max_retries=2, backoff_coefficient=2.0, initial_delay=2.0),
    max_containers=MAX_CONTAINERS,
)
@modal.concurrent(max_inputs=INPUTS_PER_CONTAINER)  # sync function: inputs run on threads
def process_item(batch_id: str, item_id: str) -> dict:
    from dxp.pipeline import run_item  # project code: runs the LangGraph graph, upserts by match key

    return run_item(db(), batch_id, item_id)  # return a plain dict, e.g. {"early_research": True}


@app.function(image=image, secrets=secrets, timeout=3600)
def run_batch(batch_id: str, item_ids: list[str]) -> dict:
    runs = db()["batch_runs"]
    runs.update_one(
        {"_id": batch_id},
        {"$set": {"status": "running", "total": len(item_ids),
                  "processed": 0, "failed": 0, "early_research": 0}},
        upsert=True,
    )
    for result in process_item.starmap(
        [(batch_id, item_id) for item_id in item_ids],
        order_outputs=False,     # yield in completion order, so the count moves steadily
        return_exceptions=True,  # a failed item comes back as an Exception; the run continues
    ):
        if isinstance(result, Exception):
            print(f"item failed: {result!r}")
            inc = {"failed": 1}
        else:
            inc = {"processed": 1, "early_research": int(bool(result.get("early_research")))}
        runs.update_one({"_id": batch_id}, {"$inc": inc})
    runs.update_one({"_id": batch_id}, {"$set": {"status": "done"}})
    return runs.find_one({"_id": batch_id})
```

`return_exceptions=True` is counted only after `retries` are exhausted. With `order_outputs=False` an exception no longer tells you which item it was: have `run_item` record its own status on the Source item before re-raising.

### Scheduled scan (FR-1)

```python
@app.function(image=image, secrets=secrets, timeout=900,
              schedule=modal.Cron("*/30 * * * *"))  # UTC unless timezone="America/Toronto"
def scheduled_scan() -> str | None:
    from datetime import datetime, timezone

    from dxp.sources import find_new_item_ids  # project code

    item_ids = find_new_item_ids(db())
    if not item_ids:
        return None
    batch_id = f"scan-{datetime.now(timezone.utc):%Y%m%dT%H%M}"
    run_batch.spawn(batch_id, item_ids)  # durable: keeps running after this function returns
    return batch_id
```

Use `modal.Cron`, not `modal.Period`: a Period restarts its clock on every redeploy. Schedules cannot be paused; remove the argument and redeploy. The dashboard has a "run now" button.

### Web API for the front end (FR-4 progress, FR-1 manual trigger)

```python
@app.function(image=image, secrets=secrets, min_containers=1, scaledown_window=300)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def api():
    import uuid

    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    web = FastAPI()
    web.add_middleware(
        CORSMiddleware,
        allow_origins=[os.environ.get("FRONTEND_ORIGIN", "*")],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @web.post("/batches")
    def start_batch(body: dict):
        batch_id, item_ids = uuid.uuid4().hex, body["item_ids"]
        db()["batch_runs"].insert_one(
            {"_id": batch_id, "status": "queued", "total": len(item_ids),
             "processed": 0, "failed": 0, "early_research": 0}
        )
        call = run_batch.spawn(batch_id, item_ids)  # returns at once
        return {"batch_id": batch_id, "call_id": call.object_id}

    @web.post("/scans")
    def start_scan():
        return {"call_id": scheduled_scan.spawn().object_id}

    @web.get("/batches/{batch_id}")
    def get_batch(batch_id: str):
        return db()["batch_runs"].find_one({"_id": batch_id}) or {"status": "unknown"}

    # optional server-sent-events route: references/reference.md

    return web


@app.local_entrypoint()
def smoke(limit: int = 3):
    print(run_batch.remote("smoke", [f"smoke-{i}" for i in range(limit)]))
```

With `@modal.asgi_app()` you add CORS yourself, as above (`@modal.fastapi_endpoint` enables it automatically, but it is one route per function). `smoke` uses made-up item IDs, so it should report them all as failed after the retries: that is the failure path working. The front end polls `GET /batches/{id}` every second; the TypeScript, and an optional server-sent-events route that respects the 150 s limit, are in [references/reference.md](references/reference.md).

### LangGraph inside a Modal function

Build the graph once per container, call it per input. LangSmith tracing needs `LANGSMITH_TRACING` and `LANGSMITH_API_KEY`, both set above, plus the two agent variables if the workspace is agent-based (see Setup). Prefer one graph run that fans out with `Send` over one graph run per item: the free LangSmith plan allows 5,000 traces a month and a per-item shape spends 500 per batch (see dxp-langgraph-langsmith).

```python
_graph = None


def graph():
    global _graph
    if _graph is None:
        from langgraph.graph import END, START, StateGraph
        from typing_extensions import TypedDict

        class State(TypedDict, total=False):
            item_id: str
            record: dict

        def extract(state: State) -> dict:
            return {"record": {}}  # call Claude here; see the Claude and LangGraph skills

        builder = StateGraph(State)
        builder.add_node("extract", extract)
        builder.add_edge(START, "extract")
        builder.add_edge("extract", END)
        _graph = builder.compile()
    return _graph  # in run_item: state = graph().invoke({"item_id": item_id})
```

### Run, serve, deploy

```bash
modal run backend/modal_app.py --limit 3        # ephemeral App, runs the local entrypoint, then stops
modal serve backend/modal_app.py                # hot reload of the web API; URL gets the -dev suffix
modal deploy backend/modal_app.py --strategy recreate   # persistent: cron live, stable URL
modal app logs dxp -f                           # -f to follow; default prints the last 100 lines
modal app stop dxp --yes                        # stops the cron and the URL
```

"Deployed" means the App persists until stopped, its cron fires with no client connected, and its URL is stable. Redeploying the same name updates it in place. Idle functions cost nothing unless `min_containers` is set. URL: `https://<workspace>--dxp-api.modal.run` (printed by the CLI); under `modal serve` it is `https://<workspace>--dxp-api-dev.modal.run`. Put it in the front end as an environment variable, not a literal.

## Limits and costs

- Function timeout: default 300 s, settable 1 s to 24 h, counted per attempt. Web request: 150 s.
- `.map` / `.starmap`: at most 1,000 inputs running at once per call, so 500 items fits one call. They are synchronous: if the caller disappears the work is cancelled within two minutes, which is why `run_batch` runs on Modal and is started with `.spawn()`.
- `.spawn()` results are kept 7 days; poll with `modal.FunctionCall.from_id(call_id).get(timeout=0)` (raises `TimeoutError` while pending).
- Idle containers shut down after 60 s by default (`scaledown_window`, 2 s to 20 min). The idle time is billed.
- Prices: CPU $0.0000131 per core-second, memory $0.00000222 per GiB-second, minimum 0.125 core and 128 MiB per container, billed on the higher of request and use.
- Estimate (arithmetic from list prices, not measured): 500 items at 50 in flight, 60 s each, is about 10 minutes on 5 containers, roughly $0.02 to $0.30. One warm API container for the whole day is under $0.50. The $30 monthly credit covers the hackathon many times over; the Claude API bill is the real cost.
- Atlas M0, if that is the tier: 500 connections, 100 operations per second, 0.5 GB. Five containers with `maxPoolSize=10` stay well inside the connection limit; 100 containers would not.

Full table and the arithmetic: [references/reference.md](references/reference.md).

## Gotchas

- Web decorators need `fastapi[standard]` in the image, or the container fails at start.
- `add_local_python_source` and `add_local_dir` must be the last image steps unless `copy=True`.
- Run the CLI from the directory where `dxp` is importable. Module paths need `-m`: `modal deploy -m backend.modal_app`.
- A sync function under `@modal.concurrent` runs inputs on threads: no shared mutable state. PyMongo's `MongoClient` is thread-safe; create it once, as above.
- Do not put counters in `modal.Dict`: the docs give no atomic increment and entries expire after 7 days idle. Use `$inc` in MongoDB.
- `modal.FunctionCall.gather(...)` raises on the first failure. Only `.map` and `.starmap` have `return_exceptions`.
- `spawn_map` is documented inconsistently (the guide says it returns no handle, the `FunctionCall.iter` reference shows one). Do not build on its return value.
- The default deploy is rolling, so old containers keep serving for a while. Use `--strategy recreate` while iterating. Changed Secrets reach only containers started after the change.
- `modal.Function.from_name("dxp", "process_item")` works only against a deployed App, never against `modal serve`.
- Web functions are public by default. `requires_proxy_auth=True` needs `Modal-Key` and `Modal-Secret` headers, so only call it from Next.js server code, never from the browser.
- `modal run file.py::fn` runs in an ephemeral App that stops when the terminal exits; anything it spawned dies with it unless you pass `--detach`.
- A browser `EventSource` reconnects when the stream ends: close it on `status == "done"`.

## Fallback

1. Cold start or slow first click: before recording, hit the API once and run `modal.Function.from_name("dxp", "process_item").autoscaler.update(min_containers=2)` (reverts on the next deploy).
2. Stream trouble: switch the front end to polling `GET /batches/{id}`. Same data, no long request.
3. Modal batch misbehaves: run the same code on a laptop. `process_item.local(batch_id, item_id)` calls the plain function with no Modal configuration applied; wrap it in a `concurrent.futures.ThreadPoolExecutor`, install the image's packages locally and export the secrets as environment variables. The progress document and the UI are unchanged because progress lives in MongoDB.
4. Modal web endpoint down: keep the FastAPI construction in a plain function so that a local ASGI server can serve the same app (the exact local command is UNVERIFIED here), and point the front end's API URL at it.
5. Cron does not fire on camera: press "run now" in the dashboard or `POST /scans`, and say so. Run the Baseline load before the demo regardless; only the Held-back set needs to run live.

## Links

- Batch, invocation limits, concurrency: https://modal.com/docs/guide/function-invocation-methods , https://modal.com/docs/guide/scale , https://modal.com/docs/guide/concurrent-inputs
- Web functions, the 150 s limit, streaming: https://modal.com/docs/guide/webhooks , https://modal.com/docs/guide/webhook-timeouts , https://modal.com/docs/guide/streaming-endpoints
- Schedules, secrets, cold starts: https://modal.com/docs/guide/cron , https://modal.com/docs/guide/secrets , https://modal.com/docs/guide/cold-start
- Static IP Proxies (Team plan): https://modal.com/docs/guide/proxy-ips
- 1.0 migration and release notes: https://modal.com/docs/guide/modal-1-0-migration , https://modal.com/docs/sdk/py/releases
- Pricing, plan limits, `App.function` parameters: https://modal.com/pricing , https://modal.com/docs/sdk/py/latest/App
