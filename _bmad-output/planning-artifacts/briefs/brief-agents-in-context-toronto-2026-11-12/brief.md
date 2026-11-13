---
title: "Product Brief: DxProvida (DxP)"
status: final
created: 2026-11-12
updated: 2026-11-12
---

# Product Brief: DxProvida (DxP)

Draft built from `plan.md` (12 Nov), the filters and extraction approach Luis supplied, and the event's page and official rules. Deeper detail, and the location of `plan.md`, is in `addendum.md` in this folder.

## Executive Summary

DxProvida (DxP) is a platform with agents that proactively searches for new lung cancer diagnostic approaches, such as ctDNA, MRD, companion diagnostics and AI pathology, and lets each team know about the ones relevant to them. It brings what it finds into one source, as checked and structured records in MongoDB Atlas, so the relevant diagnostic information is easy to retrieve.

DxP tracks each diagnostic approach over time as it moves through its cycle, from discovery to adoption. Once an approach is being tracked, a team is alerted only when it becomes applicable to them.

**Pitch:** DxP proactively tracks new cancer diagnostics, holds all the information in one source and makes the relevant diagnostic information easy to retrieve.

A team of two will build it in one day at Agents in Context Toronto, a MongoDB hackathon, on Saturday 14 November 2026. The event asks for agents that hold context across sessions, adapt their own guardrails and operate reliably under real workloads.

## The Problem

Two kinds of team need to know which lung cancer diagnostics are emerging and maturing:

- **Centres of excellence**, which track new diagnostic tools as they appear and mature.
- **Pharmaceutical therapy-area teams**, which track diagnostics tied to their own drugs and to competitors' drugs.

Today the research is done by hand, by an agency or by the teams themselves. The information is spread across trial registries, publications and regulatory lists, so there is no single place to look. The work is slow, costly and not personalised: the plan's demo script puts the wait at days or weeks.

No user interviews or cost figures back this up yet. The problem statement is the team's own account.

## The Solution

### What a team gets

- **Proactive search.** DxP searches its sources and the web on a schedule, without being asked, and lets a team know when a new diagnostic approach is relevant to them, with an optional audio briefing.
- **One source.** Every finding becomes a structured record with the same fields, each field backed by a quote from the source.
- **Easy retrieval.** A team asks a question or applies a filter and gets the relevant findings. Search understands synonyms, so "liquid biopsy" finds ctDNA. A galaxy view maps the findings by meaning.
- **Longitudinal tracking.** DxP follows each diagnostic approach through the nine stages of its cycle: discovery, assay development, analytical validation, clinical validation, clinical utility, regulatory approval, guideline inclusion, reimbursement and adoption. The addendum defines each stage. A team is not alerted at every update, only when the approach becomes applicable to them. An approach is applicable when it is not already in the system and it is at the assay development or analytical validation stage.
- **Memory across sessions.** DxP remembers what each team asked, opened and dismissed, and resumes from there.
- **Evidence and review.** Every claim opens an evidence card with the source quote, a confidence score and the result of the automated check. Low-confidence items go to a reviewer, and a reviewer's correction makes the check stricter for that field from then on.

### Filters

- **Tumour type and modality.** Each tumour type, starting with lung, is matched against a strict set of diagnostic modalities.
- **Stage and clinical phase.** Each finding is placed by tumour stage or clinical therapy phase, with a focus on early stages.
- **Credibility.** Inputs are restricted to credible sources and centres of excellence with sufficient trial data. Unverified proposals are held back until they meet the validation standard. Required for Saturday.

### Extraction fields

Agreed with Medical.

1. Diagnostic method or modality
2. Biomarker or gene
3. Tumour type
4. Stage or line of therapy
5. Sample type (blood, tissue, urine)
6. Clinical use (screening, treatment selection, monitoring or MRD)
7. Study size and key result
8. Sponsor or company
9. Trial ID (NCT) and linked drug
10. Source quote for each field

### Pipeline

1. **Ingest.** Scheduled pulls, with more frequent checks around congress release dates and embargoes.
2. **Triage.** A fast model flags the records that are about diagnostics.
3. **Extraction.** A stronger model fills the fields in a fixed structured format, with supporting quotes.
4. **Normalisation.** Terms are mapped to standards: official gene names, OncoTree and an internal assay master list. Unmatched terms go to review.
5. **Deduplication.** The same work is linked across congresses and publications.
6. **Linking.** Records are connected to trials and approvals through NCT IDs and drug names.
7. **Human review.** Low-confidence items go to reviewers, and their corrections feed back in as examples.

Accuracy is tracked per field against a hand-labelled gold set. A field is automated only once it passes an agreed threshold.

For Saturday, `plan.md` narrows this: the sources are ClinicalTrials.gov, PubMed and the FDA companion diagnostics list, with no congress abstracts for licensing reasons, and the gold set is 30 to 50 records, not the 200 of the full approach. That is enough for the hackathon. If the team wins, it will take congress sources further and approach legal on licensing.

### Agents and stack

Agents carry out the proactive search and the pipeline. How many agents there are and how the work divides between them is an architecture decision; the four-agent split in `plan.md` is a starting point, not a commitment. Models are Claude, with Tavily for web search. Data, search and memory live in MongoDB Atlas, and embeddings come from Atlas Automated Embedding.

## What Makes This Different

- **One source with evidence.** Each structured field carries its source quote, so a team can check any claim without leaving DxP.
- **Tracking over time.** DxP follows a diagnostic through its cycle and alerts on applicability, whereas a periodic report restates everything.
- **What the team builds itself:** the diagnostics ontology and synonym list, and the rules learned from reviewer corrections. The embedding models are stock, through Automated Embedding, so the team will claim "tuned on this data set" only if it has measured a before-and-after on held-out questions.
- **Against Capsule:** Capsule is congress-led competitive intelligence for life sciences. DxP is a checked, longitudinal system of record for oncology diagnostics, with per-field evidence, applicability alerts and guardrails that tighten from reviewer corrections.

## Who This Serves

- **Primary:** an analyst or lead in a centre of excellence or a pharma therapy-area team, who today waits on an agency report or assembles one by hand.
- **Secondary:** the reviewer who corrects extractions, and Medical, who agreed the extraction fields.
- **On Saturday:** the judges, drawn from MongoDB, Cohere, Vector Institute, Microsoft, Okta, Wealthsimple and others. They score creativity, originality and novelty equally, with technical execution as the tie-break.

## Constraints for the Day

- **Team:** two people, working with coding agents on Claude Ultra and Claude Max plans. Work is divided through epics and stories.
- **Clock:** the event runs 9:00 to 21:00. The official rules put the submission deadline at 17:00 ET; the event page's metadata says 21:00; no agenda is published. The team's working assumption is talks until about 10:00, one hour for the demo video, judging 19:00 to 20:00 and winners 20:00 to 21:00. The team is planning on six hours of coding.
- **Rules:** the project must be substantially developed on the day. Pre-existing code and datasets must be disclosed, and the demo must identify what was built that day. Data preparation before Saturday falls under that disclosure.
- **Submission:** a project description, a public repository and a demo video. The team is aiming for three minutes.
- **Platform:** the Atlas tier supports Automated Embedding and MongoDB will provide credits. Atlas Agent Memory is in public preview; the fallback is plain collections holding the same memory types.

## Scope

**In, as the ambition for the day:** lung cancer only; the platform with agents running end to end, from proactive search through the pipeline to one searchable source; the three filters, including the credibility gate; longitudinal tracking with applicability alerts; memory across sessions; evidence cards and reviewer corrections; the galaxy view; a parallel batch of 300 to 500 records; an audio briefing on alerts; a three-minute demo video.

**The piece that must work:** the platform with agents.

**Out, and the cut line:** to be settled during the PRD and planning, once the work is broken into epics and features.

## Success Criteria

- Submitted before the deadline with all three required items.
- The demo shows the platform with agents working on real data: a proactive find, retrieval from the one source and an alert on a tracked diagnostic.
- The demo shows each behaviour the event asks for: memory across sessions, a check that tightens after a correction and a batch of records processed in parallel.
- Every claim shown in the demo links to an evidence card.
- Per-field extraction accuracy on the gold set is measured and reported.
- A top-three placing, or the Best Project Built with ElevenLabs prize.

## Vision

The same platform extends to other tumour types and therapy areas by adding ontology and sources.

## Open Questions

1. When is the real submission deadline, 17:00 or 21:00? To confirm at the opening.
2. For the PRD: how do "relevant to a team" (proactive search) and "applicable" (the alert rule) fit together, and how does "not already in the system" square with tracking an approach from discovery onward?
3. For architecture: a reviewer's correction is described as making the check stricter, as feeding back in as an example, and as a learned rule. Is that one mechanism or three?
