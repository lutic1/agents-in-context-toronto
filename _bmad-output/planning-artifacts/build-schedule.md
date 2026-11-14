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

This schedule follows `sprint-change-proposal-2026-11-14-discovery-agent.md` (V1 to V24), which wins over every earlier planning document, and adopts its section 7 cuts 1 to 5 as the baseline, with HeyGen kept as the supporting PR B08 (V13). The readiness fixes D1 to D57 and the Slack decisions S1 to S13 still apply wherever that proposal does not replace them. The PR cards, with start and merge requirements and owned files, are in `development-plan.md`.

**Every time below is a forecast, not a validated run.** Cycle times come from `epics.md`; merge times are an assumption (about 10 minutes each). The milestones are where the day checks the forecast, and each has a fallback.

## Assumptions

- Hacking runs 10:45 to 17:00; no coding before 10:45 unless an organiser permits it in writing. Code freeze 16:30. R1 records the 60-second video and submits 16:30 to 16:55. The sandbox is reset 16:55 to 17:10. The live 3-minute demo starts at 17:15.
- We build on the Atlas Sandbox from the start (AD-24).
- No prepared code or assets are reused (D1). The prior collection, the FDA seed and memory M1 are all created during the event (V15); M1 comes from Sam's correction through the real UI.
- **Capacity (V19):** Luis runs up to 44 agents on his Claude plan and holds the product's keys. Vlad runs up to 22 agents (Sonnet 5.5 at high effort) on Claude Pro plus $300 of API credit; his lane runs at 1.25 times Luis's cycle times.
- **Concurrency does not remove sequential work.** Agents run side by side, but a module still waits for the modules it calls, an integration still waits for its merges, CI still takes its minutes, and a person still looks at and merges each PR. Adding agents adds PRs to review and merge; it does not add merge desks or shorten a chain. That is why this schedule is limited by the dependency chain and the merge queue, not by agent count.
- **Merges:** each merge on Luis's desk is about 10 minutes of CI plus a human look, one at a time. Vlad merges his own lane after Luis's review agent passes each PR. Each merge rebases on the latest `main`.

## The result in one paragraph

With the section 7 cuts as written, the plan does not fit: Luis would merge 15 PRs one at a time, and since only four of them can be ready before 12:40, the last would merge about 14:30 to 14:40 whatever order is chosen; the loop would then be green about 15:15 to 15:30, and the rehearsal's first pass would end after the 16:30 freeze. Two levers, added by this schedule and to be confirmed by Luis, make it fit: **L1**, the four long PRs (A06, A08, A19+A20, A21+A22) start at 10:45 as drafts against the shapes already written in AD-14 and Epic 10, as A03 does, so they are ready by 12:50 to 13:10 instead of all at 13:45; **L2**, Vlad's desk also merges four of Luis's leaf PRs (A05, A13, A14, A09), so Luis's desk holds 11 merges, not 15. With both, the last core merge lands at 14:00, the loop's first green pass is forecast for 14:30 and the I1 slot ends 14:45, approval and the task end 15:15, and the rehearsal ends 16:25. **Hard float to the freeze is 5 minutes.** The soft float is 30 minutes: 15 inside the I1 loop slot, and the 25-minute second rehearsal pass, which is dropped first. Without L1 or without L2, the 14:30 and 15:15 milestones are not reachable.

## Timeline

| Time | What |
|---|---|
| 9:00 to 10:45 | Doors, breakfast, kick-off. No coding. Luis confirms the deadline, sandbox access and the clearance items (OD4), records them in `docs/clearance.md`; checks the sandbox for Vector Search and Automated Embedding (OD1) |
| 10:45 | Hacking starts. A01, A02, A03 (generating the three DxP keys into `.env`, D48), B01, and the four draft PRs (A06, A08, A19+A20, A21+A22, lever L1). Luis queries ClinicalTrials.gov by hand, chooses the cursor and confirms NCT04712877 (OD2), and starts one HeyGen test render by hand to time it (OD7) |
| 11:00 | A04 deploy starts |
| 11:45 | A01 merged; contracts frozen; the contract keeper posts the diff and the draft PRs rebase. Every other Luis PR starts. Vlad's spend checked |
| 12:10 | B01 merged; B04 (two builders), B02 and B03 start; A04 merges at 12:20 |
| 12:30 | A03 merged; B06 and B08 start |
| 12:50 to 14:00 | Luis's desk merges without a gap: A06, A19+A20, A07+A11, A08, A21+A22, A24+A25, A10. Vlad's desk merges A05, A13, A14, A09, then B04 |
| 13:30 to 13:50 | I1 step 1 on the sandbox: grant, policy and scope seed; FDA seed; prior collection; embeddings and indexes ready |
| 14:00 to 14:15 | I1 step 2: the setup run on NCT05715229, Sam's correction through the deployed report page creates M1, the snapshot |
| **14:15 to 14:45** | **I1 discovery loop; first green pass by 14:30** |
| 14:25 to 15:05 | Vlad's desk merges B02, B06 (by 14:45), B03, B07, B08 (by 15:15) |
| **14:45 to 15:15** | **I3: approval, promotion and the follow-up task;** S1 (briefing) and S3 (memory correct and revoke) checked |
| 15:15 to 16:25 | A16: reset, pass 1 = core acceptance (S2 avatar checked just before), reset, pass 2, reset for the video |
| 16:30 | Code freeze |
| 16:30 to 16:55 | R1: record the 60-second video and submit; add the video link to the README |
| 16:55 to 17:10 | Reset for the live demo |
| 17:15 | Live 3-minute demo |

## Inputs to the computation

Cycle times from `epics.md` (agent cycle time for each story; a bundle runs its stories with separate builders, so it takes about as long as its longest story, plus the rebase on A01 for a draft PR). "Ready" means reviewed and green, waiting for its merge slot.

| PR | Cycle basis | Start | Ready |
|---|---|---|---|
| A01 | 1.0 h | 10:45 | 11:35 |
| A02 | 1.0 h | 10:45 | 11:45 |
| A03 | 1.5 h (9.2), drafting from 10:45 | 10:45 | 12:10 |
| A04 | 1.0 h | 11:00 | 12:00 |
| A06 | 2.1 h (1.6), with 9.3 and 10.7 by parallel builders; draft (L1) plus 15 min rebase | 10:45 | 12:50 |
| A19+A20 | 2.0 h (10.3), with 10.2 and 10.4 in parallel; draft (L1) plus rebase | 10:45 | 13:00 |
| A21+A22 | 2.0 h (10.6), with 10.5 in parallel; draft (L1) plus rebase | 10:45 | 13:10 |
| A08 | 2.0 h with two builders (as on the previous plan), draft (L1), tuned once live trials are reachable | 10:45 | 13:05 |
| A05 | 1.2 h (10.1), with 1.4 in parallel | 11:45 | 12:55 |
| A07+A11 | 1.2 h (9.5, 9.6), with 9.1 in parallel | 11:45 | 13:00 |
| A24+A25 | 1.2 h (10.8, 10.9) | 11:45 | 13:00 |
| A13 | 1.5 h (1.2 plus the snapshot script) | 11:45 | 13:15 |
| A14 | 1.5 h (2.3 value review, A18 read model) | 11:45 | 13:15 |
| A09 | 1.75 h (9.4, slightly simpler with Slack) | 11:45 | 13:30 |
| A10 | 1.75 h (as on the previous plan) | 11:45 | 13:30 |
| B01 | 1.0 h × 1.25 | 10:45 | 12:00 |
| B04 | 4 h (10.10) with two builders × 1.25 ≈ 1.6 h after B01 | 12:10 | 13:45 |
| B02 | about 1.65 h × 1.25 | 12:10 | 14:15 |
| B03 | about 1.9 h × 1.25 (V14 additions) | 12:10 | 14:35 |
| B06 | 1.5 h × 1.25 | 12:30 | 14:25 |
| B08 | about 1.75 h × 1.25 (async render and its states) | 12:30 | 14:45 |
| B07 | 1.0 h × 1.25 | 12:45 | 14:00 |

Integration time: I1 setup 30 minutes of work (step 1 about 20 minutes including the index build; step 2 about 10 minutes plus 5 for the snapshot), I1 loop 30 minutes, I3 30 minutes (proposal section 6). A16: two resets and two passes plus the video reset, 70 minutes. Reset forecast 10 minutes each (OD6).

## The merge queue

Luis's desk (desk L), one merge at a time, about 10 minutes each:

| Slot | PR | Ready | Waited | Why it is here |
|---|---|---|---|---|
| 11:35 to 11:45 | A01 | 11:35 | 0 | contract freeze |
| 11:45 to 11:55 | A02 | 11:45 | 0 | |
| 12:10 to 12:20 | A04 | 12:00 | 10 min | merges after B01 (12:10, D39) |
| 12:20 to 12:30 | A03 | 12:10 | 10 min | |
| 12:30 to 12:50 | idle | | | nothing critical is ready |
| 12:50 to 13:00 | A06 | 12:50 | 0 | head of the late queue; A14, A19+A20 and A24+A25 merge after it |
| 13:00 to 13:10 | A19+A20 | 13:00 | 0 | I1 step 1 needs it |
| 13:10 to 13:20 | A07+A11 | 13:00 | 10 min | A24+A25 merges after it |
| 13:20 to 13:30 | A08 | 13:05 | 15 min | I1 step 1 needs it (the prior collection is extracted); merges after A05 (13:05) |
| 13:30 to 13:40 | A21+A22 | 13:10 | 20 min | merges after A19+A20 |
| 13:40 to 13:50 | A24+A25 | 13:00 | 40 min | merges after A06, A07+A11, A21+A22 |
| 13:50 to 14:00 | A10 | 13:30 | 20 min | last; built over stubs, so its wait costs nothing until step 2 |

From 12:50 to 14:00 the desk is saturated: seven merges back to back with no gap. **Any merge that takes 20 minutes instead of 10 moves A10, I1 step 2 and everything after it by 10 minutes.**

Vlad's desk (desk V), his own PRs and four of Luis's leaf PRs (lever L2; each of Luis's passes Luis's review agent and the contract keeper first, and Luis sees it in the integrator's smoke test):

| Slot | PR | Ready |
|---|---|---|
| 12:00 to 12:10 | B01 | 12:00 |
| 12:55 to 13:05 | A05 | 12:55 |
| 13:15 to 13:25 | A13 | 13:15 |
| 13:25 to 13:35 | A14 (merges after A06) | 13:15 |
| 13:35 to 13:45 | A09 (merges after A03) | 13:30 |
| 13:45 to 13:55 | B04 | 13:45 |
| 14:15 to 14:25 | B02 | 14:15 |
| 14:25 to 14:35 | B06 (must merge by 14:45) | 14:25 |
| 14:35 to 14:45 | B03 | 14:35 |
| 14:45 to 14:55 | B07 | 14:00 |
| 14:55 to 15:05 | B08 (must merge by 15:15) | 14:45 |

Fix PRs from I1, I3 and A16 go first in the owning desk's queue.

**Without the levers.** With all of Luis's PRs starting at 11:45 and one desk, the four long PRs are all ready at 13:45 and the queue after 12:40 holds 11 merges, so the last lands about 14:40. With L1 alone (one desk) the last still lands about 14:30, because only four merges can happen before 12:40 and 11 remain. With L2 alone the long PRs still land at 13:45 and A24+A25 and A10 merge about 14:25 to 14:35. In each case I1 step 2 starts after 14:30, the loop ends about 15:15 to 15:30, I3 about 15:45 to 16:00, and the rehearsal's first pass alone runs past the 16:30 freeze. **The section 7 estimate of "about 13 merges, about 1.5 hours" is optimistic: the bundles leave 15 build-window merges on Luis's lane (about 2.5 hours on one desk).**

## The critical path

### Main chain

```
10:45  A01 contract ............................................ merged 11:45
10:45  long PRs drafted (L1); 11:45 the rest start
12:50  desk L saturated: A06 → A19+A20 → A07+A11 → A08 → A21+A22 → A24+A25 → A10
14:00  A10 merged (last core merge); B04 deployed (merged 13:55 on desk V)
14:00  I1 step 2: setup run on NCT05715229, Sam's correction creates M1 ...... 14:10
14:10  snapshot with M1 (OD6) ............................................... 14:15
14:15  I1 discovery loop: first green pass 14:30, slot ends ................. 14:45
14:45  I3 approval → promotion → follow-up task ............................. 15:15
15:15  A16: reset 15:15, pass 1 (core acceptance) 15:25–15:50,
       reset 15:50, pass 2 16:00–16:15, reset for the video 16:15 .......... 16:25
16:30  freeze (5 min hard float); R1 16:30–16:55 (5 min to 17:00)
16:55  reset 16:55–17:10 (5 min); live demo 17:15
```

The longest chain runs through the merge queue: the four draft PRs and the leaf PRs all feed one saturated desk, and A10 (or whichever PR is last) gates I1 step 2.

### Near-critical chains and their slack

| Chain | Ready or done | Needed by | Slack |
|---|---|---|---|
| Desk L queue, 12:50 to 14:00 | last merge 14:00 | I1 step 2 at 14:00 | **0** |
| B04 (Vlad, two builders) → merged 13:55 → deployed about 14:00 | 14:00 | I1 step 2 (Sam's correction through the UI, V15) at 14:00 | **0 to 5 min** |
| I1 loop first green pass | 14:30 | the end of the I1 slot, 14:45 | 15 min (fix buffer inside the slot) |
| A16 pass 2 | 16:15 | nothing core | 25 min of soft float if dropped |
| Rehearsal end | 16:25 | freeze 16:30 | **5 min** |
| R1 | 16:55 | deadline 17:00 | 5 min |
| Live-demo reset | 17:10 | 17:15 | 5 min |
| I1 step 1 (A03, A05, A06, A08, A13, A19+A20, all merged by 13:30) | 13:50 incl. index build | step 2 at 14:00 | 10 min |
| A06 draft | ready 12:50 | its slot 12:50 | 0 (it is the head of the queue; a late A06 delays every slot after it) |
| A08 draft | ready 13:05 | its slot 13:20 | 15 min |
| A19+A20 draft | ready 13:00 | its slot 13:00 | 0 |
| A21+A22 draft | ready 13:10 | its slot 13:30 | 20 min |
| A24+A25 | ready 13:00 | its slot 13:40 | 40 min |
| A10 | ready 13:30 | its slot 13:50 | 20 min |
| A05, A13, A14, A09 (desk V) | 12:55 to 13:30 | their slots, and step 1 at 13:30 (A05, A13) | 0 to 10 min |
| A03 | 12:10 | 12:20 slot; A06 merge at 12:50 | 10 to 40 min |
| A04 deploy and secrets | 12:20 | B04 deploy and the Slack links at 14:00 | 1 h 40 min |
| B02 Run console | 14:25 | A16 pass 1 at 15:25 (I1 starts runs through the API) | 1 h |
| B03 Audit view | 14:45 | A16 pass 1 at 15:25 | 40 min |
| B06 briefing | 14:35 | the 14:45 cut rule (cut 4) | 10 min |
| B08 avatar | 15:05 | the 15:15 cut rule, then S2 before pass 1 | 10 min; render time (OD7) is separate and may be hours |
| B07 README, script | 14:55 | R1 at 16:30 | 1 h 35 min |

Read honestly:

- **Hard float is 5 minutes**, the same as the proposal's section 6. The section 7 claim of 35 to 40 minutes holds only as soft float: 15 minutes of fix time inside the I1 loop slot and 25 minutes from dropping A16 pass 2. Nothing else is free.
- **The merge queue is the real critical path.** Seven back-to-back merges on Luis's desk and the B04 deploy both feed I1 step 2 at 14:00 with no slack.
- **M1 puts Vlad's lane on the critical path.** M1 must come from Sam's correction through the real report page (V15), so B04 deployed is a start requirement of I1 step 2, not only of I3.
- **The 14:30 milestone is the first green pass, not the end of I1.** The I1 slot ends at 14:45 (as in the proposal's section 6); 14:30 leaves 15 minutes for one round of fixes.
- **L1 has a cost.** Four PRs drafted before the freeze may need rework if A01 departs from AD-14 and Epic 10; 15 minutes of rebase are in their forecasts. If the contract changes more than that, those PRs slip and the queue slips with them.
- **L2 has a cost.** Vlad spends about 40 minutes looking at back-end diffs, which is why only leaf PRs go to his desk and only after Luis's review agent passes them.

## Who does what

**Luis (up to 44 agents, the product's keys):** A01 to A10 with the bundles, A13, A14, A16, A19+A20, A21+A22, A24+A25, I1 and I3; merges the 11 critical PRs on desk L; R1 with Vlad; the live-demo reset; `docs/clearance.md`; runs the review agent on Vlad's lane.

**Vlad (up to 22 agents, Sonnet 5.5 at high effort):** B01, B02, B03, B04 (two builders), B06, B07, B08; merges his lane and four of Luis's leaf PRs on desk V (L2); R1 with Luis.

- Vlad's PRs need the Atlas Sandbox connection string; Luis shares it through `.env`, never in the repository. Vlad's lane needs no Slack, ElevenLabs or HeyGen key: those calls run in the back end on Modal.
- If B04 is late, Luis's agents add a third builder to it at 13:15; it is on the critical path. B02 and B03 are core for the rehearsal: if either is not merged by 14:45, Luis's agents take it over.
- **Review of Vlad's lane.** One review agent run by Luis checks each of Vlad's PRs against its acceptance criteria, D1 and for secrets, at about 15 minutes a PR; B04 is reviewed first. If a PR waits more than 20 minutes, Luis starts a second review agent.
- **Vlad's credit.** Seven PRs and up to 22 agents. [ASSUMPTION: about $5 an agent-hour on the API.] Roughly 25 to 30 agent-hours is about $125 to $150, inside the $300. Check the spend at 11:45: above $50 an hour, cap the builders and stop B08 first.
- **Product keys (Luis's).** Anthropic: set a spend alert at $50 (the prior collection's extraction, the setup run, tuning, I1, I3 and two rehearsal passes). ElevenLabs: one short briefing per report (OD3). HeyGen: one render per report, on a paid plan or funded API wallet (OD7).

## Schedule by PR

| PR | Owner | What | Start | Ready | Merged | Path |
|---|---|---|---|---|---|---|
| A01 | Luis | Contract, stubs only | 10:45 | 11:35 | 11:45 (L) | critical |
| A02 | Luis | Registry, identity, aliases | 10:45 | 11:45 | 11:55 (L) | feeds A06 |
| A03 | Luis | Grants, policies including claim policies, the research scope, validators | 10:45 | 12:10 | 12:30 (L) | 20 min to A06's slot |
| B01 | Vlad | Web skeleton, shell, flags, player stubs | 10:45 | 12:00 | 12:10 (V) | feeds B04 |
| A04 | Luis | Deploy and secrets, including ElevenLabs and HeyGen | 11:00 | 12:00 | 12:20 (L) | 1 h 40 min |
| A06 | Luis | Ledger, gate, apply, claim checks (draft, L1) | 10:45 | 12:50 | 13:00 (L) | critical (queue head) |
| A05 | Luis | Discovery scan, prior collection, setup item | 11:45 | 12:55 | 13:05 (V) | feeds I1 step 1 |
| A19+A20 | Luis | Retrieval, relationships, report (draft, L1) | 10:45 | 13:00 | 13:10 (L) | critical |
| A07+A11 | Luis | Runs, stop, audit API with V14 | 11:45 | 13:00 | 13:20 (L) | critical (queue) |
| A13 | Luis | FDA seed, snapshot and reset | 11:45 | 13:15 | 13:25 (V) | feeds I1 step 1 |
| A08 | Luis | Extraction (draft, L1) | 10:45 | 13:05 | 13:30 (L) | critical (queue) |
| A14 | Luis | Read model, accepted knowledge, value review | 11:45 | 13:15 | 13:35 (V) | feeds the accepted knowledge link (I1) |
| A21+A22 | Luis | Reviewer memory (draft, L1) | 10:45 | 13:10 | 13:40 (L) | critical (queue) |
| A09 | Luis | Slack notifier, one alert per report | 11:45 | 13:30 | 13:45 (V) | feeds I1 step 2 |
| A24+A25 | Luis | Approval, promotion, task | 11:45 | 13:00 | 13:50 (L) | critical (queue; the reject path makes M1) |
| B04 | Vlad | Report page, reports list, accepted knowledge view | 12:10 | 13:45 | 13:55 (V) | critical (0 to 5 min) |
| A10 | Luis | The run | 11:45 | 13:30 | 14:00 (L) | critical (last merge) |
| I1 | Luis | Setup (data 13:30 to 13:50; M1 and snapshot 14:00 to 14:15), loop 14:15 to 14:45 | 13:30 | | 14:45 | critical |
| B07 | Vlad | README, submission text, video script | 12:45 | 14:00 | 14:55 (V) | 1 h 35 min |
| B02 | Vlad | Run console | 12:10 | 14:15 | 14:25 (V) | 1 h to A16 pass 1 |
| B06 | Vlad | ElevenLabs briefing (`briefing` flag) | 12:30 | 14:25 | 14:35 (V) | supporting; out if not merged by 14:45 |
| B03 | Vlad | Audit view with V14 | 12:10 | 14:35 | 14:45 (V) | 40 min to A16 pass 1 |
| B08 | Vlad | HeyGen avatar video (`avatar` flag) | 12:30 | 14:45 | 15:05 (V) | supporting, off the critical path; out if not merged by 15:15; render time OD7 |
| I3 | Luis | Approval, promotion, follow-up task | 14:45 | | 15:15 | critical |
| A16 | Luis | Rehearsal: pass 1 core acceptance, pass 2, video reset | 15:15 | | 16:25 | critical |
| R1 | Luis and Vlad | Record and submit | 16:30 | | 16:55 | critical |
| Reset | Luis | Reset for the live demo | 16:55 | | 17:10 | critical |

Cut and not scheduled: A12, A15, B05, A17. Folded: A18 into A14, A23 into A06, I2 into A16 pass 1.

## Dependencies for the integrations

| Step | Depends on | Does not depend on |
|---|---|---|
| I1 step 1 (data) | A03, A04, A05, A06, A08, A13, A19+A20 | any screen; A09, A10, A21+A22, A24+A25 |
| I1 step 2 (M1, snapshot) | step 1, A07+A11, A09, A10, A21+A22, A24+A25 (its reject path creates the memory), B04 deployed | B02, B03, B06, B08 |
| I1 loop | step 2's snapshot | B02, B03 (runs are started through the API), B06, B08 |
| I3 | I1 green; A24+A25, B04 (already in) | B02, B03, B06, B08 |
| A16 | I3; B02 and B03 for pass 1; A13's reset and I1's snapshot | B06 and B08 (they join only if S1 and S2 passed) |
| R1 | A16 (including the video reset), B07 | any supporting item |
| Live-demo reset | A13's script, I1's snapshot | anything else |
| S1 briefing | B06 merged by 14:45, a filed report | |
| S2 avatar | B08 merged by 15:15, B06, a filed report, a HeyGen render that finished (OD7) | |
| S3 memory correct and revoke | A21+A22, B04's memory panel, I3 | |

## Milestones and fallback triggers

Cuts are triggered by a missed milestone, not decided in advance. No core PR is ever replaced by a stub, and the demo never names a stub (D37, NFR5).

| By | Check | If missed |
|---|---|---|
| 10:45 | Cursor chosen and NCT04712877 confirmed by a manual query (OD2); one HeyGen render started by hand (OD7); sandbox Vector Search and Automated Embedding checked (OD1) | OD2: use any in-scope trial updated since the cursor and tell B07. OD7: see 12:00. OD1: set `DXP_EMBEDDING` to `voyage` (if cleared) or `none` before A19+A20 freezes its config |
| 11:45 | A01 merged, contracts frozen; draft PRs rebased; Vlad's spend checked | Hold other merges; everything slips one for one. A draft PR needing more than 15 minutes of rework loses its slot and joins the end of the queue. Spend above $50 an hour: cap Vlad's builders, stop B08 |
| 12:00 | The 10:45 HeyGen render finished, and its time recorded (OD7) | Not finished, or watermarked or refused (no paid plan): B08 is not built (cut 1); Vlad's B08 builders move to B04 |
| 12:20 | A04: deployed on the sandbox; every secret set (`DXP_BASE_URL`, `SLACK_WEBHOOK_URL`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY`); OD1 and OD6 results recorded | One agent fixes the deploy; the build continues locally against the sandbox. Without `DXP_BASE_URL` the notifier refuses to start |
| 13:00 | A06 merged (head of the late queue) | Every later slot on desk L slips one for one. The late PR gets more builders; B08 stops to free attention |
| 13:15 | FDA list fetched and parsed (A13) | Seed only the Diagnostics the scope and the prior collection name, typed from the FDA page; Luis tells B07 |
| 13:30 | I1 step 1's PRs merged (A03, A05, A06, A08, A13, A19+A20) | Step 1 starts with what has merged; the index build (about 10 minutes) starts first, as soon as A19+A20 is in |
| 13:50 | Indexes queryable (OD1) | Switch to `DXP_EMBEDDING=none`; every screen and the video say "related by text search" |
| 14:00 | Every core PR merged (A10 last) and B04 deployed | Stop B06 and B08 work; everyone on the late PR. Step 2 starts when it lands; each minute late comes out of the I1 loop's 15-minute fix buffer, then out of A16 pass 2 |
| 14:15 | M1 created by Sam through the UI and the snapshot taken (OD6) | If `mongodump` fails, record it: every reset reruns the setup, about 30 minutes with Sam's correction, so A16 drops pass 2 and its reset |
| **14:30** | **Loop first green pass (I1): discovery → FoundationOne CDx team-scope block (the "showed" claim block recorded if draft 1 writes it, V21) → report with M1's effect from the two gated drafts → Slack alert whose link opens the report** | Stop all supporting work; everyone fixes the loop. Cut B08 (flag `avatar` off) |
| 14:45 | I1 slot ends green; B06 merged | Not green: cut B06 (flag `briefing` off) and, if the second discovery item is what fails, demo the first only. B06 not merged: it drops out (cut 4) |
| **15:15** | **Approval, promotion and the follow-up task (I3); S1 and S3 checked; B08 merged** | If memory correct or revoke fails: cut the memory correction and revoke UI (flag `memory_edit` off; creation and use stay). If the task's filing fails: the task still runs and is gated, its results are shown in the audit only. B08 not merged: it drops out |
| 15:25 | S2: a HeyGen render reached `ready` on the sandbox | Flag `avatar` off |
| 15:50 | A16 pass 1, core acceptance, passed | Rehearse and record only what passed; drop pass 2 and use its 25 minutes for one fix and a rerun |
| **16:25** | **Rehearsal ended and the sandbox reset for the video** | Use the remaining minutes only for the reset; never fix during it |
| 16:30 | Code freeze | R1 records what works on the reset sandbox; the video names only behaviour shown |
| 16:55 | Submitted (R1) | Submit what exists |
| 17:10 | Sandbox reset for the live demo | Start the live demo with a new run; old Slack alerts stay in the channel and are told apart by action ID |

### Slip cut order (proposal section 7)

If a milestone slips, cut in this order. Nothing else may be cut.

1. **B08, the HeyGen avatar video.** Flag `avatar` off; the player is hidden; `briefing.render_avatar` stays a no-op if B08 never merged.
2. **B06, the ElevenLabs briefing.** Flag `briefing` off; the player is hidden; `briefing.generate` stays a no-op if B06 never merged. Also out if not merged by 14:45 (cut 4).
3. **The memory correction and revoke UI.** Flag `memory_edit` off. Memory creation (M1) and use (its effect in the report) stay: they are core.
4. **The follow-up task's related-evidence filing.** The task still runs under its own grant and gate; its results are shown in the audit only.
5. **The second discovery item.** The demo shows NCT04712877 only; stop is shown on the follow-up task's run.

Each cut leaves every core dependency intact:

| Cut | What refers to it | Why core still works |
|---|---|---|
| B08 | The report page's avatar player; A10's `briefing.render_avatar` call | Player hidden by flag; the call is A01's no-op stub or returns `unavailable`; the loop never waits for HeyGen |
| B06 | The briefing player; A10's `briefing.generate` call; B08's script | Hidden by flag; no-op stub; B08 is cut before B06, so nothing needs the script |
| Memory correct and revoke UI | B04's memory panel controls | Hidden by flag; the routes exist and are supporting; M1 creation and retrieval are untouched |
| Task related-evidence filing | `reports.add_related` from the task | The task's run, grant, gate and audit stay; only the filing step is skipped |
| Second discovery item | The scan's later results | The first item carries every V16 step; stop moves to the task's run |

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
| `retrieval/embed.py`, `retrieval/indexes.py`, `retrieval/related.py`, `reports/relate.py`, `reports/draft.py`, `reports/file.py`, `llm/prompts/relate.*`, `llm/prompts/report.*`, `api/routes_reports.py` | A19+A20 |
| `memory/store.py`, `memory/retrieve.py`, `api/routes_memories.py` | A21+A22 |
| `reports/decide.py`, `tasks/authorise.py`, `tasks/run.py`, `gate/grants.py`, `api/routes_report_decision.py` | A24+A25 |
| `docs/demo-and-reset.md` | A16 |
| `backend/tests/<id>/` | the PR with that ID (I1: `tests/i1/`, I3: `tests/i3/`) |
| `docs/clearance.md` | Luis |
| `web/` including `package.json`, `lib/api.ts`, `lib/features.ts`, `lib/format.ts`, `components/shell/`; not the paths below | B01 |
| `web/app/runs/page.tsx`, `web/app/runs/[run_id]/page.tsx`, `web/components/run-console/` | B02 |
| `web/app/runs/[run_id]/audit/`, `web/components/audit/` | B03 |
| `web/app/reports/` (not the `briefing/` and `avatar/` folders), `web/app/diagnostics/`, `web/components/report/`, `web/components/report-decision/`, `web/components/memory-panel/` | B04 |
| `briefing/script.py`, `briefing/audio.py`, `api/routes_briefing.py`, `web/app/reports/[report_id]/briefing/` | B06 |
| `briefing/avatar.py`, `api/routes_avatar.py`, `web/app/reports/[report_id]/avatar/` | B08 |
| `README.md`, `docs/video-script.md`, `docs/submission.md` | B07 (R1 adds only the video link) |

Checked for this change: no file has two owners. Removed with the cuts: `search/changes.py`, `routes_changes.py` (A12), `search/graph.py`, `routes_graph.py` (A15), the impact pages and graph components (B05), `gate/drafts.py`, `routes_policy_drafts.py` (A17), `ledger/decide.py` (superseded, V8), the old `api/briefing.py` and `routes_audio.py` (9.10), `web/app/review/` (replaced by the report page). B06 and B08 share no file: B06's script is called by B08 through `briefing.script_for`.

## Agent roles

- **Builders:** one or more per PR as in `development-plan.md`. A06 and A19+A20 have three each; B04 has two.
- **Reviewers:** one agent per open PR: acceptance criteria, the six required behaviours, D1, owned files only, secrets (Slack webhook, Anthropic, ElevenLabs, HeyGen, Voyage keys), `.env` values, tokens and PubMed text.
- **Contract keeper:** watches `models.py`, the signature stubs and the generated types; at 11:45 posts the A01 diff for the draft PRs.
- **Integrator:** runs I1, I3 and S1 to S3, and from 13:30 keeps the smoke test green in `DXP_DB=dxp_smoke` with the fake Slack, ElevenLabs and HeyGen senders, so merges post nothing and render nothing.

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox. A merged PR that has not passed I1, I3, A16 pass 1 or its own S check is not done.

## Not modelled

- Rate limits or outages of the Claude API, ClinicalTrials.gov, the FDA site, Slack, ElevenLabs, HeyGen or Voyage AI.
- HeyGen's render queue beyond the 10:45 measurement (OD7): the API documentation says 1 to 5 minutes for most videos; HeyGen's help centre says the regular queue can average just under 24 hours on weekdays.
- The time to build the Vector Search indexes on the sandbox (forecast about 10 minutes, OD1).
- The reset's duration (forecast 10 minutes, OD6).
- Fix PRs from I1, I3 and A16: each takes a slot on its owner's desk.
- Whether the model's first draft actually writes the "showed" claim (V21: not required; the team-scope block is the guaranteed block).

## Open items

### Open dependencies (proposal section 8)

| # | Dependency | Owner | Due | Until it is resolved |
|---|---|---|---|---|
| OD1 | The Atlas Sandbox supports Vector Search indexes and Automated Embedding; or a Voyage AI key is cleared | Luis | Checked 9:00 to 10:45 when access arrives; `DXP_EMBEDDING` set by 11:45; index queryable by 13:50 | Plan for `auto`. Fallback: `voyage` if cleared, else `none` and text search, labelled "related by text search" everywhere (V3) |
| OD2 | On Saturday the live API still returns NCT04712877 as updated after the cursor, RECRUITING, without results | Luis | 10:45, by a manual query; the cursor goes into A03's `gate/seed_data/` by 11:45 | Any in-scope trial updated since the cursor works; the claim policy applies the same way. Luis tells B07 and A16 which trial |
| OD3 | ElevenLabs key and quota | Luis | Key in `.env` before 10:45; in the Modal secret by 12:20 (A04) | B06 builds against a fake; without the key the briefing player is hidden (flag `briefing` off) |
| OD4 | Organiser clearance (D1, D57): the submission deadline, coding before 10:45, prepared `data/` and the logo, and the Slack channel's volume (one alert per report in `#all-mango-db-hackathon` across setup, tuning, I1, I3, rehearsals, the video and the live demo) | Luis | 9:00 to 10:45 | Plan for a 17:00 deadline, no coding before 10:45, live fetches, the text wordmark and `#all-mango-db-hackathon`. Luis records the answers in `docs/clearance.md`. If the channel is not acceptable, the webhook points at a team channel and A03 renames the grant's destination before the seed |
| OD5 | Change streams on the sandbox | — | — | **Closed:** no longer needed (A12 cut); screens poll |
| OD6 | `mongodump` and `mongorestore` work against the sandbox | Luis | Checked by A04 by 12:20; proven at the I1 snapshot, 14:10 to 14:15 | Each reset reruns the setup, about 30 minutes including Sam's correction, so A16 drops pass 2 and R1's reset may not fit before 17:15 |
| OD7 | HeyGen needs a paid plan or a funded API wallet (from US$5; the free plan is watermarked and non-commercial); render time is 1 to 5 minutes per the API docs, but the regular queue can average just under 24 hours on weekdays | Luis (account and key), Vlad (B08) | One render started by hand at 10:45 and timed by 12:00; key in the Modal secret by 12:20 | If the 10:45 render is not back by 12:00, B08 is not built. On the day, the render is triggered when the report is filed and the report is opened last on camera; if it is not ready, the page shows "Rendering" or "Avatar unavailable" and the loop is unaffected |

### Other open items

| Item | Owner | Due | Until it is resolved |
|---|---|---|---|
| Confirm levers L1 (four draft PRs from 10:45) and L2 (Vlad merges A05, A13, A14, A09) | Luis | Before 10:45 | Without both, the 14:30 and 15:15 milestones are not reachable (see "The merge queue") |
| Draft order: settled by V21 (two gated drafts, without then with memories) | — | — | Closed |
| One name for the report-level filing kind: settled by V24 (report-level `file_proposal`) | — | — | Closed |
| M1's retrieval filter: NCT05715229 names Guardant360, NCT04712877 names FoundationOne Liquid CDx, so memory retrieval must match on `claim_kind`, not on the assay tag (A21+A22 card) | Luis | 11:45 | Settled by V22 (Team + active + `claim_kind`). Closed |
| Set `DXP_BASE_URL` to the production URL; confirm `/reports/<report_id>` and `/diagnostics/<dx_id>` resolve (S12, V11) | Luis | During A04; rechecked in I1 | The notifier refuses to start without it |
| Keep `SLACK_WEBHOOK_URL`, `ELEVENLABS_API_KEY`, `HEYGEN_API_KEY` and `VOYAGE_API_KEY` only in `.env` and the Modal secret; never committed, logged or shown | Luis | Before 10:45, and on every PR review | Tests use fakes; I1 cannot pass without the real webhook |
