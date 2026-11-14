# DxP submission

Text for the Agents in Context Toronto submission form (Problem Statement 1, "Agents You Can Audit"). R1 pastes it in with the video link by 16:55.

**Wording status.** Every behaviour below is written as planned behaviour until the matching row of "Verified on the sandbox" in the README has passed. Before submitting, R1 resolves each `[[PENDING: ...]]` marker, and deletes any sentence about a feature whose check did not pass. A marker left in the form is a failed submission check.

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

DxP is a proactive diagnostic-evidence research agent that discovers newly updated clinical trials in a team's scope, checks every claim and action against policies stored in MongoDB Atlas, and never lets its work become accepted knowledge without a human approval.

## Description

Diagnostics teams follow public clinical evidence by hand. A trial gets updated, and someone has to notice it, connect it to what the team already knows, and decide what it means. An AI agent could do that work, but a team can trust it only if it can answer who acted, under what authority, what the agent was allowed to do, what it was stopped from doing, and why.

DxP is that agent, built around those answers. Its agent, `dxp-curator`, works for one research scope, "Plasma ctDNA genotyping assays in NSCLC", under a scoped grant. In one governed loop it:

- **discovers** trials in the scope that were updated since the last scan, and looks only at what changed;
- **relates** each one to the evidence the team already holds, using [[PENDING: Atlas Vector Search or text search (OD1)]], and labels each relationship only when it can back it with a checked quote from both sides;
- **remembers** the team's reviewer corrections and shows exactly which memory changed its wording;
- **checks** every claim and every action against versioned policies before it takes effect; a blocked action changes nothing and is still recorded;
- **files one pending report** that names one evidence gap, and sends **one Slack alert** that links back to it;
- **waits for a human.** A reviewer approves or rejects in DxP. Approval moves the report's own update into accepted knowledge and authorises one follow-up task under its own narrow grant; what that task later finds stays pending until a reviewer decides on it.

The demo uses real ClinicalTrials.gov data fetched during the event. When a trial record mentions an assay name, DxP says the name is "named in the record" and never says the trial used or studied it. It makes no claim about how any assay performs. [[PENDING: the demo anchor trial and its one-line signal, verified against the live API at 10:45 (OD2)]]

### How to stop or roll back an agent mid-run

Nothing the agent does is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo. The agent cannot change accepted knowledge without a human approval. Beyond that:

- pending reports can be rejected;
- memories can be revoked;
- history and source versions are never overwritten;
- an approval can be reverted with a note: the update leaves accepted knowledge, nothing is deleted, and a follow-up task that has not started is cancelled. [[PENDING: keep this line only if revert passed its check (S4)]]

DxP does not undo effects outside itself. A Slack alert that was sent stays sent, and the audit records it.

### MongoDB Atlas as the identity, policy and audit layer

Only capabilities proven on the sandbox are named here. [[PENDING: which capabilities were proven on the sandbox (I1, I3; README table)]] The plan uses:

- schema validation, so a malformed grant, policy, decision or task cannot be saved;
- conditional updates and transactions, so one Slack alert is claimed once, a stop settles once, and an approval and its task authorisation are saved together;
- [[PENDING: Vector Search or text search, whichever ran (OD1)]] for related evidence and for the team's memories, with scores shown and never used as evidence;
- versioned documents, so grants, policy sets, memories and source versions are never edited in place and every audit answer can be replayed;
- the decisions and actions collections as the audit history;
- [[PENDING: change streams for live run updates, only if they passed (S5, OD5); otherwise delete this line, the screens polled]].

### The longitudinal value

The scope's scan cursor and the team's memories accumulate over time: the next scan reads only what changed since the last one, and a correction made earlier in the day shapes the next report. DxP is aimed at team-specific, longitudinal intelligence on the diagnostics a team follows. The demo shows one turn of that loop.

### Optional extras

[[PENDING: which supporting features passed their checks: briefing (B06), avatar (B08, OD7), revert (S4), live stream (S5), follow-up task run (I3b)]] Each is on demand and none gates the loop. A ten-second ElevenLabs briefing and a HeyGen avatar video are made from the report's own text script, which is always shown as text. Running the authorised follow-up task is a stretch goal. If it did not run, DxP says "Follow-up task authorised; not run" and claims no follow-up results.

### Built on the day, and what was prepared

All code, all data in Atlas and every briefing and video were produced during the event. Prepared material (planning documents, reference skills, open data files, logo images, the Slack webhook and channel, and any ElevenLabs and HeyGen accounts) is listed in the README, with what was and was not used. No code, data file, logo or clip prepared beforehand is reused. [[PENDING: organiser answers on prepared material (docs/clearance.md)]]

### Limits

DxP supports research review. It gives no medical advice and is not a clinical decision tool. Reports state what a source says and what it does not say. Reviewers are synthetic personas in the demo.

## Short version (about 50 words, if the form has a short field)

DxP is a research agent that discovers updated clinical trials in a team's scope, relates them to the team's evidence, checks every action against policies in MongoDB Atlas, and files one pending report. Nothing is accepted until a human approves, so stopping it mid-run never leaves accepted knowledge to undo.
