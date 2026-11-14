---
title: DxP development plan, Saturday 14 November 2026
status: draft (follows the discovery-agent proposal, which is draft until Luis confirms it)
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/build-schedule.md
---

# DxP development plan

Who builds what on Saturday, one pull request at a time.

DxP is a **proactive diagnostic-evidence research agent**, entered under Statement 1, "Agents You Can Audit". Within one research scope it discovers newly updated ClinicalTrials.gov trials, relates them to the evidence it already holds through Atlas Vector Search, retrieves the reviewer corrections it remembers, checks every claim and action against explicit policies, and files one pending research report that names one evidence gap. It alerts Slack once per report. When Sam approves, the report's own updates are promoted into accepted knowledge and one follow-up task that answers the gap is authorised; whatever that task finds stays pending until a Reviewer decides on it (V27). Running the task is supporting scope (V28). Identity, grants, policies, decisions, stop and audit carry that loop; they are no longer the whole product. The scope cursor and the Team's memories accumulate over time, so the demo shows one turn of team-specific, longitudinal intelligence (V32). DxP supports research review and gives no medical advice.

Which document wins:

1. `sprint-change-proposal-2026-11-14-discovery-agent.md`. Within it, V25 to V32 (section 10) win over V1 to V24, and V33 to V37 (section 11, the registry check) win over V25 to V27. This plan adopts the section 7 cuts as the baseline, except that A24 and A25 are split again (V28), and it applies the V28 core cut line and supporting cut order.
2. The readiness fixes D1 to D57 (`readiness-fixes-2026-11-14.md`) and the Slack decisions S1 to S13 (`sprint-change-proposal-2026-11-14-slack.md`), wherever the discovery-agent proposal does not replace them.
3. The architecture spine's AD-14 table is the single reference for routes and shapes (D40). Where `epics.md` and AD-14 name a route body differently (for example `POST /runs { grant_id, set }`), AD-14 wins and the contract keeper settles it in A01.

Every PR below has an owner, its stories, a branch, what must be merged before it starts, what must be merged before it merges, the files it owns, the design reference for screens, and a forecast. Timing, the merge queue, milestones and fallback cuts are in `build-schedule.md`. The forecasts come from a model, not from a validated run; the milestones in `build-schedule.md` are how the day checks them.

## The two lanes

| | Luis | Vlad |
|---|---|---|
| Agents | Up to 44: builders, one reviewer agent per open PR, the contract keeper and the integrator | Up to 22, Sonnet 5.5 at high effort: builders and his coordinating agent |
| Model budget | Claude plan; the product runs on Luis's API keys (Anthropic, ElevenLabs, HeyGen, Voyage if cleared) | Claude Pro plus $300 of API credit |
| Owns | Contract, registry and exact name matching, grants and policies, deploy, discovery scan and prior collection, ledger, gate and claim checks, runs, stop and audit API, extraction, Slack notifier, the run, setup data and reset, read model and value review, retrieval and report assembly, memory, the report decision and task authorisation, follow-up task execution, both integrations, rehearsal; `docs/clearance.md` | The web skeleton, Run console, Audit view, report page with decisions and the memory panel, the ElevenLabs briefing, the HeyGen avatar video, the submission package |
| PRs | 17 (A01 to A10 with the bundles, A13, A14, A16, A19+A20, A21+A22, A24, A25) plus the integration PRs I1 and I3 (I3b is an optional part of I3) | 7 (B01, B02, B03, B04, B06, B07, B08) |
| Merge desk | Luis merges 12 PRs on desk L: 11 core and A25 (see `build-schedule.md`, merge queue) | Vlad merges his own 7 PRs after Luis's review agent passes each, and four of Luis's leaf PRs (A05, A13, A14, A09) only when each is already green in CI and passed by Luis's review agent and the contract keeper (lever L2, V31). His look is a scope and secrets check, not a back-end review. A failing CI or a conflict sends the PR back to its author |
| Shared task | R1: record the 60-second video and submit (with Vlad); then the reset for the live demo | R1 (with Luis) |

**Concurrency does not remove sequential work.** Forty-four agents shorten nothing on a dependency chain: A10 cannot be wired before the modules it calls exist, I1 cannot start before its PRs merge, and each merge still needs CI (about 10 minutes with a human look) and a person to press the button. More agents add review and merge load; they do not add merge desks. The plan therefore cuts merges (bundles), staggers finishes and adds a second merge desk under a proof step (V31), rather than adding builders.

PR counts are not workload: Luis's lane holds every core back-end behaviour and both integrations.

### Bundles and cuts (proposal section 7)

| Change | Effect |
|---|---|
| A23 (claim checks) folded into A06 | One gate PR |
| A18 (read model) folded into A14 | One read and value-review PR |
| A07 and A11 bundled | Runs, stop and the audit API in one PR |
| A19 and A20 bundled | Retrieval feeds the relationships and the report in one PR |
| A21 and A22 bundled | Memory store, retrieval and effect in one PR |
| A24 and A25 **split again** (V28) | A24 (report decision, promotion, task authorisation) is core; A25 (task execution) is supporting and the first substantial cut. Separate cards, branches and owned files, so A25 can be cut without touching the core |
| A12 (live feed), A15 (graph API), B05 (impact view), A17 (policy drafts) | **Cut.** Screens poll; the report's relationship list is the relationship view; policies stay hand-written (NFR15) |
| I2 (core acceptance) | **Folded** into the rehearsal's first pass (A16 pass 1 is core acceptance) |
| B04 report page | Two builders in Vlad's lane: the report body; decisions plus the memory panel |
| B06 ElevenLabs briefing | Supporting, behind the `briefing` flag; on demand from a "Generate briefing" button, never automatic (V29); drops out of the demo if not merged by 14:45 |
| B08 HeyGen avatar video | Supporting, behind the `avatar` flag (V13); on demand from a "Render avatar" button; for the demo, one render for the demo report only, requested as soon as it is filed (V29); never gates the report, Slack, the decision, the task or the rehearsal; built only if the 10:45 HeyGen account check passed; first in the supporting cut order |
| Old PR B05, old Story 9.10 audio page, `web/app/review/` | Gone. The report page replaces the Review page as the Slack link target |

## No prepared code or assets (D1)

| Rule | Detail |
|---|---|
| Code | No code from `scripts/data/` or from any `dxp-*` skill is copied into `backend/` or `web/`, and none is run on Saturday. Skills (including `dxp-heygen`, `dxp-elevenlabs`, `dxp-mongodb-atlas`) are reference documentation only (APIs, limits, gotchas). Every line of project code is written during the event |
| Trials | A05 fetches the prior collection and NCT05715229 by NCT ID, and the discovery scan queries the ClinicalTrials.gov API v2, all during the event |
| FDA list | A13 fetches the FDA list of cleared or approved companion diagnostics during the event and keeps the lung rows |
| Memory M1 | Created by Sam through the real UI during I1 setup (V15). Never seeded from a file |
| Briefing and avatar | Generated during the event, on demand, from a report's own fields. No audio or video clip is made beforehand |
| Prepared `data/` files | Not loaded unless an organiser clears them in writing on Saturday morning (open item OD4; Luis records the answer in `docs/clearance.md`). If cleared, A05 and A13 may load them instead of fetching |
| Logo | B01 uses a text wordmark, "DxP", in the interface font, unless an organiser clears the prepared logo |
| Accounts | The Slack webhook, and the ElevenLabs and HeyGen accounts if created before the event, are prepared accounts, listed in the README. Their keys live only in `.env` and the Modal secret |
| Disclosure | The README lists prepared material so judges can see it, not so agents can use it |

## Demo scenario (V1, V16, as amended by V25 to V37)

**Wording rule (V33, V37).** NCT04712877 lists "FoundationOne CDx" and "FoundationOne Liquid" only as alternate names (`otherNames`) of one generic intervention, "ctDNA, tumor NGS" (DIAGNOSTIC_TEST). Every report, alert, briefing, avatar script, acceptance criterion, demo note and narration calls them names **mentioned in the record** ("named in the record"), never assays the trial "uses" or "studies". Nothing says the trial studies FoundationOne Liquid CDx or shows any assay's performance. The FDA treats FoundationOne CDx (tissue) and FoundationOne Liquid CDx (plasma cfDNA) as separate devices, and no report merges them.

| | |
|---|---|
| Research scope | "Plasma ctDNA genotyping assays in NSCLC" (all stages, V25; `research_scopes`), owned by Team "Team Liquid Biopsy Dx" and named by the agent grant `lbdx@v1` for the agent `dxp-curator`. Its assays are the four exact strings of D45: "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx", "Agilent Resolution ctDx FIRST assay". Every other Diagnostic, the tissue test FoundationOne CDx among them, is out of scope |
| Already in Atlas before the run (setup, I1) | The FDA seed as accepted baseline knowledge; the prior collection (the D30 trials last updated before the cursor, fetched by NCT ID, extracted and filed in `baseline` mode) with embeddings; memory M1, created by Sam correcting the report on NCT05715229 ("Terminated trial with no posted results: describe its status; do not state outcomes"); the snapshot |
| Discovery anchor (V36, OD2) | `POST /runs { grant_id: "lbdx", set: "discover" }`. The scan (gated `search_source` to `source:clinicaltrials.gov`) returns the trials updated since the cursor. The demo anchor is whichever in-scope early-stage trial the live API actually returns as updated after the cursor chosen at 10:45, with its update date, status and results verified in the response. **NCT04712877 is the expected candidate only** (on 14 Nov the API returned `lastUpdatePostDate` 2026-11-12, RECRUITING, `hasResults` false; the record-history page showed 17 July 2024, so the date is unverified). If another trial is the anchor, the framing below follows V33 from its own fields |
| The signal (V33) | "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted." |
| Relate | Vector Search retrieves related prior evidence in the scope; each item gets `supports`, `contradicts`, `extends` or `new_question` with a checked quote from both sides, or "related (no relationship established)". Similarity is shown and never used as evidence |
| Remember | M1 is retrieved and its effect is shown: "Wording changed because of M1 (Sam, 14 Nov): states recruiting status, no results yet" |
| Uncertainties (V34, V37) | The intervention wording is kept verbatim ("ctDNA, tumor NGS"; other names "FoundationOne CDx", "FoundationOne Liquid"). The report states: "The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample." "FoundationOne Liquid" matches no seeded trade name exactly, so it stays as written and is listed: "The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated." It is never mapped to an approved product |
| The gap (V33) | "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?" |
| Allowed (V35) | The report files one pending knowledge update: add the anchor to the scope's evidence collection as an early-stage plasma-plus-tissue profiling study. No assay record is changed |
| Blocked (V35, V37) | **Guaranteed:** the record names "FoundationOne CDx" exactly. The agent proposes linking that mention to the Team's plasma research scope; check 2 blocks the link before it is filed, because the configured scope excludes the tissue assay. One blocked Decision is recorded, citing the mention and the scope rule. **If it occurs:** an unsupported performance or results claim in draft 1 (no memories), for example that the trial "showed" an assay detecting EGFR, is blocked before filing by `claim_performed_or_results` and shown; the model may not write it (V21). Draft 2 is filed |
| Report and Slack | One pending report; one Slack alert in `#all-mango-db-hackathon` whose "Review in DxP" link opens `${DXP_BASE_URL}/reports/<report_id>` and "Open diagnostic" opens `${DXP_BASE_URL}/diagnostics/<dx_id>` for the scope's accepted knowledge. Approval happens only in DxP (S4) |
| Brief (V29) | On demand only. The script, built only from the report's fields, is always shown as text. "Generate briefing" (`briefing` flag) and "Render avatar" (`avatar` flag) call ElevenLabs and HeyGen; for the demo, one avatar render is requested for the demo report as soon as it is filed. A failure says "unavailable" and the text stays correct. Nothing waits on either service |
| Decide (V27, V35) | Sam approves under `sam@v1`: the report's one update is applied through `ledger.apply` (the anchor accepted into the scope's evidence collection; no assay record changed) and one task is authorised under `task-<hex>@v1` to answer the gap: "Search ClinicalTrials.gov for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling, and report which have posted results (at most 5)." The page says: "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." **Approved is not accepted for the task** |
| Follow-up task (A25, supporting, I3b) | Only if A25 joins at the 14:30 gate: Sam presses "Run follow-up task"; the task runs under its own grant and gate, answers the gap ("None with posted results" is a valid, honest answer), and files its findings as pending related evidence; a sixth result or a step outside the scope is blocked. Otherwise the task is shown as "authorised, not run" |
| Stop | Shown honestly: on the follow-up task's run if I3b ran; otherwise on a second discover item with items remaining (that item is then not cut, V28) |
| Audit question | "What did the agent find, which memory changed its wording, what was blocked, and who authorised the follow-up?" |
| Longitudinal value (V32) | The narration states that the scope cursor and the Team's memories accumulate over time: the scan only looks at what changed since the last scan, and M1 came from a correction earlier in the day. The pitch names the bigger value from the original brief, team-specific, longitudinal intelligence on the diagnostics a team follows; the demo shows one turn of that loop |
| Pacing | `DXP_DEMO_PACE` (A10): one item at a time, a few seconds per item, the anchor first among the discovered items |

The demo order itself is in `build-schedule.md` ("Demo order") and in A16's `docs/demo-and-reset.md`.
| Reset (D34, D41, V15) | A13 owns `scripts/reset_demo.py` (`--snapshot` and restore) and the snapshot procedure. The snapshot is taken at the end of I1 setup, after M1 exists and before the discovery run. The reset restores it before A16 pass 1, before A16 pass 2, before the video and before the live demo. Smoke tests never touch the demo database: they run in `DXP_DB=dxp_smoke` |

## Contracts come first, and they cover more than API shapes

A01 and A02 start at 10:45 and merge by 11:55 (A01 at 11:45). A01 writes stubs only: every route returns 501 and every signature raises `NotImplementedError` until the PR named in the A01 card finishes it. Exceptions: `ledger.recover_applying()` and `retrieval.ensure_indexes()` are no-op stubs, because A01's startup hook calls them before their owners merge. Nothing calls the briefing or avatar functions automatically (V29), so they need no no-op stub.

The shapes are already written in AD-14 and in Epic 10 of `epics.md`; A01 codifies them, it does not invent them. That is what lets the two most stable long PRs, A06 and A08, draft against them from 10:45 (lever L1, V31), as A03 already does. A19+A20 and A21+A22 start after the contract, at 11:45. Each draft carries a 20-minute rebase budget after the freeze. After 11:45 a change to any of these goes through the contract keeper in its own PR, which states the rebase cost it imposes.

A01, A02 and A03 freeze:

- **Every route in the AD-14 table**, under `/api/v1`, registered once in `app.py` so no later PR edits it. Each route's status (core, supporting, cut, superseded, deferred) is stated only in AD-14 (D40); this plan names owners. Owners:
  - `GET /schema` (A01, the only route A01 finishes)
  - `GET /whoami`, `GET /grants`, `GET /grants/<grant_id>`, `GET /policies` (A03)
  - `POST /runs { grant_id, set }` with `set` = `discover`, `nct:<NCT ID>` (setup only) or `task:<task_id>`; `GET /runs`, `GET /runs/<run_id>`, `POST /runs/<run_id>/stop`, `GET /runs/<run_id>/audit`, `GET /decisions/<decision_id>`, `GET /actions`, `GET /actions/<action_id>` (A07+A11)
  - `POST /actions/<action_id>/resolve` (A09)
  - `GET /scopes`, `GET /scopes/<scope_id>` (A05)
  - `GET /reports?status=&run_id=`, `GET /reports/<report_id>` (A19+A20)
  - `POST /reports/<report_id>/decision { action: approve | reject, note, correction }`, `GET /tasks?report_id=`, `GET /tasks/<task_id>` (A24, all in `routes_report_decision.py`). A25 owns no route: a task runs through `POST /runs { set: "task:<task_id>" }` (A07+A11) and A10's handoff
  - `GET /memories?team_id=&status=`, `GET /memories/<memory_id>`, `POST /memories/<memory_id>/correct`, `POST /memories/<memory_id>/revoke` (A21+A22)
  - `GET /diagnostics/<dx_id>` (accepted knowledge), `POST /diagnostics/<dx_id>/values/<value_id>/review`, `GET /proposals?…&report_id=`, `GET /proposals/<p_id>` (A14)
  - `GET /teams` (A13)
  - `POST /reports/<report_id>/briefing` and `GET /reports/<report_id>/briefing` (B06), `POST /reports/<report_id>/avatar` and `GET /reports/<report_id>/avatar` (B08): on demand only (V29); each GET returns the grounded script as text whatever the media status
  - Registered and left 501: `POST /proposals/<p_id>/decision` (superseded by the report decision, V8), `GET /changes` and `GET /graph` (cut), `POST /policies/<policy_id>/approve` (cut), `GET /runs/<run_id>/audit/audio` (superseded), and every deferred route
- **One error shape** for every route: `{ error: { code, message } }`. A blocked action is not an error: it returns 200 with the `Decision`, creates one `decisions` document and one `action_blocked` event, and no `actions` document (D5).
- **The shapes** in `models.py`, exactly as AD-14, and the generated `web/lib/types.ts`: the D16 to D53 shapes (`Principal`, `Run` with `initiated_by` and `agent`, `Grant` with `kind` now also `task`, `Stamp`, `PolicySet`, `Admission`, `Decision`, `Action` with `result` and `resolution`, `Audit`, `Proposal` with `report_id` and read-time `notification`, `Record`, `Event`), plus the Epic 10 shapes `Scope`, `Report` (with `gap`, `uncertainties` and the record's `name_mentions`, V33, V37), `Relationship`, `Retrieval`, `MemoryUse`, `Memory`, `Task` (with `question`, the gap it answers, and `answer`, V26, V33) and `Media`. `Audit` gains the V14 sections (sources fetched with cursor, retrieval, memories used, relationships, report and task decisions, the task's run).
- **Action kinds** (AD-14): machine `search_source`, `file_proposal` (also at report level: filing a report is a report-level `file_proposal` in AD-14; one name, settled by V24), `file_related_evidence`, `notify_slack`, and seed `apply_value`; the on-demand external kinds `generate_briefing` and `generate_avatar_video`, Reviewer-initiated under `sam@v1` only (V29; the run never calls either service); human `decide_report`, `authorise_task`, `create_memory`, `correct_memory`, `revoke_memory`, `review_value`, `resolve_notification`. `decide_proposal` is superseded.
- **Display formats (D40):** grants as `{grant_id}@v{version}`; policy sets as `ps_ab12… (N policies)`; run, action, report and memory IDs as stored.
- **The `$jsonSchema` validators** for `grants`, `policies`, `policy_sets`, `runs`, `admissions`, `decisions`, `actions`, `research_scopes`, `reports` (relationships embedded as `related[]`, no separate collection), `memories`, `tasks` and `media`, all in `store/schemas/`, owned by A03; `store.ensure_indexes()` (A01) applies them at collection creation.
- **The frozen signatures** (AD-17 to AD-22 and the Epic 10 additions):
  - `resolve_actor(api_key) -> Principal` (A03); `gate.policy_sets.current_grant(grant_id)`, `current_set()` (A03).
  - `identity.derive()`, `normalise_name()`, `identity.resolve_exact(name)` (A02; exact FDA trade-name match after `normalise_name()`, or `None`; no hand-written aliases, V34).
  - `runs.start(caller, grant_id, set) -> Run`, `runs.context(run_id, key)`, `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle`, `runs.finish`, `runs.stop`, `runs.stamp` (A07+A11, unchanged from D22 to D24 and D43).
  - `gate.evaluate(ctx, action) -> Decision` (A06), five checks in order; check 4 now includes the claim checks (V7).
  - `ledger.file(finding_id, changes, mode, ctx)`, `ledger.apply(proposal_id)`, `ledger.recover_applying()` (A06).
  - `llm.extract(item)`, `llm.check(finding, source_text)`, `llm.call_structured(model, schema, messages)` (A08; `llm` stays the only Claude caller, AD-11).
  - `discovery.scan(scope_id, ctx) -> list[source_ref]` (A05).
  - `retrieval.ensure_indexes()`, `retrieval.embed()`, `retrieval.related(scope_id, text, k, exclude)`, `retrieval.memories(team_id, text, tags, k)` (A19+A20).
  - `reports.relate(new_item, related_item)`, `reports.draft(item, findings, related, memories)` (drafts with and without memories, so each memory's before-and-after effect is known), `reports.file(...)`, `reports.add_related(report_id, refs, ctx)` (A19+A20); `reports.decide(report_id, action, note, correction, reviewer)`, `reports.recover_accepting()` (A24).
  - `memory.create`, `memory.correct`, `memory.revoke`, `memory.retrieve(team_id, text, tags)` (A21+A22).
  - `tasks.authorise(report_id, reviewer) -> Task`, `gate.grants.issue_task_grant()` (A24); `tasks.run(task_id)` (A25, called only by A10 for a `task:` run).
  - `actions.dispatch`, `actions.mark_unknown`, `actions.mark_failed`, `actions.resolve` (A09).
  - `pipeline.run(run_id)` (A10).
  - `briefing.script_for(report) -> str`, `briefing.generate(report_id, ctx)` (B06); `briefing.render_avatar(report_id, ctx)`, `briefing.avatar_status(report_id)` (B08). Called only from their own routes, on demand (V29).
- **Import rule (AD-28):** `gate`, `runs` and `actions` import nothing from `memory`, `retrieval` or `reports`. A memory informs a draft; it never reaches a grant, a policy or a check.

## Required acceptance behaviours

These six are binding on Stories 9.3 to 9.6 and on every Epic 10 story that acts (D4 to D7, refined by D16 to D25, with Slack per S7 to S9 and one alert per report per V11). Each card restates the ones that apply to it, and the reviewer agent checks them.

| Concern | Required behaviour |
|---|---|
| Ambiguous external result | Save the action ID in Atlas first and put it in the alert's header. HTTP 200 with body `ok` is `delivered`; another 4xx is `failed`, never retried; a 429 is retried once after `Retry-After` while still holding the claim, and a second 429 is `failed`; a timeout, connection error or 5xx is `unknown`, never retried, and a Reviewer resolves it through `POST /actions/<action_id>/resolve` (S7, S8). Every status update is conditional on the current status (D24). ElevenLabs and HeyGen calls record their own result the same way, and a failure never blocks the report |
| Concurrent retries | Claim the action atomically (`queued` to `dispatching`, conditional update), so two workers never both dispatch it |
| Stop semantics | Check 5 means the action holds an `admitted` admission for this run and the run is not `stopped`; one admission per action (D22); admit only while `running`, in one transaction; release once; the background sweep settles abandoned actions (D23, D24, D43). Stop works the same on a discover run and on a task's run |
| Blocked action | One `decisions` document records every check, the grant evaluated, the policy-set version and, for a claim check, the failed claim policy; one `action_blocked` event carries its `decision_id`. No action, no report, no proposal, no record change, no external call |
| Authority | The caller is resolved server-side from `X-DxP-Key` (D17). A run records `initiated_by` and `agent`; a task's run carries its own task grant. Reviewer decisions carry `run_id: null`, `agent: null`, the Reviewer stamp, a `request_id` and a `cause`. A memory never changes a grant, a policy or a gate outcome. A client-supplied name never confers permission |
| Audit reconstruction | Every gate evaluation is a Decision with inputs, evidence reference, checks, grant, policy-set version, outcome, timestamps and `seq` (D21). The run audit also shows the sources fetched with the cursor, the retrieval (method, top-k, scores), the memories used with their effect, the relationship labels with both quotes, the Slack result, the report decision, the task authorisation and a link to the task's run (V14). "Who authorised" is the Decision's `authorised_by` |

## Start requirements and merge requirements are separate

Each card says two things:

- **Start when merged:** what must be on `main` before the agent starts. For most PRs this is only A01. Two long PRs (A06, A08) start at 10:45 as drafts against the shapes in AD-14 and Epic 10, as A03 does, and rebase on A01 at 11:45 inside a 20-minute budget (lever L1, V31).

- **Merge after:** what must be on `main` before this PR merges, because it calls real code or another PR's file.

A PR that calls a module not yet merged builds against the frozen signature and is proved against the real module in I1 or I3.

## Integration and acceptance checks

| Check | PR | When | Needs merged | What runs |
|---|---|---|---|---|
| Setup, step 1: data | I1 | 13:35 to 14:05 (data 13:35 to 13:55; embeddings and indexes 13:55 to 14:05, once A19+A20 is in) | A03, A04, A05, A06, A08, A13; A19+A20 for the indexes | On the sandbox, in the spine's setup order (`docs/demo-and-reset.md` records it): `python -m dxp.gate.seed` (grants, policies including the three claim policies, and the research scope with the cursor chosen at 10:45, OD2); `python -m dxp.sources.fda_cdx` then `python -m dxp.ledger.seed` (FDA rows, aliases, Teams); `python -m dxp.pipeline.prior` (A05: fetches the prior collection by NCT ID, through `python -m dxp.sources.load --set prior --scope <scope_id>`, then extracts and files it in `baseline` mode under `seed@v1`); `retrieval.ensure_indexes()` (embeddings by the `DXP_EMBEDDING` path and the vector and text indexes), waiting until every index is queryable (OD1; else `DXP_EMBEDDING=none` and text search, labelled honestly) |
| Setup, step 2: M1 and the snapshot | I1 | 14:05 to 14:20 | everything in step 1, plus A07+A11, A09, A10, A21+A22, A24 and B04 deployed | `POST /runs { grant_id: "lbdx", set: "nct:NCT05715229" }`; its report is filed and alerted; Sam opens the report through the deployed report page and chooses "Reject" with the note "Terminated trial with no posted results: describe its status; do not state outcomes", which creates M1 through `create_memory`; M1 is listed with author Sam and its source decision; then `scripts/reset_demo.py --snapshot` (`mongodump` of `dxp`, OD6). If B04 is not deployed, step 2 waits for it: M1 must come from the real UI (V15) |
| The discovery loop | I1 | 14:20 to 14:45 (first green pass forecast 14:35) | as step 2 | `POST /runs { set: "discover" }` on the snapshot. **Assertions (V35, V37):** the scan returns the anchor verified at 10:45 (expected NCT04712877), with its update date after the cursor, status and results as in the live response; the record's names are stored as mentions (`name_mentions`: "FoundationOne CDx" resolves exactly to the seeded tissue test; "FoundationOne Liquid" resolves to nothing and stays as written); the proposed link of the "FoundationOne CDx" mention to the plasma scope is blocked by check 2 before filing, with one blocked Decision citing the mention and the scope rule (guaranteed); if draft 1 writes an unsupported performance or results claim, its blocked Decision naming `claim_performed_or_results` is recorded (not required, V21); draft 2 is filed as one pending report whose only knowledge update adds the anchor to the scope's evidence collection (no assay record change); the report keeps the intervention wording verbatim, lists the ambiguous intervention field and the unresolved "FoundationOne Liquid" under uncertainties, names the gap, and contains no "uses", "studies", "showed" or performance wording about either name; related evidence carries labels, both quotes, similarity and method; M1 is in "memories used" with its before-and-after effect taken from the two gated drafts; exactly one Slack alert is `delivered`, its text follows the same wording rule, its "Review in DxP" link opens the report on the deployed app and "Open diagnostic" opens the accepted knowledge view; the audit reconstructs all of it (V14) |
| Approval, promotion, authorisation and audit | I3 | 14:45 to 15:00 | I1 green (A24 and B04 are already in) | Sam approves the anchor's report in the report page: the one update applied once through `ledger.apply`; the report `accepted`; the anchor accepted into the scope's evidence collection, with no assay record changed; one task authorised under `task-<hex>@v1` with the gap as its `question`; the page, the Audit view and the narration say "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review" (V27); the run audit shows the decision and who authorised the task. Also checks "Approve with correction" creates a memory, and S3 (memory correct and revoke) inside the slot; the 15:00 reset restores M1 |
| Follow-up task execution (optional) | I3b | 15:00 to 15:15, only if A25 is merged by 14:30 and the loop is green by 14:30 | I3, A25, flag `task_run` on | Sam presses "Run follow-up task": `POST /runs { grant_id: "task-<hex>", set: "task:<task_id>" }` with `initiated_by: sam`; the run passes its own gate; it searches for early-stage NSCLC trials combining ctDNA or plasma testing with tissue profiling and records which have posted results (at most 5; "None with posted results" is valid); its findings are filed as pending related evidence, never accepted; a sixth result is blocked; the run audit links the task's run. It uses 15 of the 20 minutes of hard float; if the gate is missed, A25 is cut |
| Core acceptance | A16 pass 1 | 15:10 to 15:35 after the 15:00 reset (15:25 to 15:50 if I3b ran) | I3 | The full demo order (`build-schedule.md`) through the screens, from the reset sandbox with `DXP_DEMO_PACE` set. This is the former I2 (cut 1) |

Supporting items each have their own check, run by the integrator. An item joins the rehearsal only if its check passed. None of them blocks I1, I3 or A16.

| Check | Items | Needs | By | Passes when | If it fails or is late |
|---|---|---|---|---|---|
| S1 briefing | B06 | B06 merged by 14:45, a filed report | 15:00 | "Generate briefing" produces a ten-second briefing whose script, always shown as text, contains only facts from the report's fields and follows the mention wording (V37); a missing key or a failure says "unavailable" and the text stays | Flag `briefing` off; the player is hidden; nothing else changes |
| S2 avatar video | B08 | B08 merged by 15:00, B06 merged (the shared script), a filed report | 15:10 (before A16 pass 1) | A render requested from "Render avatar" for the demo report reaches `ready` and plays; a failed or slow render shows "Rendering" then "unavailable", the script stays as text, and nothing waits | Flag `avatar` off; the player is hidden |
| S3 memory correct and revoke | A21+A22 routes, B04 memory panel | I3 | 15:00 (inside the I3 slot) | Correcting M1 writes a new version that supersedes it; revoking it removes its effect from the next report; grants, policies and gate outcomes unchanged | The memory panel's Correct and Revoke controls are hidden; memory creation and use stay |

The feature flags live in B01's `web/lib/features.ts`, read from `NEXT_PUBLIC_DXP_FEATURES` (`briefing`, `avatar`, `memory_edit`, `task_run`). Turning a flag off needs no code change.

**The core cut line (V28).** Core, never cut: discovery; an evidence relationship with quotes; a memory changing the report; a policy block; the Slack notification opening the report; the human decision (approve with promotion, or reject or correct with a memory); the audit trail; stop. Core, but cheap: the recommended task and its authorisation, a record created at approval (A24). **Only these supporting items may be cut, in this order:** (1) B08, the HeyGen avatar; (2) B06, the ElevenLabs briefing; (3) the memory correct and revoke screen; (4) follow-up task execution (A25), the first substantial cut; (5) a second discovery item, only while A25 is in, because stop needs a run with items remaining. No core PR is replaced by a stub, in I1 or in the demo (D37, NFR5).

## How agent slots are used

The forecast is about 9 builders in Luis's lane from 10:45 (A01, A02, A03, three on A06, two on A08, A04 from 11:00) rising to about 30 from 11:45, plus one reviewer agent per open PR (about 10 at the peak), the contract keeper and the integrator: about 42 of Luis's 44. Vlad's lane peaks at about 13 builders (two on B04, two each on B02, B03, B06 and B08, one on B07) plus his coordinating agent, within his 22.

- A06 gets three builders (gate and decisions, `ledger/apply.py`, `gate/claims.py`); A19+A20 three (retrieval and indexes, relationships, report assembly); A08, A21+A22, A24, A25, A07+A11, A09, A10, A13 and A14 two each (one writing the tests).
- One independent reviewer agent per open PR checks acceptance criteria, the required behaviours, D1 (no prepared code), owned files only, secrets, `.env` values, tokens and PubMed text.
- The contract keeper rejects any PR that changes a frozen contract without regenerating the types, at 11:45 posts the A01 diff that the A06 and A08 drafts rebase on, passes each PR merged on desk V, and states the rebase cost of any contract change after 11:45.
- The integrator runs I1, I3, I3b and S1 to S3, and from 13:35 keeps a smoke test green on every merge: one discover run over a fake source with one blocked claim, one report, one alert through the fake Slack sender (merges post nothing to the channel), one memory, one audit read. It runs in `DXP_DB=dxp_smoke`, never in `dxp` (D41).

People spend their attention on unclear behaviour, failures and merges, not on reading every diff.

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox. A merged PR that has not passed I1, I3, I3b (for A25), A16 pass 1 or its own S check is not done.

## How to brief an agent for one PR

Give each agent one PR ID and this brief, filled in from its card:

```
You are building PR <ID> of DxP: <What>.
Read first: _bmad-output/planning-artifacts/development-plan.md (card <ID>,
"No prepared code or assets" and "Required acceptance behaviours"),
sprint-change-proposal-2026-11-14-discovery-agent.md (the V decisions the
card cites; V25 to V37 win over V1 to V24), readiness-fixes-2026-11-14.md, the acceptance criteria of
Story <n.n> in epics.md, the architecture spine (AD rules it cites; the
AD-14 table wins on routes and shapes), and for screens DESIGN.md and
EXPERIENCE.md. There are no mockups: every screen is built during the event.
Write every line of code yourself during the event. Do not copy, import
or run code from scripts/data/ or from any dxp-* skill; skills are
reference documentation only. Do not load files from data/ or use the
prepared logo unless the plan records that an organiser cleared them.
Branch: <branch>, from the latest main. Start only when every PR under
"Start when merged" is on main (only A06 and A08 start at 10:45 as drafts
against the shapes in AD-14 and Epic 10, then rebase on A01 at 11:45
within 20 minutes). Code against
the frozen contracts and signatures for anything not merged yet. Only edit
the files this PR owns; a change in another PR's file goes in a separate
small PR that the file's owner reviews. Do not merge until every PR under
"Merge after" is on main. Build and test against the Atlas Sandbox, in
your own test database, never in dxp.
Never commit secrets, tokens or .env values (Slack webhook, Anthropic,
ElevenLabs, HeyGen, Voyage keys). Never write PubMed abstract text to any
file. Open the PR as "Story <n.n>: <What> (<ID>)" with the acceptance
criteria and required behaviours as a checklist, and follow the PR and
merge steps in epics.md.
```

The PR title format above is the only one (D40). A fix PR found during I1, I3 or A16 uses it too, with the story and ID of the PR that owns the file: "Story <n.n>: Fix <what> (<owner ID>)". A bundle is titled after its first story and lists every story it carries.

Tests: each PR's back-end tests live in `backend/tests/<id>/` (for example `backend/tests/a06/`, `backend/tests/a19_a20/`), owned by that PR; `backend/tests/conftest.py` is A01's (D36).

## Luis's PRs

Times are forecasts: "Ready" is when the PR is reviewed and green; "Merged" is its slot in the merge queue (`build-schedule.md`). Desk L is Luis's merge desk; desk V is Vlad's.

| PR | Stories | What | Branch | Start when merged | Merge after | Start | Ready | Merged (desk) |
|---|---|---|---|---|---|---|---|---|
| A01 | 1.1, 9.1 | Contract: routes, shapes, error shape, frozen signatures, Epic 10 shapes; stubs only | `story/1.1-contract` | none | none | 10:45 | 11:35 | 11:45 (L) |
| A02 | 1.2 | Registry, identity and exact trade-name matching (no hand-written aliases, V34) | `story/1.2a-registry-identity` | none | none | 10:45 | 11:45 | 11:55 (L) |
| A03 | 9.2 | Grants (`lbdx@v1` with the scope, `sam@v1`, `seed@v1`, task grant kind), hand-written policies including the three claim policies, policy sets, validators, server-side actor resolution | `story/9.2-grants-policies` | none (drafts against A01) | A01 | 10:45 | 12:10 | 12:30 (L) |
| A04 | 8.1 | CI, Vercel and Modal deploy on the sandbox; every secret of the Modal secret set by hand, including `ELEVENLABS_API_KEY` and `HEYGEN_API_KEY` | `story/8.1-deploy-sandbox` | none | A01, B01 | 11:00 | 12:00 | 12:20 (L) |
| A05 | 10.1, 1.4 | Discovery scan, research scope and cursor; the ClinicalTrials.gov client; prior collection and setup item by NCT ID | `story/10.1-discovery-scan` | A01 | none (fake gate) | 11:45 | 12:55 | 13:05 (V, proof merge 1) |
| A06 | 1.6, 9.3, 10.7 | Ledger with the policy gate before every write, decisions, apply and recovery, and the claim checks in check 4 (A23 folded in) | `story/9.3-policy-gate` | none (draft from 10:45, L1) | A01, A02, A03 | 10:45 | 12:55 | 13:05 (L) |
| A24 | 10.8 | Report decision, promotion and task authorisation (core) | `story/10.8-approve-task` | A01 | A06 | 11:45 | 13:00 | 13:15 (L) |
| A07+A11 | 9.1, 9.5, 9.6 | Runs (`discover`, `nct:`, `task:` sets), admissions, stop and sweep; audit API with the V14 additions | `story/9.5-runs-stop` | A01 | A03 | 11:45 | 13:00 | 13:25 (L) |
| A13 | 1.2 | FDA fetch and seed; `scripts/reset_demo.py` with `--snapshot` (taken after M1 exists) and restore | `story/1.2b-seed` | A01, A02 | none (fake gate, D38) | 11:45 | 13:15 | 13:25 (V, proof merge 2) |
| A08 | 1.5 | Extraction with quote and support checks, exact trade-name matching only (V34); the `llm` client | `story/1.5-extraction` | none (draft from 10:45, L1) | A01, A05 | 10:45 | 13:10 | 13:35 (L) |
| A14 | 1.1, 1.3, 2.2, 2.3 | Read model and the accepted knowledge route, proposals read routes, value review (A18 folded in) | `story/2.3-proposals-decisions` | A01 | A06 | 11:45 | 13:15 | 13:35 (V) |
| A10 | 1.7 | The run: scan, extract, retrieve, relate, remember, draft, gate, file, notify | `story/1.7-run` | A01 | none | 11:45 | 13:30 | 13:45 (L) |
| A09 | 9.4 | Slack notifier, one alert per report, links to the report page | `story/9.4-slack-notify` | A01 | A03 | 11:45 | 13:30 | 13:45 (V) |
| A19+A20 | 10.2, 10.3, 10.4 | Embeddings, vector and text indexes, related retrieval; relationship classification with quotes from both sides; report assembly (gap, uncertainties, name mentions) and filing | `story/10.2-retrieval-report` | A01 (starts after the contract, V31) | A01, A06 | 11:45 | 13:45 | 13:55 (L) |
| A21+A22 | 10.5, 10.6 | Reviewer memory: create, correct, revoke, retrieval and visible effect | `story/10.5-memory` | A01 (starts after the contract, V31) | A01, A19+A20 | 11:45 | 13:45 | 14:05 (L, last core merge) |
| A25 | 10.9 | Follow-up task execution (supporting, first substantial cut) | `story/10.9-task-run` | A01 | A24, A07+A11, A19+A20 | 11:45 | 13:00 | 14:15 (L; must be merged by 14:30 to join I3b) |
| I1 | 10.1, 10.4, 10.5, 10.6, 10.7, 9.4 | Integration: setup (data, M1 through the UI, snapshot), then the discovery loop | `integration/i1-discovery-loop` | step 1: A03, A04, A05, A06, A08, A13 (A19+A20 for the indexes); step 2 and loop: all core above and B04 | none | 13:35 | 14:45 | 14:45 (L) |
| I3 | 10.8, 10.10 (and 10.9 in I3b) | Integration: approval, promotion, task authorisation and audit; optional I3b, task execution | `integration/i3-approve-task` | I1 | none | 14:45 | 15:00 (15:15 with I3b) | 15:00 (L) |
| A16 | 8.2 | Rehearsal: pass 1 is core acceptance, pass 2, each from a reset; then the reset for the video | `story/8.2-rehearsal` | I3 | none | 15:00 (15:15 with I3b) | 16:10 (16:25 with I3b) | 16:10 (L) |

Cut: A12, A15, A17 (section 7, cut 3). Folded: A18 into A14, A23 into A06, I2 into A16 pass 1. Split again: A24 and A25 (V28).

**Float (V30, V36).** With these merges the rehearsal ends at 16:10, which leaves **20 minutes of hard float at the 16:30 freeze**, the only float figure in the plan (15 of them used if I3b runs). It is a forecast, conditional on the merge milestones, including the L2 proof at 12:30 and the 13:00 desk decision; otherwise the emergency path in `build-schedule.md` applies: one desk, the V28 cut line (A25, B06 and B08 out), one rehearsal pass and no float.

## Vlad's PRs

Vlad's lane runs at 1.25 times Luis's cycle times (Sonnet 5.5 at high effort).

| PR | Stories | What | Branch | Start when merged | Merge after | Start | Ready | Merged (desk V) |
|---|---|---|---|---|---|---|---|---|
| B01 | 1.12 | Web skeleton, minimal shell, text wordmark, feature flags, the player stubs | `story/1.12-web-shell` | none | none | 10:45 | 12:00 | 12:10 |
| B04 | 10.10, 1.3, 2.4 | Report page (two builders: report body; decisions and the memory panel), pending reports list, accepted knowledge view | `story/10.10-report-page` | B01 | A01 | 12:10 | 13:45 | 13:55 |
| B07 | 8.3, 8.4 | README, submission text, 60-second video script (V17) | `story/8.3-submission` | none | none | 12:45 | 14:00 | 14:10 |
| B02 | 9.7, 10.1, 10.9 | Run console for discover and task runs | `story/9.7-run-console` | B01 | A01 | 12:10 | 14:15 | 14:25 |
| B06 | 10.11 | Ten-second ElevenLabs briefing, on demand (`briefing` flag) | `story/10.11-briefing` | B01 | A01, A19+A20 | 12:30 | 14:25 | 14:35 (must merge by 14:45) |
| B03 | 9.8, V14 | Audit view with the V14 additions | `story/9.8-audit-view` | B01 | A01 | 12:10 | 14:35 | 14:45 |
| B08 | 10.12 | HeyGen avatar video from the same grounded script, on demand (`avatar` flag); built only if the 10:45 account check passed | `story/10.12-heygen-avatar` | B01 | A01, A19+A20, B06 | 12:30 | 14:45 | 14:55 (must merge by 15:00) |

Vlad's desk also merges A05 (13:05) and A13 (13:25), the two timed proof merges of lever L2, then A14 (13:35) and A09 (13:45) from Luis's lane, each only when already green in CI and passed by Luis's review agent and the contract keeper (V31).


## Shared task

| Task | Story | What | Owners | Needs | Start | Finish |
|---|---|---|---|---|---|---|
| R1 | 8.4 | Record the 60-second video from B07's script (V17) on the sandbox reset at the end of A16; submit the description, public repository, video and team members; add the video link to the README; then reset the sandbox for the live demo with A13's `scripts/reset_demo.py` (16:55 to 17:10) | Luis and Vlad | A16 (including the video reset), B07 | 16:30 | 16:55 (reset done 17:10) |

## PR cards

### A01: Contract

- **Owner:** Luis · **Stories:** 1.1, 9.1 · **Branch:** `story/1.1-contract` · **Forecast:** 10:45 to 11:35, merged 11:45 · **Critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Stubs only, codifying AD-14 and Epic 10 (nothing invented). Create the `backend/` package with `uv`; `create_app(run_function)` in `api/app.py` with every route of "Contracts come first" registered and returning 501 (except `GET /schema`), allowed origins from `DXP_ALLOWED_ORIGINS`, and a startup hook calling `ledger.recover_applying()` and `retrieval.ensure_indexes()` (both no-op stubs until A06 and A19+A20); the error shape; `models.py` with every shape, including `Scope`, `Report` (with `gap`, `uncertainties`, `name_mentions`), `Relationship`, `Retrieval`, `MemoryUse`, `Memory`, `Task` (with `question` and `answer`), `Media` and the V14 `Audit` sections; the `store` module with `ensure_indexes()` (regular indexes for every collection, `admissions` unique on `(run_id, item_key)`, `memories` unique on `(memory_id, version)`, applying A03's validators) and `emit_event()`; the frozen signature stubs listed above (the briefing and avatar functions are called only by their own on-demand routes, V29, so they need no no-op stub); `tools/gen_types.sh`; every backend dependency in `pyproject.toml` up front (FastAPI, PyMongo, Anthropic, LangGraph, httpx, Modal, ElevenLabs, voyageai, pytest), so no later PR edits it or `uv.lock`; `backend/tests/conftest.py` (sandbox connection, a fresh test database per session, fake keys, a fake gate, a fake Slack sender hook, fake ElevenLabs and HeyGen hooks); `.env.example` naming every variable with no values: `MONGODB_URI`, `DXP_DB`; `ANTHROPIC_API_KEY`; `DXP_API_KEY`, `DXP_AGENT_KEY`, `DXP_SEED_KEY`; `SLACK_WEBHOOK_URL`, `DXP_BASE_URL`, `DXP_ALLOWED_ORIGINS`, `DXP_DEMO_PACE`; `DXP_EMBEDDING`, `VOYAGE_API_KEY`; `ELEVENLABS_API_KEY`; `HEYGEN_API_KEY`; `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_DXP_FEATURES`; `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`. Credentials never get example values. `DXP_FEED` is dropped (A12 cut). After A01 merges, each stub belongs to the card that finishes it:

  | Stub | Finished by |
  |---|---|
  | `GET /schema` | A01 |
  | `routes_grants.py`, `api/auth.py`, `gate/policy_sets.py`, `store/schemas/` | A03 |
  | `routes_scopes.py`; `discovery/scan.py`; `sources/ctgov.py`, `sources/load.py`; `pipeline/prior.py` | A05 |
  | `gate/__init__.py`, `gate/checks.py`, `gate/claims.py`, `gate/decisions.py`; `ledger/__init__.py`, `ledger/file.py`, `ledger/types.py`, `ledger/apply.py` | A06 |
  | `routes_runs.py`, `routes_audit.py`, `routes_actions.py`; `runs/`; `search/audit.py` | A07+A11 |
  | `llm/` (except the A19+A20 files); `evidence/` | A08 |
  | `actions/`; `routes_resolve.py` | A09 |
  | `pipeline/` (except `prior.py`) | A10 |
  | `routes_teams.py`; `sources/fda_cdx.py`; `ledger/seed.py` | A13 |
  | `routes_diagnostics.py`, `routes_proposals.py`, `routes_review.py`; `search/readmodel.py`; `ledger/review.py` | A14 |
  | `retrieval/embed.py`, `indexes.py`, `related.py`; `reports/relate.py`, `draft.py`, `file.py`; `routes_reports.py` | A19+A20 |
  | `memory/store.py`, `memory/retrieve.py`; `routes_memories.py` | A21+A22 |
  | `reports/decide.py`; `tasks/authorise.py`; `gate/grants.py`; `routes_report_decision.py` | A24 |
  | `tasks/run.py` | A25 (supporting; stays a stub if cut, and nothing calls it while flag `task_run` is off) |
  | `briefing/script.py`, `briefing/audio.py`; `routes_briefing.py` | B06 (supporting; stays a stub and 501 if cut) |
  | `briefing/avatar.py`; `routes_avatar.py` | B08 (supporting; stays a stub and 501 if cut) |

- **Files this PR owns:** `backend/pyproject.toml`, `backend/uv.lock`, `backend/tests/conftest.py`, `.env.example`, `backend/dxp/api/app.py`, `backend/dxp/api/models.py`, `backend/dxp/store/` (except `store/schemas/`), the package `__init__.py` files no other card owns (`backend/dxp/`, `api/`, `search/`, `sources/`, `schema/`, `discovery/`, `retrieval/`, `reports/`, `memory/`, `tasks/`, `briefing/`), `tools/gen_types.sh`, `web/lib/types.ts`. It creates the stub files above and hands each to its finishing card at merge.
- **Slack contract (S1 to S10, V11):** kinds `notify_slack` and `resolve_notification`; one `notify_slack` action per report; Action statuses and `result { http_status, response_body, posted_at, link_urls { report_url, diagnostic_url } }`, with `report_url` = `${DXP_BASE_URL}/reports/<report_id>`; the resolve route. Nothing names GitHub.
- **Done when:** the Story 1.1 and 9.1 contract criteria pass, `/openapi.json` lists every route above, `tools/gen_types.sh` regenerates `types.ts` cleanly, and the PR is merged. The contract keeper posts the diff for the draft PRs.

### A02: Registry and identity

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2a-registry-identity` · **Forecast:** 10:45 to 11:45, merged 11:55 · **Critical**
- **Start when merged:** nothing · **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `schema/registry.py`, `identity.derive()`, `identity.normalise_name()` (removes "®" and folds case, D45), and `identity.resolve_exact(name)`: a name resolves to a seeded Diagnostic only if it equals an FDA trade name exactly after `normalise_name()`; otherwise it returns `None`. **No hand-written aliases (V34):** the D31 aliases "FoundationOne Liquid" → FoundationOne Liquid CDx, "Guardant360" → Guardant360 CDx and "FoundationOne" → FoundationOne CDx are removed, and there is no `identity/aliases.py`. An unresolved name stays as it appears in the source and goes into the report's uncertainties (A19+A20); it is never mapped to an approved product. A03 derives the scope's `dx_id`s from the four exact D45 strings; A05 builds the scan's `query.term` from the scope's assay names and the condition only.
- **Files this PR owns:** `backend/dxp/schema/registry.py`, `backend/dxp/identity/` (including `__init__.py`), `backend/tests/a02/`
- **Done when:** the Story 1.2 registry and identity criteria pass; tests show "FoundationOne CDx" resolves exactly to the tissue Diagnostic, "FoundationOne Liquid CDx" to the plasma Diagnostic, and "FoundationOne Liquid", "Guardant360" and "FoundationOne" resolve to nothing (V34, V37); the PR is merged.

### A03: Grants and policies

- **Owner:** Luis · **Story:** 9.2 · **Branch:** `story/9.2-grants-policies` · **Forecast:** 10:45 to 12:10, merged 12:30
- **Start when merged:** nothing: drafts against the A01 shapes from 10:45 · **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** The `$jsonSchema` validators for every collection named in "Contracts come first", including `memories` (status `active | corrected | revoked`, `version`, `supersedes`), `tasks` and grants of kind `task`; the grant validator rejects `scope: { all: true }` unless the principal is `seed` (D16). `gate/policy_sets.py` (latest version first, then status, D6). **Keys (D48):** at 10:45 A03 generates `DXP_AGENT_KEY`, `DXP_API_KEY` and `DXP_SEED_KEY` locally into Luis's `.env`; nothing is committed. `python -m dxp.gate.seed`, from the command line with `DXP_SEED_KEY`, reading hand-written documents in `gate/seed_data/`, seeds:
  - **Agent grant `lbdx@v1`** (Team "Team Liquid Biopsy Dx"): principal `dxp-curator`, kind `agent`, `scope_id` of the research scope and `scope.diagnostic_ids` = the four D45 trade names derived with A02's `identity`; actions `search_source`, `file_proposal` (also gating a report as a whole), `notify_slack`; destinations `source:clinicaltrials.gov`, `ledger`, `slack:#all-mango-db-hackathon`; `startable_by: [sam]`; an expiry. The media kinds are not on this grant: the run never calls ElevenLabs or HeyGen (V29).
  - **Reviewer grant `sam@v1`:** principal `sam` (`DXP_API_KEY`), kind `person`, actions `decide_report`, `authorise_task`, `create_memory`, `correct_memory`, `revoke_memory`, `review_value`, `resolve_notification`, `generate_briefing`, `generate_avatar_video`; destinations `ledger`, `tts:elevenlabs`, `video:heygen` (the two media kinds on demand, V29; on the grant whether or not their flags are on); the same `diagnostic_ids` and `scope_id`.
  - **Seed grant `seed@v1`:** principal `seed`, kind `seed`, action `apply_value`, destination `ledger`, scope `{ all: true }`.
  - **Research scope (V1, V25):** the `research_scopes` document "Plasma ctDNA genotyping assays in NSCLC" (all stages), hand-written in `gate/seed_data/` with the cursor Luis chose at 10:45 (OD2, V36) and a rule excluding every Diagnostic outside the four plasma assays (so a link to the tissue test FoundationOne CDx fails check 2, V35); A05 reads it and advances its cursor.
  - **Policies:** the existing evidence policies (`requires` limited to `quote_found`, `supported`, `min_confidence`) and the three hand-written claim policies of V7, `claim_performed_or_results`, `claim_planned`, `claim_preclinical`, each versioned and in the policy set. Task grants are not seeded: A24 inserts each one at approval, and this validator accepts it.

  `resolve_actor(api_key)` by `key_hash` across all grant versions, 401 only for an unknown key (D17); `GET /whoami` with the caller's current actions (D53); `GET /grants`, `GET /grants/<grant_id>` (with `team_name` and the scope title, so the Run console labels the grant), `GET /policies?status=`.
- **Required behaviour (Authority):** the caller is resolved server-side; a revoked key still resolves and the gate blocks it.
- **Files this PR owns:** `backend/dxp/gate/policy_sets.py`, `backend/dxp/gate/seed.py`, `backend/dxp/gate/seed_data/`, `backend/dxp/store/schemas/`, `backend/dxp/api/auth.py`, `backend/dxp/api/routes_grants.py`, `backend/tests/a03/`
- **Done when:** the Story 9.2 criteria pass; each validator rejects a bad document; a newer `revoked` grant version blocks; a task grant validates; the three claim policies are in the current set; the PR is merged. The seed runs on the sandbox in I1 step 1.

### A04: Deploy on the Atlas Sandbox

- **Owner:** Luis · **Story:** 8.1 · **Branch:** `story/8.1-deploy-sandbox` · **Forecast:** 11:00 to 12:00, merged 12:20
- **Start when merged:** nothing: starts on the bare package and CI · **Merge after:** A01 and B01 (D39)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Deploy configuration only; edits no API file and not the README (D36). GitHub Actions on every pull request; Vercel previews and production from `main`; `backend/modal_app.py` (wraps `pipeline.run` with a 3600-second timeout, passes it to `create_app()`, mounts the ASGI app); `modal deploy` against the sandbox. **Secrets (D48, V12, V13), set by hand from Luis's `.env`, never in a file:** Vercel gets `DXP_API_KEY` and `NEXT_PUBLIC_API_URL`; the Modal secret gets `DXP_AGENT_KEY`, `SLACK_WEBHOOK_URL`, `ANTHROPIC_API_KEY`, `MONGODB_URI`, `DXP_BASE_URL`, `DXP_ALLOWED_ORIGINS`, `DXP_EMBEDDING`, `ELEVENLABS_API_KEY` (OD3), `HEYGEN_API_KEY` (OD7) and `VOYAGE_API_KEY` only if cleared (OD1). `DXP_BASE_URL` is the Vercel production URL; once B04 is deployed, confirm `${DXP_BASE_URL}/reports/<report_id>` and `${DXP_BASE_URL}/diagnostics/<dx_id>` resolve (the integrator repeats this in I1). Record in `docs/deploy.md` the sandbox checks: Vector Search and Automated Embedding available or not (OD1), `mongodump` and `mongorestore` work against the sandbox (OD6); change streams are no longer checked (OD5 closed). `docs/deploy.md` names each variable, never its value.
- **Files this PR owns:** `backend/modal_app.py`, `.github/workflows/`, `web/vercel.json`, `docs/deploy.md`
- **Done when:** the Story 8.1 criteria pass on the sandbox, every secret above is set (no value in the repository), the OD1 and OD6 results are recorded, and the PR is merged. I1 needs this deploy (D51).

### A05: Discovery scan and prior collection

- **Owner:** Luis · **Stories:** 10.1, 1.4 · **Branch:** `story/10.1-discovery-scan` · **Forecast:** 11:45 to 12:55, merged 13:05 (desk V)
- **Start when merged:** A01 · **Merge after:** nothing beyond its own checks (fake gate and ledger)
- **Prepared material (D1):** fetch during the event. No code from `scripts/data/` or `dxp-*` skills (`dxp-open-data-sources` is reference only); no files from `data/` unless cleared.
- **Scope:**
  - **The scope (V1, V25).** The `research_scopes` document is hand-written in A03's `gate/seed_data/` and loaded by `python -m dxp.gate.seed`: `{ scope_id, team_id, title: "Plasma ctDNA genotyping assays in NSCLC", assays (the four D45 strings), condition: "non-small cell lung cancer" (all stages), cursor, version }`, with no aliases (V34) and the cursor Luis chose at 10:45 (OD2). **Anchor verification (V36):** at 10:45 Luis queries the live API for the scan and records which in-scope early-stage trial is actually updated after the chosen cursor, with its update date, status and results as returned. NCT04712877 is the expected candidate only; if it is not updated after the cursor, the scan's real result is the anchor and the framing follows V33. A05 reads it and advances the cursor; `GET /scopes`, `GET /scopes/<scope_id>`.
  - **The client.** `sources/ctgov.py` (the spine's ClinicalTrials.gov fetch and query helpers): ClinicalTrials.gov API v2 search and fetch by NCT ID, keeping `overall_status`, `has_results`, `last_update_posted`, the interventions verbatim (name, type and `otherNames`, which are kept as name mentions, V37) and the text fields; `evidence_text` built at load (AD-15).
  - **The scan (V2).** `discovery.scan(scope_id, ctx)`: one admission, then `gate.evaluate()` as `search_source` to `source:clinicaltrials.gov` before any request; `query.term` = the scope's assay names (plus, for the demo scan, the plasma ctDNA terms that find early-stage profiling studies; no aliases), `query.cond` = the condition, `filter.advanced` = `AREA[LastUpdatePostDate]RANGE[<cursor>,MAX]`; each result upserted as `clinicaltrials.gov:<NCT ID>` with `window: "discovered"`, `scope_ids`; a re-scan never overwrites `raw_text` that Evidence points at; the cursor advances by a conditional update on the scope's `version` only after the scan finishes. Returns the source refs in last-update order with the verified anchor first (for `DXP_DEMO_PACE`). Also used by the follow-up task (A25) with its own grant and a `max`.
  - **The prior collection and the setup item.** `sources/selected.json` (the D30 list); `python -m dxp.sources.load --nct NCT05715229` (the setup item, `window: "setup"`); `python -m dxp.pipeline.prior` (in `pipeline/prior.py`), from a laptop with `DXP_SEED_KEY`: fetches by NCT ID the D30 trials last updated before the cursor (excluding NCT05715229 and anything on or after the cursor), extracts them with `llm.extract` and files them through `ledger.file()` in `baseline` mode under `seed@v1`, so they are accepted knowledge to relate to.
- **Required behaviours:** blocked action (a blocked scan makes no request and records one Decision); audit (the run audit records the cursor used and after, V14).
- **Files this PR owns:** `backend/dxp/discovery/scan.py`, `backend/dxp/sources/ctgov.py`, `backend/dxp/sources/load.py`, `backend/dxp/sources/selected.json`, `backend/dxp/pipeline/prior.py`, `backend/dxp/api/routes_scopes.py`, `backend/tests/a05/`
- **Done when:** the Story 10.1 and 1.4 criteria pass; against the live API the scan with the chosen cursor returns the anchor verified at 10:45 (expected NCT04712877), with its update date, status and results as the response gives them; the intervention `otherNames` are stored verbatim; a failed scan leaves the cursor unchanged; the prior command loads idempotently into a test database; the PR is merged.

### A06: Ledger, policy gate and claim checks

- **Owner:** Luis · **Stories:** 1.6, 9.3, 10.7 (A23 folded in) · **Branch:** `story/9.3-policy-gate` · **Forecast:** 10:45 to 12:55 (draft from 10:45 with three builders, inside a 20-minute rebase budget on A01, V31), merged 13:05 · **Critical, head of the late merge queue**
- **Start when merged:** nothing: drafts from 10:45 against AD-14 and D16 to D50 (L1; over the 20-minute rebase budget by 12:05 means L1 has failed) · **Merge after:** A01, A02, A03
- **Never stubbed (D37).**
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Everything the previous A06 card required (five checks in order, decisions with derived IDs and `seq`, filing in `live` mode only as pending proposals, seed `baseline` mode, `ledger.apply` and `ledger.recover_applying` in `ledger/apply.py`, D5, D16, D20, D21, D26 to D28, D50), with these changes:
  - **Kinds.** Check 3 knows every kind and destination of AD-14; check 4 applies to `file_proposal` (per change and for a report as a whole), `file_related_evidence`, `notify_slack`, `generate_briefing` and `generate_avatar_video` (Reviewer-initiated under `sam@v1`, V29; the script may hold only the report's own facts), and records `n/a` for `search_source`, `apply_value` and every human kind; check 5 records `n/a` for Reviewer and seed writes.
  - **Claim checks (V7, `gate/claims.py`).** Check 4 evaluates each claim in the action's payload, each with a `claim_kind`, against the source's own fields and checked quotes: `claim_performed_or_results` needs `has_results: true` or a checked quote saying the assay was performed with results; `claim_planned` requires NOT_YET_RECRUITING or RECRUITING (or planned) trials to be described as planned or ongoing; `claim_preclinical` requires cell-line or animal evidence to be labelled preclinical. A failing claim blocks the action; the Decision names the failed claim policy and the claim text. The redraft is a new evaluation with its own Decision.
  - **Reports.** `ledger.file()` accepts a `report_id` and links each pending proposal to it; one gate evaluation per change, as before. A change may add a trial to the scope's evidence collection (the allowed demo update, V35) or link a name mention to a Diagnostic.
  - **Check 2 on a name mention (V35, V37).** A proposed link from a trial's name mention to a Diagnostic outside the scope (the record's "FoundationOne CDx" mention, a tissue test, against the plasma scope) is blocked before filing; the Decision cites the mention verbatim, the Diagnostic and the scope rule.
- **Required behaviours:** blocked action; authority; audit reconstruction (fields this PR writes); stop semantics (check 5).
- **Files this PR owns:** `backend/dxp/gate/` (`__init__.py`, `checks.py`, `claims.py`, `decisions.py`; not `policy_sets.py`, `seed.py` or `seed_data/` (A03), nor `grants.py` (A24)), `backend/dxp/ledger/__init__.py`, `ledger/file.py`, `ledger/types.py`, `ledger/apply.py`, `backend/tests/a06/`
- **Done when:** the previous A06 tests pass (each check blocks on its own, a blocked action leaves everything untouched, concurrent applies apply once, recovery is idempotent, edges keep their first `run_id`); each claim policy blocks on its own and leaves records, reports and Slack untouched; a "showed" claim on a RECRUITING trial without results is blocked and the redraft "is recruiting; no results posted" is allowed; a proposed link of a "FoundationOne CDx" mention to the plasma scope is blocked by check 2 and its Decision cites the mention and the scope rule; adding a trial to the scope's evidence collection is allowed; the Story 1.6, 9.3 and 10.7 criteria pass; the PR is merged.

### A07+A11: Runs, stop and the audit API

- **Owner:** Luis · **Stories:** 9.1, 9.5, 9.6 · **Branch:** `story/9.5-runs-stop` · **Forecast:** 11:45 to 13:00, merged 13:25 · **Critical**
- **Start when merged:** A01 · **Merge after:** A03
- **Never stubbed (D37).**
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Everything the previous A07 and A11 cards required (two identities, `startable_by`, 401/403/409, admissions under the D22 names, stop, the sweep's background task calling `actions.mark_failed` and `actions.mark_unknown`, `settle`, `finish`; the audit in `seq` order with "After the run", `authorised_by` from the Decision, `GET /decisions/<decision_id>`, the two `GET /actions` routes; A11 only reads), with these changes:
  - **Sets.** `POST /runs { grant_id, set }` with `set` = `discover` (agent grant: the run calls `discovery.scan`), `nct:<NCT ID>` (setup only: one Source item) or `task:<task_id>` (only under that task's grant, only for an `authorised` task, started by Sam from the report page while flag `task_run` is on; the run carries `cause { task_id, report_id }`; A10 hands it to A25's `tasks.run`). 403 for a `task:` set under another grant.
  - **Audit (V14).** `GET /runs/<run_id>/audit` adds: sources fetched with the cursor before and after; each retrieval (method, index, top-k, scores); memories used with author, source and effect; relationships with label, both quotes and similarity; the report and its Slack result; under "After the run", the report decision ("1 update accepted"), the task authorisation with who authorised it and the gap it answers, memory changes, and either a link to the task's run and its audit or "authorised, not run" (V27). All read from `decisions`, `actions`, `events`, `reports` (with its embedded `related[]`), `memories` and `tasks`; nothing recomputed from current grants or policies.
- **Required behaviours:** stop semantics; authority; audit reconstruction; blocked action (in the trail with the failed check or claim policy).
- **Files this PR owns:** `backend/dxp/runs/` (including `__init__.py` and `admissions.py`), `backend/dxp/api/routes_runs.py`, `backend/dxp/search/audit.py`, `backend/dxp/api/routes_audit.py`, `backend/dxp/api/routes_actions.py`, `backend/tests/a07_a11/`
- **Done when:** the previous A07 and A11 tests pass; a fixture discover run with a blocked claim, a filed report, a delivered alert, a memory used, an approval and a task run reconstructs in order with every V14 section; a `task:` set under the wrong grant is refused; the Story 9.1, 9.5 and 9.6 criteria pass; the PR is merged.

### A08: Extraction

- **Owner:** Luis · **Story:** 1.5 · **Branch:** `story/1.5-extraction` · **Forecast:** 10:45 to 13:10 (draft from 10:45 with two builders and a 20-minute rebase budget; tuned on live trials fetched by the builder after A05's client lands), merged 13:35 · **Critical**
- **Start when merged:** nothing: drafts from 10:45 against the AD-14 `Finding` shape (L1; over the 20-minute rebase budget by 12:05 means L1 has failed) · **Merge after:** A01, A05
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-claude-api` is reference only).
- **Scope:** `llm.extract(item)` and `llm.check()`, a quote and confidence per field, failure records, never raise. **No aliases (V34):** an extracted name resolves to a seeded Diagnostic only through A02's `identity.resolve_exact()`; anything else stays as written in the source and is returned as an unresolved name. Names in an intervention's `otherNames` are returned as **name mentions** with their field (V37), never as evidence that the trial used that product; `evidence.quote_in_source()` and the support check. Adds `llm.call_structured(model, schema, messages)`, the one client that A19+A20's `relate` and `draft` use (AD-11), and each Finding's `summary` (embedded by A19+A20). Tuned on the prior collection, NCT05715229 and NCT04712877. No PubMed text in any file.
- **Files this PR owns:** `backend/dxp/llm/` (client, extract, check, prompts; except `llm/prompts/relate.*` and `llm/prompts/report.*`, which are A19+A20's), `backend/dxp/evidence/` (including `__init__.py`, D36), `backend/tests/a08/`
- **Done when:** NCT04712877 yields the intervention "ctDNA, tumor NGS" verbatim, a name mention "FoundationOne CDx" resolved exactly to the tissue Diagnostic, and a name mention "FoundationOne Liquid" left unresolved (never mapped to FoundationOne Liquid CDx, never `new`); no Finding says the trial uses or studies either product; NCT05715229 yields a Finding for its status without stating outcomes; every quote is found; the Story 1.5 criteria pass; the PR is merged.

### A09: Slack notifier, one alert per report

- **Owner:** Luis · **Story:** 9.4 · **Branch:** `story/9.4-slack-notify` · **Forecast:** 11:45 to 13:30, merged 13:45 (desk V) · **Critical**
- **Start when merged:** A01 · **Merge after:** A03
- **Never stubbed (D37).**
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills. The script used to test the webhook before the event is not reused (S12).
- **Scope:** Everything the previous A09 card required (S3 to S9: configuration, gate first, atomic claim, observed outcome, 429 once, `unknown` never retried, `mark_unknown`, `mark_failed`, `resolve`, the fake sender), with these changes (V11):
  - **One alert per report**, not per proposal: the `notify_slack` action's `item_key` carries the `report_id`.
  - **The message:** header "New research report for review" plus the action ID; the report headline (the V33 signal, with the mention wording of V37, never "uses", "studies" or performance wording); the discovery (NCT ID with its ClinicalTrials.gov link, status, "No results posted" when so), the gap and the relationship summary (for example "extends 1"); who acted (agent, run ID, grant, policy set); the context line "Approve or reject in DxP. Slack only notifies."
  - **Links:** "Review in DxP" → `${DXP_BASE_URL}/reports/<report_id>`; "Open diagnostic" → `${DXP_BASE_URL}/diagnostics/<dx_id>`. The sender refuses to start without `DXP_BASE_URL`.
  - A09 writes only `actions` (and, through the gate, `decisions`); never `reports` or `proposals`.
- **Required behaviours:** ambiguous external result; concurrent retries; blocked action; authority; audit reconstruction (S9).
- **Files this PR owns:** `backend/dxp/actions/` (`__init__.py`, dispatch, `slack.py`, resolve, `mark_unknown`, `mark_failed`, the fake sender), `backend/dxp/api/routes_resolve.py`, `backend/tests/a09/`
- **Done when:** the previous A09 tests pass; one report with two proposals produces exactly one alert; the alert's links point at the report page and the accepted knowledge view; no test output or log contains the webhook URL; the Story 9.4 criteria pass; the PR is merged. The real alert and its links are checked in I1.

### A10: The run

- **Owner:** Luis · **Story:** 1.7 · **Branch:** `story/1.7-run` · **Forecast:** 11:45 to 13:30, merged 13:45 · **Critical**
- **Start when merged:** A01 · **Merge after:** nothing beyond its own checks (real modules are wired in I1)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-langgraph-langsmith` is reference only).
- **Scope:** `pipeline.run(run_id)`, with the agent key and a context from `runs.context()`. It first calls `ledger.recover_applying()`. One LangGraph run:
  1. **Items.** `discover`: `discovery.scan(scope_id)`; `nct:`: the one Source item; `task:` is handed to `tasks.run` (A25; never started while flag `task_run` is off). With `DXP_DEMO_PACE`, one item at a time, a few seconds each, the verified anchor first.
  2. **Per item:** `llm.extract`, `llm.check`; `retrieval.related(...)` (A19+A20); `memory.retrieve(team_id, text, tags)` (A21+A22); `reports.relate(...)` per related item; `reports.draft(...)`, which drafts with and without the memories as reviewer guidance and records each memory's before-and-after effect; then one admission per action (D22) and `reports.file(...)`, which calls the gate (the report-level `file_proposal` with the claim checks, then `file_proposal` per change). On a blocked claim, redraft once (a new evaluation and Decision); a second failure ends the item with nothing filed.
  3. **After filing:** `actions.dispatch()` for the report's one `notify_slack` action. No briefing or avatar call: media is on demand from the report page (V29).
  4. `runs.release()` in a `finally` for every admission; `runs.finish()` after the last item; `failed` only on an unrecoverable error (D23).
- **Files this PR owns:** `backend/dxp/pipeline/` (except `prior.py`, which is A05's), `backend/tests/a10/`
- **Done when:** over stubs, a discover run with one item produces one blocked claim, one redraft, one report with its proposals, one alert through the fake sender, and no ElevenLabs or HeyGen call; a blocked report gets no alert;
 every admission is released once; the run ends `done`; the Story 1.7 criteria this covers pass; the PR is merged.

### A13: Setup data, snapshot and reset

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2b-seed` · **Forecast:** 11:45 to 13:15 (a second builder on the scripts), merged 13:25 (desk V)
- **Start when merged:** A01, A02 · **Merge after:** nothing beyond its own checks: merges on fake-gate tests (D38)
- **Prepared material (D1):** fetch during the event. No code from `scripts/data/` or `dxp-*` skills; no files from `data/` unless cleared.
- **Scope:**
  - `python -m dxp.sources.fda_cdx` and `python -m dxp.ledger.seed` as before (lung rows, D45 row IDs, Diagnostics in `baseline` mode (no hand-written aliases, V34) under `seed@v1`, three synthetic Teams, D56); `GET /teams`. If the FDA page cannot be fetched or parsed by 13:15, seed only the Diagnostics the scope and prior collection name, typed from the FDA page during the event; Luis tells B07.
  - **Snapshot and reset (D34, D41, V15).** `scripts/reset_demo.py --snapshot` is run by I1 only after `GET /memories?team_id=` shows M1, created through the real UI (V15). The snapshot is `mongodump` of database `dxp` to a folder outside the repository, taken after M1 exists and before any discover run, so it contains the seed, the prior collection with embeddings, the setup report and M1. `scripts/reset_demo.py`: `delete_many({})` on every collection (never drop: validators and indexes, including the search indexes, stay), then `mongorestore`. If `mongodump` or `mongorestore` does not work against the sandbox (OD6), the reset reruns the setup commands, which needs Sam to recreate the memory through the UI; that takes about 30 minutes and is the fallback only. The reset posts nothing to Slack and never touches `dxp_smoke`.
- **Files this PR owns:** `backend/dxp/sources/fda_cdx.py`, `backend/dxp/ledger/seed.py`, `backend/dxp/api/routes_teams.py`, `scripts/reset_demo.py`, `backend/tests/a13/`
- **Done when:** the FDA fetch parses the live list; the seed is idempotent against a fake ledger; `reset_demo.py` restores a dump into a test database with validators and indexes intact; the PR is merged. The real setup and snapshot are I1's.

### A14: Read model, accepted knowledge and value review (A18 folded in)

- **Owner:** Luis · **Stories:** 1.1 (read model), 1.3 (narrowed), 2.2, 2.3 (value review only) · **Branch:** `story/2.3-proposals-decisions` · **Forecast:** 11:45 to 13:15, merged 13:35 (desk V) · **Core**
- **Start when merged:** A01 · **Merge after:** A06 (value review calls the gate and `ledger.apply`)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `search.readmodel.get_diagnostic(dx_id)` and `GET /diagnostics/<dx_id>`: **accepted knowledge only** by default (accepted values with Evidence, accepted trials and findings, each linked to the report and decision that accepted it), plus a list of pending reports that would change it, never mixed into accepted values (V5, V10). `GET /proposals?status=&field=&diagnostic_id=&run_id=&report_id=` and `GET /proposals/<p_id>` (D42), with `notification` built at read time (D47). `POST /diagnostics/<dx_id>/values/<value_id>/review` (`review_value`, D16). `POST /proposals/<p_id>/decision` is superseded by the report decision (V8) and stays 501; `ledger/decide.py` is not written.
- **Files this PR owns:** `backend/dxp/search/readmodel.py`, `backend/dxp/api/routes_diagnostics.py`, `backend/dxp/api/routes_proposals.py`, `backend/dxp/api/routes_review.py`, `backend/dxp/ledger/review.py`, `backend/tests/a14/`
- **Done when:** the accepted knowledge route never returns a pending value as accepted; a pending report is listed as such; value review accepts, edits and rejects through the gate; the trimmed Story 1.1, 1.3, 2.2 and 2.3 criteria pass; the PR is merged.

### A19+A20: Retrieval, relationships and the report

- **Owner:** Luis · **Stories:** 10.2, 10.3, 10.4 · **Branch:** `story/10.2-retrieval-report` · **Forecast:** 11:45 to 13:45 (three builders: retrieval and indexes; relationships; report assembly), merged 13:55 · **Critical** (the index build in I1 step 1 waits for it)
- **Start when merged:** A01 (starts after the contract, V31; not a draft) · **Merge after:** A01, A06
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-mongodb-atlas` is reference only).
- **Scope:**
  - **Retrieval (V3, AD-15).** `retrieval.ensure_indexes()` (`retrieval/indexes.py`): vector indexes `vs_source_items`, `vs_findings`, `vs_memories` (filter fields `scope_ids`, `team_id`, `status`, `tags.assay`, `tags.claim_kind`) and the text fallback indexes. Embedding path chosen once by `DXP_EMBEDDING`: `auto` (Atlas Automated Embedding), `voyage` (`retrieval.embed()` in `retrieval/embed.py`, the only holder of `VOYAGE_API_KEY`, only with a cleared key), or `none`. `retrieval.related(scope_id, text, k, exclude)` and `retrieval.memories(team_id, text, tags, k)` (`retrieval/related.py`) return `Retrieval { method, index, top_k, filter, items[{ ref, score }] }`; a failed vector query falls back to text search with `method: text_search`. A score never enters a check, a label or a claim.
  - **Relationships (V4).** `reports.relate(new_item, related_item)` (`reports/relate.py`, through `llm`; one name, settled by V24): one label from `supports`, `contradicts`, `extends`, `new_question`, a rationale and one quote from each side (at most 300 characters), both checked with `evidence.quote_in_source()`; without two checked quotes the item is "related (no relationship established)"; a model error yields the same and never fails the item. Embedded in the report as `report.related[]` (label, both quotes, similarity) with derived `rel_` IDs (AD-26); there is no separate `relationships` collection.
  - **Report (V5, V26, V33 to V37).** `reports.draft(item, findings, related, memories)` (`reports/draft.py`) drafts with and without the retrieved memories, so each memory used carries its effect (the sentence or label it changed, before and after, or "retrieved, no change"), and returns:
    - the headline, written as the signal of V33 from the trial's own fields (for the expected anchor: "This study investigates molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer, to find actionable drivers before surgery. No results posted."); it never says the trial uses or studies a named product, nor implies any assay's performance;
    - the discovery sentences and claims, each with a `claim_kind`;
    - `name_mentions`: each name the record gives, verbatim, with its field (for example `otherNames` of "ctDNA, tumor NGS"), described as "named in the record" (V37);
    - uncertainties, including the ambiguous intervention field ("The trial's intervention field is ambiguous: it lists assay names as alternate names of a generic ctDNA and tumour NGS intervention, and does not say which assay was used for which sample.") and each unresolved name ("The record names 'FoundationOne Liquid'. Whether this is the FDA-approved FoundationOne Liquid CDx is not stated."), V34;
    - one evidence gap (V26, V33): "Have early-stage NSCLC studies that combine plasma ctDNA with tissue profiling posted results?";
    - one recommended task that answers exactly that gap: `search_related` with `question` = the gap and params { condition: NSCLC, stage: "early", testing: ["ctDNA or plasma", "tissue profiling"], has_results: true, max: 5 };
    - the knowledge updates: for the demo, one allowed update adding the trial to the scope's evidence collection (V35), and the proposed link of the "FoundationOne CDx" mention, which the gate blocks on check 2 before filing. `reports.file(...)` (`reports/file.py`) gates the report as a whole as a report-level `file_proposal` (the claim checks run here; there is no `file_report` kind, V24), writes the `reports` document `pending` with `memories_used`, files each knowledge update through `ledger.file()` as a pending proposal linked to the report, and creates the report's one `notify_slack` action through A09's `dispatch` contract. `reports.add_related(report_id, refs, ctx)` (`file_related_evidence`, used by the task). `GET /reports?status=&run_id=` and `GET /reports/<report_id>` (quotes only, never `raw_text`; 404 in the error shape).
  - **Draft order:** settled by V21 (draft 1 without memories, draft 2 with them, both gated; the before/after effect comes from the two real drafts).
- **Required behaviours:** blocked action (a blocked report writes nothing but its Decision and event); audit reconstruction (retrieval, relationships and report fields for V14).
- **Files this PR owns:** `backend/dxp/retrieval/` (except `__init__.py`), `backend/dxp/reports/relate.py`, `reports/draft.py`, `reports/file.py`, `backend/dxp/llm/prompts/relate.*`, `backend/dxp/llm/prompts/report.*`, `backend/dxp/api/routes_reports.py`, `backend/tests/a19_a20/`
- **Done when:** the Story 10.2 to 10.4 criteria pass; a high-similarity pair with one unchecked quote gets no label; with `DXP_EMBEDDING=none` every response says `text_search`; a report with two updates files two pending proposals and one notification action; on a fixture of NCT04712877 the report keeps the intervention wording verbatim, lists the two uncertainties above, names the gap and its task, files only the evidence-collection update (the mention link is blocked), and contains no "uses", "studies" or "showed" wording about either name; the PR is merged. The real index build is I1 step 1.

### A21+A22: Reviewer memory

- **Owner:** Luis · **Stories:** 10.5, 10.6 · **Branch:** `story/10.5-memory` · **Forecast:** 11:45 to 13:45 (two builders), merged 14:05, the last core merge · **Critical** (correct and revoke are supporting, S3)
- **Start when merged:** A01 (starts after the contract, V31; not a draft) · **Merge after:** A01, A19+A20 (`retrieval.memories`)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-atlas-agent-memory` describes the deferred preview SDK and is not used).
- **Scope:** `memory.create(team_id, text, tags, source, reviewer, ctx)` (`create_memory`, under `sam@v1`; author from the key), `memory.correct()` (new version, `supersedes`, old one `corrected`) and `memory.revoke()`, each gated, recorded as a Decision with a `request_id`, conditional on the current status; `GET /memories?team_id=&status=`, `GET /memories/<memory_id>`, `POST /memories/<memory_id>/correct`, `POST /memories/<memory_id>/revoke`. `memory.retrieve(team_id, text, tags)`: only `active` versions of the Team, ranked by `retrieval.memories`. **Tag filter (V22):** M1 comes from NCT05715229 and must be retrieved for the anchor, which names different assays (and, with no aliases, may name none that resolve, V34); so retrieval filters on `claim_kind` (for example `outcome_claim_without_results`), never on `assay` (the assay tag is recorded and shown, not required to match). The before-and-after effect is computed in A19+A20's `reports.draft`, from the memories this PR retrieves. No code path reads a memory into a grant, a policy or the gate (AD-28).
- **Required behaviours:** authority (a memory never changes permissions; the author is the key's principal); audit reconstruction (memories used and changed appear in the run audit).
- **Files this PR owns:** `backend/dxp/memory/store.py`, `backend/dxp/memory/retrieve.py`, `backend/dxp/api/routes_memories.py`, `backend/tests/a21_a22/`
- **Done when:** the Story 10.5 and 10.6 criteria pass; a memory created on one trial's report is retrieved for a different trial's discovery with no assay in common and the same `claim_kind`;
 revoking it removes its effect from the next report; creating, correcting or revoking a memory leaves grants, policies, policy sets and gate outcomes unchanged; the PR is merged.

### A24: Report decision, promotion and task authorisation (core)

- **Owner:** Luis · **Story:** 10.8 · **Branch:** `story/10.8-approve-task` · **Forecast:** 11:45 to 13:00, merged 13:15 · **Critical** (its reject path creates M1 in I1 step 2)
- **Start when merged:** A01 · **Merge after:** A06 (`ledger.apply`); `memory.create` is coded against its frozen signature and proved against A21+A22 in I1 step 2
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope (V8, V27, V35):** `POST /reports/<report_id>/decision { action: approve | reject, note, correction }` through `api/routes_report_decision.py`, which calls `reports.decide()`, then `tasks.authorise()`, then `memory.create()` (AD-29).
  - **Approve** is gated as `decide_report` under `sam@v1` and applies every pending proposal of the report through `ledger.apply`, all or nothing, then marks the report `accepted`. For the demo that is the one allowed update: the anchor added to the scope's evidence collection; no assay record changes (V35).
  - **Authorise** is a second evaluation, `authorise_task`, which inserts one `tasks` document `{ task_id, report_id, kind: "search_related", question: <the report's gap>, params { condition, stage: "early", testing, has_results: true, max: 5 }, grant_id: "task-<hex>@v1", status: authorised, result: null }` and one versioned task grant `task-<hex>@v1` (kind `task`; actions `search_source`, `file_related_evidence`; the same scope; destinations `source:clinicaltrials.gov`, `ledger`; `startable_by: [sam]`; expiry one hour). A24 **does not run the task** and calls nothing in `tasks/run.py`.
  - **The response and the wording (V27):** the decision returns, and the report page shows, "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." Approved is not accepted for the task.
  - **Reject** (note required, else 400) or **approve with a correction** is gated as `create_memory` and creates the memory; reject promotes nothing and authorises no task.
  - A second decision returns the current state. Each evaluation is its own Reviewer Decision (`run_id: null`, `request_id`, `cause { report_id, origin_run_id }`). `reports.recover_accepting()` finishes an interrupted approval. `GET /tasks?report_id=`, `GET /tasks/<task_id>` (with `status` and, once A25 has run it, `result { answer, with_posted_results[] }`).
- **Required behaviours:** authority (the task grant is the only permission the approval creates); blocked action; audit reconstruction ("After the run": the decision and who authorised the task).
- **Files this PR owns:** `backend/dxp/reports/decide.py`, `backend/dxp/tasks/authorise.py`, `backend/dxp/gate/grants.py` (`issue_task_grant()`, the only runtime grant writer), `backend/dxp/api/routes_report_decision.py` (including `GET /tasks`), `backend/tests/a24/`
- **Done when:** the Story 10.8 criteria pass; a concurrent double approval applies once; a reject without a note returns 400; approval leaves every assay record unchanged and the task `authorised` with the gap as its `question`; the task grant expires after one hour; nothing in A24 imports `tasks/run.py`; the PR is merged.

### A25: Follow-up task execution (supporting, first substantial cut)

- **Owner:** Luis · **Story:** 10.9 · **Branch:** `story/10.9-task-run` · **Forecast:** 11:45 to 13:00, merged 14:15 (desk L, after the last core merge) · **Supporting**, flag `task_run`; joins I3b only if merged by 14:30 and the I1 loop is green by 14:30, otherwise cut (V28, V30)
- **Start when merged:** A01 · **Merge after:** A24 (task document and grant), A07+A11 (`task:` runs), A19+A20 (`reports.add_related`)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope (V9, V26, V33):** `tasks.run(task_id)` in `tasks/run.py`, reached only through a `task:` run: Sam presses "Run follow-up task" on the report page (B04, flag `task_run`), which calls `POST /runs { grant_id: "task-<hex>", set: "task:<task_id>" }` (A07+A11) with `initiated_by: sam`, `agent: dxp-curator`; A10 hands the run to `tasks.run`. The task answers the report's gap: it searches ClinicalTrials.gov through `discovery.scan` with the task grant for early-stage NSCLC trials that combine ctDNA or plasma testing with tissue profiling, at most 5, and records `result { answer, with_posted_results[] }`: the answer to the task's `question` and the trials with posted results ("None with posted results" is a valid, honest `answer`, with an empty `with_posted_results`). Its findings are filed through `reports.add_related()` as pending related evidence on the report, never accepted knowledge (V27). Each step holds an admission and passes its own gate (grant, scope, destination, limit, run authorisation); a sixth result or a step outside the scope is blocked and recorded. Stop works on the task's run.
- **Required behaviours:** authority (runs only under the task grant); blocked action; stop semantics; audit reconstruction (the task's run linked from the origin run's "After the run").
- **Files this PR owns:** `backend/dxp/tasks/run.py`, `backend/tests/a25/`
- **If cut:** flag `task_run` off; `tasks/run.py` stays A01's stub if never merged; no `task:` run is started; the report page and the audit show "Follow-up task authorised; not run". Nothing in the core changes.
- **Done when:** the Story 10.9 criteria pass; a task with no matching results answers "None with posted results"; the sixth result is blocked; findings are pending, never accepted; stop works on the task's run; the PR is merged; I3b passes.

### I1: Integration, setup and the discovery loop

- **Owner:** Luis · **Stories:** 10.1, 10.4, 10.5, 10.6, 10.7, 9.4 · **Branch:** `integration/i1-discovery-loop` · **Forecast:** 13:35 to 14:45 (step 1 data 13:35 to 13:55, indexes 13:55 to 14:05; step 2 14:05 to 14:20; loop 14:20 to 14:45, first green pass forecast 14:35) · **Critical**
- **Start when merged:** step 1: A03, A04, A05, A06, A08, A13 (A19+A20 for the indexes); step 2 and the loop: also A07+A11, A09, A10, A21+A22, A24, and B04 deployed
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Fixes are written during the event.
- **Scope:** the three rows of "Integration and acceptance checks" for I1: step 1 (13:35 to 14:05), step 2 with Sam's correction through the deployed report page and the snapshot (14:05 to 14:20), the discovery loop (14:20 to 14:45) with the V35 and V37 assertions. What breaks is fixed in small PRs to the owning file, reviewed by its owner (D36), never edited from this branch.
- **Required behaviours checked here:** all six, end to end.
- **Files this PR owns:** `backend/tests/i1/` (the integration test and its notes)
- **Done when:** M1 exists and is in the snapshot; the loop passes on the sandbox; the PR is merged.

### I3: Integration, approval, promotion, authorisation and audit (with optional I3b)

- **Owner:** Luis · **Stories:** 10.8, 10.10 (and 10.9 in I3b) · **Branch:** `integration/i3-approve-task` · **Forecast:** 14:45 to 15:00; I3b 15:00 to 15:15 only if it joins · **Critical** (I3b supporting)
- **Start when merged:** I1 · **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Fixes are written during the event.
- **Scope:** the I3 row of "Integration and acceptance checks", from the report the I1 loop filed, with the V27 wording checked on the page and in the audit ("Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review"), plus the S3 memory check inside the slot. **I3b** runs only if A25 is merged by 14:30 and the I1 loop is green by 14:30: the I3b row (the task runs, is gated, answers the gap, its findings stay pending). If the gate is missed, A25 is cut and I3 ends at 15:00.
- **Files this PR owns:** `backend/tests/i3/` (I3 and I3b)
- **Done when:** approval, promotion, task authorisation and the audit pass on the sandbox (and I3b, if it ran), and the PR is merged.

### A16: Rehearsal and reset

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `story/8.2-rehearsal` · **Forecast:** 15:00 to 16:10 (15:15 to 16:25 if I3b ran) · **Critical**
- **Start when merged:** I3 · **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `docs/demo-and-reset.md`: the setup order and how M1 is created (V15); the demo order of `build-schedule.md` (the second screen is Slack `#all-mango-db-hackathon`); `DXP_DEMO_PACE`; when and how to run A13's reset. Uses A13's `scripts/reset_demo.py`; does not create or edit it. **Demo notes:**
  - **The anchor (V36):** which trial the 10:45 check verified (expected NCT04712877), with its update date, status and results; if it is another trial, the headline, gap and narration are rewritten from its own fields following V33.
  - **Wording (V33, V37):** "FoundationOne CDx" and "FoundationOne Liquid" are "named in the record" or "mentioned", never "used" or "studied"; nothing implies any assay's performance; the blocked case is "the proposed link of the record's 'FoundationOne CDx' mention to the plasma scope, blocked by check 2"; the report keeps the intervention wording verbatim and flags the intervention field as ambiguous.
  - **Approval (V27):** "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." Approved is not accepted for the task.
  - **Media (V29):** the script is always shown as text; play the briefing or avatar only if its check passed; never wait for either.
  - **The longitudinal narrative (V32):** the scope cursor and the Team's memories accumulate over time; the scan only looked at what changed since the last scan; M1 came from a correction earlier in the day; the bigger value from the original brief is team-specific, longitudinal intelligence on the diagnostics a team follows, and the demo shows one turn of that loop.
  - 15:00 to 15:10 reset; **pass 1, core acceptance** (the former I2, cut 1), 15:10 to 15:35: the full demo order through the screens, with only the supporting items whose check passed (S1 to S3, and I3b if it ran).
  - 15:35 to 15:45 reset; **pass 2**, 15:45 to 16:00: the 3-minute live demo and the 60-second script (V17) back to back.
  - 16:00 to 16:10 the reset for the video. If I3b ran, every time above is 15 minutes later.
- **Files this PR owns:** `docs/demo-and-reset.md`
- **Done when:** pass 1 passes without a fix, the sandbox is reset for the video by 16:10 (16:25 if I3b ran), and the PR is merged. If pass 1 fails, pass 2 is dropped and its slot used for one fix and a rerun. On the emergency path (`build-schedule.md`) there is one pass only.

### B01: Web skeleton and minimal shell

- **Owner:** Vlad · **Story:** 1.12 · **Branch:** `story/1.12-web-shell` · **Forecast:** 10:45 to 12:00, merged 12:10
- **Start when merged:** nothing · **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-vercel-frontend` is reference only). Text wordmark "DxP"; the prepared logo is not used unless cleared.
- **Scope:** `web/` from `create-next-app` (Next.js 16, TypeScript, App Router, Tailwind), `shadcn init`, every screen dependency installed up front (no `react-force-graph-2d`: the graph is cut); a `gen:types` script; `web/lib/api.ts` (typed get and post by path); `web/lib/features.ts` reading `NEXT_PUBLIC_DXP_FEATURES` (`briefing`, `avatar`, `memory_edit`, `task_run`); `web/lib/format.ts` (D40 formats); the one server route that adds `X-DxP-Key`; the shell: tokens and fonts from `DESIGN.md`, the wordmark, a top bar with Run console, Reports (pending count, polling `GET /reports?status=pending` every 2 seconds), Audit, and the read-only "Signed in as" chip; `/` redirects to the latest run. **Player stubs:** `web/app/reports/[report_id]/briefing/player.tsx` and `web/app/reports/[report_id]/avatar/player.tsx`, each rendering nothing, handed to B06 and B08 at merge, so B04 can place them behind their flags before either exists.
- **Files this PR owns:** `web/` including `package.json`, `lib/api.ts`, `lib/features.ts`, `lib/format.ts`, `components/shell/`; except `web/lib/types.ts` (A01), `web/vercel.json` (A04), and the paths of B02, B03, B04, B06 and B08 (the two player directories after B01 merges)
- **Design reference:** `DESIGN.md` tokens; EXPERIENCE.md "Information Architecture" (top bar) and "Accessibility Floor"
- **Done when:** the trimmed Story 1.12 criteria pass, `next build` succeeds, and the PR is merged. It deploys once A04 lands (D39).

### B02: Run console

- **Owner:** Vlad · **Stories:** 9.7, 10.1, 10.9 · **Branch:** `story/9.7-run-console` · **Forecast:** 12:10 to 14:15, merged 14:25 · **Core** (needed by A16 pass 1, not by I1)
- **Start when merged:** B01 · **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Start a discovery scan with `POST /runs { grant_id, set: "discover" }`, choosing a grant labelled with its Team and scope (no Team picker, D18); the identity card (agent, initiated by, grant, policy set, scope, cursor); the action feed by polling `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` every 2 seconds: allowed, blocked (failed check or claim policy named), in flight, `reconciling`, unknown with Resolve shown only when `GET /whoami`'s actions include `resolve_notification` (D53); "Slack alert delivered" with its time; a link to each report the run filed; stop with `stopping` then `stopped`. A task's run opens here labelled "Follow-up task" with a link back to its report (only if A25 joined, flag `task_run`).
- **Files this PR owns:** `web/app/runs/page.tsx`, `web/app/runs/[run_id]/page.tsx`, `web/components/run-console/`
- **Design reference:** EXPERIENCE.md "Information Architecture" (Run console row), "Component Patterns: Run, gate and audit", "State Patterns: Claim blocked", "Follow-up task", "Run, Slack and general"; `DESIGN.md` tokens
- **Done when:** the Story 9.7 criteria pass against the sandbox, a discover run displays and stops (and a task run, if A25 joined), and the PR is merged.

### B03: Audit view

- **Owner:** Vlad · **Stories:** 9.8, V14 · **Branch:** `story/9.8-audit-view` · **Forecast:** 12:10 to 14:35, merged 14:45 · **Core** (needed by A16 pass 1)
- **Start when merged:** B01 · **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** One run reconstructed from `GET /runs/<run_id>/audit`, polled while running: sources fetched with the scan cursor; retrieval (method, top-k, scores; "related by text search" when that ran); memories used with author and effect; relationship labels with both quotes; every decision allowed or blocked, including the blocked link of the record's "FoundationOne CDx" mention to the plasma scope (check 2, citing the mention and the scope rule, V35, V37) and, when draft 1 wrote it, the blocked performance or results claim with its failed claim policy (V21); the Slack result; "After the run": the report decision ("Approved: 1 update accepted"), the task authorisation with who authorised it and the gap it answers, "its findings will be pending review" (V27), memory changes, and a link to the task's run and audit, or "authorised, not run" if A25 did not join. Resolve on an `unknown` notification as B02 (D53); the "Who authorised this?" panel from `authorised_by` (D40). It answers the audit question of V16.
- **Files this PR owns:** `web/app/runs/[run_id]/audit/`, `web/components/audit/`
- **Design reference:** EXPERIENCE.md "Information Architecture" (Audit view row), "Component Patterns: Run, gate and audit", "Evidence Display Rules", "MongoDB Capability Tags"; `DESIGN.md` tokens
- **Done when:** the Story 9.8 criteria and the V14 sections pass against the sandbox, the view answers the V16 question, and the PR is merged.

### B04: Report page, pending reports and accepted knowledge (two builders)

- **Owner:** Vlad · **Stories:** 10.10, 1.3 (narrowed), 2.4 (narrowed) · **Branch:** `story/10.10-report-page` · **Forecast:** 12:10 to 13:45 with two builders, merged 13:55, deployed about 14:00 · **Near-critical** (I1 step 2 at 14:05 creates M1 through it)
- **Start when merged:** B01 · **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:**
  - **Builder 1, the report body.** `web/app/reports/[report_id]/` from `GET /reports/<report_id>`: the headline (the V33 signal); the discovery with its status, "No results posted" when so, and quotes; the intervention wording verbatim with its names labelled "named in the record" (V37), never "uses" or "studies"; related evidence with label, both quotes and similarity, or "related (no relationship established)"; the retrieval method, with "related by text search" when that ran; uncertainties, including the ambiguous intervention field and any unresolved name (V34); the gap; memories used with author, source and before-and-after effect; the proposed updates marked pending (for the demo, the trial added to the scope's evidence collection); the recommended task with the gap it answers; the briefing and avatar panels (B06's and B08's folders, on demand, V29) behind the `briefing` and `avatar` flags; "Report not found" for an unknown ID. The pending reports list `web/app/reports/page.tsx`. The accepted knowledge view `web/app/diagnostics/[dx_id]/` from `GET /diagnostics/<dx_id>` (accepted only, with a notice for pending reports).
  - **Builder 2, decisions and memory.** The decisions bar: Approve, Reject and "Approve with correction" through `POST /reports/<report_id>/decision` (a note is required for Reject and for a correction). After approval the page says, in words (V27): "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." Accepted and pending are labelled differently. Behind flag `task_run`, a "Run follow-up task" button starts the task's run (`POST /runs { grant_id: "task-<hex>", set: "task:<task_id>" }`); the task's status, its answer (pending, "None with posted results" shown as a valid answer) and a link to its run. With the flag off: "Follow-up task authorised; not run". The memories panel in the right-hand column: each memory's author, source, status, and Correct and Revoke (behind `memory_edit`) through the memory routes. A 400 or 403 shows as a message and the page stays.
- **Files this PR owns:** `web/app/reports/` (list and `[report_id]/`), `web/app/diagnostics/`, `web/components/report/` (builder 1), `web/components/report-decision/` and `web/components/memory-panel/` (builder 2)
- **Design reference:** EXPERIENCE.md "Information Architecture" (Report page, Pending reports list, Accepted knowledge view rows), "Component Patterns: Discovery and report", "State Patterns: Relationship labels, Memory statuses, Pending and accepted, Claim blocked, Follow-up task", "Key Flows: Flow 0" (Sam's correction creates M1); `DESIGN.md` tokens
- **Done when:** the Story 10.10 criteria pass against the sandbox; `/reports/<report_id>` and `/diagnostics/<dx_id>` serve on the deployed app (the Slack link targets); Reject with a note creates a memory; the page shows the V27 approval sentence and no "uses", "studies" or performance wording about a named product; the PR is merged.

### B06: Ten-second ElevenLabs briefing

- **Owner:** Vlad · **Story:** 10.11 · **Branch:** `story/10.11-briefing` · **Forecast:** 12:30 to 14:25, merged 14:35; drops out of the demo if not merged by 14:45 · **Supporting (check S1), `briefing` flag, second in the cut order**
- **Start when merged:** B01 · **Merge after:** A01, A19+A20
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-elevenlabs` is reference only). No audio is made before the event.
- **Scope (V29):** `briefing.script_for(report)`: a script of about ten seconds built only from the report's fields (the signal, its status, the gap), adding no fact and following the mention wording of V37; the same function B08 uses. **On demand only:** a "Generate briefing" button in the panel calls `POST /reports/<report_id>/briefing`, which runs `briefing.generate(report_id, ctx)`: gated as `generate_briefing` to `tts:elevenlabs` under the Reviewer grant `sam@v1` (never the agent grant; the run never calls it), recording who requested it; ElevenLabs text to speech with ctDNA, NSCLC and NGS pronounced correctly, cached once per report state in `audio`; a failure is recorded and never affects the report, Slack, the decision, the task or the rehearsal. Nothing generates a briefing automatically. `GET /reports/<report_id>/briefing` returns the script as text always, plus the audio status and URL (`unavailable` without a key, OD3). The panel always shows the script as text; the player says "unavailable" on failure.
- **Files this PR owns:** `backend/dxp/briefing/script.py`, `backend/dxp/briefing/audio.py`, `backend/dxp/api/routes_briefing.py`, `web/app/reports/[report_id]/briefing/`, `backend/tests/b06/`
- **Design reference:** EXPERIENCE.md "State Patterns: Briefing player"; `DESIGN.md` tokens
- **Done when:** the Story 10.11 criteria pass; a test proves the script contains only report fields and no "uses", "studies" or performance wording; without the key the script still shows as text, the player says "unavailable" and the report works; filing a report makes no ElevenLabs call; the PR is merged; S1 passes.

### B08: HeyGen avatar video

- **Owner:** Vlad · **Story:** 10.12 · **Branch:** `story/10.12-heygen-avatar` · **Forecast:** 12:30 to 14:45, merged 14:55; drops out of the demo if not merged by 15:00 and checked by 15:10 · **Supporting (check S2), `avatar` flag, first in the cut order.** Built only if the 10:45 HeyGen account check passed; that check is off the critical path (V29)
- **Start when merged:** B01 · **Merge after:** A01, A19+A20, B06 (it uses `briefing.script_for`)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (`dxp-heygen` is reference only). No clip is made before the event; the 10:45 check is an account check only (OD7).
- **Scope (V29):** **on demand only.** A "Render avatar" button calls `POST /reports/<report_id>/avatar`, which runs `briefing.render_avatar(report_id, ctx)`: gated as `generate_avatar_video` to `video:heygen` under the Reviewer grant `sam@v1` (never the agent grant; the run never calls it), recording who requested it. For the demo, one render is requested for the demo report only, as soon as it is filed; nothing renders automatically per report. It builds a script of about 20 seconds from `briefing.script_for(report)` (the same grounded script, adding nothing) and asks the HeyGen API v3 to render it asynchronously with `HEYGEN_API_KEY` (only in `.env` and the Modal secret; never logged or returned); records a `media` document `{ report_id, status: rendering, video_id, requested_at }`. `GET /reports/<report_id>/avatar` returns `Media { status: rendering | ready | unavailable, video_url }`, checking a `rendering` video's status with HeyGen in the background and never waiting (AD-30); a failed render or one not finished within the run's window is `unavailable`. The panel always shows the script as text; the player beside it has the states "Rendering", "Ready", "Playing" and "unavailable", polling every few seconds, captions on, never autoplay. The report, Slack, the decision, the task and the rehearsal never wait for HeyGen.
- **Files this PR owns:** `backend/dxp/briefing/avatar.py`, `backend/dxp/api/routes_avatar.py`, `web/app/reports/[report_id]/avatar/`, `backend/tests/b08/` (distinct from every B06 file)
- **Design reference:** EXPERIENCE.md "State Patterns: Avatar video player", "Demo on Camera" (open the report last when the render is slow); `DESIGN.md` tokens
- **Done when:** the Story 10.12 criteria pass; a test with a fake HeyGen client covers rendering, ready and failed; filing a report makes no HeyGen call; without the key the script still shows as text and the player says "unavailable"; the PR is merged; S2 passes (an on-demand render completes on the sandbox, or the flag stays off).

### B07: Submission package

- **Owner:** Vlad · **Stories:** 8.3, 8.4 · **Branch:** `story/8.3-submission` · **Forecast:** 12:45 to 14:00, merged 14:10
- **Start when merged:** nothing · **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** The README, which B07 alone owns on Saturday (D36): the one-line description and the governed discovery loop, with the scope "Plasma ctDNA genotyping assays in NSCLC" and the longitudinal value (V32); the prepared vs built-today table (planning documents, reference skills, `data/` and `scripts/data/` not used without clearance, the logo, the Slack webhook and channel, and the ElevenLabs and HeyGen accounts if created before the event, with keys never in the repository and every briefing and video made during the event); what is not reused and why; the organiser answers from `docs/clearance.md`; the MongoDB capability table (only capabilities proven on the sandbox: say "text search" if Vector Search fell back, OD1); credits; links to `docs/deploy.md`, `docs/demo-and-reset.md`, `docs/clearance.md`. The submission description. The 60-second video script in `docs/video-script.md`, with the V17 timings: 0 to 10 s the scope and the agent's identity, and that the scan only looks at what changed since the last scan (V32); 10 to 25 s the signal (V33: "molecular profiling using blood (ctDNA) and tumour tissue in early-stage (IA2 to III) lung cancer … No results posted"), its related evidence, the gap, and M1, from a correction earlier in the day, changing the wording; 25 to 35 s the blocked case: the proposed link of the record's "FoundationOne CDx" mention to the plasma scope, blocked by check 2 (and the blocked performance claim if it occurred); 35 to 45 s the Slack alert opening the report; 45 to 60 s approval ("Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review", V27), the audit answer, and a closing line on team-specific, longitudinal intelligence (V32). The task's run appears only if I3b passed. **Wording (V33, V37):** both "FoundationOne CDx" and "FoundationOne Liquid" are "named in the record" or "mentioned", never "used" or "studied"; nothing implies any assay's performance; the script uses the anchor verified at 10:45 (V36). Recording and submitting is R1, which adds the video link.
- **Files this PR owns:** `README.md`, `docs/video-script.md`, `docs/submission.md`
- **Done when:** the Story 8.3 criteria and the Story 8.4 script criteria pass, and the PR is merged.

### R1: Record and submit

- **Owners:** Luis and Vlad · **Story:** 8.4 · **When:** 16:30 to 16:55, then the reset 16:55 to 17:10 · **Critical**
- **Needs:** A16 done (including the video reset), B07 merged
- **Scope:** Record the 60-second video from `docs/video-script.md` on the reset sandbox with `DXP_DEMO_PACE` set, showing only behaviour that passed and never a key or the webhook URL; add the video link to the README (the only README edit outside B07, D36); submit the description, public repository, video and team members by 16:55. Then Luis runs `scripts/reset_demo.py` (16:55 to 17:10) so the live demo at 17:15 starts from the snapshot with M1.
- **Done when:** the submission is confirmed before 17:00 and the sandbox is reset by 17:10.

## Cut, superseded and deferred work

Cut on 14 November (proposal section 7, cut 3), not built: A12 live feed (9.9), A15 graph API (5.1), B05 impact view (5.2), A17 policy drafts (9.11). Split again (V28): the A24+A25 bundle, now A24 (core) and A25 (supporting). Removed (V34): the hand-written aliases of D31 and `identity/aliases.py`.
 Superseded: the old audio briefing (9.10) by B06 (10.11); `POST /proposals/<p_id>/decision` by the report decision (V8); the `/review?proposal=` page by the report page (V10).

Deferred (pivot, 13 Nov, and V18). No agent builds these on Saturday. The old PR IDs P01 to P42 and V01 to V19 are retired; do not reuse them.

| Deferred | Stories |
|---|---|
| Full Baseline load, scheduled scan, Tavily provider scan, PubMed | 1.9, 1.10, 1.11 |
| Jobs page (replaced by the Run console) | 1.8 |
| Held-back dry run, value history, Learned rules API and Rules on screen, Learned-rule enforcement | 2.1, 2.5, 2.6, 2.7 |
| Alerts API, Alerts inbox, Digest, alert audio | 3.1 to 3.5 |
| Find and Categories | 4.1 to 4.8 |
| Changed highlight on the graph | 5.3 |
| Agent Memory preview, resume, synthetic Team history, Home hero | 6.1 to 6.4 |
| Quick capture | 7.1 |
| The Home dashboard and the full app shell | parts of 1.12 |
| The Diagnostics list and `GET /diagnostics` | parts of 1.1 and 1.3 (D40) |
| `GET /teams/<team_id>`, `POST /teams/<team_id>/seen` | parts of 5.1 and 6.3 |
