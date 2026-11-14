---
name: DxProvida (DxP)
title: DxProvida (DxP) Experience
status: draft
created: 2026-11-13
updated: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxProvida (DxP) — Experience Spine

## Foundation

- One responsive web app, desktop first, built on Next.js 16 App Router with shadcn/ui and Tailwind. `DESIGN.md` is the visual identity; this file is the behaviour. Both win over any mock.
- The web app reads and writes only through the API (AD-9, AD-14). It applies no display rule of its own: what the read model returns is what the screen shows (AD-6).
- There is no login. The top bar holds a **Team picker** (which Team's view you are in) and a **"your name" picker** (sent as `actor` on every decision). Both are kept in the browser.
- Fonts load through `next/font/google`: Atkinson Hyperlegible Next, Atkinson Hyperlegible Mono, Source Serif 4. [ASSUMPTION: if a family is missing from `next/font/google`, fall back to Atkinson Hyperlegible.]
- This file adds no stories of its own; the two pieces it needed (Story 1.12, the wider Story 6.4) were added to `epics.md` on 13 November. It is guidance for the WEB stories already in `epics.md`; the Story column below says which story builds each surface.

## Information Architecture

| Surface | Route | Reached from | Purpose | Stories |
|---|---|---|---|---|
| Home | `/` | App open, logo | Hero: the Team's mini network with what changed glowing, and the welcome-back panel docked over it; below: latest Alerts and the Digest | 6.4, 3.3, reuses the Graph component from 5.2 |
| Diagnostics | `/diagnostics` | Top bar | Every tracked Diagnostic with stage track and Early research badge | 1.3 |
| Record | `/diagnostics/[id]` | Any Diagnostic name, graph node, Alert, table row | All fields with Evidence, value history, review of unreviewed values, add a value | 1.3, 2.5, 4.7 |
| Find | `/find` | Top bar, welcome-back "Reopen" | Plain-language query, parsed-query chips, comparison table, Shortlist, export | 4.3, 4.4, 4.5 |
| Categories | `/categories` | Top bar | One Category's full field set, thin and stale Records marked, add a value | 4.6, 4.7 |
| Graph | `/graph` | Top bar | Connected view of Diagnostics, biomarkers, trials, drugs, tumour types, Providers; what changed | 5.2, 5.3 |
| Review | `/review` | Top bar (with pending count), Digest | Pending Proposed changes; accept, edit, reject; Learned rule draft | 2.4, 2.7 |
| Rules | `/rules` | Review, top bar overflow | Every Learned rule with on/off | 2.7 |
| Alerts | `/alerts` | Top bar (with unread count), Home | The Team's Alerts with why it matters and audio | 3.2, 3.5 |
| Jobs | `/jobs`, `/jobs/[id]` | Top bar | Start a job; live count; failures | 1.8 |
| Terms | `/terms` | Rules page link | Unmatched terms | 4.8 |

The top bar, design tokens, stage track and badges are built once in Story 1.12. Top bar, left to right: DxP logo, Home, Diagnostics, Find, Categories, Graph, Review (count), Alerts (count), Jobs; then the capture box (Story 7.1), Team picker, your-name picker. Footer: the credits line.

Dialogs stack one level deep. The right-hand panel (360px) opens Evidence, history and the rule draft without leaving the page.

## Voice and Tone

Microcopy. DxP speaks plainly to a scientist in a hurry. It names things the way the PRD Glossary does: Diagnostic, Record, Evidence, Proposed change, Learned rule, Alert, Team, Shortlist, Intended use, Lifecycle stage, Early research.

| Do | Don't |
|---|---|
| "No data for this indication" | "N/A", "—", "Unknown" |
| "Stage not determined" | "Unstaged", "TBD" |
| "3 changes since your last visit, 2 November" | "You have new updates!" |
| "Accept", "Edit", "Reject"; toast "Accepted", "Edited", "Rejected" | "Submit", "Confirm action" |
| "Reason for rejecting (DxP will suggest a rule from it)" | "Comment (optional)" |
| "DxP suggests this rule: …" | "AI-generated rule" |
| "A job is already running. Open it" | "Error 409" |
| "Couldn't reach the API. Retrying in 5 seconds." | "Oops! Something went wrong." |
| "Early research" on discovery and assay development | "Unvalidated", "Low quality" |
| "Synthetic" on every made-up Team, rule, correction and memory | Leaving synthetic data unlabelled |

## Component Patterns

Behavioural. Visual specs live in `DESIGN.md` Components.

| Component | Where | Behaviour |
|---|---|---|
| Stage track | Diagnostics list, Record header, comparison table, graph tooltip, Alerts | Read-only. Tooltip names all nine stages and the date each was reached. A just-advanced segment shows `{colors.eosin}` until the Team marks as seen. |
| Evidence quote | Record, comparison table cell, Review row, Alert | Always shows source, identifier link and "data as of". Opens in the right-hand panel from a table cell (click or Enter). Never shows a value without it. |
| Value with history | Record | Current value(s) first. "History" disclosure lists superseded and rejected values newest first with Evidence, who decided and when (Story 2.5). Unreviewed values show "Unreviewed" and, for a Reviewer, Accept / Edit / Reject inline. |
| Proposal row | Review | Diagnostic, field, current → new written as a sentence ("Add trial NCT06422546 to Trials"), quote, confidence, rule flags. The focused row shows full Accept / Edit / Reject buttons; other rows show the same three as compact ghost buttons on one line, so every action stays reachable without hover. Edit opens an inline field plus a required reason. Reject opens a required reason. On save, the row collapses with its toast and the next row takes focus. |
| Rule draft panel | Review, right-hand panel | Appears after an Edit or Reject that returns `rule_draft`. Text is editable. "Turn on rule" activates it and then lists the pending proposals it now flags; "Discard" closes it. If drafting failed, the panel does not appear. |
| Rule switch | Rules | On/off per rule, immediate. Turning off removes its flags; the count of affected proposals is shown in the toast. |
| Alert item | Alerts, Home | Kind (First seen / Update), trigger in words ("Moved to clinical utility"), the why line, stage track, Early research badge, link to Evidence, play button, dismiss. |
| Parsed-query chips | Find | Each filter DxP read from the text becomes a chip (field: value). Remove a chip or add one from a field menu; any change re-runs the query with filters only (no model call). The original text stays above. |
| Comparison table | Find, Categories | One row per Diagnostic, one column per criterion. Row checkbox for Shortlist. Each cell is focusable; Enter opens its Evidence. Empty cell: "No data for this indication". Sort by any column. |
| Job counter | Jobs | Processed / failed / Early research counts and a progress bar, polled every 2 seconds while running. Failures listed with `source_ref` and error. |
| Changed highlight | Graph, Home hero | Anything with `changed: true` or `seq` above the Team's `last_seen_seq` carries the changed mark. "Mark as seen" clears it for the Team. |
| Welcome-back panel | Home | Resume summary (2–3 sentences), "Since your last visit" list with links, "Reopen" buttons for last Intended use and Shortlist, capability tag naming the memory backend. |
| Capability tag | See the MongoDB section | Static. Hover or focus shows one sentence on what the capability does here. |
| Capture box | Top bar | One line. Enter submits; result toast links to the new or matched Record. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Loading | Any data surface | shadcn `Skeleton` rows shaped like the final layout. Never the "No data" text while loading. |
| Field with no value | Record, tables | "No data for this indication" in `{colors.muted-foreground}`. |
| No stage evidence | Anywhere a stage shows | Empty stage track and "Stage not determined". |
| Value failed the check | Everywhere | Not shown at all (AD-6). Nothing to design. |
| Low confidence | Record, Review | "Low confidence" marker; in Review these rows come first, then rows flagged by a Learned rule, then the rest. |
| Empty review queue | Review | "Nothing waiting for review. New proposals arrive when a live job runs." Link to Jobs. |
| No Alerts | Alerts, Home | "No Alerts for {Team} yet. You'll get one when a Diagnostic matching your profile appears." |
| Empty Digest | Home | "Nothing new for {Team} since {date}." |
| Query with no results | Find | Parsed chips stay. "No Diagnostics match these filters. Remove a filter to widen the search." |
| Job running | Jobs | Counter live; Start disabled with "A job is running". |
| Job stalled | Jobs | "No progress for 10 minutes. Start it again to resume." with a Start button. |
| Memory unavailable | Home | Welcome-back panel shows what changed and last Intended use (from DxP collections) and "Memory unavailable right now" in place of the summary. |
| Audio failed | Alert item | Inline: "Couldn't load the briefing." The why line stays readable. |
| API unreachable | Global | One toast: "Couldn't reach the API. Retrying in 5 seconds." Retries with backoff; no modal. |
| Synthetic data | Teams, rules, corrections, recalled memory | Synthetic badge, always. |

## Interaction Primitives

- Mouse and keyboard equally. The Reviewer may work by keyboard: in Review, `j` / `k` move between rows, `a` accepts, `e` edits, `r` rejects, `Esc` cancels. Shortcuts are listed on the Review page.
- Live data by polling, never by reload: Jobs every 2 seconds while running; Alerts, Review count and Graph from `GET /changes` (AD-10).
- Long work is a job. No page waits on a request longer than 30 seconds (AD-9); the query shows a progress state and returns in under 10 seconds.
- Banned: infinite scroll (paginate with `next`), hover-only actions, modal on modal, auto-playing audio, any celebratory animation.
- Motion: one orchestrated moment only, the network pulse. On the Home hero and on the Graph page (the same component), changed nodes and links pulse once together when the view loads or when a live job files a change, then settle. Nothing else animates. Respect `prefers-reduced-motion` by skipping the pulse.

## Accessibility Floor

- WCAG 2.2 AA. Colour contrast in `DESIGN.md` (eosin uses `{colors.eosin-text}` for text).
- Every Reviewer action is a labelled button reachable by keyboard; tab order follows reading order.
- The comparison table is the non-visual equivalent of the Graph view (architecture convention). The Graph page links to it: "View as table".
- Colour is never the only signal: change has the word "New"/"Changed", confidence has "Low confidence", node types have shapes.
- Live regions: job counts and the Review count announce politely (`aria-live="polite"`).
- Focus rings use shadcn's `ring`, visible on the slide background.

## Evidence Display Rules

Product-specific. These restate AD-6 for the screen so no WEB story invents its own.

- A value appears only with its Evidence. The quote, source name, identifier link and "data as of" date travel together.
- PubMed abstract text never appears; only the quote (at most 300 characters) does.
- Manually sourced values show the submitter, the note and "Manually sourced" instead of a quote.
- Unreviewed values are visible to everyone and labelled "Unreviewed".
- The Early research label is computed by the API (`early_research`); the screen only displays it.

## MongoDB Capability Tags

Shown on screen because the video is judged on it (NFR10). One quiet tag per panel, never more.

| Panel | Tag | Hover sentence |
|---|---|---|
| Find query box | Atlas Vector Search | "Finds Diagnostics by meaning, using embeddings MongoDB creates automatically. Synonyms mean ‘liquid biopsy’ also finds ctDNA tests." |
| Welcome-back panel | Agent Memory (or "Memory in Atlas collections" on the fallback) | "Remembers what your team searched and opened between visits." |
| Rules page | Agent Memory, procedural | "Each rule you turn on is also stored as procedural memory." |
| Graph | `$graphLookup` | "Follows links between Diagnostics, biomarkers, trials and drugs in the database." |
| Jobs and Alerts live updates | Change streams, shown only if the optional long-poll wake-up in Story 1.1 is built | "New results appear as the database changes." |

The memory tag text follows the agreed wording: "Agent Memory (public preview)" when `agent_engine` is in use, "Memory in Atlas collections" on the fallback. [NOTE FOR UX: no API field reports the live backend yet; until one exists, the web app reads it from a `NEXT_PUBLIC_MEMORY_BACKEND` variable set to match `DXP_MEMORY_BACKEND`.]

## Demo on Camera

The video is judged, so the demo surfaces are tuned for a 1440 × 900 recording [ASSUMPTION]:

- Browser zoom 110% for recording; nothing essential below the fold on Jobs, Review, Graph and Home.
- Before recording, choose the demo Team and set "your name"; the Team's `last_seen_seq` is set before the live run so the Graph and Home show changes.
- The one motion moment (graph pulse) is the visual climax; nothing else animates.

## Inspiration & Anti-patterns

- **From pathology:** the H&E palette and the idea that pink means "look here".
- **From journal reading:** quotes in serif, with the source underneath, like a citation.
- **From shadcn:** the whole component vocabulary; DxP adds only the brand layer.
- **Rejected: dark "AI dashboard" look.** It reads as generic and fights the tables.
- **Rejected: KPI cards on Home.** The home page answers "what changed for my team", not "how big is the database".
- **Rejected: a chat box as the main interface.** Plain-language query lives in Find, with its parsed result shown and editable.

## Key Flows

Protagonists: Rowan, Director of Diagnostics at a pharmaceutical therapy-area team, and Sam, the data curator who reviews proposals. [ASSUMPTION: names invented for these flows; the PRD names roles only.]

### Flow 1 — The live run (the video)

1. Sam opens Jobs and starts a live job over the held-back ClinicalTrials.gov set. The counter climbs; the Early research count ticks up.
2. Sam opens Review. Proposed changes arrive: a trial adds MET to a Diagnostic's biomarkers, with the quote from the trial record.
3. Sam rejects one change: "Cell-line study, not patients." DxP suggests a rule: "Flag findings from cell-line or animal studies." Sam turns it on; two other pending proposals now carry its flag.
4. Rowan's Team gets an Alert: a ctDNA assay they follow moved to clinical utility. The why line names their interest in EGFR. Rowan presses play and hears the briefing.
5. **Climax:** Rowan opens the Graph. The Diagnostic and its new trial link draw in with an eosin ring that pulses once; Rowan follows the link across from the plasma test to the tissue test that shares the biomarker.

Failure: a job item fails. It appears in the failures list with its source; the job continues.

### Flow 2 — Back after six weeks (UJ-1)

1. Rowan opens DxP. Home greets them with the welcome-back panel: "Last time you were comparing MRD tests for early-stage relapse monitoring. 4 changes since 2 October."
2. Rowan presses "Reopen" on the last Intended use. Find opens with the original text and its parsed chips.
3. Rowan removes the tissue-only chip, adds sample type: plasma. The table re-runs without a model call.
4. **Climax:** the table fills: one row per Diagnostic, each cell a value with its quote one click away, "No data for this indication" where nothing is published. Rowan ticks three rows, saves the Shortlist as "Relapse monitoring, stage I–III" and exports it with every reference.

Failure: memory is unavailable. The panel still shows what changed and the last Intended use, and says "Memory unavailable right now".

### Flow 3 — Clearing the Digest (UJ-3)

1. Sam opens Home for the curation Team. The Digest lists 6 pending proposals and 2 Alerts.
2. Sam works through Review by keyboard: `a`, `a`, `e` (corrects a drug name, reason "Brand name, use generic"), `r` with a reason.
3. **Climax:** the queue empties to "Nothing waiting for review", and the Record pages show the accepted values with Sam's name and today's date in their history.

### Flow 4 — Filling a Category's gaps (UJ-2)

1. A domain expert opens Categories and picks ctDNA.
2. Thin and stale Records are marked. One Record has no sample type.
3. **Climax:** they add "plasma" with a note and their name; the value appears for everyone, marked "Manually sourced".
