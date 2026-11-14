---
title: DxP build schedule for Saturday 14 November 2026
status: draft
created: 2026-11-13
updated: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxP build schedule for Saturday

This schedule follows the approved course correction in `sprint-change-proposal-2026-11-13.md`: DxP is pitched and built for Statement 1, "Agents You Can Audit", and the governed agent is the product. The PR-by-PR assignment that agents work from is `development-plan.md`. This file plans by dependencies and agent capacity, and names the milestones that trigger a fallback cut if they are missed.

## Assumptions

- Hacking runs 10:45 to 17:00. No coding before 10:45 unless an organiser permits it in writing. 9:00 to 10:45 is doors, breakfast and kick-off; Luis uses it to confirm the open items below with the organisers.
- Code freeze is 16:30. The 60-second video is recorded 16:30 to 16:50. The submission (description, public repository, video, team members) goes in by 16:55. The live 3-minute demo for judging starts at 17:15.
- We build on the Atlas Sandbox from the start. Our own cluster is not the final environment. Change streams must be confirmed on the sandbox tier before the live feed depends on them.
- Capacity: Luis runs up to 44 agents on Luis's Claude plan and holds the product's API key. Vlad has Claude Pro plus $300 of API credit and runs Sonnet 5.5 at high effort through ten subagents. Luis's review agent reviews every PR on Vlad's lane. Agents build, review, test and integrate; Luis and Vlad decide and merge.
- A module can be built against its contract before the modules it calls exist. A01 and A02 freeze the contracts by 11:45. Real wiring happens in the two integration PRs, I1 and I2.
- Every time below is a model forecast, not a validated run. The milestones are where the day checks them.

## Timeline

| Time | What |
|---|---|
| 9:00 to 10:45 | Doors, breakfast, kick-off. No coding. Luis confirms the deadline, sandbox access and the prepared-material rules with the organisers |
| 10:45 | Hacking starts: contracts (A01, A02), web skeleton (B01), deploy on the sandbox (A04), grants and policies (A03) |
| 11:45 | Contracts frozen; everything else builds in parallel against them |
| 13:45 | Gate, extraction and the GitHub action merged; I1 starts |
| **14:30** | **First complete allowed-and-blocked loop on the sandbox:** one real issue created, one action blocked before execution, the audit reconstructs both |
| 14:30 to 15:00 | Supporting screens integrated, stop control proven; stretch only if the loop is green |
| 15:00 to 15:30 | Final acceptance (I2) |
| 15:30 to 16:15 | Live-demo rehearsal and reset (A16); recording preparation starts |
| 16:30 | Code freeze |
| 16:30 to 16:50 | Record the 60-second video |
| By 16:55 | Submit |
| 17:15 | Live 3-minute demo |

## What limits the day

**Capacity is not the limit.** At the peak, about 11 builders run in Luis's lane and 5 in Vlad's. Reviewer agents, the contract keeper and the integrator take a fraction of Luis's 44 slots.

**The dependency path is the limit.** The critical path is:

A01 contract (10:45 to 11:45) → A06 ledger and gate, A09 GitHub action, A08 extraction, A07 runs and stop, A10 the run, built in parallel (11:45 to 13:45) → I1 the allowed-and-blocked loop (13:45 to 14:30) → I2 final acceptance (15:00 to 15:30) → A16 rehearsal (15:30 to 16:15) → code freeze at 16:30.

| Path | Ready | Needed by | Slack |
|---|---|---|---|
| A06 ledger and gate, A08 extraction, A09 GitHub action | 13:45 | I1 at 13:45 | none |
| A13 seed through the ledger | 13:45 | I1 at 13:45 | none, and it cannot merge before A06 |
| A10 the run | 13:30 | I1 at 13:45 | 15 minutes |
| A07 runs and stop, A11 audit API | 13:15 | I1 at 13:45 | 30 minutes |
| A12 change feed | 13:00 | I1 at 13:45 | 45 minutes |
| A05 selected trial set, A03 grants and policies | 12:15 | I1 at 13:45 | 90 minutes |
| I1 loop green | 14:30 | I2 at 15:00 | 30 minutes |
| B05 impact view | 14:30 | I2 at 15:00 | 30 minutes |
| B02 run console | 14:15 | I2 at 15:00 | 45 minutes |
| B03 audit view, B04 record and review | 14:00 | I2 at 15:00 | 1 hour |
| A16 rehearsal done | 16:15 | code freeze at 16:30 | 15 minutes |

Read honestly: four PRs reach I1 with no slack, and the whole chain from 13:45 to the freeze holds about 45 minutes of float (30 minutes before I2 and 15 after the rehearsal). A slip of more than 45 minutes in any of A06, A08, A09 or A13 pushes the rehearsal into the freeze. The 13:45 and 14:30 milestones are where that shows first.

What keeps the path this short:

1. A01, A02, A03 and B01 start together at 10:45. A03 drafts against the A01 shapes and merges after A01.
2. Every builder after 11:45 codes against the frozen signatures, so A06, A07, A08, A09, A10 and A11 run side by side instead of one after another.
3. The batch is a selected set of 10 to 20 held-back trials, not 443 items, so the run itself is short.
4. The 30 minutes between I1 and I2 are kept for supporting integration and the stop proof, not for new features.

## Who does what

Luis owns the critical path: the contract, the ledger and gate, runs and stop, extraction, the GitHub action, the audit API and both integrations. Vlad owns the screens, the web skeleton, the stretch audio and the submission package. The PR-by-PR assignment, with start and merge requirements and owned files, is in `development-plan.md`.

**Luis (up to 44 agents, the product's API key):** A01 to A17, I1 and I2. Luis coordinates merges on Luis's lane and runs the review agent on Vlad's lane.

**Vlad (Claude Pro plus $300 of API credit, Sonnet 5.5 at high effort, ten subagents):** B01 to B07. Vlad coordinates merges on Vlad's lane after Luis's review agent passes each PR.

- Vlad's PRs need the Atlas Sandbox connection string; Luis shares it through `.env`, never in the repository.
- If Vlad's lane falls behind, B06 is cut first. B02 and B03 are core screens: if either is not merged by 14:15, Luis's agents take it over.

**Review of Vlad's lane.** One review agent run by Luis checks each of Vlad's PRs against its acceptance criteria and for secrets, `.env` values, tokens and PubMed text, at about 15 minutes a PR. Most of Vlad's PRs arrive between 14:00 and 14:30; if a PR waits more than 20 minutes, Luis starts a second review agent.

**Forecast for Vlad's credit.** Vlad's lane is now seven PRs. [ASSUMPTION: a Sonnet 5.5 subagent costs about $5 an agent-hour on the API, mostly cache reads, including the main agent's coordination.] Roughly 15 to 20 agent-hours is about $100, well inside the $300. Check the spend at 11:45: if it is running above $40 an hour, cap the subagents at six and drop B06.

**Product API budget (Luis's key).** The selected set is 10 to 20 trials, run a few times during tuning, I1, I2 and the rehearsal, plus the stretch policy draft. Set a spend alert at $50.

## Schedule

Start requirements and merge requirements for each PR are in `development-plan.md`.

| PR | Owner | What | Start | Finish | Path |
|---|---|---|---|---|---|
| A01 | Luis | Contract: routes, shapes, error shape, frozen signatures | 10:45 | 11:45 | critical |
| A02 | Luis | Registry and identity | 10:45 | 11:45 | critical |
| A03 | Luis | Grants and policies, schema validation, seeded; server-side actor resolution | 10:45 | 12:15 | |
| B01 | Vlad | Web skeleton and minimal shell | 10:45 | 12:00 | |
| A04 | Luis | CI, Vercel and Modal deploy on the Atlas Sandbox; change streams checked | 11:00 | 12:00 | |
| A05 | Luis | Load the selected trial set | 11:45 | 12:15 | |
| A06 | Luis | Ledger with the policy gate before every write | 11:45 | 13:45 | critical |
| A07 | Luis | Runs: identity stamping, atomic admission, stop | 11:45 | 13:15 | critical (30 min slack) |
| A08 | Luis | Extraction with quote and support checks | 11:45 | 13:45 | critical |
| A09 | Luis | GitHub review issue with claim, read-back and reconcile | 11:45 | 13:45 | critical |
| A10 | Luis | The run: LangGraph over the selected set | 11:45 | 13:30 | critical (15 min slack) |
| A11 | Luis | Audit API and "who authorised" | 11:45 | 13:15 | |
| A14 | Luis | Proposals and decisions API, minimal | 11:45 | 13:15 | |
| A12 | Luis | Change-stream feed with polling fallback | 12:00 | 13:00 | |
| A15 | Luis | Graph API scoped by `run_id` | 12:00 | 13:30 | |
| B02 | Vlad | Run console | 12:00 | 14:15 | |
| B03 | Vlad | Audit view | 12:00 | 14:00 | |
| B04 | Vlad | Record and Review screen, minimal | 12:00 | 14:00 | |
| B05 | Vlad | Run impact view | 12:00 | 14:30 | |
| B06 | Vlad | Stretch: spoken audit briefing | 13:00 | 14:30 | stretch |
| B07 | Vlad | README, submission text, video script | 13:00 | 14:00 | |
| A13 | Luis | Seed the FDA rows and synthetic Teams through the ledger | 13:15 | 13:45 | critical |
| I1 | Luis | Integration: the allowed-and-blocked loop on the sandbox | 13:45 | 14:30 | critical |
| A17 | Luis | Stretch: rejection drafts a policy for approval | 14:30 | 15:30 | stretch, only if I1 is green |
| I2 | Luis | Final acceptance on the sandbox | 15:00 | 15:30 | critical |
| A16 | Luis | Live-demo rehearsal and reset procedure | 15:30 | 16:15 | critical |

## Milestones and fallback triggers

Cuts are triggered by a missed milestone, not decided in advance.

| By | Check | If missed |
|---|---|---|
| 11:45 | Contracts frozen (A01, A02) | Hold other merges until they land; everything slips one for one |
| 11:45 | Vlad's spend rate checked | Above $40 an hour: cap subagents at six, drop B06 |
| 12:00 | Deployed on the Atlas Sandbox; change streams confirmed or polling chosen (A04) | One agent fixes the deploy; the build continues locally against the sandbox |
| 13:45 | Gate, runs, extraction and the GitHub action each merged (A06, A07, A08, A09) | Integrate what exists; the missing piece is stubbed for I1 and named in the demo |
| **14:30** | **Allowed-and-blocked loop green (I1)** | Stop all supporting and stretch work; everyone fixes the loop |
| 15:30 | Final acceptance passed (I2) | Demo only what passed |
| 16:15 | Rehearsal done and the sandbox reset (A16) | Use the time to 16:30 to fix and rehearse again |
| 16:30 | Code freeze | Record what works; the video names only behaviour shown |
| 16:55 | Submitted | Submit what exists |

If a fallback is triggered, cut in this order:

1. **Stretch first:** B06 spoken audit briefing, A17 policy draft, then the narrowly scoped reversal of a run (not scheduled; built only if the loop is green by 14:30).
2. **Then supporting:** B05 impact view, A15 graph API, then A12 change streams, which falls back to `/changes` polling.
3. **Never core:** A01 to A11, A13, I1, I2, B02 and B03 are not cut. B04 and A14 are supporting but the live demo uses Sam's review, so cut them only if the loop is still red at 15:30.

## Who owns which files

Extra agents only help if two of them never edit the same module at once.

| Module | Owner | Others call it, never edit it |
|---|---|---|
| `backend/dxp/api/models.py`, `backend/dxp/store/`, generated `web/lib/types.ts`, the frozen signature stubs | A01 | Every PR; a change goes through the contract keeper in its own PR and regenerates the types |
| `backend/dxp/schema/registry.py`, `backend/dxp/identity/` | A02 | A06, A08, A13 |
| `backend/dxp/gate/seed.py` and `gate/seed/` (`python -m dxp.gate.seed`), the `grants` and `policies` validator schemas in `backend/dxp/store/schemas/`, `backend/dxp/api/auth.py` (`resolve_actor`) | A03 | A06 reads grants and policies; A07 calls `resolve_actor`; A17 adds draft policies through its API only |
| `backend/dxp/gate/` (`gate.evaluate`, except the seed) and `backend/dxp/ledger/file.py` | A06 | A09, A10, A13, A14 |
| `backend/dxp/runs/` (`runs.admit`, `runs.release`, `runs.stop`, `runs.stamp`) | A07 | A10 calls admit and release; A11 reads runs |
| `backend/dxp/llm/`, `backend/dxp/evidence/` | A08 | A17 adds its own prompt file under `llm/prompts/` |
| `backend/dxp/actions/` (`actions.dispatch`, `actions/github.py`), reconcile route | A09 | A10 |
| `backend/dxp/pipeline/` (the run graph) | A10 | none |
| `backend/dxp/search/audit.py`, audit and actions routes | A11 | B03; B06 reads the audit response from `backend/dxp/api/briefing.py` |
| `backend/dxp/search/changes.py` and `/changes` | A12 | B02 |
| `backend/dxp/ledger/seed.py` | A13 | none |
| `backend/dxp/ledger/decide.py`, proposals routes | A14 | B04 |
| `backend/dxp/search/graph.py`, graph route | A15 | B05 |
| `backend/dxp/api/briefing.py`, audio route, `web/components/audit/audio.tsx` (stretch) | B06 | none |
| `backend/dxp/gate/drafts.py`, policy-draft prompt and routes (stretch) | A17 | none |
| `.github/workflows/`, deploy config, README deploy section | A04 | none |
| `web/` skeleton, `web/lib/api.ts`, `web/components/shell/` | B01 | every screen |
| `web/app/runs/page.tsx`, `web/app/runs/[run_id]/page.tsx`, `web/components/run-console/` (Run console) | B02 | none |
| `web/app/runs/[run_id]/audit/`, `web/components/audit/` (Audit view) | B03 | B06 adds `audio.tsx` beside it |
| `web/app/diagnostics/`, `web/app/review/` (Record and Review) | B04 | B02 and B03 link to them |
| `web/app/runs/[run_id]/impact/`, `web/components/graph/` (Run impact view) | B05 | none |
| README submission sections, video script | B07 | A16 adds the demo notes and reset section |

## Agent roles

- **Builders:** one per PR in the schedule. A06, A08 and A09 have no slack, so each gets a second builder for tests.
- **Reviewers:** one agent per open pull request. It checks the acceptance criteria, the six required behaviours where they apply, and looks for secrets, `.env` values, tokens and PubMed text before Luis or Vlad merges.
- **Contract keeper:** watches `models.py`, the signature stubs and the generated types, and rejects a pull request that changes a contract without regenerating them.
- **Integrator:** runs I1 and I2 and keeps an end-to-end smoke test (one allowed action, one blocked action, audit read) passing on every merge after 13:45.

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox. A merged PR that has not passed I1 or I2 is not done.

## Not modelled

- Claude API and GitHub API rate limits. The run uses low concurrency over 10 to 20 trials; agents share the same accounts' limits.
- The time Luis and Vlad spend reading and merging pull requests: 26 merges between 11:45 and 16:15, 19 on Luis's lane and 7 on Vlad's.
- Account and key setup, assumed done before 10:45.

## Open items

| Item | Owner | Due | Until it is resolved |
|---|---|---|---|
| Atlas Sandbox access: confirm Vector Search, change streams and the Agent Memory preview | Luis | As soon as access arrives | A04 checks change streams at 12:00; if absent, A12 ships polling only |
| Confirm with organisers: the submission deadline, whether coding may start before 10:45, and how to present prepared material | Luis | 9:00 to 10:45 Saturday | Plan for 17:00 submission, no coding before 10:45, and the README's prepared vs built-today table |
| Create `dxp-review-sandbox` and a fine-grained token restricted to it (issues only), kept in `.env` | Luis | Before 10:45 Saturday | A09 builds against a fake GitHub client; I1 cannot pass without it |
