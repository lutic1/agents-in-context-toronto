# UX review: Alerts v1 and Jobs v1

Reviewer: senior UX (subagent), 13 November 2026.
Inputs: `shots/alerts-v1.png`, `shots/jobs-v1.png`, `key-alerts.html`, `key-jobs.html`; `EXPERIENCE.md`, `DESIGN.md`; Stories 1.7, 1.8, 3.1, 3.2, 3.4, 3.5; AD-14 in `ARCHITECTURE-SPINE.md`; consistency against `key-home.html` (v7), `key-review.html` (v5), `key-graph.html` (v4); trial text from `data/clinicaltrials/heldback.jsonl` and `manifest.json`.

## Verdicts

| Page | Verdict | One line |
|---|---|---|
| Alerts | **Fix then ship** | Layout, voice and the audio states are right. But the `why` line doesn't name the Team's interest (Flow 1 step 4), and the detail panel shows fields the `Alert` shape doesn't carry. |
| Jobs | **Fix then ship** | A strong Flow 1 step 1 page. The per-trial grid, the "In progress" count, the times and the trace link have no API source. The live region also reads the clock aloud every 2 seconds. |

Neither page needs a rework. Both fit 1440 × 1000. Jobs fits down to its footer. On Alerts, the fifth row ends at about y 968 and the footer sits below the fold, which is acceptable.

---

## Alerts

### What works
- The list-and-detail layout reads in one glance. Each row shows its kind ("First seen" / "Update:") and its trigger in words, as the Alert item pattern asks, and the Early research badge appears on the MRD approach.
- The header copy, "5 new since your last visit on 2 November", follows Voice and Tone exactly.
- The audio states are well handled. Playing shows a real pause button with an `aria-label` and a progress bar. The error row says "Couldn't load the briefing. The alert text is above. Try again" in amber with a warning icon, so colour is not the only signal, and the row's `why` line stays readable. Nothing autoplays: the mock shows playback after Rowan pressed play.
- The detail panel carries everything Rowan needs. The stage track uses an eosin segment plus the words "Changed from clinical validation". The Evidence quote is in serif with "ClinicalTrials.gov, NCT06422546, data as of 12 November 2026". "Open Record" and "Show in the graph" hand off to Flow 1 step 5.
- The data matches the other screens. All five Alerts match Home v7's five changes in name, trigger, date and order. The detail quote is word for word from NCT06422546 and matches Home and Graph. The `why` lines are accurate to the trial text (I checked NCT04769388 for "persistence ctDNA EGFRm by SuperARMS at 3 weeks" and NCT04712877 for FoundationOne CDx plus FoundationOne Liquid as interventions, with 12 drivers).
- No PubMed text appears anywhere.
- The MongoDB tag is omitted, which is correct: the Change streams tag shows only if the long-poll is built.
- Contrast passes: `eosin-text` on the selected row's ink-tint is about 4.6:1, and `muted` on ink-tint about 5:1.

### Must-fix
1. **Make the `why` line name the Team's interest.** Story 3.1 asks for one `why` line "naming the Team's matching interest and the change". Flow 1 step 4 says "The why line names their interest in EGFR". The mock splits this across two lines:
   - The `why` line itself is change-only: "A real-world study now uses…".
   - The interest sits in a separate caption: "Why this matters to your team: it is a ctDNA test for EGFR, both in your profile."
   
   The web app composes that caption itself, which breaks AD-6 / Foundation ("applies no display rule of its own").
   
   **Fix:** show the API's single `why` verbatim in both the row and the detail, for example "Your team follows plasma EGFR testing: a real-world study now uses SuperARMS to track response to osimertinib." Delete the `.why-cap` line.
2. **Close the gap between the detail panel and the `Alert` shape.** AD-14 defines `Alert { id, team_id, diagnostic_id, kind, trigger, why, early_research, seq, at, dismissed }`. That shape has none of these, which the mock shows:
   - the Diagnostic name;
   - the current stage;
   - the previous stage ("Changed from clinical validation");
   - the Evidence quote, source, identifier and data date.
   
   Story 3.1 also says each Alert "links to the Evidence", yet there is no field for it. Fetching each Record and guessing which value triggered the Alert is a client-side display rule.
   
   **Fix:** pick one option and record it.
   - (a) Ask the architect to add `diagnostic_name`, `lifecycle_stage`, `from_stage` (stage advance only) and `evidence` (`quote`, `source`, `source_id`, `url`, `data_as_of`), or a `value_id`, to `Alert` in AD-14 and Story 3.1. This is the preferred option: it is cheap, and the alert is created right where all of these are known.
   - (b) Reduce the detail to the `why` line, the name from the Record, and "Open Record".
3. **Fix the Alerts badge count on the other pages.** Story 3.1 says 5 is correct. MRD approach is created in this run, so it gets one first Alert and no update. Each of the four applied changes on existing Diagnostics carries `stage_advance` or `used_in_trial` on a profile match (ctDNA, EGFR, KRAS), so each raises its own update Alert. SuperARMS gets two because they are two changes with two derived IDs.

   Home v7, Review v5 and Graph v4 show "Alerts 2" in the top bar while Alerts shows 5 and the header says "5 new". Change Home, Review and Graph to **Alerts 5**. Home's "Alerts for your team" panel can still preview two, but add "See all 5 Alerts".
4. **Make the Alert dates match the run that raised them.** `Alert.at` is the creation time, and Alerts are raised only by a live run (Baseline raises none). The SuperARMS Alerts are dated "6 Nov" / "6 November 2026", yet their Evidence says "data as of 12 November 2026", and in the Jobs mock NCT06422546 and NCT04769388 are still in progress in the held-back live run. An Alert can't predate its data.

   **Fix:** date all five Alerts on the live-run day (for example "Today, 14:12" or "13 Nov"), and order them by `seq`. Make the same change on Home v7 ("6 Nov" rows) and Graph v4 ("moved to clinical utility, 6 November").

   Bonus for the video: once ordered by `seq`, the SuperARMS stage-advance Alert can sit at the top. It is now fourth, and at the spine's 1440 × 900 at 110% recording size it falls below the fold.

### Should-fix
- **Add the loading state** (Story 3.5 AC: "with a loading state"). The mock shows playing and failed but not loading. Specify it: the play button becomes a spinner with `aria-label="Loading briefing"`, the player title reads "Loading the briefing…", and the button is `aria-busy`. It should take under 2 seconds on a cached file.
- **Don't let the unread dot carry meaning alone.** It is `aria-hidden` and colour only. In the "All" view, nothing but the pink dot separates new from seen. Add the word "New" (visible or `sr-only`) per the Accessibility Floor rule "change has the word New/Changed".
- **Add the missing Alert item parts to the list rows.** The Alert item pattern lists a stage track and a dismiss control. The rows have neither, and dismiss exists only in the detail panel. Add a compact stage track under the name, and a small "Dismiss" ghost button beside play. It must stay always visible, not on hover.
- **Fix the filter semantics.** "New / All / Dismissed" uses `role="tablist"` / `role="tab"`, but there are no tabpanels and no arrow-key handling. Use a toggle group (`aria-pressed`) or radio buttons instead.
- **Define what the row does when activated.** The `h3` is a link to `#`. Specify that activating a row selects it, shows the detail and moves focus to the detail `h2`, and that "Open Record" is the route to `/diagnostics/[id]`. Otherwise keyboard users land somewhere unexpected.
- **Announce new arrivals.** The inbox refreshes from `GET /changes`, but nothing announces a new Alert. Add a polite live region, for example "1 new Alert for Thoracic oncology".
- **Show one player for one audio element.** The selected row's button shows pause and the detail player shows pause. Both are fine, but they must be bound to the same audio element. Playing a second Alert stops the first.
- **Check the stage-advance evidence.** NCT06422546 is a non-interventional, observational real-world study, which is arguably clinical validation. NCT04769388, a randomised trial that enrols on a SuperARMS result, is the stronger clinical-utility evidence. A domain judge may notice. Consider letting the stage advance cite NCT04769388 and the `used_in_trial` cite NCT06422546, and swap the two on Home, Graph and Review too.
- **Find a source for "since your last visit on 2 November".** `Team` has `last_seen_seq` and no date. Either the API resolves the event's `at`, or the copy drops the date.

### Nice-to-have
- Make the progress bar a seekable slider (`role="slider"`) with 5-second skip keys.
- Put a "Play all new" control in the header. It runs on a user click only, so it is not autoplay.
- Show the Synthetic badge next to the Team name in the header subline as well, not only in the top bar.

---

## Jobs

### What works
- The page is an exact match for Flow 1 step 1. The header reads "Live run over the held-back ClinicalTrials.gov set narrow, 40 trials". The plain line "The agents read up to 16 trials at once; checks run on every value before it is filed" sells the parallelism to a judge.
- The counts add up:
  - 22 processed, of which 3 are Early research; 16 in progress; 1 failed; 1 waiting; 40 in total.
  - The bar widths are 55% and 2.5%, and the progressbar's `aria-valuenow` of 23 matches.
  - The 40 cell IDs are exactly `subsets.narrow.heldback` in manifest order.
  - Baseline CT.gov shows 288 + 5 = 293, matching `recent_baseline_narrow`.
- The failure handling matches Flow 1. The failure line reads "1 failed. The job carries on without it.", the failure row gives `clinicaltrials.gov:NCT05257967` plus the error, with no source text (Story 1.5). The job keeps running.
- The Job running state follows the spine. Start is disabled with "A job is running. Open it", matching State Patterns and Voice ("A job is already running. Open it").
- The Mode hint "Live files Proposed changes and raises Alerts for matching Teams" and the note "Baseline jobs raise no Alerts" teach the model in two lines.
- Colour is never the only signal. The cells and swatches use fill, outline, dashed and hatched patterns, and every cell has `sr-only` text.
- No PubMed text appears. The MongoDB tag is correctly omitted.

### Must-fix
1. **Find an API source for the per-trial grid, or replace it.** `GET /jobs/<id>` returns `Job { id, mode, source, set, status, counts { total, done, failed, early_research }, failures [ { source_ref, error } ] }` (AD-14, Story 1.7). It has no per-item state, so the 40 ID-labelled cells, their in-progress / waiting / Early research states and "Hover a cell for its trial ID" cannot be built. Pick one option:
   - (a) Ask the architect to add `items: [ { source_ref, state: waiting | running | done | failed, early_research } ]` to `Job`. The item node would write it at start and end. Update AD-14 and the Story 1.7 AC.
   - (b) Keep the tray as a **count-driven** strip with no IDs. Fill `done` cells, then `early_research` cells (dashed), then `failed` cells (hatched), then `total − done − failed` empty cells labelled "To go". Drop the "out of order" and "Hover a cell" copy.
   
   Option (b) costs nothing and keeps the visual that matters for the video.
2. **Remove or source the counts and labels that `Job` doesn't supply:**
   - "16 In progress" and "Waiting": `counts` has no running figure. Without (a) above, show "17 to go".
   - "Started by Sam at 14:06" and "Running for 3 min 40 s": `Job` has no `actor`, `started_at` or `updated_at`.
   - "4 proposed changes filed so far": `Job` has no count, and the Event has `run_id` but the Job doesn't expose one.
   - "Trace in LangSmith": no trace URL. This one can be a static project URL from an env var; say so in the spec.
   - Past-job times "11:12" and "10:20", and "Earlier jobs today": no timestamps.
   
   Either add `actor`, `started_at`, `finished_at`, `run_id` and `filed` to `Job` (cheap, and the same AD-14 change as item 1), or drop these from the mock. Recommend the AD-14 change: the elapsed time and the "filed so far" count both help the video.
3. **Stop the live region announcing every 2 seconds.** `aria-live="polite"` sits on the whole `.counts` block, which includes "Running for 3 min 40 s". A screen reader would announce the clock every 2 seconds.
   
   **Fix:** move the elapsed time out of the region. Put `aria-live="polite" aria-atomic="true"` on a single `sr-only` summary that changes only when a count changes, for example "22 of 40 processed, 1 failed, 3 Early research". Throttle it to at most one announcement per 10 seconds.
4. **Fix the past-jobs row that POST /jobs can't create.** "Baseline, PubMed: 150 most recent of set small" is not expressible, because POST /jobs takes `{ mode, source, set }` with no limit. Also, the PubMed `small` set has 626 + 24 items, not 150.
   
   **Fix:** use a real set name and its manifest count, for example `small_one_year`, 322 items, with Done 318 and Failed 4. Show the API's `set` string exactly, as the CT.gov row already does.
5. **Make the top-bar counts match the mid-run moment.** The Jobs top bar shows Review 7 and Alerts 5 while the page says "4 proposed changes filed so far". NCT06422546, NCT04769388, NCT04712877 and NCT07894458 are still in progress, yet the other mocks' Alerts and Review rows come from those trials.
   
   **Fix:** set the badges to **Review 4** and **Alerts 1**. The one Alert is the first-seen Alert for the MRD approach, because NCT07921888 is already done and is Early research. In the video the badges then visibly climb between step 1 and steps 2 and 4.

### Should-fix
- **Show the exact set name.** The header says set `narrow`, but the manifest set is `narrow.heldback` (with `narrow.baseline` alongside it). The Set picker says "Held-back, narrow". Show the exact `set` value the API takes in mono, as the past-jobs table does, so Sam's run is reproducible.
- **Hide "Dry run" from the Mode control.** Story 2.1's `dry_run` writes nothing and prints results to the console, so on this page it would start a job whose results Sam can never see. Remove it, or keep it behind the "More" menu with a hint, "Prints matches to the job log; files nothing". Two choices are also easier on camera.
- **Make the trial IDs reachable without hover** (only if grid option (a) is kept). "Hover a cell for its trial ID" is hover-only, which Interaction Primitives bans, and the `li` cells are not focusable. Make each cell focusable (roving tabindex) with a visible tooltip on focus, or list the in-progress IDs in text.
- **Make "Waiting" look different from "In progress"** (only if the grid is kept). The only difference is a 2px dark border against a 1px light one, which is near-identical at video compression. Give waiting cells a dotted border or a lighter fill.
- **Source the failure copy.** "The model was overloaded after three retries (529). Start the job again to retry this trial." should come from a web-side map of the error codes in `failures[].error`, for example overloaded, rate_limited, refusal and parse_error, with the raw message as fallback. Note this in the spec so the backend doesn't hand-write user copy.
- **Account for the PubMed proposals.** Review v5 shows PubMed proposals (PMIDs, data as of 13 November). Baseline mode applies changes as unreviewed and never as pending, so those proposals need a live PubMed job, and the past-jobs list doesn't have one. Add a "Live, PubMed" row, or drop the PubMed rows from Review.
- **Show who is working.** Sam is the user, but the Team picker says "Thoracic oncology", which is Rowan's Team. Flow 3 puts Sam in a curation Team. This doesn't matter for Jobs, which aren't Team-scoped, but on camera the avatar switch from Sam to Rowan is the only cue that the viewer changed.

### Nice-to-have
- Keep the Job stalled state ready, since it is part of the spec: "No progress for 10 minutes. Start it again to resume." with a Start button.
- When the job finishes, swap "Running" for "Finished" and make "Open review" the single primary action. Use no celebratory animation, which the spine bans.
- If the long-poll from Story 1.1 is built, add the Change streams tag to the counter panel, worded "New results appear as the database changes."

---

## Cross-page notes, outside these two pages
- The spine's top bar includes **Categories**. All v7-system mocks use "More" instead. Either update the IA line in EXPERIENCE.md or show Categories.
- Demo on Camera assumes 1440 × 900 at 110% zoom, about 745 CSS px of content height. Jobs keeps its counter, failure and "Open review" above that line. On Alerts, the detail panel fits but rows 4 and 5 don't, which must-fix 4 (ordering by `seq`) solves.

---

## Round 2

Reviewer: senior UX (subagent), 13 November 2026.
Inputs: `shots/alerts-v2.png`, `alerts-v2-900.png`, `jobs-v2.png`, `jobs-v2-900.png`; `key-alerts.html`, `key-jobs.html`; `shared-story.md` (wins); Stories 1.7, 1.8, 3.1, 3.2, 3.5 as updated (`Job` with limit, actor, started_at, finished_at, counts.filed, active; `Alert` with diagnostic_name, lifecycle_stage, from_stage and Evidence). Settled and not re-raised: stage-advance Evidence stays NCT06422546; top-bar order is fixed globally later.

### Verdicts

| Page | Verdict | One line |
|---|---|---|
| Alerts | **Ship after two small fixes** | Every round-1 must-fix on this page is done. Two leftovers: the mock shows two audio states at once, and the "last visit" date has no field. Other pages still show "Alerts 2". |
| Jobs | **Ship after two copy fixes** | The new `Job` fields now support every figure on the page, and the "Agents working now" list is a better video moment than the grid was. The past-jobs panel contradicts the shared timeline, and one set name could swallow the held-back items. |

Both pages fit 1440 × 900: on Jobs the counter, the agents list, the failure and "Open review" are above the line; on Alerts the top four rows and the whole detail panel are.

### Round-1 must-fix status

**Alerts**

| # | Item | Status | Note |
|---|---|---|---|
| 1 | `why` names the Team's interest | **Fixed** | Each row and the detail show one `why` line, word for word the same, starting "Your team follows…". The `.why-cap` caption is gone, and the header note says the line is shown verbatim. |
| 2 | Detail panel vs `Alert` shape | **Fixed** | Story 3.1 now carries `diagnostic_name`, `lifecycle_stage`, `from_stage` and Evidence (quote, source, link, data date). Every element in the detail maps to a field. "Show in the graph" uses `diagnostic_id`. |
| 3 | Alerts badge count on other pages | **Partly** | Alerts, Diagnostics and Record show 5, and Jobs shows 1. Home, Graph, Review, Find, Categories, Rules and Terms still show **Alerts 2**. |
| 4 | Alert dates match the run | **Partly** | Alerts is fixed: all five Alerts are dated 13 Nov between 14:09 and 14:16, newest first, and the stage advance is on top. That also lines up with Jobs: started 14:06, 3 min 40 s in, Alerts 1 (MRD at 14:09). `key-home.html` still has two "6 Nov" dates. |

**Jobs**

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Per-trial grid has no source | **Fixed** | The grid is now a count-driven strip (19 done + 3 Early research + 1 failed + 17 to go = 40). The in-progress IDs come from `active[{source_ref, step}]` as a readable list with no hover. |
| 2 | Counts and labels `Job` didn't supply | **Fixed** | "Started by Sam at 14:06" comes from `actor` and `started_at`. "Running for 3 min 40 s" is computed from `started_at`. "4 Proposed changes filed" comes from `counts.filed`. The LangSmith link is a static env URL and is noted in the source. Past-job times come from `started_at`. |
| 3 | Live region reads the clock | **Fixed** | A single `sr-only` region (`aria-live="polite" aria-atomic="true"`) holds counts only. The elapsed time sits outside it. Throttling to one announcement per 10 s still belongs in the spec. |
| 4 | Past-jobs row POST can't create | **Fixed, but see new J2** | `limit` now exists, so "150 most recent" can be expressed and 146 + 4 = 150. The set it runs on is the new problem. |
| 5 | Top-bar counts mid-run | **Fixed** | Review 4 and Alerts 1, as in `shared-story.md`. |

Round-1 should-fix items that are now done: the loading state, the visible word "New", stage tracks and Dismiss on each row, `aria-pressed` filters instead of tabs, row activation moving focus to the detail `h2`, a polite live region on Alerts, the exact set name `narrow.heldback`, Dry run removed, failure copy mapped from error codes. Still open as should-fix: the PubMed proposals on Review need a live PubMed job, and the Sam/Thoracic oncology Team picker on Jobs.

### New must-fix

**Alerts**

1. **Show one audio state at a time.** Row 1 shows Pause and the detail player shows "Playing the briefing", while row 3 shows Loading. The source says "One audio element: playing another Alert stops this one". Pressing play on row 3 would have reset row 1 to Play. A developer building from this mock, or a judge watching it, sees two briefings active at once.
   **Fix:** move the loading state into its own frame, as was done for the error state, and set row 3 back to Play. Or show the loading state on row 1 and the detail player ("Loading the briefing…", `aria-busy`) instead of playing.
2. **Drop the date from "since your last visit on 12 November", or give it a source.** `Team` has `last_seen_seq` and no timestamp, and `GET /alerts` doesn't return one (this was round-1 should-fix; under the rule "show nothing the API can't supply" it now counts as must-fix).
   **Fix:** write "5 new since your last visit, for Thoracic oncology: ctDNA testing, EGFR and KRAS". Or add `last_seen_at` to the Team, written by `POST /teams/<id>/seen`, and note that in Story 5.1.

**Cross-page (carried over from round-1 items 3 and 4)**

3. Set **Alerts 5** in the top bar of `key-home`, `key-graph`, `key-review`, `key-find`, `key-categories`, `key-rules` and `key-terms`. Replace the two "6 Nov" dates in `key-home.html` with 13 Nov times that match the Alerts page (14:16 and 14:15 for the two newest).

**Jobs**

4. **Date the earlier jobs correctly ("Earlier jobs today").** `shared-story.md` puts the Baseline load on 8 Nov, and the live run is on 13 Nov. Both rows say "started 11:12" and "started 10:20" under "Earlier jobs today", which says the Baseline ran this morning. That contradicts Home and Record, where Sam accepted the Baseline values on 9 Nov.
   **Fix:** retitle the panel "Earlier jobs" and write "started 8 Nov, 10:20" and "started 8 Nov, 11:12", from `started_at`.
5. **Name a Baseline-only set on the PubMed row.** "`small`, 150 most recent" is ambiguous. The PubMed manifest's `small` has `baseline` (626) and `heldback` (24) halves, and the held-back items are by definition the most recent. A Baseline over the 150 most recent of the whole set would load the held-back items as Unreviewed and empty the live run. The CT.gov row already names a baseline-only set (`recent_baseline_narrow`).
   **Fix:** show `small.baseline`, 150 most recent (or `small_one_year`, 322 items, as in round 1), with Done and Failed adding up to that total. Show whatever exact `set` string the API takes.

### Should-fix (new, brief)
- On Jobs, hide "Trace in LangSmith" for `pubmed` jobs, because Story 1.7 turns tracing off for them. Note this in the source comment.
- On Alerts, announce through the live region only when something new arrives, for example "1 new Alert for Thoracic oncology", not "5 new Alerts" on page load. The current static text would be read on load.
