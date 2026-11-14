"""One LangGraph run per run (AD-12): an `items` node, then a `Send` fan-out over the items.

- `items`: `discover` calls `discovery.scan(scope_id, ctx)` (A05, which admits and gates its
  own `search_source`); `nct:<NCT ID>` is the one setup item; a `task:` run is handed to
  `tasks.run` (A25) and fans out over nothing.
- `item`: one Source item, `pipeline.item.process`. Concurrency is `max_concurrency` from
  `config.concurrency()` (1 with `DXP_DEMO_PACE`, so the items keep the scan's order, the
  anchor first, with a pause after each).
- Tracing: LangSmith traces the graph when `LANGSMITH_TRACING` is on; the run is named after
  the run ID. No source text is put into the graph state, only refs and result codes.
"""

from __future__ import annotations

import asyncio
import operator
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from dxp.pipeline import config


class RunState(TypedDict, total=False):
    refs: list[str]
    results: Annotated[list[dict[str, Any]], operator.add]


class ItemState(TypedDict):
    ref: str
    index: int


ListItems = Callable[[], Awaitable[list[str]]]
ProcessItem = Callable[[str], Awaitable[dict[str, Any]]]


def build(list_items: ListItems, process_item: ProcessItem, pace: float | None) -> Any:
    async def items_node(state: RunState) -> dict[str, Any]:
        return {"refs": await list_items()}

    def fan_out(state: RunState) -> list[Send] | str:
        refs = state.get("refs") or []
        if not refs:
            return END
        return [Send("item", {"ref": ref, "index": i}) for i, ref in enumerate(refs)]

    async def item_node(state: ItemState) -> dict[str, Any]:
        result = await process_item(state["ref"])
        if pace and result.get("status") not in ("not_started",):
            await asyncio.sleep(pace)
        return {"results": [result]}

    graph = StateGraph(RunState)
    graph.add_node("items", items_node)
    graph.add_node("item", item_node)
    graph.add_edge(START, "items")
    graph.add_conditional_edges("items", fan_out, ["item", END])
    graph.add_edge("item", END)
    return graph.compile()


async def invoke(run_id: str, list_items: ListItems, process_item: ProcessItem) -> list[dict[str, Any]]:
    pace = config.pace_seconds()
    graph = build(list_items, process_item, pace)
    final = await graph.ainvoke(
        {"refs": [], "results": []},
        config={
            "max_concurrency": config.concurrency(),
            "run_name": f"dxp run {run_id}",
            "tags": ["dxp", "run"],
            "metadata": {"run_id": run_id},
        },
    )
    return list(final.get("results") or [])
