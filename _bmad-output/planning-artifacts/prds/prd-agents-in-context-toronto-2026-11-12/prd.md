---
title: "PRD: DxProvida (DxP)"
status: draft
created: 2026-11-12
updated: 2026-11-13
---

# PRD: DxProvida (DxP)

## 0. Document purpose

This PRD is for the two teammates building DxP on Saturday 14 November 2026, and for the architecture and epics work that follows. It builds on the product brief in `../../briefs/brief-agents-in-context-toronto-2026-11-12/` and does not repeat the event facts or stack choices held there.

**Course correction, 13 Nov.** The organisers' participant guide arrived on 13 November. DxP is now pitched and built for hackathon Problem Statement 1, "Agents You Can Audit". The governed agent is the product. The approved change is in `../../sprint-change-proposal-2026-11-13.md`; the rationale is in `addendum.md` §5. Requirements the pivot sets aside stay in this document, marked **Deferred (pivot, 13 Nov)**, so no agent builds them on Saturday. Requirements kept in a smaller form carry a short "Trimmed" note.

Glossary terms (§3) are used exactly. Features are grouped in §4 with requirements numbered FR-1 to FR-46. The governed-action requirements are FR-31 to FR-46 in §4.10. Existing IDs never change. Constraints carry the NFR IDs used in `epics.md`. Inferences are tagged `[ASSUMPTION]` inline and indexed in §10. The user journeys as supplied, technical notes for architecture and the pivot rationale are in `addendum.md`.

## 1. Vision

**In one line:** DxP is an agent that keeps a pharma team's diagnostic evidence current, and it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action, and an audit trail a reviewer can replay.

The product is the governed agent. It reads a selected set of real lung cancer trials, drafts evidence-backed Proposed changes to Records, and opens a review issue in GitHub for a person to act on. Before every action it checks who it is acting for, what it is allowed to touch and which policy applies. When an action is out of scope, nothing happens except one audit event that says why. A person can stop a run at any time. Afterwards, a reviewer can rebuild the whole run, action by action, and answer "who authorised this, and under what authority?"

The screens exist to inspect and control the agent. They are not the product. The Run console shows the run live; the Audit view replays it; the Record and Review screen shows the evidence; the impact view shows what one run touched.

The evidence work from the original plan carries over unchanged. Every value in a Record carries its Evidence, and a Lifecycle stage changes only through an accepted Proposed change. The wider tracker described in the brief (Find, Categories, Alerts, memory and resume, capture) is deferred.

**Earlier novelty claim** (deferred with FR-19 and FR-28): DxP is an evidence analyst whose guardrails are written by its Reviewers. One rejection, with a reason, becomes a rule the agents follow from then on, and DxP remembers every Team between visits.

On Saturday DxP covers lung cancer only.

## 2. Target user

DxP serves a diagnostics team inside a pharmaceutical company. The team tracks evidence about diagnostic tests (trials, approvals, published studies) to plan pilots and partnerships. It is a research and strategy tool for professionals.

**DxP is not patient-facing and gives no medical advice.** It does not diagnose, recommend a test or treatment for anyone, or interpret a result for an individual. The hackathon bans AI that gives medical advice, and DxP stays clear of it by design.

The person at the centre of the demo is the data curator (Sam in the UX flows), who reviews what the agent proposes. The second audience is anyone who must later answer for what the agent did: a team lead, a quality reviewer or an auditor.

### 2.1 Jobs to be done

- **Data curator.** Keep the evidence trustworthy with less manual work, and stay in control of an agent that writes to the Records and opens work items in other systems. Continuous, low-intensity use.
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
  Sam starts a run over a selected set of real lung cancer trials. The Run console shows the agent's identity card: agent name, model, prompt version, policy-set version, and the person it acts for. It also shows the grant: which Team's Diagnostics it may touch, which destination and which actions, and when the grant expires. Actions stream in. One drafts a Proposed change with its quote and opens a review issue in the GitHub repository `dxp-review-sandbox`; Sam opens the issue in GitHub itself. Another tries to touch a Diagnostic outside the grant and is blocked before anything happens; the console shows which check failed. Sam reviews a Proposed change. Then Sam stops the run mid-flight: the run shows "stopping" while admitted actions finish, then "stopped". Finally, Sam opens the Audit view and answers "who moved SuperARMS to clinical utility, and under what authority?"
  **Climax:** a real action in another system, a blocked action that left no trace except its audit event, and a replay that names the person, the grant and the policy version behind every step.
  **Edge case:** an uncertain result from GitHub (a timeout or a server error). The agent must never create a second issue by retrying blindly. It searches for the action ID first, and if it still cannot tell, it marks the action `unknown` for a person to reconcile.
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
- **Selected trial set** — The 10 to 20 held-back ClinicalTrials.gov trials, chosen because they touch Diagnostics in the FDA seed, that a Saturday run works over.
- **Monitored set** — The Diagnostics that the scheduled scans keep up to date.
- **Gold set** — The 30 to 50 hand-labelled Source items used to measure extraction accuracy.
- **Graph view** — The visual map of Diagnostics, biomarkers, tumour types, trials, drugs and Providers, and the connections between them.
- **Run** — One execution of the agent, with its own `run_id`. Every write, event and external action the agent makes belongs to one Run.
- **Run identity** — The facts stamped on a Run and on everything it does: agent name, model, prompt version, policy-set version, and the person the agent acts for. Resolved on the server, never taken from the client.
- **Grant** — A stored permission for an agent: which Team's Diagnostics it may touch, which destination (the Record ledger or a GitHub repository), which actions, and an expiry. A Grant has a version.
- **Policy** — A hand-written, versioned rule the agent's actions are checked against. Policies are grouped into a policy set, which also has a version.
- **Action** — One thing the agent tries to do that has an effect: a write to a Record or a call to another system. Every Action has an action ID, a status and a decision.
- **Policy gate** — The five checks run before every Action (FR-33). An Action runs only if all five pass.
- **Blocked action** — An Action that failed the Policy gate. It changes nothing and calls nothing; it leaves one audit event.
- **Audit event** — The stored record of one decision or outcome for an Action, stamped with the Run identity, Grant version and policy-set version.
- **Review issue** — The GitHub issue the agent opens in `dxp-review-sandbox` so that a person reviews a Proposed change. The real external action for Saturday.
- **Stop** — The control that ends a Run. After a Stop, no new Action is admitted; admitted Actions may finish.
- **Atlas Sandbox** — The MongoDB Atlas environment the organisers provide. Finalists must build on it.

## 4. Features

### 4.1 Monitoring and the Maturity gate — P1

Agents scan the approved Sources on a schedule and on demand, with nobody logged in. Everything a person sees has been through the Maturity gate. Realizes UJ-3.

*Pivot, 13 Nov:* on Saturday the agent runs on demand over the Selected trial set. Scheduled scans, Tavily web searches and the full Baseline load are deferred.

- **FR-1. Unattended scan.** *Trimmed (pivot, 13 Nov): on-demand runs only; scheduled scans and web sources are deferred.* The system scans every approved Source type on a schedule and can be triggered manually. *Test:* a scan completes and records its Findings with no user session open.
- **FR-2. Maturity gate.** The system accepts Findings only from approved Source types, and marks a Diagnostic at discovery or assay development as Early research wherever it appears. A Diagnostic whose Lifecycle stage cannot be determined is shown as "stage not determined" `[ASSUMPTION]`. *Test:* a Diagnostic at discovery or assay development carries the Early research label in every table, Alert, Digest and Graph view. Numeric thresholds (sample count, study design) are later development.
- **FR-3. Match before create, no duplicates.** The system identifies each Diagnostic by a defined match key, attaches a Finding to the existing Diagnostic where the key matches, and creates a new Diagnostic only when none does. Parallel processing never creates a duplicate. The match key is set in architecture. *Test:* processing the same batch twice, or two Source items about one Diagnostic at the same moment, leaves one Record.
- **FR-4. Batch processing.** *Trimmed (pivot, 13 Nov): a run covers the Selected trial set (10 to 20 trials) at lower concurrency, not 300 to 500 items.* The system processes a batch of 300 to 500 Source items in parallel and shows progress. *Test:* a live count of processed and failed Source items, and of Diagnostics marked Early research, is visible during the run.
- **FR-30. Baseline load and Held-back set.** *Trimmed (pivot, 13 Nov): the comprehensive Baseline load is deferred. A small FDA seed stands in for it, and the Selected trial set comes from the Held-back set.* The first ingest is a Baseline load: it creates Records and sends no Alerts. It leaves out Source items from the last four weeks. That Held-back set is ingested afterwards, so that Proposed changes, Lifecycle stage changes and Alerts are produced by real data. *Test:* the Baseline load produces zero Alerts; ingesting the Held-back set produces at least one Proposed change and one Alert.

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

*Pivot, 13 Nov:* Lifecycle history is kept, because the audit question in the demo is about a Lifecycle stage change. Team Alerts are deferred.

- **FR-11. Lifecycle stage with history.** The system assigns each Diagnostic one Lifecycle stage, with Evidence, and keeps every earlier stage and its date. *Test:* a Record shows when and on what Evidence the Lifecycle stage last changed.
- **FR-12. First Alert.** **Deferred (pivot, 13 Nov).** A Team receives a first Alert for a Diagnostic when it matches the Team profile, comes from an approved Source, and the Team has not been alerted about it before. The Alert is sent at whatever Lifecycle stage the Diagnostic is at, discovery included. Credibility never suppresses an Alert: where there is no credible validation, the Alert carries the Early research label. *Test:* a matching Diagnostic at discovery produces exactly one first Alert, labelled Early research.
- **FR-13. Update Alerts.** **Deferred (pivot, 13 Nov).** After the first Alert, a Team is alerted again only when the Diagnostic advances a Lifecycle stage, is adopted for a line of therapy, is used in a trial, or becomes standard of care. The system uses semantic matching, not keyword rules, to decide whether a Finding falls under one of these four topics, so that it is caught however it is worded. *Test:* a new Finding that changes none of these produces no Alert; a Finding that describes one of them in unusual wording still produces one.
- **FR-14. Why it matters.** **Deferred (pivot, 13 Nov).** The audio part returns as the stretch spoken audit briefing (FR-44). Each Alert states in one line why it matters to that Team, and links to the Evidence. An Alert can carry an audio briefing. *Test:* the line names the element of the Team profile that matched.

**Notes:** FR-13 reads the team's "treatments moving up the lifecycle" as Diagnostics moving up `[ASSUMPTION]`.

### 4.4 Agent proposals and review — P1

Agents never change a Record silently. They draft, a Reviewer decides, and DxP tightens its own checks from the decision. Realizes UJ-3, UJ-5.

*Pivot, 13 Nov:* proposals and decisions are kept in a minimal form. Every Proposed change is now an Action that passes the Policy gate (§4.10) before it is written. Learned rules and the Digest are deferred.

- **FR-15. Field-level Proposed change.** For a Finding about a tracked Diagnostic, the system drafts a Proposed change showing the current value, the new value and the Evidence. Examples of what triggers an update: a new study readout, a regulatory submission or approval, a new trial that uses the Diagnostic, adoption for a line of therapy, and a guideline recommendation. A Proposed change either sets a single-valued field or adds an entry to a list-valued field. Trials, study results and linked drugs are lists, so a new trial is added and never overwrites an earlier one. *Test:* a new readout proposes a change to the key result, such as a sensitivity figure; a regulatory submission proposes a change to regulatory status; a second trial for one Diagnostic leaves the first in place.
- **FR-16. Accept, edit or reject.** *Trimmed (pivot, 13 Nov): minimal decisions API and one Record and Review screen.* A Reviewer can accept, edit or reject each Proposed change. An accepted change updates the Record with its Evidence attached. Values in a newly created Record are marked unreviewed until a Reviewer accepts them. A Lifecycle stage changes only through an accepted Proposed change. *Test:* no value in an existing Record changes without a Reviewer action logged against it, and every unreviewed value is visibly marked.
- **FR-17. Prior value retained.** The system keeps the previous value and its Evidence after every change. *Test:* any field shows its earlier values, who accepted each change and when.
- **FR-18. Confidence and automated check.** Each extracted field carries a confidence score and the result of an automated check against its quote. The check confirms that the quote appears word for word in its Source item. Low-confidence fields are marked for the Reviewer. *Test:* a quote that does not appear in its Source item fails the check and its value is not displayed; a field whose quote does not support its value also fails.
- **FR-19. Learned rule.** **Deferred (pivot, 13 Nov).** The stretch item FR-45 replaces it: a rejection drafts a Policy for explicit approval. A Reviewer who rejects or edits a Proposed change gives a reason. The system drafts a Learned rule for that field from the reason, shows it in plain language, and applies it once the Reviewer confirms it. A confirmed rule flags later and pending Proposed changes that break it; it does not withdraw them. A Reviewer can switch a Learned rule off. *Test:* after one rejection with a reason and a confirmed rule, a pending Proposed change with the same fault is flagged with the rule named; switching the rule off removes the flag.
- **FR-20. Digest.** **Deferred (pivot, 13 Nov).** The system sends a Digest of Proposed changes and Alerts, weekly or when an event warrants. *Test:* a Team with nothing applicable receives no Digest.

**Notes:** Before the pivot, this feature was the wow moment: agents working with memory (FR-19, FR-28), shown in the Graph view. From 13 Nov the wow moment is the governed run in §4.10: a real action in GitHub, a blocked action and a replayable audit trail, with the MongoDB capability named at each step. The mapping is in `addendum.md` §3 and §5.

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

- **FR-26. Connected graph.** *Trimmed (pivot, 13 Nov): the graph is scoped to one Run by `run_id` and adds Review issues as nodes; see FR-43.* The system shows Diagnostics, biomarkers, tumour types, trials, drugs and Providers as nodes, with the links between them, including links that cross Categories. Selecting a node opens its Record or Evidence. *Test:* a Diagnostic's linked trial, drug and Provider can each be reached from it in one step.
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

Each requirement is labelled **Core**, **Supporting** or **Stretch**. Core requirements must be green by 14:30 on Saturday. Supporting work starts only after that. Stretch work starts only if the core loop is green.

#### Identity and authority

- **FR-31. Run identity.** *Core.* Every Run has a `run_id`, agent name, model, prompt version, policy-set version, and the person the agent acts for. The server resolves these when the Run starts. Every write, event and external Action in the Run is stamped with them. *Test:* any Record change, audit event or Review issue from a Run shows the same `run_id` and identity; a change with no Run identity cannot be written.
- **FR-32. Grants and server-side authority.** *Core.* Grants are stored in Atlas: agent, Team, destination, allowed actions and expiry, each with a version. The server resolves the actor and the Grant from the API key. A name sent by the client never gives permission. Grants are seeded for the demo. *Test:* a request that names a different actor in its body is still evaluated against the Grant linked to its API key; a Grant past its expiry allows nothing.
- **FR-33. Versioned policies checked before every Action.** *Core.* Policies are hand-written, versioned and stored in Atlas with schema validation. Before every Action, the Policy gate runs five checks, in this order:
  1. The Run has an active, unexpired Grant.
  2. The Diagnostic is in the Team scope the Grant authorises.
  3. The destination and the Action type match the Grant.
  4. The required evidence checks passed (the quote is found and supports the value, as in FR-18).
  5. The Run is still authorised to act (it is `running`, not stopping or stopped).

  The Action runs only if all five pass. The decision records which policy-set version and Grant version were applied. *Test:* changing a Policy creates a new version and later decisions cite it; earlier decisions keep the version they were made under.
- **FR-34. Blocked action.** *Core.* An Action that fails any check changes no business record and makes no external call. The system writes exactly one audit event, with the Run identity, the policy-set and Grant versions, and the check that failed. *Test:* an out-of-scope Action leaves the Records and the GitHub repository unchanged, and the audit shows one event naming the failed check.

#### The external action

- **FR-35. Review issue in GitHub.** *Core.* For an allowed Proposed change, the agent opens a Review issue in the GitHub repository `dxp-review-sandbox`. The issue names the Diagnostic, the Proposed change, the Evidence quote and its source link, the `run_id` and the action ID. The system reads the issue back and stores its number and URL on the Action. The GitHub token is restricted to that repository and to issues only. *Test:* an allowed Action produces one real issue that opens in GitHub and links back to the Run.
- **FR-36. Ambiguous external result.** *Core.* The system saves an action ID in Atlas before calling GitHub and includes it in the issue. If the outcome is uncertain (a timeout or a 5xx error), the system searches the repository for the action ID before doing anything else. It never retries issue creation blindly. If the search does not settle it, the Action is marked `unknown` for a person to reconcile. *Test:* with a simulated timeout after GitHub created the issue, the system finds the issue by action ID and creates no second one; with no issue found and no clear answer, the Action shows `unknown`.
- **FR-37. Atomic claim.** *Core.* An Action moves from `queued` to `dispatching` through one conditional update in Atlas. Only the worker whose update succeeds may call GitHub. *Test:* two workers retrying the same Action at the same moment produce one external call and one issue.

#### Control and audit

- **FR-38. Stop control.** *Core.* A person can stop a Run. Admission of an Action is an atomic, conditional update on the Run that succeeds only while the Run is `running`, so a stop and an admission cannot race. After a stop, nothing new is admitted. Admitted Actions may finish and show as in flight. The Run shows `stopping` until no Action is in flight, then `stopped`. *Test:* stopping mid-run admits no further Action; the Run moves from `stopping` to `stopped` once in-flight Actions reach zero.
- **FR-39. Audit reconstruction.** *Core.* For any Run, the system returns every Action in order. Each Action keeps its inputs, Evidence reference, Grant version, policy-set version, decision, timestamps (proposed, decided, sent, observed) and external result (issue number and URL, or `unknown`). For any Record change it answers "who authorised this Action, and under what authority?" *Test:* from the audit alone, a reviewer can name the person, Grant, policy version and Evidence behind one Lifecycle stage change, and the result of every Action in the Run.
- **FR-40. Run console.** *Core.* One screen shows the Run identity card and Grant scope, a live list of Actions with their status (allowed, blocked, in flight, `unknown`), the stop button and links to the Review issues. *Test:* a person can start a Run, watch an Action be blocked with its failed check named, and stop the Run from this screen.
- **FR-41. Audit view.** *Core.* One screen reconstructs a Run, Action by Action, from FR-39, and answers "who authorised this" for a selected Action. *Test:* the demo question about SuperARMS is answered from this screen without opening a log.

#### Supporting

- **FR-42. Live action feed.** *Supporting.* The Run console updates as Actions are decided, through Atlas change streams. If change streams are not available on the Atlas Sandbox tier, the screen polls `/changes` instead. *Test:* a new Action appears on the console within a few seconds without a page reload.
- **FR-43. Run-scoped impact view.** *Supporting.* A graph of exactly what one Run touched, fed by `run_id`: the Diagnostics changed, their linked trials and biomarkers, and the Review issues as nodes. *Test:* every node in the view traces back to an Action in that Run's audit; nothing from other Runs appears.

#### Stretch

- **FR-44. Spoken audit briefing.** *Stretch.* ElevenLabs reads a short audit summary of one Run aloud. Replaces the audio part of FR-14 and targets the ElevenLabs prize.
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

- **Core:** §4.10 core requirements (FR-31 to FR-41), with the evidence work they rely on: FR-3, FR-5, FR-7, FR-11, FR-15 to FR-18, and trimmed FR-1, FR-4 and FR-30 over the Selected trial set. Milestone: by 14:30 on the Atlas Sandbox, one allowed Action creates a real GitHub issue, one out-of-scope Action is blocked before execution, and the audit reconstructs both.
- **Supporting:** a minimal Record and Review screen (FR-8, FR-16), the live action feed (FR-42) and the run-scoped impact view (FR-26 trimmed, FR-43).
- **Stretch:** FR-44, FR-45, FR-46, only if the core loop is green by 14:30.

### 6.2 Out of scope for Saturday

- Everything marked **Deferred (pivot, 13 Nov)**: Find and the comparison table, Categories, the broad Home dashboard, Tavily and scheduled scans, quick capture, the comprehensive Baseline load, Learned rules, Team Alerts and the Digest, memory and resume.
- Tumour types other than lung.
- Congress abstracts, posters and presentations as a Source, and photographs of congress posters, for licensing reasons. Revisit with legal if the team wins.
- Fields beyond the ten agreed with Medical and regulatory status: Performance values by tumour type and Tumour stage, operational fields and operational filters (FR-6, FR-10, FR-23). Later development.
- Numeric thresholds for the Maturity gate. Later development.
- External actions other than a Review issue in `dxp-review-sandbox`.
- The 3D body model and the 2D radar.
- Custom fine-tuned embeddings.
- Atlas's agent runtime.
- A live talking avatar.
- Recording what happened to a Shortlist (pilot proposed, deprioritised) and capturing advisor feedback. Both were inferred in the source journeys, not asked for `[ASSUMPTION]`.

## 7. Success metrics

**Primary**
- **SM-1.** Submitted by 16:55, before the 17:00 deadline, with a description, a public repository, a one-minute video and the team members. *Updated 13 Nov.*
- **SM-2.** The 60-second video shows the governed loop on real data, in four parts. *Updated 13 Nov.*
  - 0 to 10 s: the problem and the agent's authorised scope (identity card, Grant, policy set).
  - 10 to 30 s: an allowed Action across two systems: the Record updated with its quote, and the Review issue open in GitHub itself.
  - 30 to 45 s: an out-of-scope Action blocked before execution: no Record change, no issue, one audit event.
  - 45 to 60 s: the Run stopped (stopping, then stopped) and the audit answering who authorised the completed Action.

  Validates FR-31 to FR-41.
- **SM-3.** A UJ-1 query returns a populated comparison table in which every displayed value has Evidence. **Deferred (pivot, 13 Nov).** Zero uncited values still applies to every Record value shown (FR-7).
- **SM-4.** The 3-minute live demo shows every behaviour Statement 1 asks for. Start a Run over the Selected trial set. The console shows identity and scope, and Actions stream in. One Action creates a real GitHub issue, which is opened. One is blocked before execution, with the failed check shown. Sam reviews a Proposed change. The Run is stopped mid-flight. The Audit view answers "who moved SuperARMS to clinical utility, and under what authority?" The impact view shows exactly what the Run touched. Stretch: the spoken audit briefing. *Updated 13 Nov.*
- **SM-7.** The video and the project description open with the one-line description from §1. *Updated 13 Nov.*
- **SM-8.** By 14:30 on the Atlas Sandbox, one allowed Action creates a real GitHub issue, one out-of-scope Action is blocked before execution, and the Audit view reconstructs both with identity, Grant, policy version and result. *New 13 Nov.*
- **SM-9.** All six required acceptance behaviours in §4.10 pass on the Atlas Sandbox before code freeze at 16:30. *New 13 Nov.*

**Secondary**
- **SM-5.** Extraction accuracy per field on the gold set is measured and reported. Validates FR-5.
- **SM-6.** A top-three placing, or the Best Project Built with ElevenLabs prize.

**Counter-metrics (do not optimise)**
- **SM-C1.** Number of Alerts sent. More Alerts is the firehose the users do not want. Deferred with Alerts.
- **SM-C2.** Share of table cells filled. A blank cell is better than an uncited value. Counterbalances SM-3.
- **SM-C3.** Number of Source items ingested. Counterbalances SM-4: 10 to 20 trials is enough.
- **SM-C4.** Number of Actions allowed. A correctly blocked Action is a success, not a failure. Counterbalances SM-2. *New 13 Nov.*

## 8. Constraints and guardrails

NFR IDs match `epics.md`. New constraints from the participant guide are NFR12 to NFR15.

- **NFR1. Evidence.** Provenance is the product. Any shortcut that shows a value without Evidence fails the PRD.
- **NFR2. Human decision.** Every agent change to a Record is a Reviewer's decision, logged.
- **NFR3. Unattended operation.** *Trimmed (pivot, 13 Nov): on Saturday a person starts each Run; once started, it runs without a person in the loop until a Reviewer decision or a stop.* Scans, the Maturity gate and Proposed changes run with nobody logged in.
- **NFR4. Open data only.** Every Source item is openly and publicly available. Sources on Saturday are ClinicalTrials.gov, PubMed and the FDA companion diagnostics list. Provider websites through web search are deferred with Tavily. Nothing licensed or paywalled is ingested. The Held-back set is real data from these Sources. Provider websites, if used later, are scanned only from an allow-list of domains, because the web search tool does not filter out licensed pages. PubMed abstracts are public but not licensed for redistribution: DxP shows short quotes with a citation and a link, and no abstract text is committed to the public repository or written into a Review issue.
- **NFR5. Real behaviour on camera.** *Updated 13 Nov.* The video and the live demo show a real Review issue created in GitHub, a real blocked Action and a real stop, each made live. Synthetic history may set the scene; it does not stand in for these.
- **NFR6. Synthetic data.** Synthetic Teams, Grants, session history and Reviewer corrections are labelled as synthetic wherever they appear.
- **NFR7. Event rules.** *Updated 13 Nov.* Only work built during the event may be highlighted. The README separates prepared material (planning documents, data fetchers, skills) from what was built on 14 November, in a table. The demo shows only what was built that day. No coding before 10:45 unless an organiser permits it in writing.
- **NFR8. Time.** *Updated 13 Nov.* Hacking runs 10:45 to 17:00: 6 hours 15 minutes in total, two people, including recording and submitting. Submission is due at 17:00: description, public repository, a one-minute video and team members. Code freeze at 16:30; the video is recorded 16:30 to 16:50; submit by 16:55. The 3-minute live demo for judging starts at 17:15.
- **Agent Memory.** **Deferred (pivot, 13 Nov)** with memory and resume. If time allows later, Agent Memory remains the intended route; it needs its own setup on the Atlas Sandbox.
- **NFR9. Model limits.** Before a Run, the team confirms that the Claude API key works and that its rate limits allow the Selected trial set at the chosen concurrency.
- **NFR10. MongoDB as the advantage.** The video and the project description present MongoDB's capabilities as DxP's competitive advantage, and say which capability powers which behaviour: Grants and Policies with schema validation, atomic conditional updates for claim and stop, change streams for the live feed, and the audit history.
- **NFR11. Attribution.** Every Evidence shows its source and that source's data date; the app footer carries the credits line.
- **NFR12. Atlas Sandbox.** *New 13 Nov.* Finalists must use the Atlas Sandbox the organisers provide. DxP is built and validated on it from the start; the team's own cluster is not the final environment. Change streams are confirmed on the sandbox tier before the live feed depends on them.
- **NFR13. Problem statement fit and banned project types.** *New 13 Nov.* DxP is built for Problem Statement 1, "Agents You Can Audit". Two project types are banned: a dashboard as the main feature, and AI that gives medical advice. The governed agent is the product, and DxP gives no patient or medical advice.
- **NFR14. Least privilege for external actions.** *New 13 Nov.* The GitHub token is fine-grained, restricted to `dxp-review-sandbox` and to issues only. It is kept in `.env` and never committed, logged or shown on screen.
- **NFR15. Policies are written by people.** *New 13 Nov.* Grants and Policies are hand-written and versioned. A model may draft a Policy (FR-45, stretch) but it takes effect only after a person approves it.

## 9. Open questions

None block the build. Deferred to later development:

1. The Maturity gate's numeric thresholds: minimum sample count, and which study designs count.
2. Medical's agreement to fields beyond the ten: regulatory status (added for Saturday by the team), Performance values by tumour type and Tumour stage, and the operational fields.
3. Licensing for congress abstracts, posters and photographs of posters, to raise with legal if the team wins.
4. How the Lifecycle stage, which is not one of the extracted fields, is derived and checked for accuracy (ADV-10). For architecture.

To confirm with the organisers on Saturday between 9:00 and 10:45 (owner Luis):

5. The submission deadline (the guide says 17:00), whether coding may start before 10:45, and how to present prepared material.
6. Atlas Sandbox access, and whether it supports Vector Search, change streams and the Agent Memory preview.

Before 10:45 Saturday (owner Luis): create `dxp-review-sandbox` and a fine-grained token restricted to it.

## 10. Assumptions index

- §2.1, §2.3 UJ-1 — The Director of Diagnostics is the strategy lead and works in a pharmaceutical therapy-area team; the Intended use shown is an example.
- §1 — The wording of the earlier novelty claim (now deferred).
- §4.1 — A Diagnostic whose Lifecycle stage cannot be determined is shown as "stage not determined".
- §4.3 — "Treatments moving up the lifecycle" was read as Diagnostics moving up.
- §6.2 — Closing the loop on a Shortlist and capturing advisor feedback were inferred in the source journeys, and are treated as out for Saturday.

Resolved on 13 Nov: DxP is not a clinical decision tool and gives no medical advice (now a stated rule, NFR13). The P1, P2, P3 order is replaced by the Core, Supporting and Stretch priorities in the approved change.
