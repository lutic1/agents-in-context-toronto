# Graph v4: graphic design critique

Reviewed: `shots/graph-v4.png` against `shots/home-v7.png`, `shots/review-v5.png`, `DESIGN.md` and `key-graph.html`.

## Verdict: fix then ship

The page now belongs to the same product as Home v7 and Review v5. The top bar, logo, nav pill, counters, team picker and avatar match exactly. The glass is used where DESIGN.md allows it: the toolbar, the legend and the docked side panel. The side panel is the strongest part of the page: a clear title, the eosin "Changed" line, a stage track whose fifth segment is eosin because the stage just advanced, a serif quote with a mono NCT source, and a highlighted "Shares EGFR with therascreen…" row. It reads like a real medical-affairs tool.

The canvas is the weak part, and this page is the video's climax. On camera it reads as a light, even hairball. Every node, label and link has about the same weight. The four pink "New link" paths are the loudest marks on screen, so they pull the eye away from the story the narration is telling (plasma test, then EGFR, then tissue test). Several nodes, osimertinib among them, are drawn underneath the glass panels. Next to Home's dark glowing hero it looks like the quieter page, which is backwards for a climax. Everything that needs fixing is in the composition. The system and tokens are right.

## Must-fix

1. **Make the focus path the hero of the canvas.** When SuperARMS is focused, dim everything outside its two-hop neighbourhood to about 30% opacity, labels included. Draw SuperARMS → EGFR → therascreen EGFR RGQ PCR Kit as a 3px ink stroke on a 10–12px `ink-tint` halo. Right now it is a 2px line with a faint lavender halo, and it is barely heavier than the other cross-category links. Size the three path nodes up: SuperARMS and therascreen at 16px (the spec maximum), and EGFR at 26px with its label in heading weight. A viewer should see the path within one second without reading anything.
2. **Pull the layout into the visible canvas.** The SVG lays nodes out across the full 1400px, but the side panel covers x > 1000. The whole ALK and MET cluster (Ventana ALK, Vysis ALK, Ventana MET, alectinib, the ALK and MET biomarkers) is hidden under the glass. Links run off to the right edge and stop dead (from Oncomine and from FoundationOne Liquid CDx). This looks like a cropping bug, not depth. Lay the graph out inside roughly x 40–980 and y 210–870, or drop the off-canvas nodes from this focused view.
3. **Unhide osimertinib.** Its label (y 49–73) sits behind the toolbar, so on screen it is an unlabelled blue triangle under the header. The side panel says "response to osimertinib" and the pending proposal is about osimertinib, so the viewer has to be able to find it. Move it below the toolbar and give it a label.
4. **Remove the dashed selection ring on SuperARMS.** In DESIGN.md a dashed outline means Early research, and the MRD node right next to it uses that meaning. Using a dashed ring for "selected" on a clinical-utility test contradicts the legend on camera. Mark selection with a solid 1.5px ink ring outside the eosin ring, or let the halo and the dark-bordered label do that job.
5. **Quiet the change layer so it supports the focus instead of competing with it.** Keep the four new links eosin, as the spec requires. Inside the dimmed context, though, draw them at 2px and leave out their "New link NCTxxxx" pills: the legend and the side panel already pair the colour with a word. Keep the pills only on the two trials connected to the focused node (NCT06422546 and NCT04769388). That takes the on-canvas pink labels from 6 to 3.
6. **Label clutter and collisions.** Labels sit on top of links in several places. The "therascreen EGFR RGQ PCR Kit" pill covers the focus path itself. Links cross under the "FoundationOne Liquid CDx" and "Oncomine Dx Target Test" pills. The EGFR pill sits off to the left of its node and the label is easy to lose. Place labels away from incident edges, so no pill sits on the focus path. Label the hubs (EGFR, KRAS) larger than the leaves.

## Should-fix

- **Add one "Focus path" entry to the legend**: an ink line with a halo, titled "Shared biomarker". It is the one encoding on the canvas that the legend leaves out, and it is the one that carries the story.
- **Give the canvas some depth to match Home.** DESIGN.md asks for a defocused micrograph at half strength behind the Graph. At this opacity the blurred nuclei read as grey smudges on the lens (see around 400,130 and 520,295), not as tissue. Either make them slightly larger and more clearly cell-like, or remove the darkest few. A very soft radial ink-tint vignette centred on EGFR would also help pull the eye in.
- **Close the dead space in the side panel.** There is about 120px of empty glass between the proposed-change box and the buttons. Either top-align the actions under the content or use the space for a compact "Shared with therascreen" comparison (sample type plasma vs tissue, each with its stage track). The comparison makes the cross-category point a second time, in words.
- **Fill the empty canvas areas.** Bottom-centre (x 600–1000, y 760–880) and the band right under the toolbar are empty, while the left third is crowded. Rebalancing the layout in must-fix 2 should fix this.
- **Fix the evidence-quote rule colour**: it is `#D9DCF0`, and the token is `ink-tint` `#E3E5F3`. The stage-track Early research segments also use `#D9DCF0`. Use the token, or add `#D9DCF0` to DESIGN.md as a token.
- **Keep the footer credit line inside a 900px recording frame.** In the shot it is clipped mid-sentence.

## Nice-to-have

- **Animate the focus once when the page loads**: the context dims, then the path draws from SuperARMS to EGFR to therascreen in about 600ms, then the eosin pulse fires. This is the climactic beat for the video. Skip it under reduced motion.
- **Hover on a link shows a small glass tooltip** with the source quote in the serif, so the "every value has a source" idea reaches the graph too.
- **Give the "Changed" label pill on SuperARMS an `eosin-tint` background.** The spec allows tint behind a single chip, and this would set apart the one focused, changed node.
- **Show the plasma vs tissue category as a small caption** under the two path labels ("plasma ctDNA", "tissue"), so the cross-category point can be read off the canvas.

## Checks that pass

- **Top bar, logo, nav pill, counters, team picker with the Synthetic badge, and avatar** are identical to Home v7.
- **Typography**: Atkinson Hyperlegible Next across the UI. Source Serif 4 appears only in the evidence quote. Mono appears only on NCT IDs, on the canvas, in the source line and in the connection rows. Everything is sentence case.
- **Eosin is used only for new or changed**: rings, links, stage segment, "Changed", "New" and "New link" text in `eosin-text`. No pink buttons or fills.
- **Node shapes and colours follow the spec**: circle, rounded square, diamond, triangle, hexagon, hollow square, dashed Early research. Every type can be told apart by shape.
- **One primary button in the panel.** One capability tag (MongoDB $graphLookup) in the legend. Icons are lucide, each paired with a label.
- **No generic-AI tells.** No gradient text, no icon circles, no emoji, no purple used outside the logo.

---

## Round 2: graph v5b

Reviewed: `shots/graph-v5b.png` (1000px tall) and `shots/graph-v5b-900.png` against round 1, `key-graph.html` and `DESIGN.md`. The top bar's Alerts count and the nav order are left for the global pass. The path-draw animation was declined under the one-motion rule, so it is not raised again.

### Verdict: fix then ship (one must-fix left)

This is a big step forward. The ink path SuperARMS → EGFR → therascreen now reads first, the whole graph sits inside the visible canvas, osimertinib is findable, and the panel's "Plasma and tissue, side by side" table makes the cross-category point a second time, in words. What still holds the canvas back is the change layer. It was never dimmed, so the bottom half (FoundationOne CDx → NCT04712877 → FoundationOne Liquid CDx, and MRD → NCT07921888) is drawn as loud as the story path and pulls the eye down and away from it.

### Round-1 must-fix status

1. **Make the focus path the hero: partly fixed.** The path is now a 3px ink stroke, SuperARMS and therascreen are 16px, EGFR is a 26px node with a bold label, and the plain context is dimmed to .35. Two things are still missing. (a) The 12px halo is `#E3E5F3` drawn on a canvas that is already about that colour, so you cannot see it. Use `#D5D8EE` or a white halo at 0.9 so the line visibly lifts off the canvas. (b) The dimming leaves out every eosin node, link and label outside the two-hop neighbourhood (`key-graph.html` lines 222–225 sit outside `.dim`). See must-fix R2-1.
2. **Pull the layout into the visible canvas: fixed.** Every node now sits left of the panel and nothing runs off the edge. Both the top and bottom rows of nodes clear the toolbar and the legend.
3. **Unhide osimertinib: fixed.** It is labelled at the top right below the toolbar. It is dimmed, which is right because the proposal is not accepted yet.
4. **Remove the dashed selection ring: fixed.** SuperARMS now has a solid 1.5px ink ring outside the eosin ring. The only dashed mark left on the canvas is the Early research MRD node, which matches the legend.
5. **Quiet the change layer: partly fixed.** The "New link" pills are gone and the eosin links are 2px. But there are still 8 eosin words on the canvas: Changed SuperARMS, two New trials on the focus, two Changed FoundationOne, New MRD and two more New trials. All of them are at full strength, so the pink count went from 6 to 8, not to 3.
6. **Label clutter and collisions: mostly fixed.** No pill sits on the focus path any more, and the EGFR and KRAS hub labels are bigger than the leaf labels. Small collisions remain: a dimmed link runs under the "New Tumour-informed ctDNA MRD" pill, and the KRAS → Liquid CDx link grazes the Oncomine and Guardant360 labels. These are should-fix, not blockers.

### New must-fix

- **R2-1. Dim the change layer outside the focus.** Put the eosin rings, links and pills for FoundationOne CDx, FoundationOne Liquid CDx, NCT04712877, NCT07921888 and the MRD node in the same `.dim` group as the rest of the context. Opacity about .45 keeps them a little above the grey context, so a viewer can still see that changes exist. Leave these at full strength: SuperARMS, NCT06422546 and NCT04769388, together with their two links and their pills. The canvas then has one loud area, the focus and its own changes, and the "5 changes since 12 November" control in the toolbar still covers the rest. Without this, the lower-right eosin chain is the strongest shape on screen and it competes with the climax shot.

### Should-fix (new)

- **In the 900px frame, the panel silently drops the "1 change waiting: Add osimertinib…" box.** It is clipped below the comparison table and nothing shows that the panel scrolls. If the narration mentions the pending proposal, tighten the comparison table (put Sample type and Biomarker on one row) so the box fits at 900. Otherwise accept it.
- **Two provider hollow squares have no label** (near 498,350 and 678,655), and one of them sits on a link crossing. Either label them in dimmed text or drop them from this focused view. As they stand they look like stray glyphs.
- **"Changed: moved to clinical utility, 13 November" wraps and leaves "November" alone on the second line.** Shorten it to "Changed: clinical utility, 13 Nov", or let the date wrap as a unit.

### Checks that still pass

The tokens, the type, the one primary button and one capability tag, eosin used only for new or changed, the glass placement, and node shapes that match the legend are all unchanged from round 1 and still correct. The new "Focus path" legend entry and the comparison table both stay in the system.
