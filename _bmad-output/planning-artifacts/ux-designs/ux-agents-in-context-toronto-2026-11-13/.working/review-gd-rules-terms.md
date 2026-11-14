# Graphic design critique: Rules v1 and Terms v1

Reviewed: `shots/rules-v1.png`, `shots/terms-v1.png` against `shots/home-v7.png`, `shots/review-v5.png` and `DESIGN.md`.

## Verdicts

| Page | Verdict | One line |
|---|---|---|
| Rules v1 | **Fix then ship** | Right system, clean type and colour; let down by an off-grid column split, ragged right-hand status text and a header caption that floats. |
| Terms v1 | **Fix then ship** | The table is solid enterprise work; the right panel reads like a demo annotation and leaves the right half of the screen empty, and the table has no action, so it reads as a report, not a tool. |

## What already works (keep it)

- Top bar matches Review v5 exactly: logo, icon+label nav, counts, capture box, Team picker with Synthetic badge, Sam avatar. Page title size and position (y≈186) match Review, so a cut between pages will not jump.
- Type discipline is right: Atkinson Hyperlegible Next everywhere, Mono only on the PMID, no serif on either page (there are no quotes, so that is correct).
- Colour discipline is right: eosin appears once, as dot + "New" on the rule created live from Sam's rejection. Nothing else is pink. No gradients on panels.
- None of the AI tells: no all-caps eyebrows, no arrows on buttons, no middle-dot meta strings (meta uses spacing and icons), no card soup, sentence case throughout.
- Turned-off rule is greyed and labelled "Off", not colour alone. Numbers in the terms table are right-aligned with tabular figures.

## Must-fix

### Both pages

1. **Snap the two-column split to the grid used by Home and Review.** Home v7 and Review v5 split the 1294px content width at 750 / 518 (about 7 / 5 columns), right panel left edge at x=850. Rules and Terms use `grid-template-columns: 880px 392px` (right panel at x=978), which is neither the approved split nor a true 8 / 4 (that would be about 855 / 415). In the video, cutting Review to Rules makes the right panel visibly jump 128px. Change `.lower` to the same column values Review uses.

### Rules

2. **Make the right-hand status column one consistent, single-line pattern.** Today it is "2 flagged / in Review" (link, wrapped), "Nothing pending / to flag" (wrapped) and "Off, flags / nothing" (wrapped), all ragged right in a 150px column. It looks unfinished. Use one line each, same structure: flag icon + "2 flagged in Review" (link), flag icon + "1 flagged in Review" (link), "None flagged" (muted), "Off" (muted) or simply nothing for the off rule. Widen the column or shorten the copy so none of them wrap; top-align to the title baseline.
3. **Fix the header's floating capability caption.** "Each rule you turn on is also saved to MongoDB Agent Memory as a procedural rule." is set right-aligned over two lines opposite the title, where it competes with the H1 and reads as a stray note. Either move it left-aligned as one caption line under the subtitle (database icon + text, as on Home v7), or reduce it to the single outlined capability tag "Agent Memory" top right per `DESIGN.md` capability-tag.

### Terms

4. **Replace the "Curated synonyms" explainer with a real panel.** "A matched term, for comparison… So 'liquid biopsy' in Find returns every ctDNA test." is presenter narration, not product UI, and one chip in a 190px-tall panel leaves ~450px of empty field under it next to an 800px table. Make it a list of 4–6 curated pairs (liquid biopsy / ctDNA, NGS / next-generation sequencing, CGP / comprehensive genomic profiling, CDx / companion diagnostic, …) as rows with the link icon between terms, a one-line muted caption, and one capability tag ("Atlas Search synonyms"). Keep the narration for the voice-over.
5. **Give the table an action so it reads as a working tool.** Each row is "a gap in DxP's vocabulary", but nothing lets the user close the gap. Add a right-hand column with a quiet outline/ghost button "Map to…" (or "Add synonym") per row, or show one selected row in `ink-tint` with an inline mapping control. Without it the page is a static report.
6. **Separate "Times seen" from "Last seen".** The right-aligned count sits ~30px from the left-aligned date, so rows read as "7 13 November 2026" while the Term→Field gap is ~200px. Rebalance widths (narrow the Term column, give the count column real right padding, 40px+ before the date) and use short dates ("13 Nov") as Home v7 does in lists.

## Should-fix

- **Rules: "More: Rules" in the active nav pill** reads like a dev placeholder. Use "Rules" with the chevron in the active ink-tint pill (the menu still opens from it), or keep "More" active and let the page title name the page.
- **Rules: copy mismatch** - the side panel says "9 words the agents met"; the Terms page says "9 terms". Use "terms" in both.
- **Rules: empty lower third.** Both panels end by y≈700 / 437 with ~300px of bare field below. Add the footer data-credits line `DESIGN.md` requires (it is missing on both pages) and consider a second right-column panel (for example "Flagged this week", 2–3 rows linking to Review) so the right column ends near the main panel.
- **Terms: bold on every term** makes the first column the heaviest thing on the page. Use 500/600 weight, or regular weight with the row as the hover target.
- **Terms: header link "Learned rules"** is a ghost link floating top-right with no clear relation to the panel. Rules cross-links to Terms with a side panel; Terms cross-links back with a header link. Pick one pattern for both pages (a small "Learned rules" outline button in the same position on both is simplest).
- **Terms: field icons.** "Tumour types" uses a dashed-corner scan glyph that reads as a placeholder. Use `DESIGN.md` icons (Biomarker `dna`, Trial `flask-conical`, etc.) and pick a clearer one for tumour types, or drop icons from the table cells and let the field name carry it.
- **Rules: icon for Biomarkers** looks like a sparkle at 16px and can read as the "AI magic" glyph. Confirm it is lucide `dna` and that it renders as a helix at size; same on Review v5.

## Nice-to-have

- Use curly quotes in the rule origin line (“Add biomarker ZNF471 to Guardant360 CDx”).
- On Terms, mark terms first seen since the last visit with the eosin dot + "New" (for example "methylation signature", seen 13 November) so the page shares the product's one signal.
- Rule titles end with full stops; fine as they are imperative sentences, and Review v5 does the same, so keep it consistent rather than change one.
- Give the Terms footer note the same left inset as the table text (x=102) - it is, keep it when the column widths change.
