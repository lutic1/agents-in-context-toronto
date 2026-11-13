# Reality check: ARCHITECTURE-SPINE.md

Reviewed 13 November 2026 against `ARCHITECTURE-SPINE.md` (status draft, updated 2026-11-13). The spine and the skills were not edited.

## Verdict

The stack is sound: every version is evidenced and the whole Python set resolves together on Python 3.13. The mechanisms are mostly real, but nine places in the spine are risky or contradicted by documentation, and two matter most: the ingest job has no stated timeout (Modal's default is 300 seconds; the Baseline job needs 10 to 20 minutes), and the live feed as described can miss events.

| Result | Count |
| --- | --- |
| Verified | 43 (18 stack rows, 6 compatibility checks, 19 mechanism claims) |
| Risky or contradicted | 9 findings (R1 to R9), each with paste-in text |
| Unverifiable | 9 (section 5) |

## How this was checked

- **Skills.** The "Verified" and "Read this first" sections of the ten `dxp-*` skills under `/Users/luis/agents-in-context-toronto/.claude/skills/`, plus their reference files.
- **Registries, today.** PyPI JSON for every Python package and the npm registry for the front-end packages.
- **Package source, today.** Wheels of `langgraph` 1.2.21, `langchain-anthropic` 1.7.10, `anthropic` 2.8.0, `pymongo` 4.19.0, `agent-engine-sdk-memory` 0.11.14, `modal` 1.6.4 and `langsmith` 0.14.17 were downloaded and read. Nothing was installed or run.
- **Joint resolution, today.** `uv pip compile --python-version 3.13` over the eleven pinned Python packages.
- **Official pages, fetched today.** URLs are given beside each finding.

Verdict words: **verified** (evidence found), **risky** (the mechanism exists but the spine leaves out something it needs), **contradicted** (a document says otherwise), **unverifiable** (no document settles it).

## 1. Stack table

| Row | Evidence | Verdict |
| --- | --- | --- |
| Python 3.13 | `dxp-modal` (image uses `python_version="3.13"`; Modal needs `>=3.10,<3.16`). Every package's `requires_python` on PyPI admits 3.13. | Verified |
| FastAPI 0.162.5 | PyPI today: exists, Python `>=3.10`, needs `pydantic>=2.9.0`. | Verified |
| Pydantic 2.14.3 | PyPI today. Satisfies `agent-engine-sdk-memory` (`pydantic>=2.13.5`) and LangGraph (`>=2.7.4`). | Verified |
| PyMongo (async API) 4.19.0 | `dxp-mongodb-atlas` Verified (docs and API reference are for 4.19.0). PyPI today: 4.19.0 released 14 Oct 2026, not yanked, Python `>=3.11`. | Verified, see note 1 |
| MongoDB Atlas 8.0 | `dxp-mongodb-atlas` Verified (Free and Flex run 8.0). Flex page today: "Atlas uses at least MongoDB 8.0 for Flex clusters" and the version cannot be chosen. | Verified for Flex, see note 2 |
| LangGraph 1.2.21 | `dxp-langgraph-langsmith` Verified. PyPI classifiers list 3.13. | Verified |
| langchain-anthropic 1.7.10 | `dxp-langgraph-langsmith` and `dxp-claude-api` Verified. | Verified |
| LangSmith SDK 0.14.17 | `dxp-langgraph-langsmith` Verified. `langchain-core` 1.8.0 needs `langsmith>=0.14.9`. | Verified |
| Anthropic Python SDK 2.8.0 | `dxp-claude-api` Verified. PyPI: released 10 Nov 2026. | Verified |
| Claude models | `dxp-claude-api` Verified. Both IDs are in the supported list on the structured outputs page and in the rate limit tables, fetched today. | Verified |
| agent-engine-sdk-memory 0.11.14 | `dxp-atlas-agent-memory` Verified. The hosted guide still pins 0.11.8 (fetched today); the skill says to fall back to 0.11.8 if a call fails. | Verified |
| tavily-python 0.8.5 | `dxp-tavily` Verified. | Verified |
| ElevenLabs Python SDK 2.78.0 | `dxp-elevenlabs` Verified. | Verified |
| Modal 1.6.4 | `dxp-modal` Verified. | Verified |
| Next.js 16.4.6 | `dxp-vercel-frontend` Verified. npm today: peer `react ^19.0.0`, Node `>=20.9.0`. | Verified |
| React 19.3.1 | `dxp-vercel-frontend` Verified. npm today: `react-dom` 19.3.1 needs `react ^19.3.1`. | Verified |
| TypeScript 5.9 | `dxp-vercel-frontend` Verified (type-checked with tsc 5.9; `create-next-app` pins `^5`). npm: 5.9.3 is the last 5.x; `latest` is 7.0.2, which the skill marks UNVERIFIED with Next.js 16. | Verified |
| react-force-graph-2d 1.29.2 | `dxp-vercel-frontend` Verified. | Verified |

No row lacks evidence and no row disagrees with a skill's Verified section.

**Note 1, PyMongo pin.** 4.20.0 appeared on PyPI on 12 November with no release notes. `dxp-atlas-agent-memory` lists 4.20.0 in its table (the latest it saw), `dxp-modal` installs an unpinned `pymongo`, and `dxp-langgraph-langsmith` asks for `>=4.18.2`. Any of those will install 4.20.0. The spine's 4.19.0 holds only if the Modal image pins `pymongo==4.19.0` exactly.

**Note 2, MongoDB version.** On Flex the version is at least 8.0 and Atlas upgrades it. On M10 the version is chosen when the cluster is created; no skill records which versions are offered. Paste-in for the Stack row: `MongoDB Atlas | 8.0 or later (8.0 chosen if the cluster is M10)`.

**Missing from the table, needed by the stack.** `fastapi[standard]` (Modal's web decorators fail at container start without the extra, per `dxp-modal`) and Node.js 20.9 or later. `langchain` is not listed, so `init_chat_model`, which the LangGraph skill's examples use, is not available; use `ChatAnthropic` directly or add `langchain` 1.5.0.

### Compatibility checks

| Check | Evidence | Verdict |
| --- | --- | --- |
| Python 3.13 against every Python package | PyPI `requires_python`: FastAPI, Pydantic, LangGraph, LangSmith, Anthropic `>=3.10`; PyMongo, agent-engine-sdk-memory `>=3.11`; Tavily, ElevenLabs `>=3.8`; Modal `>=3.10,<3.16`. | Verified |
| The eleven pins resolve together | `uv pip compile --python-version 3.13` succeeded. It selected `langchain-core` 1.8.0, `langgraph-checkpoint` 4.3.1, `httpx` 0.28.1 beside `httpx2` 2.16.0, `typing-extensions` 4.16.0, `starlette` 1.10.0. | Verified |
| PyMongo 4.19.0 against 4.20.0 | See note 1. | Verified, pin exactly |
| React 19.3.1 with react-force-graph-2d 1.29.2 | npm today: peer `react: "*"`; its dependency `react-kapsule` 2.6 needs `react >=16.13.1`. The skill type-checked it and did not run it in a browser. | Verified |
| langchain-anthropic 1.7.10 with anthropic 2.8.0 | Requires `anthropic>=0.120.0`, no upper bound. Source: it builds its client from `anthropic.DefaultHttpxClient`, which SDK 2.8.0 still exports (now on `httpx2`), calls `beta.messages.with_raw_response.create`, which exists, and drops `None` values so no `temperature` is sent. Compatible by reading; not run. | Verified by source |
| Nothing depends on `langgraph-checkpoint-mongodb` | The spine has no `interrupt`, no checkpointer and no `thread_id`. AD-4: "there is no workflow engine state for review". AD-12: "Human review is not a graph node". | Verified |

One caution on the last row: `dxp-langgraph-langsmith` and `dxp-atlas-agent-memory` still present `MongoDBSaver` and `interrupt()` as the way to build FR-15 and FR-16. An agent that loads either skill may build it. See R9.

## 2. Mechanisms

### a. AD-12: one LangGraph run, `Send` fan-out over about 450 items, one Modal container

**The spine claims:** an ingest job is one graph run in one container, fanning out with `Send`.

| Claim | Evidence | Verdict |
| --- | --- | --- |
| LangGraph bounds fan-out concurrency | `max_concurrency` is a top-level config key: https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow . The page does not say what it bounds. The 1.2.21 source does: `pregel/_executor.py` gates every task behind `asyncio.Semaphore(max_concurrency)` under `ainvoke`, and passes it as the thread-pool size under `invoke`. `_internal/_config.py`: "The max number of concurrent steps to run, which also applies to parallelized steps." | Verified |
| Modal timeout | Default 300 seconds, settable from 1 second to 24 hours, counted per attempt: https://modal.com/docs/guide/timeouts | Verified |
| About 450 items at 16 concurrent fits | Estimate below. It fits the 24-hour maximum and does not fit the 300-second default. | Risky: R1 |

**Estimate.** The Baseline job is 443 items (293 trials plus 150 abstracts, confirmed in `data/README.md`). Each item makes a triage call (about 4 seconds on Haiku), an extraction call (10 to 20 seconds on Sonnet, per `dxp-claude-api`) and a checking call (AD-11 puts checking on Sonnet; no skill measured it; assumed 5 to 15 seconds). That is 19 to 41 seconds of model time per item, so 443 items at 16 in flight take about 9 to 19 minutes, more with retries. Output is about 1.3 million tokens across the run, at most about 150,000 a minute, under the Start tier's 400,000. The Live job (64 items) takes about 2 minutes.

Two further facts. Modal restarts a preempted function "on the same input" (https://modal.com/docs/guide/preemption), so the whole job runs again from the first item. And the docs state no limit on the number of `Send` objects; no skill ran a fan-out of this size (the skill's sizing is marked "estimate, not measured").

**R1. Paste into AD-12, end of Rule:**

> The job function is declared with `timeout=3600`: Modal's default is 300 seconds and the Baseline job needs 10 to 20 minutes. The graph is run with `ainvoke` and `{"max_concurrency": 16}`. Each item node first looks for its Source item with a finished status under the same `run_id` and skips it, so a restart after preemption repeats no model call. Run 50 items before the full Baseline job.

### b. AD-10: long-poll over a change stream, cursor is `seq`

**The spine claims:** `GET /api/v1/changes?after=<seq>` holds a change stream on `events` for at most 25 seconds and falls back to a query on `seq`.

| Claim | Evidence | Verdict |
| --- | --- | --- |
| Change streams work with PyMongo's async API on Flex and M10 | Change streams need a replica set: https://www.mongodb.com/docs/manual/changeStreams/ . Flex's only limit is on database-name filters: https://www.mongodb.com/docs/atlas/reference/flex-limitations/ . `AsyncCollection.watch()` and `try_next()` exist in 4.19.0: https://pymongo.readthedocs.io/en/4.19.0/api/pymongo/asynchronous/collection.html | Verified |
| A stream can start after a known point | `resume_after` and `start_after` take a resume token; `start_at_operation_time` takes a timestamp. The oplog must still hold that point. Same pages. | Verified |
| A 25-second request is within Modal's limit | Web requests are capped at 150 seconds: https://modal.com/docs/guide/webhook-timeouts | Verified |
| `seq` as the cursor over a stream that resumes by token | See below. | Risky: R2 |

**Is the mismatch a real problem? Yes, in two ways.**

1. *Gap between polls.* A change stream opened by a request starts at "now". An event written after the previous response and before this stream opens is never delivered, because the client holds a `seq`, not a resume token, and `seq` cannot be passed to `watch()`. As written, the `seq` query runs only when the stream fails.
2. *Order of `seq`.* The spine does not say how `seq` is assigned. With a counter and a separate insert, 16 concurrent tasks can make event 11 visible before event 10. A client that has moved its cursor to 11 never sees 10.

**Simplest correct design.** Make the `seq` query the only source of what is returned, and treat any stream as a wake-up signal. Make `seq` order safe with the mechanism AD-3 already uses.

**R2. Paste into AD-10, replacing the last sentence of Rule:**

> `events._id` is the integer `seq`. `store.emit_event()` reads the highest `seq`, inserts `seq + 1` and retries on `DuplicateKeyError`, so no event becomes visible before one with a lower `seq`. The live feed is `GET /api/v1/changes?after=<seq>`. It returns `find({_id: {$gt: after}})` at once if that finds anything. Otherwise it waits at most 25 seconds and runs the same query again before answering. The `seq` query is the only source of the response. The wait is a re-query every second. A change stream on `events`, opened before the first query, may replace the sleep as a wake-up signal; it is never the source of the events returned.

A note on cost if the stream is kept: one stream per held request holds one connection per open browser tab. `dxp-mongodb-atlas` recommends the opposite shape, one consumer per process.

### c. AD-11: structured output, no sampling parameters, one semaphore of 16

| Claim | Evidence | Verdict |
| --- | --- | --- |
| JSON-schema structured output with Pydantic on both models | `client.messages.parse(output_format=Model)` sends the schema as `output_config.format`; both model IDs are in the supported list: https://platform.claude.com/docs/en/build-with-claude/structured-outputs . `messages.parse` is in the 2.8.0 source. Through LangChain: `with_structured_output(Model, method="json_schema")`, needing `langchain-anthropic>=1.1.0`: https://docs.langchain.com/oss/python/integrations/chat/anthropic . The default method is still `function_calling` (1.7.10 source), so `method="json_schema"` must always be passed. | Verified |
| No sampling parameters | SDK 2.8.0's `create` has no `temperature`, `top_p` or `top_k` argument (source). The LangChain page: non-default values are "rejected (400)". | Verified |
| 16 is consistent with the Start tier | Start tier, Haiku 5.5 and Sonnet 5.5 each: 4,000 requests, 2,000,000 input tokens and 400,000 output tokens a minute: https://platform.claude.com/docs/en/api/rate-limits . 16 in flight is 48 to 96 calls a minute, about 100,000 to 190,000 output tokens. | Verified for one process |
| The semaphore prevents separate code paths exceeding the limit together | It cannot. See below. | Risky: R3 |

**Why R3.** Limits are per organisation. The semaphore is per process. The API container, each ingest job container, and each developer's `modal serve` are separate processes on one key. Two jobs at 16 each reach about 380,000 output tokens a minute, at the Start tier limit. The same page warns that a sharp increase returns 429 even under the limits (ramp limits), and that a new organisation may start in an Evaluation tier with lower, unpublished limits. `dxp-claude-api` says the tier "is not yet confirmed".

Two smaller points. An `asyncio.Semaphore` and an `AsyncMongoClient` each belong to one event loop, so every node must be `async` and the graph run with `ainvoke`; the skills' examples are synchronous. And AD-11 does not say which client library `llm` uses. Both work, but they differ: `ChatAnthropic` puts each model call in the LangSmith trace; the direct SDK exposes headers, error codes and cache usage (`dxp-claude-api` recommends it for the batch passes), and `langsmith` 0.14.17's `wrap_anthropic` patches `messages.create`, `messages.stream`, `beta.messages.create` and `beta.messages.parse`, not `messages.parse`.

**R3. Paste into AD-11, end of Rule:**

> The semaphore bounds one process. Across processes the limit is kept by rule: `POST /api/v1/jobs` refuses a second ingest job while one is `running`; the API process uses a limit of 4; developers set `DXP_LLM_CONCURRENCY=4` everywhere except the production deploy. 16 assumes the Start tier; read the tier at platform.claude.com/usage/limits before the Baseline job. `llm` uses one client library, the `anthropic` SDK (`AsyncAnthropic().messages.parse`), so the LangSmith trace shows node runs, not model calls. All graph nodes are `async` and the graph is run with `ainvoke`.

If model calls must appear in the trace on camera, swap the library named in that text for `ChatAnthropic(...).with_structured_output(Model, method="json_schema")`. Do not use both.

### d. AD-8: Agent Memory behind an adapter

| Claim | Evidence | Verdict |
| --- | --- | --- |
| The SDK calls exist | `bind`, `save_episode`, `list_episodes`, `save_procedure`, `discover_procedures`, `get_procedure`, `save_semantic`, `save_taxonomic`, `get_taxonomic_term`, `build_context`: https://www.mongodb.com/docs/agentengine/sdk/python/packages/agent-engine-sdk-memory/docs/api/memory/ and the 0.11.14 wheel. | Verified |
| Memory user ID can be the Team ID | `MemoryRequestContext(user_id=...)`; a service account may name any user (`references/api-signatures.md`). The limit to letters, digits, `_` and `-` comes from the skill only; the API page gives none. `team_` IDs pass either way. | Verified |
| Direct writes for episodes and procedures | Both are direct `save_*` calls. Two conditions the spine omits: `save_episode` raises `MemoryIdentityError` without both `user_id` and `session_id`, and `save_procedure` is create-only over HTTP (`update_existing=True` raises `MemoryNotSupportedError`; a second save under one name is UNVERIFIED in the skill). | Risky: R4 |
| A plain-collections backend can honour the same interface | `references/plain-collections-fallback.md` implements the same behaviours with `pymongo` only, on any tier. The spine's four functions map onto it: `remember_episode` to an insert, `recall` to a query by Team and recency, `save_rule` to nothing (`rules` is already the source of truth), `glossary` to a read of `terms`. Recall is by key and recency, not by meaning. | Verified |
| "Flex at minimum" for the cluster | The hosted guide: "Your cluster is tier `M10` or larger. Free and shared tiers are not supported": https://www.mongodb.com/docs/agentengine/add-features/memory-only/ . It also requires a database user with `readWriteAnyDatabase`. | Contradicted for the `agent_engine` backend: R5 |

The function names differ: the skill's fallback exports `end_session`, `resume`, `confirm_rule`, `rules_for`, `seed_terms`, `resolve_term`. The spine's names win, but the skill's code will not drop in unchanged.

**R4. Paste into AD-8, end of Rule:**

> `remember_episode` takes a Team ID and a session ID; the SDK refuses an episode without both, so the web app creates a session ID for each browser session. `save_rule` copies a rule to memory once, on its first activation, under the rule's ID. Later status changes stay in `rules` only. SDK calls are synchronous and run through `asyncio.to_thread`.

R5 is fixed in the deployment text under g.

### e. AD-3: alias insert as a creation lock

| Claim | Evidence | Verdict |
| --- | --- | --- |
| The exception | `pymongo.errors.DuplicateKeyError`, a subclass of `WriteError` (4.19.0 source). The async `insert_one` raises the same class. In a bulk write it arrives as `BulkWriteError` instead. | Verified |
| Safe under concurrent tasks and Modal retries | Uniqueness of `_id` is enforced by the server, so it holds across tasks, containers and retries. Two gaps remain. | Risky: R6 |

**The gaps.** (1) Between the alias insert and the Diagnostic insert, another task can read the alias and be sent to a Diagnostic that does not exist yet; a crash at that point leaves the alias pointing at nothing for every later run. (2) AD-3 gives derived IDs to Source items, Findings and Proposed changes, but not to events or Alerts. Modal re-runs inputs after a crash ("container crashes will be retried": https://modal.com/docs/guide/retries), so a retried apply can emit a second event and raise a second Alert on camera.

**R6. Paste into AD-3, as two further bullets:**

> - The alias document carries `diagnostic_id`, which is `dx_` + hash(normalised name of its first alias) and is known before the insert. Every caller, whether its insert succeeded or raised `pymongo.errors.DuplicateKeyError`, then upserts the Diagnostic on that `_id` with `$setOnInsert`, so an alias never points at a missing Diagnostic. Aliases are written with `insert_one`, never in a bulk write.
> - `ledger.apply()` does nothing for a Proposed change that is already `applied`. `events` has a unique index on `(type, ref)` and an Alert's ID is `alert_` + hash(event `ref`, Team ID), so a retry adds no second event or Alert.

### f. AD-6 and AD-2: Vector Search with Automated Embedding

| Claim | Evidence | Verdict |
| --- | --- | --- |
| Available on Flex and M10 | The rate limit table groups "M0 clusters with payment method, Flex clusters, and Dedicated clusters": https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/models/ | Verified |
| Still a Preview | Banner, fetched today: "Automated Embeddings is available as a Preview feature... Do not use this feature in your production environment": https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/ | Verified, accepted for a demo |
| The limit of three queries a minute | Applies only to "M0 clusters without a payment method". Flex and dedicated get 2,000 requests a minute, shared by the whole cluster. | Verified: no problem on the tiers named |
| A derived text field on `diagnostics` | The spine never names it. See below. | Risky: R7 |

**Why R7.** The spine's diagram shows Vector Search and Search synonyms, but no decision says which field is embedded or who writes it. It matters because the AD-2 shape cannot be indexed directly: every value sits in an array of entries, and an `autoEmbed` path inside an array of documents needs `nestedRoot` on Atlas and is unsupported in the self-managed text (https://www.mongodb.com/docs/vector-search/indexes/vector-search-type/). Indexing the entries would also embed superseded and rejected values, and values AD-6 hides. AD-1 lets only the ledger write a Diagnostic and the layer table lets `search` write nothing, so the ledger must own the derived fields. `dxp-mongodb-atlas` indexes a stored `early_research` filter field, which AD-5 says is never stored.

Three limits to carry with it: on M10, Automated Embedding requires storage auto-scaling (same page as the banner); on Flex the cluster allows "10 indexes" in total (vector-search-type page), shared by the production and both developer databases; the docs give two query shapes, `query: "..."` and `query: {text: "..."}` (the skill says try the object, then the string).

**R7. Paste into AD-6, end of Rule:**

> `ledger.apply()` also rewrites two derived parts of the Diagnostic: `search_text` (one string) and `facets.<key>` (arrays of plain strings), built only from entries that are `current` and have `check.quote_found: true`. These are the only paths in the vector index (`autoEmbed` on `search_text`, `filter` on `facets.*`) and in the search index. Early research is filtered as `facets.lifecycle_stage` in `[discovery, assay_development]`. A search returns IDs and scores; the Record data still comes from `search.readmodel` by `find`, because embedding is asynchronous.

### g. Deployment table

| Claim | Evidence | Verdict |
| --- | --- | --- |
| `modal serve` with a per-developer suffix | `dev_suffix` / `MODAL_DEV_SUFFIX`: "Overrides the default `-dev` suffix added to URLs generated for Web Functions"; a short alphanumeric string: https://modal.com/docs/reference/modal.config and `modal/config.py` in 1.6.4. Without it a second `modal serve` "will *steal* the running Function's label": https://modal.com/docs/guide/webhook-urls | Verified |
| `modal deploy` for production | "The App is persisted indefinitely until you stop it": https://modal.com/docs/guide/apps | Verified |
| The scheduled scan runs only when deployed | "To activate the schedule, deploy your App": https://modal.com/docs/guide/cron . The page says nothing about `modal serve`. | Verified |
| Atlas open to any address because Modal has no fixed address | "Proxies are available on the Team and Enterprise plans" (Beta): https://modal.com/docs/guide/proxy-ips | Verified for Modal; R5 for the conflict below |

**R5, two documents against the deployment paragraph.** First, Agent Memory needs M10, so "Flex at minimum" holds only with the `collections` backend. Second, the Agent Memory guide, on the IP access list of the same cluster: "Do not add `0.0.0.0/0` to the IP access list." It does not say what happens if the entry is there. Atlas supports temporary entries "that expire within a user-configurable 7-day period" (https://www.mongodb.com/docs/atlas/security/ip-access-list/).

**R8, two things the table leaves unsaid.** (1) Each developer has their own `DXP_DB`, but the Modal secret `dxp-secrets` is shared by the workspace, so it cannot hold a per-developer value. `modal.Secret.from_dict` exists in 1.6.4. (2) A `modal serve` app is ephemeral: it stops "when the calling program exits", and the docs do not say what a live reload does to a function that is running. A Baseline job started under `modal serve` can die when a file is saved or a laptop sleeps. `modal run --detach` keeps an ephemeral app alive (apps page).

**R5 and R8. Paste in place of the paragraph under the environment table:**

> One Atlas cluster. It is M10 if Agent Memory is used, which does not run on Flex or Free and needs a database user with `readWriteAnyDatabase`; with `DXP_MEMORY_BACKEND=collections`, Flex is enough. On M10 switch on storage auto-scaling, which Automated Embedding requires. On Flex the cluster allows 10 search and vector indexes in total, shared by all databases. Network access `[ASSUMPTION]`: `0.0.0.0/0` as a temporary entry that expires after the event, plus the two Agent Engine addresses, protected by a strong database password. The Agent Engine guide says not to add `0.0.0.0/0`: confirm on Friday that memory reaches `ready` with it present, and use the `collections` backend if it does not. `DXP_DB` reaches the container through `modal.Secret.from_dict({"DXP_DB": os.environ["DXP_DB"]})`, evaluated on the machine that runs `modal serve` or `modal deploy`; the person who deploys sets `DXP_DB=dxp`. A job started under `modal serve` stops with that terminal, so run the Baseline job from the deployed app or with `modal run --detach`. No login: the web app has a Team switcher. The scheduled scan runs only in the deployed app.

## 3. Where the spine and the skills disagree

The spine says how to use each technology "is in the `dxp-*` skills, not here". The skills' examples were written before the spine and differ from it. An agent that copies them will build the wrong thing.

| Topic | Skills | Spine |
| --- | --- | --- |
| Database name variable | `MONGODB_DB` (`dxp-mongodb-atlas`, `dxp-modal`, `dxp-langgraph-langsmith`); the memory fallback hard-codes `"dxp"` | `DXP_DB` |
| Collections | `proposed_changes`, `learned_rules`, `team_profiles`, `batch_runs`, `graph_nodes`, `graph_links`; unique `match_key` on `diagnostics` | `proposals`, `rules`, `teams`, `jobs`, `edges`; `aliases` |
| Record shape | `fields.x` with `history`, `lists.trials` | `fields.<key>` as a list of value entries (AD-2) |
| IDs | `ObjectId` references | strings only |
| Batch shape | Modal `.starmap` over `process_item` (`dxp-modal`) | one run with `Send` (AD-12) |
| Review | `interrupt()` with `MongoDBSaver` | a query on `proposals` (AD-4) |
| Update triggers | `alert_topics` vector index (`dxp-mongodb-atlas`) | enum set by the extraction model (AD-10) |
| Live updates | server-sent events (`dxp-vercel-frontend`), polling (`dxp-modal`) | long-poll (AD-10) |
| Config not in the spine's list | `AGENTIC_MEMORY_PROJECT_ID`, `AGENTENGINE_SA_CLIENT_ID`, `AGENTENGINE_SA_CLIENT_SECRET`, `ELEVENLABS_VOICE_ID`, `FRONTEND_ORIGIN` | absent |

**R9. Paste under the opening paragraph of the spine:**

> Where a `dxp-*` skill's example differs from this spine in a collection name, field shape, ID type, environment variable or mechanism, the spine wins. In particular: `DXP_DB`, not `MONGODB_DB`; review is a query on `proposals`, not `interrupt()` with `MongoDBSaver`; the batch is one `Send` run, not Modal `.starmap`; update triggers come from the extraction model, not an `alert_topics` index.

And add to the Config row: `AGENTIC_MEMORY_PROJECT_ID`, `AGENTENGINE_SA_CLIENT_ID`, `AGENTENGINE_SA_CLIENT_SECRET`, `ELEVENLABS_VOICE_ID`, `FRONTEND_ORIGIN`, `DXP_LLM_CONCURRENCY`.

## 4. Asserted from general knowledge

These are in the spine, covered by no skill and settled by no document. None is known to be wrong; each is a design call that nobody has tested.

- **AD-2, one `current` entry per `single` field.** With 16 tasks applying to one Diagnostic, two can read the same `current` entry and both add a successor. No mechanism is named. A single conditional `update_one` per apply, guarded by a revision counter and retried on no match, would hold it.
- **AD-5, "only when that stage is later than the current one".** The same check-then-write race.
- **AD-4, "a Diagnostic created in this job".** Not said how it is known. A `created_run_id` on the Diagnostic survives a Modal retry, because the retry carries the same job ID.
- **AD-7, `rules.evaluate` over all `pending` Proposed changes when a rule becomes active.** `dxp-atlas-agent-memory` describes rule checking as a model call. Many pending changes would then exceed AD-9's 20 seconds inside the activating request, so it should be a job. Not stated.
- **AD-9, the 20-second threshold.** Modal's limit is 150 seconds. Query parsing on Sonnet 5.5 runs inside a request with thinking on (it cannot be disabled, per `dxp-claude-api`); its latency is unmeasured.
- **AD-10, Team matching** on modality, biomarker or linked drug. Already tagged `[ASSUMPTION]`.
- **AD-3, the `approach:<modality>:<biomarker or any>` alias.** Already tagged `[ASSUMPTION]`.
- **AD-13, `edges` rewritten on every apply.** No skill sizes it. The `{ nodes, links }` shape does match what react-force-graph takes.
- **Hash-derived IDs.** Neither the hash nor value normalisation is specified.
- **Saturday data reaching the container.** The counts are right (293, 40 and 24 in `data/README.md`; 76 lung rows in `data/fda/cdx_lung.jsonl`, grouped into 20 assays in `assays.json`). But PubMed text is excluded from the repository, and the spine does not say how `data/` gets into the Modal image or onto the second developer's machine.
- **"Protected by a strong database password."** A judgement about an open network rule, not a verified control.

## 5. Unverifiable

1. Whether Agent Memory reaches `ready` with `0.0.0.0/0` on the access list. The guide forbids the entry without saying what happens.
2. The organisation's Claude usage tier. Only the Console shows it.
3. What `modal serve` does to a running function on live reload, and whether a schedule fires under it. Undocumented.
4. A fan-out of 443 `Send` objects in one step. No limit is documented and no skill ran one.
5. `langchain-anthropic` 1.7.10 with `anthropic` 2.8.0 at run time. They resolve and the source matches; nothing was run.
6. The `$vectorSearch` query shape for Automated Embedding. The official pages give two.
7. What a second `save_procedure` under an existing name does over HTTP.
8. The MongoDB version an M10 offers or defaults to today.
9. How long the Sonnet checking call takes. The 9 to 19 minute estimate assumes 5 to 15 seconds.

## Findings index

| ID | Where | Problem |
| --- | --- | --- |
| R1 | AD-12 | No timeout stated; restart repeats all model calls |
| R2 | AD-10 | Events missed between polls; `seq` order not guaranteed |
| R3 | AD-11 | Semaphore is per process; tier unconfirmed; client library not chosen |
| R4 | AD-8 | Episode needs a session ID; procedures are create-only |
| R5 | AD-8, deployment | Agent Memory needs M10; its guide forbids `0.0.0.0/0` |
| R6 | AD-3 | Alias can point at a missing Diagnostic; events and Alerts duplicate on retry |
| R7 | AD-6, AD-2 | Derived search fields and their writer are not in the spine |
| R8 | Deployment | No way stated for per-developer `DXP_DB`; long jobs die under `modal serve` |
| R9 | Whole spine | Skills' examples contradict the spine; precedence not stated |
