---
title: DxP build schedule for Saturday 14 November 2026
status: draft (forecast, not validated; follows the discovery-agent proposal, which is draft until Luis confirms it)
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/development-plan.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxP build schedule for Saturday

This schedule follows `sprint-change-proposal-2026-11-14-discovery-agent.md`, which wins over every earlier planning document. Within it, decisions V25 to V32 (section 10, the review of PR #8) win over V1 to V24, and V33 to V37 (section 11, the registry check) win over V25 to V27, and V38 to V44 (section 12, the review of the branch; draft, pending Luis's sign-off) win over V1 to V37. The schedule adopts the section 7 cuts as the baseline, except that A24 and A25 are split again (V28), and it applies the V28 cut line, the V29 media rule, the V30 float and the V31 levers. The readiness fixes D1 to D57 and the Slack decisions S1 to S13 still apply wherever that proposal does not replace them. The PR cards, with start and merge requirements and owned files, are in `development-plan.md`.

**Every time below is a forecast, not a validated run.** Cycle times come from `epics.md`; merge times are an assumption (about 10 minutes each). The milestones are where the day checks the forecast, and each has a fallback.

## Assumptions

- Hacking runs 10:45 to 17:00; no coding before 10:45 unless an organiser permits it in writing. Code freeze 16:30. R1 records the 60-second video and submits 16:30 to 16:55. The sandbox is reset 16:55 to 17:10. The live 3-minute demo starts at 17:15.
- We build on the Atlas Sandbox from the start (AD-24).
- No prepared code or assets are reused (D1). The prior collection, the FDA seed and memory M1 are all created during the event (V15); M1 comes from Sam's correction through the real UI.
- **Capacity (V19):** Luis runs up to 44 agents on his Claude plan and holds the product's keys. Vlad runs up to 22 agents (Sonnet 5.5 at high effort) on Claude Pro plus $300 of API credit; his lane runs at 1.25 times Luis's cycle times.
- **Concurrency does not remove sequential work.** Agents run side by side, but a module still waits for the modules it calls, an integration still waits for its merges, CI still takes its minutes, and a person still looks at and merges each PR. Adding agents adds PRs to review and merge; it does not add merge desks or shorten a chain. That is why this schedule is limited by the dependency chain and the merge queue, not by agent count.
- **Merges:** each merge on Luis's desk is about 10 minutes of CI plus a human look, one at a time. Vlad merges his own lane after Luis's review agent passes each PR. Each merge rebases on the latest `main`.
- **Media never gates anything (V29).** The briefing and the avatar are generated on demand from buttons on the report page; nothing renders automatically. The report, the Slack alert, the decision, the task and the rehearsal never wait on ElevenLabs or HeyGen.

## The result in one paragraph

The core loop ends at I3, "approval, promotion, authorisation and audit", 14:45 to 15:00; follow-up task execution (A25) is off the core path and is stretch (V28, V39); approval authorises the task and, only with the backend flag `task_run` on, queues it to start by itself (V38). The rehearsal runs 15:00 to 16:10. **That leaves 20 minutes of hard float at the 16:30 freeze. This is the only float figure in the plan (V30), and it is a forecast, conditional on the merge milestones (V36): the L2 proof at 12:30 and the 13:00 desk decision among them. If they are missed, the emergency path applies instead.** It rests on two levers, both treated as risks with a proof step and a fallback (V31): **L1**, only A06 and A08 start at 10:45 as drafts, each with a 20-minute rebase budget after the contract freeze; **L2**, Vlad's desk merges A05, A13, A14 and A09 only, once each is green in CI and passed by Luis's review agent and the contract keeper. With both, Luis's desk merges back to back from 12:55, the last core merge (A21+A22) lands at 14:05, I1 step 2 runs 14:05 to 14:20 and the discovery loop 14:20 to 14:45, with its first green pass forecast at 14:35. The follow-up task joins as I3b (15:00 to 15:15) only if A25 is merged by 14:30 and the loop is green by 14:30; it then uses 15 of the 20 minutes. On this forecast the loop is green at 14:35, so A25 joins only if the day runs ahead of the forecast; otherwise it is cut. If L1 or L2 fails by 13:00, the plan goes to one desk and applies the cut line at once: the **emergency path** fits the core with one rehearsal pass and no float.

## Timeline

| Time | What |
|---|---|
| 9:00 to 10:45 | Doors, breakfast, kick-off. No coding. Luis confirms the deadline, sandbox access and the clearance items (OD4), records them in `docs/clearance.md`; checks the sandbox for Vector Search and Automated Embedding (OD1) |
| 10:45 | Hacking starts. A01, A02, A03 (generating the three DxP keys into `.env`, D48), B01, and the two draft PRs A06 and A08 (lever L1). Luis queries the live ClinicalTrials.gov API, chooses the cursor and verifies the demo anchor in the response: update date after the cursor, status and results (OD2, V36). NCT04712877 is the expected candidate only. The HeyGen account check (V29, OD7) runs alongside, off the critical path: nothing waits on it |
| 11:00 | A04 deploy starts |
| 11:45 | A01 merged; contracts frozen; the contract keeper posts the diff; A06 and A08 rebase (20-minute budget each). Every other Luis PR starts, A19+A20 and A21+A22 among them. Vlad's spend checked |
| 12:05 | End of the L1 rebase budget for A06 and A08 |
| 12:10 | B01 merged; B04 (two builders), B02 and B03 start; A04 merges at 12:20 |
| 12:30 | A03 merged; B06 starts, and B08 only if the HeyGen account check passed. The L2 proof step opens on desk V |
| 12:55 to 14:15 | Luis's desk merges without a gap: A06, A24, A07+A11, A08, A10, A19+A20, A21+A22 (last core merge, 14:05), then A25 (stretch). Vlad's desk merges A05 (first proof merge), A13 (second proof merge), A14, A09, then B04 |
| 13:00 | L1 and L2 decision: keep both, or switch to the emergency path |
| 13:35 to 14:05 | I1 step 1 on the sandbox: grant, policy and scope seed; FDA seed; prior collection (13:35 to 13:55); embeddings and indexes once A19+A20 is in (13:55 to 14:05) |
| 14:05 to 14:20 | I1 step 2: the setup run on NCT05715229, Sam's correction through the deployed report page creates M1, the snapshot |
| **14:20 to 14:45** | **I1 discovery loop; first green pass forecast 14:35** |
| 14:30 | I3b gate: A25 merged and the loop green, or A25 is cut |
| 14:00 to 14:55 | Vlad's desk merges B07, B02, B06 (by 14:45), B03, B08 (by 15:00) |
| **14:45 to 15:00** | **I3: approval, promotion, task authorisation and audit;** S1 (briefing) and S3 (memory correct and revoke) checked |
| 15:00 to 15:15 | I3b (stretch), only if the 14:30 gate passed: the queued follow-up task starts by itself and is gated |
| 15:00 to 16:10 | A16: reset, pass 1 = core acceptance 15:10 to 15:35 (S2 avatar checked just before), reset, pass 2 15:45 to 16:00, reset for the video 16:00 to 16:10. If I3b ran: 15:15 to 16:25 |
| 16:30 | Code freeze. 20 minutes of hard float if the merge milestones held (15 of them used if I3b ran); none on the emergency path |
| 16:30 to 16:55 | R1: record the 60-second video and submit; add the video link to the README |
| 16:55 to 17:10 | Reset for the live demo |
| 17:15 | Live 3-minute demo |

## Inputs to the computation

Cycle times from `epics.md` (agent cycle time for each story; a bundle runs its stories with separate builders, so it takes about as long as its longest story). "Ready" means reviewed and green, waiting for its merge slot.

| PR | Cycle basis | Start | Ready |
|---|---|---|---|
| A01 | 1.0 h | 10:45 | 11:35 |
| A02 | 1.0 h | 10:45 | 11:45 |
| A03 | 1.5 h (9.2), drafting from 10:45 | 10:45 | 12:10 |
| A04 | 1.0 h | 11:00 | 12:00 |
| A06 | 2.1 h (1.6), with 9.3 and 10.7 by parallel builders; draft (L1) inside its 20-minute rebase budget | 10:45 | 12:55 |
| A08 | 2.0 h with two builders; draft (L1) inside its 20-minute rebase budget; tuned once live trials are reachable | 10:45 | 13:10 |
| A05 | 1.2 h (10.1), with 1.4 in parallel | 11:45 | 12:55 |
| A07+A11 | 1.2 h (9.5, 9.6), with 9.1 in parallel | 11:45 | 13:00 |
| A24 | 1.2 h (10.8) | 11:45 | 13:00 |
| A25 | 1.2 h (10.9) | 11:45 | 13:00 |
| A13 | 1.5 h (1.2 plus the snapshot script) | 11:45 | 13:15 |
| A14 | 1.5 h (2.3 value review, A18 read model) | 11:45 | 13:15 |
| A09 | 1.75 h (9.4, slightly simpler with Slack) | 11:45 | 13:30 |
| A10 | 1.75 h | 11:45 | 13:30 |
| A19+A20 | 2.0 h (10.3), with 10.2 and 10.4 in parallel; starts after the contract (V31) | 11:45 | 13:45 |
| A21+A22 | 2.0 h (10.6), with 10.5 in parallel; starts after the contract (V31) | 11:45 | 13:45 |
| B01 | 1.0 h × 1.25 | 10:45 | 12:00 |
| B04 | 4 h (10.10) with two builders × 1.25 ≈ 1.6 h after B01 | 12:10 | 13:45 |
| B02 | about 1.65 h × 1.25 | 12:10 | 14:15 |
| B03 | about 1.9 h × 1.25 (V14 additions) | 12:10 | 14:35 |
| B06 | 1.5 h × 1.25 | 12:30 | 14:25 |
| B08 | about 1.75 h × 1.25 (async render and its states) | 12:30 | 14:45 |
| B07 | 1.0 h × 1.25 | 12:45 | 14:00 |

Integration time: I1 step 1 about 30 minutes (data about 20 minutes, then the index build about 10 minutes once A19+A20 is in), I1 step 2 15 minutes (about 10 minutes plus 5 for the snapshot), I1 loop 25 minutes (about 15 to the first green pass, then one round of fixes), I3 15 minutes, I3b 15 minutes. A16: three resets and two passes, 70 minutes. Reset forecast 10 minutes each (OD6).

## The merge queue

Luis's desk (desk L), one merge at a time, about 10 minutes each. It holds 12 merges: 11 core and A25 (stretch).

| Slot | PR | Ready | Waited | Why it is here |
|---|---|---|---|---|
| 11:35 to 11:45 | A01 | 11:35 | 0 | contract freeze |
| 11:45 to 11:55 | A02 | 11:45 | 0 | |
| 12:10 to 12:20 | A04 | 12:00 | 10 min | merges after B01 (12:10, D39) |
| 12:20 to 12:30 | A03 | 12:10 | 10 min | |
| 12:30 to 12:55 | idle | | | nothing on desk L is ready |
| 12:55 to 13:05 | A06 | 12:55 | 0 | head of the late queue; A24, A14 and A19+A20 merge after it |
| 13:05 to 13:15 | A24 | 13:00 | 5 min | merges after A06; its reject path creates M1 in I1 step 2 |
| 13:15 to 13:25 | A07+A11 | 13:00 | 15 min | |
| 13:25 to 13:35 | A08 | 13:10 | 15 min | merges after A05 (13:05); I1 step 1 needs it for the prior collection |
| 13:35 to 13:45 | A10 | 13:30 | 5 min | fills the slot before the two late bundles are ready |
| 13:45 to 13:55 | A19+A20 | 13:45 | 0 | first of the two late bundles, so the index build starts at 13:55 |
| 13:55 to 14:05 | A21+A22 | 13:45 | 10 min | merges after A19+A20; **last core merge** |
| 14:05 to 14:15 | A25 | 13:00 | 65 min | stretch (V39); merges after A24, A07+A11 and A19+A20; must be merged by 14:30 to join I3b |

From 12:55 to 14:15 the desk is saturated: eight merges back to back. **Any merge that takes 20 minutes instead of 10 moves every later slot, I1 step 2 and the loop by 10 minutes,** and the minutes come out of the 20 minutes of hard float.

Vlad's desk (desk V), his own PRs and four of Luis's leaf PRs (lever L2, V31). Vlad merges a Luis PR only when it is already green in CI and passed by Luis's review agent and the contract keeper. His look is a scope and secrets check, not a back-end review; the back-end review is the agent's. A failing CI or a conflict sends the PR back to its author and never waits on desk V.

| Slot | PR | Ready |
|---|---|---|
| 12:00 to 12:10 | B01 | 12:00 |
| 12:55 to 13:05 | A05 (first proof merge) | 12:55 |
| 13:15 to 13:25 | A13 (second proof merge) | 13:15 |
| 13:25 to 13:35 | A14 (merges after A06) | 13:15 |
| 13:35 to 13:45 | A09 (merges after A03) | 13:30 |
| 13:45 to 13:55 | B04 (deployed about 14:00) | 13:45 |
| 14:00 to 14:10 | B07 | 14:00 |
| 14:15 to 14:25 | B02 | 14:15 |
| 14:25 to 14:35 | B06 (must merge by 14:45) | 14:25 |
| 14:35 to 14:45 | B03 | 14:35 |
| 14:45 to 14:55 | B08 (must merge by 15:00) | 14:45 |

Fix PRs from I1, I3 and A16 go first in the owning desk's queue.

### The levers are risks (V31)

**L1, draft starts.** Only A06 and A08 start at 10:45 as drafts, because their shapes are the most stable. A19+A20 and A21+A22 start after the contract, at 11:45. Each draft carries a 20-minute rebase budget after the contract freeze, so the L1 result is known by 12:05. Any contract change after 11:45 goes through the contract keeper in its own PR, with the rebase cost it imposes stated in the PR.

**L2, the second merge desk.** Desk V takes only A05, A13, A14 and A09, under the conditions above.

**Proof step.** Desk V opens at 12:30 with its checklist (CI green, review agent passed, contract keeper passed, scope and secrets checked). The first two merges of Luis's PRs through it, A05 (12:55 to 13:05) and A13 (13:15 to 13:25), are timed against the 10-minute budget. A05 and A13 cannot be ready before 12:55 and 13:15, so at 13:00 the proof rests on A05's merge in progress, and A13's merge completes it at 13:25.

**Fallback.** If L1 or L2 fails by 13:00 (a draft over its rebase budget, or A05's merge failing or clearly over budget), switch at once to the emergency path below. If A13's merge fails the proof at 13:25, switch then; the later switch lands inside the emergency path's timings, because A05 and A13 are already merged.

### The emergency path (one desk, cut line applied)

One desk, Luis's, merges every remaining PR, Vlad's included. The V28 cut line is applied at once: A25, B06 and B08 are out (flags `task_run`, `briefing` and `avatar` off; their files stay A01's stubs). That takes three merges off the queue. Forecast, with the switch at 13:00:

| Slot | PR |
|---|---|
| 12:55 to 13:05 | A06 |
| 13:05 to 13:15 | A05 |
| 13:15 to 13:25 | A08 |
| 13:25 to 13:35 | A13 (I1 step 1 data from 13:35) |
| 13:35 to 13:45 | A24 |
| 13:45 to 13:55 | A19+A20 (indexes 13:55 to 14:05) |
| 13:55 to 14:05 | A21+A22 |
| 14:05 to 14:15 | A07+A11 |
| 14:15 to 14:25 | A09 |
| 14:25 to 14:35 | A10 |
| 14:35 to 14:45 | B04 (deployed about 14:50) |
| 14:45 to 14:55 | A14 (the accepted knowledge route; the demo alert sends no "Open diagnostic" link, V43) |
| 14:55 to 15:25 | B02, B03, B07, behind any fix PR |

Then: I1 step 2 14:50 to 15:05; the I1 loop 15:05 to 15:30; I3 (approval, promotion, authorisation and audit) 15:30 to 15:45; reset 15:45 to 15:55; **one rehearsal pass**, which is core acceptance, 15:55 to 16:20; reset for the video 16:20 to 16:30; freeze 16:30. **On the emergency path there is no float and one rehearsal pass.** B02 and B03 must merge by 15:55 for the pass. A06 and A08 can each run up to about 25 minutes late without moving this path, because other ready PRs fill the early slots; any delay after 13:45 moves the freeze-time reset one for one.

**Without the levers and without the switch.** Without L1, A06 and A08 are ready about 13:50 and 13:45, the last core merge moves to about 14:35, the loop ends about 15:15, I3 about 15:30, and a two-pass rehearsal would run past the freeze. Without L2, desk L also carries A05, A13, A14, A09 and Vlad's PRs, and the last core merge moves to about 14:55. Either way the plan takes the emergency path.

## The critical path

### Main chain

```
10:45  A01 contract ..................................................... merged 11:45
10:45  A06 and A08 drafted (L1; 20-minute rebase budget each from 11:45)
11:45  every other Luis PR starts, A19+A20 and A21+A22 among them (ready 13:45)
12:55  desk L saturated: A06 → A24 → A07+A11 → A08 → A10 → A19+A20 → A21+A22
13:55  A19+A20 merged; embeddings and indexes build ........................... 14:05
14:05  A21+A22 merged (last core merge); B04 deployed since about 14:00 (desk V)
14:05  I1 step 2: setup run on NCT05715229, Sam's rejection creates M1 ......... 14:15
14:15  snapshot with M1 (OD6) ................................................. 14:20
14:20  I1 discovery loop: first green pass forecast 14:35, slot ends ............ 14:45
14:45  I3 approval → promotion → task authorisation → audit ................... 15:00
15:00  A16: reset, pass 1 (core acceptance) 15:10–15:35, reset,
       pass 2 15:45–16:00, reset for the video 16:00 .......................... 16:10
16:30  freeze: 20 minutes of hard float (conditional on the merge milestones, V36)
16:30  R1 16:30–16:55; reset 16:55–17:10; live demo 17:15
```

Optional branch (V30):

```
14:30  I3b gate: A25 merged (forecast 14:15) and loop green (forecast 14:35)
15:00  I3b (stretch): the queued follow-up task starts by itself, gated, answers the gap ... 15:15
15:15  A16 as above, shifted .................................................. 16:25
16:30  freeze: 15 of the 20 minutes used
```

The longest chain runs through the merge queue: A19+A20 and A21+A22 start after the contract and are ready at 13:45, and both feed I1 step 2 (the indexes and the reject path that creates M1).

### Near-critical chains

| Chain | Ready or done | Needed by | Status |
|---|---|---|---|
| Desk L queue, 12:55 to 14:05 | last core merge 14:05 | I1 step 2 at 14:05 | critical |
| A19+A20 → index build | indexes queryable 14:05 | I1 step 2 at 14:05 | critical |
| B04 (Vlad, two builders) → merged 13:55 → deployed about 14:00 | 14:00 | I1 step 2 (Sam's correction through the UI, V15) at 14:05 | near-critical; a late B04 moves step 2 one for one |
| I1 loop first green pass | 14:35 | the end of the I1 slot, 14:45; the I3b gate at 14:30 | on forecast, the I3b gate is missed |
| A25 | merged 14:15 | the I3b gate at 14:30 | stretch (V39) |
| Rehearsal end | 16:10 | freeze 16:30 | **20 minutes of hard float, the only float; conditional on the merge milestones (V36)** |
| I1 step 1 data (A03, A05, A06, A08, A13 merged by 13:35) | 13:55 | the index build at 13:55 | critical |
| A06 draft | ready 12:55 | its slot 12:55 | critical (head of the queue) |
| A08 draft | ready 13:10 | its slot 13:25 | feeds step 1 |
| A05, A13 (desk V) | merged 13:05, 13:25 | step 1 at 13:35; the L2 proof | feeds step 1 |
| A14, A09 (desk V) | merged 13:35, 13:45 | the loop (A14's accepted knowledge link) and step 2 (A09) | feeds I1 |
| A04 deploy and secrets | 12:20 | B04 deploy and the Slack links at 14:00 | off the critical path |
| B02 Run console | 14:25 | A16 pass 1 at 15:10 (I1 starts runs through the API) | needed for the rehearsal |
| B03 Audit view | 14:45 | A16 pass 1 at 15:10 | needed for the rehearsal |
| B06 briefing | 14:35 | the 14:45 cut rule | supporting |
| B08 avatar | 14:55 | the 15:00 cut rule, then S2 before pass 1 | supporting; render time (OD7) is separate and never waited on |
| B07 README, script | 14:10 | R1 at 16:30 | off the critical path |

Read honestly:

- **The float is 20 minutes of hard float at the 16:30 freeze.** No other float figure applies. It is a forecast and holds only if the merge milestones are met, including the 12:30 L2 proof and the 13:00 desk decision; otherwise the emergency path applies, with no float (V36). If I3b runs, it uses 15 of those 20 minutes.
- **The merge queue is the real critical path.** Eight back-to-back merges on Luis's desk, and the two bundles that start after the contract, feed I1 step 2 at 14:05.
- **The I3b gate is likely missed.** The loop's first green pass is forecast at 14:35, after the 14:30 gate, so follow-up task execution joins only if the day runs ahead of the forecast. That is why it is stretch (V39), not a supporting cut: the core (approval, promotion and the task's authorisation) does not depend on it, and the base plan, the pitch and the video assume "Follow-up task authorised; not run".
- **M1 puts Vlad's lane on the critical path.** M1 must come from Sam's correction through the real report page (V15), so B04 deployed is a start requirement of I1 step 2, not only of I3.
- **L1 and L2 have a cost, and a proof.** A draft over its 20-minute rebase budget, or a failed proof merge on desk V, triggers the emergency path; it is not absorbed silently.

## Demo order (V16 as amended by V25 to V37)

What A16 rehearses, R1 records and the live demo shows. The wording rules of V33 and V37 apply to every step: "FoundationOne CDx" and "FoundationOne Liquid" are names **mentioned in the record** (alternate names of the generic intervention "ctDNA, tumor NGS"), never assays the trial "uses" or "studies", and nothing implies any assay's performance.

1. Start the discovery run on the scope "Plasma ctDNA genotyping assays in NSCLC". The scan looks only at what changed since the last scan (the scope cursor, V32).
2. The scan finds the anchor (expected NCT04712877, verified at 10:45): a new trial signal, "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted."
3. Blocked before filing: the proposed link of the record's "FoundationOne CDx" mention to the plasma scope (check 2, guaranteed, one blocked Decision citing the mention and the scope rule); and, if draft 1 wrote it, an unsupported performance or results claim (V21).
4. The report is filed as pending: the intervention wording verbatim; under uncertainties, the ambiguous intervention field and the unresolved name "FoundationOne Liquid" (V34); related evidence with checked quotes; the gap, "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"; one pending update, adding the trial to the scope's evidence collection; M1's effect, from a correction made earlier in the day.
5. The Slack alert arrives; "Review in DxP" opens the report.
6. Media only if its check passed: the script is always shown as text; play the briefing or the avatar if ready (V29).
7. Stop shown honestly: on the follow-up task's run if I3b ran and it started by itself, otherwise on a second discover item with items remaining.
8. Sam approves: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." with `task_run` on, or "Approved: 1 update accepted. Follow-up task authorised; not run." with it off (V38). No assay record changes (V35); the update targets the scope's evidence collection, with no Diagnostic link (V43).
9. Only if I3b ran (stretch, V39): the queued follow-up task starts by itself (no button, V38); it is gated, answers the gap (at most 5 records searched; "No matching results found among the records searched" is valid, shown with the query, the number of records searched and the limit, V42), and its findings stay pending. If it did not run, the narration says "Follow-up task authorised; not run" and claims no completed follow-up work (V39).
10. The Audit view answers: "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"
11. Close (V32): the cursor and the Team's memories accumulate; this is one turn of team-specific, longitudinal intelligence on the diagnostics a team follows.

**Rehearsal source check (V44), in A16 pass 1.** One person takes one complete report and its briefing or narration script and (a) reads them side by side with the exact source version the report used (its stored `version_id`), confirming that every claim is supported by that version; then (b), separately, compares that version with the live ClinicalTrials.gov record for the anchor. A difference in (b) is recorded as "changed since the run", not as an error in the report. The video is not recorded until both checks pass.

## Who does what

**Luis (up to 44 agents, the product's keys):** A01 to A10 with the bundles, A13, A14, A16, A19+A20, A21+A22, A24, A25, I1 and I3 (with I3b); merges the 12 PRs on desk L; R1 with Vlad; the live-demo reset; `docs/clearance.md`; runs the review agent on Vlad's lane.

**Vlad (up to 22 agents, Sonnet 5.5 at high effort):** B01, B02, B03, B04 (two builders), B06, B07, B08; merges his lane and four of Luis's leaf PRs on desk V (L2, under the V31 conditions); R1 with Luis.

- Vlad's PRs need the Atlas Sandbox connection string; Luis shares it through `.env`, never in the repository. Vlad's lane needs no Slack, ElevenLabs or HeyGen key: those calls run in the back end on Modal.
- If B04 is late, Luis's agents add a third builder to it at 13:15; it is on the critical path. B02 and B03 are core for the rehearsal: if either is not merged by 14:45, Luis's agents take it over.
- **Review of Vlad's lane.** One review agent run by Luis checks each of Vlad's PRs against its acceptance criteria, D1 and for secrets, at about 15 minutes a PR; B04 is reviewed first. If a PR waits more than 20 minutes, Luis starts a second review agent.
- **Vlad's credit.** Seven PRs and up to 22 agents. [ASSUMPTION: about $5 an agent-hour on the API.] Roughly 25 to 30 agent-hours is about $125 to $150, inside the $300. Check the spend at 11:45: above $50 an hour, cap the builders and stop B08 first.
- **Product keys (Luis's).** Anthropic: set a spend alert at $50 (the prior collection's extraction, the setup run, tuning, I1, I3 and two rehearsal passes). ElevenLabs: on demand only, from the "Generate briefing" button (OD3). HeyGen: on demand only; for the demo, one render for the demo report, requested as soon as it is filed (V29), on a paid plan or funded API wallet (OD7).

## Schedule by PR

| PR | Owner | What | Start | Ready | Merged | Path |
|---|---|---|---|---|---|---|
| A01 | Luis | Contract, stubs only | 10:45 | 11:35 | 11:45 (L) | critical |
| A02 | Luis | Registry, identity, exact trade-name matching (no hand-written aliases, V34) | 10:45 | 11:45 | 11:55 (L) | feeds A06 |
| A03 | Luis | Grants, policies including claim policies, the research scope, validators | 10:45 | 12:10 | 12:30 (L) | feeds A06 |
| B01 | Vlad | Web skeleton, shell, flags, player stubs | 10:45 | 12:00 | 12:10 (V) | feeds B04 |
| A04 | Luis | Deploy and secrets, including ElevenLabs and HeyGen | 11:00 | 12:00 | 12:20 (L) | off the critical path |
| A06 | Luis | Ledger, gate, apply, claim checks (draft, L1) | 10:45 | 12:55 | 13:05 (L) | critical (queue head) |
| A05 | Luis | Discovery scan, prior collection, setup item | 11:45 | 12:55 | 13:05 (V, proof merge 1) | feeds I1 step 1 |
| A24 | Luis | Report decision, promotion, task authorisation | 11:45 | 13:00 | 13:15 (L) | critical (the reject path makes M1) |
| A07+A11 | Luis | Runs, stop, audit API with V14 | 11:45 | 13:00 | 13:25 (L) | critical (queue) |
| A13 | Luis | FDA seed, snapshot and reset | 11:45 | 13:15 | 13:25 (V, proof merge 2) | feeds I1 step 1 |
| A08 | Luis | Extraction (draft, L1) | 10:45 | 13:10 | 13:35 (L) | critical (queue) |
| A14 | Luis | Read model, accepted knowledge, value review | 11:45 | 13:15 | 13:35 (V) | feeds the accepted knowledge link (I1) |
| A10 | Luis | The run | 11:45 | 13:30 | 13:45 (L) | critical (queue) |
| A09 | Luis | Slack notifier, one alert per report | 11:45 | 13:30 | 13:45 (V) | feeds I1 step 2 |
| A19+A20 | Luis | Retrieval, relationships, report with its gap | 11:45 | 13:45 | 13:55 (L) | critical |
| B04 | Vlad | Report page, reports list, accepted knowledge view | 12:10 | 13:45 | 13:55 (V) | near-critical |
| A21+A22 | Luis | Reviewer memory | 11:45 | 13:45 | 14:05 (L) | critical (last core merge) |
| B07 | Vlad | README, submission text, video script | 12:45 | 14:00 | 14:10 (V) | off the critical path |
| A25 | Luis | Follow-up task execution | 11:45 | 13:00 | 14:15 (L) | stretch (V39); joins I3b only if merged by 14:30 and the loop is green by 14:30 |
| B02 | Vlad | Run console | 12:10 | 14:15 | 14:25 (V) | needed by A16 pass 1 |
| B06 | Vlad | ElevenLabs briefing, on demand (`briefing` flag) | 12:30 | 14:25 | 14:35 (V) | supporting; out if not merged by 14:45 |
| B03 | Vlad | Audit view with V14 | 12:10 | 14:35 | 14:45 (V) | needed by A16 pass 1 |
| B08 | Vlad | HeyGen avatar video, on demand (`avatar` flag) | 12:30 | 14:45 | 14:55 (V) | supporting; out if not merged by 15:00; built only if the 10:45 account check passed |
| I1 | Luis | Setup (data 13:35 to 14:05; M1 and snapshot 14:05 to 14:20), loop 14:20 to 14:45 | 13:35 | | 14:45 | critical |
| I3 | Luis | Approval, promotion, task authorisation and audit | 14:45 | | 15:00 | critical |
| I3b | Luis | Follow-up task execution (optional, same branch as I3) | 15:00 | | 15:15 | stretch (V39); only if the 14:30 gate passed |
| A16 | Luis | Rehearsal: pass 1 core acceptance, pass 2, video reset | 15:00 (15:15 with I3b) | | 16:10 (16:25 with I3b) | critical |
| R1 | Luis and Vlad | Record and submit | 16:30 | | 16:55 | critical |
| Reset | Luis | Reset for the live demo | 16:55 | | 17:10 | critical |

Cut and not scheduled: A12, A15, B05, A17. Folded: A18 into A14, A23 into A06, I2 into A16 pass 1. Split again (V28): A24 and A25.

## Dependencies for the integrations

| Step | Depends on | Does not depend on |
|---|---|---|
| I1 step 1 (data) | A03, A04, A05, A06, A08, A13; A19+A20 for the embeddings and indexes | any screen; A09, A10, A21+A22, A24, A25 |
| I1 step 2 (M1, snapshot) | step 1, A07+A11, A09, A10, A21+A22, A24 (its reject path creates the memory), B04 deployed | A25, B02, B03, B06, B08 |
| I1 loop | step 2's snapshot | A25, B02, B03 (runs are started through the API), B06, B08 |
| I3 | I1 green; A24, B04 (already in) | A25, B02, B03, B06, B08 |
| I3b | I3; A25 merged by 14:30; the loop green by 14:30; backend flag `task_run` on (`DXP_FEATURES`) | B06, B08 |
| A16 | I3 (and I3b if it ran); B02 and B03 for pass 1; A13's reset and I1's snapshot | A25, B06 and B08 (they join only if their checks passed) |
| R1 | A16 (including the video reset), B07 | any supporting item |
| Live-demo reset | A13's script, I1's snapshot | anything else |
| S1 briefing | B06 merged by 14:45, a filed report | |
| S2 avatar | B08 merged by 15:00, a filed report (its script is core, V41), a HeyGen render that finished (OD7) | |
| S3 memory correct and revoke | A21+A22, B04's memory panel, I3 | |

## Milestones and fallback triggers

Cuts are triggered by a missed milestone, not decided in advance. No core PR is ever replaced by a stub, and the demo never names a stub (D37, NFR5).

| By | Check | If missed |
|---|---|---|
| 10:45 | Cursor chosen; the demo anchor verified in the live API response: update date after the cursor, status, results (OD2, V36; NCT04712877 is the expected candidate); sandbox Vector Search and Automated Embedding checked (OD1); the HeyGen account check (paid plan or funded wallet, key works, no watermark; V29, OD7), off the critical path | OD2: the anchor is whichever in-scope early-stage trial the scan really returns; its headline, gap and narration follow V33 from its own fields, with no claim about which assay it studies; tell B07 and A16. OD1: set `DXP_EMBEDDING` to `voyage` (if cleared) or `none` before A19+A20 freezes its config. HeyGen check fails: B08 is not built; Vlad's B08 builders move to B04 |
| 11:45 | A01 merged, contracts frozen; the A06 and A08 drafts start their rebase; Vlad's spend checked | Hold other merges; everything slips one for one. Spend above $50 an hour: cap Vlad's builders, stop B08 |
| 12:05 | A06 and A08 rebased inside their 20-minute budgets (L1) | L1 has failed: the drafts keep building, and the 13:00 decision takes the emergency path |
| 12:20 | A04: deployed on the sandbox; every secret set (`DXP_BASE_URL`, `SLACK_WEBHOOK_URL`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY`); OD1 and OD6 results recorded | One agent fixes the deploy; the build continues locally against the sandbox. Without `DXP_BASE_URL` the notifier refuses to start |
| 12:30 | L2 proof step opens: desk V's checklist ready; A05 and A13 passing Luis's review agent and the contract keeper as they finish | Desk V not ready: L2 has failed; the 13:00 decision takes the emergency path |
| **13:00** | **L1 and L2 decision.** L1 held (12:05) and A05's merge on desk V is green and on pace | **Emergency path:** one desk; A25, B06 and B08 out at once (flags `task_run`, `briefing`, `avatar` off); one rehearsal pass, no float (see "The emergency path") |
| 13:05 | A06 merged (head of the late queue) | Every later slot on desk L slips one for one. The late PR gets more builders; B08 stops to free attention |
| 13:15 | FDA list fetched and parsed (A13) | Seed only the Diagnostics the scope and the prior collection name, typed from the FDA page; Luis tells B07 |
| 13:25 | A13 merged through desk V inside the 10-minute budget (second proof merge) | Switch to the emergency path now; its timings still hold |
| 13:35 | I1 step 1's data PRs merged (A03, A05, A06, A08, A13) | Step 1 starts with what has merged; the index build starts as soon as A19+A20 is in |
| 14:05 | Every core PR merged (A21+A22 last), B04 deployed, indexes queryable (OD1) | Indexes not queryable: switch to `DXP_EMBEDDING=none`; every screen and the video say "related by text search". A core PR late: stop B06 and B08 work; everyone on the late PR. Each minute late comes out of the 20 minutes of hard float |
| 14:20 | M1 created by Sam through the UI and the snapshot taken (OD6) | If `mongodump` fails, record it: every reset reruns the setup, about 30 minutes with Sam's correction, so A16 drops pass 2 and its reset |
| **14:30** | **I3b gate (stretch): A25 merged and the loop green** | **A25 is cut:** the backend flag `task_run` stays off (`DXP_FEATURES`); the task stays authorised and the report shows "Follow-up task authorised; not run"; I3 ends at 15:00 |
| **14:35** | **Loop first green pass (I1), with the V35 and V37 assertions: discovery of the anchor → the proposed link of the record's "FoundationOne CDx" mention to the plasma scope blocked by check 2 (guaranteed; the "showed" claim block recorded if draft 1 writes it, V21) → report filing the one allowed update (the trial added to the scope's evidence collection), the intervention wording verbatim, the ambiguity in uncertainties, a relationship with two checked quotes, the gap and M1's effect from the two gated drafts → Slack alert whose link opens the report** | Stop all supporting work; everyone fixes the loop. Cut B08 (flag `avatar` off) |
| 14:45 | I1 slot ends green; B06 merged | Not green: cut B06 (flag `briefing` off) and, if the second discovery item is what fails and A25 is still in, demo the first only. B06 not merged: it drops out |
| **15:00** | **I3: approval, promotion, task authorisation and audit; S1 and S3 checked; B08 merged** | Memory correct or revoke fails: cut the memory correction and revoke UI (flag `memory_edit` off; creation and use stay). B08 not merged: it drops out. I3 itself not green: the rehearsal starts late, minute for minute out of the hard float |
| 15:10 | S2: an on-demand HeyGen render reached `ready` on the sandbox | Flag `avatar` off |
| 15:15 | I3b passed (only if it ran) | Flag `task_run` off; the rehearsal starts at once |
| 15:35 | A16 pass 1, core acceptance, passed, including the V44 source check (15:50 if I3b ran) | Rehearse and record only what passed; drop pass 2 and use its slot for one fix and a rerun |
| **16:10** | **Rehearsal ended and the sandbox reset for the video** (16:25 if I3b ran) | Use the remaining minutes only for the reset; never fix during it |
| 16:30 | Code freeze | R1 records what works on the reset sandbox; the video names only behaviour shown |
| 16:55 | Submitted (R1) | Submit what exists |
| 17:10 | Sandbox reset for the live demo | Start the live demo with a new run; old Slack alerts stay in the channel and are told apart by action ID |

### The core cut line (V28)

**Core, never cut:** discovery; an evidence relationship with quotes; a memory changing the report; a policy block; the Slack notification opening the report; the human decision (approve with promotion, or reject or correct with a memory); the audit trail; stop. **Core, but cheap:** the recommended task and its authorisation, a record created at approval (A24).

### Supporting cut order

If a milestone slips, cut in this order. Nothing else may be cut. Follow-up task execution (A25) is no longer in this list: it is stretch (V39) and joins only through the 14:30 I3b gate.

1. **B08, the HeyGen avatar.** Flag `avatar` off; the player is hidden; `briefing.render_avatar` stays A01's stub if B08 never merged.
2. **B06, the ElevenLabs briefing.** Flag `briefing` off; the player is hidden; `briefing.generate` stays A01's stub if B06 never merged. Also out if not merged by 14:45.
3. **The memory correct and revoke screen.** Flag `memory_edit` off. Memory creation (M1) and use (its effect in the report) stay: they are core.
4. **A second discovery item.** The demo shows the anchor (expected NCT04712877) only. Stop is core, so this cut is allowed only while A25 is in and stop can be shown on the task's run; if A25 is already cut, the second item stays and carries the stop.

Each cut leaves every core dependency intact:

| Cut | What refers to it | Why core still works |
|---|---|---|
| B08 | The report page's avatar player and its "Render avatar" button | Hidden by flag; the route stays A01's 501 if B08 never merged; nothing calls HeyGen automatically (V29) |
| B06 | The briefing player and its "Generate briefing" button | Hidden by flag; the script stays on every report as text (core, V41) |
| Memory correct and revoke screen | B04's memory panel controls | Hidden by flag; the routes exist and are supporting; M1 creation and retrieval are untouched |
| A25, task execution (stretch, not a supporting cut) | A24's queueing and `tasks.dispatch_next()` (inactive while `task_run` is off); A10's `task:` handoff; B02's "Follow-up task" label | Backend flag `task_run` off: the task is authorised, never queued, and the report shows "Follow-up task authorised; not run"; `tasks.run` stays A01's stub if A25 never merged; no `task:` run is started. There is no start button to hide (V38) |
| Second discovery item | The scan's later results | The first item carries every V16 step; stop moves to the task's run (only while A25 is in) |

## Who owns which files

Extra agents only help if two of them never edit the same file. A01 creates the stub files listed in its card and hands each to the PR that finishes it; after that, each file has exactly one owner (D15, D36), as listed in each card of `development-plan.md` and in the spine's source tree. A bundle owns its files as one PR. Cut PRs (A12, A15, B05, A17) own nothing. A change to another PR's file, including a fix found in I1, I3 or A16, goes in a small PR reviewed by that file's owner.

| Files | Owner |
|---|---|
| `backend/pyproject.toml`, `uv.lock`, `tests/conftest.py`, `.env.example`, `api/app.py`, `api/models.py`, `store/` (not `store/schemas/`), package `__init__.py` files no one else owns (including `discovery/`, `retrieval/`, `reports/`, `memory/`, `tasks/`, `briefing/`), `tools/gen_types.sh`, `web/lib/types.ts` | A01 |
| `schema/registry.py`, `identity/` | A02 |
| `store/schemas/`, `gate/policy_sets.py`, `gate/seed.py`, `gate/seed_data/` (grants, policies, the research scope), `api/auth.py`, `api/routes_grants.py` | A03 |
| `backend/modal_app.py`, `.github/workflows/`, `web/vercel.json`, `docs/deploy.md` | A04 |
| `discovery/scan.py`, `sources/ctgov.py`, `sources/load.py`, `sources/selected.json`, `pipeline/prior.py`, `api/routes_scopes.py` | A05 |
| `gate/__init__.py`, `gate/checks.py`, `gate/claims.py`, `gate/decisions.py`, `ledger/__init__.py`, `ledger/file.py`, `ledger/types.py`, `ledger/apply.py` | A06 |
| `runs/`, `api/routes_runs.py`, `search/audit.py`, `api/routes_audit.py`, `api/routes_actions.py` | A07+A11 |
| `llm/` (not `llm/prompts/relate.*`, `llm/prompts/report.*`), `evidence/` | A08 |
| `actions/`, `api/routes_resolve.py` | A09 |
| `pipeline/` (not `prior.py`) | A10 |
| `sources/fda_cdx.py`, `ledger/seed.py`, `api/routes_teams.py`, `scripts/reset_demo.py` | A13 |
| `search/readmodel.py`, `ledger/review.py`, `api/routes_diagnostics.py`, `api/routes_proposals.py`, `api/routes_review.py` | A14 |
| `retrieval/embed.py`, `retrieval/indexes.py`, `retrieval/related.py`, `reports/relate.py`, `reports/draft.py`, `reports/file.py`, `reports/script.py` (V41), `llm/prompts/relate.*`, `llm/prompts/report.*`, `api/routes_reports.py` | A19+A20 |
| `memory/store.py`, `memory/retrieve.py`, `api/routes_memories.py` | A21+A22 |
| `reports/decide.py`, `tasks/authorise.py`, `tasks/dispatch.py` (V38), `gate/grants.py`, `api/routes_report_decision.py` | A24 |
| `tasks/run.py` | A25 |
| `docs/demo-and-reset.md` | A16 |
| `backend/tests/<id>/` | the PR with that ID (A24: `tests/a24/`, A25: `tests/a25/`, I1: `tests/i1/`, I3 and I3b: `tests/i3/`) |
| `docs/clearance.md` | Luis |
| `web/` including `package.json`, `lib/api.ts`, `lib/features.ts`, `lib/format.ts`, `components/shell/`; not the paths below | B01 |
| `web/app/runs/page.tsx`, `web/app/runs/[run_id]/page.tsx`, `web/components/run-console/` | B02 |
| `web/app/runs/[run_id]/audit/`, `web/components/audit/` | B03 |
| `web/app/reports/` (not the `briefing/` and `avatar/` folders), `web/app/diagnostics/`, `web/components/report/`, `web/components/report-decision/`, `web/components/memory-panel/` | B04 |
| `briefing/audio.py`, `api/routes_briefing.py`, `web/app/reports/[report_id]/briefing/` | B06 |
| `briefing/avatar.py`, `api/routes_avatar.py`, `web/app/reports/[report_id]/avatar/` | B08 |
| `README.md`, `docs/video-script.md`, `docs/submission.md` | B07 (R1 adds only the video link) |

Checked for this change: no file has two owners. A24 and A25 share no file: A24 writes the task, its grant and the queue entry and starts the task's run through `tasks.dispatch_next()` (V38); A25's `tasks/run.py` is reached only through that run and A10's handoff, so A24 never calls it, and no client can start a `task:` run. Removed with the cuts: `search/changes.py`, `routes_changes.py` (A12), `search/graph.py`, `routes_graph.py` (A15), the impact pages and graph components (B05), `gate/drafts.py`, `routes_policy_drafts.py` (A17), `ledger/decide.py` (superseded, V8), the old `api/briefing.py` and `routes_audio.py` (9.10), `web/app/review/` (replaced by the report page). B06 and B08 share no file, and neither builds the script: both read `report.script`, built by A19+A20's `reports/script.py` (V41).

## Agent roles

- **Builders:** one or more per PR as in `development-plan.md`. A06 and A19+A20 have three each; B04 has two.
- **Reviewers:** one agent per open PR: acceptance criteria, the six required behaviours, D1, owned files only, secrets (Slack webhook, Anthropic, ElevenLabs, HeyGen, Voyage keys), `.env` values, tokens and PubMed text. For the four PRs merged on desk V, this agent's pass is the back-end review.
- **Contract keeper:** watches `models.py`, the signature stubs and the generated types; at 11:45 posts the A01 diff for the A06 and A08 drafts; passes every PR merged on desk V; states the rebase cost of any contract change after 11:45.
- **Integrator:** runs I1, I3, I3b and S1 to S3, and from 13:35 keeps the smoke test green in `DXP_DB=dxp_smoke` with the fake Slack, ElevenLabs and HeyGen senders, so merges post nothing and render nothing.

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox. A merged PR that has not passed I1, I3, I3b (for A25), A16 pass 1 or its own S check is not done. The demo and video stories (8.2, 8.4) are not done until the V44 source check has passed, and the video and demo claim no completed follow-up work unless the task ran in that take (V39).

## Not modelled

- Rate limits or outages of the Claude API, ClinicalTrials.gov, the FDA site, Slack, ElevenLabs, HeyGen or Voyage AI.
- HeyGen's render queue (OD7): the API documentation says 1 to 5 minutes for most videos; HeyGen's help centre says the regular queue can average just under 24 hours on weekdays. Nothing waits on it (V29).
- The time to build the Vector Search indexes on the sandbox (forecast about 10 minutes, OD1).
- The reset's duration (forecast 10 minutes, OD6).
- Fix PRs from I1, I3 and A16: each takes a slot on its owner's desk.
- Whether the model's first draft actually writes the "showed" claim (V21: not required; the guaranteed block is check 2 on the proposed link of the record's "FoundationOne CDx" mention to the plasma scope, V35, V37).
- Whether the model labels a relationship with two checked quotes (V4: if it cannot, the item is shown as "related (no relationship established)").

## Open items

### Open dependencies (proposal section 8)

| # | Dependency | Owner | Due | Until it is resolved |
|---|---|---|---|---|
| OD1 | The Atlas Sandbox supports Vector Search indexes and Automated Embedding; or a Voyage AI key is cleared | Luis | Checked 9:00 to 10:45 when access arrives; `DXP_EMBEDDING` set by 11:45; index queryable by 14:05 | Plan for `auto`. Fallback: `voyage` if cleared, else `none` and text search, labelled "related by text search" everywhere (V3) |
| OD2 | The demo anchor. On 14 Nov the API v2 returned NCT04712877 with `lastUpdatePostDate` 2026-11-12, RECRUITING, `hasResults` false, but the record-history page showed a latest update of 17 July 2024, so the date is unverified (V36) | Luis | 10:45, by a live API query for the scan; the cursor goes into A03's `gate/seed_data/` by 11:45 | The anchor is whichever in-scope early-stage trial is actually updated after the cursor, verified in the response; NCT04712877 is the expected candidate only. The framing follows V33 from that trial's own fields; Luis tells B07 and A16 which trial |
| OD3 | ElevenLabs key and quota | Luis | Key in `.env` before 10:45; in the Modal secret by 12:20 (A04) | B06 builds against a fake; without the key the player says "unavailable" and the script stays as text (V29) |
| OD4 | Organiser clearance (D1, D57): the submission deadline, coding before 10:45, prepared `data/` and the logo, and the Slack channel's volume (one alert per report in `#all-mango-db-hackathon` across setup, tuning, I1, I3, rehearsals, the video and the live demo) | Luis | 9:00 to 10:45 | Plan for a 17:00 deadline, no coding before 10:45, live fetches, the text wordmark and `#all-mango-db-hackathon`. Luis records the answers in `docs/clearance.md`. If the channel is not acceptable, the webhook points at a team channel and A03 renames the grant's destination before the seed |
| OD5 | Change streams on the sandbox | — | — | **Closed:** no longer needed (A12 cut); screens poll |
| OD6 | `mongodump` and `mongorestore` work against the sandbox | Luis | Checked by A04 by 12:20; proven at the I1 snapshot, 14:15 to 14:20 | Each reset reruns the setup, about 30 minutes including Sam's correction, so A16 drops pass 2 and R1's reset may not fit before 17:15 |
| OD7 | HeyGen needs a paid plan or a funded API wallet (from US$5; the free plan is watermarked and non-commercial); render time is 1 to 5 minutes per the API docs, but the regular queue can average just under 24 hours on weekdays | Luis (account and key), Vlad (B08) | Account check at 10:45, off the critical path (V29); key in the Modal secret by 12:20 | Check fails: B08 is not built. On the day, one render is requested from the "Render avatar" button for the demo report only, as soon as it is filed; the report is opened last on camera; if it is not ready, the player says "Rendering" or "unavailable", the script stays as text, and nothing waits |

### Other open items

| Item | Owner | Due | Until it is resolved |
|---|---|---|---|
| Run the L1 and L2 proof (V31): A06 and A08 inside their 20-minute rebase budgets by 12:05; desk V open at 12:30 and its first two timed merges (A05, A13) | Luis, Vlad | 12:05, 13:00, 13:25 | Failure takes the emergency path (one desk, cut line applied, one rehearsal pass, no float) |
| Draft order: settled by V21 (two gated drafts, without then with memories) | — | — | Closed |
| One name for the report-level filing kind: settled by V24 (report-level `file_proposal`) | — | — | Closed |
| M1's retrieval filter: settled by V22 (Team + active + `claim_kind`) | — | — | Closed |
| Set `DXP_BASE_URL` to the production URL; confirm `/reports/<report_id>` and `/diagnostics/<dx_id>` resolve (S12, V11) | Luis | During A04; rechecked in I1 | The notifier refuses to start without it |
| Keep `SLACK_WEBHOOK_URL`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY` and `VOYAGE_API_KEY` only in `.env` and the Modal secret; never committed, logged or shown | Luis | Before 10:45, and on every PR review | Tests use fakes; I1 cannot pass without the real webhook |
| The epics, the spine (AD-14 routes, `Report.gap`, `Task.question` and `Task.answer`, the name mentions of V37) and `EXPERIENCE.md` must match the A24/A25 split, on-demand media and the removal of the hand-written aliases (V25 to V37 handoff) | Luis | Before 10:45 | Where they differ, this schedule and `development-plan.md` win on PR split, timing and ownership |
