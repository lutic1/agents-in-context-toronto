# Graphic design review: Find v1 and Categories v1

Reviewer: senior graphic designer. Inputs: `shots/find-v1.png`, `shots/categories-v1.png`, references `shots/home-v7.png`, `shots/review-v5.png`, `DESIGN.md`, `key-find.html`, `key-categories.html`. Judged at 1440×900 as it will read in a 1080p screen recording.

## Verdicts

| Page | Verdict | One line |
|---|---|---|
| Find v1 | **Fix then ship** | Right family as Home and Review: same top bar, panels and type. The table is too small for camera and its rows are uneven. |
| Categories v1 | **Fix then ship** | A credible enterprise grid with honest gaps. It has four craft faults: the top bar overflows, the popover is detached from its cell, the type is too small, and every column has the same width. |

Neither page has generic-AI tells: no ALL-CAPS eyebrows, no "→" on buttons, no middle-dot meta strings, no decorative gradients and no card soup. Eosin is used correctly on both pages, only for the "Changed" mark (Find, NCT04712877) and the just-advanced stage segment (SuperARMS on both). The serif appears only in Evidence quotes, and Mono only on NCT and PMA identifiers. Glass is used only on the top bar and on the docked Evidence panel. Everything else is solid white, as the spec requires. Those are the hard parts, and they are right.

---

## Find v1

### Must-fix

1. **The table type is below spec and below camera legibility.** Cells are 13.5px and headers 13px, against the DESIGN.md `table` token of 15px. Captions such as provider, stage name and "No data for this indication" are 12.5px. At 1080p compression, 12.5px muted grey turns to mush.
   - Set cells to 15px, the Diagnostic name to 15.5px/700, headers to 13.5px/600, and secondary lines (provider, stage name, no-data) to 13px.
   - Keep `.id` at 14px, which is the identifier token.
2. **The row rhythm is uneven** (row heights run about 60, 80, 79, 60, 80 and 79px). The cause is the 184px Diagnostic column, which wraps "FoundationOne Liquid CDx", "Agilent Resolution ctDx FIRST assay" and "cobas EGFR Mutation Test v2" onto two lines while their neighbours stay on one.
   - Rebalance the 910px table as follows: checkbox 40, Diagnostic 236, Lifecycle stage 132 (the small stage track needs 124px plus padding, and 128 is currently too tight), Sample 72, Biomarkers 112, Linked drugs 116, Clinical uses 100, Trials 102.
   - Also set a `min-height` on rows so that a single-line row and a two-line row share one rhythm. Vertically align all cells to the top, as they are now.
3. **The open-cell indicator is too heavy and doesn't connect to the panel.** The 2px near-black ring around "EGFR, ERBB2, KRAS" reads as a keyboard-focus bug, not as "this cell's Evidence is open".
   - Use an `{colors.ink-tint}` fill with a 2px `{colors.foreground}` left bar, or a 1.5px ring at `--foreground` with 60% opacity.
   - Echo the link in the panel title (see should-fix 1) so the eye travels cell → panel.
4. **The table toolbar label is misbound.** "3 selected" sits directly before the name input and reads as the input's label. The `<label for="sl-name">` really is "3 selected", which is also an accessibility bug.
   - Move "3 selected" next to the count ("6 diagnostics, best match first, 3 selected"), or onto the Save button ("Save 3 to shortlist").
   - Give the input a real label, "Shortlist name", either visually hidden or as a placeholder-style caption above it.

### Should-fix

1. **The Evidence panel title is generic.** "Biomarkers" plus the two-line subtitle "Guardant360 CDx, each value with its Evidence" buries the subject.
   - Make the title "Guardant360 CDx" (heading 19px) and the subtitle "Biomarkers, each with its Evidence" on one line.
   - Align the close X to the title's cap height. It currently floats about 6px high.
2. **There are two filled primary buttons in one view** (Search and Save shortlist). Once results exist, Save shortlist is the climax action of Flow 2.
   - Make Search the outline/secondary style when results are showing, or keep Search primary and make Save the outline style. Either way, one ink-filled button per view, as on Review v5, where Accept is the only filled one.
3. **"Add filter" is orphaned** on a second line at x≈113. That aligns neither with the "DxP read this as" lead (x=100) nor with the first chip (x=209).
   - Fit it on line one by shortening the chip copy ("you changed this" becomes "edited"), or wrap the whole chip group so line two starts under the first chip.
4. **The query footer has developer copy and weak structure.** "Re-run from your filters, no model call." reads like an engineering note.
   - Rewrite it as "Changing a filter re-runs instantly", or drop it.
   - Render the capability line as the `capability-tag` component (1px border, 4px radius, caption), the way the Home "Agent Memory (public preview)" line should also be. A bare icon-and-text line on the right edge looks like a stray footnote.
5. **The grid split does not match Home/Review.** Home and Review split the content at 752/520. Find splits at 912/360, which follows the spec's 360px right panel. As a result, the vertical edge of the right column jumps from x=849 to x=1009 between pages, and in a video cut that reads as a layout shift.
   - Keep 360 (it is the spec), but declare it as a named token (`--evidence:360px`) and document that Home is the exception.
   - Or snap all of them to one 12-column grid: 1296 content, 24px gutters, column ≈86px. That gives 9+3 = 942/330 for Find and 8+4 = 856/416 for Home.
6. **The selected-row tint (#F1F2FA) is very close to the panel white** and will vanish on camera. Use `{colors.ink-tint}` at about 60%, or a 3px ink left edge on selected rows.
7. **"Lifecycle stage" with its sort icon** is the only header with a sort affordance, and the icon sits at 70% opacity at 13px. On the sorted column, make the icon full opacity and give the header text the foreground colour, so viewers can see what the order is.

### Nice-to-have

- "No data for this indication" is required copy (EXPERIENCE.md). Set it in `--muted` at 13px with no italics. In the Trials column, a 1px dashed underline on hover would hint that it can be added to.
- In the Evidence panel, the source lines indent 17px to sit under the quote text. Align them to the quote rule (0px) instead, so the left edge reads as one column.
- The FDA quote "ERBB2 Activating Mutations (SNVs And Exon 20 Insertions)" is title case from the source. That is correct to keep verbatim, so don't "fix" it.
- Radius token drift: the mocks use 12/16px (`--r-lg`/`--r-xl`), while DESIGN.md says lg = 18px. Home uses the same values, so this is consistent within the mock set. Reconcile DESIGN.md or the CSS before build.

---

## Categories v1

### Must-fix

1. **The top bar overflows and doesn't match Home.** On this page the "More ▾" item becomes an active "Categories ▾" pill. That widens the nav by about 50px and pushes the Rowan button to x≈1425, past the 24px top-bar padding (Home and Find end at about 1414). In a cut between pages, the right cluster jumps.
   - Pick one model. EXPERIENCE.md lists Categories as a permanent item between Find and Graph, so add it there on every page and drop "More". If that doesn't fit, shorten the capture box to "Add a diagnostic". Alternatively, keep "More ▾" and show it active, with Categories checked inside.
   - Either way, the right cluster must end at the same x on every page.
2. **The popover is detached from its target.** The target cell (Agilent row, Tumour stage) ends at x≈863, but the popover starts at x≈953 and its arrow points at the Biomarkers column ("KRAS"). The popover also hides the Biomarkers, Tumour types, Trials and Linked drugs values for four rows, right where the viewer is looking.
   - Anchor the popover's arrow to the target cell's right edge (popover left ≈ 872), or open it below the cell, spanning the Tumour stage to Tumour types columns.
   - Raise the shadow/scrim contrast slightly so the popover reads as a layer, not as part of the table.
3. **The type is too small for a 12-column grid on camera.** Cells are 13px, headers 12.5px, and the stage name and badges 11.5 to 12px. This is the densest screen in the video and it will not survive 1080p.
   - Set cells to 14px minimum, the Diagnostic name to 15px/700, and headers to 13px/600.
   - To make room, drop the Provider column into the Diagnostic cell as a secondary line, as Find already does. That leaves 11 columns and gives the others about 9px more each.
4. **Every column has the same width.** Ten `auto` columns at about 100px each ignore their content. "FDA approved (PMA)" wraps, while "NSCLC" and "Plasma" sit in half-empty columns. The last column also runs to within 7px of the panel edge (left padding is 22px), so the table looks cut off on the right.
   - Set explicit widths by content. For example: Diagnostic 236, Filled 64, Regulatory 128, Clinical uses 116, Sample 76, Tumour stage 112, Biomarkers 116, Tumour types 76, Trials 112, Linked drugs 120, Study results 112, plus 22px right padding on the last cell to mirror the left.
   - Right-align "7 of 10" with tabular figures (DESIGN.md Layout: numbers right-aligned, tabular).

### Should-fix

1. **The modality tabs look like primary buttons.** The active "ctDNA 6" tab is an ink-deep filled pill, the same fill as a primary button. The selection language is now inconsistent: the nav and chips use `ink-tint` for "selected", and the tabs use ink-deep.
   - Use a segmented control on `ink-tint` with a white active segment and foreground text, or an underline tab (2px foreground) to match shadcn `Tabs`.
2. **The header subtitle is ambiguous.** "6 diagnostics with all ten fields." reads as if every Diagnostic has all ten fields filled, which contradicts the "4 of 10" in the table.
   - Rewrite it as "6 diagnostics, all ten fields shown. 1 is thin; none are stale."
3. **The legend's placement is weak.** The Thin/Stale key floats at the top right as two pills with definitions, and the key instruction "Click an empty field to add a value you know." is the last line in muted 13.5px. That instruction is the point of Flow 4.
   - Promote it to the subtitle line under the title, at body size.
   - Keep the Thin/Stale key on a single line right-aligned with the tabs: `[Thin] fewer than 5 of 10 filled   [Stale] newest Evidence over a year old`.
4. **The Diagnostic cell is too tall.** Name, stage track, stage name and badges stack up to four lines, making rows 77 to 95px tall and uneven.
   - Put the stage name on the same line as the track (track, then caption, inline), as on Review v5. Wrap the badges onto that line too.
   - This gives a target rhythm of three lines and about 72px per row.
5. **The "No data for this indication" text forms a wall of grey.** About 25 instances dominate the right half of the grid. The words are mandated, so treat them visually instead:
   - set them in 13px `--muted`, with a faint dashed cell outline on hover only;
   - consider a very light `#FAFBFD` cell fill on empty cells, so that the gaps read as a pattern (the story of this page) rather than as text noise.
6. **The Filled column duplicates the Thin badge.** "7 of 10" as plain text is the least scannable way to show it. A 10-segment micro-meter (same visual language as the stage track but smaller and in foreground) with "7/10" in tabular figures would read instantly on camera. Thin rows would then show visibly short meters.

### Nice-to-have

- In the popover, the "Value" select and "Your note" textarea are correct shadcn. The hint "Saved for everyone as Manually sourced, with your name, Rowan." is good copy. Bold "Manually sourced" so the provenance term registers.
- The "Early research" dashed badge and the "Thin" badge sit next to each other with near-identical pill shapes. Give Thin the `capability-tag` 4px radius so the two families (lifecycle vs data quality) differ in shape, not just in border style.
- The URL `categories?modality=ctdna` is a nice touch that confirms state. Keep it.
- The footer credits line is present and correctly quiet. Find v1 should show it too, because it is cropped out of the screenshot.

---

## Cross-page consistency checklist

| Item | Home v7 / Review v5 | Find v1 | Categories v1 |
|---|---|---|---|
| Top bar, logo, right cluster position | reference | matches | **overflows by ~10px; nav item differs** |
| Page title (icon 22 + 26px/700) | Review matches | matches | matches |
| Panel radius / shadow | 12px, soft | matches | matches |
| Table cell size vs 15px token | n/a | 13.5px (low) | 13px (low) |
| Eosin only for change | yes | yes | yes |
| Serif only in quotes / Mono only on IDs | yes | yes | yes (no quotes shown) |
| Glass only on top bar + docked panels | yes | yes (Evidence panel) | yes (popover is solid, correct) |
| One filled primary per view | yes | **two** | one |
| Generic-AI tells | none | none | none |

---

# Round 2: Find v2 and Categories v2, plus top bar v2

Inputs: `shots/find-v2.png`, `shots/categories-v2.png`, `key-find.html`, `key-categories.html`. I also measured both sources in headless Chrome at a 1309px viewport.

## Verdicts

| Item | Verdict | One line |
|---|---|---|
| Find v2 | **Ship after two fixes** | All four round-1 must-fixes are done. The table is now camera-legible, and Save is the only filled button. What remains is the settled-decision breach: Changed marks and the eosin stage segment. |
| Categories v2 | **Ship after three fixes** | The popover, type, columns and tabs are all fixed. It still breaks the New/Changed rule, and the target-cell ring repeats the "focus bug" look that Find has already dropped. |
| Top bar v2 | **Right content, wrong width** | The nine items plus More, the permanent Categories item and "Add a diagnostic" all read well, and the right cluster ends at x≈1414 on both pages at 1440. But at 1309px it overflows by about 73px and the Rowan button is clipped off-canvas. |

## Round-1 must-fix status

### Find

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Table type below spec | **Fixed** | Cells 15px, name 15.5/700, headers 13.5/600, provider and no-data text 13px, IDs 14px Mono. |
| 2 | Uneven row rhythm | **Fixed** | Diagnostic is now 300px with nowrap, and the rows sit at an even ~62px. "Plasma, Tissue" and "ALK, BRAF, EGFR +2" wrap, but they don't break the rhythm because the stage cell is already two lines. |
| 3 | Open-cell ring | **Fixed** | Tinted fill with a left bar, and the panel title now names "Guardant360 CDx" with the subtitle "Biomarkers, each with its Evidence". |
| 4 | Misbound "3 selected" label | **Fixed** | There is now a separate "Save as a shortlist" panel with an "Intended use" label and the button "Save 3 as shortlist", and the count line reads "3 selected". Search is now the outline style, so there is one filled primary. |

The round-1 should-fixes were also largely taken. "Add filter" is now on line one. Atlas Vector Search is rendered as a `cap-tag`. The grid now matches Home at 752/520. The developer copy is gone, replaced by "Removed ... Undo", which is good.

### Categories

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Top bar overflow / nav model | **Fixed at 1440, not at 1309** | Categories is now a permanent item, More is kept, and the right cluster ends at the same x as on Find. See new must-fix T1. |
| 2 | Popover detached | **Fixed** | It is anchored to the Clinical uses cell of the MRD row, the arrow points at the target, and the shadow now reads as a layer. |
| 3 | Type too small | **Fixed** | Cells 14px, name 15/700, headers 13/600. Provider has moved into the Diagnostic cell. |
| 4 | Equal column widths | **Fixed** | Explicit `colgroup` widths. "7 of 10" is right-aligned with tabular figures, and the last column has its right padding. |

The round-1 should-fixes were mostly taken. The tabs are now a segmented control on tint. The subtitle is clear ("2 are thin; 1 is stale"). The instruction "Select an empty field to add a value you know." is promoted to body size. The legend is on one line. The empty cells now have a faint fill, so the gaps read as a pattern. Still open, and still should-fix rather than must-fix: Diagnostic cells stack to 4 to 5 lines, so row heights run 77 to 125px. The MRD row is the tallest, and it is the row the camera lands on.

## New must-fix

### Top bar (applies to every page)

**T1. It overflows at 1309px.** I measured `.topbar-inner` in headless Chrome at a 1309px viewport. The content needs 1333px, but only 1259px is available, so the right cluster runs to x≈1358 against a 1285 content edge. Because `.frame` has `overflow:hidden`, the avatar and "Rowan" are cut off, and part of the scope control goes with them. Nothing in the bar has `flex-shrink` or a breakpoint, because every item is `nowrap`.
- Preferred fix: below about 1400px, hide the nav icons (16px icon plus 6px gap, across 9 items, saves about 198px). Text-only nav at 14px still reads cleanly, and the active pill carries the state.
- Alternative fix: make the user control avatar-only (saves about 55px) and tighten nav padding from 7px to 5px (saves about 40px). That nets about 95px against the 73px needed, which is too tight to trust.
- Whichever fix is chosen, re-shoot one page at 1309px to prove it. Note too that the page bodies are fixed at 1440: Find's 72 + 752 + 24 + 520 + 72 grid puts the table edge at x≈1368 at 1309px. If the video records at 1309, the content grid needs the same treatment, either fluid columns or a 1309 frame.

### Find

**F1. Remove the Changed marks (settled decision: only Graph and Home).** There are three:
- the stage cell on SuperARMS ("• Changed" under Clinical utility);
- Trials NCT04712877 on FoundationOne Liquid CDx;
- Trials NCT06422546 on SuperARMS.

Also make the SuperARMS track's 5th segment a plain `.f` fill instead of eosin `.adv`, and drop "changed since your last visit" from its `aria-label`. Eosin then disappears from Find entirely, which is correct.

### Categories

**C1. Remove the New and Changed marks.** There are five:
- "• New" in the MRD Diagnostic cell (next to Early research and Thin);
- "New" under NCT07921888 in the MRD Trials cell;
- "• Changed" on SuperARMS in the Diagnostic cell;
- Changed under NCT04712877;
- Changed under NCT06422546.

Also apply the same `.adv` segment and `aria-label` fix as F1. Removing the New mark from the MRD badge row also shortens that row to Early research and Thin.

**C2. The target cell uses the 2px near-black ring.** The empty Clinical uses cell on the MRD row has the same 2px near-black ring that Find round-1 must-fix 3 removed. The target cell is now the visual focus of Flow 4, and it reads as a keyboard-focus bug. Apply Find's open-cell treatment (ink-tint fill with a left bar) so the two pages share one "this cell is open" language.

## Should-fix (carried or new, not blocking)

- **Categories:** put the track and stage name on one line, and the badges on the line under the provider, to bring rows to about 72 to 80px (carried from round 1).
- **Categories:** the "Manually sourced, Rowan, 11 Nov" value (FoundationOne, Tumour stage) is the one value on screen whose quote or note isn't visible. That fits the cell-click Evidence pattern. But since this is the manual-value story, consider a hover or open state in the video that shows Rowan's note, to keep faith with "every value shows its quote".
- **Find:** the Evidence panel now sits above the table, so the open cell (y≈633) and the panel (y≈136 to 503) are far apart. The tinted cell plus the "Guardant360 CDx" title carries the link well enough, but a 1px ink rule or matching tint on the panel header would tighten it.
- **Find:** "No data for this indication" wraps to two lines in the narrow Trials column. Widen Trials by about 20px by taking it from Diagnostic (300px holds the longest name with room to spare).
- **Find:** `.unrev` "1 Unreviewed" is still 12.5px. Raise it to 13px to match the other secondary text.

## Cross-page checklist, round 2

| Item | Find v2 | Categories v2 |
|---|---|---|
| Top bar matches, right cluster ends at x≈1414 @1440 | yes | yes |
| Top bar fits at 1309 | **no, 73px over** | **no, 73px over** |
| Type at or above token | yes | yes (14px cell for density, acceptable) |
| One filled primary | yes (Save 3 as shortlist) | yes (Add value) |
| New/Changed only on Graph/Home | **no, 3 marks plus eosin segment** | **no, 5 marks plus eosin segment** |
| Serif only in quotes / Mono only on IDs | yes | yes |
| Generic-AI tells | none | none |
