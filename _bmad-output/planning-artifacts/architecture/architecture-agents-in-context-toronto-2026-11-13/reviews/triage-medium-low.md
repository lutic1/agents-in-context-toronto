---
title: "Triage of medium and low findings, hackathon lens"
created: 2026-11-13
target: ../ARCHITECTURE-SPINE.md (current text, rewritten after the reviews)
inputs: review-adversarial.md (SPN-11 to SPN-30), review-rubric.md (RUB medium and low), reconcile-inputs.md (REC medium and low), review-reality-check.md (section 5, unverifiable)
---

# Triage of medium and low findings

Lens: a one-day build by two developers, about six hours of coding, a three-minute video at 18:00. APPLY only if the finding can plausibly break Saturday and the fix is one or two spine sentences and at most about fifteen minutes of build work. Every finding was judged against the current spine, not the text the review quotes.

**Counts:** 47 FIXED, 5 APPLY, 12 DROP (64 items).

## 1. Classification

### Adversarial review (SPN)

| ID | Class | Reason, or the spine line that closes it |
| --- | --- | --- |
| SPN-11 | FIXED | AD-7: "Only `rules` writes `check.flags`, and only on `pending` Proposed changes ... Setting a rule `off` removes its flags." Diagram has `pipeline --> rules`, `api --> rules`. |
| SPN-12 | FIXED | AD-6: "A hand-typed value has `evidence.manual` and `review: manual`, and is shown marked as manually sourced." Read model shows entries "that passed or are `manual`". The leftover (which `finding_id` a manual value uses) is backend-internal. |
| SPN-13 | FIXED | AD-10: "assigned by inserting and retrying on a duplicate key ... The query on `seq` is the only source of truth." AD-8 and AD-14: `last_seen_seq`, `POST /teams/<team_id>/seen`. |
| SPN-14 | FIXED | AD-3: "uses the alias `approach:<modality>:<biomarker>`, with registry values, taking the first biomarker in alphabetical order or `any`." Provider overwrite closed by AD-2's last bullet. |
| SPN-15 | FIXED | AD-3: "Writes of Findings and Proposed changes are insert-if-absent (`$setOnInsert`)." AD-16: `processed_at`. |
| SPN-16 | FIXED | AD-4: "A Reviewer accepts, edits or rejects an `unreviewed` value through `ledger.review_value()`"; route `POST /diagnostics/<dx_id>/values/<value_id>/review`. |
| SPN-17 | FIXED | AD-11: "An ingest job may hold 16 calls at once; all other callers share 4." AD-16: "At most one ingest job runs at a time." |
| SPN-18 | FIXED | AD-13: "`{ _id: derive("e_", from, to, kind), ... }`, upserted by `ledger.apply()`"; `Link { source, target, kind, changed }`. |
| SPN-19 | FIXED | AD-10: "The ledger sets `stage_advance` when it applies a `lifecycle_stage` change. The extraction model sets the other three." |
| SPN-20 | FIXED | AD-1: "A Proposed change whose canonical value equals a `current` entry of that field is not filed." |
| SPN-21 | FIXED | AD-1: every value, including "seed values", enters through `ledger.file`; `provider` is a registry field in AD-2. |
| SPN-22 | FIXED | AD-8 gives the four signatures; "Rule copies use `<DXP_DB>:reviewers`." |
| SPN-23 | FIXED | AD-9: "Anything that can run longer than 30 seconds is a job ... The one long request is the 25-second long-poll in AD-10." |
| SPN-24 | FIXED | Diagram now has `api --> foundation`, `pipeline --> memory`; AD-5: "`registry.is_early_research(stage)` is the only test"; AD-10: "`store.emit_event()` is the only writer of `events`". |
| SPN-25 | **APPLY** | AD-16 still says the job "is started by name with `spawn`". Modal documents `Function.from_name` as looking up "a Function from a deployed App" (https://modal.com/docs/reference/modal.Function; `dxp-modal`: "works only against a deployed App, never against `modal serve`"). A developer's `modal serve` API would fail, or start the production job against `DXP_DB=dxp`. Line 73 also contradicts the `modal --> api` arrow. |
| SPN-26 | FIXED | AD-14 route table: "`GET /alerts/<alert_id>/audio` | audio, the one non-JSON response". |
| SPN-27 | FIXED | AD-2: "the low-confidence threshold live only in `backend/dxp/schema/registry.py`. The web app reads them from `GET /api/v1/schema`." |
| SPN-28 | FIXED | AD-1: `ledger.file(finding_id, changes, mode)`; sequence: "file(finding, changes with evidence and check, mode)". |
| SPN-29 | FIXED | AD-3: "The `raw_text` of a Source item that has Evidence pointing at it is never overwritten." Deferred: "Versions of a Source item". |
| SPN-30 | FIXED | AD-14: "`GET /digest?team_id=` | `{ pending: Proposal[], alerts: Alert[] }`". Export is Deferred. |

### Rubric review (RUB)

| ID | Class | Reason, or the spine line that closes it |
| --- | --- | --- |
| RUB-02 | FIXED | AD-6 manual line (see SPN-12). The check on an edited value is a nicety: drop the remainder. |
| RUB-03 | FIXED | AD-14 route table and the `Record`, `Job`, `Node`, `Link` shapes. |
| RUB-04 | FIXED | AD-14: "Every changing request carries `actor`"; `POST /teams/<team_id>/seen { seq }`. |
| RUB-05 | **APPLY** | AD-8 writes unmatched terms into `terms`, and the capability table makes `terms` the source of the Search synonym mapping. MongoDB Search "doesn't create indexes if the indexes use synonym mappings that reference collections with invalid documents" (https://www.mongodb.com/docs/atlas/atlas-search/synonyms/). One unmatched-term document without `mappingType` and `synonyms` breaks the search index on camera. |
| RUB-06 | FIXED | AD-10 first-Alert and update-Alert rules; AD-3: "Alert ID: `derive("alert_", team_id, diagnostic_id, kind, cause)`". |
| RUB-07 | FIXED | AD-15: "The Vector Search index with Automated Embedding is on `search_text` only. `search.query` filters on `facets` and ranks on `search_text`." |
| RUB-10 | FIXED | AD-6: "A value passes when `quote_found` and `supported` are both true. A value that does not pass is recorded on its Finding and goes no further." |
| RUB-11 | FIXED | AD-2: "a `single` field that already has a `current` entry is not superseded: the new value stays `pending` for a Reviewer." |
| RUB-12 | FIXED | AD-3: alphabetical first biomarker; `ledger.ensure_diagnostic()`; "The file's own `assay_normalised` is not used as a key." |
| RUB-13 | FIXED | AD-7: `{ field, text, status: draft \| active \| off, from_proposal_id, synthetic }`; "Setting a rule `off` removes its flags." |
| RUB-14 | FIXED | AD-4: `ledger.review_value()`. |
| RUB-15 | FIXED | AD-5: "`registry.is_early_research(stage)` is the only test for the label". |
| RUB-16 | FIXED | AD-14: `GET /digest` returns pending Proposed changes and Alerts. |
| RUB-17 | FIXED | AD-11: "through `langchain-anthropic` and nothing else"; the Anthropic SDK row is gone from Stack. |
| RUB-18 | DROP | Bookkeeping in the Binds lines and the map; nothing diverges. |
| RUB-19 | **APPLY** | Operations table has no retake path. After the on-camera live job, `processed_at` is set and Alerts exist, so a second take does nothing. A failed take near 18:00 with no reset path eats the end of the day. |
| RUB-20 | DROP | Shared-key rate limits across developer databases: the Operations row "Rate-limit errors: lower the ingest limit in `llm`" covers it. Cost is Deferred. |
| RUB-21 | FIXED | AD-14: "`POST /jobs` and every route that calls a model require the header `X-DxP-Key`". Enterprise concern in any case; see Simplifications. |
| RUB-22 | FIXED | AD-8: "The memory user ID is `<DXP_DB>:<team_id>`." |
| RUB-23 | DROP | The spine defers variable names to the skills ("The skills name the variables each service needs"). Lower-case keys in the local `.env` show up as an auth error in the first minute: a Friday setup item, not a rule. |
| RUB-24 | FIXED | Environment table: "`DXP_DB` passed with `modal.Secret.from_dict`"; "M10 is required for the `agent_engine` memory backend; Flex is enough for `collections`." Developer indexes: Operations "run `store.ensure_indexes()`". |
| RUB-25 | FIXED | Conventions "Accessibility" row. See Simplifications: cut it. |
| RUB-26 | FIXED | The arrows `api --> rules`, `api --> foundation`, `pipeline --> rules` and `pipeline --> memory` are drawn. Part (g) and the "Nothing imports `api`" sentence are handled by the SPN-25 APPLY. |
| RUB-27 | DROP | Small diagram mismatches (the sequence diagram's post-`alt` step, the entity links). Agents build from the AD text. |
| RUB-28 | DROP | Wording cuts (`[ADOPTED]` tag, Agent SDK line, stale counts). Harmless. |

### Reconciliation (REC)

| ID | Class | Reason, or the spine line that closes it |
| --- | --- | --- |
| REC-03 | FIXED | Section "MongoDB capabilities, for the video", with fallback wording. |
| REC-04 | **APPLY** | AD-8 says "Text recalled from a synthetic episode is labelled synthetic", but `remember_episode(team_id, session_id, kind, text)` has no synthetic argument and `recall` returns `list[str]`. The seeder and the adapter can be built by different people, and an unlabelled synthetic history would then appear in the resume on camera, against PRD §8. |
| REC-05 | FIXED | Deferred: "Lifecycle stage per clinical use, and its accuracy ... Stage labels can be added to the Gold set." |
| REC-06 | FIXED | Deferred: "Versions of a Source item"; AD-3 forbids overwriting `raw_text`. |
| REC-07 | FIXED | Conventions "Attribution": footer credits line; "Every Evidence shows its source and that source's data date." `Value` carries `evidence.data_as_of`. |
| REC-08 | FIXED | AD-16: "Membership comes from the manifest ID lists, never from a date comparison." |
| REC-09 | FIXED | AD-6: PubMed `raw_text` is never "written to a file in the repository ... A quote is at most 300 characters." Deferred Gold set: "never PubMed text". |
| REC-10 | DROP | Distinguishing "withheld" from "no data" is a nicety. |
| REC-11 | FIXED | AD-2 evidence: `{ source_ref, source, source_url, source_date, quote }`. |
| REC-12 | **APPLY** | Event rule. `scripts/data/dxp_sources.py` (and the `dxp-*` skills it was copied from) are pre-made work. `data/README.md` says "Nothing here is product code". Agents will copy `quote_in_source` and the fetchers into `backend/`, so the disclosure becomes untrue unless someone is told to update it. |

### Reality check, unverifiable items

| # | Item | Class | Reason |
| --- | --- | --- | --- |
| U1 | Agent Memory `ready` with `0.0.0.0/0` | FIXED | "Agent Memory check, Friday ... If either step fails with the open entry present, set `DXP_MEMORY_BACKEND=collections` and move on." |
| U2 | Claude usage tier | DROP | No spine change. Friday test below. |
| U3 | `modal serve` reload and schedules | FIXED | "The Baseline job runs in the deployed app or with `modal run --detach`, never under `modal serve`. The scheduled scan runs only when deployed." |
| U4 | 443 `Send` targets in one step | DROP | No documented limit (section 4). Friday test below. |
| U5 | `langchain-anthropic` 1.7.10 with `anthropic` 2.8.0 | DROP | Declared range admits it (section 4). Friday test below. |
| U6 | `$vectorSearch` query shape | DROP | The reference settles it as an object; the skill already says to try the object first. Friday test below. |
| U7 | Second `save_procedure` under one name | FIXED | AD-7: "Agent Memory receives one copy when a rule first becomes `active`." |
| U8 | MongoDB version on M10 | DROP | Choose 8.0 or later when creating the cluster. Friday test below. |
| U9 | Sonnet checking-call latency | DROP | The 50-item Friday run measures it. |

## 2. APPLY texts

**SPN-25.** In AD-16, replace "It is started by name with `spawn`, never called inside a request." with:

> `modal_app.py` passes the job function to `api.create_app()`, and the API starts it with `.spawn()` on that object, never with `modal.Function.from_name`, so a `modal serve` API starts its own job and never production's. It is never called inside a request.

On line 73, replace "Nothing imports `api` or `modal_app`." with:

> Only `modal_app` imports `api`; nothing imports `modal_app`.

**RUB-05.** In AD-8, append to the "Synonyms are owned by `search.terms`" bullet:

> Every `terms` document is a valid synonym document, `{ mappingType: "equivalent", synonyms: [...] }` plus DxP's own fields; an unmatched term is stored as `synonyms: [<term>]`. One invalid document stops the MongoDB Search index from building.

**RUB-19.** Add a row to "Operations on the day":

> | Retake the live demo | Straight after the Baseline jobs, `mongodump` database `dxp` to a folder outside the repository. To retake, `delete_many({})` every collection (dropping would delete the search indexes) and `mongorestore` that dump. |

**REC-04.** In AD-8, after "Text recalled from a synthetic episode is labelled synthetic.", add:

> Synthetic episodes are written with a `session_id` that starts `synthetic_`, and `recall` prefixes their text with `[synthetic] `.

**REC-12.** On line 73, after "The backend imports nothing from `scripts/`.", add:

> Code copied into `backend/` from `scripts/data/` or from a `dxp-*` skill is pre-made work and is listed in the README disclosure.

## 3. Simplifications

MongoDB judges matter: change streams, `$graphLookup`, Vector Search with Automated Embedding, synonym mappings and Agent Memory are named on camera. No cut below removes one of them.

| Item | Verdict | Replacement text |
| --- | --- | --- |
| `X-DxP-Key`, sent from server-side code only (AD-14) | **Simplify** | Server-side-only sending forces a Next.js proxy route for `/jobs`, `/query`, `/proposals/.../decision` (rule drafting) and audio. That is a second request path for one day's protection. Replace the last sentence of AD-14 with: "`POST /jobs` alone requires the header `X-DxP-Key`. The web app asks for the key once on the jobs page and sends it from the browser; the API's CORS settings allow that header. No other route is protected." |
| Change-stream wake-up in the long-poll (AD-10) | **Simplify** (keep the capability, defer the mechanism) | Keeping a change stream per held request needs `@modal.concurrent` on the API, async stream handling and a timeout loop. The contract does not depend on it. Replace AD-10's third bullet with: "`GET /api/v1/changes?after=<seq>` returns events with a higher `seq` at once, and the web app calls it every 2 seconds. The query on `seq` is the only source of truth. Once that works, the handler may wait up to 25 seconds on a change stream over `events` before answering; the web app works either way." In AD-9, change "The one long request is the 25-second long-poll in AD-10." to "The only request that may wait is `GET /changes` (AD-10)." The capability row "Change streams: wake-up for the live feed" stays, but should be named on camera only if the wait was built. |
| `dedupe_key` on events (AD-10) | **Cut** | The key's value is undefined, so each emitter would invent one. Retries are already idempotent upstream: the claim in AD-1, `$setOnInsert` in AD-3 and `processed_at` in AD-16. Replace "Each event has a unique `dedupe_key`, so a retry emits nothing new." with: "An event is emitted only after a write that changed something (a successful claim or an inserted document), so a retry emits nothing new." |
| Accessibility convention row | **Cut** | It prevents no divergence between the two developers, and native buttons are keyboard-reachable anyway. Delete the row. |
| Web types from `openapi-typescript` (AD-14) | **Keep, with one tweak** | Generation is one command and is the only thing that stops the two sides guessing shapes. The tweak lets the web start before an API is deployed. Replace the second sentence of AD-14 with: "Every route declares `response_model`. `web/lib/types.ts` is generated with `openapi-typescript` from `web/openapi.json`, which the backend writes from `app.openapi()` without a server running, and is never edited by hand. `api/models.py` is written first, in the first half hour." |
| `terms` unmatched queue and `GET /terms` route | **Cut** | Nothing in the demo shows it. Cutting it also removes most of the synonym-validity risk in RUB-05. In AD-8, replace "A term the pipeline cannot match is written to `terms` with `status: unmatched` for the Reviewer." with: "A term the pipeline cannot match is kept as written in the value's `label`; on Saturday it is not queued." Delete the `GET /terms` route row and "unmatched `terms`" from the Ingest filters row of the layer table. Keep the RUB-05 APPLY sentence for curated and seeded terms. |
| Separate limit of 4 for non-ingest calls (AD-11) | **Cut** | The API's calls come from clicks: a few at a time. The 4-slot limit adds a caller-type parameter, and it would slow the rule re-flag sweep (AD-7) on camera. Replace "An ingest job may hold 16 calls at once; all other callers share 4." with: "An ingest job holds at most 16 calls at once. Other callers are not limited." |

Nothing else in the spine looks over-built for the day.

## 4. Online checks

| Item | Status | Evidence |
| --- | --- | --- |
| `langchain-anthropic` 1.7.10 with `anthropic` 2.8.0 | **Settled at declaration level.** `requires_dist`: `anthropic>=0.120.0` (no upper bound), `langchain-core>=1.7.5,<2.0.0`, `pydantic>=2.7.4`. 1.7.10 was uploaded 4 Nov 2026 and `anthropic` 2.8.0 on 10 Nov, so 1.7.10 was never tested against 2.8.0. Run-time behaviour is still open. | https://pypi.org/pypi/langchain-anthropic/1.7.10/json, https://pypi.org/pypi/anthropic/2.8.0/json |
| LangGraph `Send` target limit and `max_concurrency` | **Settled.** No limit on `Send` targets is documented. "Pass `max_concurrency` as a top-level config key (not under `configurable`)", for example `graph.ainvoke(inputs, {"max_concurrency": 16})`. Also documented: if any branch in a superstep raises, "none of that superstep's updates apply to state", so the AD-12 per-item catch is essential. | https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow |
| `$vectorSearch` shape for Automated Embedding | **Settled by the reference:** `"query": { "text": "<query-text>" }`, mutually exclusive with `queryVector`; `model` is optional in the query. The feature overview still shows `"query": "<query-text>"`, so test both. | https://www.mongodb.com/docs/vector-search/query/aggregation-stages/vector-search-stage/ ; overview: https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/ |
| Does `modal serve` run scheduled functions? | **Still open, but moot.** The docs only say "To activate the schedule, deploy your App" and "Functions in a deployed App that have an attached schedule will be run on a schedule". The spine already runs the scan only when deployed. | https://modal.com/docs/guide/cron, https://modal.com/docs/guide/apps |
| MongoDB version on M10 | **Partly settled.** Dedicated clusters offer "7.0, 8.0, 9.0, and Latest Version With Auto Upgrades". The default is not named: the Admin API says the "current recommended default" (a recent LTS), while the CLI says the latest stable. On M10, Automated Embedding requires storage auto-scaling. | https://www.mongodb.com/docs/atlas/manage-clusters/ ; https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/ |
| `Function.from_name` (for SPN-25) | **Settled.** Documented as referencing "a Function from a deployed App by its name". | https://modal.com/docs/reference/modal.Function |
| Synonym source collection validity (for RUB-05) | **Settled.** "MongoDB Search doesn't create indexes if the indexes use synonym mappings that reference collections with invalid documents." Extra fields are allowed. | https://www.mongodb.com/docs/atlas/atlas-search/synonyms/ |

## 5. Five-minute tests for Friday

1. **Claude client.** Inside the Modal image with the pinned packages, call `ChatAnthropic(model=...).with_structured_output(Model, method="json_schema").ainvoke(...)` once on `claude-haiku-5-5` and once on `claude-sonnet-5-5`. Pass means a parsed object comes back. On failure, pin `anthropic` to the newest 1.x or 2.x release before 4 Nov.
2. **Fan-out.** Run the graph with `ainvoke` and `{"max_concurrency": 16}` over 50 Source items. Check that all 50 complete, one forced failure is recorded per AD-12, and the timing gives about two minutes per 50 items.
3. **Vector query.** On one test document, run `$vectorSearch` with `query: {text: "egfr plasma"}`, then with `query: "egfr plasma"`. Keep whichever returns results.
4. **Cluster.** When creating the M10, choose 8.0 or later and confirm storage auto-scaling is on. Then run `db.version()`, and check that the vector index and a synonym-mapped search index both reach READY.
5. **Claude tier.** Read the tier at platform.claude.com/usage/limits.
6. **Job start in development.** Under `modal serve`, `POST /jobs` with 3 items. The `jobs` document must land in the developer's `DXP_DB`, not in `dxp`.
