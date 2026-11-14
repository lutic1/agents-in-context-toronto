# UX review: Find and Categories (v1)

Reviewed: `shots/find-v1.png`, `shots/categories-v1.png`, `key-find.html`, `key-categories.html`, compared against `EXPERIENCE.md`, `DESIGN.md`, epics Stories 1.2 and 4.2 to 4.7, ARCHITECTURE-SPINE (AD-2, AD-6, API contract), and the Home, Review, Graph, Record and Diagnostics mocks. FDA quotes were checked against `data/fda/assays.json`.

## Verdicts

| Page | Verdict | Why |
|---|---|---|
| Find | **Fix, then ship** | The structure is right: original text above, chips, one quiet tag, a table with Evidence one click away, and an Evidence panel with source, identifier link, date and "Unreviewed". The FDA quotes match the source word for word. The problems are: a chip state that contradicts the query, rows that contradict the Record and Diagnostics mocks, no "Unreviewed" label in the table, and a change shown by colour alone. |
| Categories | **Fix, then ship** | The thin mark, the key, the empty-cell rule and the manual-value form all read well. But the tabs and the thin/stale/"Filled" numbers depend on things the API does not return yet. Two rows contradict the Record and Diagnostics mocks. And the Flow 4 climax (a value shown as "Manually sourced") never appears in the table. |

## Flow 2: keep Home's search, change EXPERIENCE

**Change EXPERIENCE Flow 2. Leave the mocks on "Plasma EGFR and KRAS genotyping".** Reasons:

- Home, Graph, Review, the Alerts, the Team profile (ctDNA, EGFR, KRAS) and the shortlist of three plasma companion diagnostics all tell the EGFR and KRAS story. An earlier review (review-ux.md H1, H2-1) already moved Home this way.
- The climax of Flow 2 is "the table fills". With the FDA seed, every EGFR/KRAS cell has a word-for-word quote. An MRD relapse-monitoring search would match only the Tumour-informed ctDNA MRD approach (thin, Early research) and perhaps SuperARMS, so the table would be mostly "No data for this indication". That is a weak climax for the video.
- The PRD's UJ-1 example is marked `[ASSUMPTION: example]`, so changing it is allowed.

Proposed Flow 2 text (it also fixes F1 below):

1. Home: "Last time you shortlisted Guardant360 CDx, FoundationOne Liquid CDx and Agilent Resolution ctDx FIRST assay for plasma EGFR and KRAS genotyping in advanced NSCLC. 5 changes since {date}."
2. "Reopen last search": Find opens with the original text. Its chips include **Tumour stage or line: advanced or metastatic**, because DxP did read "advanced".
3. Only FoundationOne Liquid CDx matches, because it is the only Record with a tumour-stage value (Rowan's own manual value on the Record mock). Rowan removes that chip. The table re-runs from filters only and widens to 6 rows.
4. Climax as now. Rowan ticks three rows, saves the Shortlist and exports it.

The title "Back after six weeks" cannot work with this data either (see X1). Retitle it "Back after a week" or something similar.

## Must-fix

### Cross-page

- **X1. The timeline is impossible.** Find says "Reopened from your last visit on 2 November", and Home says Rowan shortlisted three Records then. But the FDA data is dated 3 November, the Baseline load set those values on 8 November (Record: "Set by rule, 8 Nov 2026"), and Rowan added a manual value on 11 November (Record). Rowan cannot have shortlisted Records that did not exist yet, or been away while adding a value. Fix: Baseline load 3 Nov, Sam accepts on 4 Nov, last visit **5 November** (the changes on 6 and 12 Nov stay "since your last visit"), and the 11 Nov manual value goes to another person, marked Synthetic. Update Find's line to "Reopened from your last visit on 5 November", and update Home and Graph to match.

### Find

- **F1. The "you changed this" chip contradicts the query, and one parsed filter is missing.** The text says "Plasma…", so the model would have produced `Sample type: plasma` itself; marking it as "you changed this" makes no sense. Also, "advanced" produced no chip, so the parse looks incomplete. Fix: show every chip as DxP read it, including `Tumour stage or line: advanced or metastatic`. Mock the moment just after Rowan removed it: a single muted line under the chips reading "Removed Tumour stage or line: advanced or metastatic. 6 diagnostics, was 1. Undo". This is client state only, so no API change is needed, and it matches the Flow 2 rewrite.
- **F2. SuperARMS reads "Provider: no data".** That breaks the Voice and Tone rule (it must read "No data for this indication"). It also contradicts the Diagnostics mock, which says **Amoy Diagnostics**. Show "Amoy Diagnostics".
- **F3. Rows contradict the Record, Review and Home mocks.**
  - FoundationOne Liquid CDx shows Clinical uses "treatment selection". In the Record, Home Digest and Review mocks that value is still waiting for review. The accepted value is "Companion diagnostic". A pending proposal is not a value, so it must not appear.
  - FoundationOne Liquid CDx Trials shows one trial. The Record lists four, so show "NCT04712877 +3".
  - The FDA rows show "treatment selection", but the seed files "Companion diagnostic" (see the Record). Guardant360 CDx's "+1" must not include its pending "response monitoring" (Review).
- **F4. No "Unreviewed" label in the table.** Evidence Display Rules say "Unreviewed values are visible to everyone and labelled 'Unreviewed'". The Guardant360 CDx, Guardant360 Liquid, Agilent and cobas values are Baseline values and still Unreviewed. FoundationOne Liquid's were accepted by Sam. Only the side panel says so. Cheapest fix: one muted caption per row under the provider, such as "5 values Unreviewed", built from `review` on each value the read model returns. Alternatively, use a small "Unreviewed" caption in each cell.
- **F5. A change is shown by colour alone.** SuperARMS's just-advanced eosin segment has no word next to it, which breaks the accessibility floor ("change has the word"). Add the Changed mark after "Clinical utility" ("● Changed"). This applies to both pages.

### Categories

- **C1. The tabs are not something the API has.** The Diagnostics mock shows modality values "ctDNA NGS panel", "ctDNA PCR", "cfDNA NGS panel", "Tissue NGS panel", "PCR" and "IHC". The registry has no "ctDNA" or "Tissue NGS" Category grouping, `?modality=ctdna` is not an enum value, no endpoint returns per-Category counts, and the tab counts add up to 22 while the Diagnostics page shows 23. Pick one fix and write it into Story 4.6:
  - (a) Tabs are the registry `modality` values from `GET /schema`, filtered with `GET /diagnostics?modality=`. Drop the counts, or fetch one count per tab.
  - (b) Recommended for the demo: add a `categories` map to the registry, for example "Liquid biopsy" = ctDNA NGS panel + ctDNA PCR + cfDNA NGS panel. That keeps SuperARMS (ctDNA PCR) correctly in the tab and also brings in the EBUS-TBNA cfDNA approach, whose newest Evidence (3 Apr 2025) makes it **stale**. Flow 4 step 2 then shows both marks.
- **C2. Thin, stale and "Filled n of 10" are display rules with no API owner.** AD-6 and the Foundation section say the web app applies no display rule of its own. The `Record` shape has no completeness fields, and Story 4.6 is WEB only. Fix: add `completeness { filled, total, thin, stale, newest_evidence_at }` to `search.readmodel`, with an API acceptance criterion on Story 4.6 (or 4.2). In the same criterion, fix the denominator. The PRD's "ten fields" are modality, provider, clinical uses, sample types, tumour stage or line, biomarkers, tumour types, trials, linked drugs and study results, plus regulatory status. The mock counts regulatory status and drops modality. Either show Modality (a caption under the name is enough) and count those ten, or state "n of 11". Do not count against a list the registry does not have.
- **C3. Rows contradict other mocks, and the climax state is missing.**
  - SuperARMS Provider should be Amoy Diagnostics, so it is "6 of 10", not 5.
  - FoundationOne Liquid CDx Tumour stage or line should show "Advanced or metastatic" with "Manually sourced" (Record), which makes it 9 of 10. Its Trials should be "NCT04712877 +3", and its Clinical uses "Companion diagnostic" (F3).
  - Showing that one Manually sourced cell also gives the table the Flow 4 climax state ("the value appears for everyone, marked Manually sourced"). The mock currently shows only the form, never the result.
- **C4. "Unreviewed" is missing in the table.** Same as F4.
- **C5. The colour-only stage change on SuperARMS.** Same as F5.

## Should-fix

### Find

- **The capability tag is a sentence, not a tag.** DESIGN.md asks for a quiet outlined tag in caption type. Show "Atlas Vector Search" beside the query box, with the EXPERIENCE hover sentence. The current inline text also credits synonyms to Vector Search, but synonyms come from the MongoDB Search synonym mapping (Story 4.1).
- **Ranking after a chip edit is not defined in the contract.** Story 4.2 says `filters` without `text` means no model call. But then there is nothing to rank by, so "best match first" after a chip edit has no basis. Add `text` plus `parse: false` to `POST /query`, or have the response echo the embedding text. Ranking by automated embedding is not a Claude call, so the "no model call" promise still holds.
- **The Shortlist state after "Reopen" is wrong.** The three ticked rows are an existing Shortlist, but the bar offers "Save shortlist" as if it were new. Show "Shortlist: Plasma EGFR and KRAS genotyping, saved {date} by Rowan", and rename the button "Save as new shortlist", because the API only has POST. Also:
  - Label the name field "Intended use", because Story 4.4 stores `intended_use`.
  - The `<label for="sl-name">` currently gives the field the accessible name "3 selected". Fix it.
- **The export button is ambiguous.** "Export CSV" with 3 rows ticked: does it export the table or the Shortlist? Use "Export table" and "Export shortlist", or "Export 3 selected".
- **Microcopy.** Change "Re-run from your filters, no model call." (which reads like a broken button) to "Change a filter and the table updates at once. DxP doesn't re-read your text."
- **Keyboard (for the build; the mock only shows the pattern on one cell).**
  - Every value cell is a focusable button, and Enter opens its Evidence.
  - Checkboxes are shadcn `Checkbox`, not `span role=checkbox` with no tabindex.
  - Every column header is a sort button with `aria-sort`. The spec says "sort by any column", but only Lifecycle stage has the icon.
  - When the Evidence panel opens, focus moves into it, and Esc returns focus to the cell.
- **States not designed:**
  - the query progress state (under 10 s)
  - Skeleton rows while loading (never "No data" while loading, FR-8)
  - no results, where the chips stay
  - the text-search fallback notice from Story 4.1
  Add a small state strip or note to the mock.
- **Recording fit.** It fits 1440×1000. But at the spec's 1440×900 and 110% zoom, only the query panel and about two rows show, and Find is the Flow 2 climax. Merge the `qfoot` line into the chip row (saves about 40px) and tighten the panel padding, or record Find at 100%. The fixed 912 + 360 grid must become fluid in the build.
- **Names and casing must match other pages.** "Guardant Health" here vs "Guardant Health, Inc." on Diagnostics and Record: use the `normalise_name` output everywhere. Values are lower case here ("treatment selection") but sentence case on the Record ("Companion diagnostic"): use one registry label everywhere.

### Categories

- **Export is missing.** FR-29 and UJ-2 require the landscape to be exportable. Reuse Story 4.5's CSV from the data already on the page.
- **Filled cells must open their Evidence too.** Categories is a comparison table (Component Patterns). Enter on a filled cell opens the 360px Evidence panel; Enter on an empty cell opens Add value. Show or note both.
- **Microcopy.**
  - "6 diagnostics with all ten fields" reads as if all ten fields are filled. Use "6 diagnostics, all ten fields shown. 1 is thin; none is stale."
  - "Click an empty field…" should be "Select an empty field…", because keyboard users matter.
- **Add-value form.**
  - The Value options must come from the `GET /schema` enum. Check that "second line or later" is a real `tumour_stage_or_line` value; the Record uses "Advanced or metastatic".
  - Mark the note as required.
  - Associate the labels with their inputs.
  - On submit, the cell turns into the value plus "Manually sourced · Rowan" with a toast. That is the state for C3.
- **Stale is never shown.** With option C1(b), the EBUS-TBNA cfDNA approach is stale. Otherwise, the key explains a mark that never appears.
- **Update EXPERIENCE Flow 4 to match the mock.** Every ctDNA row already has plasma, so "add sample type plasma" cannot happen. Change it to "Agilent Resolution ctDx FIRST assay has no Tumour stage or line; add 'second line or later' (or whatever enum value is correct) with a note." Also say who acts: Rowan or a named, Synthetic domain expert.

## Nice-to-have

- **Find Evidence panel, more sources.** Guardant360 CDx has two EGFR rows (amivantamab, exon 20 insertions) and two ERBB2 rows in the FDA list. Show "1 more source" under each value instead of hiding them.
- **Find Evidence panel material.** It is glass. DESIGN.md says glass is only for panels docked over the hero or the Graph; elsewhere use solid white.
- **Find select-all.** Add a select-all checkbox in the table header.
- **Find Early research.** The current query never shows the Early research label in the table (Story 4.3). Leaving it out here is honest, but make sure some screen in the video shows it in a table.
- **Categories popover placement.** The popover hides four columns, including the MRD row's "New" trial mark. Open it as the 360px right panel or below the cell so the changed marks stay visible on camera.
- **Categories nav.** "Categories ▾" replaces "More" in the top bar, and the chevron suggests a menu. Keep "More ▾" highlighted, with Categories shown active inside it, so the bar is the same on every page.

## Checks that pass

- **No PubMed text.** Neither page shows PubMed abstract text. The FDA quotes (EGFR exon 19…, ERBB2 Activating Mutations…, G12C) are word for word from `assays.json`, and the linked-drug counts match it.
- **MongoDB tag rule.** Find has one tag on the query panel. Categories correctly has none.
- **Chips.** Chips are removable and labelled, "Add filter" opens a field menu, and the original text stays above.
- **No data vs loading.** "No data for this indication" is used consistently (apart from F2), and it is visually distinct from content.
- **Evidence panel.** It has the quote in serif, source, identifier link, "Data as of", "Unreviewed" per value, and "Open Record". FDA rows show `regulatory_approval` with the FDA list as Evidence (Story 1.2).
- **Badges and marks.** The thin mark has an icon and a word, and the Early research badge is dashed. The Changed and New marks on trials match the Home change list (NCT04712877, NCT07921888).
- **Size.** Both pages fit 1440×1000, and each panel has one primary button.

---

# Round 2: Find v2 and Categories v2

Reviewed: `shots/find-v2.png`, `shots/categories-v2.png`, `key-find.html`, `key-categories.html`, against EXPERIENCE Flows 2 and 4 (rewritten), `shared-story.md` (wins), epics Stories 1.4 and 4.2 to 4.7. Settled rules applied: New/Changed marks only on Graph and Home; every value shows its quote; top bar is the new template.

## Verdicts

| Page | Verdict | Why |
|---|---|---|
| Find | **Fix, then ship (small)** | Every round-1 data and timeline issue is fixed. The chips, Undo line, tag, Evidence panel ("Accepted by Sam, 9 Nov 2026", "data as of 3 Nov 2026", "1 more source") and export label are right. What is left: the Changed marks have to go, one row is missing its Unreviewed label, and the top bar needs fixes. |
| Categories | **Fix, then ship** | The Category map, the ten countable columns, `completeness` from the read model, Thin and Stale shown together, and Rowan's Manually sourced value all work. I checked all seven "n of 10" counts and they are correct. What is left: the New/Changed marks, the Stale date and tab counts that the API does not supply, Unreviewed labels on three rows, and a Flow 4 text that no longer matches the mock. |

## Round-1 must-fix status

| # | Status | Note |
|---|---|---|
| X1 timeline | **Fixed** | "Reopened from your last visit on 12 November" matches shared-story and Flow 2. |
| F1 chips | **Fixed** | Three chips as DxP read them, and the removed-chip line "6 diagnostics, was 1. Undo" with `role="status"`. |
| F2 SuperARMS provider | **Fixed** | Amoy Diagnostics. |
| F3 rows vs other mocks | **Fixed** | Companion diagnostic everywhere, "NCT04712877 +3", and no pending values shown. |
| F4 Unreviewed in table | **Partly** | FoundationOne shows "1 Unreviewed". SuperARMS shows nothing. Its values are Baseline values but not FDA-seeded, so per shared-story (Sam accepted only FDA-seeded values on 9 Nov) they are still Unreviewed. |
| F5 change by colour | **Superseded** | The word was added, but marks are not allowed on Find at all. See N1. |
| C1 tabs | **Partly** | The Story 4.6 registry Category map is in, and the tab counts sum to 23. But no route returns a count per Category: `completeness` is per Record and `GET /diagnostics?modality=` returns lists. See N4. |
| C2 completeness | **Fixed** | `completeness { filled, of, thin, stale }` is in Story 4.6. Modality is now a column, so the ten fields are countable, and the counts are right (7, 7, 9, 7, 6, 4, 4). |
| C3 rows and climax state | **Fixed in the mock** | Amoy 6 of 10, and FoundationOne 9 of 10 with "Manually sourced, Rowan, 11 Nov". But EXPERIENCE Flow 4 now contradicts the mock. See N3. |
| C4 Unreviewed | **Partly** | Same gap as F4, on SuperARMS, the EBUS-TBNA approach and the MRD approach. |
| C5 colour-only change | **Superseded** | See N1. |

## New must-fix

- **N1. Remove every New/Changed mark from Find and Categories.** These marks belong only on Graph and Home.
  - Find: SuperARMS Lifecycle "Changed", SuperARMS Trials "Changed", FoundationOne Trials "Changed".
  - Categories: SuperARMS "● Changed" under the name, both Trials "Changed" marks, and the MRD approach "● New" plus its Trials "New".
  - Also drop the eosin `adv` segment on SuperARMS's stage track, and the aria-label suffix "changed since your last visit". The track shows plain stage 5 of 9, as on the Diagnostics mock.
  - Keep Early research, Thin, Stale and Manually sourced: those are states, not changes.
- **N2. Top bar accessibility (template, so every page).**
  - The counts are bare numbers. "Review 7" and "Alerts 5" are read as just that. Add text: visible or `sr-only`, such as "Review, 7 waiting" and "Alerts, 5 unread".
  - More is a menu button but has no `aria-expanded="false"` and no `aria-controls` pointing at a `role="menu"` list.
  - "Add a diagnostic" is a `<label>` with no control, so it cannot be focused or used by keyboard. Make it a `<button>`.
- **N3. EXPERIENCE Flow 4 contradicts the mock and shared-story.**
  - Flow 4 step 2 says FoundationOne "has no tumour stage or line", and the climax adds it.
  - Shared-story and the mock say Rowan added it on 11 Nov. The open form is "Disease monitoring" on the Tumour-informed ctDNA MRD approach's Clinical uses.
  - Rewrite Flow 4 to match the mock: step 2, "FoundationOne Liquid CDx already shows Rowan's Manually sourced Tumour stage or line"; climax, "Rowan adds Disease monitoring to the MRD approach with a note. It appears for everyone, marked Manually sourced, and the row goes from 4 to 5 of 10 and loses Thin." The read model recomputes `completeness` on submit.
  - That lost Thin mark is a better beat for the video.
- **N4. Values on Categories that the API does not supply.**
  - (a) "Stale, 3 Apr 2025": `completeness.stale` is a boolean with no date. Show "Stale" alone (the key already explains it), or add `newest_evidence_at` to `completeness` in Story 4.6.
  - (b) The tab counts (7, 5, 4, 6, 1): drop them, or add one sentence to Story 4.6 saying `GET /schema` returns the Category map with a count per Category.
- **N5. Unreviewed labels (finishes F4/C4).** Add the "n Unreviewed" caption, built from `review` on each value:
  - Find: SuperARMS.
  - Categories: SuperARMS and EBUS-TBNA (Baseline, not FDA-seeded), and the MRD approach.
  - If the MRD approach's values are still pending proposals from the live run, they must not appear at all. Its row must then show only accepted or Unreviewed values.

## Should-fix still open (from round 1, not blocking)

- Find keyboard:
  - Value cells are plain `<td>`, not focusable buttons that open Evidence.
  - The checkboxes are `span`s with no `input` and no tabindex.
  - Only one column is sortable.
- Find: `<label for="iu">` points at a `span role="textbox"`, so the field has no accessible name. Use a real `<input>`.
- Flow 2's climax names the Intended use "Plasma EGFR and KRAS genotyping", but the mock and shared-story use "... in advanced NSCLC". Align EXPERIENCE to the shared-story.
- Categories:
  - The tabs are `<button>`s without `type` or `aria-controls`.
  - The Add-value popover still covers four columns. A 360px right panel would keep the row visible on camera.
  - Note on the combobox: the Value options must come from the `clinical_uses` enum in `GET /schema`.
- Neither page designs the loading, no-result or text-search-fallback states.

## Checks that pass in round 2

- Every value in the Find Evidence panel shows its quote, source, identifier link and "data as of 3 Nov 2026" (the FDA list date, Story 1.4).
- The Atlas Vector Search tag is now a quiet outlined tag, with the tooltip text available to screen readers.
- "Export table, 6 rows" and Categories' "Export table" are both present.
- The Thin and Stale key has icon and word. Early research appears in a table (MRD approach), which covers Story 4.3's label on camera.
