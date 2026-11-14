# DxP submission

Text for the Agents in Context Toronto submission form (Problem Statement 1, "Agents You Can Audit"). R1 pastes it in with the video link by 16:55.

**R1, read this first.** Each sentence below that describes behaviour ends with a tag in the form `[[VERIFY: I1 | I3 | A16 pass 1]]`. Nothing the tag gates has been verified yet. The tag names every check that must have passed before that sentence is submitted: read the results in the README "Verified on the sandbox" table and in `docs/demo-and-reset.md` (A16 pass 1). If any check named in a tag did not pass, delete the sentence (or the whole bullet). Then remove every remaining `[[VERIFY: ...]]` tag before pasting. Resolve each marker that starts with the word PENDING in double square brackets in the same way: fill in the fact, or delete the sentence. A VERIFY or PENDING marker left in the form is a failed submission check. One exception: the rollback sentences under "How to stop or roll back an agent mid-run" are the V48 line, which is never cut. If their checks did not pass, do not submit; tell Luis.

**Wording status.** Features that are optional or not built yet are written as planned and are not tagged. They stay phrased as planned unless the matching row of "Verified on the sandbox" in the README has passed, in which case R1 may rewrite that one sentence in the present tense.

## Form fields

| Field | Value |
|---|---|
| Project name | DxP |
| Problem statement | Statement 1, "Agents You Can Audit" |
| Public repository | [[PENDING: public repository URL (R1)]] |
| Production URL | [[PENDING: production URL (A04, docs/deploy.md)]] |
| Video (60 seconds) | [[PENDING: video link (R1)]] |
| Team members | [[PENDING: team members as submitted (R1)]] |

## One line

DxP is a proactive diagnostic-evidence research agent for a team's clinical-trial scope. It is built to discover newly updated trials, check every claim and action against policies stored in MongoDB Atlas, and keep its work out of accepted knowledge until a human approves. [[VERIFY: I1 | I3 | A16 pass 1]]

## Description

Diagnostics teams follow public clinical evidence by hand. A trial gets updated, and someone has to notice it, connect it to what the team already knows, and decide what it means. An AI agent could do that work, but a team can trust it only if it can answer who acted, under what authority, what the agent was allowed to do, what it was stopped from doing, and why.

DxP is that agent, built around those answers. Its agent, `dxp-curator`, works for one research scope, "Plasma ctDNA genotyping assays in NSCLC", under a scoped grant. [[VERIFY: I1]] In one governed loop it:

- **discovers** trials in the scope that were updated since the last scan, and looks only at what changed [[VERIFY: I1]];
- **relates** each one to the evidence the team already holds, using [[PENDING: Atlas Vector Search or text search (OD1)]], and labels each relationship only when it can back it with a checked quote from both sides [[VERIFY: I1]];
- **remembers** the team's reviewer corrections and shows exactly which memory changed its wording [[VERIFY: I1]];
- **checks** every claim and every action against versioned policies before it takes effect; a blocked action changes nothing and is still recorded [[VERIFY: I1]];
- **files one pending report** that names one evidence gap, and sends **one Slack alert** that links back to it [[VERIFY: I1]];
- **waits for a human.** A reviewer approves or rejects in DxP. Approval moves the report's own update into accepted knowledge and authorises one follow-up task under its own narrow grant [[VERIFY: I3]]. Running that task is a stretch goal. If it runs, what it finds is planned to stay pending until a reviewer decides on it [[VERIFY: I3b]]. If it does not run, DxP says "Follow-up task authorised; not run" [[VERIFY: I3]].

The demo is planned to use ClinicalTrials.gov data fetched during the event [[PENDING: whether any prepared data file was loaded instead (docs/clearance.md)]]. When a trial record mentions an assay name, DxP says the name is "named in the record" [[VERIFY: I1 | A16 pass 1]]. A name in a record is not evidence that the trial used or studied that product. DxP is built to describe each assay name as "named in the record", and its claim check is planned to block any performance or results claim the source version does not support. A person is planned to check a full report against its source version before it is shown. [[PENDING: result of that source check (A16 pass 1)]] [[PENDING: the demo anchor trial and its one-line signal, verified against the live API at 10:45 (OD2)]]

### How to stop or roll back an agent mid-run

Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. The agent cannot change accepted knowledge without a human approval. [[VERIFY: I3 | A16 pass 1]] Beyond that:

- pending reports can be rejected [[VERIFY: I3]];
- memories can be revoked [[VERIFY: S3]];
- history and source versions are never overwritten [[VERIFY: I1 | I3]];
- an approval can be reverted with a note: the update leaves accepted knowledge, nothing is deleted, and a follow-up task that has not started is cancelled [[VERIFY: S4]].

DxP does not undo effects outside itself. A Slack alert that was sent stays sent, and the audit records it. [[VERIFY: I1 | I3]]

### MongoDB Atlas as the identity, policy and audit layer

Only capabilities proven on the sandbox may stay in this list. Each bullet carries the checks that prove it; delete the bullet if any did not pass:

- schema validation, so a malformed grant, policy, decision or task cannot be saved [[VERIFY: I1]];
- conditional updates and transactions, so one Slack alert is claimed once, a stop settles once, and an approval and its task authorisation are saved together [[VERIFY: I1 | I3]];
- [[PENDING: Atlas Vector Search or Atlas text search, whichever ran (OD1)]] for related evidence and for the team's memories, with scores shown and never used as evidence [[VERIFY: I1]];
- versioned documents, so grants, policy sets, memories and source versions are never edited in place and every audit answer can be replayed [[VERIFY: I1 | I3]];
- the decisions and actions collections as the audit history [[VERIFY: I3]];
- change streams for live run updates [[VERIFY: S5 | OD5]]. If the check did not pass, delete this bullet: the screens polled.

### The longitudinal value

The scope's scan cursor and the team's memories are kept over time, so the next scan reads only what changed since the last one [[VERIFY: I1]], and a correction made earlier in the day shapes the next report [[VERIFY: I1]]. DxP is aimed at team-specific, longitudinal intelligence on the diagnostics a team follows. The demo shows one turn of that loop.

### Optional extras

Each of these is optional, on demand and planned. None gates the loop. Keep a sentence only if its check passed, and say nothing about the rest. [[PENDING: which supporting features passed their checks: briefing (B06), LiveAvatar (B08, OD7, V49), revert (S4), live stream (S5), follow-up task run (I3b)]]

- A ten-second ElevenLabs briefing is planned to be made on demand from the report's own text script. [[VERIFY: B06]]
- LiveAvatar (HeyGen), pending approval (proposed V70), is a live, interactive avatar planned to speak only the report's verified script. It is pending Luis's approval as a proposed decision V70, it is the first supporting cut, and the sentence stays only if V49 was approved and its check passed. [[VERIFY: B08 | OD7 | V49]]
- The script is always shown as text. [[VERIFY: I1]]
- Running the authorised follow-up task is a stretch goal. If it did not run, DxP says "Follow-up task authorised; not run" and claims no follow-up results.

### Built on the day, and what was prepared

The plan is that all code, all data in Atlas and any briefing or LiveAvatar session are produced during the event, and that no prepared code, data file, logo or clip is reused unless an organiser cleared it in writing. [[PENDING: whether any prepared data file or logo was cleared and used (docs/clearance.md)]] Prepared material (planning documents, reference skills, open data files, logo images, the Slack webhook and channel, and any ElevenLabs and LiveAvatar (HeyGen), pending approval (proposed V70), accounts) is listed in the README, with what was and was not used. [[PENDING: organiser answers on prepared material (docs/clearance.md)]]

### Limits

DxP supports research review. It gives no medical advice and is not a clinical decision tool. Reports state what a source says and what it does not say. [[VERIFY: A16 pass 1]] Reviewers are synthetic personas in the demo.

## Short version (about 50 words, if the form has a short field)

R1 pastes this only after the longer text is confirmed, using the same rule: delete a sentence whose check did not pass, and remove the tags. If the MongoDB capability is not proven, drop "in MongoDB Atlas".

DxP is a research agent that discovers updated clinical trials in a team's scope, relates them to the team's evidence, checks every action against policies in MongoDB Atlas, and files one pending report. [[VERIFY: I1]] Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. [[VERIFY: I3 | A16 pass 1]]
