# DxP

DxP is a proactive research agent for diagnostics teams: it discovers new clinical trials, connects them to the evidence the team already holds, remembers reviewer corrections and proposes useful follow-up work, and it cannot act without a named identity, a scoped grant, a policy check before every action and an audit trail a reviewer can replay.

Built for **Agents in Context Toronto: a MongoDB Hackathon** (Cerebral Valley), Problem Statement 1, "Agents You Can Audit".

- Date: Saturday, November 14, 2026. Hacking runs 10:45 AM to 5:00 PM EST.
- Location: The Quay, 100 Queens Quay E 3rd Floor, Toronto, ON M5E 1V3, Canada
- Event page: https://cerebralvalley.ai/e/mongodb-toronto-hackathon
- Team: Luis and Vlad

## What DxP does

DxP works for one research scope, "Plasma ctDNA genotyping assays in advanced NSCLC", owned by a pharma diagnostics team. It reads public evidence (ClinicalTrials.gov and the FDA list of companion diagnostics) and keeps its collection, embeddings, reviewer memory, grants, policies and audit trail in MongoDB Atlas.

The governed discovery loop:

1. **Discover.** The agent searches ClinicalTrials.gov for trials in the scope updated since its last scan.
2. **Relate.** Atlas Vector Search finds related evidence; each link is labelled supports, contradicts, extends or new question, with a checked quote from both sides. A similarity score is shown but never used as evidence.
3. **Remember.** The agent retrieves the team's reviewer corrections and shows what each one changed. A memory is attributable, can be corrected or revoked, and never changes permissions.
4. **Gate.** Explicit policies are checked before every action; for example, the agent cannot say an assay produced results unless the source reports them. A blocked action changes nothing and is still recorded.
5. **Propose.** The agent files one pending research report: the discovery, quotes, related evidence, uncertainties and one recommended next task. Nothing becomes accepted knowledge yet.
6. **Notify.** One Slack alert per report links back to the report in DxP. Approval and rejection happen only in DxP.
7. **Brief.** A ten-second ElevenLabs briefing and a short HeyGen avatar video explain the report, both from the same script built only from the report's evidence (supporting, behind flags).
8. **Decide.** Approval promotes the report's updates into accepted knowledge and authorises one follow-up task, which runs under its own narrow grant and policy gate. A rejection or a correction becomes a memory for the next discovery.

Every step can be replayed in the audit: what the agent found, which memory changed its wording, what was blocked, and who authorised the follow-up. A person can stop any run.

DxP supports research review. It is not a clinical decision tool and gives no medical advice.

## Status

- Planning was finished on 13 and 14 November 2026, before the event started at 10:45 on 14 November.
- Everything else is built on 14 November 2026, from 10:45.

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
| OD2 | The live ClinicalTrials.gov API still shows NCT04712877 updated after the scan cursor, recruiting, without results | Luis, 10:45 | Any in-scope trial updated since the cursor; the claim policy applies the same way |
| OD3 | ElevenLabs key and quota | Luis, before 10:45 | The briefing is hidden |
| OD4 | Organiser clearance: prepared data, logo, Slack channel volume | Luis, 9:00 to 10:45 | Live fetches, the text wordmark, a team channel if needed |
| OD5 | Change streams on the sandbox | — | Closed: not needed, screens poll |
| OD6 | `mongodump` and `mongorestore` work against the sandbox, for the reset before each take | Luis, by 12:20; proven at 14:15 | Reset by rerunning the setup, which takes longer |
| OD7 | HeyGen needs a paid plan or funded API wallet; render time can range from minutes to many hours | Luis and Vlad, one timed render at 10:45, decided by 12:00 | The report shows "Rendering" or "Avatar unavailable" and the loop is unaffected; the avatar is the first thing cut |

Also: set `DXP_BASE_URL` to the production URL and confirm the Slack alert's links resolve (Luis, during the deploy); keep `SLACK_WEBHOOK_URL` and every API key only in `.env` and the Modal secret.

## Ground rules

- This repo is public. Never commit API keys, tokens, connection strings or credentials of any kind.
- Secrets live in `.env` (gitignored) or the deployment platform's secret store, never in the repo.
- MongoDB connection strings stay out of committed code. Use environment variables.

## Data credits

Data: ClinicalTrials.gov (U.S. National Library of Medicine), PubMed (courtesy of the U.S. National Library of Medicine), U.S. Food and Drug Administration (fda.gov and open.fda.gov), HGNC, OncoTree (CC BY 4.0), NCI Thesaurus (CC BY 4.0), MeSH (U.S. National Library of Medicine). DxP is not endorsed by these organisations. Abstract copyright remains with publishers or authors. Details per source are in `data/README.md`.
