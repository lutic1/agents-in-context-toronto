---
title: "PRD Addendum: DxProvida (DxP)"
created: 2026-11-12
updated: 2026-11-14
---

# PRD Addendum: DxProvida (DxP)

Detail that belongs in architecture, UX or epics, kept here so the PRD stays short. Stack choices, data sources, the nine Lifecycle stage definitions and the event facts are in the brief's addendum at `../../briefs/brief-agents-in-context-toronto-2026-11-12/addendum.md` and are not repeated.

## 1. Users and journeys as supplied by Luis (12 Nov)

These come from a discovery session with users. Items marked "inferred" were not raised in that session.

### Roles

| Role | Role in the journey | Usage frequency |
|---|---|---|
| Strategy lead | Defines intended uses, shortlists vendors, commissions pilots and external-facing comparison reports | Episodic. Bursts around a new intended use or a major congress |
| Domain expert | Subject specialist; builds category landscapes, prepares external advisory boards | Project-driven. Heavy use for weeks, then quiet |
| Data curator | Owns the existing curated dataset and acts as the quality gate | Continuous, low-intensity. Wants less manual work, not a new place to do it |
| Downstream consumers | Colleagues who read the outputs | Read-only. Inferred |
| New or returning user | Joins mid-project, or returns after months away, with no working memory of the tool | Cold start, repeatedly |

Design consequence: nobody logs in daily, so the app must be self-explanatory on return after six weeks away, and the automation has to run unattended in between.

### Journey 1: intended-use shortlisting (primary)

Trigger: a new intended use is defined, for example monitoring patients with a specific cancer type and stage.

| Stage | What the user does | What the app does |
|---|---|---|
| 1. State the need | Describes the intended use in plain language or sets filters: modality, target indication, minimum specificity, minimum sensitivity, validated clinical data in that indication | Parses into a structured query across all records |
| 2. See candidates | Scans a result set, not individual records | Returns a comparison table, one row per assay, columns being the criteria asked for |
| 3. Judge the evidence | Checks where each number comes from: which study, what population, cohort or randomised, retrospective or prospective, analytical or clinical validation, number of samples | Shows each performance value with its citation and study context inline |
| 4. Apply operational constraints | Narrows on sample volume, sample material, turnaround, regulatory status | Filters on the operational field set |
| 5. Shortlist | Picks the top two or three providers | Saves the shortlist against the named intended use |
| 6. Export | Takes it into a vendor meeting, or packages it as a comparison report for external experts | Generates the comparison output with references intact |
| 7. Close the loop | Records what happened: pilot proposed, deprioritised, specifications requested | Keeps the decision attached to the intended use. Inferred |

What is being fixed: today the user opens each record and extracts sensitivity and specificity by hand. The journey succeeds the moment a cross-record query returns a populated table.

Where it fails: a number without a traceable source. An uncited 97% specificity is worse than a blank cell. The app also needs an explicit "no data for this indication" state, because for many realistic queries nothing is published.

### Journey 2: category landscape refresh

Trigger: a planned deliverable, such as an annual planning landscape or an external advisory board.

1. Selects a category, for example all assays of one detection approach.
2. Pulls the full field set per assay: approach type, number of cancer types covered, studies available, performance by cancer stage and cancer type, provenance of the clinical data, regulatory status and timeline.
3. Spots the gaps: records that are thin, stale or missing a needed field.
4. Fills gaps manually from their own searching, and the entry persists for everyone.
5. Exports a landscape view for a presentation and the advisory discussion.
6. Brings external advisor insight back. Inferred: nothing in the session said the app captures advisor feedback.

Design consequence: performance is not one number per assay. It is a matrix of stage by cancer type, and must be stored that way from the start or Journey 1's filtering will compare incomparable figures.

### Journey 3: monitored-update digest (the automation core)

Trigger: the app, on a scheduled scan of the agreed sources.

| Stage | Detail |
|---|---|
| Scan | Approved source types only: peer-reviewed literature databases, clinical trial registries, regulatory filing and approval records, provider websites, and congress abstracts, posters and oral presentations |
| Gate | Apply the maturity criteria before anything surfaces: number of samples, cohort or randomised design, analytical or clinical validation. A technology with no credible validation behind it should never reach the queue |
| Match | Attach the find to an existing tracked tool wherever possible. The stated need is updates to tools already on the list, not a firehose of novelty |
| Propose | Draft the field-level change: a new readout updates sensitivity; a regulatory submission updates approval status |
| Notify | A digest sized for an episodic user. Weekly or event-driven, spiking around congress season |
| Act | User reviews, accepts, edits or rejects; accepted changes update the record with the source attached and the prior value retained |

Where it fails: silent overwriting.

Difference from the PRD: congress abstracts, posters and presentations are listed here as approved sources and are out of scope for Saturday.

### Journey 4: capture on the go

Trigger: something learned off-platform, such as a congress conversation about an untracked technology.

1. User submits what they have: a provider name, a conversation note, or a photograph of a poster.
2. An agent extracts what it can into the structured fields and flags what is missing.
3. It checks whether the organisation already exists, to avoid a duplicate.
4. User confirms or corrects; the entry is tagged as manually sourced, with submitter and date.
5. It joins the monitored set, so later automated scans pick it up.

This journey is the one most likely to be used from a phone, in a convention centre, on poor wifi, by someone who will not come back to tidy it up. A partial record clearly marked partial is the right outcome.

## 2. Notes for architecture

- **Performance storage.** Later development, not Saturday. One entry per Diagnostic, tumour type and Tumour stage, each with its own study context and Evidence (FR-6).
- **Field history.** Every field keeps its earlier values, the Evidence for each, and the Reviewer decision that replaced it (FR-17).
- **Reviewer corrections.** The brief described a correction three ways: making the check stricter, feeding back as an example, and a learned rule. The PRD requires only the visible behaviour in FR-19. Whether that is one mechanism or several is an architecture decision.
- **Agent roster.** Not fixed by the PRD. The plan's watcher, extractor, checker and writer split is a starting point.
- **Graph view.** The team wants connections between clusters visible, not only clusters. The plan's Knowledge layer already holds the links between assay, biomarker, tumour type, trial, drug and company.
- **Alert rule inputs.** FR-12 and FR-13 need, per Team and Diagnostic, whether a first Alert has been sent, and per Diagnostic, the Lifecycle stage history, lines of therapy, linked trials and standard-of-care status.

## 3. The wow moment and the MongoDB mapping

*Superseded on 13 Nov by §5: the wow moment is now the governed run. Rows for FR-9, FR-19, FR-21, FR-27 and FR-28 are deferred with their requirements. Kept for reference.* *Superseded again on 14 Nov by §6: the wow moment is the discovery research loop.*

Decided 12 Nov: the wow moment is the agentic work with memory, shown in the video connecting to the Graph view, with MongoDB's capabilities presented as the competitive advantage. Judges score creativity, originality and novelty equally.

Which MongoDB capability powers which behaviour, taken from the team's plan. Architecture confirms or changes each row.

Names checked against MongoDB's documentation on 13 Nov, to use on camera: the product is MongoDB Atlas Agent Engine (public preview since 29 Sep 2026) and the feature is Agent Memory, with semantic, episodic, procedural and taxonomic types. Atlas Vector Search and Atlas Search are now called MongoDB Vector Search and MongoDB Search. Automated Embedding is the correct name and still carries a preview banner.

| Behaviour in the PRD | MongoDB capability named in the plan |
|---|---|
| Resume after weeks away (FR-28) | Agent Memory, episodic |
| Learned rule after a rejection (FR-19) | Agent Memory, procedural |
| Synonyms: "liquid biopsy" finds ctDNA (FR-9) | Agent Memory, taxonomic; synonym search |
| Plain-language query across Records (FR-21) | Automated Embedding with vector search |
| Connected Graph view (FR-26) | Graph lookup across assay, biomarker, tumour type, trial, drug and company |
| Alerts and the graph updating as a change lands (FR-13, FR-27) | Change streams |
| A new kind of Diagnostic arriving with new fields | Flexible documents, no schema change |

Earlier candidates, kept for the scoping session: the guardrail that rewrites itself and flags other pending Proposed changes (FR-19), and the graph redrawing as an accepted change lands (FR-26, FR-27). Both sit inside the decided wow moment. The photographed poster is out for Saturday on licensing grounds.

## 4. Findings from the documentation check (13 Nov)

Ten skills under `.claude/skills/dxp-*` hold the detail, each written from official documentation fetched on 12 and 13 Nov. These are the findings that change the plan. None was tested against a live paid service.

### To do on Friday

- **Atlas cluster.** A free cluster is not enough: without a payment method it allows 3 embedding queries a minute, 100 operations a second and 3 search indexes. Ask MongoDB staff for Flex or M10. M10 also meets the Agent Memory requirement.
- **Agent Memory.** It is a separate platform to provision, not a cluster switch: a command-line tool, a Voyage key, a model key, a service account and IP access list entries.
- **Claude API tier.** The 300 to 500 item batch is confirmed only for the Start tier and above, at a concurrency of 16. Limits for the lowest tier are not published. Check the key's tier.
- **Paid plans.** HeyGen was deferred by readiness fix D55; on 14 Nov it returned as supporting scope (PRD FR-58, §6 below), and its video is rendered during the event. HeyGen's free plan is watermarked and not licensed for a public video (Creator is USD 29 a month, or an API wallet from USD 5). ElevenLabs' free plan has no commercial licence and requires attribution (Starter is USD 6).
- **LangSmith.** A new organisation needs an agent record and two extra environment variables; setting the old project variable sends no traces. The free plan allows 5,000 traces a month.

### For architecture

- **Match key (FR-3).** No identifier for a Diagnostic is shared across ClinicalTrials.gov, PubMed and FDA. The key has to be designed. Modal also retries inputs, so uniqueness must be enforced in MongoDB.
- **Baseline and Held-back set (FR-30).** A wide lung diagnostics query returns about 3,300 Source items, not 300 to 500; the data-sources skill gives narrower query sets. The last four weeks hold about 45 trials and 90 abstracts. FDA adds almost nothing in that window, and web page dates are estimates, so the Held-back set comes from ClinicalTrials.gov and PubMed.
- **Quotes (FR-18).** The Claude API's citations feature cannot be combined with structured output. Web search returns cleaned text, so quotes are checked against the stored snapshot of the Source item.
- **Learned rule off-switch (FR-19).** The Agent Memory SDK has no delete or update, so switching a rule off is a flag in a DxP collection.
- **Team memory (FR-28).** Agent Memory is scoped per user; bind the user ID to the Team. Use direct writes for the live demo, because background extraction is asynchronous.
- **Batch and live updates (FR-4, FR-27).** Modal caps a web request at 150 seconds. The batch runs as a background job that writes progress to MongoDB, and the front end polls or reconnects.
- **Network access.** Modal has no fixed outbound address on its free plan, so Atlas must allow any address or the team pays for a static one.
- **Graph view (FR-26).** `react-force-graph-2d` is the recommended library, with working code in the front-end skill.
- **Orchestration.** Agent Memory has its own SDK and does not depend on LangGraph, so LangGraph against the Claude Agent SDK is an open architecture choice. The reviewer pause that persists in MongoDB and the LangSmith trace favour LangGraph.

### For the video

- HeyGen was deferred by readiness fix D55. *Updated 14 Nov (discovery):* it is now supporting scope (PRD FR-58): an avatar video of about 20 seconds per report, rendered during the event from the briefing's grounded script, behind the `avatar` flag. Only HeyGen API v3 works, and render queues can be long, so the report page shows "Rendering" until the video is ready (OD7).
- Give judges the production URL. Vercel preview URLs ask for a login.
- The event page publishes no criteria for the ElevenLabs prize.

## 5. The pivot to Problem Statement 1 (13 Nov)

*Updated 14 Nov (discovery):* the vision correction in §6 wins over this section where they disagree. The governance design below still applies; the demo scenario, the per-proposal alert and the `/review?proposal=` link are replaced as §6 describes.

The full change, with the Saturday timeline and the PR plan, is in `../../sprint-change-proposal-2026-11-13.md`. This section records only why, the demo scenario and the design notes for the Slack alert. The readiness fixes of 14 Nov (`../../readiness-fixes-2026-11-14.md`, D1 to D57) win over both documents where they disagree. The Slack change of 14 Nov (`../../sprint-change-proposal-2026-11-14-slack.md`, S1 to S13) wins over all three wherever they mention the external system.

### Why Statement 1

The participant guide arrived on 13 Nov. It requires every project to fit one of three problem statements, bans a dashboard as the main feature and bans AI that gives medical advice. It also cuts the build to 10:45 to 17:00 and requires the Atlas Sandbox.

After a party-mode session, Luis chose Statement 1, "Agents You Can Audit", for four reasons:

- **DxP already had the hard part.** Evidence with a checked quote, field history and a Reviewer decision on every change are the raw material of an audit trail. Most of the ledger and extraction work carries over unchanged.
- **It answers the bans.** The governed agent is the product and the screens only inspect it, so DxP is not a dashboard. It serves a pharma team's evidence work and gives no patient advice.
- **It fits the hours.** The core loop (identity, Grant, Policy gate, one external action, stop, audit) is small enough to be green by 14:30 and leave time for the demo.
- **MongoDB does real work in it.** Schema validation on Grants and Policies, atomic conditional updates for the claim and the stop, change streams for the live feed, and the action history for the audit.

### Alternatives rejected

- **Statement 2, "Memory You Can Govern", and Statement 3, "Finish the Job".** Statement 2 leans on Agent Memory, a public preview that may not run on the Atlas Sandbox, and would need memory correction, expiry and cross-Team isolation built from scratch. Statement 3 asks for adapting when a system's layout changes and resuming after crashes; DxP's sources are static files, so it was the weakest fit. Pitching either would have kept the old tracker as the product. In that form, the broad screens (Find, Categories, the Home dashboard) risked reading as a dashboard-led project, and the governance story would have been a side note rather than the point.
- **Keeping the old plan and renaming screens.** Rejected in the session: a renamed graph is "a dashboard in a costume" unless it is fed by `run_id`. That is why the graph survives only as the run-scoped impact view (FR-43).

### What changed in the wow moment

Before: agents working with memory, a Learned rule from a rejection, and the change landing in the Graph view (§3). After: a real Slack alert in `#all-mango-db-hackathon` that links back to the proposal in DxP, an out-of-scope Action blocked before it runs, a stop mid-run, and an audit that answers "who authorised this, and under what authority?" The MongoDB capability is named at each step.

### The demo scenario (updated 14 Nov)

*Superseded 14 Nov (discovery) by the demo order in PRD SM-4 and the video in SM-2 (proposal V16 and V17). Kept for reference.*

Decided in `../../readiness-fixes-2026-11-14.md` (D9, D30 to D34, D45, D46, D52, D54, D56). The demo uses a change the rules allow, from real data. No Lifecycle stage change is demonstrated, and the SuperARMS stage-advance story is removed.

- Selected trial NCT04712877 names FoundationOne Liquid CDx (a plasma test) and FoundationOne CDx (a tissue test). Both are FDA-seeded. Hand-written aliases make both Findings resolve to the seeded Diagnostics: "FoundationOne Liquid" maps to FoundationOne Liquid CDx, and "FoundationOne" not followed by "Liquid" maps to FoundationOne CDx (PRD §4.1, "Data notes").
- The agent `dxp-curator` acts under the Grant `lbdx@v1`, Team "Team Liquid Biopsy Dx". Its scope uses exactly these trade-name strings: "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay" (`normalise_name()` removes "®" and folds case). Every other Diagnostic is out of scope. Sam is the Reviewer principal `sam` with grant `sam@v1`; the seed principal is `seed` with grant `seed@v1`.
- The Selected trial set is 20 named public trials, fetched by NCT ID during the event (NFR7) and processed in the order listed in PRD §4.1, NCT04712877 first. The live Run is paced with `DXP_DEMO_PACE` (one item at a time, a few seconds per item), so the stop lands mid-run. Selected trials are stored with `window: "selected"`.
- The gate is evaluated once per change, and each filed proposal gets its own `notify_slack` Action, so there is one Slack alert per proposal (superseded 14 Nov: one alert per report, V11).
- The order, for both the 60-second video and the live demo:
  1. Start the Run, choosing the Grant labelled with its Team.
  2. The proposal to add NCT04712877 to FoundationOne Liquid CDx's trials is allowed: a pending Proposed change plus a Slack alert. The second screen shows the alert arriving in `#all-mango-db-hackathon`; its "Review in DxP" link opens the focused proposal. Then the same trial's proposal for FoundationOne CDx is blocked before execution: check 2 fails, because the tissue test is outside the Team's scope. No proposal is filed and no Slack message is sent.
  3. Stop the Run while items remain.
  4. Sam approves the pending proposal in DxP. Approval and rejection happen in DxP, never in Slack. It appears under "After the run".
  5. Ask the scripted question in the Audit view: "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"
- **Video timings (D52).** 0 to 10 s: the problem and the scope. 10 to 30 s: the allowed proposal and its Slack alert, then the blocked change. 30 to 45 s: stop the Run. 45 to 60 s: Sam approves in DxP, then "who authorised this?" in the Audit view.
- The impact view and the audio briefing are shown only if each passed its own acceptance check.
- **Reset before each take.** A snapshot is taken after seeding and before any Run. The reset restores it with `mongodump` and `mongorestore`. It runs before the video (16:30) and again between submission and the live demo (16:55 to 17:10).

### Design notes for the Slack alert (FR-35 to FR-37)

*Updated 14 Nov to match the readiness fixes (D4 to D8, D13, D16 to D28, D42, D44, D46, D47, D50, D53, D56) and the Slack change (S1 to S13).* *Updated 14 Nov (discovery, V11):* there is one alert per Research report, not per proposal. Its body is the report headline, the relationship summary and "Approve or reject in DxP". "Review in DxP" links to `${DXP_BASE_URL}/reports/<report_id>`, and "Open diagnostic" links to the Accepted knowledge view. Where the notes below say "proposal" for the alert, read "report". The header reads "New research report for review". Decisions are made per report, through `POST /reports/<report_id>/decision` (kind `decide_report`); the per-proposal decision `POST /proposals/<p_id>/decision` and the kind `decide_proposal` are superseded (V8, V24), and a Reviewer decision's `cause` names the report, memory or action it decided. `sam@v1` holds `decide_report`, `authorise_task`, `create_memory`, `correct_memory`, `revoke_memory`, `review_value` and `resolve_notification`. Everything else (sending, outcomes, manual resolution, stop, audit) is unchanged.

- **Destination.** One Slack channel, `#all-mango-db-hackathon`, reached through an incoming webhook. The action kind is `notify_slack` and the destination is `slack:#all-mango-db-hackathon`. The agent's Grant allows the actions `file_proposal` and `notify_slack` and the destinations `ledger` and `slack:#all-mango-db-hackathon`; a notification to any other destination fails check 3. No other external action is in scope.
- **Configuration.** `SLACK_WEBHOOK_URL` holds the webhook. It is a credential: it lives only in `.env` and in the Modal secret, and is never committed, logged, stored in an audit record or shown on screen (NFR14). `DXP_BASE_URL` is the production web address, used to build links back to DxP; the sender refuses to start without it.
- **Notify only.** The message has links and no interactive elements: no approve or reject buttons and no Slack actions. Slack sends nothing back to DxP, and DxP exposes no Slack callback route. Approval and rejection happen in DxP, never in Slack.
- **Who acts.** The Run was started with `POST /runs { grant_id, set }` by `initiated_by`, under a Grant whose `startable_by` includes them; the Grant defines the Team. The worker acts as the agent `dxp-curator`, with the agent's key and the `run_id`; the key must resolve to the Run's `agent` (FR-31, FR-32). A key resolves to its principal whatever its Grant's status, so a revoked or expired Grant leaves a blocked Decision, and 401 means only an unknown key.
- **Order of operations.** After extraction, take an admission for the Action while the Run is `running`, with `item_key = "<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"` (FR-38). Run the Policy gate (FR-33) and record the Decision, allowed or blocked (FR-34). If blocked, stop there: no Action, no Record change, no Slack post; emit `action_blocked` with the `decision_id`. If allowed, the ledger files the Proposed change once, as pending (it is never applied directly, on a new Diagnostic or an existing one), and write the Action to Atlas with its action ID, its `decision_id` and status `queued`. Claim it with one conditional update from `queued` to `dispatching` (FR-37). Post the alert to the webhook. Record the outcome with an update conditional on the current status (see "Sending and its outcome"). Nothing is written back to the proposal: its `notification { action_id, status, posted_at }` is built at read time from its `notify_slack` Action. Release the admission once. After the last item the pipeline calls `runs.finish`.
- **The alert asks for review in DxP.** The Slack alert tells a person that a pending Proposed change is waiting. Applying it happens only through a Reviewer decision in DxP, written with `run_id: null`, a Reviewer stamp (`agent: null`, `initiated_by` the Reviewer) and `cause: { proposal_id, origin_run_id }`, under the Reviewer grant `sam@v1`. The decision calls the ledger's apply. Applying is all or nothing and recoverable: `pending` to `applying` to `applied`, with the proposal ID recorded in `applied_proposal_ids` so the update runs once. Edges are upserted after the update and `value_applied` is emitted with a `dedupe_key`; recovery always re-upserts the edges and re-emits the event (FR-16).
- **The message (S5).** A Block Kit alert with:
  - a header "New diagnostic evidence for review", plus the action ID;
  - the Diagnostic name;
  - the Evidence: the trial NCT ID with its ClinicalTrials.gov link, and the quote of at most 300 characters;
  - the Proposed change, for example "Add trial NCT04712877 to Trials";
  - who acted: the agent, the `run_id`, the Grant `{grant_id}@v{version}` and the policy set `ps_…`;
  - a context line: "Approve or reject in DxP. Slack only notifies."

  Never PubMed abstract text beyond a short quote, and never a secret or a personal email address.
- **Links back to DxP (S6).** *Superseded 14 Nov (V10, V11): "Review in DxP" links to `${DXP_BASE_URL}/reports/<report_id>` and "Open diagnostic" to the Accepted knowledge view `web/app/diagnostics/[dx_id]/`; the text below is kept for reference.* Built from `DXP_BASE_URL`. "Review in DxP" links to `${DXP_BASE_URL}/review?proposal=<p_id>`: the Review page (`web/app/review/`, PR B04) loads that proposal with `GET /proposals/<p_id>`, which returns one proposal whatever its status, opens with it focused, and shows "Proposal not found" if the ID is unknown. "Open diagnostic" links to `${DXP_BASE_URL}/diagnostics/<dx_id>`, the Record page (`web/app/diagnostics/[id]`, PR B04). Story 9.4 tests that both links resolve on the deployed web app.
- **Action ID in the alert.** The action ID goes in the alert header, so a Reviewer can find it in the channel when an outcome is unknown.
- **Sending and its outcome (S7).** A webhook post cannot be looked up afterwards, so DxP records exactly what it observed. The statuses are `queued`, `dispatching`, `delivered`, `failed` and `unknown`, plus `reconciling` at read time only. Every update is conditional on the current status.
  - **HTTP 200 with body `ok`:** `delivered`, with the time posted and the response.
  - **HTTP 4xx** (for example `invalid_payload`, `no_service`, `channel_not_found`): `failed`, never retried.
  - **HTTP 429:** nothing was posted. Retry once, after `Retry-After`, while still holding the claim. A second 429 means `failed`.
  - **Timeout, connection error or HTTP 5xx:** the outcome is ambiguous, so the Action is `unknown`. It is never retried automatically, because a retry could post a second alert (FR-36).
- **Manual resolution (S8).** `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }` lets a Reviewer settle an `unknown` notification after checking `#all-mango-db-hackathon` for the action ID. It is gated as kind `resolve_notification` under `sam@v1`, records check 4 as `n/a`, and is audited as a Decision with the Reviewer's stamp. The Action then carries `resolution { outcome, note, decision_id, by, at }`. The Run console and the Audit view show the Resolve control only when the signed-in principal's `actions`, from `GET /whoami` (`Principal { id, name, kind, actions }`), include `resolve_notification`. There is no automatic reconciliation and no listing of messages.
- **Stop.** Check 5, "run still authorised", means: the Action holds an admission for this Run, and the Run is not `stopped`. New admissions are granted only while the Run is `running`. An admitted Action may finish while the Run is `stopping`. Each admission is released once. `runs.sweep` marks admissions past their lease `abandoned`, marks any `dispatching` Action they hold `unknown` (never retried; a Reviewer resolves it), and marks any `queued` Action they hold `failed` with reason `abandoned_before_send`. `GET /runs/<run_id>` never calls Slack: it starts the sweep in the background and shows the Actions it is still settling as `reconciling`. `runs.settle` only moves the Run from `stopping` to `stopped`, when no `admitted` admissions remain; `runs.finish` moves it from `running` to `done`. A Run is `failed` only after an error the pipeline cannot recover from (FR-38).
- **Audit (S9).** Each notification Action keeps its Decision (the agent, `initiated_by`, the Grant evaluated, the policy set and every check), its inputs and Evidence reference, the destination, four timestamps (queued, claimed, posted, observed) and the result, `result { http_status, response_body, posted_at, link_urls { report_url, diagnostic_url } }`. It never stores the webhook URL. The audit and the Audit view also show the proposal's live DxP review status: pending, applied or rejected, with who decided and when. "Who authorised this?" answers from the Decision's `authorised_by`. `GET /runs/<run_id>/audit` lists Decisions and Actions in order, then "After the run" with the Reviewer decisions caused by the Run, `resolve_notification` included. `GET /decisions/<decision_id>` reconstructs any Decision, blocked ones included (FR-34, FR-39).
- **Versions.** Each Decision names the Grant actually evaluated (`grant_id@version`) and the `policy_set_version`, whose members are stored in `policy_sets`. Policies and Grants are selected by latest version first, then status; a newer `revoked` or `expired` version blocks (FR-33).
- **Seed and Reviewer grants.** `seed@v1` lets the seed principal `apply_value` to the `ledger` with scope `{ all: true }`, which is valid for the seed principal only. `sam@v1` lets the principal `sam` (Sam) `decide_proposal`, `review_value` and `resolve_notification` on the `ledger`, over the same Diagnostics as the agent's Grant `lbdx@v1`. Check 4 (evidence) applies only to `file_proposal` and `notify_slack`; it records `n/a` for `apply_value` (seed), `decide_proposal`, `review_value` and `resolve_notification`; an edit or reject must carry a reason, and a resolve carries a note (FR-32, FR-33).
- **Test without Slack.** Simulate a timeout, a 4xx, a single 429 and a double 429 against a stub, and two workers claiming the same Action, before relying on the live channel.

### Alternative rejected: GitHub issues

The first plan opened a review issue in a sandbox GitHub repository and reconciled ambiguous results by listing the repository's issues. Rejected on 14 Nov in favour of a Slack alert, for three reasons:

- **Slack is where the team already works.** An alert in `#all-mango-db-hackathon` reaches the Reviewer where they already are, and its link takes them straight to the proposal in DxP.
- **The webhook is tested.** Luis posted a Block Kit alert for a new diagnostic to the channel through the incoming webhook before the event, so the integration path is known to work.
- **No write access to a repository is needed.** The agent needs no repository, no token with write access to it and no issue permissions, which leaves less authority to scope and guard.

The cost is that a webhook post cannot be looked up afterwards, so an ambiguous outcome is resolved by a Reviewer in DxP instead of by an automatic lookup.

## 6. Restoring the discovery-agent vision (14 Nov)

The full change is in `../../sprint-change-proposal-2026-11-14-discovery-agent.md` (V1 to V24). It wins over §5, the readiness fixes and the Slack change where they disagree. The D1 to D57 fixes and S1 to S13 still apply wherever it does not replace them. Its section 7 cuts 1 to 5 are the baseline.

### The vision correction

While the plan narrowed to an audit demo, it lost the product. DxP is a **proactive diagnostic-evidence research agent**. It discovers new trials, connects them to existing evidence, remembers reviewer corrections and proposes useful follow-up work. Governance (identity, grants, policies, decisions, stop, audit) supports that workflow rather than being the whole product.

The entry stays under Statement 1, "Agents You Can Audit". Atlas remains the identity, policy and audit layer, and now also stores the evidence collection, its embeddings and the Reviewer memory. DxP supports research review and gives no medical advice.

The working loop is: discover, relate, remember, gate, propose, notify, brief, decide (PRD UJ-6). The wow moment is now a real discovery tied to earlier evidence, a past correction visibly changing the agent's wording, an unsupported claim blocked before filing, and an approval that authorises a small, governed follow-up task.

### Covered, restored and added

**Already covered by the plan (kept, with D1 to D57 and S1 to S13).**

- Run identity with two identities, grants, key resolution and the 401 rule (FR-31, FR-32).
- The Policy gate before every action, Decisions for allowed and blocked outcomes, policy sets, stable IDs and `seq` (FR-33, FR-34).
- Admissions, stop, sweep and recovery (FR-38).
- Pending-only review, and an all-or-nothing apply owned by the ledger (FR-16).
- The Slack notify-only alert with outcomes and manual resolution (FR-35 to FR-37), now one alert per report.
- The audit API and view (FR-39, FR-41), extended.
- The Atlas Sandbox, reuse rules, resets, single file owners and the tracker.
- The FDA seed as accepted baseline knowledge, the aliases and the Team scope.

**Restored (deferred in the 13 Nov pivot).**

| Capability | Was | Now |
|---|---|---|
| Proactive discovery | FR-1 scans deferred; only a fixed NCT list was fetched | FR-47: a scoped ClinicalTrials.gov search with a cursor on the last-update date. Tavily and scheduled scans stay deferred |
| Embeddings and Vector Search | Deferred | FR-48: embeddings on evidence and findings, an Atlas Vector Search index, related-evidence retrieval, and an honest text-search fallback |
| Reviewer memory | Memory and Learned rules deferred | FR-51, FR-52: Team-scoped, attributable, correctable and revocable memories retrieved into proposals. Not Learned-rule enforcement: memories never change permissions. The Agent Memory preview stays deferred |
| Audio briefing | Stretch (FR-44) | FR-57: a ten-second briefing inside the report, supporting |

**Added.**

| Capability | PRD |
|---|---|
| Relationship classification: supports, contradicts, extends or new question, with checked quotes from both sides; similarity is never evidence | FR-49 |
| The Research report as the pending proposal, separate from accepted knowledge | FR-50 |
| Claim-accuracy policies: performed or results only if reported; planned or recruiting described as such; cell-line or animal labelled preclinical | FR-53 |
| Approval promotes to accepted knowledge and authorises one follow-up task | FR-54 |
| The follow-up task runs under its own grant and gate | FR-55 |
| The report page, opened from Slack, with approve, reject or correct, and a memories panel | FR-56 |
| A HeyGen avatar video from the briefing's grounded script, supporting, behind the `avatar` flag | FR-58 |

**Cut or narrowed, so the loop fits.**

| Item | Change |
|---|---|
| Live change-stream feed (FR-42) | Cut. Screens poll |
| Learned-rule policy drafts (FR-45) | Cut. Policies stay hand-written (NFR15) |
| The old spoken audit briefing (FR-44) | Replaced by FR-57 |
| Separate Review list screen | Narrowed to a small pending-reports list linking to the report page |
| The Record page | Narrowed to an Accepted knowledge view of one Diagnostic, reached from the report |
| Impact graph as a separate view (FR-26, FR-43) | Cut. Kept only as an evidence-relationship view inside the report, if time allows |
| The Selected trial set as the demo's source of new data | Narrowed. Split into the Prior collection, loaded in baseline mode during setup, and the live Discovery scan |

**Still deferred (V18).** Find and Categories, Team Alerts, the Home dashboard, Tavily, scheduled scans, PubMed, the Agent Memory preview, Learned-rule enforcement and quick capture.

### Later decisions (V21 to V24)

- **Two gated drafts (V21).** The drafter writes each report twice, first without memories and then with the retrieved memories. Both drafts pass the gate as the report-level `file_proposal`, each its own Decision; the second is filed. The memory's before and after come from the two real drafts. The "showed" claim is blocked whenever the first draft writes it, but it is not guaranteed, so must-show 3 rests on the team-scope block on FoundationOne CDx.
- **Retrieval by claim kind (V22).** Memories are retrieved by Team, active status and `claim_kind` (for example `outcome_claim_without_results`), then ranked by similarity, never filtered by assay. M1, written on the Guardant360 CDx trial NCT05715229 by correcting the report of the setup run `set: "nct:NCT05715229"` (the trial is excluded from the prior collection), is therefore retrieved for the FoundationOne Liquid CDx discovery.
- **Scheduling levers (V23), pending Luis's decision.** L1: the long PRs A06, A08, A19+A20 and A21+A22 start at 10:45 as drafts against the contract shapes and rebase after 11:45. L2: Vlad's desk merges four of Luis's leaf PRs (A05, A13, A14, A09). Neither is decided yet; without both, the loop slips past 15:15 (`build-schedule.md`).
- **Names follow the architecture spine (V24).** A report is filed as a report-level `file_proposal` (no `file_report` kind); runs start with `POST /runs { grant_id, set }`, `set` being `discover`, `nct:<id>` or `task:<id>`; the report decision supersedes per-proposal decisions, while the proposal read routes and `review_value` stay. The agent grant `lbdx@v1` carries `generate_briefing` and `generate_avatar_video` with destinations `tts:elevenlabs` and `video:heygen`; the web flags are `briefing`, `avatar` and `memory_edit`.

### MongoDB mapping, updated

| Behaviour | MongoDB capability |
|---|---|
| Related evidence and memory retrieval (FR-48, FR-51) | Atlas Vector Search, with Automated Embedding if available (OD1); Atlas Search text search as the labelled fallback |
| Reports, memories, tasks and scopes (FR-47, FR-50, FR-51, FR-54) | Flexible documents |
| Grants and Policies (FR-32, FR-33) | Schema validation and versioned documents |
| Claim, stop and apply (FR-16, FR-37, FR-38) | Atomic conditional updates |
| Audit (FR-39) | The Decision and Action history |

### Alternative rejected: an audit-only demo

Keep the 13 Nov plan as it stood: a fixed list of 20 trials, one proposal filed, one scope block, a stop and an audit question. Rejected on 14 Nov for three reasons:

- **It lost the product.** The team's users want an agent that finds new evidence and tells them how it relates to what they know. An audit-only demo showed governance around an agent that did very little worth governing.
- **It wasted what DxP already had.** Checked quotes, accepted knowledge and Reviewer decisions are exactly what discovery, relationship labels and memory need. Restoring them costs one new epic, not a new product.
- **It made a weaker Statement 1 entry.** Governance is more convincing when it controls real work: a discovery scan under a scope, a claim the source does not support, a memory that changes wording but never permissions, and a follow-up task with its own narrow grant. Each is a new, specific thing to audit.

The cost is a longer critical path with little float and a heavy merge queue. Section 7 of the proposal handles it: fold core acceptance into the first rehearsal pass, bundle and stagger PRs, cut the change-stream feed, the Learned-rule drafts and the separate impact graph, keep the briefing and the avatar video behind flags, and give the report page two builders. If a milestone slips, cut in this order: the avatar video, the briefing, the memory correct and revoke UI, the follow-up task's related-evidence filing, then the second discovery item.
