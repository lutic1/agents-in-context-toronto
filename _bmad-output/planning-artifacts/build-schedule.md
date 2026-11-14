---
title: DxP build schedule for Saturday 14 November 2026
status: draft
created: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxP build schedule for Saturday

This schedule keeps the whole scope of `epics.md`. It plans by dependencies and agent capacity, not by summed hours, and it names the milestones that trigger a fallback cut if they are missed.

## Assumptions

- Coding starts about 9:39 and runs to 18:00: about 8 hours 20 minutes. Clock times below start from 9:39.
- Capacity: Luis runs up to 44 agents on his Claude plan. Vlad has Claude Pro, which runs one or two agents before its usage limit, plus $300 of API credit. Agents build, review, test and integrate; Luis and Vlad decide and merge.
- Task durations are agent cycle times: the story's time in `epics.md` (developer estimate × CVH factor), split where a story has separable parts. A cycle time runs from start to merge and includes tests and review.
- A module can be built against its contract before the modules it calls exist. Story 1.1 and task C3 publish those contracts in the first 90 minutes. Real wiring happens in the two integration tasks, I1 and I2.

## What limits the day

**Capacity is not the limit.** At the peak, about 29 build tasks run at once. Add a reviewer agent for each open pull request and two or three integration and contract agents, and the peak need is about 45 agents. Luis's 44 is just enough on its own, so the plan puts every Demo path build on Luis's agents. Vlad's capacity goes where people are needed, not agents.

**The dependency path is the limit.** The longest path runs through the real-data pipeline:

C1 contract (1 h) → C3 Finding fixtures (0.5 h) → 1.5 extraction calls (1.5 h) → 1.5 tuning on real items (1 h) → I1 50-item integration run (0.75 h) → 1.9 Baseline load (0.9 h) → I2 screens on production data (0.5 h) → 8.2 rehearsal (0.75 h)

That is **6.9 hours, ending about 16:33**: it fits, with about 1 hour 25 minutes to spare before 18:00. Three choices keep it that short; without them the path is about 7.6 hours and ends about 17:15, which still fits, with no room for a slip:

1. The ledger builds its Baseline-mode path first, so the seed (1.2) runs on it by about 13:20 while live mode is finished separately.
2. The Baseline load runs the 293 trials first. The 150 PubMed items continue in the background while I2 runs.
3. The web skeleton starts at 9:39 without waiting for the API contract, so the graph component starts at 10:24. Otherwise the graph screens become the longest path, about 7.5 hours, ending about 17:09.

The next-longest paths are the graph screens and the Home hero, which finish about 14:54 with about 25 minutes of slack before I2, and Value history (2.5), which finishes about 16:39. The Review screen finishes about 13:54, with about 1.5 hours of slack.

## Who does what

Luis has the agent capacity; Vlad has a person's time, a small agent budget and the API key the product itself runs on. So Luis builds everything on the Demo path, and Vlad owns the work that needs a person and five small stories that nothing else depends on.

**Luis (up to 44 agents):** the contracts (C1, C2, C3), the whole pipeline (1.4 to 1.7, 1.2), the review loop (2.2 to 2.7), Alerts (3.1 to 3.3, 3.5), Find and Categories (4.1 to 4.7), the graph (5.1 to 5.3), memory and Home (6.1 to 6.4), the shell (1.12) and both integration runs. Luis merges the API lane.

**Vlad (a person, one or two agents, $300 of API credit):**

| When | What | Kind |
|---|---|---|
| 9:39 to 11:39 | Story 8.1: CI, Modal and Vercel deploys, secrets in Modal and Vercel; Vlad is the one person who runs `modal deploy` | Person, one agent |
| From 11:39 | Merges the web lane's pull requests after Luis's reviewer agents have checked them | Person |
| From 11:39, in the background | Five isolated stories, in this order: 3.4 audio briefing, 1.11 Tavily scan, 1.10 scheduled scan, 7.1 quick capture, 4.8 unmatched terms page. About 5.2 hours of agent time | One or two agents |
| 14:24 to 15:19 | Runs the Baseline load in production (1.9) and saves the snapshot | Person |
| 14:24 to 14:54 | Reads the dry run (2.1) and picks the items to show on camera | Person |
| 15:00 to 16:00 | Story 8.3 README and submission text; the HeyGen intro and close clips | Person, one agent |
| 15:49 to 16:34 | Rehearsal (8.2) with Luis: Vlad drives the live run, Luis watches the screens | Person |

**Forecast for Vlad's stories.** With one or two agents, about 5.2 hours of agent time lands by about 15:00 if Pro's usage limit holds through the morning. If the limit stops Vlad's agents, he switches Claude Code to the API key for the rest of them. These five are the first fallback cuts anyway, so a slip here never touches the Demo path. If Vlad finishes early, he takes 4.5 export and 4.7 add-a-value from Luis's list, in that order.

**API budget ($300, on Vlad's account).** The product's own calls come first. Extraction on Sonnet 5.5 is about $14 per 500 items (from `dxp-claude-api`), and the quote check roughly doubles it. Saturday runs about 800 items: the 50-item test, the 443-item Baseline, the dry run, the rehearsal, two retakes and the tuning items. Add the rule drafts, why lines, query parsing and resume summaries, and the product needs about $50 to $80. Keep $100 for it. That leaves about $200 for Vlad's coding agents if Pro runs out. Set a spend alert at $150, and never let coding agents spend the product's share. [ASSUMPTION: the product uses Vlad's API key; Luis's Claude plan does not include API credit.]

## Schedule

| Task | Owner | What | Depends on | Cycle time | Start | Finish | |
|---|---|---|---|---|---|---|---|
| C4 | Luis | Web skeleton: create-next-app, shadcn, api.ts (1.3) | none | 0.75 h | 09:39 | 10:24 | |
| C1 | Luis | API models, OpenAPI, generated types, store, indexes (1.1) | none | 1 h | 09:39 | 10:39 | **critical** |
| C2 | Luis | Registry and identity (1.2) | none | 1 h | 09:39 | 10:39 | |
| 4.8 | Vlad | Unmatched terms page (4.8) | C4 | 1 h | 10:24 | 11:24 | |
| 1.8 | Luis | Jobs page (1.8) | C4 | 2 h | 10:24 | 12:24 | |
| 2.7 | Luis | Rules on screen (2.7) | C4 | 2 h | 10:24 | 12:24 | |
| 3.2 | Luis | Alerts inbox (3.2) | C4 | 2 h | 10:24 | 12:24 | |
| 3.3 | Luis | Digest (3.3) | C4 | 2 h | 10:24 | 12:24 | |
| 6.4b | Luis | Home welcome panel, Alerts and Digest layout (6.4) | C4 | 2 h | 10:24 | 12:24 | |
| 4.6 | Luis | Category landscape (4.6) | C4 | 2 h | 10:24 | 12:24 | |
| 5.2a | Luis | Graph component (5.2) | C4 | 2.5 h | 10:24 | 12:54 | |
| 1.12 | Luis | App shell (1.12) | C4 | 3 h | 10:24 | 13:24 | |
| 2.4 | Luis | Review screen (2.4) | C4 | 3.5 h | 10:24 | 13:54 | |
| 4.3 | Luis | Comparison table (4.3) | C4 | 3.5 h | 10:24 | 13:54 | |
| C3 | Luis | Finding fixtures and module interfaces (llm, ledger.file, job item) | C1, C2 | 0.5 h | 10:39 | 11:09 | **critical** |
| 1.4 | Luis | Load Source items (1.4) | C1 | 0.6 h | 10:39 | 11:15 | |
| C5 | Vlad | CI, Modal and Vercel walking skeleton (8.1) | C1, C4 | 1 h | 10:39 | 11:39 | |
| 1.1b | Luis | Read model and /changes (1.1) | C1 | 1 h | 10:39 | 11:39 | |
| 6.1 | Luis | Memory adapter, two backends (6.1) | C1 | 3 h | 10:39 | 13:39 | |
| 4.1 | Luis | Search indexes and synonyms (4.1) | C1 | 4.8 h | 10:39 | 15:27 | |
| 2.2 | Luis | Proposals queue API (2.2) | C3 | 0.9 h | 11:09 | 12:03 | |
| 1.5b | Luis | Quote check and supported check (1.5) | C3 | 1 h | 11:09 | 12:09 | |
| 4.7 | Luis | Add a value API (4.7) | C3 | 1.2 h | 11:09 | 12:21 | |
| 1.11 | Vlad | Tavily provider scan (1.11) | C3 | 1.2 h | 11:09 | 12:21 | |
| 7.1 | Vlad | Quick capture (7.1) | C3 | 1.2 h | 11:09 | 12:21 | |
| 1.6m | Luis | Ledger baseline-mode path first (1.6) | C3 | 1.4 h | 11:09 | 12:33 | |
| 1.5a | Luis | Triage and extraction calls (1.5) | C3 | 1.5 h | 11:09 | 12:39 | **critical** |
| 2.3 | Luis | Decisions API (2.3) | C3 | 1.5 h | 11:09 | 12:39 | |
| 2.6 | Luis | Learned rules API (2.6) | C3 | 2.4 h | 11:09 | 13:33 | |
| 5.1 | Luis | Graph API (5.1) | C3 | 2.4 h | 11:09 | 13:33 | |
| 1.7 | Luis | Batch job with stubbed extraction and ledger (1.7) | C3 | 2.5 h | 11:09 | 13:39 | |
| 3.1 | Luis | Alerts API (3.1) | C3 | 2.8 h | 11:09 | 13:57 | |
| 4.2 | Luis | Plain-language query, two agents: parsing and ranking (4.2) | C3 | 2.8 h | 11:09 | 13:57 | |
| 8.3 | Vlad | Submission package (8.3) | C5 | 1 h | 11:39 | 12:39 | |
| 1.3 | Luis | Diagnostics and Record pages (1.3) | C4, 1.1b | 3.5 h | 11:39 | 15:09 | |
| 3.5 | Luis | Play button (3.5) | 3.2 | 1 h | 12:24 | 13:24 | |
| 1.6 | Luis | Ledger live mode, pending and stage rules (1.6) | 1.6m | 0.7 h | 12:33 | 13:15 | |
| 1.2b | Luis | Seed FDA rows, Teams and terms through the ledger (1.2) | 1.6m, C2 | 0.75 h | 12:33 | 13:18 | |
| 1.5c | Luis | Tune extraction on 20 real items (1.5) | 1.5a, 1.5b, 1.4 | 1 h | 12:39 | 13:39 | **critical** |
| 5.2b | Luis | Graph page, click-through and focus, two agents (5.2) | 5.2a | 2 h | 12:54 | 14:54 | |
| 5.3 | Luis | Changed highlight, pulse and live updates, two agents (5.3) | 5.2a | 2 h | 12:54 | 14:54 | |
| 6.4a | Luis | Home hero network (6.4) | 5.2a | 2 h | 12:54 | 14:54 | |
| 6.2 | Luis | Synthetic Team history (6.2) | 6.1, 1.2b | 0.6 h | 13:39 | 14:15 | |
| I1 | Luis | Integration: 50-item run on the dev database | 1.5c, 1.6, 1.7, 1.4, 1.2b | 0.75 h | 13:39 | 14:24 | **critical** |
| 1.10 | Vlad | Scheduled scan (1.10) | 1.7 | 0.9 h | 13:39 | 14:33 | |
| 6.3 | Luis | Resume summary (6.3) | 6.1, 1.1b | 1.6 h | 13:39 | 15:15 | |
| 4.5 | Luis | Export (4.5) | 4.3 | 0.9 h | 13:54 | 14:48 | |
| 4.4 | Luis | Shortlist (4.4) | 4.3 | 2 h | 13:54 | 15:54 | |
| 3.4 | Vlad | Audio briefing (3.4) | 3.1 | 0.9 h | 13:57 | 14:51 | |
| 2.1 | Vlad | Dry run of the Held-back set on the dev database (2.1) | I1 | 0.5 h | 14:24 | 14:54 | |
| 1.9 | Vlad | Baseline load in production: trials first, PubMed continues in the background (1.9) | I1, 1.2b, C5 | 0.9 h | 14:24 | 15:18 | **critical** |
| 2.5 | Luis | Value history (2.5) | 1.3 | 1.5 h | 15:09 | 16:39 | |
| I2 | Both | Integration: every demo screen on production data | 1.9, 1.3, 1.12, 1.8, 2.4, 2.7, 3.2, 3.3, 5.2b, 5.3, 6.4a, 6.4b, 2.2, 2.3, 2.6, 3.1, 5.1, 6.2, 6.3 | 0.5 h | 15:18 | 15:48 | **critical** |
| 8.2 | Both | Rehearsal: live run, decisions, rule, memory, restore (8.2) | I2, 2.1 | 0.75 h | 15:48 | 16:33 | **critical** |

## Milestones and fallback triggers

Cuts are triggered by a missed milestone, not decided in advance.

| By | Milestone | If missed |
|---|---|---|
| 11:09 | C1, C2 and C3 merged: types generated, registry, identity and Finding fixtures published | Everything slips one for one. Hold all other merges until the contracts land |
| 11:39 | CI and the walking skeleton deployed to Modal and Vercel (8.1) | One person fixes the deploy while the rest continue; nothing merges to production until it works |
| 13:19 | Seed in the dev database through the ledger | Seed directly in Baseline mode with a script, and reconcile it in I1 |
| 13:39 | Extraction passes on 20 real items with quotes found | Narrow the Baseline to the 100 most recent trials (about 20 minutes) |
| 14:24 | I1 passes: 50 items, one forced failure, no duplicates | Run the Baseline anyway, on whatever passes. Skip the separate dry run (2.1) and rely on the I1 data to pick the camera items |
| 15:19 | Baseline in production and the snapshot saved | Rehearse on the dev database, and record from production after 18:00 |
| 15:49 | I2 passes: every demo screen shows production data | Drop the stories that are not on the Demo path from the rehearsal; leave them deployed if they work |
| 16:34 | Rehearsal done and the database restored | Record what works; the video names only behaviour shown live |

If a fallback is triggered, these go first, in this order, because no Demo path story needs them: 7.1, 1.11, 1.10, 4.8, 4.6 with 4.7, 4.5, 4.4, then 3.4 with 3.5.

## Who owns which files

Extra agents only help if two of them never edit the same module at once.

| Module | Owner | Others call it, never edit it |
|---|---|---|
| `backend/dxp/api/models.py`, `store`, read model | C1 (Story 1.1) | Every story; a change goes through a pull request that regenerates `web/lib/types.ts` |
| `schema/registry.py`, `identity` | C2 (Story 1.2) | 1.5, 1.6, 4.6 (the Category map is added by 4.6 as its own function) |
| `ledger/file.py` (filing, modes, stage rule) | 1.6 | 1.2 seeds through it; 1.7 calls it |
| `ledger/seed.py` | 1.2 | none |
| `ledger/decide.py` (claim and apply a decision, review a value) | 2.3 | 2.4 calls it through the API |
| `llm` | 1.5 | 2.6, 3.1, 4.2, 6.3 add their own prompt files; only 1.5 edits the client |
| `memory` | 6.1 | 2.6, 6.2, 6.3 |
| `web/components/graph` | 5.2 | 6.4 reuses it; only 5.2 edits it |
| `web/components/shell` (top bar, tokens, badges) | 1.12 | every screen |

## Agent roles

- **Builders:** one per task in the schedule, more for the tasks marked "two agents".
- **Reviewers:** one agent per open pull request. It checks the acceptance criteria and looks for secrets, `.env` values and PubMed text before Luis or Vlad merges.
- **Contract keeper:** watches `models.py` and the generated types, and rejects a pull request that changes a contract without regenerating them.
- **Integrators:** run I1 and I2 and keep an end-to-end smoke test passing on every merge.

## Not modelled

- Claude API rate limits: the pipeline is set to 16 concurrent calls (Story 1.7), and agents share the same account's limits.
- The time Luis and Vlad spend reading and merging pull requests: about 45 merges in about 8 hours 20 minutes, one every 11 minutes or so for the two of them.
- Account and key setup, assumed done on Friday.

## Open questions

1. When is the submission due? `epics.md` plans the video after 18:00, about 30 minutes. If the video must be in by 18:00, coding ends about 17:15; the path above still fits, with about 40 minutes to spare.
