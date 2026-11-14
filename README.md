# DxP

**DxP is a proactive diagnostic-evidence research agent: it finds newly updated clinical trials in a team's research scope, relates them to what the team already knows, checks every claim and action against explicit policies, and files one pending report that a human approves or rejects.**

Built for **Agents in Context Toronto: a MongoDB Hackathon** (Cerebral Valley), Problem Statement 1, "Agents You Can Audit".

**Status: the build is in progress on Saturday 14 November 2026 (hacking runs 10:45 to 17:00 ET).** Everything below describes planned behaviour until the "Verified on the sandbox" section says otherwise. Facts we do not know yet are shown as `[[PENDING: ...]]` markers, each with where the answer will come from. No marker is a claim.

- Event page: https://cerebralvalley.ai/e/mongodb-toronto-hackathon
- Location: The Quay, 100 Queens Quay E 3rd Floor, Toronto, ON M5E 1V3, Canada
- Production URL: [[PENDING: production URL (A04, docs/deploy.md)]]
- Public repository: [[PENDING: public repository URL (R1)]]
- 60-second video: [[PENDING: video link (R1)]]
- Team: [[PENDING: team members as submitted (R1)]]

DxP supports research review. It is not a clinical decision tool and gives no medical advice.

## What it does

A diagnostics team follows public evidence in one research area. Finding a newly updated trial, connecting it to what the team already holds, and deciding what to do next is slow manual work. An agent can do that work only if the team can answer: who acted, under what authority, what was it allowed to do, what was it stopped from doing, and why.

DxP's agent, `dxp-curator`, works for one research scope under a scoped grant. The demo scope is **"Plasma ctDNA genotyping assays in NSCLC"**, owned by a synthetic team, "Team Liquid Biopsy Dx". The data layer is MongoDB Atlas: identity, grants, policies, decisions and audit are all documents there.

### The governed discovery loop

1. **Discover.** A run queries ClinicalTrials.gov for trials in the scope that were updated since the scope's last scan. The scan only looks at what changed since the last scan, so the work does not repeat.
2. **Relate.** The agent finds related evidence the team already holds, using [[PENDING: Atlas Vector Search or text search, whichever the sandbox supports (OD1)]]. Each relationship (supports, contradicts, extends, new question) needs a quote checked against the source from both sides, or the item is shown as "related (no relationship established)". A similarity score is displayed and never counted as evidence.
3. **Remember.** The agent retrieves the team's reviewer corrections ("memories") and shows what each one changed in its draft. A memory belongs to the team, names its author, can be corrected or revoked, and never changes permissions.
4. **Gate.** Versioned policies are checked before every action, and every check is recorded as a Decision. A blocked action changes nothing and is still recorded. The checks cover: the grant is active, the target is in the team's scope, the destination and action match the grant, the required evidence is present (including claim checks), and the run is still authorised.
5. **Propose.** The agent files one pending report: the finding, its quotes, related evidence, uncertainties, the evidence gap, and one recommended follow-up task. Nothing becomes accepted knowledge yet.
6. **Notify.** One Slack alert per report links back to the report in DxP. Slack only notifies; approving and rejecting happen only in DxP.
7. **Decide.** A reviewer approves or rejects in DxP. Approval moves the report's own update into accepted knowledge and authorises one follow-up task under its own narrow grant. Whatever that task later finds stays pending until a reviewer decides on it ("approved" is not "accepted" for the task). A rejection or a correction becomes a memory for the next discovery.
8. **Audit and stop.** Every step can be replayed: what the agent found, which memory changed its wording, what was blocked, and who authorised the follow-up. A person can stop a run at any moment.
   - **The rollback story (planned behaviour).** Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. The agent cannot change accepted knowledge without a human approval.
   - Pending reports can be rejected. Memories can be revoked. History and source versions are never overwritten.
   - Planned as a supporting extra: an approval can be reverted with a note. The update leaves accepted knowledge, nothing is deleted, and a follow-up task that has not started is cancelled. [[PENDING: whether revert passed its check (S4)]]
   - None of this undoes effects outside DxP. A Slack alert that was sent stays sent, and the audit records it.
   - The run console and audit view are planned to update live from an Atlas change stream, and to say "Refreshing every 2 s" when they poll instead. [[PENDING: whether change streams are used or the screens poll (S5, OD5)]]

### The longitudinal value

The scope's scan cursor and the team's memories accumulate over time. A scan reads only what changed since the last one, and a correction a reviewer made earlier in the day shapes the next report. The larger idea is team-specific, longitudinal intelligence on the diagnostics a team follows. The demo shows one turn of that loop.

### The planned demo

One discovery run on the scope finds [[PENDING: the demo anchor trial, verified against the live API at 10:45 (OD2)]]. The report states what the record says, in the record's own words, and its evidence gap. A reviewer memory from earlier in the day changes the report's wording. One proposed action is blocked by a policy check before anything is filed. A Slack alert opens the report, a human approves, and the audit view answers: "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"

When the demo or the report mentions an assay name that appears in a trial record, we say it is "named in the record". A name in a record is not evidence that the trial used or studied that product, and nothing in DxP states or implies how any assay performs.

Two optional extras, both on demand and neither on the critical path: a ten-second ElevenLabs briefing and a HeyGen avatar video, each made from the report's own text script. The script is always shown as text. Running the approved follow-up task is a stretch goal behind a feature flag; if it does not run, DxP says "Follow-up task authorised; not run" and claims no follow-up results.

## Verified on the sandbox

Each row is filled in with its evidence when it passes, and stays a marker until then.

| Behaviour | Status |
|---|---|
| Discovery, relationship with quotes, memory effect, policy block, pending report | [[PENDING: pass or fail and evidence (I1)]] |
| Slack alert that opens the report | [[PENDING: pass or fail (I1)]] |
| Approval, promotion and task authorisation, audit answer | [[PENDING: pass or fail (I3)]] |
| Stop | [[PENDING: pass or fail (A16 pass 1)]] |
| Ten-second briefing | [[PENDING: passed or not (B06 check)]] |
| Avatar video | [[PENDING: passed or not (B08 check, OD7)]] |
| Revert an approval | [[PENDING: passed or not (S4)]] |
| Live updates from a change stream | [[PENDING: passed or not (S5)]] |
| Follow-up task run | [[PENDING: ran or not (I3b)]] |

## MongoDB capabilities

Only capabilities proven on the Atlas Sandbox are listed as used. Until a row is proven, its status is a marker.

| Capability | What DxP uses it for | Proven on the sandbox |
|---|---|---|
| Schema validation (`$jsonSchema`) | Grants, policies, decisions, actions, reports, memories and tasks reject malformed documents | [[PENDING: proven or not (I1)]] |
| Conditional updates and transactions | One claim per action, so two workers never both send; admissions and stop; approval claim; task authorisation saved in one transaction | [[PENDING: proven or not (I1, I3)]] |
| [[PENDING: Atlas Vector Search or text search (OD1)]] | Related evidence in the scope, and the team's active memories. Scores are shown and never used as evidence. If Vector Search was unavailable this row says "text search" and every screen says "related by text search" | [[PENDING: proven or not (OD1, I1)]] |
| Versioned documents | Grants, policy sets, memories and source versions are never edited in place, so every audit answer can be replayed | [[PENDING: proven or not (I1, I3)]] |
| Decisions and actions collections | The audit history: who acted, under which grant and policy set, what was allowed or blocked, and the Slack result | [[PENDING: proven or not (I3)]] |
| Change streams | Live run updates. This row stays only if the check passed; otherwise the screens polled and the row is removed | [[PENDING: passed or not (S5, OD5)]] |

## What was prepared, and what is built on 14 November

The event rules allow only work built during the event to be highlighted. This table lists what existed beforehand so judges can see it. Listing it here does not mean it is used.

| Prepared before the event | Used on Saturday? |
|---|---|
| Planning documents in `_bmad-output/`: brief, PRD, architecture, UX specifications (text only), epics and stories, build schedule, development plan | They are the plan, not product. No product code or data comes from them |
| Reference skills in `.claude/skills/dxp-*`: documentation for coding agents about the APIs, limits and gotchas of the tools we use | Read as documentation only. No code is copied from them or run |
| The BMad method files in `_bmad/` and the `bmad-*` skills | Process tooling for the team's agents. Not product |
| `data/` and `scripts/data/`: open data downloaded and fetch scripts written before the event | Not used without written organiser clearance. [[PENDING: whether the organisers cleared them (docs/clearance.md)]]. The build fetches its own data during the event |
| Logo images in the UX folder | Not used without written organiser clearance. [[PENDING: whether the organisers cleared them (docs/clearance.md)]]. The interface uses a text wordmark, "DxP" |
| The Slack incoming webhook for `#all-mango-db-hackathon`, created and tested before the event | The channel is used. The webhook address lives only in `.env` and the Modal secret and is never committed. Any script used to test it is not reused; the notifier is written during the event |
| The ElevenLabs and HeyGen accounts, if created before the event [[PENDING: which accounts existed beforehand (OD3, OD7)]] | Keys live only in `.env` and the Modal secret and are never committed. Every briefing and avatar video is generated during the event, on demand, from a report's own fields. No clip was made beforehand |
| A modified copy of the BMad sprint-planning status script | Planning tool only. It never recommends deferred stories. Not product |

| Built on 14 November (in progress; the verified table above says what passed) |
|---|
| All of `backend/`: the API, the agent run, the gate, the ledger, retrieval, memory, reports, the Slack notifier, stop and audit |
| All of `web/`: the report page, run console, audit view and accepted-knowledge view |
| The data in Atlas, all created during the event: the FDA companion-diagnostic list fetched live and filtered to lung rows, the prior trial collection fetched live from ClinicalTrials.gov, and the reviewer memory a person created through the real UI |
| `README.md`, `docs/submission.md` and `docs/video-script.md`, written for this submission |

### What is not reused, and why

- **No code from `scripts/data/` or any `dxp-*` skill**, because every line of project code must be written during the event. The skills are reference documentation.
- **No file from `data/`**, so the evidence in the demo comes from live fetches that can be repeated, unless an organiser cleared it in writing.
- **No prepared logo**, so the interface carries only a text wordmark, unless an organiser cleared it.
- **No script used to test the Slack webhook**, so the notifier is written and tested during the event.
- **No clip made beforehand** with ElevenLabs or HeyGen, so every briefing and avatar video shows the product working on the day.
- **No seeded reviewer memory.** It is created by a person through the interface.

## Organiser answers

The answers are recorded in [docs/clearance.md](docs/clearance.md) on Saturday morning. This table copies them in.

| Question | Answer |
|---|---|
| Submission deadline (the event guide says 17:00) | [[PENDING: organiser answer (docs/clearance.md)]] |
| May any coding start before 10:45? | [[PENDING: organiser answer (docs/clearance.md)]] |
| How should prepared material be presented? | [[PENDING: organiser answer (docs/clearance.md)]] |
| May the prepared data in `data/` and the logo images be used? | [[PENDING: organiser answer (docs/clearance.md)]] |
| Is one Slack alert per report in `#all-mango-db-hackathon` acceptable for that channel? | [[PENDING: organiser answer (docs/clearance.md)]] |

## Architecture in brief

| Part | Plan |
|---|---|
| Web app | Next.js on Vercel: report page, run console, audit view |
| API and agent | FastAPI and LangGraph on Modal, with Claude models |
| Data, identity, policy, audit | MongoDB Atlas Sandbox |
| External systems | ClinicalTrials.gov API (read), Slack incoming webhook (notify only), ElevenLabs and HeyGen (on demand) |

Rules the design holds to:

- **Two identities per run:** who started it, and the agent that executes it.
- **Grants are resolved on the server.** A name sent by a client never grants permission.
- **Every action passes the gate first.** Each check result is recorded as a Decision.
- **Source versions are pinned.** Quotes, retrieval results, proposals and audit entries keep the exact source version they used, so a later change to a trial never alters evidence that was already reviewed.
- **Notification outcomes are recorded honestly.** An uncertain Slack result is marked unknown, never retried blindly, and a reviewer resolves it in DxP.
- **Approval survives a crash.** The approval is saved before the report is accepted, and an interrupted approval is completed on restart with the reviewer's authority checked again.

## Documentation

- [Deployment](docs/deploy.md)
- [Demo setup, rehearsal and reset](docs/demo-and-reset.md)
- [Organiser clearance](docs/clearance.md)
- [Submission description](docs/submission.md)
- [60-second video script](docs/video-script.md)
- The full plan is in `_bmad-output/planning-artifacts/`: the discovery-agent change of 14 November (`sprint-change-proposal-2026-11-14-discovery-agent.md`), the pivot of 13 November (`sprint-change-proposal-2026-11-13.md`), the epics, the architecture and the development plan.

## Ground rules

- This repository is public. Never commit API keys, tokens, webhook addresses, connection strings or any credential.
- Secrets live in `.env` (git-ignored) or the deployment platform's secret store. `.env.example` lists names only.

## Credits

Data fetched during the event: ClinicalTrials.gov (U.S. National Library of Medicine) and the U.S. Food and Drug Administration (fda.gov and open.fda.gov). Platform and services: MongoDB Atlas, Claude (Anthropic), Slack, Modal and Vercel, and, if their checks passed, ElevenLabs and HeyGen. DxP is not endorsed by any of these organisations. Prepared open data under `data/` is not used unless an organiser cleared it; its sources are credited in `data/README.md`. Built by [[PENDING: team members as submitted (R1)]] at Agents in Context Toronto.
