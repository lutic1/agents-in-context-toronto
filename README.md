# DxP

DxP is an agent that keeps a pharma team's diagnostic evidence current, and it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action, and an audit trail a reviewer can replay.

Built for **Agents in Context Toronto: a MongoDB Hackathon** (Cerebral Valley), Problem Statement 1, "Agents You Can Audit".

- Date: Saturday, November 14, 2026. Hacking runs 10:45 AM to 5:00 PM EST.
- Location: The Quay, 100 Queens Quay E 3rd Floor, Toronto, ON M5E 1V3, Canada
- Event page: https://cerebralvalley.ai/e/mongodb-toronto-hackathon
- Team: Luis and Vlad

## What DxP does

DxP is for diagnostics teams in pharmaceutical companies. It reads public evidence about lung cancer diagnostic tests (clinical trials and the FDA list of companion diagnostics) and proposes updates to the team's records, each backed by a quote from the source.

The governed agent is the product. Every run follows the same loop:

1. **Identity.** Each run has a `run_id`, the agent that executes it and the person who started it, resolved on the server from the caller's key.
2. **Authority.** A grant stored in MongoDB Atlas names what the agent may do, for which team, in which destination, until when.
3. **Policy check before the action.** Hand-written, versioned policies are checked before every action. A blocked action changes nothing and calls nothing; the decision is still recorded.
4. **Action.** An allowed change to a record is filed as a pending proposal, and DxP posts a Slack alert (Block Kit) to `#all-mango-db-hackathon` with links back to the proposal in DxP. A human reviewer approves or rejects it in DxP, never in Slack; Slack only notifies.
5. **Audit.** Every decision, allowed or blocked, can be replayed later: who authorised it, under which grant and policy version, with what evidence.
6. **Stop.** A person can stop a run at any time. Nothing new starts after a stop; work already admitted finishes and is shown as in flight.

The screens only inspect the agent: a run console, an audit view, a record and review screen, and a view of what a run touched.

DxP tracks evidence about diagnostic tests. It is not a clinical decision tool and gives no medical advice.

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
| The BMad sprint-planning status script (`.claude/skills/bmad-sprint-planning/scripts/sprint_plan.py`), modified before the event so it never recommends deferred stories | |

## Open questions for the organisers

To confirm on Saturday between 9:00 and 10:45:

- The submission deadline (the guide says 17:00), and whether any coding may start before 10:45.
- How to present prepared material, and whether the prepared data in `data/` and the logo images may be used.
- Atlas Sandbox access, and whether it supports change streams.

## Open items

- Set `DXP_BASE_URL` to the production URL and confirm the Slack alert's links back to DxP resolve (owner Luis, during A04).
- Keep `SLACK_WEBHOOK_URL` only in `.env` and the Modal secret.

## Ground rules

- This repo is public. Never commit API keys, tokens, connection strings or credentials of any kind.
- Secrets live in `.env` (gitignored) or the deployment platform's secret store, never in the repo.
- MongoDB connection strings stay out of committed code. Use environment variables.

## Data credits

Data: ClinicalTrials.gov (U.S. National Library of Medicine), PubMed (courtesy of the U.S. National Library of Medicine), U.S. Food and Drug Administration (fda.gov and open.fda.gov), HGNC, OncoTree (CC BY 4.0), NCI Thesaurus (CC BY 4.0), MeSH (U.S. National Library of Medicine). DxP is not endorsed by these organisations. Abstract copyright remains with publishers or authors. Details per source are in `data/README.md`.
