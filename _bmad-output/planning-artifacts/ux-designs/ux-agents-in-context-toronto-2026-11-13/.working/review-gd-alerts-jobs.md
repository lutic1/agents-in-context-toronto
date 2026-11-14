# Graphic design review: Alerts v1 and Jobs v1

Reviewed: `shots/alerts-v1.png`, `shots/jobs-v1.png` against `shots/home-v7.png`, `shots/review-v5.png` and `DESIGN.md`. Sources read: `key-alerts.html`, `key-jobs.html`.

Both pages carry the shared shell well. The top bar, logo, nav icons, type stack, tokens, panel radius and shadow all match Home v7 and Review v5. There are no ALL-CAPS eyebrows, no arrows on buttons, no middle-dot meta strings and no decorative gradients beyond the specified primary-button gradient. Serif is used only for the Evidence quote, and mono is used for identifiers, with one exception noted below.

## Verdicts

| Page | Verdict |
|---|---|
| Alerts v1 | **Fix then ship** |
| Jobs v1 | **Fix then ship**, but the parallelism fix is close to a rework of the centre of the panel |

---

## Alerts v1

### Must-fix

1. **The column split is inverted against Review.** `.lower` is `560px 712px`, so the list ends at x=632 and the detail panel starts at x=658. Review and Jobs are `752px 520px`, with the right panel at x=850. When the video cuts from Review to Alerts, the layout jumps. Use `752px 520px` so the right edge of the list and the left edge of the detail land on the same lines as Review. The list rows have room at 752px, and the detail at 520px still fits the player, quote and three buttons. "Open Record" and "Show in the graph" fit on one row, and Dismiss can drop to the right of the heading or below.
2. **There is a large dead area under the detail panel.** At the current height the right panel ends at y≈643, which leaves about 360px of empty tissue field beside a full list. After the 7/5 change the panel gets taller (the text wraps more), and that helps. Also fill it with real content, not filler. Add a "What changed" before/after line (Clinical validation to Clinical utility, with the source and date), or the second Evidence item for the same Diagnostic. Either way, make the panel `position: sticky` so it stays level with the selected row.
3. **The alert count disagrees across pages.** Home v7 and Review v5 show an Alerts badge of **2**, but Alerts v1 shows **5** in the badge and "5 new" in the header. Home's panel headline says "5 changes since 2 November". Pick one number for the demo storyline and use it in the badge, the Home panel and the Alerts header. On camera the viewer will catch a 2 that turns into a 5.
4. **The timecode is set in mono.** `.player .time` uses `--mono` for "0:07 / 0:22". The spec reserves mono for identifiers a user copies, such as NCT IDs and PMIDs. Use the sans with `font-variant-numeric: tabular-nums`.
5. **The selected row treatment differs from Review.** Here the selected row is a flat ink-tint fill. In Review the selected item is a lifted white card with a 3px ink left bar. Use the Review treatment so "selected" looks the same everywhere.

### Should-fix

- **The audio-failed state is in the hero shot.** The amber "Couldn't load the briefing. Try again" sits mid-list, between two good rows. It is a valid state, but in a three-minute video it reads as a bug. Move it to a separate state frame, or at least to the last row.
- **Play buttons are icon-only.** The 32px square play buttons in the list have no label. The spec says never to show an icon alone without a label or tooltip. Home uses "Play briefing" with a label. On camera they also read as checkboxes. Add the label "Play", or a tooltip plus aria-label, and match Home's button style.
- **Labels are repeated in eosin.** Every row is new, so every row carries an eosin dot and eosin label. That is correct under the New filter, but four rows start with "Update: used in a trial" and the column turns into a pink stripe. Shorten the eosin part to the spec's word ("New" / "Changed") in eosin-text, and put the rest ("used in a trial") in the muted foreground. This also matches the Home changes list ("Changed FoundationOne Liquid CDx used in trial ...").
- **The detail heading has weak hierarchy.** "SuperARMS EGFR mutation detection" (~26px bold) is almost the size of the page H1 "Alerts". Drop it to the panel-heading size used on Review ("Rule from your rejection", ~20px). Alternatively, keep it and make the page H1 the only 28px element.
- **Item padding is off.** List items use 12px left padding, while the panel header uses 28px, so the eosin dots sit 16px inside the "Alerts" heading's left edge. Align the dot column with the heading icon, as Review does with its card left edge.

### Nice-to-have

- Show a thin elapsed-progress fill on the selected row's pause button, so the list and the player visibly link.
- Under "All", show seen alerts without the dot, in ink, so the eosin rule ("only what changed since you looked") is demonstrable in one tap.
- Add the stage track to list rows for stage-change alerts only (it is on Home's alert card), so the eosin segment appears in the list too.

---

## Jobs v1

### Must-fix

1. **"Agents working in parallel" does not read on camera.** The 16 in-progress trials are drawn as **hollow white squares with a 2px ink border** (`.c.run`), with no motion (the file has no `@keyframes`). Hollow reads as "empty / not started", so the grid looks like a half-filled progress chart, and the 16 concurrent agents are the least visible thing on the page. Make in-progress the most alive state:
   - Fill in-progress cells with ink-tint and add an animated diagonal sweep or a bottom-up fill showing the agent's step. Triage, extract and check could each take a third of the cell height. Keep the motion to one subtle loop, and use a static step fill under reduced motion.
   - Add a pulsing 6px dot (ink, **not** eosin) to the "Running" pill so motion carries to the header too.
   - For the video, consider a compact "16 agents" strip above the grid: 16 narrow lanes, each with the trial's NCT ID in mono and its current step (Triage / Extract / Check), like a build log. A viewer gets "16 things at once" in under a second. The grid then becomes the overview of all 40.
2. **In-progress and waiting look alike.** The `.c.run` (2px ink border) and `.c.wait` (1px grey border) cells differ only by border weight, and the single waiting cell at the end looks like a rendering glitch. Once in-progress is filled and animated (point 1) this resolves. Make waiting the faintest state: ink-tint at 40%, no border.
3. **The failed state is drawn in amber hatching.** `--low` (#9A6512) is the low-confidence colour in Review. Reusing it for "Failed" muddies two meanings. The spec says red is for errors and rejection. Use the error red for the failed cell, the bar segment and the circle-x icon, or keep amber and rename the state so it does not say "failed". Keep the hatching, since it helps colour-blind viewers.
4. **The payoff is buried.** "4 proposed changes filed so far." is muted 13.5px text bottom-left, but it is the result the job exists to produce, and the thing that links to Review. Promote it into the counts row as a fifth stat ("4 Proposed changes", linked to Review). The "Running for / Updates every" text can then drop under the progress bar.

### Should-fix

- **The legend is duplicated.** The counts row already carries a swatch for each state, and then the legend under the grid repeats them. Keep one legend. The counts row is better, but it needs to include Waiting.
- **The "Start a job" heading icon reads as a disclosure caret.** The solid ▶ before the heading looks like a collapsed accordion. Use lucide `play` at 1.75px stroke, the outline version like the other heading icons, or `circle-play`.
- **The Earlier jobs meta wraps badly.** "Set recent_baseline_narrow, 293 trials, 10:20" breaks the mono identifier across lines, and the two rows phrase their meta differently ("150 most recent of set small, 11:12"). Use one pattern, "`recent_baseline_narrow`, 293 trials, started 10:20", and either let the Job column take the extra width or move the time into its own column.
- **"Running for 3 min 40 s" is grey caption text floating at the far right of the counts row.** It is detached from everything else. Put it under the progress bar on the left: "22 of 40 done, running for 3 min 40 s, updates every 2 seconds".
- **The disabled Start job button competes.** The greyed lavender button is still a large saturated block in the right panel. Make it a quieter disabled style (white with a muted border), so the eye stays on the live job.
- **The mono set name is in the subtitle.** "narrow" in mono inside a sentence-weight heading looks like a typo at video resolution. Either keep the mono and add the word "set" before it ("set `narrow`"), or write it in plain words ("held-back narrow set").

### Nice-to-have

- Advance the bar and grid during the take. Even a scripted tick every 2 s for the eight seconds the page is on screen sells "live" more than any static styling.
- Hovering a cell shows its NCT ID. For the video, pin one tooltip open on an in-progress cell ("NCT06422546, extracting") so it reads as real trials, not abstract squares.
- The data-sources footer appears here. Make sure Alerts, Review and Home show it in the same place, or none of them do.

---

## Consistency checklist

| Check | Alerts v1 | Jobs v1 |
|---|---|---|
| Top bar, logo, nav icons, active pill | Pass | Pass |
| 7/5 split, right panel at x≈850 | **Fail** (x=658) | Pass |
| Page H1 with inline icon, same size as Review | Pass | Pass (Running pill fine) |
| Serif only for quotes | Pass | Pass (no quotes) |
| Mono only for identifiers | **Fail** (timecode) | Borderline (set name in heading) |
| Eosin only for new/changed | Pass, but overused as a stripe | Pass (no eosin, correct) |
| No ALL-CAPS eyebrows, arrows or middle-dot meta | Pass | Pass |
| Card soup | Pass | Pass (two stacked right panels, fine) |
| Empty space | **~360px dead area bottom-right** | Fine |
| Selected state matches Review | **Fail** | n/a |
| Numbers consistent with Home/Review | **Fail** (badge 5 vs 2) | Pass (Review 7 and Alerts 5 badges; align Alerts with the chosen number) |

---

## Round 2: Alerts v2 and Jobs v2

Reviewed: `shots/alerts-v2.png`, `alerts-v2-900.png`, `jobs-v2.png`, `jobs-v2-900.png`, and the sources `key-alerts.html` and `key-jobs.html`. The settled decisions are respected and not re-raised: no lane animation and no pulsing dot, lanes come from `active` and there is no per-trial grid, and nav order is handled in the global pass.

### Verdicts

| Page | Verdict |
|---|---|
| Alerts v2 | **Fix then ship**. Two small items are left, and one of them lives in the Home and Review files. |
| Jobs v2 | **Ship**. Only should-fix items are left. |

### Alerts: round-1 must-fix status

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Column split 7/5, right panel at x=850 | **Fixed** | The list ends at x=824 and the detail starts at x=850, which matches Review and Jobs. |
| 2 | Dead area under the detail panel | **Partly fixed** | The panel is now `position: sticky`, and it has a before/after line ("Changed from clinical validation"). It still ends at y≈612, though. In the 900px frame that leaves about 290px of empty tissue field beside a full list, and the static hero shot still shows a short card next to a long column. |
| 3 | Alert count consistent across pages | **Not fixed** | Alerts shows a badge of 5 and "5 new". `key-home.html` and `key-review.html` still show an **Alerts badge of 2**, while Home's own panel says "5 changes". A 2 that turns into a 5 is still visible on the cut from Home or Review to Alerts. (Jobs shows Review 4 and Alerts 1 mid-run. That is documented as climbing during the run, and it is fine as long as Jobs comes before Alerts in the video.) |
| 4 | Timecode not in mono | **Fixed** | `.player .time` uses the sans with tabular numerals. The slashed zero comes from Atkinson Next itself. |
| 5 | Selected row matches Review | **Fixed** | The selected row is a lifted card with an ink left bar. |

The round-1 should-fix items are mostly done. The play buttons now have labels, the eosin text is cut down to "New" with the rest muted, the detail heading is dropped to panel size, and the audio-error state moved to its own frame.

### Alerts: new or remaining must-fix

1. **Make the Alerts badge the same everywhere (5).** Change `Alerts <span class="count">2` to 5 in `key-home.html` and `key-review.html`, or fold this into the global top-bar pass. Do it before any recording.
2. **Fill the detail panel to about the list's visible height.** Add real content under the Evidence. Two options:
   - a second Evidence item: the earlier source that set "Clinical validation", with its date, so the before and after are both cited;
   - a short "Also changed for this diagnostic" line that links to the 13 Nov 14:15 row.

   Either one adds about 150–200px and closes most of the gap in the 900px frame. Do not add filler.

### Alerts: should-fix (new)

- The **"Loading" button on row 3** is a second transient state in the hero frame. It reads as stuck. Show Play there instead, and keep Loading for its own state frame, the same way the error state was handled.
- The detail meta line "New Update, moved to clinical utility 13 November 2026, 14:16" runs the date straight into the label. Put the date on the right, as the list rows do, or give it its own line in muted text.

### Jobs: round-1 must-fix status

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Parallel agents do not read on camera | **Fixed** (within settled decisions) | The "Agents working now" block shows 16 lanes, each with an NCT ID in mono and a 1/2/3-segment step bar labelled Triage, Extract or Check. It reads as "16 at once" in under a second, with no motion. |
| 2 | In-progress and waiting look alike | **Fixed** | The strip no longer has in-progress cells. Done is solid ink, Early research is a tint with an ink edge, Failed is red hatching, and to-go cells are white with a faint edge. The four states are clearly different. |
| 3 | Failed drawn in amber | **Fixed** | Failed uses `--error` #C42B1C hatching, and the failure line uses a red circle-x icon. Amber is back to meaning low confidence only. |
| 4 | Payoff buried | **Fixed** | "4 Proposed changes filed" is now the fourth stat and is linked. "Open review" is the primary button. |

The round-1 should-fix items are done as well. There is one legend (in the counts row, plus "17 to go"), the heading icon is the outline circle-play, the subtitle says "set `narrow.heldback`", the elapsed time sits under the bar, and the disabled Start job button is now quiet.

### Jobs: new must-fix

None.

### Jobs: should-fix (new or remaining)

- **The counts mix two kinds of number.** "22 of 40 Done", "3 Early research" and "1 Failed" are set as equal siblings. In the strip, though, the 3 Early research are part of the 22 done, while the failed one is counted separately (19 + 3 + 1 + 17 = 40). A pharma viewer who adds them up gets 26. Change the label to "3 of them Early research", or nest it under Done.
- **The baseline in the failure line is off.** The mono `clinicaltrials.gov:NCT05257967` sits about 3px below "1 failed:", because `.head` is an inline-flex. Align the two to the same baseline.
- **Earlier jobs meta still wraps.** The pattern is now unified, but "started 10:20" still drops onto its own line under `recent_baseline_narrow`. Shorten it to "293 trials, 10:20", or let the Job column take more of the width.
