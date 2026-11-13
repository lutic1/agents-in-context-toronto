# Reviewer pause and resume with a MongoDB checkpointer (FR-16, FR-19)

Verified 2026-11-12 against langgraph 1.2.21 and langgraph-checkpoint-mongodb 0.5.1 (`MongoDBSaver` signature read from the package source). Sources are listed in SKILL.md.

One Proposed change is one thread (`thread_id` = the change id). The graph pauses twice at most: once for accept, edit or reject, and once more to confirm the drafted Learned rule. Between pauses nothing is running; the state sits in MongoDB, so a restart or redeploy loses nothing.

```
START -> review (pause 1) -> apply_decision -+-> END                       accept, or no reason given
                                             +-> draft_rule -> confirm_rule (pause 2) -+-> save_rule -> END
                                                                                      +-> END   not confirmed
```

## dxp/review.py

```python
import os
from typing import Literal

from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt
from pydantic import BaseModel, Field
from pymongo import MongoClient
from typing_extensions import NotRequired, TypedDict

from dxp import store
from dxp.models import EXTRACT_MODEL, chat_model


class ReviewState(TypedDict):
    change_id: str
    diagnostic_id: str
    field: str
    current_value: str | None
    proposed_value: str
    evidence: dict                      # {"quote", "source_id", "url"}
    decision: NotRequired[dict]         # {"action", "value", "reason", "reviewer"}
    rule: NotRequired[dict]             # {"field", "text", "confirmed"}
    status: NotRequired[str]


def review(state: ReviewState) -> dict:
    # Nothing but payload building before interrupt(): this node re-runs from its first line on resume.
    decision = interrupt(
        {
            "kind": "proposed_change",
            "change_id": state["change_id"],
            "field": state["field"],
            "current_value": state["current_value"],
            "proposed_value": state["proposed_value"],
            "evidence": state["evidence"],
            "actions": ["accept", "edit", "reject"],
        }
    )
    return {"decision": decision}       # whatever was passed to Command(resume=...)


def apply_decision(state: ReviewState) -> dict:
    decision = state["decision"]
    store.apply_decision(state["change_id"], decision, dict(state))   # idempotent write, after the pause
    return {"status": {"accept": "accepted", "edit": "edited", "reject": "rejected"}[decision["action"]]}


def needs_rule(state: ReviewState) -> Literal["draft_rule", END]:
    decision = state["decision"]
    return "draft_rule" if decision["action"] in ("edit", "reject") and decision.get("reason") else END


class RuleDraft(BaseModel):
    rule: str = Field(description="One plain-language sentence, specific to this field, that a Reviewer can confirm")


rule_llm = chat_model(EXTRACT_MODEL).with_structured_output(RuleDraft, method="json_schema")


def draft_rule(state: ReviewState) -> dict:
    # Own node: if the model call shared a node with interrupt() it would run again on resume.
    decision = state["decision"]
    draft = rule_llm.invoke(
        [
            ("system", "A Reviewer corrected an extracted value. Write one stricter rule for this field so the same fault is flagged next time."),
            ("human", f"Field: {state['field']}\nProposed: {state['proposed_value']}\nReviewer action: {decision['action']}\n"
                      f"Reviewer value: {decision.get('value')}\nReason: {decision['reason']}\nQuote: {state['evidence'].get('quote')}"),
        ]
    )
    return {"rule": {"field": state["field"], "text": draft.rule, "confirmed": False}}


def confirm_rule(state: ReviewState) -> dict:
    answer = interrupt({"kind": "learned_rule", "change_id": state["change_id"], "rule": state["rule"]})
    text = answer.get("text") or state["rule"]["text"]          # the Reviewer may reword it
    return {"rule": {**state["rule"], "text": text, "confirmed": bool(answer.get("confirmed"))}}


def after_confirm(state: ReviewState) -> Literal["save_rule", END]:
    return "save_rule" if state["rule"]["confirmed"] else END


def save_rule(state: ReviewState) -> dict:
    store.save_rule(state["change_id"], state["rule"])          # app code flags pending changes here (FR-19)
    return {"status": f"{state['status']}+rule"}


builder = StateGraph(ReviewState)
builder.add_node("review", review)
builder.add_node("apply_decision", apply_decision)
builder.add_node("draft_rule", draft_rule, retry_policy=RetryPolicy(max_attempts=2))
builder.add_node("confirm_rule", confirm_rule)
builder.add_node("save_rule", save_rule)
builder.add_edge(START, "review")
builder.add_edge("review", "apply_decision")
builder.add_conditional_edges("apply_decision", needs_rule)
builder.add_edge("draft_rule", "confirm_rule")
builder.add_conditional_edges("confirm_rule", after_confirm)
builder.add_edge("save_rule", END)

_client = MongoClient(os.environ["MONGODB_URI"])
# Default collection names: checkpoints and checkpoint_writes. The constructor creates their indexes.
checkpointer = MongoDBSaver(_client, db_name=os.environ.get("MONGODB_DB", "dxp"))
review_graph = builder.compile(checkpointer=checkpointer)


def _config(change_id: str, step: str) -> dict:
    return {
        "configurable": {"thread_id": change_id},
        "run_name": f"dxp-review-{step}",
        "tags": ["dxp", "review"],
        "metadata": {"thread_id": change_id},   # groups the open and resume traces into one LangSmith thread
    }


def _awaiting(result: dict) -> dict | None:
    pending = result.get("__interrupt__")
    return pending[0].value if pending else None


def open_review(change: dict) -> dict | None:
    """Start the thread for a Proposed change. Returns the payload a Reviewer must answer."""
    result = review_graph.invoke(change, _config(change["change_id"], "open"), durability="sync")
    return _awaiting(result)


def submit(change_id: str, answer: dict) -> dict:
    """Resume with the Reviewer's answer. Works in a different process from open_review."""
    config = _config(change_id, "resume")
    if not review_graph.get_state(config).next:
        raise ValueError(f"{change_id} is not waiting for a Reviewer")   # finished, or never opened
    result = review_graph.invoke(Command(resume=answer), config, durability="sync")
    return {"awaiting": _awaiting(result), "status": result.get("status"), "rule": result.get("rule")}
```

## Using it

```python
from dxp.review import open_review, submit

payload = open_review({
    "change_id": "chg-001", "diagnostic_id": "dx-17", "field": "sensitivity",
    "current_value": "81%", "proposed_value": "92%",
    "evidence": {"quote": "sensitivity of 92% in stage III-IV disease", "source_id": "PMID-1", "url": "https://example.org"},
})
# payload["kind"] == "proposed_change". Stop the process here if you like; the pause is in MongoDB.

out = submit("chg-001", {"action": "reject", "reason": "Stage III-IV only; the field is for all stages", "reviewer": "ana"})
# out["awaiting"]["kind"] == "learned_rule", out["awaiting"]["rule"]["text"] is the drafted rule

out = submit("chg-001", {"confirmed": True})
# out == {"awaiting": None, "status": "rejected+rule", "rule": {..., "confirmed": True}}
```

Accept is `{"action": "accept", "reviewer": "ana"}`. Edit is `{"action": "edit", "value": "92% (stage III-IV)", "reason": "...", "reviewer": "ana"}`. Validate the answer in the API layer (a Pydantic model on the route) before calling `submit`; resume values must be JSON-serialisable.

Inspect a thread without resuming it:

```python
snap = review_graph.get_state({"configurable": {"thread_id": "chg-001"}})
snap.next                             # ("review",) or ("confirm_rule",) while paused, () when finished
snap.values                           # current state
snap.tasks[0].interrupts[0].value     # the payload again, while paused
```

## Rules that bite

- **The Reviewer queue is not in LangGraph.** LangGraph keeps no searchable index of paused threads. Write each Proposed change to its own collection with a `status` before calling `open_review`, and let the UI list from that collection. The checkpoint only holds the paused run.
- **Resume re-runs the node from its first line.** Keep writes after `interrupt()` or in a later node, and make them upserts.
- **One `interrupt()` per node, never inside `try/except Exception`.** The pause is raised as an exception; a broad except swallows it. Resume values are matched to interrupts by position inside a node.
- **Only `Command(resume=...)` is valid as graph input.** Passing `Command(update=...)` as input resumes from the last checkpoint instead of starting a run.
- **Do not rename or remove `review` or `confirm_rule` while threads are paused on them.** Resume looks the node up by name and fails. Adding nodes, edges and `NotRequired` state keys is safe. If you must rename, drop the `checkpoints` and `checkpoint_writes` collections and reopen the pending changes.
- **`durability="sync"`** writes each checkpoint before the next step starts, which is what you want in a short-lived container.
- **`MongoDBSaver(..., ttl=seconds)`** adds a TTL index. Leave it off: a pending review must not expire.
- **Batch resume.** If several parallel nodes are paused in one thread, resume them together with `Command(resume={interrupt.id: value, ...})`. One thread per Proposed change avoids the need.
- **Optional, `langgraph>=1.2.12`:** `interrupt(payload, response_schema=Decision)` validates the resume value against a Pydantic model and returns the model instance.
- **Other ways to read the pause.** `graph.invoke(..., version="v2")` returns a `GraphOutput` with `.value` and `.interrupts`; `graph.stream_events(..., version="v3")` exposes `.interrupted`, `.interrupts` and `.output` and is what the docs now recommend for streaming UIs. On a `GraphOutput`, `result["__interrupt__"]` is deprecated. The plain `invoke` used above returns a dict and is the current default.
