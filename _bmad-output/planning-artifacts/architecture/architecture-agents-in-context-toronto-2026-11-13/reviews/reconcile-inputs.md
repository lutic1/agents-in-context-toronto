---
title: "Reconciliation: ARCHITECTURE-SPINE.md against its inputs, DxProvida (DxP)"
created: 2026-11-13
target: ../ARCHITECTURE-SPINE.md
part: B (what the inputs require that the spine does not carry)
companion: review-rubric.md (Part A, quality checklist; findings RUB-01 to RUB-28)
---

# Reconciliation of the spine against its inputs

Review only. No existing file was changed. Line numbers refer to `ARCHITECTURE-SPINE.md` unless another file is named. Skill paths are under `.claude/skills/`.

**Verdict.** Most of what the inputs require landed: the match key, the two ingest modes, the one Learned rule mechanism, the off-switch outside Agent Memory, the 150-second cap, the concurrency of 16, the PubMed rule for responses and exports, and the Saturday subsets. Two things that affect the build on the day did not: how Source items reach a job running on Modal, and PubMed text leaving the backend through LangSmith traces.

**Counts.** 0 critical, 2 high, 4 medium, 6 low. Items already raised in Part A are cross-referenced by their RUB number and not counted again.

**Severity** is the same scale as Part A: critical, a PRD guardrail is breached if built as written; high, two builders diverge or a P1 path has no home; medium, a real gap with a quick workaround; low, wording or bookkeeping.

**Inputs read.** `prd.md`, `addendum.md` (all four sections), `review-adversarial.md` (ADV-01 to ADV-43), `data/README.md`, the four `data/*/manifest.json` files, one record from each data file, `scripts/data/dxp_sources.py`, and the "Read this first" section of each of the ten `dxp-*` skills, plus the skill passages cited below.

---

## 1. PRD (`prd.md`)

| Requirement or constraint | Where it landed | Status |
| --- | --- | --- |
| §8 Open data only; four Sources; nothing licensed | Deployment diagram (line 222); `sources` adapters; Tavily allow-list in Deferred (line 339) | Landed |
| §8 PubMed: short quotes, citation and link; no abstract text in the repository | AD-6, line 117, for responses and exports | Partly. Traces: **REC-02**. Fixtures and quote length: **REC-09** |
| §8 Real behaviour on camera: one live memory write and read, one live Learned rule | AD-7 and AD-8 make both possible; the direct-write detail is in the memory skill | Landed. Shared memory between environments puts the live read at risk: RUB-22 |
| §8 Synthetic data labelled wherever it appears | Conventions "Synthetic data", line 172 | Partly: **REC-04** |
| FR-30 and Glossary: Baseline load leaves out the last four weeks | "Saturday data", lines 319 to 321, by subset name | Landed as seed. Not enforceable until Source items carry their set: **REC-01** |
| §8 Agent Memory by decision, plain collections as fallback | AD-8, `DXP_MEMORY_BACKEND` | Landed. Tier wording: RUB-24 |
| §8 Model limits: confirm key and rate limits before the batch | AD-11 (semaphore of 16); the check itself is in the Claude skill | Landed; correctly split |
| §8 MongoDB as the advantage: say which capability powers which behaviour | Nowhere | **REC-03** |
| §8 Human decision, logged | AD-1, AD-4, `decided_by` | Landed. Who `decided_by` is: RUB-04 |
| §9 Open question 4: how Lifecycle stage is derived and checked for accuracy | AD-5 answers "derived" | "Checked" not answered: **REC-05** |
| FR-7 and FR-29 together: no uncited value, yet hand-typed values are shown | AD-6 against AD-1 | Contradiction: RUB-02 |
| FR-12: "the Team has not been alerted about it before" | Nowhere | RUB-06 |
| FR-18: unsupported value "also fails"; low confidence marked | `check` shape only | RUB-10 |
| FR-19: switching a rule off removes the flag | AD-7, no trigger | RUB-13 |
| FR-9: unmatched terms go to the Reviewer | Nowhere | RUB-05 |
| FR-20: Digest of Proposed changes and Alerts | Deferred, line 343, from `events` only | RUB-16 |
| FR-2: "stage not determined" | AD-5, `not_determined` in the registry | Landed |
| FR-13: semantic matching, not keyword rules | AD-10: the extraction model sets the trigger | Landed. The MongoDB skill's vector matching for FR-13 is not used: RUB-01 |
| §6.2 Lung only; no congress sources; no Atlas agent runtime | Data and `sources` adapters; AD-12 runs LangGraph on Modal | Landed |
| §8 Event rules: prepared work disclosed | `data/README.md`, outside the spine | Not architecture. One consequence: **REC-12** |

## 2. PRD addendum (`addendum.md`)

| Item | Where it landed | Status |
| --- | --- | --- |
| §2 Field history | AD-2 | Landed |
| §2 Reviewer corrections: one mechanism or several | AD-7 | Landed |
| §2 Agent roster | Paradigm, line 27: five filters | Landed |
| §2 Graph view: connections between clusters | AD-13 | Landed |
| §2 Alert rule inputs: first Alert sent per Team and Diagnostic; stage history; lines of therapy; linked trials; standard-of-care status | Stage history and trials through AD-2 | First-Alert state missing: RUB-06 |
| §3 MongoDB mapping: "Architecture confirms or changes each row" | Nowhere | **REC-03** |
| §4 Friday: Atlas tier | Line 247 | Landed (RUB-24) |
| §4 Friday: Agent Memory provisioning | Memory skill, "Read this first" 3 and 4 | Correctly left to the skill |
| §4 Friday: Claude tier and concurrency of 16 | AD-11; tier check in the Claude skill | Landed |
| §4 Friday: paid plans for HeyGen and ElevenLabs | Their skills | Correctly left to the skills |
| §4 Friday: LangSmith agent record and two variables; 5,000 traces | AD-12 for the allowance; `LANGSMITH_*` in the Config row | Allowance landed. Variables left to the skill, with a caveat: RUB-23 |
| §4 Match key designed; uniqueness enforced in MongoDB | AD-3 | Landed (RUB-09, RUB-12) |
| §4 Narrower query sets; Held-back set from ClinicalTrials.gov and PubMed | "Saturday data" | Landed |
| §4 Citations cannot be combined with structured output; check against the stored snapshot | AD-11 (JSON-schema method); AD-6 | Landed |
| §4 Learned rule off-switch is a flag in a DxP collection | AD-7 | Landed |
| §4 Memory scoped per user, bound to the Team; direct writes for the live demo | AD-8 for the binding; direct writes in the memory skill | Landed; correctly split |
| §4 150-second cap; background job; front end polls | AD-9, AD-10 | Landed |
| §4 Modal has no fixed address; Atlas allows any address | Line 247, `[ASSUMPTION]` | Landed |
| §4 `react-force-graph-2d` | Stack | Landed |
| §4 Orchestration: LangGraph or the Claude Agent SDK | AD-12; Deferred line 350 | Landed |
| §4 Give judges the production URL | Environment table, line 245 | Landed |
| §1 Journeys 2 and 4 (performance matrix, capture) | Deferred, lines 341 and 346 | Landed |

## 3. Adversarial review (`review-adversarial.md`)

Only findings that affect how the system is built are listed. ADV-14, 15, 21, 27, 30, 31, 34 to 39, 41 concern the PRD, the video or the schedule.

| Finding | Absorbed by the PRD | In the spine | Status |
| --- | --- | --- | --- |
| ADV-01 P1 too large | Noted in §6.1 | Deferred, line 338 | Landed |
| ADV-02 set and add | FR-15 | AD-2 | Landed |
| ADV-03 held-back set; two dates per change | FR-30; dates not absorbed | AD-4; no Source item date on a value | **REC-11** |
| ADV-04 quote must exist in the Source | FR-18 | AD-6 | Landed |
| ADV-05 creation and stage bypass review | FR-16 | AD-4, AD-5 | Landed (RUB-14) |
| ADV-06 first batch alerts everyone | FR-30 | AD-4; AD-10 `[ASSUMPTION]` on tumour type | Landed |
| ADV-07 paths with no Alert; dismissal | FR-12 rewritten; dismissal not | Dismissal in Memory only | RUB-06 |
| ADV-08 trigger firehose; duplicates; backward stage | Not absorbed | Alerts fire on applied events (AD-10) | RUB-06, RUB-08 |
| ADV-09 Early research boundary | FR-2 | AD-5 | Landed |
| ADV-10 stage is unmeasured and one per Diagnostic | §9 question 4 | AD-5 derives it | **REC-05** |
| ADV-11 match key; parallel creation; named against unnamed | FR-3 defers to architecture | AD-3; merges in Deferred | Landed. Several biomarkers, who creates the document: RUB-12 |
| ADV-12 Learned rule | FR-19 | AD-7 | Landed (RUB-13) |
| ADV-13 preview dependency; name what ran | §8 Agent Memory | AD-8, two backends | Landed. Naming what ran: **REC-03** |
| ADV-16 synthetic data behind the theme behaviours | §8 | Conventions row | **REC-04**, RUB-13 |
| ADV-17 model capacity; spend cap | §8 Model limits | AD-11 | Spend and shared key: RUB-20 |
| ADV-18 human-entered values against FR-7 | Not absorbed | AD-6 against AD-1 | RUB-02 |
| ADV-19 "no data" claims too much; withheld state | Not absorbed | One no-data state | **REC-10** |
| ADV-20 scans not idempotent; stale proposals | Not absorbed | Derived IDs only | RUB-09 and **REC-06** |
| ADV-22 no users | Not absorbed | Team switcher | RUB-04 |
| ADV-23 "liquid biopsy" is a broader term | Not absorbed | Nothing | RUB-05 |
| ADV-24 structured query against vector search | Not absorbed | AD-11 "query parsing" | RUB-07 |
| ADV-25 capabilities the requirements do not need | Not absorbed | Nothing | **REC-03** |
| ADV-26 graph has no scope | Not absorbed | Whole graph implied | RUB-03 |
| ADV-28 repeat the loop from a reset state | Not absorbed | Nothing | RUB-19 |
| ADV-29 confidence threshold | Not absorbed | Nothing | RUB-10 |
| ADV-32 Provider websites; sole Evidence for a stage | §8 allow-list | Deferred, line 339 | Landed; the sole-Evidence bar can wait for the adapter |
| ADV-33 fetch against process | Not absorbed | Nothing | **REC-01** |
| ADV-40 "why it matters" is generated text | Not absorbed | Not decided; one module | No change needed; AD-11 already routes any model call |
| ADV-42 repository holds identifiers and quotes only | §8 | AD-6 | **REC-09** |
| ADV-43 failed items; skipped count | Not absorbed | Failure result per item | RUB-19, RUB-03 |

## 4. Dataset notes (`data/README.md` and manifests)

| Item | Where it landed | Status |
| --- | --- | --- |
| Subsets `recent_baseline_narrow`, `narrow`, `small` | "Saturday data" | Landed. Verified: the 293 Baseline trials and the 40 Held-back trials share no ID |
| PubMed text is not in the repository | `.gitignore`; AD-6 | No path from the files to a job: **REC-01** |
| `NCBI_EMAIL` read from the environment | Config row | Landed |
| Re-run the downloads on Saturday morning | Nothing | Counts in "Saturday data" go stale: RUB-28 |
| "Liquid biopsy" not linked to ctDNA; add a curated entry, labelled | Nothing | RUB-05 |
| Noisy synonym matches; review `vocab/synonyms.json` | Nothing | Correctly left to the data notes; it is a review task, not a rule |
| PMID 30335319 not downloaded | Nothing | No action: it is not in the downloaded files, so it cannot be loaded |
| FDA adds little to the Held-back set | "Saturday data" uses trials and abstracts | Landed |
| No shared identifier; `fda/assays.json` holds normalised names | AD-3 | Landed (RUB-12) |
| Three PubMed records whose stored date is a day outside their window | Nothing | **REC-08** |
| Attribution and terms per source | Conventions "Attribution", line 173 | Partly: **REC-07** |

---

## Findings

### REC-01 (high). Nothing says how Source items reach a job on Modal, or whether Saturday's "scan" fetches or reads

**Sources:** `data/README.md`, "PubMed abstracts are not in this repository"; `.gitignore`, `data/pubmed/*.jsonl`; addendum §4, "Baseline and Held-back set"; ADV-33; PRD FR-1 and FR-30.

**Where:** "Saturday data", lines 317 to 321; source tree, line 301: `sources/ # one adapter per Source: fetch(window) -> Source items`; AD-12, line 153.

**Problem:** The sets are named by manifest subset, and the adapter is specified as a fetch by window. Those do not meet. (a) A window fetch against the live APIs returns a query's whole window (699 and 45 trials, 2,521 and 90 abstracts with the default queries), not the chosen subsets, which are ID lists in the manifests. (b) The job runs on Modal. The Modal skill's image adds only the `dxp` package, and PubMed text is not in the repository, so the deployed job cannot read `data/pubmed/*.jsonl` unless the deployer's laptop has the file and the image is told to include it. (c) No Source item records which set it belongs to, so a `baseline` job cannot refuse a Held-back item and FR-30's exclusion rests on whoever picks the IDs. (d) The scheduled scan runs "only in the deployed app" with `mode: live`, and nothing says what it fetches or when; it could fire during the recording and change production. (e) ADV-33's point stands: the video could show a file being read and imply a fetch. One developer will build `sources` and the other `modal_app`; each needs this answered.

**Fix.** Replace the three bullets of "Saturday data" with:

> - **Load, no model calls, run from a laptop that has the files:** `python -m dxp.sources.load` inserts the chosen items from `data/*.jsonl` into `source_items` (insert-if-absent), each with `set: seed | baseline | heldback` taken from the manifest subset ID lists, never from a date comparison. PubMed text reaches Atlas only this way; `data/` is not added to the Modal image.
> - **Seed:** `set: seed` is `data/fda/assays.json` and the lung rows of the FDA list.
> - **Baseline job** reads `set: baseline`: the trials in `recent_baseline_narrow` and the 150 most recent abstracts of the PubMed `small` baseline subset. A `baseline` job refuses any other set.
> - **Live job, on camera,** reads `set: heldback`: the trials in `narrow` and the abstracts in `small`. On Saturday no job calls a Source API.
> - **Scheduled scan:** the one live fetch. It calls the ClinicalTrials.gov adapter for records posted since the last scan, daily at 06:00 UTC, so it cannot fire during the recording `[ASSUMPTION]`. The video says which items were fetched live.

### REC-02 (high). PubMed text leaves the backend through LangSmith, and the plan is to share a trace by public link

**Sources:** PRD §8, "Open data only": "PubMed abstracts are public but not licensed for redistribution"; `dxp-open-data-sources/references/terms.md`, team policy: DxP should not "show a whole abstract in the UI, the Digest, the audio briefing or the video"; `dxp-langgraph-langsmith`, "What DxP uses it for": "SM-2 the trace shown on camera: LangSmith run names, tags and a public share link", and pattern 6: "copy the public link (anyone with the link can view)".

**Where:** AD-6, line 117: "PubMed `raw_text` never leaves the backend". AD-12, line 153: one LangGraph run per job, traced. "Saturday data", line 321: the on-camera job includes 24 abstracts.

**Problem:** AD-6's sentence is true for API responses and exports only. Under AD-12 the on-camera job is one trace, and whatever the graph passes as state or prompt goes into it, including PubMed `raw_text`. Sharing that trace by public link, or scrolling it in the video, publishes abstract text. The two builders will not see this: one reads AD-6 and believes the rule is met, the other follows the skill and shares the link.

**Fix.** Add to AD-6's Rule:

> The same rule covers traces. A job whose Source items include PubMed runs with tracing off (`langsmith.tracing_context(enabled=False)`), or its trace is never shared by link or shown in the video. The trace shown on camera comes from a job over ClinicalTrials.gov items only.

In "Saturday data", make the on-camera run two jobs: Held-back trials first (traced), Held-back abstracts second (untraced).

### REC-03 (medium). The MongoDB capability map was neither confirmed nor changed

**Sources:** addendum §3: "Architecture confirms or changes each row"; PRD §8, "MongoDB as the advantage"; SM-2: "Each step names the MongoDB capability behind it"; ADV-13 ("The video names what actually ran") and ADV-25.

**Where:** no section. The Capability map, lines 325 to 334, has no capability column. The deployment diagram names Vector Search, Search synonyms and Agent Memory without tying them to a behaviour.

**Problem:** The spine changes or leaves open several rows without saying so. FR-21 is mapped to Automated Embedding with vector search, while AD-11 gives query parsing to Claude and no rule mentions vector search (RUB-07). FR-9 is mapped to taxonomic memory, while AD-8 keeps the exact list in `terms`. `rules` is the source of truth and Agent Memory only receives a copy that nothing reads (AD-7), so "Agent Memory, procedural" does not power FR-19. `GET /api/v1/graph` is "built from `edges`" (AD-13) with no `$graphLookup`. The row "a new kind of Diagnostic arriving with new fields" contradicts the fixed registry (AD-2). On the `collections` backend nothing is Agent Memory. The system diagram is meant for the video, so the mismatch will be on camera.

**Fix.** Add a column "MongoDB capability that runs" to the Capability map, or add this table under it, and correct any row the team disagrees with:

> | Behaviour | Capability that runs |
> | --- | --- |
> | Resume (FR-28) | Agent Memory, episodic, on `agent_engine`; plain collections on `collections` |
> | Learned rule (FR-19) | The `rules` collection applies the rule; Agent Memory, procedural, holds a copy and is named only if `recall` reads it back on camera |
> | Synonyms (FR-9) | MongoDB Search synonym mapping generated from `terms`; Agent Memory, taxonomic, holds a copy |
> | Plain-language query (FR-21) | Claude parses filters; Vector Search with Automated Embedding orders the rows |
> | Graph view (FR-26) | `$graphLookup` over `edges` for a node's neighbourhood |
> | Live change (FR-13, FR-27) | Change stream on `events` |
> | New kind of Diagnostic with new fields | Dropped: the registry is fixed for Saturday |
>
> `GET /api/v1/health` returns `{ memory_backend }` so the captions name what ran.

### REC-04 (medium). The synthetic label does not reach content that comes from memory

**Sources:** PRD §8, "Synthetic data": labelled "wherever they appear"; "Real behaviour on camera": synthetic history "does not stand in"; ADV-16.

**Where:** Conventions "Synthetic data", line 172: "the read model passes the flag through". AD-8, line 129: Memory holds session history and "supplies the resume summary".

**Problem:** Synthetic session history lives in Memory, and the resume summary comes from `memory.recall`, not from `search.readmodel`. The convention's mechanism does not cover it. A resume built from seeded episodes would appear unlabelled, next to the one real episode the video must show. The memory skill shows `metadata` on writes and no synthetic field, so each backend builder will decide alone.

**Fix.** Add to AD-8's Rule:

> `remember_episode` takes `synthetic: bool` and `recall` returns it for every item, on both backends. A resume summary built from any synthetic item is returned with `synthetic: true`.

### REC-05 (medium). Lifecycle stage accuracy is still unmeasured, and the per-use question is not recorded

**Sources:** PRD §9, question 4: "How the Lifecycle stage ... is derived and checked for accuracy (ADV-10). For architecture."; ADV-10.

**Where:** AD-5, line 111. Deferred, line 348: "Gold-set accuracy harness (SM-5). A script over the pipeline's extract filter".

**Problem:** AD-5 answers how stage is derived. Nothing answers how it is checked: the Gold-set line does not say that `stage_evidence` is labelled, so SM-5 still reports nothing about the value that drives every Alert and the Early research label. ADV-10's second point, one stage per Diagnostic when validation differs by clinical use, is decided by AD-5 in favour of one stage and is not listed anywhere as a choice.

**Fix.** Replace the Gold-set line and add one Deferred line:

> - **Gold-set accuracy harness (SM-5).** A script over the pipeline's extract filter. Gold-set labels include `stage_evidence.stage`, so stage accuracy is reported with the fields.
> - **Lifecycle stage per clinical use (ADV-10).** Not built. Stage is one value per Diagnostic.

### REC-06 (medium). A Source item has no version, so an updated record either overwrites the text its quotes were checked against or is ignored

**Sources:** ADV-20: "A Source item is processed once per version"; `dxp-open-data-sources`, "Read this first" 5: ClinicalTrials.gov returns only the current version; same skill, FR-30 notes: "treat one as updated only when `text_sha256` differs". Every record in `data/*.jsonl` carries `text_sha256`.

**Where:** AD-3, line 92: Source item ID `<source>:<source_item_id>`, upsert. AD-6, line 117: the check runs against stored `raw_text`.

**Problem:** With a replacing upsert, a later version of a trial overwrites `raw_text`, and every earlier quote from that trial can no longer be verified. With insert-if-absent (RUB-09), the later version is never read, so FR-15's "new study readout" on a known trial cannot produce a Proposed change. Saturday's sets do not overlap, so this bites on the first scheduled scan, not in the two planned jobs.

**Fix.** In AD-3, replace "Source item `<source>:<source_item_id>`" with:

> Source item `<source>:<source_item_id>@<first 8 characters of text_sha256>`. A version already stored is skipped. Evidence points at the version it was checked against.

### REC-07 (low). Attribution covers the Evidence line and misses three other obligations

**Sources:** `data/README.md`, "Attribution and terms"; `dxp-open-data-sources/references/terms.md`: ClinicalTrials.gov asks for attribution, the processing date and a statement of modifications; the Held-back set "must be labelled as a dated snapshot"; PubMed: show the publisher's copyright line where it exists; OncoTree and NCI Thesaurus are CC BY 4.0.

**Where:** Conventions "Attribution", line 173: "The read model attaches the source name and its data date to every Evidence."

**Problem:** (a) The data date sits in a different place per source: `dates.source_data_timestamp` on trials, `dates.page_content_current_as_of` on FDA rows, and only in the manifest for PubMed. (b) Nothing carries the statement of modifications, the "dated snapshot" note or the non-endorsement line. (c) Vocabulary terms shown in the app are not Evidence, so the CC BY credit has no home. (d) The PubMed copyright line (`extra.abstract_copyright`) is not attached.

**Fix.** Replace the Attribution row with:

> | Attribution | The loader stores `data_date` on every Source item (from `dates.source_data_timestamp`, `dates.page_content_current_as_of`, or the PubMed manifest's `content_current_as_of`). The read model attaches source name, `data_date` and, for PubMed, the publisher's copyright line to every Evidence. `GET /api/v1/attribution` returns the attribution and modification lines from `data/*/manifest.json`; the web app shows them in the footer and every export includes them. |

### REC-08 (low). The three PubMed edge records do not affect Saturday's sets, provided membership is never decided by date

**Sources:** `data/pubmed/manifest.json`, `split_date_outside_window`: PMIDs 39534334 and 39537244 (Baseline, stored date 2024-11-13) and 42888302 (Held-back, stored date 2026-10-16, the last Baseline day).

**Where:** "Saturday data", lines 320 to 321.

**Problem:** Checked against the manifest: none of the three is in the `small` Baseline or Held-back subset, and none is among the 150 most recent `small` Baseline abstracts (those run from 2026-05-22 to 2026-10-16). PMID 42888302 is in the `narrow` Held-back subset. If any code assigns a set by comparing `dates.split_date` with the cut-off, or the team switches to `narrow`, that record is loaded as Baseline and FR-30's exclusion is broken by one item.

**Fix.** Covered by the first bullet of REC-01's text ("taken from the manifest subset ID lists, never from a date comparison"). No other change.

### REC-09 (low). No rule keeps PubMed text out of fixtures and Gold-set files, and "short quote" has no length

**Sources:** PRD §8: "DxP shows short quotes"; `terms.md` team policy: do not commit abstract text "in seed files, fixtures, Gold set files or test snapshots"; show "a sentence or two"; ADV-42.

**Where:** AD-6, line 117. Deferred, lines 348 to 349 (Gold set, tests).

**Problem:** `.gitignore` protects `data/pubmed/*.jsonl` only. A Gold-set file or a test snapshot written on Saturday would hold abstract text under another path. Nothing stops a model from returning a whole abstract as its quote, which the app would then display. The policy exists in a skill reference file that the builder of a test or the harness has no reason to load.

**Fix.** Add to AD-6's Rule:

> No file in the repository holds PubMed text: fixtures, Gold-set files and test snapshots keep PMIDs and labels and re-fetch. A quote longer than 400 characters fails the check `[ASSUMPTION]`.

### REC-10 (low). "No data" also covers a value DxP has and withheld

**Sources:** ADV-19; PRD FR-8.

**Where:** AD-6, line 117: the read model "drops any value entry whose `check.quote_found` is false and adds the no-data state for empty fields".

**Problem:** A field whose only entry failed the gate is returned as "no data for this indication". The Director reads that as "nothing published", when DxP found a value and could not verify it.

**Fix.** In AD-6, replace "adds the no-data state for empty fields" with:

> returns `no_data` for a field with no entry and `withheld` for a field whose entries were all dropped by the gate

### REC-11 (low). A value entry has no Source item date, so stage history in a replay shows only 14 November

**Sources:** ADV-03: "Every Record change stores two dates, the Source item's publication date and the date DxP ingested it"; PRD FR-11: "keeps every earlier stage and its date".

**Where:** AD-2, lines 80 to 84: `decided_at` is the only date. Conventions "Dates", line 167.

**Problem:** Every value is applied on Saturday, so every `decided_at` is the same day. The Lifecycle history and the tie-break proposed in RUB-11 both need the date of the Source item.

**Fix.** In AD-2, extend the evidence shape:

> `evidence: { source_item_id, quote, source_url, source_date }`, where `source_date` is the Source item's `dates.split_date`.

### REC-12 (low). The quote check and the fetchers already exist in `scripts/data`, and the spine does not say whether the backend may use them

**Sources:** `scripts/data/dxp_sources.py`: `normalise`, `quote_in_source`, `fetch_ctgov(window=...)`, `fetch_pubmed(window=...)`; its header says it was copied from the data-sources skill. `data/README.md`: "Nothing here is product code." `text_sha256` in every data file was computed with that `normalise`.

**Where:** AD-6, line 117: "`evidence.quote_in_source()` is the only quote check". Source tree, lines 298, 301 and 314.

**Problem:** There will be two implementations of the check unless one is declared the source. If `evidence.normalise` differs from the script's (Unicode NFKC, whitespace collapsed), stored hashes stop matching and "word for word" changes meaning. If `sources` copies the fetchers, the README's disclosure sentence is no longer true and must be updated for the event rules.

**Fix.** Add to AD-6's Rule and to the source tree comment for `scripts/data/`:

> `evidence.normalise` is Unicode NFKC with whitespace collapsed, the rule that produced `text_sha256` in the data files. `backend` does not import `scripts/data`; code copied from it is listed in the README disclosure.

---

## Correctly left to the technology skills

These were checked in the skills and do not belong in the spine, because each is used inside one module or is a setup task:

- Agent Memory provisioning, the command-line tool, keys and the M10 requirement (`dxp-atlas-agent-memory`, "Read this first" 3 and 4), and direct writes instead of background extraction (item 6). Only `memory` imports the SDK (AD-8).
- The Claude tier check, the ramp to 16 and then 32, refusal handling and the rejected parameters (`dxp-claude-api`). Only `llm` calls Claude (AD-11).
- The LangSmith agent record and variable names (`dxp-langgraph-langsmith`, "Read this first" 1). The spine's `LANGSMITH_*` is enough if RUB-23's fuller list is not taken; the trap is that setting `LANGSMITH_PROJECT` as well sends no traces.
- Product names to say on camera (`dxp-mongodb-atlas` 1 and 2, `dxp-atlas-agent-memory` 2).
- Paid plans and rendering time for HeyGen and ElevenLabs. HeyGen is outside the product.
- Modal timeouts, input concurrency for the long-poll, cold starts and the secret (`dxp-modal`).
- ClinicalTrials.gov markdown escapes, NCBI request etiquette, the retired PMC service and the FDA page move (`dxp-open-data-sources`). The stored `raw_text` is already cleaned.
- The Tavily allow-list code and date filters (`dxp-tavily`), deferred with the adapter.
- Next.js scaffold flags, preview protection and CORS code (`dxp-vercel-frontend`).
- Noisy synonym matches and the missing book chapter (`data/README.md`): review tasks with no rule to write.

Not left safely to the skills, because the skill and the spine disagree or the skill is silent: the six patterns in RUB-01, the trace share link (REC-02), the image contents (REC-01), the synthetic flag in memory (REC-04) and the memory user ID across environments (RUB-22).
