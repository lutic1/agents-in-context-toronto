---
name: 'Adversarial review of the DxP architecture spine'
type: review
lens: 'pairs of units that obey every AD and still build incompatibly'
reviewed: '../ARCHITECTURE-SPINE.md (draft, 2026-11-13)'
against: '../../../prds/prd-agents-in-context-toronto-2026-11-12/prd.md, sections 3, 4, 6 and 8'
date: '2026-11-13'
---

# Adversarial review — Architecture Spine, DxProvida (DxP)

## Verdict

The spine fixes the write path well (one ledger, one value-entry shape, one gate), but it leaves the three contracts that cross the two developers unwritten: the API surface, the shape of a field `value`, and the event. Two agents can obey all 13 ADs and still produce a web app and a backend that do not fit. 30 findings: 2 critical, 8 high, 12 medium, 8 low.

Not re-argued: LangGraph, the MongoDB review queue, match on normalised name with no auto-merge, stage per Finding, the two modes, lung only, the field list.

## What was checked beyond the spine and the PRD

- `data/fda/assays.json`, `data/fda/*.jsonl`, `data/clinicaltrials/*.jsonl`, `data/pubmed/heldback.jsonl`: the real shape of `source`, `source_item_id` and the seed's name key.
- `.claude/skills/dxp-mongodb-atlas/references/data-model.md` and `graph-and-streams.md`, `dxp-vercel-frontend/references/data-and-table.md`, `graph-view.md`, `live-updates.md`, `dxp-modal/SKILL.md`: the sample contracts the agents will load, because line 23 of the spine sends them there.

## The suspected places

| Suspicion | Result | Finding |
| --- | --- | --- |
| AD-2 and AD-13: `value` of a list field has no shape, yet node IDs come from it | Confirmed | SPN-02 |
| AD-3: Finding ID depends on an undefined Diagnostic ID; approach alias | Confirmed. The hash itself also has no stated function or join | SPN-05, SPN-14 |
| AD-4: "created in this job" under parallel fan-out | Confirmed | SPN-05, SPN-07 |
| AD-1 and AD-7: who changes `check.flags` on a pending Proposed change | Partly. Writing flags on `proposals` is not writing a Record, so AD-1 holds. The owner, the off-switch and the flags copied into value entries are open | SPN-11 |
| AD-10: who assigns `seq` | Dismissed as a two-owner problem: `store.emit_event()` is the single assigner. Confirmed as an ordering problem for the long-poll | SPN-13 |
| AD-10: what `team_ids` means | Confirmed | SPN-06 |
| AD-9: the API surface is not listed | Confirmed, and made worse by the skills | SPN-01, SPN-03 |
| Layer table "may write" against AD-1 and AD-3 | Confirmed in four places | SPN-05, SPN-11, SPN-24 |

---

## Critical

### SPN-01 — The API surface and its shapes are not written anywhere (critical)

- **Concerns:** AD-9, AD-6, AD-13, Conventions "API".
- **Units:** `web/lib/api.ts` and the screens (developer B) against `backend/dxp/api` and `search.readmodel` (developer A).
- **What each builds:** The spine names five routes (`/schema`, `/jobs`, `/jobs/<job_id>`, `/changes`, `/graph`) and no response shape. Everything else is a guess: the table query, a Record, the reviewer queue, the decision, rules, Alerts, Teams, resume, manual entry. The web agent will take its types from `dxp-vercel-frontend/references/data-and-table.md` (`Cell = { state: "value" | "no_data" | "loading", value, evidence: { source_url, source_title, quote }, reviewed }`, `POST /proposals/<id>/review`). The backend agent will serialise the AD-2 entry (`{ value_id, value, state: current | ..., review, evidence: { source_item_id, quote, source_url }, check }`).
- **Collision:** the web reads `cell.state === "value"` and `cell.evidence.source_title`; the API sends `state: "current"` and no `source_title`. The web posts `POST /api/v1/proposals/p_1/review`; the API serves something else. The no-data state (FR-8) has no agreed encoding, so an empty list, `null` and a missing key are all in play. How the Team ID and the Reviewer's name travel (no login) is also unstated, so `decided_by` has no source.
- **Rule to paste (new AD):**

> **AD-14 — One API contract, written first.** `backend/dxp/schema/api.py` holds the Pydantic request and response models for every route. FastAPI serves them at `/api/v1/openapi.json`, and `web/lib/api-types.ts` is generated from that document and never edited by hand. The contract file and one fixture JSON per response are committed before either side builds a screen. The route table below is the whole surface; a route is added to the table before it is built. The Team ID travels as the query parameter `team_id`; the Reviewer travels as the string `reviewer` in the request body.
>
> | Route | Returns |
> | --- | --- |
> | `GET /schema` | registry |
> | `GET /teams`, `GET /teams/{team_id}/resume`, `POST /teams/{team_id}/seen` | Team list, resume summary, nothing |
> | `POST /query/parse`, `POST /table` | parsed query, `{ criteria, rows: [Record] }` |
> | `GET /diagnostics/{diagnostic_id}` | Record |
> | `GET /proposals?status=&field=`, `POST /proposals/{proposal_id}/decision` | `{ items: [Proposal], next }`, Proposal |
> | `POST /diagnostics/{diagnostic_id}/values` | Record (manual value) |
> | `GET /rules`, `POST /rules/{rule_id}/status` | rules, rule |
> | `GET /alerts?team_id=` | `{ items: [Alert], next }` |
> | `GET /graph?team_id=` | Graph |
> | `GET /changes?after=` | `{ items: [Event], next }` |
> | `POST /jobs`, `GET /jobs/{job_id}` | Job |
>
> ```text
> Record   { diagnostic_id, name, kind: assay | approach, early_research, synthetic,
>            fields: { <key>: { state: value | no_data, current: [Entry], history: [Entry] } } }
> Entry    { value_id, value, label, state, review,
>            evidence: { source_item_id, quote, source_url, source_name, source_date },
>            check: { supported, confidence, low_confidence, flags: [ { rule_id, note } ] },
>            proposal_id, decided_by, decided_at }
> Proposal { proposal_id, diagnostic_id, diagnostic_name, field, value, label, current: [Entry],
>            evidence, check, status, reason, decided_by, decided_at }
> Alert    { alert_id, team_id, diagnostic_id, kind: first | update, trigger, why, matched_on,
>            early_research, evidence, at }
> Job      { job_id, kind, mode, status: queued | running | done | failed,
>            total, processed, failed, early_research }
> Graph    { nodes: [ { id, type, label, category, lifecycle_stage, early_research, changed } ],
>            links: [ { source, target, kind, changed } ] }
> ```

The names are a proposal; what matters is that one written copy exists before either side builds a screen.

### SPN-02 — `value` has no shape or canonical form, and four units key on it (critical)

- **Concerns:** AD-2 (entry shape), AD-13 (node IDs), AD-3 ("normalised value" in the Proposed change ID), AD-10 (Team match).
- **Units:** the pipeline's extract filter (decides what `value` is); `ledger` (hashes it, derives `trial:<id>` and `drug:<id>` from it); `alerts` (compares it with a Team profile); the web table and graph (render it, open a node by it).
- **What each builds:** Extraction returns `trials` as `{ nct_id, title, phase }` and `linked_drugs` as the string in the source. The FDA rows hold `"TAGRISSO®"` with generic `osimertinib`; a trial says `osimertinib`. The ledger builds node IDs from whatever arrives. The web renders `value` as a string.
- **Collision:** one Diagnostic gets `drug:TAGRISSO®` and `drug:osimertinib` as two nodes. A Team that follows `osimertinib` matches one and not the other. The table prints `[object Object]` for a trial. The `p_` hash of an object depends on key order, so a re-run files a second Proposed change. The same trial reported by its registration and by an abstract gives two Findings, two `p_` IDs and two `current` entries with one value, because "a `list` field adds an entry and never supersedes on add".
- **Rule to paste (into AD-2):**

> `value` is always a JSON string, for every field. For an enum field it is the registry key. For the fields below it is the canonical key returned by `registry.canonical(field, raw)`, which is the only value normaliser and is what "normalised value" means in AD-3: `biomarkers` the HGNC approved symbol in upper case, or a registry enum key for a marker that is not a gene; `trials` the NCT ID; `linked_drugs` the generic name in lower case, with no trade name; `tumour_types` the OncoTree code; `provider` `identity.normalise_name()` of the Provider name. Free-text fields (`study_results`) hold the text. What a person reads goes in an optional `label` string beside `value`. A node ID is `<type>:<value>` with that string unchanged, and `diagnostic:<Diagnostic ID>`; the registry gives each field its node `type`. Team profiles store the same canonical keys. `ledger.propose()` files nothing and returns `noop` when a `current` entry of that field already has the same `value`.

---

## High

### SPN-03 — The skills carry a different data model and the spine does not say it wins (high)

- **Concerns:** line 23 ("How to use each technology is in the `dxp-*` skills"), AD-2, AD-3, AD-4, AD-10, AD-13, Conventions "IDs".
- **Units:** any agent that loads `dxp-mongodb-atlas` or `dxp-vercel-frontend` (they trigger on `pymongo`, `next`, `EventSource`) against any agent that builds from the spine alone.
- **Collision, each line checked in the skill text:**

| Topic | Spine | Skill sample |
| --- | --- | --- |
| Collections | `proposals`, `edges`, `jobs` | `proposed_changes`, `graph_nodes` and `graph_links`, `batch_runs` |
| Record fields | `fields.<key>` is always a list of entries | `fields.<f>` is one object with `history`; lists under `lists`; `lifecycle` at top level |
| Early research | never stored | `early_research` stored on the Record |
| Identity | `aliases` collection, `_id` is the normalised name | unique `match_key` on `diagnostics`, `name|provider` |
| IDs | strings, never ObjectId | `ObjectId()` |
| Proposed change status | `pending | applied | rejected` | `pending | applying | accepted | edited | rejected` |
| Check keys | `quote_found`, `supported` | `quote_in_source`, `supports_value` |
| Node type | `tumour` | `tumour_type` |
| Link | `{ from, to, kind }` | `{ source, target, relation }` (front end), `rel` (MongoDB) |
| Live feed | long-poll `GET /api/v1/changes?after=<seq>` | server-sent events on `GET /events` |
| Paths | `/api/v1/...` | `/graph`, `/batches`, `/events`, no prefix |

- **Rule to paste (under the title, replacing the last sentence of line 23):**

> How to use each technology is in the `dxp-*` skills. Their sample collections, field names, statuses, routes, ID types and payloads were written before this spine. Where a sample differs from this spine, the spine wins and the sample is adapted. Known differences: collection names, the Record field shape, stored `early_research`, `match_key`, ObjectId, Proposed change statuses, check key names, the `tumour_type` node type, link key names, server-sent events and unprefixed paths.

### SPN-04 — The seed file already holds a name key, made by a different normaliser (high)

- **Concerns:** AD-3 ("`identity.normalise_name` is the only name normaliser"; "Diagnostics are seeded from `data/fda/assays.json`").
- **Units:** the seed loader against `identity.normalise_name` as the pipeline calls it.
- **What each builds:** `assays.json` has a field named `assay_normalised` and states its rule: marks removed, `PD-LI` corrected to `PD-L1`, punctuation removed except `- + / .`, lower case. The seed agent uses it as the alias `_id`. The identity agent writes a general normaliser. The spine gives no algorithm.
- **Collision (run against the file):** with "lower case, every run of non-alphanumerics to one space", 5 of the 20 seed keys differ, for example seed `pd-l1 ihc 22c3 pharmdx` against `pd l1 ihc 22c3 pharmdx`. A held-back trial that names "PD-L1 IHC 22C3 pharmDx" finds no alias, creates a second Diagnostic, and in `live` mode that Diagnostic is "created in this job": its values are applied with no Reviewer and a first Alert goes out for an assay the FDA list already holds.
- **Rule to paste (into AD-3):**

> `identity.normalise_name(s)`: Unicode NFKC; remove `®`, `™`, `(R)` and `(TM)`; lower case; replace every run of characters other than `a-z` and `0-9` with one space; trim. The seed loader calls it on every entry of `name_strings_in_list` and inserts one alias per entry, all pointing at one Diagnostic. `assay_normalised` in the file is never used as a key. `backend/dxp/identity/test_vectors.json` holds the 21 FDA name strings with their expected keys and is the acceptance check for any change to the function.

### SPN-05 — Nobody is allowed to create the `diagnostics` document, and "created in this job" has three readings (high)

- **Concerns:** AD-3, AD-4, layer table, Conventions "IDs" and "Run tracing".
- **Units:** `identity.resolve_diagnostic` (foundation, may write `aliases` only); the pipeline's resolve filter; `ledger.propose()`.
- **What each builds:** AD-3 lists derived IDs for Source item, Finding and Proposed change, not for a Diagnostic, so `dx_` is random or derived at the builder's choice. `identity` inserts the alias but may not write `diagnostics`, and cannot import the ledger. So the document is created by the pipeline (not allowed by the table), by `identity` (not allowed), or lazily by the ledger. "Created in this job" is then read as (a) `resolve_diagnostic` returned `created = true`, (b) `aliases.run_id == job_id`, or (c) `diagnostics.run_id == job_id`, where `run_id` may mean creator or last writer.
- **Collision:** held-back items A and B both name new assay X. A wins the alias insert, B gets the duplicate-key path. Under reading (a), A's values are applied as `unreviewed` and B's wait as `pending`, and which is which changes from run to run. Under (c) with "last writer", a later job that touches the document makes an old Diagnostic look new. Meanwhile B reads the Diagnostic's current stage for AD-5 before any document exists.
- **Rule to paste (into AD-3 and AD-4):**

> A hash in any ID is the first 16 hex characters of SHA-256 over the parts joined with `|`. The Diagnostic ID is derived: `dx_` + hash(the alias key that first created it). `identity.resolve_diagnostic(name)` writes only `aliases` (`{ _id, diagnostic_id }`) and returns the Diagnostic ID. The `diagnostics` document is created by the ledger alone, inside `propose()`, by an upsert with `$setOnInsert { name, kind, created_run_id, created_mode, created_at }`; a reader treats a missing document as a Diagnostic with no values. "Created in this job" means `diagnostics.created_run_id == job_id`, read by the ledger inside `propose()`; the pipeline never passes a "created" flag. `created_run_id` is never overwritten.

### SPN-06 — The event has no `type` values, no meaning for `ref`, `team_ids` or mode (high)

- **Concerns:** AD-10, Conventions "Run tracing".
- **Units:** `ledger` and `rules` (emit); `alerts` (reacts); `api` and the web (serve and read `/changes`).
- **What each builds:** `type` is named in prose only ("applied Proposed change, new Diagnostic, Alert and rule status change"), so each side invents strings. `ref` is a bare ID, or `{ collection, id }`. `team_ids` must be filled at emit time, but Team matching lives in `alerts`, which only runs after the event exists. "In `live` mode" has no field on the event; the convention gives `mode` only to documents "written by a job", and a Reviewer's accept is not a job.
- **Collision:** the Reviewer accepts a `pending` Proposed change. The ledger emits `{ type: "proposal_applied", ref: "p_9", team_ids: [] }` with no `mode`. `alerts` checks `event.mode == "live"` and raises nothing, so no update Alert is ever produced (FR-13). The web switches on `type === "change_applied"` and highlights nothing (FR-27).
- **Rule to paste (into AD-10):**

> Event `type` is one of `diagnostic_created | change_applied | alert_created | rule_status_changed`. `ref` is the ID string of the Diagnostic, Proposed change, Alert or rule; the collection follows from `type`. A `change_applied` event also carries `field`. Every event carries `mode`, copied from the Proposed change's job and not from whoever applied it. `team_ids` is empty except on `alert_created`, where it holds the one Team alerted. An `events` document is never updated.

### SPN-07 — The first Alert has no defined trigger, and nothing makes it single (high)

- **Concerns:** AD-4 ("a first Alert is raised"), AD-10 ("only in reaction to an event"), FR-12 ("exactly one first Alert").
- **Units:** whoever emits the new-Diagnostic event (`identity`, pipeline or `ledger`) against `alerts`.
- **What each builds:** `alerts` reacts to the new-Diagnostic event for first Alerts and to applied changes for update Alerts. The emitter fires the new-Diagnostic event when the alias or document is created.
- **Collision:** at that moment the Diagnostic has no field values, so the match "on modality, biomarker or linked drug" fails and no first Alert is raised; the FR-30 test ("at least one Alert") fails. If `alerts` instead reacts to each applied change, one Finding emits about eight events and parallel items emit more; each handler checks "no Alert yet for this Team" and inserts, and two of them race. `alert_` has no derivation, so both inserts succeed.
- **Rule to paste (into AD-10):**

> `diagnostic_created` is emitted by the ledger when it inserts the `diagnostics` document, and `alerts` ignores it. `alerts` evaluates every `change_applied` event whose `mode` is `live`. If the Diagnostic's `created_mode` is `live` and it matches a Team, `alerts` inserts a first Alert with `_id = alert_ + hash(team_id, diagnostic_id, "first")` and ignores a duplicate-key error. An update Alert has `_id = alert_ + hash(team_id, finding_id, trigger)` and is inserted the same way. A Team therefore gets at most one first Alert per Diagnostic and one Alert per Finding and trigger, in any event order.

### SPN-08 — A value that fails the quote check is still applied, supersedes good values and reaches the Graph view (high)

- **Concerns:** AD-4 ("applies every Proposed change"), AD-6 (gate on the read side), AD-13 (`/graph` is built from `edges`), FR-7, FR-18.
- **Units:** `ledger.apply()` (writes entries and `edges`) against `search.readmodel` (the only gate) and `search.graph`.
- **What each builds:** in `baseline` the ledger applies everything, including an entry with `check.quote_found: false`, and rewrites `edges` from the entries it holds. The read model drops that entry. The graph endpoint reads `edges`, which AD-13 tells it to do.
- **Collision:** a model quote with an ellipsis fails the check. For `regulatory_status` (single) the failed entry becomes `current` and the good one `superseded`; the read model drops `current` and the table shows "no data" for a field that has a cited value. For `trials` the ledger writes `diagnostic:dx_1 → trial:NCT0…`; the table hides the trial and the Graph view shows the link. AD-6's own "Prevents" names this split.
- **Rule to paste (into AD-4, with a cross-reference in AD-6):**

> A Proposed change whose `check.quote_found` is false is never applied, in any mode. `ledger.propose()` stores it with `status: rejected`, `decided_by: system`, `reason: quote_not_found`, and it does not appear in the reviewer queue. `edges` are derived only from entries in `state: current`. The read-side gate in AD-6 stays as the second check.

### SPN-09 — Stage order is checked in the pipeline, before the write, by parallel items (high)

- **Concerns:** AD-5 ("the pipeline proposes ... only when that stage is later than the Diagnostic's current one"), AD-2 ("at most one entry in state `current`"), AD-12 (fan-out).
- **Units:** the pipeline's propose filter (reads the stage, decides) against `ledger.apply()` (writes later, in arrival order), and against the Reviewer's order of decisions.
- **Collision 1, baseline:** items A and B concern one Diagnostic and run together. Both read stage `not_determined`. A proposes `clinical_validation`, B proposes `analytical_validation`. A is applied, then B, and B supersedes A: the stage moves backwards and differs between runs.
- **Collision 2, live:** two `pending` Proposed changes, `clinical_utility` and `regulatory_approval`. The Reviewer accepts the later stage first and the earlier one second. The Record ends at `clinical_utility`.
- **Collision 3, any single field:** two `apply()` calls (two items, or the job and a Reviewer's accept from an API container) both read "no `current` entry" and both append one. The field has two `current` entries.
- **Rule to paste (into AD-5 and AD-2):**

> The ledger, not the pipeline, enforces stage order. `ledger.apply()` on `lifecycle_stage` compares the proposed stage with the `current` entry at apply time; if it is not later, the Proposed change is closed as `rejected` with `decided_by: system`, `reason: not_later_stage`, and no event. Every `ledger.apply()` write is conditional on the Diagnostic's `version` counter and increments it; on a miss it re-reads and retries. The pipeline's comparison in AD-5 only saves work.

### SPN-10 — "Source item ID" means two things, and the `source` names break the enum convention (high)

- **Concerns:** AD-3 (`<source>:<source_item_id>`), AD-2 (`evidence.source_item_id`), AD-6 (quote check against `source_items.raw_text`), Conventions "Enums".
- **Units:** `sources` and the seed loader against `ledger`, `evidence` and `search.readmodel`.
- **What each builds:** the data files carry `source` and `source_item_id` as separate fields: `clinicaltrials.gov` + `NCT05257967`, `pubmed` + `42888302`, `openfda_device_pma` + `P240037/S003`, `fda_cdx_list` + `FDA-CDX:P240040/S005:260295ce75`. AD-3 makes `_id` the pair joined by `:`. AD-2's evidence has a key also called `source_item_id`. The enum convention is lower `snake_case`, which `clinicaltrials.gov` is not; the MongoDB skill writes `clinicaltrials`.
- **Collision:** the pipeline stores `evidence.source_item_id: "NCT05257967"` (the file's field). The read model looks up `source_items` by `_id` to attach the source name and date, finds nothing, and the attribution is missing; a later quote check finds no `raw_text`. The registry agent defines `clinicaltrials_gov`, the adapter passes `clinicaltrials.gov` through, and the same trial gets two `_id` values, two Finding IDs and two sets of Proposed changes. The FDA IDs contain `:` and `/`, so an ID cannot be split back or placed in a URL path.
- **Rule to paste (into AD-3):**

> `source_items._id` is `<source>:<native id>`. `<source>` is exactly the `source` string in `data/` (`clinicaltrials.gov`, `pubmed`, `fda_cdx_list`, `openfda_device_pma`), an agreed exception to the enum convention; `<native id>` is the file's `source_item_id` unchanged, stored as `native_id`. Everywhere else, including `evidence.source_item_id`, `findings` and every hash, "Source item ID" means the full `_id`. It is never split on `:` and never placed in a URL path.

---

## Medium

### SPN-11 — Flags have no owner, no off-switch path, and go stale on applied values (medium)

- **Concerns:** AD-7, AD-1, layer table, dependency diagram.
- **Units:** `rules` against `ledger` and `api`.
- **Collision:** `rules` may not import `ledger` (the arrow runs the other way), so the sweep over `pending` Proposed changes is done by `rules` writing `proposals` itself, or by the API, or not at all. AD-7 sweeps only "when a rule becomes `active`", so switching a rule off leaves the flags and the FR-19 test fails. An accepted value entry copies `check.flags`; AD-1 forbids anyone but `apply()` touching `diagnostics.fields`, so a flag for a rule that is now `off` stays on the Record. AD-7 has the pipeline call `rules.evaluate`, and the diagram has no `pipeline --> rules` or `api --> rules` arrow. The layer table lets `rules` and `alerts` write `diagnostics`, which is wider than AD-1.
- **Rule to paste (into AD-7):**

> Flags on a Proposed change are written only by `ledger.reflag(field)`, which calls `rules.evaluate` for each `pending` Proposed change of that field and replaces its `check.flags`. The API calls it after every rule status change, to `active` or to `off`. `rules` writes only the `rules` collection, and `alerts` only `alerts`. A value entry keeps the flags it had when applied; the read model drops any flag whose rule is not `active`. The diagram gains `pipeline --> rules` and `api --> rules`.

### SPN-12 — A hand-typed value has no ID, no mode, and is dropped by the gate (medium)

- **Concerns:** AD-1 ("values a user types by hand"), AD-2 (`review: manual`), AD-3 (`p_` needs a Finding ID), AD-6, FR-29, FR-7.
- **Units:** the manual-entry route and form against `ledger.propose()` and `search.readmodel`.
- **Collision:** there is no Finding, so `p_` + hash(Finding ID, ...) cannot be computed and `propose(finding, ...)` has nothing to take. There is no quote, so the ledger sets `quote_found: false` and the read model drops the value (the FR-29 test fails), or sets it `true`, which is false. AD-4 covers ingest jobs only, so whether the value waits for a Reviewer is unstated. The gate also keys on `check.quote_found` alone: an entry whose Evidence is removed still shows, which fails the FR-7 test.
- **Rule to paste (into AD-1 and AD-6):**

> A hand-typed value is filed by `ledger.propose_manual(diagnostic_id, field, value, submitter, note, source_url)`. Its ID is `p_` + hash(`manual`, diagnostic_id, field, canonical value, submitter). It has no Finding, `evidence: { source_item_id: null, quote: note, source_url }` and `check: null`, and is applied at once with `review: manual`; its event carries `mode: manual`, which `alerts` ignores. The read-side gate keeps an entry when `review` is `manual`, or when `evidence.quote` is not empty and `check.quote_found` is true. It drops every other entry.

### SPN-13 — `seq` order, the gap between two long-polls, and "last seen" (medium)

- **Concerns:** AD-10, AD-8.
- **Units:** `store.emit_event` (called from the job container and from API containers) against the `/changes` handler and the web client.
- **Collision:** a change stream opened per request sees only inserts made after it opens. An event written between two polls is never delivered unless the handler queries first. With a counter, writer 1 takes `seq` 10 and writer 2 takes 11 and inserts first; a client that has seen 11 asks `after=11` and never gets 10. `teams` "last seen" is a date for one builder and a `seq` for the other; if `GET .../resume` also updates it, a second fetch returns "nothing changed".
- **Rule to paste (into AD-10 and AD-8):**

> `seq` is assigned only inside `store.emit_event()`, by an atomic `$inc` on one counter document. The `/changes` handler first queries `seq > after`; it waits on the change stream only when that query is empty. It returns `{ items, next }`, where `next` is the highest `seq` returned, or `after` when empty; the web passes `next` back unchanged. The web treats an event as a prompt to refetch what it shows, never as the data. `teams.last_seen_seq` is a `seq`, written only by `POST /teams/{team_id}/seen`.

### SPN-14 — The approach alias: normalised or not, which biomarker, and whose Provider (medium)

- **Concerns:** AD-3 (`approach:<modality>:<biomarker or any>`, `[ASSUMPTION]`).
- **Units:** the pipeline's resolve filter (builds the string) against `identity` (owns alias keys), and the read model (needs to tell an approach from an assay).
- **Collision:** if the string goes through `normalise_name`, the colons go and HGNC case is lost; if not, `aliases._id` is no longer always `normalise_name(name)` as AD-3 states. A Finding with EGFR, ALK and KRAS gives `approach:ngs:EGFR` for one builder (first named, which changes between model runs), `approach:ngs:ALK` for another (sorted) and `approach:ngs:any` for a third; a second run then creates a second Diagnostic, against the FR-3 test. Every unnamed EGFR ctDNA study shares one Diagnostic, so `provider` (single) is superseded by each trial sponsor in turn.
- **Rule to paste (into AD-3):**

> The approach key is built only by `identity.approach_key(modality, biomarkers)`: `approach:<modality enum>:<symbol>`, where `<symbol>` is the canonical biomarker when the Finding has exactly one, and `any` otherwise. It is stored as the alias `_id` as built and is not passed through `normalise_name`. Its Diagnostic has `kind: approach`, and the pipeline files no `provider` Proposed change for it.

### SPN-15 — "All writes are upserts" does not say what a second run does to a decided Proposed change (medium)

- **Concerns:** AD-3 ("Prevents ... when a batch ... is retried by Modal, or is run twice").
- **Units:** `ledger.propose()` on a first run against the same function on a retry; the extraction model against the `p_` hash.
- **Collision:** a Reviewer rejects `p_7`. The scan runs again, the same value arrives, and an upsert with `$set` writes `status: pending` again: the rejected change returns to the queue. For free-text fields the model words the value differently on the second run, the hash differs, and a second Proposed change is filed and, in `baseline`, applied as a second list entry. The rule therefore does not prevent its stated duplicate.
- **Rule to paste (into AD-3):**

> `ledger.propose()` writes a Proposed change with `$setOnInsert` only; an existing one is left as it is, whatever its status. A job skips any Source item whose `status` is `done` and whose stored `text_sha256` is unchanged; `status` becomes `done` only after all of that item's Proposed changes are filed. A retry or second run therefore makes no model call for a finished item.

### SPN-16 — There is no path for reviewing an `unreviewed` value (medium)

- **Concerns:** AD-2 (`state: rejected`, `review: accepted`), AD-4 (statuses), FR-16 ("unreviewed until a Reviewer accepts them").
- **Units:** the web review screens against `ledger.decide()`.
- **Collision:** the queue is "a query on `proposals`" for `status: pending`. Values applied in `baseline` or on a new Diagnostic have `status: applied`. The web offers "accept" on an unreviewed value and posts a decision for `p_3`; the ledger's `decide()` accepts only `pending` and returns an error. AD-2 has an entry state `rejected` that no stated path can produce.
- **Rule to paste (into AD-4):**

> A Reviewer decides an `unreviewed` value through the same `ledger.decide()`, using the entry's `proposal_id`. Accept sets `review: accepted`. Edit adds an entry with `review: edited` and supersedes the old one. Reject sets the entry's `state: rejected` and the Proposed change's `status: rejected`; for a `single` field the most recent `superseded` entry becomes `current` again. `decide()` on a Proposed change a person has already decided returns 409. The reviewer queue lists `pending` only; unreviewed values are reached from the Record.

### SPN-17 — A process-wide semaphore does not cover two containers (medium)

- **Concerns:** AD-11 ("one process-wide semaphore of 16"; Prevents "separate code paths together exceeding the rate limit"), AD-9, AD-12, system diagram (`job --> claude`, `api --> claude`).
- **Units:** the job container against the API container, and a manual scan against the scheduled scan.
- **Collision:** the job holds 16 calls; a query parse, a rule draft and a "why it matters" line in the API container make 19. Two `live` jobs at once make 32. The rule cannot prevent what it says it prevents.
- **Rule to paste (into AD-11 and AD-12):**

> The limit is per container: 12 in the job container and 4 in the API, which runs in one container. Only one ingest job runs at a time: `POST /jobs` returns 409 while a `jobs` document has `status: running`, and the scheduled scan skips its turn.

### SPN-18 — "Rewritten for the affected Diagnostic" loses edges under parallel applies (medium)

- **Concerns:** AD-13.
- **Units:** two concurrent `ledger.apply()` calls on one Diagnostic; `search.graph` against the web graph.
- **Collision:** A reads the Record, B writes a new trial and inserts its edge, A deletes all edges of the Diagnostic and inserts the set it read: B's edge is gone. `edges` has no `_id` rule, so two inserts of one link both succeed. `kind` has no values. react-force-graph reads `source` and `target` by default; the store holds `from` and `to`.
- **Rule to paste (into AD-13):**

> An edge is `{ _id: "<from>|<kind>|<to>", from, to, kind }`. `from` is always the `diagnostic:` node and `kind` is the registry field key that produced the link. `ledger.apply()` upserts the edge of an entry that becomes `current` and deletes the edge of an entry that leaves `current`; it never deletes and re-inserts all edges of a Diagnostic. `GET /graph` returns links as `{ source, target, kind }`.

### SPN-19 — `stage_advance` has two sources of truth (medium)

- **Concerns:** AD-5 against AD-10.
- **Units:** the extraction model's trigger label against the pipeline's stage comparison, as read by `alerts`.
- **Collision:** the model labels a Finding `stage_advance`; the pipeline finds the stage is not later and files no change. One `alerts` builder reads the label and sends "stage advanced" for a Record whose stage did not move; another reads the applied `lifecycle_stage` change and sends nothing. The reverse case sends an Alert under one build only.
- **Rule to paste (into AD-10):**

> The extraction model sets only `line_of_therapy | used_in_trial | standard_of_care`. `stage_advance` is never a model output: it is the trigger when a `change_applied` event has `field: lifecycle_stage`.

### SPN-20 — Nobody is told to suppress a Proposed change that repeats the current value (medium)

- **Concerns:** AD-4 ("every Proposed change waits in `proposals`").
- **Units:** the pipeline's propose filter against `ledger.propose()`.
- **Collision:** a held-back trial about a seeded assay repeats `biomarkers: EGFR`, `sample_types: plasma` and five more values the Record already has. If neither unit filters, the 64 held-back items fill the queue with changes that change nothing, and the one real update is hard to find on camera. If both filter, they compare differently (raw string against canonical).
- **Rule to paste:** the last sentence of the SPN-02 rule (`propose()` returns `noop` when a `current` entry has the same `value`), plus: "The pipeline does not pre-filter."

### SPN-21 — The Provider has two homes (medium)

- **Concerns:** AD-3 ("The Provider is stored on the Diagnostic") against the registry field `provider (single)`.
- **Units:** the seed loader and `identity` against `ledger` and `search`.
- **Collision:** the seed writes `diagnostics.provider: "Guardant Health, Inc."` at the top level with no Evidence; the ledger writes `fields.provider[0]` with Evidence. The table reads one, the graph's `provider:` node the other. The top-level copy is a Record value with no Proposed change, against AD-1.
- **Rule to paste (into AD-3):**

> The Provider exists only as the registry field `provider`. The top level of a `diagnostics` document holds `_id, name, kind, version, created_run_id, created_mode, created_at, fields` and nothing else.

### SPN-22 — The memory adapter's signatures, and which Team owns a Learned rule (medium)

- **Concerns:** AD-8 ("The memory user ID is the Team ID") against AD-7 ("Agent Memory receives a copy when a rule is activated").
- **Units:** `rules` and `api` (callers) against `memory` (adapter).
- **Collision:** a rule document has no Team, and a Reviewer is not a Team. `rules` calls `memory.save_rule(rule)`; the adapter, following AD-8, defines `save_rule(team_id, rule)`. The four function names are fixed and their arguments are not.
- **Rule to paste (into AD-8):**

> Signatures: `remember_episode(team_id, session_id, kind, payload)`, `recall(team_id, query, limit)`, `save_rule(rule)`, `glossary()`. Learned rules are global: `save_rule` stores under the fixed memory user `dxp_shared`, not under a Team.

---

## Low

### SPN-23 — AD-9's 20-second rule against AD-10's 25-second long-poll (low)

- **Collision:** a `web/lib/api.ts` built to AD-9 aborts any request at 20 seconds; the handler built to AD-10 holds for 25. Every idle poll ends as a client error.
- **Rule to paste (into AD-10):** "The long-poll waits at most 15 seconds."

### SPN-24 — The diagram is not closed, and the layer table has gaps (low)

- **Concerns:** "Imports point down this diagram only", layer table, AD-5.
- **Collision:** `api` writes `teams` through `store` and there is no `api --> foundation` arrow, so the arrows are not the full list; then nothing says whether `alerts --> search` or `pipeline --> search` is "down". Both need the Early research label (FR-12, FR-4), which AD-5 places in the read model, so each will re-implement it. `store.emit_event` (foundation) writes `events`, which the table gives to the ledger layer. No layer may write `terms` (AD-8). The system diagram has `job --> mem`; the dependency diagram has no `pipeline --> memory`.
- **Rule to paste:**

> Every package may import foundation. Between other packages, only the drawn arrows are allowed. `registry.is_early_research(stage)` is the one implementation, used by the read model, `alerts` and the job counters. `events` is written only through `store.emit_event()`, called by `ledger`, `rules` and `alerts`. `terms` is written only by `memory`.

### SPN-25 — `api` must start a Modal function it may not import (low)

- **Concerns:** AD-9 against "Nothing imports `api` or `modal_app`".
- **Collision:** the jobs route looks the function up by a name the `modal_app.py` builder did not use, or imports `modal_app` and creates a cycle.
- **Rule to paste (into AD-9):** "`modal_app.py` passes a `spawn_job(job_id)` callable to `api.create_app()`. `api` never imports or looks up a Modal function."

### SPN-26 — The audio briefing against "HTTP JSON only" (low)

- **Concerns:** Deferred "Audio briefing", the `web --> api` arrow.
- **Collision:** the web uses `<audio src=".../alerts/<id>/audio">` and expects `audio/mpeg`; the API, holding to JSON only, returns base64 in JSON.
- **Rule to paste (into Deferred):** "`GET /alerts/{alert_id}/audio` returns `audio/mpeg` bytes; it is the one response that is not JSON."

### SPN-27 — The low-confidence mark needs a threshold someone must own (low)

- **Concerns:** AD-6 ("applies no display rule of its own"), FR-18.
- **Collision:** the entry carries `confidence: 0..1`; the web picks 0.7 to draw the mark, which is a display rule.
- **Rule to paste (into AD-6):** "The threshold is in the registry; the read model sets `check.low_confidence`."

### SPN-28 — `propose()` in the sequence diagram takes no `check` (low)

- **Concerns:** "Proposed change lifecycle" diagram against AD-7.
- **Collision:** the pipeline passes `check` as a fifth argument; a ledger built to the diagram recomputes it or drops it. On an edit nobody re-checks the new value.
- **Rule to paste:** "`propose(finding_id, field, value, evidence, check)`. `check` is computed only by the pipeline's check filter. On an edit the ledger keeps `quote_found` and sets `supported` and `confidence` to null."

### SPN-29 — A Source item whose text changes overwrites the text its old quotes came from (low)

- **Concerns:** AD-3 (upsert on `_id`), AD-6.
- **Status:** not a Saturday risk with the prepared files: none of the 45 held-back trial IDs is in the baseline file. It becomes real when the scheduled scan fetches live.
- **Rule to paste (into Deferred):** "On Saturday `source_items` is insert-only: a changed text for an existing ID is skipped and logged."

### SPN-30 — Two Deferred items still need an owner (low)

- **Collision:** Export (FR-25) can be built in the browser from table data or as an API route; both meet "built from the read model" and both, or neither, may be built. The Digest is "built from `events`", but `pending` Proposed changes emit no event, so it cannot list them (FR-20).
- **Rule to paste (into Deferred):** "Export is an API route. The Digest reads applied changes and Alerts from `events` and pending Proposed changes from `proposals`."

---

## Checked and found sound

- AD-12 and AD-4 agree: review is not a graph node, and no LangGraph state is needed to resume a review.
- AD-8's split holds: nothing the app must read exactly is placed in Agent Memory.
- AD-1 is enforceable by search: any write to `diagnostics` outside `backend/dxp/ledger` is a breach.
- The registry field list (12 keys) matches "ten agreed fields plus regulatory status" plus `lifecycle_stage`.
- The Saturday counts match the data folder: 76 FDA lung rows, 20 assays, 40 and 24 in the named held-back subsets.
