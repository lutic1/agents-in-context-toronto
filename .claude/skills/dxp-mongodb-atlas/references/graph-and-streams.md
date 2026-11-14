> Reference only. Do not copy this code into the project; it was written before the event.

# Graph view and live updates (FR-13, FR-26, FR-27)

Checked on 12 November 2026 against the `$graphLookup` and change stream pages of the MongoDB manual and the PyMongo 4.19 API reference.

## Graph storage

`$graphLookup` walks one collection by matching a field in one document to a field in another. So keep every node type in one collection.

```python
# graph_nodes
{"_id": "diagnostic:66f0...",          # "<type>:<stable id>"
 "type": "diagnostic",                 # diagnostic | biomarker | tumour_type | trial | drug | provider
 "label": "Guardant360 CDx",
 "ref": {"collection": "diagnostics", "id": ObjectId("66f0...")},   # what a click opens
 "neighbours": ["trial:NCT01234567", "drug:osimertinib", "provider:guardant health"],
 "lifecycle_stage": "regulatory approval", "early_research": False,  # diagnostics only
 "created_at": datetime, "updated_at": datetime, "last_change_id": None}

# graph_links: one document per pair, _id = the two node ids sorted and joined with "|"
{"_id": "diagnostic:66f0...|trial:NCT01234567", "source": "diagnostic:66f0...",
 "target": "trial:NCT01234567", "rel": "used_in", "created_at": datetime,
 "updated_at": datetime, "change_id": None}
```

Store `neighbours` on both ends. `$graphLookup` follows `connectFromField` outwards only, so a one-way list makes trials reachable from a Diagnostic but not the reverse.

Writing a link, safe under parallel workers:

```python
from datetime import datetime, timezone

async def upsert_node(db, node_id: str, type_: str, label: str, extra: dict | None = None):
    now = datetime.now(timezone.utc)
    await db.graph_nodes.update_one(
        {"_id": node_id},
        {"$setOnInsert": {"type": type_, "label": label, "created_at": now},
         "$set": {"updated_at": now, **(extra or {})}},
        upsert=True)

async def link(db, a: str, b: str, rel: str, change_id=None):
    now = datetime.now(timezone.utc)
    await db.graph_nodes.update_one({"_id": a}, {"$addToSet": {"neighbours": b}, "$set": {"updated_at": now}})
    await db.graph_nodes.update_one({"_id": b}, {"$addToSet": {"neighbours": a}, "$set": {"updated_at": now}})
    s, t = sorted([a, b])
    await db.graph_links.update_one(
        {"_id": f"{s}|{t}"},
        {"$setOnInsert": {"source": s, "target": t, "rel": rel, "created_at": now},
         "$set": {"updated_at": now, "change_id": change_id}},
        upsert=True)
```

Call `upsert_node` for both ends before `link`: `link` does not create nodes. `$addToSet` is right here because `neighbours` holds plain strings. `_id` is always unique, so the link upsert cannot duplicate. Do not put the same path (`label`, `type`) in both `$setOnInsert` and `$set`: one path in two operators is an error.

## Neighbourhood of a node with `$graphLookup`

```python
async def neighbourhood(db, node_id: str, hops: int = 1, skip_types: list[str] | None = None) -> dict:
    lookup = {
        "from": "graph_nodes",
        "startWith": "$neighbours",            # an array: the search starts from every element
        "connectFromField": "neighbours",
        "connectToField": "_id",
        "as": "reached",
        "maxDepth": hops - 1,                  # 0 = direct neighbours only
        "depthField": "depth",                 # 0 for direct neighbours
    }
    if skip_types:
        lookup["restrictSearchWithMatch"] = {"type": {"$nin": skip_types}}
    cursor = await db.graph_nodes.aggregate([
        {"$match": {"_id": node_id}},
        {"$graphLookup": lookup},
    ])
    roots = [d async for d in cursor]
    if not roots:
        return {"nodes": [], "links": []}
    root = roots[0]
    reached = root.pop("reached")
    nodes = {root["_id"]: {**root, "depth": -1}}
    for n in reached:
        nodes.setdefault(n["_id"], n)
    ids = list(nodes)
    links = [l async for l in db.graph_links.find({"source": {"$in": ids}, "target": {"$in": ids}})]
    return to_payload(nodes.values(), links)
```

Front-end payload: a flat `nodes` and `links` object, the shape force-directed graph libraries take.

```python
def to_payload(nodes, links, last_visit=None) -> dict:
    def changed(d):
        return bool(last_visit and d.get("updated_at") and d["updated_at"] > last_visit)
    return {
        "nodes": [{"id": n["_id"], "type": n["type"], "label": n["label"],
                   "lifecycleStage": n.get("lifecycle_stage"), "earlyResearch": n.get("early_research", False),
                   "ref": {"collection": n["ref"]["collection"], "id": str(n["ref"]["id"])} if n.get("ref") else None,
                   "changed": changed(n)} for n in nodes],
        "links": [{"id": l["_id"], "source": l["source"], "target": l["target"], "rel": l["rel"],
                   "changed": changed(l)} for l in links],
    }
```

`last_visit` comes from the Team's stored session state (FR-27, FR-28). Convert every `ObjectId` and `datetime` before returning JSON.

The whole graph does not need `$graphLookup`: at DxP's size, `find({})` on both collections and `to_payload` is simpler and faster. Use `$graphLookup` for "expand this node", for FR-26's test (trial, drug and Provider one step from a Diagnostic: `hops=1`), and for links that cross Categories (`hops=2`).

## `$graphLookup` limits

- `from` must be in the same database. All matches for one start document land in one array inside one result document, so the result is capped by the 16 MB document limit.
- The stage has 100 MB of memory. Free and Flex clusters ignore `allowDiskUse`, so past 100 MB it errors instead of spilling to disk.
- Hub nodes blow up depth. Every lung Diagnostic links to the same tumour type, so `hops=2` through `tumour_type:nsclc` returns most of the graph. Pass `skip_types=["tumour_type"]` or keep `hops=1`.
- `restrictSearchWithMatch` takes ordinary query syntax only; `"$field"` references are treated as string literals.
- `reached` is unordered. Sort in Python by `depth` if order matters.
- There is no edge information in the output, only the documents reached. That is why links live in `graph_links`.
- `connectToField` should be indexed. `_id` always is.

## Change streams

Requirements: a replica set or sharded cluster. Every Atlas cluster qualifies, Free included (three nodes). No extra tier, no flag.

One consumer process watches the database and fans events out to browsers. Run it in the Python backend, not in a short-lived serverless function.

```python
import asyncio
from pymongo.errors import PyMongoError

WATCHED = ["diagnostics", "proposed_changes", "alerts", "graph_nodes", "graph_links", "batch_runs"]
PIPELINE = [{"$match": {"ns.coll": {"$in": WATCHED},
                        "operationType": {"$in": ["insert", "update", "replace"]}}}]

async def consume(db, handle, name: str = "ui-fanout"):
    """handle(event: dict) is an async callable. Resumes where it stopped after a restart."""
    state = await db.stream_state.find_one({"_id": name})
    token = state["token"] if state else None
    failures = 0
    while True:
        try:
            kwargs = {"resume_after": token} if token else {}
            async with await db.watch(PIPELINE, full_document="updateLookup", **kwargs) as stream:
                async for change in stream:
                    failures = 0
                    await handle({
                        "collection": change["ns"]["coll"],
                        "op": change["operationType"],
                        "id": str(change["documentKey"]["_id"]),
                        "updated": list(change.get("updateDescription", {}).get("updatedFields", {})),
                        "doc": change.get("fullDocument"),   # holds ObjectId and datetime: convert before JSON
                    })
                    token = stream.resume_token
                    await db.stream_state.update_one(
                        {"_id": name}, {"$set": {"token": token}}, upsert=True)
        except PyMongoError:
            failures += 1
            if failures >= 3 and token is not None:   # the token is probably too old: start from now
                token = None
                await db.stream_state.delete_one({"_id": name})
            await asyncio.sleep(1)
```

Notes:

- Do not add `stream_state` to `WATCHED`: the consumer writes it on every event and would feed itself.
- Saving the token costs one write per event. During a large batch on a Free or Flex cluster, save it every 20 events instead.
- The driver already retries resumable network errors inside `async for`. The `except` is for everything else. After three failures in a row the token is dropped and the stream starts from now; events in the gap are lost, so the UI should refetch on reconnect.
- The resume token is the event's `_id`. Never remove or rewrite `_id` in the pipeline: the server raises an error.
- A token can only be resumed while the oplog still holds that point. A consumer that was down for hours on a busy cluster should start fresh.
- Resume with the same pipeline and options that produced the token.
- `full_document="updateLookup"` returns the document as it is at lookup time, which can be later than the change. Fine for a UI; do not use it as an audit record.
- Allowed pipeline stages: `$match`, `$project`, `$addFields`, `$set`, `$unset`, `$replaceRoot`, `$replaceWith`, `$redact`.
- Free and Flex: a filter on the database name may use only a string or a regular expression. Filtering on `ns.coll` with `$in`, as above, is allowed.

Sync version for a script: `with db.watch(PIPELINE) as stream: for change in stream: ...`.

## Using the events

- FR-27 live: forward `graph_nodes` and `graph_links` events to the browser (server-sent events or a websocket from the backend) and patch the node or link by `id`. On reconnect, refetch the graph.
- FR-27 since last visit: this is a plain query, not a stream. `to_payload(..., last_visit=...)` marks anything with `updated_at` after the Team's last visit.
- FR-13 Alerts: react to an `update` on `diagnostics` whose `updated` list contains a `lifecycle.` path or a `lists.trials` path, or to an `insert` on `proposed_changes` with status `accepted`, then run the topic match and write the Alert. During the Baseline load (FR-30) the handler must skip Alert creation: carry a `baseline: true` flag on the batch run and check it.
- FR-4 progress: forward `batch_runs` updates.
