---
status: draft
stepsCompleted: [1, 2]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/reviews/triage-medium-low.md
  - data/README.md
  - _bmad-output/planning-artifacts/ux-designs/ux-agents-in-context-toronto-2026-11-13/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-agents-in-context-toronto-2026-11-13/EXPERIENCE.md
---

# DxProvida (DxP) - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for DxProvida (DxP), decomposing the requirements from the PRD and the architecture spine into implementable stories. The UX is in `ux-designs/ux-agents-in-context-toronto-2026-11-13/` (`DESIGN.md` for the look, `EXPERIENCE.md` for behaviour); WEB stories build to it. Build day is Saturday 14 November 2026: two developers driving AI coding agents, about six hours of coding, submission at 18:00. Every story carries story points so the team can set the cut line afterwards.

## Requirements Inventory

### Functional Requirements

In scope for Saturday:

- FR1: The system scans every approved Source type on a schedule and on demand, with nobody logged in.
- FR2: The system accepts Findings only from approved Source types, and labels a Diagnostic at discovery or assay development as Early research wherever it appears; a Diagnostic with no stage evidence shows "stage not determined".
- FR3: The system attaches a Finding to the existing Diagnostic when the match key matches and creates a new one only when none does; parallel processing or a re-run never creates a duplicate.
- FR4: The system processes a batch of 300 to 500 Source items in parallel and shows a live count of processed, failed and Early research items.
- FR5: The system fills each Record field from a Finding in a fixed format, with a supporting quote for every field.
- FR7: The system never displays a field value without Evidence.
- FR8: The system shows "no data for this indication" where nothing is published, distinguishable from a cell that is loading.
- FR9: The system maps terms to standard names and finds a Diagnostic by any synonym ("liquid biopsy" returns ctDNA Diagnostics); unmatched terms go to the Reviewer.
- FR11: The system assigns each Diagnostic one Lifecycle stage, with Evidence, and keeps every earlier stage and its date.
- FR12: A Team receives one first Alert for a matching Diagnostic at whatever Lifecycle stage it is at, labelled Early research where it applies.
- FR13: After the first Alert, a Team is alerted again only when the Diagnostic advances a Lifecycle stage, is adopted for a line of therapy, is used in a trial or becomes standard of care, decided semantically.
- FR14: Each Alert states in one line why it matters to that Team and links to the Evidence; an Alert can carry an audio briefing.
- FR15: For a Finding about a tracked Diagnostic, the system drafts a field-level Proposed change with current value, new value and Evidence; list fields add entries and never overwrite.
- FR16: A Reviewer can accept, edit or reject each Proposed change; values in a new Record are marked unreviewed until accepted; Lifecycle stage changes only through an accepted change.
- FR17: The system keeps every previous value with its Evidence, who decided and when.
- FR18: Each extracted field carries a confidence score and an automated check that its quote appears word for word in its Source item; failing values are not displayed; low confidence is marked.
- FR19: A rejection or edit carries a reason; the system drafts a plain-language Learned rule, applies it once confirmed, flags later and pending Proposed changes that break it, and lets the Reviewer switch it off.
- FR20: The system produces a Digest of Proposed changes and Alerts; a Team with nothing applicable gets none.
- FR21: A user describes an Intended use in plain language or with filters on the agreed fields; the parsed query is shown and can be corrected.
- FR22: The system returns a comparison table, one row per Diagnostic and one column per criterion, with Evidence inline.
- FR24: The user saves a Shortlist against a named Intended use.
- FR25: The system exports the comparison or Shortlist with every reference intact.
- FR26: The Graph view shows Diagnostics, biomarkers, tumour types, trials, drugs and Providers as nodes with their links, including links across Categories; selecting a node opens its Record or Evidence.
- FR27: The Graph view marks nodes and links new or changed since the user's last visit, and each Diagnostic's Lifecycle stage.
- FR28: The system keeps the Team profile across sessions and on return shows what changed and offers the last Intended use and Shortlist.
- FR29: A user selects a Category and sees every Diagnostic's full field set with thin, stale or incomplete Records marked; a value added by hand is saved for everyone, marked manually sourced.
- FR30: The first ingest is a Baseline load that sends no Alerts and leaves out the last four weeks; the Held-back set is ingested afterwards and produces real Proposed changes and Alerts.

Later development, not built on Saturday: FR6 (performance by tumour type and stage), FR10 (operational fields), FR23 (operational filters). Capture on the go (PRD §4.9, UJ-4) has no numbered requirement and is P3.

### NonFunctional Requirements

- NFR1: Provenance. No value is shown without Evidence; a quote must appear word for word in its Source item.
- NFR2: Human decision. Every agent change to an existing Record is a logged Reviewer decision.
- NFR3: Unattended operation. Scans, the Maturity gate and Proposed changes run with nobody logged in.
- NFR4: Open data only. Every Source item is openly available; provider websites only from an allow-list; PubMed abstract text is never returned by the API, committed to the repository or shown in a shared trace.
- NFR5: Real behaviour on camera. One memory write and read and one Learned rule are made live in the video.
- NFR6: Synthetic data. Synthetic Team profiles, history, corrections and rules are labelled synthetic wherever they appear.
- NFR7: Event rules. Pre-made data and code are disclosed; the demo says what was built on the day.
- NFR8: Time. Six hours of coding by two people; submission of description, public repository and a three-minute video at 18:00.
- NFR9: Model limits. The batch stays within the Claude API rate limit: at most 16 concurrent calls in an ingest job.
- NFR10: MongoDB as the advantage. The video and description name which MongoDB capability powers which behaviour.
- NFR11: Attribution. Every Evidence shows its source and that source's data date; the app footer carries the credits line.

### Additional Requirements

From the architecture spine (AD-1 to AD-16). No starter template is mandated; the spine fixes a two-folder repository, `backend/` (Python 3.13, FastAPI on Modal) and `web/` (Next.js 16, App Router).

- Foundation: one MongoDB client in `store`, database named by `DXP_DB`, `store.ensure_indexes()`; the field registry in `schema/registry.py` with `registry.canonical()`; `identity.derive()` and `identity.normalise_name()`; `evidence.quote_in_source()`; all Claude calls through `llm` with `langchain-anthropic`, JSON-schema structured output, no sampling parameters.
- Ledger as the single writer of Records (AD-1): `ensure_diagnostic`, `file`, `apply` (claim, then one update writing the value entry, `rev`, `search_text`, `facets`, edges), `review_value`, `seed`.
- Value-entry shape and canonical forms per field (AD-2); derived IDs and insert-if-absent writes (AD-3); stage order enforced at apply (AD-5).
- Ingest modes `baseline` and `live` on every job, Proposed change and event (AD-4).
- Evidence check before filing and one read model for every endpoint (AD-6).
- Learned rules in a `rules` collection, evaluated in one place, flag only, switchable off (AD-7).
- Memory adapter with `agent_engine` and `collections` backends chosen by `DXP_MEMORY_BACKEND`; memory user ID `<DXP_DB>:<team_id>` (AD-8).
- The web app calls only the API; long work is a job (AD-9, AD-16).
- Events outbox with integer `seq`, `GET /changes` feed, alerts reacting once per ledger call (AD-10).
- One LangGraph run per job, `Send` fan-out, `max_concurrency` 16, per-item error capture (AD-12).
- Graph node IDs `<type>:<value>` and an `edges` collection maintained by the ledger (AD-13).
- API contract: the route table and wire shapes in AD-14; web types generated with `openapi-typescript`.
- `search_text` and `facets` written by the ledger; Vector Search with Automated Embedding on `search_text`; synonym documents in `terms` (AD-15, AD-8).
- Source items loaded from a laptop with `window` and `sets`; one job at a time; resumable through `processed_at`; Modal timeout 3600 s; PubMed jobs untraced (AD-16).
- Seed Diagnostics from `data/fda/assays.json` via `normalise_name`; seed a curated liquid biopsy to ctDNA synonym, since public vocabularies do not link them.
- Environments: per-developer `DXP_DB`, production `dxp`; Vercel production URL for judges.
- Friday setup (before the build, not story work): M10 cluster with storage auto-scaling, temporary open network entry, Agent Memory `apply --wait` test, Claude tier check, LangSmith workspace variables, paid HeyGen and ElevenLabs plans.
- Demo retake: `mongodump` after the Baseline jobs and restore by `delete_many` plus `mongorestore`.
- Saturday data: seed 76 FDA lung rows; Baseline jobs over 293 trials and 150 abstracts; live jobs over 40 trials (traced) and 24 abstracts (untraced).

### UX Design Requirements

No UX design document exists. UI behaviour comes from the PRD journeys and the architecture's API contract.

### FR Coverage Map

FR1: Epic 1 - Scheduled and on-demand scans of approved sources, unattended
FR2: Epic 1 - Approved sources only; Early research label; "stage not determined"
FR3: Epic 1 - Match key attaches Findings; no duplicates under parallel runs or re-runs
FR4: Epic 1 - Parallel batch of 300 to 500 items with a live processed, failed and Early research count
FR5: Epic 1 - Fixed-format field extraction with a supporting quote per field
FR7: Epic 1 - No value displayed without Evidence
FR8: Epic 1 - "No data for this indication", distinct from loading
FR9: Epic 4 - Synonym mapping and search; unmatched terms to the Reviewer
FR11: Epic 1 - One Lifecycle stage with Evidence and stage history
FR12: Epic 3 - One first Alert per matching Diagnostic at any stage
FR13: Epic 3 - Update Alerts on stage advance, line-of-therapy adoption, trial use, standard of care
FR14: Epic 3 - One-line "why it matters" with Evidence link; optional audio briefing
FR15: Epic 2 - Field-level Proposed changes for tracked Diagnostics; list fields add, never overwrite
FR16: Epic 2 - Accept, edit or reject; unreviewed marking; stage changes only through accepted changes
FR17: Epic 2 - Every previous value kept with Evidence, decider and time
FR18: Epic 1 - Confidence score and word-for-word quote check; failing values hidden
FR19: Epic 2 - Reasons, drafted Learned rules, flagging, off switch
FR20: Epic 3 - Digest of Proposed changes and Alerts; none when nothing applies
FR21: Epic 4 - Intended use in plain language or filters; parsed query shown and correctable
FR22: Epic 4 - Comparison table with Evidence inline
FR24: Epic 4 - Shortlist saved against a named Intended use
FR25: Epic 4 - Export with references intact
FR26: Epic 5 - Graph view with cross-Category links; node opens Record or Evidence
FR27: Epic 5 - New or changed since last visit marked; Lifecycle stage per Diagnostic
FR28: Epic 6 - Team profile across sessions; what changed; last Intended use and Shortlist
FR29: Epic 4 - Category gap view; manual values saved for everyone, marked manually sourced
FR30: Epic 1 - Baseline load with no Alerts and the last four weeks held back; live mode for the Held-back set

Later development, not mapped: FR6, FR10, FR23. Capture on the go (PRD section 4.9) maps to Epic 7.

## Epic List

Eight epics. Epic 1 is the foundation; Epics 2, 3, 4 and 5 depend only on Epic 1 and can run in parallel; Epic 6 also needs Epics 3 (team profiles in use) and 4 (Shortlist); Epic 7 needs Epic 1; Epic 8's deploy skeleton starts in hour one and is redeployed throughout. Every story is tagged **[API]** (backend and pipeline developer) or **[WEB]** (web developer). Ledger changes are confined to named [API] stories so two agents never edit `ledger.py` at once.

Changes applied from Advanced Elicitation (pre-mortem, cascading failure, war room, persona focus group, assumption audit):

- C1: live ingest mode moved into Epic 1, so Epics 2 and 3 do not depend on each other.
- C2: Epic 1 opens with seeding the 76 FDA rows and the synthetic Team profiles, and an API stub with generated types, so both developers have real data and a contract in hour one.
- C3: Epic 2 opens with a dry run matching the Held-back set against the Baseline to pick demo items early.
- C4: the Category gap view (FR29) folded into Epic 4; capture on the go kept as Epic 7 and pointed.
- C6: Epic 8 split into an early deploy skeleton and the final video and submission.
- C7: every story tagged [API] or [WEB]; ledger edits confined to named stories.
- C8: build risks recorded below.

### Epic 1: Evidence-backed records from real data
The team loads real trials, abstracts and FDA rows into Diagnostic Records where every value carries a word-for-word quote, a Lifecycle stage and an Early research label where it applies; anyone can watch the agents work through a batch with a live count and open a Record to see each value with its Evidence. The same job runs in Baseline mode (no Alerts) and live mode (Held-back set).
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR7, FR8, FR11, FR18, FR30

### Epic 2: Agents propose, the Reviewer decides, guardrails learn
When new evidence arrives about a tracked Diagnostic, the agents draft field-level Proposed changes; a Reviewer accepts, edits or rejects each with a reason, the system drafts a Learned rule from the rejection, applies it once confirmed to flag other proposals, and lets the Reviewer switch it off. Every earlier value stays in the history.
**FRs covered:** FR15, FR16, FR17, FR19

### Epic 3: Teams get told what matters
Each Team gets a first Alert for a matching Diagnostic at any stage, then update Alerts only for meaningful moves (stage advance, line-of-therapy adoption, trial use, standard of care), each with a one-line reason and Evidence link, an optional audio briefing and an in-app Digest.
**FRs covered:** FR12, FR13, FR14, FR20

### Epic 4: Find, compare and fill gaps
A user describes an Intended use in plain words or filters, corrects the parsed query, finds Diagnostics by any synonym, compares them in a table with Evidence inline, saves and exports a Shortlist, and sees a Category's thin Records and fills a value by hand.
**FRs covered:** FR9, FR21, FR22, FR24, FR25, FR29

### Epic 5: See the connections
A user explores Diagnostics, biomarkers, tumour types, trials, drugs and Providers as a connected graph with links across Categories, sees each Diagnostic's stage and what changed since the last visit, and clicks through to Records and Evidence.
**FRs covered:** FR26, FR27

### Epic 6: Pick up where you left off
A returning Team sees what changed since its last visit, a resume summary from memory, and its last Intended use and Shortlist, kept across sessions in MongoDB Atlas Agent Memory (or the collections fallback).
**FRs covered:** FR28

### Epic 7: Capture on the go (P3)
A user types a Diagnostic name or a note and DxP turns it into a partial Record for the agents to fill.
**FRs covered:** none numbered (PRD section 4.9, UJ-4)

### Epic 8: Ship it to the judges
A judge opens a working production URL at any point in the day, and at 18:00 receives the description, the public repository and a three-minute video that names which MongoDB capability powers which behaviour, with disclosure and credits.
**FRs covered:** none; NFR5, NFR7, NFR8, NFR10, NFR11

### Build risks

| Assumption | Confidence | Impact | Settled by |
|---|---|---|---|
| Baseline of 443 items finishes in under an hour at 16 concurrent calls | Medium | High | Friday check 2 (50 items); otherwise run 100 first |
| Held-back items hit tracked Diagnostics, so Proposed changes appear | Medium | High | Story 2.1 dry run |
| Agent Memory works on the day | Medium | Medium | Friday test; fallback `DXP_MEMORY_BACKEND=collections` |
| Vector index READY | High after Friday | Medium | Friday check 4; fallback text search |
| Graph has cross-Category links | High | High | FDA rows share biomarkers across tissue and plasma tests |
| Both developers productive from hour one | Medium | High | Story 1.1 contract stub and seed data |

## Story points

1 point is about 30 minutes of one developer driving an AI coding agent. Two developers coding until 18:00 (about seven hours each) is about 28 points; plan on about 24 after merges, redeploys and debugging. Points use 1, 2, 3, 5. **Cut candidate** marks a story the team can drop without breaking the stories after it; nothing is cut in this document.

## How every story lands: PR and merge

A story is done only when it is merged into `main` and working in production. Every story with points follows these steps:

1. Branch from the latest `main` as `story/<n.n>-<short-name>` (for example `story/2.4-review-screen`).
2. Open a pull request into `main` titled `Story <n.n>: <story title>`, listing the acceptance criteria as a checklist.
3. The CI checks from Story 8.1 pass: the web app's type check and build, and the backend tests.
4. The other developer (or their agent) reads the diff. They check that no secret, `.env` value or PubMed abstract text is in it, and that each acceptance criterion is met.
5. Squash-merge and delete the branch. If an API model changed, rebase first and regenerate `web/lib/types.ts`, so the two lanes never merge conflicting types.
6. After the merge, check production. Vercel deploys `main` itself; the person named in the README runs `modal deploy` for API changes.

Each pull request costs about 10 minutes: opening it, waiting for checks, the review and the merge. This time is not inside the story points. It is counted once, in the capacity: about 14 merged stories in a day is about 2.5 hours, which is most of the gap between the 28 points of capacity and the 24 to plan on. Merge small and often; never hold a story back to merge at the end of the day.

## Epic 1: Evidence-backed records from real data

The team loads real trials, abstracts and FDA rows into Diagnostic Records where every value carries a word-for-word quote, a Lifecycle stage and an Early research label where it applies; anyone can watch the agents work through a batch with a live count and open a Record to see each value with its Evidence. The same job runs in Baseline mode (no Alerts) and live mode (Held-back set).

### Story 1.1: API contract stub, read model and change feed

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** AD-6, AD-9, AD-10, AD-14 · **Demo path**

As the web developer,
I want the API's routes and response shapes running and published as generated TypeScript types in the first hour,
So that I can build pages against the real contract while the pipeline is still being written.

**Acceptance Criteria:**

**Given** `backend/dxp/api/models.py` holds Pydantic classes for Record, Value, Proposal, Rule, Alert, Event, Job, Node, Link and Team exactly as AD-14
**When** the API runs under `modal serve`
**Then** `GET /api/v1/schema`, `GET /api/v1/diagnostics` and `GET /api/v1/diagnostics/<dx_id>` respond with those shapes (empty lists are fine)
**And** `/openapi.json` lists every route in the AD-14 table, unimplemented ones returning `{ error: { code: "not_implemented", message } }` with 501
**And** `web/lib/types.ts` is generated from it with `openapi-typescript` by one npm script and committed
**And** `store` is the only module that creates a MongoDB client, reading `MONGODB_URI` and `DXP_DB`, and `store.ensure_indexes()` runs at startup
**And** `GET /diagnostics` and `GET /diagnostics/<dx_id>` are built by `search.readmodel`, which returns only entries that passed the check or are `manual`, sets `no_data` on an empty field, attaches the source name and `data_as_of`, and passes `synthetic` through
**And** `GET /changes?after=<seq>` returns events from `events` with a higher `seq` and the `last_seq`, by plain polling; the 25-second long-poll with a change-stream wake-up is optional
**And** no secret is in the repository.

### Story 1.2: FDA-authorised lung diagnostics and synthetic Teams seeded through the ledger

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** FR3, FR11, NFR6, AD-1, AD-2, AD-3, AD-5, AD-13, AD-15 · **Demo path**

As a Director of Diagnostics,
I want the FDA-authorised lung companion diagnostics already in DxP, each at regulatory approval with the FDA list as Evidence,
So that DxP starts from a trusted base and the other developer has real Records to show in hour one.

**Acceptance Criteria:**

**Given** `schema/registry.py` defines the ten fields, their cardinality, enums, stage order and confidence threshold, `registry.canonical()` and `registry.is_early_research()`
**And** `identity.derive()` and `identity.normalise_name()` behave as AD-3
**When** `ledger.seed()` runs over `data/fda/assays.json` and the 76 lung rows
**Then** each assay becomes one Diagnostic found through `aliases`, with every `name_strings_in_list` entry as an alias, values filed through `ledger.file()` in `baseline` mode and applied as `unreviewed`
**And** `registry.canonical()` maps biomarkers to HGNC approved symbols from `data/vocab/hgnc_genes.jsonl`, tumour types to OncoTree codes from `data/vocab/oncotree_lung.json`, and every other field to the enum values taken from the PRD's field list
**And** each has `lifecycle_stage: regulatory_approval` by rule, with no model call, and Evidence citing the FDA list and its data date
**And** each apply writes the value entry, `rev`, `search_text`, `facets` and `edges` in one update
**And** running the seed twice creates no new document and changes no existing one
**And** three synthetic Teams with profiles on modality, biomarker and linked drug are inserted into `teams` with `synthetic: true`, and `GET /teams` returns them
**And** the curated synonym "liquid biopsy" to ctDNA is inserted into `terms` with `curated: true` as a valid synonym document.

### Story 1.3: Browse diagnostics and open a Record with its Evidence

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [WEB] · **Covers:** FR2, FR7, FR8, NFR1, NFR11, AD-6, AD-9 · **Demo path**

As a Director of Diagnostics,
I want to list the diagnostics DxP tracks and open one to see every value with its quote, source and data date,
So that I can trust each value without leaving the page.

**Acceptance Criteria:**

**Given** the Next.js 16 app calls the API only through `web/lib/api.ts` using the generated types
**When** I open the diagnostics page
**Then** I see each Diagnostic's name, Lifecycle stage and an Early research label where `early_research` is true, or "stage not determined"
**When** I open a Record
**Then** each field shows its values with the quote, source name, link and data date, and unreviewed values are marked unreviewed
**And** an empty field shows "no data for this indication", visibly different from the loading state
**And** the page renders only what the API's read model returns, applying no display rule of its own
**And** the footer carries the credits line from `dxp-open-data-sources/references/terms.md`
**And** the header has a "your name" picker, kept in the browser, whose value every later changing request sends as `actor`
**And** one server-side Next.js route forwards requests that need `X-DxP-Key` (jobs and every model-calling route), so the key never reaches the browser.

### Story 1.4: Load the downloaded Source items into MongoDB

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [API] · **Covers:** FR30, NFR4, AD-16 · **Demo path**

As the team,
I want the files under `data/` loaded into `source_items` with their window and subset names,
So that jobs on Modal can read them without the laptop.

**Acceptance Criteria:**

**Given** the files and manifests under `data/`, including the git-ignored PubMed `.jsonl` on the laptop
**When** `python -m dxp.sources.load` runs
**Then** every item is upserted with `_id` = `<source>:<source_item_id>`, `window` (`baseline` or `heldback`) and `sets` taken from the manifest ID lists, never from a date comparison
**And** running it twice changes nothing, and never overwrites the `raw_text` of an item that Evidence points at
**And** each item carries its `source_date`, which becomes `evidence.source_date` and the "data as of" date on screen: a trial's `last_update_posted`, a PubMed item's publication date, and the FDA list's download date
**And** the counts it prints match the manifests
**And** a missing PubMed `.jsonl` (a laptop without it) is skipped with a warning, not an error.

### Story 1.5: Extract a Finding from one Source item with a quote for every field

**Points:** 5 · **Time:** ~2.5 h · **Lane:** [API] · **Covers:** FR2, FR5, FR18, NFR4, NFR9, AD-6, AD-11 · **Demo path**

As a Director of Diagnostics,
I want the agents to read a trial or abstract and pull out the ten fields, each with a word-for-word quote and a confidence,
So that nothing reaches a Record without evidence I can check.

**Acceptance Criteria:**

**Given** `llm` is the only module calling Claude, through `langchain-anthropic` with JSON-schema structured output and no sampling parameters
**When** an item is processed
**Then** a triage call on `claude-haiku-5-5` decides whether it concerns a lung cancer diagnostic, and only relevant items go to extraction on `claude-sonnet-5-5`
**And** an item rejected at triage counts as done, not failed, and yields no Finding
**And** one item can name several diagnostics, so extraction returns one Finding per Diagnostic it names
**And** extraction returns, per field, the raw value, a quote of at most 300 characters and a confidence, plus at most one `stage_evidence` and the update triggers `line_of_therapy`, `used_in_trial` and `standard_of_care` where the text supports them
**And** `evidence.quote_in_source()` sets `quote_found`; a check call on `claude-sonnet-5-5` sets `supported` (the quote backs the value), which roughly doubles the model calls per relevant item; a value passes only when `quote_found` and `supported` are both true; a failing value is recorded on the Finding and goes no further
**And** values are canonicalised with `registry.canonical()`
**And** rate-limit and overload errors back off and retry inside `llm`
**And** a model error or refusal returns a failure record and does not raise, and the failure line carries no source text
**And** running it on five baseline trials from the command line prints the Findings, with no PubMed text written to any file.

### Story 1.6: The ledger files Findings without duplicates and keeps the stage moving forward

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** FR3, FR11, FR30, AD-1, AD-3, AD-4, AD-5, AD-10, AD-13 · **Demo path**

As a Director of Diagnostics,
I want each new piece of evidence attached to the right Diagnostic, a new Diagnostic created only when none matches, and the stage only ever advancing,
So that parallel agents never produce duplicates or move a diagnostic backwards.

**Acceptance Criteria:**

**Given** a Finding from Story 1.5
**When** `ledger.file(finding_id, changes, mode)` runs
**Then** `ensure_diagnostic` matches on `aliases` (or the alias `approach:<modality>:<biomarker>` when no assay is named) and creates a Diagnostic only on a miss, treating a duplicate-key error as "exists"
**And** Findings and Proposed changes are insert-if-absent with IDs from `identity.derive`
**And** in `baseline` mode every change is applied as `unreviewed`; in `live` mode changes are applied only on a Diagnostic created by this run, and wait as `pending` otherwise
**And** a change equal to a `current` value is not filed; a `single` field with a `current` value keeps the new value `pending`
**And** a `lifecycle_stage` change that is not later than the stored stage is never filed; one that is later is applied only when the stored stage is still earlier, and sets the `stage_advance` trigger
**And** `store.emit_event()` writes events with an integer `seq` and a unique `dedupe_key`
**And** filing the same Finding twice, or two Findings for the same Diagnostic at once, leaves one Diagnostic and no duplicate value.

### Story 1.7: Run a batch of Source items in parallel as one job

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** FR1, FR4, FR30, NFR3, NFR9, AD-12, AD-16 · **Demo path**

As the team,
I want to start a job over a named set and have the agents process it in parallel, unattended, resuming where it stopped,
So that 300 to 500 items are processed without anyone watching and without exceeding the rate limit.

**Acceptance Criteria:**

**Given** `POST /api/v1/jobs { mode, source, set, limit?, actor }` with the `X-DxP-Key` header, where `limit` takes the most recent N items of the set
**When** no job is running
**Then** the API starts the job with `.spawn()` on the job function passed to `api.create_app()`, with a 3600-second Modal timeout, and returns the `Job`
**And** while one is running it returns 409
**And** the job is one LangGraph run fanning out with `Send` at `max_concurrency` 16; each item node catches its own error and returns a failure record
**And** `jobs` holds `counts { total, done, failed, early_research, filed }` (`filed` = Proposed changes filed), `actor`, `started_at`, `finished_at`, one failure line per failed item, and `active`: the `source_ref` and step (triage, extract or check) of each item in progress, added when it starts and removed when it ends; all readable at `GET /jobs/<job_id>`
**And** `processed_at` is set per filed item, so starting the same job again skips finished items
**And** a `pubmed` job runs with tracing off; a `clinicaltrials.gov` job is traced in LangSmith
**And** a job with no progress for 10 minutes counts as stalled: `POST /jobs` treats it as not running, so the same job can be started again and resumes
**And** a 50-item run with one forced failure finishes with 49 done and 1 failed.

### Story 1.8: Watch the agents work through a batch

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR4, NFR5 · **Demo path**

As a judge watching the demo,
I want a job page with a live count of processed, failed and Early research items,
So that I can see the agents working in parallel on real data.

**Acceptance Criteria:**

**Given** the job page
**When** a user starts a job by choosing mode, source and set
**Then** the request goes through server-side Next.js code that adds `X-DxP-Key`, which never reaches the browser
**And** the page polls `GET /jobs/<job_id>` and updates the processed, failed and Early research counts and a progress bar
**And** failures are listed with their `source_ref` and error
**And** a 409 shows "a job is already running" with a link to it
**And** the list of past jobs shows mode, source, set, status and counts.

### Story 1.9: Run the Saturday Baseline load and save a retake snapshot

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [API] · **Covers:** FR30, AD-4, operations · **Demo path**

As the team,
I want the Baseline loaded into production once, with no Alerts, and a snapshot taken right after,
So that the live demo can be retaken from the same starting point.

**Acceptance Criteria:**

**Given** production (`DXP_DB=dxp`) is seeded (Story 1.2) and loaded (Story 1.4)
**When** the `baseline` jobs run, `clinicaltrials.gov` set `recent_baseline_narrow` (293) and then the 150 most recent `pubmed` items of set `small` in the `baseline` window (never the held-back items), in the deployed app or with `modal run --detach`
**Then** both finish with a failure count under 5 percent, and no Alert exists
**And** re-running either job processes nothing new
**And** `mongodump` of `dxp` is saved outside the repository, and the retake procedure (`delete_many` per collection, then `mongorestore`) is written in the README.

### Story 1.10: Scheduled scan with nobody logged in

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR1, NFR3, AD-16 · **Cut candidate:** the demo uses manual triggers

As a Director of Diagnostics,
I want DxP to check the sources on a schedule without anyone logged in,
So that new evidence arrives without someone remembering to look.

**Acceptance Criteria:**

**Given** the deployed Modal app
**When** the `modal.Cron` schedule fires
**Then** each `sources` adapter's `fetch(since)` adds new Source items for ClinicalTrials.gov and PubMed, and a `live` job starts over them through the same job function
**And** if a job is already running, the scan skips starting one and logs it
**And** a manual "scan now" call runs the same code.

### Story 1.11: Scan allow-listed provider websites through Tavily

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR1, FR2, NFR4 · **Cut candidate:** the Saturday data has no web sources

As a Director of Diagnostics,
I want DxP to pick up announcements from diagnostic providers' own websites,
So that a new assay or approval is noticed even before a paper or trial lists it.

**Acceptance Criteria:**

**Given** an allow-list of provider domains in config
**When** the provider adapter's `fetch(since)` runs
**Then** it searches with Tavily restricted to `include_domains` from the allow-list and `start_date`, and stores each result as a Source item with `source: provider_web`, its URL, date and extracted text
**And** no domain outside the allow-list is ever stored
**And** the items go through the same job and checks as every other source.

### Story 1.12: App shell in the DxP design

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** NFR5, NFR11, `DESIGN.md`, `EXPERIENCE.md` Foundation and Information Architecture · **Demo path**

As a judge watching the demo,
I want every page to share one finished look and one navigation,
So that DxP reads as a real product, not a set of pages.

**Acceptance Criteria:**

**Given** the Next.js app with shadcn/ui and Tailwind
**When** any page loads
**Then** the colour, radius and font tokens from `DESIGN.md` are set as CSS variables, and the three fonts load through `next/font/google`
**And** the top bar shows the DxP logo from the UX workspace, the icon navigation in the `EXPERIENCE.md` order, the Review count from `GET /proposals?status=pending` and the Alerts count from `GET /alerts?team_id=`, the Team picker and the "your name" picker
**And** the top bar is the glass panel, and the page background is the tissue field drawn in CSS, with no image file
**And** a shared stage-track component draws nine segments: reached stages solid, Early research stages in the ink tint, future stages hollow, with a tooltip naming each stage
**And** the shared Early research and Synthetic badges match `DESIGN.md`
**And** the API-unreachable toast and the loading skeletons from `EXPERIENCE.md` State Patterns are in place
**And** the pages built before this story (Story 1.3) move into the shell without changing what they show.

## Epic 2: Agents propose, the Reviewer decides, guardrails learn

When new evidence arrives about a tracked Diagnostic, the agents draft field-level Proposed changes; a Reviewer accepts, edits or rejects each with a reason, the system drafts a Learned rule from the rejection, applies it once confirmed to flag other proposals, and lets the Reviewer switch it off. Every earlier value stays in the history.

### Story 2.1: Dry run the Held-back set against the Baseline

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR15, FR30, build risk "Held-back items hit tracked Diagnostics" · **Demo path**

As the team,
I want to know, before the demo, which held-back items will produce Proposed changes on which Diagnostics,
So that we find a matching problem while there is still time to fix it and pick the items to show on camera.

**Acceptance Criteria:**

**Given** the Baseline is loaded in a developer database
**When** a job runs with `mode: dry_run` over the held-back sets
**Then** it triages and extracts as a live job would, matches through `aliases`, and writes nothing to `diagnostics`, `proposals` or `events`
**And** it prints, per item, the matched Diagnostic or "new", and the fields that would become Proposed changes
**And** the team records at least five items that hit tracked Diagnostics, in the README's demo notes.

### Story 2.2: Reviewer queue of Proposed changes

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR15, FR18, AD-4, AD-14 · **Demo path**

As a Reviewer,
I want every pending Proposed change listed with the current value, the new value and its Evidence,
So that I can decide each one without opening the source.

**Acceptance Criteria:**

**Given** a live job has filed `pending` Proposed changes on tracked Diagnostics
**When** I call `GET /api/v1/proposals?status=pending`, optionally with `diagnostic_id=` for one Record's pending changes
**Then** each Proposal carries diagnostic name, field, new value and label, `current_value`, Evidence with source and data date, `check` with confidence and flags, `mode` and `trigger`
**And** low-confidence proposals come first, then proposals flagged by a Learned rule, then the rest
**And** for a `list` field the proposal adds an entry and never replaces one
**And** PubMed `raw_text` never appears in the response; only the quote does.

### Story 2.3: Accept, edit or reject a Proposed change, keeping the history

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR16, FR17, NFR2, AD-1, AD-4 · **Demo path**

As a Reviewer,
I want to accept, edit or reject each change with a reason, and to review unreviewed values on new Records,
So that no agent change reaches a tracked Record without a logged human decision.

**Acceptance Criteria:**

**Given** a `pending` Proposed change
**When** I `POST /proposals/<p_id>/decision` with `accept`, `edit` (with a value) or `reject`, and an `actor`
**Then** `edit` and `reject` without a `reason` return 400, and an edited value outside the field's allowed values returns 400
**And** `accept` and `edit` claim the proposal (`pending` to `applied`) and apply it in one update; a second decision on the same proposal does nothing and returns the current state
**And** the superseded value stays on the Record with its Evidence, `decided_by` and `decided_at`; nothing is deleted
**And** `lifecycle_stage` changes only through this path once a Diagnostic exists
**And** `POST /diagnostics/<dx_id>/values/<value_id>/review` accepts, edits or rejects an `unreviewed` value through `ledger.review_value()`
**And** each decision emits an event.

### Story 2.4: Review screen

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [WEB] · **Covers:** FR15, FR16, FR18, accessibility convention · **Demo path**

As a Reviewer,
I want one screen where I work through pending changes, see current against new with the quote, and decide each with a reason,
So that reviewing a batch takes minutes.

**Acceptance Criteria:**

**Given** the review page
**When** pending proposals exist
**Then** each row shows Diagnostic, field, current value, new value, the quote with source link and data date, confidence (low marked) and any rule flags
**And** Accept, Edit and Reject are buttons reachable and usable by keyboard, with labels; the focused row shows them full size and the other rows as compact buttons
**And** `j` and `k` move between rows, `a` accepts, `e` edits, `r` rejects and `Esc` cancels, and the page lists these keys
**And** Edit and Reject require a reason before they submit
**And** a decided row leaves the queue and the count updates
**And** the actor name chosen in the app is sent with every decision.

### Story 2.5: Value history on the Record page

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [WEB] · **Covers:** FR17

As a Director of Diagnostics,
I want to see every earlier value of a field with its Evidence, who decided and when,
So that I can see how the picture of a diagnostic changed.

**Acceptance Criteria:**

**Given** a Record with superseded or rejected values
**When** I expand a field's history
**Then** each earlier value shows its quote, source, data date, state, `decided_by`, `decided_at` and the reason for an edit or rejection (kept on the value entry by Story 2.3), newest first
**And** the Lifecycle stage shows each earlier stage with its date.

### Story 2.6: Draft, activate and switch off a Learned rule

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** FR19, AD-7, AD-11 · **Demo path**

As a Reviewer,
I want DxP to turn my rejection reason into a plain-language rule, apply it once I confirm, and let me switch it off,
So that the agents stop repeating a mistake I have already corrected.

**Acceptance Criteria:**

**Given** a rejection or edit with a reason
**When** the decision is saved
**Then** `rules.draft()` asks the model for a one-sentence rule and the response carries it as `rule_draft` with `status: draft`
**When** I `POST /rules/<rule_id>/status { status: active }`
**Then** `rules.evaluate()` runs over every `pending` Proposed change for that field and writes `check.flags` with the rule's note, and the pipeline's check filter calls `rules.evaluate()` on every later item
**And** a rule only flags; it never rejects or withdraws a proposal
**When** I set the rule `off`
**Then** its flags are removed from every pending proposal
**And** each status change emits `rule_status_changed`
**And** if drafting fails, the decision is still saved and `rule_draft` is null
**And** `GET /rules` lists every rule
**And** pre-made rules and corrections are inserted with `synthetic: true`.

### Story 2.7: Confirm and manage Learned rules on screen

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR19, NFR5, NFR6 · **Demo path**

As a Reviewer,
I want to see the drafted rule straight after I reject, edit its wording, confirm it, and later switch it off,
So that the learning is visible and under my control.

**Acceptance Criteria:**

**Given** I rejected a proposal with a reason
**When** the response carries a `rule_draft`
**Then** a panel shows the drafted text, editable, with Confirm and Discard
**And** confirming shows which pending proposals the rule now flags
**And** the rules page lists every rule with field, text, status and an on/off switch, with synthetic rules labelled synthetic
**And** the rule panel and the rules page carry the Agent Memory capability tag from `EXPERIENCE.md`
**And** a flagged proposal on the review screen shows the rule's note.

## Epic 3: Teams get told what matters

Each Team gets a first Alert for a matching Diagnostic at any stage, then update Alerts only for meaningful moves (stage advance, line-of-therapy adoption, trial use, standard of care), each with a one-line reason and Evidence link, an optional audio briefing and an in-app Digest.

### Story 3.1: Raise first and update Alerts for matching Teams

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** FR12, FR13, FR14, FR30, AD-10, AD-11 · **Demo path**

As a Director of Diagnostics,
I want one Alert when a diagnostic relevant to my team first appears, at any stage, and another only when it meaningfully moves,
So that I hear about what matters and nothing else.

**Acceptance Criteria:**

**Given** `alerts.react()` runs once at the end of each `ledger` call in `live` mode
**When** a Diagnostic created in `live` mode matches a Team's profile on modality, biomarker or linked drug
**Then** one first Alert is created for that pair, labelled Early research where `registry.is_early_research()` is true
**When** an applied change on a matching Diagnostic carries `stage_advance`, `line_of_therapy`, `used_in_trial` or `standard_of_care`
**Then** one update Alert is created with that trigger
**And** tumour type alone never matches, and Baseline Diagnostics never get a first Alert
**And** Alert IDs come from `identity.derive`, so a retry creates no second Alert
**And** each Alert has a one-line `why` naming the Team's matching interest and the change, written by the model through `llm` with a template fallback
**And** each Alert carries `diagnostic_name`, the current `lifecycle_stage`, `from_stage` for a stage advance, and the Evidence of the value that triggered it (quote, source, link, data date), so the screen needs no second call
**And** a Diagnostic created in this run gets its first Alert only, with no update Alerts from the same run
**And** each Alert emits `alert_created`
**And** `GET /alerts?team_id=` lists a Team's Alerts and `POST /alerts/<alert_id>/dismiss` dismisses one.

### Story 3.2: Alerts inbox for a Team

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR12, FR13, FR14, NFR6 · **Demo path**

As a Director of Diagnostics,
I want to pick my team and see its Alerts with why each matters,
So that I can act on them in one place.

**Acceptance Criteria:**

**Given** the Team picker lists the Teams, with synthetic ones labelled synthetic
**When** I choose a Team
**Then** its Alerts show newest first, with kind (first or update), trigger, the `why` line, an Early research label where it applies, and a link to the Record's Evidence
**And** I can dismiss an Alert
**And** the inbox refreshes from `GET /changes` without a page reload.

### Story 3.3: Digest of Proposed changes and Alerts

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR20

As a Director of Diagnostics,
I want a digest of what changed for my team and what is waiting for review,
So that I can catch up in one view.

**Acceptance Criteria:**

**Given** `GET /api/v1/digest?team_id=`
**When** the Team has undismissed Alerts or pending proposals on Diagnostics that match its profile
**Then** the response lists them, and the web app shows them as a Digest panel on the Home page
**And** a Team with nothing applicable gets an empty digest and the panel says "nothing new".

### Story 3.4: Audio briefing for an Alert

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [API] · **Covers:** FR14 · **Cut candidate:** Alerts work without it

As a Director of Diagnostics,
I want to hear an Alert read aloud,
So that I can catch up while away from a screen.

**Acceptance Criteria:**

**Given** `GET /api/v1/alerts/<alert_id>/audio`
**When** it is called
**Then** ElevenLabs text to speech reads the Diagnostic name, the `why` line and the stage, with ctDNA, MRD, EGFR and NSCLC pronounced correctly
**And** the audio is generated once and cached, so a second call costs nothing
**And** if ElevenLabs fails, the route returns `{ error }` with 503.

### Story 3.5: Play button on an Alert

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [WEB] · **Covers:** FR14 · **Cut candidate:** goes with Story 3.4

As a Director of Diagnostics,
I want a play button on each Alert,
So that the briefing is one click away.

**Acceptance Criteria:**

**Given** an Alert in the inbox
**When** I press play
**Then** the audio streams from the API and plays in the page, with a loading state and an error message if it fails.

## Epic 4: Find, compare and fill gaps

A user describes an Intended use in plain words or filters, corrects the parsed query, finds Diagnostics by any synonym, compares them in a table with Evidence inline, saves and exports a Shortlist, and sees a Category's thin Records and fills a value by hand.

### Story 4.1: Search indexes and synonym expansion

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR9, AD-8, AD-15

As a Director of Diagnostics,
I want "liquid biopsy" to find ctDNA tests and searches to understand meaning, not just words,
So that I find the right diagnostics whatever I call them.

**Acceptance Criteria:**

**Given** `store.ensure_indexes()`
**When** it runs
**Then** a Vector Search index with Automated Embedding exists on `diagnostics.search_text`, and a MongoDB Search index with a synonym mapping over `terms`, and both reach READY
**And** `search.terms` expands a term through `terms`, so "liquid biopsy" returns ctDNA Diagnostics
**And** a term the pipeline cannot match is written to `terms` with `status: unmatched` as a valid synonym document
**And** if the vector index is not READY, search falls back to text search and says so in the response.

### Story 4.2: Plain-language query with a correctable parsed query

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [API] · **Covers:** FR21, FR22, AD-11, AD-15

As a Director of Diagnostics,
I want to type what I need in plain words and see how DxP understood it,
So that I can correct it before trusting the results.

**Acceptance Criteria:**

**Given** `POST /api/v1/query { text, filters, team_id }`
**When** `text` is given
**Then** the model turns it into filters on the agreed fields (registry enum values only), returned as `parsed`
**And** results are filtered on `facets` and ranked by `$vectorSearch` on `search_text`, and returned as `rows` of read-model Records with `columns` from the registry
**When** `filters` are sent without `text`
**Then** no model call is made
**And** a query with no recognisable filters is ranked by meaning only, and no results returns an empty `rows` with the `parsed` query
**And** a typical query returns in under 10 seconds.

### Story 4.3: Comparison table with Evidence inline

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [WEB] · **Covers:** FR8, FR21, FR22, accessibility convention

As a Director of Diagnostics,
I want one row per diagnostic and one column per criterion, with the quote one click away in each cell,
So that I can compare options side by side and check any cell.

**Acceptance Criteria:**

**Given** the find page
**When** I type a query or set filters
**Then** the parsed query shows as editable chips, and changing a chip re-runs the query with filters only
**And** the table shows one row per Diagnostic and one column per criterion, with Lifecycle stage and Early research label
**And** each cell opens its quote, source and data date inline
**And** an empty cell shows "no data for this indication"
**And** the table is usable by keyboard, as the non-visual equivalent of the Graph view
**And** the query box carries the Atlas Vector Search capability tag.

### Story 4.4: Save a Shortlist against an Intended use

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR24, AD-8, AD-14

As a Director of Diagnostics,
I want to save chosen diagnostics as a Shortlist named after what I need them for,
So that I can come back to it and share it.

**Acceptance Criteria:**

**Given** new routes `POST /api/v1/shortlists { team_id, intended_use, query, diagnostic_ids, actor }` and `GET /api/v1/shortlists?team_id=`, added to the contract and the generated types
**When** I save a Shortlist
**Then** it is stored in `shortlists` and the Team's last Intended use is updated in `teams`
**And** the find page has row checkboxes and a "Save shortlist" action with a name field.

### Story 4.5: Export the comparison or Shortlist with references

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [WEB] · **Covers:** FR25, NFR11

As a Director of Diagnostics,
I want to download the table with every reference intact,
So that I can put it in a report.

**Acceptance Criteria:**

**Given** a comparison table or Shortlist on screen
**When** I export
**Then** a CSV downloads with one row per Diagnostic and, per cell, the value, quote, source URL and data date
**And** commas, quotes and line breaks are escaped, and a cell starting with `=`, `+`, `-` or `@` is prefixed with `'` so a spreadsheet does not run it as a formula
**And** the file ends with the credits line
**And** it is built from API data already on the page, with no new data path.

### Story 4.6: Category landscape with thin Records marked

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR29 · **Cut candidate:** judges barely notice it in three minutes

As a Director of Diagnostics,
I want to pick a category and see every diagnostic's full field set with the thin, stale or incomplete ones marked,
So that I know where the evidence is weak.

**Acceptance Criteria:**

**Given** the category page
**When** I pick a modality
**Then** every Diagnostic in it shows all ten fields
**And** a Record with fewer than half its fields filled is marked thin, one whose newest Evidence is over a year old is marked stale, and empty fields show "no data for this indication"
**And** thin, stale and the filled count come from the read model as `completeness { filled, of, thin, stale }` (computed in `search.readmodel`, not in the web app), and the Categories are a map in `schema/registry.py` from a Category name to modality values (for example "Liquid biopsy" = ctDNA NGS, ctDNA PCR and cfDNA NGS).

### Story 4.7: Add a value by hand

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR29, AD-1, AD-6 · **Cut candidate:** goes with Story 4.6

As a Director of Diagnostics,
I want to add a value I know that the sources do not have,
So that everyone sees it, clearly marked as manually sourced.

**Acceptance Criteria:**

**Given** `POST /diagnostics/<dx_id>/values { field, value, note, actor }`
**When** I submit a value
**Then** it is filed through `ledger.file()` with `evidence.manual` and `review: manual`, canonicalised by the registry
**And** the Record shows it marked "manually sourced" with the submitter and note
**And** the category page and the Record page have an "Add value" form that calls it.

### Story 4.8: Unmatched terms list for the Reviewer

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [WEB] · **Covers:** FR9 · **Cut candidate:** listed in `triage-medium-low.md`

As a Reviewer,
I want to see the terms DxP could not map to a standard name,
So that I can spot gaps in the vocabulary.

**Acceptance Criteria:**

**Given** `GET /terms?status=unmatched`
**When** I open the terms page
**Then** each unmatched term shows with the number of times it was seen.

## Epic 5: See the connections

A user explores Diagnostics, biomarkers, tumour types, trials, drugs and Providers as a connected graph with links across Categories, sees each Diagnostic's stage and what changed since the last visit, and clicks through to Records and Evidence.

### Story 5.1: Graph API built from the ledger's edges

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR26, FR27, AD-10, AD-13 · **Demo path**

As the web developer,
I want nodes and links served from `edges`,
So that the Graph view never derives links itself.

**Acceptance Criteria:**

**Given** `GET /api/v1/graph?after=<seq>`
**When** it is called
**Then** it returns nodes with IDs `<type>:<value>`, type, label, Lifecycle stage, Early research and sample type for Diagnostics, and links with kind
**And** nodes and links whose `seq` is above `after` carry `changed: true`
**And** an optional `focus=<node_id>&depth=<n>` returns that node's neighbourhood using `$graphLookup` over `edges`
**And** an optional `team_id=<team_id>` returns the neighbourhood of the Team's profile biomarkers, modalities and drugs, for the Home hero (Story 6.4)
**And** `POST /teams/<team_id>/seen { seq }` stores the Team's `last_seen_seq` and `last_seen_at`, so screens can say "since 12 November"
**And** the seeded FDA data alone produces links that cross categories, such as one biomarker shared by a tissue test and a plasma test.

### Story 5.2: Graph view with click-through

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [WEB] · **Covers:** FR26, NFR5 · **Demo path**

As a judge,
I want to see diagnostics, biomarkers, tumour types, trials, drugs and providers as one connected graph,
So that I see how the evidence links up, not just a list.

**Acceptance Criteria:**

**Given** the graph page using `react-force-graph-2d` loaded with `next/dynamic` and no server rendering
**When** it loads
**Then** each node type has its own colour and its own shape and a legend, Diagnostic nodes show their stage, and Early research nodes are marked
**And** clicking a Diagnostic opens its Record; clicking a trial opens its Evidence
**And** focusing a node shows its neighbourhood
**And** the graph is one component the Home hero reuses (Story 6.4)
**And** the page links to the comparison table with "View as table" and carries the `$graphLookup` capability tag
**And** it renders every node from the Saturday data and stays interactive (drag, zoom, click) without visible stalls.

### Story 5.3: Highlight what changed since the last visit

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** FR27, AD-10 · **Demo path**

As a Director of Diagnostics,
I want new and changed nodes and links highlighted since my last visit, and new ones to appear while I watch,
So that I see what moved without hunting.

**Acceptance Criteria:**

**Given** the chosen Team's `last_seen_seq`
**When** the graph loads
**Then** nodes and links with `changed: true` are highlighted in eosin with the word "New" or "Changed"
**And** the changed nodes and links pulse once together when the view loads or a live job files a change, and never under `prefers-reduced-motion`
**And** the page long-polls `GET /changes` and adds new nodes and links as a live job files them
**And** a "Mark as seen" action calls `POST /teams/<team_id>/seen` and clears the highlight.

## Epic 6: Pick up where you left off

A returning Team sees what changed since its last visit, a resume summary from memory, and its last Intended use and Shortlist, kept across sessions in MongoDB Atlas Agent Memory (or the collections fallback).

### Story 6.1: Memory adapter with two backends

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR19, FR28, NFR5, NFR10, AD-8 · **Demo path**

As the team,
I want one memory interface that runs on Atlas Agent Memory or on plain collections,
So that the demo works whether or not the preview service behaves on the day.

**Acceptance Criteria:**

**Given** `DXP_MEMORY_BACKEND` set to `agent_engine` or `collections`
**When** `remember_episode`, `recall`, `save_rule` or `glossary` is called
**Then** only `backend/dxp/memory` imports the Agent Memory SDK, and both backends pass the same small test
**And** the memory user ID is `<DXP_DB>:<team_id>`, and rule copies use `<DXP_DB>:reviewers`
**And** episodes with a `session_id` starting `synthetic_` come back from `recall` prefixed `[synthetic] `
**And** when a rule first becomes `active` (Story 2.6), one copy is saved with `save_rule`
**And** a memory backend error never fails the request; callers get an empty result and the resume says "memory unavailable".

### Story 6.2: Seed a synthetic past for each Team

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [API] · **Covers:** FR28, NFR6 · **Demo path**

As the team,
I want each synthetic Team to have a short history of past searches, opened Records and dismissals,
So that the resume on camera has something real to recall.

**Acceptance Criteria:**

**Given** the three synthetic Teams
**When** the seed runs
**Then** each gets five to ten episodes written through `remember_episode` with `session_id` starting `synthetic_`, a last Intended use and one Shortlist
**And** running it twice does not duplicate them.

### Story 6.3: Resume summary on return

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR28, AD-8, AD-10 · **Demo path**

As a returning Director of Diagnostics,
I want DxP to tell me what changed since I was last here and what I was working on,
So that I pick up where I left off.

**Acceptance Criteria:**

**Given** `GET /api/v1/teams/<team_id>`
**When** the Team returns
**Then** the response carries a count and short list of events after `last_seen_seq` that matter to the Team, a two-to-three-sentence resume summary written from `recall`, and the last Intended use and Shortlist
**And** searching, opening a Record and dismissing an Alert each write an episode
**And** synthetic recalled text stays labelled synthetic.

### Story 6.4: Home page with the Team's network and the welcome-back panel

**Points:** 3 · **Time:** ~1.5 h · **Lane:** [WEB] · **Covers:** FR27, FR28, NFR5, `DESIGN.md` graph-led hero · **Demo path**

As a returning Director of Diagnostics,
I want the home page to open on my team's network with what changed glowing, and a welcome-back panel beside it,
So that I see what moved and can reopen my last search in one click.

**Acceptance Criteria:**

**Given** I choose a Team
**When** the home page loads
**Then** the dark hero shows the Team's network from `GET /graph?team_id=` (Story 5.1), drawn with the Graph component from Story 5.2, with changed nodes and links in eosin and the one pulse from Story 5.3
**And** clicking a hero node opens the Graph page focused on it
**And** a glass panel over the hero shows the resume summary, what changed since the last visit with links, and buttons to reopen the last Intended use and Shortlist
**And** the panel names the memory backend in use, as the video wording requires, read from `NEXT_PUBLIC_MEMORY_BACKEND` set to match `DXP_MEMORY_BACKEND`
**And** below the hero, the Team's latest Alerts (the Alert item from Story 3.2) and the Digest panel (Story 3.3) sit side by side
**And** if memory is unavailable, the panel still shows what changed and the last Intended use, and says "Memory unavailable right now".

## Epic 7: Capture on the go (P3)

A user types a Diagnostic name or a note and DxP turns it into a partial Record for the agents to fill.

### Story 7.1: Quick capture of a name or note

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** PRD section 4.9, UJ-4 · **Cut candidate:** P3

As a Director of Diagnostics,
I want to type a diagnostic I heard about at a conference and have DxP start a Record,
So that I do not lose it.

**Acceptance Criteria:**

**Given** a capture box in the web app header
**When** I submit a name or a short note
**Then** the model pulls out a name, and `ledger.ensure_diagnostic()` finds or creates the Diagnostic
**And** a new one is a partial Record whose note is a manual value, marked manually sourced
**And** the result links to the Record.

## Epic 8: Ship it to the judges

A judge opens a working production URL at any point in the day, and at 18:00 receives the description, the public repository and a three-minute video that names which MongoDB capability powers which behaviour, with disclosure and credits.

### Story 8.1: Deploy a walking skeleton to production

**Points:** 2 · **Time:** ~1 h · **Lane:** [WEB] · **Covers:** NFR8, environments, PR and merge · **Demo path**

As the team,
I want the API on Modal and the web app on Vercel live in production from the first two hours, and every story merged through a checked pull request,
So that deploy and merge problems surface early, not at 17:00.

**Acceptance Criteria:**

**Given** Stories 1.1 and 1.3 are done
**When** one person runs `modal deploy` with `DXP_DB=dxp` and the web app deploys to Vercel production with `NEXT_PUBLIC_API_URL`
**Then** the production URL shows the seeded diagnostics
**And** CORS allows only the Vercel origins
**And** a GitHub Actions workflow runs on every pull request into `main`: the web app's type check and build, and the backend tests
**And** Vercel builds a preview for each pull request and deploys `main` to production on merge
**And** `main` accepts changes only through a pull request with passing checks, merged by squash
**And** the README says who deploys the API and how, and describes the PR and merge steps above.

### Story 8.2: Rehearse the live run

**Points:** 2 · **Time:** ~1 h · **Lane:** [API] · **Covers:** FR30, NFR5 · **Demo path**

As the team,
I want to run the live demo end to end once before recording, then restore,
So that what we record works the first time.

**Acceptance Criteria:**

**Given** the Baseline snapshot from Story 1.9
**When** the live jobs run, `clinicaltrials.gov` held-back set `narrow` (40, traced) then `pubmed` held-back set `small` (24, untraced)
**Then** Proposed changes and Alerts appear, one is accepted, one is rejected with a reason, and a Learned rule is confirmed and flags another proposal
**And** a memory write and read happens live
**And** the database is restored from the snapshot afterwards with `delete_many` and `mongorestore`.

### Story 8.3: Submission package

**Points:** 1 · **Time:** ~0.5 h · **Lane:** [WEB] · **Covers:** NFR7, NFR10, NFR11 · **Demo path**

As a judge,
I want a README and description that say what was built on the day, what was prepared before, and which MongoDB capability does what,
So that I can judge the work fairly.

**Acceptance Criteria:**

**Given** the public repository
**When** a judge opens the README
**Then** it discloses the pre-made data, scripts, skills and planning documents, lists what was built on Saturday, carries the MongoDB capability table and the credits, and links the production URL and the video.

### Story 8.4: Three-minute demo video

**Points:** 0 (after 18:00, about 30 minutes, both people) · **Lane:** both · **Covers:** NFR5, NFR10 · **Demo path**

As a judge,
I want a three-minute video showing the agents, the review and learning loop, memory and the graph on real data,
So that I see real behaviour, not a mock-up.

**Acceptance Criteria:**

**Given** the HeyGen intro and close clips
**When** the video is recorded
**Then** it shows a live job, a Proposed change decided, a Learned rule created and flagging, a memory write and read, and the graph highlighting what changed
**And** it names the MongoDB capability behind each behaviour, using the agreed memory wording for whichever backend ran
**And** it is under three minutes and recorded after 18:00 in about 30 minutes.

## Route ownership

Every route in the AD-14 table, plus the two Story 4.4 adds, is built by exactly one story.

| Route under `/api/v1` | Story |
|---|---|
| `GET /schema` | 1.1 |
| `GET /diagnostics`, `GET /diagnostics/<dx_id>` | 1.1 |
| `GET /changes` | 1.1 |
| `GET /teams` | 1.2 |
| `POST /jobs`, `GET /jobs`, `GET /jobs/<job_id>` | 1.7 |
| `GET /proposals` | 2.2 |
| `POST /proposals/<p_id>/decision`, `POST /diagnostics/<dx_id>/values/<value_id>/review` | 2.3 |
| `GET /rules`, `POST /rules/<rule_id>/status` | 2.6 |
| `GET /alerts`, `POST /alerts/<alert_id>/dismiss` | 3.1 |
| `GET /digest` | 3.3 |
| `GET /alerts/<alert_id>/audio` | 3.4 |
| `GET /terms` | 4.1 |
| `POST /query` | 4.2 |
| `POST /shortlists`, `GET /shortlists` | 4.4 |
| `POST /diagnostics/<dx_id>/values` | 4.7 |
| `GET /graph` (with `focus` and `team_id`), `POST /teams/<team_id>/seen` | 5.1 |
| `GET /teams/<team_id>` (with resume) | 6.3 |

## Points and time summary

| Epic | Stories | Points | Time | Demo path | Cut candidates |
|---|---|---|---|---|---|
| 1 Evidence-backed records from real data | 12 | 30 | 15 h | 26 pts (13 h) | 4 pts (2 h) |
| 2 Agents propose, the Reviewer decides, guardrails learn | 7 | 15 | 7.5 h | 14 pts (7 h) | 0 pts (0 h) |
| 3 Teams get told what matters | 5 | 9 | 4.5 h | 5 pts (2.5 h) | 2 pts (1 h) |
| 4 Find, compare and fill gaps | 8 | 16 | 8 h | 0 pts (0 h) | 5 pts (2.5 h) |
| 5 See the connections | 3 | 7 | 3.5 h | 7 pts (3.5 h) | 0 pts (0 h) |
| 6 Pick up where you left off | 4 | 8 | 4 h | 8 pts (4 h) | 0 pts (0 h) |
| 7 Capture on the go | 1 | 2 | 1 h | 0 pts (0 h) | 2 pts (1 h) |
| 8 Ship it to the judges | 4 | 5 | 2.5 h | 5 pts (2.5 h) | 0 pts (0 h) |
| **Total** | **44** | **92** | **46 h** | **65 pts (32.5 h)** | **13 pts (6.5 h)** |

| Lane | Points | Time |
|---|---|---|
| [API] | 52 | 26 h |
| [WEB] | 40 | 20 h |

PR and merge, outside the points: about 10 minutes per story. All 43 stories with points would be 43 pull requests, about 7 hours; the 28 Demo path stories with points, about 4.5 hours.

Capacity: the video moved after 18:00, so coding runs to 18:00: two developers for about seven hours is about 28 points (14 developer-hours), about 14 points per lane, or about 24 once PRs and merges are taken out. The full plan is 3.3 times capacity; the Demo path alone is 2.3 times. Story 8.4, the video, is 0 points: it is made after 18:00 in about 30 minutes, outside coding time.

Departures from the architecture spine introduced by these stories, to confirm or reverse when cutting:

- Story 2.1 adds a `dry_run` job mode beside `baseline` and `live` (AD-4); it writes nothing.
- Story 4.4 adds `POST /shortlists` and `GET /shortlists` to the AD-14 route table.
- Fields added to AD-14 shapes so the screens in the UX can be built: `Job` gets `limit`, `actor`, `started_at`, `finished_at`, `counts.filed` and `active` (Story 1.7); `Alert` gets `diagnostic_name`, `lifecycle_stage`, `from_stage` and its Evidence (Story 3.1); graph nodes get `sample_type` (Story 5.1); `GET /graph` takes `team_id` (Story 5.1).
- Story 1.1 serves `GET /changes` by plain polling; the long-poll in AD-10 is optional.
