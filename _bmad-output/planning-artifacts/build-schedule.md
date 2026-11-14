---
title: DxP build schedule for Saturday 14 November 2026
status: draft
created: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxP build schedule for Saturday

This schedule keeps the whole scope of `epics.md`. The PR-by-PR assignment that agents work from is `development-plan.md`. It plans by dependencies and agent capacity, not by summed hours, and it names the milestones that trigger a fallback cut if they are missed.

## Assumptions

- Coding starts about 9:39. Until the submission deadline is confirmed, the plan assumes the earliest plausible one, 18:00 with the video included: coding stops at 17:15, the video is recorded 17:15 to 17:45 and the submission goes in by 17:55. Clock times below start from 9:39.
- Capacity: Luis runs up to 44 agents on Luis's Claude plan and holds the product's API key. Vlad has Claude Pro plus $300 of API credit and runs Sonnet 5.5 at high effort through ten subagents. Agents build, review, test and integrate; Luis and Vlad decide and merge.
- Task durations are agent cycle times: the story's time in `epics.md` (developer estimate × CVH factor), split where a story has separable parts. A cycle time runs from start to merge and includes tests and review.
- A module can be built against its contract before the modules it calls exist. Story 1.1 and task C3 publish those contracts in the first 90 minutes. Real wiring happens in the two integration tasks, I1 and I2.

## What limits the day

**Capacity is not the limit.** At the peak, about 19 builders run in Luis's lane and 10 in Vlad's. Reviewer agents, the contract keeper and the integrators take the rest of Luis's 44 slots.

**The dependency path is the limit, and several paths are close.** With contracts frozen in the first hour and start requirements separate from merge requirements (see `development-plan.md`), the model gives:

| Path | Reaches final acceptance (P38) | Slack |
|---|---|---|
| Web skeleton → graph component → graph page, changed highlight, Home hero | 14:54 | none: this is the critical path |
| Contracts → extraction → tuning → 50-item run (P15) → Baseline load (P16) | 14:48 | 6 minutes |
| 50-item run → screens on the small ingest (P42) | 14:24 | 30 minutes |
| Memory adapter → resume summary | 14:15 | 39 minutes |
| Every other screen and API | by 13:54 | an hour or more |

Final acceptance runs 14:54 to 15:24 and the rehearsal 15:24 to 16:09. That leaves **about 1 hour 6 minutes before the 17:15 code freeze**, but three paths arrive within six minutes of each other, so a slip on any of them moves the end. These are forecasts from a model, not a validated run; the milestones below are where the day checks them.

What keeps the paths this short:

1. P01, P02 and P04 start together at 9:39. The Finding fixtures are drafted from the architecture spine and validated when the contracts merge, so nothing waits an extra hour for them.
2. The web skeleton and the memory adapter start at 9:39, because neither needs the API contract to begin.
3. The ledger builds its Baseline-mode path first, so the seed runs on it at 12:03.
4. The Baseline load runs the trials first; the PubMed items continue in the background during final acceptance.

**The 50-item run (P15) needs five things, and the schedule tracks each:**

| Needed | PR | Ready | Slack |
|---|---|---|---|
| Tuned extraction | P14 | 13:09 | none |
| Batch job | P12 | 13:09 | none |
| Ledger, live mode | P13 | 12:45 | 24 minutes |
| Seed | P11 | 12:48 | 21 minutes |
| Source items loaded | P07 | 11:15 | about 2 hours |
| Production environment and CI | P06 | 11:39 | 90 minutes |

**The rehearsal needs** final acceptance, the dry run (P17, ready 14:24) and, through final acceptance, the review loop, rules, Alerts and memory APIs, all merged by 14:15 at the latest.

## Who does what

Both people build from 9:39. Luis has the agent capacity and the product's API key, so Luis takes the critical path, the ingest pipeline, the three integration checks and every production task. Vlad takes Find and Categories (Epic 4), three screens whose files are independent of Luis's (Jobs page, Digest, Rules on screen), five isolated stories and Value history. The PR-by-PR assignment, with start and merge requirements and owned files, is in `development-plan.md`.

**Luis (up to 44 agents, the product's API key):** contracts (P01 to P04), read model, deploys and CI, the ingest pipeline (P07 to P15), the review loop and Alerts APIs, graph, memory, Home, the shell, Review and Alerts inbox screens, Diagnostics and Record, the Baseline load, the dry run, the three integration checks (P41, P42, P38), the rehearsal and the submission. Luis coordinates merges on Luis's lane.

**Vlad (Claude Pro plus $300 of API credit, Sonnet 5.5 at high effort, ten subagents):** V01 to V19, about 39 agent-hours on Sonnet. The Jobs page, Digest and Rules screens finish about 12:54, two hours before final acceptance needs them. Epic 4 finishes by about 15:24 and the whole lane about 15:49. Vlad coordinates merges on Vlad's lane after Luis's review agent passes each PR.

- [ASSUMPTION: Sonnet 5.5 at high effort takes about 1.25 times as long per story as the Opus 5.5 agents the CVH factors were measured on.]
- Vlad's stories need one developer database in Atlas; Luis shares its connection string through `.env`, never in the repository.
- If Vlad's lane falls behind, the cut order in the milestones section applies first to 7.1, 1.11, 1.10 and 4.8. The three moved screens are on the Demo path, so if they slip past 14:00, Luis's agents take them back.

**Review of Vlad's lane.** One review agent run by Luis checks each of Vlad's PRs against its acceptance criteria and for secrets, `.env` values and PubMed text, at about 15 minutes a PR. Between about 12:15 and 14:00 most of Vlad's PRs arrive; if a PR waits more than 30 minutes, Luis starts a second review agent.

**Forecast for Vlad's credit.** Sonnet 5.5 costs half of Opus 5.5 ($2 and $10 per million input and output tokens). [ASSUMPTION: a Sonnet subagent costs about $5 an hour on the API, mostly cache reads, and the main agent coordinating ten adds about a quarter on top; Pro covers the first hour or two.] About 39 agent-hours is then about $240, leaving about $60. At the morning peak, ten subagents spend about $50 to $60 an hour. Check at 10:39: above $60 an hour, cap the subagents at six and drop 7.1 and 1.10.

**Product API budget (Luis's key).** About 800 items on Saturday, plus rule drafts, why lines, query parsing and resume summaries: about $50 to $80. Set a spend alert at $100.

## Schedule

Start requirements and merge requirements for each PR are in `development-plan.md`. Vlad's times assume ten Sonnet subagents with cycle times 1.25 times the Opus figures.

| PR | Owner | What | Cycle time | Start | Finish | Path |
|---|---|---|---|---|---|---|
| P03 | Luis | Web skeleton | 0.75 h | 09:39 | 10:24 | critical |
| P01 | Luis | API contract stub and generated types | 1 h | 09:39 | 10:39 | near-critical |
| P02 | Luis | Registry and identity | 1 h | 09:39 | 10:39 | |
| P04 | Luis | Finding contract and module interfaces | 1 h | 09:39 | 10:39 | near-critical |
| P23 | Luis | Memory adapter | 3 h | 09:39 | 12:39 | |
| V01 | Vlad | Unmatched terms page | 1.25 h | 10:24 | 11:39 | |
| V02 | Vlad | Comparison table: Evidence panel and keyboard | 1.875 h | 10:24 | 12:17 | |
| P34 | Luis | Home welcome panel, Alerts and Digest layout | 2 h | 10:24 | 12:24 | |
| P31 | Luis | Alerts inbox | 2 h | 10:24 | 12:24 | |
| P33 | Luis | Graph component | 2.5 h | 10:24 | 12:54 | critical |
| V17 | Vlad | Jobs page | 2.5 h | 10:24 | 12:54 | |
| V18 | Vlad | Digest | 2.5 h | 10:24 | 12:54 | |
| V19 | Vlad | Rules on screen | 2.5 h | 10:24 | 12:54 | |
| V06 | Vlad | Comparison table and chips | 2.5 h | 10:24 | 12:54 | |
| V07 | Vlad | Category landscape | 2.5 h | 10:24 | 12:54 | |
| P27 | Luis | App shell | 3 h | 10:24 | 13:24 | |
| P26 | Luis | Diagnostics and Record pages | 3.5 h | 10:24 | 13:54 | |
| P29 | Luis | Review screen | 3.5 h | 10:24 | 13:54 | |
| P07 | Luis | Load Source items | 0.6 h | 10:39 | 11:15 | |
| P18 | Luis | Proposals queue API | 0.9 h | 10:39 | 11:33 | |
| P06 | Luis | Deploy and CI | 1 h | 10:39 | 11:39 | |
| P05 | Luis | Read model and change feed | 1 h | 10:39 | 11:39 | |
| P09 | Luis | Quote and support checks | 1 h | 10:39 | 11:39 | |
| P10 | Luis | Ledger, Baseline mode | 1.4 h | 10:39 | 12:03 | |
| P08 | Luis | Triage and extraction calls | 1.5 h | 10:39 | 12:09 | near-critical |
| P19 | Luis | Decisions API | 1.5 h | 10:39 | 12:09 | |
| P20 | Luis | Learned rules API | 2.4 h | 10:39 | 13:03 | |
| P22 | Luis | Graph API | 2.4 h | 10:39 | 13:03 | |
| P12 | Luis | Batch job | 2.5 h | 10:39 | 13:09 | near-critical |
| P21 | Luis | Alerts API | 2.8 h | 10:39 | 13:27 | |
| V08 | Vlad | Search index with synonyms | 2.875 h | 10:39 | 13:31 | |
| V09 | Vlad | Vector Search index | 3.125 h | 10:39 | 13:47 | |
| V11 | Vlad | Plain-language query API | 3.5 h | 10:39 | 14:09 | |
| P40 | Luis | Submission package | 1 h | 11:39 | 12:39 | |
| V03 | Vlad | Add a value API | 1.5 h | 11:39 | 13:09 | |
| P13 | Luis | Ledger, live mode and stage rule | 0.7 h | 12:03 | 12:45 | |
| P11 | Luis | Seed FDA rows, Teams and terms | 0.75 h | 12:03 | 12:48 | |
| P14 | Luis | Tune extraction on real items | 1 h | 12:09 | 13:09 | near-critical |
| V04 | Vlad | Tavily provider scan | 1.5 h | 12:17 | 13:47 | |
| P25 | Luis | Resume summary | 1.6 h | 12:39 | 14:15 | |
| P41 | Luis | Integration: screens on seeded records | 0.5 h | 12:48 | 13:18 | |
| P24 | Luis | Synthetic Team history | 0.6 h | 12:48 | 13:24 | |
| V10 | Vlad | Export | 1.125 h | 12:54 | 14:01 | |
| V05 | Vlad | Quick capture | 1.5 h | 12:54 | 14:24 | |
| P35 | Luis | Graph page | 2 h | 12:54 | 14:54 | critical |
| P36 | Luis | Changed highlight | 2 h | 12:54 | 14:54 | critical |
| P37 | Luis | Home hero network | 2 h | 12:54 | 14:54 | critical |
| V14 | Vlad | Shortlist | 2.5 h | 12:54 | 15:24 | |
| P15 | Luis | Integration run: 50 items | 0.75 h | 13:09 | 13:54 | near-critical |
| V12 | Vlad | Scheduled scan | 1.125 h | 13:09 | 14:17 | |
| V13 | Vlad | Audio briefing | 1.125 h | 13:27 | 14:35 | |
| P42 | Luis | Integration: screens on the small real ingest | 0.5 h | 13:54 | 14:24 | |
| P17 | Luis | Dry run of the Held-back set | 0.5 h | 13:54 | 14:24 | |
| P16 | Luis | Baseline load and snapshot | 0.9 h | 13:54 | 14:48 | near-critical |
| V16 | Vlad | Value history | 1.875 h | 13:54 | 15:47 | |
| V15 | Vlad | Play button | 1.25 h | 14:35 | 15:49 | |
| P38 | Luis | Final acceptance on production data | 0.5 h | 14:54 | 15:24 | critical |
| P39 | Luis | Rehearsal | 0.75 h | 15:24 | 16:09 | critical |

## Milestones and fallback triggers

Cuts are triggered by a missed milestone, not decided in advance.

| By | Milestone | If missed |
|---|---|---|
| 10:39 | P01, P02 and P04 merged: routes, shapes, errors, signatures and Finding fixtures frozen | Everything slips one for one. Hold other merges until the contracts land |
| 11:39 | CI and the walking skeleton deployed to Modal and Vercel (P06) | One agent fixes the deploy while the rest continue; nothing merges to production until it works |
| 12:48 | Seed in the dev database through the ledger (P11) | Seed directly in Baseline mode with a script, and reconcile it in P15 |
| 13:09 | Extraction passes on 20 real items with quotes found (P14) | Narrow the Baseline to the 100 most recent trials (about 20 minutes) |
| 13:18 | Screens on seeded records (P41) | Fix before more screens merge; a broken contract shows here first |
| 13:54 | 50-item run passes: one forced failure, no duplicates (P15) | Run the Baseline anyway, on whatever passes. Skip the separate dry run (P17) and pick camera items from the P15 data |
| 14:24 | Screens on the small real ingest (P42) | Fix the read model or the screen before the Baseline finishes |
| 14:48 | Baseline in production and the snapshot saved (P16) | Rehearse on the dev database; record from production at 17:15 if the Baseline is in by then |
| 14:54 | Graph page, changed highlight and Home hero merged (P35, P36, P37) | Rehearse with the graph as it is; the Home hero falls back to the welcome panel alone |
| 15:24 | Final acceptance on production data (P38) | Drop the stories that are not on the Demo path from the rehearsal; leave them deployed if they work |
| 16:09 | Rehearsal done and the database restored (P39) | Use the time to 17:15 to fix and rehearse again |
| 17:15 | Code freeze; record the video (Story 8.4) | Record what works; the video names only behaviour shown live |
| 17:55 | Submission in: description, repository link, video | Submit what exists at 17:55 |

If a fallback is triggered, these go first, in this order, because no Demo path story needs them: 7.1, 1.11, 1.10, 4.8, 4.6 with 4.7, 4.5, 4.4, then 3.4 with 3.5.

## Who owns which files

Extra agents only help if two of them never edit the same module at once.

| Module | Owner | Others call it, never edit it |
|---|---|---|
| `backend/dxp/api/models.py`, `store`, read model | P01 and P05 (Story 1.1) | Every story; a change goes through a pull request that regenerates `web/lib/types.ts` |
| `schema/registry.py`, `identity` | P02 (Story 1.2) | 1.5, 1.6; the Category map lives in Vlad's `schema/categories.py` (V07) |
| `ledger/file.py` (filing, modes, stage rule) | 1.6 | 1.2 seeds through it; 1.7 calls it |
| `ledger/seed.py` | 1.2 | none |
| `ledger/decide.py` (claim and apply a decision, review a value) | 2.3 | 2.4 calls it through the API |
| `llm` | 1.5 | 2.6, 3.1, 4.2, 6.3 add their own prompt files; only 1.5 edits the client |
| `memory` | 6.1 | 2.6, 6.2, 6.3 |
| `web/components/graph` | 5.2 | 6.4 reuses it; only 5.2 edits it |
| `web/components/shell` (top bar, tokens, badges) | 1.12 | every screen |
| `web/components/rule-panel` | V19 (Story 2.7, Vlad) | P29 Review screen embeds it |
| `web/components/digest` | V18 (Story 3.3, Vlad) | P34 Home embeds it |
| `web/components/alert-item` | P31 (Story 3.2) | V15 adds `audio.tsx` beside it; P34 Home embeds it |
| `search/completeness.py`, `schema/categories.py` | V07 (Story 4.6, Vlad) | P05's read model calls `completeness()` through its frozen signature |

## Agent roles

- **Builders:** one per task in the schedule, more for the tasks marked "two agents".
- **Reviewers:** one agent per open pull request. It checks the acceptance criteria and looks for secrets, `.env` values and PubMed text before Luis or Vlad merges.
- **Contract keeper:** watches `models.py` and the generated types, and rejects a pull request that changes a contract without regenerating them.
- **Integrators:** run I1 and I2 and keep an end-to-end smoke test passing on every merge.

## Not modelled

- Claude API rate limits: the pipeline is set to 16 concurrent calls (Story 1.7), and agents share the same account's limits.
- The time Luis and Vlad spend reading and merging pull requests: 58 merges in about 7 hours 36 minutes: 39 on Luis's lane (one every 12 minutes or so) and 19 on Vlad's.
- Account and key setup, assumed done on Friday.

## Open items

| Item | Owner | Due | Until it is resolved |
|---|---|---|---|
| Update the architecture spine's AD-14 with the fields and routes `epics.md` adds (listed under "Departures" there), so agents have one reference | Luis | Before P01 merges, about 10:39 on Saturday | P01's card is the reference for those fields; no other PR codes against them before P01 merges |
| Confirm the submission deadline with the organisers, and whether it includes the video | Luis | 9:39 on Saturday | Plan for the earliest plausible deadline: code freeze 17:15, record 17:15 to 17:45, submit by 17:55 |

The PASS from sprint planning means the plan and tracking are ready. It does not prove the delivery schedule fits; the milestones above are how the day tests that.
