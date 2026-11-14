# 60-second video script

Script for the 60-second submission video (Story 8.4, recorded by R1 from 16:30 to 16:50, submitted by 16:55). Timings follow V17 as amended by V25 to V48. If two decisions disagree, the higher number wins (V48 over V1 to V47; V38 to V47 over everything earlier; V33 to V37 over V25 to V27).

Facts not known yet are `[[PENDING: ...]]` markers. Resolve each one in the pre-recording checklist, and never record with a marker unresolved. Narration is written for the case where every supporting feature is optional: nothing here needs the briefing, the avatar, revert, the live stream or the follow-up task run.

## Fixed rules for every take

1. **Wording (V33, V37).** Both "FoundationOne CDx" and "FoundationOne Liquid" are "named in the record" or "mentioned". Never say the trial "uses", "used", "studies" or "showed" either one. Say nothing that implies any assay's performance. Never merge the two names or map "FoundationOne Liquid" to an FDA-approved product.
2. **The anchor (V36).** The script uses the trial the live API returned at 10:45. [[PENDING: the anchor trial, verified at 10:45 with its update date, status and results (OD2)]] The text below is written for the expected candidate. If the anchor is another trial, rewrite segments 2 and 3 from that trial's own fields, following the V33 pattern, and recount the words.
3. **Follow-up work (V39).** Narrate completed follow-up work only if the task actually ran in this take. Otherwise say "Follow-up task authorised; not run" and nothing more about it.
4. **The rollback line (V48, never cut).** Segment 5 says, word for word: "Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo." Say the agent "cannot change accepted knowledge without a human approval" (caption, see segment 5). Never claim any automatic rollback of external effects: a Slack alert that was sent stays sent.
5. **Only what passed (D1, V29).** Show only behaviour that passed on the integrated build, built on 14 November. Never show a key, the Slack webhook address, `.env`, the Modal or Vercel secret pages, or browser developer tools.
6. **Capability names.** Name a MongoDB capability only if it was proven on the sandbox. Say "Vector Search" only if the report's retrieval method was Vector Search; if it fell back, the screen reads "Related by text search" and the tag reads "Atlas Search (text)". Say "change streams" only if the console label read "Live (change stream)" on this take; otherwise do not name them. [[PENDING: retrieval method on this take, Vector Search or text search (OD1)]] [[PENDING: whether the console label reads "Live (change stream)" (S5, OD5)]]
7. **Pace.** About 150 words a minute. Set `DXP_DEMO_PACE` so the anchor is the first item and the block is visible as it happens. Total narration budget is 150 words.

## Approval variants

Segment 5 has two narrations. Choose before recording, by the state of the backend flag `task_run` on this take.

| Variant | When | Approval line, on screen and spoken |
|---|---|---|
| **A (V27, V38 flag on)** | `task_run` is on, so the approved task was queued | "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." |
| **B (V38 flag off)** | `task_run` is off, or the task did not run | "Approved: 1 update accepted. Follow-up task authorised; not run." |

In variant A the task's run may be shown only if it actually ran in this take, and its findings are shown as "Pending review". Approved is not accepted for the task. If the flag is on but the task has not started or has not finished within the take, record variant A's approval line without showing any task result and claim nothing completed. [[PENDING: which variant applies on the recording take (R1, I3b, task_run state)]]

## Timeline

| Seconds | Segment | Cap at 150 wpm | Narration words |
|---|---|---|---|
| 0 to 10 | 1. Scope and identity | 25 | 25 |
| 10 to 25 | 2. The signal, related evidence, the gap and M1 | 37 | 37 |
| 25 to 35 | 3. The block | 25 | 25 (24 with the claim variant) |
| 35 to 45 | 4. Slack opens the report | 25 | 20 |
| 45 to 60 | 5. Approval, the rollback line, audit | 37 | 36 (variant A), 35 (variant B) |
| | **Total** | 149 | 143 to 144 (about 57 seconds) |

Recount after any edit: count the words of the quoted narration in each segment, and keep each segment at or under its cap.

## Segment 1: 0 to 10 s, the scope and the agent's identity

**On screen**
1. 0:00 Run console. Sam (Synthetic) chooses the grant labelled "Team Liquid Biopsy Dx (Synthetic), Plasma ctDNA genotyping assays in NSCLC".
2. 0:03 Press "Start run".
3. 0:05 The identity card fills: agent `dxp-curator`, "Started by Sam", the grant shown as its id and version, the policy set shown as `ps_...` with its policy count, and "Scanning trials updated since" the cursor date. Hold on the card until 0:10.
4. Caption tag: "Schema validation" (grants and policies), only if proven. [[PENDING: whether schema validation was proven on the sandbox (I1)]]

**Narration (25 words)**
> Our scope: plasma ctDNA genotyping assays in NSCLC. The agent, dxp-curator, holds a scoped grant. Each scan reads only what changed since the last one.

**Notes.** This is the V32 line: the scan looks only at what changed since the last scan.

## Segment 2: 10 to 25 s, the signal, its related evidence, the gap and M1

**On screen**
1. 0:10 The scan row "Search source" is allowed; the anchor appears first in the feed.
2. 0:13 The report page opens on the headline (V33): "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." This text is for the expected candidate and is the report's own words. [[PENDING: the anchor's headline as the report states it (OD2)]]
3. 0:16 The first related item with its relationship label and both checked quotes; the score reads "similarity, not evidence". The tag reads "Atlas Vector Search", or "Atlas Search (text)" with "Related by text search" if that was the fallback. [[PENDING: Vector Search or text search (OD1)]]
4. 0:20 The evidence gap: "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?"
5. 0:22 The M1 chip: "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet", with Before and After. Tag "Memory in Atlas".
6. The report must show "Named in the record" for both names and the intervention uncertainty. Do not zoom on or read any statement about an assay.

**Narration (37 words)**
> It finds a new trial: molecular profiling using blood and tumour tissue in early-stage lung cancer. No results posted. Related evidence carries checked quotes, the gap is named. M1, a correction from earlier today, changed the wording.

**Notes.** "A correction from earlier today" is the V32 line: M1 was created by Sam through the real UI during setup. If retrieval fell back to text search, replace "Related evidence carries checked quotes" with "Related evidence, by text search, carries checked quotes" and trim "the gap is named" to stay at 37 words or fewer.

## Segment 3: 25 to 35 s, the blocked case

**On screen**
1. 0:25 The feed row: "Blocked before it ran: Diagnostic in team scope failed", with the explanation that the record names "FoundationOne CDx" (a tissue assay) and the team's plasma scope excludes it. This block is guaranteed on the expected anchor (V35, V37). [[PENDING: whether the block is on the record's "FoundationOne CDx" mention for the actual anchor (OD2)]]
2. 0:30 Open the one blocked Decision: the check, the mention and the scope rule. Tag "Atomic updates" or "Schema validation" only if proven.
3. If the first draft also wrote an unsupported performance or results claim on this take, show its row too: "Claim blocked before filing: 'showed' needs reported results. The source is RECRUITING and has no posted results." The model may not be made to write it; never promise it, and never stage it.

**Narration (25 words)**
> Blocked before filing: the agent proposed linking the record's FoundationOne CDx mention to our plasma scope. Check two failed: that assay is out of scope.

**Claim variant (24 words), only if the claim block occurred on this take**
> A claim needing posted results was blocked too. The agent's link from the record's FoundationOne CDx mention to our plasma scope failed check two.

**Notes.** "Mention" is deliberate (V33, V37). Do not say the trial uses, studies or tested the assay. Check 2 is "Diagnostic in team scope".

## Segment 4: 35 to 45 s, the Slack alert opens the report

**On screen**
1. 0:35 Switch to the second tab, Slack `#all-mango-db-hackathon`, already signed in. The one alert for this report is visible: headline, relationship summary, "Approve or reject in DxP".
2. 0:39 Press "Review in DxP". The same report opens in DxP on the deployed app (`/reports/<report_id>`). The webhook address and the Slack integration settings are never shown.
3. Hold on the report with "Pending review" visible.

**Narration (20 words)**
> One Slack alert per report. Review in DxP opens that same report. Slack only notifies; the decision happens in DxP.

**Notes.** Slack for the rehearsals and earlier takes remains in the channel; the alert for this take is told apart by its run ID. [[PENDING: whether the organisers accept the alert volume in this channel (docs/clearance.md)]]

## Segment 5: 45 to 60 s, approval, the rollback line, the audit answer and the close

**On screen**
1. 0:45 Press "Approve". The page shows the approval line for the chosen variant (see the table above) and the update "Accepted" in the scope's evidence collection. No assay record changes. Task line reads "Authorised" (or "Not run").
2. 0:49 Open the Audit view. Caption the scripted question: "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" Scroll slowly through the sources and cursor, the retrieval, M1 with its effect, the block, the Slack result, and under "After the run", Sam's approval and the task authorisation.
3. 0:53 Caption, one line at a time, over the audit view: "The agent cannot change accepted knowledge without a human approval." then "Pending reports can be rejected. Memories can be revoked. History and source versions are never overwritten." The Slack row stays as it is: the alert that was sent stays sent.
4. Optional caption, only if S4 (revert) passed: "An approval can be reverted." Do not press "Revert approval" in the video. [[PENDING: whether revert passed its check (S4)]]
5. Optional tag "Change streams", only if the console label read "Live (change stream)" on this take. [[PENDING: live label on this take (S5)]]
6. 0:57 Hold on the Audit view for the close.

**Narration, variant A (36 words, `task_run` on, V27)**
> Approved: one update accepted. Follow-up task authorised; its findings will be pending review. Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. Team-specific, longitudinal intelligence.

**Narration, variant B (35 words, flag off, V38)**
> Approved: one update accepted. Follow-up task authorised; not run. Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. Team-specific, longitudinal intelligence: one turn shown.

**Notes**
- **The close (V32).** The last words name the bigger value, team-specific, longitudinal intelligence. If time allows in variant A, add "one turn shown"; do not exceed 37 words.
- **The 15-second limit.** At 150 words a minute, 15 seconds holds about 37 words. The approval line, the 22-word rollback line and the close already fill it, so the spoken script cannot also carry the audit answer or the supporting points. The audit question and the supporting points are therefore on-screen captions, and the audit view carries the answer visually. This is a deliberate choice; if more spoken time is wanted, take it from segment 4, not from the rollback line.
- **The approval line on screen (V27, V38).** The full sentence appears as the page's own text, even though the narration reads "one" for "1".
- **No completed follow-up work (V39).** Do not say the task found, completed or answered anything unless it ran in this take. "Approved" is not "accepted" for the task's findings.
- **Rollback of external effects.** Never say or caption that anything was rolled back outside DxP.

## Pre-recording checklist

Complete all items before R1 presses record. Do not skip the source check.

### Facts to resolve
- [ ] Anchor trial confirmed from the 10:45 check, with its update date, status and results (OD2). Segments 2 and 3 match its own fields. [[PENDING: the anchor trial (OD2)]]
- [ ] Retrieval method on the sandbox: Vector Search or text search (OD1). Tags and narration match. [[PENDING: retrieval method (OD1)]]
- [ ] Variant A or B chosen from the `task_run` state, and the task's run is shown only if it actually ran in this take. [[PENDING: variant for this take (task_run state)]]
- [ ] Live label read: "Live (change stream)" or "Refreshing every 2 s". Change streams are named only for the first. [[PENDING: label on the console (S5)]]
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
- [ ] Briefing and avatar are not part of the 60 seconds.

### Wording check
- [ ] No narration, caption or on-screen text says the trial "uses", "used" or "studies" either assay name, or implies how any assay performs.
- [ ] "FoundationOne Liquid" is never mapped to an FDA-approved product; the report's uncertainty about it stays on screen if it is shown.
- [ ] The rollback line is said word for word. No automatic rollback of external effects is claimed.
- [ ] No completed follow-up work is narrated unless the task ran in this take.
- [ ] Narration is 150 words or fewer in total and fits 60 seconds.

### After the take (R1)
- [ ] Upload the video, add its link to the README (the only README edit outside B07) and paste `docs/submission.md` into the form with the public repository and team members, by 16:55.
- [ ] Luis runs `scripts/reset_demo.py` between 16:55 and 17:10, ready for the 17:15 live demo.
