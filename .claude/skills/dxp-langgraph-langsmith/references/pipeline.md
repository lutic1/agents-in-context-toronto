> Reference only. Do not copy this code into the project; it was written before the event.

# Two-pass item graph and batch fan-out (FR-4, FR-5, FR-18)

Verified 2026-11-12 against langgraph 1.2.21, langchain 1.5.0, langchain-anthropic 1.7.10. Every LangGraph and LangChain call below appears on an official page listed in SKILL.md. Nodes are sync so the same code runs under LangGraph's own fan-out and under Modal's thread-based `.map` (see `dxp-modal`).

The reference implementation below, in five files, shows the approach; write your own during the event. In it, `store.py` is a stand-in whose bodies would be MongoDB calls.

## dxp/models.py

```python
import os

from langchain.chat_models import init_chat_model
from langchain.rate_limiters import InMemoryRateLimiter

# "provider:model" strings. Change the environment variable to swap model or provider.
TRIAGE_MODEL = os.environ.get("DXP_TRIAGE_MODEL", "anthropic:claude-haiku-5-5")
EXTRACT_MODEL = os.environ.get("DXP_EXTRACT_MODEL", "anthropic:claude-sonnet-5-5")

# Thread safe; shared by every model in the process. Limits request rate only, not tokens.
_limiter = InMemoryRateLimiter(
    requests_per_second=float(os.environ.get("DXP_LLM_RPS", "8")),
    check_every_n_seconds=0.1,
    max_bucket_size=16,
)


def chat_model(model_id: str, **kwargs):
    # Do NOT pass temperature, top_p or top_k: current Claude models answer 400.
    return init_chat_model(
        model_id,
        max_tokens=8192,   # thinking tokens count toward max_tokens; too low truncates the JSON
        timeout=120,       # seconds per request
        max_retries=6,     # default; retries 429, 5xx and network errors with backoff
        rate_limiter=_limiter,
        **kwargs,
    )
```

## dxp/schemas.py

```python
from pydantic import BaseModel, Field

# Native structured output rejects numeric and string constraints (ge, le, min_length ...),
# recursive models and open dicts. Keep models flat; validate ranges in code.


class Triage(BaseModel):
    """Fast first pass: is this Source item about a lung cancer diagnostic?"""

    relevant: bool = Field(description="True only if the text describes a lung cancer diagnostic")
    reason: str = Field(description="One short sentence")


class FieldValue(BaseModel):
    field: str = Field(description="Record field name, from the list in the system prompt")
    value: str
    quote: str = Field(description="Span copied word for word from the source text that supports the value")
    confidence: float = Field(description="Between 0 and 1")


class Extraction(BaseModel):
    """Second pass: one entry per Record field the text supports. Omit unsupported fields."""

    diagnostic_name: str
    fields: list[FieldValue]
```

## dxp/item_graph.py

```python
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy
from typing_extensions import NotRequired, TypedDict

from dxp.models import EXTRACT_MODEL, TRIAGE_MODEL, chat_model
from dxp.schemas import Extraction, Triage

TRIAGE_PROMPT = "Decide whether the text describes a diagnostic test for lung cancer. Answer in the given format."
EXTRACT_PROMPT = (
    "Extract Record fields for the lung cancer diagnostic described in the text. "
    "For every field give a quote copied word for word from the text. Leave out fields the text does not support."
)
TRIAGE_CHARS = 6000


class ItemState(TypedDict):
    source_id: str
    source_type: str
    text: str
    triage: NotRequired[dict]
    extraction: NotRequired[dict]
    checks: NotRequired[list[dict]]


# reasoning_effort is the provider-neutral name; ChatAnthropic also accepts effort= (langchain-anthropic >= 1.5.3).
triage_llm = chat_model(TRIAGE_MODEL, reasoning_effort="low").with_structured_output(Triage, method="json_schema")
extract_llm = chat_model(EXTRACT_MODEL, reasoning_effort="medium").with_structured_output(Extraction, method="json_schema")


def triage(state: ItemState) -> dict:
    verdict = triage_llm.invoke([("system", TRIAGE_PROMPT), ("human", state["text"][:TRIAGE_CHARS])])
    return {"triage": verdict.model_dump()}


def route_after_triage(state: ItemState) -> Literal["extract", END]:
    return "extract" if state["triage"]["relevant"] else END


def extract(state: ItemState) -> dict:
    result = extract_llm.invoke([("system", EXTRACT_PROMPT), ("human", state["text"])])
    return {"extraction": result.model_dump()}


def _norm(text: str) -> str:
    return " ".join(text.split())


def verify_quotes(state: ItemState) -> dict:
    """FR-18: the quote must appear word for word in the Source item. No model call."""
    source = _norm(state["text"])
    return {
        "checks": [
            {"field": f["field"], "quote_in_source": bool(f["quote"]) and _norm(f["quote"]) in source}
            for f in state["extraction"]["fields"]
        ]
    }


builder = StateGraph(ItemState)
builder.add_node("triage", triage, retry_policy=RetryPolicy(max_attempts=2))
builder.add_node("extract", extract, retry_policy=RetryPolicy(max_attempts=2))
builder.add_node("verify_quotes", verify_quotes)
builder.add_edge(START, "triage")
builder.add_conditional_edges("triage", route_after_triage)
builder.add_edge("extract", "verify_quotes")
builder.add_edge("verify_quotes", END)
item_graph = builder.compile()  # no checkpointer: an item is cheap to redo


def process_source(source: dict) -> dict:
    """Pure function, no database I/O. source = {"source_id", "source_type", "text"}."""
    out = item_graph.invoke(source)
    return {
        "source_id": source["source_id"],
        "relevant": out["triage"]["relevant"],
        "triage": out["triage"],
        "extraction": out.get("extraction"),
        "checks": out.get("checks", []),
    }
```

`process_source` is the single entry point for one Source item. Both fan-out shapes call it: `dxp/batch.py` below, and the per-item Modal function in `dxp-modal`.

## dxp/batch.py

```python
import operator
from collections import Counter
from typing import Annotated

from langchain_core.tracers.langchain import wait_for_all_tracers
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from typing_extensions import NotRequired, TypedDict

from dxp import store
from dxp.item_graph import process_source


class BatchState(TypedDict):
    batch_id: str
    source_ids: list[str]                          # ids only; workers load the text themselves
    done: Annotated[list[dict], operator.add]      # reducer: every worker appends one entry
    summary: NotRequired[dict]


class WorkerInput(TypedDict):                      # what Send passes; not the batch state
    batch_id: str
    source_id: str


def plan(state: BatchState) -> dict:
    return {"source_ids": sorted(set(state["source_ids"]))}


def fan_out(state: BatchState) -> list[Send]:
    return [Send("process_item", {"batch_id": state["batch_id"], "source_id": sid}) for sid in state["source_ids"]]


def process_item(state: WorkerInput) -> dict:
    sid, status, error = state["source_id"], "failed", None
    try:
        result = process_source(store.load_source(sid))
        if result["extraction"]:
            store.save_extraction(sid, result)     # must be an upsert: retries re-run this
            status = "extracted"
        else:
            status = "skipped"
    except Exception as exc:                       # a raise here would discard the WHOLE fan-out step
        error = f"{type(exc).__name__}: {exc}"
    try:
        store.bump_progress(state["batch_id"], status)   # FR-4 live count
    except Exception:
        pass
    return {"done": [{"source_id": sid, "status": status, "error": error}]}


def summarise(state: BatchState) -> dict:
    return {"summary": dict(Counter(d["status"] for d in state["done"]))}


builder = StateGraph(BatchState)
builder.add_node("plan", plan)
builder.add_node("process_item", process_item)
builder.add_node("summarise", summarise)
builder.add_edge(START, "plan")
builder.add_conditional_edges("plan", fan_out, ["process_item"])
builder.add_edge("process_item", "summarise")      # runs once, after every worker has finished
builder.add_edge("summarise", END)
batch_graph = builder.compile()                    # no checkpointer on purpose, see SKILL.md


def run_batch(batch_id: str, source_ids: list[str], max_concurrency: int = 16) -> dict:
    if not source_ids:
        return {}
    config = {
        "max_concurrency": max_concurrency,        # top level, not under "configurable"
        "run_name": f"dxp-batch-{batch_id}",
        "tags": ["dxp", "batch"],
        "metadata": {"batch_id": batch_id, "items": len(source_ids)},
    }
    try:
        state = batch_graph.invoke({"batch_id": batch_id, "source_ids": source_ids, "done": []}, config)
        return state["summary"]
    finally:
        wait_for_all_tracers()                     # tracing posts from a background thread
```

Notes on behaviour, all from the official pages:

- All `Send` tasks run in one super-step. The step is transactional: if any worker raises, none of that step's updates are applied. That is why `process_item` catches everything and reports `failed` as data.
- `max_concurrency` caps how many workers run at once. Start at 8 to 16 and size it to the Claude rate limit (PRD section 8), not to LangGraph.
- Updates from a parallel step are not ordered. Do not rely on the order of `done`.
- `batch_graph.stream(inputs, config, stream_mode="updates")` yields one chunk per worker, shaped `{"process_item": {"done": [...]}}`. Whether chunks arrive as each worker finishes or at the end of the step is `UNVERIFIED`; the live count for FR-4 therefore comes from `store.bump_progress`.
- `langgraph>=1.2` also offers `error_handler=` on `add_node` and `set_node_defaults(...)`. The try/except above is simpler and is the form the docs recommend for parallel branches.
- Going async: make the nodes `async def`, call `ainvoke`, and then `add_node(..., timeout=60)` or `Send(..., timeout=...)` becomes available. Node timeouts are rejected at compile time on sync nodes.

## dxp/store.py (stand-in)

In-memory so the graphs run before MongoDB is wired. Keep the signatures; replace the bodies using `dxp-mongodb-atlas`. Every write must be idempotent.

```python
from collections import Counter, defaultdict

SOURCES: dict[str, dict] = {}       # source_id -> {"source_id", "source_type", "text"}
EXTRACTIONS: dict[str, dict] = {}
PROGRESS: dict[str, Counter] = defaultdict(Counter)
DECISIONS: dict[str, dict] = {}
RULES: dict[str, dict] = {}


def load_source(source_id: str) -> dict:
    return SOURCES[source_id]


def save_extraction(source_id: str, result: dict) -> None:
    EXTRACTIONS[source_id] = result                 # MongoDB: upsert keyed by source_id / match key (FR-3)


def bump_progress(batch_id: str, status: str) -> None:
    PROGRESS[batch_id][status] += 1                 # MongoDB: $inc on the batch document


def apply_decision(change_id: str, decision: dict, change: dict) -> None:
    DECISIONS[change_id] = decision                 # MongoDB: update Record, keep prior value, log reviewer (FR-16, FR-17)


def save_rule(change_id: str, rule: dict) -> None:
    RULES[change_id] = rule                         # MongoDB: store Learned rule, flag pending changes (FR-19)
```

Smoke test without MongoDB (needs `ANTHROPIC_API_KEY`):

```python
from dxp import store
from dxp.batch import run_batch

store.SOURCES["s1"] = {"source_id": "s1", "source_type": "pubmed", "text": "A ctDNA assay for early-stage NSCLC reached 85% sensitivity."}
store.SOURCES["s2"] = {"source_id": "s2", "source_type": "pubmed", "text": "A study of knee replacement outcomes."}
print(run_batch("smoke", ["s1", "s2", "missing"]))   # {'extracted': 1, 'skipped': 1, 'failed': 1}
```
