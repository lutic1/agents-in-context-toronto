---
status: final
updated: 2026-11-14
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/reviews/triage-medium-low.md
  - data/README.md
  - _bmad-output/planning-artifacts/ux-designs/ux-agents-in-context-toronto-2026-11-13/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-agents-in-context-toronto-2026-11-13/EXPERIENCE.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md
---

# DxProvida (DxP) - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for DxProvida (DxP), decomposing the requirements from the PRD and the architecture spine into implementable stories. The UX is in `ux-designs/ux-agents-in-context-toronto-2026-11-13/` (`DESIGN.md` for the look, `EXPERIENCE.md` for behaviour); WEB stories build to it. Every story carries story points so the team can set the cut line afterwards.

**Pivot, 13 November 2026 (approved course correction, `sprint-change-proposal-2026-11-13.md`).** DxP is now a governed agent built for Problem Statement 1, "Agents You Can Audit". The governed agent is the product: it keeps a pharma team's diagnostic evidence current, and it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action, and an audit trail a reviewer can replay. The screens only inspect it. Build day is Saturday 14 November 2026: hacking runs 10:45 to 17:00 on the provided Atlas Sandbox, with no coding before 10:45. Contracts freeze at 11:45, the first allowed-and-blocked loop is green by 14:30, code freezes at 16:30, the 60-second video is recorded 16:30 to 16:50 and submitted by 16:55, and the 3-minute live demo for judging is at 17:15. Epic 9 holds the new core work. Stories the pivot defers keep their old text and carry **Deferred (pivot, 13 Nov)** so no agent builds them on Saturday.

**Readiness fixes, 14 November 2026 (`readiness-fixes-2026-11-14.md`, decisions D1 to D40; that file wins over any earlier text, and D16 to D40 win over D1 to D15 where they differ).** Every kept story's acceptance criteria are rewritten in full as the single specification for Saturday, and the old "Pivot change" overrides are gone from kept stories. Nothing prepared before the event is reused: no code from `scripts/data/` or any `dxp-*` skill, no file from `data/` and no prepared logo, unless an organiser clears it in writing (D1). The demo scenario is trial NCT04712877, the first of the twenty selected trials (D30): the proposal for FoundationOne Liquid CDx is allowed, the one for FoundationOne CDx is blocked by team scope, and the question is "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?" (D9; that scenario and the D31 aliases are replaced by V33 to V35 below). The second audit added the seed and Reviewer grants (D16), one admission per action (D22), apply owned by the ledger in A06 (D26), the named selected set and hand-written aliases (D30, D31), the demo order and pacing (D33) and the rule that core never depends on supporting work (D37).

**Slack replaces GitHub, 14 November 2026 (approved, `sprint-change-proposal-2026-11-14-slack.md`, decisions S1 to S13; that file wins over any earlier text that mentions GitHub, a review issue, `dxp-review-sandbox` or reconciling against GitHub).** The external system is Slack: an allowed proposal sends one notify-only Block Kit alert (`notify_slack`) to `#all-mango-db-hackathon` through an incoming webhook, with links back to DxP (since V11, one alert per research report, not per proposal). Approval and rejection happen in DxP, never in Slack. An uncertain send is marked `unknown`, never retried, and a Reviewer resolves it in DxP.

**Final audit, 14 November 2026 (`readiness-fixes-2026-11-14.md`, decisions D41 to D57; they win in the same way).** The demo database is reset from the post-seed snapshot before every take (D41); one proposal loads through `GET /proposals/<p_id>` (D42); the sweep's layering and names are fixed (D43); the Action shape follows AD-14 exactly (D44); FDA row IDs and the grant's trade names are exact (D45); the gate runs once per change, with one Slack alert per filed proposal (D46, since replaced by one alert per report, V11); a proposal's `notification` is built at read time (D47); keys are generated at 10:45 and never committed (D48); and the principals and grants are named `dxp-curator`, `lbdx@v1`, `sam@v1` and `seed@v1` (D56).

**Discovery-agent vision restored, 14 November 2026 (`sprint-change-proposal-2026-11-14-discovery-agent.md`, decisions V1 to V24; that file wins over every earlier one, and D1 to D57 and S1 to S13 still apply wherever it does not replace them; the cuts 1 to 5 of its section 7 are the baseline; V21 to V24 add the two gated drafts, memory retrieval by claim kind, the scheduling levers L1 and L2 (V23, replaced by V31, approved by Luis) and the spine's names).** DxP is a **proactive diagnostic-evidence research agent**, entered under Statement 1, "Agents You Can Audit". Within one research scope ("Plasma ctDNA genotyping assays in NSCLC", Team "Team Liquid Biopsy Dx") it discovers trials on ClinicalTrials.gov updated since its last scan, relates them to existing evidence through Atlas Vector Search (supports, contradicts, extends or new question, each with checked quotes from both sides; a similarity score is never evidence), retrieves the reviewer corrections it remembers and shows what each changed, checks every claim and action against explicit policies before it takes effect, files one pending research report, sends one Slack alert per report linking to `/reports/<report_id>`, and, when Sam approves, promotes the report's updates into accepted knowledge and runs one follow-up task under its own grant and gate. Each report also carries a ten-second ElevenLabs briefing and a short HeyGen avatar video from the same grounded script, both supporting and behind flags. Governance (identity, grants, policies, decisions, stop, audit) supports that loop; Atlas is the identity, policy and audit layer and also holds the evidence collection, its embeddings and the reviewer memory. Memories are Team-scoped, attributable, correctable and revocable, and never change permissions. DxP supports research review and gives no medical advice. The new core work is Epic 10. The demo scenario becomes the discovery of NCT04712877 (RECRUITING, no results) with memory M1, created during the event by Sam's correction of the report from the setup run `set: "nct:NCT05715229"` (TERMINATED, no results; excluded from the prior collection); team scope blocks FoundationOne CDx, which guarantees must-show 3, and a "showed" claim in the first of two gated drafts is blocked before filing whenever the model writes it (V21); the audit question becomes "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" (V16). Stories 9.9 and 9.11 are cut, 9.10 is superseded by 10.11, 5.1 and 5.2 are cut (A15 and B05), and 1.3 and 2.4 are narrowed.

**Review of PR #8 and the registry check, 14 November 2026 (sections 10 and 11 of the same proposal, decisions V25 to V36; they win over V1 to V24 where they differ, and V33 to V36 win over V25 to V27).**

- **The demo claim is honest (V25, V33).** The research scope is "Plasma ctDNA genotyping assays in NSCLC" (all stages), so an early-stage trial is in scope. The expected anchor, NCT04712877 ("LEADER Neoadjuvant Screening Trial: LCMC4 Evaluation of Actionable Drivers in Early Stage Lung Cancers"), is RECRUITING with no results; its one intervention is "ctDNA, tumor NGS", with other names "FoundationOne CDx" and "FoundationOne Liquid". The report frames it as a **new trial signal worth investigating**: "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." The expected relationship to the prior collection (plasma ctDNA genotyping in advanced NSCLC) is `extends` (a new setting), backed by two checked quotes, or the item is shown without a relationship. No report, Slack alert, briefing, avatar or narration says the trial studies FoundationOne Liquid CDx, or that it shows any assay's performance.
- **No unverified alias (V34).** The hand-written aliases "FoundationOne Liquid", "Guardant360" and "FoundationOne" (D31) are removed. Only an exact FDA trade-name match, after `normalise_name()`, resolves to a seeded Diagnostic. An extracted name that matches no seeded alias exactly stays as it appears in the source, is never mapped to an approved product, and is listed in the report's uncertainties, for example: "The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated."
- **The allowed and blocked actions (V35).** Allowed: the report files one pending knowledge update that adds NCT04712877 to the scope's evidence collection, as an early-stage plasma-plus-tissue profiling study; on approval it is accepted into the collection, and no assay record changes. Blocked (guaranteed): the agent proposes linking the record's "FoundationOne CDx" mention to the Team's plasma research scope, and the gate blocks that link before it is filed, because the configured scope excludes the tissue assay (check 2), with one blocked Decision citing the mention and the scope rule (V35, V37). Blocked (if it occurs): an unsupported performance or results claim in the first draft (V21).
- **A name in the record is a mention, not proof of use (V37).** NCT04712877 lists "FoundationOne CDx" and "FoundationOne Liquid" only as alternate names (`otherNames`) of a generic intervention, "ctDNA, tumor NGS". DxP records each as a name present in the record, never as evidence that the trial used that product. FoundationOne CDx (tissue) and FoundationOne Liquid CDx (plasma cfDNA) are separate FDA devices and are never merged. The report keeps the original wording verbatim ("ctDNA, tumor NGS"; other names "FoundationOne CDx", "FoundationOne Liquid") and states under uncertainties: "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample." Acceptance criteria, the demo script and narration say "mention" or "named in the record", never "uses" or "studies", for both names.
- **Every report names one evidence gap, and the task answers it (V26, V33).** The demo gap: "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?" The recommended task searches ClinicalTrials.gov for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling and reports which have posted results (at most 5); "No matching results found among the records searched" is a valid, honest answer, shown with the query, the number of records searched and the limit (V42). Its findings are pending related evidence, never accepted knowledge.
- **Approved is not accepted for the task (V27).** Approval promotes the report's own update and authorises the task; anything the task finds stays pending until a Reviewer decides on it. The report page, the Audit view and the narration say so: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review."
- **The anchor is verified live (V36).** At 10:45 (OD2) the live API is queried for the scan; the demo anchor is whichever in-scope early-stage trial is actually updated after the chosen cursor, with its update date, status and results verified in the response. NCT04712877 is the expected candidate; if it is not updated after the cursor, the scan's real result is used with the same framing and no claim about which assay it studies.
- **A hard core cut line (V28).** Core, never cut: discovery, an evidence relationship with quotes, a memory changing the report, a policy block, the Slack notification opening the report, the human decision (approve with promotion, or reject or correct with a memory), the audit trail and stop. Core but cheap: the recommended task and its authorisation, a record created at approval (Story 10.8). Supporting, cut in this order: (1) the HeyGen avatar (10.12), (2) the ElevenLabs briefing (10.11), (3) the memory correct and revoke screen (memory creation and use stay core), (4) a second discovery item; follow-up task execution (Story 10.9) is now stretch, not a supporting cut (V39). A24 (decision, promotion, task authorisation) and A25 (task execution) are split again, so A25 can be cut without touching the core.
- **Media on demand (V29).** The report page has "Generate briefing" and "Render avatar" buttons behind the `briefing` and `avatar` flags; nothing renders automatically per report. For the demo, one avatar render is requested for the demo report only, as soon as it is filed. The report, the Slack alert, the decision, the task and the rehearsal never wait on either service. The script is built only from the report's fields and is always shown as text; if ElevenLabs or HeyGen fails, the player says "unavailable". The 10:45 HeyGen check is an account check, off the critical path; if it fails, B08 is not built.
- **One float number (V30).** With A25 and media off the core path, I3 is "approval, promotion, authorisation and audit" (14:45 to 15:00), and the rehearsal runs 15:00 to 16:10 (pass 1 as core acceptance, a reset, pass 2, a reset for the video). That gives **20 minutes of hard float at the 16:30 freeze, conditional on the merge milestones** (the L2 proof at 12:30 and the 13:00 desk decision, V36), the only float figure in the plan; otherwise the emergency path applies (one desk, the V28 cut line, one rehearsal pass, no float). If A25 is merged by 14:30 and the loop is green by 14:30, the follow-up task joins I3 (to 15:15) and uses 15 of those 20 minutes; otherwise A25 is cut. The base forecast is green at about 14:35, so A25 is stretch (V39).
- **L1 and L2 are risks, approved by Luis (V31).** See "Build risks" below.
- **The longitudinal value (V32).** The demo states that the scope cursor and the Team's memories accumulate over time: the scan only looks at what changed since the last scan, and M1 came from a correction earlier in the day. The pitch names the bigger value from the original brief, team-specific, longitudinal intelligence on the diagnostics a team follows; the demo shows one turn of that loop.

**Review of the branch, 14 November 2026 (section 12 of the same proposal, decisions V38 to V44; they win over V1 to V37 where they differ; approved by Luis (14 Nov)).**

- **Approval continues the work (V38).** There is no task start button. With `task_run` on (read by the backend from `DXP_FEATURES`; `NEXT_PUBLIC_DXP_FEATURES` only controls display), approval saves the `authorise_task` Decision, the task, its grant `task-<hex>@v1` and the task in status `queued` in one transaction, and the task starts automatically as its own `task:` run (`initiated_by: sam`, `agent: dxp-curator`, its own grant and gate, stoppable as usual) on the derived run ID `derive("run_", task_id)`, insert-if-absent, so a retried approval or two workers never start it twice. If another run is active the task stays `queued` and starts when that run ends; the background sweep and the API start hook recover a crash between approval and execution. With `task_run` off, approval still accepts the evidence and authorises the task, and the report shows "Follow-up task authorised; not run".
- **Task execution is stretch (V39).** Story 10.9, A25 and I3b are stretch (the loop is forecast green at about 14:35, after the 14:30 gate). The supporting cut order is now (1) the avatar, (2) the briefing, (3) the memory correct and revoke screen, (4) a second discovery item. Nothing claims or narrates completed follow-up work unless the task ran in that recording or demo; otherwise it says "Follow-up task authorised; not run".
- **Source versions (V40).** Immutable `source_versions` and `source_items.current_version_id`; quotes, retrieval results, `report.related[]`, Findings, proposals, Decisions and audit entries carry the exact `version_id` they used, and moving the pointer never changes reviewed or accepted evidence.
- **The script is core (V41).** `reports.script_for()` in `reports/script.py` (A19+A20) builds the report's text script at filing; B06 and B08 only consume it.
- **Capped search wording (V42).** An empty task result reads "No matching results found among the records searched", always with the query, the number of records searched and the limit.
- **No resolved Diagnostic (V43).** A report whose update targets the scope collection (`diagnostic_id: null`) goes through the gate, the apply, Slack ("Review in DxP" only), the audit and the UI without assuming a `dx_id`; I1 and I3 assert it.
- **Rehearsal source check (V44).** One report and its script are checked against the exact source version they used and, separately, that version against the live registry record; a difference there is "changed since the run", not an error.

## Requirements Inventory

### Functional Requirements

From the PRD. Several of these are deferred by the pivot and are not built on Saturday; the FR Coverage Map below lists them under "Deferred (pivot, 13 Nov)":

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

Governed agent actions, added by the pivot on 13 November (PRD §4.10):

- FR31: Every run has a `run_id`, the executing `agent` (named by the grant), `initiated_by` (the principal who started it, resolved from the caller's key), model, prompt version, the grant version pinned at start and the policy-set version, all set server-side and stamped on every write, event, decision and external action.
- FR32: Grants (agent principal, `startable_by`, Team scope, destinations, allowed actions, expiry) are stored in Atlas with a version; a key resolves to its principal whatever the grant's status (401 only for an unknown key), and a client-supplied name never confers permission.
- FR33: Hand-written, versioned policies with schema validation; before every action the gate runs five checks (latest grant version active and unexpired; Diagnostic in the grant's Team scope; destination and action in the grant; required evidence checks passed, applying only to `file_proposal` and `notify_slack` and `n/a` for the seed's `apply_value` and the Reviewer kinds (D50); run still authorised, meaning the action holds an admission for this run and the run is not `stopped`), and every evaluation, allowed or blocked, is recorded as a Decision.
- FR34: A blocked action creates no action, changes no business record and makes no external call; its only writes are one blocked Decision (with the grant evaluated, the policy-set version and the failed check) and one `action_blocked` event carrying the `decision_id`.
- FR35: An allowed action sends one notify-only Slack alert for the diagnostic evidence to `slack:#all-mango-db-hackathon`, with links back to DxP; what DxP observed (HTTP status, Slack's response body, the time posted) is stored on the action. Approval and rejection happen in DxP, never in Slack.
- FR36: Ambiguous external result: the action ID is saved first and carried in the alert; if the outcome is uncertain (timeout, connection error or HTTP 5xx), the action is marked `unknown` and never retried; a Reviewer resolves it in DxP after checking the channel for the action ID.
- FR37: An action is claimed atomically (`queued` to `dispatching`) so two workers never both send it.
- FR38: Stop: each action takes one admission (`runs.admit`), granted only while the run is `running`; after a stop nothing new is admitted, an admitted action may finish while the run is `stopping`, and the run moves to `stopped` when no `admitted` admission remains.
- FR39: Audit reconstruction of every Decision and action in order, plus the Reviewer decisions "After the run", answering "who authorised this action, and under what authority?"
- FR40: Run console. FR41: Audit view. FR42 (supporting): live action feed through change streams, `/changes` polling as fallback. FR43 (supporting): run-scoped impact view.
- FR44 (stretch): spoken audit briefing. FR45 (stretch): rejection drafts a policy for explicit approval. FR46 (stretch): scoped reversal of a run.

Proactive discovery and research memory, added on 14 November (PRD §4.11, discovery-agent proposal V1 to V24). Since then FR42 and FR45 are cut, and FR44 is carried by FR57:

- FR47: Discovery scan of ClinicalTrials.gov within a Research scope, with a cursor on the last-update date.
- FR48: Embeddings on evidence and findings, an Atlas Vector Search index and related-evidence retrieval; a text-search fallback is labelled as such.
- FR49: Relationship classification (supports, contradicts, extends, new question) with checked quotes from both sides; similarity is never evidence.
- FR50: The research report as a pending proposal, separate from accepted knowledge, naming one evidence gap (V26).
- FR51: Reviewer memory: creation and use, Team-scoped, attributable, never changing permissions.
- FR52: Correct or revoke a memory.
- FR53: Claim-accuracy policies checked before filing.
- FR54: Approval promotes accepted knowledge and authorises one follow-up task that answers the report's gap; approved is not accepted for the task (V26, V27).
- FR55: The follow-up task runs under its own grant and gate, started automatically after approval; its findings stay pending (stretch since V39; V38).
- FR56: The report page.
- FR57: Ten-second audio briefing, generated on demand (supporting, V29).
- FR58: HeyGen avatar video explaining a finding, rendered on demand (supporting, V29).

Later development, not built on Saturday: FR6 (performance by tumour type and stage), FR10 (operational fields), FR23 (operational filters). Capture on the go (PRD §4.9, UJ-4) has no numbered requirement and is P3.

### NonFunctional Requirements

- NFR1: Provenance. No value is shown without Evidence; a quote must appear word for word in its Source item.
- NFR2: Human decision. Every agent change to an existing Record is a logged Reviewer decision.
- NFR3: Unattended operation. Scans, the Maturity gate and Proposed changes run with nobody logged in. Trimmed (pivot, 13 Nov): on Saturday a person starts each run; once started, it runs without a person in the loop until a Reviewer decision or a stop.
- NFR4: Open data only. Every Source item is openly available; provider websites only from an allow-list; PubMed abstract text is never returned by the API, committed to the repository, shown in a shared trace or written into a Slack alert.
- NFR5: Real behaviour on camera. Updated 14 Nov: the video and the live demo show a real Slack alert arriving in `#all-mango-db-hackathon`, a real blocked action and a real stop, each made live. Synthetic history may set the scene; it does not stand in for these.
- NFR6: Synthetic data. Synthetic Teams, grants, profiles, history, corrections and rules are labelled synthetic wherever they appear.
- NFR7: Event rules. Updated 13 Nov: only work built during the event may be highlighted. The README separates prepared material from what was built on 14 November, in a table; the demo shows only what was built that day. No coding before 10:45 unless an organiser permits it in writing.
- NFR8: Time. Updated 13 Nov: hacking runs 10:45 to 17:00 on the Atlas Sandbox, two people, including recording and submitting; code freeze 16:30; the 60-second video is recorded 16:30 to 16:50; submission (description, public repository, video, team members) by 16:55, due at 17:00; the 3-minute live demo for judging at 17:15.
- NFR9: Model limits. Before a run, the team confirms that the Claude API key works and that its rate limits allow the selected trial set at the chosen concurrency (at most 16 concurrent calls in a run).
- NFR10: MongoDB as the advantage. The video and description name which MongoDB capability powers which behaviour: grants and policies with schema validation, atomic conditional updates for claim and stop, change streams for the live feed, and the audit history.
- NFR11: Attribution. Every Evidence shows its source and that source's data date; the app footer carries the credits line.
- NFR12: Atlas Sandbox. New 13 Nov: DxP is built and validated on the organisers' Atlas Sandbox from the start; change streams are confirmed on the sandbox tier before the live feed depends on them.
- NFR13: Problem statement fit. New 13 Nov: built for Problem Statement 1, "Agents You Can Audit"; no dashboard as the main feature and no medical advice.
- NFR14: Least privilege for external actions. Updated 14 Nov: the only external credential is `SLACK_WEBHOOK_URL`, an incoming webhook that can only post to `#all-mango-db-hackathon`; it lives only in `.env` and in the Modal secret and is never committed, logged or shown on screen. The alert is notify-only: no buttons, no Slack actions, and no Slack callback route in DxP.
- NFR15: Policies are written by people. New 13 Nov: grants and policies are hand-written and versioned; a model may draft a policy (FR45, stretch) but it takes effect only after a person approves it.

### Additional Requirements

From the architecture spine (AD-1 to AD-16). No starter template is mandated; the spine fixes a two-folder repository, `backend/` (Python 3.13, FastAPI on Modal) and `web/` (Next.js 16, App Router).

- Foundation: one MongoDB client in `store`, database named by `DXP_DB`, `store.ensure_indexes()`; the field registry in `schema/registry.py` with `registry.canonical()`; `identity.derive()` and `identity.normalise_name()`; `evidence.quote_in_source()`; all Claude calls through `llm` with `langchain-anthropic`, JSON-schema structured output, no sampling parameters.
- Ledger as the single writer of Records (AD-1): `ensure_diagnostic`, `file`, `review_value`, `seed`, and `ledger/apply.py` (D26, owned by A06): claim the proposal, one guarded update on the Diagnostic (value entry, `rev`, `facets`, `applied_proposal_ids`), then upsert the derived edges (an edge's `run_id` set with `$setOnInsert`) and emit `value_applied` with a `dedupe_key` (D27). Recovery runs at API start, at the start of every run and on every decision call, and always re-upserts the edges and re-emits the event.
- Value-entry shape and canonical forms per field (AD-2); derived IDs and insert-if-absent writes (AD-3); stage order enforced at apply (AD-5). Decision and action IDs derive from `(run_id or "-", kind, diagnostic_id, proposal_id or value_id or "<field>|<value>")`, and for `resolve_notification` the target is the `action_id` (D49); seed changes carry their own derived `p_` IDs; Reviewer decisions add a server-generated `request_id` (D20).
- Ingest modes on every Proposed change and event (AD-4): `baseline` for the seed only, `live` for runs. In live mode an agent never applies; it only files pending proposals (D28).
- Evidence check before filing and one read model for every endpoint (AD-6).
- The web app calls only the API; long work is a run (AD-9).
- Events outbox with integer `seq` and the `GET /changes` feed (AD-10); a Decision's `seq` is the `seq` of its `action_allowed` or `action_blocked` event (D21).
- One LangGraph run per run, `Send` fan-out, `max_concurrency` at most 16, per-item error capture (AD-12); `DXP_DEMO_PACE` processes one item at a time, a few seconds per item, for the live demo (D33).
- Graph node IDs `<type>:<value>` and an `edges` collection maintained by the ledger (AD-13).
- API contract: the route table and wire shapes in AD-14, with the D29 fields (Proposal `decision_id` and `notification { action_id, status, posted_at }`, built at read time from the proposal's `notify_slack` action and never stored on the proposal, D47; Link `status` and `proposal_id`; Record `applied_proposal_ids`; Run `counts.early_research`); web types generated with `openapi-typescript`.
- The ledger writes `facets` on every apply (AD-15).
- The selected set (D30): twenty public ClinicalTrials.gov trials naming an FDA-listed lung assay, listed by NCT ID in Story 1.4 and fetched during the event, NCT04712877 first; one run at a time; Modal timeout 3600 s.
- The seed (D31): the FDA list of companion diagnostics fetched during the event, lung rows only. A seeded Diagnostic's ID alias is `normalise_name()` of the list's trade-name column (which removes "®" and folds case); a row's ID is `<PMA or 510(k) number>:<first 8 hex characters of sha1 of the normalised row>`, because one number covers many drug rows (D45). The D31 hand-written aliases are removed (V34): only an exact FDA trade-name match after `normalise_name()` resolves to a seeded Diagnostic; an unmatched name stays as the source writes it and is listed in the report's uncertainties.
- Environments: the provided Atlas Sandbox, production database `dxp`; Vercel production URL for judges.
- Before 10:45 (not story work, prepared material listed in the README): the Slack incoming webhook for `#all-mango-db-hackathon`, created and tested before the event (any script used for that test is not reused; the notifier is written during the event), the Claude key and rate-limit check.
- Reset (D34, D41): A13 owns the reset script `scripts/reset_demo.py` and the post-setup snapshot (taken with `mongodump` at the end of I1's setup step, after seeding, the prior collection, the vector index and memory M1, and before the discovery run; V15). The reset restores it with `mongorestore` before each rehearsal (whose first pass is core acceptance, I2 folded in) (A16, which uses the script and does not create it), before the video (16:30) and between submission and the live demo (16:55 to 17:10). The integrators' smoke tests run in their own database, `DXP_DB=dxp_smoke`, never in `dxp`.
- Pivot, 13 Nov: new collections `runs`, `grants`, `policies` and `actions`; `events` gains run and action stamps. One new external dependency (updated 14 Nov): a Slack incoming webhook posting to `#all-mango-db-hackathon`, its URL in `SLACK_WEBHOOK_URL`, kept only in `.env` and the Modal secret; `DXP_BASE_URL` (the production web address) builds the links back to DxP. `DXP_GITHUB_TOKEN` and `DXP_GITHUB_REPO` are removed. Change streams are confirmed on the sandbox tier before the live feed depends on them.
- Readiness fixes, 14 Nov: `data/` is not loaded unless an organiser clears it (D1). New collections `decisions` (every gate evaluation), `policy_sets` and `admissions`; a run records `initiated_by` and `agent`, and a grant names `startable_by` (D4 to D7). The agent principal is `dxp-curator` with grant `lbdx@v1` for Team "Team Liquid Biopsy Dx"; the Reviewer principal `sam` has grant `sam@v1`, and the seed principal `seed` has grant `seed@v1`, all defined in Story 9.2 (D16, D56).
- Deferred since the pivot, not built on Saturday: Learned rules (AD-7), the Agent Memory adapter (AD-8), synonym expansion (AD-15), the comprehensive Baseline load and abstract sources (AD-16), Team Alerts, Tavily provider scans and scheduled scans.
- Discovery-agent proposal, 14 Nov: new collections `research_scopes`, `reports` (relationships embedded as `report.related[]` with label, quotes and similarity; no separate collection), `memories` and `tasks`, all in the A01 contract; embeddings on Source items and Findings with an Atlas Vector Search index (AD-15's vector part restored, Story 10.2; text-search fallback labelled honestly, OD1); the prior collection loaded in `baseline` mode during setup; new action kinds `search_source`, `file_related_evidence` and `generate_briefing` for the agent (a report is filed as a report-level `file_proposal`; there is no `file_report` kind, V24), and `decide_report`, `authorise_task`, `create_memory`, `correct_memory` and `revoke_memory` for the Reviewer (`decide_proposal` is superseded); per-task grants `task-<hex>@v1`; claim-accuracy policies in check 4. New agent action kind `generate_avatar_video` (Story 10.12). The agent grant `lbdx@v1` adds the destinations `source:clinicaltrials.gov`, `tts:elevenlabs` and `video:heygen`. Feature flags in `NEXT_PUBLIC_DXP_FEATURES` (display only): `briefing`, `avatar`, `memory_edit`, `task_run`; the backend reads the same names from `DXP_FEATURES` in the Modal secret, and only `DXP_FEATURES` decides whether an approved task is queued (V38). A `source_versions` collection with `source_items.current_version_id` (V40). `ELEVENLABS_API_KEY` (OD3), `HEYGEN_API_KEY` (OD7) and, if used, a Voyage AI key (OD1) are kept only in `.env` and the Modal secret.

### UX Design Requirements

The UX is `DESIGN.md` and `EXPERIENCE.md` in `ux-designs/ux-agents-in-context-toronto-2026-11-13/`, revised for the pivot. There are no mockups: every screen is built during the event from those two files and the architecture's API contract.

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

FR31: Epic 9 - Run identity stamped on every write, event and external action
FR32: Epic 9 - Grants in Atlas; actor and grant resolved server-side from the API key
FR33: Epic 9 - Versioned, hand-written policies; five checks before every action
FR34: Epic 9 - A blocked action changes nothing and writes one audit event
FR35: Epic 9 - Notify-only Slack alert for diagnostic evidence to `#all-mango-db-hackathon`, with links back to DxP; observed result stored
FR36: Epic 9 - Ambiguous external result: save the action ID first; if the outcome is uncertain, mark it `unknown` and never retry; a Reviewer resolves it in DxP
FR37: Epic 9 - Atomic claim, `queued` to `dispatching`
FR38: Epic 9 - Stop control: atomic admission; stopping, then stopped
FR39: Epic 9 - Audit reconstruction; "who authorised this action"
FR40: Epic 9 - Run console
FR41: Epic 9 - Audit view
FR42: Epic 9 - Live action feed through change streams (cut 14 Nov, Story 9.9; screens poll)
FR43: Epic 5 - Run-scoped impact view (cut 14 Nov with A15 and B05; an evidence-relationship view inside the report only if time)
FR44: Epic 10 - Spoken briefing, now the ten-second report briefing (Story 10.11, supporting; supersedes Story 9.10)
FR45: Epic 9 - Rejection drafts a policy for explicit approval (cut 14 Nov, Story 9.11)
FR46: Epic 9 - Scoped reversal of a run (stretch, a separate item outside Story 9.5, built only if the loop is green by 14:30)

Later development, not mapped: FR6, FR10, FR23. Capture on the go (PRD section 4.9) maps to Epic 7.

Epic 10 (discovery-agent proposal, 14 Nov; PRD §4.11):

FR47: Epic 10 - Discovery scan of ClinicalTrials.gov within a Research scope, on demand (restores FR1 on demand) - Story 10.1
FR48: Epic 10 - Embeddings and related-evidence retrieval through Atlas Vector Search; text-search fallback labelled honestly - Story 10.2
FR49: Epic 10 - Relationship classification with two checked quotes; similarity never evidence - Story 10.3
FR50: Epic 10 - Research report as a pending proposal, separate from accepted knowledge - Story 10.4
FR51: Epic 10 - Reviewer memory: creation and use, Team-scoped and attributable, never altering permissions - Stories 10.5 and 10.6
FR52: Epic 10 - Correct or revoke a memory - Stories 10.5 (API) and 10.10 (memory panel)
FR53: Epic 10 - Claim-accuracy policies in check 4 - Story 10.7
FR54: Epic 10 - Approval promotes accepted knowledge and authorises one task - Story 10.8
FR55: Epic 10 - Follow-up task runs under its own grant and gate - Story 10.9 (stretch, V39)
FR56: Epic 10 - Report page - Story 10.10
FR57: Epic 10 - Ten-second audio briefing (supporting) - Story 10.11
FR58: Epic 10 - HeyGen avatar video explaining a finding (supporting, `avatar` flag) - Story 10.12

Deferred (pivot, 13 Nov), as updated on 14 Nov: FR1's schedule (on-demand discovery returns in Story 10.1), FR9, FR12, FR13, FR14's Team-Alert audio (the report briefing is Story 10.11), FR19's Learned rules (reviewer memory in Stories 10.5 and 10.6 replaces them; Story 9.11 is cut), FR20, FR21, FR22, FR24, FR25, FR27's "since last visit", FR28, FR29 and FR30's comprehensive Baseline load (the prior collection is loaded in `baseline` mode during setup). Cut on 14 Nov: FR42 (Story 9.9), FR45 (Story 9.11), FR43 (Stories 5.1, 5.2; A15 and B05 cut). FR44 moves to Story 10.11.

## Epic List

Ten epics. Since the discovery-agent proposal of 14 November, Epic 10 (proactive discovery and research memory) is the product loop and Epic 9 (governed agent actions) is the governance under it; both are core. Before that, since the pivot on 13 November, Epic 9 was the core, built on a trimmed Epic 1 and with Epics 2, 5 and 8 kept in part; Epics 3, 4, 6 and 7 are deferred. The original dependency notes follow for history. Epic 1 is the foundation; Epics 2, 3, 4 and 5 depend only on Epic 1 and can run in parallel; Epic 6 also needs Epics 3 (team profiles in use) and 4 (Shortlist); Epic 7 needs Epic 1; Epic 8's deploy skeleton starts in hour one and is redeployed throughout. Every story is tagged **[API]** (backend and pipeline developer) or **[WEB]** (web developer). Each file in the `backend/dxp/ledger/` package has one owning PR (A06 owns `ledger/apply.py`; A14 owns `ledger/review.py`; A13 owns `ledger/seed.py`; `ledger/decide.py` is superseded by the report decision and not written, V8), so two agents never edit the same ledger file.

Changes applied from Advanced Elicitation before the pivot (pre-mortem, cascading failure, war room, persona focus group, assumption audit), kept for history:

- C1: live ingest mode moved into Epic 1, so Epics 2 and 3 do not depend on each other.
- C2: Epic 1 opens with seeding the 76 FDA rows and the synthetic Team profiles, and an API stub with generated types, so both developers have real data and a contract in hour one.
- C3: Epic 2 opens with a dry run matching the Held-back set against the Baseline to pick demo items early.
- C4: the Category gap view (FR29) folded into Epic 4; capture on the go kept as Epic 7 and pointed.
- C6: Epic 8 split into an early deploy skeleton and the final video and submission.
- C7: every story tagged [API] or [WEB]; ledger edits confined to named stories.
- C8: build risks recorded below.

### Epic 1: Evidence-backed records from real data
The team fetches the FDA list of lung companion diagnostics and the twenty selected trials during the event, and turns them into Diagnostic Records where every value carries a word-for-word quote, a Lifecycle stage and an Early research label where it applies; the seed applies the FDA rows as unreviewed values, and a run over the selected trials only files pending proposals. Anyone can open a Record from a Review, Audit or Impact link and see each value with its Evidence. (Since the pivot, abstracts, the Baseline load and the batch page are deferred. Since 14 November the selected trials are split into a prior collection loaded in `baseline` mode during setup and the live discovery scan of Story 10.1, and the Record page is narrowed to an "Accepted knowledge" view reached from the report.)
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR7, FR8, FR11, FR18, FR30

### Epic 2: Agents propose, the Reviewer decides, guardrails learn
When new evidence arrives about a tracked Diagnostic, the agents draft field-level Proposed changes; a Reviewer accepts, edits or rejects each with a reason, the system drafts a Learned rule from the rejection, applies it once confirmed to flag other proposals, and lets the Reviewer switch it off. Every earlier value stays in the history. (Since the pivot, Saturday builds only the queue, the decision with its history and a small pending-reports list, Stories 2.2 to 2.4; Learned rules stay deferred, Story 9.11 is cut, and reviewer memory, Stories 10.5 and 10.6, is what the agent learns from.)
**FRs covered:** FR15, FR16, FR17, FR19

### Epic 3: Teams get told what matters
Each Team gets a first Alert for a matching Diagnostic at any stage, then update Alerts only for meaningful moves (stage advance, line-of-therapy adoption, trial use, standard of care), each with a one-line reason and Evidence link, an optional audio briefing and an in-app Digest.
**FRs covered:** FR12, FR13, FR14, FR20

### Epic 4: Find, compare and fill gaps
A user describes an Intended use in plain words or filters, corrects the parsed query, finds Diagnostics by any synonym, compares them in a table with Evidence inline, saves and exports a Shortlist, and sees a Category's thin Records and fills a value by hand. (Stays deferred; Vector Search returns for related-evidence retrieval in Story 10.2.)
**FRs covered:** FR9, FR21, FR22, FR24, FR25, FR29

### Epic 5: See the connections
A user explores Diagnostics, biomarkers, tumour types, trials, drugs and Providers as a connected graph with links across Categories, sees each Diagnostic's stage and what changed since the last visit, and clicks through to Records and Evidence. (Since 14 November, Stories 5.1 and 5.2 are cut with A15 and B05, and the report's relationship list is the evidence view.)
**FRs covered:** FR26, FR27

### Epic 6: Pick up where you left off
A returning Team sees what changed since its last visit, a resume summary from memory, and its last Intended use and Shortlist, kept across sessions in MongoDB Atlas Agent Memory (or the collections fallback). (Stays deferred. Its reviewer-memory purpose is superseded by Stories 10.5 and 10.6, built on plain Atlas collections, not the Agent Memory preview SDK.)
**FRs covered:** FR28

### Epic 7: Capture on the go (P3)
A user types a Diagnostic name or a note and DxP turns it into a partial Record for the agents to fill.
**FRs covered:** none numbered (PRD section 4.9, UJ-4)

### Epic 8: Ship it to the judges
A judge opens a working production URL at any point in the day, and at submission receives the description, the public repository and a 60-second video that names which MongoDB capability powers which behaviour, with disclosure and credits; the 3-minute live demo for judging follows at 17:15.
**FRs covered:** none; NFR5, NFR7, NFR8, NFR10, NFR11

### Epic 9: Governed agent actions
The agent acts only as a named run with a scoped grant: every change to a record and every action in another system passes a versioned policy check first, a blocked action changes nothing and leaves one blocked Decision and one `action_blocked` event, one allowed action sends a real Slack alert for the diagnostic evidence, a person can stop the run at any moment, and the audit view replays the run and answers "who authorised this action". Core for Problem Statement 1, "Agents You Can Audit". Stories 9.1 to 9.8 are core; since 14 November 9.9 and 9.11 are cut and 9.10 is superseded by 10.11.
**FRs covered:** FR31 to FR41, FR46 (FR42 and FR45 cut; FR44 moved to Epic 10)

### Epic 10: Proactive discovery and research memory
Within one research scope the agent discovers newly updated ClinicalTrials.gov trials, relates them to existing evidence through Atlas Vector Search with checked quotes from both sides, retrieves the Team's reviewer memories and shows what each changed, has every claim checked by explicit policies before filing, files one pending research report, alerts Slack once per report with a link to the report page, and, on Sam's approval, promotes the updates into accepted knowledge and authorises one follow-up task that answers the report's evidence gap, which then starts automatically under its own narrow grant and gate when `task_run` is on (V38). Stories 10.1 to 10.8 and 10.10 are core (10.8 covers the task's authorisation only); 10.9 (task execution, started automatically after approval, V38) is stretch (V39), and 10.11 (the briefing) and 10.12 (the HeyGen avatar video) are supporting, each behind a flag and generated on demand (V28, V29).
**FRs covered:** FR47 to FR58; also FR1 (on demand), FR14 and FR44 (the report briefing), and extensions of FR33 and FR34

### Build risks

| Assumption | Confidence | Impact | Settled by |
|---|---|---|---|
| The anchor's exact mention "FoundationOne CDx" resolves to the seeded FoundationOne CDx, and "FoundationOne Liquid" stays unresolved and appears in the report's uncertainties (V34) | Medium | High | Exact-name matching only (Story 1.2, A02), extraction constrained to exact seeded names or `unresolved` (Story 1.5, A08); asserted at I1 |
| The FDA list can be fetched and parsed during the event | Medium | High | A13 by 13:15; otherwise seed only the Diagnostics the selected set names, typed from the FDA page during the event |
| Both developers productive from hour one | Medium | High | Story 1.1 contract stub, frozen by 11:45 |
| OD1: the Atlas Sandbox supports Vector Search indexes and Automated Embedding, or a Voyage AI key is allowed | Unverified | High | Checked in A19 at the start; otherwise related retrieval and memory ranking fall back to Atlas Search text search, labelled "related by text search", never "Vector Search" (Stories 10.2, 10.6) |
| OD2: on Saturday the live ClinicalTrials.gov API returns NCT04712877 (the expected candidate) as updated after the cursor, RECRUITING, without results; its update date is unverified until 10:45 (V36) | Unverified | High | At 10:45 the live API is queried for the scan; the demo anchor is whichever in-scope early-stage trial is actually updated after the chosen cursor, with date, status and results verified in the response, framed as V33 with no claim about which assay it studies (Stories 10.1, 10.7) |
| OD3: ElevenLabs key and quota | Unverified | Low | The script stays on the page as text and the player says "unavailable"; the report page still works (Story 10.11, V29) |
| OD4: organiser clearance items from D1 and D57 (prepared data, logo, Slack channel volume) | Unverified | Medium | As in D1 and D57; all demo data, including M1, is created during the event (V15) |
| OD5: change streams on the sandbox | n/a | None | No longer needed: the live feed (Story 9.9) is cut and screens poll |
| OD6: `mongodump` and `mongorestore` against the sandbox for the reset | Unverified | Medium | Reset by rerunning the setup (FDA seed, prior collection, index, M1 through the UI), which takes longer (Stories 1.2, 8.2) |
| Merge queue: about 22 Luis PRs landing 13:15 to 13:45 at about 10 minutes each | High | High | PR bundling (A21+A22, A19+A20, A23 in A06, A18+A14, A07+A11) and staggered merges from 12:30 (proposal section 7); A24 and A25 are split again so A25 can be cut without touching the core (V28) |
| L1 (draft starts, approved by Luis, V31): only A06 and A08 start at 10:45 as drafts against the AD-14 shapes; A19+A20 and A21+A22 start after the contract (11:45) | Medium | Medium | Each draft carries a 20-minute rebase budget after the contract freeze; any contract change after 11:45 goes through the contract keeper, with the rebase cost stated. Proof and fallback as for L2 |
| L2 (second merge desk, approved by Luis, V31): Vlad merges only A05, A13, A14 and A09, and only once green in CI and passed by Luis's review agent and the contract keeper | Medium | High | A failing CI or a conflict sends the PR back to its author and never waits on Vlad's desk; Vlad's review is a scope and secrets check, not a backend review. Proof step at 12:30: the first two merges through Vlad's desk (A05, A13) are timed against the 10-minute budget. Fallback if L1 or L2 fails by 13:00: one desk, and the V28 cut line applied at once (A25, B06 and B08 out), which takes three merges off Luis's queue; the core then fits with one rehearsal pass and no float (the emergency path) |
| The report page (B04) is near-critical | Medium | High | Two builders in Vlad's lane, forecast 13:45; checked in I3 |
| The Slack webhook posts to `#all-mango-db-hackathon` at 10:45 | High | High | Created and tested before the event; `SLACK_WEBHOOK_URL` kept only in `.env` and the Modal secret; A09 is never stubbed, so a missing or broken webhook is fixed before anything else |
| The alert's links resolve on the deployed web app | Medium | High | Luis sets `DXP_BASE_URL` to the production URL during A04; the sender refuses to start without it; Story 9.4 tests that "Review in DxP" (`/reports/<report_id>`) and, when sent, "Open diagnostic" resolve; on the demo path only "Review in DxP" is sent (V43) |
| The discovery loop through Slack is green by about 14:45 (I1), and approval, promotion, authorisation and audit by 15:00 (I3, V30) | Medium | High | If not, supporting and stretch work pauses and everyone fixes the loop; A06, A07 and A09 are never stubbed; A12, A15, B05 and A17 are already cut; B08 (avatar), B06 (briefing) and A25 (task execution) are supporting and cut in the V28 order. The task joins I3 (to 15:15) only if A25 is merged and the loop is green by 14:30 |
| OD7: HeyGen API key and plan, and render time for a ~20-second video (the one demo render is requested when the demo report is filed and must finish before the report is opened on camera) | Unverified | Low | An account check at 10:45, off the critical path; if it fails, B08 is not built. Otherwise the report shows "Rendering" or "Avatar unavailable" with the script as text; the loop never waits on it (Story 10.12, V29) |

## Story points

Points are relative size (1, 2, 3, 5) and stay as the tool for comparing stories. Planning time no longer uses "1 point is 30 minutes"; it uses the agent-time estimate below. **Cut candidate** marks a story the team can drop without breaking the stories after it; the stories cut on 14 Nov carry the **Cut (14 Nov)** tag. Since the pivot, Epic 9 stories are tagged **Core** (the allowed-and-blocked loop and its inspection), **Supporting** or **Stretch**. Agents not needed on the core may build supporting and stretch items before 14:30; they never block a core PR, and if the loop is not green at 14:30 they pause (D10). Stretch items merge only once the loop is green at 14:30. Core never depends on supporting work: A06, A07 and A09 are never stubbed (D37). Since 14 November A12, A15, B05 and A17 are cut outright; B06 (the report briefing) and B08 (the HeyGen avatar video) are supporting behind flags, and the briefing drops from the demo if not merged by 14:45. Epic 10 uses the same Core, Supporting and Stretch tags. **Deferred (pivot, 13 Nov)** marks a story that is not built on Saturday; **Cut (14 Nov)** and **Superseded (14 Nov)** mark stories the discovery-agent proposal removed.

## Estimating with AI agents

The **Time** on each story follows the rules measured on the CVH pilot build (1–6 October 2026, 90 stories built by Claude Opus 5.5 agents; actual time came to 46% of the developer estimate, median story 30%):

1. Size each story as a normal developer would without agents: S is up to 4 hours, M is one working day (5 to 8 hours).
2. Multiply by the factor for the kind of work. These factors come from the CVH build; the S and M sizes for DxP are this team's judgement.

| Kind of work | Factor | Evidence from the CVH build |
|---|---|---|
| Back end and rules (API routes, ledger, seeds, jobs, CSV) | 0.3 | Sign-in, audit, texts and sign-up took 20–35% |
| Single-language desktop screens | 0.5 | Staff Hub screens took 35–48% |
| Calls to Claude that need prompt tuning (extraction, rule drafting, why lines, resume) | 0.4–0.5 | No direct CVH measure; set between back end and screens |
| New infrastructure (Modal runs, CI and deploy) | 0.5 | App skeleton 41%, first production spike 67% |
| Search and the graph views | 0.8 | Search took 54–110%; resident home and graph-like screens went over |
| Running the rehearsal | 1.0 | Waiting for real runs is not shortened by agents |

3. These times are cycle times: elapsed time from start to merge for one story, including tests, review and waiting. They are not hours of effort, and adding them up does not give a schedule. The CVH build ran about three stories at once; that was how that build was run, not a limit. Saturday's schedule, with the team's real agent capacity and the dependency path, is in `build-schedule.md`.
4. Not shortened by agents and not in these numbers: setting up accounts and keys, product decisions, waiting for review, and recording the video.

## How every story lands: PR and merge

Each story names its **Owner** (Luis or Vlad) and its **PRs**. Since the pivot, a PR ID such as A06, B02 or I1 points to a card in `development-plan.md` with the branch, scope, the files it owns and the PRs that must merge first. Luis owns the A PRs and the integration PRs (the critical path: contract, ledger and gate, runs and stop, extraction, the Slack notifier, integration); Vlad owns the B PRs (the screens, the web skeleton, the report page B04, the report briefing B06, the HeyGen avatar video B08 and the submission package), with Luis's review agent on Vlad's lane. A14 (Luis, with A18 folded in) builds Story 1.1's Record read model and `GET /diagnostics/<dx_id>`; A01 owns `GET /schema` (D36). A06 owns `ledger/apply.py`, so the seed and I1 do not depend on A14 (D26). R1 (Luis and Vlad, 16:30 to 16:55) records and submits the video; it is a task with no branch. The earlier P and V IDs are retired (the V1 to V24 decision IDs of the discovery-agent proposal are a different series). A deferred, cut or superseded story has no PR. Since 14 November several PRs are bundled (see "PR bundling" under the points and time summary); a bundle's PRs line names it as, for example, `A19+A20`. Two scheduling levers in `development-plan.md` and `build-schedule.md` are **risks with a proof step and a fallback, approved by Luis (V31, replacing V23)**: L1, only A06 and A08 start at 10:45 as drafts against AD-14, each with a 20-minute rebase budget after the contract freeze (A19+A20 and A21+A22 start after 11:45; any contract change after 11:45 goes through the contract keeper, with the rebase cost stated); L2, Vlad's desk merges only A05, A13, A14 and A09, and only once green in CI and passed by Luis's review agent and the contract keeper (a failing CI or a conflict goes back to its author; Vlad checks scope and secrets, the agent reviews the backend). Proof at 12:30: the first two merges through Vlad's desk (A05, A13), timed against the 10-minute budget. Fallback if L1 or L2 fails by 13:00: one desk and the V28 cut line at once (A25, B06 and B08 out), one rehearsal pass and no float. See "Build risks".

A story is done only when it is merged into `main` and working on the Atlas Sandbox deploy. Every story with points follows these steps:

1. Branch from the latest `main` as `story/<n.n>-<short-name>` (for example `story/9.3-policy-gate`); integration PRs use `integration/<name>`.
2. Open a pull request into `main` titled `Story <n.n>: <What> (<ID>)`, for example `Story 9.3: Ledger with the policy gate (A06)`, matching `development-plan.md`, and list the acceptance criteria as a checklist.
3. The CI checks from Story 8.1 pass: the web app's type check and build, and the backend tests. Story 8.1 (A04) is built 11:00 to 12:00, right after the contract (A01); until it is merged, the reviewer runs the same checks locally.
4. The other developer (or their agent) reads the diff. They check that no secret, `.env` value or Slack webhook URL is in it, and that each acceptance criterion is met. Fixes found during I1, I3 and the rehearsal (A16) go in small PRs reviewed by the owner of the file (D36).
5. Squash-merge and delete the branch. If an API model changed, rebase first and regenerate `web/lib/types.ts`, so the two lanes never merge conflicting types.
6. After the merge, check the deploy on the Atlas Sandbox. Vercel deploys `main` itself; the person named in `docs/deploy.md` runs `modal deploy` for API changes.

Each pull request costs about 10 minutes: opening it, waiting for checks, the review and the merge. This time is already inside each story's agent-time estimate, because the CVH actuals it comes from ran to the merge. Merge small and often; never hold a story back to merge at the end of the day.

Saturday timing: hacking 10:45 to 17:00; contracts frozen by 11:45; deployed on the sandbox by 12:00; gate, runs, extraction and the Slack notifier merged by 13:45; **the discovery loop through Slack green on the sandbox by about 14:45** (I1, after its setup steps from 13:30); approval, promotion, authorisation and audit by 15:00 (I3, V30), with the follow-up task joining I3 to 15:15 only if A25 is merged and the loop is green by 14:30; the rehearsal runs 15:00 to 16:10, its first pass being core acceptance (I2 folded in); code freeze at 16:30, with 20 minutes of hard float, conditional on the merge milestones (V30, V36). If the loop is not green on time, supporting and stretch work pauses and everyone fixes the loop; a missing core piece is fixed, never stubbed and named in the demo (D37, NFR5).

A story is **done** only when all of its PRs have merged and its acceptance criteria pass on the integrated build: on the sandbox after the discovery loop (I1) or approval and the task (I3) for most stories, and at core acceptance on the sandbox (A16 pass 1, which absorbs the former I2) for Core and Demo path stories. The last merge alone does not make a story done; until the criteria are checked it stays `review` in `sprint-status.yaml`.

## Epic 1: Evidence-backed records from real data

The team fetches the FDA list of lung companion diagnostics and the twenty selected trials during the event, and turns them into Diagnostic Records where every value carries a word-for-word quote, a Lifecycle stage and an Early research label where it applies; the seed applies the FDA rows as unreviewed values, and a run over the selected trials only files pending proposals. Anyone can open a Record from a Review, Audit or Impact link and see each value with its Evidence. (Since the pivot, abstracts, the Baseline load and the batch page are deferred. Since 14 November the selected trials are split into a prior collection loaded in `baseline` mode during setup and the live discovery scan of Story 10.1, and the Record page is narrowed to an "Accepted knowledge" view reached from the report.)

### Story 1.1: API contract stub, schema route and Record read model

**Points:** 3 · **Time:** ~3.1 h (M, 10.5 h developer estimate × 0.3, back end; the read model, formerly A18, adds about 1 h) · **Lane:** [API] · **Covers:** AD-6, AD-9, AD-14, AD-17 to AD-21 (shapes and signatures) · **Demo path** · **Owner:** Luis
**PRs:** A01 `story/1.1-contract` (Contract: every route stubbed, every shape, one error shape, the frozen module signatures and `GET /schema`, Luis, 10:45 to 11:45); A14 `story/2.3-proposals-decisions` (Record read model and the accepted knowledge route `GET /diagnostics/<dx_id>`, with A18 folded in, Luis, starts after A01, merges after A06, 11:45 to 13:35). Cards in `development-plan.md`.

As the web developer,
I want the API's routes and response shapes running and published as generated TypeScript types in the first hour, and the Record routes working soon after,
So that I can build pages against the real contract while the pipeline is still being written.

**Acceptance Criteria:**

**Given** a `backend/` Python package managed with `uv`, and `backend/dxp/api/models.py` holding Pydantic classes for Principal, Stamp, Run, Grant, Policy, PolicySet, Decision, Admission, Action, AuditEntry, Audit, Record, Value, Proposal, Event, Node, Link and Team as AD-14, using the names the readiness fixes define (`initiated_by` and `agent` on Run, `counts` including `early_research`, `startable_by` on Grant, `decision_id` on Action, `agent`, `initiated_by`, `seq`, `request_id` and `cause { proposal_id, origin_run_id }` on Decision, `decision_id` and `notification { action_id, status, posted_at }` on Proposal, `status` (`pending` or `applied`) and `proposal_id` on Link, `applied_proposal_ids` on Record)
**When** the API runs under `modal serve`
**Then** (A01) `/openapi.json` lists every core, supporting and stretch route in the route table at the end of this document, including `POST /runs { grant_id, set }` (`set` is `discover`, `nct:<NCT ID>` or `task:<task_id>`), `GET /decisions/<decision_id>` and every Epic 10 route (reports, report decision, memories correct and revoke, tasks, scopes, briefing and avatar), with the AD-14 `Scope`, `Report`, `Relationship`, `Retrieval`, `MemoryUse`, `Memory`, `Task` and `Media` shapes; superseded, cut and deferred routes (for example `POST /proposals/<p_id>/decision`) are registered and stay 501; each route not yet built returns `{ error: { code: "not_implemented", message } }` with 501, and every error uses that one shape
**And** (A01) `GET /schema` returns the registry's fields, enums and stage order; A01 owns it (D36)
**And** (A01) `tools/gen_types.sh` generates `web/lib/types.ts` from `/openapi.json` with `openapi-typescript`; A01 owns both files and commits the generated types, and B01's `gen:types` npm script calls the tool
**And** (A01) `backend/dxp/api/app.py` builds the FastAPI app and reads its allowed CORS origins from the environment; no other PR edits it for CORS
**And** (A01) owns `backend/tests/conftest.py`, `backend/uv.lock`, the package `__init__.py` files (except `evidence/__init__.py`, owned by A08) and `.env.example`
**And** (A01) `store` is the only module that creates a MongoDB client, reading `MONGODB_URI` and `DXP_DB`, and `store.ensure_indexes()` runs at startup
**And** (A01) the signatures of `gate.evaluate(ctx, action)`, `actions.dispatch(action, ctx)`, `runs.admit(run_id, item_key)`, `runs.release(admission_id)`, `runs.sweep(run_id)`, `runs.settle(run_id)`, `runs.finish(run_id)`, `runs.stop(run_id)`, `runs.stamp(run_id)`, `ledger.file(finding_id, changes, mode, ctx)`, `ledger.apply(proposal_id)`, `ledger.recover_applying()`, `llm.extract(item, aliases)` and `llm.check()` are frozen by 11:45 as stubs with typed arguments and results; the admission functions live in `runs/admissions.py` and are exported under the public names `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle` and `runs.finish` (D22)
**And** (A14, formerly A18) `GET /diagnostics/<dx_id>` is built by `search.readmodel.get_diagnostic()`, which returns only entries that passed the check or are `manual`, sets `no_data` on an empty field, attaches the source name and `data_as_of`, passes `synthetic` through, and marks `unreviewed` values; `GET /diagnostics` (the list) is deferred and stays 501, because no Diagnostics list is built on Saturday (D40)
**And** (A14, formerly A18) every value in the response keeps its `stamp`, `action_id` and `proposal_id`, and the Record carries `applied_proposal_ids`, so a Record links to the run and decision that wrote it
**And** (A14, formerly A18) tests cover a passed value, a failed value that is never returned, an empty field with `no_data` and a missing Diagnostic returning 404
**And** no secret is in the repository.

### Story 1.2: FDA-authorised lung diagnostics and synthetic Teams seeded through the ledger

**Points:** 3 · **Time:** ~1.8 h (M, 6 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR3, FR11, NFR6, AD-1, AD-2, AD-3, AD-5, AD-13, AD-17 · **Demo path** · **Owner:** Luis
**PRs:** A02 `story/1.2a-registry-identity` (Registry and identity, Luis); A13 `story/1.2b-seed` (Seed the FDA rows and synthetic Teams through the ledger, Luis). Cards in `development-plan.md`.

As a Director of Diagnostics,
I want the FDA-authorised lung companion diagnostics already in DxP, each at regulatory approval with the FDA list as Evidence,
So that DxP starts from a trusted base, the grant's team scope names real Records, and the other developer has real Records to show early.

**Acceptance Criteria:**

**Given** (A02) `schema/registry.py` defines the ten fields, their cardinality, enums, stage order and confidence threshold, `registry.canonical()` and `registry.is_early_research()`, with a small hand-written map of the biomarker symbols and tumour-type codes the seeded rows and the selected trials use; no file under `data/` is read
**And** (A02) `identity.derive()` and `identity.normalise_name()` behave as AD-3; `normalise_name()` removes "®" and folds case (D45)
**And** (A02) there are no hand-written aliases (V34, replacing D31): only an exact FDA trade-name match after `normalise_name()` resolves to a seeded Diagnostic; tests cover that "FoundationOne CDx" resolves to FoundationOne CDx, and that "FoundationOne Liquid", "Guardant360" and "FoundationOne" resolve to nothing (they are never mapped to an approved product)
**When** (A13) `python -m dxp.sources.fda_cdx` runs, then `python -m dxp.ledger.seed` runs from the command line with the dedicated seed key
**Then** the first fetches the FDA list of cleared or approved companion diagnostic devices during the event and keeps the lung rows; unless an organiser clears the prepared files in writing, nothing is loaded from `data/fda/`
**And** each kept row is stored as a Source item `fda_cdx_list:<row id>`, where the row ID is `<PMA or 510(k) number>:<first 8 hex characters of sha1 of the normalised row>`, because one number covers many drug rows (D45), whose `raw_text` is the row and whose `source_date` is the fetch date
**And** each assay becomes one Diagnostic found through `aliases`; its ID alias is `normalise_name()` of the list's trade-name column, and no other alias is added (V34); FoundationOne Liquid CDx and FoundationOne CDx are both seeded, as separate Diagnostics
**And** every value is filed through `ledger.file()` in `baseline` mode, which calls `gate.evaluate()` under the seed grant `seed@v1` (Story 9.2), and is applied at once as `unreviewed` through `ledger.apply()` (Story 1.6, A06) with its own derived `p_` ID; every write carries the stamp `{ kind: "seed", principal: "seed" }` with `run_id: null`, and each gate evaluation is recorded in `decisions` with `agent: "seed"` and `initiated_by: "seed"`
**And** each Diagnostic has `lifecycle_stage: regulatory_approval` by rule, with no model call, and Evidence quoting the FDA row with the list's data date
**And** running the seed twice creates no new document and changes no existing one
**And** three synthetic Teams with profiles on modality, biomarker and linked drug are inserted into `teams` with `synthetic: true`, one of them "Team Liquid Biopsy Dx", whose scope the agent's grant `lbdx@v1` covers (D32, D56), and `GET /teams` returns them
**And** if the FDA list cannot be fetched or parsed by 13:15, only the Diagnostics the selected set names are seeded, typed from the FDA page during the event, and A13 tells B07 so the README says so
**And** (A13) merges on tests against a fake gate; I1 step 1 (13:30 to 13:50) runs the grant, policy and scope seed, the FDA seed and `python -m dxp.pipeline.prior` on the sandbox (D38); the snapshot of `dxp` is taken with `mongodump` only at the end of I1 step 2, after M1 exists (V15)
**And** (A13) owns the reset script `scripts/reset_demo.py` (`--snapshot` and restore), which restores the post-setup snapshot including memory M1 with `mongorestore` (V15; OD6, otherwise the reset reruns the setup); it runs before each rehearsal (A16 uses it and does not create it), before the video and before the live demo (D41)
**And** the integrators' smoke tests run in their own database, `DXP_DB=dxp_smoke`, never in the demo database `dxp` (D41)
**And** no code is copied from `scripts/data/` or from any `dxp-*` skill.

### Story 1.3: Browse diagnostics and open a Record with its Evidence

**Points:** 3 · **Time:** ~3.5 h (M, 7 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR2, FR7, FR8, NFR1, NFR11, AD-6, AD-9 · **Demo path** · **Owner:** Vlad
**PRs:** A14 `story/2.3-proposals-decisions` (the read model and `GET /diagnostics/<dx_id>`, accepted knowledge only, Luis); B04 `story/10.10-report-page` (the report page, which carries the narrowed "Accepted knowledge" view, Vlad; built in B01's shell). Cards in `development-plan.md`.
**Narrowed (14 Nov):** this is now the "Accepted knowledge" view of one Diagnostic, reached from the report page (Story 10.10) and from the Slack alert's "Open diagnostic" link; it shows accepted values only and is visibly separate from pending reports and proposals.

As a Director of Diagnostics,
I want to open a Diagnostic's accepted knowledge from a report, audit or Slack link and see every value with its quote, source and data date,
So that I can trust each value without leaving the page.

**Acceptance Criteria:**

**Given** (B01) `web/` created with `create-next-app` (Next.js 16, TypeScript, App Router, Tailwind) and `shadcn init`, owning `web/package.json` with a `gen:types` script that calls `tools/gen_types.sh`, and calling the API only through `web/lib/api.ts` with the generated types
**And** no Diagnostics list is built on Saturday: the "Accepted knowledge" view at `web/app/diagnostics/[dx_id]/` is reached from the report page (Story 10.10), the Audit view and the alert's "Open diagnostic" link (D40, V11)
**And** it is labelled "Accepted knowledge", and pending items appear only as a count linking to the pending report, never mixed with accepted values (V5)
**When** I open the Accepted knowledge view (reading `GET /diagnostics/<dx_id>`)
**Then** I see the Diagnostic's name, Lifecycle stage and an Early research label where `early_research` is true, or "stage not determined"
**And** each field shows its values with the quote, source name, link and data date, and unreviewed values are marked unreviewed
**And** (B04) each unreviewed value has Accept, Edit and Reject controls that call `POST /diagnostics/<dx_id>/values/<value_id>/review { action, value, reason }` (Story 2.3); Edit and Reject require a reason before they submit, and the page shows the returned Record
**And** each value shows which run wrote it (`run_id`, or "seed"), and the report that promoted it, when there is one
**And** an empty field shows "no data for this indication", visibly different from the loading state
**And** the page renders only what the API's read model returns (Story 1.1, A14), applying no display rule of its own
**And** the footer carries the credits line for ClinicalTrials.gov and the FDA list
**And** one server-side Next.js route adds `X-DxP-Key` to every API request, so the key never reaches the browser; no request sends a name or `actor`, because the principal is resolved server-side from the key.

### Story 1.4: Fetch the selected trials into MongoDB

**Points:** 1 · **Time:** ~0.6 h (S, 2 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** NFR4, AD-16 · **Demo path** · **Owner:** Luis
**PRs:** A05 `story/10.1-discovery-scan` (Prior collection by NCT ID in baseline mode, with the discovery scan of Story 10.1, Luis). Cards in `development-plan.md`.
**Updated (14 Nov):** the selected set is split (V2, D30 narrowed). The prior collection, the selected trials last updated before the scope's cursor, is fetched by NCT ID and loaded in `baseline` mode during setup (I1 step 1); new trials, NCT04712877 on the demo path, arrive through the discovery scan (Story 10.1), not through this manifest.

As the team,
I want the prior collection fetched from ClinicalTrials.gov during the event and stored in `source_items` in baseline mode,
So that the discovery run has existing evidence to relate new trials to, runs on Modal read it without the laptop, and nothing prepared before the event is loaded.

**Acceptance Criteria:**

**Given** a checked-in manifest `backend/dxp/sources/selected.json` listing the twenty public ClinicalTrials.gov trials that name an FDA-listed lung assay (D30): NCT04712877, NCT06284317, NCT04591431, NCT05715229, NCT03248089, NCT03615443, NCT05361564, NCT04265534, NCT04698681, NCT03576937, NCT04624373, NCT04566614, NCT06918782, NCT05846594, NCT04223596, NCT04087473, NCT03199651, NCT03521154, NCT06146920, NCT05935384
**When** `python -m dxp.pipeline.prior` (A05, `pipeline/prior.py`) runs during setup from a laptop with the seed key, fetching through `python -m dxp.sources.load --set prior --scope <scope_id>`
**Then** it fetches each trial by NCT ID from the ClinicalTrials.gov API v2 (`/api/v2/studies/<nct_id>`) during the event; unless an organiser clears the prepared files in writing, nothing is read from `data/`
**And** only the trials whose `last_update_posted` is before the scope's cursor are loaded as the prior collection, excluding NCT05715229; the rest, NCT04712877 among them, are left for the discovery scan (Story 10.1, OD2)
**And** NCT05715229 is the setup item: `python -m dxp.sources.load --nct NCT05715229` stores it with `window: "setup"`, and the setup run `POST /runs { grant_id: "lbdx", set: "nct:NCT05715229" }` files the report that Sam corrects to create M1 (I1 step 2, V15)
**And** the prior collection is loaded in `baseline` mode: its Findings and embeddings are written so retrieval can find them (Story 10.2), it sends no Slack alert and files no pending report
**And** each trial is upserted with `_id` = `clinicaltrials.gov:<NCT ID>`, `window: "prior"`, `sets: ["prior"]`, `overall_status` and `has_results` kept for the claim checks (Story 10.7), `raw_text` built from the record's text fields, and `source_date` from its `last_update_posted`, which becomes `evidence.source_date` and the "data as of" date on screen
**And** each fetch writes one immutable `source_versions` document (`derive("sv_", source_ref, last_update_post_date, content_hash)`) and sets `source_items.current_version_id` (V40); running it twice changes nothing, and no version is ever overwritten
**And** the count it prints matches the manifest; a trial that fails to fetch is reported by NCT ID and the rest still load
**And** no code is copied from `scripts/data/` or from any `dxp-*` skill.

### Story 1.5: Extract a Finding from one Source item with a quote for every field

**Points:** 5 · **Time:** ~4 h (M, 8 h developer estimate × 0.5, model work) · **Lane:** [API] · **Covers:** FR2, FR5, FR18, NFR9, AD-6, AD-11 · **Demo path** · **Owner:** Luis
**PRs:** A08 `story/1.5-extraction` (Extraction with quote and support checks, tuned on the selected set, Luis). Cards in `development-plan.md`.

As a Director of Diagnostics,
I want the agent to read a trial and pull out the fields, each with a word-for-word quote and a confidence,
So that nothing reaches a Record or a Slack alert without evidence I can check.

**Acceptance Criteria:**

**Given** `llm` is the only module calling Claude, through `langchain-anthropic` with JSON-schema structured output and no sampling parameters, and it exposes `MODEL_IDS` and `PROMPT_VERSION` for the run's identity
**When** a trial from the selected set is processed
**Then** a triage call on `claude-haiku-5-5` decides whether it concerns a lung cancer diagnostic, and only relevant items go to extraction on `claude-sonnet-5-5`
**And** an item rejected at triage counts as done, not failed, and yields no Finding
**And** one item can name several Diagnostics, so extraction returns one Finding per Diagnostic it names; NCT04712877 lists "FoundationOne CDx" and "FoundationOne Liquid" only as other names of a generic "ctDNA, tumor NGS" intervention: the "FoundationOne CDx" mention matches the seeded FoundationOne CDx exactly and is recorded as a name present in the record, never as proof the trial used it (its proposed link to the plasma scope is later blocked by check 2, V35, V37), while "FoundationOne Liquid" matches no seeded name exactly and is returned as an unresolved mention, never as FoundationOne Liquid CDx (V34); the two devices are never merged (V37); the intervention wording is kept verbatim
**And** the extraction prompt is given the seeded names (Story 1.2), and the extracted assay name must be one of those exact names or `unresolved`, with the name kept exactly as the source writes it; an unresolved name creates no Diagnostic and is listed in the report's uncertainties ("The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated."); any other answer is a failure record (V34)
**And** extraction returns, per field, the raw value, a quote of at most 300 characters and a confidence, plus at most one `stage_evidence`
**And** `evidence.quote_in_source()` sets `quote_found`; a check call on `claude-sonnet-5-5` sets `supported` (the quote backs the value); a value passes only when `quote_found` and `supported` are both true; a failing value is recorded on the Finding and goes no further, and this `check` is what the gate's evidence check reads (Story 9.3)
**And** values are canonicalised with `registry.canonical()`
**And** rate-limit and overload errors back off and retry inside `llm`
**And** a model error or refusal returns a failure record and does not raise, and the failure line carries no source text
**And** (A08) owns `evidence/__init__.py` (D36)
**And** running it from the command line on five trials of the selected set prints the Findings with their quotes and checks.

### Story 1.6: The ledger files Findings without duplicates and keeps the stage moving forward

**Points:** 3 · **Time:** ~2.1 h (M, 7 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR3, FR11, AD-1, AD-3, AD-4, AD-5, AD-10, AD-13, AD-19 · **Demo path** · **Owner:** Luis
**PRs:** A06 `story/9.3-policy-gate` (Ledger with the policy gate before every write, including `ledger/apply.py`, Luis). Cards in `development-plan.md`.

As a Director of Diagnostics,
I want each new piece of evidence attached to the right Diagnostic as a proposal a person reviews, and the stage only ever advancing,
So that parallel agents never produce duplicates, never change a tracked Record on their own and never move a diagnostic backwards.

**Acceptance Criteria:**

**Given** a Finding from Story 1.5 and a run context holding the run's stamp and the item's admission
**When** `ledger.file(finding_id, changes, mode, ctx)` runs
**Then** it calls `gate.evaluate()` (Story 9.3) before any write, including `ensure_diagnostic`; a blocked decision means no business write at all (only the blocked Decision and its `action_blocked` event)
**And** `ensure_diagnostic` matches on `aliases` (or the alias `approach:<modality>:<biomarker>` when no assay is named) and creates a Diagnostic only on a miss, treating a duplicate-key error as "exists"; creating a Diagnostic outside the grant's scope is blocked by check 2 (D28)
**And** Findings and Proposed changes are insert-if-absent with IDs from `identity.derive`; decision and action IDs derive from `(run_id or "-", kind, diagnostic_id, proposal_id or value_id or "<field>|<value>")`, with the `action_id` as the target for `resolve_notification` (D20, D49)
**And** in `live` mode an agent never applies: every allowed change, including one on a Diagnostic the run itself created, is filed as a `pending` proposal carrying the run's stamp, `action_id` and `decision_id`; the proposal document has no stored `notification`, which the read model builds at read time from its report's one `notify_slack` action (D47, V11); and the only way it reaches the Record is the Reviewer's report decision (Story 10.8, `POST /reports/<report_id>/decision`) (D28, V8)
**And** the seed's values (Story 1.2) are the only values applied at once as `unreviewed`
**And** a change equal to a `current` value is not filed
**And** a `lifecycle_stage` change that is not later than the stored stage is never filed; one that is later is filed as pending like any other change
**And** `ledger/apply.py` (A06, D26) provides `ledger.apply(proposal_id)`: it claims the proposal `pending` to `applying` with a conditional update, makes one guarded update on the Diagnostic that writes the value entry, increments `rev`, rewrites `facets` and adds the proposal ID to `applied_proposal_ids`, matching only if the ID is not already there; then it upserts the derived edges, each edge's `run_id` set with `$setOnInsert` so a later run never takes over an earlier run's edge, emits `value_applied` with a `dedupe_key`, and marks the proposal `applied` (D27)
**And** recovery, `ledger.recover_applying()` over every proposal stuck in `applying`, runs at API start, at the start of every run and on every decision call; it reruns the guarded update (a no-op if it already happened), always re-upserts the derived edges and re-emits the event (deduplicated by `dedupe_key`), then marks the proposal `applied`
**And** the seed (Story 1.2), the report decision (Story 10.8, `reports/decide.py`) and value review (Story 2.3) all apply only through `ledger.apply()`, so the seed and I1 do not depend on A14
**And** the ledger action is set `done` with `result { proposal_ids, value_ids }`, or `failed`
**And** `store.emit_event()` writes events with an integer `seq`, a unique `dedupe_key` and the stamp
**And** filing the same Finding twice, or two Findings for the same Diagnostic at once, leaves one Diagnostic and no duplicate proposal; tests cover an apply interrupted after the guarded update and before the edges, completed by recovery.

### Story 1.7: Run a batch of Source items in parallel as one job

**Points:** 3 · **Time:** ~3.5 h (M, 7 h developer estimate × 0.5, new infra) · **Lane:** [API] · **Covers:** FR4, NFR3, NFR9, AD-12, AD-16, AD-21 · **Demo path** · **Owner:** Luis
**PRs:** A10 `story/1.7-run` (The run: LangGraph over the selected set, Luis). Cards in `development-plan.md`.

As the team,
I want a run started over the selected set to process its trials in parallel, unattended, with every action admitted and gated,
So that the agent works without anyone watching, within the rate limit, and stops cleanly when asked.

**Acceptance Criteria:**

**Given** a run created by `POST /runs { grant_id, set }` (Story 9.1)
**When** the API starts it with `.spawn()` on the run function passed to `api.create_app()`, with a 3600-second Modal timeout
**Then** the worker executes with the agent's key and the `run_id`; every write it makes carries the `run_id`, and the server refuses an agent write whose key does not resolve to the run's `agent`
**And** at the start of the run, apply recovery runs (Story 1.6)
**And** the run is one LangGraph run fanning out with `Send` over the Source items of its `set` (`discover`: the items the scan returned, Story 10.1; `nct:<NCT ID>`: one setup item; `task:<task_id>`: handed to `tasks.run`, Story 10.9), at low concurrency (`max_concurrency` set in config, at most 16); each item node catches its own error and returns a failure record
**And** with `DXP_DEMO_PACE` set, items are processed one at a time with a few seconds per item, so the first item is NCT04712877 and a stop lands mid-run (D33)
**And** for each item the node calls `llm.extract()` and `llm.check()` first; then, after extraction and before the gate, it takes one admission per proposed action with `runs.admit(run_id, item_key)`, where `item_key = "<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"` (D22); if no admission is granted that action ends with nothing attempted and `counts.not_admitted` goes up
**And** each admitted action passes through `gate.evaluate()` by way of `ledger.file()` or `actions.dispatch()`, carrying its `admission_id`
**And** the gate is evaluated once per change: A10 calls `ledger.file` once for each admitted change, never once for a whole Finding (D46)
**And** each filed report gets one `notify_slack` action, with its own admission, so there is one Slack alert per report, not per proposal (V11, replaces D46's per-proposal alert)
**And** `runs.release(admission_id)` runs in a `finally` once that action is blocked, `done`, `failed` or `unknown`
**And** each item is retrieved, related and drafted twice (V21): draft 1 without the retrieved memories, draft 2 with them; both go through the gate as the report-level `file_proposal` (targets `"<report_id>|draft1"` and `"<report_id>|draft2"`), each its own Decision; draft 2 is the one filed, and if it is blocked the item ends with nothing filed (Stories 10.4, 10.6, 10.7); the run never generates a briefing or renders an avatar video, which are requested on demand from the report page (V29)
**And** `runs` holds `counts { total, done, failed, filed, reports, allowed, blocked, unknown, not_admitted, early_research }`, one failure line per failed item and `active` (the `source_ref` and step of each item in progress), all readable at `GET /runs/<run_id>`
**And** a run over `clinicaltrials.gov` items is traced in LangSmith
**And** after the last item the pipeline calls `runs.finish(run_id)`, which moves the run from `running` to `done` once no `admitted` admission remains; a run becomes `failed` only when the pipeline raises an error it cannot recover from (D23)
**And** a run over the selected set with one forced item failure finishes with that item failed and every other item done.

### Story 1.8: Watch the agents work through a batch

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR4, NFR5 · **Demo path** · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Pivot change:** Replaced by Story 9.7 (Run console).

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

**Points:** 1 · **Time:** ~1.5 h (run time, not shortened by agents) · **Lane:** [API] · **Covers:** FR30, AD-4, operations · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~0.9 h (S, 3 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR1, NFR3, AD-16 · **Cut candidate:** the demo uses manual triggers · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Still deferred (14 Nov):** Story 10.1 restores on-demand scanning of ClinicalTrials.gov within a research scope; scheduled scans stay deferred (V18).

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

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR1, FR2, NFR4 · **Cut candidate:** the Saturday data has no web sources · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Still deferred (14 Nov):** discovery uses ClinicalTrials.gov only (Story 10.1); Tavily stays deferred (V18).

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

**Points:** 2 · **Time:** ~3 h (M, 6 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** NFR5, NFR11, `DESIGN.md`, `EXPERIENCE.md` Foundation and Information Architecture · **Demo path** · **Owner:** Vlad
**PRs:** B01 `story/1.12-web-shell` (Web skeleton and minimal shell: Run console, Reports with the pending count, Audit; the feature flags `briefing`, `avatar`, `memory_edit` and `task_run`; the briefing and avatar player stubs, Vlad; done when it builds locally, and deploys once A04 lands, D39). Cards in `development-plan.md`.

As a judge watching the demo,
I want every page to share one finished look and one navigation,
So that DxP reads as a real product, not a set of pages.

**Acceptance Criteria:**

**Given** the Next.js app with shadcn/ui and Tailwind
**When** any page loads
**Then** the colour, radius and font tokens from `DESIGN.md` are set as CSS variables, and the three fonts load through `next/font/google`
**And** the top bar shows a text wordmark, "DxP", set in the interface font; no prepared logo image is used unless an organiser clears it
**And** the top bar shows the destinations in the `EXPERIENCE.md` order (Run console, Reports with the pending count, Audit); the Reports count polls `GET /reports?status=pending` every 2 seconds (hidden while the route returns 501; A12 and the impact view are cut); and the read-only "Signed in as" chip from `GET /whoami`
**And** `web/lib/features.ts` reads `NEXT_PUBLIC_DXP_FEATURES` (`briefing`, `avatar`, `memory_edit`, `task_run`), which only controls display: there is no task start button, and the backend reads `task_run` from `DXP_FEATURES` (V38), and B01 ships the empty player stubs `web/app/reports/[report_id]/briefing/player.tsx` and `web/app/reports/[report_id]/avatar/player.tsx`, handed to B06 and B08; the shell is done with every flag off, and nothing in it waits on supporting work
**And** the top bar is the glass panel, and the page background is the tissue field drawn in CSS, with no image file
**And** a shared stage-track component draws nine segments: reached stages solid, Early research stages in the ink tint, future stages hollow, with a tooltip naming each stage
**And** the shared Early research and Synthetic badges match `DESIGN.md`
**And** the API-unreachable toast and the loading skeletons from `EXPERIENCE.md` State Patterns are in place
**And** nothing is copied from the prepared logo files, `scripts/` or any skill.

## Epic 2: Agents propose, the Reviewer decides, guardrails learn

When new evidence arrives about a tracked Diagnostic, the agents draft field-level Proposed changes; a Reviewer accepts, edits or rejects each with a reason, the system drafts a Learned rule from the rejection, applies it once confirmed to flag other proposals, and lets the Reviewer switch it off. Every earlier value stays in the history. (Since the pivot, Saturday builds only the queue, the decision with its history and a small pending-reports list, Stories 2.2 to 2.4; Learned rules stay deferred, Story 9.11 is cut, and reviewer memory, Stories 10.5 and 10.6, is what the agent learns from.)

### Story 2.1: Dry run the Held-back set against the Baseline

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR15, FR30, build risk "Held-back items hit tracked Diagnostics" · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~0.9 h (S, 3 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR15, FR18, AD-4, AD-14 · **Demo path** · **Owner:** Luis
**PRs:** A14 `story/2.3-proposals-decisions` (Read model, the proposal read routes and the value review, Luis). Cards in `development-plan.md`.
**Narrowed (14 Nov):** proposals are listed inside their report (`?report_id=`) and decided through the report (Story 10.8); A14 keeps only the proposal GET routes.

As a Reviewer,
I want every pending Proposed change listed with the current value, the new value and its Evidence,
So that I can decide each one without opening the source.

**Acceptance Criteria:**

**Given** a run has filed `pending` Proposed changes on existing Diagnostics
**When** I call `GET /api/v1/proposals?status=pending`, optionally with `run_id=`, `report_id=`, `diagnostic_id=` or `field=`
**Then** each Proposal carries `diagnostic_name`, field, new value and label, `current_value`, Evidence with source, quote and data date, `check` with confidence, `mode`, `run_id`, `report_id`, `action_id`, `decision_id`, `notification { action_id, status, posted_at }` (built at read time from its report's one `notify_slack` action and never written to the proposal document, D47, V11; null until that action exists; `status` is `queued`, `dispatching`, `delivered`, `failed` or `unknown`) and the stamp
**And** (A14) `GET /proposals/<p_id>` returns that one proposal, in the same shape, whatever its status, or 404 with the error shape for an unknown ID; the Slack alert's "Review in DxP" link now opens the report page, which lists its proposals with `?report_id=` (V10, V11); there is no `p_id=` query parameter (D42)
**And** low-confidence proposals come first, then the rest, newest first
**And** for a `list` field the proposal adds an entry and never replaces one
**And** the response carries quotes only, never a Source item's `raw_text`.

### Story 2.3: Accept, edit or reject a Proposed change, keeping the history

**Points:** 2 · **Time:** ~1.5 h (M, 5 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR16, FR17, NFR2, AD-1, AD-4, AD-17, AD-19 · **Demo path** · **Owner:** Luis
**PRs:** A14 `story/2.3-proposals-decisions` (value review only: `ledger/review.py`, `POST /diagnostics/<dx_id>/values/<value_id>/review` and their tests; it calls A06's `ledger/apply.py`, Luis). Cards in `development-plan.md`.
**Superseded in part (14 Nov, V8, V24):** `POST /proposals/<p_id>/decision` and the kind `decide_proposal` are superseded by the report decision `POST /reports/<report_id>/decision` (Story 10.8, A24); the route stays registered and 501, and `ledger/decide.py` is not written. The criteria about a per-proposal decision below are kept for history only; what A14 builds is the value review in the last two criteria, and the history rules (superseded values kept with Evidence, `decided_by`, `decided_at`, `reason`) hold for the report decision too.

As a Reviewer,
I want to accept, edit or reject each change with a reason, and to review unreviewed values,
So that no agent change reaches a tracked Record without a logged human decision.

**Acceptance Criteria:**

**Given** a `pending` Proposed change filed by a run
**When** (superseded, history only) I `POST /proposals/<p_id>/decision { action: accept | edit | reject, value, reason }` with the web app's server-side key
**Then** the decider is the Reviewer principal resolved from the key; no name in the body is read
**And** `edit` and `reject` without a `reason` return 400, and an edited value outside the field's allowed values returns 400
**And** the decision passes `gate.evaluate()` under Sam's Reviewer grant `sam@v1` (`decide_proposal`, scope the same `diagnostic_ids` as the agent grant, Story 9.2); check 4 records `n/a` for Reviewer kinds, and check 5 records `n/a` outside a run
**And** the Decision is written with `run_id: null`, `agent: null`, `initiated_by` the Reviewer principal, the Reviewer's stamp, a server-generated `request_id` (so a blocked Reviewer decision can be retried and gets a new Decision) and `cause { proposal_id, origin_run_id }`, where `origin_run_id` is the run that filed the proposal (D19, D20)
**And** `accept` and `edit` call `ledger.apply(proposal_id)` (Story 1.6, A06), which claims the proposal, makes the guarded update, upserts the edges, emits `value_applied` and marks it `applied`; A14 owns `ledger/review.py` (not `ledger/decide.py`, which is superseded) and does not edit `ledger/apply.py`
**And** apply recovery runs on every decision call before the decision is applied (Story 1.6)
**And** a second decision on the same proposal does nothing and returns its current state
**And** `reject` marks the proposal `rejected` with the reason and changes no Record value
**And** the superseded value stays on the Record with its Evidence, `decided_by`, `decided_at` and `reason`; nothing is deleted
**And** `lifecycle_stage` changes only through this path once a Diagnostic exists
**And** `POST /diagnostics/<dx_id>/values/<value_id>/review { action, value, reason }` accepts, edits or rejects an `unreviewed` value through `ledger.review_value()` with the action kind `review_value` (D16), gated under `sam@v1` and recorded the same way with `run_id: null`, the Reviewer's stamp and a `request_id`; `edit` and `reject` without a reason return 400; it returns the `Record`
**And** each decision emits an event with the Reviewer's stamp, and the response's `rule_draft` is null.

### Story 2.4: Review screen

**Points:** 3 · **Time:** ~3.5 h (M, 7 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR15, FR16, FR18, accessibility convention · **Demo path** · **Owner:** Vlad
**PRs:** B04 `story/10.10-report-page` (the report page with the small pending-reports list, Vlad). Cards in `development-plan.md`.
**Narrowed (14 Nov):** the separate Review list screen is replaced by a small pending-reports list linking to the report page (Story 10.10), where decisions are made. The per-proposal rows below remain only as the proposals section inside a report; the focused `?proposal=` page is no longer a Slack target.

As a Reviewer,
I want a short list of pending research reports, each opening the full report,
So that Sam can find and approve the agent's report on camera in seconds.

**Acceptance Criteria:**

**Given** (B04) a small pending-reports list at `web/app/reports/`, reading `GET /reports?status=pending` (Story 10.4), showing each report's headline, discovery, counts of related items and memories used, and created time, each linking to `web/app/reports/[report_id]/`; it polls every few seconds and the top bar's count uses the same route
**And** pending reports and accepted knowledge are labelled differently (V5)
**When** a report's proposals are shown inside the report page
**Then** each row shows Diagnostic (linked to its "Accepted knowledge" view), field, current value, new value marked pending, the quote with source link and data date, confidence (low marked) and the `run_id` that filed it; decisions are made once for the whole report (Story 10.10), so rows carry no buttons of their own, and there are no Slack buttons, because approval and rejection happen in DxP, never in Slack
**And** (B04) the "Accepted knowledge" view answers at `web/app/diagnostics/[dx_id]/`, the target of the alert's "Open diagnostic" link
**And** the list is reachable and usable by keyboard, with labelled links
**And** a decided report leaves the pending list and the count updates; the list polls `GET /reports?status=pending` (A12 is cut, D40)
**And** a 400 or 403 from the API is shown as a message, and the list stays
**And** no name is chosen or sent; the decider is resolved server-side from the key.

### Story 2.5: Value history on the Record page

**Points:** 1 · **Time:** ~1.5 h (S, 3 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR17 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

As a Director of Diagnostics,
I want to see every earlier value of a field with its Evidence, who decided and when,
So that I can see how the picture of a diagnostic changed.

**Acceptance Criteria:**

**Given** a Record with superseded or rejected values
**When** I expand a field's history
**Then** each earlier value shows its quote, source, data date, state, `decided_by`, `decided_at` and the reason for an edit or rejection (kept on the value entry by Story 2.3), newest first
**And** the Lifecycle stage shows each earlier stage with its date.

### Story 2.6: Draft, activate and switch off a Learned rule

**Points:** 3 · **Time:** ~2.4 h (M, 6 h developer estimate × 0.4, model work) · **Lane:** [API] · **Covers:** FR19, AD-7, AD-11 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Pivot change:** Returned as stretch Story 9.11, which is now cut (14 Nov). Stays deferred: reviewer memory (Stories 10.5, 10.6) is what the agent learns from, and memories never become rules or change permissions.

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

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR19, NFR5, NFR6 · **Demo path** · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Still deferred (14 Nov):** the memory panel inside the report page (Story 10.10) replaces a rules page.

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

**Points:** 3 · **Time:** ~2.8 h (M, 7 h developer estimate × 0.4, model work) · **Lane:** [API] · **Covers:** FR12, FR13, FR14, FR30, AD-10, AD-11 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR12, FR13, FR14, NFR6 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR20 · **Demo path** (the Home page in Story 6.4 shows it) · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

As a Director of Diagnostics,
I want a digest of what changed for my team and what is waiting for review,
So that I can catch up in one view.

**Acceptance Criteria:**

**Given** `GET /api/v1/digest?team_id=`
**When** the Team has undismissed Alerts or pending proposals on Diagnostics that match its profile
**Then** the response lists them, and the web app shows them as a Digest panel on the Home page
**And** a Team with nothing applicable gets an empty digest and the panel says "nothing new".

### Story 3.4: Audio briefing for an Alert

**Points:** 1 · **Time:** ~0.9 h (S, 3 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR14 · **Cut candidate:** Alerts work without it · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Pivot change:** Replaced by stretch Story 9.10 (spoken audit briefing).

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

**Points:** 1 · **Time:** ~1 h (S, 2 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR14 · **Cut candidate:** goes with Story 3.4 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Pivot change:** Replaced by stretch Story 9.10 (spoken audit briefing).

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

**Points:** 2 · **Time:** ~4.8 h (M, 6 h developer estimate × 0.8, search) · **Lane:** [API] · **Covers:** FR9, AD-8, AD-15 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.
**Still deferred (14 Nov):** the synonym mapping stays deferred; Vector Search and embeddings are restored for related-evidence retrieval in Story 10.2 (A19+A20), on evidence and findings, not on `diagnostics.search_text`.

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

**Points:** 3 · **Time:** ~5.6 h (M, 7 h developer estimate × 0.8, search) · **Lane:** [API] · **Covers:** FR21, FR22, AD-11, AD-15 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 3 · **Time:** ~3.5 h (M, 7 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR8, FR21, FR22, accessibility convention · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR24, AD-8, AD-14 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

As a Director of Diagnostics,
I want to save chosen diagnostics as a Shortlist named after what I need them for,
So that I can come back to it and share it.

**Acceptance Criteria:**

**Given** new routes `POST /api/v1/shortlists { team_id, intended_use, query, diagnostic_ids, actor }` and `GET /api/v1/shortlists?team_id=`, added to the contract and the generated types
**When** I save a Shortlist
**Then** it is stored in `shortlists` and the Team's last Intended use is updated in `teams`
**And** the find page has row checkboxes and a "Save shortlist" action with a name field.

### Story 4.5: Export the comparison or Shortlist with references

**Points:** 1 · **Time:** ~0.9 h (S, 3 h developer estimate × 0.3, back end) · **Lane:** [WEB] · **Covers:** FR25, NFR11 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR29 · **Cut candidate:** judges barely notice it in three minutes · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR29, AD-1, AD-6 · **Cut candidate:** goes with Story 4.6 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 1 · **Time:** ~1 h (S, 2 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR9 · **Cut candidate:** listed in `triage-medium-low.md` · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 2 · **Time:** ~2.4 h (M, 6 h developer estimate × 0.4, back end) · **Lane:** [WEB] · **Covers:** FR26, FR43, AD-13 · **Cut (14 Nov)** · **Owner:** Luis
**PRs:** none — cut (A15 removed under the proposal's section 7, cut 3; `GET /graph` stays registered and 501).
**Cut (14 Nov):** A15 is cut under the proposal's section 7; the report's relationship list (Story 10.3) is enough. Revived only after the event, and then only as an evidence-relationship view inside the report page.

As the web developer,
I want the nodes and links one run touched served by the API, with context only on request,
So that the impact view never derives links itself and never attributes to a run what it did not do.

**Acceptance Criteria:**

**Given** `GET /api/v1/graph?run_id=<run_id>`
**When** it is called
**Then** it returns only the changed elements: the values, proposals, edges and Slack notifications the run itself created or changed, each node and link carrying that `run_id`
**And** nodes have IDs `<type>:<value>`, type, label, and for Diagnostics the Lifecycle stage, Early research and sample type
**And** every Link carries `status` (`pending` or `applied`) and `proposal_id` (D29): a pending proposal appears as a link from its Diagnostic to the proposed value's node with `status: pending`, and an applied one with `status: applied`; an edge keeps the `run_id` of the run that first created it
**And** each Slack notification of the run is a node `notification:<action_id>` with its status (`delivered`, `failed` or `unknown`) and `posted_at`, linked to its Diagnostic with kind `notification`, built at read time from `actions`, never stored in `edges`; it carries no webhook URL
**And** a blocked decision adds nothing to the graph, because it changed nothing
**When** `context=true` is added
**Then** the touched Diagnostics' other neighbours are added from `edges`, each node and link marked `context: true` and carrying no `run_id`
**And** a run that touched nothing returns empty `nodes` and `links`
**And** it is supporting: no core PR depends on it, and A15 may be cut (D37).

### Story 5.2: Graph view with click-through

**Points:** 3 · **Time:** ~5.6 h (M, 7 h developer estimate × 0.8, graph view) · **Lane:** [WEB] · **Covers:** FR26, FR43, NFR5 · **Cut (14 Nov)** · **Owner:** Vlad
**PRs:** none — cut (B05 removed under the proposal's section 7, cut 3).
**Cut (14 Nov):** B05 is cut under the proposal's section 7. Revived only after the event, and then only as an evidence-relationship view inside the report page (Story 10.10), not a separate screen.

As a judge,
I want to see what one run changed as a small graph, and its surroundings only when I ask,
So that I see the agent's footprint at a glance and can click through to the Record or the Slack alert's action in the audit.

**Acceptance Criteria:**

**Given** the Run impact view using `react-force-graph-2d` loaded with `next/dynamic` and no server rendering, reading `GET /graph?run_id=` (Story 5.1)
**When** it loads for a run
**Then** it shows only the run's changed elements, each node type with its own colour, shape and a legend, and pending proposal links drawn as pending
**And** clicking a Diagnostic opens its Record; clicking a notification node opens its decision in the Audit view, showing the Slack alert's result
**And** a "Show context" control loads `context=true`; context nodes and links are visibly marked as context (muted and labelled) and are never shown as changed by the run
**And** beside the graph, a keyboard-usable list of the changed elements, each with its `run_id`, is the non-visual equivalent
**And** an empty run shows "This run changed nothing"
**And** the view and every link to it sit behind the `impact` flag; with the flag off nothing links to it, and no core screen depends on it (D37). B05 may be cut.

### Story 5.3: Highlight what changed since the last visit

**Points:** 2 · **Time:** ~3.2 h (S, 4 h developer estimate × 0.8, graph view) · **Lane:** [WEB] · **Covers:** FR27, AD-10 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

Stays deferred (14 Nov). Reviewer memory is superseded by Stories 10.5 and 10.6, which keep Team-scoped, attributable, correctable and revocable memories in a plain Atlas collection, `memories`; the Agent Memory preview SDK is not used on Saturday.

### Story 6.1: Memory adapter with two backends

**Points:** 2 · **Time:** ~3 h (M, 6 h developer estimate × 0.5, new infra) · **Lane:** [API] · **Covers:** FR19, FR28, NFR5, NFR10, AD-8 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 1 · **Time:** ~0.6 h (S, 2 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR28, NFR6 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

As the team,
I want each synthetic Team to have a short history of past searches, opened Records and dismissals,
So that the resume on camera has something real to recall.

**Acceptance Criteria:**

**Given** the three synthetic Teams
**When** the seed runs
**Then** each gets five to ten episodes written through `remember_episode` with `session_id` starting `synthetic_`, a last Intended use and one Shortlist
**And** running it twice does not duplicate them.

### Story 6.3: Resume summary on return

**Points:** 2 · **Time:** ~1.6 h (S, 4 h developer estimate × 0.4, model work) · **Lane:** [API] · **Covers:** FR28, AD-8, AD-10 · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

**Points:** 3 · **Time:** ~5.6 h (M, 7 h developer estimate × 0.8, graph view) · **Lane:** [WEB] · **Covers:** FR27, FR28, NFR5, `DESIGN.md` graph-led hero · **Demo path** · **Owner:** Luis · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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
**And** if memory is unavailable, the panel still shows what changed and the last Intended use, and says "Memory unavailable right now"
**And** the "Reopen" buttons open Find (Stories 4.3 and 4.4); if those stories are not built, the panel shows the last Intended use and Shortlist as text without the buttons.

## Epic 7: Capture on the go (P3)

A user types a Diagnostic name or a note and DxP turns it into a partial Record for the agents to fill.

### Story 7.1: Quick capture of a name or note

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** PRD section 4.9, UJ-4 · **Cut candidate:** P3 · **Owner:** Vlad · **Deferred (pivot, 13 Nov)**
**PRs:** none — deferred.

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

A judge opens a working production URL at any point in the day, and at submission receives the description, the public repository and a 60-second video that names which MongoDB capability powers which behaviour, with disclosure and credits; the 3-minute live demo for judging follows at 17:15.

### Story 8.1: Deploy a walking skeleton to production

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, new infra) · **Lane:** [WEB] · **Covers:** NFR8, NFR12, AD-23, AD-24, PR and merge · **Demo path** · **Owner:** Luis
**PRs:** A04 `story/8.1-deploy-sandbox` (CI, Vercel and Modal deploy against the Atlas Sandbox, Luis). Cards in `development-plan.md`.

As the team,
I want the API on Modal and the web app on Vercel live against the Atlas Sandbox by 12:00, and every story merged through a checked pull request,
So that deploy and merge problems surface early, not at 17:00.

**Acceptance Criteria:**

**Given** the contract stub (A01) and the web skeleton (B01) merged; A04 merges after B01, and B01 is done when it builds locally (D39)
**When** one person runs `modal deploy` with `DXP_DB=dxp` on the Atlas Sandbox and the web app deploys to Vercel production with `NEXT_PUBLIC_API_URL`
**Then** the production URL loads the shell and the API answers, with stub routes returning the 501 error shape
**And** A04 owns `backend/modal_app.py` and the deploy configuration only; the allowed CORS origins are set as an environment value that `app.py` (A01) reads, and A04 edits no API file
**And** A04 records in `docs/deploy.md` whether Vector Search and Automated Embedding are available on the sandbox (OD1) and whether `mongodump` and `mongorestore` work against it (OD6); change streams are no longer checked (Story 9.9 is cut, OD5) and `DXP_FEED` is retired
**And** (A04, Luis) secrets go in two places only, entered from `.env` and never committed, logged or shown on screen (D48): Vercel holds `DXP_API_KEY` and `NEXT_PUBLIC_API_URL`; the Modal secret holds `DXP_AGENT_KEY`, `SLACK_WEBHOOK_URL`, `ANTHROPIC_API_KEY`, `MONGODB_URI`, `DXP_BASE_URL`, `DXP_ALLOWED_ORIGINS`, `DXP_EMBEDDING`, `ELEVENLABS_API_KEY` (OD3), `HEYGEN_API_KEY` (OD7) and `VOYAGE_API_KEY` only if cleared (OD1), with `DXP_BASE_URL` set to the Vercel production URL
**And** `.env.example` (A01) lists, with no values: `MONGODB_URI`, `DXP_DB`, `ANTHROPIC_API_KEY`, `DXP_API_KEY`, `DXP_AGENT_KEY`, `DXP_SEED_KEY`, `SLACK_WEBHOOK_URL`, `DXP_BASE_URL`, `DXP_ALLOWED_ORIGINS`, `DXP_DEMO_PACE`, `DXP_EMBEDDING`, `VOYAGE_API_KEY`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY`, `DXP_FEATURES`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_DXP_FEATURES`, `LANGSMITH_TRACING`, `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT`; `DXP_FEED` is dropped, and `DXP_GITHUB_TOKEN` and `DXP_GITHUB_REPO` exist nowhere (D48)
**And** a GitHub Actions workflow runs on every pull request into `main`: the web app's type check and build, and the backend tests
**And** Vercel builds a preview for each pull request and deploys `main` to production on merge
**And** `main` accepts changes only through a pull request with passing checks, merged by squash
**And** (A04) `docs/deploy.md` says who deploys the API and how, and describes the PR and merge steps; A04 does not edit the README, which B07 alone owns (D36).

### Story 8.2: Rehearse the live run

**Points:** 2 · **Time:** ~2 h (run time, not shortened by agents) · **Lane:** [API] · **Covers:** NFR5, NFR10 · **Demo path** · **Owner:** Luis
**PRs:** A16 `story/8.2-rehearsal` (Live-demo rehearsal and reset procedure; pass 1 is core acceptance, with I2 folded in; a reset, then pass 2 and the reset for the video, Luis, 15:00 to 16:10; starts when I3 has merged; 20 minutes of hard float remain at the 16:30 freeze, conditional on the merge milestones, V30, V36). Cards in `development-plan.md`.
**Updated (14 Nov):** I2 is folded into the rehearsal's first pass (proposal section 7, cut 1), and the demo order is V16 (replaces D33). The setup and the loop it rehearses are I1 (13:30 to 14:45, Stories 10.1, 10.4 to 10.7, 9.4) and I3 (14:45 to 15:00: approval, promotion, authorisation and audit, Stories 10.8 and 10.10; Story 10.9, stretch since V39, joins, to 15:15, only if A25 is merged and the loop is green by 14:30, V30). The demo framing follows V33 to V35, the gap and task V26 and V33, and the narration V27 and V32.

As the team,
I want the 3-minute live demo run end to end on the sandbox before recording, then reset,
So that what we show the judges works the first time.

**Acceptance Criteria:**

**Given** (I1, setup) on the Atlas Sandbox, created during the event (V15, D1): the grant and policy seed, the FDA seed, the research scope, the prior collection loaded in `baseline` mode by NCT ID (Story 1.4), embeddings written and the vector index READY (or the text-search fallback recorded, OD1); then (I1 step 2) the setup run `POST /runs { grant_id: "lbdx", set: "nct:NCT05715229" }` (NCT05715229 is not in the prior collection) files a pending report on NCT05715229 and Sam rejects it through the real report page with "Terminated trial with no posted results: describe its status; do not state outcomes", creating memory M1 (Story 10.5); then the post-setup snapshot of `dxp` is taken with `mongodump` (A13, D41; OD6), so it includes M1, and `scripts/reset_demo.py` restores it before the rehearsal
**And** at 10:45 the live API is queried for the scan and the anchor is whichever in-scope early-stage trial is actually updated after the chosen cursor, with its update date, status and results verified in the response; NCT04712877 is the expected candidate (OD2, V36)
**When** a discovery run is started from the Run console under the agent grant `lbdx@v1` for "Team Liquid Biopsy Dx" over the research scope (D56, V1), with `DXP_DEMO_PACE` set
**Then** the steps run in the demo order V16, used for both the 60-second video and the live demo:
1. the discovery run starts;
2. the scan finds the anchor, NCT04712877 if it is the trial verified at 10:45 (Story 10.1); the narration says the scan looks only at what changed since the scope's last scan (V32);
3. the proposed link of the record's "FoundationOne CDx" mention to the Team's plasma scope is blocked by team scope (check 2), because the configured scope excludes the tissue assay, with one blocked Decision citing the mention and the scope rule; this guarantees must-show 3 (V35, V37); if draft 1 (written without memories) makes an unsupported performance or results claim (for example that the trial "showed" blood profiling detecting drivers), the claim-accuracy policy blocks it before filing (RECRUITING, `has_results: false`) with one blocked Decision, and it is shown whenever it occurs, since the model may not write it (V21, Story 10.7);
4. the report is filed as pending, framed as a new trial signal worth investigating: "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." It shows its related evidence (expected: `extends` the prior collection's advanced-NSCLC evidence, with two checked quotes, or no relationship), the intervention wording verbatim ("ctDNA, tumor NGS"; other names "FoundationOne CDx", "FoundationOne Liquid"), under uncertainties the unresolved mention "FoundationOne Liquid" and "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample.", the gap "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?", and M1's effect: "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet"; the narration says M1 came from a correction earlier in the day (Stories 10.4, 10.6, V32, V33);
5. one Slack alert for the report arrives in `#all-mango-db-hackathon`, recorded `delivered`, and its "Review in DxP" link opens `${DXP_BASE_URL}/reports/<report_id>` (Story 9.4);
6. if B06 and B08 merged and their flags are on: the script is on the page as text; Sam presses "Generate briefing" and plays it, and the avatar video rendered on demand for this demo report plays if it is ready; otherwise the player shows "Rendering" or "unavailable" and the demo moves on (Stories 10.11, 10.12, V29);
7. stop is shown honestly, on a second run with remaining items or on the follow-up task's run if it started by itself and is still running: `stopping`, then `stopped`, with admitted actions finishing (Story 9.5, V38);
8. Sam approves the report: NCT04712877 is accepted into the scope's evidence collection (no assay record changes) and the follow-up task is authorised; the page and the narration say "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." when `task_run` is on, or "Approved: 1 update accepted. Follow-up task authorised; not run." when it is off (Story 10.8, V27, V35, V38);
9. only if A25 joined I3 (stretch, V39): the follow-up task starts by itself under its own grant and gate and reports which of the records it searched have posted results, with the query, the number of records searched and the limit (at most 5; "No matching results found among the records searched" when none, V42), filed as pending related evidence (Story 10.9, V33); otherwise nothing claims or narrates completed follow-up work;
10. the Audit view answers "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" (Stories 9.6, 9.8)
**And** nothing said on screen or in the narration states that the trial studies or uses FoundationOne Liquid CDx or FoundationOne CDx, or shows any assay's performance; both names are called a "mention" or "named in the record" (V33, V37)
**And** the rehearsal's first pass is core acceptance (I2 folded in); the briefing, the avatar video and the task run join only if their own acceptance checks passed and their flags are on (V28, V39)
**And** (V44, source check) during the rehearsal one person checks one complete report and its briefing or narration script twice: (a) side by side with the exact source version the report used (its stored `version_id`), confirming every claim is supported by that version; (b) separately, that version against the live ClinicalTrials.gov record for the anchor, where a difference is recorded as "changed since the run", not as an error in the report; the rehearsal is not done until both checks pass
**And** (A16) the reset procedure is written in `docs/demo-and-reset.md` (not the README, which B07 owns); A16 uses A13's `scripts/reset_demo.py` and does not create it (D41): `mongorestore` of the post-setup snapshot returns `dxp` to the state after setup (with M1 and the initial cursor), so each take starts from the same point; the rehearsal's Slack alerts stay in the channel, and each take's alert is told apart by its action ID and run ID
**And** the reset runs before each rehearsal (the first being core acceptance), before the video (16:30) and between submission and the live demo (16:55 to 17:10) (D34, D41)
**And** the integrators' smoke tests run with `DXP_DB=dxp_smoke`, never in `dxp` (D41).

### Story 8.3: Submission package

**Points:** 1 · **Time:** ~1 h (S, 2 h developer estimate × 0.5, docs) · **Lane:** [WEB] · **Covers:** NFR7, NFR10, NFR11, NFR13 · **Demo path** · **Owner:** Vlad
**PRs:** B07 `story/8.3-submission` (README with the prepared vs built-today table, submission text, 60-second video script, Vlad, done by 14:00). Cards in `development-plan.md`.

As a judge,
I want a README and description that say what was built on the day, what was prepared before, and which MongoDB capability does what,
So that I can judge the work fairly.

**Acceptance Criteria:**

**Given** the public repository
**When** a judge opens the README
**Then** it describes DxP as a proactive diagnostic-evidence research agent for Statement 1, "Agents You Can Audit" (discover, relate, remember, gate, propose, notify, brief, decide), with the pivot of 13 November and the discovery-agent proposal of 14 November
**And** (B07) the README is owned by B07 alone; other PRs write `docs/deploy.md` (A04), `docs/demo-and-reset.md` (A16) and `docs/clearance.md` (Luis), and the README links them (D36)
**And** a table separates material prepared before the event (planning documents, skills, `scripts/data/`, `data/`, logo images, the Slack incoming webhook and its channel `#all-mango-db-hackathon`, created and tested before the event, and the modified tracker script) from what was built on 14 November
**And** it states what is not reused: no code from `scripts/data/` or any `dxp-*` skill, no file from `data/`, no prepared logo and no script used to test the Slack webhook (the notifier is written during the event), unless an organiser cleared it in writing, and lists the open organiser questions
**And** it carries the MongoDB capability table (grants and policies with schema validation, conditional updates for the action claim, admissions and stop, Atlas Vector Search for related evidence, the `memories` collection for reviewer memory, the `decisions` and `actions` audit history) and the credits line
**And** it links the production URL; R1 adds the video link at submission (Story 8.4)
**And** the submission text and the 60-second video script are written by 14:00.

### Story 8.4: 60-second video, submission and live demo

**Points:** 0 (about 30 minutes, both people) · **Lane:** both · **Covers:** NFR5, NFR10 · **Demo path** · **Owner:** Luis and Vlad
**PRs:** B07 `story/8.3-submission` (60-second video script, Vlad, by 14:00); R1, no branch (Record the video and submit, Luis and Vlad, 16:30 to 16:55). Cards in `development-plan.md`.
**Updated (14 Nov):** the video follows V17 (replaces D52) and the live demo follows V16 (replaces D33).

As a judge,
I want a 60-second video of the research agent discovering, relating, remembering, being blocked and being approved, plus a 3-minute live demo,
So that I see real behaviour, not a mock-up.

**Acceptance Criteria:**

**Given** (B07) the 60-second script written by 14:00, and `dxp` reset to the post-setup snapshot, which includes memory M1 created by Sam through the real UI during I1's setup step (Story 8.2, V15, D41), before 16:30
**When** (R1) the video is recorded 16:30 to 16:50, after code freeze, with `DXP_DEMO_PACE` set
**Then** it follows these timings (V17): 0 to 10 s, the research scope and the agent's identity (the identity card, the grant as `{grant_id}@v{version}` and the policy set as `ps_ab12… (N policies)`)
**And** 10 to 25 s shows the discovery of the anchor (NCT04712877 if verified at 10:45) as a new trial signal worth investigating, in the V33 wording, its related evidence with relationship labels and quotes, its evidence gap, and M1 changing the wording ("Wording changed because of M1 (Sam, 14 Nov)"), with the narration that the scan looks only at what changed since the last scan and M1 came from a correction earlier in the day (V32)
**And** 25 to 35 s shows the block before it takes effect: an unsupported performance or results claim blocked before filing with its one blocked Decision if draft 1 wrote it on that take, otherwise the blocked link of the record's "FoundationOne CDx" mention to the plasma scope (team scope), which always occurs (V21, V35, V37)
**And** 35 to 45 s shows the Slack alert in `#all-mango-db-hackathon` whose "Review in DxP" link opens `/reports/<report_id>`
**And** 45 to 60 s shows Sam's approval with the words "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27) if `task_run` is on, or "Approved: 1 update accepted. Follow-up task authorised; not run." if it is off (V38), the follow-up task running under its own grant and gate only if it actually ran in that recording (stretch, V39), and the Audit view answering "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"
**And** the briefing and the avatar video are not required in the 60 seconds; they appear in the live demo only if ready (on demand, V29)
**And** nothing in the video or its narration says the trial studies or uses FoundationOne Liquid CDx or FoundationOne CDx, or shows any assay's performance; both are "named in the record" (V33, V37); the close names the bigger value, team-specific, longitudinal intelligence on the diagnostics a team follows, of which the demo shows one turn (V32)
**And** it names the MongoDB capability behind each behaviour (Vector Search for related evidence, the `memories` collection, grants and policies with schema validation, conditional updates for claim and stop, the `decisions` and `actions` audit history) and shows only what was built on 14 November
**And** the video and the live demo never claim or narrate completed follow-up work unless the task actually ran in that recording or demo; when it did not, they say "Follow-up task authorised; not run" (V39)
**And** the video is recorded only after the V44 source check of Story 8.2 passed for the report it shows (the claims against the stored source version, and that version against the live record)
**And** (R1) the description, public repository, video and team members are submitted by 16:55, and R1 adds the video link to the README
**And** (R1) the reset (`scripts/reset_demo.py`, D41) is run again between 16:55 and 17:10, and the 3-minute live demo for judging at 17:15 follows the V16 order of Story 8.2: start the discovery run, the scan finds the anchor, the team-scope block on the record's "FoundationOne CDx" mention (and an unsupported claim block when draft 1 wrote it, V21), the report is filed with its gap and M1's effect, the Slack alert opens the report on the second screen, the briefing and the avatar video play if ready, stop is shown honestly, Sam approves ("Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." with `task_run` on, else "… Follow-up task authorised; not run."), the follow-up task starts by itself and is gated only if A25 joined (stretch), and the audit question is answered.

## Epic 9: Governed agent actions

Added by the pivot on 13 November for Problem Statement 1, "Agents You Can Audit". The agent acts only as a named run with a scoped grant: every change to a record and every action in another system passes a versioned policy check first, a blocked action changes nothing and leaves one blocked Decision and one `action_blocked` event, one allowed action sends a real notify-only Slack alert to `#all-mango-db-hackathon` (approval and rejection stay in DxP), a person can stop the run at any moment, and the audit view replays the run and answers "who authorised this action". The first allowed-and-blocked loop must be green on the Atlas Sandbox by 14:30 (I1).

Since 14 November (the discovery-agent proposal) this epic is the governance under Epic 10's research loop: Stories 9.2, 9.3, 9.4, 9.6 and 9.8 gain the additions below, Story 9.9 and Story 9.11 are cut, and Story 9.10 is superseded by Story 10.11.

### Story 9.1: Runs and identity

**Points:** 2 · **Time:** ~0.9 h (S, 3 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR31, AD-17 · **Core** · **Owner:** Luis
**PRs:** A01 `story/1.1-contract` (Contract, including the run shapes and the frozen `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle`, `runs.finish` and `runs.stop` signatures, Luis); A07+A11 bundle `story/9.5-runs-stop` (Runs with the `discover`, `nct:` and `task:` sets: identity, admissions, stop, and the audit API, Luis). Cards in `development-plan.md`.

As a reviewer auditing the agent,
I want every run to carry two server-set identities, who started it and which agent executes it, and every write, event, decision and external action stamped with them,
So that I can always tell which agent, model, prompt and policy set did something, and who started it.

**Acceptance Criteria:**

**Given** `POST /api/v1/runs { grant_id, set }` with the `X-DxP-Key` header, where `set` is `discover` (agent grant, Story 10.1), `nct:<NCT ID>` (setup only) or `task:<task_id>` (only under that task's grant, Story 10.9; 403 otherwise); there is no `team_id` in the body, because the grant defines the Team (D18)
**When** a run is requested
**Then** the server resolves the caller from the key (401 only for an unknown key, D17), loads the latest version of the grant, and checks that it is active and that the caller is in its `startable_by`; otherwise it returns 403 and creates nothing
**And** it creates a `runs` document with `run_id`, `agent` (the executing agent principal named by the grant), `initiated_by` (the caller), the grant version pinned at start (`grant_id`, `grant_version`), model and prompt version from `llm`, the `policy_set_version`, `team_id` taken from the grant, and `status: running`; none of them is taken from the request body, and a client-supplied name never confers permission
**And** it returns 409 while another run is `running` or `stopping`
**And** `GET /runs` and `GET /runs/<run_id>` return the run with its identity, status and counts (including `early_research`)
**And** a run becomes `done` only through `runs.finish(run_id)` and `failed` only when the pipeline raises an error it cannot recover from (D23)
**And** the worker executes with the agent's key and the `run_id`; every agent write requires a `run_id`, and a write whose key does not resolve to that run's `agent` is refused and reaches neither the ledger nor Slack
**And** `runs.stamp(run_id)` is the only stamp maker, and every Finding, proposal, value entry, edge, event, decision and action of the run carries its stamp
**And** a Reviewer decision is allowed without a run: it carries `run_id: null`, `agent: null`, `initiated_by` the Reviewer principal, the Reviewer's stamp and `cause { report_id | memory_id | action_id | proposal_id, origin_run_id }`; agent writes without a `run_id` are not allowed (D19)
**And** the seed runs only from the command line with the dedicated seed key; its writes carry `{ kind: "seed", principal: "seed" }` and `run_id: null`, its decisions carry `agent: "seed"` and `initiated_by: "seed"`, and no route starts a seed
**And** the caller's identity has the shape `Principal { id, name, kind, actions }`, where `actions` are the actions of the caller's current grant; `GET /whoami` (Story 9.2) returns it (D53)
**And** `runs`, its index on `status` and its schema validation are created by `store.ensure_indexes()`.

### Story 9.2: Grants and versioned policies in Atlas

**Points:** 3 · **Time:** ~1.5 h (M, 5 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR32, FR33, AD-18 · **Core** · **Owner:** Luis
**PRs:** A03 `story/9.2-grants-policies` (Grants, policies and policy sets with schema validation, seeded; server-side principal resolution, Luis). Cards in `development-plan.md`.
**Updated (14 Nov):** grant additions for the discovery loop (V1, V2, V6 to V9, V12, V13), in the last criterion below. Since V29 the briefing and the avatar video are requested on demand by the Reviewer from the report page, so `generate_briefing` and `generate_avatar_video` and their destinations move from `lbdx@v1` to `sam@v1` (a derived consequence of V29: the run no longer calls them).

As a reviewer auditing the agent,
I want the agent's authority written down in Atlas as versioned grants and hand-written, versioned policies,
So that what the agent may do is explicit, checkable and reconstructable for any past decision.

**Acceptance Criteria:**

**Given** the collections `grants`, `policies` and `policy_sets`, each with `$jsonSchema` validation applied at creation (`validationLevel: strict`, `validationAction: error`)
**When** `python -m dxp.gate.seed` runs from the command line with the seed key, reading the hand-written documents in `gate/seed_data/` (D36)
**Then** it inserts hand-written grants and the demo policies, and running it twice changes nothing:
1. the agent grant `lbdx@v1` for Team "Team Liquid Biopsy Dx": agent principal `dxp-curator`, `startable_by` with `sam`, `scope.diagnostic_ids` exactly the Diagnostics whose trade names are "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay", matched through `normalise_name()` (every other Diagnostic, FoundationOne CDx among them, is out of scope and blocked by check 2, D32, D45, D56), `scope.scope_id` the research scope (V1), destinations `source:clinicaltrials.gov`, `ledger` and `slack:#all-mango-db-hackathon`, actions `search_source`, `file_proposal` (also gating a report as a whole, as the report-level `file_proposal`, and the report's pending update to the scope's evidence collection, V35) and `notify_slack`, `expires_at`;
2. Sam's Reviewer grant `sam@v1`: principal `sam`, actions `[decide_report, authorise_task, create_memory, correct_memory, revoke_memory, review_value, resolve_notification, generate_briefing, generate_avatar_video]` (`decide_proposal` is superseded and granted to no one, V8; the two media kinds since V29), destinations `ledger`, `tts:elevenlabs` and `video:heygen`, scope the same `diagnostic_ids` and `scope_id` as the agent grant (D16);
3. the seed grant `seed@v1`: principal `seed`, actions `[apply_value]`, destination `ledger`, scope `{ all: true }` (D16)
**And** at 10:45, A03 generates `DXP_AGENT_KEY`, `DXP_API_KEY` and `DXP_SEED_KEY` locally into `.env`; `python -m dxp.gate.seed` computes each grant's `key_hash` from the environment at seed time, so `gate/seed_data/` holds no key hash, and no key is ever committed (D48)
**And** `scope.all: true` is valid only for the seed principal; the validator rejects it on any other grant
**And** a document that breaks the schema is rejected by Atlas, not only by application code
**And** grants and policies are never edited in place: a change inserts a new version, and a revocation or expiry is a new version with that status
**And** selection works the same way for both: for each grant or policy ID, take the latest version first, then check its status; only a latest version that is `active` (and unexpired, for a grant) counts, so a newer `revoked` or `expired` version blocks
**And** the first time a policy set is used, a `policy_sets` document `{ _id: policy_set_version, members: ["<policy_id>@v<n>", ...], created_at }` is written, where the version is the hash of the sorted members, so any decision's policy set can be rebuilt
**And** the API hashes `X-DxP-Key` with SHA-256 and resolves the principal (the agent, Sam, or the seed) by `key_hash` across all grant versions, whatever their status; 401 means only an unknown key, and a revoked or expired grant is caught by check 1 and recorded as a blocked Decision (D17); the raw key is never stored, logged or traced; a request that names a different actor in its body is still judged as the key's principal
**And** `GET /grants` (each grant with its Team and `startable_by`, so the Run console can list the grants the caller may start), `GET /grants/<grant_id>` (latest version; `?version=` for an earlier one) and `GET /policies` return the grants and the current policy set with their versions, for the Run console's grant picker and identity card, and `GET /whoami` returns `Principal { id, name, kind, actions }`, where `actions` are the actions of the caller's current grant, for the read-only "Signed in as" chip and for showing the Resolve control (D53)
**And** the 14 Nov additions above (the research scope as `scope.scope_id`, the agent destination `source:clinicaltrials.gov` and action `search_source`, and the Reviewer actions `decide_report`, `authorise_task`, `create_memory`, `correct_memory`, `revoke_memory`, `generate_briefing` and `generate_avatar_video` with the destinations `tts:elevenlabs` and `video:heygen`) are written by hand during the event in `gate/seed_data/`; `generate_briefing` and `generate_avatar_video` are on `sam@v1` whether or not their flags are on (V29); there is no `file_report` kind (V24), and the three claim policies `claim_performed_or_results`, `claim_planned` and `claim_preclinical` are seeded with the other policies (Story 10.7)
**And** per-task grants `task-<hex>@v1` (the 16 hex characters of the `task_id`, AD-3) are inserted only by an approved, gated `authorise_task` decision (Story 10.8): principal `dxp-curator`, `startable_by` Sam, actions `search_source` and `file_related_evidence` only, the same research scope and `diagnostic_ids`, destinations `source:clinicaltrials.gov` and `ledger`, and `expires_at` one hour after approval; the validator rejects `scope.all` and any other action on a task grant
**And** only an authorised grant or policy change alters permissions: memories (Stories 10.5, 10.6) are never read into a grant or policy (V6).

### Story 9.3: Policy gate before every action

**Points:** 3 · **Time:** ~1.8 h (M, 6 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR33, FR34, AD-19 · **Core** · **Owner:** Luis
**PRs:** A06 `story/9.3-policy-gate` (Ledger with the policy gate before every write, including `ledger/apply.py`, and A23's claim checks inside it, Luis). Proved end to end in I1 (Story 10.7's integration). Cards in `development-plan.md`.
**Updated (14 Nov):** check 4 gains the claim-accuracy checks of Story 10.7 (A23 inside A06), and the gate covers the new action kinds.

As a reviewer auditing the agent,
I want every proposed action checked against the grant and the policy set before anything happens, and every check recorded,
So that the agent cannot change a record or act in another system outside its authority, and I can see why.

**Acceptance Criteria:**

**Given** a proposed action (a ledger write, a Slack alert or a Reviewer's resolution of a notification)
**When** `gate.evaluate(ctx, action)` runs
**Then** it runs five checks in this order, stopping at the first failure:
1. `grant_active`: the latest version of the run's grant is `active` and unexpired; if it differs from the version pinned at run start and is not active, this check fails
2. `team_scope`: the target Diagnostic, including one the action would create, is in the grant's `scope.diagnostic_ids`; for a pending update to the scope's evidence collection (V35) the target is the scope, which must be the grant's `scope.scope_id`; a proposed link of a mention that resolves to an out-of-scope Diagnostic, such as the record's "FoundationOne CDx" mention, fails here, and its blocked Decision cites the mention and the scope rule (V37)
3. `destination_action`: the destination and the action kind are in the grant; a `notify_slack` action to any destination other than `slack:#all-mango-db-hackathon` fails this check
4. `evidence_checks`: applies to `file_proposal` (per change, and for a report as a whole as the report-level `file_proposal`; there is no `file_report` kind, V24), `notify_slack` and, since 14 Nov, `file_related_evidence`, `generate_briefing` and `generate_avatar_video`, where every `requires` key of the run's policy set that applies to the action kind is met by the change's `check` (quote found, supported, confidence, Story 1.5); it records `n/a` for the seed's `apply_value` and for the Reviewer kinds `review_value` and `resolve_notification` (`decide_proposal` is superseded), and a Reviewer `edit` or `reject` must carry a reason instead (D16, D50); it also records `n/a` for `search_source` and the Reviewer kinds `decide_report`, `authorise_task`, `create_memory`, `correct_memory` and `revoke_memory`. Check 4 also runs the claim-accuracy checks of Story 10.7 (`claim_performed_or_results`, `claim_planned`, `claim_preclinical`), decided from the source's own fields and checked quotes; a failing claim is blocked before filing with one blocked Decision naming the failed claim policy (V7)
5. `run_authorised`: the action holds an admission for this run (one admission per action, `item_key = "<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"`, D22), and the run is not `stopped`; an admitted action may finish while the run is `stopping`; outside a run (a Reviewer decision or the seed) it records `n/a`
**And** every evaluation writes one `decisions` document: `decision_id`, `run_id`, the agent and `initiated_by` (`agent: null` and the Reviewer for Reviewer decisions; `"seed"` and `"seed"` for the seed, D19), the action kind and inputs, the evidence reference (source item, quote, checks), the destination, every check with its result and detail, the grant actually evaluated (`grant_id@version`), the `policy_set_version`, the outcome (`allowed` or `blocked`), `authorised_by` (principal, initiated by, acting for, granted by, the grant and version evaluated, expiry and policy-set version), timestamps, and `seq`, which is the `seq` of its `action_allowed` or `action_blocked` event (D21)
**And** decision and action IDs derive from `(run_id or "-", kind, diagnostic_id, proposal_id or value_id or "<field>|<value>")`, with the `action_id` as the target for `resolve_notification` (D49), and Reviewer decisions add a server-generated `request_id`, so IDs never collide and a blocked Reviewer decision can be retried as a new Decision (D20)
**And** allowed: the gate creates an action that points back to its `decision_id` (`status: queued`) and emits `action_allowed`; in `live` mode an allowed change to an existing Diagnostic is filed as a `pending` proposal and is never applied directly
**And** blocked: no action, no business-record change and no external call; the only writes are the blocked decision, with the policy-set and grant versions and the failed check, and one `action_blocked` event carrying its `decision_id`
**And** authority: the principal and grant used by the gate are resolved server-side from the API key; a client-supplied name never confers permission
**And** `ledger.file`, `ledger.review_value`, the report decision (Story 10.8) and `actions.dispatch` call `gate.evaluate` first, so no code path writes a Record or posts to Slack without a decision
**And** tests prove each of the five checks blocks on its own and leaves the Records untouched and Slack uncalled
**And** the gate is evaluated once per change: A10 calls `ledger.file` once for each admitted change, and each filed report gets one `notify_slack` action, so there is one Slack alert per report, not per proposal (V11, replaces D46's per-proposal alert)
**And** (I1) step 1 (13:30 to 13:50) runs the grant, policy and scope seed, the FDA seed and the prior collection on the sandbox (D38); the post-setup snapshot is taken with A13's procedure only after step 2 has created M1 (D41, V15)
**And** (I1) asserts that the anchor's "FoundationOne CDx" mention resolves by exact name to the seeded FoundationOne CDx as a name present in the record (never as proof of use), and that the "FoundationOne Liquid" mention resolves to nothing and appears in the report's uncertainties with the V37 intervention-ambiguity sentence (V34, V37)
**And** (I1) the loop is proved on the sandbox without A14, asserting at least (D46, V11): the NCT04712877 report filed as `pending` with its one pending update adding the trial to the scope's evidence collection (V35), and the report's one real Slack alert delivered to `#all-mango-db-hackathon` (HTTP 200 `ok` recorded on the action) and its "Review in DxP" link resolving on the deployed web app; the proposed link of the record's "FoundationOne CDx" mention to the plasma scope blocked before execution (`team_scope`, with no Slack message); and `GET /runs/<run_id>/audit` reconstructing them; other reports and alerts from the run may also appear; screens poll (A12 is cut).

### Story 9.4: External action: a Slack alert for diagnostic evidence

**Points:** 5 · **Time:** ~2.1 h (M, 7 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR35, FR36, FR37, AD-20, NFR14 · **Core** · **Owner:** Luis
**PRs:** A09 `story/9.4-slack-notify` (Slack notifier: action ID saved first, atomic claim, Block Kit alert with links back to DxP, observed outcome, `unknown` never retried, manual resolution, Luis); I1 `integration/i1-discovery-loop` (Integration: setup and the discovery loop on the sandbox, Luis). Cards in `development-plan.md`.
**Updated (14 Nov):** one alert per report, not per proposal (V11, replaces D46's per-proposal alert); "Review in DxP" links to `${DXP_BASE_URL}/reports/<report_id>`. The criteria below are amended accordingly; where they still say proposal, read report.

As a reviewer,
I want an allowed proposal to send one Slack alert for its diagnostic evidence, exactly once, with links back to DxP, and an honest record of what happened even when the network fails,
So that the team is told about new evidence in the channel it already watches, while approval stays in DxP and nothing is ever sent twice.

**Acceptance Criteria:**

**Given** an allowed action of kind `notify_slack` for a `pending` report (one per report, V11), created by the gate with its `decision_id`, with destination `slack:#all-mango-db-hackathon` (S1, S2)
**And** `SLACK_WEBHOOK_URL` read from the environment, set only in `.env` and in the Modal secret, and `DXP_BASE_URL` set to the production web address (S3)
**When** `actions.dispatch(action, ctx)` runs
**Then** the sender refuses to start, and the action stays `queued`, if `DXP_BASE_URL` or `SLACK_WEBHOOK_URL` is not set; it never posts a link built from an empty base URL
**And** the action ID (`derive("act_", run_id, kind, diagnostic_id, report_id)`, the target being the `report_id`, D20, V11) is saved in `actions` before anything is sent; Story 9.4 never writes to `proposals`, because a proposal's `notification { action_id, status, posted_at }` is built at read time from this action (A14, A11, D47)
**And** the action has the AD-14 shape exactly (D44): `result { http_status, response_body, posted_at, link_urls { report_url, diagnostic_url } }` and, once resolved by a Reviewer, `resolution { outcome, note, decision_id, by, at }`
**And** concurrent retries: the action is claimed atomically in Atlas with one conditional update from `queued` to `dispatching`, recording `claimed_at`; only the worker whose update succeeds posts to Slack, so two workers retrying the same action at once produce one post (S7)
**And** the message is a Block Kit alert (S5) whose body is the report headline, the relationship summary and "Approve or reject in DxP" (V11), with: a header "New research report for review" and the action ID; the report headline in the V33 framing (a new trial signal; never a claim that the trial studies a named assay or shows performance); the evidence, as the trial NCT ID with its ClinicalTrials.gov link and the quote of at most 300 characters; the proposed update, for example "Add trial NCT04712877 to the scope's evidence collection" (V35); who acted, as the agent, the `run_id`, the grant as `{grant_id}@v{version}` and the policy set `ps_…`; and a context line "Approve or reject in DxP. Slack only notifies."
**And** the alert carries two links built from `DXP_BASE_URL` (S6): "Review in DxP" to `${DXP_BASE_URL}/reports/<report_id>` (the report page, Story 10.10, B04) and, only when the report names an in-scope Diagnostic that resolved by exact name, "Open diagnostic" to `${DXP_BASE_URL}/diagnostics/<dx_id>` (the "Accepted knowledge" view, Story 1.3, B04; on the demo path the report changes no assay record, so the link is left out and `link_urls.diagnostic_url` is null, V35); a test checks that every link sent resolves on the deployed web app, "Review in DxP" opening the report and an unknown ID showing "Report not found"
**And** notify only (S4): the message has links and no interactive elements, no approve or reject buttons and no Slack actions; Slack sends nothing back to DxP, and DxP exposes no Slack callback route
**And** the outcome is recorded exactly as observed, because a webhook post cannot be looked up afterwards (S7):
1. HTTP 200 with body `ok`: `delivered`, with `result.posted_at`, `result.http_status`, `result.response_body` and `result.link_urls`;
2. HTTP 4xx other than 429 (for example `invalid_payload`, `no_service`, `channel_not_found`): `failed` with the status and body, never retried;
3. HTTP 429: nothing was posted; the worker retries once after `Retry-After` while still holding the claim, and a second 429 means `failed`;
4. timeout, connection error or HTTP 5xx: the outcome is ambiguous, so the action is marked `unknown` and is never retried automatically
**And** every status update is conditional on the current status (`dispatching` to `delivered`, `failed` or `unknown`), so a slow worker never overwrites a later state (D24); each change emits `action_status_changed` and writes nothing to the proposal (D47)
**And** `actions.mark_unknown(action_id, "abandoned_in_flight")` marks an action left `dispatching` by an abandoned admission `unknown`, never re-sent, and `actions.mark_failed(action_id, "abandoned_before_send")` marks one still `queued` `failed`; both are conditional updates called by the sweep's background task (Story 9.5, D43)
**And** manual resolution (S8): `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }` lets a Reviewer settle an `unknown` notification after checking `#all-mango-db-hackathon` for the action ID; it passes `gate.evaluate()` as kind `resolve_notification` under `sam@v1` (Story 9.2), is recorded as a Decision whose ID target is the `action_id` (D49), with the Reviewer's stamp, `run_id: null`, a `request_id` and `cause { action_id, origin_run_id }`, moves the action from `unknown` with a conditional update that writes `resolution { outcome, note, decision_id, by, at }` (D44), never posts to Slack, and returns 409 for an action that is not `unknown`
**And** the audit record of each notification action (S9) keeps its Decision (the agent, `initiated_by`, the grant evaluated, the policy set and every check), its inputs and evidence reference, the destination, the timestamps queued, claimed, posted and observed, and the `result { http_status, response_body, posted_at, link_urls { report_url, diagnostic_url } }` (D44)
**And** the webhook URL never appears in a log, a response, a trace, an event, an action, a decision, the screen or the repository; `.env.example` names `SLACK_WEBHOOK_URL` with no value
**And** A09 is never stubbed: if the webhook or `DXP_BASE_URL` is missing, it is fixed before anything else (D37)
**And** (I1) the alert for the NCT04712877 report is one real Slack alert delivered to `#all-mango-db-hackathon` (one alert per report, V11), recorded `delivered`, whose "Review in DxP" link opens `/reports/<report_id>` on the deployed web app; the blocked action sends no Slack message.

### Story 9.5: Stop control

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR38, AD-21 · **Core** · **Owner:** Luis
**PRs:** A07+A11 bundle `story/9.5-runs-stop` (Runs: identity, admissions, stop, with the audit API, Luis). Cards in `development-plan.md`.

As the person who started the run,
I want to stop it at any moment and see exactly what is still finishing,
So that I stay in control of the agent without losing track of actions already under way.

**Acceptance Criteria:**

**Given** a collection `admissions`, unique on `(run_id, item_key)`, each with `status` (`admitted`, `released` or `abandoned`) and a 10-minute lease `expires_at`; one admission per action, `item_key = "<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"`, taken after extraction and before the gate (D22)
**And** the public API is `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle` and `runs.finish`, implemented in `runs/admissions.py`
**When** `runs.admit(run_id, item_key)` is called
**Then** it inserts an admission only if the run is `running`: the conditional check on the run and the insert happen in one transaction, or the run's `admitting` counter guards them, so a stop and an admission cannot race; it returns the `admission_id`, or nothing when refused
**And** `runs.release(admission_id)` changes `admitted` to `released` with a conditional update, so a second release does nothing, then calls `runs.settle(run_id)`
**And** sweep layering (D43): `runs` imports nothing from `actions`; `runs.sweep(run_id)` marks admissions past their lease `abandoned` and returns the actions they held
**And** the background task in `routes_runs.py` then calls `actions.mark_unknown(action_id, "abandoned_in_flight")` for each `dispatching` action (its post may or may not have reached Slack; never re-sent and never retried, for a Reviewer to resolve in DxP, Story 9.4, S8) and `actions.mark_failed(action_id, "abandoned_before_send")` for each `queued` action (never sent, so safe), and finally calls `runs.settle(run_id)` (D24, D43); these names are used everywhere, and the name `mark_abandoned` is retired
**And** `GET /runs/<run_id>` never calls Slack: it starts the sweep's background task and returns current state; `reconciling` exists only at read time, for an action the sweep is about to settle (D24, S7)
**When** I `POST /runs/<run_id>/stop`
**Then** stop semantics: a conditional update moves the run from `running` to `stopping`; after the stop, nothing new is admitted; admitted actions may finish and show as in flight; the run shows `stopping` until no `admitted` admissions remain, then `stopped`; the stop request starts the sweep's background task and does not call Slack itself
**And** `runs.settle(run_id)` only moves a run from `stopping` to `stopped`, with a conditional update, when no `admitted` admission remains; it never ends a `running` run (D23)
**And** `runs.finish(run_id)`, called by the pipeline after the last item, moves the run from `running` to `done` once no `admitted` admission remains; a run becomes `failed` only when the pipeline raises an error it cannot recover from (D23)
**And** stopping a run that is already `stopping`, `stopped`, `done` or `failed` changes nothing and returns its current state
**And** each status change emits `run_status_changed` stamped with the `run_id`
**And** a concurrency test fires a stop and many admissions together and never admits after the stop
**And** A07 is never stubbed (D37). Reversal of a run (FR46) is not part of this story; it is a separate stretch item (D37).

### Story 9.6: Audit reconstruction

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR39, AD-22 · **Core** · **Owner:** Luis
**PRs:** A07+A11 bundle `story/9.5-runs-stop` (Audit API, decision detail and "who authorised", bundled with the runs and stop under the proposal's section 7, Luis). Cards in `development-plan.md`.
**Updated (14 Nov):** audit additions V14, in the last criteria below; the demo question becomes "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" (V16).

As a reviewer auditing the agent,
I want to replay a run decision by decision from stored data alone,
So that I can answer "Who filed trial NCT04712877 into the scope's evidence collection, and under what authority?" without opening a log.

**Acceptance Criteria:**

**Given** a run with allowed, blocked and `unknown` entries, and a Reviewer decision on one of its proposals
**When** I call `GET /api/v1/runs/<run_id>/audit`
**Then** it returns the run (with `agent`, `initiated_by` and the pinned grant version), its policy set rebuilt from `policy_sets`, and every decision of the run in `seq` order (D21), allowed and blocked, each allowed one with its action
**And** audit reconstruction: each entry keeps its inputs, evidence reference, grant version, policy-set version, decision, destination, timestamps (proposed, decided, queued, claimed, posted, observed) and, for a notification, its result (S9): the status (`delivered`, `failed` or `unknown`) and the action's `result { http_status, response_body, posted_at, link_urls { report_url, diagnostic_url } }` and, when resolved, `resolution { outcome, note, decision_id, by, at }`, exactly as AD-14 (D44), never the webhook URL
**And** each entry with a proposal also shows that proposal's live DxP review status (`pending`, `applied` or `rejected`, with who decided and when), and each report entry its `report_review`, read at request time (S9); any proposal `notification` A11 returns is built at read time from its report's `notify_slack` action (D47, V11)
**And** a Reviewer's `resolve_notification` decision on an `unknown` action appears under "After the run" with the Reviewer, the outcome, the note and the time
**And** after them, a section "After the run" lists the Reviewer decisions whose `cause.origin_run_id` is this run, with the Reviewer, the outcome, the reason and the time
**And** `GET /decisions/<decision_id>` returns the audit detail of any entry, allowed or blocked: the agent, `initiated_by`, the action and inputs, the evidence quote and source, every check with its result, the grant evaluated read at its recorded version, the policy-set version with its members, the outcome, the action it created, if any, and `authorised_by` (principal, initiated by, acting for, granted by, the grant and version evaluated, expiry, policy-set version)
**And** "who authorised" is always read from the Decision's `authorised_by`, never from `GET /actions/<action_id>` (D40)
**And** `GET /actions/<action_id>` stays for action status and results, and `GET /actions?run_id=&status=` lists them
**And** a blocked entry shows its failed check; an `unknown` action is listed, never hidden
**And** grants and policies are read at the versions recorded, so a later version never changes an earlier answer
**And** the response carries quotes only, never a Source item's `raw_text`
**And** from the audit alone a reviewer answers the demo question: the agent and `initiated_by`, the grant and its version and scope, the policy-set version, the evidence quote, the Slack alert's result, the proposal's live DxP review status, and Sam's approval under "After the run"
**And** audit additions (V14): the run audit also returns the sources fetched with the scan cursor used and the cursor after (Story 10.1); the retrieval, with its method (`vector_search` or `text_search`), top-k and scores (Story 10.2); the memories used, each with author, source and its before-and-after effect (Story 10.6); the relationship labels with both quotes (Story 10.3); and the report and task decisions (`decide_report`, `authorise_task`, `create_memory`, `correct_memory`, `revoke_memory`), with the follow-up task's run linked by `task_id` (Stories 10.8, 10.9)
**And** blocked claim-accuracy decisions show the failed claim policy (Story 10.7)
**And** the task authorisation entry and any task-run entries say that the task's findings are pending related evidence, not accepted knowledge: approval accepted the report's own update only (V27)
**And** from the audit alone a reviewer answers "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"

### Story 9.7: Run console

**Points:** 3 · **Time:** ~3 h (M, 6 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR40 · **Core** · **Owner:** Vlad
**PRs:** B02 `story/9.7-run-console` (Run console for discover and task runs, Vlad; also carries the console parts of Stories 10.1 and 10.9). Cards in `development-plan.md`.

As the person who starts the agent,
I want one screen showing who the agent is, what it may do, what it is doing and a stop button,
So that I can watch the agent work and stop it.

**Acceptance Criteria:**

**Given** the Run console in the minimal shell (Story 1.12)
**When** I start a discovery scan (`set: "discover"`) by choosing a grant from a picker that lists the grants I may start (from `GET /grants`), each labelled with its Team; there is no separate Team picker (D18)
**Then** the request `POST /runs { grant_id, set }` goes through server-side Next.js code that adds `X-DxP-Key`, which never reaches the browser
**And** a 403 (not allowed to start under this grant) and a 409 (a run is already running, with a link to it) are shown as messages
**And** an identity card shows the agent, `initiated_by`, model, prompt version, the policy set as `ps_ab12… (N policies)`, the grant as `{grant_id}@v{version}`, and the grant's Team scope; run and action IDs show in their stored `run_` and `act_` forms (D40)
**And** a list of the run's decisions shows each as allowed (with its action in flight, done, or, for the Slack alert, "Slack alert delivered" with the time, Failed or Unknown) or blocked (with the failed check named); each Diagnostic links to its Accepted knowledge view, each filed report links to its report page, and a task's run is labelled "Follow-up task" with a link back to its report (the impact view is cut)
**And** an `unknown` Slack alert shows a Resolve control, calling `POST /actions/<action_id>/resolve { outcome, note }` through the server-side key, only when the `actions` from `GET /whoami` include `resolve_notification` (D53)
**And** a stop button calls `POST /runs/<run_id>/stop`; the status shows `stopping` with the number of admitted actions still finishing, then `stopped`
**And** the console polls `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` every 2 seconds; the live feed (Story 9.9, A12) is cut (D40)
**And** buttons are reachable by keyboard and labelled.

### Story 9.8: Audit view

**Points:** 2 · **Time:** ~2 h (S, 4 h developer estimate × 0.5, screen) · **Lane:** [WEB] · **Covers:** FR41 · **Core** · **Owner:** Vlad
**PRs:** B03 `story/9.8-audit-view` (Audit view, Vlad). Cards in `development-plan.md`.
**Updated (14 Nov):** shows the V14 audit additions and answers the V16 audit question, in the last criteria below.

As a reviewer auditing the agent,
I want one run reconstructed on screen, decision by decision,
So that I can answer "who authorised this" for any entry in front of the judges.

**Acceptance Criteria:**

**Given** `GET /runs/<run_id>/audit` and `GET /decisions/<decision_id>` (Story 9.6)
**When** I open the Audit view for a run
**Then** each entry shows in order with its outcome, inputs, Evidence quote and source, the grant as `{grant_id}@v{version}`, the policy set as `ps_ab12… (N policies)`, the timestamps and, for a notification, its result ("Slack alert delivered" with the time, Failed or Unknown, with the HTTP status, Slack's response and the link URLs sent), plus the proposal's live DxP review status (pending, applied or rejected, with who decided and when); each Diagnostic links to its Accepted knowledge view
**And** selecting an entry loads its decision detail and shows "who authorised this" from the Decision's `authorised_by` (D40): the agent, `initiated_by`, the grant and its version and scope, the policy set and every check
**And** the view polls `GET /runs/<run_id>/audit` while the run is running (A12 and the impact view are cut)
**And** blocked entries show the failed check, and `unknown` notifications are marked "Unknown: check #all-mango-db-hackathon for the action ID" with a Resolve control that calls `POST /actions/<action_id>/resolve { outcome, note }` through the server-side key (Story 9.4); the control is shown only when the `actions` in `GET /whoami`'s `Principal { id, name, kind, actions }` include `resolve_notification` (D53); there is no reconcile button
**And** a section "After the run" shows the Reviewer decisions on the run's proposals, such as Sam's approval
**And** the earlier demo question, "Who filed trial NCT04712877 into the scope's evidence collection, and under what authority?", is answered on this screen without leaving it (V35)
**And** the screen renders only what the API returns, applying no rule of its own
**And** audit additions (V14): it shows the sources fetched with the scan cursor; the retrieval method, top-k and scores, with "related by text search" when that fallback ran; the memories used with author, source and effect; the relationship labels with both quotes; the blocked claim with its failed claim policy; and the report and task decisions with a link to the follow-up task's run
**And** under "After the run" the approval reads "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review.", and every item the task filed shows "Pending review", never "Accepted" (V27)
**And** the question "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" is answered on this screen without leaving it.

### Story 9.9: Live action feed through change streams

**Points:** 2 · **Time:** ~1.5 h (S, 3 h developer estimate × 0.5, new infra) · **Lane:** [API] · **Covers:** FR42, AD-10, AD-23 · **Cut (14 Nov)** · **Owner:** Luis
**PRs:** none — cut (A12 removed under the proposal's section 7, cut 3). Screens poll (D40); change streams are no longer needed (OD5).

As the person who starts the agent,
I want decisions and actions to appear on the console as they happen,
So that I see the agent work in real time.

**Acceptance Criteria:**

**Given** the run's events in Atlas, each with an integer `seq` and the stamp
**When** the Run console calls `GET /changes?after=<seq>&run_id=`
**Then** it returns the events after `seq` for that run and the `last_seq`; the query on `seq` is the only source of truth
**And** `action_allowed` and `action_blocked` events carry their `decision_id`, and run and action status changes are events, so the feed shows allowed, blocked, in flight and `unknown` without reading `actions`
**And** with `DXP_FEED=change_stream` the request waits up to 25 seconds and is woken by an Atlas change stream on `events`, so new entries appear within a few seconds
**And** if change streams are not available on the Atlas Sandbox tier (checked in A04), `DXP_FEED=poll` returns at once and the console polls the same route every 2 seconds, with the same response shape
**And** a dropped connection resumes from the last `seq` without missing or repeating an entry
**And** it never blocks a core PR, and A12 may be cut (D37); until it has passed its check, the console, the Audit view and the Review count poll (Stories 9.7, 9.8, 1.12).

### Story 9.10: Spoken audit briefing

**Points:** 2 · **Time:** ~1.6 h (S, 4 h developer estimate × 0.4, model work and screen) · **Lane:** [API] and [WEB] · **Covers:** FR44 · **Superseded (14 Nov)** by Story 10.11 · **Owner:** Vlad
**PRs:** none — superseded. B06 now builds Story 10.11, the ten-second report briefing (`story/10.11-briefing`).

As a reviewer,
I want to hear a short audit summary of a run,
So that I can catch up on what the agent did without reading the log (and the team can enter the ElevenLabs prize).

**Acceptance Criteria:**

**Given** `GET /api/v1/runs/<run_id>/audit/audio`
**When** it is called
**Then** ElevenLabs text to speech reads a short summary built only from the run's audit response (decisions allowed and blocked, actions `unknown`, Slack alerts delivered, the agent and `initiated_by`, and Reviewer decisions after the run), with ctDNA, MRD, EGFR and NSCLC pronounced correctly
**And** the audio is generated once per run state and cached
**And** if ElevenLabs fails, the route returns the error shape with 503 and the Audit view still works
**And** the Audit view has a "Listen" link to B06's briefing page for the run, which plays the audio with a loading state and an error message; the link shows only when the stretch flag is on
**And** it may be built from 13:00 behind a flag, never blocks a core PR, and merges only after the allowed-and-blocked loop is green at 14:30; it replaces Stories 3.4 and 3.5.

### Story 9.11: Rejection drafts a policy for explicit approval

**Points:** 3 · **Time:** ~2 h (M, 5 h developer estimate × 0.4, model work) · **Lane:** [API] and [WEB] · **Covers:** FR45, NFR15 · **Cut (14 Nov)** · **Owner:** Luis
**PRs:** none — cut (A17 removed under the proposal's section 7, cut 3). Policies stay hand-written (NFR15); reviewer corrections become memories (Stories 10.5, 10.6), which never change permissions.

As a Reviewer,
I want my rejection reason turned into a draft policy that I approve before it takes effect,
So that a correction tightens the agent's authority without model prose ever becoming authority by itself.

**Acceptance Criteria:**

**Given** Sam rejects a proposed change with a reason (Story 2.3)
**When** the decision is saved
**Then** the model drafts a new policy version as structured data limited to what a policy supports (`applies_to` and a `requires` object with only `quote_found`, `supported` and `min_confidence`), returned as `rule_draft` with `status: draft`
**And** a draft that needs a check the gate does not support is refused with a message, not stored as a policy
**And** the draft takes effect only after explicit approval by a person principal through `POST /policies/<policy_id>/approve { version }`, which inserts a new `active` version; the next run pins a new policy set, written to `policy_sets` on first use, and its decisions cite it; a run already under way keeps its pinned set
**And** model text is never executed as authority: the gate reads only the structured policy fields
**And** if drafting fails, the decision is still saved and `rule_draft` is null
**And** built only if the loop is green by 14:30; it replaces deferred Stories 2.6 and 2.7.

## Epic 10: Proactive discovery and research memory

Added by the discovery-agent proposal of 14 November (`sprint-change-proposal-2026-11-14-discovery-agent.md`, decisions V1 to V24; it wins over every earlier file; the architecture spine wins on routes, shapes, action kinds, modules and statuses, and `development-plan.md` on PR IDs, branches, owners and times). DxP is a proactive diagnostic-evidence research agent for Statement 1, "Agents You Can Audit": within one research scope it discovers newly updated ClinicalTrials.gov trials, relates them to the evidence it already holds through Atlas Vector Search, retrieves the reviewer corrections it remembers, checks every claim and action against explicit policies, files one pending research report, alerts Slack once per report, and, when Sam approves, promotes the report's update into accepted knowledge and authorises one small follow-up task that answers the report's evidence gap, which starts automatically under its own grant and gate when Story 10.9 (stretch) is in and `task_run` is on (V26, V38, V39). Section 12 (V38 to V44) wins over V1 to V37. Sections 10 and 11 of the proposal (V25 to V36) win over V1 to V24, and V33 to V36 over V25 to V27: the demo signal is the V33 framing, only exact FDA trade names resolve (V34), the allowed update adds the trial to the scope's evidence collection and the guaranteed block is the proposed link of the record's "FoundationOne CDx" mention to the plasma scope (V35, V37), names in the record are mentions, never proof of use (V37), and the anchor is verified live at 10:45 (V36). Epic 9's identity, grants, gate, decisions, stop and audit carry this loop; they are no longer the whole product. Memories inform the agent's reasoning only and never change permissions. DxP supports research review and gives no medical advice. The PRD numbers the new requirements FR47 to FR58 (PRD §4.11). Open dependencies OD1 to OD7 are in the build risks above. The PR IDs are the bundles of the proposal's section 7 (A19 with A20, A21 with A22, A23 inside A06), except that A24 (Story 10.8) and A25 (Story 10.9) are split again (V28).

### Story 10.1: Discovery scan of ClinicalTrials.gov within one research scope

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR47 (discovery scan within a Research scope), FR1 on demand, FR31, FR33, V1, V2 · **Core** · **Owner:** Luis
**PRs:** A05 `story/10.1-discovery-scan` (Prior collection by NCT ID in baseline mode, the research scope and `discovery.scan(scope_id, ctx)`, Luis; also carries Story 1.4); B02 `story/9.7-run-console` (starting a discover run and showing the scan cursor, Vlad); I1 `integration/i1-discovery-loop` (setup and the discovery loop on the sandbox, Luis). Cards in `development-plan.md`.

As a Director of Diagnostics,
I want DxP to search ClinicalTrials.gov on demand for trials in my team's research scope updated since its last scan,
So that new evidence is found by the agent instead of by someone remembering to look.

**Acceptance Criteria:**

**Given** a `research_scopes` document, written by hand during the event in A03's `gate/seed_data/` and loaded by `python -m dxp.gate.seed`, in the AD-14 `Scope` shape: `{ _id: "scope_plasma_ctdna_nsclc", name: "Plasma ctDNA genotyping assays in NSCLC" (all stages, V25), team_id, assays: [the four exact trade-name strings of D45], aliases (search terms only, for example "ctDNA", "cell-free DNA" and "liquid biopsy"; never used to resolve a name to a Diagnostic, V34), condition: "non-small cell lung cancer", source: "clinicaltrials.gov", cursor: { last_update_post_date, set_at, set_by_run_id } }`, owned by "Team Liquid Biopsy Dx" and named by the agent grant `lbdx@v1` as `scope.scope_id` (V1, Story 9.2)
**And** the prior collection: the D30 trials last updated before the cursor, excluding NCT05715229, fetched by NCT ID and loaded in `baseline` mode during setup by `python -m dxp.pipeline.prior` (Story 1.4, I1 step 1); nothing is read from `data/` (D1)
**When** a discovery run starts (`POST /runs { grant_id: "lbdx", set: "discover" }`, Story 9.1) and its first step calls `discovery.scan(scope_id, ctx)` (`discovery/scan.py`, with the ClinicalTrials.gov client in `sources/ctgov.py`)
**Then** the scan is admitted and passes `gate.evaluate()` as action kind `search_source` with destination `source:clinicaltrials.gov` before any request is made; a blocked scan makes no request and records one blocked Decision
**And** it queries the ClinicalTrials.gov API v2 with `query.term` = the scope's assay names and search terms, `query.cond` = non-small cell lung cancer and `filter.advanced` = `AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]` (V2)
**And** each result is upserted as a Source item `clinicaltrials.gov:<NCT ID>` with `window: "discovered"`, `scope_ids`, `raw_text` and `evidence_text` from the record's text fields, `source_date` from `last_update_posted`, `overall_status` and `has_results` kept as fields for the claim checks (Story 10.7)
**And** (V40, AD-25) each result is also written as an immutable `source_versions` document, insert-if-absent on `derive("sv_", source_ref, last_update_post_date, content_hash)`, and `source_items.current_version_id` moves to it by a conditional update on the previous pointer; when a known trial has changed (a new `lastUpdatePostDate` or content hash), the scan stores the new version, moves the pointer and treats the change as a signal (the item is processed again for that version), and never overwrites or deletes an older version
**And** every record that uses source content carries the exact `version_id` it used (report quotes, retrieval results, `report.related[]`, Findings, proposals, Decisions, audit entries); advancing `current_version_id` never changes evidence that was already reviewed or accepted (I1 and I3 assert this)
**And** the cursor lives on the scope and advances, by a conditional update on the scope's current `cursor.last_update_post_date` (AD-25), only after the scan finishes; a failed or stopped scan leaves it where it was, so nothing is skipped
**And** the run audit records the sources fetched, with the cursor used and the cursor after (V14, Story 9.6)
**And** each discovered item is then processed by the same run, one admission per action (D22), in `DXP_DEMO_PACE` order when that is set
**And** (I1) at 10:45 the live API is queried for the scan (OD2, V36): the demo anchor is whichever in-scope early-stage trial is actually updated after the chosen cursor, with its update date, status and results verified in the response. NCT04712877 is the expected candidate (on 14 Nov the API returned `lastUpdatePostDate` 2026-11-12, RECRUITING, `hasResults` false; the record-history page showed a different latest update, so the date stays unverified until 10:45); if it is not updated after the cursor, the scan's real result is used, framed as V33, with no claim about which assay it studies, and the claim policy applies the same way
**And** Tavily, PubMed and scheduled scans stay deferred (Stories 1.10, 1.11; V18)
**And** no code is copied from `scripts/data/` or from any `dxp-*` skill.

### Story 10.2: Embeddings and Vector Search retrieval of related evidence

**Points:** 2 · **Time:** ~1.5 h (S, 3 h developer estimate × 0.5, new infrastructure: index and embeddings) · **Lane:** [API] · **Covers:** FR48 (embeddings and related-evidence retrieval), V3, AD-15 restored · **Core** · **Owner:** Luis
**PRs:** A19+A20 bundle `story/10.2-retrieval-report` (Embeddings, the vector index and retrieval feeding the relationships and the report, Luis; one PR with Stories 10.3 and 10.4). Cards in `development-plan.md`.

As the agent,
I want each new trial matched to the most related evidence and findings already in my scope,
So that a discovery is connected to what the team already knows, not reported in isolation.

**Acceptance Criteria:**

**Given** Source items and Findings in the scope, the prior collection loaded in setup
**When** a Source item or Finding is written
**Then** its evidence text (for a Source item) or summary (for a Finding) gets an embedding: through Atlas Automated Embedding if the sandbox supports it, otherwise through the Voyage AI embeddings API called directly if a key is cleared (OD1); the choice is a config value recorded on the run
**And** `retrieval.ensure_indexes()` (`retrieval/indexes.py`, run in I1 step 1 after the prior collection loads) creates the Vector Search indexes `vs_source_items`, `vs_findings` and `vs_memories`, with filter fields `scope_ids`, `team_id`, `status`, `tags.assay` and `tags.claim_kind`, and the text-search fallback indexes; setup waits until they are queryable (about 10 minutes, I1); the embedding path is chosen by `DXP_EMBEDDING` (`auto`, `voyage` through `retrieval/embed.py`, or `none`)
**And** `retrieval.related(scope_id, text, k, exclude)` (`retrieval/related.py`) runs `$vectorSearch` filtered to the same scope and returns a `Retrieval { method, index, top_k, filter, items[{ ref, version_id, score }] }` (each source item pinned to the version retrieved, V40) of the top-k related Source items and Findings, excluding the item itself
**And** if neither embedding path works on the day, related retrieval falls back to Atlas Search text search; the result carries `method: "text_search"`, and the report and every screen say "related by text search", never "Vector Search" (V3)
**And** the run audit records the retrieval: method, top-k and the scores (V14)
**And** a similarity score is stored and shown but is never evidence: it never stands in for a quote, never sets a relationship label and is never quoted in a claim (Story 10.3)
**And** Story 4.1's synonym expansion stays deferred; only the vector retrieval is restored here.

### Story 10.3: Relationship classification with quotes from both sides

**Points:** 3 · **Time:** ~2 h (M, 5 h developer estimate × 0.4, model work) · **Lane:** [API] · **Covers:** FR49 (relationship classification), FR5, FR18, NFR1, V4, AD-6 · **Core** · **Owner:** Luis
**PRs:** A19+A20 bundle `story/10.2-retrieval-report` (with Stories 10.2 and 10.4, Luis). Cards in `development-plan.md`.

As a Director of Diagnostics,
I want the agent to say whether a new trial supports, contradicts or extends existing evidence, or raises a new question, and to show me the words on both sides,
So that I can check every connection instead of trusting a score.

**Acceptance Criteria:**

**Given** a discovered item and its related items from Story 10.2
**When** `reports.relate()` (`reports/relate.py`, A19+A20) runs for each related item, calling Claude only through `llm.call_structured` (structured output, no sampling parameters, AD-11)
**Then** it returns one label from `supports`, `contradicts`, `extends` or `new_question`, a one-sentence rationale, a quote from the new evidence and a quote from the related evidence, each at most 300 characters
**And** both quotes are checked word for word with `evidence.quote_in_source()` against the exact source version each names (`version_id`, AD-6, V40); the label stands only when both quotes are found
**And** an item without two checked quotes is kept and shown as "related (no relationship established)", with its similarity score and no label
**And** each relationship has the AD-14 `Relationship` shape `{ id (rel_), related_ref, related_kind, related_title, label: supports | contradicts | extends | new_question | related_unestablished, rationale, new_quote { source_ref, version_id, text, quote_found }, related_quote { source_ref, version_id, text, quote_found }, similarity, retrieval_method, origin: discovery | task:<task_id>, status: pending | accepted, filed_by_decision_id }`, embedded in its report's `related` (AD-26), with derived IDs (AD-3)
**And** the similarity score is stored and shown beside the label and never used as evidence: a test proves a high-similarity pair with one unchecked quote gets no label
**And** the run audit shows each relationship label with both quotes (V14)
**And** a model error or refusal yields "related (no relationship established)" and does not fail the item
**And** on the demo path the expected label between the anchor (early-stage profiling) and the prior collection's plasma ctDNA genotyping evidence in advanced NSCLC is `extends` (a new setting); it stands only with two checked quotes, and otherwise the item is shown as "related (no relationship established)"; no rationale says the trial studies a named assay or shows any assay's performance (V25, V33).

### Story 10.4: Research report filed as a pending proposal

**Points:** 3 · **Time:** ~1.5 h (M, 5 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR50 (research report as a pending proposal), FR15, NFR2, V5, D8 · **Core** · **Owner:** Luis
**PRs:** A19+A20 bundle `story/10.2-retrieval-report` (report assembly, with Stories 10.2 and 10.3, Luis); I1 `integration/i1-discovery-loop` (Luis). Cards in `development-plan.md`.

As a Reviewer,
I want each discovery delivered as one pending research report with its evidence, connections, uncertainties, the memories used, one evidence gap and one recommended next task that answers it,
So that I review a complete piece of research in one place, and nothing becomes accepted knowledge until I approve it.

**Acceptance Criteria:**

**Given** a discovered item with its Findings (Story 1.5), relationships (Story 10.3) and retrieved memories (Story 10.6)
**When** the report is assembled
**Then** `reports.draft()` (`reports/draft.py`) writes two drafts (V21): draft 1 without the retrieved memories and draft 2 with them, so each memory's before and after come from the two real drafts
**And** `reports.file()` (`reports/file.py`) gates each draft as the report-level `file_proposal` (targets `"<report_id>|draft1"` and `"<report_id>|draft2"`, each its own Decision); draft 2, if allowed, is written as a `reports` document with `status: pending` in the AD-14 `Report` shape: `{ id (report_id), run_id, scope_id, team_id, source_ref, version_id (V40), nct_id, headline, status_line, discovery { summary, quotes (each with version_id), trial_status, has_results }, related: Relationship[], uncertainties, gap, retrieval, memories_used: MemoryUse[], proposal_ids, diagnostic_ids, recommended_task { kind: search_related, params { condition, stage, testing, has_results, max: 5 } }, draft, blocked_draft_decision_id, stamp, file_decision_id, status, notification (read time), script, script_hash, briefing, avatar, created_at }`
**And** (V41) `reports.script_for(report)` (`reports/script.py`, A19+A20, core) builds the report's grounded text script from its own fields by a template (the signal, its status, the gap; no fact beyond the report, the mention wording of V37), and `reports.file()` stores it as `script` and `script_hash`; every filed report carries its script, whether or not the briefing (B06) or the avatar (B08) exists, and `GET /reports/<report_id>` returns it
**And** the headline frames the discovery as a new trial signal worth investigating; on the demo path: "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." No headline, summary or rationale says the trial studies a named assay it does not name exactly, or shows any assay's performance (V25, V33)
**And** the uncertainties name what the source does not settle, for example "recruiting; no results posted", and every extracted name that matched no seeded name exactly, in the V34 wording: "The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated."; on the demo path also "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample." (V37)
**And** the report keeps the record's intervention wording verbatim ("ctDNA, tumor NGS"; other names "FoundationOne CDx", "FoundationOne Liquid"), records each name as a mention, never as proof of use, and never merges FoundationOne CDx (tissue) with FoundationOne Liquid CDx (plasma cfDNA) (V37)
**And** every report names exactly one evidence gap in `gap` (V26); on the demo path: "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?" (V33)
**And** the recommended task answers exactly that gap: on the demo path, search ClinicalTrials.gov for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling, and report which of the records searched have posted results (at most 5), with `params { condition: "non-small cell lung cancer", stage: "early", testing: ["ctDNA or plasma", "tissue profiling"], has_results: true, max: 5 }` (V26, V33)
**And** every proposed knowledge update is filed through `ledger.file()` as a `pending` proposal (D8, D28) linked to the report; on the demo path it is the one update that adds NCT04712877 to the scope's evidence collection, as an early-stage plasma-plus-tissue profiling study, targeting the scope, not an assay record (V35): a proposal with `diagnostic_id: null` and `target { scope_id }`, so the report's `diagnostic_ids` is empty and nothing downstream assumes a `dx_id` (V43); the proposed link of the record's "FoundationOne CDx" mention to the plasma scope is blocked by check 2 and never filed (V37); the report never writes accepted knowledge
**And** filing the report passes `gate.evaluate()` as the report-level `file_proposal` (there is no `file_report` kind, V24), including the claim checks of check 4 (Story 10.7); a claim that fails is blocked before filing
**And** accepted knowledge (Diagnostics, accepted values, accepted findings) is kept apart from pending reports and proposals, and the read model labels each `pending` or `accepted`
**And** an allowed report gets exactly one `notify_slack` action, so there is one Slack alert per report, not per proposal (V11, replaces D46's per-proposal alert; Story 9.4)
**And** `GET /reports?status=pending` lists reports (headline, discovery, counts of related items and memories used, created time) and `GET /reports/<report_id>` returns one report, whatever its status, with its relationships, memories used and proposals inline, quotes only and never `raw_text`; an unknown ID returns 404 in the error shape
**And** `GET /reports` and `GET /reports/<report_id>` are served by `api/routes_reports.py` (A19+A20)
**And** (I1) the discovery run files the NCT04712877 report on the sandbox with M1's effect visible (Story 10.6).

### Story 10.5: Reviewer memory store with correct and revoke

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR51 (reviewer memory: creation), FR52 (correct or revoke a memory), NFR2, NFR15, V6 · **Core** · **Owner:** Luis
**PRs:** A21+A22 bundle `story/10.5-memory` (Memory store, correct and revoke, retrieval and its effect, Luis; one PR with Story 10.6); I1 `integration/i1-discovery-loop` (M1 created through the real UI in setup step 2, Luis). Cards in `development-plan.md`.

As a Reviewer,
I want my corrections kept as attributable team memories that I can correct or revoke,
So that the agent learns from me in the open, and I stay in control of what it remembers.

**Acceptance Criteria:**

**Given** the collection `memories` with `$jsonSchema` validation, one document per version (AD-28): `{ _id: "<memory_id>@v<version>", memory_id, version, team_id, author, source { decision_id, report_id }, text, tags { assay, claim_kind }, embedding, status: active | corrected | revoked, supersedes, decision_id, stamp, created_at }`, written only by `memory/store.py`
**When** Sam rejects a report, or approves it with a correction note (Story 10.8)
**Then** one memory is created through action kind `create_memory`, gated under Sam's grant `sam@v1`, with the Decision recorded and `author` the Reviewer principal resolved from the key; no name in the body is read; its `tags.assay` comes from the report and its `tags.claim_kind` (for example `outcome_claim_without_results`) is the Reviewer's choice, because retrieval matches on claim kind, not assay (V22)
**And** every memory is scoped to one Team: it is written with the grant's `team_id` and is never retrieved for another Team
**And** every memory is attributable: it links to its author, its source decision and its source report, and the Audit view can follow each link
**And** `POST /memories/<memory_id>/correct { text, note }` (kind `correct_memory`) writes a new version that `supersedes` the old one and marks the old one `corrected`; `POST /memories/<memory_id>/revoke { note }` (kind `revoke_memory`) marks it `revoked`; both are gated under `sam@v1`, recorded as Decisions with a `request_id`, conditional on the current status, and audited; a revoked or corrected version is never retrieved again
**And** `GET /memories?team_id=&status=` lists the Team's memories with author, source and status
**And** memories never alter permissions: no code path reads a memory into a grant, a policy or the gate; a test proves that creating, correcting or revoking a memory leaves `grants`, `policies` and `policy_sets` unchanged and every gate outcome the same
**And** memories are not Learned-rule enforcement (Stories 2.6, 2.7 stay deferred) and do not use the Agent Memory preview SDK (Epic 6 stays deferred)
**And** (I1, setup step 2) memory M1 is created during the event through the real UI: the setup run `POST /runs { grant_id: "lbdx", set: "nct:NCT05715229" }` files a report on NCT05715229 (TERMINATED, no posted results; not in the prior collection), and Sam rejects it with "Terminated trial with no posted results: describe its status; do not state outcomes", claim kind `outcome_claim_without_results`; it is never seeded from a file (V15, D1)
**And** `GET /memories?team_id=&status=`, `GET /memories/<memory_id>` and the correct and revoke routes are served by `api/routes_memories.py`; Correct and Revoke on screen sit behind the `memory_edit` flag (Story 10.10).

### Story 10.6: Memory retrieval and its visible effect in reports

**Points:** 3 · **Time:** ~2 h (M, 5 h developer estimate × 0.4, model work) · **Lane:** [API] · **Covers:** FR51 (reviewer memory: use and effect), V6 · **Core** · **Owner:** Luis
**PRs:** A21+A22 bundle `story/10.5-memory` (with Story 10.5, Luis); I1 `integration/i1-discovery-loop` (Luis). Cards in `development-plan.md`.

As a Reviewer,
I want the agent to use my earlier corrections on the next relevant discovery and show me exactly what each one changed,
So that I can see the learning and check that it was applied correctly.

**Acceptance Criteria:**

**Given** active memories for the Team
**When** a report is drafted (Story 10.4)
**Then** `memory.retrieve(team_id, text, tags)` (`memory/retrieve.py`) filters by `team_id`, `status: active` and `tags.claim_kind`, never by assay (the assay tag is recorded and shown, not required to match), then ranks by Vector Search similarity to the discovery through `retrieval.memories()` (or by text search with the honest label when OD1 fails, Story 10.2) (V22)
**And** M1, written on the setup trial NCT05715229, is therefore retrieved for the discovery of NCT04712877, whatever assay each names; a test proves a memory with the same `claim_kind` on another assay is retrieved
**And** each memory used is passed to draft 2 as reviewer guidance, never as an instruction that can change scope, grant or policy; draft 1 is written without memories, and both drafts are gated (V21, Story 10.4)
**And** the report lists each memory used with its author, its source decision and report, and its effect: the sentence or label it changed, with `before` taken from draft 1 and `after` from draft 2 (never written by the model); a memory retrieved but with no effect is listed as "retrieved, no change"
**And** on the demo path the NCT04712877 report retrieves M1 and shows "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet"
**And** the run audit lists the memories used with their effect (V14)
**And** a revoked or corrected memory version is never retrieved; a test proves revoking M1 removes its effect from the next report.

### Story 10.7: Claim-accuracy policies block unsupported claims before filing

**Points:** 2 · **Time:** ~1.6 h (S, 4 h developer estimate × 0.4, model work: claims and one redraft) · **Lane:** [API] · **Covers:** FR53 (claim-accuracy policies), FR33, FR34, NFR1, NFR13, V7 · **Core** · **Owner:** Luis
**PRs:** A06 `story/9.3-policy-gate` (claim checks in check 4 of the gate, `gate/claims.py`, with A23 folded in, Luis); I1 `integration/i1-discovery-loop` (Luis). Cards in `development-plan.md`.

As a reviewer auditing the agent,
I want every claim the agent writes checked against what the source actually reports, before it is filed,
So that the agent never says an assay was performed, produced results or is clinical when the source does not say so.

**Acceptance Criteria:**

**Given** hand-written, versioned claim policies in the policy set (NFR15, Story 9.2), each decided only from the source's own fields (`overall_status`, `has_results`) and checked quotes
**When** check 4 (`evidence_checks`) runs for the report-level `file_proposal` on each of the two drafts (there is no `file_report` kind, V24; for `notify_slack`, `generate_briefing` and `generate_avatar_video`, check 4 passes only when the report they derive from was filed allowed, Story 9.3)
**Then** `claim_performed_or_results`: a claim that an assay was performed or produced results needs `has_results: true`, or a checked quote saying the assay was performed with results
**And** `claim_planned`: a trial whose status is NOT_YET_RECRUITING or RECRUITING, or that is planned, must be described as planned or ongoing
**And** `claim_preclinical`: cell-line or animal evidence must be labelled preclinical
**And** a claim failing any of these is blocked before filing: no report, proposal or alert is written, and the only writes are one blocked Decision naming the failed claim policy and one `action_blocked` event (FR34)
**And** the agent may redraft once; the redraft is a new evaluation with its own Decision, and a second failure ends that item with nothing filed
**And** on the demo path, if draft 1 (written without memories) makes an unsupported performance or results claim (for example that NCT04712877 "showed" blood profiling detecting actionable drivers), it is blocked because the source is RECRUITING with `has_results: false`, one blocked Decision is recorded, and draft 2 ("is recruiting; no results posted", with M1) is allowed; the model may not write the claim, so the blocked claim is shown whenever it occurs and is not guaranteed (V21)
**And** the record mentions "FoundationOne CDx" as an other name of its generic intervention, so the agent's proposed link of that mention to the Team's plasma research scope is blocked by check 2 on every take, because the configured scope excludes the tissue assay; one blocked Decision cites the mention and the scope rule (V37); that unauthorised action is what guarantees must-show 3 (V21, V35)
**And** tests cover each claim policy blocking on its own and leaving Records, reports and Slack untouched.

### Story 10.8: Approval promotes the report and authorises one follow-up task

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR54 (approval promotes accepted knowledge and authorises one task), FR16, FR17, NFR2, V8, V27, V28 · **Core** (the task's authorisation only: core, but cheap, V28) · **Owner:** Luis
**PRs:** A24 `story/10.8-approve-task` (Report decision, promotion, task authorisation and `GET /tasks`, Luis; split from A25 again, V28); I3 `integration/i3-approve-task` (approval, promotion, authorisation and audit on the sandbox, 14:45 to 15:00, Luis). Cards in `development-plan.md`.

As a Reviewer,
I want one decision on a report to promote its updates and authorise its one recommended task,
So that accepting research is a single, attributable act and the agent's next step is explicitly mine to allow.

**Acceptance Criteria:**

**Given** a `pending` report
**When** Sam calls `POST /reports/<report_id>/decision { action: approve | reject, note, correction }` with the web app's server-side key (`api/routes_report_decision.py`, which calls `reports.decide()` in `reports/decide.py`, then `tasks.authorise()` and, when the backend flag `task_run` is on (`DXP_FEATURES`, V38), `tasks.dispatch_next()` in `tasks/dispatch.py`, then `memory.create()`)
**Then** the decision is gated as kind `decide_report` under `sam@v1`, recorded as a Decision with the Reviewer's stamp, `run_id: null`, a `request_id` and `cause { report_id, origin_run_id }`
**And** approve applies the report's pending proposals through `ledger.apply()` (A06), all or nothing, and marks the report `accepted`; on the demo path NCT04712877 is accepted into the scope's evidence collection and no assay record changes (V35)
**And** (V43) the demo update has `diagnostic_id: null`: check 2 judges its `scope_id`, and the apply guards on `source_items.collections.<scope_id>` (recording the reviewed `version_id`, V40) instead of `applied_proposal_ids`, writing no `diagnostics` document, value entry, alias or edge; the response and the audit show the scope as the target
**And** approve also passes a second gated evaluation, kind `authorise_task`, and creates one `tasks` document `{ task_id, report_id, kind: "search_related", question (the report's gap), params { condition, stage: "early", testing, has_results: true, max: 5 }, grant_id: "task-<hex>", status, result: null, authorised_by_decision_id }` (the params answer the report's gap, V26, V33), with its grant `task-<hex>@v1` written by `gate.grants.issue_task_grant()` (`gate/grants.py`)
**And** (V38) the `authorise_task` Decision, the task document, its grant and the durable queue entry are saved in one Atlas transaction: with `task_run` on the task is inserted `queued` (the task itself is the queue entry), with it off it is inserted `authorised` and never queued; either all of it is saved or none of it
**And** (V38) with `task_run` on, the route then calls `tasks.dispatch_next()`, which starts the task's run automatically on the derived run ID `derive("run_", task_id)`, insert-if-absent (`initiated_by: sam`, `agent: dxp-curator`, the task grant pinned); if another run is `running` or `stopping`, the task stays `queued` and starts when that run ends (`pipeline.run`'s `finally`), or, after a crash, from the background sweep or the API start hook; there is no task start button and `POST /runs` refuses a `task:` set
**And** the task grant is narrow: actions `search_source` and `file_related_evidence` only, the same research scope, destinations `source:clinicaltrials.gov` and `ledger`, `startable_by` Sam, and `expires_at` one hour after approval; it is inserted as a versioned grant by this authorised decision, which is the only way it changes permissions
**And** approve with a `correction` also creates a memory (Story 10.5), gated as `create_memory`; reject (note required) creates the memory and promotes nothing; each is its own Decision
**And** a second decision on the same report does nothing and returns its current state: a retried approval returns the existing decision, task and run, completing only a missing step (`approval.task_step` still `"pending"`, or a `queued` task with no run; a `"blocked"` or `"done"` task step is terminal and a retry never reopens it, V45), and never starts a second run (V38)
**And** the claim that moves the report to `accepting` also stores its `approval` record (the original decision, Reviewer and intended `task_id`, `task_step: "pending"`), so a crash after acceptance and before authorisation is completed by `tasks.recover_authorisations()` at the next API start, sweep, run end or decision, with authority rechecked: authorised, or a blocked Decision with "Follow-up task not authorised: <reason>"; never a second task, and no Reviewer click is needed (V45)
**And** a crash test (V45): a fault hook stops the service after the report is `accepted` and before `tasks.authorise()`; on restart, with no second click, the start hook leaves exactly one `authorise_task` Decision (cause: the original approval), one task (`queued` with `task_run` on, `authorised` with it off) and one grant, `approval.task_step: "done"`, and at most one run; a second variant revokes `sam@v1` before the restart and expects one blocked Decision, no task, `task_step: "blocked"` and the report saying "Follow-up task not authorised"
**And** `edit` is not offered on reports; a reject without a note returns 400
**And** the decision and the task authorisation appear in the run audit under "After the run" (V14)
**And** approved is not accepted for the task (V27): the response and the report state say "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." with `task_run` on, or "Approved: 1 update accepted. Follow-up task authorised; not run." with it off (V38); anything the task later finds stays pending until a Reviewer decides on it
**And** this story covers the authorisation, the queue entry and the start rule (`tasks/dispatch.py`); executing the task is Story 10.9 (A25, stretch, V39); without A25, `task_run` stays off, the task stays `authorised` and the loop is complete
**And** approval and rejection happen only in DxP, never in Slack (S4).

### Story 10.9: The follow-up task runs under its own grant and gate

**Points:** 2 · **Time:** ~1.2 h (S, 4 h developer estimate × 0.3, back end) · **Lane:** [API] · **Covers:** FR55 (follow-up task under its own grant and gate), FR31, FR33, FR34, FR38, V9, V26, V33 · **Stretch** (V39: the loop is forecast green at about 14:35, after the 14:30 gate; joins I3, to 15:15, only if merged and the loop is green by 14:30, V30) · **Owner:** Luis
**PRs:** A25 `story/10.9-task-run` (the task run, split from A24 again so it can be cut without touching the core, V28, Luis); B02 `story/9.7-run-console` (the task's run shown as "Follow-up task" with a link back to its report, Vlad); I3 `integration/i3-approve-task` (Luis). Cards in `development-plan.md`.

As a reviewer auditing the agent,
I want the authorised follow-up task to run as its own run, under its own narrow grant and its own gate,
So that approving one task never gives the agent wider authority, and the task's work is auditable like any other.

**Acceptance Criteria:**

**Given** a `queued` task (Story 10.8, with the backend flag `task_run` on in `DXP_FEATURES`); with the flag off the task stays `authorised`, no `task:` run is started and the report shows "Follow-up task authorised; not run"
**When** `tasks.dispatch_next()` (Story 10.8) starts it automatically after approval, or when the run that was active ends; there is no task start button (V38)
**Then** it runs as its own run on the derived run ID `derive("run_", task_id)` (insert-if-absent, so a retried approval or two workers never start it twice), with `initiated_by: sam`, `agent: dxp-curator`, the task grant pinned at start, and `cause { task_id, report_id }`; `tasks/run.py` first moves the task `queued` → `running` by a conditional update (no match: another worker owns it, and it exits), then files results through `reports.add_related()` as `file_related_evidence`; the run is listed by `GET /tasks/<task_id>` and `GET /tasks?report_id=`
**And** its own gate checks every action: the task grant active and unexpired (check 1), the scope (check 2), the destination and action (check 3), evidence and claims (check 4, Story 10.7), and run authorisation with one admission per action (check 5)
**And** for the demo it answers the report's gap (V26, V33): "Search ClinicalTrials.gov for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling, and report which have posted results (at most 5)"; a capped search cannot prove that no qualifying study has posted results, so an empty result is answered "No matching results found among the records searched" (V42); the task records `result { answer, with_posted_results[], query, searched_count, limit }` (the answer to its `question`, the trials with posted results, empty when none, and the query, the number of records searched and the limit, which the report page and the audit always show)
**And** its results are filed as pending related evidence on the report, never as accepted knowledge; approval of the report did not accept them (V27)
**And** a sixth result, or any search or filing outside the scope, is blocked and recorded as a blocked Decision
**And** stop works on the task's run as on any run (Story 9.5), and the task ends `stopped`; it otherwise ends `done`, `failed` or `blocked`, each by a conditional update on `running`; a task stuck in `running` after its admissions are abandoned is set `failed` (`error: abandoned`) by the sweep and never restarted (V38)
**And** the task's run is linked from the report and from the original run's audit (V14).

### Story 10.10: Report page with decisions and the memory panel

**Points:** 5 · **Time:** ~4 h (M, 8 h developer estimate × 0.5, screen; two builders in Vlad's lane, forecast 13:45) · **Lane:** [WEB] · **Covers:** FR56 (report page), FR52 (the memory panel), FR7, NFR1, NFR11, V10 · **Core** · **Owner:** Vlad
**PRs:** B04 `story/10.10-report-page` (two builders: the report body; decisions and the memory panel, Vlad; also carries the narrowed Stories 1.3 and 2.4); I3 `integration/i3-approve-task` (Luis). Cards in `development-plan.md`.

As a Reviewer opening a Slack alert,
I want the full report on one page with everything I need to decide, and the memories it used,
So that I can approve, reject or correct it in seconds and fix a memory where I see it.

**Acceptance Criteria:**

**Given** `web/app/reports/[report_id]/` reading `GET /reports/<report_id>` (Story 10.4) through the server-side key
**When** I open it, including from the Slack alert's "Review in DxP" link `${DXP_BASE_URL}/reports/<report_id>`
**Then** it shows the discovery with its status and supporting quotes; the related evidence with each label, both quotes and the similarity score (or "related (no relationship established)"); the retrieval method, with "related by text search" when that fallback ran; the uncertainties (including any unresolved name, V34); the evidence gap; the memories used with author, source and their before-and-after effect; the proposed updates, marked pending; the recommended task that answers the gap, with its status in words and no start button (V38): "Queued", "Running" (with a link to its run), its answer with the query, the number of records searched and the limit (V42), or "Follow-up task authorised; not run" when it was not run; and the report's script, always shown as text (V41)
**And** pending and accepted are labelled differently everywhere on the page
**And** Approve, Reject and "Approve with correction" call `POST /reports/<report_id>/decision`; Reject and "Approve with correction" require a note before they submit; the page shows the returned state and, after approval, the task and its status in words: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27) when the task was queued, or "Approved: 1 update accepted. Follow-up task authorised; not run." when it was not (V38); the task's findings, when any, show "Pending review", never "Accepted"
**And** Reject and "Approve with correction" also ask for the claim kind the note is about (for example `outcome_claim_without_results`), which becomes the memory's `tags.claim_kind` (V22)
**And** the memories panel, inside this page with no separate screen, lists the memories used and lets Sam correct (new text and note) or revoke (note) one through `POST /memories/<memory_id>/correct` and `/revoke`; Correct and Revoke sit behind the `memory_edit` flag (S3)
**And** the briefing player (`briefing` flag, B06) and the avatar video player (`avatar` flag, B08) sit in their own folders under `web/app/reports/[report_id]/`; they render on demand from "Generate briefing" and "Render avatar" buttons, the script is always shown as text, and the page never waits on either (V29)
**And** "Accepted knowledge" for the Diagnostic is a separate, linked view (the narrowed Story 1.3 at `web/app/diagnostics/[dx_id]/`), linked only when the report names a Diagnostic; a scope-collection update (`diagnostic_id: null`, V43) shows its accepted state in place, with no link and no `dx_id` assumed
**And** an unknown report ID shows "Report not found"; a 400 or 403 shows as a message and the page stays
**And** the evidence-relationship graph is not built; the relationship list is the view (Stories 5.1, 5.2 are cut)
**And** controls are reachable by keyboard and labelled; no name is chosen or sent.

### Story 10.11: Ten-second ElevenLabs briefing inside the report

**Points:** 2 · **Time:** ~1.5 h (S, 3 h developer estimate × 0.5, text to speech and screen) · **Lane:** [API] and [WEB] · **Covers:** FR57 (ten-second audio briefing), FR14, FR44 (supersedes Story 9.10), V12, V29 · **Supporting** (second in the V28 cut order) · **Owner:** Vlad
**PRs:** B06 `story/10.11-briefing` (Report briefing with ElevenLabs on demand behind a flag, Vlad; drops out of the demo if not merged by 14:45). Cards in `development-plan.md`.

As a Reviewer,
I want a ten-second spoken summary of the report,
So that I hear the finding and its strongest connection before I read.

**Acceptance Criteria:**

**Given** a filed report and the `briefing` flag on
**When** Sam presses "Generate briefing" on the report page, which calls `POST /reports/<report_id>/briefing` and `briefing.generate(report_id, ctx)` (`briefing/audio.py`); nothing generates a briefing automatically per report (V29)
**Then** ElevenLabs reads the report's stored script (`report.script`, built at filing by `reports.script_for()` in the core report PR, V41; B06 only consumes it), about ten seconds, built only from the report's fields (the discovery headline, its status and the strongest relationship) and never adds a fact beyond the report; it never says the trial studies a named assay or shows any assay's performance (V33); ElevenLabs reads it with ctDNA, MRD, EGFR and NSCLC pronounced correctly
**And** generating it is gated as kind `generate_briefing` to destination `tts:elevenlabs` under Sam's grant `sam@v1` (`run_id: null`, `cause { report_id, origin_run_id }`), with a Decision recorded; a failure is recorded and never fails anything else
**And** the audio is generated once per report state and cached in `audio`; `GET /reports/<report_id>/briefing` (`api/routes_briefing.py`) serves the cache, with 404 while none exists
**And** the report page has a "Generate briefing" button, then a play control with a loading state; the script is always shown as text
**And** without the ElevenLabs key or quota (OD3), or if ElevenLabs fails, the route returns the error shape with 503 and the player says "unavailable" while the script stays on the page; the report page, the Slack alert, the decision, the task and the rehearsal never wait on it (V29)
**And** it sits behind the `briefing` flag, never blocks a core PR, and is cut second if a milestone slips, right after the avatar video (B08, V28)
**And** its grounded script is the one Story 10.12 renders as the avatar video; the script exists on every filed report even when B06 is cut or the ElevenLabs call is unavailable (V41).

### Story 10.12: HeyGen avatar explaining the finding

**Points:** 2 · **Time:** ~1.5 h (S, 3 h developer estimate × 0.5, external render API and screen) · **Lane:** [API] and [WEB] · **Covers:** FR58 (HeyGen avatar video explaining a finding), V13, V29, OD7 · **Supporting** (behind the `avatar` flag; first in the V28 cut order) · **Owner:** Vlad
**PRs:** B08 `story/10.12-heygen-avatar` (HeyGen avatar video rendered on demand from the grounded report script, behind the `avatar` flag, Vlad; not built if the 10:45 HeyGen account check fails, V29). Cards in `development-plan.md`.

As a Reviewer opening a report,
I want a short avatar video explaining the finding in the same grounded words as the briefing,
So that the discovery is easy to follow at a glance without adding anything the report does not say.

**Acceptance Criteria:**

**Given** a filed report and its stored grounded script (`report.script`, built by `reports.script_for()` at filing, Story 10.4, V41; B08 only consumes it: the discovery, its status and the strongest relationship, nothing beyond the report's evidence fields)
**When** the `avatar` flag is on and Sam presses "Render avatar" on the report page (`POST /reports/<report_id>/avatar`); nothing renders automatically per report, and for the demo one render is requested for the demo report only, as soon as it is filed (V29)
**Then** DxP asks HeyGen (API v3) to render a short avatar video (about 20 seconds) from exactly that script; the script never adds facts beyond the report and never says the trial studies a named assay or shows any assay's performance (V33)
**And** `briefing.render_avatar(report_id, ctx)` (`briefing/avatar.py`, the only holder of `HEYGEN_API_KEY`) is gated as kind `generate_avatar_video` to destination `video:heygen` under Sam's grant `sam@v1` before any call to HeyGen, with a Decision recorded; a blocked request makes no call
**And** rendering is asynchronous: a `media` document records the provider video ID and the AD-14 `Media` status (`rendering`, `ready` or `unavailable`), nothing waits on the render, and `GET /reports/<report_id>/avatar` (`api/routes_avatar.py`) checks a `rendering` video with HeyGen in the background and returns `Media { status, video_url }`
**And** the report page shows "Rendering" until the video is ready, then plays it; a failed render, a missing key or an exhausted plan (OD7) shows "Avatar unavailable", and the script stays on the page as text
**And** `HEYGEN_API_KEY` is a secret kept only in `.env` and the Modal secret, never committed, logged, traced, returned or shown on screen; `.env.example` names it with no value
**And** the video is created during the event, from a report filed during the event; no clip is made beforehand (D1, V13); the `dxp-heygen` skill is reference only
**And** the discovery loop is unaffected by any avatar failure: filing, the Slack alert, decisions, the task, the audit and the rehearsal never wait on or fail because of the render
**And** it sits behind the `avatar` flag, never blocks a core PR, and is first in the cut order if a milestone slips (before the briefing, B06)
**And** (OD7) the 10:45 HeyGen check is an account check, off the critical path; if it fails, B08 is not built; the demo report's one render must finish before the report is opened on camera; if it has not, the demo shows "Rendering" or "Avatar unavailable" and moves on.

## Route ownership

Every route in the AD-14 table, including the routes the pivot and the readiness fixes add, is built by exactly one story and one PR, and has exactly one status (core, supporting, stretch, deferred or superseded), the same as in the AD-14 table (D40). Route names match AD-14; where AD-14 has not yet caught up with `readiness-fixes-2026-11-14.md`, the names that file defines win, and the owning story stays the same. Deferred rows are kept for history: the route is registered by A01 and stays 501.

| Route under `/api/v1` | Story (PR) | Status |
|---|---|---|
| Every route as a 501 stub, the error shape and the generated types | 1.1 (A01) | core |
| `GET /schema` | 1.1 (A01) | core |
| `GET /diagnostics/<dx_id>` (accepted knowledge) | 1.1 (A14, with A18 folded in) | core |
| `GET /diagnostics` (the list) | 1.1 | deferred (no Diagnostics list, D40) |
| `GET /teams` | 1.2 (A13) | core |
| `POST /runs { grant_id, set }` (`set` is `discover` or `nct:<NCT ID>`; a `task:` set is refused with 403, task runs start only through `tasks.dispatch_next()`, V38; a `discover` run calls `discovery.scan(scope_id, ctx)`, built by 10.1 in A05, then processes the discovered items), `GET /runs`, `GET /runs/<run_id>` | 9.1 (A07+A11) | core |
| `GET /whoami` (returns `Principal { id, name, kind, actions }`, D53), `GET /grants`, `GET /grants/<grant_id>`, `GET /policies` | 9.2 (A03) | core |
| `POST /actions/<action_id>/resolve { outcome: delivered \| failed, note }` (Reviewer, kind `resolve_notification`) | 9.4 (A09) | core |
| `POST /runs/<run_id>/stop` | 9.5 (A07+A11) | core |
| `GET /runs/<run_id>/audit` (with "After the run" and the V14 additions), `GET /decisions/<decision_id>`, `GET /actions?run_id=&status=`, `GET /actions/<action_id>` | 9.6 (A07+A11) | core |
| `GET /proposals?status=&field=&diagnostic_id=&run_id=&report_id=` | 2.2 (A14) | core |
| `GET /proposals/<p_id>` (one proposal, whatever its status; no `p_id=` query parameter, D42) | 2.2 (A14) | core |
| `POST /proposals/<p_id>/decision` (kind `decide_proposal`) | 2.3 | superseded by `POST /reports/<report_id>/decision` (V8, V24); registered by A01 and left 501 |
| `POST /diagnostics/<dx_id>/values/<value_id>/review` | 2.3 (A14) | core |
| `GET /scopes`, `GET /scopes/<scope_id>` (the research scope and its cursor) | 10.1 (A05) | core |
| `GET /reports?status=`, `GET /reports/<report_id>` | 10.4 (A19+A20) | core |
| `POST /reports/<report_id>/decision { action: approve \| reject, note, correction }` (kinds `decide_report`, `authorise_task`, `create_memory`) | 10.8 (A24) | core |
| `GET /memories?team_id=&status=`, `GET /memories/<memory_id>` | 10.5 (A21+A22) | core |
| `POST /memories/<memory_id>/correct { text, note }`, `POST /memories/<memory_id>/revoke { note }` | 10.5 (A21+A22) | supporting (third in the slip order) |
| `GET /tasks/<task_id>`, `GET /tasks?report_id=` | 10.8 (A24) | core (the authorised or queued task record, V28, V38) |
| Starting a task's run (no route: `tasks.dispatch_next()`, A24) and running it (`tasks/run.py`) | 10.8 (A24) starts, 10.9 (A25) runs | running is stretch (V39) |
| `POST /reports/<report_id>/briefing` (generate on demand, kind `generate_briefing` under `sam@v1`), `GET /reports/<report_id>/briefing` | 10.11 (B06) | supporting |
| `POST /reports/<report_id>/avatar` (request a render on demand, kind `generate_avatar_video` under `sam@v1`), `GET /reports/<report_id>/avatar` (render status and, when ready, the video URL) | 10.12 (B08) | supporting |
| `GET /changes?after=<seq>&run_id=`, by change stream or polling | 9.9 (A12) | cut (screens poll, D40) |
| `GET /graph?run_id=` (with `context=true`) | 5.1 | cut (A15 cut under section 7) |
| `GET /runs/<run_id>/audit/audio` | 9.10 (B06) | superseded by `GET /reports/<report_id>/briefing` (10.11) |
| `POST /policies/<policy_id>/approve { version }` | 9.11 (A17) | cut (policies stay hand-written, NFR15) |
| `POST /jobs`, `GET /jobs`, `GET /jobs/<job_id>` | 1.7 | superseded by the `/runs` routes, not built |
| `GET /rules`, `POST /rules/<rule_id>/status` | 2.6 | deferred |
| `GET /alerts`, `POST /alerts/<alert_id>/dismiss` | 3.1 | deferred |
| `GET /digest` | 3.3 | deferred |
| `GET /alerts/<alert_id>/audio` | 3.4 | deferred (replaced by 9.10) |
| `GET /terms` | 4.1 | deferred |
| `POST /query` | 4.2 | deferred |
| `POST /shortlists`, `GET /shortlists` | 4.4 | deferred |
| `POST /diagnostics/<dx_id>/values` | 4.7 | deferred |
| `GET /graph` with `focus`, `after` and `team_id`, `POST /teams/<team_id>/seen` | 5.1 | deferred |
| `GET /teams/<team_id>` (with resume) | 6.3 | deferred |

`GET /changes` moved from Story 1.1 to Story 9.9 (A12), and A12 is now cut: the Run console polls `GET /runs/<run_id>` and `GET /runs/<run_id>/audit`, the Audit view polls `GET /runs/<run_id>/audit`, and the pending-reports count polls `GET /reports?status=pending` (D40). A01 registers every new Epic 10 route as a 501 stub with the AD-14 `Scope`, `Report`, `Relationship`, `Retrieval`, `MemoryUse`, `Memory`, `Task`, `Media` and `SourceVersion` (V40) shapes in the contract. The web pages added are `web/app/reports/[report_id]/` (Story 10.10) and the small pending-reports list (Story 2.4); the alert's "Review in DxP" link targets the report page, and `web/app/review?proposal=` is no longer an alert target.

## Points and time summary

Time is the agent-time estimate from "Estimating with AI agents" above: each story's normal developer estimate times the factor for its kind of work. Kept-and-trimmed stories keep their original estimates, so the Saturday totals are an upper bound.

Saturday scope after the discovery-agent proposal of 14 November (kept, narrowed and new stories). For Epics 9 and 10, "Demo path" counts Core and Supporting stories and "Cut candidates" counts the Stretch stories (Story 10.9 is Epic 10's one Stretch story since V39). Epic 5's two stories (5.1 and 5.2) are cut with A15 and B05 under the proposal's section 7 and are counted in the cut and superseded table below, not here.

| Epic | Stories | Points | Developer estimate | Agent time | Demo path | Cut candidates |
|---|---|---|---|---|---|---|
| 1 Evidence-backed records from real data | 8 | 23 | 53.5 h | 23.7 h | 23.7 h | 0 h |
| 2 Agents propose, the Reviewer decides, guardrails learn | 3 | 7 | 15 h | 5.9 h | 5.9 h | 0 h |
| 3 Teams get told what matters | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| 4 Find, compare and fill gaps | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| 5 See the connections | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| 6 Pick up where you left off | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| 7 Capture on the go | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| 8 Ship it to the judges | 4 | 5 | 8 h | 5 h | 5 h | 0 h |
| 9 Governed agent actions | 8 | 22 | 39 h | 13.7 h | 13.7 h | 0 h |
| 10 Proactive discovery and research memory | 12 | 30 | 52 h | 20.4 h | 19.2 h | 1.2 h |
| **Total** | **35** | **87** | **167.5 h** | **68.7 h** | **67.5 h** | **1.2 h** |

Cut or superseded on 14 November (the discovery-agent proposal, section 7), not built on Saturday:

| Story | Points | Developer estimate | Agent time | Status |
|---|---|---|---|---|
| 9.9 Live action feed (A12) | 2 | 3 h | 1.5 h | Cut; screens poll (D40) |
| 9.10 Spoken audit briefing (old B06) | 2 | 4 h | 1.6 h | Superseded by Story 10.11 |
| 9.11 Rejection drafts a policy (A17) | 3 | 5 h | 2 h | Cut; policies stay hand-written (NFR15) |
| 5.1 Graph API built from the ledger's edges (A15) | 2 | 6 h | 2.4 h | Cut; the report lists its relationships (AD-26) |
| 5.2 Graph view with click-through (B05) | 3 | 7 h | 5.6 h | Cut with Story 5.1 |
| **Total (5 stories)** | **12** | **25 h** | **13.1 h** | |

Deferred (pivot, 13 Nov), not built on Saturday:

| Epic | Stories | Points | Developer estimate | Agent time | Demo path | Cut candidates |
|---|---|---|---|---|---|---|
| 1 Evidence-backed records from real data | 4 | 7 | 12.5 h | 5.6 h | 3.5 h | 2.1 h |
| 2 Agents propose, the Reviewer decides, guardrails learn | 4 | 8 | 17 h | 7.1 h | 5.6 h | 0 h |
| 3 Teams get told what matters | 5 | 9 | 20 h | 8.7 h | 6.8 h | 1.9 h |
| 4 Find, compare and fill gaps | 8 | 16 | 37 h | 21 h | 0 h | 4.2 h |
| 5 See the connections | 1 | 2 | 4 h | 3.2 h | 3.2 h | 0 h |
| 6 Pick up where you left off | 4 | 8 | 19 h | 10.8 h | 10.8 h | 0 h |
| 7 Capture on the go | 1 | 2 | 4 h | 1.2 h | 0 h | 1.2 h |
| 8 Ship it to the judges | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| 9 Governed agent actions | 0 | 0 | 0 h | 0 h | 0 h | 0 h |
| **Total** | **27** | **52** | **113.5 h** | **57.6 h** | **29.9 h** | **9.4 h** |

All 67 stories together: 151 points, 306 h developer estimate, 139.4 h agent time. Epic 10 adds 12 stories, 30 points and 20.4 h. The readiness fixes added about 1 h to Story 1.1 for PR A18 (the Record read model and `GET /diagnostics/<dx_id>`), now folded into A14. Before the pivot the plan was 44 stories, 92 points and 97.1 h; before the discovery-agent proposal it was 55 stories, 121 points and 119 h.

| Lane (Saturday scope) | Agent time |
|---|---|
| [API] | 43.7 h |
| [WEB] | 22 h |
| [API] and [WEB] (Stories 10.11, 10.12) | 3 h |

| Owner (Saturday scope) | Agent time |
|---|---|
| Luis | 45.7 h |
| Vlad | 23 h |

PR bundling (the proposal's section 7, cut 2): to cut Luis's merges, A21 merges with A22 (memory), A19 with A20 (retrieval feeding the report), A23 lands inside A06, A18 merges with A14, and A07 with A11; A24 (decision, promotion, task authorisation, branch `story/10.8-approve-task`) and A25 (task execution, branch `story/10.9-task-run`) are split again so A25 can be cut without touching the core (V28). Each bundle is one branch and one pull request, named after its first story; the stories it carries are still tracked and checked separately. Contracts and leaf modules start first, and merges are staggered from 12:30. B04 (the report page) gets two builders in Vlad's lane. I2 is folded into the rehearsal's first pass (cut 1), which is core acceptance. HeyGen stays as a supporting PR, B08, behind the `avatar` flag, rendering on demand (V29). The core cut line (V28): discovery, an evidence relationship with quotes, a memory changing the report, a policy block, the Slack notification opening the report, the human decision, the audit trail and stop are never cut; the task's authorisation (Story 10.8) is core but cheap. If a milestone slips, cut supporting work in this order: (1) the avatar video (B08), (2) the briefing (B06), (3) the memory correct and revoke screen (memory creation and use stay core), (4) the second discovery item. Follow-up task execution (A25, Story 10.9) is stretch, not a supporting cut (V39).

PR and merge: about 10 minutes per story, already inside the measured actuals the factors come from, so not added again.

Capacity and timing for Saturday are in `build-schedule.md` and the PR cards in `development-plan.md`, both rewritten for 10:45 to 17:00. The totals above are summed cycle times, useful for comparing parts of the plan, not for deciding what fits.

Timing (`development-plan.md` and `build-schedule.md`, with the section 7 cuts and V30; L1 and L2 are risks approved by Luis, V31, and the float holds only if the merge milestones are met, including the L2 proof at 12:30 and the 13:00 desk decision, V36): hacking 10:45 to 17:00 on the Atlas Sandbox; contracts frozen 11:45; I1 setup (step 1, 13:30 to 13:50: FDA seed, prior collection, embeddings and index ready; step 2, 14:00 to 14:15: the setup run on NCT05715229, M1 created by Sam, snapshot) and the discovery loop through Slack by about 14:45; I3 approval, promotion, authorisation and audit 14:45 to 15:00 (the follow-up task, stretch since V39, joins, to 15:15, only if A25 is merged and the loop is green by 14:30, using 15 of the 20 minutes of float); the rehearsal 15:00 to 16:10, its first pass core acceptance (I2 folded in), then a reset, pass 2 and a reset for the video; code freeze 16:30, with 20 minutes of hard float, conditional on the merge milestones; the 60-second video script (Story 8.4, B07) written by 14:00; the video recorded 16:30 to 16:50 and submitted by 16:55 with the description, public repository and team members (task R1, Luis and Vlad); the 3-minute live demo for judging at 17:15.

## Departures

These departures from the architecture spine were introduced by the stories before the pivot. They are now folded into the architecture spine's AD-14, which also carries the pivot's new routes and shapes; the list stays here for history.

- Story 2.1 adds a `dry_run` job mode beside `baseline` and `live` (AD-4); it writes nothing. (Story 2.1 is deferred.)
- Story 4.4 adds `POST /shortlists` and `GET /shortlists` to the AD-14 route table. (Story 4.4 is deferred.)
- Fields added to AD-14 shapes so the screens in the UX can be built: `Job` gets `limit`, `actor`, `started_at`, `finished_at`, `counts.filed` and `active` (Story 1.7); `Alert` gets `diagnostic_name`, `lifecycle_stage`, `from_stage` and its Evidence (Story 3.1); graph nodes get `sample_type` (Story 5.1); `GET /graph` takes `team_id` (Story 5.1).
- Story 1.1 serves `GET /changes` by plain polling; the long-poll in AD-10 is optional.
