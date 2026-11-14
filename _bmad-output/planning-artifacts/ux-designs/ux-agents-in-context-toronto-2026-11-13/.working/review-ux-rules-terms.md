# UX review: Rules and Terms key screens (v1)

Reviewer: senior UX, 2026-11-13. Inputs: `shots/rules-v1.png`, `shots/terms-v1.png`, `key-rules.html`, `key-terms.html`, `../EXPERIENCE.md`, `../DESIGN.md`, Stories 2.6, 2.7, 4.8 in `epics.md`, the API contract and `Rule` shape in `ARCHITECTURE-SPINE.md`. Cross-checked against `key-review.html` and `key-home.html`. PMID 42985469 checked in `data/pubmed/heldback.jsonl` (ZNF471, osimertinib resistance, cell-line and animal work: the rejection reason fits). All nine unmatched terms occur in `data/`.

Tags: **must-fix** (breaks the story, the API contract or the accessibility floor), **should-fix** (spine conformance or clarity), **nice**.

## Verdicts

| Page | Verdict | One line |
|---|---|---|
| Rules (`/rules`, Story 2.7) | **Fix, then ship** | Meets every Story 2.7 rule-list criterion and matches Review exactly. But it shows people, dates and a "New" mark that `Rule` does not return, renders the capability tag as a sentence, and the Off switch fails non-text contrast. |
| Terms (`/terms`, Story 4.8) | **Fix, then ship** | Meets the one criterion (term + times seen). Two columns and the side panel need data that `GET /terms?status=unmatched` is not specified to return. Cut candidate: keep it cheap. |

What works: the Rules header copy ("A rule only flags proposed changes for you to look at; it never rejects them. Turning a rule off removes its flags at once.") states AD-7 plainly. The Synthetic badge is on every made-up rule and not on Sam's live one. The visible On/Off text means colour is not the only signal. The switch is a real `role="switch"` with `aria-checked` and the rule text as its name. The origin line gives a PMID only, with no abstract text, on both pages. The Terms table has proper `th scope="col"` and right-aligned tabular numbers.

---

## 0. Cross-page data consistency

| Check | Rules / Terms | Review / Home | Result |
|---|---|---|---|
| Rule text | "Flag findings from cell-line or animal studies." | Review rule card and both flag notes: same | OK |
| Source proposal | "Add biomarker ZNF471 to Guardant360 CDx", PMID 42985469, reason "Cell-line study, not patients." | Review rejected block: same | OK |
| Flag count, rule 1 | "2 flagged" | "It flags 2 of 7 pending changes" (FoundationOne CDx + MALAT1, Oncomine + GATA5, both Biomarkers) | OK |
| Flag count, rule 2 | "1 flagged" (Trials) | Ventana PD-L1 (SP263) "Add trial NCT06284317 to Trials" carries that rule's note | OK |
| Pending total | (not shown) | Review 7 in top bar | OK |
| Synthetic Team | "Thoracic oncology · Synthetic" | same | OK |
| Capability tag | Sentence: "Each rule you turn on is also saved to MongoDB Agent Memory as a procedural rule." | Review: "Also saved to MongoDB Agent Memory as a procedural rule." Home: "Agent Memory (public preview)" | **Three renderings, see R1** |
| Rule scope | Rules page: no Team scope | Review calls the synthetic trial rule "Team rule" | **Mismatch, see X1** |
| Count noun | Rules side panel: "9 words" | Terms page: "9 terms" | **Mismatch, see R9** |

| # | Tag | Problem | Fix |
|---|---|---|---|
| X1 | should-fix (in `key-review.html`) | Review labels the trial rule "Team rule". The architecture says "Rules apply to every Team", and the Rules page shows no Team. | Review: "Learned rule (Synthetic): count an assay as used…". |
| X2 | nice | The top bar on all mocks is missing "Categories" (EXPERIENCE IA lists it) and uses a "More" menu that the spine does not define. These pages show it as "More: Rules" / "More: Terms". | Either add Categories and an overflow menu to EXPERIENCE.md, or follow the IA. Keep it the same on all mocks. |

---

## 1. Rules (`/rules`)

**Story 2.7 criteria on this page:** lists every rule with field, text, status and an on/off switch (met); synthetic rules labelled (met); carries the Agent Memory capability tag (met in substance, wrong form, R1). **Story 2.6:** `GET /rules` returns `Rule { id, field, text, status: draft | active | off, from_proposal_id, synthetic }`. That shape bounds what the page can show.

### Must-fix

| # | Element | Problem | Fix |
|---|---|---|---|
| R1 | Capability tag | The spec asks for a quiet outlined **tag** reading "Agent Memory, procedural", with the hover/focus sentence "Each rule you turn on is also stored as procedural memory." (EXPERIENCE MongoDB table, DESIGN Capability tag). The mock shows a muted sentence instead, worded differently from Review's and in a different form from Home's. It also always says "Agent Memory", but on the fallback backend the spec requires "Memory in Atlas collections" (read from `NEXT_PUBLIC_MEMORY_BACKEND`). | Use one `CapabilityTag` component on all pages: an outlined caption tag "Agent Memory (public preview) · procedural", or "Memory in Atlas collections" on the fallback. Make it focusable (`tabindex="0"`), with a tooltip on hover **and** focus carrying the spec sentence. Use the same component on Review's rule card and on Home. |
| R2 | Per-rule "Sam, 13 November 2026" and "Turned off 2 November 2026" | `Rule` carries no actor, no created date and no status-change date. `POST /rules/<id>/status` takes `actor`, but the response does not return it, and the `rule_status_changed` Event has no actor or rule ID. The screen would have nothing to bind these to. | Pick one, and record the choice in the architecture or the story: **(a)** add `status_by` and `status_at` to `Rule` (two fields written by `rules.set_status`); this is cheap and keeps the page as drawn. **(b)** Drop the who/when line, and for rule 1 take "Sam, 13 November" from the source proposal's `decided_by`/`decided_at` (already in `Proposal`) inside the origin sentence. Recommended: (a). |
| R3 | "New" changed mark on rule 1 | Eosin "New" means new since this Team's last visit (`seq` above `last_seen_seq`). `Rule` has no `seq`, and the rule event carries no `rule_id`, so the client cannot compute it. | Highlight the rule you arrived with instead: Review's "Open rules" goes to `/rules?rule=<id>`. That row gets the changed mark and keyboard focus, and the mark clears when you leave. This uses no new API field, and on camera it reads as "here's the rule I just made". |
| R4 | Off switch contrast | The Off track `#C3C8D8` on white is about 1.7:1. WCAG 2.2 1.4.11 needs 3:1 for a control's boundary and state. The white thumb on that track is also below 3:1. The "Off" text keeps state from depending on colour, but the control itself is hard to see (visible in the screenshot). | Off track: white fill with a 1.5px `{colors.muted-foreground}` (#5A5F7D, 6.4:1) border, thumb `#5A5F7D`. On track stays `ink-deep` with a white thumb. |
| R5 | Draft rules | `status` has three values (`draft`, `active`, `off`), and `GET /rules` "lists every rule", so a drafted rule that was discarded or never confirmed will appear. The mock has no draft state, and a binary switch cannot show one. EXPERIENCE also says the screen applies no display rule of its own, so the page cannot quietly hide drafts. | Either (a) have Discard in the rule panel set the rule `off` (or delete the draft) so `GET /rules` never returns stale drafts (an API decision for Story 2.6), or (b) draw a draft row: dotted text, "Suggested, not on yet", a "Turn on" button instead of a switch. Recommended: (a), plus (b) as a fallback for a draft left open when the page loads. |

### Should-fix

| # | Element | Problem | Fix |
|---|---|---|---|
| R6 | Switch feedback | EXPERIENCE Rule switch: immediate, and the toast gives the count of affected proposals. The mock does not show the toast or its copy, and no failure path exists. | Specify the toasts. On to off: "Rule off. Flags removed from 2 proposed changes." Off to on: "Rule on. It flags 1 of 7 pending changes." On failure, revert the switch and toast "Couldn't change the rule. Try again." The pending switch is `aria-busy`, and the flag counts update politely (`aria-live="polite"`). |
| R7 | Flag counts | Counting `check.flags[].rule_id` over `GET /proposals?status=pending` (paginated with `next`) is a client-side join. That is fine, but it is not written down anywhere, so a developer may look for a `Rule.flag_count` that does not exist. | Add a note to Story 2.7: "flag count = pending proposals whose `check.flags` include this rule_id, from `GET /proposals?status=pending`". Or have `GET /rules` return `flagged_pending`. |
| R8 | Right-hand status column copy | Three grammars: "2 flagged / in Review", "Nothing pending / to flag", "Off, flags / nothing". The link's accessible name, "2 flagged", is ambiguous out of context, because a screen-reader link list has 2 links both called "N flagged". | Use "Flags 2 in Review", "Flags none pending" and "Off". Put the whole phrase inside the link, or add `aria-label="Open the 2 proposed changes this rule flags in Review"`. |
| R9 | Unmatched terms side panel | "9 words the agents met…" while Terms says "9 terms". Several are phrases, not words. The panel also adds a second API call and a dependency on Story 4.8, which is a cut candidate. | Change "words" to "terms". If 4.8 is cut, the panel goes too, and the page should still balance without it (see N2). |
| R10 | Empty and loading states | None are specified. EXPERIENCE lists none for Rules. | Empty: "No Learned rules yet. When you reject or edit a proposed change with a reason, DxP suggests a rule from it." with a link to Review. Loading: skeleton rows in the same three-column shape. Add both to the EXPERIENCE State Patterns table. |
| R11 | Origin line on synthetic rules | Only rule 1 explains where it came from. The three synthetic rules have `from_proposal_id` (possibly a synthetic correction) but show nothing, so the origin looks like a feature of only one rule. | When `from_proposal_id` resolves, show the same line, with the correction marked Synthetic. When it does not, show "Seeded for this demo" next to the Synthetic badge. |
| R12 | Memory claim on re-activation | The architecture says Agent Memory gets one copy "when a rule first becomes active". The tag sentence is right; just do not add copy implying that turning a rule off removes it from memory. | No change needed. Keep the off-state copy about flags only. |

### Nice-to-have

| # | Problem | Fix |
|---|---|---|
| N1 | The switch hit area is 40×22. It passes WCAG 2.5.8 through the spacing exception, but it is fiddly. | Make the switch plus its On/Off label one 44px-tall target. |
| N2 | The main panel is 880px and the aside 392px, while DESIGN specifies a 360px right-hand panel. The page has about 300px of dead space below at 1440×900. | Use the 360px aside. If Terms is cut, run the rule list full width at about 72ch for the text. |
| N3 | The off rule's text is greyed to muted, which makes it look disabled rather than off. | Keep the rule text in foreground ink. The switch and the "Off" label are enough. |
| N4 | Demo: the page is not a climax, but it is the proof that the learning is under Sam's control. | On camera: arrive from Review's "Open rules", show the highlighted rule with "Flags 2 in Review", flip the synthetic "conference abstract" rule off and on to show the toast, and leave. Under 6 seconds. |

---

## 2. Terms (`/terms`)

**Story 4.8 criterion:** each unmatched term shows with the number of times it was seen. Met. The `Term` type is not defined in the architecture's API types. The terms document is `{ mappingType: "equivalent", synonyms: [<term>], status, curated }` plus "DxP's own fields", unnamed.

### Must-fix

| # | Element | Problem | Fix |
|---|---|---|---|
| T1 | "Field it came up in" and "Last seen" columns | The contract does not specify either. The count is implied by the story, and nothing else is. The same holds for the "Counts cover every job since the Baseline load" footer, which describes counting semantics nobody has agreed on. | Either define `Term { id, term, field, seen_count, last_seen_at, status, curated }` in the architecture's API types (the pipeline already knows the field when a match fails), or drop both columns and the footer and ship term + count only. Recommended: define the type. It is three fields, and Field is what makes the list actionable. |
| T2 | "Curated synonyms" side panel | `GET /terms?status=unmatched` does not return curated terms, and no endpoint lists them. The panel shows "liquid biopsy ↔ ctDNA · Curated" as if it were data. | Either make it static explanatory copy with no data look (no "Curated" chip, no binding), or add `GET /terms?curated=true`. Recommended: static copy, or cut it. FR-9's "liquid biopsy finds ctDNA" belongs on camera in Find, where the Vector Search tag sentence already says it. |

### Should-fix

| # | Element | Problem | Fix |
|---|---|---|---|
| T3 | Empty and loading states | None are specified. | Empty: "No unmatched terms. Every term the agents met maps to a standard name." Loading: skeleton table rows. Add both to the EXPERIENCE State Patterns table. |
| T4 | Sort ties | "Sorted by times seen", but the tie order is inconsistent. In the 3s, 12 Nov comes before 11 Nov (newest first). In the 2s, TMB-high (9 Nov) comes before bronchoscopic biopsy NGS (10 Nov) (oldest first). | Sort by times seen, then by last seen, newest first: swap those two rows. Say so in the footer: "Sorted by times seen, then most recent." |
| T5 | Column header copy | "Field it came up in" is chatty, and the Voice section prefers plain glossary names. | Use "Field". |
| T6 | Header link | The "Learned rules" ghost link in the header is the only way back. It is fine, but its icon (shield) is not explained. | Keep it, or replace it with a breadcrumb: "Learned rules / Unmatched terms". |

### Nice-to-have

| # | Problem | Fix |
|---|---|---|
| N5 | The table has no `<caption>`, so screen-reader table navigation announces it unnamed. | `<table aria-labelledby="t-title">` or a visually hidden caption, "Unmatched terms, sorted by times seen". |
| N6 | The Reviewer can see a gap but do nothing about it, which the story allows. | If time allows later: "Map to…" per row (a future story). Do not add it now. |
| N7 | The page will almost certainly not appear in the 3-minute video (cut candidate). | Build it as a plain shadcn `Table` in 30 minutes. Do not polish it. |

---

## 3. Checks passed

- **PubMed abstract text:** none on either page. Only "PMID 42985469" with a link, plus the Reviewer's own reason.
- **Synthetic labelling:** on the three seeded rules and the Team picker, and not on Sam's live rule. Correct.
- **Colour never the only signal:** "New" plus dot, "On"/"Off" text, the Synthetic word. Pass.
- **Text contrast:** muted `#5A5F7D` on white 6.4:1, eosin-text `#B8325F` 5.7:1. Pass. The one failure is the Off switch (R4).
- **Keyboard:** the switches are `<button role="switch">`, the links are real `<a>`, and tab order follows reading order. Focus ring `:focus-visible` with a white halo. Pass. The mock's capture box is a `<label>` with no input (shared with the other mocks): build it as an input.
- **Voice:** plain and glossary-true ("Learned rules", "proposed changes", "Synthetic"). Apart from R8 and T5, no copy issues.
