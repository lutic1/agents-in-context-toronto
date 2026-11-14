---
title: Sprint Change Proposal, pivot to Agents You Can Audit
status: approved
created: 2026-11-13
approved_by: Luis
scope: major
---

# Sprint Change Proposal: DxP becomes a governed agent

> **Later decision:** `sprint-change-proposal-2026-11-14-discovery-agent.md` (V1 to V20) restores the discovery-agent vision and wins over this file wherever they differ. Its PR set, timeline and milestones are in `development-plan.md` and `build-schedule.md`; the timeline, pull request table, milestones and demo below are superseded by them and kept for history.

> Later decisions: `readiness-fixes-2026-11-14.md` (D1 to D57, including the final audit D41 to D57) supplements this proposal and wins where the two differ. `sprint-change-proposal-2026-11-14-slack.md` (S1 to S13) replaces GitHub with Slack `#all-mango-db-hackathon` as the external system and wins on anything about it; this proposal has been updated to match. The timeline and PR table below follow `development-plan.md` and `build-schedule.md` after D57 and the Slack change.

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
| **Core** | Run identity; scoped authority through grants in Atlas; hand-written, versioned policies checked before every action; an evidence-backed proposal from a selected set of real trials; one real external action (a Slack alert in `#all-mango-db-hackathon`, notify only, linking back to DxP, where approval happens); reconstructable audit history; a stop control; a minimal Record and Review screen, because the demo uses Sam's review (D35) |
| **Supporting** | A live action feed through Atlas change streams (polling is the default until it passes its check); a run-scoped impact view (the graph, fed by `run_id`, with the Slack notifications as `notification:<action_id>` nodes) |
| **Stretch** | A spoken audit briefing through ElevenLabs (prize); Sam's rejection drafting a policy for explicit approval, limited to the supported checks; narrowly scoped reversal of a run (outside Story 9.5, no PR, D37) |
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
| 9.1 | Runs and identity: every run has a `run_id`, two identities (`initiated_by`, the caller, and `agent`, named by the grant), model, prompt version, the pinned grant and policy-set versions and the person it acts for, resolved server-side; every write, event and external action is stamped with them | API | Core |
| 9.2 | Grants and versioned policies in Atlas: `grants` (agent, team, destination, allowed actions, expiry) and `policies` (versioned, hand-written) with `$jsonSchema` validation, seeded for the demo; actor and grant resolved server-side from the API key, never from a client-supplied name | API | Core |
| 9.3 | Policy gate before every action: five checks (active unexpired grant; Diagnostic in the authorised team scope; destination and action match the grant; required evidence checks passed; run still authorised). Every evaluation, allowed or blocked, is recorded as a decision. A blocked one writes its decision and one `action_blocked` event, and nothing else: no action, no record change, no external call (D5) | API | Core |
| 9.4 | External action: a Slack alert for diagnostic evidence, a Block Kit message to `#all-mango-db-hackathon` with links back to DxP, the action ID saved before sending, an atomic claim, the observed outcome recorded (an ambiguous one is `unknown`, never retried), and manual resolution by a Reviewer in DxP | API | Core |
| 9.5 | Stop control: new admissions are granted only while the run is `running`; an admitted action may finish while the run is `stopping` and shows as in flight; the run moves to `stopped` when no admitted admissions remain (D7) | API | Core |
| 9.6 | Audit reconstruction: `GET /runs/<run_id>/audit` returns every decision in order, allowed and blocked, with inputs, evidence reference, grant and policy versions, outcome, timestamps and, for allowed ones, the action's external result; then the Reviewer decisions "After the run"; answers "who authorised this" from the decision | API | Core |
| 9.7 | Run console: identity card, live action feed (allowed, blocked, in flight, unknown), stop button, "Slack alert delivered" on the action row, and Resolve on an unknown notification for Reviewers | WEB | Core |
| 9.8 | Audit view: one run reconstructed, action by action, with "who authorised this", and Resolve on an unknown notification for Reviewers (shown only when `GET /whoami`'s `actions` include `resolve_notification`, D53) | WEB | Core |
| 9.9 | Live action feed through Atlas change streams over `/changes`; until it passes its check, the Run console polls the run and its audit | API | Supporting |
| 9.10 | Spoken audit briefing: ElevenLabs reads a run's audit summary (replaces 3.4 and 3.5 for the ElevenLabs prize) | API + WEB | Stretch |
| 9.11 | Rejection drafts a policy for explicit approval, limited to the supported checks; never model prose as executable authority | API + WEB | Stretch |

Narrowly scoped reversal of a run is a stretch item outside Story 9.5 (D37). It has no PR and is not scheduled.

### Required acceptance criteria (binding on Stories 9.3 to 9.6)

| Concern | Required behaviour |
|---|---|
| Ambiguous external result | Save the action ID first; if the outcome is uncertain (timeout, connection error, 5xx), mark it `unknown` and never retry; a Reviewer resolves it in DxP (`POST /actions/<action_id>/resolve`, kind `resolve_notification`) after checking the channel for the action ID (S7, S8) |
| Concurrent retries | Claim the action atomically in Atlas (`queued` to `dispatching` with a conditional update) so two workers can never both dispatch it |
| Stop semantics | Check 5, "run still authorised", means the action holds an admission for this run and the run is not `stopped` (D7). New admissions are granted only while the run is `running`, in one transaction with a conditional write on the run, so a stop and an admission cannot race. An admitted action may finish while the run is `stopping`. An admission is released once; a second release does nothing. `runs.sweep` marks admissions past their lease `abandoned` and returns the actions they held, touching no action itself; a background task in `routes_runs.py` then calls `actions.mark_unknown(action_id, "abandoned_in_flight")` for `dispatching` ones, never retried (S8), and `actions.mark_failed(action_id, "abandoned_before_send")` for `queued` ones, then `runs.settle` (D43). The run moves from `stopping` to `stopped` when no `admitted` admissions remain |
| Blocked action | Every gate evaluation is recorded as a decision (D5). A blocked decision records every check, the grant evaluated and the policy-set version, and one `action_blocked` event carries its `decision_id`. It creates no action, no business-record change and no external call |
| Authority | The actor and grant are resolved server-side from the API key; a client-supplied name never confers permission |
| Audit reconstruction | Each decision, allowed or blocked, keeps its inputs, evidence reference, checks, the grant version evaluated, policy-set version, outcome and timestamps (proposed, decided); an allowed notification links to its action with its destination, the queued, claimed, posted and observed timestamps and the result (HTTP status, Slack's response body and the link URLs sent, or `unknown`), and the audit shows the proposal's live DxP review status (S9) |

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

- New collections: `runs`, `grants`, `policies`, `policy_sets`, `decisions`, `admissions`, `actions`; `events` gains action, decision and run stamps.
- One new external dependency: a Slack incoming webhook posting to `#all-mango-db-hackathon`. `SLACK_WEBHOOK_URL` is a credential kept only in `.env` and the Modal secret; `DXP_BASE_URL` (the production web address) builds the links back to DxP (S3).
- The batch runs at lower concurrency over a selected set of 20 named trials (D30), not 443 items.
- Change streams must be confirmed on the Atlas Sandbox tier before the live feed depends on them.

## 4. Recommended approach

**MVP review with direct adjustment.** The product goal changes, so this is a major-scope change, but most of the ledger, extraction and evidence work carries over unchanged. New work concentrates in Epic 9; removed work is deferred, not deleted.

Risk: the 14:30 target for the first loop leaves 30 minutes before core acceptance and about 40 minutes of float to the 17:00 deadline, after the readiness fixes moved the sandbox seed into I1 and added the reset slots (see `build-schedule.md`). If the loop is not green by 14:30, the supporting and stretch items wait and the team fixes the loop.

## 5. Saturday plan

### Timeline

**Superseded** by `build-schedule.md` after the discovery-agent proposal (I1 now ends 14:45, I3 runs 14:45 to 15:15, I2 is folded into the rehearsal). Kept for history.

| Time | What |
|---|---|
| 9:00 to 10:45 | Doors, breakfast, kick-off. No coding. Luis confirms the deadline, sandbox access, the prepared-material rules and whether `data/` and the logo are cleared, with organisers, and records the answer in `docs/clearance.md` |
| 10:45 | Hacking starts: contracts, web skeleton, grants and policies; deploy on the sandbox from 11:00 (merged after the web skeleton) |
| 11:45 | Contracts frozen; everything else builds in parallel against them |
| 12:45 | A13 starts the live FDA fetch |
| 13:30 | A13 merged on fake-gate tests |
| 13:45 | Gate, ledger and apply, extraction and the Slack notifier merged; I1 starts (the deploy, A04, is one of its start requirements, D51) |
| 13:45 to 14:00 | I1 step 1: grant seed, selected-set load, FDA fetch and seed on the sandbox, then the seeded snapshot with A13's procedure (D41) |
| 14:00 | README, submission text and video script done (B07) |
| **14:30** | **First complete loop** on the sandbox (I1): at least the NCT04712877 proposal for FoundationOne Liquid CDx filed pending and its Slack alert delivered to `#all-mango-db-hackathon` (one alert per filed proposal, D46; both links resolve once B04 is deployed), the FoundationOne CDx change blocked before execution with no Slack message, the audit reconstructs them |
| 14:30 to 15:00 | Screens wired to the loop; supporting and stretch items only if the loop is green, each with its own acceptance check |
| 15:00 to 15:30 | Core acceptance (I2), starting with a reset (D41) |
| 15:30 to 16:15 | Live-demo rehearsal (A16), each pass from a reset, with only the items that passed their check |
| 16:15 to 16:30 | Reset the sandbox for the video (D34, D41) |
| 16:30 | Code freeze |
| 16:30 to 16:55 | R1 (Luis and Vlad): record the 60-second video and submit: description, public repository, video, team members |
| 16:55 to 17:10 | Reset the sandbox for the live demo (D34) |
| 17:15 | Live 3-minute demo for judging |

### Pull requests

**Superseded** by `development-plan.md` after the discovery-agent proposal: A12, A15, A17 and B05 are cut; A18 is folded into A14, A23 into A06; A07 with A11, A19 with A20, A21 with A22 and A24 with A25 are bundled; I2 is folded into the rehearsal, and I3 and B08 are added. Kept for history.

Luis owns the critical path (contract, ledger and gate, runs and stop, extraction, the Slack notifier, integration). Vlad owns the screens, the web skeleton, the stretch audio and the submission package, with Luis's review agent on Vlad's lane.

| PR | Owner | Story | What | Start when merged | Merge after | Forecast |
|---|---|---|---|---|---|---|
| A01 | Luis | 1.1, 9.1 | Contract, stubs only: every route and shape (runs, grants, policies, decisions, admissions, actions, audit, diagnostics, proposals, graph), one error shape, frozen signatures | none | none | 10:45 to 11:45 |
| A02 | Luis | 1.2 | Registry, identity and the hand-written aliases | none | none | 10:45 to 11:45 |
| A03 | Luis | 9.2 | Keys generated into `.env` at 10:45 (D48); agent `lbdx@v1` (principal `dxp-curator`), `sam@v1` and `seed@v1` grants with `startable_by` (D56), policies, policy sets, latest-then-status selection, validators, server-side actor resolution | none (draft against A01) | A01 | 10:45 to 12:30 |
| A04 | Luis | 8.1 | CI, Vercel and Modal deploy against the Atlas Sandbox; change streams checked on the sandbox; the Vercel and Modal secrets of D48 set, including `DXP_BASE_URL` and `SLACK_WEBHOOK_URL` | none (starts on the bare package) | A01, B01 | 11:00 to 12:00 |
| A05 | Luis | 1.4 | Fetch the 20 selected trials (D30) by NCT ID from ClinicalTrials.gov during the event and load them, NCT04712877 first | A01 | none | 11:45 to 12:30 |
| A06 | Luis | 1.6, 9.3 | Ledger with the policy gate before every write; every evaluation a decision; live changes filed as pending proposals; apply and recovery (`ledger/apply.py`) | A01, A02 | A03 | 11:45 to 13:45 |
| A07 | Luis | 9.1, 9.5 | Runs: `initiated_by` and `agent`, `runs.admit`, `release`, `sweep`, `settle`, `finish`, stop | A01 | A03 | 11:45 to 13:30 |
| A08 | Luis | 1.5 | Extraction with quote and support checks, alias-constrained, tuned on the selected set | A01 | A05 | 11:45 to 13:45 |
| A09 | Luis | 9.4 | Slack notifier (`story/9.4-slack-notify`): action ID before send, atomic claim, Block Kit alert with links back to DxP, observed outcome (429 retried once, `unknown` never retried), manual resolution route | A01 | A03 | 11:45 to 13:45 |
| A10 | Luis | 1.7 | The run itself: LangGraph over the selected set in order, `DXP_DEMO_PACE`, calling admit, gate, ledger, dispatch and finish | A01 | none | 11:45 to 13:30 |
| A11 | Luis | 9.6 | Audit API, decisions and "who authorised" | A01 | none | 11:45 to 13:30 |
| A12 | Luis | 9.9 | Change-stream feed endpoint with polling fallback (supporting) | A01, A04 | none | 12:00 to 13:00 |
| A13 | Luis | 1.2 | Fetch the FDA companion diagnostics list during the event; seed lung rows and synthetic Teams through the ledger; the snapshot procedure and `scripts/reset_demo.py` (D41); merged on fake-gate tests | A01, A02 | none | 12:45 to 13:30 |
| A14 | Luis | 2.2, 2.3 | Proposals, Reviewer decisions and value review API, calling A06's apply (core) | A01 | A06 | 11:45 to 13:15 |
| A15 | Luis | 5.1 | Graph API by `run_id`: changed elements, context on request (supporting) | A01 | none | 12:00 to 13:30 |
| A18 | Luis | 1.1 | Read model and `GET /diagnostics/<dx_id>` (no Diagnostics list) | A01 | A06 | 11:45 to 12:45 |
| I1 | Luis | 9.3, 9.4 | **Integration: seed and snapshot (first 15 minutes), then the loop on the sandbox** (core PRs only) | A03, A04, A05, A06, A07, A08, A09, A10, A11, A13 | none | 13:45 to 14:30 |
| I2 | Luis | 8.2 | Reset, then core acceptance on the sandbox | I1, A14, A18, B02, B03, B04 | none | 15:00 to 15:30 |
| A16 | Luis | 8.2 | Live-demo rehearsal, each pass from a reset with A13's script; reset for the video | I2 | none | 15:30 to 16:15, reset 16:15 to 16:30 |
| A17 | Luis | 9.11 | Stretch: rejection drafts a policy for approval | I1 green | A14 | 14:30 to 15:30 |
| B01 | Vlad | 1.3, 1.12 | Web skeleton and minimal shell (Run console, Audit, Review, Impact behind its flag), text wordmark, feature flags; builds locally, deploys once A04 lands | none | none | 10:45 to 12:00 |
| B02 | Vlad | 9.7 | Run console | B01 | A01 | 12:00 to 14:15 |
| B03 | Vlad | 9.8 | Audit view | B01 | A01 | 12:00 to 14:00 |
| B04 | Vlad | 1.3, 2.4 | Record and Review screen, minimal (core), with the `?proposal=<p_id>` focus the Slack alert links to | B01 | A01, A18, A14 | 12:00 to 14:00 |
| B05 | Vlad | 5.2 | Run impact view (supporting) | B01 | A01 | 12:00 to 14:30 |
| B06 | Vlad | 9.10 | Stretch: spoken audit briefing with ElevenLabs, behind a flag | B01 | A11, and the 14:30 loop green | 13:00 to 14:30 |
| B07 | Vlad | 8.3, 8.4 | README, submission text, 60-second video script | none | none | 13:00 to 14:00 |
| R1 | Luis and Vlad | 8.4 | Task, not a PR: record the 60-second video and submit; then reset the sandbox for the live demo | A16, B07 | n/a | 16:30 to 16:55, reset 16:55 to 17:10 |

Supporting and stretch items (A12, A15 with B05, B06, A17) each have their own acceptance check and join the rehearsal only if it passed; none of them blocks I1, I2, A16 or R1. They are the only PRs that may be cut (D37).

Start and merge requirements follow `development-plan.md`, which wins where the two differ.

These are model forecasts. Vlad's times assume Sonnet 5.5 at high effort with ten subagents.

### Milestones

| By | Check | If missed |
|---|---|---|
| 11:45 | Contracts frozen (A01, A02) | Hold other merges until they land |
| 12:00 | Deployed on the Atlas Sandbox; change streams confirmed or polling chosen | One agent fixes the deploy; build continues locally against the sandbox |
| 13:45 | Gate, ledger and apply, runs, extraction and the Slack notifier merged; seed merged on fake-gate tests | Nothing core is stubbed (D37): the late PR gets more builders, I1 seeds the sandbox on time and the loop waits for it, and supporting and stretch work stops |
| 14:00 | Sandbox seeded and snapshot taken (I1 step 1) | The seed's owners fix it before the loop starts |
| 14:00 | README, submission text and video script merged (B07) | Vlad finishes it before any supporting work |
| **14:30** | **Loop green: at least the NCT04712877 proposal for FoundationOne Liquid CDx pending and its Slack alert delivered, the FoundationOne CDx change blocked with no Slack message, audit of them (D46)** | Stop all supporting and stretch work; everyone fixes the loop |
| 15:30 | Core acceptance passed | Demo only what passed |
| 16:30 | Sandbox reset for the video; code freeze | Record what works |
| 16:55 | Submitted (R1) | Submit what exists |
| 17:10 | Sandbox reset for the live demo | Start the live demo with a new run; old Slack alerts stay in the channel and nothing extra is posted |

## 6. Demo

### 60-second video

| Seconds | Shows |
|---|---|
| 0 to 10 | The problem and the scope: start the run; the agent's authorised scope (identity card, grant `lbdx@v1`, policy set) |
| 10 to 30 | The allowed proposal and its Slack alert, then the blocked change: NCT04712877 filed against FoundationOne Liquid CDx as a pending proposal with its quote, and its alert arriving in Slack `#all-mango-db-hackathon` (the second screen); then the same trial against FoundationOne CDx blocked before execution (outside the Team's scope): no record change, no proposal, no Slack message, one recorded decision |
| 30 to 45 | Stop the run while items remain (stopping, then stopped) |
| 45 to 60 | Sam approves the pending proposal in DxP (from the alert's "Review in DxP" link; it appears under "After the run"), then "who authorised this?" in the Audit view |

These are the D52 timings, used everywhere. The run uses `DXP_DEMO_PACE` (one item at a time, NCT04712877 first), so the stop lands mid-run. The sandbox is reset from the seeded snapshot with A13's `scripts/reset_demo.py` before every take: I2, each rehearsal, the video and the live demo (D33, D34, D41).

### 3-minute live demo

In the D33 order, from the reset sandbox with `DXP_DEMO_PACE` set: start a run over the selected trials; the console shows identity and scope; actions appear; the proposal to add NCT04712877 to FoundationOne Liquid CDx is filed as pending and its alert arrives in Slack `#all-mango-db-hackathon` (the second screen); the same trial's proposal for FoundationOne CDx is blocked before execution (show the failed check, `team_scope`), and no Slack message is sent; stop the run while items remain; Sam opens the alert's "Review in DxP" link and approves the focused proposal in DxP (it appears under "After the run"); open the audit view and answer "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?". No stage transition is shown. If their checks passed: the impact view shows exactly what the run changed, and the spoken audit briefing (stretch).

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
| Atlas Sandbox access: confirm change streams (Vector Search, Automated Embedding and Agent Memory are not used on Saturday) | As soon as access arrives |
| Confirm with organisers: the submission deadline, whether coding may start before 10:45, and how to present prepared material | 9:00 to 10:45 Saturday |
| Ask organisers to clear, in writing, the prepared `data/` files and logo, and record the answer in `docs/clearance.md`; until then A05 and A13 fetch live and the interface uses a text wordmark | 9:00 to 10:45 Saturday |
| Set `DXP_BASE_URL` to the production URL and confirm the alert links resolve | During A04 |
| Keep `SLACK_WEBHOOK_URL` only in `.env` and the Modal secret | Before 10:45 Saturday, and on every PR review |
| The Slack channel is used often (D57): every run posts one alert per filed proposal to `#all-mango-db-hackathon` (tuning, I1, I2, rehearsals, the video and the live demo). Confirm this is acceptable for that channel, or point the webhook at a team channel | Before 10:45 Saturday |

Success criteria: by 14:30 on the sandbox, at least the NCT04712877 proposal for FoundationOne Liquid CDx is filed as pending and its Slack alert is delivered to `#all-mango-db-hackathon` (one alert per filed proposal; both links back to DxP resolve once B04 is deployed), the out-of-scope FoundationOne CDx change is blocked before execution with no Slack message, and the audit reconstructs them with identity, grant, policy version and result.
