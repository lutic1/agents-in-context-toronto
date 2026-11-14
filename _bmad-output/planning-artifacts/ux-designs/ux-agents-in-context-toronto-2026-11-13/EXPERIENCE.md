---
name: DxProvida (DxP)
title: DxProvida (DxP) Experience
status: final  # revised for the pivot, 13 Nov (sprint-change-proposal-2026-11-13.md)
created: 2026-11-13
updated: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxProvida (DxP): experience spine

**Revised for the pivot (13 November).** DxP is now pitched and built for Statement 1, "Agents You Can Audit". The approved source is `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md`. Where this file and the proposal disagree, the proposal wins; on API routes, shapes and status values the architecture spine (AD-14, AD-17 to AD-24) wins, and on page routes and PRs `development-plan.md` wins.

## What to build from

There are no mockups. The earlier key-screen mockups and design-round files were removed on 13 November with the pivot, because the hackathon rules allow only work built during the event to be shown. Every screen is built on Saturday, from 10:45, from this file and `DESIGN.md`:

| Surface | Build from |
|---|---|
| Run console (Story 9.7) | This file's Run console sections, with `DESIGN.md` tokens |
| Audit view (Story 9.8) | This file's Audit view sections, with `DESIGN.md` tokens |
| Record and Review (Stories 1.3, 2.4 trimmed) | This file, trimmed scope |
| Run impact view (Story 5.2) | This file: scoped by `run_id`, with GitHub issues as nodes |

## Foundation

- **The governed agent is the product.** The screens only inspect it: who the agent is, what it may do, what it did, what was blocked, and who authorised each action. The hackathon bans "a dashboard as the main feature", so no screen is pitched or demoed as the product.
- **No medical advice.** DxP tracks evidence about diagnostic tests for pharma teams. It never tells anyone how to treat, test or manage a patient, and no copy reads as a recommendation for patient care.
- One responsive web app, desktop first, built on Next.js 16 App Router with shadcn/ui and Tailwind. `DESIGN.md` is the visual identity; this file is the behaviour.
- The web app reads and writes only through the API (AD-9, AD-14). It applies no display rule of its own: what the read model returns is what the screen shows (AD-6).
- **Authority is never set in the browser.** The actor and grant are resolved server-side from the API key. There is no Team picker and no "your name" picker that confers anything. The top bar shows, read-only, who the API resolved the caller as, from `GET /whoami` (AD-14).
- Everything is built and validated on the Atlas Sandbox. The demo shows only work built on 14 November.
- Fonts load through `next/font/google`: Atkinson Hyperlegible Next, Atkinson Hyperlegible Mono, Source Serif 4. [ASSUMPTION: if a family is missing from `next/font/google`, fall back to Atkinson Hyperlegible.]
- This file adds no stories of its own. The Story column below says which story builds each surface.

## Information Architecture

### Kept surfaces

| Surface | Route | Reached from | Purpose | Stories |
|---|---|---|---|---|
| Run console | `/runs`, `/runs/[run_id]` | Top bar, app open (`/` redirects to the latest run) | Start a run over the selected trial set; identity card; live action feed (allowed, blocked, in flight, unknown); stop control; links to the GitHub issues | 9.7, 9.9 |
| Audit view | `/runs/[run_id]/audit` | Run console, any action row, top bar | One run reconstructed action by action, with "Who authorised this" on every action | 9.8, 9.6 |
| Record and Review | `/diagnostics/[id]`, `/review` | Action row (record link), Audit entry, impact node, top bar (Review with pending count) | Record: fields with Evidence, unreviewed values marked. Review: pending Proposed changes, accept, edit, reject. Trimmed: no history disclosure, no Learned rules, no add-a-value | 1.3, 2.2, 2.3, 2.4 (trimmed) |
| Run impact view | `/runs/[run_id]/impact` | Run console, Audit view, top bar | The graph fed by `run_id`: exactly what the run touched (Diagnostics, trials, the fields changed) with each GitHub issue as a node | 5.1, 5.2 |

These routes are the page files in `development-plan.md`: `web/app/runs/page.tsx` and `web/app/runs/[run_id]/page.tsx` (B02), `web/app/runs/[run_id]/audit/` (B03), `web/app/diagnostics/` and `web/app/review/` (B04), `web/app/runs/[run_id]/impact/` (B05).

Top bar, left to right: DxP logo, Run console, Audit, Review (count), Impact; then the read-only "Signed in as" chip. Footer: the credits line. The top bar, tokens, stage track and badges are built once in the minimal shell (Stories 1.12 trimmed, PR B01).

Dialogs stack one level deep. The right-hand panel (360px) opens Evidence and the "Who authorised this" answer without leaving the page.

### Earlier surfaces

| Surface | Route | Status |
|---|---|---|
| Home (dashboard and graph-led hero) | `/` | **Deferred (pivot, 13 Nov).** `/` redirects to the latest run |
| Diagnostics list | `/diagnostics` | **Deferred (pivot, 13 Nov).** Records are reached from actions, audit entries and the impact view |
| Find | `/find` | **Deferred (pivot, 13 Nov)** |
| Categories | `/categories` | **Deferred (pivot, 13 Nov)** |
| Graph | `/graph` | Becomes the Run impact view, scoped by `run_id` |
| Rules | `/rules` | **Deferred (pivot, 13 Nov)** |
| Alerts | `/alerts` | **Deferred (pivot, 13 Nov).** The audio returns as the stretch spoken audit briefing (Story 9.10) |
| Jobs, as designed | `/jobs`, `/jobs/[id]` | **Deferred (pivot, 13 Nov).** Jobs becomes the Run console |
| Terms | `/terms` | **Deferred (pivot, 13 Nov)** |

## Voice and Tone

Microcopy. DxP speaks plainly to a scientist or reviewer in a hurry. It names things the way the PRD Glossary does: Diagnostic, Record, Evidence, Proposed change, Team, Lifecycle stage, Early research; and for governance: run, agent, grant, policy set, action, audit.

| Do | Don't |
|---|---|
| "Blocked before it ran: Diagnostic in team scope failed under policy v3" | "Action denied", "Permission error", "403" |
| "Result unknown. GitHub didn't confirm. Search `dxp-review-sandbox` for action A-0142 to reconcile by hand" | "Something went wrong", "Retrying…" |
| "Stopping: 2 actions in flight. No new actions will start." | "Please wait…" |
| "Stopped at 15:12. 9 took effect, 1 blocked, 0 in flight." | "Run cancelled" |
| "Who authorised this?" and the answer as one sentence: "Allowed by grant G-7 v2 (dxp-curator for Team Lung Dx, issues in `dxp-review-sandbox`) under policy set v3, in run R-0031, acting for Rowan." | "Authorization details", raw JSON |
| "Took effect: issue #12 opened in `dxp-review-sandbox`" | "Success!" |
| "Acting for Rowan (Team Lung Dx, Synthetic)" | "User: rowan" |
| "No data for this indication" | "N/A", "—", "Unknown" |
| "Stage not determined" | "Unstaged", "TBD" |
| "Accept", "Edit", "Reject"; toast "Accepted", "Edited", "Rejected" | "Submit", "Confirm action" |
| "Couldn't reach the API. Retrying in 5 seconds." | "Oops! Something went wrong." |
| "Early research" on discovery and assay development | "Unvalidated", "Low quality" |
| "Synthetic" on every made-up Team, grant holder and correction | Leaving synthetic data unlabelled |
| Evidence about a test: "Moved to clinical utility, per NCT06422546" | Patient advice: "Recommended for patients with…", "Use this test to decide treatment" |

The five checks always appear under these names: **Grant active**, **Diagnostic in team scope**, **Destination and action match the grant**, **Evidence checks passed**, **Run still authorised**. The failed check is named in the blocked line with the policy-set version that was in force.

## Component Patterns

Behavioural. Visual specs live in `DESIGN.md` Components.

### New for the governed agent

| Component | Where | Behaviour |
|---|---|---|
| Identity card | Run console (top), Audit view (top) | Shows agent name and model, run ID, prompt version, acting for (person and Team), grant (ID, version, destination, allowed actions, expiry) and policy-set version, plus the run status (running, stopping, stopped, done, failed). Every value comes from the run record, resolved server-side; nothing is editable. Identifiers are copyable. A synthetic Team or person carries the Synthetic badge. |
| Action row | Run console feed, Audit view | One row per action: kind ("Update record" or "Open review issue"), Diagnostic, field or destination, current state, time. A row appears when the gate decides (the `action_allowed` or `action_blocked` event), as either **blocked** (the failed check and policy version, nothing else happens) or **allowed** (`queued`), then **dispatching** (claimed), **in flight** (`sent`), and finally **took effect** (`done`, with the issue number linking to GitHub, or the record link), **unknown** (manual reconciliation) or **failed** (GitHub refused it, with the error). The row updates in place as its state changes; it never jumps position. Click or Enter opens the action in the Audit view. |
| Stop control | Run console identity card | "Stop run" while the run is **running**. One press, no confirmation dialog: stopping is the safe direction. The button then disables and the card reads **stopping** with the live in-flight count ("2 in flight"). When in flight reaches zero the card reads **stopped** with the totals. A stopped run cannot be restarted from here; start a new run. |
| Audit entry | Audit view | One entry per action, in order. Shows the four timestamps (proposed, decided, sent, observed), the inputs, the evidence reference (as an Evidence quote), grant version, policy-set version, the decision with the failed check if blocked, and the external result (issue number and URL, or "Result unknown"). "Who authorised this?" opens the answer in the right-hand panel. A blocked entry states that no record changed and no external call was made. |
| Run feed status | Run console, above the feed | Says how the feed is live: "Live (change streams)" or "Live (polling every 2 seconds)". Carries the capability tag. |

### Kept

| Component | Where | Behaviour |
|---|---|---|
| Stage track | Record header, Review row, impact view tooltip | Read-only. Tooltip names all nine stages and the date each was reached. A segment advanced by the current run shows `{colors.eosin}` with the word "Changed" on the impact view only; elsewhere the segment is a plain fill. |
| Evidence quote | Record, Review row, Audit entry | Always shows source, identifier link and "data as of". Never shows a value without it. |
| Value | Record | Current value(s) with Evidence. Unreviewed values show "Unreviewed" and, for a Reviewer, Accept / Edit / Reject inline. The "History" disclosure (Story 2.5) is **Deferred (pivot, 13 Nov)**. |
| Proposal row | Review | Diagnostic, field, current → new written as a sentence ("Add trial NCT06422546 to Trials"), quote, confidence, and the run ID that proposed it. The focused row shows full Accept / Edit / Reject buttons; other rows show compact ghost buttons on one line. Edit opens an inline field plus a required reason. Reject opens a required reason. On save, the row collapses with its toast and the next row takes focus. Rule flags are deferred. |
| Changed highlight | Run impact view | Anything the run touched carries the changed mark. No "Mark as seen" (deferred with Teams' `last_seen_seq`). |
| Capability tag | See the MongoDB section | Static. Hover or focus shows one sentence on what the capability does here. |

### Deferred (pivot, 13 Nov)

These serve only deferred surfaces. Do not build them on Saturday: Rule draft panel, Rule switch, Alert item, Parsed-query chips, Comparison table, Job counter (replaced by the identity card and the action feed), Welcome-back panel, Capture box.

## State Patterns

### New for the governed agent

| State | Surface | Treatment |
|---|---|---|
| Blocked | Action row, Audit entry | Blocked mark (icon and the word "Blocked", see `DESIGN.md`) and the line "Blocked before it ran: {check} failed under policy v{n}". No record link and no issue link, because neither exists. The Audit entry adds "No record changed. No external call made." |
| Unknown | Action row, Audit entry, identity card totals | Unknown mark and "Result unknown. GitHub didn't confirm. Search `dxp-review-sandbox` for action {action_id} to reconcile by hand." The action ID is copyable. It counts as unresolved in the totals until the API reports it reconciled. Never shown as success or failure. |
| Stopping | Identity card, feed header | "Stopping: {n} actions in flight. No new actions will start." Stop button disabled. In-flight rows keep updating until they settle. |
| Stopped | Identity card, feed header | "Stopped at {time}. {a} took effect, {b} blocked, {c} unknown." No new rows arrive. |
| Feed fallback | Run feed status | If change streams are unavailable on the Atlas Sandbox tier, or the stream drops, the feed polls `GET /changes` every 2 seconds. The status line and tag switch to "Live (polling every 2 seconds)". No error toast: this is a supported mode, not a failure. |
| Empty run | Run console | "No actions yet. The agent is reading the selected trials." |
| No runs | `/runs` | "No runs yet. Start one over the selected trial set." with the Start run button. |

### Kept

| State | Surface | Treatment |
|---|---|---|
| Loading | Any data surface | shadcn `Skeleton` rows shaped like the final layout. Never the "No data" text while loading. |
| Field with no value | Record | "No data for this indication" in `{colors.muted-foreground}`. |
| No stage evidence | Anywhere a stage shows | Empty stage track and "Stage not determined". |
| Value failed the check | Everywhere | Not shown at all (AD-6). Nothing to design. |
| Low confidence | Record, Review | "Low confidence" marker; in Review these rows come first. |
| Empty review queue | Review | "Nothing waiting for review. New proposals arrive when a run is going." Link to the Run console. |
| Audio failed (stretch) | Audit view | Inline: "Couldn't load the briefing." The audit stays readable. |
| API unreachable | Global | One toast: "Couldn't reach the API. Retrying in 5 seconds." Retries with backoff; no modal. |
| Synthetic data | Teams, people acting for, corrections | Synthetic badge, always. |

**Deferred (pivot, 13 Nov):** No Alerts, Empty Digest, Query with no results, Job running, Job stalled, Memory unavailable.

## Interaction Primitives

- Mouse and keyboard equally. In Review, `j` / `k` move between rows, `a` accepts, `e` edits, `r` rejects, `Esc` cancels. In the Run console and Audit view, `j` / `k` move between action rows and Enter opens one. Shortcuts are listed on each page.
- **Live data through change streams, never by reload.** The action feed, run status and Review count come from `GET /changes?after=<seq>&run_id=` (Story 9.9, PR A12), which long-polls and is woken by Atlas change streams. When change streams are unavailable, the same screens poll that route every 2 seconds (AD-10, AD-23). The screen behaves the same either way.
- Long work is a run. No page waits on a request longer than 30 seconds (AD-9).
- Banned: infinite scroll (paginate with `next`), hover-only actions, modal on modal, auto-playing audio, any celebratory animation, and spinners that suggest work the API has not reported.
- **Motion: one moment only, on the action feed.** A new action row fades and slides 8px into place once (about 200ms) when it arrives. State changes within a row are instant. Nothing else animates; the network pulse on Home and Graph is **Deferred (pivot, 13 Nov)** with the Home hero. Respect `prefers-reduced-motion` by skipping the fade.

## Accessibility Floor

- WCAG 2.2 AA. Colour contrast in `DESIGN.md` (eosin uses `{colors.eosin-text}` for text).
- Every action, including Stop run and "Who authorised this?", is a labelled button reachable by keyboard; tab order follows reading order.
- Colour is never the only signal: blocked has an icon and the word "Blocked"; unknown has an icon and "Result unknown"; change has "Changed"; confidence has "Low confidence"; node types have shapes.
- The Run impact view links to "View as list": every touched item and issue in a plain list. The Audit view is also a full text equivalent of the run.
- Live regions: run status (stopping, stopped) and the Review count announce politely (`aria-live="polite"`). The feed announces only blocked and unknown actions, so a busy run does not flood a screen reader.
- Focus rings use shadcn's `ring`, visible on the slide background.

## Evidence Display Rules

Product-specific. These restate AD-6 for the screen so no WEB story invents its own.

- A value appears only with its Evidence. The quote, source name, identifier link and "data as of" date travel together.
- PubMed abstract text never appears; only the quote (at most 300 characters) does.
- Unreviewed values are visible to everyone and labelled "Unreviewed".
- The Early research label is computed by the API (`early_research`); the screen only displays it.
- Every value changed by an agent action links to that action's Audit entry.

## MongoDB Capability Tags

Shown on screen because the demo and video are judged on it (NFR10). One quiet tag per panel, never more.

| Panel | Tag | Hover sentence |
|---|---|---|
| Run console action feed | Change streams (or "Polling" on the fallback) | "New actions appear as MongoDB records them, through Atlas change streams." |
| Identity card (grant and policy set) | Schema validation | "Grants and policies are checked by `$jsonSchema` validation in Atlas, so a malformed grant can't be saved." |
| Run impact view | `$graphLookup` | "Follows what this run touched, from each Diagnostic to its trials and review issues, in the database." |

**Deferred (pivot, 13 Nov):** Atlas Vector Search (Find), Agent Memory (welcome-back panel, Rules).

## Demo on Camera

Two judged moments: the 60-second video (recorded 16:30 to 16:50, submitted by 16:55) and the 3-minute live demo for judging from 17:15. Both show only work built on 14 November.

- Recorded at 1440 × 900 and shown live on the venue screen [ASSUMPTION: check the venue resolution at kick-off]. Browser zoom 100%; nothing essential below the fold on the Run console, Audit view or the identity card.
- Before each take: run the reset procedure (PR A16), so the selected trials are unprocessed and no run is in progress. Open a second tab on `dxp-review-sandbox` issues, signed in, so the new issue can be shown in GitHub itself.
- Check the feed status line. If it reads "Polling", the demo still works; say so rather than hide it.
- The one motion moment (rows arriving in the feed) is the visual rhythm; the climax is the blocked row and the "Who authorised this?" answer, not an animation.
- Keep the camera on the agent's behaviour: identity, gate, action, stop, audit. Record and impact screens are supporting shots.

## Inspiration & Anti-patterns

- **From pathology:** the H&E palette and the idea that pink means "look here".
- **From journal reading:** quotes in serif, with the source underneath, like a citation.
- **From audit logs and flight recorders:** every action in order, with who, under what authority, and what happened.
- **From shadcn:** the whole component vocabulary; DxP adds only the brand layer.
- **Rejected: a dashboard as the main feature.** Banned by the hackathon, and it hides the agent.
- **Rejected: dark "AI dashboard" look.** It reads as generic and fights the tables.
- **Rejected: KPI cards.** The console answers "what is the agent doing and was it allowed", not "how big is the database".
- **Rejected: a chat box as the main interface.**

## Key Flows

Protagonists: Rowan, Director of Diagnostics at a pharmaceutical therapy-area team, and Sam, the data curator who reviews proposals. [ASSUMPTION: names invented for these flows; the PRD names roles only.] The run acts for Rowan's Team; Sam operates it.

### Flow 1: the 3-minute live demo

| Time | Step |
|---|---|
| 0:00 to 0:20 | Sam opens the Run console and presses "Start run" over the selected trials. The identity card fills: agent dxp-curator, run ID, acting for Rowan (Team Lung Dx, Synthetic), grant G-7 v2, policy set v3. |
| 0:20 to 0:50 | Actions stream into the feed: allowed, dispatching, in flight. One takes effect: "Took effect: issue #12 opened in `dxp-review-sandbox`". Sam opens the issue in GitHub itself. |
| 0:50 to 1:15 | One action arrives blocked: "Blocked before it ran: Diagnostic in team scope failed under policy v3." Sam opens its Audit entry: no record changed, no external call made. |
| 1:15 to 1:40 | Sam opens Review and accepts a Proposed change, with its quote. |
| 1:40 to 2:00 | Back on the Run console, Sam presses "Stop run" mid-flight. The card reads "Stopping: 2 actions in flight", then "Stopped". |
| 2:00 to 2:35 | **Climax:** Rowan's question, "Who moved SuperARMS to clinical utility, and under what authority?" Sam opens the Audit view, finds the action and presses "Who authorised this?". The answer names the agent, run, person acted for, grant and policy-set version, with the quote and the issue. |
| 2:35 to 3:00 | The Run impact view shows exactly what the run touched, the GitHub issues as nodes. Stretch: play the spoken audit briefing. |

Failure: GitHub times out. The row shows "Result unknown" with the action ID; Sam names it as the reconciliation path, and the demo continues.

### Flow 2: the 60-second video

| Seconds | Shows | Screen |
|---|---|---|
| 0 to 10 | The problem and the agent's authorised scope | Identity card: agent, acting for, grant, policy set |
| 10 to 30 | An allowed action across two systems | The Record updated with its quote, then the review issue open in GitHub itself |
| 30 to 45 | An out-of-scope action blocked before execution | Blocked action row, then its Audit entry: no record change, no issue, one audit event |
| 45 to 60 | Stop and inspect | "Stop run", stopping, then stopped; "Who authorised this?" on the completed action |

### Earlier flows

All **Deferred (pivot, 13 Nov)**. The full text is in git history (commit `f4e943d`).

- Flow 1, the live run with Jobs, rule drafting, Alerts and the graph pulse: replaced by the two flows above.
- Flow 2, back the day after (UJ-1, Home, welcome-back, Find): deferred.
- Flow 3, clearing the Digest (UJ-3): deferred; keyboard review survives in Review.
- Flow 4, filling a Category's gaps (UJ-2): deferred.
