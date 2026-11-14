---
title: Sprint Change Proposal, pivot to Agents You Can Audit
status: approved
created: 2026-11-13
approved_by: Luis
scope: major
---

# Sprint Change Proposal: DxP becomes a governed agent

## 1. Issue summary

On 13 November 2026 the organisers' participant guide for MongoDB Agents in Context Toronto arrived. It changes the plan in six ways:

| Guide rule | Effect on DxP |
|---|---|
| Hacking runs 10:45 to 17:00; submissions are due at 17:00 | 6 hours 15 minutes in total, including recording and submitting. No coding before 10:45 unless an organiser permits it in writing |
| The submission includes a one-minute video | A 60-second recording, plus a separate 3-minute live demo for judging from 17:15 |
| Projects must fit one of three problem statements | DxP is pitched and built for Statement 1, "Agents You Can Audit" |
| Finalists must build on the provided Atlas Sandbox | Build and validate on the sandbox from the start; our own cluster is not the final environment |
| Only work built during the event may be highlighted | The README separates prepared material from what was built on 14 November; the demo shows only the latter |
| Banned: a dashboard as the main feature, and AI giving medical advice | The governed agent is the product; screens only inspect it. DxP tracks evidence about diagnostic tests for pharma teams and gives no patient advice |

Luis decided, after a party-mode session: **pivot to Statement 1. The governed agent is the product.**

## 2. The new product in one line

DxP is an agent that keeps a pharma team's diagnostic evidence current, and it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action, and an audit trail a reviewer can replay.

## 3. Impact analysis

### Scope by priority

| Priority | What |
|---|---|
| **Core** | Run identity; scoped authority through grants in Atlas; hand-written, versioned policies checked before every action; an evidence-backed proposal from a selected set of real trials; one real external action (a review issue in GitHub); reconstructable audit history; a stop control |
| **Supporting** | A minimal Record and Review screen; a live action feed through Atlas change streams (polling fallback); a run-scoped impact view (the graph, fed by `run_id`, with the GitHub issues as nodes) |
| **Stretch** | A spoken audit briefing through ElevenLabs (prize); narrowly scoped reversal of a run; Sam's rejection drafting a policy for explicit approval, limited to the supported checks |
| **Deferred** | Find, Categories, the broad Home dashboard, Tavily and scheduled scans, quick capture, the comprehensive Baseline load, Learned-rule enforcement, Team Alerts, memory and resume |

Deferred work stays in the documents, marked **Deferred (pivot, 13 Nov)**, so no agent builds it on Saturday.

### Epic impact

| Epic | Effect |
|---|---|
| 1 Evidence-backed records | Kept and trimmed: contract, registry, a small FDA seed, a selected trial set, extraction with quote and support checks, the ledger. Stories 1.9 (full Baseline), 1.10 and 1.11 deferred. 1.8 becomes the Run console (Story 9.7). 1.12 trimmed to a minimal shell |
| 2 Review and Learned rules | 2.2 and 2.3 kept minimal; 2.4 trimmed into the Record and Review screen; 2.1, 2.5, 2.6 and 2.7 deferred (2.6 returns as stretch Story 9.11) |
| 3 Alerts | Deferred, except 3.4 and 3.5, which become the stretch spoken audit briefing (Story 9.10 covers it) |
| 4 Find and Categories | Deferred |
| 5 Connections | 5.1 and 5.2 kept as the run-scoped impact view; 5.3 deferred |
| 6 Memory and resume | Deferred |
| 7 Capture | Deferred |
| 8 Ship it | Kept: deploy on the Atlas Sandbox, live-demo rehearsal, submission with the prepared vs built-today table, the 60-second video |
| **9 Governed agent actions (new, core)** | Stories 9.1 to 9.11 below |

### New Epic 9: Governed agent actions

| Story | What | Lane | Priority |
|---|---|---|---|
| 9.1 | Runs and identity: every run has a `run_id`, agent name, model, prompt version, the policy-set version and the person it acts for, resolved server-side; every write, event and external action is stamped with them | API | Core |
| 9.2 | Grants and versioned policies in Atlas: `grants` (agent, team, destination, allowed actions, expiry) and `policies` (versioned, hand-written) with `$jsonSchema` validation, seeded for the demo; actor and grant resolved server-side from the API key, never from a client-supplied name | API | Core |
| 9.3 | Policy gate before every action: five checks (active unexpired grant; Diagnostic in the authorised team scope; destination and action match the grant; required evidence checks passed; run still authorised). A blocked action writes an audit event and nothing else | API | Core |
| 9.4 | External action: an evidence-review issue in GitHub repository `dxp-review-sandbox`, with the action ID saved before sending, an atomic claim, read-back, and reconciliation on an ambiguous result | API | Core |
| 9.5 | Stop control: stop admitting new actions; admitted actions finish and show as in flight; the run shows "stopping" until they are accounted for, then "stopped" | API | Core |
| 9.6 | Audit reconstruction: `GET /runs/<run_id>/audit` returns every action in order with inputs, evidence reference, grant and policy versions, decision, timestamps and external result; answers "who authorised this action" | API | Core |
| 9.7 | Run console: identity card, live action feed (allowed, blocked, in flight, unknown), stop button, links to the GitHub issues | WEB | Core |
| 9.8 | Audit view: one run reconstructed, action by action, with "who authorised this" | WEB | Core |
| 9.9 | Live action feed through Atlas change streams, with `/changes` polling as the fallback | API | Supporting |
| 9.10 | Spoken audit briefing: ElevenLabs reads a run's audit summary (replaces 3.4 and 3.5 for the ElevenLabs prize) | API + WEB | Stretch |
| 9.11 | Rejection drafts a policy for explicit approval, limited to the supported checks; never model prose as executable authority | API + WEB | Stretch |

Narrowly scoped reversal of a run is a stretch item inside 9.5's follow-up, built only if the core loop is green by 14:30.

### Required acceptance criteria (binding on Stories 9.3 to 9.6)

| Concern | Required behaviour |
|---|---|
| Ambiguous GitHub result | Save an action ID in Atlas before sending and include it in the issue. If the outcome is uncertain (timeout, 5xx), reconcile by searching the repository for the action ID; never blindly retry creation. If still unresolved, mark the action `unknown` for manual reconciliation |
| Concurrent retries | Claim the action atomically in Atlas (`queued` to `dispatching` with a conditional update) so two workers can never both dispatch it |
| Stop semantics | Admission is an atomic, conditional update on the run (only while it is `running`), so a stop and an admission cannot race. After stop, nothing new is admitted; admitted actions may finish and show as in flight; the run shows `stopping` until in-flight reaches zero, then `stopped` |
| Blocked action | No business-record change and no external call; one audit event is written with the policy and grant versions and the failed check |
| Authority | The actor and grant are resolved server-side from the API key; a client-supplied name never confers permission |
| Audit reconstruction | Each action keeps its inputs, evidence reference, grant version, policy-set version, decision, timestamps (proposed, decided, sent, observed) and external result (issue number and URL, or `unknown`) |

### Artifact conflicts

| Artifact | Change |
|---|---|
| PRD | Reframe to Statement 1; add the governed-action requirements; mark deferred FRs; update the time constraint (NFR8) and the demo |
| Architecture spine | New decisions for runs and identity, grants and policies, the gate, external actions, stop, audit; AD-14 updated with the new routes and shapes and the earlier Departures; the Atlas Sandbox as the environment |
| UX | Information architecture reduced to Run console, Audit view, Record and Review, Run impact view; deferred surfaces marked; Key Flows and Demo on Camera rewritten. The old mockups and design-round files are removed from the repository; every screen is built during the event from the text specs |
| `epics.md` | Epic 9 added; deferred stories marked; trims and new acceptance criteria; owners and PR IDs from the plan below |
| `build-schedule.md`, `development-plan.md` | Rewritten for 10:45 to 17:00 with the PRs below |
| `sprint-status.yaml` | Regenerated; deferred stories marked in the owners section |

### Technical impact

- New collections: `runs`, `grants`, `policies`, `actions`; `events` gains action and run stamps.
- One new external dependency: the GitHub REST API with a fine-grained token restricted to `dxp-review-sandbox` (issues only), kept in `.env`.
- The batch runs at lower concurrency over a selected trial set (10 to 20 trials), not 443 items.
- Change streams must be confirmed on the Atlas Sandbox tier before the live feed depends on them.

## 4. Recommended approach

**MVP review with direct adjustment.** The product goal changes, so this is a major-scope change, but most of the ledger, extraction and evidence work carries over unchanged. New work concentrates in Epic 9; removed work is deferred, not deleted.

Risk: the 14:30 target for the first allowed-and-blocked loop leaves about 45 minutes of slack before supporting work must be integrated. If the loop is not green by 14:30, the supporting and stretch items wait and the team fixes the loop.

## 5. Saturday plan

### Timeline

| Time | What |
|---|---|
| 9:00 to 10:45 | Doors, breakfast, kick-off. No coding. Luis confirms the deadline, sandbox access and the prepared-material rules with organisers |
| 10:45 | Hacking starts: contracts, web skeleton, deploy on the sandbox, grants and policies |
| 11:45 | Contracts frozen; everything else builds in parallel against them |
| **14:30** | **First complete allowed-and-blocked loop** on the sandbox: one real issue created, one action blocked before execution, audit reconstructs both |
| 14:30 to 15:00 | Supporting screens integrated; stop control proven; stretch items only if the loop is green |
| 15:00 to 15:30 | Final acceptance (I2) |
| 15:30 to 16:15 | Live-demo rehearsal and reset (A16); recording preparation starts |
| 16:30 | Code freeze |
| 16:30 to 16:50 | Record the 60-second video |
| By 16:55 | Submit: description, public repository, video, team members |
| 17:15 | Live 3-minute demo for judging |

### Pull requests

Luis owns the critical path (contract, ledger and gate, runs and stop, extraction, the GitHub action, integration). Vlad owns the screens, the web skeleton, the stretch audio and the submission package, with Luis's review agent on Vlad's lane.

| PR | Owner | Story | What | Start when merged | Merge after | Forecast |
|---|---|---|---|---|---|---|
| A01 | Luis | 1.1, 9.1 | Contract: every route and shape (runs, grants, policies, actions, audit, diagnostics, proposals, graph), one error shape, frozen signatures for `gate.evaluate`, `actions.dispatch`, `runs.admit`, `runs.release`, `runs.stop`, `ledger.file`, `llm.extract`, `llm.check` | none | none | 10:45 to 11:45 |
| A02 | Luis | 1.2 | Registry and identity | none | none | 10:45 to 11:45 |
| A03 | Luis | 9.2 | Grants and policies with schema validation, seeded; server-side actor resolution | none (draft against A01) | A01 | 10:45 to 12:15 |
| A04 | Luis | 8.1 | CI, Vercel and Modal deploy against the Atlas Sandbox; change streams checked on the sandbox | none (starts on the bare package) | A01 | 11:00 to 12:00 |
| A05 | Luis | 1.4 | Load the selected trial set (10 to 20 held-back trials that hit FDA-seeded Diagnostics) | A01 | none | 11:45 to 12:15 |
| A06 | Luis | 1.6, 9.3 | Ledger with the policy gate before every write; blocked writes an audit event only | A01, A02 | A03 | 11:45 to 13:45 |
| A07 | Luis | 9.1, 9.5 | Runs: identity stamping, atomic admission, stop with stopping and stopped | A01 | A03 | 11:45 to 13:15 |
| A08 | Luis | 1.5 | Extraction with quote and support checks, tuned on the selected set | A01 | A05 | 11:45 to 13:45 |
| A09 | Luis | 9.4 | GitHub review issue: action ID before send, atomic claim, read-back, reconcile, `unknown` | A01 | A03 | 11:45 to 13:45 |
| A10 | Luis | 1.7 | The run itself: LangGraph over the selected set, calling admit, gate, ledger and dispatch | A01 | none | 11:45 to 13:30 |
| A11 | Luis | 9.6 | Audit API and "who authorised" | A01 | none | 11:45 to 13:15 |
| A12 | Luis | 9.9 | Change-stream feed endpoint with polling fallback | A01, A04 | none | 12:00 to 13:00 |
| A13 | Luis | 1.2 | Seed the FDA rows and synthetic Teams through the ledger | A01, A02 | A06 | 13:15 to 13:45 |
| A14 | Luis | 2.2, 2.3 | Proposals and decisions API, minimal | A01 | none | 11:45 to 13:15 |
| A15 | Luis | 5.1 | Graph API scoped by `run_id`, with GitHub issues as nodes | A01 | none | 12:00 to 13:30 |
| I1 | Luis | 9.3, 9.4 | **Integration: the allowed-and-blocked loop on the sandbox** | A05 to A13 | none | 13:45 to 14:30 |
| I2 | Luis | 8.2 | Final acceptance on the sandbox, every core and supporting piece | I1, A14, A15, B02 to B05 | none | 15:00 to 15:30 |
| A16 | Luis | 8.2 | Live-demo rehearsal and reset procedure | I2 | none | 15:30 to 16:15 |
| A17 | Luis | 9.11 | Stretch: rejection drafts a policy for approval | I1 green | A14 | 14:30 to 15:30 |
| B01 | Vlad | 1.3, 1.12 | Web skeleton and minimal shell (Run console, Audit, Review, Impact) | none | none | 10:45 to 12:00 |
| B02 | Vlad | 9.7 | Run console | B01 | A01 | 12:00 to 14:15 |
| B03 | Vlad | 9.8 | Audit view | B01 | A01 | 12:00 to 14:00 |
| B04 | Vlad | 1.3, 2.4 | Record and Review screen, minimal | B01 | A01 | 12:00 to 14:00 |
| B05 | Vlad | 5.2 | Run impact view (graph by `run_id`) | B01 | A01 | 12:00 to 14:30 |
| B06 | Vlad | 9.10 | Stretch: spoken audit briefing with ElevenLabs | B01 | A11 | 13:00 to 14:30 |
| B07 | Vlad | 8.3, 8.4 | README with the prepared vs built-today table, submission text, 60-second video script | none | none | 13:00 to 14:00 |

Start and merge requirements follow `development-plan.md`, which wins where the two differ.

These are model forecasts. Vlad's times assume Sonnet 5.5 at high effort with ten subagents.

### Milestones

| By | Check | If missed |
|---|---|---|
| 11:45 | Contracts frozen (A01, A02) | Hold other merges until they land |
| 12:00 | Deployed on the Atlas Sandbox; change streams confirmed or polling chosen | One agent fixes the deploy; build continues locally against the sandbox |
| 13:45 | Gate, runs, extraction, GitHub action each merged | Integrate what exists; the missing piece is stubbed for I1 and named in the demo |
| **14:30** | **Allowed-and-blocked loop green** | Stop all supporting and stretch work; everyone fixes the loop |
| 15:30 | Final acceptance passed | Demo only what passed |
| 16:30 | Code freeze | Record what works |
| 16:55 | Submitted | Submit what exists |

## 6. Demo

### 60-second video

| Seconds | Shows |
|---|---|
| 0 to 10 | The problem and the agent's authorised scope: identity card, grant, policy set |
| 10 to 30 | An allowed action across two systems: the record updated with its quote, and the review issue open in GitHub itself |
| 30 to 45 | An out-of-scope action blocked before execution: no record change, no issue, one audit event |
| 45 to 60 | Stop the run (stopping, then stopped) and inspect who authorised the completed action |

### 3-minute live demo

Start a run over the selected trials; the console shows identity and scope; actions stream in; one creates a real GitHub issue (open it); one is blocked before execution (show the failed check); Sam reviews a proposal; stop the run mid-flight; open the audit view and answer "who moved SuperARMS to clinical utility, and under what authority?"; the impact view shows exactly what the run touched. Stretch: the spoken audit briefing.

## 7. Implementation handoff

**Scope: major.** Routed to PM and architect work (done now through the document updates below), then to the developer agents on Saturday.

| Artifact | Updated by |
|---|---|
| PRD and addendum | Subagent |
| Architecture spine | Subagent |
| DESIGN.md and EXPERIENCE.md | Subagent |
| `epics.md` | Subagent |
| `build-schedule.md`, `development-plan.md` | Subagent |
| `sprint-status.yaml` | Regenerated after `epics.md` |

Open items, owner Luis:

| Item | Due |
|---|---|
| Atlas Sandbox access: confirm Vector Search, change streams and the Agent Memory preview | As soon as access arrives |
| Confirm with organisers: the submission deadline, whether coding may start before 10:45, and how to present prepared material | 9:00 to 10:45 Saturday |
| Create `dxp-review-sandbox` and a fine-grained token restricted to it (issues only) | Before 10:45 Saturday |

Success criteria: by 14:30 on the sandbox, one allowed action creates a real GitHub issue and one out-of-scope action is blocked before execution, and the audit view reconstructs both with identity, grant, policy version and result.
