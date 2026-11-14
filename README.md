# DxP

**Status: Planning only. Product implementation begins at 10:45 ET.**

This README describes what we plan to build. None of the product exists yet. Working setup commands, screenshots, demo links and verified feature claims will be added during the event as they become real.

Built for **Agents in Context Toronto: a MongoDB Hackathon** (Cerebral Valley), Problem Statement 1, "Agents You Can Audit".

- Date: Saturday, 14 November 2026. Hacking runs 10:45 to 17:00 ET.
- Location: The Quay, 100 Queens Quay E 3rd Floor, Toronto, ON M5E 1V3, Canada
- Event page: https://cerebralvalley.ai/e/mongodb-toronto-hackathon
- Team: Luis and Vlad

## The problem

Diagnostics teams track public clinical evidence by hand. A new or updated trial can matter to a research area, but finding it, connecting it to what the team already knows, and deciding what to do next takes time. An AI agent could do that work, but only if a team can trust it: who acted, under what authority, what it was allowed to do, what it was stopped from doing, and why.

DxP is a proposed research agent for tracking diagnostic evidence. It works under identity, policy and audit records stored in MongoDB Atlas. It supports research review. It is not a clinical decision tool and gives no medical advice.

## Intended users

- **Diagnostics researchers and pharma evidence teams** who follow trials and assays in a research area and decide what new evidence means for their work.
- **The people who must answer for the agent's work later:** team leads and auditors who need to replay what happened and who authorised it.

In the demo, these users are represented by Sam, a reviewer on "Team Liquid Biopsy Dx". Sam reviews what the agent proposes and approves or rejects it.

Everything in this README up to "Prepared before the event" describes planned capabilities, not verified functionality. During the event, verified features will be listed in their own section, each with the evidence that it works.

## Proposed workflow

The agent `dxp-curator` works for one research scope, "Plasma ctDNA genotyping assays in NSCLC", under a scoped grant.

1. **Discover.** A run searches ClinicalTrials.gov for trials in the scope updated since the last scan.
2. **Relate.** Atlas Vector Search finds related evidence the team already holds. Each link gets a relationship label backed by quotes checked against the source. A similarity score is shown, but it never counts as evidence.
3. **Remember.** The agent retrieves the team's reviewer corrections and shows what each one changed in its draft. A memory belongs to the team, records who made it, can be corrected or revoked, and never changes permissions.
4. **Gate.** Versioned policies are checked before every action. A blocked action changes nothing and is still recorded.
5. **Propose.** The agent files one pending research report: the discovery, its quotes, related evidence, uncertainties, the evidence gap, and one recommended follow-up task. Nothing becomes accepted knowledge yet.
6. **Notify.** One Slack alert per report links back to the report in DxP. Slack only notifies; approval and rejection happen only in DxP.
7. **Decide.** Sam approves or rejects in DxP. Approval moves the report's update into accepted knowledge and authorises one follow-up task. That task gets its own narrow grant and passes its own policy gate. A rejection or correction becomes a memory for the next discovery.
8. **Audit and stop.** Every step can be replayed: what the agent found, which memory changed its wording, what was blocked, and who authorised what. A person can stop any run.

Sam can also request two optional extras for a report: a ten-second ElevenLabs briefing and a HeyGen avatar video. Both use only the report's own text script, and both are checked against Sam's grant before either service is called.

## Planned architecture

| Part | Plan |
|---|---|
| Web app | Next.js 16 on Vercel: report page, run console, audit view |
| API and agent | FastAPI and LangGraph on Modal, with Claude (Haiku and Sonnet) |
| Data, identity, policy, audit | MongoDB Atlas Sandbox: sources with immutable versions, reports, memories, grants, policies, decisions, actions, tasks |
| Related evidence | Atlas Vector Search, with a text-search fallback labelled as such |
| External systems | ClinicalTrials.gov API (read), Slack incoming webhook (notify only), ElevenLabs and HeyGen (on demand) |

Key rules from the architecture:

- **Two identities per run:** who started it, and the agent that executes it.
- **Grants are resolved on the server.** A name sent by a client never grants permission.
- **Five gate checks before every action:** the grant is active, the target is in scope, the destination and action are allowed, the required evidence is present, and the action was admitted while the run is still authorised. Every check result is recorded as a Decision.
- **Source versions are pinned.** Quotes, retrieval results, proposals and audit records keep the exact source version they used, so a newer version of a trial never changes evidence that was already reviewed.
- **Notification outcomes are recorded honestly.** The action ID is saved before sending. An uncertain result is marked `unknown`, never retried blindly, and a reviewer resolves it in DxP.
- **Approval survives crashes.** The approval is saved before the report is accepted. A crash between acceptance and task authorisation is completed on restart without another click, with Sam's authority checked again.

The full design is in `_bmad-output/planning-artifacts/`; its file list is under "Planning documents" below.

## Hackathon scope

**Core (the demo depends on it):**
- discovery;
- an evidence relationship with quotes;
- a memory changing the report;
- a policy block;
- a Slack alert that opens the report;
- the human decision;
- the audit trail;
- stop.

**Supporting (cut in this order if time runs short):**
1. the HeyGen avatar;
2. the ElevenLabs briefing;
3. the screen for correcting and revoking memories;
4. a second discovery item.

**Stretch:** running the follow-up task. It stays switched off (`task_run`) until its integration checks pass. If it does not run, the demo says "Follow-up task authorised; not run" and claims no follow-up results.

**Not built:** dashboards as the main feature, medical advice, broad search and category screens.

## Build schedule (forecast)

| Time (ET) | Milestone |
|---|---|
| 10:45 | Hacking starts. Confirm the demo trial live on ClinicalTrials.gov; scaffold, contracts and deploys begin |
| 11:45 | API contracts frozen |
| 12:30 | Proof step for the two merge desks |
| 13:00 | Keep both merge desks, or switch to one desk with the cut line applied |
| 14:05 | Last core merge |
| 14:30 | Target for the full discovery-to-review loop to pass on the sandbox (base forecast: about 14:35, so the follow-up task is expected to stay off) |
| 14:45 to 15:00 | Approval, accepting the evidence and authorising the task, checked end to end |
| 15:00 to 16:10 | Rehearsal, including checking one report against its source |
| 16:30 | Code freeze |
| 16:30 to 16:55 | Record the 60-second video and submit |
| 17:15 | Live 3-minute demo |

This is a forecast, not a measured result. Details, risks and the fallback path are in `_bmad-output/planning-artifacts/build-schedule.md`.

## Planning documents

| Document | Path |
|---|---|
| Product brief | `_bmad-output/planning-artifacts/briefs/` |
| PRD | `_bmad-output/planning-artifacts/prds/` |
| Architecture spine | `_bmad-output/planning-artifacts/architecture/` |
| UX (behaviour and visual design, text only) | `_bmad-output/planning-artifacts/ux-designs/` |
| Epics and stories | `_bmad-output/planning-artifacts/epics.md` |
| Development plan (PR by PR) | `_bmad-output/planning-artifacts/development-plan.md` |
| Build schedule | `_bmad-output/planning-artifacts/build-schedule.md` |
| Approved change decisions | `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md` |
| Sprint tracker | `_bmad-output/implementation-artifacts/sprint-status.yaml` |

## Prepared before the event and built on 14 November

The event rules allow only work built during the event to be highlighted. This table lists what was prepared beforehand so judges can see it. Listing it here does not mean it is used.

| Prepared before the event | Built on 14 November |
|---|---|
| Planning documents in `_bmad-output/`: product brief, PRD, architecture, UX specifications (text only), epics and stories, build schedule and development plan | All of `backend/` (to be filled in) |
| Reference skills in `.claude/skills/dxp-*`: documentation for agents about the APIs, limits and gotchas of the tools we use. No code is copied from them | All of `web/` (to be filled in) |
| The BMad method files in `_bmad/` and the `bmad-*` skills in `.claude/skills/` | |
| `data/` and `scripts/data/`: open data downloaded and fetch scripts written before the event. They are not used on Saturday unless an organiser clears them in writing. The build fetches its own data during the event | |
| Logo images in `_bmad-output/planning-artifacts/ux-designs/`. Not used unless an organiser clears them; the interface uses a text wordmark, "DxP" | |
| The Slack incoming webhook for `#all-mango-db-hackathon`, created and tested before the event. `SLACK_WEBHOOK_URL` lives only in `.env` and the Modal secret and is never committed. Any script used for that test is not reused; the notifier is written during the event | |
| The ElevenLabs and HeyGen accounts, if created before the event. `ELEVENLABS_API_KEY` and `HEYGEN_API_KEY` live only in `.env` and the Modal secret and are never committed. Every briefing and avatar video is generated during the event from a report's own fields; no clip is made beforehand | |
| The BMad sprint-planning status script (`.claude/skills/bmad-sprint-planning/scripts/sprint_plan.py`), modified before the event so it never recommends deferred stories | |

## Open questions for the organisers

To confirm on Saturday between 9:00 and 10:45:

- The submission deadline (the guide says 17:00), and whether any coding may start before 10:45.
- How to present prepared material, and whether the prepared data in `data/` and the logo images may be used.
- Whether one Slack alert per report in `#all-mango-db-hackathon` is acceptable for that channel.

## Open items

Unverified dependencies, each with a fallback (details in `_bmad-output/planning-artifacts/build-schedule.md`):

| # | Dependency | Owner, due | Fallback |
|---|---|---|---|
| OD1 | The Atlas Sandbox supports Vector Search and Automated Embedding, or a Voyage AI key is cleared | Luis, when sandbox access arrives; decided by 11:45 | Text search, labelled "related by text search", never "Vector Search" |
| OD2 | The live ClinicalTrials.gov API still shows the expected demo trial (NCT04712877) as updated since the scan cursor, recruiting, with no results | Luis, 10:45 | Any in-scope trial updated since the cursor; the same policies apply |
| OD3 | ElevenLabs key and quota | Luis, before 10:45 | The briefing is hidden |
| OD4 | Organiser clearance: prepared data, logo, Slack channel volume | Luis, 9:00 to 10:45 | Live fetches, the text wordmark, a team channel if needed |
| OD6 | `mongodump` and `mongorestore` work against the sandbox, for the reset before each take | Luis, by 12:20 | Reset by rerunning the setup, which takes longer |
| OD7 | HeyGen needs a paid plan or funded API wallet; render time can range from minutes to many hours | Luis and Vlad, one timed render at 10:45, decided by 12:00 | The report shows "Avatar unavailable" and the loop is unaffected; the avatar is the first thing cut |

Also: set `DXP_BASE_URL` to the production URL and confirm the Slack alert's link resolves (Luis, during the deploy).

## Ground rules

- This repo is public. Never commit API keys, tokens, connection strings or credentials of any kind.
- Secrets live in `.env` (gitignored) or the deployment platform's secret store, never in the repo.
- MongoDB connection strings stay out of committed code. Use environment variables.

## Data credits

Data: ClinicalTrials.gov (U.S. National Library of Medicine), PubMed (courtesy of the U.S. National Library of Medicine), U.S. Food and Drug Administration (fda.gov and open.fda.gov), HGNC, OncoTree (CC BY 4.0), NCI Thesaurus (CC BY 4.0), MeSH (U.S. National Library of Medicine). DxP is not endorsed by these organisations. Abstract copyright remains with publishers or authors. Details per source are in `data/README.md`.
