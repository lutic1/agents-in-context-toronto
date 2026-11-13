---
title: "Adversarial review: PRD for DxProvida (DxP)"
created: 2026-11-12
lens: adversarial (bmad-review)
target: prd.md
read alongside: addendum.md, ../../briefs/brief-agents-in-context-toronto-2026-11-12/brief.md and addendum.md
---

# Adversarial review: PRD for DxProvida (DxP)

Review only. No existing file was changed. Line numbers refer to `prd.md` unless another file is named.

The owner's deliberate decisions are not re-argued: lung only, no congress sources, the ten Medical-agreed fields, no numeric gate thresholds, Early research as a label not a filter, the cut line set at the scoping session, and no fixed agent roster or learned-rule mechanism. Where a finding touches one of these, it attacks a consequence, not the decision.

Severity was added at the requester's ask (the lens itself does not rank):

- **Critical:** a primary success metric or the product's core claim fails if this is left as written.
- **High:** a P1 behaviour is undefined or contradictory, a P1 dependency can take the day, or a judge's first question has no answer.
- **Medium:** a real gap with a workaround, or one that matters after Saturday.
- **Low:** wording, consistency between documents, vacuous tests.

Counts: 4 critical, 13 high, 16 medium, 10 low.

## Verdict

The PRD describes a product, not a six-hour build: 23 of the 26 Saturday-eligible requirements are P1, the loop that SM-2 depends on needs an "update" and a history that a same-day ingest cannot produce, and the alert rule, the Lifecycle stage and the Learned rule each have cases with no defined behaviour. §9's "None block the build" does not hold: ADV-02, ADV-03, ADV-05, ADV-06 and ADV-11 each block architecture.

---

## Critical

### ADV-01 (critical). P1 is nearly everything, so it gives the scoping session nothing to cut with

**Where:** §6.1, lines 171 to 173. "**P1, the demo spine:** §4.1 to §4.4 (without FR-6 and FR-10), FR-21 and FR-22, §4.6 and §4.7."

**Problem:** That is FR-1 to 5, 7 to 9, 11 to 22 less 23, 26 to 28: 23 requirements. Only FR-24, FR-25 and FR-29 are P2, and P3 has no numbered requirements. Two people for six hours is 720 person-minutes, about 31 minutes per P1 requirement, before integration, deployment and re-running a batch. The primary success metrics (SM-2, SM-3, SM-4) validate only 12 of the 23: FR-1, 4, 7, 15, 16, 17, 19, 21, 22, 26, 27, 28. The other 11 (FR-2, 3, 5, 8, 9, 11, 12, 13, 14, 18, 20) are P1 yet no primary metric needs them, so the PRD's own metrics already imply a cut line that §6.1 does not draw.

**Smallest fix:** Split P1 in §6.1 into "P1a, must be on camera" and "P1b, build only after P1a records end to end". P1a is the SM-2 thread plus its true prerequisites: FR-5, FR-7, FR-3 (exact-key matching only, see ADV-11), FR-15, FR-16, FR-17, FR-19, FR-28, and a one-Diagnostic neighbourhood version of FR-26 and FR-27. See the feasibility table at the end for what can be reduced honestly.

### ADV-02 (critical). The ten fields are per study, the Record is per Diagnostic, and FR-15's test replaces where it should add

**Where:** FR-15, line 116. "*Test:* a new trial registration proposes a change to the trial ID and linked drug; a new study readout proposes a change to study size and key result." Glossary, line 52: "One Diagnostic has one Record." Brief, line 38: "Every finding becomes a structured record with the same fields."

**Problem:** The brief's fields were designed per finding. The PRD moved the Record to the Diagnostic without changing the fields. A Diagnostic has many trials, many studies and many linked drugs, so a second trial is an addition, not a change from "current value" to "new value". As written, accepting the demo's Proposed change replaces a valid trial ID with another, and FR-26 then shows one linked trial per Diagnostic. "Study size and key result" becomes one figure per Diagnostic, which is exactly what FR-6 forbids for Performance values ("never as one figure per Diagnostic") and what the addendum warns will "compare incomparable figures". With FR-6 deferred, the performance number still arrives on Saturday as free text inside "key result", with none of FR-6's protection. A domain-literate judge watching the wow moment sees the agent discard a trial.

**Smallest fix:** One sentence in §4.2 naming which fields hold one value per Diagnostic (modality, biomarker or gene, sample type, sponsor) and which are lists of per-study entries (trial ID with linked drug, study size with key result, stage or line of therapy, clinical use). Give Proposed change two kinds, "set" and "add". Rewrite FR-15's test: a new trial registration proposes adding a trial and linked drug; a later version of the same registration or readout proposes a change to that entry's study size or key result. In FR-22, show key result per study, never one per Diagnostic.

### ADV-03 (critical). SM-2 needs an update, a prior value and a "last visit", and a one-day ingest has none of them

**Where:** SM-2, line 191. "an agent finds an update, drafts a Proposed change, a Reviewer decides, the Record updates with the prior value retained, and the change appears in the Graph view." FR-12 test, line 106: "the same Diagnostic on reaching assay development produces exactly one." FR-27, line 140: "since the user's last visit". FR-11, line 105: "keeps every earlier stage and its date."

**Problem:** Every Record will be created on Saturday from a corpus pulled beforehand ("pulling it is the agreed next step", brief addendum line 43). Real Sources do not publish a matching update during a three-minute recording, no Diagnostic changes Lifecycle stage in six hours, and every change is "since the last visit" unless the last visit is invented. The PRD does not say how an update comes to exist. The only workable answer is to hold back real Source items and release them on a manual scan, which is honest only if disclosed, and §8's "Event rules" line does not cover it. Left unsaid, the team either discovers this at 15:00 or stages it quietly.

**Smallest fix:** Add to §8: "The demo uses a held-back set of real Source items, dated after a stated cut-off and released by a manually triggered scan. The video and the README say so. Every Record change stores two dates, the Source item's publication date and the date DxP ingested it; Lifecycle history and 'what changed' use the publication date in replay." Change SM-2 to "on real Source items, replayed".

### ADV-04 (critical). Nothing requires the quote to exist in the Source

**Where:** FR-5, line 94. "*Test:* every populated field opens to a quote from its Source." FR-18, line 119. "*Test:* a field whose quote does not support its value fails the check." §8, line 206: "Provenance is the product."

**Problem:** FR-18 checks the value against the quote. No requirement checks the quote against the Source item. A model can produce a plausible quote that is not in the document, and every test in §4.2 and §4.4 passes: the field "opens to a quote", the quote "supports" the value, FR-7 sees Evidence. A fabricated citation is worse than the uncited 97% that UJ-1 calls worse than a blank. This is the first thing a judge from Cohere or Vector Institute will ask.

**Smallest fix:** Add to FR-5: "The quote is an exact span of the stored Source item text, confirmed by string match, not by a model. A field whose quote is not found is not populated. *Test:* altering one character of a stored quote removes the value from every view." This is deterministic, cheap to build, and can replace the confidence score on Saturday (see ADV-29).

---

## High

### ADV-05 (high). Record creation and Lifecycle stage changes bypass "a Reviewer decides"

**Where:** FR-16, line 117. "*Test:* no Record field changes without a Reviewer action logged against it." §5, line 162: "Agents do not change a Record without a Reviewer's decision." FR-15, line 116, covers only "a Finding about a tracked Diagnostic". FR-11, line 105.

**Problem:** Two unstated exemptions. (1) FR-3 and FR-5 create and fill a new Record with no Reviewer, so after a 300 to 500 item batch nearly every value in the system is one "nobody vouched for", the failure UJ-3 names. Nothing distinguishes a reviewed value from an unreviewed one in the comparison table. (2) The PRD does not say whether Lifecycle stage is a Record field. If it is, FR-12 and FR-13 Alerts wait on an episodic curator and "unattended" is false for Alerts. If it is not, agents silently change the value that drives every Alert and the Early research label.

**Smallest fix:** Add to §4.4: "A new Record is created without review; each of its values is marked 'agent-extracted, not reviewed' until a Reviewer accepts it. Lifecycle stage is a Record field and changes only through an accepted Proposed change." Add the reviewed or unreviewed mark to FR-22.

### ADV-06 (high). The first batch alerts every Team about everything

**Where:** FR-12, line 106. "when it matches the Team profile". Note, line 110: "A Diagnostic first found beyond analytical validation gets a first Alert at its current Lifecycle stage `[ASSUMPTION]`." Glossary, line 67: Team profile holds "tumour types, Categories, biomarkers, linked drugs and saved Intended uses".

**Problem:** "Matches" is undefined: any element, or all. FR-14's test ("names the element of the Team profile that matched") implies any one. On Saturday every Diagnostic is lung and every Team follows lung, so every Diagnostic matches every Team on tumour type. Every Diagnostic is also "first found" in the first batch, and the Note gives each one a first Alert whatever its stage. The result is hundreds of Alerts on the first run, the opposite of line 20 ("alerts a Team only when something becomes applicable") and of SM-C1.

**Smallest fix:** In FR-12: "A match needs at least one of biomarker, Category, linked drug or saved Intended use; tumour type alone is not a match. Diagnostics present after the first load are the baseline and send no first Alert." Narrow the Note to Diagnostics first found after the baseline.

### ADV-07 (high). FR-12 has paths on which a relevant Diagnostic is never alerted

**Where:** FR-12, line 106. "is at assay development or analytical validation". FR-13, line 107. "After the first Alert".

**Problem:** Three cases have no defined behaviour. (a) A tracked Diagnostic at discovery whose next Finding places it at clinical validation: it was not "first found beyond" the window, it is not in the window, so no first Alert is ever sent, and FR-13 applies only after a first Alert. Assay development rarely has a public Source item, so this is the common path, not the rare one. (b) A Team adds a biomarker to its profile after the Diagnostic has left the window. (c) A Team dismissed the first Alert; the profile records dismissals (line 67), but FR-13 does not say whether updates still arrive. Separately, FR-12's text and the Note at line 110 disagree, and "comes from an approved Source" is redundant with FR-2.

**Smallest fix:** Restate FR-12 as one rule: "A Team gets a first Alert the first time a Diagnostic both matches its profile and is at assay development or later, if the Team has not been alerted about it." That covers (a) and (b) and absorbs the Note. Add one line on dismissal.

### ADV-08 (high). Three of FR-13's four triggers cannot fire, or fire constantly, on Saturday's Sources

**Where:** FR-13, line 107. "advances a Lifecycle stage, is adopted for a line of therapy, is used in a trial, or becomes standard of care." §8, line 209: Sources are "ClinicalTrials.gov, PubMed, the FDA companion diagnostics list and Provider websites".

**Problem:** "Used in a trial": the main corpus is a trial registry, so every new registration that names a tracked assay is an update Alert, a firehose for any widely used assay. "Becomes standard of care": the brief addendum defines adoption as "At that point it is standard of care", so this duplicates "advances a Lifecycle stage"; and guideline inclusion, reimbursement and adoption appear in no Saturday Source except a Provider's own claims. "Standard-of-care status" (addendum line 94) is not one of the ten fields. Also undefined: whether an Alert fires on the Proposed change or on its acceptance; whether two Source items reporting one advance send two Alerts; and what happens when a stage moves backward (a withdrawn approval, or a Reviewer correcting a misclassified stage), which sends nothing now and a duplicate Alert on the re-advance. The test is negative only.

**Smallest fix:** For Saturday, cut FR-13 to "advances a Lifecycle stage, on acceptance of the Proposed change, once per stage per Team", mark the other three triggers later development, and add a positive test: "an accepted advance from analytical to clinical validation sends one Alert however many Source items report it."

### ADV-09 (high). Early research has no boundary and no unknown state

**Where:** FR-2, line 86. "marks a Diagnostic with no credible validation behind it as Early research ... *Test:* a Diagnostic at discovery or assay development carries the Early research label". FR-12, line 106: "The Alert carries the Early research label where it applies."

**Problem:** With thresholds deferred, the test makes the label a function of Lifecycle stage alone, but only for two stages. A Diagnostic at analytical validation is in FR-12's alert window and has no clinical validation: labelled or not? FR-11 forces "one Lifecycle stage" with no "not determinable" option, yet a trial that uses ctDNA as an exploratory endpoint does not reveal a stage. An approved companion diagnostic first seen through a trial record, before the FDA list is matched, would be stamped Early research. Nothing says when the label comes off or who decides. The test's "discovery ... Alert" case is vacuous because §4.3 says discovery produces no Alert.

**Smallest fix:** In FR-2: "Early research applies at discovery, assay development, analytical validation and when the stage is not determinable. It is removed only when an accepted Proposed change moves the Diagnostic to clinical validation or later." Add "not determinable" to FR-11.

### ADV-10 (high). Lifecycle stage is the most consequential value, sits outside the ten fields, is one per Diagnostic and is never measured

**Where:** FR-11, line 105. "assigns each Diagnostic one Lifecycle stage, with Evidence". §4.2, line 92: "On Saturday the fields are the ten agreed with Medical". SM-5, line 196.

**Problem:** Lifecycle stage is an eleventh value, inferred by a model, not agreed with Medical and not in the gold set, so SM-5 says nothing about the value that drives every Alert and the Early research label. One stage per Diagnostic is wrong in the primary journey: an assay approved as a companion diagnostic for treatment selection in advanced disease shows "regulatory approval" with no Early research label when the Director's Intended use is relapse monitoring in early-stage disease, where it may have no validation. The PRD applied this reasoning to Performance values (FR-6) and not to stage. Also, "regulatory status" is declared out (FR-10) while the FDA list and stage six bring it in.

**Smallest fix:** Hold Lifecycle stage per Diagnostic and clinical use (field 6 already exists). State in §4.2 that Lifecycle stage is a derived value outside the ten. Add stage to the gold set labels so SM-5 reports it.

### ADV-11 (high). What counts as "the same Diagnostic" is undefined, and parallel processing breaks FR-3

**Where:** FR-3, line 87. "attaches a Finding to an existing Diagnostic where one matches ... *Test:* a second Finding about a tracked Diagnostic produces no duplicate Record." Glossary, line 52: "from an early biomarker signal to a named assay offered by a Provider." FR-4, line 88: "in parallel".

**Problem:** A Diagnostic ranges from a biomarker signal to a named product, and the PRD gives no key for a match. Most trial records say "ctDNA monitoring" and name no assay, while UJ-1 needs named assays to pilot with a Provider. When a signal becomes a named assay, the PRD does not say whether that is the same Diagnostic advancing (which FR-12's test needs) or a new one. There is no requirement to merge or split Records or to move a Finding attached to the wrong one. The test covers only the sequential easy case: under FR-4, two Source items about one untracked Diagnostic processed at the same moment both find no match and both create a Record.

**Smallest fix:** Add to FR-3: "On Saturday a match is an exact match on normalised assay name and Provider where the Source names an assay; otherwise on modality, biomarker and clinical use, held as an unnamed approach. Creation is an upsert on that key. *Test:* two Source items about one untracked Diagnostic in the same parallel batch produce one Record." Linking an unnamed approach to a named assay is a Reviewer action, later development.

### ADV-12 (high). FR-19 writes a rule from a bare rejection, applies it unconfirmed and withdraws proposals with nobody looking

**Where:** FR-19, line 120. "When a Reviewer rejects or edits a Proposed change, the system writes a Learned rule for that field ... applies it to later and pending Proposed changes. *Test:* after one rejection, a pending Proposed change with the same fault is withdrawn or flagged without further Reviewer action."

**Problem:** (a) FR-16 collects no reason, so the system must guess the fault. A rejection can mean a wrong value, a quote that does not support it, the wrong Diagnostic matched (an FR-3 fault, not a field fault), a duplicate, or a misclick. (b) The rule takes effect with no confirmation. (c) "Withdrawn ... without further Reviewer action" is silent suppression, the mirror of the silent overwrite the PRD exists to prevent: one mistaken rejection can remove every later update to that field for every Diagnostic, and Records go stale with no trace. (d) No requirement lets anyone list, disable or revert a rule, see what it withdrew, or restore it. (e) Rules only tighten; nothing loosens one when a Reviewer later accepts what it would have blocked. (f) An "edit" that fixes a typo also writes a rule. (g) "The same fault" is undefined, so the test cannot be judged. (h) The rule is model-written, so the demo's key beat is not repeatable take to take.

**Smallest fix:** In FR-16, a rejection or edit takes a reason from a short list plus optional text. In FR-19: "The system drafts a Learned rule from the reason; the Reviewer confirms it before it applies. It flags pending Proposed changes and never withdraws them. Each rule lists the Proposed changes it flagged and can be switched off, which clears its flags." Drop "withdrawn" from the test. An honest, repeatable Saturday example: the extractor takes anticipated enrolment as study size; the reason is "planned, not actual"; pending changes with the same fault are flagged.

### ADV-13 (high). Three P1 behaviours and two of the three theme behaviours rest on a preview product, and the PRD has no fallback rule

**Where:** Addendum §3, lines 104 to 106: FR-28, FR-19 and FR-9 are each mapped to "Atlas Agent Memory". SM-4, line 193. §8, line 212: "say which capability powers which behaviour". The fallback ("plain collections") appears only in the brief, line 102.

**Problem:** If Agent Memory misbehaves, the behaviours can survive on plain collections, but the PRD does not say when to switch, and the video's instruction to name the capability then becomes either false (naming Agent Memory for a plain collection) or empty. Resume and the Learned rule are the two theme behaviours in SM-4 and the "working with memory" in SM-2. The mapping table is "taken from the team's plan" and unverified; "taxonomic" memory in particular is the plan's term. I could not check it against MongoDB's documentation from these files, and a MongoDB judge can.

**Smallest fix:** Add to §8: "FR-9, FR-19 and FR-28 pass their tests on plain collections first. Agent Memory replaces them only if it works by a time set in the scoping session. The video names what actually ran." Have architecture verify each row of the addendum §3 table against current Atlas documentation before Saturday.

### ADV-14 (high). No success metric targets what is judged, and the video spends its seconds on what is not

**Where:** SM-2 to SM-4, lines 191 to 193. §8, line 212: "MongoDB as the advantage." §1, line 18: "DxP proactively tracks new cancer diagnostics, holds all the information in one source and makes the relevant diagnostic information easy to retrieve."

**Problem:** Judging is creativity, originality and novelty, equally weighted; the brief addendum found no required-technology rule and no criterion for use of MongoDB. SM-4 ticks the three theme behaviours, which every team at a themed event will also tick. Field-level proposals with a human reviewer and evidence are a familiar pattern. The pitch line describes a database. The PRD's two original ideas are not in any primary metric: an agent that stays silent until a Diagnostic becomes applicable (FR-12, in no SM) and a guardrail that tightens from one correction and reaches back to pending work (FR-19, present only as a checkbox in SM-4). "Each step names the MongoDB capability" turns three minutes into a feature tour.

**Smallest fix:** Add SM-0: "The first twenty seconds of the video and the first line of the description state one novelty claim", and choose it now, for example "an agent that rewrites its own guardrail from a single correction and tells you what it then held back". Move MongoDB naming to on-screen captions so it costs no narration time.

### ADV-15 (high). SM-2, SM-3 and SM-4 together do not fit three minutes, SM-2's steps omit what it claims to validate, and Alerts are P1 but on no metric

**Where:** SM-2, line 191: "Validates FR-1, FR-15 to FR-17, FR-19, FR-26 to FR-28." Brief addendum, line 88: the plan's demo script "needs revising".

**Problem:** SM-2's five steps follow an accepted change. FR-19 needs a rejection and FR-28 needs a second session, and neither is in the steps, so SM-2 can be met without showing either. Showing all three metrics needs: problem, a resume across two sessions, a scan, an accepted change, a rejected change with a rule and its effect on a pending change, the graph, a UJ-1 query with Evidence, a batch run and capability naming at each step. No storyboard exists; the only script is the plan's, built around the dropped galaxy view. The brief's success criteria include "an alert on a tracked diagnostic"; the PRD's metrics dropped it while keeping four Alert requirements in P1.

**Smallest fix:** Put an eight-row demo script with timings in the PRD or its addendum, and make each SM cite its rows. Either add the Alert to SM-2 or move FR-12 to FR-14 out of P1a. Add the reject path and the second session to SM-2's steps.

### ADV-16 (high). The two theme behaviours are the ones fed by synthetic data

**Where:** §8, line 209. "Synthetic Team profiles, session history and Reviewer corrections are labelled as synthetic wherever they appear." SM-2, line 191: "on real data, working with memory".

**Problem:** Memory across sessions is shown from seeded session history, and adapting guardrails from about ten seeded corrections. If the video shows only seeded state, the answer to "is that memory real?" is no, on the two behaviours the event is about. SM-2 says "real data" without saying which parts are real. Learned rules derived from synthetic corrections would act on real Proposed changes, and the PRD does not say whether a rule, or a flag it raises, inherits the synthetic label. A label on screen in the app does not make it legible in a recorded video.

**Smallest fix:** In §8: "The video shows one real write to memory and one real read: a session on camera, then a second session that resumes from it; and one Learned rule produced by an on-camera rejection. Rules derived from synthetic corrections carry the synthetic label and are switched off for the recording." In SM-2, replace "on real data" with "on real Source items; Team profiles and earlier history are synthetic and labelled".

### ADV-17 (high). FR-4 depends on model API capacity that no document mentions

**Where:** FR-4, line 88. "processes a batch of 300 to 500 Source items in parallel". FR-18, line 119. Brief, line 98: "working with coding agents on Claude Ultra and Claude Max plans".

**Problem:** A batch of 300 to 500 Source items through triage, extraction and FR-18's check is on the order of a thousand model calls per run (my estimate), and every prompt change means a re-run. The only Claude access named in the four documents is subscription plans for coding agents. No API key, rate-limit tier or spend is recorded. Parallelism is bounded by the rate limit, not by Modal. If this surfaces at 13:00, FR-4 and the "real workload" in SM-4 go with it.

**Smallest fix:** Add to §8: "Before Saturday, confirm an API key, its rate limits and a spend cap for the product's own model calls, and run 20 Source items through the pipeline as a smoke test (disclosed)." State in FR-4 that the batch is run once for the record and the recorded run is what the video shows.

---

## Medium

### ADV-18 (medium). Human-entered values contradict FR-7

**Where:** FR-7, line 96. "never displays a field value without Evidence." FR-16, line 117: "A Reviewer can accept, edit or reject". FR-29, line 152: "marked as manually sourced". Glossary, line 57: Evidence is "The Source, the supporting quote and the study context".

**Problem:** A Reviewer's edited value has either the original quote, which by definition did not support it, or none. FR-29's manual values and §4.9's partial Records have no quote. Under FR-7 and §8 none may be displayed. FR-16's edit is P1. "Study context" in the Evidence definition also belongs to Performance values, which are out.

**Smallest fix:** Extend the Evidence definition: "or, for a value entered by a person, that person, the date and their stated source." In FR-16, an edit requires the Reviewer to pick a span from the Source item or mark the value as manually sourced.

### ADV-19 (medium). "No data for this indication" needs storage that is deferred, and claims more than DxP knows

**Where:** FR-8, line 97. "shows 'no data for this indication' where nothing is published."

**Problem:** Values are not held per Indication on Saturday (FR-6 is deferred), so the system cannot tell that a value exists but not for this Indication. "Nothing is published" asserts absence in the world from absence in three Sources. The test separates no-data from loading only; it does not separate "none found" from "found but withheld under FR-7" or "extraction failed", which a Director would read very differently.

**Smallest fix:** Reword the state to "none found in the Sources scanned, as of [date]". Add a second state, "value withheld: Evidence missing". Note that per-Indication behaviour is later development.

### ADV-20 (medium). Scans are not idempotent and pending Proposed changes go stale

**Where:** FR-1, line 85. "scans every approved Source type on a schedule". FR-15, line 116: "showing the current value".

**Problem:** Nothing says a Source item already processed is skipped. A second scan re-reads the same item and re-drafts a change the Reviewer already rejected. Two pending Proposed changes on one field are possible; once one is accepted, the other shows a "current value" that is no longer current. With an episodic Reviewer, proposals can sit for weeks.

**Smallest fix:** Add to FR-1: "A Source item is processed once per version. *Test:* a second scan of unchanged Sources drafts no Proposed change." Add to FR-15: "When a field changes, other pending Proposed changes on it are re-based and marked."

### ADV-21 (medium). Several tests pass on a system that does nothing

**Where:** FR-13 test, line 107: "a new Finding that changes none of these produces no Alert." FR-20 test, line 121: "a Team with nothing applicable receives no Digest." FR-16 test, line 117. FR-3 test, line 87.

**Problem:** Each is satisfied by a system that never alerts, never sends, never changes and never creates. FR-20 also cannot be tested as written in a day ("weekly"), "when an event warrants" is undefined, no channel is named for "sends", and it mixes a Reviewer's queue of Proposed changes with a Team's Alerts although the Reviewer is not defined as a Team member.

**Smallest fix:** Give each a positive test alongside the negative one. For Saturday, define the Digest as an in-app list generated on demand, one for the Reviewer and one per Team, and mark sending and the weekly schedule later development.

### ADV-22 (medium). There are no users, so "who accepted", "last visit" and "no input" have nothing to stand on

**Where:** FR-17, line 118: "who accepted each change and when". FR-27, line 140: "since the user's last visit". FR-28, line 146: "restores the Team's context with no input from the user."

**Problem:** No requirement covers identity, sign-in or choosing a Team. FR-27 keys "last visit" to a user and FR-28 to a Team; if it is per Team, a member returning after six weeks sees nothing changed because a colleague visited yesterday. "No input from the user" cannot be met if the user must pick a Team. "Human decision, logged" (§8) logs an unauthenticated name, which a judge from Okta will notice.

**Smallest fix:** One line in §4.7: "On Saturday there is no sign-in. The user picks a named person in a Team from a list; that choice is the only input. Last visit is held per person. Authentication is later development."

### ADV-23 (medium). "Liquid biopsy" is not a synonym of ctDNA

**Where:** FR-9, line 98. "maps terms to standard names and finds a Diagnostic by any of its synonyms ... *Test:* a search for 'liquid biopsy' returns ctDNA Diagnostics."

**Problem:** Liquid biopsy is the broader term; it also covers circulating tumour cells and other analytes. Treating it as a synonym makes the mapping two-way, so a search for ctDNA returns tests that are not ctDNA, and "maps terms to standard names" would rewrite a Source's "liquid biopsy" to "ctDNA" in the modality field, narrowing the claim beyond its quote. That value then fails FR-18's own check, or passes it wrongly.

**Smallest fix:** In FR-9, separate synonyms (equivalent, two-way) from broader terms (one-way, search only, never used to rewrite a value). Add a test: "a search for ctDNA does not return a Diagnostic whose only modality is circulating tumour cells."

### ADV-24 (medium). FR-21 is specified as a structured query and mapped to vector search

**Where:** FR-21, line 129. "turns it into one query across all Records. *Test:* the parsed query is shown and can be corrected." Addendum §3, line 107: "Automated Embedding with vector search".

**Problem:** A correctable parsed query over a handful of categorical fields is a filter and needs no embeddings. If vector search decides which rows appear, the table has no defined cut-off and "the parsed query is shown" does not apply to an embedding. The brief addendum lists "20 held-out questions"; the PRD has no retrieval metric, so nothing measures whether the right Diagnostics come back.

**Smallest fix:** State in FR-21 that plain language is parsed into filters, and that vector search is used only to rank within the filtered rows or for free-text terms the filters cannot express. Add the held-out questions to SM-5 or drop them.

### ADV-25 (medium). The requirements do not need the MongoDB capabilities the video will name

**Where:** FR-26 test, line 139: "can each be reached from it in one step." FR-27, line 140. Addendum §3, lines 108 to 110.

**Problem:** A one-step link needs no graph lookup. FR-27 is defined against a stored last-visit time, which is a query, not a change stream; and a change stream needs a long-lived listener, while the brief addendum notes the front-end host is "Not for long-running agents". The row "A new kind of Diagnostic arriving with new fields" matches no requirement and contradicts FR-5's "fixed format" and the ten-field decision. A MongoDB judge will ask what each capability does that a simpler query would not.

**Smallest fix:** Add one multi-step test to FR-26, for example "from a Diagnostic, reach another Diagnostic in a different Category through a shared linked drug", which fits the pharma Team's interest in competitors' drugs. Reword FR-27 to include "and while the user is looking". Delete the flexible-documents row or write the requirement it claims.

### ADV-26 (medium). The Graph view has no scope, and the batch makes it unreadable

**Where:** FR-26, line 139. "shows Diagnostics, biomarkers, tumour types, trials, drugs and Providers as nodes, with the links between them".

**Problem:** A 300 to 500 item batch yields hundreds of Diagnostics plus their trials, drugs and Providers. Drawn whole, that is a tangle in which SM-2's "the change appears in the Graph view" cannot be seen in a video. With lung only, the tumour-type node links to everything. A custom graph with six node types, selection and change marking is among the costliest P1 items.

**Smallest fix:** In FR-26: "On Saturday the Graph view opens on one Diagnostic and its links to two steps, and expands on selection. Tumour-type nodes are not drawn while there is one tumour type."

### ADV-27 (medium). The deadline has zero slack under the official rules and no agreed cut if they hold

**Where:** §9, line 222. "the team is working to an 18:00 submission deadline. The event's rules say 17:00". §8, line 211.

**Problem:** The brief's working day is talks to about 10:00, six hours of coding and one hour for the video: 10:00 plus seven hours is 17:00. At 18:00 there is one spare hour; at 17:00 there is none, with no break and no upload margin. The PRD plans to the latest of the plausible times that the team controls and says only "confirm at the opening".

**Smallest fix:** Add to §8: "If the opening confirms 17:00, coding stops at 15:30 and P1b is dropped." Set the freeze time in the scoping session for both cases.

### ADV-28 (medium). Judging has two rounds, and every metric is about the video

**Where:** SM-1 to SM-4, lines 190 to 193. Brief addendum, line 127: "two rounds". Brief, line 99: "judging 19:00 to 20:00".

**Problem:** Nothing in the PRD covers a live round or questions from judges: whether the deployed app must still be running after 18:00, whether the held-back set can be replayed again, or who answers what. The brief's mitigation, "Recorded backup of every beat", is not carried into the PRD.

**Smallest fix:** Add SM-1b: "After submission, the deployed app can repeat the SM-2 loop once more from a reset state", and a reset step for the held-back set.

### ADV-29 (medium). FR-18's "low confidence" needs a threshold the PRD does not set

**Where:** FR-18, line 119. "Each extracted field carries a confidence score ... Low-confidence fields are marked for the Reviewer."

**Problem:** The PRD defers the Maturity gate's thresholds openly and then needs one here in P1 without saying so. A model's stated confidence is uncalibrated, and nothing measures it against the gold set. The check is a second model pass per field, which adds to ADV-17.

**Smallest fix:** For Saturday, replace the score with two deterministic checks: the quote is in the Source item (ADV-04) and the value's key token is in the quote. Mark the confidence score later development, or state the threshold and report its hit rate on the gold set.

### ADV-30 (medium). SM-5 has no requirement, no priority and no owner

**Where:** SM-5, line 196. "Extraction accuracy per field on the gold set is measured and reported. Validates FR-5." Glossary, line 76.

**Problem:** No requirement builds the measurement, and it sits in none of P1, P2 or P3. The PRD does not say when 30 to 50 Source items are hand-labelled across nine fields or by whom. Before Saturday it is a disclosed dataset; on Saturday it is an hour or more of one of two people.

**Smallest fix:** Either add "FR-30. Accuracy report, P2" with a labelling date and an owner, or move SM-5 to later development and say so.

### ADV-31 (medium). UJ-1 as written cannot happen on Saturday, and SM-3 cites it

**Where:** UJ-1, lines 42 to 43. "Each Performance value shows its study, population, design and sample count inline ... They narrow by sample type, turnaround and regulatory status ... Today they open each record and copy out sensitivity and specificity by hand." SM-3, line 192: "A UJ-1 query".

**Problem:** Performance values, turnaround and regulatory status are all later development. The journey's stated climax is the sensitivity and specificity table. On Saturday the table is descriptive metadata plus a free-text key result, and nothing in the PRD says what a Director decides from that.

**Smallest fix:** Add a "Saturday version" sentence to UJ-1 naming the columns actually shown, and point SM-3 at it.

### ADV-32 (medium). Provider websites are a fourth Source the brief did not plan, with no test of the gate's first clause

**Where:** §8, line 209. "Provider websites found through web search." FR-2, line 86: "accepts Findings only from approved Source types". Brief, line 77: "the sources are ClinicalTrials.gov, PubMed and the FDA companion diagnostics list".

**Problem:** For the three structured Sources the gate's first clause cannot fail, since FR-1 scans only approved Sources. For web search it is the whole question: something must decide that a result is a Provider's own site and not a news article or an aggregator, and FR-2 has no test for that. A Provider's site is also self-reported, and under ADV-08 it would be the only Source for the later Lifecycle stages. It is a fourth integration in six hours.

**Smallest fix:** Make Provider websites P2 in §6.1. If kept, add to FR-2: "*Test:* a web result that is not on a Provider's own domain produces no Finding", and bar a Provider's site from being the sole Evidence for a Lifecycle stage advance.

### ADV-33 (medium). "On a schedule" cannot be shown in a day, and "scan" may mean reading a file

**Where:** FR-1, line 85. "*Test:* a scan completes and records its Findings with no user session open."

**Problem:** A schedule that fires once during the build proves nothing on camera. If the corpus is pulled beforehand, Saturday's "scan" reads a prepared file, and the test passes on that. The PRD does not separate fetching from a Source from processing a Source item, so the video could show the second and imply the first.

**Smallest fix:** Split FR-1 into "fetch" and "process". For Saturday, require one live fetch from one Source on a manual trigger, and show the schedule as configuration. Say in the video which Source items were fetched live.

---

## Low

### ADV-34 (low). The addendum still says ungated technology never reaches the queue

**Where:** `addendum.md`, line 65: "A technology with no credible validation behind it should never reach the queue". Line 73 lists one "Difference from the PRD", the congress sources. Brief, line 48: "Unverified proposals are held back".

**Problem:** Both contradict FR-2's label-not-hide decision, and the addendum's list of differences omits it. Architecture reads both files.

**Smallest fix:** Add a second line under "Difference from the PRD" in the addendum: the gate labels and does not hold back.

### ADV-35 (low). The brief says no user interviews; the addendum says a discovery session with users

**Where:** Brief, line 31: "No user interviews or cost figures back this up yet." `addendum.md`, line 13: "These come from a discovery session with users."

**Problem:** Both will sit in a public repository. A judge who asks whether the team spoke to users finds two answers.

**Smallest fix:** Correct whichever is wrong, and say in one phrase who "Medical" is.

### ADV-36 (low). SM-1 does not include the disclosure the rules require

**Where:** SM-1, line 190. §8, line 210: "Data prepared beforehand is disclosed, and the demo says what was built that day."

**Problem:** The constraint has no deliverable. Prepared material is substantial: the corpus, the ontology seed, the gold set, the held-out questions, the synthetic data and these planning documents.

**Smallest fix:** Add to SM-1: "and a README section listing what was prepared before the day; the video states what was built on the day."

### ADV-37 (low). The public repository will carry the judging strategy

**Where:** Line 123: "This feature is the wow moment for the judges ... MongoDB's capabilities are presented as the competitive advantage." Brief addendum, line 9: a path on Luis's machine.

**Problem:** SM-1 requires a public repository, and these files are in it.

**Smallest fix:** Decide before Saturday whether `_bmad-output/` is published. If it is, reword line 123 to describe the feature, not the audience.

### ADV-38 (low). The "ten fields" are nine values, several of them composite, and the PRD never lists them

**Where:** §4.2, line 92: "the ten agreed with Medical, listed in the brief." Brief, lines 54 to 63.

**Problem:** Field 10 is "Source quote for each field", which is Evidence, not a field. "Stage or line of therapy" holds two different things, while FR-21 filters on Tumour stage and FR-13 triggers on line of therapy. "Study size and key result" and "Trial ID (NCT) and linked drug" are pairs, so "field-level" is ambiguous. The PRD is the document the two teammates build from and sends them to another file for its schema.

**Smallest fix:** List the Saturday fields in §4.2, splitting each composite.

### ADV-39 (low). The ElevenLabs half of SM-6 hangs on an optional clause with no test

**Where:** SM-6, line 197. FR-14, line 108: "An Alert can carry an audio briefing."

**Problem:** "Can" is not a requirement and has no test, yet a success metric depends on it. Audio work also competes with P1a.

**Smallest fix:** Make the audio briefing its own P2 requirement with a test, or remove the ElevenLabs prize from SM-6.

### ADV-40 (low). The "why it matters" line is an uncited generated sentence

**Where:** FR-14, line 108. "Each Alert states in one line why it matters to that Team".

**Problem:** A model-written reason is a claim with no Evidence in a product whose rule is that provenance is the product. The test checks only that it names the matched profile element.

**Smallest fix:** Build the line from a template: the matched profile element plus the trigger. No free generation.

### ADV-41 (low). SM-3 is met by an empty table

**Where:** SM-3, line 192. "Target: zero uncited values."

**Problem:** "Populated" is undefined and nothing counts the cells. SM-C2 warns against optimising fill and sets no floor.

**Smallest fix:** "The table has at least five Diagnostics and every displayed value passes the check in ADV-04, confirmed by a script."

### ADV-42 (low). The licensing reasoning is applied to congress material only

**Where:** §6.2, line 178. §8, line 209.

**Problem:** PubMed abstracts and Provider web pages are also third-party text, and DxP stores and displays quotes from them. The PRD does not say whether the prepared corpus is committed to the public repository. I am flagging the inconsistency, not giving a legal view.

**Smallest fix:** One line in §8: "The repository holds Source identifiers and short quotes, not full abstracts or pages."

### ADV-43 (low). FR-4 counts failures and does nothing about them

**Where:** FR-4, line 88. "a live count of processed and failed Source items".

**Problem:** There is no retry, no bound on the failure rate and no count of items triaged as not about a diagnostic, though the brief's pipeline has a triage step. The theme asks for agents that "operate reliably"; a counter does not show reliability.

**Smallest fix:** Add "skipped as not about a diagnostic" to the counts, and "a failed Source item can be re-run without creating a duplicate Finding".

---

## Feasibility table for the scoping session

The ranking is my judgement from the text, not a measurement.

**Most likely to eat the day, worst first**

| Requirement | Why |
|---|---|
| FR-3 | Entity matching with no defined key (ADV-11) |
| FR-19 | Mechanism undecided, output not repeatable, needs a planted pending change with the same fault (ADV-12) |
| FR-26, FR-27 | Custom graph, six node types, selection, change marking, no scope (ADV-26) |
| FR-12, FR-13 | Need stage inference, per-Team state and a history that does not exist yet (ADV-03, ADV-06 to ADV-08) |
| FR-4 | Parallel infrastructure and model rate limits (ADV-17) |
| FR-28 | Preview dependency (ADV-13) |
| FR-9, FR-21 | Normalisation with a review queue; plain-language parsing with a correction step |

**Must be real. Faking any of these breaks the event rules or the claim**

- Quotes are verbatim from real Source items (FR-5, FR-7).
- The Learned rule's text is produced by the system from the on-camera rejection, and the effect on the pending Proposed change is caused by that rule (FR-19).
- The resume reads state written in an earlier real session (FR-28).
- The prior value is in the store, not drawn on the screen (FR-17).
- The batch count shown is the count processed (FR-4).

**Can be reduced honestly, if the video and README say so**

| Requirement | Reduced form |
|---|---|
| FR-1 | Manual trigger, one live fetch, schedule shown as configuration; three Sources, no Provider websites |
| FR-2 | Label derived from Lifecycle stage |
| FR-3 | Exact-key match only |
| FR-4 | One recorded run at whatever size completes |
| FR-9 | The prepared synonym list, disclosed; no unmatched-terms queue |
| FR-11 | Dates taken from Source item publication dates in replay |
| FR-12 to FR-14 | One first Alert and one stage advance, templated reason, no audio |
| FR-18 | Deterministic quote checks; no confidence score |
| FR-20 | In-app list on demand; nothing sent |
| FR-21 | Filters first, plain language second |
| FR-26, FR-27 | One Diagnostic's neighbourhood |

## Questions a judge will ask in the first thirty seconds

| Judge | Question | Finding |
|---|---|---|
| Any | What is new here, beyond an extraction pipeline with a human reviewer? | ADV-14 |
| Any | Is that memory real or seeded? | ADV-16 |
| MongoDB | What does Agent Memory do here that a collection would not? Why a graph lookup for one step? Why a change stream? | ADV-13, ADV-25 |
| Cohere | How do you know the quote is in the source? How did you evaluate retrieval? | ADV-04, ADV-24 |
| Vector Institute | One rejection becomes a rule. How do you know the rule is right, and what did it suppress? How accurate is the stage classifier? | ADV-12, ADV-10 |
| Okta | Who is the Reviewer, and what stops anyone accepting a change? | ADV-22 |
| Anyone with oncology knowledge | Why did accepting that change replace the trial? Why is an approved test labelled Early research, or an unvalidated use not labelled? | ADV-02, ADV-09, ADV-10 |
