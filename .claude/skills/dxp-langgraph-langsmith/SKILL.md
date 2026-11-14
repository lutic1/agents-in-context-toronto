---
name: dxp-langgraph-langsmith
description: LangGraph 1.x (Python) orchestration and LangSmith tracing for DxP - StateGraph, Send fan-out for the 300 to 500 item batch, triage-then-extraction two-pass graph, interrupt/Command reviewer pause and resume, MongoDBSaver checkpointer, ChatAnthropic structured output. Load when a task touches `langgraph`, `StateGraph`, `Send`, `interrupt`, `Command(resume=...)`, `MongoDBSaver`, `langgraph-checkpoint-mongodb`, `langchain-anthropic`, `ChatAnthropic`, `init_chat_model`, `with_structured_output`, `langsmith`, `LANGSMITH_*` variables, traces, or the Proposed change review loop.
---

# LangGraph and LangSmith for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Event rule: everything in this skill is reference documentation. Do not copy code from it into the project; write new code during the event.
>
> Saturday scope is `_bmad-output/planning-artifacts/development-plan.md`. Baseline loading, PubMed, memory, Learned rules, Alerts, Tavily scans and the old three-minute recorded video (the 3-minute live demo is in scope) are deferred; ignore those parts of this skill.

## Verified

Checked 12 November 2026 against PyPI and the official docs (raw `.md` pages fetched that day).

| Package | Version | Note |
| - | - | - |
| `langgraph` | 1.2.21 | released 12 Nov 2026; needs `langgraph-checkpoint>=4.3.0,<5` |
| `langchain` | 1.5.0 | Python >= 3.11; pins `langgraph>=1.2.12,<1.3`; provides `init_chat_model` |
| `langchain-core` | 1.8.0 | |
| `langchain-anthropic` | 1.7.10 | `ChatAnthropic`; native structured output needs >= 1.1.0 |
| `langsmith` | 0.14.17 | agent addressing needs >= 0.14.9 |
| `langgraph-checkpoint-mongodb` | 0.5.1 | released 8 Oct 2026; Python >= 3.11; exports `MongoDBSaver` only |
| `langgraph-checkpoint` | 4.3.1 | |

Claude model IDs (Anthropic models overview): `claude-haiku-5-5` (fastest; classification, extraction, routing), `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-2`. `dxp-claude-api` is the authority on models, prices and rate limits; these are only the defaults used here.

Pages used: docs.langchain.com `oss/python/langgraph/` {`graph-api`, `graph-api-nodes`, `graph-api-control-flow`, `graph-api-send-command`, `interrupts`, `checkpointers`, `persistence`, `fault-tolerance`, `streaming`, `backward-compatibility`, `use-subgraphs`, `observability`}; `oss/python/integrations/chat/anthropic`; `oss/python/langchain/models`; `langsmith/` {`trace-with-langgraph`, `trace-with-langchain`, `log-traces-to-agent`, `create-an-agent`, `agent-registry`, `migrate-to-agent-based-workspaces`, `administration-overview`, `threads`, `share-trace`}; langchain.com/pricing; mongodb.com/docs/atlas/ai-integrations/langgraph; the `langgraph-checkpoint-mongodb` source on GitHub; platform.claude.com models overview and structured outputs.

## Read this first

1. **LangSmith no longer defaults to "projects".** A new LangSmith Cloud organisation gets an *agent-based* workspace. There you must create an agent record first, then set `LANGSMITH_AGENT_ID` and `LANGSMITH_AGENT_ENVIRONMENT` (`local`, `development`, `staging` or `production`). If only one of the two is set, or `LANGSMITH_PROJECT` is set as well, the SDK logs a warning and **sends no traces**. Older, project-based workspaces still use `LANGSMITH_PROJECT`. Check the top-left control in the UI: a workspace name means agent-based, the LangSmith logo means project-based. `dxp-modal` lists only two LangSmith variables; add these to the Modal secret.
2. **The free LangSmith plan is 1 seat and 5,000 traces a month**, hard-stopped with HTTP 429 when no card is on file. One graph run is one trace. Running one graph per Source item costs 500 traces per batch; ten batches and tracing stops. Use the single-run `Send` fan-out below, or switch tracing off for bulk runs. Two people share one API key.
3. **`AsyncMongoDBSaver` does not exist** in `langgraph-checkpoint-mongodb` 0.5.1, although the LangGraph checkpointer page still names it. Use `MongoDBSaver` for sync and async graphs (its async methods wrap the sync ones). The package also pre-dates `langgraph-checkpoint` 4.3, which `langgraph` 1.2.21 requires: pip resolves it, but compatibility is `UNVERIFIED`. Run the pause/resume smoke test in the first hour.
4. **`temperature=0` breaks.** Current Claude models reject non-default `temperature`, `top_p` and `top_k` with a 400. Never pass them. `thinking={"type": "enabled", "budget_tokens": ...}` is also not accepted on current models.
5. **One failing worker fails the whole parallel step.** A super-step is transactional: if any `Send` branch raises, none of that step's updates are applied. Catch inside the worker and return the failure as data (FR-4).
6. **Do not put a checkpointer on the batch graph.** A checkpoint stores the full state at every super-step. Checkpoint the review graph only.
7. **No LangGraph Platform, Agent Server or `langgraph.json` is needed.** A compiled graph is a plain Python object; call `invoke` inside any function.
8. API names that changed across 0.x and 1.x; write only the current ones: `add_node(..., retry_policy=...)`; `StateGraph(State, context_schema=...)` with `runtime: Runtime[Ctx]` in the node; `interrupt()` plus `Command(resume=...)` for human review (`interrupt_before` is documented as debugging only); `InMemorySaver`; default recursion limit 10,007 super-steps since 1.1.4.

## What DxP uses it for

- **FR-4** batch of 300 to 500 Source items: `Send` fan-out, `max_concurrency`, per-item error capture.
- **FR-5, FR-18** fixed-format extraction with a quote per field, then a word-for-word quote check: two-pass item graph.
- **FR-15, FR-16, FR-17** Proposed change held for a Reviewer: `interrupt()` in a checkpointed graph, resumed with accept, edit or reject.
- **FR-19** Learned rule: deferred on Saturday; do not build it.
- **FR-1** unattended scan: the same graphs called from a Modal function or cron.
- **SM-2** the trace shown on camera: LangSmith run names, tags and a public share link.

## Setup

```bash
uv add "langgraph>=1.2.12,<1.3" "langchain>=1.5,<2" "langchain-anthropic>=1.7,<2" \
       "langsmith>=0.14.12" "langgraph-checkpoint-mongodb>=0.5.1" "pymongo>=4.18.2"
```

Python 3.11 or later. `langchain` is needed only for `init_chat_model` and the rate limiter. Put the same packages in the Modal image.

Environment variable names (values live in the Modal secret, never in code):

| Name | Purpose |
| - | - |
| `ANTHROPIC_API_KEY` | read by `ChatAnthropic` |
| `LANGSMITH_TRACING` | `true` to trace; anything else and the graphs run untraced |
| `LANGSMITH_API_KEY` | tracing key |
| `LANGSMITH_AGENT_ID`, `LANGSMITH_AGENT_ENVIRONMENT` | agent-based workspace: both or neither |
| `LANGSMITH_PROJECT` | project-based workspace only; never together with the two above |
| `LANGSMITH_ENDPOINT` | only if the account is not in the US region, e.g. `https://eu.api.smith.langchain.com` |
| `LANGSMITH_WORKSPACE_ID` | only if the key is linked to several workspaces |
| `MONGODB_URI`, `MONGODB_DB` | DxP convention (see `dxp-modal`); used by the checkpointer |
| `DXP_TRIAGE_MODEL`, `DXP_EXTRACT_MODEL` | DxP convention defined here; `provider:model` strings |

`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT` are legacy names that the current docs no longer use for setup. Use the `LANGSMITH_*` names.

One-time LangSmith setup in an agent-based workspace: in the UI choose **+ Agent** > **Connect** > **Connect an existing agent**, enter a name and an **Agent ID** such as `dxp` (lowercase letters, digits, hyphens; cannot be changed later). Then set `LANGSMITH_AGENT_ID=dxp` and `LANGSMITH_AGENT_ENVIRONMENT=local` (use `production` in the Modal secret). In code, `client.agents.create(id="dxp", name="DxP", source_type="EXTERNAL")` does the same but needs a key with `projects:create`; a tracing key cannot do it.

## Core patterns

Full, runnable files are in [references/pipeline.md](references/pipeline.md) (models, two-pass item graph, batch fan-out, store stand-in) and [references/review.md](references/review.md) (reviewer pause and resume). The essentials:

### 1. Define a graph (current API)

```python
from typing import Literal
from typing_extensions import NotRequired, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

class ItemState(TypedDict):          # TypedDict, Pydantic model or dataclass
    text: str
    triage: NotRequired[dict]
    extraction: NotRequired[dict]

def triage(state: ItemState) -> dict:            # a node returns a partial state update
    return {"triage": {"relevant": "lung" in state["text"].lower()}}

def route(state: ItemState) -> Literal["extract", END]:   # a conditional edge returns the next node name
    return "extract" if state["triage"]["relevant"] else END

def extract(state: ItemState) -> dict:
    return {"extraction": {"fields": []}}

builder = StateGraph(ItemState)
builder.add_node("triage", triage, retry_policy=RetryPolicy(max_attempts=2))
builder.add_node("extract", extract)
builder.add_edge(START, "triage")
builder.add_conditional_edges("triage", route)
builder.add_edge("extract", END)
graph = builder.compile()            # required before invoke/stream
graph.invoke({"text": "A lung nodule classifier"})
```

A state key written by several parallel nodes needs a reducer: `done: Annotated[list[dict], operator.add]`. Without one, the last write overwrites.

### 2. Claude through langchain-anthropic, swappable (FR-5)

```python
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

class Triage(BaseModel):
    relevant: bool = Field(description="True only if the text describes a lung cancer diagnostic")
    reason: str

model = init_chat_model("anthropic:claude-haiku-5-5", max_tokens=8192, timeout=120, max_retries=6)
triage_llm = model.with_structured_output(Triage, method="json_schema")   # native structured output
verdict = triage_llm.invoke([("system", "Classify the text."), ("human", "A ctDNA assay for NSCLC ...")])
verdict.relevant   # a validated Triage instance
```

- The class behind it is `langchain_anthropic.ChatAnthropic(model="claude-haiku-5-5")`; the parameter is `model`. `init_chat_model("provider:model")` keeps the provider swappable through one environment variable.
- Always pass `method="json_schema"`. The default method forces a tool call, which `dxp-claude-api` reports Sonnet 5.5 and Opus 5.5 reject with a 400 (not re-tested here).
- Thinking is on by default and its tokens count toward `max_tokens`, so keep `max_tokens` generous. `reasoning_effort="low"` (alias `effort`, `langchain-anthropic>=1.5.3`) makes the triage pass faster and cheaper.
- `with_structured_output(Schema, method="json_schema", include_raw=True)` returns `{"raw", "parsed", "parsing_error"}`; token counts are in `raw.usage_metadata`. A refusal raises `langchain_core.exceptions.ModelRefusalError`.
- `rate_limiter=InMemoryRateLimiter(requests_per_second=8, check_every_n_seconds=0.1, max_bucket_size=16)` (from `langchain.rate_limiters`) throttles requests per second, not tokens.

### 3. Two-pass: fast triage, then strong extraction (FR-5, FR-18)

`triage` (Haiku) -> conditional edge -> `extract` (Sonnet, quote per field) -> `verify_quotes` (plain Python: is each quote in the source text?). Irrelevant items end after the cheap call. The whole per-item flow is `process_source(source)` in `dxp/item_graph.py`.

### 4. Fan out a batch with Send (FR-4)

```python
from langgraph.types import Send

def fan_out(state: BatchState) -> list[Send]:      # returned from a conditional edge
    return [Send("process_item", {"batch_id": state["batch_id"], "source_id": s}) for s in state["source_ids"]]

def process_item(state: WorkerInput) -> dict:      # receives the Send payload, not the batch state
    try:
        result = process_source(store.load_source(state["source_id"]))
        status = "extracted" if result["extraction"] else "skipped"
    except Exception:                              # never let one item raise out of the node
        status = "failed"
    return {"done": [{"source_id": state["source_id"], "status": status}]}

builder.add_conditional_edges("plan", fan_out, ["process_item"])
builder.add_edge("process_item", "summarise")      # runs once after all workers
batch_graph.invoke(inputs, {"max_concurrency": 16, "run_name": "dxp-batch-42", "tags": ["dxp", "batch"]})
```

`max_concurrency` is a top-level config key, not under `configurable`. Keep only ids in the batch state and load text inside the worker. `dxp-modal` describes the other shape (Modal `.map`, one container input per item, calling `process_source`); choose one and do not nest them. The `Send` shape is one trace per batch, the `.map` shape is one trace per item.

### 5. Pause for a Reviewer and resume (FR-16, FR-19)

```python
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.types import Command, interrupt
from pymongo import MongoClient

def review(state: ReviewState) -> dict:
    decision = interrupt({"kind": "proposed_change", "field": state["field"], "proposed_value": state["proposed_value"]})
    return {"decision": decision}                  # the value given to Command(resume=...)

checkpointer = MongoDBSaver(MongoClient(os.environ["MONGODB_URI"]), db_name="dxp")   # collections: checkpoints, checkpoint_writes
review_graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": change_id}}          # one thread per Proposed change
result = review_graph.invoke(change, config, durability="sync")
result["__interrupt__"][0].value                             # payload to show the Reviewer; the run is now parked in MongoDB

# later, in any process, after the Reviewer answers:
review_graph.invoke(Command(resume={"action": "reject", "reason": "wrong tumour stage", "reviewer": "ana"}), config, durability="sync")
```

`interrupt()` needs a checkpointer and a `thread_id`. On resume the node re-runs from its first line, so keep side effects after the `interrupt()` call or in a later node. Long-term memory is in `dxp-atlas-agent-memory`; this checkpointer is only the paused-run state.

### 6. Trace and tag for the camera

Tracing is automatic once the variables are set; nothing to import. Name and tag each run at the call site:

```python
config = {"run_name": "dxp-review-open", "tags": ["dxp", "review", "demo"],
          "metadata": {"thread_id": change_id, "batch_id": batch_id}}   # merge with configurable / max_concurrency
```

`tags` and `metadata` are inherited by every child run; `run_name` names only the top run. A `thread_id` (or `session_id`) metadata key groups separate traces, such as open and resume, into one LangSmith thread. To skip tracing for a bulk run: `with langsmith.tracing_context(enabled=False): ...`. For the video: open the trace, **Share** in the Details view menu, copy the public link (anyone with the link can view; unshare under **Settings** > **Shared URLs**). Filter the trace list by the `demo` tag to find it quickly.

### 7. Run inside Modal or a cron (no LangGraph Platform)

```python
@app.function(image=image, secrets=secrets, timeout=3600)          # app, image, secrets: see dxp-modal
def run_batch_graph(batch_id: str, source_ids: list[str]) -> dict:
    from dxp.batch import run_batch                                 # import inside: builds the graph once per container
    return run_batch(batch_id, source_ids)                          # calls wait_for_all_tracers() before returning

@app.function(image=image, secrets=secrets, timeout=3600, schedule=modal.Cron("0 6 * * *"))
def scheduled_scan() -> None:
    ...                                                             # collect new source ids, then run_batch(...)
```

Tracing posts from a background thread. Before a short-lived function returns, call `langchain_core.tracers.langchain.wait_for_all_tracers()`, or set `LANGCHAIN_CALLBACKS_BACKGROUND=false`. Modal's default function timeout is 300 seconds; set `timeout`.

## Limits and costs

- **LangSmith Developer plan (free):** 1 seat, 5,000 base traces a month, 14-day retention. Without a card: 5,000 traces a month hard limit, 50,000 run events an hour (creating and updating a run are 2 events), 500 MB of trace data an hour. With a card: 250,000 events and 2.5 GB an hour, pay as you go beyond 5,000 traces. At most 25,000 runs in one trace.
- **Sizing (estimate, not measured):** a batch item produces roughly 6 to 12 runs, so 500 items is about 3,000 to 6,000 runs in one trace and up to about 12,000 events. That fits, about four full batches an hour without a card. Trace size counts too: keep full page text out of the batch state.
- **Claude calls:** `max_retries` defaults to 6 with exponential backoff on 429, 5xx and network errors. A node `RetryPolicy` multiplies that (defaults: 3 attempts, 0.5 s initial interval, backoff factor 2). Size `max_concurrency` and the rate limiter to the Claude tier (PRD section 8; numbers in `dxp-claude-api`).
- **Structured output:** the first request with a new schema is slower while the grammar compiles; it is cached for 24 hours. Warm it up before the demo.
- **Node timeouts** (`add_node(..., timeout=60)`, `langgraph>=1.2`) apply only to async nodes and fail at compile time on sync nodes. For sync nodes rely on the model `timeout`.

## Gotchas

- `RetryPolicy` does not retry `ValueError`, `TypeError`, `LookupError`, `RuntimeError`, `OSError` and a few others by default, and retries HTTP-library errors only on 5xx. A Pydantic validation error is a `ValueError`: it is not retried.
- `interrupt()` is raised as an exception. Never wrap it in `try/except Exception`. It also bypasses retry policies and error handlers.
- Any `Command` passed as graph input resumes from the last checkpoint. Start a new run with a plain dict.
- Renaming or removing a node breaks threads paused on it. Add new state keys as `NotRequired`.
- Pydantic schemas for `method="json_schema"`: no `ge`/`le`/`min_length`/`max_length`, no recursive models, no free-form `dict` fields. Use flat models and lists of models.
- Updates from a parallel step arrive in no fixed order.
- `defer=True` on `add_node` delays a node until nothing else is pending. Only needed when fan-out branches have different lengths; the batch graph here does not need it.
- The prebuilt agent constructor in current docs is `langchain.agents.create_agent`. Nothing in these patterns needs it.
- Model objects are built at import time and need `ANTHROPIC_API_KEY`. Import graph modules inside the Modal function body, not at the top of the Modal file.

## Fallback

- **LangSmith misbehaves or the quota is gone:** set `LANGSMITH_TRACING=false`. Nothing else changes. Show progress from MongoDB and use a trace shared earlier for the video.
- **`MongoDBSaver` fails against the current LangGraph:** keep the Proposed change as a plain MongoDB document with a `status`, drop `interrupt()`, and call the nodes after it (`apply_decision`, `draft_rule`, `save_rule`) as a second small graph when the Reviewer acts. The pause still survives a restart because it is a document. `InMemorySaver` (`langgraph.checkpoint.memory`) keeps the interrupt code working but loses pending reviews on restart; say so if it is on camera.
- **`Send` fan-out misbehaves:** call `process_source` from a `concurrent.futures.ThreadPoolExecutor`, or use the Modal `.map` shape in `dxp-modal`. The item graph does not change.
- **Structured output returns 400 for a schema:** flatten the schema (strings only), or change the model through `DXP_EXTRACT_MODEL`.

## Links

- Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- Send and Command: https://docs.langchain.com/oss/python/langgraph/graph-api-send-command
- Interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- Fault tolerance (retries, timeouts, error handlers): https://docs.langchain.com/oss/python/langgraph/fault-tolerance
- Control flow (parallel steps, `max_concurrency`, `defer`): https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow
- Checkpointers and durability modes: https://docs.langchain.com/oss/python/langgraph/checkpointers
- MongoDB and LangGraph: https://www.mongodb.com/docs/atlas/ai-integrations/langgraph/
- ChatAnthropic: https://docs.langchain.com/oss/python/integrations/chat/anthropic
- Trace LangGraph with LangSmith: https://docs.langchain.com/langsmith/trace-with-langgraph
- Send traces to an agent (new workspaces): https://docs.langchain.com/langsmith/log-traces-to-agent
- LangSmith rate and usage limits: https://docs.langchain.com/langsmith/administration-overview#rate-limits
- LangSmith pricing: https://www.langchain.com/pricing
- Any docs page as raw Markdown: append `.md` to its URL
