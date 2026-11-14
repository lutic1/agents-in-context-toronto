# 60-second video script

Script for the 60-second submission video (Story 8.4, recorded by R1 from 16:30 to 16:50, submitted by 16:55). Timings follow V17 as amended by V25 to V48. If two decisions disagree, the higher number wins (V48 over V1 to V47; V38 to V47 over everything earlier; V33 to V37 over V25 to V27).

Facts not known yet are markers that start with the word PENDING inside double square brackets. Resolve each one in the pre-recording checklist, and never record with such a marker unresolved. Narration is written for the case where every supporting feature is optional: nothing here needs the briefing, the LiveAvatar (HeyGen), pending approval (proposed V70), revert, the live stream or the follow-up task run. LiveAvatar is a live, interactive avatar that would speak only the report's verified script. It is pending Luis's approval as decision V49, it is optional and it is the first supporting cut (V28). It is never part of the 60 seconds.

## Fixed rules for every take

1. **Wording (V33, V37).** Both "FoundationOne CDx" and "FoundationOne Liquid" are "named in the record" or "mentioned". Never say the trial "uses", "used", "studies" or "showed" either one. Say nothing that implies any assay's performance. Never merge the two names or map "FoundationOne Liquid" to an FDA-approved product.
2. **The anchor (V36).** The script uses the trial the live API returned at 10:45. The anchor is NCT04712877, updated 2026-11-12, after the 2026-11-11 scan cursor (V49 closes OD2). Confirm its status and results in the live record before recording. The text below is written for it. If the anchor is another trial, rewrite segments 2 and 3 from that trial's own fields, following the V33 pattern, and recount the words.
3. **Follow-up work (V39).** Narrate completed follow-up work only if the task actually ran in this take. Otherwise say "Follow-up task authorised; not run" and nothing more about it.
4. **The rollback line (V48, never cut).** Segment 5 says, word for word: "Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo." The agent "cannot change accepted knowledge without a human approval" is a caption (see segment 5), because the spoken line fills its window. Never claim any automatic rollback of external effects: a Slack alert that was sent stays sent.
5. **Only what passed (D1, V29).** Show only behaviour that passed on the integrated build, built on 14 November. Never show a key, the Slack webhook address, `.env`, the Modal or Vercel secret pages, or browser developer tools.
6. **Capability names.** Name a MongoDB capability only if it was proven on the sandbox. Say "Vector Search" only if the report's retrieval method was Vector Search; if it fell back, the screen reads "Related by text search" and the tag reads "Atlas Search (text)". Say "change streams" only if the console label read "Live (change stream)" on this take; otherwise do not name them. [[PENDING: retrieval method on this take, Vector Search or text search (OD1)]] [[PENDING: whether the console label reads "Live (change stream)" (S5, OD5)]]
7. **Timing and captions (measured, not counted).** A word cap does not predict read-aloud time: acronyms (ctDNA, NSCLC, DxP), long words and punctuation slow speech. Every segment is therefore timed with macOS `say`, as follows.
   - **Calibration.** A 105-word plain-prose control takes 42.46 s at `say -r 77` (41.83 s at `-r 78`; `say` moves in steps, so no rate gives exactly 42.00 s). The slower rate, 77, is used so the figures err on the long side.
   - **Measurement.** Each narration below is timed at `say -r 77` (default voice, plain text exactly as written, `afinfo` estimated duration). Each segment must end at least 0.5 s inside its window; the figure is recorded next to each narration and in the timeline table. Re-time after any edit: write the narration to a text file, run `say -r 77 -f <file> -o <file>.aiff`, and read the duration with `afinfo`.
   - **Captions.** A caption is text added in editing, including a capability tag. Show at most about 3 words per second on screen, and at most 2 captions at once. Each caption below states its window and word count. The page's own text (the headline, the feed rows, the gap, the M1 chip) is not read aloud and is not relied on as a caption, except the approval line in segment 5, which is counted as a caption.
   - **Take.** Set `DXP_DEMO_PACE` so the anchor is the first item and the block is visible in the feed. Decide before recording whether the 60 seconds is one continuous take or cut by segment. In a continuous take the report must be filed by 0:13 and the Slack alert must be visible by 0:35 on this take's own clock. If that does not hold in rehearsal pass 2, either start the run before the recording window (identity card first, then the report), or cut the take by segment and keep each segment's on-screen run time inside its boundaries.
   - **What does not fit.** Anything that did not fit its window is listed under "Held back from the 60 seconds" after the timeline, with where it went (a caption or the 3-minute live demo).

## Approval variants

Segment 5 has one narration for both variants. The variants differ only in the approval line the page shows and the first caption holds. Choose before recording, by the state of the backend flag `task_run` on this take.

| Variant | When | Approval line, shown on screen as the page's own text (not spoken in full) |
|---|---|---|
| **A (V27, V38 flag on)** | `task_run` is on, so the approved task was queued | "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." |
| **B (V38 flag off)** | `task_run` is off (the page reads "not run") | "Approved: 1 update accepted. Follow-up task authorised; not run." |

The narration says only "Approved: one update accepted." The follow-up sentence is on screen (caption K1 in segment 5) and is spoken in the 3-minute live demo. In variant A the task's run may be shown only if it actually ran in this take, and its findings are shown as "Pending review". Approved is not accepted for the task. If the flag is on but the task has not started or has not finished within the take, record variant A's approval line without showing any task result and claim nothing completed. [[PENDING: which variant applies on the recording take (R1, I3b, task_run state)]]

## Timeline

Measured with `say -r 77` (control: 105 words in 42.46 s). "Margin" is the window minus the measured time; it must be at least 0.5 s.

| Seconds | Segment | Narration words | Measured at -r 77 | Margin |
|---|---|---|---|---|
| 0 to 10 | 1. Scope and identity | 16 | 9.07 s | 0.93 s |
| 10 to 25 | 2. The signal, related evidence, the gap and M1 | 24 | 13.33 s (variants: 12.58 s, 13.88 s, 14.10 s) | 1.67 s (worst variant 0.90 s) |
| 25 to 35 | 3. The block | 15 | 8.91 s (claim variant, 18 words: 8.97 s) | 1.09 s (claim variant 1.03 s) |
| 35 to 45 | 4. Slack opens the report | 15 | 8.64 s | 1.36 s |
| 45 to 60 | 5. Approval, the rollback line, audit | 24 | 13.66 s | 1.34 s |

There is no total word budget. Total narration is about 94 words, about 53 s at these measured speeds, with the gaps between segments left for the on-screen steps.

Re-time after any edit. A segment whose measured time is less than 0.5 s inside its window is edited, not recorded.

## Segment 1: 0 to 10 s, the scope and the agent's identity

**On screen**
1. 0:00 Run console. Sam (Synthetic) chooses the grant labelled "Team Liquid Biopsy Dx (Synthetic), Plasma ctDNA genotyping assays in NSCLC".
2. 0:03 Press "Start run".
3. 0:05 The identity card fills: agent `dxp-curator`, "Started by Sam", the grant shown as its id and version, the policy set shown as `ps_...` with its policy count, and "Scanning trials updated since" the cursor date. Hold on the card until 0:10.

**Captions (2 at most at once, 8 words in all)**
- 0:03 to 0:05.5 tag "Schema validation" (2 words), only if proven. [[PENDING: whether schema validation was proven on the sandbox (I1)]]
- 0:05.5 to 0:10 "Agent dxp-curator, scoped grant" (4 words).
- 0:07 to 0:10 tag "Change streams" (2 words), only if the console label reads "Live (change stream)" on this take. [[PENDING: live label on this take (S5, OD5)]]

**Narration (16 words, 9.07 s)**
> Plasma ctDNA tests in lung cancer. The agent reads only what changed since its last scan.

**Notes.** This is the V32 line: the scan looks only at what changed since the last scan. The full scope name, "Plasma ctDNA genotyping assays in NSCLC", is on screen in the grant label, not spoken. The agent's name and its scoped grant are on the identity card and in the caption, not spoken. No acronym is expanded aloud: expanding "ctDNA" would cost about 1.5 s the window does not have.

## Segment 2: 10 to 25 s, the signal, its related evidence, the gap and M1

**On screen**
1. 0:10 The scan row "Search source" is allowed; the anchor appears first in the feed.
2. 0:13 The report page opens on the headline (V33): "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." This text is for the expected candidate and is the report's own words. It is shown, not read aloud, and the camera holds on it until 0:17. [[PENDING: the anchor's headline as the report states it (OD2)]]
3. 0:16 The first related item with its relationship label and both checked quotes (or, if it reads "related (no relationship established)", use the fallback narration below); the score reads "similarity, not evidence". The tag reads "Atlas Vector Search", or "Atlas Search (text)" with "Related by text search" if that was the fallback. [[PENDING: Vector Search or text search (OD1)]]
4. 0:20 The evidence gap, as the page's own text: "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"
5. 0:22 The M1 chip, only if it is visible on this take: "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet", with Before and After.
6. The report must show "Named in the record" for both names and the intervention uncertainty. Do not zoom on or read any statement about an assay.

**Captions (2 at most at once, 6 words in all)**
- 0:16 to 0:20 tag "Atlas Vector Search" (3 words), or "Atlas Search (text)" for the fallback.
- 0:22 to 0:25 tag "Memory in Atlas" (3 words), only if the M1 chip is visible and the tag was proven. [[PENDING: whether memories in Atlas were proven (I1, S3)]]

**Narration (24 words, 13.33 s)**
> An updated lung cancer trial, no results posted. Related evidence has checked quotes. One gap named. A correction from earlier today changed the wording.

**Fallback narration, no relationship (22 words, 12.58 s).** Use it whenever the first related item has no relationship label and both checked quotes:
> An updated lung cancer trial, no results posted. No relationship claimed. One gap named. A correction from earlier today changed the wording.

**Text-search variant (24 words, 13.88 s).** Use it when retrieval fell back to text search:
> An updated lung cancer trial, no results posted. Text-search relations have checked quotes. One gap named. A correction from earlier today changed the wording.

**Text-search variant with no relationship (24 words, 14.10 s, margin 0.90 s).** Use it when both apply:
> An updated lung cancer trial, no results posted. Text search, no relationship claimed. One gap named. A correction from earlier today changed the wording.

**Notes.** "A correction from earlier today" is the V32 line: M1 was created by Sam through the real UI during setup. "Updated trial", not "new trial": the anchor is a trial updated after the cursor (V36) and may have been in the registry for years. The detail "molecular profiling using blood and tumour tissue in early-stage lung cancer" moved from the narration to the on-screen headline; the narration carries "no results posted" and the recording must show the headline. "M1" is named by the chip, not spoken. If the M1 chip with its Before and After is not visible on this take, delete the last sentence ("A correction from earlier today changed the wording.") and the M1 on-screen step; the remaining narration is 9.16 s. Choose the variant before recording so nothing is edited on the fly.

## Segment 3: 25 to 35 s, the blocked case

**On screen**
1. 0:25 Go back to the Run console feed (or the Audit view); the block row was recorded during the scan, before the report was filed. The feed row: "Blocked before it ran: Diagnostic in team scope failed", with the explanation that the record names "FoundationOne CDx" (a tissue assay) and the team's plasma scope excludes it. This block is guaranteed on the expected anchor (V35, V37). [[PENDING: whether the block is on the record's "FoundationOne CDx" mention for the actual anchor (OD2)]]
2. 0:30 Open the one blocked Decision: the check, the mention and the scope rule.
3. If the first draft also wrote an unsupported performance or results claim on this take, show its row too, from 0:31: "Claim blocked before filing: 'showed' needs reported results. The source is RECRUITING and has no posted results." The model may not be made to write it; never promise it, and never stage it.

**Captions (1 at a time, 3 words in all)**
- 0:30 to 0:34 tag "Decisions in Atlas" (3 words), or "Schema validation" (2 words), only whichever was proven. [[PENDING: which of the two tags was proven (I1, I3)]]

**Narration (15 words, 8.91 s)**
> Blocked before filing: the agent's link from the record's FoundationOne CDx mention failed check two.

**Claim variant (18 words, 8.97 s), only if the claim block occurred on this take**
> A results claim was blocked too. The agent's link from the record's FoundationOne CDx mention failed check two.

**Notes.** "Mention" is deliberate (V33, V37). Do not say the trial uses, studies or tested the assay. Check 2 is "Diagnostic in team scope". The words "assay out of scope" moved from the narration to the page's own explanation line on the block row ("the team's plasma scope excludes it"), which stays on screen from 0:25.

## Segment 4: 35 to 45 s, the Slack alert opens the report

**On screen**
1. 0:35 Switch to the second tab, Slack `#all-mango-db-hackathon`, already signed in. The one alert for this report is visible: headline, relationship summary, "Approve or reject in DxP".
2. 0:39 Press "Review in DxP". The same report opens in DxP on the deployed app (`/reports/<report_id>`). The webhook address and the Slack integration settings are never shown.
3. Hold on the report with "Pending review" visible.

**Captions (1 at a time, 2 words in all)**
- 0:40 to 0:44 tag "Atomic updates" (2 words), only if proven. [[PENDING: whether conditional updates were proven (I1)]]

**Narration (15 words, 8.64 s)**
> One Slack alert per report. Review in DxP opens that same report. Slack only notifies.

**Notes.** "The decision happens in DxP" is now the page's own text, "Approve or reject in DxP", on the alert and the report. Slack for the rehearsals and earlier takes remains in the channel; the alert for this take is told apart by its run ID. [[PENDING: whether the organisers accept the alert volume in this channel (docs/clearance.md)]]

## Segment 5: 45 to 60 s, approval, the rollback line, the audit answer and the close

**On screen**
1. 0:45 Press "Approve". The page shows the approval line for the chosen variant (see the table above) and the update "Accepted" in the scope's evidence collection. No assay record changes. The task line reads "Authorised" (or "Not run").
2. 0:49.5 Open the Audit view. Give the answer by scrolling only the four rows the scripted question names, about 1.5 s each: what was found (the sources and cursor), M1 and its effect, the block, and the authorisation (under "After the run", Sam's approval and the task authorisation). Do not scroll past the retrieval or the Slack result in this window. The Slack row stays as it is: the alert that was sent stays sent.
3. Do not press "Revert approval" in the video.

**Captions (never more than one at a time, 39 words in all, 42 in variant A; each at about 3 words a second or slower)**

| Id | Window | Words | Text |
|---|---|---|---|
| K1 | 0:45 to 0:49.5 | 10 (variant A: 13) | The page's own approval line, held unobscured: variant A or B from the table above |
| K2 | 0:49.5 to 0:51.5 | 5 | "Audit: found, reworded, blocked, authorised." |
| K3 | 0:51.5 to 0:55 | 10 | "The agent cannot change accepted knowledge without a human approval." |
| K4 | 0:55 to 0:57.7 | 8 | "Reports can be rejected. History is never overwritten." |
| K5 | 0:57.7 to 0:59.9 | 6 | "Team-specific, longitudinal intelligence: one turn shown." |

K5 is mandatory in both variants. It is centred and separate from K3 and K4, and it is the last thing on screen. The Atlas tags ("Decisions and actions in Atlas", "Change streams") are not shown in this segment: no room at this speed. "Decisions in Atlas" is shown in segment 3 instead, and "Change streams" in segment 1.

**Narration (24 words, 13.66 s, both variants)**
> Approved: one update accepted. Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo.

**Notes**
- **The rollback line (V48, never cut).** The second sentence of the narration is the V48 line, word for word. It is 10.2 s alone at this speed, so the 15 seconds hold it, the words "Approved: one update accepted." and nothing else.
- **The close (V32).** The last thing on screen names the bigger value, team-specific, longitudinal intelligence, and says the demo shows one turn of that loop. It is caption K5, not narration; there is no spoken time left for it.
- **The approval line on screen (V27, V38).** The full sentence appears as the page's own text and is caption K1; the narration reads "one" for "1" and drops the follow-up sentence.
- **No completed follow-up work (V39).** Do not say the task found, completed or answered anything unless it ran in this take. "Approved" is not "accepted" for the task's findings.
- **Rollback of external effects.** Never say or caption that anything was rolled back outside DxP.

## Held back from the 60 seconds

Each item below did not fit its window at the measured speed. It was not dropped silently. Where it went:

| Item | Went to |
|---|---|
| Agent name `dxp-curator` and "scoped grant" (segment 1) | Caption in segment 1 and the identity card |
| Full scope name "Plasma ctDNA genotyping assays in NSCLC" (segment 1) | The grant label on screen; spoken in the 3-minute live demo |
| "Molecular profiling using blood and tumour tissue in early-stage lung cancer" (segment 2) | The report headline on screen; spoken in the 3-minute live demo |
| "M1" by name (segment 2) | The M1 chip on screen |
| "Check two: assay out of scope" (segment 3) | The block row's explanation on screen |
| "The decision happens in DxP" (segment 4) | The alert and report text, "Approve or reject in DxP" |
| "Follow-up task authorised; ..." (segment 5) | Caption K1, the page's approval line; spoken in the live demo |
| The scripted audit question (segment 5) | Live demo; the video gives caption K2 and the four audit rows |
| "Pending reports can be rejected", "history and source versions are never overwritten" (segment 5) | Caption K4, shortened to "Reports can be rejected. History is never overwritten."; "and source versions" is in the submission text and the live demo |
| "Memories can be revoked" (only if S3 passed) and "An approval can be reverted" (only if S4 passed) | The 3-minute live demo and the submission text; no caption room in the video |
| The closing line "The aim: team-specific, longitudinal intelligence on the diagnostics a team follows. This demo shows one turn of that loop." | Caption K5, shortened to "Team-specific, longitudinal intelligence: one turn shown."; the full sentence is in the submission text and the live demo |
| The full spoken form of the V48 "cannot change accepted knowledge without a human approval" sentence | Caption K3 in the video; spoken in the live demo |

Deviation from the Story 8.4 wording, recorded here so a reviewer does not fail the AC: the V48 "cannot change accepted knowledge without a human approval" sentence, the supporting points, the audit question, the close and the follow-up sentence are captions or live-demo content, because the spoken rollback line fills most of the last 15 seconds. The rollback line is the narrated part. If more spoken time is wanted, take it from segment 4, not from the rollback line.

## Pre-recording checklist

Complete all items before R1 presses record. Do not skip the source check.

### Facts to resolve
- [ ] Anchor trial confirmed from the 10:45 check, with its update date, status and results (OD2). Segments 2 and 3 match its own fields. (V49: NCT04712877, updated 2026-11-12; status and results still to confirm on the day)
- [ ] Retrieval method on the sandbox: Vector Search or text search (OD1). Tags and narration match. [[PENDING: retrieval method (OD1)]]
- [ ] Variant A or B chosen from the `task_run` state, and the task's run is shown only if it actually ran in this take. [[PENDING: variant for this take (task_run state)]]
- [ ] Live label read: "Live (change stream)" or "Refreshing every 2 s". Change streams are named only for the first. [[PENDING: label on the console (S5)]]
- [ ] The first related item shows a relationship label with both checked quotes, or the fallback narration is used; the M1 chip with Before and After is visible on this take, otherwise delete the M1 sentence and the M1 on-screen step. [[PENDING: relationship label and M1 chip on this take (OD2, I1)]]
- [ ] S3 outcome known; the "Memories can be revoked." caption is used only if memory revoke passed S3. [[PENDING: whether memory revoke passed S3 (A21+A22)]]
- [ ] The take style is decided: one continuous take, or cut by segment (rule 7). Rehearsal pass 2 confirms the report is filed by 0:13 and the Slack alert is visible by 0:35 at the chosen `DXP_DEMO_PACE`. If not, start the run before the recording window (identity card, then report) or cut by segment. The report page may be opened from the Reports list only if that report was filed earlier in the same take; the sandbox is reset with no report on the anchor, so nothing else exists to open.
- [ ] S4 outcome known; the revert caption is used only if S4 passed. [[PENDING: whether revert passed (S4)]]
- [ ] Every capability tag on screen was proven on the sandbox. [[PENDING: proven capabilities (README table)]]

### The V44 source check (the video is not recorded until both parts pass)
- [ ] **(a) Against the version used.** One person reads the complete report and its narration script side by side with the exact source version the report used (its stored `version_id`), and confirms every claim in the report, the captions and this script is supported by that version.
- [ ] **(b) Against the live record.** Separately, compare that version with the live ClinicalTrials.gov record for the anchor. A difference is noted as "changed since the run", not as an error in the report.
- [ ] The result is recorded in `docs/demo-and-reset.md` (A16). A wording search is not enough: it cannot show that nothing implies an unsupported claim.

### State of the sandbox and the screen
- [ ] The sandbox was reset to the post-setup snapshot with `scripts/reset_demo.py` (A13) at 16:30: M1 is active, no run, no report on the anchor, no task.
- [ ] `DXP_DEMO_PACE` is set; the anchor is the first item.
- [ ] `DXP_BASE_URL` is the production URL, so "Review in DxP" opens `/reports/<report_id>` on the deployed app.
- [ ] Second tab: Slack `#all-mango-db-hackathon`, signed in, nothing else showing.
- [ ] Screen 1440 x 900, browser zoom 100%. The report's header, first related item, M1 chip and decisions bar fit without scrolling, or the bar is sticky.
- [ ] No key, webhook address, `.env`, secret page or developer tools can appear in any frame, including notifications and tab titles.
- [ ] The briefing and LiveAvatar (HeyGen), pending approval (proposed V70), are not part of the 60 seconds.

### Wording check
- [ ] No narration, caption or on-screen text says the trial "uses", "used" or "studies" either assay name, or implies how any assay performs.
- [ ] "FoundationOne Liquid" is never mapped to an FDA-approved product; the report's uncertainty about it stays on screen if it is shown.
- [ ] The rollback line is said word for word. No automatic rollback of external effects is claimed.
- [ ] Both variants: the closing caption K5, "Team-specific, longitudinal intelligence: one turn shown.", is on screen from 0:57.7 to the end. The segment 5 captions K1 to K5 follow the table, one at a time.
- [ ] No completed follow-up work is narrated unless the task ran in this take.
- [ ] Every narration used was re-timed at `say -r 77` after its last edit (control: 105 words in 42.46 s) and ends at least 0.5 s inside its window. No more than 2 captions are on screen at once, at about 3 words a second or slower.

### After the take (R1)
- [ ] Upload the video, add its link to the README and paste `docs/submission.md` into the form with the public repository and team members, by 16:55.
- [ ] A B07 follow-up PR (owner Vlad) updates the README status line, the Verified table and the MongoDB capability table from the A16 and I1 to I3 results before 16:30, and deletes each README sentence tagged `[[VERIFY: ...]]` whose check did not pass and removes the tags from the rest; the video link is added by R1.
- [ ] Luis runs `scripts/reset_demo.py` between 16:55 and 17:10, ready for the 17:15 live demo.
