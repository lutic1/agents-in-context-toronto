# UX review: Home, Review, Graph key screens (v1)

Reviewer: senior UX, 2026-11-13. Inputs: `shots/home-v1.png`, `shots/review-v1.png`, `shots/graph-v1.png`, `key-*.html`, `../EXPERIENCE.md`, `../DESIGN.md`. Facts checked against `data/clinicaltrials/heldback.jsonl` and `data/pubmed/heldback.jsonl`. All quoted Evidence strings were verified verbatim in the source records.

Tags: **must-fix** (breaks the job, the story or credibility on camera), **should-fix** (spine conformance or clarity), **nice**.

---

## 0. Cross-screen: one story, one set of facts

The three screens are individually competent, but they tell three different stories with contradictory facts. A judge watching for 3 minutes will notice at least the date clash. Fix these before any per-screen polish.

| # | Tag | Problem | Fix |
|---|---|---|---|
| X1 | must-fix | **Last-visit date contradicts.** Home (Rowan): "4 changes since 2 October". Graph (Rowan, same Team): "Changed since 2 November • 5". Same Team, same `last_seen_seq`, so the date and the set must be the same. | Use one date everywhere. Recommended: **2 October** (matches Flow 2, "back after six weeks"). Graph toggle: "Highlight changes since 2 October". Make the Graph count equal the Home count, or explain the difference (see X2). |
| X2 | must-fix | **The changed sets do not match.** Home lists ctDNA MRD approach, "ctDNA monitoring approach", FoundationOne Liquid CDx, therascreen KRAS. Graph highlights only SuperARMS EGFR and NCT06422546, which Home does not mention even though EGFR is in the Team profile and it moved on 6 November. Home's FoundationOne Liquid CDx → NCT07894458 link is not marked on the Graph (NCT07894458 is drawn linked to the Early research ctDNA MRD node instead). | Derive all three screens from one change list. Recommended Home list (newest first) and the Graph marks the same items: SuperARMS EGFR moved to clinical utility (6 Nov, NCT06422546); the Early research MRD Diagnostic first seen (21 Oct, NCT07885709); Signatera Genome used in trial (27 Oct, NCT07689812); one accepted change. |
| X3 | must-fix | **The Flow 1 thread is broken.** EXPERIENCE Flow 1 step 4–5: Rowan's Alert is "a ctDNA assay they follow moved to clinical utility, why line names EGFR", then the Graph climax shows *that* Diagnostic pulsing. In the mocks the Home Alert that moved to clinical utility is "ctDNA monitoring approach" (NCT07689812), but the Graph climax is SuperARMS EGFR (NCT06422546). | Make the Home "Update" Alert **SuperARMS EGFR mutation detection**, NCT06422546, 6 November, why line naming EGFR (copy in H4). Then Alert → Play briefing → Graph is one continuous thread on camera. |
| X4 | must-fix | **Same Diagnostic, three names.** "ctDNA MRD approach" (Home list and Alert) vs "ctDNA MRD, tumour-informed" (Graph). "therascreen KRAS RGQ PCR Kit" (Home) vs "therascreen KRAS RGQ PCR" (Graph). "Ventana ALK (D5F3) CDx" / "Ventana PD-L1 (SP263) Assay" vs "VENTANA MET (SP44) RxDx" (Graph). | One canonical display name per Diagnostic, from the API. Use "therascreen KRAS RGQ PCR Kit", "Ventana MET (SP44) RxDx Assay" (match the Ventana casing used elsewhere), and one name for the MRD Diagnostic (see H5). |
| X5 | must-fix | **Two "Diagnostics" are not diagnostics.** "ctDNA MRD approach" and "ctDNA monitoring approach" are categories, not products. A Director of Diagnostics will read them as made up. NCT07689812's own intervention is "Signatera Genome ultra-sensitive ctDNA blood test". | Rename "ctDNA monitoring approach" to **Signatera Genome**. For NCT07885709 (no named assay in the record) use "MRD-guided neoadjuvant ctDNA test (unnamed)" or drop it in favour of a named assay. |
| X6 | should-fix | **Review count vs Digest count.** Top bar "Review 7" on every screen; Home Digest "3 proposed changes waiting for review". Reads as a bug. | Digest lead: "7 proposed changes waiting for review. 3 match your team:" then the 3 rows. Or make the Digest show 7. |
| X7 | should-fix | **Alerts badge styled two ways.** Home: eosin-tint pill. Review and Graph: ink pill. | Pick one. Recommended: ink pill everywhere (eosin is reserved for "new or changed" items, not unread counts). |
| X8 | should-fix | **URL bar inconsistent.** Home and Graph `dxp.vercel.app`, Review `localhost:3000/review` (looks unfinished on camera). Home URL lacks the path. | `dxp.vercel.app/`, `dxp.vercel.app/review`, `dxp.vercel.app/graph`. |
| X9 | should-fix | **Team picker wraps to two lines** on Home and Review ("Thoracic oncology / strategy"), one line on Graph. Looks broken at recording size. | Narrow the capture box to ~240px or set the picker `white-space:nowrap`. Keep the Team name; it is good. |
| X10 | nice | "Rowan" / "Sam" picker has no cue that it is the "your name" picker. | "Rowan (you)" or a small person icon; tooltip "Your name, recorded on every decision". |
| X11 | nice | Stage tracks are drawn three ways (Home Alert 2 fills discovery and assay development in full ink; Review and Graph use ink-tint for those two). DESIGN.md: passed Early research segments are `ink-tint`. | Fix Home Alert 2 track (see H6); share one component. |

---

## 1. Home (`/`)

**Job:** what changed for my team, and pick up where I left off. **Verdict:** the layout answers both questions in the right order (welcome-back first, changes second, Alerts right). Credibility and the fold let it down.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| H1 | must-fix | Welcome-back summary | The shortlist contradicts the intent. "comparing ctDNA tests for relapse monitoring in stage I–III NSCLC and shortlisted three: Guardant360 CDx, FoundationOne Liquid CDx and the Agilent Resolution ctDx FIRST assay". All three are genotyping companion diagnostics for advanced disease, not MRD/relapse-monitoring tests. A Director would spot it in one second. | Change the intent to fit the shortlist and the Team profile (ctDNA, EGFR, KRAS): "Last time you were comparing plasma ctDNA tests for EGFR and KRAS in advanced NSCLC and shortlisted three: Guardant360 CDx, FoundationOne Liquid CDx and Resolution ctDx FIRST. You dismissed one Alert about a tissue-only PD-L1 assay." (Flow 2's "MRD tests for early-stage relapse monitoring" then needs the same edit in EXPERIENCE.md, or swap the shortlist for MRD assays present in the data.) |
| H2 | must-fix | "Since your last visit" list, row 4 | "Changed therascreen KRAS RGQ PCR Kit linked drug garsorasib proposed, waiting for review". A pending proposal is not a change. It is also listed in the Digest as pending, so the same item appears twice with different statuses. The garsorasib trial in the data (NCT07472478) does not mention therascreen, so the link itself is not supported. | Remove the row from "Since your last visit" (it lives in the Digest). Heading becomes "3 changes since 2 October", or replace it with an accepted change. Replace the garsorasib proposal with one the data supports. |
| H3 | must-fix | "Since your last visit" row 3 and Digest row 2 | Row 3 says "Changed FoundationOne Liquid CDx used in trial NCT07894458" (done), while the Digest lists "FoundationOne Liquid CDx trials, add NCT07894458" (pending). Contradiction. Also, NCT07894458's record names no FoundationOne assay; its only intervention is "Adaptive therapy … based on MRD testing", so the link is unsupported. | Pick a link the data supports, e.g. "Changed FoundationOne Liquid CDx used in trial NCT04712877" (that record lists "FoundationOne Liquid"). Show it either as done (list) or pending (Digest), never both. |
| H4 | must-fix | Alert 2 ("Update: moved to clinical utility", ctDNA monitoring approach) | Why line "A randomised trial now tests whether ctDNA can guide stopping immunotherapy in advanced NSCLC. Your team follows ctDNA testing for EGFR and KRAS." The test (Signatera) is not an EGFR or KRAS test, and the trial is multi-tumour (NSCLC, melanoma, CRC). And see X3: this should be the SuperARMS Alert. | Replace the Alert: title "SuperARMS EGFR mutation detection"; kind "Update: moved to clinical utility"; why "A real-world study now uses this plasma EGFR test to track response to osimertinib. Your team follows ctDNA testing for EGFR."; quote "Baseline plasma ctDNA EGFR mutation status and mutation types will be obtained through the SuperARMS assay"; source "ClinicalTrials.gov, NCT06422546, data as of 12 November 2026". |
| H5 | must-fix | Alert 1 why line (First seen, Early research) | "A plasma ctDNA test now guides neoadjuvant therapy in resectable NSCLC … patients are selected as EGFR wild-type." "Now guides" overclaims for an Early research item. "Selected as EGFR wild-type" misreads the record: the record mentions EGFR/ALK wild-type only to describe current standard of care. "Wild-type" is also jargon for this line. | "A new single-arm study will use a ctDNA test to adjust neoadjuvant therapy in resectable NSCLC. It matches your team's interest in ctDNA testing." Name: see X5. |
| H6 | must-fix | Fold at 1440 × 900, 110% zoom | EXPERIENCE: "nothing essential below the fold on Home". The Digest (y ≈ 1000) and Alert 2's play button are well below the fold, and "Mark as seen" is at the edge. Meanwhile the left column has ~500px of empty space under the welcome panel. | Move the Digest into the left column under "Since your last visit" (as a 3-row block with "Open review"). Collapse Alert quotes to 2 lines with "Show Evidence" when more than one Alert shows, or show only the newest Alert in full. Target: both Alerts' headings and both play buttons visible in the first screen. |
| H7 | should-fix | Panel heading "Since your last visit" + H1 "Welcome back, Rowan" + H3 "4 changes since 2 October" | Three headings saying the same thing. The panel heading duplicates the sub-section heading. | Panel heading: "Pick up where you left off". Keep H1 and "N changes since 2 October". |
| H8 | should-fix | "Open shortlist" | EXPERIENCE: "Reopen" buttons for last Intended use and Shortlist; Shortlist should be named. | Buttons: "Reopen last search" (primary) and "Reopen shortlist: Relapse monitoring, stage I–III" (or the renamed shortlist from H1). |
| H9 | should-fix | Alert 2 stage track | Discovery and assay development segments drawn in full ink; DESIGN.md says passed Early research segments are ink-tint. | Classes `er er f f adv …`. |
| H10 | should-fix | Change rows | All four rows have an eosin-tint background, so nothing stands out; and eosin tint is meant to highlight against unchanged rows. | Keep the dot and the "New"/"Changed" word; drop the row tint inside a list that is by definition all changes, or keep tint only on items the Team has not opened. |
| H11 | should-fix | "Change streams" tag on Alerts panel | EXPERIENCE: shown only if the optional long-poll in Story 1.1 is built. If it is not built, this is an untrue claim on camera. | Keep only if Story 1.1 ships the wake-up; otherwise remove (the panel then has no tag, which is fine). |
| H12 | should-fix | Synthetic line "Recalled from your team's earlier sessions, made up for this demo." | Good labelling; "made up" reads slightly flippant to a judge. | "Synthetic: recalled from your team's earlier sessions, created for this demo." |
| H13 | nice | Change row stage words | "first seen at assay development" reads oddly. | "first seen, at assay development (Early research)". |
| H14 | nice | Keyboard | No visible cues on Home. Fine, but give "Mark as seen" a real button look (currently ghost text that reads as a caption). | Outline button "Mark all as seen". |

---

## 2. Review (`/review`)

**Job:** decide changes fast and see the Learned rule. **Verdict:** the layout is right (queue left, rule draft right, shortcuts visible, Accept is one click). The rejection that drives the rule is not believable, the rule wording contradicts its own hint, and the visible flag comes from a different rule, so the "rejection becomes a rule" moment does not land.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| R1 | must-fix | Rule panel: rejected change | "Rejected biomarkers: add EGFR on cobas EGFR Mutation Test v2. Reason: Cell-line study, not patients." The cobas EGFR test already is an EGFR test, so this proposal would never exist, and nothing ties it to a cell-line study. | Use a real cell-line/animal finding from the held-back PubMed set: PMID 42985469 (ZNF471 and osimertinib resistance; cell lines and xenografts). Panel: "**Rejected** New Diagnostic: ZNF471 methylation test, linked drug osimertinib (PubMed 42985469)" / "Reason: Cell-line and mouse study, not patients." |
| R2 | must-fix | Rule text vs hint | Rule "Ignore findings from cell-line or animal studies." Hint right below: "A rule only flags changes; it never rejects them." "Ignore" says the opposite. | Rule: "Flag findings that come only from cell-line or animal studies." (Update Flow 1 step 3 in EXPERIENCE.md to the same wording.) |
| R3 | must-fix | Flag on row 3 | The only visible flag is from a different, synthetic rule ("Count an assay as used in a trial only when…"). On camera the viewer cannot connect the rule just drafted to any flag; Flow 1's payoff ("two other pending proposals now carry its flag") is missing. | Mock the state after "Turn on rule": panel reads "Rule on. It flags 2 of 7 pending changes." with the two listed; rows carry "Flagged by your new rule: Flag findings that come only from cell-line or animal studies." Keep the synthetic rule's flag only if it is on a row lower in the list. |
| R4 | must-fix | Quote text in rows 1, 2, 4 | Raw enum leaks into the Evidence: "Intervention (DEVICE): …", "Intervention (DIAGNOSTIC_TEST): …". These prefixes are DxP's own flattening of the record, not the source's words, yet they are set in the source serif (DESIGN: nothing DxP writes in the serif). | Quote only the source text and say the field in sans above it. Row 1: label "Listed as a device intervention", quote "FDA-approved assays used off-label for study as treatment determining in-vitro diagnostic devices to assess subject PD-L1 quantitation." Rows 2 and 4: label "Listed as a diagnostic test intervention", quote "ctDNA, tumor NGS, FoundationOne CDx, FoundationOne Liquid. Testing for actionable oncogenic drivers". |
| R5 | must-fix | Change line | "Trials 4 trials to add NCT05642195" is ungrammatical and hides the current → new pattern. | "Trials: 4 listed → add NCT05642195". Same pattern on every row. |
| R6 | should-fix | Confidence numbers | "0.54: the trial allows either of two assays", "Confidence 0.91 / 0.78 / 0.90". Raw scores are noise for a Director; DESIGN only specifies the Low-confidence marker. | Row 1: "○ Low confidence: the trial allows either of two assays (SP263 or SP142)". Other rows: drop the number (or keep it in the Evidence panel on hover). |
| R7 | should-fix | "Trigger: used in a trial" | "Trigger" is system jargon, and it repeats the field ("Trials … add"). | Remove, or "Why proposed: used in a trial" only where it adds information (e.g. stage moves). |
| R8 | should-fix | Row 2 "New since your last visit" + 4px eosin stripe | Every proposal is new; this one-off mark is confusing. The stripe-only treatment is not the DESIGN changed mark (dot + tint). | Remove from Review. If you want arrival order, add "Arrived 12 Nov" in caption. |
| R9 | should-fix | Rule panel copy | "When it is on, DxP checks the 7 pending changes and every new one against it." Good, but the panel does not say who rejected or when. | Add caption under the rejected box: "Sam, just now". |
| R10 | should-fix | Rule panel capability tag "Agent Memory, procedural" | EXPERIENCE assigns it to the Rules page. On Review it is fine (one per panel), but the hover sentence assumes the rule is on. | Keep; hover: "When you turn this rule on, it is also stored as procedural memory." |
| R11 | should-fix | Low confidence first | Correct, but nothing tells the viewer why row 1 is first. | Under the header: "Low-confidence changes first." |
| R12 | nice | Shortcut hints inside buttons (`a`, `e`, `r`) | 11px at 70% opacity; illegible in a 1080p encode. The header legend already covers it. | Raise to 12px, full muted colour, or drop from buttons. |
| R13 | nice | Rows 2 and 4 | Same trial, same quote, two Diagnostics. Credible (the trial lists both), but on camera it looks like a duplicate. | Put a different trial on one of them, or group: "NCT04712877 adds 2 Diagnostics". |
| R14 | nice | Edit/Reject reason | Not visible in this state. EXPERIENCE copy: "Reason for rejecting (DxP will suggest a rule from it)". | Make sure the reject state mock uses exactly that label. |

---

## 3. Graph (`/graph`)

**Job:** see connections and what changed. **Verdict:** the stain palette and shapes read well, the changed path is obvious, "View as table" and the tag are in place. Label collisions and the tooltip covering the middle of the graph make it look unfinished, and the climax path (plasma test → EGFR → tissue test) is partly hidden.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| G1 | must-fix | Label collisions | "Vysis ALK Break Apart FISH" overprints "PD-L1 IHC 22C3 pharmDx"; "Oncomine Dx Target Test" overprints "BRAF"; "Guardant360 CDx" is struck through by an eosin link; "SuperARMS EGFR" label runs into the Guardant label; "pembrolizumab" is clipped at the right edge; "Foundation Medicine" is half under the card; "therascreen EGFR RGQ PCR Kit" crossed by a link. | Re-lay out the mock so no labels overlap (DESIGN: labels appear only where they do not overlap). Move PD-L1 22C3 node down/right; Vysis label left of its node; pull pembrolizumab 60px in; give labels a 2px background halo in `{colors.background}`. |
| G2 | must-fix | Tooltip card position | The card sits over the centre and hides "Agilent Resolution ctDx FIRST" (a shortlisted test, in the HTML but invisible) and most of EGFR's links, which is exactly the path Flow 1 says Rowan follows. | Anchor the card in the empty top-centre/right area (e.g. left 700, top 40) or dock it as the 360px right-hand panel. Keep EGFR, SuperARMS, cobas EGFR and the trial all visible. |
| G3 | must-fix | Climax path | Flow 1: "follows the link across from the plasma test to the tissue test that shares the biomarker." Nothing marks cobas EGFR Mutation Test v2 (tissue) as the destination; the eosin path goes to the trial and osimertinib instead. | Add a selection state: SuperARMS → EGFR → cobas EGFR in ink-tint highlight (not eosin, it is not a change) and a caption in the card: "Shares EGFR with cobas EGFR Mutation Test v2 (tissue)". |
| G4 | must-fix | Toolbar "Changed since 2 November • 5" | Contradicts Home (X1). "5" counts 2 nodes + 3 links, which a viewer reads as 5 Diagnostics. | "Highlight changes since 2 October" and the count in words the viewer can verify: "3 changed: 1 Diagnostic, 1 trial, 1 link" (match Home). |
| G5 | should-fix | Tooltip link line "Linked to EGFR and osimertinib" | SuperARMS is drawn linked to EGFR and the trial; osimertinib is linked via the trial. Text claims a direct link. | "Linked to EGFR. Used in trial NCT06422546 with osimertinib." |
| G6 | should-fix | Tooltip identifier | `NCT06422546` in the source line is not styled as a link (no underline), unlike Home and Review. Evidence rule: identifier link. | Underline it and link to clinicaltrials.gov. |
| G7 | should-fix | Biomarker vs Provider shapes | Rounded square vs small square: at 1080p they differ only by size and colour, which breaks "node types have shapes". | Provider: hollow square (1.5px grey outline, no fill), or a plus. Update DESIGN.md Graph nodes. |
| G8 | should-fix | Fold | Canvas is 740px under 108px of bars. At 1440 × 900 / 110% the bottom third (KRAS, the Early research MRD node, LUAD) is below the fold. | Fit the graph to the viewport height (≈ 600px at 110%) or pre-zoom to the EGFR neighbourhood for the recording. |
| G9 | should-fix | SuperARMS stage | The record is a non-interventional real-world study; "moved to clinical utility" is defensible, but SuperARMS is already approved in China, so the track could be challenged. | Keep clinical utility but make sure the Record shows the Evidence for the stage; nice-to-have note in the speaker script, not on screen. |
| G10 | should-fix | Toggle semantics | A switch reading "Changed since 2 November" does not say what off does. | Label "Highlight changes since 2 October". |
| G11 | nice | Keyboard cue | No hint that the graph is keyboard-navigable. | Caption next to "View as table": "Tab moves through changed items". |
| G12 | nice | "$graphLookup" tag | Fine for MongoDB judges; ensure the hover sentence shows on focus too. | No copy change. |
| G13 | nice | Legend | Legend text at 13px muted is light on camera. | Use foreground colour for legend labels. |

---

## 4. Demo-on-camera summary

- The story reads only if the three screens share facts: one last-visit date, one change list, and the SuperARMS EGFR thread running Alert → briefing → Graph pulse (X1–X3).
- Review's moment ("my rejection became a rule, and it now flags two changes") needs the post-"Turn on rule" state and a credible cell-line rejection (R1–R3).
- Clean up the Graph labels and move the card. A cluttered graph undercuts the climax more than any copy issue (G1–G2).
- Spine updates implied: EXPERIENCE Flow 1 step 3 rule wording ("Flag…", not "Ignore…"); Flow 2 step 1 intent if the shortlist stays as is; DESIGN Graph provider shape.

---

# Round 2 (v2 mocks, 2026-11-13)

Inputs: `shots/home-v2.png`, `shots/review-v2.png`, `shots/review-v2-full.png`, `shots/graph-v2.png`, `key-*.html` (v2), updated `EXPERIENCE.md`. All six v2 Evidence quotes I spot-checked are word for word in `data/clinicaltrials/heldback.jsonl` (NCT07894458, NCT06422546 ×2, NCT04712877, NCT06284317, NCT07885709). NCT07885709 does say "tumor-informed", and NCT04769388 does mention SuperARMS.

**Verdict:** Home: ship after two small fixes. Graph: ship (polish only). Review: fix first, because the rule's payoff (flagged proposals) still has nothing to show.

## R2.0 Cross-screen

Fixed: X1 (2 November on Home and Graph, kept on purpose), X2 (the same five changes on Home and Graph: the MRD test is new, SuperARMS moved stage, SuperARMS is in NCT04769388, and F1 Liquid CDx and F1 CDx are in NCT04712877; the Graph count "5 changed" matches), X3 (the SuperARMS thread runs from the Alert to the Graph card), X4 (names are the same on every screen; "Ventana MET (SP44) RxDx Assay" now uses the same casing as the others), X6 (Digest "7 waiting. 3 match your team" lists the same three proposals as the top of Review), X7 (count badges are ink everywhere), X9 (the Team picker fits on one line). Also, osimertinib reads the same on every screen: the Graph shows it linked through the trial only, the card says "Used in trial … with osimertinib", and Review proposes "Add osimertinib to Linked drugs, none listed today". Good.

| # | Tag | Problem | Fix |
|---|---|---|---|
| X2-1 | should-fix | **Change dates don't match the source.** Home lists "Tumour-informed ctDNA MRD (approach)" as first seen on **9 Nov**, but NCT07885709 was first posted 21 Oct with no later update. That falls before the 2 November last visit, so a careful viewer asks why it counts as a change since then. NCT04712877's last update is 12 Nov, but both F1 rows say **5 Nov**. | Date each row by when DxP filed the change and say so. Change the subheading to "…Dates are when DxP found the change." Then use 12 Nov for both NCT04712877 rows (its last update). Keep 9 Nov for the MRD test only if the script says the live job found it then. |
| X8 | should-fix (still open) | The Review URL is still `localhost:3000/review`. Home and Graph use `dxp.vercel.app/…`. | Change it to `dxp.vercel.app/review`. |
| X10-1 | nice | The name picker says "Rowan (you)" on Graph but "Rowan" on Home and "Sam" on Review. | Use "(you)" on every screen, or on none. |
| X11-1 | nice | SuperARMS's newly filled stage segment is eosin on Home and Graph but ink on Review. All three screens show the same Team, so the segment should look the same until someone marks it as seen. | Make it eosin on Review too, or ink on all three after "Mark all as seen". |

## R2.1 Home

Fixed: H1 (search and shortlist now agree, apart from one item, see below), H2 and H3 (no pending items in the change list; it shows accepted changes, and the line "accepted by Sam" says who accepted them), H4 and H5 (new why lines, accurate, no jargon), H6 (Digest moved to the left column, and both Alerts with their Play buttons now fit in the first screen), H7 (duplicate heading removed), H10 (row tint removed, dot and word kept), H11 (Change streams tag removed), H12, H14 ("Mark all as seen" is now a real button).

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| H2-1 | must-fix | Welcome-back summary | "plasma EGFR and KRAS genotyping … shortlisted Guardant360 CDx, FoundationOne Liquid CDx and therascreen KRAS RGQ PCR Kit". The therascreen KRAS kit is a **tissue** (FFPE) test, not a plasma one. A Director of Diagnostics will catch this. | Replace it with the plasma KRAS test already on the Graph: "…shortlisted Guardant360 CDx, FoundationOne Liquid CDx and Resolution ctDx FIRST." |
| H2-2 | should-fix | Memory note | The Synthetic label and the Agent Memory tag are now one sentence of plain text, "Synthetic: recalled from … Remembered with Agent Memory (public preview)." EXPERIENCE asks for the Synthetic **badge** on every synthetic item, and one quiet capability tag per panel. Inline text loses both signals on camera. | Restore the dotted "Synthetic" badge followed by "Recalled from your team's earlier sessions, created for this demo." Put "Agent Memory (public preview)" back as an outlined tag at the top right of the panel. |
| H2-3 | should-fix | Alert kind | "Moved to clinical utility" dropped the kind. The spec says Kind (First seen / Update) plus the trigger. The second Alert keeps "First seen", so the two Alerts now read inconsistently. | "Update: moved to clinical utility". |
| H2-4 | should-fix | Diagnostic name "Tumour-informed ctDNA MRD (approach)" | The "(approach)" in brackets reads like a placeholder that slipped through. | "Tumour-informed ctDNA MRD test (unnamed)", the same on Home and Graph. |
| H2-5 | nice | Alert 2 quote cut off at "unfavorable…" | Cutting off Evidence is acceptable, but nothing tells the viewer there is more to read. | Add a "Show full quote" link, or end the cut at a phrase boundary with "[…]". |
| H2-6 | nice | Digest at the fold | At 1440 × 900 with 110% zoom, only the Digest heading and its first row show. That is acceptable, because the Digest belongs to Flow 3 and is not in the video. | No change needed for the video. |

## R2.2 Review

Fixed: R1 (the rejection now cites PMID 42985469, a cell-line and xenograft paper, and gives the reason "Cell-line study, not patients"), R2 (the rule now says "Flag findings from cell-line or animal studies", which agrees with the hint, and EXPERIENCE Flow 1 was updated to match), R4 (no `Intervention (DEVICE)` text inside quotes), R5 (each row is a sentence: "Add trial NCT06284317 to Trials. 4 listed today"), R6 (no confidence numbers; the Low-confidence reason is written in words), R7 ("Trigger" removed), R9 ("Sam, just now"), R11 ("Low-confidence changes first"), R12 (shortcut hints removed from the buttons). The new pattern of full buttons on the focused row and compact buttons on the rest matches the updated EXPERIENCE row and reads well.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| R2-1 | must-fix | Rule payoff (Flow 1 step 3: "two other pending proposals now carry its flag") | Still not addressed (R3). The only flag on screen comes from the other, synthetic rule. None of the four visible proposals is a cell-line or animal finding, so after "Turn on rule" nothing visible would carry the new flag, and nothing says which of the three rows below would. That is the moment the rule is supposed to pay off, and it is missing. | (a) Make two of the "3 more changes below" PubMed proposals from cell-line or animal papers in the held-back set. Check each abstract first; candidates are PMIDs 42934891 and 42968152. (b) Add a second state, after "Turn on rule": panel title "Rule on", text "It flags 2 of 7 pending changes:", followed by two links (Diagnostic, field, PMID), and "Turn off" in place of "Discard". (c) Those rows show "Flagged by your new rule: Flag findings from cell-line or animal studies." Keep the synthetic rule's flag, but further down. |
| R2-2 | should-fix | "New" mark on the SuperARMS row | Still present (R8). Every proposal is new, so the eosin "New" here means nothing, and it competes with the eosin on Home and Graph that marks real changes. | Remove it. If arrival order matters, add the caption "Arrived 6 Nov". |
| R2-3 | should-fix | Rejected change "Add biomarker ZNF471 to Guardant360 CDx" | Plausible as an agent's mistake, but it shows a PMID with no link, and "biomarker" is lower-case while the other rows write field names as "Clinical uses", "Trials". | Write "Add ZNF471 to Biomarkers on Guardant360 CDx". Link "PMID 42985469" to PubMed. No quote is needed for a rejected item. |
| R2-4 | nice | Rule panel "Discard" | Shown as a ghost text button next to the primary "Turn on rule". At 1080p it reads like a caption. | Make it an outline button, the same weight as "Edit". |
| R2-5 | nice | Low-confidence reason sentence | The whole sentence is ochre. DESIGN.md only asks for the marker and the words "Low confidence" in ochre. | Keep "○ Low confidence:" in ochre and set the reason in muted ink. |

## R2.3 Graph

Fixed: G1 (no label overlaps; provider labels moved to hover), G2 (the card now sits on the right and covers no important node), G3 (the plasma-to-tissue path SuperARMS → EGFR → cobas has an ink-tint halo, and the card says "Shares EGFR with cobas EGFR Mutation Test v2, a tissue test"), G4 ("Highlight changes since 2 November • 5 changed"), G5, G6 (the identifier is a link), G7 (provider is now a hollow square, which makes the shapes distinct), G8 (the graph fits above the footer), G10, G13. The eosin rings and links match the five changes on Home exactly.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| G2-1 | should-fix | Line from the card to the SuperARMS node | It is a 1px ink line, the same as a graph link, so it looks like SuperARMS is linked to something hidden behind the card. | Make it a dotted line in `{colors.muted-foreground}`, or remove it; the eosin ring already marks the selected node. |
| G2-2 | should-fix | Label collisions that remain | "FoundationOne CDx" and "FoundationOne Liquid CDx" are each crossed by a link, and "Agilent Resolution ctDx FIRST" sits on two crossing links. They read on camera, but untidily. | Add a 2px halo in `{colors.background}` behind the labels (`paint-order: stroke`). |
| G2-3 | nice | Capability tag | "MongoDB $graphLookup" is now plain text with no outline, which no longer matches the tag style used elsewhere (the Review "Agent Memory, procedural" tag is outlined). | Restore the outlined capability tag. |
| G2-4 | nice | Keyboard cue | Still none (G11). | Add the caption "Tab moves through changed items" next to "View as table". |

---

# Round 3 (glass): Home v4

Scope: only what the glass restyle could break. Inputs: `shots/home-v4.png`, `key-home.html` (v4), DESIGN.md Glass layer, Logo and Icons.

**Verdict: ship after one must-fix.** The story still holds. Above the fold at 1440 × 900 and 110% zoom, the reader sees the welcome, all five changes, both Alerts and both Play buttons; only the Digest heading sits at the fold. Moving the Play and Dismiss buttons to the head of each Alert brought both Play buttons above the fold.

**Fixed since Round 2:**
- H2-1: the shortlist is now Guardant360 CDx, FoundationOne Liquid CDx and Agilent Resolution ctDx FIRST. All three are plasma tests, so it matches the search.
- X2-1: the subheading now says "Dates are each source's last update", and the dates match the records. NCT04712877 is 12 Nov.
- The MRD change now cites NCT07921888. It was first posted 6 Nov, which is after the last visit; its last update is 12 Nov and its quote is word for word. The Graph uses the same trial ID.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| G3-1 | must-fix | Name picker became an avatar ("RO") with the name in `title` only | The decision record depends on the actor, and on camera the viewer can no longer see who is signed in. The welcome says "Rowan", but nothing in the top bar does. A `title` tooltip also only appears on mouse hover: keyboard focus never shows it, and touch cannot reach it. That conflicts with the accessibility floor ("never an icon alone without a label or tooltip") and with the ban on hover-only content. The element is a `div`, so it cannot take focus. | Show the avatar **and** the name: "RO Rowan ▾". There is room, because the capture box got shorter. Make it a `button` with `aria-label="Your name: Rowan. Change"` and a shadcn `Tooltip` that also opens on focus. |
| G3-2 | should-fix | Synthetic badge and capability tag are still folded into one sentence (H2-2, open since Round 2, now with a `brain` icon) | "Synthetic memory created for this demo, recalled with Agent Memory (public preview)." The dotted Synthetic badge is gone from the recalled memory, and the Agent Memory tag is gone from the panel. Judges look for both. | Restore the "Synthetic" dotted badge before the sentence, and the outlined tag "Agent Memory (public preview)" (it can keep the brain icon) in the panel head. Sentence: "Recalled from your team's earlier sessions, created for this demo." |
| G3-3 | should-fix | Eosin used outside its meaning | (a) The logo's nucleus is eosin pink. (b) The tissue field puts an eosin blob (`.c2`, 22%) right behind the changes list, so the welcome panel turns pink exactly where the eosin "New"/"Changed" words and dots are. Both teach the viewer that pink is decoration, which goes against DESIGN.md "eosin … never brand decoration". | Logo: draw the nucleus in `{colors.field-haematoxylin}`, or accept the logo as the single, documented exception in DESIGN.md. Field: move `.c2` off the left column, or lower it to 12% behind content panels. |
| G3-4 | should-fix | Capture box shortened to "Add a diagnostic" | It now reads as "create a Record", not "tell DxP about something you heard". The capture flow (Story 7.1) also matches the entry to an existing Record. | "Add a diagnostic you heard of" fits in about 220px. Otherwise keep the short label and add the placeholder hint "Name or link, DxP finds the source". |
| G3-5 | should-fix | Alert kind is still "Moved to clinical utility" (H2-3) | The second Alert says "First seen", but the first one does not say "Update". | "Update: moved to clinical utility". |
| G3-6 | should-fix | Team picker shortened to "Thoracic oncology" | Acceptable, but Review and Graph v3 still say "Thoracic oncology strategy". Also, Review and Graph still show the "DxP" wordmark while Home shows "DxProvida". | Bring the top bar to Review and Graph in the same pass: same label, logo and avatar treatment. |
| G3-7 | should-fix | Focus visibility on glass | The mock defines no focus style. shadcn's default `ring` is hard to see on translucent white over a pink or violet field. | `focus-visible: 2px solid {colors.ink-deep}` with a 2px white offset on every glass control. |
| G3-8 | nice | Icon choices | Jobs uses `cpu`, which reads as "hardware"; `list-checks` or `loader` fit better. The Evidence source line uses `flask-conical` (DESIGN.md: Trial) where `file-text` is the Evidence-source icon. That is defensible because the source is a trial; keep one rule. `inbox` for the Digest is not in the DESIGN.md list, so add it. All icons sit beside words. Good. | Update the DESIGN.md icon table, or switch the icons. |
| G3-9 | nice | Dismiss `aria-label="Dismiss"` | Two identical labels on one page. | `aria-label="Dismiss alert: SuperARMS EGFR mutation detection"`. |
| G3-10 | nice | Change row 4 wraps ("…moved to clinical utility, trial / NCT06422546") | It is the key row of the story, and the wrap splits the identifier onto its own line. | Shorten to "moved to clinical utility, NCT06422546", or reduce the date column width. |
| G3-11 | nice | Contrast | Body text and source lines sit on 72% glass and read well in the shot. Captions in muted ink over the violet blob at the top left are the weakest spot; check them at 4.5:1 or above with the field rendered. The tinted outlines of the empty stage-track segments are faint at 1080p. | Measure with the field rendered. If captions fall short, use `glass-strong` behind the welcome caption. |

---

# Round 4 (graph hero): Home v5

Inputs: `shots/home-v5.png`, `key-home.html` (v5), DESIGN.md "Graph-led hero", EXPERIENCE.md (Home row, Interaction Primitives, Demo on Camera, Flow 1).

**Verdict: fix first (3 must-fixes, all cheap).** The hero answers "what changed for my team" at a glance. The eosin items sit on the left and centre of the network, and the welcome panel docked beside them lists the same items in words. The hero's changed set matches the five list rows exactly:
- the MRD test and NCT07921888
- FoundationOne Liquid CDx and NCT04712877
- FoundationOne CDx and NCT04712877
- SuperARMS and NCT06422546 (stage move)
- SuperARMS and NCT04769388

**Fixed since Round 3:**
- G3-1: the name shows as "RO Rowan", on a real button with an aria-label.
- G3-2: the dotted Synthetic badge is back, and the Agent Memory tag sits in the panel head.
- G3-4: the capture box reads "Add a diagnostic you heard about" again.
- G3-5: the Alert kind reads "Update: moved to clinical utility".
- G3-7: a `:focus-visible` ring with a white offset is defined.
- G3-9: each Dismiss button names its Alert.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| H4-1 | must-fix | Nav: Jobs moved under "More" | Flow 1, the video, starts with "Sam opens Jobs and starts a live job". It now opens on a menu instead of a visible tab. EXPERIENCE.md still says the top bar holds Categories and Jobs, and the IA table still says Jobs is "Reached from: Top bar". The spines win over the mock. | Put **Jobs** back in the bar. When a job is running, show a live count, e.g. "Jobs 112/300", which also helps the video. Keep only Categories under More. Then update the EXPERIENCE.md top-bar line to: "…Graph, Review (count), Alerts (count), Jobs, More (Categories, Rules, Terms)". |
| H4-2 | must-fix | Above the fold at 1440 × 900, 110% zoom | This is a regression from v4. Both "Play briefing" buttons sit at y ≈ 970, below the fold, because the actions moved back under the quote. Flow 1 step 4 ("Rowan presses play") now needs a scroll on camera, and EXPERIENCE says nothing essential goes below the fold on Home. | Put the Play and Dismiss buttons back in the Alert head, beside the kind line, as in v4. You can also trim each Alert quote to 2 lines with "Show full quote" to bring the Alert titles up. |
| H4-3 | must-fix | Hero pulse | All nine changed rings carry `.pulse` on page load. EXPERIENCE.md says "Motion: one orchestrated moment only", the Graph draw-in when a live job files a change, and "nothing else animates". In the video, Home is shown just before the Graph climax, so a pulse here spends the climax early. | Show the hero rings as static glows with no pulse; keep the single pulse for the Graph page during the live run. Or, if Luis wants motion on Home, amend EXPERIENCE.md to name the hero pulse as the one moment and remove the pulse from the Graph page. Do not keep both. |
| H4-4 | should-fix | Change rows lost their source | The MRD row dropped "study NCT07921888". Row 4 ("SuperARMS … moved to clinical utility") also dropped "trial NCT06422546", and row 5 lost "used" ("in trial NCT04769388"). Rows 2 and 3 keep their IDs. The list is now inconsistent, and the two rows that tell the story have no identifier, though the hero labels show it. | "New Tumour-informed ctDNA MRD (approach), Early research, study NCT07921888"; "Changed SuperARMS EGFR mutation detection moved to clinical utility, trial NCT06422546"; "Changed SuperARMS EGFR mutation detection used in trial NCT04769388". If width is tight, drop the word "trial", not the ID. |
| H4-5 | should-fix | Non-visual equivalent of the hero | The hero SVG is `aria-hidden` inside a section labelled only "Your team's neighbourhood". A screen reader hears a label with no content. The changes list is the real text equivalent, but nothing links the two. | Give the hero section `aria-describedby` pointing to the changes list heading and list, plus a visually hidden line: "Network of your team's diagnostics. 5 changed since 2 November, listed under Welcome back." Make "Open the graph" go to `/graph`, where "View as table" lives. |
| H4-6 | should-fix | Changed shown by more than colour | Changed nodes carry a ring that unchanged nodes do not, so there is a shape cue as well as colour. But changed **links** differ from other links only by colour and thickness, and the hero labels have no "New"/"Changed" word. On the dark field, the pink ring and the lavender halo of unchanged nodes look alike at 1080p. | Make the changed ring thicker (3px) and dashed, or add a small eosin dot plus "Changed" in the legend chip with the count: "○ 5 changed since 2 November". Unchanged nodes need no halo. |
| H4-7 | should-fix | Hero and Graph page use different change marks | The hero rings every endpoint of a changed link (F1 Liquid CDx, F1 CDx, NCT04712877 and the other trials). The Graph page (v2) rings only the changed Diagnostic or trial and colours the link. The hero is meant to reuse the Graph component (Story 5.2), so the same data has to look the same on both. | Use one rule: ring nodes that are new or changed themselves, and colour links that are new. The F1 nodes are unchanged; only their trial links are new. |
| H4-8 | should-fix | Logo eosin nucleus (G3-3a) | Still eosin, and the logo sits right next to the eosin hero. | Use a haematoxylin-tint nucleus, or document the logo as the single exception. |
| H4-9 | nice | Unlabelled nodes in the hero | Six lavender circles and three triangles have no label. They read as decoration, and the viewer cannot tell which tests they are. | Dim the unchanged, unlabelled nodes to 50%, or label two of them, e.g. cobas EGFR Mutation Test v2 (the tissue end of the climax path) and osimertinib. |
| H4-10 | nice | Kicker "Your team's neighbourhood" | Pleasant, but vague for a Director. | "Your team's diagnostics: what changed since 2 November". |
| H4-11 | nice | Two capability tags at the top of the page | "MongoDB $graphLookup" (hero) and "Agent Memory (public preview)" (welcome panel). They are in separate panels, which follows the one-per-panel rule, but they sit 400px apart on the same band. | Acceptable, because both are judged items. Keep them both quiet (outline, caption size). |
| H4-12 | nice | Layout below the hero | The Alerts panel (two narrow columns) and the Digest are offset; the Digest starts about 50px lower and has a spacer. On camera this reads as a misalignment. | Align the tops, or let Alerts take the full width with the Digest in the right column of the same row. |

---

# Round 5 (confirmation): Home v6

**Verdict: ship.** Nothing blocks shipping.

The Round 4 must-fixes all landed:
- **H4-1 (Jobs):** Jobs is back in the top bar. Only Categories and the rest sit under "More".
- **H4-2 (above the fold):** the Play briefing button for the SuperARMS Alert, the one Flow 1 needs, is in the Alert head at y ≈ 641, well above the fold at 1440 × 900 with 110% zoom.
- **H4-3 (pulse):** the pulse is now allowed. EXPERIENCE.md Interaction Primitives names the network pulse on the Home hero and the Graph page as the single motion moment, with reduced-motion respected.

The should-fixes landed too:
- **H4-4 (trial IDs):** all five change rows carry their identifier, including NCT07921888 and NCT06422546.
- **H4-5 (screen readers):** the hero has `aria-labelledby` and `aria-describedby`, plus a hidden link: "Network of your team's diagnostics. 5 changes since 2 November, listed below."
- **H4-6 (colour-only):** changes are no longer marked by colour alone. Changed nodes have a ring, new links are dashed, and the legend has "New or changed" (ring) and "New link" (dashed). The hero caption also says it in words: "Pink shows what changed since 2 November."
- **H4-7 (one rule):** the hero and the Graph page now mark changes the same way. Only changed nodes are ringed; the FoundationOne nodes are not, and their new links are dashed.
- **H4-10:** the kicker reads "Your team's diagnostics".
- **H4-12:** the panels below the hero are aligned.

| # | Tag | Element | Note | Fix |
|---|---|---|---|---|
| H5-1 | should-fix | Welcome-back Synthetic marker | Regressed to plain text, "Synthetic: recalled from…". The dotted badge stays on the Team picker but is gone from the recalled memory. EXPERIENCE says: Synthetic badge, always. | Put back `<span class="synthetic">Synthetic</span>` before "Recalled from your team's earlier sessions, created for this demo." |
| H5-2 | should-fix | Dismiss is now an icon only (×) | It has an aria-label and a `title`, so screen readers are covered. But DESIGN.md says "never an icon alone without a label or tooltip", and a `title` only shows on hover, not on keyboard focus. | Restore the "Dismiss" word, or use a shadcn Tooltip that also opens on focus. |
| H5-3 | nice | Second Alert's Play briefing (y ≈ 887) | Just below the fold. It is not part of Flow 1, so this is acceptable. | None needed. |
| H5-4 | nice | Logo eosin nucleus (G3-3a / H4-8) | Still open. | Use a haematoxylin-tint nucleus, or record the logo as the single exception in DESIGN.md. |
| H5-5 | nice | Climax wording in EXPERIENCE.md | Flow 1 step 5 still says "draw in with an eosin ring that pulses once". The amended primitive says changed nodes and links pulse together. | Align the Flow 1 step 5 wording with the amended primitive. |

---

# Review v4 (restyle to match Home v7)

Inputs: `shots/review-v4.png`, `shots/review-v4-full.png`, `key-review.html`, `shots/home-v7-topbar-crop.png`.

**Verdict: ship.** No must-fixes.

**Consistent with Home's story:**
- The counts match. The top bar shows Review 7 and the header says "7 proposed changes waiting". There are 6 rows on screen and "1 more change below", which makes 7.
- The three Team proposals (Guardant360 CDx response monitoring, SuperARMS osimertinib, FoundationOne Liquid CDx treatment selection) are the top three rows. They are the same three as Home's Digest, ordered low-confidence first.
- The rule finally pays off. The header says "2 are flagged by your new rule". The panel shows "Rule on", the rule text "Flag findings from cell-line or animal studies.", "It flags 2 of 7 pending changes" and lists both. Both rows exist: FoundationOne CDx with MALAT1 (PMID 42934891) and Oncomine Dx Target Test with GATA5 (PMID 42968152), each marked "Flagged by your rule". In the held-back PubMed set, 42968152 mentions cell lines and xenografts, and 42934891 mentions xenografts or mice, so the flags are credible.
- PubMed appears only as PMIDs.
- The top bar matches Home v7: the DXP logo, Jobs in the bar, "Sam" shown with the avatar, and the same Team picker.

**Conforms to EXPERIENCE.md:**
- Proposal rows are written as sentences.
- The focused row has full Accept, Edit and Reject buttons; the other rows have compact ones on one line.
- Every icon sits beside a word, with `aria-hidden` set on the icons.
- The rule draft panel shows its state after "Turn on rule".
- The capability is named once in the rule panel.
- The focused row stands out clearly.

| # | Tag | Element | Problem | Fix |
|---|---|---|---|---|
| RV4-1 | should-fix | Keyboard legend | Regression from v3: `Esc` (cancel) was dropped. EXPERIENCE.md lists j, k, a, e, r and Esc on the Review page. Edit and Reject open a reason field, and the Reviewer needs to know how to back out. | Add "<kbd>Esc</kbd> cancel" as a third group, so the legend reads "j k move · a e r accept, edit, reject · Esc cancel". |
| RV4-2 | should-fix | PubMed rows (MALAT1, GATA5) and the rejected item | They show "PubMed, PMID …" as plain text, with no link and no "data as of". Evidence rule: source, identifier **link** and "data as of" always travel together. On camera these are the only rows without Evidence, which undercuts the "every value has a source" claim at the very moment the rule pays off. | Make each PMID a link to pubmed.ncbi.nlm.nih.gov. Add "data as of 12 November 2026". Note in the mock comment that the live app shows the quote (at most 300 characters) here. |
| RV4-3 | should-fix | "New" mark on the SuperARMS row | Still present (R8, R2-2). Every proposal is new, and the eosin "New" competes with real changes. The track's eosin segment already shows that the stage moved. | Remove the "New" mark. |
| RV4-4 | nice | Flag text on the two rows | "Flagged by your rule: cell-line or animal study" paraphrases the rule. | "Flagged by your new rule: Flag findings from cell-line or animal studies." |
| RV4-5 | nice | Panel's list of flagged changes | The two items are plain text. A keyboard user cannot jump to them, and they sit below the fold. | Make each item a link that moves focus to its row. |
| RV4-6 | nice | Focused row `aria-label="Focused change"` | It replaces the row's accessible name, so a screen reader no longer hears the Diagnostic. | `aria-label="Guardant360 CDx, add response monitoring to Clinical uses (focused)"`, or use `aria-current="true"` and keep the heading as the name. |
| RV4-7 | nice | Review count | No `aria-live="polite"` on the count, which the accessibility floor asks for. | Add it to the "7 proposed changes waiting" line and to the top-bar count. |
| RV4-8 | nice | Low-confidence reason | The whole sentence is ochre (R2-5). | Keep the circle and "Low confidence:" in ochre, and set the reason in muted ink. |
