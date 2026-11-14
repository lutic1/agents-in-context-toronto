# DxP

**DxP is a proactive diagnostic-evidence research agent, built to find newly updated clinical trials in a team's research scope, relate them to what the team already knows, check every claim and action against explicit policies, and file one pending report that a human approves or rejects.**

Built for **Agents in Context Toronto: a MongoDB Hackathon** (Cerebral Valley), Problem Statement 1, "Agents You Can Audit".

**Status: the build is in progress on Saturday 14 November 2026. The organisers allowed hacking from 10:30 ET; the deadline is planned for 17:00 ET (to be confirmed in docs/clearance.md, added by Luis).** Everything in the first section describes planned behaviour until the "Verified on the sandbox" table says otherwise. That table holds the check behind each claim, and the open facts, as markers in double square brackets. See "Reading the markers" under it.

- Event page: https://cerebralvalley.ai/e/mongodb-toronto-hackathon
- Location: The Quay, 100 Queens Quay E 3rd Floor, Toronto, ON M5E 1V3, Canada
- Production URL, public repository and 60-second video: see "Submission links" below the verified table
- Team: Luis, Vlad and Gregorio

DxP supports research review. It is not a clinical decision tool and gives no medical advice.

## What it does

A diagnostics team follows public evidence in one research area. Finding a newly updated trial, connecting it to what the team already holds, and deciding what to do next is slow manual work. An agent can do that work only if the team can answer: who acted, under what authority, what was it allowed to do, what was it stopped from doing, and why.

DxP's agent, `dxp-curator`, is planned to work for one research scope under a scoped grant. The demo scope is **"Plasma ctDNA genotyping assays in NSCLC"**, owned by a synthetic team, "Team Liquid Biopsy Dx". The data layer is planned to be MongoDB Atlas: identity, grants, policies, decisions and audit are all documents there. The checks for these sentences are in the first two rows of the verified table.

### How the project changed

- **13 November, the pivot.** DxP moved to Problem Statement 1, "Agents You Can Audit": governed agent actions, with scoped grants, a policy gate, a recorded Decision for every check, notify-only Slack, a stop control and an audit view that answers who acted and why.
- **14 November, the discovery-agent change.** The agent became proactive: it is built to scan its scope for trials updated since a cursor, relate what it finds to what the team already holds, remember reviewer corrections, file one pending report for a human to approve, and build longitudinal value over time.

Both changes are described below as planned behaviour until the verified table says otherwise. Their checks are in the first two rows of that table.

### The governed discovery loop

Every step below is planned behaviour. The check behind each one is a row of the verified table.

1. **Discover.** A run is planned to query ClinicalTrials.gov for trials in the scope that were updated since the scope's last scan, so the work does not repeat. The query is built to exclude treatment trials, by adding `AND NOT AREA[DesignPrimaryPurpose]TREATMENT` (merged in #60, approved by Luis), because the scope is diagnostic evidence and treatment trials are about drugs. The demo anchor NCT04712877 is unaffected, and the exclusion is planned to be visible in the recorded query and in the audit.
2. **Relate.** The agent is planned to find related evidence the team already holds. How it retrieves that evidence is not confirmed yet (see the table). Each relationship (supports, contradicts, extends, new question) will need a quote checked against the source from both sides, or the item is shown as "related (no relationship established)". A similarity score is planned to be displayed and never counted as evidence.
3. **Remember.** The agent is planned to retrieve the team's reviewer corrections ("memories") and show what each one changed in its draft. A memory is planned to belong to the team, name its author, and never change permissions. Memories are planned to be correctable and revocable.
4. **Gate.** Versioned policies will be checked before every action, and every check will be recorded as a Decision. A blocked action is planned to change nothing and still be recorded. The checks are planned to cover: the grant is active, the target is in the team's scope, the destination and action match the grant, the required evidence is present (including claim checks), and the run is still authorised.
5. **Propose.** The agent is planned to file one pending report: the finding, its quotes, related evidence, uncertainties, the evidence gap, and one recommended follow-up task. Nothing becomes accepted knowledge yet.
6. **Notify.** One Slack alert per report is planned, linking back to the report in DxP. Slack only notifies; approving and rejecting happen only in DxP.
7. **Brief, avatar and interview (optional, on demand).** These three extras are optional, sit behind feature flags and are never on the critical path. Each is claimed in the video or the submission only if its own check passed (V39); until then it is a plan. The report's own text script is always shown as text, and nothing waits on any extra.
   - **Briefing.** A ten-second briefing is a planned on-demand extra, spoken in the ElevenLabs voice "Jessica" (#51).
   - **LiveAvatar (HeyGen), V70, approved by Luis.** Behind the `avatar` flag. It replaces the earlier pre-rendered video (B08). It runs in FULL mode with `repeat(text)` only, never `message()`, and speaks only the text the backend returned. The avatar is LiveAvatar's public "Lily (Friendly)", with the voice "Jessica" (an ElevenLabs voice). The microphone and camera are blocked on every page of the app (#45), so it never listens. The session token is minted on the server (B08, #43, #52), so the LiveAvatar key never reaches the browser. If it fails, the text answer still shows.
   - **"Interview this evidence", V70, approved by Luis (merged in #56 and #57).** Behind the `interview` flag, which stays off until its check passes. It works on an accepted report only, with typed questions only. The answer is built only from the verbatim quotes stored on that report (pinned to its version), with a citations panel, and any framing sentence comes from a fixed allowlist. The persona is "DxP's evidence guide". Each question is a gated, logged Decision. A question that asks for medical advice gets one fixed refusal and no model call, and a question the report cannot answer gets "The accepted record doesn't answer that".
   - If a check fails, that extra stays off. The avatar is the first supporting cut, then the interview page.
8. **Decide.** A reviewer approves or rejects in DxP. Approval is planned to move the report's own update into accepted knowledge and authorise one follow-up task under its own narrow grant. Whatever that task later finds is planned to stay pending until a reviewer decides on it ("approved" is not "accepted" for the task). A rejection or a correction is planned to become a memory for the next discovery.
9. **Audit and stop.** Every step is planned to be replayable: what the agent found, which memory changed its wording, what was blocked, and who authorised the follow-up. A person is planned to be able to stop a run at any moment.
   - **The rollback story (planned behaviour).** Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. The agent cannot change accepted knowledge without a human approval.
   - Pending reports are planned to be rejectable. Memories are planned to be revocable. History and source versions are planned never to be overwritten.
   - Planned as a supporting extra: an approval can be reverted with a note. The update leaves accepted knowledge, nothing is deleted, and a follow-up task that has not started is cancelled.
   - None of this is planned to undo effects outside DxP. A Slack alert that was sent stays sent, and the audit is planned to record it.
   - The run console and audit view are planned to update live from an Atlas change stream, and to say "Refreshing every 2 s" when they poll instead.

### The longitudinal value

The scope's scan cursor and the team's memories are planned to accumulate over time. A scan is planned to read only what changed since the last one, and a correction a reviewer made earlier in the day is planned to shape the next report. The larger idea is team-specific, longitudinal intelligence on the diagnostics a team follows. The demo shows one turn of that loop.

### The planned demo

One discovery run on the scope is planned to find the anchor trial NCT04712877 (updated 2026-11-12, after the scan cursor of 2026-11-11; V49). The report is planned to state what the record says, in the record's own words, and its evidence gap. A reviewer memory from earlier in the day is planned to change the report's wording. One proposed action is planned to be blocked by a policy check before anything is filed: the anchor's record is expected to name "FoundationOne CDx" (a tissue test) that the plasma scope excludes. A Slack alert opens the report, a human approves, and the audit view answers: "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?"

When the demo or the report mentions an assay name that appears in a trial record, we say it is "named in the record". A name in a record is not evidence that the trial used or studied that product. DxP is built to describe each assay name as "named in the record", and its claim check is planned to block any performance or results claim the source version does not support. A person is planned to check a full report against its source version before it is shown.

The briefing, LiveAvatar (HeyGen) and the "Interview this evidence" page (step 7) are optional, on demand, behind their flags and not on the critical path; LiveAvatar is the first supporting cut and the interview page is cut after it. Running the approved follow-up task is a stretch goal behind a feature flag; if it does not run, DxP says "Follow-up task authorised; not run" and claims no follow-up results.

## Verified on the sandbox

Each row is filled in with its evidence when it passes, and stays a marker until then. The first rows carry the check for each claim in the first section, so no check is lost when the first section reads cleanly.

| Behaviour | Status |
|---|---|
| The agent works for one scope under a scoped grant; identity, grants, policies, decisions and audit are Atlas documents ("What it does") | [[VERIFY: I1 | I3]] |
| The 13 November pivot and the 14 November discovery-agent change, as described under "How the project changed" | [[VERIFY: I1 | I3 | A16 pass 1]] |
| Step 1, Discover: the scan reads only trials updated since the scope's cursor | [[VERIFY: I1]] |
| Step 1, Discover: the treatment-trial exclusion (#60) is in the recorded query and the audit, and the anchor NCT04712877 is kept (a live query check on 14 November kept it) | [[VERIFY: I1]] |
| Step 2, Relate: a relationship needs a quote checked from both sides, else "related (no relationship established)"; the score is shown and never counted as evidence | [[VERIFY: I1]] |
| Step 2, Relate: how related evidence is retrieved (Atlas Vector Search, Automated Embedding or text search). OD1 is not confirmed on the team sandbox; Gregorio will confirm after I1 step 1. Any "semantic" wording waits for this | [[PENDING: method that ran, or not available (OD1, I1)]] |
| Step 3, Remember: the agent retrieves the team's memories; a memory belongs to the team, names its author and never changes permissions; its effect is shown on the report | [[VERIFY: I1]] |
| Step 3, Remember: a memory is correctable and revocable | [[VERIFY: S3]] [[PENDING: pass or fail (S3, A21+A22)]] |
| Step 4, Gate: policies are checked before every action, every check is a Decision, a blocked action changes nothing and is recorded | [[VERIFY: I1]] |
| Step 5, Propose: one pending report, nothing accepted yet | [[VERIFY: I1]] |
| Step 6, Notify: one Slack alert per report that opens the report in DxP; Slack only notifies | [[VERIFY: I1 | I3]] [[PENDING: pass or fail (I1)]] |
| Step 7: the report's own text script is always shown as text | [[VERIFY: I1]] |
| Step 8, Decide: approval moves the update into accepted knowledge and authorises one follow-up task | [[VERIFY: I3]] [[PENDING: pass or fail (I3)]] |
| Step 8, Decide: a rejection or a correction becomes a memory for the next discovery | [[VERIFY: I3]] |
| Step 8, Decide: what the follow-up task finds stays pending until a reviewer decides | [[VERIFY: I3b]] |
| Step 9, Audit: every step can be replayed (found, memory effect, blocked, authorised) | [[VERIFY: I3]] |
| Step 9, Stop: a person can stop a run at any moment | [[PENDING: pass or fail (A16 pass 1)]] |
| The rollback story: nothing is accepted until a human approves; the agent cannot change accepted knowledge without a human approval | [[VERIFY: I3 | A16 pass 1]] |
| Pending reports can be rejected | [[VERIFY: I3]] |
| History and source versions are never overwritten | [[VERIFY: I1 | I3]] |
| Effects outside DxP are not undone: a sent Slack alert stays sent and the audit records it | [[VERIFY: I1 | I3]] |
| Longitudinal value: a scan reads only what changed since the last one, and an earlier correction shapes the next report | [[VERIFY: I1]] |
| Demo: the anchor's record names an assay the plasma scope excludes, such as "FoundationOne CDx", so the block is on that mention | [[PENDING: whether the actual anchor's record names such an assay (OD2)]] |
| Demo: each assay name is described as "named in the record", the claim check blocks an unsupported performance or results claim, and a person checked the full report against its source version | [[PENDING: result of that source check (A16 pass 1)]] |
| Ten-second ElevenLabs briefing, in the voice "Jessica" (#51) | [[PENDING: passed or not (B06 check)]] |
| LiveAvatar (HeyGen), V70 (approved by Luis), `avatar` flag: FULL mode, `repeat(text)` only, "Lily (Friendly)" with the voice "Jessica", microphone blocked app-wide (#45), token minted on the server (B08). Replaces the earlier pre-rendered video | [[PENDING: passed or not (avatar sandbox test; OD7)]] |
| "Interview this evidence", V70 (approved by Luis; merged in #56 and #57), `interview` flag off until its check passes: typed questions on an accepted report only, answers from the report's verbatim quotes only, with citations, framing from a fixed allowlist, the persona "DxP's evidence guide", the fixed medical-advice refusal and "The accepted record doesn't answer that" | [[PENDING: passed or not (interview checks)]] |
| Revert an approval | [[PENDING: passed or not (S4)]] |
| Live updates from a change stream, or "Refreshing every 2 s" when the screens poll | [[PENDING: passed or not (S5, OD5)]] |
| Follow-up task run | [[PENDING: ran or not (I3b)]] |

### Reading the markers

Facts we do not know yet are markers that start with the word PENDING inside double square brackets, each with where the answer will come from. A marker that starts with the word VERIFY names every check (for example I1, I3 or A16 pass 1) that must pass before the claim it gates stands. The first section carries no markers: its claims are worded as planned, and each one has a row above that holds its check. As each check passes (I1, I3, A16 pass 1, S1 to S5), its result is posted, and the owner of B07 resolves the markers and deletes any sentence whose check failed. Until then it is a plan, not a claim. R1 strips every remaining marker before submission.

### Submission links

- Production URL: [[PENDING: production URL (A04, docs/deploy.md)]]
- Public repository: [[PENDING: public repository URL (R1)]]
- 60-second video: [[PENDING: video link (R1)]]

## MongoDB capabilities

A capability stays in this table as used only when its last column says proven on the Atlas Sandbox. Every row is planned use until then.

| Capability | Planned use (not a claim until proven) | Proven on the sandbox |
|---|---|---|
| Schema validation (`$jsonSchema`) | Grants, policies, decisions, actions, reports, memories and tasks are planned to reject malformed documents | [[PENDING: proven or not (I1)]] |
| Conditional updates and transactions | Planned: one claim per action, so two workers never both send; admissions and stop; approval claim; task authorisation saved in one transaction | [[PENDING: proven or not (I1, I3)]] |
| [[PENDING: Atlas Vector Search, Automated Embedding or text search, whichever the team sandbox supports (OD1; not confirmed yet, Gregorio will confirm after I1 step 1)]] | Planned: related evidence in the scope, and the team's active memories. Scores are shown and never used as evidence. If Vector Search is unavailable this row says "text search" and every screen says "related by text search". No "semantic" claim until this is confirmed | [[PENDING: proven or not (OD1, I1)]] |
| `memories` collection | Planned: the team's reviewer corrections, each naming its author, retrieved for the next discovery, with its effect shown on the report, and planned to be correctable and revocable [[PENDING: whether memory correct and revoke passed its check (S3, A21+A22)]] | [[PENDING: proven or not (I1, S3)]] |
| Versioned documents | Planned: grants, policy sets, memories and source versions are never edited in place, so every audit answer can be replayed | [[PENDING: proven or not (I1, I3)]] |
| Decisions and actions collections | Planned: the audit history of who acted, under which grant and policy set, what was allowed or blocked, and the Slack result | [[PENDING: proven or not (I3)]] |
| Change streams | Planned: live run updates. This row stays only if the check passed; otherwise the screens poll and the row is removed | [[PENDING: passed or not (S5, OD5)]] |

## What was prepared, and what is built on 14 November

The event rules allow only work built during the event to be highlighted. This table lists what existed beforehand so judges can see it. Listing it here does not mean it is used.

| Prepared before the event | Used on Saturday? |
|---|---|
| Planning documents in `_bmad-output/`: brief, PRD, architecture, UX specifications (text only), epics and stories, build schedule, development plan | They are the plan, not product. No product code or data comes from them |
| Reference skills in `.claude/skills/dxp-*`: documentation for coding agents about the APIs, limits and gotchas of the tools we use | Read as documentation only. No code is copied from them or run |
| The BMad method files in `_bmad/` and the `bmad-*` skills | Process tooling for the team's agents. Not product |
| `data/` and `scripts/data/`: open data downloaded and fetch scripts written before the event | Not used without written organiser clearance. [[PENDING: whether the organisers cleared them (docs/clearance.md)]]. The build is planned to fetch its own data during the event, unless the organisers cleared the prepared files, in which case this row is updated [[PENDING: whether any prepared data file was loaded (docs/clearance.md)]]; if the FDA page could not be fetched, the Diagnostics the scope names were typed from the FDA page during the event [[PENDING: whether the FDA fetch worked (A13)]] |
| Logo images in the UX folder | Not used without written organiser clearance. [[PENDING: whether the organisers cleared them (docs/clearance.md)]]. The interface uses a text wordmark, "DxP" |
| The Slack incoming webhook for `#all-mango-db-hackathon`, created and tested before the event | The channel is planned to be used [[PENDING: organiser answer on alert volume in that channel (docs/clearance.md)]]. The webhook address lives only in `.env` and the Modal secret and is never committed. Any script used to test it is not reused; the notifier is written during the event |
| The ElevenLabs and LiveAvatar (HeyGen), V70, accounts, if created before the event [[PENDING: which accounts existed beforehand (OD3, OD7)]] | Keys live only in `.env` and the Modal secret and are never committed. Every briefing is planned to be generated, and any LiveAvatar session opened, during the event, on demand, from a report's own verified script. [[PENDING: Luis confirms no test audio or video was made before the event (OD3, OD7)]] |
| A modified copy of the BMad sprint-planning status script | Planning tool only. It never recommends deferred stories. Not product |

| Planned to be built on 14 November (a row counts as built only once its check in the verified table passed) |
|---|
| All of `backend/`: the API, the agent run, the gate, the ledger, retrieval, memory, reports, the Slack notifier, stop and audit |
| All of `web/`: the report page, run console, audit view and accepted-knowledge view |
| The data in Atlas, planned to be created during the event: the FDA companion-diagnostic list fetched live and filtered to lung rows, the prior trial collection fetched live from ClinicalTrials.gov, and the reviewer memory a person created through the real UI, unless the organisers cleared the prepared files, in which case this row is updated [[PENDING: whether any prepared data file was loaded (docs/clearance.md)]]; if the FDA page could not be fetched, the Diagnostics the scope names were typed from the FDA page during the event [[PENDING: whether the FDA fetch worked (A13)]] |
| `README.md`, `docs/submission.md` and `docs/video-script.md`, written for this submission |

### What is not reused, and why

- **No code from `scripts/data/` or any `dxp-*` skill**, because every line of project code must be written during the event. The skills are reference documentation.
- **No file from `data/`**, so the evidence in the demo comes from live fetches that can be repeated, unless an organiser cleared it in writing.
- **No prepared logo**, so the interface carries only a text wordmark, unless an organiser cleared it.
- **No script used to test the Slack webhook**, so the notifier is written and tested during the event.
- **No clip planned to be made beforehand** with ElevenLabs or LiveAvatar (HeyGen), V70: every briefing is planned to be generated, and any LiveAvatar session opened, during the event, from a report's own verified script, so it shows the product working on the day. [[PENDING: Luis confirms no test audio or video was made before the event (OD3, OD7)]]
- **No seeded reviewer memory.** It is created by a person through the interface.

## Organiser answers

The answers are recorded in docs/clearance.md (added by Luis) on Saturday morning. This table copies them in.

| Question | Answer |
|---|---|
| Submission deadline (the event guide says 17:00) | [[PENDING: organiser answer (docs/clearance.md)]] |
| May any coding start before 10:45? | Yes, from 10:30, per the organisers |
| How should prepared material be presented? | [[PENDING: organiser answer (docs/clearance.md)]] |
| May the prepared data in `data/` and the logo images be used? | [[PENDING: organiser answer (docs/clearance.md)]] |
| Is one Slack alert per report in `#all-mango-db-hackathon` acceptable for that channel? | [[PENDING: organiser answer (docs/clearance.md)]] |

## Architecture in brief

| Part | Plan |
|---|---|
| Web app | Next.js on Vercel: report page, run console, audit view |
| API and agent | FastAPI and LangGraph on Modal, with Claude models |
| Data, identity, policy, audit | MongoDB Atlas Sandbox |
| External systems | ClinicalTrials.gov API (read), Slack incoming webhook (notify only), ElevenLabs and LiveAvatar (HeyGen), V70 (approved by Luis), plus the optional "Interview this evidence" page (all optional, on demand, behind flags; the LiveAvatar token is minted on the server) |

Rules the design holds to:

- **Two identities per run:** who started it, and the agent that executes it. [[VERIFY: I1]]
- **Grants are resolved on the server.** A name sent by a client never grants permission. [[VERIFY: I1]]
- **Every action passes the gate first.** Each check result is recorded as a Decision. [[VERIFY: I1]]
- **Source versions are pinned.** Quotes, retrieval results, proposals and audit entries keep the exact source version they used, so a later change to a trial never alters evidence that was already reviewed. [[VERIFY: I1 | I3]]
- **Notification outcomes are recorded honestly.** An uncertain Slack result is marked unknown, never retried blindly, and a reviewer resolves it in DxP. [[VERIFY: I1]]
- **Approval is designed to survive a crash.** The approval is saved before the report is accepted, and an interrupted task authorisation is completed on restart, with the reviewer's authority checked again. [[PENDING: whether the crash and retry checks passed (A24, I3)]] Known limitation: a crash right before a memory is created is repaired only when the reviewer retries the decision.

## Documentation

- [Deployment](docs/deploy.md)
- Demo setup, rehearsal and reset: docs/demo-and-reset.md (added by A16)
- Organiser clearance: docs/clearance.md (added by Luis)
- [Submission description](docs/submission.md)
- [60-second video script](docs/video-script.md)
- The full plan is in `_bmad-output/planning-artifacts/`: the discovery-agent change of 14 November (`sprint-change-proposal-2026-11-14-discovery-agent.md`), the pivot of 13 November (`sprint-change-proposal-2026-11-13.md`), the epics, the architecture and the development plan.

## Ground rules

- This repository is public. Never commit API keys, tokens, webhook addresses, connection strings or any credential.
- Secrets live in `.env` (git-ignored) or the deployment platform's secret store. `.env.example` lists names only.

## Credits

Data planned to be fetched during the event: ClinicalTrials.gov (U.S. National Library of Medicine) and the FDA list of companion diagnostics (fda.gov) [[PENDING: whether any prepared data file was loaded instead (docs/clearance.md)]]. Platform and services: MongoDB Atlas, Claude (Anthropic), Slack, Modal and Vercel, and, if their checks passed, ElevenLabs and LiveAvatar (HeyGen, V70). DxP is not endorsed by any of these organisations. Prepared open data under `data/` is not used unless an organiser cleared it; its sources, including openFDA, are credited in `data/README.md`. Built by Luis, Vlad and Gregorio at Agents in Context Toronto.
