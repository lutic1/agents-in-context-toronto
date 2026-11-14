---
name: DxProvida (DxP)
title: DxProvida (DxP) Experience
status: final  # revised for the pivot, 13 Nov, the readiness fixes, 14 Nov (readiness-fixes-2026-11-14.md), and the Slack change, 14 Nov (sprint-change-proposal-2026-11-14-slack.md)
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
---

# DxProvida (DxP): experience spine

**Restored discovery-agent vision (14 November).** DxP is a proactive diagnostic-evidence research agent. It discovers new trials, connects them to existing evidence, remembers reviewer corrections and proposes useful follow-up work. Governance (identity, grants, policies, decisions, stop, audit) supports that loop; it is not the whole product. The entry stays under Statement 1, "Agents You Can Audit".

**Which document wins.** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md` (decisions V1 to V24) wins over every earlier planning document, this file included. Its section 7 cuts 1 to 5 are the baseline here. Its sections 10 and 11 (V25 to V37) win over V1 to V24, and V33 to V37 win over V25 to V27: the honest new-trial-signal framing (V25, V33), one evidence gap per report answered by the task (V26, V33), approved is not accepted for the task (V27), the hard core cut line (V28), media on demand (V29), one float figure (V30, V36), L1 and L2 as risks (V31), the longitudinal narrative (V32), no unverified alias (V34), the allowed update to the scope's evidence collection and the blocked link of the "FoundationOne CDx" mention (V35, V37), the anchor verified live at 10:45 (V36), and a name in a record is a mention, never proof of use (V37). Its section 12 (V38 to V44, approved by Luis (14 Nov)) wins over V1 to V37: approval continues the work automatically, with no start button (V38); task execution is stretch and is never narrated unless it ran (V39); evidence pins the exact source version it used (V40); the report's script is core (V41); a capped search reads "No matching results found among the records searched" (V42); a report with no resolved Diagnostic works end to end (V43); and the rehearsal source check (V44). V48 (approved by Luis (14 Nov)) wins over V1 to V47 where they differ: the rollback story in the pitch, revert an approval (Story 10.13, `revert` flag) and live run updates through change streams with an honest source label (Story 9.12, `live_stream` flag). The readiness fixes (D1 to D57) and the Slack decisions (S1 to S13) still apply wherever V1 to V24 do not replace them. On API routes, shapes, action kinds and status values the architecture spine wins; on page routes, PRs and times `development-plan.md` wins.

**Slack is the external system.** One alert per report goes to `#all-mango-db-hackathon` through an incoming webhook (S1 to S13, V11). The alert only notifies: its body is the report headline, the relationship summary and "Approve or reject in DxP", with a "Review in DxP" link to the report page and, only when the report names a resolved in-scope Diagnostic, an "Open diagnostic" link to the Accepted knowledge view. On the demo path the update targets the scope's evidence collection, so only "Review in DxP" is sent (V43). Approval and rejection happen only in DxP.

## What to build from

There are no mockups. The hackathon rules allow only work built during the event to be shown, so every screen is built on Saturday, from 10:45, from this file and `DESIGN.md`:

| Surface | Build from | Story |
|---|---|---|
| Run console | This file's Run console sections, with `DESIGN.md` tokens | 9.7 |
| Report page and its memories panel | This file's Report page sections. Two builders (cut 5): the report body; the decisions bar plus the memories panel | 10.10 |
| Pending reports list | This file, small scope | 10.10 (narrowed 2.4) |
| Accepted knowledge view | This file, narrowed Record page | 1.3 (narrowed) |
| Audit view | This file's Audit view sections | 9.8, with the V14 additions |
| Ten-second briefing player | This file, behind the `briefing` flag, generated on demand with "Generate briefing" (V29), PR B06 (supporting; fourth in the V48 cut order) | 10.11 |
| Avatar video player | This file, behind the `avatar` flag, rendered on demand with "Render avatar" (V29), PR B08 (supporting; first in the cut order) | 10.12 |
| Revert approval control | This file, behind the `revert` flag, in B04's decisions area (supporting; second in the V48 cut order; backend A26) | 10.13 |
| Live source label | This file, behind the `live_stream` flag, in B02 and B03 (supporting; third in the V48 cut order; backend A27) | 9.12 |

## Foundation

- **The discovery agent is the product.** The screens let a reviewer inspect the agent's research and its decisions: what it found, what it related the finding to, which memories it used and what they changed, what was blocked, what it proposes, and who authorised each action. The hackathon bans "a dashboard as the main feature", so no screen is pitched or demoed as the product, and no screen is built as a dashboard.
- **No medical advice.** DxP supports research review about diagnostic tests for pharma teams. It never tells anyone how to treat, test or manage a patient. The recommended task is always a research task, and no copy, briefing or report reads as a recommendation for patient care.
- **Pending is never accepted.** A report and its proposed knowledge updates stay pending until Sam approves them in DxP. Pending and accepted are labelled differently everywhere (see Component Patterns), and the Accepted knowledge view never shows a pending item as accepted.
- **Similarity is not evidence.** A similarity score says only that two documents are near each other. A relationship label (supports, contradicts, extends, new question) needs two checked quotes, one from each side. The screen shows the score with the words "similarity, not evidence".
- **Memories inform; they never permit.** A memory can change the agent's wording or label. It never changes a grant or a policy, and the screens never present it as a rule.
- One responsive web app, desktop first, built on Next.js 16 App Router with shadcn/ui and Tailwind. `DESIGN.md` is the visual identity; this file is the behaviour.
- The web app reads and writes only through the API (AD-9, AD-14). It applies no display rule of its own: what the read model returns is what the screen shows (AD-6).
- **Authority is never set in the browser.** The actor is resolved server-side from the API key, and the grant defines the Team and the research scope. There is no Team picker and no "your name" picker that confers anything. The top bar shows, read-only, who the API resolved the caller as, from `GET /whoami`.
- **Display formats.** Grants show as `{grant_id}@v{version}` (for example `lbdx@v1`, `task-<hex>@v1`). Policy sets show as `ps_ab12… (N policies)`. Run, action, report, memory and task IDs show in their own forms (`run_…`, `act_…`, report IDs, `M1`, task IDs). Identifiers are in mono and copyable.
- **Screens poll unless the live stream works, and always say which.** The `/changes` feed is cut (proposal section 7, cut 3). Since V48 the Run console and the Audit view read the run's change stream when the `live_stream` flag is on and the stream works, and otherwise poll every 2 seconds. The label tells the truth: "Live (change stream)" or "Refreshing every 2 s". Every other live surface polls.
- Everything is built and validated on the Atlas Sandbox. The demo shows only work built on 14 November.
- Fonts load through `next/font/google`: Atkinson Hyperlegible Next, Atkinson Hyperlegible Mono, Source Serif 4. [ASSUMPTION: if a family is missing from `next/font/google`, fall back to Atkinson Hyperlegible.]
- This file adds no stories of its own.

## Information Architecture

### Surfaces

| Surface | Route | Reached from | Purpose | Stories |
|---|---|---|---|---|
| Run console | `/runs`, `/runs/[run_id]` | Top bar; app open (`/` redirects to the latest run) | Start a discovery scan for the research scope by choosing a grant labelled with its Team and scope ("`lbdx@v1`, Team Liquid Biopsy Dx (Synthetic), Plasma ctDNA genotyping assays in NSCLC"). The run scans the scope the grant names (V1, V2). Shows the identity card, the scan cursor, the action feed (live from the change stream when the `live_stream` flag is on and it works, otherwise by polling, with the source label, V48), the stop control, and a link to each report the run filed. A follow-up task's run opens here too, labelled "Follow-up task" with a link back to its report | 9.7, 10.1, 10.9 |
| Report page | `/reports/[report_id]` | The Slack alert's "Review in DxP" link; the pending reports list; the Run console; the Audit view | The pending research report, read top to bottom: the discovery headline and its quotes; related evidence with relationship labels and similarity; uncertainties; the evidence gap; memories used with their before and after effect; proposed updates, marked pending; the recommended task that answers the gap, with its state in words and no start button: after approval it starts by itself when task execution is on (V38), otherwise it reads "Follow-up task authorised; not run"; the report's script, always shown as text (V41); the ten-second briefing player (behind the `briefing` flag) and, next to it, the avatar video player (behind the `avatar` flag), both from the same grounded script, made only on demand ("Generate briefing", "Render avatar"), with the script always shown as text; the decisions bar (Approve, Reject, Approve with correction). The memories panel sits in the right-hand column, with Correct and Revoke on each memory. After a decision the page stays readable and shows the decision, the accepted update and the task's state, in words: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27) when the task was queued, or "Approved: 1 update accepted. Follow-up task authorised; not run." when it was not (V38). On an accepted report, behind the `revert` flag, "Revert approval" with a confirm step and a required note (V48) | 10.4, 10.10, 10.11, 10.12, 10.13 |
| Pending reports list | `/reports` | Top bar ("Reports" with the pending count) | A small table: headline, trial (NCT ID), run, Slack alert state, filed time, status badge. Pending first, newest first; decided reports below under "Decided". Each row opens the report page. No bulk actions, no filters | 10.10 (narrows 2.4) |
| Accepted knowledge view | `/diagnostics/[dx_id]` | The Slack alert's "Open diagnostic" link, when sent; links from the report page and the Audit view, only when the report names a Diagnostic (a scope-collection update shows its accepted state on the report page, V43) (there is no Diagnostics list) | One Diagnostic's accepted knowledge only: accepted values with their Evidence, accepted trials, accepted findings, each linked to the report and decision that accepted it. A notice lists any pending report that would change this Diagnostic ("1 pending report would add a trial. Open report"); its content is never mixed into the accepted values | 1.3 (narrowed) |
| Audit view | `/runs/[run_id]/audit` | Run console, any action row, the report page, top bar | One run reconstructed in order: sources fetched with the scan cursor; retrieval (method, top-k, scores); memories used, with author and effect; relationship labels with both quotes; every decision allowed or blocked, including the team-scope block on the record's "FoundationOne CDx" mention and, when the first draft wrote it, a blocked unsupported claim with its failed claim check; the Slack result; then "After the run": the report decision in the V27 words, the task authorisation, memory changes, any revert of the approval beside the original approval (V48), and a link to the follow-up task's own run and audit, whose findings show "Pending review". The same source label as the Run console | 9.8, 9.12, 10.9, 10.13, V14 |

Page files follow `development-plan.md`: `web/app/runs/` (B02), `web/app/runs/[run_id]/audit/` (B03), `web/app/reports/` and `web/app/reports/[report_id]/` (B04, two builders), `web/app/diagnostics/[dx_id]/` (B04), the briefing player inside the report page (B06, behind the `briefing` flag), and the avatar video player beside it (B08, behind the `avatar` flag).

Top bar, left to right: the "DxP" text wordmark (typed, built during the event; the prepared logo images in `imports/` are not used unless an organiser clears them in writing), Run console, Reports (pending count), Audit; then the read-only "Signed in as" chip. Footer: the credits line. The top bar, tokens and badges are built once in the minimal shell (PR B01).

Dialogs stack one level deep. The right-hand panel (360px) holds the memories panel on the report page, and opens Evidence and the "Who authorised this?" answer elsewhere without leaving the page.

### Cut or narrowed (discovery-agent change, 14 Nov)

| Surface or feature | Status |
|---|---|
| Live change-stream feed (9.9, A12) | **Cut** as `/changes`. **Restored in part (V48):** the Run console and the Audit view read a per-run change stream when `live_stream` is on (9.12, A27), and poll otherwise, labelled |
| Separate impact graph view, `/runs/[run_id]/impact` (5.1, 5.2, A15, B05) | **Cut.** The report's related-evidence list is the relationship view |
| Learned-rule drafts (9.11, A17) | **Cut.** Policies stay hand-written. Memories are not rules |
| Review list (2.4) | **Narrowed** to the pending reports list, `/reports` |
| Record page (1.3) | **Narrowed** to the Accepted knowledge view of one Diagnostic |
| Old audio briefing page reached from the Audit view (9.10) | **Replaced** by the briefing player inside the report page (10.11) |
| `/review?proposal=<p_id>` focus | **Replaced** by `/reports/[report_id]`, the Slack alert's target |

### Still deferred

Home dashboard (`/`), Diagnostics list, Find, Categories, Rules, Team Alerts, Jobs, Terms, Tavily scans, scheduled scans, PubMed, Agent Memory preview, Learned-rule enforcement and quick capture (V18).

## Voice and Tone

DxP speaks plainly to a scientist or reviewer in a hurry. It names things the way the PRD Glossary does (Diagnostic, Evidence, Team, Lifecycle stage, Early research) and adds: research scope, discovery, report, related evidence, relationship, memory, accepted knowledge, follow-up task; and for governance: run, agent, grant, policy set, action, audit.

| Do | Don't |
|---|---|
| "Found NCT04712877, updated 12 Nov 2026. New trial signal worth investigating." | "New insight!", "Breakthrough detected" |
| "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." | "Trial shows FoundationOne Liquid CDx works in early-stage lung cancer", "Trial uses FoundationOne Liquid CDx" |
| "Named in the record: 'FoundationOne CDx', 'FoundationOne Liquid' (other names of 'ctDNA, tumor NGS')." | "The trial uses FoundationOne CDx", "The trial studies FoundationOne Liquid CDx" |
| "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample." | Hiding the ambiguity, or merging FoundationOne CDx with FoundationOne Liquid CDx |
| "The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated." | Mapping "FoundationOne Liquid" to FoundationOne Liquid CDx |
| "Evidence gap: Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?" | "Next steps", "Opportunities" |
| "Extends: the prior trials study plasma ctDNA genotyping in advanced NSCLC; this one profiles blood and tissue in early-stage disease." with both quotes | "Strong match", "Highly relevant" |
| "Similarity 0.82 (similarity, not evidence)" | "82% match", "Confidence 0.82" |
| "Related by text search (Vector Search unavailable). Score 7.4 (text score, not evidence)" | "Vector Search" when it was text search, or hiding the fallback |
| "Related (no relationship established): fewer than two checked quotes." | "Unclear", "N/A" |
| "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet." with before and after | "AI learned from feedback", "Smart correction applied" |
| "Claim blocked before filing: 'showed' needs reported results. The source is RECRUITING and has no posted results." | "Hallucination prevented", "Error in draft" |
| "Redrafted: 'is recruiting; no results posted yet'. Allowed." | "Fixed!" |
| "Pending review" on a report or an update not yet accepted | "Draft", "Saved", "Live" |
| "Accepted by Sam at 15:42" | "Approved!", "Done!" |
| "Approve", "Reject", "Approve with correction"; toasts "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review.", "Rejected. Memory M2 created.", "Approved with correction. Memory M2 created." | "Submit", "Confirm action" |
| "Correct memory", "Revoke memory"; toasts "M1 corrected (now version 2)", "M1 revoked. It will not be used again." | "Delete", "Forget" |
| "Memories inform the agent's wording. They never change permissions." | "Rules learned", "Policy updated by memory" |
| "Recommended task: search ClinicalTrials.gov for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling, and report which have posted results (at most 5)." | "Next best action for patients", "Recommended for patients with…" |
| "Task done. No matching results found among the records searched. Query: {query}; {n} records searched; limit 5." (V42) | "Task found nothing", "No data", any wording that says no qualifying study exists |
| "Follow-up task authorised; its findings will be pending review." (task queued); "Follow-up task authorised; not run." (task not run, V38) | "Task results accepted", "Approved: task complete", any claim of completed follow-up work when the task did not run (V39) |
| "Task authorised by Sam at 15:42. Runs under grant `task-<hex>@v1`, expires 16:42." | "Task started automatically" |
| "Task blocked before it ran: limit of 5 reached under policy set `ps_ab12…` (N policies)." | "Task failed", "Limit error" |
| "Task done. 3 related items filed (pending review)." | "Task complete! 3 new results" |
| "Generate briefing" and "Render avatar" (buttons; nothing is made automatically) | "Auto-generating your summary…" |
| "Briefing, 10 seconds. Built only from this report's evidence fields." | "Listen to the AI summary" |
| "Briefing unavailable. The script is shown above." | "Audio error" |
| "Avatar video, about 20 seconds. Same script as the briefing, built only from this report's evidence fields." | "Meet your AI analyst", "Watch the AI explain" |
| "Rendering avatar video. The report is ready to review now." | "Loading…", "Please wait for the video" |
| "Avatar unavailable. The script is shown above; the report is unaffected." | "Video failed", "HeyGen error" |
| "Blocked before it ran: Diagnostic in team scope failed under policy set `ps_ab12…` (4 policies)" | "Action denied", "403" |
| "Slack alert delivered at 15:04 to #all-mango-db-hackathon" | "Sent!", "Message posted successfully" |
| "Result unknown. Slack didn't confirm. Check #all-mango-db-hackathon for `act_7f3c…`, then resolve." | "Something went wrong", "Retrying…" |
| "Approve or reject in DxP. Slack only notifies." | "Approve in Slack" |
| "Revert approval"; confirm "Revert this approval? The update leaves accepted knowledge. Nothing is deleted, and the Slack alert already sent stays sent."; then "Approval reverted by Sam at {time}: 1 update removed from accepted knowledge." (V48) | "Undo", "Rollback complete", "Changes rolled back everywhere", "Slack message recalled" |
| "Follow-up task cancelled; its grant expired." / "Follow-up task stop requested." / "Follow-up task had finished; its findings stay pending review." | "Task deleted", "Task undone" |
| "Live (change stream)" or "Refreshing every 2 s" above the feed (V48) | "Live" while polling; "Real-time" with no source |
| "The agent cannot change accepted knowledge without a human approval." (V48) | "The agent can roll back anything it did", "Everything is reversible" |
| "Report not found. Open Reports to see what is pending." | "404", "Invalid link" |
| "Started by Sam (Synthetic)"; "Team Liquid Biopsy Dx (Synthetic)" | "User: sam" |
| "Stopping: 2 in flight. No new actions will start." then "Stopped at 15:12. 3 took effect, 1 blocked, 0 unknown." | "Please wait…", "Run cancelled" |
| "Couldn't reach the API. Retrying in 5 seconds." | "Oops! Something went wrong." |
| Evidence about a record: "Trial NCT04712877 names 'FoundationOne CDx' in its intervention's other names" | Patient advice: "Use this test to decide treatment"; proof-of-use language: "the trial uses FoundationOne CDx" |

The five checks always appear under these names: **Grant active**, **Diagnostic in team scope**, **Destination and action match the grant**, **Evidence checks passed**, **Run still authorised**. **Evidence checks passed** now includes the claim checks (V7), shown by name under it: **Performed or results only if reported** (`claim_performed_or_results`), **Planned or recruiting described as such** (`claim_planned`), **Cell-line or animal labelled preclinical** (`claim_preclinical`). For a follow-up task, **Run still authorised** also covers the task authorisation, the scope and the limit. For Reviewer decisions, **Evidence checks passed** reads "Not applicable".

Action kinds always appear under these names: **Search source** (`search_source`), **File report** (the pending report and its proposals; the report-level `file_proposal` kind, since there is no `file_report` kind, V24), **Send Slack alert** (`notify_slack`), **File related evidence** (`file_related_evidence`), and for the Reviewer: **Generate briefing** (`generate_briefing`) and **Generate avatar video** (`generate_avatar_video`), both on demand from the report page (V29), **Decide report** (`decide_report`), **Revert approval** (`revert_report`, V48), **Authorise task** (`authorise_task`), **Create memory** (`create_memory`), **Correct memory** (`correct_memory`), **Revoke memory** (`revoke_memory`), **Resolve Slack alert** (`resolve_notification`).

## Component Patterns

Behavioural. Visual specs live in `DESIGN.md` Components.

### Discovery and report

| Component | Where | Behaviour |
|---|---|---|
| Discovery header | Report page (top) | The trial (NCT ID, mono, linking to ClinicalTrials.gov), its title, status word from the source (for example "Recruiting"), "updated {date}", the "New" changed mark, the report status badge (Pending review, Accepted or Rejected), the run that found it and the scope. Then the headline, framed as a new trial signal worth investigating, never as performance (V33), and the intervention wording verbatim, with any assay names labelled "Named in the record" (V37). Below: the supporting quotes as Evidence quotes. |
| Relationship label | Report page related evidence; Audit view; Slack relationship summary (words only) | One of five, always icon plus words: **Supports**, **Contradicts**, **Extends**, **New question**, or **Related (no relationship established)**. The first four need a rationale with two checked quotes, one from the new evidence and one from the related item, shown side by side under the label. Without two checked quotes the item shows only "Related (no relationship established)" and its similarity. Contradicts is a finding, not an error: it is never styled as one. |
| Related evidence item | Report page | The related document (NCT ID or earlier finding, linked), the relationship label, the two quotes, and the similarity score with "similarity, not evidence". Ordered by relationship first (supports, contradicts, extends, new question, then related), then by similarity. When retrieval fell back to text search, the panel heading carries "Related by text search" and each score reads "text score, not evidence". |
| Uncertainties | Report page | A plain list of what the agent cannot say, from the report's fields, for example "Recruiting: no results posted yet", "Status may change before the trial reports", the intervention ambiguity (V37) and any unresolved name (V34), in the exact wording of Voice and Tone. Empty: "No uncertainties recorded." |
| Evidence gap | Report page, after the uncertainties | One question the evidence does not yet answer, headed "Evidence gap", for example "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?" The recommended task below answers it (V26). |
| Memory used chip | Report page (inside the discovery and related evidence, where it applied); memories panel; Audit view | Memory ID (`M1`), author with Synthetic badge ("Sam (Synthetic)"), date, status, and its effect: "Wording changed because of M1 (Sam, 14 Nov)", then **Before** (the text the agent would have written) and **After** (the text it wrote). Before comes from the first draft (written without memories) and After from the second (written with them), both real gated drafts (V21). Selecting the chip opens the memory in the memories panel. A memory that was retrieved but changed nothing visible is listed as "Retrieved, no change". |
| Memories panel | Report page, right-hand column | Every memory retrieved for this report, each with text, author, source (the decision and report that created it, linked), tags (the claim kind it is about and the assay it was written on), status and version. A caption explains the match: "Retrieved for the same kind of claim; the assay need not match" (memories are matched by Team, active status and claim kind, never by assay, V22). **Correct** opens an inline form: the new text and a required note; "Save correction" creates a new version that supersedes the old one. **Revoke** opens an inline form with a required note; "Revoke memory" marks it revoked. Both are gated and audited, sit behind the `memory_edit` flag, and show only when the signed-in principal's `actions` include `correct_memory` or `revoke_memory`. The panel footer reads "Memories inform the agent's wording. They never change permissions." Correcting or revoking does not rewrite this report; it affects the next relevant discovery. |
| Proposed updates | Report page | Each update as a sentence ("Add trial NCT04712877 to the scope's evidence collection, as an early-stage plasma-plus-tissue profiling study"; no assay record changes, V35) with its quote and the **Pending review** badge. After approval each shows **Accepted**; an update that targets a Diagnostic links to the Accepted knowledge view, and a scope-collection update (no Diagnostic, V43) shows "Accepted into the scope's evidence collection" in place, with no link. Quotes show the source version they came from ("as of {date}", V40). |
| Recommended task | Report page | One research task as a sentence that answers the evidence gap, with its limits in plain words: scope, maximum results, grant it will run under, expiry ("Runs under its own grant after approval: search and file related evidence only, same scope, max 5, expires one hour after approval"). Shows the task state badge (see State Patterns). There is no start button (V38): when task execution is on, approval queues the task and it starts by itself as its own run (Story 10.9); when it is off the task reads "Follow-up task authorised; not run". Once its run starts it links to the task's run. |
| Decisions bar | Report page, below the recommended task; sticky at the bottom of the main column while the report is pending | Three buttons: **Approve** (primary), **Approve with correction** (secondary), **Reject** (outline). Approve asks for nothing more. Approve with correction opens an inline note (required): "What should the agent do differently next time?". Reject opens an inline required reason with the same prompt. Both forms also ask "What kind of claim is this about?" with a short choice of claim kinds (for example "Outcome stated without posted results", `outcome_claim_without_results`); the choice becomes the memory's claim-kind tag, which is how it is retrieved later (V22). Shown only when the signed-in principal's `actions` include `decide_report`. Approve promotes the proposed updates to accepted knowledge and authorises the recommended task. Approve with correction does the same and also creates a memory from the note. Reject promotes nothing and creates a memory from the reason. [ASSUMPTION: V8's line "Reject or correct creates the memory. No promotion happens" is read as "no promotion on reject"; section 2 of the proposal says approval with a correction still approves.] After a decision the bar is replaced by the decision line: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." with "Accepted by Sam at 15:42" (V27), or "Rejected by Sam at 15:42", with the memory created, if any. |
| Briefing player | Report page, under the discovery header; only when the `briefing` flag is on | The script always visible as text, so it can be checked against the report, then a "Generate briefing" button (V29: nothing is generated automatically); once generated, a play button labelled "Play briefing (10 s)" and the elapsed time. If ElevenLabs fails, it says "Briefing unavailable" and the script stays. Never autoplays. The caption reads "Built only from this report's evidence fields." The report, the decision and the task never wait on it. |
| Avatar video player | Report page, next to the briefing player (side by side; stacked below it at narrow widths); only when the `avatar` flag is on | A HeyGen avatar video (about 20 seconds) explaining the finding from the same grounded script as the briefing (V13), so the transcript shown under the briefing is its transcript too. Nothing renders automatically: a "Render avatar" button requests it (V29); for the demo, one render is requested for the demo report only, as soon as it is filed. The render is asynchronous; the page polls until it is ready. States: **Not rendered**, **Rendering**, **Ready**, **Avatar unavailable** (see State Patterns). The report, the briefing and the decisions never wait on it. Never autoplays; captions on. Caption: "Same script as the briefing, built only from this report's evidence fields." |
| Revert approval | Report page, in place of the decisions bar once the report is Accepted; only when the `revert` flag is on and the signed-in principal's `actions` include `revert_report` (V48) | A secondary "Revert approval" button beside the decision line. Pressing it opens an inline confirm step (no modal): "Revert this approval? The update leaves accepted knowledge. Nothing is deleted, and the Slack alert already sent stays sent.", a required note ("Why revert this approval?") and "Revert approval" / "Cancel". On success the decision line reads "Approval reverted by Sam at {time}: 1 update removed from accepted knowledge.", the proposed update and the accepted relationships show **Reverted**, and the task line reads one of: "Follow-up task cancelled; its grant expired." (it had not started), "Follow-up task stop requested." (it was running), "Follow-up task had finished; its findings stay pending review.". A blocked revert shows "Revert blocked: {check} failed" with the Decision linked, and nothing changes. Pressing it again on a reverted report shows the same state. The original approval stays visible in the Audit view. |
| Accepted knowledge panel | Accepted knowledge view | The Diagnostic's accepted values, trials and findings with Evidence and the **Accepted** badge, each linking to the report and decision that accepted it. A separate notice above lists pending reports affecting this Diagnostic, with links; pending content is never shown inline. |

### Run, gate and audit

| Component | Where | Behaviour |
|---|---|---|
| Identity card | Run console (top), Audit view (top) | Two identities, never merged. **Agent:** the executing agent named by the grant (name and model). **Started by:** the principal resolved from the caller's key ("Started by Sam"). Also the run ID, prompt version, the grant (`{grant_id}@v{version}` with its Team, scope, allowed actions and expiry), the policy set (`ps_ab12… (N policies)`), the scan cursor ("Scanning trials updated since {date}") and the run status. A follow-up task run shows "Follow-up task for report {report_id}", "Authorised by Sam at {time}" and the task grant `task-<hex>@v1` with its limit. Nothing is editable; identifiers are copyable. |
| Action row | Run console feed, Audit view | One row per gate decision: state icon and word, action kind, subject (trial, Diagnostic, report or destination), time. States as before: **blocked**, **allowed** (queued), **dispatching**, then the settled state. A "File report" row settles as **"Report filed (pending review)"** with a link to the report page. A blocked claim shows as **Claim blocked** (see State Patterns). A "Send Slack alert" row settles as delivered, failed, unknown or reconciling, unchanged from the Slack decisions (S1 to S13), with **Resolve** on an unknown alert for a principal whose `actions` include `resolve_notification`. Rows update in place and never jump. Enter opens the entry in the Audit view. |
| Stop control | Run console identity card | "Stop run" while running. One press, no confirmation: new admissions stop at once; the card reads "Stopping: {n} in flight", then "Stopped" with totals (D7, D22 to D24). Works the same on a follow-up task run. A stopped run is not restarted from here. |
| Run feed status | Run console and Audit view, above the feed (V48) | One of two labels, always true to the source: "Live (change stream)" while the run's change stream is open, or "Refreshing every 2 s" while polling (flag `live_stream` off, the stream failed, or A27 is not built). It switches to "Refreshing every 2 s" the moment the stream errors, and back after a successful reconnect. Carries the matching capability tag. |
| Audit entry | Audit view | One entry per gate decision, in order, loaded from `GET /decisions/<decision_id>`: timestamps, inputs, Evidence quote, destination, every check with result and detail (claim checks named under **Evidence checks passed**), the grant evaluated, the policy set and the outcome. A "Search source" entry adds the query, the cursor and the sources fetched. A "File report" entry adds the retrieval used (method "Atlas Vector Search" or "Text search", top-k, each score labelled "similarity, not evidence"), the memories used with author and before and after effect, and the relationship labels with both quotes. A blocked claim entry shows the draft sentence, the failed claim check and the source fields that failed it (status, `has_results`), then "Nothing filed. No external call made." and a link to the redraft's own entry. A "Send Slack alert" entry shows the HTTP status, Slack's response and the two link URLs; never the webhook URL. "Who authorised this?" opens the answer in the right-hand panel. |
| After the run | Audit view, below the run's entries | The Reviewer decisions caused by this run, each "Decided by Sam (Synthetic)" with no agent: the report decision, the task authorisation, any memory created, corrected or revoked, any Slack alert resolved. The task authorisation links to the follow-up task's run and its audit ("Follow-up task run `run_…`: 2 allowed, 1 blocked. Open audit"). Empty: "No Reviewer decisions yet." |
| Capability tag | See MongoDB Capability Tags | Static. Hover or focus shows one sentence on what the capability does here. |
| Evidence quote | Report page, Accepted knowledge view, Audit entry | Always shows source, identifier link and "data as of". Never a value or a relationship without it. |
| Stage track | Accepted knowledge view header | Read-only, as before. |

### Cut or deferred

Do not build on Saturday: Learned-rule draft panel, Rule switch, impact graph and its nodes, the old `/changes` feed indicator (the V48 source label replaces it), Alert item, Parsed-query chips, Comparison table, Welcome-back panel, Capture box, value-level Accept / Edit / Reject on the Accepted knowledge view.

## State Patterns

### Relationship labels

| State | Treatment |
|---|---|
| Supports | Supports mark (icon and "Supports") and two checked quotes side by side |
| Contradicts | Contradicts mark (icon and "Contradicts") and two checked quotes. Neutral styling, never the error style |
| Extends | Extends mark (icon and "Extends") and two checked quotes |
| New question | New question mark (icon and "New question") and two checked quotes, plus the question in one sentence |
| Related (no relationship established) | Muted mark and "Related (no relationship established)", the similarity, and the reason: "Fewer than two checked quotes." No quotes shown as if they argued anything |
| Related by text search | Panel heading note: "Related by text search (Vector Search unavailable)". Each score reads "text score, not evidence". Labels behave the same |

### Memory statuses

| State | Treatment |
|---|---|
| Active | Memory icon and "Active", version shown ("v1"). Can be used in retrieval; Correct and Revoke available to a permitted principal |
| Corrected | "Corrected" and "Replaced by M1 v2" (linked). The old version stays readable in the audit; it is no longer retrieved |
| Revoked | "Revoked by Sam at {time}" with the note; text shown struck through with the word "Revoked", so it never relies on the strike alone. Never retrieved again. A report that used it before revocation still shows it, with the Revoked status |

### Pending and accepted

| State | Treatment |
|---|---|
| Pending review | Pending badge (`clock` and "Pending review") on a report, a proposed update or filed related evidence |
| Accepted | Accepted badge (`circle-check` and "Accepted"), plus "Accepted by Sam at {time}" where the decision is shown |
| Rejected | Rejected badge (`circle-x` and "Rejected"), plus the reason and "Memory {id} created" |
| Reverted (V48) | Reverted badge (`undo-2` and "Reverted") on the report, its update and its relationships, plus "Approval reverted by Sam at {time}" and the note. The original "Accepted by Sam at {time}" stays readable beneath it; nothing is struck out of the history |
| Report not found | "Report not found. Open Reports to see what is pending." as an inline notice on `/reports/[report_id]`, with a link. No error toast |

### Claim blocked

| State | Surface | Treatment |
|---|---|---|
| Claim blocked | Action row, Audit entry, report page "How this report was drafted" note | Blocked mark (icon and "Claim blocked") and "Claim blocked before filing: '{word}' needs {requirement}. The source is {status} and {has_results}." The failed claim check is named. In the Audit entry: the draft sentence, the check, the source fields, "Nothing filed. No external call made." The redraft follows as its own allowed entry. On the report page a one-line note links to it: "1 draft claim was blocked before filing. See the audit." |
| Blocked (other checks) | Action row, Audit entry | "Blocked before it ran: {check} failed under policy set `ps_ab12…` (N policies)." Unchanged, for example the FoundationOne CDx (tissue) team-scope block |

### Follow-up task

| State | Treatment |
|---|---|
| Recommended (before decision) | "Recommended. Runs only if approved." Faded |
| Authorised (not run) | Task execution off (V38, V39): "Authorised by Sam at {time}" with the task grant and expiry, and "Follow-up task authorised; not run". No button |
| Not authorised | The task authorisation was blocked, at approval or when an interrupted approval was completed at restart (V45): the evidence stays accepted, and the report reads "Approved: 1 update accepted. Follow-up task not authorised: {reason}." with the blocked Decision linked. No task and no button |
| Queued | Task execution on: "Authorised by Sam at {time}. Queued: starts by itself when the current run ends." with the task grant and expiry, and "Its findings will be pending review." (V27, V38). No button |
| Running | "Running" with the count so far ("2 of max 5 filed") and a link to the task run. No spinner beyond what the API reports |
| Blocked | "Blocked before it ran: {check} failed" (for example limit reached, or out of scope), with a link to the blocked Decision |
| Done | "Done. {n} related items filed (pending review)." or, when none qualify, "Done. No matching results found among the records searched." (a valid answer, V42). Always followed by "Query: {query}. {n} records searched; limit {limit}." |
| Failed | "Failed: the task's run was abandoned. Not restarted." (V38) |
| Stopped | "Stopped at {time}. {a} took effect, {b} blocked." |
| Not authorised (report rejected) | "Not run: the report was rejected." |
| Cancelled (V48) | "Cancelled: the approval was reverted by Sam at {time}. Its grant expired." No button |

### Briefing player

| State | Treatment |
|---|---|
| Hidden | Flag off: nothing renders |
| Not generated | The transcript visible and a "Generate briefing" button (V29) |
| Generating | "Preparing briefing" with the transcript already visible |
| Ready | "Play briefing (10 s)" |
| Playing | "Pause" and the elapsed time; the transcript stays visible |
| Unavailable | No ElevenLabs key, or ElevenLabs failed: "Briefing unavailable. The script is shown above." The transcript stays |

### Avatar video player

| State | Treatment |
|---|---|
| Hidden | Flag off: nothing renders |
| Not rendered | A "Render avatar" button; the shared transcript is visible (V29) |
| Rendering | A still placeholder with "Rendering avatar video. The report is ready to review now." No progress bar or percentage, because HeyGen reports none; the page polls. The rest of the report is fully usable |
| Ready | A poster frame with "Play avatar video (about 20 s)"; captions on; never autoplays |
| Playing | Standard video controls, captions on; the shared transcript stays visible under the briefing |
| Avatar unavailable | "Avatar unavailable. The script is shown above; the report is unaffected." Shown when there is no HeyGen key, the render failed or it did not finish in time. No retry button on camera; the loop continues |

### Run, Slack and general

| State | Treatment |
|---|---|
| Slack alert delivered, Failed, Unknown, Reconciling, Failed never sent | Unchanged from the Slack decisions (S1 to S13). The proposal or report stays pending until Sam decides it in DxP |
| Report filed (pending review) | "Report filed (pending review)", then its Slack alert's state, and a link to the report page |
| Stopping, Stopped | Unchanged (D7, D22 to D24) |
| Scan found nothing | "Scan finished. No trials in scope updated since {cursor}." The cursor advances |
| Empty run | "No actions yet. The agent is scanning ClinicalTrials.gov for the scope." |
| No runs | "No runs yet. Start a scan for the research scope." with the Start run button |
| Empty pending reports | "No reports waiting. The agent files one when a scan finds something in scope." |
| Loading | shadcn `Skeleton` rows shaped like the final layout |
| API unreachable | One toast: "Couldn't reach the API. Retrying in 5 seconds." |
| Synthetic data | Synthetic badge on every synthetic Team, person, correction and memory author |
| Field with no value | "No data for this indication" |
| No stage evidence | Empty stage track and "Stage not determined" |

## Interaction Primitives

- Mouse and keyboard equally. On the report page, `a` approves, `c` opens Approve with correction, `r` opens Reject, `Esc` cancels; `j` / `k` move between related evidence items. In the Run console and Audit view, `j` / `k` move between rows and Enter opens one. Shortcuts are listed on each page.
- **Live data.** The Run console and Audit view read the run's change stream through `GET /runs/<id>/stream` when `live_stream` is on (V48), and otherwise poll `GET /runs/<id>` and `GET /runs/<id>/audit` every 2 seconds, saying which; a dropped stream reconnects and resumes without repeating a row. The report page polls the report while its task runs; the Reports count polls pending reports. No reload needed.
- Long work is a run. No page waits on a request longer than 30 seconds (AD-9).
- Banned: infinite scroll, hover-only actions, modal on modal, auto-playing audio, celebratory animation, and spinners that suggest work the API has not reported.
- **Motion: one moment only.** A new action row fades and slides 8px into place once (about 200ms). Nothing else animates. Respect `prefers-reduced-motion`.

## Accessibility Floor

- WCAG 2.2 AA. Colour contrast in `DESIGN.md`.
- Every action (Start run, Stop run, Approve, Reject, Approve with correction, Revert approval, Correct, Revoke, Play briefing, Play avatar video, Resolve, "Who authorised this?") is a labelled button reachable by keyboard; tab order follows reading order.
- The live source label is text, not only an icon, and a change between "Live (change stream)" and "Refreshing every 2 s" is announced politely (V48).
- Colour is never the only signal: every relationship label, memory status, pending, accepted and rejected badge, task state, claim block and action state carries an icon and words.
- The briefing transcript is always on screen, so the briefing and the avatar video have a text equivalent. The avatar video has captions on by default. Neither autoplays.
- Before and after text in a memory effect is labelled "Before" and "After" in words, not only by strike or colour.
- Live regions: run status, task status and the Reports count announce politely. The feed announces only blocked, claim blocked, failed and unknown rows.
- Inline forms (correction, reject, correct memory, revoke memory, resolve) are labelled; focus moves into the form when it opens and back to its button when it closes.
- The Audit view is a full text equivalent of the run, including the follow-up task's link.

## Evidence Display Rules

- A value, a claim or a relationship appears only with its Evidence. Quote, source name, identifier link and "data as of" travel together.
- A relationship label needs two checked quotes, one from each side (AD-6). Similarity never stands in for a quote and is always labelled "similarity, not evidence".
- PubMed abstract text never appears (PubMed is deferred in any case).
- The status a report states comes from the source's own fields: a recruiting trial is described as recruiting, with no results claimed unless `has_results` is true.
- Pending content and accepted knowledge are never mixed on one list.
- Every item an agent action created links to that action's Audit entry.

## MongoDB Capability Tags

Shown on screen because the demo and video are judged on it (NFR10). One quiet tag per panel, never more.

| Panel | Tag | Hover sentence |
|---|---|---|
| Report page, related evidence | "Atlas Vector Search", or "Atlas Search (text)" when the fallback was used | "Related evidence is retrieved by Vector Search over embeddings stored in Atlas. The score is similarity, not evidence." (fallback: "Related evidence is retrieved by text search in Atlas because Vector Search was unavailable.") |
| Report page, memories panel | "Memory in Atlas" | "Reviewer corrections are documents in Atlas, scoped to the Team, versioned, and retrieved by similarity to the discovery." |
| Identity card (grant and policy set) | Schema validation | "Grants and policies are checked by `$jsonSchema` validation in Atlas, so a malformed grant can't be saved." |
| Audit view, Slack entry | Atomic updates | "Each Slack alert is claimed with one conditional update in Atlas, so two workers never both post it." |
| Run console feed, Audit view (V48) | "Change streams" while the label reads "Live (change stream)"; "Polling" otherwise | "New actions arrive from an Atlas change stream on the run's events, resuming where they left off." (polling: "The console reads new actions from Atlas every 2 seconds.") |
| Report page, revert (V48) | Atomic updates | "A revert claims the report with one conditional update and removes the update through a guarded write; nothing is deleted." |

**Cut:** `$graphLookup` (impact view). Change streams are shown only when they ran (V48).

## Demo on Camera

Two judged moments: the 60-second video (recorded 16:30 to 16:50, submitted by 16:55) and the 3-minute live demo from 17:15. Both show only work built on 14 November.

- Recorded at 1440 × 900 and shown live on the venue screen [ASSUMPTION: check the venue resolution at kick-off]. Browser zoom 100%. On the report page, the discovery header, the first related item, the memory effect and the decisions bar fit without scrolling, or the bar is sticky.
- **Setup snapshot.** During I1 setup (step 1 from 13:30, step 2 from 14:00), on the sandbox and through the real UI: the FDA seed, the prior collection loaded in baseline mode, the embeddings and the index ready, and Sam's correction of the setup run's report creating memory M1 (Flow 0). The snapshot is taken after that, with the scan cursor before NCT04712877's update.
- **Reset before each take.** The reset restores the post-setup snapshot, including M1 (V15, D41): the prior collection, the FDA seed, M1 active, no discovery run, no report on NCT04712877, no task. It runs before the video (16:30) and again between submission and the live demo (16:55 to 17:10). Then open a second tab on Slack `#all-mango-db-hackathon`, signed in. Confirm `DXP_BASE_URL` is the production URL, so "Review in DxP" opens `/reports/<report_id>` on the deployed app. The webhook URL is never shown.
- **Slack opens the report.** The alert arrives in the second tab; pressing "Review in DxP" opens the report page in DxP. That hand-off is a judged moment (must-show 4).
- **Pacing.** `DXP_DEMO_PACE` paces the scan, so NCT04712877 is the first item and the claim block is visible as it happens.
- **The scenario, from real data.** The scope is "Plasma ctDNA genotyping assays in NSCLC" (all stages) for Team Liquid Biopsy Dx (Synthetic), grant `lbdx@v1`. The scan finds the anchor verified at 10:45; the expected candidate is NCT04712877 (RECRUITING, no posted results), whose one intervention, "ctDNA, tumor NGS", has "FoundationOne CDx" and "FoundationOne Liquid" as other names: both are names present in the record, never proof of use (V36, V37). The report frames it as a new trial signal worth investigating: "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." Vector Search relates it to prior in-scope trials (expected: Extends, a new early-stage setting, with two checked quotes). The agent writes two drafts, both gated (V21): the first without memories, the second with M1, which states recruiting status, no results yet. The agent's proposed link of the record's "FoundationOne CDx" mention to the Team's plasma scope is blocked by check 2 on every take, because the scope excludes the tissue assay; that is the guaranteed block (must-show 3, V35, V37). If the first draft makes an unsupported performance or results claim, the claim check blocks it before filing and it goes on camera; the model may not write it, so never promise it. The report names its gap, "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?" and its one update adds the trial to the scope's evidence collection; no assay record changes. If NCT04712877 is not updated after the cursor at 10:45 (OD2, V36), the scan's real result is the anchor, framed the same way, with no claim about which assay it studies.
- **The rollback story (V48, never cut).** At the stop (step 7) and again at the audit (step 10), Sam says: "Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo." Then: pending reports can be rejected; memories can be revoked; history and source versions are never overwritten; and, only if the revert check (S4) passed, an approval can be reverted. Say "cannot change accepted knowledge without a human approval". Never claim automatic rollback of external effects: the Slack alert that was sent stays sent, and the audit records it. Name change streams only when the label reads "Live (change stream)".
- **Say it right (V27, V33, V37, V39).** The narration calls both names a "mention" or "named in the record", never "uses" or "studies", and never says or implies that any assay performed. At approval it says: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." when the task was queued, or "Follow-up task authorised; not run" when it was not. It never claims or narrates completed follow-up work unless the task actually ran in that demo or recording.
- **Source check before camera (V44).** In rehearsal one person reads the demo report and its briefing or narration script side by side with the exact source version the report used (its stored `version_id`) and confirms every claim; separately, that version is compared with the live ClinicalTrials.gov record, and a difference is noted as "changed since the run", not as an error in the report.
- **The longitudinal value (V32).** The narration says that the scan looks only at what changed since the scope's last scan, that M1 came from Sam's correction earlier in the day, and that the cursor and the Team's memories accumulate over time: team-specific, longitudinal intelligence on the diagnostics a team follows, of which the demo shows one turn.
- **Only what passed goes on camera.** The briefing appears only if B06 merged by 14:45 and the flag is on; Sam presses "Generate briefing" on camera. The avatar video appears only if B08 merged, the `avatar` flag is on and the one render requested for the demo report is Ready (OD7, V29: it is requested when the demo report is filed, and the report is opened last on camera to give it time). If it still reads "Rendering" or "Avatar unavailable", leave it and continue; the script is on screen as text and the loop is unaffected. The follow-up task runs on camera only if A25 joined I3 (V28, V30); otherwise the task shows Authorised. If the text-search fallback is in use, the report says "Related by text search" on camera; say so rather than hide it.
- **The scripted question (Audit view):** "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"
- Keep the camera on the agent's research and decisions: discovery, relationship, memory effect, block, approval, task, audit. The Accepted knowledge view is a supporting shot.

## Inspiration & Anti-patterns

- **From pathology:** the H&E palette and the idea that pink means "look here".
- **From journal reading:** quotes in serif, with the source underneath, like a citation; relationships argued from quotes, like a review article.
- **From audit logs and flight recorders:** every action in order, with who, under what authority, and what happened.
- **From shadcn:** the whole component vocabulary; DxP adds only the brand layer.
- **Rejected: a dashboard as the main feature.** Banned by the hackathon, and it hides the agent's research.
- **Rejected: a similarity score dressed as a finding.**
- **Rejected: "the AI learned" language.** Memories are named, authored, versioned and revocable.
- **Rejected: dark "AI dashboard" look, KPI cards, and a chat box as the main interface.**

## Key Flows

Protagonists: Rowan, Director of Diagnostics at a pharmaceutical therapy-area team, who asks the questions; and Sam, the data curator who starts runs and reviews reports. [ASSUMPTION: names invented for these flows; the PRD names roles only.] The work is for Rowan's Team, Team Liquid Biopsy Dx (Synthetic).

### Flow 0: setup, Sam's correction creates M1 (during the event, I1 step 2, 14:00 to 14:15)

| Step | What happens |
|---|---|
| 1 | The FDA seed and the prior collection are loaded through real API calls (baseline mode). Embeddings and the index are ready, or the text-search fallback is confirmed. |
| 2 | The setup run `POST /runs { grant_id: "lbdx", set: "nct:NCT05715229" }` files a report on NCT05715229 (TERMINATED, no posted results). The trial is not in the prior collection. Its draft wording states outcomes. |
| 3 | Sam opens the report from its Slack alert and presses **Reject** with the note: "Terminated trial with no posted results: describe its status; do not state outcomes", and chooses the claim kind "Outcome stated without posted results" (`outcome_claim_without_results`). Reject is used here so setup authorises no follow-up task; Approve with correction would also create the memory. |
| 4 | The toast reads "Rejected. Memory M1 created." The memories panel shows M1: author Sam (Synthetic), source decision and report, tags (claim kind `outcome_claim_without_results`; the assay tag from that report), Active, v1. Because retrieval matches claim kind, not assay, M1 will apply to the next discovery whatever assay it mentions (V22). |
| 5 | The post-setup snapshot is taken, including M1. Every reset restores it. |

### Flow 1: the 3-minute live demo (V16 order)

| Time | Step |
|---|---|
| 0:00 to 0:15 | **1. Start.** Sam opens the Run console, chooses the grant labelled "Team Liquid Biopsy Dx (Synthetic), Plasma ctDNA genotyping assays in NSCLC" and presses "Start run". The identity card fills: agent dxp-curator, "Started by Sam", grant `lbdx@v1`, policy set `ps_ab12…`, "Scanning trials updated since {cursor}". |
| 0:15 to 0:30 | **2. Discover.** A "Search source" row is allowed; the scan, which looks only at what changed since the scope's last scan, finds the anchor verified at 10:45 (NCT04712877 expected): a new trial signal worth investigating (V32, V33, V36). |
| 0:30 to 0:50 | **3. Block.** The block on the record's "FoundationOne CDx" mention arrives: "Blocked before it ran: Diagnostic in team scope failed. The record names 'FoundationOne CDx' (a tissue assay); the Team's plasma scope excludes it." This one always happens (must-show 3, V35, V37). If the first draft wrote an unsupported claim, a "Claim blocked before filing: 'showed' needs reported results. The source is RECRUITING and has no posted results." row also arrives, and the second draft follows, allowed (V21). |
| 0:50 to 1:10 | **4. Report with M1.** "Report filed (pending review)". On the report page: the headline in the V33 wording; "Named in the record" for both names; the intervention-ambiguity and unresolved-name uncertainties; related evidence labelled with both quotes (expected: Extends) and similarity shown as "similarity, not evidence"; the evidence gap; the M1 chip reads "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet", with Before and After; the narration says M1 came from a correction earlier in the day (V32). |
| 1:10 to 1:30 | **5. Slack.** In the second tab the alert has arrived in `#all-mango-db-hackathon`: headline, relationship summary, "Approve or reject in DxP". Sam presses "Review in DxP"; the same report opens in DxP. |
| 1:30 to 1:45 | **6. Brief.** Only if ready (V29). The script is on screen as text. Sam presses "Generate briefing", then "Play briefing (10 s)", then "Play avatar video" if the demo report's one render reads Ready (a few seconds of it is enough live). Skipped if hidden; if either reads "Rendering" or "unavailable", Sam moves on. |
| 1:45 to 2:00 | **7. Stop.** On a second run with items remaining, Sam presses "Stop run": "Stopping: {n} in flight", then "Stopped". Sam says the rollback line (V48): "Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo." If the second discovery item is cut, Stop is shown in step 9 on the follow-up task's run while it runs (only if it started by itself, V38). |
| 2:00 to 2:15 | **8. Approve.** Back on the report, Sam presses **Approve**. The page reads, and Sam says: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." when task execution is on, or "Approved: 1 update accepted. Follow-up task authorised; not run." when it is off (V38). The update shows Accepted: NCT04712877 is in the scope's evidence collection; no assay record changed (V27, V35). |
| 2:15 to 2:35 | **9. Task (only if A25 joined; stretch, V39).** The task, queued at approval, starts by itself and answers the gap under `task-<hex>@v1`: its own Search source row, its gate checking scope, destination and limit, and its findings filed as related evidence, Pending review, or "Done. No matching results found among the records searched.", with its query, records searched and limit (V42). Otherwise the task reads "Follow-up task authorised; not run", Sam says exactly that and moves on; nobody claims or narrates completed follow-up work (V39). |
| 2:35 to 3:00 | **10. Audit.** Rowan asks: "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" Sam opens the Audit view: the sources and cursor, the retrieval and scores, M1 with its effect, the team-scope block on the "FoundationOne CDx" mention and, if it occurred, the blocked unsupported claim with its failed check, the Slack result, and under "After the run" Sam's approval and the task authorisation, linked to the task's run. "Who authorised this?" on the task answers in one sentence. Close with the rollback story (V48): pending reports can be rejected, memories revoked, history and source versions are never overwritten, and, only if S4 passed and time allows, Sam presses "Revert approval" with a note and the page reads "Approval reverted by Sam at {time}: 1 update removed from accepted knowledge.", while the Slack alert stays sent. |

Failure: the Slack post times out. The row shows "Result unknown" with the action ID and is not retried. Sam checks the channel, presses Resolve, records the outcome with a note, and opens the report from the Reports list instead.

### Flow 2: the 60-second video (V17)

| Seconds | Shows | Screen |
|---|---|---|
| 0 to 10 | The scope and the agent's identity | Grant chosen with its Team and scope, "Start run", the identity card |
| 10 to 25 | The discovery, its related evidence, its gap, and M1 changing the wording | The anchor found as a new trial signal (V33 wording); the report page with relationship labels, quotes and "similarity, not evidence", the evidence gap; the M1 chip with Before and After; narration: the scan looks only at what changed, and M1 came from a correction earlier in the day (V32) |
| 25 to 35 | A block before it takes effect (V21, V35, V37) | The "Claim blocked before filing" row and its failed claim check if the first draft wrote it on this take; otherwise the block on the record's "FoundationOne CDx" mention with its failed check |
| 35 to 45 | The Slack alert opening the report | The alert in `#all-mango-db-hackathon`, "Review in DxP", the report page |
| 45 to 60 | Approval, the follow-up task, and the audit answer | Sam presses Approve: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (task queued) or "… Follow-up task authorised; not run." (V38); the task's run is shown only if it actually ran in this recording, and otherwise the narration says "Follow-up task authorised; not run" (V39); the Audit view answers the scripted question; the narration says the rollback line (V48), "Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo.", mentions reverting an approval only if S4 passed, and claims no rollback of external effects. Never "uses" or "studies" for either name (V37) |

### Earlier flows

Replaced. The governed-audit flows of 13 and 14 November (proposal-level Review, impact view, stop before approval) and the original Jobs, Home and Digest flows are in git history.
