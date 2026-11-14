# Graphic design review: Home, Review, Graph (v1)

Reviewer lens: senior graphic and product designer. I judged the screens by how they look in a 1440-wide recording compressed for a three-minute judged video, not against the spec line by line. Screens reviewed: `shots/home-v1.png`, `shots/review-v1.png`, `shots/graph-v1.png`, with `key-*.html` and `DESIGN.md`.

Tags: **must-fix** (hurts the demo or breaks the system), **should-fix** (visible polish loss), **nice** (worth doing if time allows).

---

## What works and should stay

- **The palette holds.** Haematoxylin ink on a cool slide white, with near-white panels separated by rules, reads as clinical and calm, and it doesn't look like a stock shadcn grey. Keep every token as it is.
- **Serif quotes against sans UI.** This is the strongest idea on all three screens. Source Serif 4 quotes behind a pale 3px rule make "this is the source talking" obvious at a glance, even at thumbnail size. Keep it.
- **Eosin mostly disciplined on Graph and Review.** On the graph, the two eosin edges, the ring and the eosin trial label tell the one story of the frame. Keep the treatment.
- **Node shapes per type** (circle, rounded square, diamond, triangle, hexagon, square) with stain colours. It's distinctive and still readable without colour.
- **Display and type scale.** "Welcome back, Rowan" at 34/700 against 16px body gives a real hierarchy step. Panel headings at 19/600 are right.
- **Ochre low-confidence marker** with an open circle and a word. It's clear and it isn't a badge.
- **Right-aligned dates** in the changes list, and Atkinson's distinct glyphs (slashed zero, open I/l/1) in identifiers.
- **Flat panels, no shadows** anywhere except the graph tooltip. Correct.

---

## Global (applies to all three screens)

1. **must-fix: the stage track is too small to be "the one bold element".** At 10x8px segments with a 2px gap the strip is about 106px wide and reads as a dotted line. In a compressed 1080p video it will smear into grey. Fix: make segments 16x10px with a 3px gap (about 170px wide), and draw empty segments as `border` fill plus a 1px `#B9C0D0` inset so they show on white. The Early research (ink-tint) segments are close to invisible on `card` white (see ctDNA MRD on Home). Give them a 1px `foreground` dashed outline, matching the Early research badge. Increase the stage caption beside the track from 13px to 14px.
2. **should-fix: inconsistent top bar.** The Alerts count is an eosin-tint pill on Home but an ink pill on Review and Graph. The team picker wraps "Thoracic oncology strategy" onto two lines on Home and Review but fits on one line on Graph. The user is Rowan on Home and Graph but Sam on Review. Fix: one count style (ink pill, with eosin only if alerts are unseen, and the same on every screen). Fix the picker at 260px wide with a single-line ellipsis, or shorten the label to "Thoracic oncology". Use the same user in every shot for a coherent video.
3. **should-fix: outline inflation.** Capability tag, Synthetic pill, Early research pill, keycaps, outline buttons, the rule-flag box and the reason box are all 1px-outlined small shapes. Together they make a "sprinkled chips" texture, which is a classic generated-UI tell. Fix: keep the outline only on interactive controls (inputs, secondary buttons). Show the capability tag as plain 13px muted text with no border (for example "Powered by Agent Memory"), placed at the panel's bottom-left rather than the top-right header slot. Keep the Synthetic pill only where it labels content, and remove it from the top bar once the picker states it.
4. **should-fix: footer alignment.** On Home and Graph the data-credits footer starts at x=40, but content starts at x=72. On Review it aligns at 72. Fix: put the footer inside `content-max` with the 32px page gutter so its left edge matches the panels.
5. **nice:** At 1440 the 1360 max width plus a 72px left offset leaves about 72px on each side. That's fine. Don't add more chrome.

---

## Home (`home-v1.png`)

### must-fix

- **H1. The changes list is pink-washed.** All four rows in "4 changes since 2 October" have a solid `eosin-tint` fill, plus an eosin dot, plus an eosin "New" or "Changed" word, so each row carries the signal three times. Because every row is changed, the tint separates nothing. It just turns the left panel pink, and on video it reads as an error or warning list. Fix: remove the row background (`.change.is-new` → transparent). Separate rows with 1px `border` rules and 12px vertical padding. Keep the 6px eosin dot and the eosin-text word. If you want one pink accent, tint only the single "New" row (the first-seen diagnostic) and leave the three "Changed" rows untinted.
- **H2. The column balance is broken.** The left column ends at about y=840. The right column (two alerts plus Digest) runs to about y=1325, so roughly 500px of the left side is empty slide. That makes the screen feel unfinished and pushes Digest below the 900px recording fold. Fix: move the Digest panel into the left column under "Since your last visit" (it's about the same width and type of content). The right column then holds Alerts only and both columns end near y=980. Alternatively, cap each alert's quote at 3 lines with a "Show full quote" link, which saves about 60px per alert.
- **H3. The panel header competes with the greeting.** "Since your last visit" (19/600) sits in a header bar directly above "Welcome back, Rowan" (34/700). That's two headings for one idea, and the header bar with a right-aligned chip is the generic dashboard-card template. Fix: remove the header bar and its rule. Let "Welcome back, Rowan" open the panel at 32px top padding. Move "Agent Memory (public preview)" to a plain caption at the bottom of the memory paragraph, replacing the Synthetic line, for example: "Synthetic memory recalled with Agent Memory (public preview)".

### should-fix

- **H4. Two Synthetic markers.** One sits in the top bar and a second sits in the hero as a pill plus a sentence. Keep the sentence in the hero, drop its pill, and drop the pill in the top-bar picker (the picker says what it is).
- **H5. Alert cards are tall and repetitive.** Each alert stacks a status label, title, stage track, a 3-line summary, a 4-line serif quote, a source line and two buttons. That's about 380px each, and two identical blocks read as a template repeated. Fix: set the quote to 16px in this 360px column (it's 16 already, so keep the size and clamp it to 3 lines). Cut the summary to one sentence (the "matches your team's interest" clause is the useful part). Put "Play briefing" and "Dismiss" on the same line as the source caption, right-aligned, or show "Play briefing" on the first alert only.
- **H6. The label "Update: moved to clinical utility" uses a colon-prefixed log style.** Fix: "Moved to clinical utility", which matches the graph tooltip's wording. "First seen" is fine.
- **H7. Linked names in the changes list are bold and underlined.** That's double emphasis, and the underline collides with descenders ("approach"). Fix: bold with no underline, and show the underline on hover only. Or use a regular weight with a 1px `ink-tint` underline at 3px offset.
- **H8. The Digest "Low confidence" marker** floats right and forces the row to wrap ("add / monitoring"). Fix: put the marker on its own caption line under the row, left-aligned, so all three digest rows keep the same single-line rhythm.
- **H9. "Mark as seen"** is a ghost text button floating right with about 30px of air above and below, and it's easy to miss. Fix: put it on the "4 changes since 2 October" heading line, right-aligned, as a secondary (outline) button, which also tightens the panel bottom.

### nice

- **H10.** The hero paragraph runs about 85 characters per line. Cap it at `max-width: 68ch`.
- **H11.** "Reopen last search" (primary) and "Open shortlist" (outline) are good. Add 4px more gap between them (8 → 12px).
- **H12.** The NCT IDs in the changes list are mono at the same size as the 15px sans, so they look larger. Drop the mono to 14px (the spec says 14) so the x-heights match.

---

## Review (`review-v1.png`)

### must-fix

- **R1. A wall of buttons.** Every row has three stacked 210x36 buttons, so 12 buttons are visible and the four solid ink "Accept" slabs are the darkest, largest shapes on the screen, louder than the quotes and the stage tracks. That's the opposite of the product's argument. Fix: show the full Accept, Edit and Reject stack only on the focused row. On other rows, show nothing, or a muted one-line "a accept · e edit · r reject" hint on hover. Better still, put the buttons as a horizontal group under the quote, at 32px height, so the quote column can widen to the full row (about 860px) and the right gutter disappears.
- **R2. Red on every row.** "Reject" in destructive red text on all four rows, plus "Rejected" in red in the side panel, puts five red words on screen and makes the page look like an error state. Fix: style Reject as a neutral outline button with `foreground` text, and use red only on hover or press. Set "Rejected" in the side panel in `foreground` at 600 weight with the reason underneath. The rejection is a fact, not an alarm.
- **R3. Keycap noise inside buttons.** The 11px mono "a / e / r" at 70% opacity inside each button is unreadable on video and adds 12 tiny glyphs of clutter. Fix: remove the kbd from the buttons. Keep the single keyboard legend under the title, and raise it to 14px with 13px keycaps so it actually reads in the recording.

### should-fix

- **R4. The focused-row ring looks like a card in a list.** The focused row gets a 2px ink outline with rounded corners that sits over the list panel's own border, so the corners clash. Fix: no outline. Use an `ink-tint` row background and a 3px `foreground` left bar, the same geometry as the quote rule, so the screen has one visual language for "this one".
- **R5. The New marker is too weak.** On FoundationOne Liquid CDx, the 4px `eosin-tint` left bar is pale pink on white and invisible in a compressed video, while the "New since your last visit" text carries all the meaning. Fix: make the bar a 3px solid `eosin`, or drop the bar and keep the dot plus the words. Don't use both a tint bar and a focus treatment on the same edge.
- **R6. The change line is typographically noisy.** "Trials  4 trials  to  add NCT05642195" mixes five treatments: a muted label, a regular count, a muted "to", a bold "add" and a mono ID. The grammar is also backwards. Fix: one sentence in 15px sans, "Add trial **NCT05642195**" (mono for the ID only), followed by a muted caption "Trials field, 4 today".
- **R7. Metadata pile-up under the quote.** The source line, the confidence and trigger line, and sometimes a rule box make three or four caption-grey lines in a row. Fix: show confidence only when it's low (0.91 and 0.90 tell a curator nothing). Move "Trigger: used in a trial" into the change line. The source caption stays.
- **R8. The "Flagged by a rule" box** is an outlined box inside an outlined row inside an outlined panel, with the Synthetic pill wrapped mid-sentence. Fix: no border. Use a flat `ink-tint` background with 12px padding, and put the Synthetic pill at the end of the bold label line ("Flagged by a rule  [Synthetic]") with the rule text below.
- **R9. Duplicated demo rows.** Ventana PD-L1 (SP263) appears twice and both FoundationOne rows quote the same sentence, so the list reads as copy-pasted filler. Fix: vary the four visible changes across fields and verbs (add trial, add biomarker, change stage, add drug link), and include one stage change so the eosin-segment stage track appears on this screen.
- **R10. The side panel has four outlines:** the reason box, the rule textarea, two equal-weight buttons and the capability tag. Fix: make the rejected-change block flat `ink-tint` with no border. Make "Discard" a ghost button sized to its content (not 50% width). Make the capability tag plain muted text.

### nice

- **R11.** The "7 proposed changes waiting" subtitle at 16px muted sits only 4px under the 24px title. Give it 6px and set it at 15px so the title-subtitle-legend stack steps down evenly (24 / 15 / 14).
- **R12.** "3 more changes below. Use j to keep going." is a nice touch. Keep it.
- **R13.** The stage tracks all show the same stage ("Regulatory approval") on every row, so on this screen they add little. A varied dataset (R9) fixes that.

---

## Graph (`graph-v1.png`)

### must-fix

- **G1. Label collisions everywhere.** "Vysis ALK Break Apart FISH" runs into "PD-L1 IHC 22C3 pharmDx". "Guardant360 CDx" collides with the eosin "SuperARMS EGFR" label, and an eosin edge cuts through both. "Oncomine Dx Target Test" overlaps "BRAF". "therascreen EGFR RGQ PCR Kit" and "Foundation Medicine" are crossed by edges. "pembrolizumab" is clipped at the right canvas edge. In a judged video, overlapping text looks broken. Fix: (a) give every label a 3px `background`-coloured halo (`paint-order: stroke; stroke: #F6F8FB; stroke-width: 3px`). (b) Show labels only for Diagnostics, biomarkers and the changed subgraph at this zoom, and drop provider, trial and drug labels except for nodes adjacent to the changed one (this is what DESIGN.md already says). (c) Apply collision avoidance or manual offsets for the demo layout. (d) Pin the layout so no node sits within 120px of the canvas's right edge.
- **G2. The tooltip covers the graph's centre.** The 340x370 card sits over the EGFR to KRAS to FoundationOne hub, the densest and most meaningful part of the network, and edges visibly run underneath it. Fix: anchor the card in empty space to the upper right of the selected node (the 560–900 x 180–300 region is mostly free if the graph shifts down about 60px). Better, dock it as the 360px right panel the layout spec already defines, so the whole graph stays visible while the narrator talks.
- **G3. The hero label is truncated.** The changed node is labelled "SuperARMS EGFR" in eosin, cut short and colliding, while the tooltip says "SuperARMS EGFR mutation detection". Fix: use the full name, 14px/600 in `eosin-text`, placed to the lower-left of the node where there is space, with the halo from G1.

### should-fix

- **G4. The EGFR hub is a hairball.** About eight dark 1.5px cross-category edges converge on EGFR and dominate the left half more than the eosin story does. Fix: draw cross-category edges at 1px in `muted-foreground` at 60% opacity, and keep 1.5px dark only for edges touching the selected node. That way the eosin path is the only high-contrast line work.
- **G5. Labels are too small for video.** Node labels at 12–13px (the HTML uses 12, 12.5 and 13) will blur. Fix: 14px/600 for Diagnostic labels and 13px/400 for everything else. Drop 12.5px entirely, because half-pixel sizes render inconsistently.
- **G6. The tooltip's stage row is cramped.** The track, "Clinical / utility" (wrapped) and "since 6 November / 2026" (wrapped) form a three-column micro layout in about 300px. Fix: put the track and "Clinical utility" on one line, with "Since 6 November 2026" as a caption line below.
- **G7. The `$graphLookup` capability tag is set in monospace inside an outline,** which is monospace used as decoration, against the spec (capability tags use the caption sans). Fix: plain 13px muted text, "Graph lookup", or "MongoDB $graphLookup" with only the operator in mono. Drop the border.
- **G8. The trial label "NCT06422546" is in eosin mono.** It's acceptable as a changed node, but with the eosin "Moved to clinical utility" label and the eosin edges, four eosin text items now sit within 200px. Fix: keep the trial label in `foreground` and let the 3px eosin ring and edge carry the change.

### nice

- **G9.** Spread the layout more evenly. The right third is sparse and the left-centre is dense. Increase charge repulsion or hand-tune positions for the recorded frame.
- **G10.** Legend glyphs at 10px are fine. Add 4px more gap between legend items (currently tight against the divider).
- **G11.** The "ctDNA MRD, tumour-informed / Early research" dashed node works well. Keep it.
- **G12.** "Changed since 2 November • 5": put the eosin dot and count in a small `eosin-tint` chip so they read as one unit. That's the one place a chip is earned.

---

## Generic AI tells, summary

| Tell | Where | Verdict |
|---|---|---|
| Pink-washed rows | Home changes list | Present, must fix (H1) |
| Identical rounded cards | Home panels with header bar and right chip | Mild, fix via H3 |
| Badges sprinkled | Synthetic x2, capability tags in headers, keycaps in buttons | Present (Global 3, H4, R3) |
| Monospace as decoration | `$graphLookup` tag, keycaps | Present (G7, R3) |
| Too many outlines | Review side panel, rule box | Present (R8, R10) |
| All-caps eyebrows, middle-dot meta strings | None found | Clean |
| Gradients or shadows | Only the tooltip | Clean |

---

# Round 2 (home-v2, review-v2 / review-v2-full, graph-v2)

## Verdict

| Screen | Verdict | Why |
|---|---|---|
| Home | **Fix first** (small) | The round-one issues are solved. Two must-fixes remain: the stage-track logic and a truncated source quote. |
| Review | **Ship** after the global stage-track fix | Every round-one must-fix landed. The rest is polish. |
| Graph | **Fix first** (small) | Much better. One central label collision and one edge running under the tooltip remain. |

## Fixed since round 1

- **Home.** The pink-washed rows are gone (H1). Rows are now rule-separated, with only the dot and the word. The panel header bar was removed and "Welcome back" opens the panel (H3). Synthetic and Agent Memory merged into one caption (H4). Digest moved to the left column (H2). "Mark all as seen" sits on the heading line (H9). Low confidence has its own line (H8). The label now reads "Moved to clinical utility" (H6). The picker fits on one line and the Alerts count style is consistent (Global 2).
- **Review.** Full buttons appear only on the focused row, and other rows have quiet text actions (R1). Reject is neutral (R2). The keycaps are out of the buttons (R3). The focus is an ink-tint background plus a left ink bar, with no ring (R4). The change line reads as one sentence (R6). Confidence shows only when it's low (R7). The rule flag is a flat wash with the Synthetic pill inline (R8). The rows are varied (R9). The side panel's rejected block is flat and Discard is a ghost button (R10).
- **Graph.** The tooltip is moved off the hub (G2). The full hero label is shown (G3). The hub edges are calmer (G4). Labels are larger (G5). The tooltip's stage row is clean (G6). The `$graphLookup` text has no border (G7). The trial labels are in ink (G8). The "5 changed" chip is the one earned chip (G12). The footer aligns.
- **Stage track** is now 16x10, and it finally reads at video size.

## Global

- **must-fix: G2-1. The stage track's visual logic is inverted.** Passed Early research segments (Discovery, Assay development) now draw as **hollow outlined boxes**, while future, not-yet-reached segments are **solid grey**. Everyone reads hollow as "not done" and solid as "done", so on Review (Guardant360, SuperARMS, FoundationOne) the track appears to say the first two stages were skipped. This is the one bold element and it sits on all three screens. Fix: make future segments hollow (`card` fill, 1px `border` outline). Make passed Early research segments a solid `ink-tint` wash with no outline (or a 1px dashed `foreground` outline only when Early research is the current stage, which ties it to the Early research badge). Passed later stages stay solid `foreground`.
- **should-fix: G2-2. "Changed" is now the same story told in four different places.** Home shows an eosin segment in the alert track, the Graph tooltip shows one, but Review's SuperARMS row (marked New, just moved to clinical utility) draws the same segment in plain ink. Fix: use the eosin newly-filled segment wherever that Diagnostic's stage change is unseen, including on Review.
- **nice: G2-3.** The user shows as "Rowan (you)" on Graph but "Rowan" on Home. Pick one.

## Home (v2)

### must-fix
- **HM2-1. A source quote is truncated with an ellipsis.** The second alert's quote ends "...predictors of unfavorable…". The product's whole claim is that quotes are verbatim, and a judge watching a serif quote cut mid-phrase will read it as edited. Fix: show the full quote (it's 4 lines, and there's about 170px of free space under the right column now). Or, if it must be clamped, end on a whole clause and add a separate muted "Full quote" link beneath, never an ellipsis inside the serif.

### should-fix
- **HM2-2. A column of pink words.** Four "Changed" plus one "New" in 15px/600 `eosin-text` stack in a vertical stripe at x=127. It's much better than the pink rows, but eosin is still the loudest thing in the left panel. Fix: set "Changed" at 400 weight and keep "New" at 600. Weight then separates New from Changed, and eosin stays the signal.
- **HM2-3. Repetitive change rows.** SuperARMS appears twice and FoundationOne twice (Liquid and tissue). In a 5-row list that reads as filler. Fix: collapse the two SuperARMS rows into one ("moved to clinical utility and used in trial NCT04769388"), or swap in a different Diagnostic.
- **HM2-4. The alert footer is cramped.** The source caption wraps to two lines ("NCT06422546, / data as of…") because the Play briefing button and Dismiss share its line. Fix: put the caption on its own line and the actions on the next line, left-aligned, with 12px top margin.
- **HM2-5. The columns are now unbalanced the other way.** The right column ends at about y=828 and the left at about y=988. That's acceptable, but showing the full quote (HM2-1) fixes both at once.

### nice
- **HM2-6.** The alert summary "…ctDNA testing for EGFR." leaves a one-word widow ("EGFR."). Rephrase or add `text-wrap: pretty`.
- **HM2-7.** "Reopen last search" / "Reopen shortlist" repeat the verb. Use "Reopen last search" and "Open shortlist".

## Review (v2)

### should-fix
- **RV2-1. The capability tag is still an outlined chip** ("Agent Memory, procedural") at the bottom of the side panel. It's the last bordered badge on the screen. Fix: plain 13px muted text, "Uses Agent Memory (procedural)".
- **RV2-2. The PMID spacing is odd.** "PubMed, PMID  42985469" shows a double-width gap before the mono number, so the mono ID looks detached. Fix: one regular space, and set "PMID 42985469" entirely in mono, or keep "PMID" in sans with a non-breaking space.
- **RV2-3. Dead right gutter in the rows.** With the buttons moved under the quote, every row is about 910px wide but the content stops near x=730, leaving about 250px of empty card per row. Fix: narrow the main column to about 780px (a quote measure of about 68ch still fits) and give the side panel the extra width (about 420px), which also stops the rule textarea from wrapping.

### nice
- **RV2-4.** The keyboard legend under the title is still 13px with 12px keycaps. Use 14/13 so it reads in the recording.
- **RV2-5.** The unfocused text actions "Accept  Edit  Reject" at 600 weight repeat on every row. Set them at 400 muted, with ink on row hover, so the column is quieter still.

## Graph (v2)

### must-fix
- **GR2-1. Central label collision.** The "FoundationOne CDx" label sits on top of the eosin edge from NCT04712877 and on the node itself, right in the middle of the frame. "Agilent Resolution ctDx FIRST" is also crossed by three edges. Fix: offset the FoundationOne CDx label to the right of its node (x+14, y+4) with the 3px `background` halo, and move the Agilent node about 40px up so its label sits in clear space.

### should-fix
- **GR2-2. An edge runs under the tooltip.** The edge from SuperARMS heads right and disappears under the card at about (1013, 310), which reads as a clipping bug. Fix: hand-place that neighbour inside the visible canvas, or end the edge before the card.
- **GR2-3. Unlabelled hollow provider squares** (four of them, at about (240,278), (790,528), (420,658), (140,778)) look like empty checkboxes or failed renders. Fix: label the providers adjacent to visible Diagnostics (Roche, QIAGEN, Foundation Medicine), or hide providers at this zoom and keep them in the legend only.
- **GR2-4. Tight bottom edge.** "sotorasib", "LUAD, lung adenocarcinoma" and a provider square sit within 15px of the canvas bottom, and "Ventana MET (SP44) RxDx Assay" ends at x≈1417. Fix: 40px safe inset on all sides of the layout.
- **GR2-5. Three separate eosin stories** (SuperARMS, ctDNA MRD, FoundationOne Liquid to FoundationOne CDx) compete for attention. That's correct, since there are 5 changes, but the selected one should win. Fix: draw the eosin edges of unselected changes at 1.5px and 70% opacity, and the selected node's edges at 3px solid.

### nice
- **GR2-6.** The tooltip writes "Used in trial NCT06422546 with osimertinib." with the ID in sans. Use mono for the ID, as everywhere else.
- **GR2-7.** The tooltip source caption leaves "2026" as an orphan line. Shorten it to "data as of 12 Nov 2026" in this card.

## Remaining AI tells

Mostly gone. What's left: one outlined capability chip (RV2-1), a repeated per-row action strip (RV2-5), an ellipsis-truncated quote (HM2-1), and duplicate entities in the Home change list (HM2-3). No pink washes, eyebrows, middle-dot meta or decorative mono remain.

---

# Round 3 (glass): home-v4 and logo.svg

Rendered logo: `shots/logo-v1.png` (400x120, headless Chrome).

## Verdict

**Fix first.** It's polished and calm, and the type and content work from rounds 1 and 2 survived intact. But it reads as a well-made **generic glassmorphism SaaS template**, not a pharma or diagnostics medical-affairs tool. There are three reasons. The "tissue field" is invisible: it reads as a pastel aurora gradient, not cells. The glass therefore has nothing to be glass over, so it looks like off-white cards with big radii and soft shadows. And the screen leans on the template tells of 2024–25: icons in soft circles beside headings, an icon on every element, pill controls with drop shadows, and an app-icon squircle logo.

Big pharma and diagnostics companies present their digital tools (think Roche navify, Illumina, Thermo Fisher, AstraZeneca medical-affairs portals) as **restrained, confident and image-led**. They use one strong piece of real scientific imagery, generous white space, flat surfaces, a single brand colour, and a wordmark-led logo. "Flashy" in that world means one striking scientific image, not translucency everywhere. So the fix is **more field, less glass**.

## must-fix

- **GL-1. The tissue field doesn't read as tissue.** Five to seven blobs blurred 80–120px are a gradient mesh, and only about 72px gutters and 24px gaps of it show between the panels anyway. Nothing in the frame says "cells". Fix:
  - Replace the blobs with a **defocused micrograph**: 40–70 "nuclei" (ellipses 14–36px, slightly irregular, random rotation) in haematoxylin `#3B3F8F` at 35–55% opacity, blurred only **4–8px**. Defocused, not dissolved: the eye must still count them.
  - Cluster the nuclei in an organic band, and lay them over 4–6 eosin cytoplasm patches (`#E7A3BE`, 220–420px, 30% opacity, blur 30–40px), plus one or two pale methyl-green patches at 15%.
  - A real H&E tile (a CC-licensed TCGA LUAD crop, blurred about 6px and colour-matched to ink and eosin) is better still, and reads as pharma instantly.
- **GL-2. Give the field a stage, or it will never be seen.** Add a **hero band**: a 260–300px tall strip of the field directly under the top bar at full strength. Lay "Welcome back, Rowan" over it on the one hero glass panel, overlapping the band's lower edge by about 120px so nuclei visibly pass under the frosted edge. That overlap is what sells glass. Below the band, fade the field to about 30% strength so the working panels sit on a calm ground.
- **GL-3. Too much glass. Glass only works where something is behind it.** Fix: use frosted glass on **two surfaces only**: the top bar (`glass-strong`, 88%) and the hero welcome panel (white 64%, `blur(24px) saturate(160%)`, 1px `#FFFFFFCC` edge). Make the Changes, Digest and Alerts panels **solid `card` white** with a 1px `border` rule and the ink shadow cut to `0 8px 24px -16px #23264F1F`. They're reading surfaces, and flat white makes them look more clinical and premium, not less.
- **GL-4. Two left edges in one panel.** The 32px icon circles push the "5 changes since 2 November" heading, its description and every change row to x≈151, while the welcome text in the same panel sits at x≈107. Digest does the same (circle at 97, text at 141). It looks misaligned in every frame. Fix: remove the heading circles (see GL-6) so all text in a panel shares one left edge. If an icon stays, hang it in the gutter (icon at x−28) so the text edge holds.
- **GL-5. The active nav pill fights the logo.** The solid `ink-deep` Home pill, with a white label and a shadow, sits beside the solid ink logo tile, so two dark rounded squares butt together at top-left. It's the heaviest object on the screen and it reads as a button. Fix: make the active state an `ink-tint` (#E3E5F3) pill with `foreground` text at 600 and no shadow, or plain ink text with a 2px `foreground` underline 6px below the baseline.

## should-fix

- **GL-6. Icon-in-a-soft-circle headings** (Changes `history`, Digest `inbox`, Alerts `bell`) are the most recognisable template tell on the screen (the "feature card" bubble). Fix: drop the circles. Either remove heading icons entirely (the headings are clear words), or set the icon at 18px, `foreground`, 1.75 stroke, inline before the heading text with an 8px gap.
- **GL-7. Too many icons.** I count about 25: 8 in the nav, 4 on buttons, 3 in headings, 2 on captions, the picker, Add, Dismiss and more. When everything has an icon, none of them signals. Fix: keep the nav icons (that's the "real iconography" Luis asked for) at 16px in `muted-foreground`. Keep icons on primary actions (Reopen, Play). Remove them from "Reopen shortlist", "Mark all as seen", the memory caption and the source captions (`flask-conical`).
- **GL-8. Top-bar crowding.** The logo, 8 icon-plus-label nav items, the Add pill, the team picker with its Synthetic pill, and the avatar fill 1440px with gaps of about 10px between nav items. Fix:
  - Move **Jobs** and **Categories** into the avatar menu or a "More" item, leaving 6 items with 20px gaps.
  - Make "Add a diagnostic" a ghost button with a `plus` icon (no pill or shadow).
  - Drop the `users` icon from the team picker.
  - Make every control in the bar 36px tall with no drop shadows. Right now the Add pill, the team picker and the avatar each float with their own shadow, which reads cheap.
- **GL-9. Outline buttons with drop shadows** ("Reopen shortlist", "Mark all as seen", "Play briefing") look like a template. Fix: outline buttons get a 1px `border` and no shadow. Only the primary button keeps its subtle ink gradient and a 0 1px 2px shadow.
- **GL-10. The logo is a startup app icon, not a pharma mark.** A gradient squircle with a lowercase "d" is the default shape of a thousand SaaS logos (Discord, Dribbble, Deel). The "stained cell" idea doesn't come through: at 32px it reads as a "d" with a red record dot. Problems: `#A9A5EC` lilac is an off-palette colour, the gradient breaks "no gradients", and the two-tone wordmark ("Provida" in faded grey) looks half-disabled. Fix:
  - **Mark:** a flat ink **glass-slide silhouette**, a 2.6:1 rounded rectangle (3px radius) with the left 28% frosted as the slide's label end (ink at 25%). On the clear end, place one irregular cell outline (ink, 2px stroke) holding an `eosin` nucleus offset to the lower right. It's ownable, it ties directly to "Stained slide", and it stays legible at 24px as "slide plus pink dot". Remove the gradient and the lilac.
  - **Wordmark:** a single colour, `ink-deep`, with "Dx" at 700 and "Provida" at 500, tracking −0.01em. The weight contrast replaces the colour contrast. Optionally add a 1px vertical rule and the descriptor "Diagnostics intelligence" in 13px `muted-foreground` beside it on Home only. Pharma tools almost always carry a descriptor.
- **GL-11. Panel radius.** At 18px, panels with 6px buttons and 3px chips read soft and consumer. Fix: 12px for panels and 6px for controls, so it reads more instrument than app.
- **GL-12. Carried over from round 2.** There are still two SuperARMS rows and two FoundationOne rows (HM2-3). The SuperARMS "moved to clinical utility" row also wraps its NCT ID onto a second line and breaks the list rhythm. Fix: merge the two SuperARMS rows ("moved to clinical utility; used in trial NCT04769388") and keep every row on one line.
- **GL-13. Avatar initials "RO"** are the first two letters of a first name, which looks like a bug. Fix: "R", or full initials (for example "RK"), in a 28px `ink-deep` circle with no ring or shadow.

## nice

- **GL-14.** Once the hero band exists (GL-2), add one confident number as the flash: "5" at 56px/700 `foreground` beside "changes since 2 November", in the hero, not in a card. A big real number on a scientific image is how pharma dashboards earn "wow".
- **GL-15.** The `microscope` icon at 16px reads as a squiggle. At that size `test-tube-diagonal` or `scan-search` is cleaner for Diagnostics.
- **GL-16.** The Synthetic pill in the team picker could be a 6px dotted ring dot with a tooltip, since the hero caption already says "Synthetic".

## What improved and should stay

- The stage track logic is fixed: future segments are hollow and passed Early research segments are a pale fill (G2-1).
- "Changed" is now at regular weight and "New" is bold (HM2-2).
- The alert quotes are complete, with no ellipsis (HM2-1).
- Play briefing and Dismiss on the alert's status line save about 50px per alert and read well.
- The primary button's subtle ink gradient feels premium. Keep it as the one gradient.
- Contrast on glass is fine at 72% over the current faint field (body above 7:1, captions above 5:1). If GL-1 darkens the field, keep the hero glass at 64% or more and check `muted-foreground` captions over the darkest nucleus. Raise to 72% if any caption drops below 4.5:1.

## Remaining AI tells (round 3)

Pastel blob background, icon-in-circle headings, icons on everything, a shadowed pill on every control, an app-icon squircle logo with a two-tone wordmark, and an oversized panel radius. Fix GL-1 to GL-10 and it stops looking like a template.

---

# Round 4 (graph hero): home-v5 and logo.svg v2

Rendered logo: `shots/logo-v2.png` (top row at 60px height, bottom row at 32px, and the mark alone at 32px).

## Verdict

**Right direction, fix first.** This is the first Home that is memorable in a demo video. A dark haematoxylin band with the team's own network glowing, and eosin paths showing exactly what changed, is a frame a judge will remember, and it shows the product rather than decorating it. Three things hold it back:

1. **The lower grid is broken.** There are three different right edges and the panel tops are misaligned.
2. **The hero background is drifting toward the stock "AI network on dark bokeh" image.** It needs to read as H&E pathology, not cyberspace.
3. **The welcome panel is overloaded and brought back fixed issues.** The capability chips, the "Update:" label, the wrapped captions and the "RO" avatar are back.

## must-fix

- **R4-1. Grid alignment below the hero.** Today:
  - The welcome panel spans x≈799–1399.
  - Digest spans x≈849–1367.
  - Alerts spans x≈73–823. Its right edge passes *under* the welcome panel's left edge (799), so the two overlap horizontally by about 24px.
  - Alerts starts at y≈605 and Digest at y≈683, so the tops don't align.

  Fix: use one 12-column grid inside 72–1368 with a 24px gutter.
  - Welcome panel: columns 8–12 (x=848–1368, 520px wide), the same column as Digest.
  - Alerts: columns 1–7 (x=72–824).
  - Digest: x=848–1368.

  Let the welcome panel overlap the hero's bottom edge by a fixed 96px. Alerts then starts at hero bottom + 24px, and Digest starts at welcome bottom + 24px. Alerts' top then aligns with the welcome panel's overhang, and every right edge lands on 1368, the same as the top bar's content edge.
- **R4-2. Make the hero read as tissue, not tech.** A glowing node-link network over purple bokeh, with a radial spotlight in the centre, is the default stock visual for "AI" and "blockchain". What makes this one DxP is pathology. Fix:
  - Remove the radial spotlight.
  - Replace the uniform purple bokeh with an H&E field: 40–60 haematoxylin nuclei (`#5A5FB0`, 14–30px, 25–35% opacity, blur 3–6px) over 4–5 large eosin cytoplasm patches (`#D2457A` at 10–14%, 300–500px, blur 60px). The dark band then has a warm pink undertone in places.
  - Keep the band gradient `#23264F` to `#171A3D` at a 160° angle.
  - Result: the background says "slide under a microscope", and the eosin paths still win because they're saturated and sharp.
- **R4-3. The welcome panel is doing three jobs.** The greeting, the memory recap, two buttons and the whole 5-row change list are packed into a 600px-tall floating panel, with change rows at about 14px and the caption wrapping to an orphan ("update."). It's the densest object on the page and it sits on the most important visual. Fix: keep only the greeting, the recap, the memory caption and the buttons in the docked panel (target about 280px tall). Move "5 changes since 2 November" to the top of the left column as its own solid panel above Alerts. It's the written companion to the hero's eosin paths, and it reads better at full width with one-line rows.
- **R4-4. Regressions from rounds 2 and 3:**
  - "Agent Memory (public preview)" is back as an outlined chip in the welcome panel's top-right (RV2-1/GL-7). Make it plain 13px muted text in the memory caption line.
  - "MongoDB $graphLookup" is an outlined chip inside the hero legend. Make it plain 12px text at 60% white at the far right of the legend row, with no border.
  - "Update: moved to clinical utility" has returned (HM2-6). Use "Moved to clinical utility".
  - The Synthetic pill appears twice (top bar and welcome panel). Keep the welcome panel's caption text and remove its pill.

## should-fix

- **R4-5. Hero labels.**
  - Five white mono NCT labels on dark (NCT04769388, NCT06422546, NCT04712877, NCT07921888) add mono noise and pull the eye to IDs instead of the diagnostics. Drop the trial labels in the hero (they show on hover). Label only the changed diagnostics and the Team's biomarkers, as DESIGN.md says.
  - "NCT06422546" starts at x≈40, against the hero's left edge. Keep a 48px safe inset.
  - "SuperARMS EGFR mutation detection" and "NCT04712877" are crossed by links. Add a 3px `#1B1E45` halo (`paint-order: stroke`) to every hero label.
  - Use 14px/600 white for diagnostic labels and 13px/600 in the biomarker green for EGFR and KRAS.
- **R4-6. Unlabelled nodes.** About 10 lavender diagnostic circles, 3 drug triangles and 2 hollow provider squares carry no label. In the hero that's fine as texture, but the hollow provider squares look like broken renders on dark. Remove providers from the hero. Make unlabelled diagnostics 70% opacity with a 4px glow, and give labelled or changed ones 100% opacity with an 8px glow, so there's a clear foreground and background. osimertinib is in the SuperARMS story but its triangle is unlabelled. Label it.
- **R4-7. The hero title is too quiet.** "Your team's neighbourhood" at about 15px/600 is the heading of the most important frame. Make it 19px/600 white, and add a 13px caption at 70% white: "Diagnostics, biomarkers and trials your team follows. Pink shows what changed since 2 November." That caption also replaces the legend's "Changed since 2 November" item.
- **R4-8. The Alerts two-up columns are too narrow.** Two alerts side by side in a 750px panel give a serif quote measure of about 36 characters (5 lines), uneven heights, and the source caption wraps "12 / November 2026". Once R4-3 moves Changes above, stack the alerts vertically in the left column (as in v2), which gives a quote measure of about 65 characters. Put Play briefing and Dismiss back on the status line (that worked in v4).
- **R4-9. Logo: it reads as a toggle switch.** At 32px the mark is a filled block on the left and a round knob with a dot on the right, which is exactly toggle-switch or webcam geometry. The diagonal hatching on the label end reads as a "disabled" pattern. And the cell doesn't read as a "d", so drop that claim. Fix:
  - Make the label end a flat 22% ink fill with no hatch lines.
  - Make the cell clearly non-circular: an ellipse about 16x11 within the 48x22 slide, rotated −12°, with a slightly irregular outline.
  - Offset the eosin nucleus to the lower-left inside the cell, not centred.
  - Add a second, fainter cell (ink at 30%, no nucleus) clipped by the slide's right edge.
  - Two cells, one cut off, reads as "tissue on a slide" instead of a control.
  - The wordmark (one colour, weight contrast 700/500) is good. Keep it.
- **R4-10. The avatar still says "RO".** It's carried over from GL-13. Use "R" or real two-letter initials.

## nice

- **R4-11.** The one-time eosin pulse on load is the video's best moment. Time it to start about 600ms after the hero paints, so the recording catches the network still and then the change lighting up.
- **R4-12.** "Open the graph" (white outline on dark) works. Add the `arrow-right` icon after the label instead of the `waypoints` icon before it, so it reads as a destination.
- **R4-13.** The hero's bottom edge is a hard horizontal cut. A 40px gradient from `#171A3D` to the page `background` softens the transition without making it look like a template.
- **R4-14.** Panel radius is still about 16px. Use 12px (GL-11).

## What works and should stay

- The dark hero with stain-coloured nodes and eosin change paths. It is the product's argument made visual. Keep it as the one bold moment.
- The welcome panel docked over the hero's right edge, once it's slimmed down (R4-3) and on the grid (R4-1).
- The top bar is cleaner: the active pill is ink-tint, Categories and Jobs moved into More, and there's a one-line team picker.
- The stage track logic, the alert quotes and the Digest are all solid.
- The logo now looks like a slide and the wordmark is credible. It's one iteration (R4-9) from being a real mark.

## Remaining AI tells (round 4)

A glowing network over bokeh with a centre spotlight (R4-2), outlined capability chips (R4-4), mono ID labels as hero decoration (R4-5), and the toggle-shaped logo (R4-9). The heading circles, pink rows, shadowed pills and gradient squircle are gone.

---

# Round 5 (confirmation): home-v6 and logo-v3

Decisions that override round 4: keep "Update:" on the alert, keep the "RO Rowan" avatar and name, and show capability tags as plain caption text with a database icon.

## Verdict: **Ship.** Nothing blocks shipping.

## Round 4 must-fixes

- **R4-1 Grid: landed.** The welcome panel, Alerts and the top bar's content now share the 1368 right edge. Changes and Digest (x=73–823) and the welcome panel and Alerts (x=849–1368) sit on one two-column grid with a 26px gutter, and Changes and Alerts start on the same top (y≈566). The welcome panel now sits inside the hero instead of overhanging it, which is cleaner than the overlap I proposed.
- **R4-2 Hero reads as tissue: mostly landed.** The spotlight is gone and the band has a warm plum and eosin undertone, so it reads as H&E rather than cyberspace. The background dots are still mostly round and purple (see the nice item below).
- **R4-3 Welcome panel slimmed: landed.** It now holds only the greeting, recap, memory caption and two buttons, at about 275px. Changes is its own full-width panel with one-line rows.
- **R4-4 Regressions: landed or resolved by decision.** Capability tags are plain caption text, the Synthetic pill is gone from the welcome panel, and "Update:" stays by decision.
- **Also fixed:** the NCT labels are out of the hero, the hero title is 19px with an explanatory caption, osimertinib is labelled, providers are out of the hero, the alerts are stacked with a wide quote measure, and Play briefing and Dismiss are back on the status line.
- **Logo (logo-v3):** the toggle reading is gone. The mark alone is a "d" formed by a cell outline with an eosin nucleus, which holds at 16–32px and works as the favicon. The slide lockup with a clipped second cell reads as "slide with tissue". It's credible as a brand mark.

## should-fix (post-demo, not blocking)

- **R5-1.** There are still two SuperARMS rows in "5 changes" (HM2-3). Merge them if the data allows.
- **R5-2.** The top bar now shows both "Jobs" and "More". Move Jobs into More, or remove More if it only holds Categories.
- **R5-3.** The top-bar lockup uses the bare "d" mark while the slide lockup exists. Decide which is the primary lockup and use it everywhere: the slide lockup in the top bar at 1440, and the "d" mark for the favicon and small sizes.

## nice

- **R5-4.** Hero background nuclei: vary the size (14–30px) and make them slightly elliptical, so they stop reading as bokeh.
- **R5-5.** The 12–13px legend at 70% white along the hero bottom is small for a compressed video. Use 13px at 80% white.

---

# Review v4 (against Home v7)

Screens: `shots/review-v4.png` (1440x1000 frame), `shots/review-v4-full.png`. Reference: `shots/home-v7.png`.

## Verdict

**Ship after one fix.** Review now reads as the same product as Home v7. It shares the top bar, panel radius and shadow, lucide icons, the faint tissue field in the gutters, the plain caption capability line, the stage track and the serif quotes. Keeping the dark band for Home only is correct ("every other page stays calm"). The one blocking issue is about the story, not the styling: the rule's effect isn't visible in the recorded frame.

## must-fix

- **RV4-1. The flagged changes are below the fold.** The rule panel says "It flags 2 of 7 pending changes" and lists FoundationOne CDx (MALAT1) and Oncomine Dx Target Test (GATA5), but neither row appears in the 1000px frame. The first flagged row (FoundationOne CDx) starts at y≈1300. The demo beat ("reject once, DxP learns a rule, the rule flags matching changes") never lands on screen. Fix: sort the list as the focused low-confidence row, then the 2 rows flagged by your rule, then the rest. Change the subtitle to "Low-confidence first, then the 2 your new rule flagged." Also make each flag-list item in the rule panel a link that scrolls to and focuses its row.

## should-fix

- **RV4-2. The focused-row geometry is clumsy.** The focused row is a floating card (12px radius, about 0 12px 32px shadow) inset 9px inside the list panel, so you get a card inside a card. Its 4px ink left bar is a separate straight bar that starts about 16px below the card's rounded top corner (x≈83, y≈280 versus the card top at y≈264), so the bar and the radius visibly disagree. Fix: either (a) a flush row with no inset, no shadow and no radius, an `ink-tint` (#EEF0FA) background, and a 3px `foreground` bar running the full row height on the panel's inner edge; or (b) keep the lifted card and draw the bar as `box-shadow: inset 3px 0 0 #23264F` so it follows the radius. Option (a) matches Home's calm list style better.
- **RV4-3. Three left-bar idioms on one screen.** The quote rule (3px `ink-tint`, meaning the source speaks), the focused-row bar (4px ink, meaning selection) and the rule statement bar (3px ink, meaning DxP's rule) are three left bars with three meanings. Fix: keep the bar for quotes only. For the rule statement, drop the bar and set it at 19px/600 inside a flat `ink-tint` block with 16px padding, or use the dark treatment in RV4-4. The focused row uses its background (RV4-2a).
- **RV4-4. The page is plain next to Home.** A white queue and a white side panel read as an admin form. Lift it with one deliberate moment, the learned rule. Fix: render the "Rule on" block (from the green dot down to "Turn off / Open rules") as a dark card in Home's hero palette: an `ink-deep` to `primary` gradient at 160°, 12px radius, white rule text at 19px/600, the methyl-green dot with "Rule on" in 13px at 80% white, the flagged list in 15px white with `flag` icons, and the Agent Memory caption at 70% white. Keep the Rejected block above it flat and light. This echoes the Home hero, ties the two pages together, and gives the video a strong second frame. No glow and no pulse here; Home keeps the motion.
- **RV4-5. Icons on everything again.** Every row carries a field icon (stethoscope, link, flask, waypoints) and a `file-text` icon before every source caption, which adds about 10 small icons to the list. Fix: remove the `file-text` icon from the source captions (the source name already says what it is). Keep the field icons but check them against DESIGN.md: Biomarker should be `dna`, but MALAT1's row shows a waypoints-like glyph. Use 16px in `muted-foreground` so they sit behind the words.
- **RV4-6. Two flag styles, three flagged rows.** Ventana PD-L1 has "Flagged by a rule [Synthetic]" with a long explanation (a different, team rule), and FoundationOne CDx has "Flagged by your rule: cell-line or animal study". With the panel saying "2 flagged", a viewer counting flags gets three. Fix: style the team rule's flag as muted ("Team rule [Synthetic]" in 13px `muted-foreground`, no wash) and keep the `ink-tint` wash and `flag` icon only for flags from *your* new rule, so the two sets read differently.
- **RV4-7. Dead right gutter.** The quotes stop at about x≈690 inside an 850px-wide list, the same issue as RV2-3. Fix: reduce the list panel to about 780px and widen the rule panel to about 440px. The rule statement then sits on two lines instead of wrapping awkwardly.

## nice

- **RV4-8.** The keyboard legend (12px keycaps, top-right of the list panel) is too small for the video and reads like a form hint. Set the keycaps at 13px with labels at 14px, or move it under the subtitle on one line as in v2.
- **RV4-9.** The subtitle mixes a bold fragment ("7 proposed changes waiting.") with regular text. Bold the number only ("**7** proposed changes waiting"), which reads more like a product than a form.
- **RV4-10.** The rejected block's "Sam, just now" line could carry the 20px avatar circle used in the top bar. It's a small, human touch that's consistent with Home.

## What works and should stay

- One product: the same top bar, the "SA Sam" avatar pattern, panels, icons, caption capability lines and stage tracks as Home v7.
- The focused row clearly leads: full Accept/Edit/Reject buttons with icons and an ink primary, while other rows have quiet text actions. The hierarchy is right.
- Reject is neutral at rest. Low confidence sits in ochre on its own line.
- The rule panel's narrative order (Rejected, then the rule, then what it flags, then Memory) is exactly the demo story.
