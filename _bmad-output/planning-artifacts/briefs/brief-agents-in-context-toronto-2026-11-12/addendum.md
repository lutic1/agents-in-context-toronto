---
title: "Addendum: DxProvida (DxP)"
created: 2026-11-12
updated: 2026-11-12
---

# Addendum: DxProvida (DxP)

Detail that belongs in the PRD, architecture or epics, kept here so the brief stays short. The full original is `/Users/luis/Downloads/plan.md` (team planning draft, 12 Nov 2026), which is on Luis's machine only.

Much of what follows is carried over from that plan. Where the team has decided otherwise since, the later decision stands: the team is two people, not four; the agent roster is not fixed; models are Claude with Tavily for web search; the build window is six hours; and what is out of scope is settled in the PRD and planning.

## Context layers (for architecture)

| Layer | Holds | Lives in | Shown as |
|---|---|---|---|
| Knowledge | Findings and the graph of assay, biomarker, tumour type, trial, drug, company | Atlas, Automated Embedding, graph lookup | Stars and links in the galaxy |
| Taxonomy | Diagnostics ontology and synonym list | Atlas Agent Memory | "Liquid biopsy" lights up ctDNA |
| Episodes | What each team asked, opened, dismissed | Atlas Agent Memory | Session resume |
| Procedure | Rules learned from reviewer corrections | Atlas Agent Memory | Checker tightens a threshold live |
| Agents | Watcher, extractor, checker, writer | LangGraph, traced in LangSmith | Pipeline strip and trace |

The four-agent split (watcher, extractor, checker, writer) used throughout this addendum is the plan's starting point. Architecture decides the roster.

## Stack choices (for architecture)

Only the Claude and Tavily rows are decisions the team made on 12 Nov. The other rows are carried over from the plan and open to architecture.

| Need | Choice | Note |
|---|---|---|
| Data, search, alerts | MongoDB Atlas | Automated Embedding, vector and synonym search, graph lookup, change streams |
| Agent memory | Atlas Agent Memory | Public preview; fall back to plain collections |
| Orchestration | LangGraph with LangSmith | LangSmith credits are among the prizes |
| Models | Claude | Decided 12 Nov. Fast model for triage, stronger for extraction |
| Web search | Tavily | Decided 12 Nov. Used for the proactive search |
| Agent and batch hosting | Modal | Parallel batch ingest is the real-workload proof |
| Front end hosting | Vercel | Not for long-running agents |
| Voice | ElevenLabs | Separate prize for best ElevenLabs project |
| Demo video | HeyGen for intro and close only | Product footage is real screen recording |

## Data (for PRD and epics)

- **ClinicalTrials.gov:** lung cancer trials mentioning ctDNA, liquid biopsy, MRD, companion diagnostics, biomarkers, digital pathology, radiomics, methylation. Main corpus; pulling it is the agreed next step. Target across sources: 300 to 500 lung cancer records.
- **PubMed:** lung diagnostic abstracts from the last two years.
- **FDA companion diagnostics list:** assay, drug and company pairs, as real graph edges.
- **Ontology seed:** official gene names, lung tumour codes, about 50 assay synonyms.
- **Gold set:** 30 to 50 hand-labelled records and 20 held-out questions.
- **Synthetic, labelled as such:** three team profiles, their session history, about ten reviewer corrections.

All of this prepared before Saturday must be disclosed under the event rules.

## The diagnostic cycle (for PRD and data model)

The nine stages DxP tracks each diagnostic approach through, as supplied by Luis:

1. **Discovery.** Researchers find a biomarker or signal linked to a cancer, a treatment response or relapse. This mostly appears in papers and early congress abstracts.
2. **Assay development.** The finding is turned into a test that works reliably on real samples (tissue, blood or urine).
3. **Analytical validation.** This proves the test measures what it claims to, accurately and consistently across labs, samples and runs.
4. **Clinical validation.** This proves the result matches the clinical question, such as who has the cancer, who will respond or who will relapse. It is usually done in retrospective studies first, then prospective ones.
5. **Clinical utility.** This shows that using the test changes decisions and improves outcomes for patients. It is often the hardest stage and where many tests stall.
6. **Regulatory approval.** FDA clearance or approval, Health Canada licensing or a CE mark. Companion diagnostics are often approved alongside a specific drug. Some tests skip this stage and launch as lab-developed tests.
7. **Guideline inclusion.** The test is recommended by bodies such as NCCN, ESMO or ASCO, or by pathology groups such as CAP and IASLC. This is the biggest signal for clinical practice.
8. **Reimbursement.** Payers agree to cover the test. In Canada that often means provincial funding decisions, which can lag years behind approval.
9. **Adoption.** Labs implement the test, turnaround times become practical and clinicians order it routinely. At that point it is standard of care.

Applicability rule (decided 12 Nov): a diagnostic triggers an alert when it is not already in the system and it is at the assay development or analytical validation stage.

## Extraction approach: full version against Saturday (for PRD)

The brief carries the ten extraction fields and the seven-step pipeline. Two points differ between the full approach Luis supplied and `plan.md`. The team's decision (12 Nov): the `plan.md` values are enough for the hackathon, and if the team wins it will take congress sources further and approach legal on licensing.

| Point | Full approach | `plan.md` for Saturday |
|---|---|---|
| Congress sources | Ingest checks more often around congress release dates and embargoes; deduplication links work across congresses and publications | No congress abstracts, for licensing reasons |
| Gold set | About 200 hand-labelled abstracts | 30 to 50 hand-labelled records and 20 held-out questions |

## Candidate out-of-scope list from the plan (to be discussed in PRD and planning)

- 3D body model and the 2D radar
- Custom fine-tuned embeddings
- Atlas's agent runtime (memory layer only)
- Live talking avatar

Already settled for Saturday: lung cancer only, and no congress abstracts.

## Demo script from the plan (three minutes)

Written before the 12 Nov reframing. It has no proactive-search beat, and "stage grid" is not defined, so it needs revising against the brief's success criteria.

| Time | Beat |
|---|---|
| 0:00 | The problem: an agency does this by hand and teams wait days or weeks |
| 0:20 | The galaxy: every lung diagnostic finding, grouped by meaning |
| 0:45 | Ask a patient scenario; open one evidence card and show the source quote |
| 1:15 | Session resume as the lung team |
| 1:40 | Batch ingest through the agents; a new diagnostic type lands with no schema change |
| 2:10 | A reviewer rejects an extraction; the checker tightens its threshold and shows the rule |
| 2:30 | The alert arrives with the audio briefing |
| 2:45 | Close on the stage grid and measured numbers |

## Roles in the plan (written for four people; team is now two)

The two teammates will divide the work through epics and stories. These four groupings are kept as a list of what needs an owner.

| Role | Owns |
|---|---|
| Data and extraction | Source pulls, extraction prompts, gold set, accuracy number |
| MongoDB | Collections, indexes, Automated Embedding, graph, change streams, Agent Memory |
| Agents | LangGraph flow, checker and learned rules, LangSmith traces, Modal deployment |
| Front end and demo | Galaxy, evidence card, session resume view, alert, voice, video |

## Risks and mitigations from the plan

| Risk | Mitigation |
|---|---|
| Agent Memory preview misbehaves | Plain collections holding the same memory types |
| Live demo fails | Recorded backup of every beat |
| Extraction errors on stage | Show the checker and evidence cards catching one |
| Scope creep | A cut list and a freeze on new work late in the day. The plan set the freeze at 16:00 on a longer timeline, so the time needs resetting for six hours of coding |
| "How is this different from Capsule?" | Capsule is congress-led competitive intelligence for life sciences; DxP is a checked, longitudinal system of record for oncology diagnostics, with per-field evidence, applicability alerts and guardrails that tighten from reviewer corrections |

## Event facts (researched 12 Nov 2026)

Source for all items unless noted: the event page and the official rules embedded in its registration waiver, https://cerebralvalley.ai/e/mongodb-toronto-hackathon

- **Theme wording:** agents that "hold context across sessions, adapt their own guardrails, and operate reliably under real workloads", built with "MongoDB Atlas, Vector Search, and Agentic Memory tooling that push past demos into something durable". No tracks published.
- **Judging:** creativity, originality, novelty, equally weighted; technical execution as tie-break; two rounds. Sixteen judges listed, from MongoDB, Pelmorex, Okta, Acerta, Microsoft, Wealthsimple, Vector Institute, Speak AI, Cohere, Zafin, Omni, Stan and Quantiphi.
- **Rules:** solo or teams of up to four; one project per team; must be substantially developed on the day; pre-existing code, open-source components, datasets and tools disclosed; demo identifies what was built on the day.
- **Submission:** description, public repo, short demo video. No length limit found.
- **Deadline conflict:** the event runs 9:00 to 21:00. Rules say 17:00 ET; page metadata says 21:00 EST. No agenda published.
- **Prizes:** first USD 7,000 plus USD 3,000 LangSmith credits; second 5,000 plus 2,000; third 3,000 plus 1,000; each with three months of ElevenLabs Pro. Best Project Built with ElevenLabs: three months of Scale tier. The events listing says "CAD $21,000 in cash", which conflicts with the rules' USD 15,000.
- **Required technology:** no hard rule found for Toronto. A January 2026 San Francisco guide said finalists "must build on MongoDB Atlas".
- **Past first-place winners:** ForgetMeNot (SF, Oct 2025; real-time context for dementia patients), Plan Pass AI (London, May 2026; agents check UK planning rules), Amelia (SF, Aug 2026; conversation memory for deaf users, with ElevenLabs voice). Each paired one concrete human or vertical problem with memory as the core mechanism.
