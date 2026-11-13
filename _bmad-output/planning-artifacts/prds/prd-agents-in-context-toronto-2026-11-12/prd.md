---
title: "PRD: DxProvida (DxP)"
status: draft
created: 2026-11-12
updated: 2026-11-12
---

# PRD: DxProvida (DxP)

## 0. Document Purpose

This PRD is for the two teammates building DxP on Saturday 14 November 2026, and for the architecture and epics work that follows. It builds on the product brief in `../../briefs/brief-agents-in-context-toronto-2026-11-12/` and does not repeat the event facts or stack choices held there.

Glossary terms (§3) are used exactly. Features are grouped in §4 with requirements numbered FR-1 to FR-30. Inferences are tagged `[ASSUMPTION]` inline and indexed in §10. Each feature carries a proposed priority for Saturday (P1, P2, P3), which the scoping session confirms. The user journeys as supplied, and technical notes for architecture, are in `addendum.md`.

## 1. Vision

DxP proactively tracks new cancer diagnostics, holds all the information in one source and makes the relevant diagnostic information easy to retrieve.

Agents scan approved Sources without being asked, label anything without credible validation as Early research, and keep each Diagnostic's Record current by drafting Proposed changes that a Reviewer accepts, edits or rejects. Every value in a Record carries its Evidence. DxP follows each Diagnostic through its nine Lifecycle stages and alerts a Team when a Diagnostic they follow first appears, at any stage, and again when it moves.

**Novelty claim** `[ASSUMPTION: wording for the team to confirm]`: DxP is an evidence analyst whose guardrails are written by its Reviewers. One rejection, with a reason, becomes a rule the agents follow from then on, and DxP remembers every Team between visits.

The people who use DxP are episodic users. Nobody logs in daily. DxP has to run unattended between visits and be self-explanatory to someone returning after six weeks away. On Saturday it covers lung cancer only.

## 2. Target User

### 2.1 Jobs To Be Done

- **Strategy lead (the Director of Diagnostics `[ASSUMPTION]`).** When a new Intended use is defined, shortlist the two or three Diagnostics worth a pilot, with Evidence that stands up in a meeting with a Provider. Uses DxP in bursts around a new Intended use or a major congress.
- **Domain expert.** Build a Category landscape for a planning cycle or an external advisory board without opening every Record. Heavy use for weeks, then quiet.
- **Data curator.** Keep the curated dataset trustworthy with less manual work, not a new place to do the same work. Continuous, low-intensity use.
- **New or returning user.** Pick the work up mid-project or after months away, with no memory of the tool.
- **Downstream consumer.** Read the outputs. Never queries DxP directly.

### 2.2 Non-Users

- Clinicians deciding care for an individual patient. DxP informs strategy and is not a clinical decision tool `[ASSUMPTION]`.
- Anyone who wants a daily feed of everything new.

### 2.3 Key User Journeys

- **UJ-1. The Director of Diagnostics shortlists Diagnostics for a new Intended use.** *(Primary.)*
  The Director of Diagnostics, in a pharmaceutical therapy-area team `[ASSUMPTION]`, has a new Intended use: monitoring patients with early-stage lung cancer for relapse `[ASSUMPTION: example]`. They last opened DxP six weeks ago. They open it in a browser and DxP shows what changed since that visit. They describe the Intended use in plain language. DxP returns a comparison table with one row per Diagnostic and a column for each criterion they asked for. Each Performance value shows its study, population, design and sample count inline. Where nothing is published, the cell reads "no data for this indication". They narrow by sample type, turnaround and regulatory status, pick three, save the Shortlist against the Intended use and export the comparison with its references.
  **Climax:** a populated table arrives in one query. Today they open each record and copy out sensitivity and specificity by hand.
  **Edge case:** a value with no Evidence is never shown. An uncited 97% is worse than a blank cell, because a blank prompts a check and a bare number does not.
- **UJ-2. A domain expert refreshes a Category landscape.** Ahead of an advisory board, the domain expert selects a Category, sees the full field set for every Diagnostic in it, spots Records that are thin, stale or missing a field, fills gaps from their own searching so that each added value persists for everyone, and exports the landscape.
- **UJ-3. DxP prepares the monitored-update Digest.** *(The automation core. Triggered by DxP, not by a person.)* On a schedule, agents scan the approved Sources, apply the Maturity gate, match each Finding to a tracked Diagnostic where one exists, and draft a Proposed change at field level. The data curator receives a Digest sized for an episodic user and accepts, edits or rejects each Proposed change.
  **Edge case:** silent overwriting. If a value changes without showing what changed and why, UJ-1 inherits values nobody vouched for.
- **UJ-4. Someone captures a lead at a congress.** A user learns of an untracked Diagnostic in a conversation. On a phone, on poor wifi, they submit a Provider name, a note or a photograph of a poster. An agent fills what fields it can, flags what is missing and checks for a duplicate Provider. The user confirms or corrects. The Record is marked partial and manually sourced, and joins the Monitored set.

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
- **Monitored set** — The Diagnostics that the scheduled scans keep up to date.
- **Gold set** — The 30 to 50 hand-labelled Source items used to measure extraction accuracy.
- **Graph view** — The visual map of Diagnostics, biomarkers, tumour types, trials, drugs and Providers, and the connections between them.

## 4. Features

### 4.1 Monitoring and the Maturity gate — P1

Agents scan the approved Sources on a schedule and on demand, with nobody logged in. Everything a person sees has been through the Maturity gate. Realizes UJ-3.

- **FR-1. Unattended scan.** The system scans every approved Source type on a schedule and can be triggered manually. *Test:* a scan completes and records its Findings with no user session open.
- **FR-2. Maturity gate.** The system accepts Findings only from approved Source types, and marks a Diagnostic at discovery or assay development as Early research wherever it appears. A Diagnostic whose Lifecycle stage cannot be determined is shown as "stage not determined" `[ASSUMPTION]`. *Test:* a Diagnostic at discovery or assay development carries the Early research label in every table, Alert, Digest and Graph view. Numeric thresholds (sample count, study design) are later development.
- **FR-3. Match before create, no duplicates.** The system identifies each Diagnostic by a defined match key, attaches a Finding to the existing Diagnostic where the key matches, and creates a new Diagnostic only when none does. Parallel processing never creates a duplicate. The match key is set in architecture. *Test:* processing the same batch twice, or two Source items about one Diagnostic at the same moment, leaves one Record.
- **FR-4. Batch processing.** The system processes a batch of 300 to 500 Source items in parallel and shows progress. *Test:* a live count of processed and failed Source items, and of Diagnostics marked Early research, is visible during the run.
- **FR-30. Baseline load and Held-back set.** The first ingest is a Baseline load: it creates Records and sends no Alerts. It leaves out Source items from the last four weeks. That Held-back set is ingested afterwards, so that Proposed changes, Lifecycle stage changes and Alerts are produced by real data. *Test:* the Baseline load produces zero Alerts; ingesting the Held-back set produces at least one Proposed change and one Alert.

### 4.2 Records with Evidence — P1

Each Diagnostic has one Record. This feature covers what DxP extracts when it finds a new Diagnostic. On Saturday that is the ten fields agreed with Medical, listed in the brief, plus regulatory status. Performance values and operational fields are later development. What triggers an update to a Diagnostic that DxP already tracks is a separate matter, covered in §4.3 and §4.4. Realizes UJ-1, UJ-2.

- **FR-5. Structured extraction.** The system fills each Record field from a Finding in a fixed format, with the supporting quote for every field. *Test:* every populated field opens to a quote from its Source.
- **FR-6. Performance by tumour type and Tumour stage.** *(Later development; out for Saturday.)* The system stores each Performance value against one tumour type and one Tumour stage with its study context, never as one figure per Diagnostic. *Test:* two values from different Tumour stages are never merged or compared as the same measure.
- **FR-7. No uncited values.** The system never displays a field value without Evidence. *Test:* removing a value's Evidence removes the value from every view.
- **FR-8. Explicit no-data state.** The system shows "no data for this indication" where nothing is published. *Test:* a no-data cell is distinguishable from a cell that is still loading.
- **FR-9. Standard terms and synonyms.** The system maps terms to standard names and finds a Diagnostic by any of its synonyms. Unmatched terms go to the Reviewer. *Test:* a search for "liquid biopsy" returns ctDNA Diagnostics.
- **FR-10. Operational fields.** *(Later development; out for Saturday.)* A Record holds sample volume and turnaround time. Regulatory status is not part of this requirement; it is in for Saturday under §4.2. *Test:* each can be used as a filter in FR-23.

### 4.3 Lifecycle tracking and Alerts — P1

DxP places every Diagnostic at a Lifecycle stage and keeps the history. A Diagnostic that matches a Team profile produces an Alert at any Lifecycle stage, discovery included, and whatever its credibility. Realizes UJ-3.

- **FR-11. Lifecycle stage with history.** The system assigns each Diagnostic one Lifecycle stage, with Evidence, and keeps every earlier stage and its date. *Test:* a Record shows when and on what Evidence the Lifecycle stage last changed.
- **FR-12. First Alert.** A Team receives a first Alert for a Diagnostic when it matches the Team profile, comes from an approved Source, and the Team has not been alerted about it before. The Alert is sent at whatever Lifecycle stage the Diagnostic is at, discovery included. Credibility never suppresses an Alert: where there is no credible validation, the Alert carries the Early research label. *Test:* a matching Diagnostic at discovery produces exactly one first Alert, labelled Early research.
- **FR-13. Update Alerts.** After the first Alert, a Team is alerted again only when the Diagnostic advances a Lifecycle stage, is adopted for a line of therapy, is used in a trial, or becomes standard of care. The system uses semantic matching, not keyword rules, to decide whether a Finding falls under one of these four topics, so that it is caught however it is worded. *Test:* a new Finding that changes none of these produces no Alert; a Finding that describes one of them in unusual wording still produces one.
- **FR-14. Why it matters.** Each Alert states in one line why it matters to that Team, and links to the Evidence. An Alert can carry an audio briefing. *Test:* the line names the element of the Team profile that matched.

**Notes:** FR-13 reads the team's "treatments moving up the lifecycle" as Diagnostics moving up `[ASSUMPTION]`.

### 4.4 Agent proposals and review (the agentic piece) — P1

Agents never change a Record silently. They draft, a Reviewer decides, and DxP tightens its own checks from the decision. Realizes UJ-3.

- **FR-15. Field-level Proposed change.** For a Finding about a tracked Diagnostic, the system drafts a Proposed change showing the current value, the new value and the Evidence. Examples of what triggers an update: a new study readout, a regulatory submission or approval, a new trial that uses the Diagnostic, adoption for a line of therapy, and a guideline recommendation. A Proposed change either sets a single-valued field or adds an entry to a list-valued field. Trials, study results and linked drugs are lists, so a new trial is added and never overwrites an earlier one. *Test:* a new readout proposes a change to the key result, such as a sensitivity figure; a regulatory submission proposes a change to regulatory status; a second trial for one Diagnostic leaves the first in place.
- **FR-16. Accept, edit or reject.** A Reviewer can accept, edit or reject each Proposed change. An accepted change updates the Record with its Evidence attached. Values in a newly created Record are marked unreviewed until a Reviewer accepts them. A Lifecycle stage changes only through an accepted Proposed change. *Test:* no value in an existing Record changes without a Reviewer action logged against it, and every unreviewed value is visibly marked.
- **FR-17. Prior value retained.** The system keeps the previous value and its Evidence after every change. *Test:* any field shows its earlier values, who accepted each change and when.
- **FR-18. Confidence and automated check.** Each extracted field carries a confidence score and the result of an automated check against its quote. The check confirms that the quote appears word for word in its Source item. Low-confidence fields are marked for the Reviewer. *Test:* a quote that does not appear in its Source item fails the check and its value is not displayed; a field whose quote does not support its value also fails.
- **FR-19. Learned rule.** A Reviewer who rejects or edits a Proposed change gives a reason. The system drafts a Learned rule for that field from the reason, shows it in plain language, and applies it once the Reviewer confirms it. A confirmed rule flags later and pending Proposed changes that break it; it does not withdraw them. A Reviewer can switch a Learned rule off. *Test:* after one rejection with a reason and a confirmed rule, a pending Proposed change with the same fault is flagged with the rule named; switching the rule off removes the flag.
- **FR-20. Digest.** The system sends a Digest of Proposed changes and Alerts, weekly or when an event warrants. *Test:* a Team with nothing applicable receives no Digest.

**Notes:** This feature is the wow moment for the judges. The video shows the agents working with memory (FR-19, FR-28) and the result appearing in the Graph view (§4.6), and names the MongoDB capability doing the work at each step. MongoDB's capabilities are presented as the competitive advantage. The mapping is in `addendum.md` §3.

### 4.5 Intended-use shortlisting — query and table P1; Shortlist and export P2

Realizes UJ-1. On Saturday the filters and table columns come from the ten agreed fields and regulatory status. Filtering on minimum sensitivity and specificity, and on operational fields, is later development.

- **FR-21. State the need.** A user describes an Intended use in plain language or sets filters on the agreed fields, such as modality, tumour type, Tumour stage, sample type, clinical use and regulatory status. The system turns it into one query across all Records. *Test:* the parsed query is shown and can be corrected.
- **FR-22. Comparison table.** The system returns one row per Diagnostic and one column per criterion asked for, with the Evidence inline for each value. *Test:* no step requires opening an individual Record to read a value.
- **FR-23. Operational filters.** *(Later development; out for Saturday.)* The user narrows the table on the operational fields in FR-10.
- **FR-24. Shortlist.** The user saves a Shortlist against a named Intended use. *Test:* reopening the Intended use shows its Shortlist.
- **FR-25. Export.** The system exports the comparison or Shortlist with every reference intact. *Test:* every value in the export carries its Evidence.

### 4.6 Graph view — P1

The Graph view replaces the galaxy view described in the brief. It shows the connections between clusters of Diagnostics, not only the clusters. Realizes UJ-1, UJ-2.

- **FR-26. Connected graph.** The system shows Diagnostics, biomarkers, tumour types, trials, drugs and Providers as nodes, with the links between them, including links that cross Categories. Selecting a node opens its Record or Evidence. *Test:* a Diagnostic's linked trial, drug and Provider can each be reached from it in one step.
- **FR-27. What changed.** The Graph view marks nodes and links that are new or changed since the user's last visit, and each Diagnostic's Lifecycle stage. *Test:* a Proposed change accepted since the last visit is marked on its node.

### 4.7 Memory across sessions — P1

Realizes UJ-1 and the returning-user job.

- **FR-28. Resume.** The system keeps the Team profile across sessions and, on return, shows what changed since the last visit and offers the last Intended use and Shortlist. *Test:* closing and reopening a session restores the Team's context with no input from the user.

### 4.8 Category landscape — P2

Realizes UJ-2.

- **FR-29. Landscape with gaps.** A user selects a Category and sees the full field set for every Diagnostic in it, with thin, stale or incomplete Records marked. A value the user adds by hand is saved for everyone, marked as manually sourced with submitter and date, and the landscape can be exported. *Test:* a value added by one user is visible to another, with the manual mark.

### 4.9 Capture on the go — P3

Realizes UJ-4. No numbered requirements yet; scoped only if the scoping session keeps it. Photographs of congress posters are out for Saturday, for the same licensing reason as congress abstracts. A submission of a name or note becomes a partial Record, clearly marked partial and manually sourced, checked for a duplicate Provider, and added to the Monitored set.

## 5. Non-Goals

- DxP is not a clinical decision tool and gives no advice about an individual patient `[ASSUMPTION]`.
- DxP is not a news feed. Updates to tracked Diagnostics matter more than a stream of novelty.
- Agents do not change a Record without a Reviewer's decision.
- DxP is not built for daily use.

## 6. Scope for Saturday

### 6.1 In Scope

Lung cancer only. The features in §4, apart from the requirements marked later development, are the ambition for six hours of coding by two people. The adversarial review judged P1 too large for six hours (ADV-01 in `review-adversarial.md`); the team will make that check in the scoping session. The proposed order, to be confirmed in the scoping session once epics and stories exist `[ASSUMPTION]`:

- **P1, the demo spine:** §4.1 to §4.4 (without FR-6 and FR-10), FR-21 and FR-22, §4.6 and §4.7.
- **P2:** FR-24, FR-25 and §4.8.
- **P3:** §4.9.

### 6.2 Out of Scope for Saturday

- Tumour types other than lung.
- Congress abstracts, posters and presentations as a Source, and photographs of congress posters, for licensing reasons. Revisit with legal if the team wins.
- Fields beyond the ten agreed with Medical and regulatory status: Performance values by tumour type and Tumour stage, operational fields and operational filters (FR-6, FR-10, FR-23). Later development.
- Numeric thresholds for the Maturity gate. Later development.
- The 3D body model and the 2D radar.
- Custom fine-tuned embeddings.
- Atlas's agent runtime.
- A live talking avatar.
- Recording what happened to a Shortlist (pilot proposed, deprioritised) and capturing advisor feedback. Both were inferred in the source journeys, not asked for `[ASSUMPTION]`.

## 7. Success Metrics

**Primary**
- **SM-1.** Submitted before the 18:00 deadline with a description, a public repository and a three-minute video.
- **SM-2.** The video shows the agent loop on real data, working with memory. An agent finds an update in the Held-back set and drafts a Proposed change. A Reviewer accepts one Proposed change and rejects another with a reason. DxP drafts a Learned rule, the Reviewer confirms it, and it flags another pending Proposed change. The Record updates with the prior value retained and the change appears in the Graph view. A second session then resumes with what the Team did in the first. Each step names the MongoDB capability behind it. Validates FR-1, FR-15 to FR-19, FR-26 to FR-28, FR-30.
- **SM-3.** A UJ-1 query returns a populated comparison table in which every displayed value has Evidence. Target: zero uncited values. Validates FR-7, FR-21, FR-22.
- **SM-4.** The demo shows each behaviour the event asks for: context kept across sessions (FR-28), a guardrail that tightens after a correction (FR-19) and a real workload (FR-4).
- **SM-7.** The video and the project description open with the one-line novelty claim from §1.

**Secondary**
- **SM-5.** Extraction accuracy per field on the gold set is measured and reported. Validates FR-5.
- **SM-6.** A top-three placing, or the Best Project Built with ElevenLabs prize.

**Counter-metrics (do not optimise)**
- **SM-C1.** Number of Alerts sent. More Alerts is the firehose the users do not want. Counterbalances SM-2: a busier agent loop is not a better one.
- **SM-C2.** Share of table cells filled. A blank cell is better than an uncited value. Counterbalances SM-3.
- **SM-C3.** Number of Source items ingested. Counterbalances SM-4.

## 8. Constraints and Guardrails

- **Evidence.** Provenance is the product. Any shortcut that shows a value without Evidence fails the PRD.
- **Human decision.** Every agent change to a Record is a Reviewer's decision, logged.
- **Unattended operation.** Scans, the Maturity gate and Proposed changes run with nobody logged in.
- **Open data only.** Every Source item is openly and publicly available. Sources on Saturday are ClinicalTrials.gov, PubMed, the FDA companion diagnostics list and Provider websites found through web search. Nothing licensed or paywalled is ingested. The Held-back set is real data from these Sources.
- **Real behaviour on camera.** The video shows one memory write and read made live, and one Learned rule made live from a real rejection. Synthetic history may set the scene; it does not stand in for these two.
- **Synthetic data.** Synthetic Team profiles, session history and Reviewer corrections are labelled as synthetic wherever they appear.
- **Event rules.** The project must be substantially developed on the day. Data prepared beforehand is disclosed, and the demo says what was built that day.
- **Time.** Six hours of coding, two people. Submission is due at 18:00.
- **Agent Memory.** The team builds on Atlas Agent Memory in preview, by decision. Plain collections holding the same memory types remain the fallback.
- **Model limits.** Before the batch in FR-4 runs, the team confirms that the Claude API key works and that its rate limits allow the batch size.
- **MongoDB as the advantage.** The video and the project description present MongoDB's capabilities as DxP's competitive advantage, and say which capability powers which behaviour.

## 9. Open Questions

None block the build. Deferred to later development:

1. The Maturity gate's numeric thresholds: minimum sample count, and which study designs count.
2. Medical's agreement to fields beyond the ten: regulatory status (added for Saturday by the team), Performance values by tumour type and Tumour stage, and the operational fields.
3. Licensing for congress abstracts, posters and photographs of posters, to raise with legal if the team wins.

4. Whether Atlas Agent Memory offers a taxonomic memory type, as the team's plan says. Verify before it is named in the video.
5. How the Lifecycle stage, which is not one of the extracted fields, is derived and checked for accuracy (ADV-10). For architecture.

To check on the day: the team is working to an 18:00 submission deadline. The event's rules say 17:00 and its page says 21:00, so confirm at the opening.

## 10. Assumptions Index

- §2.2, §5 — DxP is not a clinical decision tool for individual patients.
- §2.1, §2.3 UJ-1 — The Director of Diagnostics is the strategy lead and works in a pharmaceutical therapy-area team; the Intended use shown is an example.
- §1 — The wording of the novelty claim.
- §4.1 — A Diagnostic whose Lifecycle stage cannot be determined is shown as "stage not determined".
- §4.3 — "Treatments moving up the lifecycle" was read as Diagnostics moving up.
- §6.1 — The P1, P2, P3 order is a proposal for the scoping session.
- §6.2 — Closing the loop on a Shortlist and capturing advisor feedback were inferred in the source journeys, and are treated as out for Saturday.
