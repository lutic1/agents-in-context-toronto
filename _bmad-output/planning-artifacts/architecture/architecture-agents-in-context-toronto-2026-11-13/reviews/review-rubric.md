---
title: "Rubric review: ARCHITECTURE-SPINE.md, DxProvida (DxP)"
created: 2026-11-13
target: ../ARCHITECTURE-SPINE.md
part: A (quality checklist)
companion: reconcile-inputs.md (Part B, reconciliation against the inputs)
---

# Rubric review of the architecture spine

Review only. No existing file was changed. Line numbers refer to `ARCHITECTURE-SPINE.md` unless another file is named. Skill paths are under `.claude/skills/`.

**Verdict.** The paradigm, the single writer, the value-entry shape and the Evidence gate are the right invariants and are stated tersely. The spine is not yet safe to build from in parallel: it does not say that it overrides the `dxp-*` skills, which teach different mechanisms for six of its decisions, and two of its rules (AD-3, AD-5 with AD-13) do not hold under the parallel fan-out and re-runs that AD-12 creates.

**Counts.** 0 critical, 3 high, 14 medium, 11 low.

**Severity.**

- **Critical:** built as written, a PRD guardrail is breached or the build cannot hold together.
- **High:** two builders will diverge, or a rule fails to prevent the divergence it names, on a P1 path.
- **Medium:** a real gap with a quick workaround, a P2 path, or a single-builder ambiguity that changes visible behaviour.
- **Low:** wording, bookkeeping, or a line that should be cut.

**What was checked and how.** Every AD was read against the PRD requirement it binds, the layer table, both flowcharts, the sequence diagram and the entity diagram. The four Mermaid blocks were parsed with Mermaid 11.17.2 (`mermaid.parse`). Skill claims were checked in the skill files. Dataset claims were checked in `data/*/manifest.json` and the data files. Versions were not re-verified.

| # | Checklist item | Verdict |
| --- | --- | --- |
| 1 | Fixes the real divergence points, misses none | Partly. Seven gaps: RUB-01 to RUB-07 |
| 2 | Every Rule is enforceable and prevents its divergence | Partly. AD-3 and AD-5 fail under concurrency and re-runs: RUB-08 to RUB-15 |
| 3 | Nothing under Deferred lets two units diverge | Mostly. One line is wrong: RUB-16 |
| 4 | Named technology has a version | Pass, one ambiguity: RUB-17 |
| 5 | Every in-scope FR has a home | 25 of 27 homed; FR-9 is partly homed and FR-29's home is contradicted by AD-6; FR-24 is homed but bound by no AD: table below, RUB-18 |
| 6 | Every dimension decided, deferred or raised | Operations, cost, security and accessibility are silent or thin: RUB-19 to RUB-25 |
| 7 | Diagrams valid and agree with the text | All four parse. The dependency diagram disagrees with AD-7, AD-8 and the layer table: RUB-26, RUB-27 |
| 8 | Terse | Pass, three small cuts: RUB-28 |

---

## 1. Divergence points

### RUB-01 (high). The spine does not say it overrides the skills, and six skill patterns contradict it

**Where:** line 23, "How to use each technology is in the `dxp-*` skills, not here." Frontmatter `sources`, line 16.

**Problem:** Each developer's coding agent loads a skill by trigger and copies its pattern. These patterns differ from the spine:

| Spine | Skill pattern that differs |
| --- | --- |
| AD-4, AD-12: review is a query on `proposals`, not a graph node | `dxp-langgraph-langsmith` pattern 5, "Pause for a Reviewer and resume (FR-16, FR-19)": `interrupt()` with `MongoDBSaver` |
| AD-12: one graph run per job; AD-9: `jobs`, `/api/v1/jobs` | `dxp-modal` "Worker and batch runner": `process_item.starmap` per item, collection `batch_runs`, routes `/batches` and `/scans` |
| AD-10: update triggers set by the extraction model | `dxp-mongodb-atlas` "FR-13": `$vectorSearch` on `alert_topics` with a `topic_vector` index |
| AD-10: long-poll `GET /api/v1/changes?after=<seq>` | `dxp-vercel-frontend` "Live updates": server-sent events with `EventSource` and `useDxpEvents` |
| AD-2, AD-6: a field is a list of value entries with `review` in four states | `dxp-vercel-frontend` "Comparison table": `Cell` holds one `value` and `reviewed: boolean` |
| AD-7, AD-8: `rules`, `teams`, `mem_*`; adapter `remember_episode`, `recall`, `save_rule`, `glossary` | `dxp-atlas-agent-memory` fallback: `learned_rules`, `team_profiles`, `memory_episodes`; functions `end_session`, `resume`, `confirm_rule`, `resolve_term` |

The ElevenLabs skill also offers a Next.js streaming route, which the Deferred line on audio rules out.

**Fix.** Replace the last sentence of line 23 with:

> How to use each technology is in the `dxp-*` skills. Where a skill and this spine disagree, the spine wins. Known differences: review is the `proposals` queue, not LangGraph `interrupt` (AD-4, AD-12); a job is one graph run tracked in `jobs`, not `process_item.starmap` with `batch_runs` (AD-9, AD-12); update triggers come from the extraction model, not the `alert_topics` vector index (AD-10); live updates are the `/changes` long-poll, not server-sent events (AD-10); a table cell follows the read-model shape, not the front-end skill's `Cell` type (AD-2, AD-6); collection and function names for memory, rules and Teams are the ones in AD-7 and AD-8; audio is generated by the Python API, not a Next.js route.

### RUB-02 (medium). The Evidence gate hides hand-typed values and leaves Reviewer edits undefined

**Where:** AD-6, line 117: the read model "drops any value entry whose `check.quote_found` is false". AD-1, line 71: "values a user types by hand" enter through the ledger. AD-2, lines 80 to 84: `evidence: { source_item_id, quote, source_url }`. Map row §4.8, line 334, governs FR-29 by AD-6.

**Problem:** A hand-typed value has no Source item and no quote, so the gate drops it and FR-29's test fails ("a value added by one user is visible to another, with the manual mark"). An edited value (FR-16, P1) keeps a quote that was written for a different value, and nothing says what its `check` is. AD-4's modes cover ingest jobs only, so whether a hand-typed value is applied at once is also open. This is ADV-18, which the PRD did not absorb. Rated medium because FR-29 is P2; it is high if FR-29 stays in Saturday's cut.

**Fix.** Add to AD-6's Rule:

> An entry with `review: manual` carries `evidence: { source_item_id: null, quote: null, source_url, stated_source }`, is exempt from the quote gate, and is always returned with the manual mark, `decided_by` and `decided_at`. A Reviewer edit keeps the original quote only if the edited value passes the check against it; otherwise it is stored as `manual`. A hand-typed value is applied at once.

Add `stated_source` to the `evidence` shape in AD-2.

### RUB-03 (medium). The stored shape is fixed, the wire shape is not

**Where:** AD-2 (line 77) names one endpoint, `GET /api/v1/schema`. AD-6 (line 117) says the read model "adds the no-data state". AD-9 (line 135) says a job "writes progress to `jobs`". AD-13 (line 159) says `GET /api/v1/graph` returns `{ nodes, links }`. Conventions, "Naming" (line 165): "TypeScript types mirror them".

**Problem:** The two developers meet at the API. The spine fixes what is stored and leaves open what is returned: the shape of a table cell and of the no-data state, the progress counters FR-4's test needs (processed, failed, Early research), whether the graph endpoint returns everything or a neighbourhood (ADV-26), and how the TypeScript types are produced. The only cell shape in the repository is the front-end skill's, which disagrees with AD-2 (RUB-01).

**Fix.** Add a Conventions row:

> | API contract | FastAPI's `/openapi.json`, built from the Pydantic models in `schema`, is the contract. `web/lib/api.ts` types are generated from it, never hand-written. A read-model cell is `{ entries: [value entry, source_name, data_date, synthetic], no_data: bool }`; "loading" exists only in the web app. A job is `{ status: queued \| running \| done \| failed, total, processed, failed, skipped, early_research, failures: [ { source_item_id, error } ] }`. `GET /api/v1/graph?node=<node id>&depth=<n>` returns that neighbourhood; without `node` it returns the whole graph. |

### RUB-04 (medium). No identity: who `decided_by` is, how the Team reaches the API, when "last seen" moves

**Where:** AD-2, line 84: `decided_by`. AD-8, line 129: `teams` (last seen). Line 247: "No login: the web app has a Team switcher."

**Problem:** FR-17 needs "who accepted each change", FR-29 needs a submitter, FR-27 and FR-28 need a last visit. The spine does not say what value goes in `decided_by`, how a request names its Team (path, query or header), or what advances last seen. If it advances on page load, "what changed" is empty after one refresh. ADV-22 is not absorbed by the PRD.

**Fix.** Add a Conventions row:

> | Identity | No login. Every request carries `X-DXP-Team` (Team ID) and `X-DXP-User` (display name), set by the Team switcher. `decided_by` is the `X-DXP-User` value, or `agent` for auto-applied entries. `teams.last_seen_seq` is advanced only by `POST /api/v1/teams/<team_id>/seen`, sent when the user closes the what-changed panel, never on page load. |

### RUB-05 (medium). FR-9 has a lookup but no owner, no route to it and no unmatched-term path

**Where:** AD-8, line 129: `glossary`, `terms`. Layer table, lines 31 to 36. Deployment diagram, line 217: "Search synonyms". Map row §4.2, line 328.

**Problem:** (a) No layer may write `terms`. (b) The callers of a term lookup are the pipeline's resolve filter and `search`; neither has an arrow to `memory` in the dependency diagram. (c) MongoDB Search synonyms need their own source collection (`search_synonyms` in the MongoDB skill); nothing says it is derived from `terms` or by whom. (d) "Unmatched terms go to the Reviewer" (FR-9) has no home. (e) The shape has no way to tell a synonym from a broader term (ADV-23) or to label a curated entry, which `data/README.md` requires for the "liquid biopsy" link.

**Fix.** Add to AD-8's Rule, and add `terms` to the Memory row of the layer table:

> `memory` owns `terms`: `{ _id: normalised term, canonical, kind: synonym \| broader, source: ncit \| mesh \| hgnc \| oncotree \| curated }`, seeded from `data/vocab` plus a curated file. `memory.glossary(term)` is the only term lookup. A `synonym` is mapped to its canonical name before a value is proposed; a `broader` term widens a search and never rewrites a value. An extracted term with no match keeps its text and gets the flag `unmatched_term`. `store.ensure_indexes()` generates the Search synonym collection from `terms`.

Add `pipeline --> memory` and `search --> memory` to the dependency diagram (see RUB-26).

### RUB-06 (medium). Alert rules are incomplete: "not alerted before", kinds, and two sources for a stage advance

**Where:** AD-10, line 141. AD-4, line 104: "a first Alert is raised". AD-5, line 111.

**Problem:** (a) FR-12 needs, per Team and Diagnostic, whether a first Alert was sent (addendum §2, "Alert rule inputs"); the spine places that state nowhere. (b) Baseline Diagnostics never get a first Alert, and FR-13 allows an update "after the first Alert"; whether the first live change to a Baseline Diagnostic alerts, and as which kind, is open. (c) A Diagnostic created in a live job emits a "new Diagnostic" event and one event per applied value; if those carry `used_in_trial`, the Team gets a first Alert and update Alerts from the same Source item, against FR-12's "exactly one". (d) `stage_advance` is set by the model per Finding (AD-10) while the real advance is decided by the stage comparison (AD-5); the two can disagree. (e) Dismissal lives in Memory (AD-8), which is not an exact store.

**Fix.** Add to AD-10's Rule:

> An Alert is `{ team_id, diagnostic_id, kind: first \| update, trigger, matched: { element, value }, status: new \| seen \| dismissed }`. `first`: at most one per Team and Diagnostic, raised when a matching Diagnostic is created in a `live` job, or on the first applied `live` change to a Diagnostic that Team has no Alert for `[ASSUMPTION]`. `update`: only when a `first` exists; events from the job that created the Diagnostic raise none. `stage_advance` is set by the ledger when an applied `lifecycle_stage` moves later, never by the model; the model sets the other three.

### RUB-07 (medium). Vector Search is in the deployment diagram and in no rule

**Where:** line 216, "Vector Search with Automated Embedding". AD-11, line 147: "query parsing" uses the stronger model. Map row §4.5, line 331.

**Problem:** Nothing says what text is embedded, which module queries it, or whether it decides which rows appear in the FR-21 table (ADV-24, not absorbed by the PRD). The MongoDB skill embeds a `search_text` field on `diagnostics`; under AD-1 only the ledger may write a Diagnostic, so someone has to own that field.

**Fix.** Add a Conventions row:

> | Search | FR-21: `search.query` asks the model for registry filters and returns them for correction; the filters decide which rows appear. `$vectorSearch` over `diagnostics.search_text` only orders those rows and serves free-text terms no filter expresses. `ledger.apply()` rewrites `search_text`; nothing else writes it. |

---

## 2. Enforceability of each Rule

| AD | Enforceable as written | Prevents its stated divergence |
| --- | --- | --- |
| AD-1 | Yes: one module writes `diagnostics` | Yes, once RUB-08 adds atomicity |
| AD-2 | Yes | Yes. Arrival-order conflicts on `single` fields: RUB-11 |
| AD-3 | Partly | No for re-runs and retries: RUB-09. Details open: RUB-12 |
| AD-4 | Yes: `mode` and `run_id` are on every document | Yes. Path to accept unreviewed values missing: RUB-14 |
| AD-5 | No: the comparison is in the wrong module | No under parallel items: RUB-08. Second place computing the label: RUB-15 |
| AD-6 | Yes | Yes for quotes. `supported` and confidence have no outcome: RUB-10. Manual values: RUB-02 |
| AD-7 | Yes | Yes. Off-switch trigger missing: RUB-13 |
| AD-8 | Yes: one importer of the SDK | Yes. Environments share memory: RUB-22 |
| AD-9 | Yes | Yes |
| AD-10 | Yes | Partly: RUB-06 |
| AD-11 | Yes: one importer of the client | Within one process only: RUB-20 |
| AD-12 | Yes | Yes |
| AD-13 | Yes | Yes. "Rewritten" is unsafe under concurrency: RUB-08 |

### RUB-08 (high). Nothing makes `ledger.apply()` safe under the fan-out, so stage can move backward and edges can be lost

**Where:** AD-5, line 111: "The pipeline proposes a change to the `lifecycle_stage` field only when that stage is later than the Diagnostic's current one". AD-2, line 77: "applying a new value moves the old one to `superseded`". AD-13, line 159: `edges` "is rewritten by `ledger.apply()` for the affected Diagnostic". AD-12, line 153: items fan out in one run; AD-11 allows 16 at once.

**Problem:** The stage comparison happens in the pipeline, before the write. Two items about one Diagnostic both read the same current stage, both propose, and the one applied last wins, even if its stage is earlier. The same happens in `live` when a Reviewer accepts an older pending stage change after a newer one. Most trial records name no assay (ADV-11), so many Source items will resolve to a few `approach:` Diagnostics, and concurrent applies on one document are the normal case. A read-then-write supersede loses entries, and a delete-and-insert of `edges` loses links. Stage drives the Early research label and `stage_advance` Alerts.

**Fix.** Add to AD-1's Rule:

> `ledger.apply()` changes a Diagnostic with one atomic update, never a read followed by a write.

In AD-5, replace the sentence quoted above with:

> The pipeline proposes every `stage_evidence`. `ledger.apply()` makes a stage `current` only if it is later than the current one, in the same atomic update; an earlier stage is stored as `superseded`. A Reviewer edit may move the stage either way.

In AD-13, replace "is rewritten by `ledger.apply()` for the affected Diagnostic" with:

> is upserted by `ledger.apply()` with `_id` = hash(from, to, kind); an edge is deleted only when no `current` entry supports it.

### RUB-09 (high). AD-3's upserts do not make a re-run or a Modal retry harmless

**Where:** AD-3, line 92: "All writes of these are upserts on `_id`." Prevents, line 90: "is retried by Modal, or is run twice". AD-4, line 103: "the ledger applies every Proposed change at once". AD-10, line 141: each applied change "appends one document to `events`".

**Problem:** The rule covers Source items, Findings and Proposed changes. It does not say the upsert is insert-only, so a second run can reset a rejected or applied Proposed change to `pending` (ADV-20: a re-scan re-drafts what the Reviewer rejected). It does not say `apply` is a no-op the second time, so a `list` field gains a duplicate entry ("adds an entry and never supersedes on add") and a `single` field supersedes itself. Events and Alerts have no derived ID, so each re-run appends them again: "what changed" doubles and FR-12's "exactly one first Alert" fails. A whole-job retry is the unit AD-12 creates, and developers will re-run batches all day.

**Fix.** In AD-3, replace "All writes of these are upserts on `_id`." with:

> All writes of these are insert-if-absent on `_id`; a re-run never changes `status`, `review` or `check` on a document that exists. `ledger.apply()` does nothing for a Proposed change that is already `applied` or `rejected`. Event `_id` is `e_` + hash(type, ref, new state) and Alert `_id` is `alert_` + hash(Team ID, Diagnostic ID, kind, trigger, ref); both are insert-if-absent.

### RUB-10 (medium). `supported: false` and low confidence have no outcome

**Where:** AD-2, line 83: `check: { quote_found, supported, confidence, flags }`. AD-6, line 117. AD-4, line 103.

**Problem:** FR-18 says a field whose quote does not support its value "also fails", and that low-confidence fields are marked for the Reviewer. The read model drops only on `quote_found`. In `baseline` every Proposed change is applied, including one with `supported: false`, and it is then displayed. No threshold defines low confidence (ADV-29), and AD-6 forbids the web app from applying its own.

**Fix.** Add to AD-6's Rule:

> A Proposed change with `quote_found: false` or `supported: false` is never auto-applied; it stays `pending` with a flag. The read model also drops entries with `supported: false`, and sets `low_confidence: true` when `check.confidence` is below `registry.LOW_CONFIDENCE` (0.7 `[ASSUMPTION]`).

### RUB-11 (medium). In auto-apply, a `single` field is decided by arrival order

**Where:** AD-4, lines 103 to 104. AD-2, line 77. Line 288: `modality`, `provider`, `regulatory_status`, `lifecycle_stage` are `single`.

**Problem:** In `baseline`, and for a Diagnostic created in a `live` job, every later Finding supersedes the `single` value set by an earlier one, with no Reviewer. A trial sponsor replaces the manufacturer seeded from the FDA list; an abstract replaces a seeded regulatory status. Two runs of the same batch give different Records.

**Fix.** Add to AD-4's Rule:

> In auto-apply, a `single` field that already has a `current` entry keeps it unless the new value's Source item date is later; the other entry is stored as `superseded`. Values seeded from the FDA list are not superseded by auto-apply.

### RUB-12 (medium). Three AD-3 details are left to whoever gets there first

**Where:** AD-3, lines 93 to 96. Source tree, line 299: `identity/ # normalise_name, resolve_diagnostic`. Layer table, line 31: Foundation may write `aliases` only.

**Problem:** (a) `approach:<modality>:<biomarker or any>` is not deterministic when a Finding names several biomarkers; the memlog says "primary biomarker", which is a model's choice. (b) `identity` may write only `aliases`, and no rule says who creates the `diagnostics` document, which AD-4 relies on to tell "created in this job". (c) `data/fda/assays.json` already holds `assay_normalised`, produced by the download script's own rule (described in the file's `normalisation` field). `identity.normalise_name` is not written yet; if it differs and the seed copies the file's keys, names found in trials will not match.

**Fix.** Add to AD-3's Rule:

> The approach alias uses the HGNC symbol when the Finding names exactly one biomarker, otherwise `any`. `identity` writes only `aliases`; `ledger` creates the `diagnostics` document on first apply, insert-if-absent, carrying the creating `run_id`. The seed passes each `name_strings_in_list` value through `identity.normalise_name`; `assay_normalised` is not used as a key.

### RUB-13 (low). Switching a rule off has no trigger, and a rule cannot be labelled synthetic

**Where:** AD-7, line 123: `rules.evaluate` is called "when a rule becomes `active`".

**Problem:** FR-19's test ends "switching the rule off removes the flag". The Rule names no evaluation when a rule becomes `off`. A rule drafted from a synthetic correction has nowhere to carry the label (ADV-16).

**Fix.** In AD-7, change the rule document to `{ field, text, status: draft | active | off, from_proposal_id, synthetic }` and replace "when a rule becomes `active`, over all `pending` Proposed changes for that field" with:

> when a rule becomes `active` or `off`, over all `pending` Proposed changes for that field, adding or removing its flags

### RUB-14 (low). No path to accept an unreviewed value

**Where:** AD-4, line 105: "The reviewer queue is a query on `proposals`" with `status: pending`.

**Problem:** FR-16 says values in a new Record are "marked unreviewed until a Reviewer accepts them". Those values are `applied`, so they are not in the queue, and nothing says `ledger.decide()` takes them.

**Fix.** Add to AD-4's Rule:

> `ledger.decide()` also takes an applied entry with `review: unreviewed` and sets it to `accepted`, `edited` or `rejected`.

### RUB-15 (low). The Early research label is computed in a second place

**Where:** AD-5, line 111: "computed by the read model". FR-4's test needs a live count "of Diagnostics marked Early research" during the job.

**Problem:** The job must count Early research Diagnostics and has no arrow to `search`. It will re-implement the test.

**Fix.** In AD-5, replace "is computed by the read model as `stage in {discovery, assay_development}`" with:

> is computed by `schema.registry.is_early_research(stage)`, which the read model and the job counter both call

---

## 3. Deferred

Twelve of thirteen lines are safe: each either removes scope or fixes the one constraint that matters if the item is built (Tavily needs an allow-list; a merge is a Proposed change; a capture is a Source item with `source: manual`; an export is built from the read model).

### RUB-16 (low). The Digest line builds FR-20 from the wrong source

**Where:** line 343: "An in-app page built from `events`."

**Problem:** A Digest is "Proposed changes and Alerts" (PRD Glossary). Pending Proposed changes produce no event (AD-10 lists applied changes only), so a Digest built from `events` cannot show the Reviewer's queue.

**Fix.** Replace the sentence with:

> An in-app page built from `events` and pending `proposals`.

---

## 4. Versions

Every row of the Stack table has a version, and model IDs stand as versions for Claude. Hosted services with no client version (Vercel, LangSmith service, the Source APIs) are acceptable without one.

### RUB-17 (low). Two Claude clients are listed for one module

**Where:** Stack, lines 187 and 189: `langchain-anthropic` and `Anthropic Python SDK`. AD-11, line 147.

**Problem:** AD-11 says one module calls Claude and does not say with which client. The two differ in what LangSmith traces without extra code, which matters for the API-side calls (rule drafting is the demo's key beat).

**Fix.** Name the one client in AD-11's Rule and delete the other Stack row. For example:

> `llm` uses `langchain-anthropic` for every call, so calls made from the API are traced like calls made from a job.

---

## 5. Requirement coverage

| FR | Home in the map and ADs | Verdict |
| --- | --- | --- |
| FR-1 | §4.1; `modal_app` cron; AD-9, AD-12 | Homed. What the scheduled scan fetches is not stated (REC-01 in Part B) |
| FR-2 | §4.1; AD-5; `sources` adapters are the approved types | Homed (RUB-15) |
| FR-3 | §4.1; AD-3 | Homed (RUB-09, RUB-12) |
| FR-4 | §4.1; AD-9, AD-11, AD-12 | Homed. Counter names open (RUB-03) |
| FR-5 | §4.2; AD-2, AD-11 | Homed |
| FR-6 | Deferred, line 341 | Deferred, acceptable |
| FR-7 | §4.2; AD-6 | Homed. Conflicts with manual values (RUB-02) |
| FR-8 | §4.2; AD-6 | Homed. Shape open (RUB-03) |
| FR-9 | §4.2; AD-8 | Partly homed (RUB-05) |
| FR-10 | Deferred, line 341 | Deferred, acceptable |
| FR-11 | §4.3; AD-1, AD-2, AD-5 | Homed. Unsafe under concurrency (RUB-08) |
| FR-12 | §4.3; AD-4, AD-10 | Homed. "Not alerted before" and "exactly one" unsecured (RUB-06, RUB-09) |
| FR-13 | §4.3; AD-10, AD-11 | Homed. Two sources for a stage advance (RUB-06) |
| FR-14 | §4.3; `alerts`, AD-10; audio at line 344 | Homed |
| FR-15 | §4.4; AD-1, AD-2, AD-4 | Homed |
| FR-16 | §4.4; AD-1, AD-4 | Homed (RUB-02, RUB-04, RUB-14) |
| FR-17 | §4.4; AD-2 | Homed |
| FR-18 | §4.4; AD-2, AD-6, AD-11 | Homed for the quote check. Other outcomes open (RUB-10) |
| FR-19 | §4.4; AD-7, AD-8 | Homed (RUB-13) |
| FR-20 | §4.4; AD-10; line 343 | Homed, from the wrong source (RUB-16) |
| FR-21 | §4.5; `search`; AD-9, AD-11 | Homed. Role of vector search open (RUB-07) |
| FR-22 | §4.5; AD-2, AD-6 | Homed. Cell shape open (RUB-03) |
| FR-23 | Deferred, line 341 | Deferred, acceptable |
| FR-24 | §4.5; `shortlists` in AD-8's Rule and the layer table | Homed in text; no AD binds it (RUB-18) |
| FR-25 | §4.5; AD-6; line 345 | Homed |
| FR-26 | §4.6; AD-13 | Homed. Scope of the endpoint open (RUB-03) |
| FR-27 | §4.6; AD-9, AD-10, AD-13 | Homed (RUB-04) |
| FR-28 | §4.7; AD-8, AD-10 | Homed (RUB-04, RUB-22) |
| FR-29 | §4.8; AD-1, AD-2, AD-6 | Home contradicted by AD-6 (RUB-02) |
| FR-30 | §4.1; AD-3, AD-4; "Saturday data" | Homed. Load path missing (REC-01 in Part B) |

### RUB-18 (low). FR-24 is bound by no AD, and four map rows omit an AD or module that governs them

**Where:** Binds lines of AD-1 to AD-13; map, lines 327 to 331.

**Problem:** No AD lists FR-24, although `shortlists` is decided in AD-8. Row §4.1 omits AD-9 (jobs, FR-1, FR-4). Row §4.2 omits `memory` (FR-9). Row §4.3 omits `api` and `audio` (FR-14). Row §4.5 omits AD-2 and AD-8.

**Fix.** Add FR-24 to AD-8's Binds. In the map: add AD-9 to §4.1; add `memory` to "Lives in" for §4.2; add `api` (audio) to §4.3; add AD-2 and AD-8 to §4.5.

---

## 6. Dimensions

| Dimension | State | Evidence |
| --- | --- | --- |
| Deployment and environments | Decided | Lines 204 to 247: diagram, environment table, one cluster, one deployer. Gaps: RUB-22, RUB-24 |
| Secrets and configuration | Decided, list incomplete | Conventions "Config", line 174. RUB-23 |
| Operations on the day | Silent, except the memory backend switch (AD-8) and the change-stream fallback (AD-10) | RUB-19 |
| Observability | Decided, thin | AD-12 (one trace per job), "Run tracing" (line 171), `jobs` progress. API-side calls: RUB-17 |
| Data seeding and migration | Partly decided | "Saturday data", lines 317 to 321; `store.ensure_indexes()`. No load path, no seed for Teams or terms, no reset: REC-01 in Part B, RUB-05, RUB-19 |
| Cost and rate limits | Decided for Claude and LangSmith only | AD-11, AD-12. RUB-20 |
| Security and privacy | Partly decided | No login (line 342), Atlas open to any address `[ASSUMPTION]` (line 247), no secret in the repository, PubMed text kept in the backend (AD-6). RUB-21, and REC-02 in Part B |
| Accessibility | Silent | RUB-25 |

### RUB-19 (medium). Operations on the day are not decided: seeing a failure, re-running, resetting, a provider being down

**Where:** no section. AD-12, line 153, records a failure result per item and stops there.

**Problem:** (a) No job status values and no place where failed items are listed (ADV-43). (b) No way to re-run only the failures, and no rule that a re-run skips finished items, so a retry repeats every model call. (c) The on-camera live job can be run once: nothing says how the production database returns to its post-Baseline state for a second take (ADV-28). (d) Nothing says what to do when Claude, Agent Memory, LangSmith or ElevenLabs fails during the build or the recording; the skills each have a Fallback section, but the spine does not point to them.

**Fix.** Add a block under Structural Seed:

> ### Operations on the day
>
> - A job ends `done` or `failed`. Failed items are listed in `jobs.failures` and shown on the progress screen.
> - `POST /api/v1/jobs` takes `{ mode, set, source_item_ids? }`, so failed items can be re-run. A job skips a Source item whose `processed_at` is set, unless `force` is true.
> - Reset for a new take: restore database `dxp` from the copy `dxp_baseline` taken straight after the Baseline job, then run `store.ensure_indexes()`. Test the restore once before recording.
> - Provider down: Claude, retry in `llm`, then the item fails and is re-run. Agent Memory, set `DXP_MEMORY_BACKEND=collections` and redeploy. LangSmith, set `LANGSMITH_TRACING=false`. ElevenLabs, the Alert is shown without audio. Each skill's Fallback section has the detail.

### RUB-20 (medium). The rate-limit rule holds inside one process, and cost has no line

**Where:** AD-11, line 147: "one process-wide semaphore of 16". Prevents: "separate code paths together exceeding the rate limit".

**Problem:** The API container, the job container and each developer's `modal serve` are separate processes on one API key. Two developers running a batch at once are at 32 or more, and the Claude skill warns that a sharp increase returns 429 even under the per-minute limit. No line bounds how often the Baseline job (293 trials plus 150 abstracts, at least two model passes each) is run, and ADV-17's spend cap is not absorbed.

**Fix.** Add to AD-11's Rule:

> The semaphore is per process. `POST /api/v1/jobs` returns 409 while a job is `running` in that database. Developers test with at most 20 Source items; the full Baseline job runs in production only.

### RUB-21 (medium). The public API can be made to spend money and change Records by anyone with the URL

**Where:** line 247: "No login". Line 342, Deferred "Login and tenancy". AD-9, line 135: `POST /api/v1/jobs`.

**Problem:** The API address is in the browser bundle (`NEXT_PUBLIC_API_URL`) of a site whose URL is given to judges, and the repository is public. With no check at all, anyone can start an ingest job (Claude spend), request audio (ElevenLabs credits), or accept and reject Proposed changes before or during judging. Deferring login is fine; leaving the spend endpoints open is a separate decision the spine does not make.

**Fix.** Add after line 247:

> `POST /api/v1/jobs` and audio generation require the header `X-DXP-Admin` equal to `DXP_ADMIN_KEY`, which the operator types into the web app once. CORS allows `FRONTEND_ORIGIN` and `http://localhost:3000` only.

### RUB-22 (medium). Developer databases and production share one memory that cannot be cleaned

**Where:** AD-8, line 129: "The memory user ID is the Team ID." Environment table, lines 242 to 245.

**Problem:** `DXP_DB` separates the collections. Agent Memory is one platform project for the cluster, and the memory skill states the public SDK cannot delete or update a memory. Every test write a developer makes for a seeded Team on Saturday stays in the memory that the on-camera resume reads, and PRD §8 requires that read to be real.

**Fix.** In AD-8, replace "The memory user ID is the Team ID." with:

> The memory user ID is `<DXP_DB>:<team_id>`, so developer databases and production never share memory.

### RUB-23 (low). The Config row reads as a closed list and is missing names the skills require

**Where:** Conventions "Config", line 174. Environment table, line 244, names `MODAL_DEV_SUFFIX`, which the row omits.

**Problem:** Missing: `FRONTEND_ORIGIN` (CORS, both the Modal and front-end skills), `ELEVENLABS_VOICE_ID` (ElevenLabs skill), `AGENTIC_MEMORY_PROJECT_ID`, `AGENTENGINE_SA_CLIENT_ID` and `AGENTENGINE_SA_CLIENT_SECRET` (memory skill), `MODAL_DEV_SUFFIX`. `LANGSMITH_*` hides the two variables a new workspace needs and the one that must not be set. Separately, the `.env` at the repository root uses `claude_api_key`, `elevenlabs_api_key` and `tavily_api_key`, which are not the names in this row; a Modal secret made from it will not be read.

**Fix.** Replace the list in the Config row with:

> `MONGODB_URI`, `DXP_DB`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_AGENT_ID`, `LANGSMITH_AGENT_ENVIRONMENT` (never `LANGSMITH_PROJECT` with these), `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `DXP_MEMORY_BACKEND`, `AGENTIC_MEMORY_PROJECT_ID`, `AGENTENGINE_SA_CLIENT_ID`, `AGENTENGINE_SA_CLIENT_SECRET`, `FRONTEND_ORIGIN`, `NCBI_EMAIL`, `NEXT_PUBLIC_API_URL`, `MODAL_DEV_SUFFIX`. Names are upper case exactly as written; rename the keys in the local `.env` to match before creating the Modal secret.

### RUB-24 (low). Developer isolation and the cluster tier are stated without the condition that makes them true

**Where:** line 244: "own `DXP_DB`". Line 170: indexes "run at deploy". Line 247: "Flex at minimum and M10 preferred".

**Problem:** (a) The Modal skill puts all variables in one shared secret, `dxp-secrets`; if `DXP_DB` is in it, `modal serve` writes to production. (b) Developers never deploy, so nothing creates indexes in their databases. (c) The memory skill says the standalone memory service needs M10; Flex is enough only with the `collections` backend. (d) The MongoDB skill gives Flex 10 search and vector indexes in total; three databases share that cap.

**Fix.** Replace the paragraph's first sentence at line 247 and extend line 170:

> One Atlas cluster: M10 when `DXP_MEMORY_BACKEND=agent_engine`, Flex only with `collections`. Flex allows 10 search and vector indexes across all databases. `DXP_DB` is set per developer outside the shared Modal secret.

> Indexes are created in `store.ensure_indexes()`, run at deploy and once by each developer against their own database.

### RUB-25 (low). Accessibility of the web app is not mentioned

**Where:** no line. Stack, line 198: `react-force-graph-2d`, which the front-end skill says paints on canvas.

**Problem:** The dimension is silent. Two parts of it affect the build and the video: status shown by colour alone cannot be read in a recording (ADV-16 makes the same point for the synthetic label), and a canvas graph is the only way to reach some facts.

**Fix.** Add a Deferred line:

> - **Accessibility.** Not audited on Saturday. Two rules hold: every status (Early research, unreviewed, manual, synthetic, flagged, no data) is shown as text, not by colour alone; every fact in the Graph view is also reachable from a table or a Record page.

---

## 7. Diagrams

All four Mermaid blocks parse (Mermaid 11.17.2). The deployment flowchart agrees with the environment table and with AD-9, AD-10 and AD-12. The sequence diagram agrees with AD-4 except for one step (RUB-27).

### RUB-26 (medium). The dependency diagram lacks arrows that the ADs and the layer table need, and one sentence contradicts it

**Where:** lines 41 to 65. Line 65: "Imports point down this diagram only. Nothing imports `api` or `modal_app`."

**Problem:** (a) "Down" is ambiguous: along a drawn arrow, or to anything reachable. (b) Read as drawn arrows, AD-7 cannot be built: `rules.evaluate` "is called by the pipeline's check filter" and there is no `pipeline --> rules`. (c) The layer table lets `api` write `teams`, `shortlists` and `audio`, and only `store` creates a client, but there is no `api --> foundation`. (d) A Reviewer confirms a rule and switches it off through the API; there is no `api --> rules`. (e) The deployment diagram has `job --> mem`; the dependency diagram has no `pipeline --> memory`, and no AD says what a job reads or writes in memory. (f) "Nothing imports `api`" contradicts the arrow `modal --> api`. (g) `api` must start a Modal function without importing `modal_app`; the Modal skill states that looking a function up by name "works only against a deployed App, never against `modal serve`", so the developer environment needs the handle passed in.

**Fix.** Add these lines to the flowchart:

```text
  api --> rules
  api --> foundation
  pipeline --> rules
  pipeline --> memory
  search --> memory
```

Replace line 65 with:

> A module imports only the modules it has an arrow to. Only `modal_app` imports `api`; nothing imports `modal_app`. `modal_app` passes the job-start function into the API when it builds the app, so `api` never looks a Modal function up by name.

### RUB-27 (low). Small disagreements in the entity diagram, the sequence diagram and the layer table

**Where:** entity diagram, lines 272 to 285; sequence diagram, lines 264 to 266; layer table, lines 31 to 36.

**Problem:** (a) The entity diagram has no link from ALERT to DIAGNOSTIC or from SHORTLIST to DIAGNOSTIC, although an Alert is about one Diagnostic and a Shortlist is a set of them; it has no link for `rules.from_proposal_id`; `TERM }o--o{ DIAGNOSTIC` matches no stored field. (b) The sequence diagram runs "write value entry" and "event appended" after the `alt` block, so also after a reject, while AD-10 emits events for applied changes only. (c) The layer table gives `events` to the Ledger layer, but AD-10 writes it through `store.emit_event()` in Foundation; `terms` has no writer (RUB-05); `api` creates the `jobs` document that the table gives to Ingest filters.

**Fix.** In the entity diagram add `DIAGNOSTIC ||--o{ ALERT : about`, `SHORTLIST }o--o{ DIAGNOSTIC : picks`, `PROPOSAL ||--o| RULE : "drafted from"`, and delete the TERM line. In the sequence diagram wrap lines 264 to 266 in `opt applied (not rejected)` and `end`. In the layer table add to Foundation's "May write": "`events` (through `emit_event`, called by the Ledger layer)", and to Edge: "`jobs` (create only)".

---

## 8. Terseness

The spine records decisions and keeps rationale out. Prevents lines state the divergence in one clause. The Stack, source tree and entity diagram are seed and are short.

### RUB-28 (low). Three small cuts and one unexplained tag

**Where:** line 350; lines 343 to 345; AD headings at lines 67, 87, 131, 149.

**Problem:** (a) "Claude Agent SDK. Not used. Revisit after the hackathon if the scan becomes an open-ended researcher." is a rejected option with its rationale. (b) The Deferred lines for the Digest, the audio briefing and the export each state a decision; they are not deferred. (c) Four of thirteen ADs carry `[ADOPTED]` and nothing says what the tag or its absence means for the other nine. (d) "Saturday data" repeats counts (293, 150, 40, 24, 76) that live in the manifests and change if the downloads are re-run on Saturday morning, as `data/README.md` advises.

**Fix.** Delete line 350. Move the decided sentences of lines 343 to 345 into the Conventions table as rows "Digest", "Audio" and "Export". Add to line 23: "`[ADOPTED]` marks a decision the team confirmed one by one; the others were accepted as a set and bind equally." In "Saturday data" add: "Counts are as of 13 November; the manifest subset names decide membership."
