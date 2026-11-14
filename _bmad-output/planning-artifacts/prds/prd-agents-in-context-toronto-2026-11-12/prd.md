---
title: "PRD: DxProvida (DxP)"
status: draft
created: 2026-11-12
updated: 2026-11-14
---

# PRD: DxProvida (DxP)

## 0. Document purpose

This PRD is for the two teammates building DxP on Saturday 14 November 2026, and for the architecture and epics work that follows. It builds on the product brief in `../../briefs/brief-agents-in-context-toronto-2026-11-12/` and does not repeat the event facts or stack choices held there.

**Course correction, 13 Nov.** The organisers' participant guide arrived on 13 November. DxP is now pitched and built for hackathon Problem Statement 1, "Agents You Can Audit". The governed agent is the product. The approved change is in `../../sprint-change-proposal-2026-11-13.md`; the rationale is in `addendum.md` §5. Requirements the pivot sets aside stay in this document, marked **Deferred (pivot, 13 Nov)**, so no agent builds them on Saturday. Requirements kept in a smaller form carry a short "Trimmed" note.

**Readiness fixes, 14 Nov.** An audit of the pivot found gaps that would have stopped build agents. The decisions are in `../../readiness-fixes-2026-11-14.md` (D1 to D15, D16 to D40 from a second audit the same day, and D41 to D57 from the final audit), and that file wins where any document disagrees. This PRD now follows it; changed requirements carry an "Updated 14 Nov" note.

**Slack replaces GitHub, 14 Nov.** The external system is now a Slack alert posted to `#all-mango-db-hackathon`, not an issue in GitHub. The approved change is in `../../sprint-change-proposal-2026-11-14-slack.md` (S1 to S13), and that file wins where any document disagrees. The Slack alert only notifies. Approval and rejection happen in DxP, never in Slack.

Glossary terms (§3) are used exactly. Features are grouped in §4 with requirements numbered FR-1 to FR-46. The governed-action requirements are FR-31 to FR-46 in §4.10. Existing IDs never change. Constraints carry the NFR IDs used in `epics.md`. Inferences are tagged `[ASSUMPTION]` inline and indexed in §10. The user journeys as supplied, technical notes for architecture and the pivot rationale are in `addendum.md`.

## 1. Vision

**In one line:** DxP is an agent that keeps a pharma team's diagnostic evidence current, and it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action, and an audit trail a reviewer can replay.

The product is the governed agent. It reads a selected set of real lung cancer trials, drafts evidence-backed Proposed changes to Records, and posts a Slack alert so a person reviews each one in DxP. Before every action it checks who it is acting for, what it is allowed to touch and which policy applies. When an action is out of scope, nothing happens except one recorded decision that says why. A person can stop a run at any time. Afterwards, a reviewer can rebuild the whole run, action by action, and answer "who authorised this, and under what authority?"

The screens exist to inspect and control the agent. They are not the product. The Run console shows the run live; the Audit view replays it; the Record and Review screen shows the evidence; the impact view shows what one run touched.

The evidence work from the original plan carries over unchanged. Every value in a Record carries its Evidence, and a Lifecycle stage changes only through an accepted Proposed change. The wider tracker described in the brief (Find, Categories, Alerts, memory and resume, capture) is deferred.

**Earlier novelty claim** (deferred with FR-19 and FR-28): DxP is an evidence analyst whose guardrails are written by its Reviewers. One rejection, with a reason, becomes a rule the agents follow from then on, and DxP remembers every Team between visits.

On Saturday DxP covers lung cancer only.

## 2. Target user

DxP serves a diagnostics team inside a pharmaceutical company. The team tracks evidence about diagnostic tests (trials, approvals, published studies) to plan pilots and partnerships. It is a research and strategy tool for professionals.

**DxP is not patient-facing and gives no medical advice.** It does not diagnose, recommend a test or treatment for anyone, or interpret a result for an individual. The hackathon bans AI that gives medical advice, and DxP stays clear of it by design.

The person at the centre of the demo is the data curator (Sam in the UX flows), who reviews what the agent proposes. The second audience is anyone who must later answer for what the agent did: a team lead, a quality reviewer or an auditor.

### 2.1 Jobs to be done

- **Data curator.** Keep the evidence trustworthy with less manual work, and stay in control of an agent that writes to the Records and posts alerts in other systems. Continuous, low-intensity use.
- **Reviewer or auditor (new, 13 Nov).** After a run, reconstruct what the agent did, on whose authority and under which policy version, without reading logs. Episodic: after a run, or when someone asks a question about a Record.
- **Strategy lead (the Director of Diagnostics `[ASSUMPTION]`).** When a new Intended use is defined, shortlist the two or three Diagnostics worth a pilot, with Evidence that stands up in a meeting with a Provider. **Deferred (pivot, 13 Nov)** as a Saturday user; the evidence the agent keeps is what this job will rely on later.
- **Domain expert.** Build a Category landscape for a planning cycle or an external advisory board without opening every Record. **Deferred (pivot, 13 Nov).**
- **New or returning user.** Pick the work up mid-project or after months away, with no memory of the tool. **Deferred (pivot, 13 Nov)** with memory and resume.
- **Downstream consumer.** Read the outputs. Never queries DxP directly.

### 2.2 Non-users

- Patients, and clinicians deciding care for an individual patient. DxP informs a pharma team's strategy and is not a clinical decision tool.
- Anyone who wants a daily feed of everything new.

### 2.3 Key user journeys

- **UJ-5. A governed run, reviewed and replayed.** *(Primary from 13 Nov.)*
  Sam starts a run over the Selected trial set by choosing a Grant, which is labelled with its Team; there is no separate Team picker. The Run console shows the agent's identity card: the executing agent, model, prompt version, policy-set version, and the person who started the run. It also shows the grant: which Team's Diagnostics it may touch, which destinations (`ledger` and `slack:#all-mango-db-hackathon`) and which actions (`file_proposal` and `notify_slack`), and when the grant expires. The demo run is paced (`DXP_DEMO_PACE`: one item at a time, a few seconds per item), so actions arrive one by one and the first item is NCT04712877. The grant is `lbdx@v1`, for Team "Team Liquid Biopsy Dx", executed by the agent `dxp-curator`. Selected trial NCT04712877 names two FDA-seeded Diagnostics: FoundationOne Liquid CDx (a plasma test) and FoundationOne CDx (a tissue test). The demo then runs in this order:
  1. Sam starts the run.
  2. The proposal to add the trial to FoundationOne Liquid CDx is allowed: it is filed as a pending Proposed change with its quote, and its own Slack alert arrives in `#all-mango-db-hackathon` (one alert per filed proposal). Sam sees the alert in Slack itself; its "Review in DxP" link opens the focused proposal in DxP. Then the same trial's proposal for FoundationOne CDx is blocked before anything happens, because the tissue test is outside the Team's scope; the console shows that check 2 failed.
  3. Sam stops the run while items remain: the run shows "stopping" while admitted actions finish, then "stopped".
  4. Sam approves the pending Proposed change in DxP. Approval and rejection happen in DxP, never in Slack. The approval appears in the Audit view under "After the run".
  5. Sam opens the Audit view and answers "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"

  *Updated 14 Nov: no Lifecycle stage change is demonstrated; the order above follows readiness fix D33. The external system is Slack (Slack change S11).*
  **Climax:** a real action in another system, a blocked action that changed nothing and left only its recorded decision, and a replay that names the person, the grant and the policy version behind every step.
  **Edge case:** an uncertain result from Slack (a timeout, a connection error or a server error). A webhook post cannot be looked up afterwards, so the agent never retries it automatically and never risks a second alert. It marks the action `unknown`, and a Reviewer checks `#all-mango-db-hackathon` for the action ID and resolves the action in DxP.
- **UJ-1. The Director of Diagnostics shortlists Diagnostics for a new Intended use.** **Deferred (pivot, 13 Nov).**
  The Director of Diagnostics, in a pharmaceutical therapy-area team `[ASSUMPTION]`, has a new Intended use: monitoring patients with early-stage lung cancer for relapse `[ASSUMPTION: example]`. They last opened DxP six weeks ago. They open it in a browser and DxP shows what changed since that visit. They describe the Intended use in plain language. DxP returns a comparison table with one row per Diagnostic and a column for each criterion they asked for. Each Performance value shows its study, population, design and sample count inline. Where nothing is published, the cell reads "no data for this indication". They narrow by sample type, turnaround and regulatory status, pick three, save the Shortlist against the Intended use and export the comparison with its references.
  **Climax:** a populated table arrives in one query. Today they open each record and copy out sensitivity and specificity by hand.
  **Edge case:** a value with no Evidence is never shown. An uncited 97% is worse than a blank cell, because a blank prompts a check and a bare number does not.
- **UJ-2. A domain expert refreshes a Category landscape.** **Deferred (pivot, 13 Nov).** Ahead of an advisory board, the domain expert selects a Category, sees the full field set for every Diagnostic in it, spots Records that are thin, stale or missing a field, fills gaps from their own searching so that each added value persists for everyone, and exports the landscape.
- **UJ-3. DxP prepares the monitored-update Digest.** *Trimmed (pivot, 13 Nov): the run is started on demand over a selected trial set; scheduled scans and the Digest are deferred. UJ-5 replaces it as the demo path.* On a schedule, agents scan the approved Sources, apply the Maturity gate, match each Finding to a tracked Diagnostic where one exists, and draft a Proposed change at field level. The data curator receives a Digest sized for an episodic user and accepts, edits or rejects each Proposed change.
  **Edge case:** silent overwriting. If a value changes without showing what changed and why, UJ-1 inherits values nobody vouched for.
- **UJ-4. Someone captures a lead at a congress.** **Deferred (pivot, 13 Nov).** A user learns of an untracked Diagnostic in a conversation. On a phone, on poor wifi, they submit a Provider name, a note or a photograph of a poster. An agent fills what fields it can, flags what is missing and checks for a duplicate Provider. The user confirms or corrects. The Record is marked partial and manually sourced, and joins the Monitored set.

## 3. Glossary

- **Diagnostic** — The thing DxP tracks: a test or testing approach for cancer, from an early biomarker signal to a named assay offered by a Provider. One Diagnostic has one Record.
- **Record** — The structured entry for one Diagnostic. Made of fields; every field value carries Evidence.
- **Finding** — One piece of information from a Source about a Diagnostic, such as a study readout, a trial registration or an approval.
- **Source** — A place DxP scans. Approved Source types are peer-reviewed literature databases, clinical trial registries, regulatory filing and approval records, and Provider websites.
- **Source item** — One document from a Source, such as one trial registration or one abstract.
- **Evidence** — The Source, the supporting quote and the study context behind one field value.
- **Performance value** — A measured figure such as sensitivity or specificity, held for one tumour type and one Tumour stage, with its study context: population, cohort or randomised, retrospective or prospective, analytical or clinical validation, and sample count. Later development; not built on Saturday.
- **Lifecycle stage** — One of nine stages a Diagnostic moves through: discovery, assay development, analytical validation, clinical validation, clinical utility, regulatory approval, guideline inclusion, reimbursement, adoption. Not the same as Tumour stage.
- **Tumour stage** — The clinical stage of the cancer a Finding or Performance value applies to.
- **Maturity gate** — The credibility check applied to every Finding. It accepts Findings only from approved Source types, and marks a Diagnostic at discovery or assay development as Early research.
- **Early research** — The label shown on a Diagnostic at discovery or assay development, the two Lifecycle stages before any validation. The Diagnostic stays visible and still produces Alerts; the label says how far to trust it.
- **Proposed change** — An agent's draft change to one field of one Record, showing the current value, the new value and the Evidence.
- **Reviewer** — The person who accepts, edits or rejects a Proposed change. Usually the data curator.
- **Learned rule** — A stricter check for one field, drafted by DxP from a Reviewer's rejection or edit and the reason given, stated in plain language, and applied once the Reviewer confirms it.
- **Team** — A group of users who share one Team profile.
- **Team profile** — What a Team follows: tumour types, Categories, biomarkers, linked drugs and saved Intended uses, plus what its members asked, opened and dismissed.
- **Alert** — A notice to a Team about one Diagnostic, sent under FR-12 and FR-13.
- **Digest** — The periodic summary of Proposed changes and Alerts.
- **Intended use** — A stated clinical purpose for a Diagnostic, such as monitoring one tumour type at one Tumour stage.
- **Indication** — The tumour type, Tumour stage and clinical use that a value or an Intended use applies to.
- **Shortlist** — The Diagnostics a user picks for one Intended use.
- **Category** — A group of Diagnostics that share a detection approach or modality.
- **Provider** — The company or laboratory that offers a Diagnostic.
- **Baseline load** — The first ingest. It creates Records, sends no Alerts, and leaves out Source items from the last four weeks.
- **Held-back set** — The real Source items from the last four weeks, ingested after the Baseline load so that updates and Alerts come from real data.
- **Selected trial set** — The 20 named public ClinicalTrials.gov trials that a Saturday run works over, each naming an FDA-listed lung assay. They are fetched by NCT ID during the event (NFR7) and processed in a fixed order, NCT04712877 first. The list is in §4.1, "Data notes".
- **Monitored set** — The Diagnostics that the scheduled scans keep up to date.
- **Gold set** — The 30 to 50 hand-labelled Source items used to measure extraction accuracy.
- **Graph view** — The visual map of Diagnostics, biomarkers, tumour types, trials, drugs and Providers, and the connections between them.
- **Run** — One execution of the agent, with its own `run_id`. Every write, event and external action the agent makes belongs to one Run.
- **Run identity** — The facts stamped on a Run and on everything it does: the executing agent (`agent`), model, prompt version, policy-set version, the Grant version, and the principal who started the Run (`initiated_by`). Resolved on the server, never taken from the client.
- **Grant** — A stored permission for one agent: which Team's Diagnostics it may touch, which destinations (the Record ledger, `ledger`, or the Slack channel, `slack:#all-mango-db-hackathon`), which actions, an expiry, and which principals may start Runs under it (`startable_by`). A Grant has a version.
- **Policy** — A hand-written, versioned rule the agent's actions are checked against. Policies are grouped into a policy set, which also has a version: the hash of its sorted members.
- **Decision** — The stored record of one Policy gate evaluation, allowed or blocked, with every check and the Grant and policy-set versions evaluated (FR-34).
- **Action** — One thing the agent tries to do that has an effect: a write to a Record (`file_proposal`) or a Slack alert (`notify_slack`). Every Action has an action ID, a status and a decision. A notification Action's status is `queued`, `dispatching`, `delivered`, `failed` or `unknown`, and is shown as `reconciling` at read time only.
- **Policy gate** — The five checks run before every Action (FR-33). An Action runs only if all five pass.
- **Blocked action** — An Action that failed the Policy gate. It changes nothing and calls nothing; it leaves one blocked Decision and one `action_blocked` event that carries the decision ID.
- **Audit event** — The stored record of one outcome for an Action or Decision, stamped with the Run identity, Grant version and policy-set version.
- **Slack alert** — The Block Kit message the agent posts to Slack `#all-mango-db-hackathon` through an incoming webhook, so that a person reviews a Proposed change in DxP. It carries a "Review in DxP" link and an "Open diagnostic" link, and no buttons. It only notifies: approval and rejection happen in DxP, never in Slack. The real external action for Saturday.
- **Stop** — The control that ends a Run. After a Stop, no new Action is admitted; admitted Actions may finish while the Run is `stopping`.
- **Atlas Sandbox** — The MongoDB Atlas environment the organisers provide. Finalists must build on it.

## 4. Features

### 4.1 Monitoring and the Maturity gate — P1

Agents scan the approved Sources on a schedule and on demand, with nobody logged in. Everything a person sees has been through the Maturity gate. Realizes UJ-3.

*Pivot, 13 Nov:* on Saturday the agent runs on demand over the Selected trial set. Scheduled scans, Tavily web searches and the full Baseline load are deferred.

- **FR-1. Unattended scan.** *Trimmed (pivot, 13 Nov): on-demand runs only; scheduled scans and web sources are deferred.* The system scans every approved Source type on a schedule and can be triggered manually. *Test:* a scan completes and records its Findings with no user session open.
- **FR-2. Maturity gate.** The system accepts Findings only from approved Source types, and marks a Diagnostic at discovery or assay development as Early research wherever it appears. A Diagnostic whose Lifecycle stage cannot be determined is shown as "stage not determined" `[ASSUMPTION]`. *Test:* a Diagnostic at discovery or assay development carries the Early research label in every table, Alert, Digest and Graph view. Numeric thresholds (sample count, study design) are later development.
- **FR-3. Match before create, no duplicates.** The system identifies each Diagnostic by a defined match key, attaches a Finding to the existing Diagnostic where the key matches, and creates a new Diagnostic only when none does. Parallel processing never creates a duplicate. The match key is set in architecture. *Test:* processing the same batch twice, or two Source items about one Diagnostic at the same moment, leaves one Record.
- **FR-4. Batch processing.** *Trimmed (pivot, 13 Nov): a run covers the Selected trial set (20 trials) at lower concurrency, not 300 to 500 items.* The system processes a batch of 300 to 500 Source items in parallel and shows progress. *Test:* a live count of processed and failed Source items, and of Diagnostics marked Early research, is visible during the run.
- **FR-30. Baseline load and Held-back set.** *Trimmed (pivot, 13 Nov): the comprehensive Baseline load is deferred. A small FDA seed stands in for it, and the Selected trial set stands in for the Held-back set. Selected trials are stored with `window: "selected"`, not `heldback`, and are called "the selected trials" (readiness fix D54).* The first ingest is a Baseline load: it creates Records and sends no Alerts. It leaves out Source items from the last four weeks. That Held-back set is ingested afterwards, so that Proposed changes, Lifecycle stage changes and Alerts are produced by real data. *Test:* the Baseline load produces zero Alerts; ingesting the Held-back set produces at least one Proposed change and one Alert.

**Data notes (updated 14 Nov, readiness fixes D30 to D32 and D45).**

- **The Selected trial set is named.** Twenty public ClinicalTrials.gov trials that name an FDA-listed lung assay, fetched by NCT ID during the event and processed in this order:
  1. NCT04712877
  2. NCT06284317
  3. NCT04591431
  4. NCT05715229
  5. NCT03248089
  6. NCT03615443
  7. NCT05361564
  8. NCT04265534
  9. NCT04698681
  10. NCT03576937
  11. NCT04624373
  12. NCT04566614
  13. NCT06918782
  14. NCT05846594
  15. NCT04223596
  16. NCT04087473
  17. NCT03199651
  18. NCT03521154
  19. NCT06146920
  20. NCT05935384
- **Aliases.** Aliases are hand-written during the event. "FoundationOne Liquid" maps to FoundationOne Liquid CDx, "Guardant360" to Guardant360 CDx, and "FoundationOne" (when not followed by "Liquid") to FoundationOne CDx.
  - The ID alias of a seeded Diagnostic is `normalise_name()` of the FDA list's trade-name column. `normalise_name()` removes "®" and folds case.
  - An FDA row's ID is `<PMA or 510(k) number>:<first 8 hex characters of sha1 of the normalised row>`, because one number covers many drug rows.
  - Extraction is given the seeded alias list, and the extracted assay name must be one of those aliases or `new`.
  - Both NCT04712877 Findings must resolve to the seeded FoundationOne Liquid CDx and FoundationOne CDx.
- **Team scope.** The Grant `lbdx@v1` (Team "Team Liquid Biopsy Dx") covers exactly these trade-name strings: "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay". Every other Diagnostic is out of scope, so a proposal for one is blocked by check 2 (FR-33).

### 4.2 Records with Evidence — P1

Each Diagnostic has one Record. This feature covers what DxP extracts when it finds a new Diagnostic. On Saturday that is the ten fields agreed with Medical, listed in the brief, plus regulatory status. Performance values and operational fields are later development. What triggers an update to a Diagnostic that DxP already tracks is a separate matter, covered in §4.3 and §4.4. Realizes UJ-1, UJ-2, UJ-5.

*Pivot, 13 Nov:* kept. Evidence is what makes the agent's actions worth auditing. On Saturday it is shown in one minimal Record and Review screen.

- **FR-5. Structured extraction.** The system fills each Record field from a Finding in a fixed format, with the supporting quote for every field. *Test:* every populated field opens to a quote from its Source.
- **FR-6. Performance by tumour type and Tumour stage.** *(Later development; out for Saturday.)* The system stores each Performance value against one tumour type and one Tumour stage with its study context, never as one figure per Diagnostic. *Test:* two values from different Tumour stages are never merged or compared as the same measure.
- **FR-7. No uncited values.** The system never displays a field value without Evidence. *Test:* removing a value's Evidence removes the value from every view.
- **FR-8. Explicit no-data state.** *Trimmed (pivot, 13 Nov): applies to the Record and Review screen only; the comparison table is deferred.* The system shows "no data for this indication" where nothing is published. *Test:* a no-data cell is distinguishable from a cell that is still loading.
- **FR-9. Standard terms and synonyms.** **Deferred (pivot, 13 Nov).** The system maps terms to standard names and finds a Diagnostic by any of its synonyms. Unmatched terms go to the Reviewer. *Test:* a search for "liquid biopsy" returns ctDNA Diagnostics.
- **FR-10. Operational fields.** *(Later development; out for Saturday.)* A Record holds sample volume and turnaround time. Regulatory status is not part of this requirement; it is in for Saturday under §4.2. *Test:* each can be used as a filter in FR-23.

### 4.3 Lifecycle tracking and Alerts — P1

DxP places every Diagnostic at a Lifecycle stage and keeps the history. A Diagnostic that matches a Team profile produces an Alert at any Lifecycle stage, discovery included, and whatever its credibility. Realizes UJ-3.

*Pivot, 13 Nov:* Lifecycle history is kept as part of the Record. Team Alerts are deferred. *Updated 14 Nov:* no Lifecycle stage change is demonstrated on Saturday; the demo question is about a trial filed against a Diagnostic (UJ-5).

- **FR-11. Lifecycle stage with history.** The system assigns each Diagnostic one Lifecycle stage, with Evidence, and keeps every earlier stage and its date. *Test:* a Record shows when and on what Evidence the Lifecycle stage last changed.
- **FR-12. First Alert.** **Deferred (pivot, 13 Nov).** A Team receives a first Alert for a Diagnostic when it matches the Team profile, comes from an approved Source, and the Team has not been alerted about it before. The Alert is sent at whatever Lifecycle stage the Diagnostic is at, discovery included. Credibility never suppresses an Alert: where there is no credible validation, the Alert carries the Early research label. *Test:* a matching Diagnostic at discovery produces exactly one first Alert, labelled Early research.
- **FR-13. Update Alerts.** **Deferred (pivot, 13 Nov).** After the first Alert, a Team is alerted again only when the Diagnostic advances a Lifecycle stage, is adopted for a line of therapy, is used in a trial, or becomes standard of care. The system uses semantic matching, not keyword rules, to decide whether a Finding falls under one of these four topics, so that it is caught however it is worded. *Test:* a new Finding that changes none of these produces no Alert; a Finding that describes one of them in unusual wording still produces one.
- **FR-14. Why it matters.** **Deferred (pivot, 13 Nov).** The audio part returns as the stretch spoken audit briefing (FR-44). Each Alert states in one line why it matters to that Team, and links to the Evidence. An Alert can carry an audio briefing. *Test:* the line names the element of the Team profile that matched.

**Notes:** FR-13 reads the team's "treatments moving up the lifecycle" as Diagnostics moving up `[ASSUMPTION]`.

### 4.4 Agent proposals and review — P1

Agents never change a Record silently. They draft, a Reviewer decides, and DxP tightens its own checks from the decision. Realizes UJ-3, UJ-5.

*Pivot, 13 Nov:* proposals and decisions are kept in a minimal form. Every Proposed change is now an Action that passes the Policy gate (§4.10) before it is written. Learned rules and the Digest are deferred. *Updated 14 Nov:* in a live Run, a change to an existing Diagnostic is filed as a pending Proposed change and is never applied directly. It is applied only through a Reviewer decision (FR-16).

- **FR-15. Field-level Proposed change.** For a Finding about a tracked Diagnostic, the system drafts a Proposed change showing the current value, the new value and the Evidence. Examples of what triggers an update: a new study readout, a regulatory submission or approval, a new trial that uses the Diagnostic, adoption for a line of therapy, and a guideline recommendation. A Proposed change either sets a single-valued field or adds an entry to a list-valued field. Trials, study results and linked drugs are lists, so a new trial is added and never overwrites an earlier one. *Test:* a new readout proposes a change to the key result, such as a sensitivity figure; a regulatory submission proposes a change to regulatory status; a second trial for one Diagnostic leaves the first in place.
- **FR-16. Accept, edit or reject.** *Trimmed (pivot, 13 Nov): minimal decisions API and one Record and Review screen.* A Reviewer can accept, edit or reject each Proposed change. An accepted change updates the Record with its Evidence attached. Values in a newly created Record are marked unreviewed until a Reviewer accepts them. A Lifecycle stage changes only through an accepted Proposed change. *Updated 14 Nov:* applying an accepted Proposed change is all or nothing and recoverable. The proposal moves from `pending` to `applying` (claimed) to `applied`. The Diagnostic update records the proposal ID in `applied_proposal_ids` and runs only if the ID is not already there, so running it twice changes nothing. On recovery, a proposal stuck in `applying` reruns the guarded update and then marks itself `applied`.
  - **Apply belongs to the ledger.** Claim, guarded update and recovery live in the ledger's apply module, so the seed and the first integration do not depend on the review work. The Reviewer decision path calls the ledger's apply for the proposal. Recovery runs at API start, at the start of every Run and on every decision call.
  - **Apply is complete and recoverable.** The Diagnostic update is one guarded update. The derived edges are upserted after it, and the `value_applied` event is emitted with a `dedupe_key`. Recovery always re-upserts the edges and re-emits the event, whatever the guard returns. An edge's `run_id` is set only when the edge is first inserted, so a later Run never takes over an earlier Run's edge.
  - **No live apply, even on new Diagnostics.** In a live Run the agent never applies a change; it only files Proposed changes. There is no shortcut that applies changes at once to a Diagnostic the Run itself created. Creating a Diagnostic outside the Grant's Team scope is blocked by check 2 (FR-33).
  - **Unreviewed values.** A Reviewer accepts, edits or rejects an unreviewed value through the value-review route, `POST /diagnostics/<dx_id>/values/<value_id>/review`, as the `review_value` action (FR-32, FR-33).

  *Test:* no value in an existing Record changes without a Reviewer action logged against it, and every unreviewed value is visibly marked; a proposal interrupted in `applying` and recovered is applied exactly once, with its edges present once and its `value_applied` event recorded once; an edge first created by one Run keeps that Run's `run_id` after a later Run touches it.
- **FR-17. Prior value retained.** The system keeps the previous value and its Evidence after every change. *Test:* any field shows its earlier values, who accepted each change and when.
- **FR-18. Confidence and automated check.** Each extracted field carries a confidence score and the result of an automated check against its quote. The check confirms that the quote appears word for word in its Source item. Low-confidence fields are marked for the Reviewer. *Test:* a quote that does not appear in its Source item fails the check and its value is not displayed; a field whose quote does not support its value also fails.
- **FR-19. Learned rule.** **Deferred (pivot, 13 Nov).** The stretch item FR-45 replaces it: a rejection drafts a Policy for explicit approval. A Reviewer who rejects or edits a Proposed change gives a reason. The system drafts a Learned rule for that field from the reason, shows it in plain language, and applies it once the Reviewer confirms it. A confirmed rule flags later and pending Proposed changes that break it; it does not withdraw them. A Reviewer can switch a Learned rule off. *Test:* after one rejection with a reason and a confirmed rule, a pending Proposed change with the same fault is flagged with the rule named; switching the rule off removes the flag.
- **FR-20. Digest.** **Deferred (pivot, 13 Nov).** The system sends a Digest of Proposed changes and Alerts, weekly or when an event warrants. *Test:* a Team with nothing applicable receives no Digest.

**Notes:** Before the pivot, this feature was the wow moment: agents working with memory (FR-19, FR-28), shown in the Graph view. From 13 Nov the wow moment is the governed run in §4.10: a real alert in Slack, a blocked action and a replayable audit trail, with the MongoDB capability named at each step. The mapping is in `addendum.md` §3 and §5.

### 4.5 Intended-use shortlisting — Deferred (pivot, 13 Nov)

Realizes UJ-1. On Saturday the filters and table columns come from the ten agreed fields and regulatory status. Filtering on minimum sensitivity and specificity, and on operational fields, is later development.

- **FR-21. State the need.** **Deferred (pivot, 13 Nov).** A user describes an Intended use in plain language or sets filters on the agreed fields, such as modality, tumour type, Tumour stage, sample type, clinical use and regulatory status. The system turns it into one query across all Records. *Test:* the parsed query is shown and can be corrected.
- **FR-22. Comparison table.** **Deferred (pivot, 13 Nov).** The system returns one row per Diagnostic and one column per criterion asked for, with the Evidence inline for each value. *Test:* no step requires opening an individual Record to read a value.
- **FR-23. Operational filters.** *(Later development; out for Saturday.)* The user narrows the table on the operational fields in FR-10.
- **FR-24. Shortlist.** **Deferred (pivot, 13 Nov).** The user saves a Shortlist against a named Intended use. *Test:* reopening the Intended use shows its Shortlist.
- **FR-25. Export.** **Deferred (pivot, 13 Nov).** The system exports the comparison or Shortlist with every reference intact. *Test:* every value in the export carries its Evidence.

### 4.6 Graph view — P1, trimmed to the run-scoped impact view

The Graph view replaces the galaxy view described in the brief. It shows the connections between clusters of Diagnostics, not only the clusters. Realizes UJ-1, UJ-2.

*Pivot, 13 Nov:* the graph is kept only as the run-scoped impact view (FR-43), a supporting screen.

- **FR-26. Connected graph.** *Trimmed (pivot, 13 Nov): the graph is scoped to one Run by `run_id` and adds Slack alerts as notification nodes; see FR-43.* The system shows Diagnostics, biomarkers, tumour types, trials, drugs and Providers as nodes, with the links between them, including links that cross Categories. Selecting a node opens its Record or Evidence. *Test:* a Diagnostic's linked trial, drug and Provider can each be reached from it in one step.
- **FR-27. What changed.** **Deferred (pivot, 13 Nov).** The Graph view marks nodes and links that are new or changed since the user's last visit, and each Diagnostic's Lifecycle stage. *Test:* a Proposed change accepted since the last visit is marked on its node.

### 4.7 Memory across sessions — Deferred (pivot, 13 Nov)

Realizes UJ-1 and the returning-user job.

- **FR-28. Resume.** **Deferred (pivot, 13 Nov).** The system keeps the Team profile across sessions and, on return, shows what changed since the last visit and offers the last Intended use and Shortlist. *Test:* closing and reopening a session restores the Team's context with no input from the user.

### 4.8 Category landscape — Deferred (pivot, 13 Nov)

Realizes UJ-2.

- **FR-29. Landscape with gaps.** **Deferred (pivot, 13 Nov).** A user selects a Category and sees the full field set for every Diagnostic in it, with thin, stale or incomplete Records marked. A value the user adds by hand is saved for everyone, marked as manually sourced with submitter and date, and the landscape can be exported. *Test:* a value added by one user is visible to another, with the manual mark.

### 4.9 Capture on the go — Deferred (pivot, 13 Nov)

Realizes UJ-4. No numbered requirements. **Deferred (pivot, 13 Nov).** Photographs of congress posters are out for Saturday, for the same licensing reason as congress abstracts. A submission of a name or note becomes a partial Record, clearly marked partial and manually sourced, checked for a duplicate Provider, and added to the Monitored set.

### 4.10 Governed agent actions — Core (new, 13 Nov)

This is the product for Problem Statement 1. The agent may act only under a named identity, a scoped Grant and a policy check made before the action. Every decision leaves an audit event a reviewer can replay. Realizes UJ-5. Epic 9 in `epics.md` implements it.

Each requirement is labelled **Core**, **Supporting** or **Stretch**. Core requirements must be green by 14:30 on Saturday. *Updated 14 Nov:* supporting and stretch work may be built before 14:30 by agents not needed on the core. It never blocks a core PR. If the core loop is not green at 14:30, that work pauses. Each supporting or stretch item has its own acceptance check and joins the rehearsal only if it passed. The audio briefing (FR-44) may be built from 13:00 behind a flag and merges only after the 14:30 loop is green.

#### Identity and authority

- **FR-31. Run identity.** *Core. Updated 14 Nov.* A Run has two identities: who started it and who executes it. Every Run records `initiated_by` (the principal who started it, resolved from the caller's key) and `agent` (the executing agent principal named by the Grant), plus its `run_id`, model, prompt version, policy-set version and the Grant version pinned at start. The server resolves these when the Run starts. The worker executes with the agent's key and the `run_id`. Every agent write requires a `run_id`, and the worker's key must resolve to the Run's `agent`. Every write, event and external Action in the Run is stamped with this identity. Two kinds of write carry `run_id: null`, and no agent write does:
  - **Reviewer decisions** carry a stamp for the Reviewer and `cause: { proposal_id, origin_run_id }`, linking the decision to the Proposed change and the Run that filed it. Their Decisions carry `agent: null` and `initiated_by: <reviewer principal>`.
  - **Seeding** runs only from the command line with a dedicated seed key. Its writes carry the stamp `{ kind: "seed", principal: "seed" }`. Its Decisions carry `agent: "seed"` and `initiated_by: "seed"`.

  *Test:* any Record change, audit event or Slack alert from a Run shows the same `run_id` and identity; an agent write with no `run_id`, or from a key that does not resolve to the Run's `agent`, is refused; a Reviewer decision shows `run_id: null` and its `cause`.
- **FR-32. Grants and server-side authority.** *Core. Updated 14 Nov.* Grants are stored in Atlas, each with a version: the agent it authorises, Team, destinations, allowed actions, expiry, and `startable_by` (the principals allowed to start Runs under it). A Run is started with `POST /runs { grant_id, set }`. There is no `team_id` in the body: the Grant defines the Team. The web app lists the Grants the caller may start, each labelled with its Team; there is no separate Team picker. The server resolves the caller from `X-DxP-Key`, loads the latest version of the Grant, checks that it is active and that the caller is in `startable_by`, then creates the Run with `agent` from the Grant, `initiated_by` from the caller and the Grant version pinned. Grant versions are selected like Policies (FR-33): latest version first, then status, so a newer `revoked` or `expired` version blocks. A name sent by the client never gives permission.
  - **Keys resolve whatever the Grant's status.** The principal is found by `key_hash` across all Grant versions, whatever their status. A 401 means only an unknown key. A revoked or expired Grant is caught by check 1 (FR-33) and recorded as a blocked Decision (FR-34).
  - **Seeded Grants.** Grants are seeded for the demo through the seed path (FR-31). *Updated 14 Nov (Slack change S1, S2, S8).*
    - Agent grant `lbdx@v1`: agent principal `dxp-curator`, Team "Team Liquid Biopsy Dx", actions `[file_proposal, notify_slack]`, destinations `[ledger, slack:#all-mango-db-hackathon]`. A notification to any other destination fails check 3 (FR-33).
    - Seed grant `seed@v1`: principal `seed`, actions `[apply_value]`, destination `ledger`, scope `{ all: true }`. `all: true` is valid only for the seed principal; the validator rejects it on any other Grant.
    - Reviewer grant `sam@v1`: principal `sam` (Sam), actions `[decide_proposal, review_value, resolve_notification]`, destination `ledger`, scope the same `diagnostic_ids` as the agent's Grant.
  - **`review_value`** is an action kind, used by `POST /diagnostics/<dx_id>/values/<value_id>/review` when a Reviewer accepts, edits or rejects an unreviewed value (FR-16).
  - **`resolve_notification`** is an action kind, used by `POST /actions/<action_id>/resolve` when a Reviewer settles an `unknown` Slack alert (FR-36).

  *Test:* a request that names a different actor in its body is still evaluated against the principal its key resolves to; a caller not in `startable_by` cannot start a Run; a Grant past its expiry, or whose latest version is revoked, allows nothing and its key's requests leave blocked Decisions, not 401s; an unknown key gets 401; a non-seed Grant with `all: true` is rejected by the validator; a `notify_slack` Action to a destination other than `slack:#all-mango-db-hackathon` is blocked by check 3.
- **FR-33. Versioned policies checked before every Action.** *Core. Updated 14 Nov.* Policies are hand-written, versioned and stored in Atlas with schema validation. **Selection:** for each Policy ID, take the latest version first, then check its status; only versions whose latest status is `active` are members of the set. The set's membership is persisted in `policy_sets` as `{ _id: policy_set_version, members: ["<policy_id>@v<n>", ...], created_at }` when the set is first used; the version is the hash of the sorted members. Before every Action, the Policy gate runs five checks, in this order:
  1. The Run has an active, unexpired Grant. The gate evaluates the latest version of the Grant. If it differs from the version pinned at start and is not active, this check fails.
  2. The Diagnostic is in the Team scope the Grant authorises.
  3. The destination and the Action type match the Grant. For the agent, the actions are `file_proposal` and `notify_slack`, and the destinations are `ledger` and `slack:#all-mango-db-hackathon`.
  4. The required evidence checks passed (the quote is found and supports the value, as in FR-18). This check applies only to `file_proposal` and `notify_slack`. It records `n/a` for `apply_value` (seed), `decide_proposal`, `review_value` and `resolve_notification` (readiness fix D50). An `edit` or `reject` must carry a reason instead, and a `resolve_notification` carries a note.
  5. The Run is still authorised to act: the Action holds an admission for this Run, and the Run is not `stopped`. New admissions are granted only while the Run is `running`. An admitted Action may finish while the Run is `stopping` (FR-38).

  The Action runs only if all five pass. Every evaluation, allowed or blocked, is recorded as a Decision (FR-34) that names the Grant actually evaluated (`grant_id@version`) and the `policy_set_version`. *Test:* changing a Policy creates a new version and later Decisions cite it; earlier Decisions keep the version they were made under; the members of any cited `policy_set_version` can be read back from `policy_sets`; a Reviewer decision records check 4 as `n/a`, and an edit or reject without a reason is refused.
- **FR-34. Every gate evaluation is a Decision; blocked actions change nothing.** *Core. Updated 14 Nov.* The system writes one document to `decisions` for every Policy gate evaluation, allowed or blocked. Each keeps: `decision_id`, `run_id`, the agent and `initiated_by`; the Action kind and its inputs, the Evidence reference (Source item, quote, checks) and the destination; every check with its result and detail; the Grant evaluated (`grant_id@version`) and the `policy_set_version`; the outcome (`allowed` or `blocked`) and timestamps. An allowed Decision creates an Action that points back to it (`decision_id`). A blocked Decision creates no Action, changes no business record and makes no external call; the `action_blocked` event carries its `decision_id`. Any Decision can be reconstructed in full from `GET /decisions/<decision_id>`. `GET /actions/<action_id>` stays for Action status and results. *Test:* an out-of-scope Action leaves the Records unchanged and posts nothing to Slack, and `GET /decisions/<decision_id>` for it shows every check, the one that failed, and the Grant and policy-set versions evaluated.

#### The external action

- **FR-35. Slack alert.** *Core. Updated 14 Nov (Slack change S1 to S6, readiness fixes D42, D46, D47).* The Policy gate is evaluated once per change: the ledger files each admitted change once, and each filed proposal gets its own `notify_slack` Action, so there is one Slack alert per proposal. For an allowed Proposed change, filed as pending, the agent posts a Slack alert as a `notify_slack` Action to the destination `slack:#all-mango-db-hackathon`, through the incoming webhook in `SLACK_WEBHOOK_URL`.
  - **The message** is a Block Kit alert with:
    - a header "New diagnostic evidence for review", plus the action ID;
    - the Diagnostic name;
    - the Evidence: the trial NCT ID with its ClinicalTrials.gov link, and the quote of at most 300 characters;
    - the Proposed change, for example "Add trial NCT04712877 to Trials";
    - who acted: the agent, the `run_id`, the Grant `{grant_id}@v{version}` and the policy set `ps_…`;
    - a context line: "Approve or reject in DxP. Slack only notifies."
  - **Links back to DxP**, built from `DXP_BASE_URL`: "Review in DxP" opens `${DXP_BASE_URL}/review?proposal=<p_id>`, the Review page with that proposal focused. The Review page loads the focused proposal with `GET /proposals/<p_id>`, which returns one proposal whatever its status; there is no `p_id=` query parameter. "Open diagnostic" opens `${DXP_BASE_URL}/diagnostics/<dx_id>`, the Record page. The sender refuses to start if `DXP_BASE_URL` is not set.
  - **Notify only.** The message has links and no interactive elements: no approve or reject buttons and no Slack actions. Slack sends nothing back to DxP, and DxP exposes no Slack callback route. Approval and rejection happen in DxP, never in Slack.
  - **The proposal points to its alert.** A Proposed change is read with `notification { action_id, status, posted_at }`. This field is read-time only: the API builds it from the proposal's `notify_slack` Action, and nothing writes it to the proposal document.
  - **No apply from the alert.** In a live Run the agent only files Proposed changes, on new and existing Diagnostics alike, and applying one happens only through a Reviewer decision in DxP and the ledger's apply (FR-16).

  *Test:* an allowed Action produces one real alert in `#all-mango-db-hackathon`; its "Review in DxP" link opens the focused proposal and its "Open diagnostic" link opens the Record on the deployed web app; the Record is unchanged until a Reviewer decides the proposal in DxP; the sender does not start without `DXP_BASE_URL`.
- **FR-36. Ambiguous external result.** *Core. Updated 14 Nov (Slack change S7, S8).* A webhook post cannot be looked up afterwards, so DxP records exactly what it observed. The system saves the action ID in Atlas before posting, and includes it in the alert header. All status updates are conditional on the current status.
  - **HTTP 200 with body `ok`:** `delivered`, with the time posted and the response.
  - **HTTP 4xx** (for example `invalid_payload`, `no_service`, `channel_not_found`): `failed`, never retried.
  - **HTTP 429:** nothing was posted. Retry once, after `Retry-After`, while still holding the claim. A second 429 means `failed`.
  - **Timeout, connection error or HTTP 5xx:** the outcome is ambiguous, so the Action is `unknown`. It is never retried automatically.
  - **Manual resolution.** A Reviewer settles an `unknown` alert in DxP with `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }`, after checking `#all-mango-db-hackathon` for the action ID. The call is gated as kind `resolve_notification` and audited as a Decision with the Reviewer's stamp. The Action then carries `resolution { outcome, note, decision_id, by, at }`.

  *Test:* with a simulated timeout, the Action shows `unknown` and no second post is made; a 4xx leaves `failed` with no retry; a single 429 is retried once after `Retry-After`, and a second 429 leaves `failed`; a Reviewer resolves an `unknown` Action as `delivered` or `failed`, and the resolution appears in the audit with the Reviewer's stamp and note.
- **FR-37. Atomic claim.** *Core. Updated 14 Nov.* An Action moves from `queued` to `dispatching` through one conditional update in Atlas, after its action ID is saved. Only the worker whose update succeeds may post to Slack. *Test:* two workers retrying the same Action at the same moment produce one webhook post and one alert.

#### Control and audit

- **FR-38. Stop control.** *Core. Updated 14 Nov.* A person can stop a Run. Check 5 of the Policy gate, "run still authorised", means: the Action holds an admission for this Run, and the Run is not `stopped`. New admissions are granted only while the Run is `running`. An admitted Action may finish while the Run is `stopping`. Admissions are stored in `admissions`, unique on `(run_id, item_key)`, with status `admitted`, `released` or `abandoned` and a lease `expires_at`.
  - **One admission per Action.** `item_key = "<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"`. The admission is taken after extraction and before the Policy gate, so one Source item that yields two Actions takes two admissions.
  - **One public API.** `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle` and `runs.finish`, implemented in `runs/admissions.py`. Every document uses these names.
  - `runs.admit(run_id, item_key)` inserts an admission only if the Run is `running`. The conditional check and the insert happen in one transaction, or the Run's `admitting` counter guards them, so a stop and an admission cannot race.
  - `runs.release(admission_id)` changes `admitted` to `released` with a conditional update, so an admission is released once and a second release does nothing.
  - `runs.sweep` marks admissions past their lease `abandoned`. Any Action they hold that is `dispatching` is marked `unknown` and never retried; a Reviewer resolves it in DxP, as in FR-36. Any Action they hold that is still `queued` is marked `failed` with reason `abandoned_before_send`; it was never sent, so this is safe.
  - Updates to `delivered` and `failed` are conditional on the Action's current status, so a slow worker never overwrites an `unknown` set by the sweep.
  - `GET /runs/<run_id>` never calls Slack. It starts the sweep in the background and returns the current state, showing Actions the sweep is still settling as `reconciling` (a read-time status only).
  - **`settle` only stops.** `runs.settle(run_id)` only moves a Run from `stopping` to `stopped`, once no `admitted` admission remains. `runs.finish(run_id)`, called by the pipeline after the last item, moves a Run from `running` to `done` once no admission remains. A Run becomes `failed` only when the pipeline raises an error it cannot recover from.

  *Test:* stopping mid-run admits no further Action; an admitted Action finishes while the Run is `stopping`; releasing an admission twice has no further effect; a `dispatching` Action held by an abandoned admission becomes `unknown` and is not retried, and a `queued` Action it held becomes `failed` with reason `abandoned_before_send`; a slow worker's late `delivered` does not overwrite `unknown`; `settle` on a `running` Run changes nothing; the Run moves from `stopping` to `stopped` once no `admitted` admissions remain, and from `running` to `done` through `finish`.
- **FR-39. Audit reconstruction.** *Core. Updated 14 Nov.* `GET /runs/<run_id>/audit` returns the Run's Decisions (allowed and blocked, FR-34) and Actions in order, then a section **"After the run"** with the Reviewer decisions whose `cause.origin_run_id` is this Run, including any `resolve_notification` Decision. *Updated 14 Nov (Slack change S9).*
  - **Each notification Action keeps:** its `decision_id` (the agent, `initiated_by`, the Grant evaluated, the policy set and every check); its inputs and Evidence reference; the destination; timestamps (queued, claimed, posted, observed); and the notification result, `result { http_status, response_body, posted_at, link_urls { review_url, diagnostic_url } }`, or `unknown` until a Reviewer resolves it, then `resolution { outcome, note, decision_id, by, at }`. It never stores the webhook URL.
  - **Live review status.** Next to each notification, the audit shows the proposal's live DxP review status: pending, applied or rejected, with who decided and when.
  - Each blocked Decision can be opened in full through `GET /decisions/<decision_id>`. For any Record change it answers "who authorised this Action, and under what authority?" from the Decision's `authorised_by`.

  *Test:* from the audit alone, a reviewer can name the person who started the Run, the executing agent, the Grant, the policy version and the Evidence behind the trial filed against FoundationOne Liquid CDx, the Slack alert's result, the proposal's live review status, the Reviewer decision that applied it, the blocked Decision for FoundationOne CDx, and the result of every Action in the Run.
- **FR-40. Run console.** *Core. Updated 14 Nov.* One screen shows the Run identity card and Grant scope, a list of Actions with their status, and the stop button. Each notification Action's row shows "Slack alert delivered" with the time, or Failed, Unknown or Reconciling; an Unknown row tells a Reviewer to check `#all-mango-db-hackathon` for the action ID and offers a Resolve control (FR-36). The Resolve control shows only when the signed-in principal's `actions`, from `GET /whoami` (`Principal { id, name, kind, actions }`, the actions of the caller's current Grant), include `resolve_notification` (readiness fix D53). Other rows show allowed, blocked or in flight. A Run is started by choosing a Grant, labelled with its Team (FR-32). The screen is complete with the live feed (FR-42) switched off: it polls until that feed passes its check. *Test:* a person can start a Run, watch an Action be blocked with its failed check named, and stop the Run from this screen, with the live feed off.
- **FR-41. Audit view.** *Core. Updated 14 Nov.* One screen reconstructs a Run from FR-39: its Decisions and Actions in order, blocked Decisions included with their failed check, then the "After the run" Reviewer decisions. Each notification entry shows its result (delivered with the time, failed or unknown) and the proposal's live DxP review status. An unknown entry offers the same Resolve control as the Run console, shown under the same rule (FR-40). It answers "who authorised this" for a selected entry, from the Decision's `authorised_by`. *Test:* the demo question "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?" is answered from this screen without opening a log, and the blocked FoundationOne CDx Decision opens to its full detail.

#### Supporting

- **FR-42. Live action feed.** *Supporting. Updated 14 Nov.* The Run console updates as Actions are decided, through Atlas change streams. Until this feed passes its acceptance check, and whenever change streams are not available on the Atlas Sandbox tier, the screens poll `GET /runs/<run_id>` and `GET /runs/<run_id>/audit`, and the Review count polls `GET /proposals?status=pending`. The Run console is complete with this feed switched off (FR-40). *Test:* a new Action appears on the console within a few seconds without a page reload.
- **FR-43. Run-scoped impact view.** *Supporting. Updated 14 Nov.* A graph of exactly what one Run touched, fed by `run_id`. It separates two kinds of node:
  - **Changed elements:** the values, Proposed changes, edges and notification nodes (`notification:<action_id>`, one per Slack alert) the Run itself created or changed, each with its `run_id`.
  - **Context:** a touched Diagnostic's other neighbours (trials, biomarkers and so on), shown only when asked ("Show context"), visibly marked as context and not attributed to the Run.

  Links to the impact view are hidden when its `impact` flag is off.

  *Test:* every changed element in the view traces back to an entry in that Run's audit; context appears only on request, is marked as context and carries no `run_id` from this Run; nothing from other Runs is attributed to it.

#### Stretch

- **FR-44. Spoken audit briefing.** *Stretch.* ElevenLabs reads a short audit summary of one Run aloud. The Audit view links to it with a "Listen" link that opens a separate briefing page. Replaces the audio part of FR-14 and targets the ElevenLabs prize.
- **FR-45. Rejection drafts a Policy.** *Stretch.* When a Reviewer rejects a Proposed change with a reason, the system drafts a new Policy version for explicit approval. The draft is limited to the checks the Policy gate supports. Model text never becomes executable authority by itself.
- **FR-46. Scoped reversal of a Run.** *Stretch.* A person can reverse the Record changes of one Run, recorded as new audited Actions. Built only if the core loop is green by 14:30.

#### Required acceptance behaviours

These six behaviours are binding. Each must pass on the Atlas Sandbox before the demo.

| Concern | Requirement |
|---|---|
| Ambiguous result | FR-36 |
| Atomic claim | FR-37 |
| Stop semantics | FR-38 |
| Blocked action | FR-34 |
| Authority | FR-32 |
| Audit reconstruction | FR-39 |

## 5. Non-goals

- DxP is not patient-facing, is not a clinical decision tool and gives no medical advice about anyone.
- DxP is not a dashboard. The screens inspect and control the agent; the agent is the product.
- DxP is not a news feed. Updates to tracked Diagnostics matter more than a stream of novelty.
- Agents do not change a Record without a Reviewer's decision, and do not act anywhere without passing the Policy gate.
- Model output never becomes authority. Grants and Policies are written by people.
- DxP is not built for daily use.

## 6. Scope for Saturday

### 6.1 In scope

Lung cancer only. Hacking runs from 10:45 to 17:00, two people. The priorities from the approved change:

- **Core:** §4.10 core requirements (FR-31 to FR-41), with the evidence work they rely on: FR-3, FR-5, FR-7, FR-11, FR-15 to FR-18, and trimmed FR-1, FR-4 and FR-30 over the Selected trial set. Milestone (SM-8): by 14:30 on the Atlas Sandbox, one Proposed change is filed as pending with a real Slack alert in `#all-mango-db-hackathon`, one out-of-scope Action is blocked before execution, and the audit reconstructs all three. Until the live feed lands, the console polls. *Updated 14 Nov:* the minimal Record and Review screen (FR-8, FR-16) is core, because core acceptance needs a Reviewer decision.
- **Supporting:** the live action feed (FR-42) and the run-scoped impact view (FR-26 trimmed, FR-43). Core never depends on them.
- **Stretch:** FR-44, FR-45, FR-46.
- **Timing for supporting and stretch work.** *Updated 14 Nov.* Agents not needed on the core may build it before 14:30. It never blocks a core PR. If the core loop is not green at 14:30, it pauses. The audio briefing (FR-44) may be built from 13:00 behind a flag and merges only after the 14:30 loop is green.

### 6.2 Out of scope for Saturday

- Everything marked **Deferred (pivot, 13 Nov)**: Find and the comparison table, Categories, the broad Home dashboard, Tavily and scheduled scans, quick capture, the comprehensive Baseline load, Learned rules, Team Alerts and the Digest, memory and resume.
- Tumour types other than lung.
- Congress abstracts, posters and presentations as a Source, and photographs of congress posters, for licensing reasons. Revisit with legal if the team wins.
- Fields beyond the ten agreed with Medical and regulatory status: Performance values by tumour type and Tumour stage, operational fields and operational filters (FR-6, FR-10, FR-23). Later development.
- Numeric thresholds for the Maturity gate. Later development.
- External actions other than a Slack alert to `#all-mango-db-hackathon`. Interactive Slack messages (buttons, Slack actions, callbacks into DxP) are out: the alert only notifies.
- The 3D body model and the 2D radar.
- Custom fine-tuned embeddings.
- Atlas's agent runtime.
- A live talking avatar.
- Recording what happened to a Shortlist (pilot proposed, deprioritised) and capturing advisor feedback. Both were inferred in the source journeys, not asked for `[ASSUMPTION]`.

## 7. Success metrics

**Primary**
- **SM-1.** Submitted by 16:55, before the 17:00 deadline, with a description, a public repository, a one-minute video and the team members. *Updated 13 Nov.*
- **SM-2.** The 60-second video shows the governed loop on real data, in four parts. *Updated 13 Nov. Updated 14 Nov (readiness fix D52).*
  - 0 to 10 s: the problem and the scope (identity card, Grant, policy set).
  - 10 to 30 s: the allowed proposal and its Slack alert, then the blocked change. NCT04712877 is filed against FoundationOne Liquid CDx as a pending Proposed change with its quote, and its Slack alert arrives in `#all-mango-db-hackathon`. Then the same trial's proposal for FoundationOne CDx is blocked before execution (check 2, outside the Team's scope): no Record change, no Slack message, one recorded Decision.
  - 30 to 45 s: stop the Run while items remain (stopping, then stopped).
  - 45 to 60 s: Sam approves the pending Proposed change in DxP, which appears under "After the run", then "who authorised this?" in the Audit view, answering "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"

  The Run starts at 0 s and is paced (`DXP_DEMO_PACE`), so NCT04712877 is the first item and the stop lands mid-run. The reset (NFR8) runs before the take. *Updated 14 Nov: same order as SM-4 and UJ-5 (readiness fix D33).*

  Validates FR-31 to FR-41.
- **SM-3.** A UJ-1 query returns a populated comparison table in which every displayed value has Evidence. **Deferred (pivot, 13 Nov).** Zero uncited values still applies to every Record value shown (FR-7).
- **SM-4.** The 3-minute live demo shows every behaviour Statement 1 asks for, in this order. The reset (NFR8) runs before it, and the Run is paced (`DXP_DEMO_PACE`) so NCT04712877 is the first item.
  1. Start a Run over the Selected trial set. The console shows identity and scope, and Actions arrive one by one.
  2. The proposal to add NCT04712877 to FoundationOne Liquid CDx is allowed: it is filed as pending and posts a real Slack alert, shown arriving in `#all-mango-db-hackathon` on the second screen. Its "Review in DxP" link opens the focused proposal. Then the same trial's proposal for FoundationOne CDx is blocked before execution, with check 2 (Team scope) shown as failed, and no Slack message is sent.
  3. The Run is stopped while items remain: stopping, then stopped.
  4. Sam approves the pending Proposed change in DxP, never in Slack; the approval appears under "After the run".
  5. The Audit view answers "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"

  The impact view, showing exactly what the Run touched, appears only if it passed its acceptance check. The spoken audit briefing (stretch) appears only if it passed its acceptance check after the 14:30 loop was green. No Lifecycle stage change is demonstrated. *Updated 14 Nov.*
- **SM-7.** The video and the project description open with the one-line description from §1. *Updated 13 Nov.*
- **SM-8.** By 14:30 on the Atlas Sandbox, the governed loop is proved without bypassing review: one Proposed change is filed as pending (never applied directly), one real Slack alert is delivered to `#all-mango-db-hackathon` (HTTP 200 `ok` recorded on the Action) and its "Review in DxP" link opens the focused proposal, one out-of-scope Action is blocked before execution, and the audit reconstructs all three with identity, Grant, policy version and result. Applying the Proposed change needs a Reviewer decision (FR-16) and is not part of this check; it is proved at core acceptance. *New 13 Nov. Updated 14 Nov.*
- **SM-9.** All six required acceptance behaviours in §4.10 pass on the Atlas Sandbox before code freeze at 16:30. *New 13 Nov.*

**Secondary**
- **SM-5.** Extraction accuracy per field on the gold set is measured and reported. Validates FR-5.
- **SM-6.** A top-three placing, or the Best Project Built with ElevenLabs prize.

**Counter-metrics (do not optimise)**
- **SM-C1.** Number of Alerts sent. More Alerts is the firehose the users do not want. Deferred with Alerts.
- **SM-C2.** Share of table cells filled. A blank cell is better than an uncited value. Counterbalances SM-3.
- **SM-C3.** Number of Source items ingested. Counterbalances SM-4: 20 trials is enough.
- **SM-C4.** Number of Actions allowed. A correctly blocked Action is a success, not a failure. Counterbalances SM-2. *New 13 Nov.*

## 8. Constraints and guardrails

NFR IDs match `epics.md`. New constraints from the participant guide are NFR12 to NFR15.

- **NFR1. Evidence.** Provenance is the product. Any shortcut that shows a value without Evidence fails the PRD.
- **NFR2. Human decision.** Every agent change to a Record is a Reviewer's decision, logged.
- **NFR3. Unattended operation.** *Trimmed (pivot, 13 Nov): on Saturday a person starts each Run; once started, it runs without a person in the loop until a Reviewer decision or a stop.* Scans, the Maturity gate and Proposed changes run with nobody logged in.
- **NFR4. Open data only.** Every Source item is openly and publicly available. Sources on Saturday are ClinicalTrials.gov and the FDA companion diagnostics list, fetched during the event (NFR7). PubMed is deferred. Provider websites through web search are deferred with Tavily. Nothing licensed or paywalled is ingested. The selected trials are real data from these Sources. Provider websites, if used later, are scanned only from an allow-list of domains, because the web search tool does not filter out licensed pages. PubMed abstracts are public but not licensed for redistribution: DxP shows short quotes with a citation and a link, and no abstract text is committed to the public repository or posted in a Slack alert.
- **NFR5. Real behaviour on camera.** *Updated 13 Nov and 14 Nov.* The video and the live demo show a real Slack alert arriving in `#all-mango-db-hackathon`, a real blocked Action and a real stop, each made live. Synthetic history may set the scene; it does not stand in for these.
- **NFR6. Synthetic data.** Synthetic Teams, Grants, session history and Reviewer corrections are labelled as synthetic wherever they appear.
- **NFR7. Event rules.** *Updated 14 Nov.* Only work built during the event may be highlighted. The README separates prepared material (planning documents, data fetchers, skills) from what was built on 14 November, in a table. The demo shows only what was built that day. No coding before 10:45 unless an organiser permits it in writing.
  - **No prepared code or assets are reused.** No code from `scripts/data/` or from any `dxp-*` skill is copied into `backend/` or `web/`, and none is run on Saturday. Skills are reference documentation for agents; every line of project code is written during the event.
  - **Disclosure does not authorise reuse.** The README lists prepared material so judges can see it, not so agents can use it.
  - **Data is fetched during the event.** The files in `data/` were downloaded and filtered before the event and are not loaded unless an organiser clears them in writing on Saturday morning. Otherwise the selected trials are fetched by NCT ID from the ClinicalTrials.gov API v2, and the FDA list of cleared or approved companion diagnostics is fetched and filtered to the lung rows, both during the event. The list of selected NCT IDs is a planning decision, written down in advance in §4.1 ("Data notes").
  - **Text wordmark.** The prepared logo images are not used unless an organiser clears them. The interface shows a text wordmark, "DxP", set in the interface font during the event.
  - `scripts/data/` and `data/` stay in the repository as history, each with a notice that they are not used on Saturday without written clearance.
- **NFR8. Time.** *Updated 14 Nov.* Hacking runs 10:45 to 17:00: 6 hours 15 minutes in total, two people, including recording and submitting. Submission is due at 17:00: description, public repository, a one-minute video and team members. The timeline:
  - 16:30: code freeze, then the reset.
  - 16:30 to 16:50: the video is recorded.
  - By 16:55: submit.
  - 16:55 to 17:10: the reset runs again.
  - 17:15: the 3-minute live demo for judging starts.

  **The reset.** A snapshot is taken after seeding and before any Run. The reset restores it with `mongodump` and `mongorestore`, so the Selected trials are unprocessed and no Run is in progress. It runs before the video and again before the live demo.
- **Agent Memory.** **Deferred (pivot, 13 Nov)** with memory and resume. If time allows later, Agent Memory remains the intended route; it needs its own setup on the Atlas Sandbox.
- **NFR9. Model limits.** Before a Run, the team confirms that the Claude API key works and that its rate limits allow the Selected trial set at the chosen concurrency.
- **NFR10. MongoDB as the advantage.** The video and the project description present MongoDB's capabilities as DxP's competitive advantage, and say which capability powers which behaviour: Grants and Policies with schema validation, atomic conditional updates for claim and stop, change streams for the live feed, and the audit history.
- **NFR11. Attribution.** Every Evidence shows its source and that source's data date; the app footer carries the credits line.
- **NFR12. Atlas Sandbox.** *New 13 Nov.* Finalists must use the Atlas Sandbox the organisers provide. DxP is built and validated on it from the start; the team's own cluster is not the final environment. Change streams are confirmed on the sandbox tier before the live feed depends on them.
- **NFR13. Problem statement fit and banned project types.** *New 13 Nov.* DxP is built for Problem Statement 1, "Agents You Can Audit". Two project types are banned: a dashboard as the main feature, and AI that gives medical advice. The governed agent is the product, and DxP gives no patient or medical advice.
- **NFR14. Least privilege for external actions.** *New 13 Nov. Updated 14 Nov (Slack change S3, S4).*
  - `SLACK_WEBHOOK_URL` is a credential. It lives only in `.env` and in the Modal secret, and is never committed, logged, stored in an audit record or shown on screen.
  - The webhook posts only to `#all-mango-db-hackathon`, and the Grant allows only that destination (check 3).
  - The alert only notifies. Slack sends nothing back to DxP, and DxP exposes no Slack callback route, so Slack holds no authority over a Record.
  - `DXP_BASE_URL` is configured to the production web address and is used only to build the links in the alert. The sender refuses to start without it.
  - The old `DXP_GITHUB_TOKEN` and `DXP_GITHUB_REPO` are removed.
- **NFR15. Policies are written by people.** *New 13 Nov.* Grants and Policies are hand-written and versioned. A model may draft a Policy (FR-45, stretch) but it takes effect only after a person approves it.

## 9. Open questions

None block the build. Deferred to later development:

1. The Maturity gate's numeric thresholds: minimum sample count, and which study designs count.
2. Medical's agreement to fields beyond the ten: regulatory status (added for Saturday by the team), Performance values by tumour type and Tumour stage, and the operational fields.
3. Licensing for congress abstracts, posters and photographs of posters, to raise with legal if the team wins.
4. How the Lifecycle stage, which is not one of the extracted fields, is derived and checked for accuracy (ADV-10). For architecture.

To confirm with the organisers on Saturday between 9:00 and 10:45 (owner Luis):

5. The submission deadline (the guide says 17:00), whether coding may start before 10:45, and how to present prepared material. Also whether the prepared data files in `data/` and the prepared logo may be used; without written clearance they are not (NFR7).
6. Atlas Sandbox access, and whether it supports Vector Search, change streams and the Agent Memory preview.

During the build (owner Luis):

7. Set `DXP_BASE_URL` to the production URL and confirm that the alert's "Review in DxP" and "Open diagnostic" links resolve on the deployed web app (during A04).
8. Keep `SLACK_WEBHOOK_URL` only in `.env` and the Modal secret.

Before 10:45 (owner Luis):

9. The Slack channel is used often. Every Run posts one alert per filed proposal to `#all-mango-db-hackathon`: tuning, I1, I2, rehearsals, the video and the live demo. Confirm that this volume is acceptable for that channel, or point the webhook at a team channel (readiness fix D57).

## 10. Assumptions index

- §2.1, §2.3 UJ-1 — The Director of Diagnostics is the strategy lead and works in a pharmaceutical therapy-area team; the Intended use shown is an example.
- §1 — The wording of the earlier novelty claim (now deferred).
- §4.1 — A Diagnostic whose Lifecycle stage cannot be determined is shown as "stage not determined".
- §4.3 — "Treatments moving up the lifecycle" was read as Diagnostics moving up.
- §6.2 — Closing the loop on a Shortlist and capturing advisor feedback were inferred in the source journeys, and are treated as out for Saturday.

Resolved on 13 Nov: DxP is not a clinical decision tool and gives no medical advice (now a stated rule, NFR13). The P1, P2, P3 order is replaced by the Core, Supporting and Stretch priorities in the approved change.
