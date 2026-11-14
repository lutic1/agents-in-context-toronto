---
name: dxp-mongodb-atlas
description: MongoDB Atlas core features for DxP - PyMongo (sync and async), unique indexes and upserts, the Record document shape with field history, MongoDB Vector Search with Automated Embedding (`autoEmbed`, `$vectorSearch`, Voyage models), MongoDB Search synonym mappings (`$search`), `$graphLookup` for the Graph view and change streams (`watch`). Load when a task touches `pymongo`, `AsyncMongoClient`, `MongoClient`, `motor`, `MONGODB_URI`, `SearchIndexModel`, `create_search_index`, `$vectorSearch`, `$search`, `$graphLookup`, `watch()`, upserts, duplicates, M0 / Flex / M10 tiers. Agent memory is in `dxp-atlas-agent-memory`, not here.
---

# MongoDB Atlas core for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Event rule: everything in this skill is reference documentation. Do not copy code from it into the project; write new code during the event.
>
> Saturday scope is `_bmad-output/planning-artifacts/development-plan.md`. Baseline loading, PubMed, memory, Learned rules, Alerts, Tavily scans and the old three-minute recorded video (the 3-minute live demo is in scope) are deferred; ignore those parts of this skill.

## Verified

Checked 12 November 2026 against the official pages in Links.

- PyMongo: docs and API reference are for **4.19.0** (released 14 Oct 2026). PyPI also shows **4.20.0**, published 12 Nov 2026, with no entry yet in the official release notes. Python **3.11+** is required from 4.19.
- Motor: last release 3.7.1 (May 2025). Deprecated on 14 May 2026; critical fixes only until 14 May 2027.
- Atlas Free (M0) and Flex clusters run MongoDB 8.0.
- Automated Embedding models: `voyage-4-lite`, `voyage-4`, `voyage-4-large`, `voyage-code-4`, `voyage-code-3`.

## Read this first

1. **Names changed.** The docs now say "MongoDB Vector Search" and "MongoDB Search" (formerly Atlas Vector Search and Atlas Search). The feature is **Automated Embedding**; the index field type is `autoEmbed`. Use these names in the video.
2. **Automated Embedding status is not clearly GA.** The Atlas changelog lists it as Public Preview (May 2026) and has no later GA entry. The quick start page still carries a Preview banner; the Atlas tab of the feature page does not. Do not say "generally available" in the video. Ask MongoDB staff on the day.
3. **A Free cluster without a payment method gets 3 requests per minute (2,000 tokens per minute) for query-time embedding.** Every `$vectorSearch` with query text is one request. That breaks FR-13 (one query per Finding) and makes FR-21 fragile in a demo. A Free cluster with a payment method on the organisation, a Flex cluster or a dedicated cluster gets 2,000 requests per minute. `UNVERIFIED`: whether hackathon credits count as a payment method. Ask staff first thing.
4. **Nothing in this skill needs a dedicated (M10+) tier.** Search, Vector Search, Automated Embedding, `$graphLookup`, change streams and unique indexes all work on Free and Flex. What Free cannot do is carry the batch: see the tier table in Limits. The `dxp-atlas-agent-memory` skill reports that Agent Memory does not run on Free and wants M10, so one shared cluster will be an M10 in practice. On M10+ switch on storage auto-scaling, which Automated Embedding requires.
5. **Use PyMongo's async API, not Motor.** `from pymongo import AsyncMongoClient`. Do not `pip install motor`.
6. **Embeddings are generated asynchronously.** A document inserted a second ago is not yet returned by `$vectorSearch`. The same applies to `$search`.
7. The docs disagree on the query shape. The `$vectorSearch` reference and the Python quick start use `"query": {"text": "..."}`; the feature overview shows `"query": "..."`. Use the object form; if the server rejects it, try the string.

## What DxP uses it for

- FR-3: unique indexes and upserts so parallel processing never creates a duplicate Diagnostic.
- FR-4: atomic `$inc` counters for the live batch progress.
- FR-9: MongoDB Search synonym mapping, so "liquid biopsy" finds ctDNA Diagnostics.
- FR-11, FR-15, FR-16, FR-17: Record shape with per-field Evidence, status and history; list-valued fields that only grow.
- FR-13: Automated Embedding to match a Finding to one of the four update topics however it is worded.
- FR-21, FR-22: plain-language query plus filters as one `$vectorSearch` across all Records.
- FR-26, FR-27: `$graphLookup` for a node's neighbourhood; change streams to push changes to the Graph view and Alerts.

## Setup

```bash
pip install "pymongo~=4.19.0"   # dnspython comes with it; mongodb+srv:// works. 4.20.0 is hours old: not reviewed.
```

PyMongo reads no environment variable itself. DxP convention: `MONGODB_URI` (the `mongodb+srv://` string from Atlas) and `MONGODB_DB`.

Atlas: one project, one cluster. Add a database user. Add the callers' IP addresses to the project's IP access list; Modal and Vercel have changing addresses, so allow all addresses for the day (not re-checked today; the symptom is `ServerSelectionTimeoutError`). Creating search indexes from a driver needs the `Project Data Access Admin` role or higher.

Clients:

```python
import os
from pymongo import AsyncMongoClient, MongoClient

def sync_db():                       # scripts, index setup, seeding
    return MongoClient(os.environ["MONGODB_URI"])[os.environ["MONGODB_DB"]]

_client: AsyncMongoClient | None = None
def get_db():                        # API and agents: one client per process and event loop
    global _client
    if _client is None:
        _client = AsyncMongoClient(os.environ["MONGODB_URI"], maxPoolSize=50)
    return _client[os.environ["MONGODB_DB"]]
```

Async rules: every network call is awaited. `find()` is not awaited and returns a cursor for `async for`. `aggregate()` and `watch()` are awaited first: `cursor = await coll.aggregate(pipeline)`. An `AsyncMongoClient` must not be shared across threads or event loops.

## Core patterns

Document shape, upserts, accepting a change: `references/data-model.md`. Graph and change streams: `references/graph-and-streams.md`.

### One-off index setup (sync script, run before any ingest)

```python
import time
from pymongo import ASCENDING
from pymongo.operations import SearchIndexModel

db = sync_db()
db.diagnostics.create_index("match_key", unique=True)                      # FR-3
db.source_items.create_index([("source", ASCENDING), ("source_item_id", ASCENDING)], unique=True)
db.proposed_changes.create_index(
    [("diagnostic_id", ASCENDING), ("field", ASCENDING), ("finding_id", ASCENDING)], unique=True)

def ensure_search_index(coll, model: SearchIndexModel, name: str):
    if name not in {i["name"] for i in coll.list_search_indexes()}:
        coll.create_search_index(model=model)
    while True:                                   # creation returns before the index is built
        found = list(coll.list_search_indexes(name))
        if found and found[0].get("queryable"):
            return
        time.sleep(5)

# FR-21: Records. search_text is a string you assemble (name, synonyms, biomarker, summary).
ensure_search_index(db.diagnostics, SearchIndexModel(
    name="dx_vector", type="vectorSearch",
    definition={"fields": [
        {"type": "autoEmbed", "modality": "text", "path": "search_text", "model": "voyage-4"},
        {"type": "filter", "path": "facets.modality"},
        {"type": "filter", "path": "facets.tumour_type"},
        {"type": "filter", "path": "facets.tumour_stage"},
        {"type": "filter", "path": "facets.sample_type"},
        {"type": "filter", "path": "facets.clinical_use"},
        {"type": "filter", "path": "facets.regulatory_status"},
        {"type": "filter", "path": "early_research"},
    ]}), "dx_vector")

# FR-13: seed alert_topics first (several example phrasings per topic), then index it.
ensure_search_index(db.alert_topics, SearchIndexModel(
    name="topic_vector", type="vectorSearch",
    definition={"fields": [
        {"type": "autoEmbed", "modality": "text", "path": "text", "model": "voyage-4"}]}), "topic_vector")

# FR-9: insert the synonym documents into search_synonyms BEFORE creating this index.
ensure_search_index(db.diagnostics, SearchIndexModel(
    name="dx_search",
    definition={
        "mappings": {"dynamic": False, "fields": {
            "name":        {"type": "string", "analyzer": "lucene.standard"},
            "synonyms":    {"type": "string", "analyzer": "lucene.standard"},
            "search_text": {"type": "string", "analyzer": "lucene.standard"}}},
        "synonyms": [{"name": "dx_synonyms", "analyzer": "lucene.standard",
                      "source": {"collection": "search_synonyms"}}]}), "dx_search")
```

Optional `autoEmbed` settings: `numDimensions` 256, 512, 1024 (default) or 2048; `quantization` `float`, `scalar` (default), `binary`, `binaryNoRescore`; `similarity`. After creation `path`, `model`, `quantization` and `numDimensions` cannot be edited: drop and recreate. An index cannot mix `vector` and `autoEmbed` fields.

### FR-21: plain-language query with filters

```python
async def search_records(db, text: str, filters: dict, limit: int = 20) -> list[dict]:
    """filters uses facets.* paths, e.g. {"facets.tumour_stage": {"$in": ["I", "II"]}}."""
    stage = {"index": "dx_vector", "path": "search_text", "query": {"text": text},
             "exact": True, "limit": limit}          # exact search: fine for a few thousand Records
    if filters:
        stage["filter"] = filters
    cursor = await db.diagnostics.aggregate([
        {"$vectorSearch": stage},
        {"$project": {"name": 1, "fields": 1, "lists": 1, "lifecycle": 1, "early_research": 1,
                      "score": {"$meta": "vectorSearchScore"}}},
    ])
    return [d async for d in cursor]
```

`$vectorSearch` must be the first stage and cannot go inside `$lookup` or `$facet`. `filter` accepts only `$eq $ne $gt $lt $gte $lte $in $nin $exists $not $nor $and $or` on fields indexed as `filter`. For approximate search drop `exact` and pass `numCandidates` (at most 10000, about 20 times `limit`). If only filters are given and no text, use a plain `find` on `facets.*`.

### FR-13: does this Finding fall under an update topic?

`alert_topics` documents: `{"topic": "lifecycle_advance" | "line_of_therapy" | "used_in_trial" | "standard_of_care", "text": "<one example phrasing>"}`.

```python
async def match_topic(db, finding_text: str, threshold: float) -> dict | None:
    cursor = await db.alert_topics.aggregate([
        {"$vectorSearch": {"index": "topic_vector", "path": "text",
                           "query": {"text": finding_text}, "exact": True, "limit": 1}},
        {"$project": {"_id": 0, "topic": 1, "text": 1, "score": {"$meta": "vectorSearchScore"}}},
    ])
    hits = [d async for d in cursor]
    return hits[0] if hits and hits[0]["score"] >= threshold else None
```

Calibrate `threshold` on real Findings before the demo. Scores run from 0 to 1, but the official sample's good matches score about 0.50, so do not guess 0.8. On a Free cluster with no payment method, turn this round: index the Findings' text instead (index-time embedding is not held to 3 per minute) and run the four topic queries per sweep, spaced 20 seconds apart.

### FR-9: synonyms

Source collection `search_synonyms`, same database as `diagnostics`. Use `explicit` for broader-to-narrower, `equivalent` for true synonyms:

```python
db.search_synonyms.insert_many([
    {"mappingType": "explicit", "input": ["liquid biopsy"],
     "synonyms": ["liquid biopsy", "ctdna", "cfdna", "circulating tumor dna", "circulating tumour dna"]},
    {"mappingType": "equivalent",
     "synonyms": ["ctdna", "circulating tumor dna", "circulating tumour dna"]},
])
```

```python
async def keyword_search(db, term: str, limit: int = 20) -> list[dict]:
    cursor = await db.diagnostics.aggregate([
        {"$search": {"index": "dx_search", "text": {
            "query": term, "path": ["name", "synonyms", "search_text"],
            "synonyms": "dx_synonyms", "matchCriteria": "all"}}},
        {"$limit": limit},
        {"$project": {"name": 1, "score": {"$meta": "searchScore"}}},
    ])
    return [d async for d in cursor]
```

Always pass `matchCriteria` with `synonyms`. `fuzzy` cannot be combined with `synonyms`. Synonyms work only in the `text` and `phrase` operators and only on fields analysed with the mapping's analyzer. Edits to the source collection are picked up without rebuilding the index, after a delay. The docs show a multi-word synonym only on the output side, so run the FR-9 test ("liquid biopsy" returns ctDNA Diagnostics) as soon as the index is queryable; if `text` misses, use the `phrase` operator with the same `synonyms` option.

## Limits and costs

Dedicated-tier limits were not looked up today; that column says only what the Free, Flex and Automated Embedding pages state.

| | Free (M0) | Flex | Dedicated (M10+) |
| --- | --- | --- | --- |
| Throughput | 100 operations per second, then throttled | 500 operations per second | no such cap on the pages read |
| Storage | 0.5 GB | 5 GB | by disk size |
| Connections | 500 | 500 | not checked |
| Search plus vector indexes | 3 in total | 10 | no fixed count; small tiers degrade |
| Query-time embedding | 3 requests per minute without a payment method | 2,000 per minute | 2,000 per minute |
| Synonyms | one mapping per index, 10,000 synonym documents | no such limit listed | no such limit listed |
| `allowDiskUse` | ignored | ignored | not checked |
| Change streams | yes | yes | yes |
| Cost | free | $8 to $30 per 30 days | not checked |

- **Ask for a Flex cluster or an M10 from the credits.** Free's 100 operations per second throttles a batch of 300 to 500 Source items that each write several times, and its three-index cap is used up by `dx_vector`, `topic_vector` and `dx_search`. `UNVERIFIED`: whether one `bulk_write` counts as one operation against the cap.
- On a dedicated cluster, Automated Embedding requires storage auto-scaling to be switched on.
- Embedding cost: 200 million free tokens per model per organisation, once. Then `voyage-4` is $0.06 per million tokens. Index-time inserts and updates: 2,000 requests per minute. Text over 32,000 tokens is truncated at index time; query text over that fails with `context-limit-exceeded`.
- Embedding inference runs on MongoDB infrastructure in any region by default; there is no cluster-region requirement.
- `maxPoolSize` defaults to 100. With many Modal containers, set it so that containers times pool size stays under the 500-connection cap.
- Free and Flex: pipelines of at most 50 stages, 32 MB in-memory sort, no `$where`.

## Gotchas

- PyMongo 4.19 dropped Python 3.9 and 3.10. On those, `pip install "pymongo~=4.19.0"` finds no matching distribution. Pin the Modal image to Python 3.11 or later.
- Upsert filters for FR-3 must be equality on exactly the unique-index fields, and the update must not write those fields. Otherwise concurrent upserts raise `DuplicateKeyError` instead of converging. Catch it and retry once anyway.
- `$addToSet` does not deduplicate list entries that carry Evidence: it compares whole documents, field order included. Guard with `{"lists.trials.key": {"$ne": key}}` and `$push`.
- Do not `$set` `fields.x` and `$push` `fields.x.history` in one update: parent and child paths conflict. Set the sub-keys.
- `create_search_index` returns before the index exists. Query only after `queryable` is true. Creating a `dx_search` index while `search_synonyms` holds a malformed document fails the build.
- A misspelt index name in `$vectorSearch` returns no results and no error.
- `$vectorSearch` and `$search` are eventually consistent. For "the Record just changed" paths (FR-16, FR-27) read with `find`, never through search.
- Change streams on Free and Flex: database-name filters accept only strings and regular expressions. Filtering on collection names is unrestricted.
- PyMongo 4.18 and later raise `ConfigurationError` when an `aggregate` or `pipeline` keyword argument is passed to `aggregate()` or `list_search_indexes()`. Pass the pipeline positionally.
- Never write to the `__mdb_internal_search` database; Automated Embedding stores its vectors there.
- Motor idioms that fail: `AsyncIOMotorClient(io_loop=...)`, `cursor.each()`, `to_list(0)` (use `to_list(None)`).

## Fallback

- Automated Embedding unavailable or rate-limited: FR-21 becomes Claude parsing the request into `facets.*` filters plus `keyword_search` on the remaining terms; FR-13 becomes Claude classifying the Finding against the four topic definitions. Say so in the video; do not credit Vector Search for it.
- Synonym index will not build: expand the term in the application by looking it up in `search_synonyms` and querying `{"synonyms_norm": {"$in": expanded}}` with `find`.
- `$graphLookup` trouble: two `find` calls (the node, then `{"_id": {"$in": node["neighbours"]}}`).
- Change stream trouble: poll `find({"updated_at": {"$gt": last_seen}})` every two seconds.
- Free cluster throttling mid-batch: lower batch concurrency and group writes with `bulk_write(ops, ordered=False)`.

## Links

- Automated Embedding: https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/
- Models, rate limits, free tokens: https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/models/
- Vector index definition: https://www.mongodb.com/docs/vector-search/indexes/vector-search-type/
- `$vectorSearch` stage: https://www.mongodb.com/docs/vector-search/query/aggregation-stages/vector-search-stage/
- Vector Search quick start (Python `autoEmbed` sample): https://www.mongodb.com/docs/vector-search/tutorials/quick-start/
- Synonym mappings: https://www.mongodb.com/docs/search/indexes/synonyms/
- `text` operator: https://www.mongodb.com/docs/search/query/operators-collectors/text/
- `$graphLookup`: https://www.mongodb.com/docs/manual/reference/operator/aggregation/graphLookup/
- Change streams: https://www.mongodb.com/docs/manual/changeStreams/
- Upsert with a unique index: https://www.mongodb.com/docs/manual/reference/method/db.collection.update/
- Free cluster limits: https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/
- Flex limits and costs: https://www.mongodb.com/docs/atlas/reference/flex-limitations/ and https://www.mongodb.com/docs/atlas/billing/atlas-flex-costs/
- PyMongo guide: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/
- Motor to PyMongo Async: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/
- PyMongo API reference: https://pymongo.readthedocs.io/en/4.19.0/api/
- Atlas changelog: https://www.mongodb.com/docs/atlas/release-notes/changelog/
