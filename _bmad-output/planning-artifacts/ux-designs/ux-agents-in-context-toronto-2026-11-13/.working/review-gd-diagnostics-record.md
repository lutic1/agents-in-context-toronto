# Graphic design review: Diagnostics v1 and Record v1

Reviewer lens: senior graphic designer. Judged against Home v7 and Review v5 (approved look), DESIGN.md, and the sources `key-diagnostics.html` and `key-record.html`. Screens: `shots/diagnostics-v1.png`, `shots/record-v1.png`, `shots/record-v1-full.png`.

## Verdicts

| Page | Verdict | One line |
|---|---|---|
| Diagnostics | **Fix then ship** | A clean, credible enterprise table with good craft. It reads as flat and grey next to Review v5, and one filter contradicts the data. |
| Record | **Fix then ship** | The parts are right: the stage track header, quote treatment and inline review. But twelve identical rows make a wall, the grid breaks from Review's split, and the right column goes empty for 1,100px. |

What already works on both pages, and should stay:
- The top bar, logo, nav pill, counts, Team picker and avatar match Home v7 and Review v5 pixel for pixel.
- No ALL-CAPS eyebrows, no "→" on buttons, no middle-dot meta strings and no decorative gradients. Glass appears only on the top bar.
- Diagnostics: the table has quiet rules, a muted header row, name over provider, and a dense stage track with its name beside it. This reads like a real medical-affairs tool.
- Record: the header (display name, provider line, large stage track with "since 26 August 2020") is the strongest part of the page.

---

## Diagnostics

### Must fix
1. **The filter contradicts the rows.** The active filter reads "Sample: Plasma, Tissue", but the last row's sample type is "EBUS-TBNA supernatant". A pharma viewer will catch this. Either clear the filter (show plain "Sample type" with no `.on` state) or drop the EBUS row.
2. **Gene symbols are set in Mono.** `td.bio` uses `--mono`. DESIGN.md allows Mono only for identifiers a user copies (NCT, PMID, PMA). Review v5 and Home v7 set MALAT1, EGFR and KRAS in the sans. Switch `td.bio` to the sans at 14px, weight 500, with a 10px gap. As it stands, the column reads like a code dump and wraps to two lines (ALK BRAF EGFR / MET ROS1).
3. **There is no tissue field behind the page.** `.frame` is flat `#EEF0F8`. Review v5 has the fixed, heavily blurred haematoxylin, eosin and green circles, so its glass top bar has something to frost. Without them this page looks noticeably greyer and more "lacklustre" in a cut from Review. Copy the field layer from key-review v5 as it is.
4. **Changed marks are missing, so the story breaks between Home and Diagnostics.** On Home, Tumour-informed ctDNA MRD is "New", FoundationOne Liquid CDx and CDx are "Changed" (trial NCT04712877), and SuperARMS moved to clinical utility. These rows sit at the top of this list with no signal. Add the DESIGN.md changed mark before the name: a 6px eosin dot plus "New" or "Changed" in `eosin-text`, 13px, with no row fill. On SuperARMS, colour the newly filled 5th stage segment eosin, as Home's alert card does. This is the page's only allowed colour moment, and it is the right one.

### Should fix
- **The sort icon has no direction.** "Latest evidence" uses `arrow-up-down`, which means "sortable". The column is sorted descending, so use `arrow-down` (lucide `arrow-down-narrow-wide`) and keep `arrow-up-down` for unsorted headers.
- **Toggle affordance.** "Early research only" looks like a select with its chevron missing. Make it a shadcn Checkbox or Switch inside the filter bar, labelled "Early research only".
- **The Diagnostic column is too narrow.** "Tumour-informed ctDNA MRD (approach)" and "EBUS-TBNA supernatant cfDNA genotyping (approach)" wrap to three lines with the badge stranded. Give the first column about 340px. Take the space from Latest evidence by putting the date and source on one line ("12 Nov 2026, NCT04712877"; the source name can go in a tooltip) or by narrowing Modality.
- **The persona changes.** Diagnostics shows Rowan, and the Record it opens shows Sam. If the video clicks from one to the other, the avatar changes mid-flow. Use the same person on both, or plan a deliberate cut.
- **Page title style.** The H1 sits on the field at 30px. Review v5 puts its title and icon inside the panel. Either move "Diagnostics" (with the microscope icon at 18px) into the panel's head row above the filters, or keep it outside on every list page. The choice needs to be made once and kept everywhere. Moving it inside also removes the band of bare field between the top bar and the panel.
- **Seven of ten rows are identical "Regulatory approval".** That is honest data, but the column turns into a striped bar. Once the changed marks and the eosin segment exist, this matters less. Otherwise default the sort to place one Early research and one Clinical utility row in the first five.

### Nice to have
- Right-align "Showing 10 of 23" with the pager by moving it into the footer row ("10 of 23, sorted by latest evidence, newest first"). This frees the filter row.
- Hover row background `#F6F7FC` should use the `ink-tint` token at 50% so it stays on-token.
- Tabular figures on dates (`font-variant-numeric: tabular-nums`) so "12 Nov" and "3 Nov" align.

---

## Record

### Must fix
1. **The grid does not match Review's split.** `.grid` is `836px 436px`. Review v5 is about 750 / 518 (7/5 of 12 columns), and the file already declares `--left:752px; --right:520px` without using them. Set `grid-template-columns: var(--left) var(--right)`. Cut together in the video, the rail edge currently jumps about 85px between Review and Record.
2. **The twelve fields form a wall.** Every row has the same label, bold value, grey state and grey source, at the same weight and spacing, for 1,800px. Break it into three titled groups inside the fields panel. Each group gets a 19px heading (DESIGN `heading`) with a 24px top gap and a full-width rule:
   - **Status**: Lifecycle stage, Regulatory status
   - **What it detects**: Modality, Sample types, Biomarkers, Tumour types, Tumour stage or line, Provider
   - **How it is used**: Clinical uses, Linked drugs, Trials, Study results

   This also fixes the field order: Biomarkers currently comes after Linked drugs, but biomarker, then drug, then clinical use is the order a medical-affairs reader thinks in. Sentence case, no icons in the group headings.
3. **Orphaned "2026" lines.** Three source lines wrap so that only "2026" sits on the second line (Lifecycle stage, Sample types, Unreviewed tepotinib), plus "November 2026" in the rail. Shorten source lines: drop "first decision 26 August 2020" from Lifecycle stage, since the header already says "since 26 August 2020"; write "FDA list" as Diagnostics already does; and use the short date form ("data as of 3 Nov 2026"), which matches the state lines that already use "8 Nov 2026". At present one line mixes "8 Nov 2026" and "3 November 2026".
4. **The right column is empty from y≈1000 to the footer.** The rail ends after "Add a value", leaving more than half the page height as bare field on the right. Make `.rail` `position: sticky; top: 84px` so "Waiting for review" and "Add a value" follow the scroll. In the video, the reviewer action then stays in frame while the scroll reaches Clinical uses.
5. **The New/Changed mark is missing here too.** The trial NCT04712877 was "added 13 Nov 2026" and is the "Changed" item on Home. Its chip should carry the changed mark: an eosin dot plus "New" in `eosin-text` on the evidence line ("New: evidence for NCT04712877, added 13 Nov 2026"), with `eosin-tint` behind that one chip in place of the current `ink-tint`. This is the only place the Record needs pink, and the place where the Home story pays off.
6. **Mono is used outside identifiers.** The Biomarker chips (ALK, BRAF, EGFR, MET, ROS1) and "NSCLC" after Tumour types are set in Mono. Switch them to the sans; keep Mono for NCT, PMA and S-numbers only.
7. **Rail body indent.** `.rp-body` is padded 48px, so the body hangs off the heading text rather than the icon. DESIGN.md says the body sits "on the same left edge" as the heading icon, which is how Review v5's "Rule from your rejection" panel works. Set the left padding to 22px to match `.rp-head`.

### Should fix
- **Quote size.** Blockquotes are 15.5px with line-height 1.5. The spec token `quote` is 17px with line-height 1.6, and that is what makes Review v5's quotes read as literature. Set the main-column quotes to 17px and keep 15px only inside the History list. At 15.5 the serif barely separates from the 16px sans values.
- **Too much dashing.** Dashes now mean four things: the Early research badge (the spec'd use), the Unreviewed tag, the Unreviewed box, the tepotinib chip and the header pip. Keep dashed for Early research only. Show Unreviewed as an `ink-tint` box with a solid rule and the lucide `circle-dashed` icon plus the word "Unreviewed", and give the chip a solid border.
- **Header status pips.** The 8px hollow circles beside "1 unreviewed value" and "1 change waiting for review" read as radio buttons. Use lucide icons at 16px instead: `circle-dashed` and `clipboard-check`.
- **Duplicate "Add a value".** There is a header button and a rail panel with the same name. Remove the header button; the rail form is the real thing.
- **Repeated quotes.** "Exon 19 deletion or exon 21 L858R…" appears in Biomarkers and again directly below in Clinical uses. "The ultimate goal…" appears in the rail and again in the Clinical uses history. Pick a different EGFR clinical-use quote (the osimertinib indication text), and leave Clinical uses history collapsed by default (`aria-expanded="false"`) in the key screen.
- **Nested cards.** The History list is a grey card inside the white panel, and the Unreviewed box is a dashed card inside the same panel, so it reads as card in card in card. Drop the History background and use a 3px `ink-tint` left rule with a 16px indent, the same language as the quote rule.
- **Verbatim enum.** The Trials quote starts with "Intervention (DIAGNOSTIC_TEST):". That is an all-caps token in the most visible serif on the page. Quote the substring "ctDNA, tumor NGS, FoundationOne CDx, FoundationOne Liquid" instead; it is still verbatim.
- **Title size.** H1 is 30px; DESIGN `display` for a Record name is 34px. Use 34px so the Record outranks the list's page title.
- **Accept hierarchy.** For Sam as the reviewer, the one primary button on screen is "Add value", in the rail. Accept on the unreviewed tepotinib is the action that matters. Make Accept the primary there and turn "Add value" into a secondary button, so there is still one primary per panel.
- **"Word for word from the FDA…".** This is DxP's phrase sitting where the quote would be. Either show the source text as a serif quote, as other fields do, or write "Exact wording on the FDA list".

### Nice to have
- Add an inline "Add a value" text link on the Study results row ("No data for this indication. Add a value"), tied to the rail form that already preselects Study results.
- Remove the stray `<br>` in the Study results label so its baseline matches the other labels.
- Make the History toggle a ghost button with a count badge instead of underlined text, to match Review's quiet action links.
- Give each source line the lucide `file-text` icon at 14px, as Review v5 does. The two pages would then share one evidence-source pattern.

---

## Round 2 (diagnostics-v2, record-v2)

Screens: `shots/diagnostics-v2.png`, `shots/record-v2.png`, `shots/record-v2-full.png`. Settled and not re-raised: no New/Changed marks on these pages, a quote on every value even when it repeats the value, and top-bar nav order (global pass).

### Verdicts

| Page | Verdict | One line |
|---|---|---|
| Diagnostics | **Ship** | All open must-fixes are done. The title now sits in the panel, the filters are honest, the gene symbols use the sans and the tissue field sits behind the page. It now belongs next to Review v5. |
| Record | **Ship** | Every round-1 must-fix is done. The three groups break up the wall, the grid matches Review, and the rail is sticky with the right primary button. |

### Round-1 must-fix status

**Diagnostics**
1. Filter contradicts rows: **fixed**. All filters read "Any", so the EBUS row is consistent.
2. Gene symbols in Mono: **fixed**. `td.bio` is sans, 14px, weight 500, with a 10px gap.
3. No tissue field: **fixed**. The `.tissue` layer is present and the pink and lilac bloom shows under the glass bar.
4. Changed marks: **withdrawn** (settled: these marks appear only on Graph and Home).

**Record**
1. Grid split: **fixed**. `grid-template-columns: var(--left) var(--right)` (752 / 520), so the rail edge matches Review.
2. Wall of twelve fields: **fixed**. Status, What it detects and How it is used, with biomarker before drug before use.
3. Orphaned "2026" lines: **fixed**. Short dates everywhere ("data as of 3 Nov 2026") and no widows.
4. Empty right column: **fixed**. `.rail` is `position: sticky; top: 84px`. The full-page capture still shows bare field below the rail, but that is expected from a static capture; in the live scroll the rail stays in frame.
5. New/Changed mark: **withdrawn** (settled).
6. Mono outside identifiers: **fixed**. Biomarker chips and "NSCLC" use the sans; Mono is kept for NCT, PMA and S-numbers.
7. Rail body indent: **fixed**. `.rp-body` is padded 22px, on the same edge as the head icon.

Should-fix items also landed: quotes at 17/1.6, dashes limited to Early research, lucide status icons in the header, the duplicate header "Add a value" removed, the History card replaced by a left rule, the Trials quote trimmed to the substring, the H1 at 34px, Accept as the primary button, and the same persona (Sam) on both pages.

### New must-fix

None on either page.

### Should fix (carry-over, not blocking)
- Record: Clinical uses History is still open by default. It adds about 150px of grey text between Clinical uses and Linked drugs right where the video scroll lands on the tepotinib review. Collapse it in the key screen (`aria-expanded="false"`).
- Diagnostics: seven of ten rows still read "Regulatory approval / FDA approved, PMA". Now that the changed marks are gone from this page, the Early research badge is its only accent. If the video holds on this page for more than a beat, start the list on a sort or page that puts the SuperARMS and MRD rows in the first four.
- Diagnostics: "No data for this indication" in the Biomarkers column wraps to two lines. Use "No data" in that narrow cell, or widen the column by about 20px.
