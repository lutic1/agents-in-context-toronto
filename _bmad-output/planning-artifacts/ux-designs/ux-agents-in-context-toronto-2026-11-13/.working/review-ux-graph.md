# UX review: Graph v4 (`key-graph.html`, `shots/graph-v4.png`)

Reviewed against EXPERIENCE.md, DESIGN.md, epics.md Stories 5.1 to 5.3, and the Home v7 and Review v5 mocks for data consistency.

## Verdict: fix, then ship

The climax reads. SuperARMS is ringed and labelled "Changed". The ink path SuperARMS → EGFR → therascreen EGFR is the darkest line on the canvas, and the side panel tells the plasma-to-tissue story in words. These match Home and Review:

- The five changes and their dates
- The trial IDs
- The stage: 5 of 9, clinical utility, with the eosin segment
- The CT.gov quote. It is under 300 characters, and no PubMed abstract text appears anywhere.
- The pending osimertinib proposal, which is not drawn

Other parts already meet the spec:

- There is one capability tag.
- `prefers-reduced-motion` stops the pulse.
- Changes carry words, not only colour.
- "View as table", "Mark as seen" and "Open Record" are all present.

Six problems block shipping. Two of them affect what the camera sees: labels hidden under the panels, and the page not fitting the recording size. The rest are a missing story criterion (trial click-through), a change rule that disagrees with Home, a control that isn't reachable by keyboard, and panel text the API can't supply.

## Must-fix

1. **Nodes and labels are hidden under the glass panels.**
   - The `osimertinib` label (SVG y=49) is completely under the toolbar, and its triangle is clipped. That is the drug in the pending proposal and in the Alert story.
   - Three Diagnostics are under the side panel: Ventana ALK (D5F3) CDx, Vysis ALK Break Apart FISH and Ventana MET (SP44) RxDx Assay. So are ALK, MET and alectinib. Their links run off under the panel's edge, but the page description still says "13 lung cancer diagnostics".
   - Fix: lay out the graph only in the area the panels leave uncovered. In the build, either set the `react-force-graph-2d` width to viewport minus panel, or use `zoomToFit` with padding for the toolbar (top), legend (bottom) and side panel (right). In the mock, move those nodes into the open area.

2. **Clicking a trial doesn't open its Evidence** (Story 5.2 acceptance criterion).
   - In Connections, the trial IDs `NCT06422546` and `NCT04769388` are plain `<span>`s.
   - Make each trial row a link or button that opens its Evidence in the 360px right-hand panel: quote, source, identifier link, "data as of".
   - Clicking a trial node on the canvas should do the same.
   - The therascreen link should go to that Record (it is `href="#"` today).

3. **The change marks don't match Home's change list or the API's `changed` rule.**
   - Home's list says "Changed FoundationOne Liquid CDx used in trial NCT04712877" and "Changed FoundationOne CDx …". In the Graph, both nodes are unmarked; only their links are pink.
   - The four trial diamonds have no ring, yet their labels read "New link NCT…". The word sits on a node label, but it describes a link.
   - Pick one rule and apply it everywhere:
     - Every node with `changed: true` gets the 3px eosin ring plus "New" or "Changed" on its label.
     - New trial nodes get a ring and "New".
     - FoundationOne Liquid CDx and FoundationOne CDx get "Changed", as on Home.
     - Pink links need no word of their own, or a "New link" legend entry is enough.
   - Then all five Home rows have a ringed, worded node on the Graph, and the pulse covers the same set.

4. **The "Highlight changes" switch isn't keyboard-operable, and no story asks for it.**
   - It is a `<span role="switch">` with no `tabindex` and no handler. The `aria-label` sits on a span inside a `<label>`.
   - It also blurs the meaning of "Mark as seen", since both seem to clear the pink.
   - Remove it (preferred). If it stays, make it a real `<button role="switch" aria-checked>`.

5. **The page doesn't fit the recording size.**
   - EXPERIENCE.md "Demo on Camera" sets 1440 × 900 at 110% zoom, with nothing essential below the fold on Graph. That leaves about 1309 × 730 CSS px for the page.
   - The graph area is a fixed 836px under a 60px top bar. The side panel needs about 800px. "Open Record" and "Show neighbourhood" would fall below the fold, and so would the legend with the `$graphLookup` tag.
   - Fix:
     - Make `.graph` `height: calc(100vh - topbar)`.
     - Let the side panel's middle section (quote and Connections) scroll inside the panel, with the actions pinned at the bottom.
     - Re-shoot at 1309 × 730 as well as 1440 × 1000.

6. **The side panel shows text the API doesn't supply** (AD-6: the web app applies no display rule of its own).
   - **"a tissue test"** needs the neighbour's sample type. Graph nodes (Story 5.1) carry only ID, type, label, stage and Early research. Either add `sample_type` to Diagnostic nodes in Story 5.1, or fetch the neighbour's Record. This phrase carries the climax, so keep it and source it; don't drop it.
   - **"response to osimertinib"** on the NCT06422546 row isn't a field anywhere. Remove it, or take the trial title from the Record's Trials value and its Evidence.
   - **"Changed: moved to clinical utility, 6 November"** must come from the `GET /changes?after=<last_seen_seq>` event for this Diagnostic, the same source as Home's list. It must not be pieced together from the stage and a date.

## Should-fix

- **Make the change count a list.** "5 changes since 2 November" is plain text. Make it a disclosure that lists the five changes as links, each focusing its node. Today a screen-reader user hears the count but can't reach the items. Home already has this list, so the Graph should have it too.
- **Mock the live-arrival frame** (Story 5.3 long-poll; the Flow 1 climax is "draw in … pulses once").
  - The mock shows only the settled state. Add the arrival moment: the new link and node appear, the count goes 4 → 5, and one polite live-region announcement plays ("New: SuperARMS EGFR mutation detection used in trial NCT04769388").
  - Opening the Graph from the Alert should land on `/graph?focus=diagnostic:<id>` with the panel already open. The URL bar shows plain `/graph`.
- **Make the pulse run together.** The node ring (`.pulse`, 1.6s) and the link stroke (`.newlinks`, 1.4s) have different durations. Use one duration and one easing so it reads as a single moment.
- **Show stage on the nodes** (Story 5.2: "Diagnostic nodes show their stage"). Today the stage appears only in the side panel. Add the stage track to the node hover/focus tooltip, as DESIGN.md says ("graph tooltip"), and mock one tooltip.
- **Tidy the capability tag.** "MongoDB $graphLookup" is a non-focusable span with a left border. Per spec it should be a quiet outlined tag. Hover or focus should show: "Follows links between Diagnostics, biomarkers, trials and drugs in the database."
- **Legend wording.** The legend says "Changed", but the MRD approach is "New". Use "New or changed", as Home's legend does.
- **"Mark as seen" wording and safety.**
  - Home says "Mark all as seen" and the Graph says "Mark as seen". Use the spec wording, "Mark as seen", in both.
  - This clears the pink for the whole Team. Confirm with a toast, "Marked as seen for Thoracic oncology", with Undo, which POSTs the previous `seq` back.
- **Pending proposal copy.**
  - Mirror the Review sentence: "1 Proposed change waiting: Add osimertinib to Linked drugs. Not drawn until accepted. Open review".
  - Source it from `GET /proposals?status=pending`, filtered by Diagnostic. Add a `dx_id` parameter, or filter the client-side list of 7.
  - "Open review" should open Review focused on that row.
- **Keep the climax path visible.** The highlighted ink path from SuperARMS to EGFR runs under the "Changed SuperARMS…" label box, so it looks broken right at the node. Move the label to the side away from the path.
- **Side panel width.** It is 400px; the spine says the right-hand panel is 360px.
- **Tissue nuclei near the focus look like nodes.** Blurred nuclei near the focus area (around 640,286; 527,393; 651,177) are node-sized and node-coloured. In 1080p compressed video they look like phantom nodes. Thin them out near the graph's centre, or lighten them further.
- **The canvas has the wrong accessible name.** The canvas is labelled by the H1 "Graph" but carries no node semantics. In the build, mark the force-graph canvas `aria-hidden` and keep the `graph-desc` paragraph plus "View as table" and the changes list as the non-visual route. That route also needs the five changes, which "View as table" doesn't show.
- **Top bar (affects all mocks, not Graph only).** "More ▾" replaces "Categories", which the IA lists in the top bar. Home and Review match each other, so fix this in the spine or in all three mocks together.

## Nice-to-have

- The five Provider squares have no labels. Label them on hover, or leave Providers out of the default view; anonymous nodes add noise to the video.
- "View as table" could open Find filtered to the Diagnostics currently in view, with the changed rows marked.
- "Show neighbourhood" could also run on its own when a node is focused. Keep the button as the keyboard path.
- Put a "Synthetic" note near "since 2 November", since the last-visit date is staged for the demo. The Team picker already carries the badge, so this is optional.

## Checked and passing

- Names, trial IDs and dates match Home v7 and Review v5:
  - MRD approach: NCT07921888, 12 Nov
  - SuperARMS: NCT06422546 and NCT04769388, 6 Nov
  - FoundationOne Liquid CDx and FoundationOne CDx: NCT04712877, 12 Nov
  - Data as of 12 November 2026
- Review count 7 and Alerts count 2 match.
- Stage track: two Early-research washed segments, two filled, eosin at stage 5 (clinical utility), four hollow, with the aria-label "Stage 5 of 9".
- Early research shows as a dashed node plus the words "Early research".
- The evidence quote uses the serif with source, linked ID and "data as of".
- There is one capability tag on the page.
- No PubMed abstract text appears.
- Under reduced motion, both animations are set to none.
- The microcopy follows Voice and Tone: plain, with glossary terms and no exclamation marks.

---

## Round 2: Graph v5b (`shots/graph-v5b.png`, `shots/graph-v5b-900.png`, `key-graph.html`)

I also rendered the mock at the recording size, 1309 × 730 CSS px. That is 1440 × 900 at 110% zoom: frame width 1309, window 790 including the mock's 60px browser chrome.

### Verdict: fix, then ship (one small must-fix)

The climax reads. The focus path is unbroken, every changed node is ringed and worded, the panel text comes from the API, and nothing sits under the glass. One problem is left, and it appears only at the recording size.

### Round-1 must-fixes

1. **Nodes hidden under panels: fixed.**
   - The canvas is now the area the panels leave uncovered (`left:28px; right:412px; top:92px; bottom:84px`).
   - osimertinib is fully visible.
   - The Ventana, Vysis, ALK, MET and alectinib nodes have been dropped, and `graph-desc` now says "9 lung cancer diagnostics", which matches the 9 drawn.
2. **Trial click opens Evidence: fixed in the panel. The canvas behaviour is unstated.**
   - Both trial IDs in Connections are now `<button class="idbtn">` with the label "Open Evidence for trial NCT…".
   - Clicking a trial diamond on the canvas is not noted anywhere. Add one line to the header comment: "Clicking a trial node opens its Evidence in the side panel (Story 5.2)", so the build doesn't miss it.
   - The therascreen link is still `href="#"`. That is fine for a mock, but it should be the Record route.
3. **Change marks match the `changed` rule: fixed.**
   - SuperARMS, FoundationOne CDx and FoundationOne Liquid CDx have a ring and "Changed".
   - The MRD approach and the four trials have a ring and "New".
   - Pink links carry no word, and the legend says "New or changed".
4. **"Highlight changes" switch: fixed.** It has been removed.
5. **Fits the recording size: partly fixed.**
   - These are fixed:
     - `.graph` is the viewport minus the top bar.
     - The side panel body scrolls (`.side-body` has `overflow-y:auto` and `tabindex="0"`).
     - Open Record and Show neighbourhood are pinned.
     - The 900 shot shows everything above the fold.
   - At 1309 px wide, the legend clips: the `$graphLookup` capability tag is cut off at the right edge. See the new must-fix below.
6. **Panel text the API doesn't supply: fixed.**
   - "a tissue test" now comes from `sample_type` on Diagnostic nodes, and Story 5.1 includes it.
   - The phrase "response to osimertinib" is gone.
   - The "Changed: moved to clinical utility, 13 November" line is sourced from `GET /changes` (header comment). Its date matches `shared-story.md`, where all changes are on 13 November and the header says "since 12 November".

### New must-fix

- **The capability tag is clipped at the recording width.**
  - At 1309 px the legend row is 869 px wide. With `white-space:nowrap` and `overflow:hidden`, the `$graphLookup` tag is cut to "$grap".
  - Story 5.2 requires the tag, and it is the page's one MongoDB moment on camera.
  - Fix: move the tag into the toolbar, after "View as table", where there is about 250 px spare at 1309. Or let the legend wrap or shrink its gaps.
  - Re-shoot at 1309 × 730.

### Should-fix (carried over or new, not blocking)

- **Node labels are small on camera.** At 1309 the canvas SVG scales by about 0.87, so labels render at about 11 px, and the faded context labels (cobas, Guardant360, Oncomine) at the same size and lower contrast. In the build, keep label font size constant in screen px (`react-force-graph` `nodeCanvasObject` with font size divided by `globalScale`).
- **The comparison table and pending proposal scroll out of view at the recording size.** That is fine, but the narration should not rely on the "Plasma and tissue, side by side" table without scrolling the panel. Either note that in the Demo on Camera script or move the table above Connections.
- **The change-count button has no panel.** It has `aria-controls="change-list"`, but no `#change-list` element exists in the mock. Mock the open list: five linked rows, each focusing its node.
- **Use the glossary term in the pending-proposal copy.** "1 change waiting" should be "1 Proposed change waiting", per the EXPERIENCE.md Glossary.
- **Still open from round 1:**
  - The live-arrival frame and its polite live-region announcement
  - The stage on the node hover/focus tooltip
  - The "Marked as seen for Thoracic oncology" toast with Undo
- **Pulse: fixed.** Both animations now use 1.4s with `ease-out` and a .6s delay.
