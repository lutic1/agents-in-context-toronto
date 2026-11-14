---
title: Sprint Change Proposal, restore the discovery-agent vision
status: approved
approved_by: Luis
approved: 2026-11-14 (V1 to V45, including the V45 memory-creation recovery limitation)
created: 2026-11-14
scope: major
supplements: sprint-change-proposal-2026-11-13.md, readiness-fixes-2026-11-14.md, sprint-change-proposal-2026-11-14-slack.md
---

# Restore the discovery-agent vision

Where an earlier planning document disagrees with this file, this file wins. The D1 to D57 audit fixes and the Slack decisions (S1 to S13) still apply wherever this file does not replace them.

## 1. Why

While we narrowed the plan to an audit demo, we lost the product. DxP is a **proactive diagnostic-evidence research agent**:

- It discovers new trials.
- It connects them to existing evidence.
- It remembers reviewer corrections.
- It proposes useful follow-up work.

Governance (identity, grants, policies, decisions, stop, audit) supports that workflow rather than being the whole product. The entry stays under **Statement 1, "Agents You Can Audit"**. Atlas remains the identity, policy and audit layer, and now also stores the evidence collection, its embeddings and the reviewer memory. DxP supports research review and gives no medical advice.

## 2. The experience, as one working loop

1. **Discover.** The agent searches ClinicalTrials.gov, the one public discovery source, within one research scope. It looks for trials updated since its last scan.
2. **Relate.** Atlas Vector Search retrieves related documents and earlier findings. The agent then says whether the new evidence **supports**, **contradicts** or **extends** existing research, or **raises a new question**. Each label cites quotes from both sides. A similarity score is shown, but it is never used as evidence for a claim.
3. **Remember.**
   - The agent retrieves relevant reviewer corrections from memory, and the report shows what each one changed.
   - Each memory is scoped to the Team, linked to its author and source decision, and can be corrected or revoked.
   - A memory informs reasoning only; it never changes permissions.
4. **Gate.** Explicit policies are checked before every action. Examples:
   - The agent cannot say an assay was performed, or that it produced results, unless the source reports that.
   - Planned or recruiting trials must be described as planned or ongoing.
   - Cell-line or animal findings must be labelled preclinical.
   - Only an authorised policy change alters permissions.
5. **Propose.**
   - The agent prepares a **pending research report**: the discovery, supporting quotes, related evidence with relationship labels, uncertainties, and one recommended next research task.
   - The report and its proposed knowledge updates are stored in Atlas as pending, clearly separated from accepted knowledge.
6. **Notify.**
   - A governed Slack alert (S1 to S13, webhook already validated) has a "Review in DxP" link that opens the full report.
   - Approval and rejection happen only in DxP.
7. **Brief.**
   - The report includes a ten-second ElevenLabs audio briefing, generated only from the report's evidence fields.
   - It also includes a short HeyGen avatar video explaining the finding from the same grounded script. This is supporting scope, behind a flag (Luis, 14 Nov: "make it part of it").
8. **Decide.**
   - Approval promotes the report's proposed updates into accepted knowledge and authorises the one recommended follow-up task. The task then runs under its own grant and passes its own policy gate.
   - Rejection, or approval with a correction, creates an attributable memory used for the next relevant discovery.

## 3. What the demo must show

| # | Must show | How |
|---|---|---|
| 1 | One real discovery connected to previous evidence | The scan finds NCT04712877, updated 12 Nov 2026, which names FoundationOne Liquid CDx. Vector Search retrieves related prior evidence, for example other in-scope trials naming FoundationOne Liquid CDx or Guardant360 CDx. The report labels each relationship and cites quotes from both sides |
| 2 | One retrieved reviewer correction visibly changing the next proposal | Earlier in the day (during the event, through the real UI), Sam corrects a report on NCT05715229, which was terminated with no results: "Terminated trial with no posted results: describe its status; do not state outcomes". That creates memory M1. The discovery report on NCT04712877 retrieves M1 and shows its effect: "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet" |
| 3 | One unsupported claim or unauthorised action blocked before it takes effect | The agent's first draft states that NCT04712877 "showed" FoundationOne Liquid CDx detecting EGFR. The claim-accuracy policy blocks it before filing: the source status is RECRUITING and `has_results` is false. One blocked Decision is recorded. Team scope still blocks FoundationOne CDx (tissue), as before |
| 4 | A Slack alert opening the evidence report in DxP | `#all-mango-db-hackathon` gets one alert per report. "Review in DxP" opens `${DXP_BASE_URL}/reports/<report_id>` |
| 5 | Human approval, then a small concrete research task | Sam approves. The accepted updates land, for example NCT04712877 is added to FoundationOne Liquid CDx's Trials. The authorised task runs at once under its own grant: "Search ClinicalTrials.gov for other NSCLC trials naming FoundationOne Liquid CDx and file them as related evidence (max 5)". Its own gate checks the source, scope and limit, and its results are filed as pending related evidence |
| 6 | An audit trail and an honest stop | The Audit view reconstructs: the sources, the memories used (with author), the agent identity, the grant and policy versions, every decision allowed or blocked, the Slack result, the review decision, and the task's run. Stop works as defined in D7 and D22 to D24 |

These facts were checked in the prepared data during planning: NCT04712877 is RECRUITING with `has_results: false`, and NCT05715229 is TERMINATED with `has_results: false`. The build re-fetches them live (D1). The live API may differ on the day; see open dependency OD2.

## 4. Covered, restored and added

### Already covered by the current plan (keep, with D1 to D57 and S1 to S13)

- Run identity with two identities, grants, key resolution and the 401 rule (D4, D16 to D19).
- The policy gate before every action, with Decisions for allowed and blocked outcomes, policy sets, and stable IDs and `seq` (D5, D6, D20, D21).
- Admissions, stop, sweep and recovery (D7, D22 to D24).
- Pending-only review, and an all-or-nothing apply owned by A06 (D8, D13, D26 to D28).
- The Slack notify-only alert with outcomes and manual resolution (S1 to S13).
- The audit API and view, extended below.
- The Atlas Sandbox, reuse rules, resets, single file owners and the tracker (D1, D41, D36, D35).
- The FDA seed as accepted baseline knowledge, the aliases and the team scope (D30 to D32, D45, D56).

### Restored (was deferred in the pivot)

| Capability | Was | Now |
|---|---|---|
| Proactive discovery | FR-1 scans, Stories 1.10 and 1.11 deferred; only a fixed NCT list was fetched | Story 10.1: a scoped ClinicalTrials.gov search, with a cursor on the last-update date. Tavily and scheduled scans stay deferred |
| Embeddings and Vector Search | Story 4.1 and AD-15 deferred | Story 10.2: embeddings on evidence and findings, an Atlas Vector Search index, and related-evidence retrieval |
| Reviewer memory | Epic 6 and AD-8 memory deferred; Learned rules (2.6) deferred | Stories 10.5 and 10.6: Team-scoped, attributable, correctable and revocable memories in Atlas, retrieved into proposals. They are **not** Learned-rule enforcement: memories never change permissions. Agent Memory preview stays deferred |
| Audio briefing | Story 9.10 was stretch | Story 10.11: a ten-second briefing inside the report, at supporting priority |

### Added (new)

| Capability | Story |
|---|---|
| Relationship classification: supports, contradicts, extends or new question, with quotes from both sides; similarity is never evidence | 10.3 |
| The research report as the pending proposal: discovery, quotes, related evidence, uncertainties, recommended task | 10.4 |
| Claim-accuracy policies: performed or results only if reported; planned or recruiting described as such; cell-line or animal labelled preclinical | 10.7 |
| Approval promotes to accepted knowledge and authorises one follow-up task | 10.8 |
| The follow-up task runs under its own grant and gate | 10.9 |
| The report page in DxP, opened from Slack, with approve, reject or correct, and memories used | 10.10 |
| A memory panel for correcting or revoking a memory | Inside 10.10 (no separate screen) |
| HeyGen avatar explaining the finding, from the same grounded script as the briefing | 10.12, supporting, behind the `avatar` flag, PR B08 (Vlad) |

### Cut or narrowed now, so the loop fits

| Item | Change |
|---|---|
| Live change-stream feed (9.9, A12) | Cut. Screens poll (D40) |
| Learned-rule policy drafts (9.11, A17) | Cut. Policies stay hand-written (NFR15) |
| The old audio briefing (9.10) | Replaced by 10.11 |
| Separate Review list screen (2.4) | Narrowed: a small pending-reports list linking to the report page (10.10) |
| The Record page (1.3) | Narrowed to an "Accepted knowledge" view of one Diagnostic, reached from the report |
| Impact graph (5.1, 5.2, A15, B05) | Supporting and first-cut. Kept only as an evidence-relationship view inside the report, if time allows; the report's relationship list is enough |
| The 20-trial selected set as the demo's source of new data (D30) | Narrowed. The trials are split into a prior collection, loaded in baseline mode before the discovery run, and the live discovery scan |

## 5. Decisions (V1 to V20)

### Discovery and retrieval

- **V1. Research scope.** "Plasma ctDNA genotyping assays in advanced NSCLC", owned by the Team "Team Liquid Biopsy Dx" (`lbdx@v1`). The assays are the four exact strings in D45. The scope is a document in Atlas (`research_scopes`), and the agent grant names it.
- **V2. Discovery (Story 10.1, PR A05).**
  - `discovery.scan(scope_id)` queries ClinicalTrials.gov API v2 with:
    - `query.term` = the in-scope assay names and aliases;
    - `query.cond` = non-small cell lung cancer;
    - `filter.advanced` = `AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]`.
  - Each result becomes a Source item with `window: "discovered"`.
  - The cursor lives on the scope and advances only after a scan finishes.
  - Gated as action kind `search_source` with destination `source:clinicaltrials.gov`.
  - The prior collection is the D30 trials last updated before the cursor. It is fetched by NCT ID and loaded in baseline mode during setup.
- **V3. Embeddings and Vector Search (Story 10.2, PR A19).**
  - Each Source item's evidence text and each Finding's summary get an embedding, through Atlas Automated Embedding if the sandbox supports it (OD1). Otherwise the Voyage AI embeddings API is called directly, if a key is cleared (OD1).
  - `$vectorSearch` retrieves the top related items within the same scope.
  - If neither works on the day, related retrieval falls back to Atlas Search text search. The report then says "related by text search", never "Vector Search".
- **V4. Relationships (Story 10.3, PR A20).**
  - The model classifies each related item as `supports`, `contradicts`, `extends` or `new_question`. Each classification has a rationale that quotes both the new and the related evidence; both quotes are checked word for word (AD-6).
  - The similarity score is stored and shown, and it never stands in for a quote.
  - An item without two checked quotes is shown as "related (no relationship established)".

### Reports and memory

- **V5. Report (Story 10.4, PR A20).** Collection `reports`. A pending report contains:
  - the discovery and its supporting quotes;
  - the related evidence with labels;
  - uncertainties, for example status or missing results;
  - the memories used, each with its effect;
  - the proposed knowledge updates, which are pending proposals (D8);
  - one recommended follow-up task.

  Accepted knowledge (Diagnostics, accepted values, accepted findings) is separate, and the UI labels pending and accepted differently.
- **V6. Memory (Stories 10.5 and 10.6, PRs A21 and A22).**
  - Collection `memories`: `{ memory_id, team_id, author, source { decision_id, report_id }, text, tags { assay, claim_kind }, embedding, status: active | corrected | revoked, version, supersedes }`.
  - A memory is created by a Reviewer rejection, or by an approval with a correction note, through action kind `create_memory`, gated under the Reviewer's grant.
  - It can be corrected (a new version superseding the old) or revoked through `correct_memory` and `revoke_memory`, also gated and audited.
  - Retrieval is filtered by Team, `active` status and tags, then ranked by Vector Search similarity to the discovery.
  - The report lists each memory used, with author, source and effect: the sentence or label it changed, before and after.
  - Memories never change grants or policies.

### Policies, approval and the follow-up task

- **V7. Claim-accuracy policies (Story 10.7, PR A23).** Check 4 (evidence) gains claim checks, decided from the source's own fields and quotes:
  - `claim_performed_or_results` needs `has_results: true`, or a quote saying the assay was performed with results.
  - `claim_planned` must be used when the status is NOT_YET_RECRUITING or RECRUITING, or the trial is planned.
  - `claim_preclinical` must label cell-line or animal evidence.

  A claim failing these checks is blocked before filing, with one blocked Decision recorded. The agent may redraft once; the redraft is a new evaluation with its own Decision.
- **V8. Approval and promotion (Story 10.8, PR A24).**
  - `POST /reports/<report_id>/decision { approve | reject, note }` is gated as kinds `decide_report` and `authorise_task` under `sam@v1`.
  - Approve applies the report's pending proposals through `ledger.apply` (A06) and marks the report `accepted`.
  - It creates one `tasks` document: `{ task_id, report_id, kind: "search_related", params: { assay, condition, max: 5 }, grant_id: "task-<id>@v1", status: authorised }`.
  - The task grant is narrow: action `search_source` and `file_related_evidence`, the same scope, and an expiry of one hour.
  - **Approve with correction** does everything Approve does (promote, authorise the task) and also creates a memory from the correction note (V6).
  - **Reject** promotes nothing and authorises no task. If the reason should guide future proposals, it creates a memory (V6).
- **V9. Follow-up execution (Story 10.9, PR A25).**
  - An authorised task runs as its own run, under its task grant, with `initiated_by: sam` and `agent: dxp-curator`.
  - Its own gate checks the grant, scope, destination, limit and run authorisation.
  - Its results are filed as pending related evidence on the report, never as accepted knowledge.
  - Exceeding the limit or leaving the scope is blocked and recorded.

### The report page, Slack and audio

- **V10. Report page (Story 10.10, PR B04).**
  - `web/app/reports/[report_id]/` shows the discovery, quotes, related evidence with labels and similarity, uncertainties, memories used and their effect, the proposed updates, the recommended task, and Approve, Reject or "Approve with correction".
  - A memory can be corrected or revoked from the memories panel.
  - "Accepted knowledge" for the Diagnostic is a separate, linked view.
- **V11. Slack.**
  - S1 to S13 apply, with one alert per report, not per proposal (this replaces D46's per-proposal alert).
  - "Review in DxP" links to `${DXP_BASE_URL}/reports/<report_id>`, and "Open diagnostic" links to `${DXP_BASE_URL}/diagnostics/<dx_id>` (accepted knowledge).
  - The alert's body is the report headline, the relationship summary and "Approve or reject in DxP".
- **V12. Audio briefing (Story 10.11, PR B06).**
  - ElevenLabs reads a ten-second script built from the report's evidence fields: the discovery, its status and the strongest relationship.
  - It is cached and has a play control on the report page.
  - The script never adds facts beyond the report. It is gated as `generate_briefing`.
  - It depends on the ElevenLabs key (OD3).
- **V13. HeyGen avatar (Story 10.12, PR B08, supporting).**
  - After a report is filed, DxP asks HeyGen (API v3) to render a short avatar video (about 20 seconds) from the same grounded script as V12. The script never adds facts beyond the report.
  - Gated as `generate_avatar_video`. Rendering is asynchronous: the report page shows "Rendering" until the video is ready, then plays it. A failed render shows "Avatar unavailable" and the loop is unaffected.
  - `HEYGEN_API_KEY` is a secret, kept only in `.env` and the Modal secret.
  - The video is created during the event; no clip is made beforehand.
  - The `dxp-heygen` skill is reference only (D1) and is no longer marked deferred.

### Audit and the demo

- **V14. Audit additions (PR A11, B03).** The run audit also shows:
  - the sources fetched, with the scan cursor;
  - the retrieval (method, top-k, scores);
  - the memories used, with their effect;
  - the relationship labels and quotes;
  - report and task decisions, and the follow-up task's run, linked.
- **V15. Demo data, all created during the event (D1).**
  - The prior collection, the FDA seed and the memory M1 all come from real API calls and real UI actions on Saturday.
  - M1 is created by Sam during setup (I1 step 2), not seeded from a file.
  - The post-setup snapshot includes M1, and the reset restores it (D41).
- **V16. The demo order (replaces D33).**
  1. Start the discovery run.
  2. The scan finds NCT04712877.
  3. The draft "showed" claim is blocked before filing.
  4. The report is filed with M1's effect visible.
  5. The Slack alert arrives; "Review in DxP" opens the report.
  6. Play the ten-second briefing and the avatar video (if ready).
  7. Stop is shown honestly, on a second run with remaining items, or on the follow-up task if it is still running.
  8. Sam approves.
  9. The follow-up task runs and is gated.
  10. The Audit view answers: "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"
- **V17. 60-second video (replaces D52).**
  - 0 to 10 s: the scope and the agent's identity.
  - 10 to 25 s: the discovery and its related evidence, and M1 changing the wording.
  - 25 to 35 s: the blocked claim.
  - 35 to 45 s: the Slack alert opening the report.
  - 45 to 60 s: approval, the follow-up task, and the audit answer.

### Statuses and capacity

- **V18. What stays deferred.** Find and Categories, Team Alerts, the Home dashboard, Tavily, scheduled scans, PubMed, Agent Memory preview, Learned-rule enforcement and quick capture.
- **V19. Capacity (replaces the earlier assumption).** Luis up to 44 agents; Vlad up to 22 agents (Sonnet 5.5 high). Concurrency does not shorten the chain of dependent tasks, and every PR still needs CI and a human merge (see section 6).
- **V20. Status.** This file is draft until Luis confirms it.
- **V21. The blocked claim and the memory effect come from two gated drafts.**
  - The drafter writes the report twice: first without memories, then with the retrieved memories.
  - Both drafts go through the gate, and each evaluation is its own Decision.
  - An unsupported claim in the first draft (for example "showed") is blocked before filing. The second draft is filed. The report's before/after memory effect comes from the two real drafts.
  - The blocked claim is not guaranteed, because the model may not write it. Must-show 3 is therefore guaranteed by the team-scope block on FoundationOne CDx (an unauthorised action), and the blocked claim is shown whenever it occurs.
- **V22. Memory retrieval matches what the correction is about.**
  - Memories are retrieved by Team, `active` status and `claim_kind` (for example `outcome_claim_without_results`), then ranked by similarity. They are not filtered by assay.
  - M1 (written on a Guardant360 trial) is therefore retrieved for the FoundationOne Liquid CDx discovery.
- **V23. Scheduling changes the plan depends on (for Luis to decide).**
  - L1: A06, A08, A19 with A20, and A21 with A22 start at 10:45 as drafts against the shapes in this file and the spine, then rebase onto the contract after 11:45.
  - L2: Vlad merges four of Luis's self-contained PRs (A05, A13, A14, A09) after Luis's review agent and the contract keeper pass them.
  - Without both, the merge queue pushes the loop past 15:15 and the rehearsal past the freeze.
- **V24. Names follow the architecture spine.**
  - A report is filed as a report-level `file_proposal`; there is no `file_report` kind.
  - `POST /runs { grant_id, set }`, with `set` one of `discover`, `nct:<id>` or `task:<id>`.
  - Per-proposal decisions are superseded by the report decision (`POST /reports/<report_id>/decision`). A14 keeps the proposal GET routes and `review_value`.

## 6. Critical path

### Sequential work, from the dependency model

Start 10:45. Cycle times are agent cycle times from `epics.md`. Vlad's lane runs at 1.25 times.

```
10:45 ─ A01 contract (+ reports, memories, tasks, scopes, relationships shapes)  1.0 h
11:45 ─ parallel builds against the contract:
        A06 ledger + gate (+ A23 claim checks)              2.0 h  → 13:45
        A08 extraction                                       2.0 h  → 13:45
        A20 relationships + report assembly                  2.0 h  → 13:45
        A19 embeddings + vector index + retrieval            1.5 h  → 13:15 (+ index build ~10 min)
        A05 discovery scan, A21 memory, A22 retrieval,
        A24 promote, A25 task run, A07 runs/stop, A11 audit, A09 Slack  ≤ 2.0 h → ≤ 13:45
        B01 shell 10:45→11:45, then B04 report page (2.5 h × 1.25 ≈ 3.1 h) → 14:50
13:45 ─ I1 integration: setup (FDA seed, prior collection, embeddings, index ready; Sam's correction creates M1; snapshot) 30 min
14:15 ─ I1 loop: discovery → blocked claim → report with M1 → Slack                     30 min → 14:45
14:45 ─ I3 approval → promotion → follow-up task (needs A24, A25, B04)                   30 min → 15:15
15:15 ─ I2 core acceptance on the sandbox (reset first)                                  30 min → 15:45
15:45 ─ A16 rehearsal (one pass + reset)                                                  40 min → 16:25
16:30 ─ freeze; R1 video 16:30–16:50; submit 16:55; reset 16:55–17:10; live demo 17:15
```

### Result

- **The longest chain ends about 16:25, so float is about 5 minutes.** That is not enough.
- **Second near-critical chain:** B04 (the report page) finishes about 14:50. It is needed by "Slack opens the report", which is now checked in I3, not I1.

### The hidden limit: merges

- About 22 of Luis's PRs would finish between 13:15 and 13:45.
- At about 10 minutes per merge (CI plus a human look), that is about 3.5 hours of merging for one person. More agents do not fix this; only fewer, staggered PRs do.

## 7. Cuts to make it fit

Recommended. They take float from about 5 to about 35 to 40 minutes, and the merge queue from about 3.5 hours to about 1.5:

1. **Fold I2 into the rehearsal's first pass.** Rehearsal pass 1 is core acceptance. Saves 30 min. Risk: issues are found later.
2. **Bundle PRs to cut merges** (about 22 down to about 13 for Luis):
   - A21 with A22 (memory);
   - A24 with A25 (approval and task);
   - A19 with A20, with retrieval feeding the report;
   - A23 inside A06;
   - A18 with A14;
   - A07 with A11.
   - Stagger them: start contracts and leaf modules first, merge from 12:30.
3. **Cut A12, A15, B05 and A17** outright. HeyGen stays, as a supporting PR (B08) behind a flag. Screens poll. The report shows relationships as a list.
4. **Keep the ElevenLabs briefing (B06) as supporting, behind a flag.** If it isn't merged by 14:45, it drops out of the demo.
5. **B04 report page gets two builders (Vlad's lane):** the report body, and decisions plus the memory panel. Forecast 13:45 instead of 14:50.

If a milestone slips, cut in this order: the avatar video (B08), the briefing (B06), the memory correction and revoke UI (keeping memory creation and use), the follow-up task's related-evidence filing (the task runs and is gated; results shown in the audit only), then the second discovery item.

## 8. Open dependencies (unverified)

| # | Dependency | Fallback |
|---|---|---|
| OD1 | Atlas Sandbox supports Vector Search indexes and Automated Embedding; or a Voyage AI key is allowed | Text search, labelled honestly |
| OD2 | On Saturday, the live ClinicalTrials.gov API still returns NCT04712877 as updated after the cursor, RECRUITING, without results | Choose the cursor and confirm the target trial at 10:45 by a manual query; any in-scope trial updated since the cursor works, and the claim policy applies the same way |
| OD3 | ElevenLabs key and quota | The briefing is hidden |
| OD7 | HeyGen needs a paid plan or a funded API wallet (from US$5); the free plan is watermarked and licensed for non-commercial use only. Render time: the API docs say 1 to 5 minutes for most videos, but HeyGen's help centre says the regular queue can average just under 24 hours on weekdays (faster at weekends, priority for higher tiers). The demo report's video must finish during the run | Trigger the render as soon as the report is filed and open the report last on camera. If it is not ready, the report shows "Rendering" or "Avatar unavailable" and the loop is unaffected. Measure one render at 10:45 to decide |
| OD4 | Organiser clearance items from D1 and D57 (prepared data, logo, Slack channel volume) | As in D1 and D57 |
| OD5 | Change streams on the sandbox | No longer needed (cut) |
| OD6 | `mongodump` and `mongorestore` against the sandbox for the reset | Reset by rerunning the setup, which takes longer |

## 9. Handoff

Update together:
- the PRD and addendum;
- the architecture spine;
- `EXPERIENCE.md` and `DESIGN.md`;
- `epics.md` (new Epic 10; supersede or narrow the stories in section 4);
- `development-plan.md` (PRs and owners as in section 7);
- `build-schedule.md` (critical path, merge queue, milestones);
- the earlier change proposals (a pointer to this file);
- `sprint-status.yaml` (scopes);
- `README.md` (the one-line description and the loop).

## 10. Review of PR #8: decisions V25 to V32

A review of PR #8 found that the direction is strong, but the plan is not yet a low-risk build. These decisions fix that, and they win over V1 to V24 where they differ.

### What the demo claims

- **V25. Frame the discovery honestly, as a new trial signal worth investigating.**
  - NCT04712877 ("Testing Tumor Tissue and Blood to Help Select Personalized Treatments for Patients With Suspected Lung Cancers") is RECRUITING with no results. It pairs FoundationOne Liquid (blood) with FoundationOne CDx (tissue) to find 12 actionable drivers in stage IA2 to III disease, for neoadjuvant trial eligibility.
  - The report's headline is: "New trial signal: plasma genotyping with FoundationOne Liquid CDx is being studied in early-stage (IA2 to III) lung cancer, alongside tissue testing. No results yet."
  - The expected relationship to the prior collection (advanced NSCLC use) is `extends` (a new setting). The model must back it with two checked quotes, and if it cannot, the item is shown without a relationship.
  - Nothing in the report, the Slack alert, the briefing or the avatar says or implies the trial showed assay performance.
  - The research scope becomes "Plasma ctDNA genotyping assays in NSCLC" (all stages), so the early-stage trial is in scope.
- **V26. Define the gap first, then make the follow-up answer it.**
  - Every report names one evidence gap. For the demo: "Has any study posted results for FoundationOne Liquid CDx in early-stage (resectable) NSCLC?"
  - The recommended task answers exactly that gap: search ClinicalTrials.gov for NSCLC trials naming FoundationOne Liquid CDx in early-stage disease, and report which have posted results (at most 5).
  - "None with posted results" is a valid, honest answer, and the task reports it as such. *(Note, V42: a capped search cannot prove this; the answer is now "No matching results found among the records searched", with the query, the number of records searched and the limit.)*
  - The task's findings are filed as pending related evidence. They are never accepted knowledge.
- **V27. Approved is not accepted for the task.**
  - Approval promotes the report's own updates to accepted knowledge, and authorises the follow-up task.
  - Anything the task finds stays pending until a Reviewer decides on it.
  - The report page, the Audit view and the demo narration say this in words, for example: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review."

### What must ship, and what gets cut

- **V28. A hard core cut line.**
  - **Core: never cut.**
    - discovery;
    - an evidence relationship with quotes;
    - a memory changing the report;
    - a policy block;
    - the Slack notification opening the report;
    - the human decision (approve with promotion, or reject or correct with a memory);
    - the audit trail;
    - stop.
  - **Core, but cheap:** the recommended task and its authorisation, which is a record created at approval.
  - **Supporting, cut in this order:**
    1. the HeyGen avatar;
    2. the ElevenLabs briefing;
    3. the memory correct and revoke screen (memory creation and use stay core);
    4. **follow-up task execution**, the first substantial feature cut; *(Note, V39: task execution is now stretch, not a supporting cut.)*
    5. a second discovery item.
  - A24 (decision, promotion, task authorisation) and A25 (task execution) are split again, so A25 can be cut without touching the core.
- **V29. Media is on demand, and never gates anything.**
  - The report page has "Generate briefing" and "Render avatar" buttons, behind the `briefing` and `avatar` flags. Nothing renders automatically per report.
  - For the demo, one avatar render is requested for the demo report only, as soon as it is filed.
  - The report, the Slack alert, the decision, the task and the rehearsal never wait on either service.
  - The script is built only from the report's fields and is always shown as text. If ElevenLabs or HeyGen fails, the text stays correct and the player says "unavailable".
  - The 10:45 HeyGen check is an account check, off the critical path. If it fails, B08 is not built.

### The schedule

- **V30. One float number.**
  - With A25 and media off the core path: I3 becomes "approval, promotion, authorisation and audit" (14:45 to 15:00).
  - The rehearsal runs 15:00 to 16:10: pass 1 as core acceptance, a reset, pass 2, and a reset for the video.
  - That gives **20 minutes of hard float at the 16:30 freeze**. This is the only float figure in the plan.
  - If A25 is merged by 14:30 and the loop is green by 14:30, the follow-up task joins I3 (to 15:15) and uses 15 of those 20 minutes. Otherwise A25 is cut.
- **V31. L1 and L2 are risks with a proof step and a fallback, not assumptions.**
  - **L1 (draft starts):** only A06 and A08 start at 10:45 as drafts, because their shapes are the most stable. A19 with A20, and A21 with A22, start after the contract (11:45).
    - Rework risk: each draft carries a 20-minute rebase budget after the contract freeze.
    - Any contract change after 11:45 goes through the contract keeper, with the rebase cost stated.
  - **L2 (second merge desk):** Vlad merges only PRs that are already green in CI and passed by Luis's review agent and the contract keeper, and only A05, A13, A14 and A09.
    - A failing CI or a conflict sends the PR back to its author and never waits on Vlad's desk.
    - Vlad's review is a scope and secrets check, not a backend review; the backend review is the agent's.
  - **Proof step at 12:30:** the first two merges through Vlad's desk (A05, A13) show the flow works, timed against the 10-minute budget.
  - **Fallback if L1 or L2 fails by 13:00:** go to one desk, and apply the V28 cut line at once (A25, B06 and B08 out). That takes three merges off Luis's queue. The core then fits with one rehearsal pass and no float. This is stated in the schedule as the emergency path.
- **V32. Show the longitudinal value in the narrative.**
  - The demo states that the scope cursor and the Team's memories accumulate over time.
  - The scan only looks at what changed since the last scan, and M1 came from a correction earlier in the day.
  - The pitch names the bigger value from the original brief: team-specific, longitudinal intelligence on the diagnostics a team follows. The demo shows one turn of that loop.

## 11. Registry check: decisions V33 to V36

A second review checked the registry and challenged the demo's anchor. On 14 Nov, Claude fetched the live record through the ClinicalTrials.gov API v2:
- `lastUpdatePostDate` is 2026-11-12, `overallStatus` is RECRUITING and `hasResults` is false.
- The official title is "LEADER Neoadjuvant Screening Trial: LCMC4 Evaluation of Actionable Drivers in Early Stage Lung Cancers".
- There is one intervention, "ctDNA, tumor NGS" (DIAGNOSTIC_TEST), with `otherNames` "FoundationOne CDx" and "FoundationOne Liquid".

The reviewer saw a latest posted update of 17 July 2024 on the record-history page. That page could not be read here, so the update date is treated as unverified until 10:45 (OD2). In either case, the record never names "FoundationOne Liquid CDx". Treating "FoundationOne Liquid" as that FDA-approved product was our own assumption (D31), not something the registry states. These decisions replace V25 to V27 where they differ.

- **V33. Change the question, not the anchor's honesty.**
  - The demo signal is now: "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted."
  - No report, alert, briefing, avatar or narration says the trial studies FoundationOne Liquid CDx, or that it shows any assay's performance.
  - **The gap:** "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"
  - **The follow-up task** (when it runs; it is still the first substantial cut): search ClinicalTrials.gov for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling, and report which have posted results (at most 5). "None with posted results" is a valid answer. *(Note, V42: now "No matching results found among the records searched", with the query, the number searched and the limit. Note, V39: task execution is now stretch, not a supporting cut.)*
- **V34. No unverified alias.**
  - The hand-written alias "FoundationOne Liquid" → FoundationOne Liquid CDx (D31) is removed.
  - An extracted name that matches no seeded alias exactly stays as it appears in the source. The report lists it under **uncertainties**, for example: "The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated." It is never mapped to an approved product.
  - The aliases "Guardant360" → Guardant360 CDx and "FoundationOne" → FoundationOne CDx are removed for the same reason. Only exact FDA trade-name matches (after `normalise_name()`) resolve to a seeded Diagnostic.
- **V35. What the allowed and blocked actions are now.**
  - **Allowed:** the report files one pending knowledge update that adds NCT04712877 to the scope's evidence collection, as an early-stage plasma-plus-tissue profiling study. On approval, it is accepted into the collection; no assay record is changed.
  - **Blocked (guaranteed):** the record names "FoundationOne CDx" exactly. A proposed link from the trial to FoundationOne CDx (a tissue test outside the Team's plasma scope) is blocked by check 2.
  - **Blocked (if it occurs):** an unsupported performance or results claim in the first draft (V21).
- **V36. Anchor verification and conditional timing.**
  - At 10:45 (OD2), the live API is queried for the scan. The demo anchor is whichever in-scope early-stage trial is actually updated after the chosen cursor, with its update date, status and results verified in the response.
  - NCT04712877 is the expected candidate. If it is not updated after the cursor, the scan's real result is used and the framing follows V33, with no claim about which assay it studies.
  - **Timing is conditional.** The 20 minutes of hard float (V30) is a forecast. It holds only if the merge milestones are met, including the L2 proof at 12:30 and the 13:00 desk decision. Otherwise the emergency path applies: one desk, the V28 cut line, one rehearsal pass and no float.
- **V37. A name in the record is a mention, not proof of use.**
  - NCT04712877 lists "FoundationOne CDx" and "FoundationOne Liquid" only as alternate names (`otherNames`) of a generic intervention, "ctDNA, tumor NGS".
  - DxP records each one as **a name present in the record**, never as evidence that the trial used that product.
  - The FDA treats FoundationOne CDx (tissue) and FoundationOne Liquid CDx (plasma cfDNA) as separate devices, and the report must not merge them.
  - **The deterministic blocked case:**
    - The agent proposes linking the record's "FoundationOne CDx" mention to the Team's plasma research scope.
    - The gate blocks that link before it is filed, because the configured scope excludes the tissue assay (check 2).
    - One blocked Decision is recorded, citing the mention and the scope rule.
  - **The report:**
    - It keeps the original wording verbatim ("ctDNA, tumor NGS"; other names "FoundationOne CDx", "FoundationOne Liquid").
    - It states under uncertainties: "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample."
  - Acceptance criteria, the demo script and narration use the words "mention" or "named in the record", never "uses" or "studies", for both names.

## 12. Review of the branch: decisions V38 to V44

A review of the V25 to V37 branch produced these decisions. They win over V1 to V37 where they differ, and like the rest of this file they are approved by Luis (14 Nov). The review also recommended keeping three earlier choices as they are (recommended in review; approved by Luis (14 Nov)):
- the media kinds stay under `sam@v1`, and the backend checks Sam's grant before calling either provider;
- approval adds scope-level evidence (the scope's evidence collection, V35);
- "FoundationOne Liquid" is kept verbatim and unresolved (V34).

### The follow-up task

- **V38. Approval continues the agent's work automatically.** This replaces the "Run follow-up task" button model (V8, V9, V28 to V30 where they assumed a button).
  - **With `task_run` on:** an approved `decide_report` passes its own gated `authorise_task`. That inserts the task and its grant `task-<hex>@v1` and queues the task, which starts automatically as its own `task:` run: `initiated_by: sam`, `agent: dxp-curator`, its own grant pinned, its own gate, and stoppable with the normal stop control.
  - **Duplicate-start protection.**
    - The task ID is `derive("task_", report_id)` (AD-3, as before). The task's run ID is `derive("run_", task_id)`, the one run ID that is derived rather than random.
    - The `tasks` document moves `authorised` → `queued` → `running` → `done` | `failed` | `blocked` | `stopped`, each step after the insert a conditional (compare-and-set) update on the previous status. With the flag on, the task is inserted already `queued`; with it off, it is inserted `authorised` and never queued.
    - Starting the run is insert-if-absent on the derived run ID; only the caller whose insert succeeded starts the worker.
    - So a retried approval request, or two workers, can never start it twice. A retried approval finds the report `accepted` and returns the existing decision, task and run, completing only a step that is missing (for example a task still `authorised` while the flag is on).
  - **Crash safety: one transaction.** `tasks.authorise()` saves together, in one Atlas transaction: the `authorise_task` Decision, the `tasks` document, its grant `task-<hex>@v1` and the durable queue entry. With `task_run` on, the queue entry is the task itself in status `queued`; there is no separate queue collection. Either all of it exists or none of it does.
  - **If another run is active (the start rule).** The task stays `queued`. The run-finish path starts it: when a run ends (`runs.finish()`, or `runs.settle()` after a stop), `pipeline.run` calls `tasks.dispatch_next()` in its `finally`, which starts the oldest `queued` task if no run is `running` or `stopping`. The approval route calls the same function once, right after the transaction commits. This fits the existing admissions and settle design: `runs` still imports nothing from `tasks`, and the at-most-one-run rule (AD-16) is unchanged.
  - **Recovery.**
    - *Crash after approval, before execution.* The background sweep in `api/routes_runs.py` (started by every `GET /runs/<run_id>` and stop, AD-21) calls `tasks.dispatch_next()` after `runs.settle()`, and so does the API start hook (beside `ledger.recover_applying()`). It finds the oldest `queued` task and starts it through the same insert-if-absent derived run ID. If that run already exists but its worker never moved the task to `running` within the AD-16 stall window (10 minutes), it starts the worker again on the same run ID; the conditional `queued` → `running` update lets only one worker execute.
    - *A task stuck in `running` after an abandoned admission.* Handled like the existing abandoned-admission rule (D43): when the sweep abandons the task run's admissions, the actions they held are marked `failed` or `unknown` and never re-sent, and the task is set `failed` (`error: abandoned`) by a conditional update on `running`. It is never restarted automatically.
  - **With `task_run` off:** approval still succeeds: the evidence is accepted, the task is authorised (never queued), and the report clearly shows "Follow-up task authorised; not run". No run is started.
  - **No button.** The "Run follow-up task" button is removed everywhere. `POST /runs` no longer accepts a `task:` set from a client (403, no run); task runs start only through `tasks.dispatch_next()`.
  - **One owner for each step.** `api/routes_report_decision.py` (A24) calls `reports.decide()`, `tasks.authorise()` and, when `task_run` is on, `tasks.queue()` and `tasks.dispatch_next()` (`tasks/dispatch.py`, A24, which also holds the recovery above). `tasks/run.py` (A25) executes the task. If A25 is not merged, `task_run` stays off.
  - **The flag is read on the server.** The backend reads a new setting, `DXP_FEATURES` (in the Modal secret; same flag names), and only `DXP_FEATURES` decides whether a task is queued. `NEXT_PUBLIC_DXP_FEATURES` only controls what the web app displays.
  - **Wording.** With the flag on, the approval reads "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27). With it off: "Approved: 1 update accepted. Follow-up task authorised; not run."
- **V39. Follow-up task execution is stretch.**
  - The base forecast reaches a green loop at about 14:35, after the 14:30 gate, so A25, Story 10.9 and I3b are **stretch**, not supporting. They join only if A25 is merged and the loop is green by 14:30.
  - The supporting cut order (V28) is now: (1) the HeyGen avatar (B08); (2) the ElevenLabs briefing (B06); (3) the memory correct and revoke screen; (4) a second discovery item. Task execution is no longer a supporting cut; it is stretch.
  - Task authorisation (A24) stays core.
  - **Pitch and video rule.** Never claim or narrate completed follow-up work unless the task actually ran in that recording or demo. When it did not run, say "Follow-up task authorised; not run".

### Evidence and the report contract

- **V40. Source versions (fixes AD-25).**
  - Until now an existing `source_ref` kept its document and only gained the scope, so changed trial content was dropped.
  - **New rule:** immutable source versions plus a current-version pointer.
    - A `source_versions` collection, one document per version: `_id` = `derive("sv_", source_ref, last_update_post_date, content_hash)`, with the source's own version marker (`lastUpdatePostDate`), a content hash of the normalised `raw_text`, the `raw_text`, `evidence_text`, status fields and verbatim interventions, `fetched_at`, the run, and `previous_version_id`.
    - `source_items.current_version_id` points at the current version and moves by a conditional update on the previous pointer. `source_items` keeps a copy of the current version's fields for reading.
    - **Version pinning everywhere.** Every record that uses source content carries the exact `version_id` it used: reports and their quotes, retrieval and Vector Search results (`Retrieval.items`, `report.related[]` and both relationship quotes), Findings, proposals and value-entry Evidence, Decisions (`evidence_ref`) and audit entries. The Finding ID becomes `derive("f_", version_id, diagnostic_id)`.
    - **Invariant:** advancing `source_items.current_version_id` never changes evidence that was already reviewed or accepted. Readers of reviewed or accepted evidence follow the stored `version_id`, never the current pointer.
  - **Why a separate collection, not an embedded array:** insert-if-absent on a derived `_id` makes parallel or repeated scans idempotent with no array compare-and-set; `source_items` stays small; and each version has a stable ID that Evidence can point at.
  - When a known trial changes, discovery stores a new version, moves the pointer and treats the change as a signal (the item is processed again; `processed_at` is kept per scope and version). It never overwrites an older version.
  - **Provenance:** accepted evidence keeps pointing at the version that was reviewed.
  - Owner: A05 (`sources/load.py`, `discovery/scan.py`); A01 adds the shape and collection, and A03 the validator. I1 and I3 assert the invariant.
- **V41. The report script is core (fixes AD-30).**
  - AD-30 requires the text script with every report, but its builder was in the supporting ElevenLabs PR (B06).
  - The script builder moves into the core report-filing PR, A19+A20: `reports.script_for(report)` in `reports/script.py`. `reports.file()` stores it on the report (`script`, `script_hash`), and `GET /reports/<report_id>` returns it.
  - B06 (ElevenLabs) and B08 (HeyGen) only consume `report.script`. Cutting B06 and B08 leaves the report contract complete, with the script always shown as text on the report page (B04).
- **V42. Capped search wording.**
  - A capped search (at most 5) cannot prove that no qualifying study has posted results. Every "None with posted results" answer becomes: "No matching results found among the records searched".
  - The query, the number of records searched and the search limit are always shown.
  - `Task.result` is `{ answer, with_posted_results[], query, searched_count, limit, source_refs, related_ids }`.
  - V26 and V33 keep their original wording, with a note pointing here.
- **V43. Reports without a resolved Diagnostic.**
  - The review recommended keeping AD-27 (`diagnostic_id: null`; approval adds evidence to the scope collection) and AD-20 (Slack omits the "Open diagnostic" link) as they are (recommended in review; approved by Luis (14 Nov)).
  - Every step handles `diagnostic_id: null` without assuming a `dx_id`:
    - the report (empty `diagnostic_ids`) and the proposal (`target: { scope_id }`);
    - the five gate checks, especially check 2, which judges the `scope_id` and looks up no Diagnostic;
    - IDs and admission keys, which use `"-"` for the Diagnostic;
    - the apply transaction, which guards on the scope collection entry instead of `applied_proposal_ids` and writes no `diagnostics` document, edge or search field;
    - the Slack message, which has "Review in DxP" only, with `diagnostic_url: null`;
    - the audit and the UI, which show the scope as the target and no "Accepted knowledge" link;
    - an explicit I1 and I3 assertion.
- **V44. Rehearsal source check.**
  - A wording search cannot prove that nothing implies an unsupported claim.
  - During rehearsal, one person runs two separate checks on one complete report and its briefing or narration script:
    1. **Against the version used.** Read the report and its script side by side with the exact source version it used (its stored `version_id`), and confirm that every claim is supported by that version.
    2. **Against the live record.** Separately, compare that version with the live ClinicalTrials.gov record for the anchor. The registry may have changed since the run; a difference is reported as "changed since the run", not as an error in the report.
  - This is a rehearsal step, and part of the done rule for the demo and video stories.

- **V45. Crash between acceptance and authorisation (review of d38e5e2).**
  - **Gap.** Approval applied the evidence and marked the report `accepted`, then authorised the task in a separate transaction. A crash between the two left an accepted report with no task, and only a retried approval repaired it.
  - **Fix.** The conditional write that claims the report (`pending` → `accepting`) also stores an `approval` record: the original decision ID, request ID, Reviewer, note, correction, the intended `task_id` and `task_step: "pending"`. The unfinished work is therefore saved before the report can become `accepted`.
  - **Recovery.** `tasks.recover_authorisations()` (A24) finds accepted reports with `task_step: "pending"` and completes them without a Reviewer click:
    - it keeps the original approval's identity and the intended task;
    - it rechecks authority through the gate as it stands now, under `sam@v1`;
    - allowed: one transaction saves the Decision, task, grant and `task_step: "done"`;
    - blocked: a blocked Decision is recorded with `task_step: "blocked"`, and the report says "Follow-up task not authorised: <reason>".
  - **No duplicates.** The derived Decision and task IDs make recovery safe to repeat.
  - **Callers.** The decision route, the API start hook, the background sweep and the end of every run.
  - **Test.** A24 crashes after acceptance and before authorisation, restarts, and checks a truthful final state with no second click and no duplicate task. A second variant revokes `sam@v1` first and expects the blocked outcome.
  - **Abandoned task execution.** A run that is abandoned ends visibly as `failed`, and its partial results stay pending. This is a hackathon limitation; DxP does not resume task execution.

- **V46. Memory-creation recovery limitation, and the build rules (approved by Luis with V25 to V45).**
  - On a reject, or an approval with a correction, the `create_memory` step is not covered by V45's recovery. A crash right before it is repaired only when the Reviewer retries the decision. It promotes nothing and starts no task. This is a known hackathon limitation.
  - "Memory saved" is shown only after `memory.create()` succeeds. Until then the report shows the decision without that confirmation.
  - Build the core discovery-to-review loop first. `task_run` stays off until I3b passes.
  - The crash, retry and revocation checks (A24, I3, I3b) are implementation acceptance requirements. They are planned tests, not evidence that anything has passed.
