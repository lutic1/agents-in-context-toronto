# UX review: Diagnostics list and Record (v1)

Reviewed: `shots/diagnostics-v1.png`, `shots/record-v1.png`, `shots/record-v1-full.png`, `key-diagnostics.html`, `key-record.html`, against EXPERIENCE.md, DESIGN.md, Stories 1.2, 1.3, 2.3, 2.5 and 4.7, AD-2, AD-4, AD-5, AD-6 and AD-14. I checked the data against `data/fda/assays.json`, `data/fda/cdx_lung.jsonl`, `data/clinicaltrials/*.jsonl` and the Home, Review and Graph mocks.

## Verdicts

| Page | Verdict | Why |
|---|---|---|
| Diagnostics (`/diagnostics`) | **Fix, then ship** | The layout, stage tracks, Early research badge, "Stage not determined" and "No data for this indication" are right. But three controls show data the API contract cannot supply: the total count, the "Latest evidence" column with its sort, and "Early research only". One active filter also contradicts a visible row. |
| Record (`/diagnostics/[id]`) | **Fix, then ship** | The structure is strong: inline review of the Unreviewed value, history newest first with who and when, a manual value, and the pending proposal in the right-hand rail. But six values on the page have no quote, and two state lines ("Set by rule", "Filed … by the Baseline load") come from fields the API does not have. All of these fixes are small. |

The data is real and consistent. Every quote I checked appears word for word in its Source item's `raw_text`, including NCT04624373, NCT04712877, NCT04591431 and P190032/S015. P190032/S015 is tepotinib with a decision on 14 Nov 2024. The FDA "data as of 3 November 2026" date matches `page_content_current_as_of`. FoundationOne Liquid CDx shows ALK, BRAF, EGFR, MET and ROS1 with eight drugs, which matches the FDA rows. Neither page shows PubMed abstract text. All quotes are well under 300 characters.

## The three questions

### 1. Omitted serif quote and "Set by rule": does it break "never a value without Evidence"?

**Yes, on both counts.**

- EXPERIENCE.md, Evidence Display Rules: "The quote, source name, identifier link and 'data as of' date travel together." The Evidence quote pattern says "Never shows a value without it." A source line on its own is a citation without the quote.
- AD-6 says the web app applies no display rule of its own. Hiding the quote when it repeats the value is a display rule the web invented. AD-2 evidence always carries `quote` (`{ source_ref, source, source_url, source_date, quote }`), so the API sends one and the screen must show it.
- "Set by rule" is not a review state. AD-2 allows `review: unreviewed | accepted | edited | manual`. Under Story 1.2 the seed applies every value, including `lifecycle_stage: regulatory_approval`, as `unreviewed`. The mock therefore hides two Unreviewed values. The header count should read 3 unreviewed, not 1, unless Sam has accepted them.
- On camera, the argument is "every value has a quote". The first two rows of the Record are exactly where a judge looks, and they have no serif.

**Recommended treatment.** Every non-manual value gets its serif quote, its source line and its real review state. The FDA list quotes are short, so the cost is about 28px per row. Quotes taken from the P190032 `raw_text`:

| Field | Value | Serif quote | State line |
|---|---|---|---|
| Lifecycle stage | Regulatory approval | `P190032 (08/26/2020)` | "Unreviewed" with Accept / Edit / Reject, or "Accepted by Sam, 9 Nov 2026" |
| Regulatory status | FDA approved, PMA | `P190032 (08/26/2020)` | same |
| Provider | Foundation Medicine, Inc. | `FoundationOne Liquid CDx (Foundation Medicine, Inc.)` | Accepted by Sam, 9 Nov 2026 |
| Sample types | Plasma | `Non-Small Cell Lung Cancer (NSCLC) - Plasma` | Accepted by Sam, 9 Nov 2026 |

- Drop "Word for word from …". The serif already says "these are the source's words".
- To keep "by rule" provenance, it needs an API field, such as the value's `mode`/origin or `evidence.by_rule`. Without one, drop the phrase. The FDA list as the source already explains it.
- Use the "since 26 August 2020" in the header only if it comes from the stage value's `evidence.source_date`. It can.

### 2. Can the API supply everything shown?

Not everything. AD-14 gives `GET /diagnostics?<facet>=&q=` → `{ items: Record[], next }`. `Record` has `id, name, lifecycle_stage, early_research, created_mode, rev, synthetic, fields{values, no_data}`. The AD-2 Value has `decided_by`, `decided_at` and `proposal_id`, but no filed date, no mode and no reason.

| Shown | Supplied? | Fix |
|---|---|---|
| "23 lung cancer diagnostics tracked", "Showing 10 of 23" | No. There is no total. | Add `total` to the list response, or reword without a number ("10 shown"). |
| "Latest evidence" column and its sort | No. There is no such field and no `sort` param. Computing a max over every value's date on the client is a display rule, and the sort would only cover the current page. | Add `latest_evidence { date, source, source_ref }` and `sort=latest` to AD-14, or replace the column with an API-backed one (Regulatory status, or the Trials count) and sort by name. |
| Date meaning in that column | Mixed. CT.gov rows use the trial's `last_update_posted` (NCT04624373 shows 3 Apr 2025). FDA rows use the list's data-as-of date (3 Nov 2026), not a decision date. | If kept, define it as `evidence.source_date` everywhere. FDA rows then show their latest decision date, which changes the order. |
| Modality, Sample, Stage filters | Yes, as facets (`lifecycle_stage` is a field). | Specify how several values in one param combine (Plasma OR Tissue). |
| "Early research only" | No. `early_research` is computed and is not a facet. Filtering on two stage values would be a web rule. | Add an `early_research=true` param, or remove the toggle. |
| "Filter by name, provider or biomarker" | Yes, through `q`. | None. |
| Previous / Next page | Next yes; Previous only if the client keeps a stack of cursors. | Keep a cursor stack, or show Next only. |
| "Approach, no named assay" subline | No field. The web infers it from a missing provider. | Drop it (the name already says "(approach)"), or render the provider field's no-data state. |
| Record: values, quotes, history counts, unreviewed count, manual submitter and note | Yes. | None. |
| "Set by rule, 8 Nov 2026" | No. | See question 1. |
| "Filed Unreviewed by the Baseline load, 8 Nov 2026", "added 13 Nov 2026", "Added by Rowan, 11 Nov 2026" | No `filed_at` or `mode` on a Value. | Add `filed_at` and `mode` to the Value entry (AD-2), or drop the phrases. |
| "Reason: Tested once at progression…" on a rejected value | No `reason` on a Value. Only a Proposal has one. Rejecting an unreviewed value through `review_value()` loses it. | Add `reason` to the Value entry. Story 2.3 already requires a reason on reject. |
| "Waiting for review" rail and the pending item in History | `GET /proposals?status=&field=` has no `diagnostic_id` filter, and a Proposal has no created date. | Add `diagnostic_id` to `/proposals` (or embed pending proposals in `GET /diagnostics/<id>`), plus `created_at` on Proposal. |

These are small contract additions, but they change AD-2 and AD-14. Agree them with the API lane (Story 1.1 generates the types) before the WEB stories start.

### 3. Gendered pronouns

**None found.** I searched the visible text of both pages for he, she, his, her, him and hers; HER2 and HER1 do not match. The copy uses names only: "Accepted by Sam", "Rejected by Sam", "Added by Rowan", "Saved as Sam". Keep that rule in the toasts and the history strings when they are built.

## Must-fix

**Diagnostics**

1. **Active filter contradicts a row.** "Sample: Plasma, Tissue" is on, yet the EBUS-TBNA row (sample "EBUS-TBNA supernatant") is listed. Either turn the chip off or remove that row. If it stays, confirm "EBUS-TBNA supernatant" and "cfDNA NGS panel" are registry enum values; they are the only ones that differ from the rest.
2. **"Latest evidence" column and sort.** The API cannot supply this, and the dates mean different things on different rows (see question 2). Replace it with an API-backed column, or add `latest_evidence` and `sort` to AD-14 and use `source_date` throughout.
3. **Counts.** "23 tracked" and "Showing 10 of 23" need `total` in the list response, or a rewording. Also reconcile with the Graph mock's "Graph of 13 lung cancer diagnostics". If the Graph is scoped to the Team, say so there. Otherwise use one number on every page. The FDA data alone gives 20 assays, so 23 is plausible.
4. **"Early research only."** Add an `early_research` param or remove the toggle. Every control on the page must map to a contract parameter.

**Record**

5. **Lifecycle stage and Regulatory status.** Show the serif quote (`P190032 (08/26/2020)`). Replace "Set by rule" with the API review state. If they are Unreviewed, show the tag and inline Accept / Edit / Reject, and update the header count.
6. **Provider and Sample types.** Show the serif quote. Remove "Word for word from".
7. **Linked drugs.** Seven accepted drugs have no way to reach their Evidence. Use the same pattern as Biomarkers and Trials: one chip selected and its quote below. For example, osimertinib → `Tagrisso (osimertinib) NDA 208065`, P190032/S008.
8. **Chips must be buttons.** Biomarker, Trial and drug chips are the only path to most Evidence. They are `<span aria-pressed>`, which cannot be reached by keyboard. Make them `<button aria-pressed>` with the accessible name "Show Evidence for EGFR". Add one caption line: "Select a value to see its Evidence".
9. **Copy that needs missing fields.** This covers "Filed Unreviewed by the Baseline load, 8 Nov", "added 13 Nov", "proposed 13 Nov 2026 by the live run", "Added by Rowan, 11 Nov", the rejection "Reason:" and the per-Diagnostic pending proposal. Add `filed_at`, `mode` and `reason` to the Value entry, a `diagnostic_id` filter and `created_at` to Proposals. Otherwise cut the copy. Decide this before building.
10. **The History entry for the current value has no quote.** The "Companion diagnostic" entry repeats the current value with a source line only. Either remove the current value from History (EXPERIENCE says History lists superseded and rejected values) and put "filed by the Baseline load, 8 Nov" in the current value's state line, or show its quote.

## Should-fix

- **The Clinical use quote does not support its value.** "Companion diagnostic" is backed by `Exon 19 deletion or exon 21 L858R substitution mutation`, which says nothing about clinical use; the check requires `supported`. Use the drug line instead: `Tagrisso (osimertinib) NDA 208065`. The same quote also appears under EGFR, so it reads as copy-paste.
- **FDA identifiers link to `#`.** Link P190032 and P190032/S008 to the PMA database records (`extra.record_links`) or to `source_url`, as the NCT links do.
- **Pending proposal inside History.** "Treatment selection — Waiting for review" is not a historical value. Keep it in the rail only, or give it its own "Waiting" sub-heading above History. It is also counted in "History (3)".
- **Reviewer buttons.** Give Accept, Edit and Reject accessible names that carry the value and field ("Accept tepotinib in Linked drugs"). Reject should be the outline variant that turns destructive on hover and focus (DESIGN.md), not ghost. Show the state after Edit or Reject is pressed: inline field, required reason, then the toast "Accepted", "Edited" or "Rejected".
- **Add a value form.** The Value control should follow the field type from `GET /schema`: a select for enum fields and free text for Study results. Mark "Where this comes from" as required. Use real `<label for>` and input pairs. Pre-selecting "Study results", the empty field, is a good touch.
- **Loading state.** Story 1.3 requires "no data" to be visibly different from loading. Add one Skeleton frame, or an annotation, for the list and the Record so the builder does not reuse the no-data text.
- **"Approach, no named assay" subline** is not from the API. Drop it.
- **Pagination.** Previous needs a client-side cursor stack (the API only returns `next`). Either commit to that or show Next only.
- **Diagnostics accessibility.** Make the "Latest evidence" header a button inside `th[aria-sort]`. "Early research only" needs `aria-pressed`. The search and filters need to be real inputs and selects with labels.
- **Nav counts** "7" and "2" need accessible text ("7 waiting for review", "2 new Alerts"). Across pages, the Alerts page shows 5 while this top bar shows 2, so pick one. The top bar is missing Categories (EXPERIENCE IA); it may sit under "More", but confirm.
- **Rail width** is 436px; DESIGN.md says 360px for the right-hand panel. Change one or the other.
- **For the video.** At 1440×1000 the Unreviewed tepotinib box starts at the fold. At the recording setting of 1440×900 at 110% it is well below. The header link "1 unreviewed value" jumps to it, so script that click. Alternatively, move unreviewed values into a short "Needs review" strip under the header.

## Nice-to-have

- A stage track tooltip naming all nine stages and the date each was reached (Component Patterns). This needs the stage history dates, which Story 2.5 already provides.
- A "Changed" mark (eosin dot plus the word) on list rows and Record values changed since the Team's `last_seen_seq`. Home already lists FoundationOne Liquid CDx as changed on 12 Nov. This needs `seq` on the Record or the Value.
- A Trials count column on the list (it is in the Record), which is a strong signal for Rowan.
- "Open in graph" should open the Graph focused on this Diagnostic (`?focus=`).
- The header subline ("Foundation Medicine, Inc., plasma ctDNA NGS panel") is built from three values. That is fine, but make it link down to those fields.

## Acceptance criteria check

| Story / criterion | Status |
|---|---|
| 1.3: name, stage, Early research label, "stage not determined" | Met |
| 1.3: each value with quote, source, link and data date | Not met: Lifecycle stage, Regulatory status, Provider, Sample types, seven Linked drugs, and the current entry in History |
| 1.3: unreviewed values marked | Met for tepotinib. The two seeded values shown as "Set by rule" should be Unreviewed |
| 1.3: empty field shows "no data", different from loading | No-data met; loading not shown |
| 1.3: renders only what the read model returns | Not met: "Latest evidence", the "Set by rule" and "Word for word" rules, the approach subline |
| 1.3: footer credits, "your name" picker | Met |
| 2.3: inline review of unreviewed values | Buttons present; reason-required states not shown |
| 2.5: history newest first, with quote, source, data date, state, who and when | Met (13 → 10 → 9 Nov, names and dates shown), except the current entry has no quote and the rejection reason has no API field |
| 2.5: Lifecycle stage history with dates | Collapsed; nothing contradicts it |
| 4.7: Add value form; shown as "Manually sourced" with submitter and note | Met. The Value control should follow the field type |
| Voice: "No data for this indication", "Stage not determined", Accept / Edit / Reject | Met |
| Accessibility floor | Partial: stage track `role=img` labels are good; chips, sort header, toggle, reviewer button names and form labels need the fixes above |
| No PubMed abstract text; quotes at most 300 characters | Met |
| Fits 1440×1000 | Diagnostics fits, with the pager at about 960px. The Record scrolls by nature; the key moment sits at the fold (see the video note) |

---

# Round 2 (v2)

Reviewed: `shots/diagnostics-v2.png`, `shots/record-v2.png`, `shots/record-v2-full.png`, `key-diagnostics.html`, `key-record.html`, against EXPERIENCE.md, `shared-story.md`, Stories 1.2, 1.3, 2.2 (now with `diagnostic_id=`), 2.3, 2.5 (now with the reason on the value entry) and 4.7. I checked every quote on the Record against `data/` again; all ten appear word for word in their Source item's `raw_text`, and the new Regulatory status quote `P200006 (10/26/2020)` is a real FoundationOne Liquid CDx row (Alecensa, decided 26 Oct 2020).

## Verdicts

| Page | Verdict | Why |
|---|---|---|
| Diagnostics | **Ship** | All four round-1 must-fixes are fixed. Every control now maps to an AD-14 parameter. One small contract note remains (sort order). |
| Record | **Ship after one small fix** | Every round-1 must-fix is fixed. Every non-manual value now carries its serif quote, source line and a real review state. One new must-fix: two baseline values say "Accepted 9 Nov" / "Rejected 10 Nov" above Evidence "data as of 12 Nov 2026", which reads as impossible on camera. |

## Round-1 must-fix status

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Active Sample filter contradicted the EBUS-TBNA row | **Fixed** | Filters now read "Any". "EBUS-TBNA supernatant" must still be a registry `sample_types` value (Story 4.8's Category map confirms `cfDNA NGS` and `ctDNA PCR` modalities exist). |
| 2 | "Latest evidence" column and sort | **Fixed** | Replaced by Regulatory status, which the API supplies. |
| 3 | Counts ("23 tracked", "Showing 10 of 23") | **Fixed** | Removed; the Graph count conflict is moot here. |
| 4 | "Early research only" toggle | **Fixed** | Removed; the badge stays in the row. |
| 5 | Lifecycle stage and Regulatory status quotes and "Set by rule" | **Fixed** | Both show the serif quote and "Accepted by Sam, 9 Nov 2026", matching the shared story. |
| 6 | Provider and Sample types quotes; drop "Word for word" | **Fixed** | |
| 7 | Linked drugs had no Evidence path | **Fixed** | Chips with one selected and its quote below, plus the caption "Select a value to see its Evidence". |
| 8 | Chips as buttons | **Fixed** | `<button aria-pressed>` with names such as "Show Evidence for EGFR in Biomarkers". |
| 9 | Copy needing missing fields | **Fixed** | "Filed … by the Baseline load", "added 13 Nov" and the proposal's date are gone. The rejection reason is now backed by Story 2.5; the rail is backed by Story 2.2's `diagnostic_id=`. "Added by Rowan, 11 Nov 2026" uses `decided_by` / `decided_at`, which a manual value has. |
| 10 | History entry for the current value | **Fixed** | History (1) holds only the rejected value, with its quote. The Clinical uses quote now supports its value (`Tagrisso (osimertinib) NDA 208065`). |

Round-1 should-fixes also landed: Reject is the outline-danger variant, the reviewer buttons carry the value and field in their names, the pending proposal left History, FDA identifiers link to the PMA database, the Add-a-value form labels the note as required and says fixed-choice fields show a list, and the pager shows Next only.

## New must-fix

1. **Record: Evidence dated after the decision.** Modality ("Accepted by Sam, 9 Nov 2026") and the rejected History entry ("Rejected by Sam, 10 Nov 2026") both cite ClinicalTrials.gov "data as of 12 Nov 2026". The shared story has the Baseline load on 8 Nov, so a judge reads a value accepted three days before its source data existed. The API would really send 12 Nov if `source_date` is the CT.gov dataset timestamp (`manifest.json` `source_data_timestamp` is 2026-11-12 for both windows). Cheapest consistent fix: define a CT.gov item's `evidence.source_date` as its `dates.last_update_posted`. Baseline trials then show their own earlier dates (NCT04624373: 3 Apr 2025; NCT04591431: 3 Oct 2023) and the held-back NCT04712877 still shows 12 Nov 2026, so the live-run values stay as they are. Put the rule in AD-2 so the Review and Find mocks use it too.

## Should-fix (new or still open)

- **"since 26 Aug 2020" in the header** is not obviously in the contract: the stage value's `source_date` is the FDA list's data date (3 Nov 2026), and parsing `(08/26/2020)` out of the quote would be a web display rule. Either carry the decision date on the Evidence (the FDA item has `dates.decision_dates`) or drop the phrase.
- **Diagnostics sort.** "Sorted by name, A to Z" plus a sort button in `th[aria-sort]` implies a toggle; AD-14 has no `sort` param and states no default order. Write "items ordered by name" into AD-14 and make the header plain text, not a button.
- **Nav counts** "7" and "5" still need accessible text ("7 waiting for review", "5 new Alerts").
- **Form controls in the mock** are `div`/`button` stand-ins with `label for` pointing at them. Fine for a picture; the build must use real `input`, `select` and `textarea`.
- **History button** should have `aria-controls` pointing at its section.

## The Unreviewed tepotinib value about 1,800px down

**Acceptable for the demo, on three conditions.** Moving it into a "Needs review" strip would separate the value from its field and its chip row, which is worse for the "Evidence always with the value" argument, and the header link already says exactly what is waiting. The conditions:

1. **Script the click.** The video clicks "1 unreviewed value" and the page scrolls to the box; never scroll by hand past 1,800px on camera.
2. **The target must exist on arrival.** The Evidence box only renders for the selected chip, so the Record must select the unreviewed chip by default in each chip field (tepotinib here). Otherwise `#unreviewed` is not in the DOM and the link goes nowhere.
3. **Land well.** Give `#unreviewed` a `scroll-margin-top` of about 120px so the "Linked drugs" label and chip row stay above it, move focus to the box (`tabindex="-1"`) so keyboard users land on Accept, and use smooth scroll so viewers see the jump. An optional one-second ring highlight on arrival helps the video.

If the build runs short of time, condition 2 is the only one that matters for the demo to work.
