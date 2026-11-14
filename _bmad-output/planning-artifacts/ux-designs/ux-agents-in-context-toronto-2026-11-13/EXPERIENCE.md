---
name: DxProvida (DxP)
title: DxProvida (DxP) Experience
status: final  # revised for the pivot, 13 Nov, the readiness fixes, 14 Nov (readiness-fixes-2026-11-14.md), and the Slack change, 14 Nov (sprint-change-proposal-2026-11-14-slack.md)
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxProvida (DxP): experience spine

**Revised for the pivot (13 November).** DxP is now pitched and built for Statement 1, "Agents You Can Audit". The approved sources are `_bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md` (decisions D1 to D57) and `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md`. Where this file disagrees with either, the readiness fixes win first, then the proposal; on API routes, shapes and status values the architecture spine (AD-14, AD-17 to AD-24) wins, and on page routes and PRs `development-plan.md` wins.

**Slack replaces GitHub (14 November).** The external system is a Slack alert posted to `#all-mango-db-hackathon` through an incoming webhook (`sprint-change-proposal-2026-11-14-slack.md`, S1 to S13). That file wins wherever any document mentions the external system. The alert only notifies: it carries a "Review in DxP" link and an "Open diagnostic" link, and no buttons. Approval and rejection happen in DxP, never in Slack.

## What to build from

There are no mockups. The earlier key-screen mockups and design-round files were removed on 13 November with the pivot, because the hackathon rules allow only work built during the event to be shown. Every screen is built on Saturday, from 10:45, from this file and `DESIGN.md`:

| Surface | Build from |
|---|---|
| Run console (Story 9.7) | This file's Run console sections, with `DESIGN.md` tokens |
| Audit view (Story 9.8) | This file's Audit view sections, with `DESIGN.md` tokens |
| Record and Review (Stories 1.3, 2.4 trimmed) | This file, trimmed scope |
| Run impact view (Story 5.2) | This file: scoped by `run_id`, with Slack alerts as notification nodes |

## Foundation

- **The governed agent is the product.** The screens only inspect it: who the agent is, what it may do, what it did, what was blocked, and who authorised each action. The hackathon bans "a dashboard as the main feature", so no screen is pitched or demoed as the product.
- **No medical advice.** DxP tracks evidence about diagnostic tests for pharma teams. It never tells anyone how to treat, test or manage a patient, and no copy reads as a recommendation for patient care.
- One responsive web app, desktop first, built on Next.js 16 App Router with shadcn/ui and Tailwind. `DESIGN.md` is the visual identity; this file is the behaviour.
- The web app reads and writes only through the API (AD-9, AD-14). It applies no display rule of its own: what the read model returns is what the screen shows (AD-6).
- **Authority is never set in the browser.** The actor is resolved server-side from the API key, and the grant defines the Team. There is no Team picker and no "your name" picker that confers anything. The Run console starts a run by choosing a grant from the ones the caller may start, each labelled with its Team (`POST /runs { grant_id, set }`). The top bar shows, read-only, who the API resolved the caller as, from `GET /whoami` (AD-14).
- **Display formats.** Grants show as `{grant_id}@v{version}` (for example `lbdx@v1`). Policy sets show as `ps_ab12… (N policies)`: the first characters of the hash and the member count. Run and action IDs show in their `run_…` and `act_…` forms. Identifiers are in mono and copyable.
- Everything is built and validated on the Atlas Sandbox. The demo shows only work built on 14 November.
- Fonts load through `next/font/google`: Atkinson Hyperlegible Next, Atkinson Hyperlegible Mono, Source Serif 4. [ASSUMPTION: if a family is missing from `next/font/google`, fall back to Atkinson Hyperlegible.]
- This file adds no stories of its own. The Story column below says which story builds each surface.

## Information Architecture

### Kept surfaces

| Surface | Route | Reached from | Purpose | Stories |
|---|---|---|---|---|
| Run console | `/runs`, `/runs/[run_id]` | Top bar, app open (`/` redirects to the latest run) | Start a run over the selected trial set by choosing a grant labelled with its Team; identity card; action feed (allowed, blocked, dispatching, Slack alert delivered, reconciling, unknown, failed); stop control; Resolve for an unknown alert, shown only when the signed-in principal's `actions` include `resolve_notification`. Complete with the live-feed flag off: it polls until PR A12 passes | 9.7, 9.9 |
| Audit view | `/runs/[run_id]/audit` | Run console, any action row, top bar | One run reconstructed decision by decision, allowed or blocked, with "Who authorised this" on every entry, and Resolve on an unknown alert under the same rule as the Run console; then an "After the run" section with the Reviewer decisions caused by the run | 9.8, 9.6 |
| Record and Review | `/diagnostics/[id]`, `/review`, `/review?proposal=<p_id>` | Record: links from Review rows, Audit entries, impact nodes and the Slack alert's "Open diagnostic" link (there is no Diagnostics list). Review: top bar (Review with pending count), and the Slack alert's "Review in DxP" link, which opens `/review?proposal=<p_id>` with that proposal focused | Record: fields with Evidence, unreviewed values marked, with Accept, Edit and Reject through the value-review route. Review: pending Proposed changes, accept, edit, reject; a focused proposal from `?proposal=`, loaded with `GET /proposals/<p_id>` (one proposal, whatever its status), or "Proposal not found". Trimmed: no history disclosure, no Learned rules, no add-a-value. Core, because core acceptance needs a Reviewer decision | 1.3, 2.2, 2.3, 2.4 (trimmed) |
| Run impact view | `/runs/[run_id]/impact` | Run console, Audit view, top bar; every link to it is hidden when the `impact` flag is off | The graph fed by `run_id`: by default only the changed elements (the values, proposals, edges and Slack alerts the run itself created or changed, each attributed to the run), with each Slack alert as a notification node (`notification:<action_id>`). "Show context" adds a touched Diagnostic's other neighbours, marked as context and not attributed to the run | 5.1, 5.2 |

These routes are the page files in `development-plan.md`: `web/app/runs/page.tsx` and `web/app/runs/[run_id]/page.tsx` (B02), `web/app/runs/[run_id]/audit/` (B03), `web/app/diagnostics/` and `web/app/review/` (B04), `web/app/runs/[run_id]/impact/` (B05).

Top bar, left to right: the "DxP" text wordmark (set in the interface font and built during the event; the prepared logo images in `imports/` are not used unless an organiser clears them in writing), Run console, Audit, Review (count), Impact (only when the `impact` flag is on); then the read-only "Signed in as" chip. Footer: the credits line. The top bar, tokens, stage track and badges are built once in the minimal shell (Stories 1.12 trimmed, PR B01).

Dialogs stack one level deep. The right-hand panel (360px) opens Evidence and the "Who authorised this" answer without leaving the page.

### Earlier surfaces

| Surface | Route | Status |
|---|---|---|
| Home (dashboard and graph-led hero) | `/` | **Deferred (pivot, 13 Nov).** `/` redirects to the latest run |
| Diagnostics list | `/diagnostics` | **Not built (deferred, pivot 13 Nov).** The Record page is reached from Review, Audit and Impact links |
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
| "Blocked before it ran: Diagnostic in team scope failed under policy set `ps_ab12…` (4 policies)" | "Action denied", "Permission error", "403" |
| "Result unknown. Slack didn't confirm. Check #all-mango-db-hackathon for `act_7f3c…`, then resolve." | "Something went wrong", "Retrying…" |
| "Slack alert delivered at 15:04 to #all-mango-db-hackathon" | "Sent!", "Message posted successfully" |
| "Slack alert failed: Slack refused it (`channel_not_found`). Not retried." | "Error 404", "Webhook error" |
| "Approve or reject in DxP. Slack only notifies." | "Approve in Slack", "Reply in Slack to approve" |
| "Stopping: 2 in flight. No new actions will start." | "Please wait…" |
| "Stopped at 15:12. 9 took effect, 1 blocked, 0 unknown." | "Run cancelled" |
| "Who authorised this?" and the answer as one sentence, built from the Decision's `authorised_by`: "Allowed by grant `lbdx@v1` (dxp-curator for Team Liquid Biopsy Dx, proposals to the ledger and alerts to #all-mango-db-hackathon) under policy set `ps_ab12…` (4 policies), executed by agent dxp-curator in run `run_8c41…`, started by Sam." | "Authorization details", raw JSON |
| "Proposal filed (pending review): add trial NCT04712877 to FoundationOne Liquid CDx. Slack alert delivered at 15:04" | "Success!", "Record updated" |
| "Proposal not found. Open Review to see what is pending." | "404", "Invalid link" |
| "Started by Sam (Synthetic)"; "Team Liquid Biopsy Dx (Synthetic)" | "User: sam" |
| "No data for this indication" | "N/A", "—", "Unknown" |
| "Stage not determined" | "Unstaged", "TBD" |
| "Accept", "Edit", "Reject"; toast "Accepted", "Edited", "Rejected" | "Submit", "Confirm action" |
| "Couldn't reach the API. Retrying in 5 seconds." | "Oops! Something went wrong." |
| "Early research" on discovery and assay development | "Unvalidated", "Low quality" |
| "Synthetic" on every made-up Team, grant holder and correction | Leaving synthetic data unlabelled |
| Evidence about a test: "Trial NCT04712877 names FoundationOne Liquid CDx" | Patient advice: "Recommended for patients with…", "Use this test to decide treatment" |

The five checks always appear under these names: **Grant active**, **Diagnostic in team scope**, **Destination and action match the grant**, **Evidence checks passed**, **Run still authorised**. The failed check is named in the blocked line with the policy set that was in force, shown as `ps_ab12… (N policies)`. For Reviewer decisions (accept, edit, reject, review a value, and resolve an unknown alert), **Evidence checks passed** reads "Not applicable" (the API records `n/a`, as it does for seed writes, `apply_value`). The check applies only to **File proposal** and **Send Slack alert**. An edit or reject carries its reason instead, and a resolve carries its note.

Action kinds always appear under these names: **File proposal** (`file_proposal`) and **Send Slack alert** (`notify_slack`). A Reviewer's settling of an unknown alert appears as **Resolve Slack alert** (`resolve_notification`).

## Component Patterns

Behavioural. Visual specs live in `DESIGN.md` Components.

### New for the governed agent

| Component | Where | Behaviour |
|---|---|---|
| Identity card | Run console (top), Audit view (top) | Two identities, never merged. **Agent:** the executing agent named by the grant (name and model). **Started by:** "Started by {initiated_by}", the principal resolved server-side from the caller's key when the run was started. Also the run ID (`run_…`), prompt version, the grant as `{grant_id}@v{version}` (version pinned at start, with its Team, destination, allowed actions and expiry), the policy set as `ps_ab12… (N policies)`, and the run status (running, stopping, stopped, done, failed). Every value comes from the run record; nothing is editable. Identifiers are copyable. A synthetic Team or person carries the Synthetic badge. The top bar's "Signed in as" chip is separate and unchanged: it shows who the current viewer is, not who started the run. |
| Action row | Run console feed, Audit view | One row per gate decision: kind ("File proposal" or "Send Slack alert"), Diagnostic, field or destination (`ledger` or `#all-mango-db-hackathon`), current state, time. A row appears when the gate decides (the `action_allowed` or `action_blocked` event), as either **blocked** (the failed check and policy version, nothing else happens) or **allowed** (`queued`), then **dispatching** (claimed, in flight). A "File proposal" row settles as **"Proposal filed (pending review)"**: in live mode an allowed change to a Diagnostic never updates the record directly, and is applied only when a Reviewer decides it in DxP. A "Send Slack alert" row settles in one of these states (see State Patterns): **"Slack alert delivered"** with the time posted; **Failed** with Slack's error (a 4xx, or a second 429), never retried; **Unknown** when the outcome is ambiguous (a timeout, a connection error or a 5xx), never retried, with "Check #all-mango-db-hackathon for {action_id}, then resolve" and, when the signed-in principal's `actions` include `resolve_notification`, a **Resolve** control; or **Reconciling** while the sweep settles it. When an admission is abandoned, `GET /runs/<id>` starts the background sweep and returns at once without calling Slack. A `dispatching` alert of that admission shows as **reconciling** while the sweep runs, then **unknown**. A `queued` action of that admission was never sent: it shows as **failed** with the reason "Never sent (`abandoned_before_send`)". The row updates in place as its state changes; it never jumps position. Click or Enter opens the entry in the Audit view. |
| Resolve control | Unknown "Send Slack alert" row, in the Run console and the Audit view; shown only when the signed-in principal's `actions` include `resolve_notification`. `GET /whoami` returns `Principal { id, name, kind, actions }`, where `actions` are the actions of the caller's current grant (for Sam, principal `sam` with grant `sam@v1`) | A secondary button "Resolve". It opens an inline form, not a dialog: the action ID (copyable), the instruction "Check #all-mango-db-hackathon for {action_id}, then resolve", two radio options "Delivered: I found it in the channel" and "Failed: it is not in the channel", and a required note. "Save resolution" calls `POST /actions/<action_id>/resolve { outcome, note }`. On success the action carries `resolution { outcome, note, decision_id, by, at }`; the row shows the chosen state with "Resolved by Sam at {time}", and the resolution appears under "After the run". Viewers whose `actions` do not include `resolve_notification` see the Unknown state and the instruction, but no button. |
| Stop control | Run console identity card | "Stop run" while the run is **running**. One press, no confirmation dialog: stopping is the safe direction. New admissions stop at once: no new action starts after the press. The button then disables and the card reads **"Stopping: {n} in flight"** while actions already admitted finish. When none remain in flight the card reads **"Stopped"** with the totals. A stopped run cannot be restarted from here; start a new run. |
| Audit entry | Audit view | One entry per gate decision, allowed or blocked, in order. Opening any entry loads its detail from `GET /decisions/<decision_id>`. Every entry shows the timestamps, the inputs, the evidence reference (as an Evidence quote), the destination, every check with its result and detail, the grant actually evaluated (`{grant_id}@v{version}`), the policy set (`ps_ab12… (N policies)`) and the outcome. An allowed entry adds the action's status and result. A "File proposal" entry shows "Proposal filed (pending review)". A "Send Slack alert" entry shows the destination `#all-mango-db-hackathon`, the timestamps (queued, claimed, posted, observed) and the notification result from `result { http_status, response_body, posted_at, link_urls { review_url, diagnostic_url } }`: "Slack alert delivered at {time}" with the HTTP status and Slack's response, "Failed" with the error, or "Result unknown"; plus the two link URLs sent ("Review in DxP" and "Open diagnostic"). A resolved alert also shows its `resolution { outcome, note, decision_id, by, at }`. The webhook URL never appears. Both kinds also show the proposal's **live review status** in DxP: "Pending review", "Applied by Sam at {time}" or "Rejected by Sam at {time}", read live, so it changes after the run when Sam decides. A blocked entry names the failed check and states "No record changed. No external call made." "Who authorised this?" opens the answer in the right-hand panel, built from the Decision's `authorised_by`. |
| After the run | Audit view, below the run's entries | The Reviewer decisions caused by this run (accept, edit, reject, and resolving an unknown Slack alert), each with the Reviewer, the time and links to the originating run and proposal. These are written without a run ID and stamped `agent: null`, `initiated_by: <reviewer>`, so the entry reads "Decided by Sam (Synthetic)" with no agent. They sit in their own section, never mixed into the agent's entries. Empty state: "No Reviewer decisions yet." |
| Run feed status | Run console, above the feed | Says how the feed is live: "Live (polling every 2 seconds)" by default, or "Live (change streams)" once the change-streams feed (PR A12) has passed its acceptance check. Carries the capability tag. The Run console is complete with the feed flag off; the change-streams feed shows only if A12 passed. |

### Kept

| Component | Where | Behaviour |
|---|---|---|
| Stage track | Record header, Review row, impact view tooltip | Read-only. Tooltip names all nine stages and the date each was reached. A segment advanced by the current run shows `{colors.eosin}` with the word "Changed" on the impact view only; elsewhere the segment is a plain fill. |
| Evidence quote | Record, Review row, Audit entry | Always shows source, identifier link and "data as of". Never shows a value without it. |
| Value | Record | Current value(s) with Evidence. Unreviewed values show "Unreviewed" and, for a Reviewer, Accept / Edit / Reject inline. Each goes through the value-review route, `POST /diagnostics/<dx_id>/values/<value_id>/review`; Edit and Reject require a reason. There is no "Mark reviewed" button. The "History" disclosure (Story 2.5) is **Deferred (pivot, 13 Nov)**. |
| Proposal row | Review | Diagnostic, field, current → new written as a sentence ("Add trial NCT04712877 to Trials"), quote, confidence, the run ID that proposed it and its Slack alert status (from the proposal's `notification { action_id, status, posted_at }`, which the API builds at read time from the proposal's `notify_slack` action; each filed proposal has its own alert), for example "Slack alert delivered at 15:04". The Diagnostic name links to its Record. **Focused from a link:** when the page opens as `/review?proposal=<p_id>` (the Slack alert's "Review in DxP" link), the page loads it with `GET /proposals/<p_id>` (there is no `p_id=` query parameter), and that proposal is scrolled into view, focused and outlined, even if it is no longer pending; a decided proposal shows its decision ("Applied by Sam at {time}") instead of the buttons. If the ID is unknown, the page shows "Proposal not found. Open Review to see what is pending." above the normal queue. The focused row shows full Accept / Edit / Reject buttons; other rows show compact ghost buttons on one line. Edit opens an inline field plus a required reason. Reject opens a required reason. On save, the row collapses with its toast and the next row takes focus. Rule flags are deferred. |
| Changed highlight | Run impact view | Only the changed elements (values, proposals, edges and notification nodes the run itself created or changed) carry the changed mark and the run ID. Context nodes shown by "Show context" never carry it: they are drawn faded with the word "Context" and are not attributed to the run. No "Mark as seen" (deferred with Teams' `last_seen_seq`). |
| Capability tag | See the MongoDB section | Static. Hover or focus shows one sentence on what the capability does here. |

### Deferred (pivot, 13 Nov)

These serve only deferred surfaces. Do not build them on Saturday: Rule draft panel, Rule switch, Alert item, Parsed-query chips, Comparison table, Job counter (replaced by the identity card and the action feed), Welcome-back panel, Capture box.

## State Patterns

### New for the governed agent

| State | Surface | Treatment |
|---|---|---|
| Blocked | Action row, Audit entry | Blocked mark (icon and the word "Blocked", see `DESIGN.md`) and the line "Blocked before it ran: {check} failed under policy set `ps_ab12…` (N policies)". No record link and no Slack alert, because neither exists. The Audit entry adds "No record changed. No external call made." |
| Slack alert delivered | Action row, Audit entry, proposal row | Delivered mark (`bell` icon and the words "Slack alert delivered") and the time posted: "Slack alert delivered at 15:04 to #all-mango-db-hackathon". Slack answered HTTP 200 `ok`. The proposal is still pending until a Reviewer decides it in DxP; the row never reads as "approved". |
| Failed | Action row, Audit entry | Failed mark (`circle-x` and the word "Failed") and Slack's error: "Slack alert failed: Slack refused it (`{error}`). Not retried." Covers a 4xx and a second 429. Nothing to resolve. |
| Unknown | Action row, Audit entry, identity card totals | Unknown mark and "Result unknown. Slack didn't confirm. Check #all-mango-db-hackathon for {action_id}, then resolve." The action ID is copyable. The **Resolve** control shows when the signed-in principal's `actions` include `resolve_notification` (see Component Patterns). It is never retried automatically. It counts as unresolved in the totals until a Reviewer resolves it. Never shown as success or failure. |
| Proposal filed (pending review) | Action row, Audit entry | An allowed change to a Diagnostic, filed as a pending proposal: "Proposal filed (pending review)", followed by its Slack alert's state. The record itself does not change until Sam accepts or edits the proposal in DxP, in Record and Review; that decision then appears under "After the run". |
| Proposal not found | Review (`/review?proposal=<p_id>`) | The `proposal` ID is unknown: "Proposal not found. Open Review to see what is pending." shown as an inline notice above the queue, with the normal queue below it. No error toast. |
| Stopping | Identity card, feed header | "Stopping: {n} in flight. No new actions will start." New admissions stopped at the press. Stop button disabled. Actions already admitted may finish, and their rows keep updating until they settle. |
| Stopped | Identity card, feed header | "Stopped at {time}. {a} took effect, {b} blocked, {c} unknown." Shown once no admitted action remains. No new rows arrive. |
| Reconciling | Action row, Audit entry | A read-time state only: an action whose admission was abandoned (its lease ran out) while it was dispatching. `GET /runs/<id>` never calls Slack: it starts the background sweep and returns the current state at once, with the action as `reconciling`. "Reconciling: settling action {action_id}." It then shows Unknown, never retried, for a Reviewer to resolve. Counts as unresolved in the totals. |
| Failed, never sent | Action row, Audit entry | A `queued` action whose admission was abandoned. The sweep marks it `failed` with reason `abandoned_before_send`. "Failed: never sent. Its admission ran out before the Slack alert was posted." Failed mark (`circle-x`). It was never sent, so there is nothing to resolve. |
| Feed fallback | Run feed status | Until the change-streams feed (PR A12) passes its acceptance check, the screens poll every 2 seconds: the Run console and Audit view poll `GET /runs/<id>` and `GET /runs/<id>/audit`, and the Review count polls `GET /proposals?status=pending`. Polling is also the fallback if change streams are unavailable or the stream drops. The status line and tag read "Live (polling every 2 seconds)". No error toast: this is a supported mode, not a failure. |
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
| Audio briefing (stretch) | Audit view, briefing page | The Audit view shows a "Listen" link that opens a separate briefing page; the Audit view itself has no player. On the briefing page, if the audio fails: "Couldn't load the briefing." The audit stays readable. The "Listen" link appears at all only if the audio (PR B06) passed its acceptance check after the 14:30 loop was green. |
| API unreachable | Global | One toast: "Couldn't reach the API. Retrying in 5 seconds." Retries with backoff; no modal. |
| Synthetic data | Teams, people who start runs, corrections | Synthetic badge, always. |

**Deferred (pivot, 13 Nov):** No Alerts, Empty Digest, Query with no results, Job running, Job stalled, Memory unavailable.

## Interaction Primitives

- Mouse and keyboard equally. In Review, `j` / `k` move between rows, `a` accepts, `e` edits, `r` rejects, `Esc` cancels. In the Run console and Audit view, `j` / `k` move between action rows and Enter opens one. Shortcuts are listed on each page.
- **Live data, never by reload.** Until the change-streams feed (Story 9.9, PR A12) lands and passes its acceptance check, the screens poll every 2 seconds: the action feed and run status from `GET /runs/<id>` and `GET /runs/<id>/audit`, and the Review count from `GET /proposals?status=pending`. After A12 passes, the feed is woken by Atlas change streams, and polling stays as the fallback (AD-10, AD-23). The screen behaves the same either way, and is complete with the feed flag off.
- Long work is a run. No page waits on a request longer than 30 seconds (AD-9).
- Banned: infinite scroll (paginate with `next`), hover-only actions, modal on modal, auto-playing audio, any celebratory animation, and spinners that suggest work the API has not reported.
- **Motion: one moment only, on the action feed.** A new action row fades and slides 8px into place once (about 200ms) when it arrives. State changes within a row are instant. Nothing else animates; the network pulse on Home and Graph is **Deferred (pivot, 13 Nov)** with the Home hero. Respect `prefers-reduced-motion` by skipping the fade.

## Accessibility Floor

- WCAG 2.2 AA. Colour contrast in `DESIGN.md` (eosin uses `{colors.eosin-text}` for text).
- Every action, including Stop run and "Who authorised this?", is a labelled button reachable by keyboard; tab order follows reading order.
- Colour is never the only signal: blocked has an icon and the word "Blocked"; unknown has an icon and "Result unknown"; a delivered alert has the `bell` icon and "Slack alert delivered"; failed has an icon and "Failed"; change has "Changed"; confidence has "Low confidence"; node types have shapes.
- The Run impact view links to "View as list": every changed element and Slack alert in a plain list, with context items (when shown) in a separate list headed "Context, not changed by this run". The Audit view is also a full text equivalent of the run.
- Live regions: run status (stopping, stopped) and the Review count announce politely (`aria-live="polite"`). The feed announces only blocked, failed and unknown actions, so a busy run does not flood a screen reader.
- The Resolve form's radio options and note are labelled; focus moves into the form when it opens and back to the row when it closes.
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
| Run console action feed | "Polling" by default; "Change streams" only once PR A12 passed its acceptance check | "New actions appear as MongoDB records them, through Atlas change streams." |
| Identity card (grant and policy set) | Schema validation | "Grants and policies are checked by `$jsonSchema` validation in Atlas, so a malformed grant can't be saved." |
| Audit view, notification entry | Atomic updates | "Each Slack alert is claimed with one conditional update in Atlas, so two workers never both post it." |
| Run impact view (only if it passed its acceptance check) | `$graphLookup` | "Follows what this run changed, from each Diagnostic to its trials and Slack alerts, in the database." |

**Deferred (pivot, 13 Nov):** Atlas Vector Search (Find), Agent Memory (welcome-back panel, Rules).

## Demo on Camera

Two judged moments: the 60-second video (recorded 16:30 to 16:50, submitted by 16:55) and the 3-minute live demo for judging from 17:15. Both show only work built on 14 November.

- Recorded at 1440 × 900 and shown live on the venue screen [ASSUMPTION: check the venue resolution at kick-off]. Browser zoom 100%; nothing essential below the fold on the Run console, Audit view or the identity card.
- **Reset before each take (PR A16).** A snapshot is taken after seeding and before any run; the reset restores it with `mongodump` and `mongorestore`, so the selected trials are unprocessed and no run is in progress. It runs before the video (16:30) and again between submission and the live demo (16:55 to 17:10). Then open a second tab on Slack `#all-mango-db-hackathon`, signed in, so the new alert can be shown arriving in Slack itself. Confirm that `DXP_BASE_URL` points at the production URL, so the alert's "Review in DxP" link opens the deployed app. The webhook URL is never shown on screen.
- **Pacing.** The run uses `DXP_DEMO_PACE`: one item at a time, a few seconds per item. The selected trials are processed in a fixed order, so the first item is NCT04712877 and the stop lands while items remain.
- **The scenario, from real data.** Selected trial NCT04712877 names both FoundationOne Liquid CDx (a plasma test) and FoundationOne CDx (a tissue test); both are FDA-seeded. The agent dxp-curator acts under grant `lbdx@v1`, Team Liquid Biopsy Dx (Synthetic), whose scope is "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay". The proposal to add NCT04712877 to FoundationOne Liquid CDx's trials is allowed: a pending proposal plus its own Slack alert (one alert per filed proposal). The same trial's proposal for FoundationOne CDx is blocked before execution, because **Diagnostic in team scope** fails: the tissue test is outside the Team's scope. No proposal is filed and no Slack message is sent. No stage transition is shown.
- **The order, for both the video and the live demo:**
  1. Start the run.
  2. The allowed proposal and its Slack alert arriving in `#all-mango-db-hackathon` on the second tab; its "Review in DxP" link opens the focused proposal. Then the blocked one.
  3. Stop the run while items remain.
  4. Sam approves the pending proposal in DxP; it appears under "After the run". Nothing is approved in Slack.
  5. Ask the scripted question in the Audit view.
- **The scripted question:** "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"
- **Only what passed goes on camera.** The core loop (identity card, feed by polling, proposal and Slack alert, blocked row, stop, Review, Audit) is always shown. The change-streams feed, the Run impact view and the audio briefing appear only if each passed its own acceptance check; the audio also only if it passed after the 14:30 loop was green. When the `impact` flag is off, no impact link shows. Anything else is left out, not apologised for.
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

Protagonists: Rowan, Director of Diagnostics at a pharmaceutical therapy-area team, and Sam, the data curator who reviews proposals. [ASSUMPTION: names invented for these flows; the PRD names roles only.] The run works for Rowan's Team, Team Liquid Biopsy Dx (Synthetic); Sam starts and operates it, so the identity card reads "Started by Sam".

### Flow 1: the 3-minute live demo

| Time | Step |
|---|---|
| 0:00 to 0:20 | **Start.** Sam opens the Run console, chooses the grant labelled "Team Liquid Biopsy Dx (Synthetic)" and presses "Start run" over the selected trials. The identity card fills: agent dxp-curator, run `run_8c41…`, "Started by Sam", grant `lbdx@v1`, policy set `ps_ab12…` (4 policies). The run is paced, so the first item is NCT04712877. |
| 0:20 to 0:50 | **Allowed.** The first actions arrive: allowed, dispatching. The NCT04712877 proposal for FoundationOne Liquid CDx reads "Proposal filed (pending review)", and its alert row reads "Slack alert delivered at {time}". Sam switches to the second tab: the alert has arrived in Slack `#all-mango-db-hackathon`, with the action ID, the quote and "Approve or reject in DxP. Slack only notifies." Sam presses "Review in DxP", which opens Review with that proposal focused, still pending, then returns to the Run console. |
| 0:50 to 1:15 | **Blocked.** The same trial's proposal for FoundationOne CDx arrives blocked: "Blocked before it ran: Diagnostic in team scope failed under policy set `ps_ab12…` (4 policies)." Sam opens its Audit entry: every check with its result, the grant evaluated, the policy set, inputs, evidence and destination, and "No record changed. No external call made." |
| 1:15 to 1:35 | **Stop.** Back on the Run console, Sam presses "Stop run" while items remain. No new action starts. The card reads "Stopping: 2 in flight" while admitted actions finish, then "Stopped". |
| 1:35 to 2:00 | **Approve.** Sam returns to the focused proposal in Review and accepts it in DxP, with its quote. Only now does the record change. The acceptance appears in the Audit view under "After the run". |
| 2:00 to 2:35 | **Climax, the question.** Rowan asks, "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?" Sam opens the Audit view, finds the entry and presses "Who authorised this?". The answer, from the Decision's `authorised_by`, names the agent, the run, who started it, the grant and the policy set, with the quote, the Slack alert's result and the proposal's live review status ("Applied by Sam at {time}"). Under "After the run", Sam's own acceptance links back to the run and the proposal. |
| 2:35 to 3:00 | If it passed its acceptance check: the Run impact view shows only what the run changed, the Slack alert as a notification node; "Show context" adds neighbours marked as context. If the audio briefing passed its check after the 14:30 loop: follow "Listen" to the briefing page and play it. Otherwise close on the Audit view. |

Failure: the Slack post times out. The row shows "Result unknown" with the action ID and is not retried. Sam checks `#all-mango-db-hackathon` for the action ID, presses Resolve and records the outcome with a note, and the demo continues.

### Flow 2: the 60-second video

| Seconds | Shows | Screen |
|---|---|---|
| 0 to 10 | The problem and the scope; the run starts | Grant chosen (labelled with its Team), "Start run", then the identity card: agent dxp-curator, "Started by Sam", grant `lbdx@v1`, policy set `ps_ab12…` (4 policies) |
| 10 to 30 | The allowed proposal and its Slack alert, then the blocked change | "Proposal filed (pending review)" for NCT04712877 on FoundationOne Liquid CDx, then the alert arriving in Slack `#all-mango-db-hackathon`; then the FoundationOne CDx row blocked on **Diagnostic in team scope**: no record change, no Slack message |
| 30 to 45 | Stop | "Stop run" while items remain, stopping, then stopped |
| 45 to 60 | Sam approves in DxP, then "who authorised this?" | Sam accepts the pending proposal in Review in DxP, and it appears under "After the run"; then "Who authorised this?" in the Audit view answering "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?" |

The timings follow readiness fix D52 and match PRD SM-2.

### Earlier flows

All **Deferred (pivot, 13 Nov)**. The full text is in git history (commit `f4e943d`).

- Flow 1, the live run with Jobs, rule drafting, Alerts and the graph pulse: replaced by the two flows above.
- Flow 2, back the day after (UJ-1, Home, welcome-back, Find): deferred.
- Flow 3, clearing the Digest (UJ-3): deferred; keyboard review survives in Review.
- Flow 4, filling a Category's gaps (UJ-2): deferred.
