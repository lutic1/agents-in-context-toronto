---
title: Sprint Change Proposal, restore the discovery-agent vision
status: draft (for Luis to confirm)
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
