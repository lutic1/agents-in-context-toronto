---
title: "PRD Addendum: DxProvida (DxP)"
created: 2026-11-12
updated: 2026-11-12
---

# PRD Addendum: DxProvida (DxP)

Detail that belongs in architecture, UX or epics, kept here so the PRD stays short. Stack choices, data sources, the nine Lifecycle stage definitions and the event facts are in the brief's addendum at `../../briefs/brief-agents-in-context-toronto-2026-11-12/addendum.md` and are not repeated.

## 1. Users and journeys as supplied by Luis (12 Nov)

These come from a discovery session with users. Items marked "inferred" were not raised in that session.

### Roles

| Role | Role in the journey | Usage frequency |
|---|---|---|
| Strategy lead | Defines intended uses, shortlists vendors, commissions pilots and external-facing comparison reports | Episodic. Bursts around a new intended use or a major congress |
| Domain expert | Subject specialist; builds category landscapes, prepares external advisory boards | Project-driven. Heavy use for weeks, then quiet |
| Data curator | Owns the existing curated dataset and acts as the quality gate | Continuous, low-intensity. Wants less manual work, not a new place to do it |
| Downstream consumers | Colleagues who read the outputs | Read-only. Inferred |
| New or returning user | Joins mid-project, or returns after months away, with no working memory of the tool | Cold start, repeatedly |

Design consequence: nobody logs in daily, so the app must be self-explanatory on return after six weeks away, and the automation has to run unattended in between.

### Journey 1: intended-use shortlisting (primary)

Trigger: a new intended use is defined, for example monitoring patients with a specific cancer type and stage.

| Stage | What the user does | What the app does |
|---|---|---|
| 1. State the need | Describes the intended use in plain language or sets filters: modality, target indication, minimum specificity, minimum sensitivity, validated clinical data in that indication | Parses into a structured query across all records |
| 2. See candidates | Scans a result set, not individual records | Returns a comparison table, one row per assay, columns being the criteria asked for |
| 3. Judge the evidence | Checks where each number comes from: which study, what population, cohort or randomised, retrospective or prospective, analytical or clinical validation, number of samples | Shows each performance value with its citation and study context inline |
| 4. Apply operational constraints | Narrows on sample volume, sample material, turnaround, regulatory status | Filters on the operational field set |
| 5. Shortlist | Picks the top two or three providers | Saves the shortlist against the named intended use |
| 6. Export | Takes it into a vendor meeting, or packages it as a comparison report for external experts | Generates the comparison output with references intact |
| 7. Close the loop | Records what happened: pilot proposed, deprioritised, specifications requested | Keeps the decision attached to the intended use. Inferred |

What is being fixed: today the user opens each record and extracts sensitivity and specificity by hand. The journey succeeds the moment a cross-record query returns a populated table.

Where it fails: a number without a traceable source. An uncited 97% specificity is worse than a blank cell. The app also needs an explicit "no data for this indication" state, because for many realistic queries nothing is published.

### Journey 2: category landscape refresh

Trigger: a planned deliverable, such as an annual planning landscape or an external advisory board.

1. Selects a category, for example all assays of one detection approach.
2. Pulls the full field set per assay: approach type, number of cancer types covered, studies available, performance by cancer stage and cancer type, provenance of the clinical data, regulatory status and timeline.
3. Spots the gaps: records that are thin, stale or missing a needed field.
4. Fills gaps manually from their own searching, and the entry persists for everyone.
5. Exports a landscape view for a presentation and the advisory discussion.
6. Brings external advisor insight back. Inferred: nothing in the session said the app captures advisor feedback.

Design consequence: performance is not one number per assay. It is a matrix of stage by cancer type, and must be stored that way from the start or Journey 1's filtering will compare incomparable figures.

### Journey 3: monitored-update digest (the automation core)

Trigger: the app, on a scheduled scan of the agreed sources.

| Stage | Detail |
|---|---|
| Scan | Approved source types only: peer-reviewed literature databases, clinical trial registries, regulatory filing and approval records, provider websites, and congress abstracts, posters and oral presentations |
| Gate | Apply the maturity criteria before anything surfaces: number of samples, cohort or randomised design, analytical or clinical validation. A technology with no credible validation behind it should never reach the queue |
| Match | Attach the find to an existing tracked tool wherever possible. The stated need is updates to tools already on the list, not a firehose of novelty |
| Propose | Draft the field-level change: a new readout updates sensitivity; a regulatory submission updates approval status |
| Notify | A digest sized for an episodic user. Weekly or event-driven, spiking around congress season |
| Act | User reviews, accepts, edits or rejects; accepted changes update the record with the source attached and the prior value retained |

Where it fails: silent overwriting.

Difference from the PRD: congress abstracts, posters and presentations are listed here as approved sources and are out of scope for Saturday.

### Journey 4: capture on the go

Trigger: something learned off-platform, such as a congress conversation about an untracked technology.

1. User submits what they have: a provider name, a conversation note, or a photograph of a poster.
2. An agent extracts what it can into the structured fields and flags what is missing.
3. It checks whether the organisation already exists, to avoid a duplicate.
4. User confirms or corrects; the entry is tagged as manually sourced, with submitter and date.
5. It joins the monitored set, so later automated scans pick it up.

This journey is the one most likely to be used from a phone, in a convention centre, on poor wifi, by someone who will not come back to tidy it up. A partial record clearly marked partial is the right outcome.

## 2. Notes for architecture

- **Performance storage.** Later development, not Saturday. One entry per Diagnostic, tumour type and Tumour stage, each with its own study context and Evidence (FR-6).
- **Field history.** Every field keeps its earlier values, the Evidence for each, and the Reviewer decision that replaced it (FR-17).
- **Reviewer corrections.** The brief described a correction three ways: making the check stricter, feeding back as an example, and a learned rule. The PRD requires only the visible behaviour in FR-19. Whether that is one mechanism or several is an architecture decision.
- **Agent roster.** Not fixed by the PRD. The plan's watcher, extractor, checker and writer split is a starting point.
- **Graph view.** The team wants connections between clusters visible, not only clusters. The plan's Knowledge layer already holds the links between assay, biomarker, tumour type, trial, drug and company.
- **Alert rule inputs.** FR-12 and FR-13 need, per Team and Diagnostic, whether a first Alert has been sent, and per Diagnostic, the Lifecycle stage history, lines of therapy, linked trials and standard-of-care status.

## 3. The wow moment and the MongoDB mapping

Decided 12 Nov: the wow moment is the agentic work with memory, shown in the video connecting to the Graph view, with MongoDB's capabilities presented as the competitive advantage. Judges score creativity, originality and novelty equally.

Which MongoDB capability powers which behaviour, taken from the team's plan. Architecture confirms or changes each row.

| Behaviour in the PRD | MongoDB capability named in the plan |
|---|---|
| Resume after weeks away (FR-28) | Atlas Agent Memory, episodic |
| Learned rule after a rejection (FR-19) | Atlas Agent Memory, procedural |
| Synonyms: "liquid biopsy" finds ctDNA (FR-9) | Atlas Agent Memory, taxonomic; synonym search |
| Plain-language query across Records (FR-21) | Automated Embedding with vector search |
| Connected Graph view (FR-26) | Graph lookup across assay, biomarker, tumour type, trial, drug and company |
| Alerts and the graph updating as a change lands (FR-13, FR-27) | Change streams |
| A new kind of Diagnostic arriving with new fields | Flexible documents, no schema change |

Earlier candidates, kept for the scoping session: the guardrail that rewrites itself and flags other pending Proposed changes (FR-19), and the graph redrawing as an accepted change lands (FR-26, FR-27). Both sit inside the decided wow moment. The photographed poster is out for Saturday on licensing grounds.
