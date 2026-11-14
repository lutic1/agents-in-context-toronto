---
title: DxP build schedule for Saturday 14 November 2026
status: draft
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxP build schedule for Saturday

This schedule follows the approved course correction in `sprint-change-proposal-2026-11-13.md` and the readiness fixes D1 to D57 (including the final audit, D41 to D57) in `readiness-fixes-2026-11-14.md`, which win where any document disagrees, and the Slack change S1 to S13 in `sprint-change-proposal-2026-11-14-slack.md`: Slack `#all-mango-db-hackathon` replaces GitHub as the external system, and that file wins on anything about the notification. DxP is pitched and built for Statement 1, "Agents You Can Audit", and the governed agent is the product. The PR-by-PR assignment that agents work from is `development-plan.md`. This file plans by dependencies and agent capacity, and names the milestones that trigger a fallback cut if they are missed.

## Assumptions

- Hacking runs 10:45 to 17:00. No coding before 10:45 unless an organiser permits it in writing. 9:00 to 10:45 is doors, breakfast and kick-off; Luis uses it to confirm the open items below with the organisers.
- Code freeze is 16:30. The sandbox is reset with A13's `scripts/reset_demo.py` before every take (D41): at the start of I2, before each rehearsal, before the video (16:15 to 16:30) and before the live demo. R1 (Luis and Vlad) records the 60-second video and submits (description, public repository, video, team members) from 16:30 to 16:55. The sandbox is reset again from 16:55 to 17:10 (D34). The live 3-minute demo for judging starts at 17:15.
- We build on the Atlas Sandbox from the start. Our own cluster is not the final environment. Change streams must be confirmed on the sandbox tier before the live feed depends on them.
- No prepared code or assets are reused (D1). Skills are reference documentation only. A05 fetches the 20 selected trials (D30) from ClinicalTrials.gov and A13 fetches the FDA companion diagnostics list during the event; prepared `data/` files are loaded only if an organiser clears them in writing.
- Capacity: Luis runs up to 44 agents on Luis's Claude plan and holds the product's API key. Vlad has Claude Pro plus $300 of API credit and runs Sonnet 5.5 at high effort through ten subagents. Luis's review agent reviews every PR on Vlad's lane. Agents build, review, test and integrate; Luis and Vlad decide and merge.
- A module can be built against its contract before the modules it calls exist. A01 and A02 freeze the contracts by 11:45. Real wiring happens in the two integration PRs, I1 and I2. The sandbox is seeded for the first time in I1's first 15 minutes (D38).
- Every time below is a model forecast, not a validated run. The milestones are where the day checks them.

## Timeline

| Time | What |
|---|---|
| 9:00 to 10:45 | Doors, breakfast, kick-off. No coding. Luis confirms the deadline, sandbox access, the prepared-material rules and whether `data/` and the logo are cleared, and records the answer in `docs/clearance.md` |
| 10:45 | Hacking starts: contracts (A01, A02), web skeleton (B01), grants and policies (A03, which first generates `DXP_AGENT_KEY`, `DXP_API_KEY` and `DXP_SEED_KEY` locally into `.env`, D48); deploy on the sandbox (A04) from 11:00 |
| 11:45 | Contracts frozen; everything else builds in parallel against them |
| 12:00 | B01 merged; A04 merges after it (D39) |
| 12:45 | A13 starts the FDA fetch, with a second builder on the snapshot procedure and `scripts/reset_demo.py` (D41); A18 built, waiting for A06 |
| 13:30 | A13 merged on fake-gate tests (D38); A07, A10, A11 merged; A14 built, waiting for A06 |
| 13:45 | Gate, ledger and apply (A06), extraction (A08) and the Slack notifier (A09) merged; A18 and A14 merge after A06; I1 starts (A04's deploy, merged at 12:00, is one of its start requirements, D51) |
| 13:45 to 14:00 | I1 step 1 (D38, D41): grant seed, selected-set load, FDA fetch and seed on the sandbox, then the seeded snapshot with A13's procedure (`mongodump`) |
| 14:00 | B07 done: README, submission text and video script |
| **14:30** | **First complete loop on the sandbox (I1):** at least the NCT04712877 proposal for FoundationOne Liquid CDx filed pending and its Slack alert delivered to `#all-mango-db-hackathon` (one alert per filed proposal, D46; both links resolve once B04 is deployed), the FoundationOne CDx change blocked before execution with no Slack message, the audit reconstructs them |
| 14:30 to 15:00 | Screens wired to the loop; B06 may merge if the loop is green; S1 (live feed) checked by 15:00 |
| 15:00 to 15:30 | Core acceptance (I2), starting with a reset (forecast 10 minutes, D41); S2 and S3 checked by 15:30 |
| 15:30 to 16:15 | Live-demo rehearsal (A16), twice, each from a reset with A13's script, with only the supporting and stretch items that passed their check; S4 by 15:45 joins the second pass |
| 16:15 to 16:30 | Reset the sandbox for the video (A13's `scripts/reset_demo.py`, run by A16, D34, D41) |
| 16:30 | Code freeze |
| 16:30 to 16:55 | R1: record the 60-second video and submit; add the video link to the README |
| 16:55 to 17:10 | Reset the sandbox for the live demo (Luis, A13's script, D34, D41) |
| 17:15 | Live 3-minute demo |

## What limits the day

**Capacity is not the limit.** At the peak, about 12 builders run in Luis's lane and 5 in Vlad's. Reviewer agents, the contract keeper and the integrator take a fraction of Luis's 44 slots.

**The dependency path is the limit.** Recomputed after D26 (apply moved into A06), D38 (the sandbox seed moved into I1) and the D34 reset slots, the critical path is:

A01 contract (10:45 to 11:45) → A06 ledger, gate and apply (11:45 to 13:45, no slack), with A08 extraction and A09 Slack notifier finishing at the same time → I1 step 1, seed and snapshot (13:45 to 14:00) → I1 the loop (14:00 to 14:30) → **30 minutes** → I2 core acceptance, starting with a reset (15:00 to 15:30) → A16 rehearsal (15:30 to 16:15) → reset for the video (16:15 to about 16:25) → **5 minutes** → code freeze at 16:30 → R1 record and submit (16:30 to 16:55) → **5 minutes** → deadline 17:00. For the live demo, the second reset (16:55 to 17:10) leaves **5 minutes** before 17:15.

| Path | Ready | Needed by | Slack |
|---|---|---|---|
| A06 ledger, gate and apply; A08 extraction; A09 Slack notifier | 13:45 | I1 at 13:45 | none (A09 likely has a little in practice; see below) |
| A13 FDA fetch and seed, snapshot procedure and `scripts/reset_demo.py` (second builder), merged on fake-gate tests (12:45 to 13:30) | 13:30 | I1 at 13:45 (the snapshot) and I2 at 15:00 (the first reset) | 15 minutes |
| A07 runs and stop, A10 the run, A11 audit API | 13:30 | I1 at 13:45 | 15 minutes |
| A05 fetch and load the 20 selected trials | 12:30 | A08 merge and I1 at 13:45 | 75 minutes |
| A03 grants (agent, `sam@v1`, `seed@v1`), policies, policy sets, validators | 12:30 | A07 and A09 merges at 13:30 | 60 minutes |
| B01 web skeleton | 12:00 | A04 merge (D39) and the screens | none for A04's merge, which only A12 (supporting) and the Vercel deploy wait on |
| A04 deploy, with the D48 Vercel and Modal secrets | 12:00 (merged after B01) | I1 at 13:45 (a direct start requirement, D51) | 105 minutes |
| A18 read model (built by 12:45) | 13:45 (merged after A06) | B04 merge at 14:00 | 15 minutes after A06; 60 minutes of build slack |
| A14 proposals, Reviewer decisions, value review (built by 13:15) | 13:45 (merged after A06) | B04 merge at 14:00 | 15 minutes after A06; 30 minutes of build slack |
| I1 step 1: sandbox seeded and snapshot taken | 14:00 | the I1 loop | none |
| I1 loop green | 14:30 | I2 at 15:00 | 30 minutes |
| B02 run console | 14:15 | I2 at 15:00 | 45 minutes |
| B03 audit view, B04 record and review | 14:00 | I2 at 15:00 | 1 hour |
| B04 deployed, so the Slack alert's two links resolve | about 14:00 | the link check in I1 (by 14:30), else in I2 | 30 minutes to I1's end; the I1 loop never waits for it |
| I2 core acceptance (reset forecast 10 minutes, then about 20 minutes of acceptance) | 15:30 | A16 at 15:30 | none |
| A16 rehearsal done | 16:15 | the reset at 16:15 | none |
| Reset for the video (forecast 10 minutes) | 16:25 | code freeze at 16:30 | 5 minutes |
| B07 README, submission text, video script | 14:00 | R1 at 16:30 | 2.5 hours |
| R1 video recorded and submitted | 16:55 | deadline 17:00 | 5 minutes |
| Reset for the live demo (forecast 10 to 15 minutes) | 17:10 | live demo at 17:15 | 5 minutes |
| A12 feed, A15 graph, B05 impact, B06 audio, A17 policy draft | 13:00 to 15:30 | nothing core | not on the path |

Read honestly:

- **Float fell from 50 to 40 minutes.** From 13:45 to the 17:00 deadline the chain holds 30 minutes before I2, 5 before the freeze and 5 after R1. A slip of more than 35 minutes in A06, A08 or A09 pushes the video reset into the freeze; more than 40 misses the submission deadline. Before these fixes the limit was 45.
- **The I1 loop itself lost 15 minutes.** D38 put the seed, the selected-set load and the snapshot in I1's first 15 minutes, so the loop now has 30 minutes instead of 45 to reach the 14:30 milestone. If the loop needs the 45 minutes it had before, I1 ends at 14:45 and the 30 minutes before I2 shrink to 15. The 30 minutes before I2 are also when the screens are wired to the loop, so real float is smaller still.
- **A06 is bigger.** D26 moved `ledger/apply.py` (claim, guarded update, edges, event, recovery) from A14 into A06. Its 13:45 forecast holds only because a third builder writes `apply.py` in parallel from 11:45, the same builder-time A14 had; review of A06 takes longer. A06 is still the riskiest PR: it gates the merges of A14 and A18 and the start of I1, and through A14 and A18 it gates B04 after 15 minutes. A slip in A06 delays I1 one for one.
- **A09 is likely slightly simpler with Slack, but the path does not change.** The Slack notifier has no read-back, no issue listing or pagination to reconcile, and one webhook call whose observed outcome is recorded as is (S7); it adds the Block Kit layout, the single 429 retry and the resolve route (S8). That probably frees some of A09's builder time, but A06 and A08 still finish at 13:45, so the critical path, its 40 minutes of float and every forecast stay as they were. A09 keeps its forecast and its second builder; if it finishes early, that builder moves to A06's tests.
- **The alert's links need B04 deployed.** I1 checks that both links in the real alert resolve on the deployed web app (S6). B04 merges after A14 and A18 (about 13:45) and is forecast at 14:00, so the check normally fits inside I1; the loop does not wait for it, and if B04 is late the check moves to I2. This adds nothing to the path.
- **A13 left the no-slack list.** It merges on fake-gate tests at about 13:30 and no longer waits for A06 (D38), so three PRs, not four, reach I1 with no slack. Its real risk moved into I1's first 15 minutes: if the FDA seed fails on the sandbox, the loop cannot start. A fetch or parse problem still shows at 13:15 (A13's fallback in its card).
- **The reset slots took the last float.** The 15 minutes after the rehearsal are now the video reset (D34); 5 minutes remain if it takes 10. The second reset (16:55 to 17:10) has 5 minutes before the live demo. If `mongodump` or `mongorestore` does not work against the sandbox, the reset reruns the four seed commands instead, which may take the full 15 minutes; this is checked in I1's step 1 (open items).
- **A reset before every take (D41) moves no milestone, but tightens I2 and the rehearsal.** I2 now starts with a reset, so its 30 minutes hold about 10 of reset and 20 of acceptance; if the reset is slow or acceptance needs the full 30 minutes, I2 ends late and the slip comes out of A16's rehearsal time, not the freeze. A16 already rehearsed each pass from a reset: two resets of about 10 minutes plus two passes of about 5 minutes (the 3-minute demo and the 60-second script) fit its 45 minutes with about 5 to spare for notes. A13 gains `scripts/reset_demo.py` and the snapshot procedure from A16; a second builder writes them, so A13 keeps its 13:30 forecast and 15 minutes of slack. The integrator's smoke test runs in `DXP_DB=dxp_smoke`, so it never dirties the demo database between resets.
- **Supporting and stretch work is off the path.** Removing A12 from I1, limiting I2 to core plus Record and Review, and gating every Impact and Listen link behind flags means none of A12, A15, B05, B06 or A17 can delay I1, I2, A16 or R1 (D37).

What keeps the path this short:

1. A01, A02, A03 and B01 start together at 10:45. A03 drafts against the A01 shapes and merges after A01.
2. Every builder after 11:45 codes against the frozen signatures, so A06, A07, A08, A09, A10, A11, A14 and A18 run side by side instead of one after another.
3. A13 merges on fake-gate tests, so it never waits for A06; the real seed runs once, in I1's first step (D38).
4. A06 gets a third builder for `ledger/apply.py`, so moving apply out of A14 (D26) does not lengthen A06's forecast.
5. The batch is the 20 selected trials (D30, stored with `window: "selected"`, D54), not 443 items, so the run itself is short.
6. The 30 minutes between I1 and I2 are kept for wiring the screens and the S1 check, not for new features.

## Who does what

Luis owns the critical path: the contract, the registry and aliases, grants and policies, the ledger, gate and apply, runs and stop, extraction, the Slack notifier, the FDA fetch and seed, the read model, proposals and review, the audit API, both integrations, the rehearsal and resets, and `docs/clearance.md`. Vlad owns the screens, the web skeleton, the stretch audio and the submission package. Both record and submit (R1). The PR-by-PR assignment, with start and merge requirements and owned files, is in `development-plan.md`.

**Luis (up to 44 agents, the product's API key):** A01 to A18, I1 and I2, R1 with Vlad, and the live-demo reset at 16:55. Luis coordinates merges on Luis's lane and runs the review agent on Vlad's lane.

**Vlad (Claude Pro plus $300 of API credit, Sonnet 5.5 at high effort, ten subagents):** B01 to B07, and R1 with Luis. Vlad coordinates merges on Vlad's lane after Luis's review agent passes each PR.

- Vlad's PRs need the Atlas Sandbox connection string; Luis shares it through `.env`, never in the repository. Vlad's lane does not need `SLACK_WEBHOOK_URL`: no screen posts to Slack, and the screens read notification status from the API.
- If Vlad's lane falls behind, B06 is cut first. B02, B03 and B04 are core: if any is not merged by 14:15, Luis's agents take it over.

**Review of Vlad's lane.** One review agent run by Luis checks each of Vlad's PRs against its acceptance criteria, D1 (no prepared code) and for secrets, `.env` values, tokens and PubMed text, at about 15 minutes a PR. Most of Vlad's PRs arrive between 14:00 and 14:30; if a PR waits more than 20 minutes, Luis starts a second review agent.

**Forecast for Vlad's credit.** Vlad's lane is seven PRs. [ASSUMPTION: a Sonnet 5.5 subagent costs about $5 an agent-hour on the API, mostly cache reads, including the main agent's coordination.] Roughly 15 to 20 agent-hours is about $100, well inside the $300. Check the spend at 11:45: if it is running above $40 an hour, cap the subagents at six and drop B06.

**Product API budget (Luis's key).** The selected set is 20 trials, run a few times during tuning, I1, I2 and the rehearsal, plus the stretch policy draft. Set a spend alert at $50.

## Schedule

Start requirements and merge requirements for each PR are in `development-plan.md`.

| PR | Owner | What | Start | Finish | Path |
|---|---|---|---|---|---|
| A01 | Luis | Contract: routes, shapes, error shape, frozen signatures; stubs only | 10:45 | 11:45 | critical |
| A02 | Luis | Registry, identity and the hand-written aliases | 10:45 | 11:45 | critical |
| A03 | Luis | Agent, `sam@v1` and `seed@v1` grants with `startable_by`, policies, policy sets, validators, server-side actor resolution | 10:45 | 12:30 | 60 min slack |
| B01 | Vlad | Web skeleton, minimal shell, text wordmark, feature flags; builds locally, deploys once A04 lands | 10:45 | 12:00 | core |
| A04 | Luis | CI, Vercel and Modal deploy on the Atlas Sandbox; change streams checked; `DXP_BASE_URL` and the `SLACK_WEBHOOK_URL` Modal secret set; merges after B01 | 11:00 | 12:00 | 105 min slack |
| A05 | Luis | Fetch the 20 selected trials by NCT ID from ClinicalTrials.gov and load them | 11:45 | 12:30 | 75 min slack |
| A06 | Luis | Ledger with the policy gate before every write; decisions; pending proposals; apply and recovery | 11:45 | 13:45 | critical (no slack) |
| A07 | Luis | Runs: two identities, admissions, stop, sweep, settle and finish | 11:45 | 13:30 | 15 min slack |
| A08 | Luis | Extraction with quote and support checks, alias-constrained | 11:45 | 13:45 | critical (no slack) |
| A09 | Luis | Slack notifier (`story/9.4-slack-notify`): action ID first, atomic claim, Block Kit alert with links back to DxP, observed outcome, `unknown` never retried, manual resolution | 11:45 | 13:45 | critical (no slack) |
| A10 | Luis | The run: LangGraph over the selected set, with `DXP_DEMO_PACE` | 11:45 | 13:30 | 15 min slack |
| A11 | Luis | Audit API, decisions and "who authorised" | 11:45 | 13:30 | 15 min slack |
| A18 | Luis | Read model and `GET /diagnostics/<dx_id>` (merged after A06) | 11:45 | 12:45 | core (15 min after A06) |
| A14 | Luis | Proposals, Reviewer decisions and value review API, calling A06's apply (merged after A06) | 11:45 | 13:15 | core (15 min after A06) |
| A12 | Luis | Change-stream feed with polling fallback | 12:00 | 13:00 | supporting (S1) |
| A15 | Luis | Graph API by run: changed elements, context on request | 12:00 | 13:30 | supporting (S2) |
| B02 | Vlad | Run console | 12:00 | 14:15 | core (45 min slack) |
| B03 | Vlad | Audit view | 12:00 | 14:00 | core (1 h slack) |
| B04 | Vlad | Record and Review screen, minimal | 12:00 | 14:00 | core (1 h slack) |
| B05 | Vlad | Run impact view | 12:00 | 14:30 | supporting (S2) |
| A13 | Luis | Fetch the FDA companion diagnostics list; seed lung rows and synthetic Teams through the ledger; snapshot procedure and `scripts/reset_demo.py` (D41); merged on fake-gate tests | 12:45 | 13:30 | 15 min slack |
| B06 | Vlad | Stretch: spoken audit briefing, behind a flag; merged only after the 14:30 loop is green | 13:00 | 14:30 | stretch (S3) |
| B07 | Vlad | README, submission text, video script | 13:00 | 14:00 | core (2.5 h slack) |
| I1 | Luis | Integration: seed and snapshot (13:45 to 14:00), then the loop on the sandbox (core PRs only, A04 among them, D51) | 13:45 | 14:30 | critical |
| A17 | Luis | Stretch: rejection drafts a policy for approval | 14:30 | 15:30 | stretch (S4), only if I1 is green |
| I2 | Luis | Reset, then core acceptance on the sandbox | 15:00 | 15:30 | critical |
| A16 | Luis | Live-demo rehearsal, each pass from a reset with A13's script, then the reset for the video (16:15 to 16:30) | 15:30 | 16:15 (reset done 16:30) | critical |
| R1 | Luis and Vlad | Record the 60-second video and submit | 16:30 | 16:55 | critical |
| Reset | Luis | Reset the sandbox for the live demo (A13's `scripts/reset_demo.py`) | 16:55 | 17:10 | critical |

## Dependencies for the integrations

| Step | Depends on | Does not depend on |
|---|---|---|
| I1 | A03, A04, A05, A06, A07, A08, A09, A10, A11, A13 (A04 directly: the deploy, `DXP_BASE_URL` and the Modal secret, D51; through them A01, A02) | A12 (no feed in I1), A14 (apply is A06's, D26), A15, A18, any screen. Only the alert-link check uses B04's deployed pages; the loop does not wait for it, and it moves to I2 if B04 is late |
| I2 | I1, A14, A18, B02, B03, B04; its first reset uses A13's script and I1's snapshot | A12, A15, B05, B06, A17 |
| A16 | I2 only as a start requirement (D41); it uses A13's script and I1's seeded snapshot, and creates neither | any supporting or stretch item |
| R1 | A16 (including the reset for the video), B07 | any supporting or stretch item |
| Live-demo reset | A13's script, I1's snapshot | anything else |
| S1 live feed | A12, B02, I1 green | |
| S2 impact view | A15, B05, I1 green | |
| S3 spoken briefing | B06 merged after the loop is green, A11 | |
| S4 policy draft | A17, A14 | |

Supporting and stretch items may be built before 14:30 by agents not needed on the core. They never block a core PR. If the loop is not green at 14:30, they pause. Each joins the rehearsal only if its own check passed (S1 to S4 in `development-plan.md`); a failed or late check turns its feature flag off and needs no code change.

## Milestones and fallback triggers

Cuts are triggered by a missed milestone, not decided in advance. No core PR is ever replaced by a stub, and the demo never names a stub (D37, NFR5).

| By | Check | If missed |
|---|---|---|
| 11:45 | Contracts frozen (A01, A02) | Hold other merges until they land; everything slips one for one |
| 11:45 | Vlad's spend rate checked | Above $40 an hour: cap subagents at six, drop B06 |
| 12:00 | B01 merged, then A04: deployed on the Atlas Sandbox; change streams confirmed or polling chosen; `DXP_BASE_URL` set to the production URL and `SLACK_WEBHOOK_URL` in the Modal secret | One agent fixes the deploy; the build continues locally against the sandbox. Without `DXP_BASE_URL` the notifier refuses to start, so it must be set before I1 |
| 13:15 | FDA list fetched and parsed (A13) | A13 seeds only the Diagnostics the selected set names, typed from the FDA page during the event; Luis tells B07, which says so in the README |
| 13:45 | Gate, ledger and apply (A06), runs (A07), extraction (A08), the Slack notifier (A09) merged; A13 merged on fake-gate tests | Nothing core is stubbed (D37). The late PR gets more builders. I1 starts its seed step on time with what has merged, and the loop waits for the late PR. Supporting and stretch work (A12, A15, B05, B06, A17) stops to free builders and attention. Every minute late comes out of the 30 minutes before I2 |
| 14:00 | Sandbox seeded and snapshot taken (I1 step 1) | The seed's owners (A03, A05, A13, A06) fix it in small PRs before the loop starts; without a snapshot there is no fast reset, so the reset falls back to rerunning the seeds |
| 14:00 | B07 merged | Vlad finishes it before any supporting work; R1 needs the script |
| 14:15 | B02, B03, B04 merged | Luis's agents take over the late screen |
| **14:30** | **Loop green (I1): at least the NCT04712877 proposal for FoundationOne Liquid CDx pending and its Slack alert delivered to `#all-mango-db-hackathon`, the FoundationOne CDx change blocked with no Slack message, audit of them (D46)** | Stop all supporting and stretch work; everyone fixes the loop. B06 stays unmerged |
| 15:00 | S1 live feed passed | Flag `feed` off; the console polls `GET /runs/<run_id>` and the audit |
| 15:30 | I2 core acceptance passed (it starts with a reset, D41) | Rehearse only what passed. If Sam's approval fails, the demo drops it; the scripted question is still answered from the filing decision, which I1 proved |
| 15:30 | S2 and S3 passed | Flags `impact` and `audio` off |
| 15:45 | S4 passed | A17 is left out of the demo |
| 16:15 | Rehearsal done (A16) | Use the reset slot only for the reset; do not fix during it |
| 16:30 | Sandbox reset for the video; code freeze | R1 records what works on the reset sandbox; the video names only behaviour shown |
| 16:55 | Submitted (R1) | Submit what exists |
| 17:10 | Sandbox reset for the live demo | Start the live demo with a new run: a new `run_id` gives new action IDs, so the new alert is told apart from the earlier ones in `#all-mango-db-hackathon`. Old alerts stay in the channel; nothing is deleted or posted there by hand |

If a fallback is triggered, cut in this order. Only A12, A15, B05, B06 and A17 may be cut (D37):

1. **Stretch first:** B06 spoken briefing (never merged unless the loop is green; flag `audio` off; B03's "Listen" link hidden), then A17 policy draft (not started unless I1 is green; the approve route stays 501). Reversal of a run is stretch outside Story 9.5 and has no PR, so there is nothing to cut.
2. **Then supporting:** B05 impact view (flag `impact` off; every Impact link hidden), A15 graph API (only B05 calls it), then A12 change feed (B02 polls `GET /runs/<run_id>` and `GET /runs/<run_id>/audit`, which are A07's and A11's and core).
3. **Never cut, never stubbed:** A01 to A11, A13, A14, A16, A18, B01, B02, B03, B04, B07, I1, I2, R1 and both resets. A14, A18 and B04 are core because the live demo uses Sam's review (D35).

Each cut leaves every core dependency intact:

| Cut | What refers to it | Why core still works |
|---|---|---|
| B06 | B03's "Listen" link | Shown only when `audio` is on; the audio route stays 501 and nothing core calls it |
| A17 | A14's `rule_draft`; `POST /policies/<policy_id>/approve` | `rule_draft` is always null in A14; the approve route stays 501; no screen calls it |
| B05 | The shell's Impact nav item; Impact links in B02 and B03 | All hidden when `impact` is off; the Record page is reached from Review and Audit |
| A15 | B05 only | Cut together with B05, or B05 is flagged off |
| A12 | B02's feed when `feed` is on | `feed` is off unless S1 passed; B02 and B04 poll A07, A11 and A14 routes, all core; B02 is done with `feed` off |

## Who owns which files

Extra agents only help if two of them never edit the same file. A01 creates the stub files listed in its card and hands each to the PR that finishes it when A01 merges; after that, each file below has exactly one owner (D15, D36). A change to another PR's file, including a fix found during I1 or I2, goes in a small PR reviewed by that file's owner.

| Files | Owner | Others call it, never edit it |
|---|---|---|
| `backend/pyproject.toml` and `backend/uv.lock` (every dependency declared up front), `backend/tests/conftest.py`, `.env.example` (names every D48 variable, never a value), `backend/dxp/api/app.py` (`create_app()`, every route registered, origins from `DXP_ALLOWED_ORIGINS`, the startup hook calling `ledger.recover_applying()`), `backend/dxp/api/models.py`, `backend/dxp/store/` except `store/schemas/`, the package `__init__.py` files no one else owns (`backend/dxp/`, `api/`, `search/`, `sources/`, `schema/`), `tools/gen_types.sh`, generated `web/lib/types.ts`; `GET /schema` | A01 | Every PR; a change goes through the contract keeper in its own PR and regenerates the types |
| `backend/dxp/schema/registry.py`, `backend/dxp/identity/` (including `identity/aliases.py`, the hand-written alias map) | A02 | A03, A06, A08, A10, A13 |
| `backend/dxp/store/schemas/` (validators for `grants`, `policies`, `policy_sets`, `runs`, `admissions`, `decisions`, `actions`), `backend/dxp/gate/policy_sets.py`, `backend/dxp/gate/seed.py`, `backend/dxp/gate/seed_data/`, `backend/dxp/api/auth.py`, `backend/dxp/api/routes_grants.py` | A03 | A01's `ensure_indexes()` applies the validators; A06 and A07 call `policy_sets`; every route calls `resolve_actor`; A17 adds draft policies through its API only |
| `backend/modal_app.py`, `.github/workflows/`, `web/vercel.json`, `docs/deploy.md`; the Vercel variables `DXP_API_KEY` and `NEXT_PUBLIC_API_URL`, and the Modal secret's `DXP_AGENT_KEY`, `SLACK_WEBHOOK_URL`, `ANTHROPIC_API_KEY`, `MONGODB_URI` and `DXP_BASE_URL` (D48; set by hand, never in a file) | A04 | none; A04 edits no API file and not the README |
| `backend/dxp/sources/load.py`, `backend/dxp/sources/selected.json` | A05 | A08, A10 |
| `backend/dxp/gate/` (`__init__.py`, the checks, `decisions.py`; not `policy_sets.py`, `seed.py`, `seed_data/` or `drafts.py`), `backend/dxp/ledger/__init__.py`, `ledger/file.py`, `ledger/types.py`, `ledger/apply.py` (apply and `recover_applying`, D26) | A06 | A01's startup hook, A09, A10, A13, A14 |
| `backend/dxp/runs/` (including `runs/__init__.py` and `runs/admissions.py`: `runs.admit`, `release`, `sweep`, `settle`, `finish`; imports nothing from `actions`, D43), `backend/dxp/api/routes_runs.py` (including the sweep's background task) | A07 | A06 reads admissions; A10 calls admit, release and finish; A11 reads runs |
| `backend/dxp/llm/` (not `prompts/policy_draft.*`), `backend/dxp/evidence/` (including `evidence/__init__.py`) | A08 | A10, A17 |
| `backend/dxp/actions/` (`__init__.py`, `dispatch`, `slack.py`, `resolve`, `mark_unknown`, `mark_failed`, the fake Slack sender), `backend/dxp/api/routes_resolve.py` (`POST /actions/<action_id>/resolve`) | A09 | A07 (the sweep's background task in `routes_runs.py` calls `mark_unknown` and `mark_failed`, D43), A10 (`dispatch`), B02 and B03 (the resolve route, D53) |
| `backend/dxp/pipeline/` (and the meaning of `DXP_DEMO_PACE`) | A10 | A04 wraps the run function; A07 spawns it |
| `backend/dxp/search/audit.py`, `backend/dxp/api/routes_audit.py`, `backend/dxp/api/routes_actions.py` (the two `GET /actions` routes only; the resolve route is A09's `routes_resolve.py`) | A11 | B02 (polling), B03; B06 reads the audit response |
| `backend/dxp/search/changes.py`, `backend/dxp/api/routes_changes.py` | A12 | B02 |
| `backend/dxp/sources/fda_cdx.py`, `backend/dxp/ledger/seed.py`, `backend/dxp/api/routes_teams.py`, `scripts/reset_demo.py` and the snapshot procedure (D41) | A13 | I1 runs the commands and takes the snapshot; I2, A16 and R1 run the reset; B02 reads `GET /teams` |
| `backend/dxp/ledger/decide.py`, `ledger/review.py`, `backend/dxp/api/routes_proposals.py`, `backend/dxp/api/routes_review.py` | A14 | B04, A17 |
| `backend/dxp/search/graph.py`, `backend/dxp/api/routes_graph.py` | A15 | B05 |
| `docs/demo-and-reset.md` | A16 | none; it documents A13's reset command |
| `backend/dxp/gate/drafts.py`, `backend/dxp/llm/prompts/policy_draft.*`, `backend/dxp/api/routes_policy_drafts.py` (stretch) | A17 | none |
| `backend/dxp/search/readmodel.py`, `backend/dxp/api/routes_diagnostics.py` | A18 | B04 |
| `backend/tests/<id>/` (for example `backend/tests/a06/`, `backend/tests/i1/`) | the PR with that ID | none |
| `docs/clearance.md` (the organisers' answer on `data/` and the logo) | Luis | B07's README cites it |
| `web/` including `web/package.json` (every screen dependency installed up front; `gen:types` calls `tools/gen_types.sh`), `web/lib/api.ts`, `web/lib/features.ts`, `web/lib/format.ts` (D40 display formats), `web/components/shell/`; not `web/lib/types.ts`, `web/vercel.json` or the screen paths below | B01 | every screen |
| `web/app/runs/page.tsx`, `web/app/runs/[run_id]/page.tsx`, `web/components/run-console/` | B02 | none |
| `web/app/runs/[run_id]/audit/`, `web/components/audit/` | B03 | none; it links to B06's page behind the `audio` flag |
| `web/app/diagnostics/` (the Record page only, no list), `web/app/review/` (including the `?proposal=<p_id>` focus and "Proposal not found") | B04 | B02, B03 and B05 link to the Record page; A09's Slack alert links to both pages |
| `web/app/runs/[run_id]/impact/`, `web/components/graph/` | B05 | none |
| `backend/dxp/api/briefing.py`, `backend/dxp/api/routes_audio.py`, `web/app/runs/[run_id]/briefing/`, `web/components/briefing/` (stretch) | B06 | none |
| `README.md`, `docs/video-script.md`, `docs/submission.md` | B07 | R1 uses the script; the README links to A04's, A16's and Luis's docs. R1 adds one line, the video link, after B07 has merged and the freeze has passed (D36); no one else edits the README |

Overlaps found and removed: `backend/modal_app.py` (A01 and A04, now A04), `backend/dxp/api/app.py` (A01 and A04, now A01), `web/package.json` (A01 and B01, now B01), `README.md` (A04, A13, A16, the clearance record and B07, now B07 alone, with A04, A16 and Luis writing their own docs), `web/components/audit/audio.tsx` inside B03's directory (now B06's own briefing page), the policy-set selection and validators (now A03), `GET /schema` (A01 and A18, now A01), `evidence/__init__.py` (A01 and A08, now A08), `gate/seed.py` beside a `gate/seed/` package (A03's data is now `gate/seed_data/`), `ledger/apply.py` (now A06, D26), `scripts/reset_demo.py` (A16 and A13, now A13 alone, D41; A16 keeps only `docs/demo-and-reset.md`), and B07's duplicate NOTICE files (dropped: `data/README.md` and `scripts/data/README.md` already carry the notice). After the Slack change, `routes_reconcile.py` and `github.py` are gone; the resolve route is A09's own file `routes_resolve.py`, separate from A11's `routes_actions.py`. Files that had no owner (`backend/tests/conftest.py`, `backend/uv.lock`, the package `__init__.py` files, `.env.example`) are A01's. Checked again after these fixes and after D41: no file has two owners.

## Agent roles

- **Builders:** one per PR in the schedule. A06, A08 and A09 have no slack, so each gets a second builder for tests; A06 gets a third for `ledger/apply.py`.
- **Reviewers:** one agent per open pull request. It checks the acceptance criteria, the six required behaviours where they apply, D1 (nothing copied from `scripts/data/` or `dxp-*` skills), that the PR edits only its own files, and looks for secrets, `.env` values, tokens and PubMed text before Luis or Vlad merges.
- **Contract keeper:** watches `models.py`, the signature stubs and the generated types, and rejects a pull request that changes a contract without regenerating them.
- **Integrator:** runs I1 (including the seed and the snapshot), I2 and the S1 to S4 checks and keeps an end-to-end smoke test (one pending proposal with its notification through the fake Slack sender, one blocked action, audit read) passing on every merge after 14:00, so merges post nothing to `#all-mango-db-hackathon`. The smoke test runs in its own database, `DXP_DB=dxp_smoke`, never in the demo database `dxp` (D41).

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox. A merged PR that has not passed I1, I2 or its own S check is not done.

## Not modelled

- Claude API, Slack webhook, ClinicalTrials.gov and FDA site rate limits or outages (a Slack 429 is retried once, then `failed`, S7). The run uses low concurrency over 20 trials; agents share the same accounts' limits.
- The time Luis and Vlad spend reading and merging pull requests: 27 merges between 11:45 and 16:15, 20 on Luis's lane and 7 on Vlad's, plus the small fix PRs from I1 and I2.
- Account and third-party key setup, assumed done before 10:45. The three DxP keys (`DXP_AGENT_KEY`, `DXP_API_KEY`, `DXP_SEED_KEY`) are generated by A03 at 10:45 into `.env`, never committed (D48).
- The reset's duration: forecast 10 minutes for the video reset and 10 to 15 for the live-demo reset; not yet measured.

## Open items

| Item | Owner | Due | Until it is resolved |
|---|---|---|---|
| Atlas Sandbox access: confirm change streams (Vector Search, Automated Embedding and Agent Memory are not used on Saturday) | Luis | As soon as access arrives | A04 checks change streams at 12:00; if absent, A12 ships polling only |
| Confirm with organisers: the submission deadline, whether coding may start before 10:45, and how to present prepared material | Luis | 9:00 to 10:45 Saturday | Plan for 17:00 submission, no coding before 10:45, and the README's prepared vs built-today table |
| Ask organisers to clear, in writing, the prepared `data/` files and the prepared logo | Luis | 9:00 to 10:45 Saturday | Not cleared: A05 and A13 fetch live, B01 uses the text wordmark "DxP". Either way Luis records the answer in `docs/clearance.md`, which B07's README cites. Cleared: A05 and A13 may load the files |
| Set `DXP_BASE_URL` to the production URL and confirm the alert links resolve (S12) | Luis | During A04 (11:00 to 12:00); links rechecked in I1 once B04 is deployed | The notifier refuses to start without it, so I1 cannot send the alert |
| Keep `SLACK_WEBHOOK_URL` only in `.env` and the Modal secret; never committed, logged or shown on screen (S3, S12) | Luis | Before 10:45, and on every PR review | A09 builds and tests against the fake Slack sender; I1 cannot pass without the real webhook |
| Confirm `mongodump` and `mongorestore` run against the sandbox from Luis's laptop | Luis | I1 step 1, 13:45 to 14:00 | The reset reruns the four seed commands instead of restoring the snapshot, which may take the full 15-minute slot |
| The Slack channel is used often (D57): every run posts one alert per filed proposal to `#all-mango-db-hackathon` (tuning, I1, I2, rehearsals, the video and the live demo). Confirm this is acceptable for that channel, or point the webhook at a team channel | Luis | Before 10:45 Saturday | Plan for `#all-mango-db-hackathon`. The smoke test already uses the fake Slack sender and posts nothing. If the channel is not acceptable, the webhook points at a team channel, and the grant's Slack destination is renamed to match before A03 seeds it |
