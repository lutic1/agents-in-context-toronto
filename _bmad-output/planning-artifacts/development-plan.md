---
title: DxP development plan, Saturday 14 November 2026
status: final
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/build-schedule.md
---

# DxP development plan

Who builds what on Saturday, one pull request at a time, after the approved pivot to Statement 1, "Agents You Can Audit" (`sprint-change-proposal-2026-11-13.md`), with the readiness fixes D1 to D57 (`readiness-fixes-2026-11-14.md`, including the final audit D41 to D57, which wins where any document disagrees), and the Slack change S1 to S13 (`sprint-change-proposal-2026-11-14-slack.md`: Slack replaces GitHub as the external system; it wins on anything about the notification). The governed agent is the product: it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action and an audit trail a reviewer can replay. Screens only inspect it.

Every PR below has an owner, a story, a branch, what must be merged before it starts, what must be merged before it merges, the files it owns and a forecast. Timing, milestones and fallback cuts are in `build-schedule.md`. The forecasts come from a model, not from a validated run; the milestones in `build-schedule.md` are how the day checks them.

## The two lanes

| | Luis | Vlad |
|---|---|---|
| Agents | Up to 44: builders, reviewer agents, the contract keeper and the integrator | Sonnet 5.5 at high effort: one main agent and ten subagents |
| Model budget | Claude plan; the product runs on Luis's API key | Claude Pro plus $300 of API credit (forecast about $100) |
| Owns | The critical path: contract, registry and aliases, grants and policies, deploy, trial fetch, ledger, gate and apply, runs and stop, extraction, the Slack notifier, the run, audit API, feed, FDA fetch and seed, proposals and review API, read model, graph API, both integrations, rehearsal and reset, stretch policy draft; `docs/clearance.md` | The web skeleton and shell, Run console, Audit view, Record and Review, Run impact view, stretch spoken briefing, submission package |
| PRs | 20 (A01 to A18, I1, I2) | 7 (B01 to B07) |
| Shared task | R1: record the 60-second video and submit (with Vlad); then the reset for the live demo | R1 (with Luis) |
| Merge coordinator | Luis, for Luis's lane | Vlad, for Vlad's lane, after Luis's review agent passes each PR |

PR counts are not workload: Luis's lane holds every core back-end behaviour and both integrations, so Luis's attention goes to the loop and its failures.

## No prepared code or assets (D1)

| Rule | Detail |
|---|---|
| Code | No code from `scripts/data/` or from any `dxp-*` skill is copied into `backend/` or `web/`, and none is run on Saturday. Skills are reference documentation only (APIs, limits, gotchas). Every line of project code is written during the event |
| Trials | A05 fetches the selected trials by NCT ID from the ClinicalTrials.gov API v2 during the event |
| FDA list | A13 fetches the FDA list of cleared or approved companion diagnostics during the event and keeps the lung rows |
| Prepared `data/` files | Not loaded unless an organiser clears them in writing on Saturday morning (open item in `build-schedule.md`; Luis records the answer in `docs/clearance.md`). If cleared, A05 and A13 may load them instead of fetching |
| Logo | B01 uses a text wordmark, "DxP", in the interface font, unless an organiser clears the prepared logo |
| Disclosure | The README lists prepared material so judges can see it, not so agents can use it |

## Demo scenario (D9)

| | |
|---|---|
| Scripted question | **"Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"** |
| Source | Selected trial NCT04712877 names FoundationOne Liquid CDx (plasma) and FoundationOne CDx (tissue). Both are FDA-seeded by A13. The trial's own names ("FoundationOne Liquid", "FoundationOne CDx") resolve to the seeded Diagnostics through A02's hand-written aliases (D31) |
| Grant | The agent grant `lbdx@v1` of Team "Team Liquid Biopsy Dx" (A03, D32, D56), for the agent principal `dxp-curator`: `scope.diagnostic_ids` = the `dx_id`s of "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay" (D45). Every other Diagnostic, FoundationOne CDx among them, is out of scope |
| Allowed | At least the proposal to add NCT04712877 to FoundationOne Liquid CDx's trials (D46: other selected trials may file more, each with its own alert): a pending proposal plus a real Slack alert in `#all-mango-db-hackathon` (S5), whose "Review in DxP" link opens that proposal focused on the Review page. Approval happens in DxP, never in Slack (S4) |
| Blocked, external side | No proposal is filed for FoundationOne CDx, so no Slack message is sent (S11) |
| Blocked | The same trial's proposal for FoundationOne CDx: blocked before execution, check 2 (`team_scope`) fails |
| Review | Sam approves the allowed proposal under the Reviewer grant `sam@v1` (A14, B04); it appears under "After the run"; the Audit view answers the question |
| Not shown | No stage transition. The SuperARMS stage-advance story is out of the demo |
| Selected set | The 20 trials named in D30, in that order, NCT04712877 first (A05) |
| Pacing (D33) | The live run uses `DXP_DEMO_PACE` (A10): one item at a time, a few seconds per item, so the first item is NCT04712877 and the stop lands while items remain |
| Order (D33, S11), video and live demo | 1. start the run; 2. the allowed proposal, then the second screen: its alert arriving in Slack `#all-mango-db-hackathon`; then the blocked one; 3. stop the run while items remain; 4. Sam opens the alert's "Review in DxP" link and approves the focused proposal in DxP (it appears under "After the run"); 5. ask the scripted question in the Audit view |
| Reset (D34, D41) | A13 owns `scripts/reset_demo.py` and the snapshot procedure. The snapshot is taken after seeding and before any run (I1's first step). The reset restores it before every take: at the start of I2, before each A16 rehearsal, before the video (16:15 to 16:30) and between submission and the live demo (16:55 to 17:10). Smoke tests never touch the demo database: they run in `DXP_DB=dxp_smoke` |

## Contracts come first, and they cover more than API shapes

A01 and A02 start at 10:45 and merge by 11:45. A03 drafts against A01 from 10:45 and merges after it. A01 writes stubs only: every route returns 501 and every signature raises `NotImplementedError` until the PR named in the A01 card finishes it (one exception: `ledger.recover_applying()` is a no-op stub, because A01's startup hook calls it). The architecture spine's AD-14 table and AD-17 to AD-22 are the reference, and the readiness fixes win where they differ; between them A01, A02 and A03 freeze:

- **Every route** in the AD-14 table, under `/api/v1`, registered once in `app.py` so no later PR edits it. **Each route's status (core, supporting, stretch, deferred) is stated in one place only, the AD-14 table (D40);** the list below names owners and does not restate statuses. Deferred routes are registered and stay 501; no card finishes them.
  - schema: `GET /schema` (A01, the only route A01 finishes)
  - identity: `GET /whoami` (A03), returning `Principal { id, name, kind, actions }`, where `actions` are the actions of the caller's current grant (D53)
  - runs (A07): `POST /runs { grant_id, set }` (no `team_id`: the grant defines the Team, D18; no `source`, no `limit`; 401 only for an unknown key, 403 when the grant's latest version is not active or the caller is not in `startable_by`, 409 while a run is `running` or `stopping`), `GET /runs`, `GET /runs/<run_id>`, `POST /runs/<run_id>/stop`. Neither `GET /runs/<run_id>` nor stop calls Slack: each starts the sweep in the background and returns current state, with a `dispatching` action the sweep is settling shown `reconciling` (read time only, never stored; D24, S7)
  - actions: `GET /actions?run_id=&status=`, `GET /actions/<action_id>` (status and result) (A11); `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }` (A09, action kind `resolve_notification`, S8). There is no Slack callback route and no reconcile route (S4, S8)
  - audit (A11): `GET /runs/<run_id>/audit`, `GET /decisions/<decision_id>` (audit detail for any entry, allowed or blocked, with `authorised_by`)
  - grants and policies (A03): `GET /grants`, `GET /grants/<grant_id>`, `GET /policies?status=`
  - feed (A12): `GET /changes?after=<seq>&run_id=`
  - diagnostics: `GET /diagnostics/<dx_id>` (A18); `POST /diagnostics/<dx_id>/values/<value_id>/review { action, value, reason }` (A14, action kind `review_value`). `GET /diagnostics` (the list) is deferred: no Diagnostics list is built (D40)
  - proposals (A14): `GET /proposals?status=&field=&diagnostic_id=&run_id=`, `GET /proposals/<p_id>` (one proposal, whatever its status; the Review page's `?proposal=<p_id>` focus uses it, and there is no `p_id=` query parameter, D42), `POST /proposals/<p_id>/decision { action, value, reason }` (returns `{ proposal, decision, rule_draft }`)
  - teams: `GET /teams` (A13); `GET /teams/<team_id>` and `POST /teams/<team_id>/seen` are deferred
  - graph (A15): `GET /graph?run_id=&context=`
  - stretch: `GET /runs/<run_id>/audit/audio` (B06), `POST /policies/<policy_id>/approve { version }` (A17)
- **One error shape** for every route: `{ error: { code, message } }`. A blocked action is not an error: it returns 200 with the `Decision`. It creates a `decisions` document and one `action_blocked` event, and no `actions` document (D5).
- **The shapes** in `models.py`, exactly as AD-14, and the generated `web/lib/types.ts`. The ones the readiness fixes changed:
  - `Principal`: `{ id, name, kind, actions }`, returned by `GET /whoami`; `actions` are the actions of the caller's current grant (D53).
  - `Run`: two identities, `initiated_by` (the caller) and `agent` (the grant's `principal`); `team_id` from the grant; `grant_id` and `grant_version` pinned at start; `policy_set_version` pinned; `in_flight` is the count of `admitted` admissions; `counts` keep `early_research` (D29); `limit` is dropped. Status `running`, `stopping`, `stopped`, `done`, `failed`: `done` only through `runs.finish`, `stopped` only through `runs.settle`, `failed` only on an error the pipeline cannot recover from (D23).
  - `Grant`: `grant_id`, `version`, `principal` (the agent, person or seed it authorises), `kind` (`agent`, `person`, `seed`), `startable_by` (principal IDs), `key_hash`, `acting_for`, `granted_by`, `team_id`, `team_name`, `scope` (`{ diagnostic_ids }`, or `{ all: true }` for the seed principal only, D16), `destinations` (`ledger`, `slack:#all-mango-db-hackathon`, S2), `actions` (agent kinds `file_proposal`, `notify_slack`; seed kind `apply_value`; human kinds `decide_proposal`, `review_value`, `resolve_notification`; S1, S8), `expires_at`, `status` (`active`, `revoked`, `expired`).
  - `Stamp`: `kind` (`run`, `reviewer`, `seed`). Run writes carry the `run_id` and `principal` = the agent; Reviewer writes carry `run_id: null` and the Reviewer's principal and grant (`sam@v1`); seed writes carry only `{ kind: "seed", principal: "seed", run_id: null }`.
  - `PolicySet`: `id` (the `policy_set_version`, `derive("ps_", *sorted members)`), `members` (`"<policy_id>@v<n>"`), `created_at`.
  - `Admission`: `id` (`derive("adm_", run_id, item_key)`), `run_id`, `item_key`, `status` (`admitted`, `released`, `abandoned`), `admitted_at`, `expires_at` (`admitted_at` + 10 minutes), `released_at`. One admission per action (D22): `item_key` = `"<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"`, taken after extraction and before the gate.
  - `Decision`: `id` (`derive("dec_", run_id or "-", kind, diagnostic_id, target[, request_id])`, where `target` is the `action_id` for `resolve_notification` (D49), else the `proposal_id`, else the `value_id`, else `"<field>|<value>"`, D20), `run_id` (null for Reviewer and seed decisions), `agent` and `initiated_by` (a run's own; Reviewer: `agent: null`, `initiated_by` = the Reviewer; seed: both `"seed"`, D19), `request_id` (Reviewer decisions only, server-generated, so a blocked Reviewer decision can be retried and gets a new Decision), `stamp`, `cause` (Reviewer only: `proposal_id`, `origin_run_id`), `kind`, `inputs`, `evidence_ref`, `destination`, `target`, `checks` (check, passed or `n/a`, detail), `failed_check`, `grant_id` and `grant_version` evaluated, `run_grant_version` pinned, `policy_set_version`, `outcome` (`allowed`, `blocked`), `action_id` (allowed only), `seq` (the `seq` of its `action_allowed` or `action_blocked` event, D21), `decided_at`, `authorised_by`.
  - `Action`: `id` derived from the same parts as its decision with prefix `act_` (D20); adds `decision_id`, `admission_id`, `proposal_id` and `destination`; status `queued`, `dispatching`, `delivered` (a `notify_slack` action), `done` (a `file_proposal` action), `failed`, `unknown` (`reconciling` is returned in place of `dispatching` at read time only, while the background sweep settles it, and is never stored; S7); `error` (for example `abandoned_before_send`, `abandoned_in_flight`, `invalid_payload`, `rate_limited`); timestamps `proposed_at`, `decided_at` (queued), `claimed_at`, `posted_at`, `observed_at` (S9); `result` for a notification, exactly as AD-14 (D44): `{ http_status, response_body, posted_at, link_urls: { review_url, diagnostic_url } }` (S9, never the webhook URL); `resolution` when a Reviewer settled an `unknown` one, exactly as AD-14 (D44): `{ outcome, note, decision_id, by, at }` (S8); `authorised_by`.
  - `Audit`: `run`, `policies`, `entries` (the run's decisions in `seq` order, each with its action when allowed; a notification entry also carries its proposal's live DxP review status `{ status: pending | applied | rejected, decided_by, decided_at }`, S9) and `after_run` (Reviewer decisions whose `cause.origin_run_id` is this run, including `resolve_notification` decisions). `authorised_by`: principal, initiated by, acting for, granted by, the grant and version evaluated, expiry, policy-set version. It is read from the Decision; "who authorised" never comes from `GET /actions/<action_id>` (D40).
  - `Proposal`: status `pending`, `applying`, `applied`, `rejected`; gains `decision_id` and `notification { action_id, status, posted_at }` (D29, S10). `notification` is read-time only (D47): A14 and A11 build it from the proposal's `notify_slack` action when they serve it, and nothing writes it to the proposal document. Seed changes carry their own derived `p_` IDs (D20).
  - `Record` gains `applied_proposal_ids` (D29). Graph `Node` carries `run_id`, `changed` and `context`, and a notification node has kind `notification` and ID `notification:<action_id>` (S10); `Link` carries `status` (`pending`, `applied`), `proposal_id`, `run_id`, `changed` and `context` (D29).
  - `Event`: `action_allowed` and `action_blocked` carry `decision_id`; `value_applied` carries a `dedupe_key`.
- **Display formats (D40),** used by every screen: grants as `{grant_id}@v{version}` (for example `sam@v1`); policy sets as `ps_ab12… (N policies)`; run and action IDs in their `run_` and `act_` forms as stored, never renamed.
- **The `$jsonSchema` validators** for `grants`, `policies`, `policy_sets`, `runs`, `admissions`, `decisions` and `actions` (AD-18), all in `store/schemas/`, owned by A03; `store.ensure_indexes()` (A01) applies them at collection creation. The grant validator rejects `scope: { all: true }` unless the principal is `seed` (D16).
- **The frozen signatures**, return types and error behaviour back-end PRs code against, as AD-17 to AD-22 with the readiness fixes:
  - `resolve_actor(api_key) -> Principal` (A03, `api/auth.py`): SHA-256 of `X-DxP-Key` matched against `key_hash` across all grant versions, whatever their status (D17). 401 means only an unknown key; a revoked or expired grant is caught by check 1 and recorded as a blocked Decision.
  - `gate.policy_sets.current_grant(grant_id) -> Grant` and `gate.policy_sets.current_set() -> PolicySet` (A03): latest version first, then status (D6). A newer `revoked` or `expired` grant version blocks; only policies whose latest version is `active` are members; the `policy_sets` document is inserted if absent the first time a set is used.
  - `identity.derive()`, `identity.normalise_name()` and `identity.aliases` (A02): the hand-written alias map of D31.
  - `runs.start(caller, grant_id, set) -> Run` (A07): loads the latest grant version, checks it is active, unexpired and that the caller is in `startable_by`, then creates the run with `agent` = the grant's `principal`, `initiated_by` = the caller, `team_id` from the grant, grant and policy-set versions pinned, and spawns the run function that `modal_app.py` passed to `create_app()`.
  - `runs.context(run_id, key) -> RunContext` (A07): the only way to build an agent context; refuses unless the key (`DXP_AGENT_KEY`) resolves to the run's `agent`. Every agent write requires a `run_id`.
  - **Admissions (D22): the public API is `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle` and `runs.finish`, implemented in `runs/admissions.py` and exported from `runs/__init__.py`.** Every card uses these names.
    - `runs.admit(run_id, item_key) -> Admission | None`: in one transaction, a conditional `$inc` of `admitting` on the run while `running`, then the insert; not matched returns `None`; a duplicate key returns the existing admission if still `admitted`, else `None`.
    - `runs.release(admission_id) -> None`: `admitted` to `released` with a conditional update; a second release does nothing; then `runs.settle(run_id)`.
    - `runs.sweep(run_id) -> list[str]`: marks `admitted` admissions past `expires_at` as `abandoned` and returns the IDs of the actions they held (D43). `runs` imports nothing from `actions`, so the sweep touches no action.
    - The sweep's background task, in `routes_runs.py` (A07), started on `GET /runs/<run_id>` and `POST /runs/<run_id>/stop`: calls `runs.sweep(run_id)`; for each held action, calls `actions.mark_unknown(action_id, "abandoned_in_flight")` if it is `dispatching` (never retried, S8) and `actions.mark_failed(action_id, "abandoned_before_send")` if it is `queued` (never sent, so safe); finally calls `runs.settle(run_id)` (D24, D43). The name `mark_abandoned` is retired.
    - `runs.settle(run_id)`: only moves a run from `stopping` to `stopped` when no `admitted` admission remains (D23).
    - `runs.finish(run_id)`: called by the pipeline after the last item; moves the run from `running` to `done` once no `admitted` admission remains (D23).
  - `runs.stop(run_id) -> Run`; `runs.stamp(run_id) -> Stamp`, the only stamp maker for run writes.
  - `gate.evaluate(ctx, action) -> Decision` (A06). The five checks, in order, stopping at the first failure: (1) `grant_active`: the latest version of the grant (for a Reviewer write, the caller's grant) is active and unexpired; the decision records it beside the run's pinned version, and if they differ and the latest is not active the check fails; (2) `team_scope`: the target Diagnostic, including one the action would create, is in `scope.diagnostic_ids`, or the grant is `seed@v1` with `{ all: true }`; (3) `destination_action`: the action kind and destination are both in the grant (a `notify_slack` to any destination other than `slack:#all-mango-db-hackathon` fails here, S2); (4) `evidence_checks`, only for `file_proposal` and `notify_slack`; for `apply_value` (seed), `decide_proposal`, `review_value` and `resolve_notification` it records `n/a` (D50), and an `edit` or `reject` without a `reason` is refused before the gate (D16); (5) `run_authorised`: the action holds an `admitted` admission for this run, and the run is not `stopped` (`n/a` for Reviewer and seed writes). Every evaluation inserts one `decisions` document through `gate.decisions` (A06). Allowed inserts the `actions` document (`queued`, with `decision_id`) and emits `action_allowed`; blocked emits one `action_blocked` event with the `decision_id` and writes nothing else. The decision's `seq` is set from that event (D21).
  - `actions.dispatch(action, ctx) -> Action` (A09, S7): calls `gate.evaluate` first, which saves the action ID before anything is sent; on `allowed` claims atomically (`queued` to `dispatching`), posts the Block Kit alert once to `SLACK_WEBHOOK_URL`, and records what it observed: HTTP 200 with body `ok` is `delivered`; another 4xx is `failed`, never retried; a 429 is retried once after `Retry-After` while still holding the claim, and a second 429 is `failed`; a timeout, connection error or 5xx is `unknown`, never retried. Never raises on an ambiguous result. Every status update is conditional on the current status. `actions.mark_unknown(action_id, error) -> Action`: conditional `dispatching` to `unknown`; `actions.mark_failed(action_id, error) -> Action`: conditional `queued` to `failed`; both called only by the sweep's background task in A07's `routes_runs.py` (D43). `actions.resolve(action_id, outcome, note, reviewer) -> Decision` (S8): gated as kind `resolve_notification` under the Reviewer's grant, with the `action_id` as the Decision's target (D49), then a conditional `unknown` to `delivered` or `failed`, recorded as a Reviewer Decision.
  - `ledger.file(finding_id, changes, mode, ctx) -> FileResult` (A06): calls `gate.evaluate` first; on `blocked` nothing else is written. In `live` mode an agent never applies: every change, to an existing Diagnostic or to one the run itself created, is filed as a `pending` proposal (AD-1, AD-4, D8, D28). Only the seed (`baseline` mode, `seed@v1`) applies at once, through `ledger.apply`.
  - `ledger.apply(proposal_id)` and `ledger.recover_applying()` (A06, `ledger/apply.py`, exported from `ledger/__init__.py`, D26): claim, guarded update, edges, `value_applied` event, `applied` (D13, D27). Recovery runs at API start (A01's startup hook), at the start of every run (A10) and on every decision call (A14).
  - `ledger.decide.decide(proposal_id, decision, reviewer) -> DecisionResult` and `ledger.review.review_value(dx_id, value_id, body, reviewer) -> Record` (A14); both call the gate and then `ledger.apply`.
  - `search.readmodel.get_diagnostic(dx_id)` (A18). There is no list function (D40).
  - `pipeline.run(run_id)` (A10): the run function; `modal_app.py` (A04) wraps it with a 3600-second timeout and passes it to `create_app()`. It reads `DXP_DEMO_PACE` (owned by A10, D33).
  - `llm.extract(item, aliases) -> list[Finding] | Failure` and `llm.check(finding, source_text) -> CheckResult` (A08): failure record, never raise. Each Finding's assay name is one of `aliases` (the seeded alias list) or `new` (D31).

After 11:45 a change to any of these goes through the contract keeper in its own PR.

## Required acceptance behaviours

These six are binding on Stories 9.3 to 9.6, in the wording of D4 to D7 as refined by D16 to D25, with the external system changed to Slack (S7 to S9). Each card below restates the ones that apply to it, and the reviewer agent checks them.

| Concern | Required behaviour |
|---|---|
| Ambiguous external result | Save the action ID in Atlas first and put it in the alert's header. A webhook post cannot be looked up afterwards, so DxP records exactly what it observed (S7): HTTP 200 with body `ok` is `delivered`; another 4xx is `failed`, never retried; a 429 means nothing was posted, so retry once after `Retry-After` while still holding the claim, and a second 429 is `failed`. If the outcome is uncertain (timeout, connection error, 5xx), mark the action `unknown` and never retry it; a Reviewer resolves it in DxP through `POST /actions/<action_id>/resolve` (kind `resolve_notification`) after checking the channel for the action ID (S8). Every status update is conditional on the current status, so a slow worker never overwrites an `unknown` or a resolution (D24) |
| Concurrent retries | Claim the action atomically in Atlas (`queued` to `dispatching` with a conditional update) so two workers can never both dispatch it |
| Stop semantics | Check 5, "run still authorised", means the action holds an `admitted` admission for this run and the run is not `stopped`. One admission per action, `item_key` = `"<source_ref>\|<kind>\|<diagnostic_id>\|<proposal_id or '-'>"`, taken after extraction and before the gate (D22). `runs.admit(run_id, item_key)` grants an admission only while the run is `running`, in one transaction with a conditional write on the run, so a stop and an admission cannot race. An admitted action may finish while the run is `stopping`. `runs.release(admission_id)` releases once; a second release does nothing. A background task in `routes_runs.py`, started by the API on `GET /runs/<run_id>` and on stop (neither request calls Slack), calls `runs.sweep(run_id)`, which marks admissions past their 10-minute lease `abandoned` and returns the actions they held; the task then calls `actions.mark_failed(action_id, "abandoned_before_send")` for `queued` ones and `actions.mark_unknown(action_id, "abandoned_in_flight")` for `dispatching` ones, never retried, and finally `runs.settle(run_id)` (D24, D43, S8). `runs.settle(run_id)` only moves a run from `stopping` to `stopped` when no `admitted` admissions remain; `runs.finish(run_id)` moves it from `running` to `done` after the last item; `failed` only on an error the pipeline cannot recover from (D23) |
| Blocked action | One `decisions` document records every check, the grant evaluated and the policy-set version; one `action_blocked` event carries its `decision_id`. No action, no business-record change and no external call |
| Authority | The caller is resolved server-side from `X-DxP-Key`, by `key_hash` across all grant versions whatever their status; 401 means only an unknown key, and a revoked or expired grant is a blocked Decision on check 1 (D17). A run records `initiated_by` (the caller, who must be in the grant's `startable_by`) and `agent` (named by the grant). Every agent write needs a `run_id` and a key that resolves to the run's `agent`. Reviewer decisions carry `run_id: null`, `agent: null`, `initiated_by` = the Reviewer, the Reviewer stamp (`sam@v1`), a `request_id` and a `cause`. A client-supplied name never confers permission |
| Audit reconstruction | Every gate evaluation, allowed or blocked, is a `decisions` document with inputs, evidence reference, checks, the grant evaluated, policy-set version, outcome, timestamps (proposed, decided) and `seq` from its event (D21). An allowed notification links to its action with its destination and the queued, claimed, posted and observed timestamps, and the result: HTTP status, Slack's response body and the link URLs sent, or `unknown` (S9). The audit also shows the proposal's live DxP review status (pending, applied or rejected, with who decided and when). Reviewer decisions caused by a run, including a `resolve_notification`, are listed after it. "Who authorised" is the Decision's `authorised_by` |

## Start requirements and merge requirements are separate

Each card says two things:

- **Start when merged:** what must be on `main` before the agent starts. For most PRs this is only A01, so work runs in parallel instead of one PR after another.
- **Merge after:** what must be on `main` before this PR merges, because it calls real code or another PR's file.

A PR that calls a module not yet merged builds against the frozen signature and is proved against the real module at I1 or I2.

## Integration and acceptance checks

| Check | PR | When | Depends on | What runs |
|---|---|---|---|---|
| Allowed-and-blocked loop | I1 | 13:45 to 14:30 | Core PRs only: A03, A04, A05, A06, A07, A08, A09, A10, A11, A13 (A04 directly, for the deploy, `DXP_BASE_URL` and the Modal secret, D51; through them A01, A02) | First 15 minutes (D38, D41): on the sandbox, the grant seed, the selected-set load, the FDA fetch and seed, then the seeded snapshot with A13's procedure. Then a run over the selected set (D46): at least the NCT04712877 proposal for FoundationOne Liquid CDx filed as `pending`, and its real Slack alert `delivered` to `#all-mango-db-hackathon` (HTTP 200, body `ok`, seen in the channel with its action ID; one alert per filed proposal); the FoundationOne CDx change blocked before execution, with no Slack message; the audit reconstructs all three; both NCT04712877 Findings resolve to the seeded Diagnostics. Both alert links resolve on the deployed web app once B04 is deployed (forecast 14:00); the loop does not wait for it, and if B04 is late the link check moves to I2. No A12 (the feed polls) and no A14 (D26) |
| Core acceptance | I2 | 15:00 to 15:30 | I1, B02, B03, B04, A18, A14 only | First a reset with A13's `scripts/reset_demo.py` (forecast 10 minutes, D41). Then the core loop through the screens, in the D33 order: start a run, see the allowed action as "Slack alert delivered" and the alert in Slack, then the blocked one, stop while items remain, Sam opens the alert's "Review in DxP" link and approves the focused proposal, the Audit view answers the scripted question |

Supporting and stretch items each have their own acceptance check, run by the integrator on the sandbox. An item joins the rehearsal only if its check passed. None of them blocks I1, I2 or A16.

| Check | Items | Needs | By | Passes when | If it fails or is late |
|---|---|---|---|---|---|
| S1 live feed | A12 | A12, B02, I1 green | 15:00 | An action written on the sandbox appears in the Run console within a few seconds through `/changes` | Flag `feed` off; the console polls `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` every 2 seconds |
| S2 impact view | A15, B05 | A15, B05, I1 green | 15:30 | For the demo run, the view shows only the changed elements, each with its `run_id`; context appears only after "Show context", marked as context | Flag `impact` off; every Impact link (shell, B02, B03) is hidden |
| S3 spoken briefing | B06 | B06 (merged only after the 14:30 loop is green), A11 | 15:30 | Audio for the demo run plays on the briefing page reached from the Audit view's "Listen" link; a failure shows the error state | Flag `audio` off; B06 is not merged |
| S4 policy draft | A17 | A17, A14 | 15:45 | A rejection with a reason produces a draft; a person's approval creates a new `active` version and a new policy-set version | Not shown; the approve route stays 501. If it passes after 15:30 it joins the second rehearsal pass only |

The feature flags live in B01's `web/lib/features.ts`, read from `NEXT_PUBLIC_DXP_FEATURES`. Turning a flag off needs no code change.

**Only A12, A15, B05, B06 and A17 may be cut (D37).** Every core screen is done with every flag off: B02 polls instead of using the feed, and every Impact and Listen link is hidden. A06, A07 and A09 are never stubbed; no core PR is replaced by a stub, in I1 or in the demo.

## How agent slots are used

27 PRs are not 27 builders at once. The forecast peak is about 12 builders in Luis's lane (11:45 to 13:15) and 5 in Vlad's (12:00 to 14:00). The rest of Luis's slots go to:

- a second builder on each of A06, A08 and A09, which have no schedule slack, writing the tests, and a third on A06 writing `ledger/apply.py` (moved from A14 by D26);
- one independent reviewer agent per open PR, checking acceptance criteria, the required behaviours, D1 (no prepared code), secrets, `.env` values, tokens and PubMed text;
- the contract keeper, who rejects any PR that changes a frozen contract without regenerating the types;
- the integrator, who runs I1, I2 and the S1 to S4 checks, and keeps a smoke test (one pending proposal with its notification through the fake Slack sender, so merges post nothing to the channel; one blocked action; audit read) passing on every merge once the sandbox is seeded at 14:00. The smoke test runs in its own database, `DXP_DB=dxp_smoke`, seeded there with the same commands, never in the demo database `dxp` (D41). Builders test in their own databases (A01's `conftest.py`), never in the seeded `dxp` database, so the snapshot holds only the seed.

People spend their attention on unclear behaviour and failures, not on reading every diff.

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox.

## How to brief an agent for one PR

Give each agent one PR ID and this brief, filled in from its card:

```
You are building PR <ID> of DxP: <What>.
Read first: _bmad-output/planning-artifacts/development-plan.md (card <ID>,
"No prepared code or assets" and "Required acceptance behaviours"),
readiness-fixes-2026-11-14.md, the Story <n.n> acceptance criteria in
epics.md, the architecture spine (AD rules it cites), and for screens
DESIGN.md and EXPERIENCE.md. There are no mockups: every screen is built
during the event.
Write every line of code yourself during the event. Do not copy, import
or run code from scripts/data/ or from any dxp-* skill; skills are
reference documentation only (APIs, limits, gotchas). Do not load files
from data/ or use the prepared logo unless the plan records that an
organiser cleared them in writing.
Branch: <branch>, from the latest main. Start only when every PR under
"Start when merged" is on main. Code against the frozen contracts and
signatures from A01 and A02 for anything not merged yet. Only edit the
files this PR owns. A change needed in another PR's file goes in a
separate small PR that the file's owner reviews; never edit it from this
branch. Do not merge until every PR under "Merge after" is on main.
Build and test against the Atlas Sandbox.
Never commit secrets, tokens or .env values. Never write PubMed abstract
text to any file. Open the PR as "Story <n.n>: <What> (<ID>)" with the
acceptance criteria and required behaviours as a checklist, and follow
the PR and merge steps in epics.md.
```

The PR title format above is the only one (D40). A fix PR found during I1 or I2 uses it too, with the story and ID of the PR that owns the file: "Story <n.n>: Fix <what> (<owner ID>)".

Tests: each PR's back-end tests live in `backend/tests/<id>/` (for example `backend/tests/a06/`), owned by that PR; "their tests" in a card means that folder. `backend/tests/conftest.py` is A01's (D36).

For example: "You are building PR A06 of DxP: ledger with the policy gate before every write", branch `story/9.3-policy-gate`; or "PR B02: Run console", branch `story/9.7-run-console`.

## Luis's PRs

| PR | Story | What | Branch | Start when merged | Merge after | Start | Finish |
|---|---|---|---|---|---|---|---|
| A01 | 1.1, 9.1 | Contract: routes, shapes, error shape, frozen signatures; stubs only (critical) | `story/1.1-contract` | none | none | 10:45 | 11:45 |
| A02 | 1.2 | Registry, identity and the hand-written aliases (critical) | `story/1.2a-registry-identity` | none | none | 10:45 | 11:45 |
| A03 | 9.2 | Agent, Reviewer (`sam@v1`) and seed (`seed@v1`) grants with `startable_by`, policies, policy sets, latest-then-status selection, server-side actor resolution | `story/9.2-grants-policies` | none (drafts against A01) | A01 | 10:45 | 12:30 |
| A04 | 8.1 | CI, Vercel and Modal deploy on the Atlas Sandbox; change streams checked; `DXP_BASE_URL` and the `SLACK_WEBHOOK_URL` secret set | `story/8.1-deploy-sandbox` | none (starts on the bare package) | A01, B01 (D39) | 11:00 | 12:00 |
| A05 | 1.4 | Fetch the 20 selected trials (D30) by NCT ID from ClinicalTrials.gov and load them | `story/1.4-selected-trials` | A01 | none | 11:45 | 12:30 |
| A06 | 1.6, 9.3 | Ledger with the policy gate before every write; decisions; pending proposals; apply and recovery (critical) | `story/9.3-policy-gate` | A01, A02 | A03 | 11:45 | 13:45 |
| A07 | 9.1, 9.5 | Runs: two identities, admissions, stop and sweep (critical) | `story/9.5-runs-stop` | A01 | A03 | 11:45 | 13:30 |
| A08 | 1.5 | Extraction with quote and support checks, tuned on the selected set (critical) | `story/1.5-extraction` | A01 | A05 | 11:45 | 13:45 |
| A09 | 9.4 | Slack notifier: action ID first, atomic claim, Block Kit alert with links back to DxP, observed outcome, `unknown` never retried, manual resolution (critical) | `story/9.4-slack-notify` | A01 | A03 | 11:45 | 13:45 |
| A10 | 1.7 | The run: LangGraph over the selected set (critical) | `story/1.7-run` | A01 | none | 11:45 | 13:30 |
| A11 | 9.6 | Audit API, decisions and "who authorised" (critical) | `story/9.6-audit-api` | A01 | none | 11:45 | 13:30 |
| A18 | 1.1 | Read model and the Record route `GET /diagnostics/<dx_id>` (core) | `story/1.1b-readmodel` | A01 | A06 | 11:45 | 12:45 |
| A14 | 2.2, 2.3 | Proposals, Reviewer decisions and value review API, calling A06's apply (core) | `story/2.3-proposals-decisions` | A01 | A06 | 11:45 | 13:15 |
| A12 | 9.9 | Change-stream feed with polling fallback (supporting) | `story/9.9-change-feed` | A01, A04 | none | 12:00 | 13:00 |
| A15 | 5.1 | Graph API by run: changed elements, context on request (supporting) | `story/5.1-graph-api` | A01 | none | 12:00 | 13:30 |
| A13 | 1.2 | Fetch the FDA companion diagnostics list; seed the lung rows and synthetic Teams through the ledger; the snapshot procedure and `scripts/reset_demo.py` (D41); merged on fake-gate tests (critical) | `story/1.2b-seed` | A01, A02 | none (D38) | 12:45 | 13:30 |
| I1 | 9.3, 9.4 | Integration: seed the sandbox and take the snapshot (first 15 minutes), then the allowed-and-blocked loop (critical) | `integration/i1-allowed-blocked` | A03, A04, A05, A06, A07, A08, A09, A10, A11, A13 | none | 13:45 | 14:30 |
| A17 | 9.11 | Stretch: rejection drafts a policy for approval | `story/9.11-policy-draft` | I1 green | A14 | 14:30 | 15:30 |
| I2 | 8.2 | Core acceptance on the sandbox (critical) | `integration/i2-acceptance` | I1, A14, A18, B02, B03, B04 | none | 15:00 | 15:30 |
| A16 | 8.2 | Live-demo rehearsal, each pass from a reset with A13's script; the reset for the video 16:15 to 16:30 (critical) | `story/8.2-rehearsal` | I2 | none | 15:30 | 16:15 |

A18 is built from 11:45 to 12:45 and waits for A06 to merge it at about 13:45; A14 waits for A06 the same way. A13 does not wait for A06: it merges on fake-gate tests, and the real seed runs on the sandbox in I1's first 15 minutes (D38), followed by the snapshot with A13's procedure (D41).

## Vlad's PRs

| PR | Story | What | Branch | Start when merged | Merge after | Start | Finish |
|---|---|---|---|---|---|---|---|
| B01 | 1.3, 1.12 | Web skeleton, minimal shell, text wordmark, feature flags; builds locally, deploys once A04 lands (D39) | `story/1.12-web-shell` | none | none | 10:45 | 12:00 |
| B02 | 9.7 | Run console (core) | `story/9.7-run-console` | B01 | A01 | 12:00 | 14:15 |
| B03 | 9.8 | Audit view (core) | `story/9.8-audit-view` | B01 | A01 | 12:00 | 14:00 |
| B04 | 1.3, 2.4 | Record and Review screen, minimal (core) | `story/2.4-record-review` | B01 | A01, A18, A14 | 12:00 | 14:00 |
| B05 | 5.2 | Run impact view (supporting) | `story/5.2-impact-view` | B01 | A01 | 12:00 | 14:30 |
| B06 | 9.10 | Stretch: spoken audit briefing with ElevenLabs, behind a flag | `story/9.10-audio-briefing` | B01 | A11, I1 green (14:30 loop) | 13:00 | 14:30 |
| B07 | 8.3, 8.4 | README, submission text and 60-second video script | `story/8.3-submission` | none | none | 13:00 | 14:00 |

Vlad's times assume Sonnet 5.5 at high effort with ten subagents.

## Shared task

| Task | Story | What | Owners | Needs | Start | Finish |
|---|---|---|---|---|---|---|
| R1 | 8.4 | Record the 60-second video from B07's script on the reset sandbox and submit (description, public repository, video, team members); add the video link to the README; then reset the sandbox for the live demo with A13's `scripts/reset_demo.py` (16:55 to 17:10) | Luis and Vlad | A16 (including the 16:15 to 16:30 reset), B07 | 16:30 | 16:55 (reset done 17:10) |

## PR cards

### A01: Contract

- **Owner:** Luis · **Story:** 1.1, 9.1 · **Branch:** `story/1.1-contract` · **Forecast:** 10:45 to 11:45 · **Critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Stubs only. Create the `backend/` package with `uv` (`pyproject.toml` and `uv.lock`), `create_app(run_function)` in `backend/dxp/api/app.py` with every route under "Contracts come first" registered and returning 501 (except `GET /schema`, which A01 finishes: it serves `schema.registry`, A02's file, and returns an empty registry until A02 merges), allowed origins read from `DXP_ALLOWED_ORIGINS`, and a startup hook that calls `ledger.recover_applying()` (a no-op stub until A06, D26); the error shape `{ error: { code, message } }`; `models.py` with every shape, including the D29 fields, `Principal { id, name, kind, actions }` (D53) and the Action `result` and `resolution` exactly as AD-14 (D44); the `store` module with `ensure_indexes()` (indexes for every collection, including `admissions` unique on `(run_id, item_key)`, and applying A03's validators from `store/schemas/` at collection creation) and `emit_event()` (events carry `run_id`, `action_id` and `decision_id`; `dedupe_key` makes a repeat emit nothing new); the frozen signature stubs, with the public names of D22 (`runs.admit`, `runs.release`, `runs.sweep`, `runs.settle`, `runs.finish`) and D26 (`ledger.apply`, `ledger.recover_applying`); `tools/gen_types.sh`, which writes `web/lib/types.ts`; every backend dependency declared in `pyproject.toml` up front (FastAPI, PyMongo, Anthropic, LangGraph, httpx, Modal, ElevenLabs, pytest), so no later PR edits it or `uv.lock`; `backend/tests/conftest.py` (sandbox connection, a fresh test database per session, the fake-key fixtures); `.env.example` naming every variable of D48 with no values: `MONGODB_URI`, `DXP_DB`; `ANTHROPIC_API_KEY`; `DXP_API_KEY`, `DXP_AGENT_KEY`, `DXP_SEED_KEY`; `SLACK_WEBHOOK_URL`, `DXP_BASE_URL`, `DXP_ALLOWED_ORIGINS`, `DXP_FEED`, `DXP_DEMO_PACE`; `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_DXP_FEATURES`; `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`; plus `ELEVENLABS_API_KEY` for the stretch B06 (S3: there is no `DXP_GITHUB_TOKEN` or `DXP_GITHUB_REPO`; `SLACK_WEBHOOK_URL` is a credential and never gets an example value). No stub is the finished behaviour. After A01 merges, each stub belongs to the card that finishes it:

  | Stub | Finished by |
  |---|---|
  | `GET /schema` | A01 (the only route A01 finishes, D36) |
  | `GET /whoami`, `GET /grants`, `GET /grants/<grant_id>`, `GET /policies` (`routes_grants.py`); `api/auth.py` (`resolve_actor`); `gate/policy_sets.py`; every validator in `store/schemas/` | A03 |
  | `gate/__init__.py` (`gate.evaluate`), `gate/decisions.py`; `ledger/__init__.py` (`ledger.file`, and the exports of `ledger.apply` and `ledger.recover_applying`); `ledger/apply.py` (D26) | A06 |
  | `POST /runs`, `GET /runs`, `GET /runs/<run_id>`, `POST /runs/<run_id>/stop` (`routes_runs.py`); `runs` package including `runs/__init__.py` and `runs/admissions.py` | A07 |
  | `llm` package; `evidence` package including `evidence/__init__.py` (D36) | A08 |
  | `actions` package (`actions.dispatch`, `actions.mark_unknown`, `actions.mark_failed`, `actions.resolve`); `POST /actions/<action_id>/resolve` (`routes_resolve.py`) | A09 |
  | `pipeline.run` | A10 |
  | `GET /runs/<run_id>/audit`, `GET /decisions/<decision_id>` (`routes_audit.py`); `GET /actions`, `GET /actions/<action_id>` (`routes_actions.py`) | A11 |
  | `GET /changes` (`routes_changes.py`) | A12 |
  | `GET /teams` (`routes_teams.py`; `GET /teams/<team_id>` stays 501, deferred) | A13 |
  | `GET /proposals`, `GET /proposals/<p_id>` (D42), `POST /proposals/<p_id>/decision` (`routes_proposals.py`); `POST /diagnostics/<dx_id>/values/<value_id>/review` (`routes_review.py`); `ledger/decide.py`, `ledger/review.py` | A14 |
  | `GET /graph` (`routes_graph.py`) | A15 |
  | `POST /policies/<policy_id>/approve` (`routes_policy_drafts.py`) | A17 (stretch; stays 501 if cut) |
  | `GET /diagnostics/<dx_id>` (`routes_diagnostics.py`; `GET /diagnostics` stays 501, deferred); `search.readmodel` | A18 |
  | `GET /runs/<run_id>/audit/audio` (`routes_audio.py`) | B06 (stretch; stays 501 if cut) |

- **Files this PR owns:** backend/pyproject.toml, backend/uv.lock, backend/tests/conftest.py, .env.example, backend/dxp/api/app.py, backend/dxp/api/models.py, backend/dxp/store/ (except store/schemas/, which A03 owns), the package `__init__.py` files no other card owns (`backend/dxp/__init__.py`, `api/__init__.py`, `search/__init__.py`, `sources/__init__.py`, `schema/__init__.py`), tools/gen_types.sh, web/lib/types.ts. It creates the stub files in the table above and hands each to its finishing card at merge.
- **Slack contract (S1, S2, S7 to S10):** the kinds `notify_slack` and `resolve_notification` (no `create_review_issue`); the Action statuses `queued`, `dispatching`, `delivered`, `done`, `failed`, `unknown` (`reconciling` at read time only); the Action `result { http_status, response_body, posted_at, link_urls { review_url, diagnostic_url } }`, `resolution { outcome, note, decision_id, by, at }` (D44) and timestamp fields; `notification { action_id, status, posted_at }` on `Proposal`, read-time only (D47); notification graph nodes `notification:<action_id>`; the live review status on audit entries; the resolve route. Nothing in the contract names GitHub.
- **Done when:** the Story 1.1 and 9.1 contract criteria pass, `tools/gen_types.sh` regenerates `types.ts` cleanly, and the PR is merged.

### A02: Registry and identity

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2a-registry-identity` · **Forecast:** 10:45 to 11:45 · **Critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `schema/registry.py` (fields, cardinality, enums, stage order, confidence threshold, `canonical()`) and `identity.derive()`, `identity.normalise_name()` as AD-3 (`normalise_name()` removes "®" and folds case, D45), so A03 can derive the `dx_id` of each Diagnostic in the grant scope (`derive("dx_", normalise_name(<FDA trade name>))`, D31) before A13 seeds it. The hand-written alias map, written during the event (D31), in `identity/aliases.py`: "FoundationOne Liquid" → FoundationOne Liquid CDx; "Guardant360" → Guardant360 CDx; "FoundationOne" (when not followed by "Liquid") → FoundationOne CDx. A13 seeds these aliases with the Diagnostics; A08 passes the seeded alias list to extraction. Seeding is A13.
- **Files this PR owns:** backend/dxp/schema/registry.py, backend/dxp/identity/ (including `identity/__init__.py` and `identity/aliases.py`), their tests
- **Done when:** the Story 1.2 registry and identity criteria pass; a test shows "FoundationOne Liquid" and "FoundationOne CDx" (NCT04712877's names) map to two different seeded Diagnostics; the PR is merged.

### A03: Grants and policies

- **Owner:** Luis · **Story:** 9.2 · **Branch:** `story/9.2-grants-policies` · **Forecast:** 10:45 to 12:30
- **Start when merged:** nothing: drafts against the A01 shapes from 10:45
- **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** The `$jsonSchema` validators (AD-18) for `grants`, `policies`, `policy_sets`, `runs`, `admissions`, `decisions` and `actions`, which `store.ensure_indexes()` applies at collection creation; versioned, hand-written grant and policy documents, each policy's `requires` limited to `quote_found`, `supported` and `min_confidence`; each grant names its `principal` (the agent), `key_hash` and `startable_by`. `gate/policy_sets.py`: `current_grant(grant_id)` and `current_set()`, latest version first, then status (D6); a newer `revoked` or `expired` grant version blocks; only policies whose latest version is `active` are members; the `policy_sets` document is inserted if absent the first time a set is used, `_id` = `derive("ps_", *sorted members)`. The grant validator rejects `scope: { all: true }` on any grant whose principal is not `seed` (D16). **Keys (D48).** At 10:45 A03 generates `DXP_AGENT_KEY`, `DXP_API_KEY` and `DXP_SEED_KEY` locally into Luis's `.env`; no key is ever committed or written into `gate/seed_data/`. The seed `python -m dxp.gate.seed`, run only from the command line with `DXP_SEED_KEY`, reading the hand-written documents in `gate/seed_data/` (D36), computes each grant's `key_hash` from the environment at seed time and seeds three grants with the D56 names (D16, D32):
  - **Agent grant `lbdx@v1`** (Team "Team Liquid Biopsy Dx"): principal the agent `dxp-curator` (`DXP_AGENT_KEY`), kind `agent`, actions `[file_proposal, notify_slack]`, destinations `ledger` and `slack:#all-mango-db-hackathon` (S1, S2), `startable_by: [sam]`, an expiry, `scope.diagnostic_ids` = the `dx_id`s of these exact FDA trade-name strings (D45): "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay", each derived with A02's `identity` as `derive("dx_", normalise_name(<trade name>))` (D31). Every other Diagnostic, FoundationOne CDx among them, is out of scope.
  - **Reviewer grant `sam@v1`:** principal `sam` (`DXP_API_KEY`, the web app's server-side key), kind `person`, actions `[decide_proposal, review_value, resolve_notification]` (S8), destination `ledger`, `scope.diagnostic_ids` = the same IDs as the agent grant.
  - **Seed grant `seed@v1`:** principal `seed` (`DXP_SEED_KEY`), kind `seed`, actions `[apply_value]`, destination `ledger`, scope `{ all: true }`.

  `resolve_actor(api_key)`, which hashes `X-DxP-Key` with SHA-256 and finds the principal by `key_hash` across all grant versions, whatever their status; 401 only for an unknown key (D17). `GET /whoami`, returning `Principal { id, name, kind, actions }` with the actions of the caller's current grant (D53); `GET /grants`, `GET /grants/<grant_id>` (each with `team_name`, so the Run console labels a grant with its Team, D18), `GET /policies?status=`.
- **Required behaviour (Authority):** the caller is resolved server-side from the API key; a client-supplied name never confers permission; a revoked key still resolves, and the gate blocks it.
- **Files this PR owns:** backend/dxp/gate/policy_sets.py, backend/dxp/gate/seed.py, backend/dxp/gate/seed_data/, backend/dxp/store/schemas/ (all seven validators), backend/dxp/api/auth.py, backend/dxp/api/routes_grants.py, their tests
- **Done when:** the Story 9.2 criteria pass; a write with an invalid grant, decision or admission is rejected by its validator, and so is `{ all: true }` on a non-seed grant; tests show a newer `revoked` grant version blocks, a revoked key still resolves (no 401), and a retired latest policy version leaves the set; the agent grant validates with `notify_slack` and `slack:#all-mango-db-hackathon`; the PR is merged. The seed runs on the sandbox in I1's first step.

### A04: Deploy on the Atlas Sandbox

- **Owner:** Luis · **Story:** 8.1 · **Branch:** `story/8.1-deploy-sandbox` · **Forecast:** 11:00 to 12:00
- **Start when merged:** nothing: starts on the bare package and CI
- **Merge after:** A01 and B01 (D39: the Vercel deploy needs `web/` to exist)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Deploy configuration only; edits no API file and not the README (D36). GitHub Actions on every pull request (web type check and build, backend tests); Vercel previews and production from `main`; `backend/modal_app.py`, which wraps `pipeline.run` as the run function (3600-second timeout), passes it to `create_app()` and mounts the ASGI app, against A01's frozen entry points (no cron: the sweep runs inside the API); `modal deploy` against the Atlas Sandbox; `DXP_ALLOWED_ORIGINS` set to the Vercel origins in the Modal secret. **Secrets (D48), set by hand from Luis's `.env`:** Vercel gets `DXP_API_KEY` and `NEXT_PUBLIC_API_URL`; the Modal secret gets `DXP_AGENT_KEY`, `SLACK_WEBHOOK_URL`, `ANTHROPIC_API_KEY`, `MONGODB_URI` and `DXP_BASE_URL`. **Slack configuration (S3, S6, S12):** `DXP_BASE_URL` set to the Vercel production URL in the Modal secret and `.env`; `SLACK_WEBHOOK_URL` added to the Modal secret by hand from Luis's `.env`, never committed, logged, echoed in CI output or written in `docs/deploy.md` (which names the variable only). Check that `DXP_BASE_URL` serves the deployed web app; once B04 is deployed, confirm `${DXP_BASE_URL}/review?proposal=<p_id>` and `${DXP_BASE_URL}/diagnostics/<dx_id>` resolve (the integrator repeats this in I1). Check change streams on the sandbox tier and record the result in `docs/deploy.md`; if they are not available, A12 ships polling only (`DXP_FEED=poll`). `docs/deploy.md` also says who deploys and the PR steps.
- **Files this PR owns:** backend/modal_app.py, .github/workflows/, web/vercel.json if needed, docs/deploy.md
- **Done when:** the Story 8.1 criteria pass on the sandbox, the change-stream result is recorded, the Vercel and Modal secrets of D48 are set (no value in the repository), and the PR is merged. I1 needs this deploy (D51).

### A05: Fetch and load the selected trial set

- **Owner:** Luis · **Story:** 1.4 · **Branch:** `story/1.4-selected-trials` · **Forecast:** 11:45 to 12:30 (15 minutes added for the live fetch)
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** fetch during the event. No code from `scripts/data/` or `dxp-*` skills (reference docs only); no files from `data/` unless an organiser clears them in writing.
- **Scope:** `selected.json`, a checked-in, ordered manifest of the 20 NCT IDs named in D30, public ClinicalTrials.gov trials that name an FDA-listed lung assay. The run processes them in this order:

  | # | NCT ID | # | NCT ID | # | NCT ID | # | NCT ID |
  |---|---|---|---|---|---|---|---|
  | 1 | NCT04712877 | 6 | NCT03615443 | 11 | NCT04624373 | 16 | NCT04087473 |
  | 2 | NCT06284317 | 7 | NCT05361564 | 12 | NCT04566614 | 17 | NCT03199651 |
  | 3 | NCT04591431 | 8 | NCT04265534 | 13 | NCT06918782 | 18 | NCT03521154 |
  | 4 | NCT05715229 | 9 | NCT04698681 | 14 | NCT05846594 | 19 | NCT06146920 |
  | 5 | NCT03248089 | 10 | NCT03576937 | 15 | NCT04223596 | 20 | NCT05935384 |

  `python -m dxp.sources.load --set selected`, run from a laptop, fetches each trial by NCT ID from the ClinicalTrials.gov API v2 during the event and upserts it into `source_items` with `window: "selected"` (D54: "the selected trials", not "held-back"), `sets`, its position in the set and `source_date` (the trial's `last_update_posted`). The set must produce at least the allowed proposal (NCT04712877 on FoundationOne Liquid CDx) and the blocked one (NCT04712877 on FoundationOne CDx).
- **Files this PR owns:** backend/dxp/sources/load.py, backend/dxp/sources/selected.json, their tests
- **Done when:** the Story 1.4 criteria this scope covers pass, all 20 trials fetch and load idempotently on the sandbox in the listed order, and the PR is merged. The load runs again in I1's first step.

### A06: Ledger with the policy gate

- **Owner:** Luis · **Story:** 1.6, 9.3 · **Branch:** `story/9.3-policy-gate` · **Forecast:** 11:45 to 13:45, with a third builder on `ledger/apply.py` · **Critical, no slack**
- **Start when merged:** A01, A02
- **Merge after:** A03
- **Never stubbed (D37):** if A06 is late, it gets more builders; nothing replaces it with a stub.
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:**
  - **Gate.** `gate.evaluate(ctx, action)` with the five checks in order (`grant_active`, `team_scope`, `destination_action`, `evidence_checks`, `run_authorised`), each returning the failed check by name, using `gate.policy_sets` from A03. Check 1 evaluates the latest grant version (for a Reviewer write, the caller's grant) and records it beside the run's pinned version; if they differ and the latest is not active, it fails. Check 2 passes for a Diagnostic in `scope.diagnostic_ids`, including one the action would create, or for `seed@v1` with `{ all: true }` (D16, D28). Check 3 passes only when the kind and destination are both in the grant: a `notify_slack` to any destination other than `slack:#all-mango-db-hackathon` fails it (S2). Check 4 applies only to `file_proposal` and `notify_slack`; for `apply_value` (seed), `decide_proposal`, `review_value` and `resolve_notification` it records `n/a` (D16, D50, S8). Check 5 passes only when the action holds an `admitted` admission for this run and the run is not `stopped`; for Reviewer and seed writes it records `n/a`.
  - **Decisions.** Every evaluation inserts one `decisions` document through `gate/decisions.py` (D5), insert-if-absent on its derived `decision_id` (D20: `run_id` or `"-"`, kind, `diagnostic_id`, then the `action_id` for `resolve_notification` (D49), else `proposal_id`, else `value_id`, else `"<field>|<value>"`, plus `request_id` for Reviewer decisions); `agent` and `initiated_by` as D19 for run, Reviewer and seed decisions. On `allowed` the gate inserts the `actions` document (`queued`, with `decision_id`, ID derived the same way with `act_`) and emits `action_allowed`; on `blocked` it emits one `action_blocked` event carrying the `decision_id` and nothing else. The decision's `seq` is set from that event (D21).
  - **Filing.** `ledger.file()` calls the gate before every write. In `live` mode A10 calls it once for each admitted change, so the gate is evaluated once per change and each filed proposal is its own Decision (D46). In `live` mode an agent never applies (D28): every change, to an existing Diagnostic or to one the run itself created, is filed as a `pending` proposal (with `run_id` and `decision_id`, event `proposal_pending`) and the action is then set `done` (AD-4, D8). There is no branch that applies a live change at once. Creating a Diagnostic outside the grant's scope is blocked by check 2. Seed writes (`baseline` mode) are not agent writes: they carry the seed stamp and `run_id: null`, are accepted only with `DXP_SEED_KEY` from the command line under `seed@v1` (no API route accepts it), need no run admission (D4), carry their own derived `p_` IDs (D20) and apply at once through `ledger.apply`.
  - **Apply and recovery (D26, D27), `ledger/apply.py`.** `ledger.apply(proposal_id)`: claim `pending` → `applying` (conditional); one guarded update on the Diagnostic that writes the value and adds the proposal ID to `applied_proposal_ids` only if it is not already there; upsert the derived edges, with `run_id`, `seq` and `proposal_id` set by `$setOnInsert` so a later run never takes over an earlier run's edge, and only `status` set to `applied`; emit `value_applied` with `dedupe_key`; mark the proposal `applied`. `ledger.recover_applying()`: for a proposal stuck in `applying`, rerun the guarded update (a no-op if done), then always re-upsert its edges and re-emit its event, whatever the guard returned, then mark it `applied`. Recovery runs at API start (A01's startup hook), at the start of every run (A10) and on every decision call (A14). A14 calls `ledger.apply`; nothing else applies a change.
- **Required behaviours:**
  - **Blocked action:** one `decisions` document with every check, the grant evaluated and the policy-set version; one `action_blocked` event with its `decision_id`; no action, no business-record change, no external call.
  - **Authority:** every agent write needs a `run_id` and a context from `runs.context()`, whose key resolves to the run's `agent`; a client-supplied name never confers permission.
  - **Audit reconstruction (fields this PR writes):** each decision keeps its inputs, evidence reference, checks, grant evaluated, policy-set version, outcome and the proposed and decided timestamps.
  - **Stop semantics (check 5):** the action holds an `admitted` admission for this run, and the run is not `stopped`.
- **Files this PR owns:** backend/dxp/gate/ including gate/__init__.py and gate/decisions.py (except policy_sets.py, seed.py and seed_data/, which are A03's, and drafts.py, which is A17's), backend/dxp/ledger/__init__.py, backend/dxp/ledger/file.py, backend/dxp/ledger/types.py, backend/dxp/ledger/apply.py, their tests
- **Done when:** tests prove each of the five checks blocks on its own (check 3 with a `notify_slack` to another destination), a blocked action leaves the record untouched, sends no Slack message and writes one decision, a live change to an existing Diagnostic or to a Diagnostic the run created becomes a pending proposal with no record change, two concurrent applies of one proposal apply it once, a crash in `applying` recovers to `applied` with one update, its edges and one `value_applied` event, and a second run's apply never changes an earlier edge's `run_id`; the Story 1.6 and 9.3 criteria pass; the PR is merged.

### A07: Runs, admissions and stop

- **Owner:** Luis · **Story:** 9.1, 9.5 · **Branch:** `story/9.5-runs-stop` · **Forecast:** 11:45 to 13:30 · **Critical, 15 minutes slack**
- **Start when merged:** A01
- **Merge after:** A03
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Never stubbed (D37).**
- **Scope:** `POST /runs { grant_id, set }` (no `team_id`: the grant defines the Team, D18) through `runs.start(caller, grant_id, set)`: resolve the caller from `X-DxP-Key` (401 only for an unknown key, D17), load the latest grant version, check it is active, unexpired and that the caller is in `startable_by` (403, no run), then create the run (`_id` `run_<random>`) with `agent` = the grant's `principal`, `initiated_by` = the caller, `team_id` and `acting_for` from the grant, model, prompt version, and the grant and policy-set versions pinned; 409 while another run is `running` or `stopping`; then `.spawn(run_id)` on the run function passed to `create_app()`. `runs.context(run_id, key)`, refusing unless the key resolves to the run's `agent`. `runs.stamp(run_id)`, the only stamp maker for run writes. **The admission API, under the frozen public names (D22), implemented in `runs/admissions.py` and exported from `runs/__init__.py`:**
  - `runs.admit(run_id, item_key)`, one admission per action, `item_key` = `"<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"`, in one transaction (conditional `$inc` of `admitting` on a `running` run, then the insert with a 10-minute lease);
  - `runs.release(admission_id)`, a conditional `admitted` to `released`, then `settle`;
  - `runs.sweep(run_id)`: marks expired leases `abandoned` and returns the actions they held; it touches no action, and the `runs` package imports nothing from `actions` (D43);
  - the sweep's background task in `routes_runs.py`: calls `runs.sweep(run_id)`, then A09's `actions.mark_failed(action_id, "abandoned_before_send")` for each held `queued` action and `actions.mark_unknown(action_id, "abandoned_in_flight")` for each held `dispatching` action, which is never retried and waits for a Reviewer's resolution (S8), then `runs.settle(run_id)` (D24, D43);
  - `runs.settle(run_id)`: only `stopping` to `stopped`, when no `admitted` admission remains (D23);
  - `runs.finish(run_id)`: `running` to `done` once no `admitted` admission remains, called by the pipeline after the last item (D23). A run becomes `failed` only when the pipeline raises an error it cannot recover from.

  `runs.stop()`; `run_status_changed` on every status change; `GET /runs`; `GET /runs/<run_id>` with `in_flight` counted from admissions and `counts` including `early_research` (D29). Neither `GET /runs/<run_id>` nor `POST /runs/<run_id>/stop` calls Slack: each starts the sweep's background task and returns current state, showing a `dispatching` action the sweep is settling as `reconciling` (read time only, D24, S7).
- **Required behaviours:**
  - **Stop semantics:** as the table above (D7, D22 to D24): admission only while `running`, admitted actions may finish while `stopping`, release once, abandoned leases settled by the background task (`queued` through `actions.mark_failed`, `dispatching` through `actions.mark_unknown`, never retried), `stopped` when no `admitted` admissions remain, `done` only through `runs.finish`.
  - **Authority:** `initiated_by` comes from the caller's key and must be in `startable_by`; `agent` comes from the grant; neither ever comes from the request body.
- **Files this PR owns:** backend/dxp/runs/ (including `runs/__init__.py` and `runs/admissions.py`), backend/dxp/api/routes_runs.py, their tests
- **Done when:** a concurrency test fires stop and admissions together and never admits after stop; two actions from one item for the same Diagnostic get two admissions; a second release is a no-op; `settle` never ends a `running` run; an expired lease is abandoned and `runs.sweep` returns its held actions; the background task fails its `queued` action through `actions.mark_failed(action_id, "abandoned_before_send")` and makes its `dispatching` action `unknown` through `actions.mark_unknown(action_id, "abandoned_in_flight")`, not retried; nothing under `runs/` imports `actions`; and `GET /runs/<run_id>` returns without waiting on the sweep; a caller not in `startable_by` gets 403; the Story 9.1 and 9.5 criteria pass; the PR is merged.

### A08: Extraction with quote and support checks

- **Owner:** Luis · **Story:** 1.5 · **Branch:** `story/1.5-extraction` · **Forecast:** 11:45 to 13:45 · **Critical, no slack**
- **Start when merged:** A01
- **Merge after:** A05
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `llm.extract(item, aliases)` (Sonnet 5.5) and `llm.check()` through the one `llm` module: one Finding per Diagnostic named, raw value, quote and confidence per field, backoff and failure records. Extraction is alias-constrained (D31): the caller passes the seeded alias list (the FDA names plus A02's hand-written aliases) into the prompt, and each Finding's assay name must be one of those aliases or `new`; anything else is a failure record. `evidence.quote_in_source()` and the support check, a value passes only when both are true. Tune the prompts on the selected set until quotes are found, including both Diagnostics named by NCT04712877. No PubMed text in any file.
- **Files this PR owns:** backend/dxp/llm/ (client, extract, check, prompts; except prompts/policy_draft.*, which is A17's), backend/dxp/evidence/ including `evidence/__init__.py` (D36), their tests
- **Done when:** extraction over the selected set returns Findings with found quotes, and NCT04712877 yields two Findings named "FoundationOne Liquid CDx" and "FoundationOne CDx" (or their aliases), never `new`; the Story 1.5 criteria pass; the PR is merged.

### A09: Slack notifier

- **Owner:** Luis · **Story:** 9.4, "External action: a Slack alert for diagnostic evidence" · **Branch:** `story/9.4-slack-notify` · **Forecast:** 11:45 to 13:45 · **Critical, no schedule slack**
- **Start when merged:** A01 (A03 lands at 12:30; until then the agent codes against the frozen grant shapes)
- **Merge after:** A03
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only). The script Luis used to test the webhook before the event is not reused (S12).
- **Never stubbed (D37).**
- **Scope:** `actions.dispatch()` for `notify_slack` actions to `slack:#all-mango-db-hackathon`, using a context from `runs.context()` (the worker's key must resolve to the run's `agent`). Notify only (S4): the message has links and no interactive elements, Slack sends nothing back, and DxP exposes no Slack callback route. Approval and rejection happen in DxP, never in Slack.
  - **Configuration (S3).** `backend/dxp/actions/slack.py` reads `SLACK_WEBHOOK_URL` (only in `.env` and the Modal secret; never committed, logged, put in an error message, an Action `result` or on screen) and `DXP_BASE_URL`. The sender refuses to start if `DXP_BASE_URL` is not set (S6).
  - **Order (S7).** Call `gate.evaluate()` first, which saves the action ID before anything is sent, and send nothing when blocked. Claim atomically (`queued` to `dispatching`, conditional, `claimed_at`) so two workers never both send it.
  - **The message (S5).** A Block Kit alert: header "New diagnostic evidence for review" plus the action ID; the Diagnostic name; the evidence (the trial NCT ID with its ClinicalTrials.gov link, and the quote cut to at most 300 characters); the proposed change (for example "Add trial NCT04712877 to Trials"); who acted (the agent, the run ID, the grant `{grant_id}@v{version}` and the policy set `ps_…`); a context line "Approve or reject in DxP. Slack only notifies."
  - **Links back to DxP (S6).** "Review in DxP" → `${DXP_BASE_URL}/review?proposal=<p_id>` (B04's Review page, focused); "Open diagnostic" → `${DXP_BASE_URL}/diagnostics/<dx_id>` (B04's Record page).
  - **Outcome (S7).** Post once and record what was observed, setting `posted_at`, `observed_at` and `result { http_status, response_body, posted_at, link_urls { review_url, diagnostic_url } }` (D44): HTTP 200 with body `ok` → `delivered`; another 4xx (for example `invalid_payload`, `no_service`, `channel_not_found`) → `failed`, never retried; HTTP 429 → nothing was posted, so retry once after `Retry-After` while still holding the claim, and a second 429 → `failed`; timeout, connection error or HTTP 5xx → `unknown`, never retried automatically. Every update is conditional on the current status. Emit `action_status_changed` on every status change. A09 writes only `actions` (and, through the gate, `decisions`); it never writes to `proposals`: a proposal's `notification` is built at read time by A14 and A11 (D47).
  - **Sweep hooks (S8, D43).** `actions.mark_unknown(action_id, error)`: a conditional `dispatching` to `unknown`, never retried; `actions.mark_failed(action_id, error)`: a conditional `queued` to `failed`. Both are called only by the sweep's background task in A07's `routes_runs.py`, with the actions `runs.sweep` returned, as `mark_unknown(action_id, "abandoned_in_flight")` and `mark_failed(action_id, "abandoned_before_send")`. The name `mark_abandoned` is retired.
  - **Manual resolution (S8).** `actions.resolve(action_id, outcome, note, reviewer)` behind `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }` (`routes_resolve.py`): a Reviewer settles an `unknown` notification after checking the channel for the action ID. It is gated as kind `resolve_notification` under the Reviewer's grant (`sam@v1`; check 4 and check 5 record `n/a`), with the `action_id` as the Decision and Action ID target (D49), written as a Reviewer Decision with the Reviewer stamp, a server-generated `request_id` and `cause { proposal_id, origin_run_id }`, so it appears under "After the run"; then a conditional `unknown` to `delivered` or `failed`, recording `resolution { outcome, note, decision_id, by, at }` (D44). Any other current status returns 409 and changes nothing.
  - **Tests.** A fake Slack sender for tests, with `ok`, 4xx, 429 (with `Retry-After`), timeout, connection-error and 5xx modes; the integrator's smoke test uses it so merges post nothing to the channel.
- **Required behaviours:**
  - **Ambiguous external result:** save the action ID first; if the outcome is uncertain, mark it `unknown` and never retry; a Reviewer resolves it in DxP.
  - **Concurrent retries:** claim the action atomically in Atlas (`queued` to `dispatching` with a conditional update) so two workers can never both send it.
  - **Blocked action:** `dispatch` sends nothing when the gate blocks it.
  - **Authority:** a key that does not resolve to the run's `agent` is refused before the gate; `resolve` takes the Reviewer from the key, never from the body.
  - **Audit reconstruction (fields this PR writes, S9):** the destination, the claimed, posted and observed timestamps, and the result (HTTP status, Slack's response body and the link URLs sent), or `unknown` and its resolution.
- **Files this PR owns:** backend/dxp/actions/ (`__init__.py`, dispatch, `slack.py`, resolve, `mark_unknown` and `mark_failed`, the fake sender), backend/dxp/api/routes_resolve.py, their tests
- **Done when:** tests prove two concurrent dispatches post once; `ok` ends `delivered`; a 4xx ends `failed` with no retry; a 429 is retried once after `Retry-After` and a second 429 ends `failed`; a timeout, connection error or 5xx ends `unknown` and is never retried; a late update does not overwrite `unknown` or a resolution; `mark_unknown` moves only a `dispatching` action and `mark_failed` only a `queued` one; no code path writes to `proposals`; `resolve` settles only an `unknown` action and writes one Reviewer Decision; the sender refuses to start without `DXP_BASE_URL`; no test output or log contains the webhook URL. On the sandbox, a real alert is posted to `#all-mango-db-hackathon` and ends `delivered`, and its two links resolve on the deployed web app (once B04 is deployed; the integrator confirms it in I1, or in I2 if B04 is late). The Story 9.4 criteria pass; the PR is merged.
- **Size against the GitHub plan:** likely slightly simpler: no read-back, no listing or pagination for reconciliation, one HTTP call with no response to parse, against a new resolve route and the Block Kit layout. The forecast is kept at 13:45 because A06 and A08 still end at 13:45, so the critical path does not change.

### A10: The run

- **Owner:** Luis · **Story:** 1.7 · **Branch:** `story/1.7-run` · **Forecast:** 11:45 to 13:30 · **Critical, 15 minutes slack**
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks (real modules are wired in I1)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `pipeline.run(run_id)`, the run function A04 wraps and A07 spawns; it executes with the agent's key (`DXP_AGENT_KEY`) and the `run_id` and builds its context with `runs.context()`. It first calls `ledger.recover_applying()` (D26). One LangGraph run over the selected set, in the `selected.json` order (D30), at low concurrency; with `DXP_DEMO_PACE` set (A10 owns this variable, D33) it processes one item at a time and waits a few seconds per item, so the first item is NCT04712877 and a stop lands while items remain. For each item: `llm.extract(item, aliases)` with the seeded alias list (D31) and `llm.check()`; then, after extraction and before the gate, one admission per action (D22): `runs.admit(run_id, item_key)` with `item_key` = `"<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"` (`None` ends that step with no action), then `ledger.file()` once for each admitted change (D46: one change per call, so one gate evaluation per change and one pending proposal per allowed change) or, once that proposal is filed, `actions.dispatch()` (its own `notify_slack` alert, with the `proposal_id` in its `item_key`; one alert per filed proposal), each of which calls the gate, and `runs.release(admission_id)` in a `finally` once the action is blocked, `done`, `delivered`, `failed` or `unknown`. A blocked proposal gets no notification (S11). Stops admitting when the run is stopped. After the last item it calls `runs.finish(run_id)`; an error it cannot recover from marks the run `failed` (D23). Built against stubs of the frozen signatures.
- **Files this PR owns:** backend/dxp/pipeline/, its tests
- **Done when:** the run completes over stubs with one pending proposal, one Slack notification for it (fake sender) and one blocked action with no notification; an item with two allowed changes makes two `ledger.file` calls, two proposals and two alerts; every admission is released once, the run ends `done` through `runs.finish`, and with `DXP_DEMO_PACE` set the items run one at a time in the listed order; the Story 1.7 criteria this scope covers pass; the PR is merged.

### A11: Audit API

- **Owner:** Luis · **Story:** 9.6 · **Branch:** `story/9.6-audit-api` · **Forecast:** 11:45 to 13:30 · **Critical, 15 minutes slack**
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `search.audit` and `GET /runs/<run_id>/audit`: the run's `decisions` in `seq` order (D21), allowed and blocked, each with its action when allowed; for a notification: status, destination, the queued, claimed, posted and observed timestamps, and the result (HTTP status, Slack's response body and the link URLs sent) or `unknown` with any resolution (S9), plus the proposal's live DxP review status (pending, applied or rejected, with who decided and when), read from `proposals` at request time; then the section **"After the run"** with the Reviewer decisions whose `cause.origin_run_id` is this run, including `resolve_notification` decisions. Every decision carries `authorised_by`, which answers "who authorised this" (agent, initiated by, acting for, granted by, the grant and version evaluated, expiry, policy-set version); screens read it from the Decision, never from `GET /actions/<action_id>` (D40). `GET /decisions/<decision_id>`: audit detail for any entry, allowed or blocked (D5). `GET /actions/<action_id>` (status and result) and `GET /actions?run_id=&status=`, with `result` and `resolution` in the D44 shapes. Wherever the audit shows a proposal, its `notification { action_id, status, posted_at }` is built at read time from the proposal's `notify_slack` action, never written to the proposal (D47). A11 only reads: it never calls `runs.sweep`, `actions.mark_unknown` or `actions.mark_failed`; settling abandoned actions is the background task in A07's `routes_runs.py` (D43). Built from `decisions`, `actions`, `runs` and `events`, with grants and policies read at the recorded versions; nothing is recomputed from current grants or policies.
- **Required behaviours:**
  - **Audit reconstruction:** every decision with inputs, evidence reference, checks, grant evaluated, policy-set version, outcome and timestamps; allowed notifications with their Slack result and the proposal's live review status.
  - **Blocked action:** the blocked decision appears in the trail with the failed check, and `GET /decisions/<decision_id>` returns it.
  - **Authority:** "who authorised" reports the server-resolved `initiated_by`, `agent` and grant, never a client-supplied name.
- **Files this PR owns:** backend/dxp/search/audit.py, backend/dxp/api/routes_audit.py, backend/dxp/api/routes_actions.py, their tests
- **Done when:** the trail for a fixture run with a pending proposal, a delivered Slack notification, a blocked action and a later Reviewer decision reconstructs all four in order with every field above, and the notification entry's review status changes from pending to applied after the Reviewer accepts; the Story 9.6 criteria pass; the PR is merged.

### A12: Change-stream feed

- **Owner:** Luis · **Story:** 9.9 · **Branch:** `story/9.9-change-feed` · **Forecast:** 12:00 to 13:00 · **Supporting (check S1)**
- **Start when merged:** A01, A04
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** The live action feed for a run, served to the web as `GET /changes?after=<seq>&run_id=` over `events` (AD-10, AD-23). With `DXP_FEED=change_stream` it waits up to 25 seconds, woken by `events.watch()` on inserts; with `DXP_FEED=poll` (when A04 found no change streams on the sandbox) it returns at once and the web app polls every 2 seconds. The query on `seq` is the only source of truth, and the response is the same either way. Nothing core waits for it: until it passes S1, the Run console polls `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` (D40). Cuttable (D37).
- **Files this PR owns:** backend/dxp/search/changes.py, backend/dxp/api/routes_changes.py, their tests
- **Done when:** an action written on the sandbox appears in the feed within a few seconds, by change stream or polling; the Story 9.9 criteria pass; the PR is merged; S1 passes.

### A13: Fetch the FDA list and seed through the ledger

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2b-seed` · **Forecast:** 12:45 to 13:30 (30 minutes added for the live fetch, absorbed by starting earlier; the sandbox seed moved to I1, D38; the reset script, moved here from A16 by D41, is written by a second builder in parallel, so the forecast is unchanged) · **Critical, 15 minutes slack**
- **Start when merged:** A01, A02 (the agent codes against the frozen `ledger.file` and `ledger.apply` signatures; A06 merges at 13:45)
- **Merge after:** nothing beyond its own checks: A13 merges on fake-gate tests (D38). It does not need A06 or A14 to merge (D26)
- **Prepared material (D1):** fetch during the event. No code from `scripts/data/` or `dxp-*` skills (reference docs only); no files from `data/` unless an organiser clears them in writing.
- **Scope:** Two commands, always run in this order, and named the same everywhere (D40): `python -m dxp.sources.fda_cdx`, then `python -m dxp.ledger.seed`.
  - `python -m dxp.sources.fda_cdx` fetches the FDA list of cleared or approved companion diagnostics during the event, keeps the lung rows ("FoundationOne Liquid CDx", "FoundationOne CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay" among them) and writes them to `source_items` with source `fda_cdx_list`, `source_item_id` = `<PMA or 510(k) number>:<first 8 hex characters of sha1 of the normalised row>`, because one number covers many drug rows (D45, replacing the number-only rule of D31), and `source_date` = fetch date. It needs no ledger.
  - `python -m dxp.ledger.seed` reads those `fda_cdx_list` source items and seeds, from the command line with `DXP_SEED_KEY` under `seed@v1`, the Diagnostics through `ledger.file()` in `baseline` mode (each Diagnostic's ID alias is `normalise_name()` of the trade-name column, D31; every device and trade name becomes an alias, plus A02's hand-written aliases), and three synthetic Teams, including "Team Liquid Biopsy Dx" (D56). Writes carry `{ kind: "seed", principal: "seed" }` and `run_id: null`; seed changes carry their own derived `p_` IDs (D20). Idempotent.
  - `GET /teams` (the Run console labels each grant with its Team).
  - If the FDA page cannot be fetched or parsed by 13:15, seed only the Diagnostics the selected set names, typed from the FDA page during the event; Luis tells B07, which says so in the README (D36: A13 does not edit the README).
  - **Snapshot and reset (D34, D41).** A13 owns the snapshot procedure and `scripts/reset_demo.py`; a second builder writes them in parallel from 12:45, so the forecast holds. The snapshot: after the four seed commands and before any run, `mongodump` of database `dxp` to a folder outside the repository; I1's first step runs it. `scripts/reset_demo.py` restores it: `delete_many({})` on every collection (dropping would delete validators and indexes), then `mongorestore` the dump. It touches nothing outside Atlas: old Slack alerts stay in `#all-mango-db-hackathon`, and the reset posts nothing there; a new run gives new action IDs, so the new alert is told apart by its action ID. If the snapshot is missing, it reruns the four seed commands in I1's order and dumps again. It resets only the demo database `dxp`; the smoke database `dxp_smoke` is never snapshotted or reset. The reset runs at the start of I2, before each A16 rehearsal, before the video and before the live demo; A16 and R1 use it and never edit it.
- **Files this PR owns:** backend/dxp/sources/fda_cdx.py, backend/dxp/ledger/seed.py, backend/dxp/api/routes_teams.py, scripts/reset_demo.py, their tests
- **Done when:** `python -m dxp.sources.fda_cdx` fetches and parses the live list and writes the lung rows with the D45 row IDs (two drug rows under one PMA number get two IDs); `python -m dxp.ledger.seed` passes its tests against a fake gate and ledger, run twice with no duplicates and with both FoundationOne Diagnostics and their aliases seeded; `scripts/reset_demo.py` restores a dump into a test database with validators and indexes intact; the Story 1.2 seed criteria this covers pass; the PR is merged. The real seed and the snapshot on the sandbox are I1's first step (D38, D41).

### A14: Proposals, decisions and value review API

- **Owner:** Luis · **Story:** 2.2, 2.3 · **Branch:** `story/2.3-proposals-decisions` · **Forecast:** 11:45 to 13:15 (apply moved to A06, D26), merged after A06 at about 13:45 · **Core (D35; in core acceptance, I2)**
- **Start when merged:** A01
- **Merge after:** A06 (decisions call the real gate and `ledger.apply`)
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `GET /proposals?status=&field=&diagnostic_id=&run_id=` and `GET /proposals/<p_id>` (one proposal, whatever its status; 404 in the error shape if unknown; the target of the Review page's `?proposal=<p_id>` focus; there is no `p_id=` query parameter, D42), each proposal with `decision_id` and `notification { action_id, status, posted_at }` built at read time from the `notify_slack` action for that proposal (D29, S10, D47), or null when none was sent; nothing writes `notification` to the proposal document. The Review count polls `?status=pending`. `POST /proposals/<p_id>/decision { action, value, reason }` (accept, edit, reject; `edit` and `reject` need a `reason`, D16) through `ledger/decide.py`, action kind `decide_proposal`, returning `{ proposal, decision, rule_draft }`. `POST /diagnostics/<dx_id>/values/<value_id>/review { action, value, reason }` through `ledger/review.py`: Accept, Edit or Reject an unreviewed value, action kind `review_value` (D16, D40). Both call `ledger.recover_applying()` first (D26), then the gate with the Reviewer's grant `sam@v1` (check 4 records `n/a`), then, when allowed, A06's `ledger.apply(proposal_id)`; A14 writes no apply code. The Reviewer is resolved from the key; Reviewer decisions are written to `decisions` with `run_id: null`, `agent: null`, `initiated_by` = the Reviewer (D19), the Reviewer stamp, a server-generated `request_id` (D20) and `cause: { proposal_id, origin_run_id }` (D4), and are allowed without a run ID. History kept, every write stamped; `rule_draft` is always null. Minimal: no rule flags, no learned rules.
- **Files this PR owns:** backend/dxp/ledger/decide.py, backend/dxp/ledger/review.py, backend/dxp/api/routes_proposals.py, backend/dxp/api/routes_review.py, their tests
- **Done when:** tests prove an accept applies through `ledger.apply` once, a blocked Reviewer decision can be retried and gets a new Decision, a Reviewer decision carries `run_id: null`, `agent: null` and its `cause`, an `edit` or `reject` without a reason is refused, a proposal carries `notification { action_id, status, posted_at }` built at read time from its `notify_slack` action (the stored proposal has no `notification` field), `GET /proposals/<p_id>` returns a pending, applied or rejected proposal and 404 for an unknown ID, and the review endpoint accepts, edits and rejects a value; the trimmed Story 2.2 and 2.3 criteria pass; the PR is merged.

### A15: Graph API by run

- **Owner:** Luis · **Story:** 5.1 · **Branch:** `story/5.1-graph-api` · **Forecast:** 12:00 to 13:30 · **Supporting (check S2)**
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `GET /graph?run_id=` returns the changed elements only: the values, proposals, edges and notification nodes (`notification:<action_id>`, linked to their proposal, S10) the run itself created or changed, each with its `run_id` (D12); each `Link` carries `status` (`pending` or `applied`) and `proposal_id` (D29). `GET /graph?run_id=&context=true` adds a touched Diagnostic's other neighbours through `$graphLookup`, each marked `context: true` and not attributed to the run. Cuttable (D37): only B05 calls it.
- **Files this PR owns:** backend/dxp/search/graph.py, backend/dxp/api/routes_graph.py, their tests
- **Done when:** for a fixture run, the default response has no element without the run's `run_id`, and context elements appear only on request and are marked; the trimmed Story 5.1 criteria pass; the PR is merged.

### A18: Read model and Diagnostics API

- **Owner:** Luis · **Story:** 1.1 · **Branch:** `story/1.1b-readmodel` · **Forecast:** 11:45 to 12:45, merged after A06 at about 13:45 · **Core (in core acceptance, I2)**
- **Start when merged:** A01
- **Merge after:** A06
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `search.readmodel.get_diagnostic(dx_id)` and `GET /diagnostics/<dx_id>`, returning the `Record` with `applied_proposal_ids` (D29) and each value with its Evidence, the `run_id` that last changed it and its review state, plus the Diagnostic's pending proposals. No Diagnostics list: `GET /diagnostics` stays 501 and there is no list function (D40); the Record page is reached from Review, Audit and Impact links.
- **Files this PR owns:** backend/dxp/search/readmodel.py, backend/dxp/api/routes_diagnostics.py, their tests
- **Done when:** the route returns the A01 `Record` shape for seeded fixtures; the Story 1.1 read criteria this covers pass; the PR is merged.

### I1: Integration, the allowed-and-blocked loop

- **Owner:** Luis · **Story:** 9.3, 9.4 · **Branch:** `integration/i1-allowed-blocked` · **Forecast:** 13:45 to 14:30 · **Critical**
- **Start when merged:** A03, A04, A05, A06, A07, A08, A09, A10, A11, A13 (core PRs only; A04 directly, because I1 needs the deploy, `DXP_BASE_URL` and the Modal secret, D51; not A12, not A14, D26)
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Fixes are written during the event.
- **Scope:**
  1. **Seed the sandbox (13:45 to 14:00, D38),** in this order: `python -m dxp.gate.seed` (the agent grant `lbdx@v1`, `sam@v1`, `seed@v1`, policies); `python -m dxp.sources.load --set selected` (the 20 trials); `python -m dxp.sources.fda_cdx`, then `python -m dxp.ledger.seed` (Diagnostics, aliases, Teams). Then take the seeded snapshot with A13's procedure (`mongodump` of database `dxp` to a folder outside the repository, D34, D41); A13's `scripts/reset_demo.py` restores it before every later take. The integrator's smoke test is seeded separately in `DXP_DB=dxp_smoke`, never in `dxp`.
  2. **The loop (14:00 to 14:30).** Wire the real modules into the run on the sandbox. A run over the selected set proves, as "at least" assertions because other selected trials may file more proposals, each with its own alert (D46): both NCT04712877 Findings resolve to the seeded FoundationOne Liquid CDx and FoundationOne CDx (D31); at least the proposal to add NCT04712877 to FoundationOne Liquid CDx is filed as `pending`, with its quote; its Slack alert is `delivered` (HTTP 200, body `ok`) and is seen in `#all-mango-db-hackathon` with its action ID (S7), and every filed proposal has exactly one alert; the FoundationOne CDx change is blocked before execution on `team_scope`, and no Slack message is sent for it; the audit API reconstructs all three with `initiated_by`, `agent`, the grant evaluated, policy-set version and result (HTTP status, response body, link URLs). Both alert links, `${DXP_BASE_URL}/review?proposal=<p_id>` and `${DXP_BASE_URL}/diagnostics/<dx_id>`, resolve on the deployed web app (S6); this needs B04 deployed (forecast 14:00), the loop does not wait for it, and if B04 is late the link check moves to I2. It does not apply the proposal: applying happens only through a Reviewer decision (A14), proved at I2.

  What breaks is fixed in small PRs to the owning file, each reviewed by that file's owner (D36), never edited from this branch.
- **Required behaviours checked here:** all six, end to end.
- **Files this PR owns:** none; it holds the integration test and its notes only (`backend/tests/i1/`)
- **Done when:** the seed and snapshot are done, the loop passes on the sandbox by 14:30, and the PR is merged.

### A17: Stretch, rejection drafts a policy

- **Owner:** Luis · **Story:** 9.11 · **Branch:** `story/9.11-policy-draft` · **Forecast:** 14:30 to 15:30 · **Stretch (check S4), only if I1 is green**
- **Start when merged:** I1 green
- **Merge after:** A14
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** When Sam rejects a proposal with a reason, the model drafts a policy as structured data: a `requires` object limited to `quote_found`, `supported` and `min_confidence`, with `applies_to`; it stays `draft` until a person principal approves it through `POST /policies/<policy_id>/approve { version }`, and then becomes a new `active` version and a new policy-set version. Model prose is never executable authority. Cuttable (D37): `rule_draft` stays null and the approve route stays 501.
- **Files this PR owns:** backend/dxp/gate/drafts.py, backend/dxp/llm/prompts/policy_draft.*, backend/dxp/api/routes_policy_drafts.py
- **Done when:** the Story 9.11 criteria pass; the PR is merged; S4 passes.

### I2: Core acceptance

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `integration/i2-acceptance` · **Forecast:** 15:00 to 15:30 · **Critical**
- **Start when merged:** I1, A14, A18, B02, B03, B04 (core PRs plus the minimal Record and Review screen; no supporting or stretch item)
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Fixes are written during the event.
- **Scope:** Core acceptance, not first contact. It starts with a reset: `scripts/reset_demo.py` (A13) restores the seeded snapshot, forecast 10 minutes inside the 15:00 to 15:30 slot (D41), so the I1 loop's run, proposals and actions are cleared from Atlas (its Slack alerts stay in the channel). The acceptance itself then has about 20 minutes. Then the core loop on the sandbox through the screens, with `DXP_DEMO_PACE` set, in the D33 order. Start a run from the Run console (choosing the agent grant, labelled with its Team); actions appear (through `/changes` if S1 passed, otherwise by polling `GET /runs/<run_id>` and the audit), the allowed one as "Slack alert delivered" with its time; see the alert in `#all-mango-db-hackathon`; see the blocked FoundationOne CDx action and its failed check, with no Slack message; stop the run while items remain (`stopping`, then `stopped`); Sam opens the alert's "Review in DxP" link, which lands on the focused proposal (loaded through `GET /proposals/<p_id>`, D42), and approves it there; it is applied once and the audit's review status shows applied; the Audit view answers "Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?", with Sam's approval under "After the run". Supporting and stretch items are checked separately (S1 to S4). Fixes go in small PRs reviewed by the file's owner (D36).
- **Files this PR owns:** none; it holds the acceptance test and its notes only (`backend/tests/i2/`)
- **Done when:** the Story 8.2 core acceptance criteria pass on the sandbox, and the PR is merged.

### A16: Rehearsal and reset

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `story/8.2-rehearsal` · **Forecast:** 15:30 to 16:15 · **Critical**
- **Start when merged:** I2 (only)
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** A16 uses A13's `scripts/reset_demo.py`; it does not create or edit it (D41). `docs/demo-and-reset.md`: the demo steps in the D33 order (the second screen is Slack `#all-mango-db-hackathon`, S11), `DXP_DEMO_PACE`, and when and how to run A13's reset command. Rehearse the 3-minute live demo and the 60-second video script on the sandbox twice, each from a reset run immediately before it, including only the supporting and stretch items whose check passed. Then run the reset for the video (16:15 to 16:30).
- **Reset slots (D34, D41):** at the start of I2 (15:00); before each rehearsal pass (inside 15:30 to 16:15); before the video, 16:15 to 16:30 (A16); between submission and the live demo, 16:55 to 17:10 (R1).
- **Files this PR owns:** docs/demo-and-reset.md
- **Done when:** the demo runs twice from a reset without a fix, the sandbox is reset for the video by 16:30, and the PR is merged.

### B01: Web skeleton and minimal shell

- **Owner:** Vlad · **Story:** 1.3, 1.12 · **Branch:** `story/1.12-web-shell` · **Forecast:** 10:45 to 12:00
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only). Use a text wordmark, "DxP", in the interface font; the prepared logo images are not used unless an organiser clears them.
- **Scope:** `web/` from `create-next-app` (Next.js 16, TypeScript, App Router, Tailwind), `shadcn init`, and every screen dependency installed up front (including `react-force-graph-2d`) so no screen PR edits `web/package.json`; a `gen:types` script that calls `tools/gen_types.sh`; `web/lib/api.ts` with a generic typed get and post keyed by the paths in `types.ts`, so screens never edit it (a hand stub until A01 lands); `web/lib/features.ts` reading `NEXT_PUBLIC_DXP_FEATURES` (`feed`, `impact`, `audio`); `web/lib/format.ts` with the D40 display formats (grants `{grant_id}@v{version}`, policy sets `ps_ab12… (N policies)`, `run_` and `act_` IDs as stored), so every screen formats them one way; the one server route that adds `X-DxP-Key`; a minimal shell: tokens and fonts from `DESIGN.md`, the text wordmark, a top bar with Run console, Audit, Review and Impact (hidden when `impact` is off) and the read-only "Signed in as" chip from `GET /whoami` (no name picker), badges, toasts, skeletons. No Diagnostics list and no nav item for one (D40).
- **Files this PR owns:** web/ including web/package.json, web/lib/api.ts, web/lib/features.ts, web/lib/format.ts, web/components/shell/; except web/lib/types.ts (A01), web/vercel.json (A04) and the screen paths owned by B02 to B06
- **Design reference:** tokens from `DESIGN.md`; the interface is built during the event
- **Done when:** the trimmed Story 1.3 and 1.12 criteria pass, the skeleton builds locally (`next build`), and the PR is merged. It deploys on Vercel once A04 lands; A04 merges after B01 (D39).

### B02: Run console

- **Owner:** Vlad · **Story:** 9.7 · **Branch:** `story/9.7-run-console` · **Forecast:** 12:00 to 14:15 · **Core**
- **Start when merged:** B01
- **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Start a run with `POST /runs { grant_id, set }` (D18): the console lists the grants the caller may start (`GET /grants`, those whose `startable_by` includes the caller from `GET /whoami`), each labelled with its Team; there is no separate Team picker. Identity card (agent, initiated by, model, prompt version, policy-set version, acting for, grant and scope, in the D40 display formats); action feed with allowed, blocked (failed check named), in flight, `reconciling` and unknown states. A notification's row shows "Slack alert delivered" with the posted time, or Failed, or Unknown (S10); an Unknown row has a Resolve control, shown only when the `actions` of `GET /whoami`'s `Principal { id, name, kind, actions }` include `resolve_notification` (D53), which asks for an outcome (delivered or failed) and a note and calls `POST /actions/<action_id>/resolve` (S8). Nothing in the console links to or acts in Slack. **Polling is the default (D40):** `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` every 2 seconds; `/changes` only when the `feed` flag is on, which it is only if A12 passed S1 (D37). Stop button with `stopping` then `stopped`; links to the Audit view, to the Record page and to the focused Review page; the Impact link only when the `impact` flag is on (D37).
- **Files this PR owns:** web/app/runs/[run_id]/page.tsx, web/app/runs/page.tsx, web/components/run-console/
- **Design reference:** the Run console section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the Story 9.7 criteria pass against the sandbox with the `feed` flag off, and the PR is merged (D37). Feed-on behaviour is checked in S1, not here.

### B03: Audit view

- **Owner:** Vlad · **Story:** 9.8 · **Branch:** `story/9.8-audit-view` · **Forecast:** 12:00 to 14:00 · **Core**
- **Start when merged:** B01
- **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** One run reconstructed decision by decision from `GET /runs/<run_id>/audit`, polled every 2 seconds while the run is `running` or `stopping` (D40): inputs, evidence quote, checks, grant evaluated (`{grant_id}@v{version}`) and policy-set version (`ps_ab12… (N policies)`), outcome and failed check, the timestamps; for a notification its destination, the queued, claimed, posted and observed times, the result (HTTP status, Slack's response body and the link URLs sent) or `unknown` with any resolution, and the proposal's live review status (pending, applied or rejected, with who decided and when) (S9); the "After the run" section with Reviewer decisions, including resolutions; on an `unknown` notification entry, the same Resolve control as B02 (D53): shown only when the `actions` of `GET /whoami`'s `Principal` include `resolve_notification`, it asks for an outcome (delivered or failed) and a note and calls `POST /actions/<action_id>/resolve`; detail for any entry from `GET /decisions/<decision_id>`; a "who authorised this" panel from the Decision's `authorised_by` (D40), never from `GET /actions/<action_id>`. Links to the Record page; the Impact link only when the `impact` flag is on (D37). A "Listen" link to `/runs/<run_id>/briefing`, shown only when the `audio` flag is on.
- **Files this PR owns:** web/app/runs/[run_id]/audit/, web/components/audit/
- **Design reference:** the Audit view section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the Story 9.8 criteria pass against the sandbox, the view answers the scripted question, Resolve appears on an `unknown` notification only for a caller whose `actions` include `resolve_notification`, and the PR is merged.

### B04: Record and Review, minimal

- **Owner:** Vlad · **Story:** 1.3, 2.4 · **Branch:** `story/2.4-record-review` · **Forecast:** 12:00 to 14:00 · **Core (D35; in core acceptance, I2)**
- **Start when merged:** B01
- **Merge after:** A01, A18, A14
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** The Record page from `GET /diagnostics/<dx_id>` (A18) with Evidence on every value and the `run_id` that last changed it; unreviewed values have Accept, Edit and Reject (Edit and Reject need a reason) through `POST /diagnostics/<dx_id>/values/<value_id>/review` (A14, D40). No Diagnostics list: the Record page is reached from Review, Audit and Impact links (D40). A minimal Review queue for one run's pending proposals, each with its notification status ("Slack alert delivered" with the time, Failed or Unknown), with accept, edit and reject with reason (A14). `/review?proposal=<p_id>`, the target of the alert's "Review in DxP" link (S6), opens with that proposal focused, loaded through `GET /proposals/<p_id>` whatever its status (D42; there is no `p_id=` query parameter), and shows "Proposal not found" when that route returns 404; the Review count polls `GET /proposals?status=pending` every 2 seconds until A12 passes S1 (D40).
- **Files this PR owns:** web/app/diagnostics/, web/app/review/
- **Design reference:** the Record and Review section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the trimmed Story 1.3 and 2.4 criteria pass against the sandbox, `/review?proposal=<p_id>` focuses a known proposal and shows "Proposal not found" for an unknown one, `/diagnostics/<dx_id>` serves the Record page on the deployed app (both are the Slack alert's link targets), and the PR is merged.

### B05: Run impact view

- **Owner:** Vlad · **Story:** 5.2 · **Branch:** `story/5.2-impact-view` · **Forecast:** 12:00 to 14:30 · **Supporting (check S2)**
- **Start when merged:** B01
- **Merge after:** A01
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** `react-force-graph-2d` through `next/dynamic` over `GET /graph?run_id=`: the changed elements only (values, proposals, edges and notification nodes `notification:<action_id>` the run created or changed, each with its `run_id`, S10); a "Show context" control that loads `context=true` and draws context neighbours visibly marked as context and not attributed to the run (D12); pending and applied links drawn differently from `Link.status`; click-through to the Record, and from a notification node to its Audit entry (status, posted time, links sent); View as table. Cuttable (D37): with the `impact` flag off nothing links to it.
- **Files this PR owns:** web/app/runs/[run_id]/impact/, web/components/graph/
- **Design reference:** the Run impact view section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the trimmed Story 5.2 criteria pass against the sandbox, and the PR is merged; S2 passes.

### B06: Stretch, spoken audit briefing

- **Owner:** Vlad · **Story:** 9.10 · **Branch:** `story/9.10-audio-briefing` · **Forecast:** 13:00 to 14:30, merged only after the 14:30 loop is green · **Stretch (check S3)**
- **Start when merged:** B01
- **Merge after:** A11, and I1 green at 14:30
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** Built behind the `audio` flag. `GET /runs/<run_id>/audit/audio`: ElevenLabs reads a run's audit summary, a short script built from the `GET /runs/<run_id>/audit` response only, cached in `audio` per run, 503 on failure; the briefing page `/runs/<run_id>/briefing` with play, pause, loading and error states, reached from B03's "Listen" link. Cuttable (D37): with the `audio` flag off the link is hidden and the route stays 501.
- **Files this PR owns:** backend/dxp/api/briefing.py, backend/dxp/api/routes_audio.py, web/app/runs/[run_id]/briefing/, web/components/briefing/
- **Done when:** the Story 9.10 criteria pass, and the PR is merged; S3 passes.

### B07: Submission package

- **Owner:** Vlad · **Story:** 8.3, 8.4 · **Branch:** `story/8.3-submission` · **Forecast:** 13:00 to 14:00
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Prepared material (D1):** none. Write every line; copy nothing from `scripts/data/` or `dxp-*` skills (reference docs only).
- **Scope:** The README (D14), which B07 alone owns (D36): the pivot and problem statement (Statement 1), the prepared vs built-today table (including the Slack incoming webhook and its channel `#all-mango-db-hackathon`, created and tested before the event, with the note that the test script is not reused and the notifier was written during the event (S12); the webhook URL itself never appears; and the modified tracker script, D40), what is not reused and why, the open organiser questions and the clearance answer from `docs/clearance.md`, a note that planning was finished on 13 and 14 November, the MongoDB capability table (only capabilities proven on the sandbox), credits, and links to `docs/deploy.md`, `docs/demo-and-reset.md` and `docs/clearance.md`; if A13 fell back to typed rows at 13:15, the README says so. The submission description. The 60-second video script in the D33 order, with the D52 timings: 0 to 10 s the problem and the scope (the run starts; identity card, grant `lbdx@v1`, policy set); 10 to 30 s the allowed proposal and its Slack alert, then the blocked change: the FoundationOne Liquid CDx proposal filed pending and its alert arriving in Slack `#all-mango-db-hackathon` (the second screen), then the FoundationOne CDx change blocked, with no Slack message (S11); 30 to 45 s stop the run while items remain; 45 to 60 s Sam approves in DxP (following the alert's "Review in DxP" link; it appears under "After the run"), then "who authorised this?" in the Audit view. The existing `README.md` notices in `scripts/data/` and `data/` already say they are not used without written clearance, so B07 adds no NOTICE files (D36). Done by 14:00. Recording and submitting is R1, which adds the video link to the README.
- **Files this PR owns:** README.md, docs/video-script.md, docs/submission.md
- **Done when:** the Story 8.3 criteria and the Story 8.4 script criteria pass, and the PR is merged.

### R1: Record and submit

- **Owners:** Luis and Vlad · **Story:** 8.4 · **When:** 16:30 to 16:55, then the reset 16:55 to 17:10 · **Critical**
- **Needs:** A16 done (including the 16:15 to 16:30 reset for the video), B07 merged
- **Scope:** Record the 60-second video from `docs/video-script.md` on the reset sandbox with `DXP_DEMO_PACE` set, in the D33 order (the second screen is Slack `#all-mango-db-hackathon`, S11), showing only behaviour that passed and never the webhook URL; add the video link to the README (the only README edit outside B07, D36); submit the description, public repository, video and team members by 16:55. Then Luis runs A13's `scripts/reset_demo.py` (16:55 to 17:10) so the live demo at 17:15 starts from the seeded snapshot (D34).
- **Done when:** the submission is confirmed before 17:00 and the sandbox is reset by 17:10.

## Deferred work

Deferred (pivot, 13 Nov). No agent builds these on Saturday. The old PR IDs P01 to P42 and V01 to V19 are retired; do not reuse them.

| Deferred | Stories |
|---|---|
| Full Baseline load and snapshot, scheduled scan, Tavily provider scan | 1.9, 1.10, 1.11 |
| Jobs page (replaced by the Run console, 9.7) | 1.8 |
| Dry run of the Held-back set (the deferred full set; the 20 selected trials of D30 are not deferred), Value history, Learned rules API and Rules on screen | 2.1, 2.5, 2.6, 2.7 (2.6 returns only as stretch Story 9.11) |
| Alerts API, Alerts inbox, Digest, audio briefing and play button (audio returns as stretch Story 9.10) | 3.1, 3.2, 3.3, 3.4, 3.5 |
| Find and Categories: search indexes, query API, comparison table, shortlist, export, add a value, Category landscape, unmatched terms | 4.1 to 4.8 |
| Changed highlight on the graph | 5.3 |
| Memory and resume, synthetic Team history, Home hero and welcome panel | 6.1 to 6.4 |
| Quick capture | 7.1 |
| The broad Home dashboard and the full app shell beyond B01 | parts of 1.12 |
| The Diagnostics list and `GET /diagnostics` (the Record page is reached from Review, Audit and Impact links) | parts of 1.1 and 1.3 (D40) |
| `GET /teams/<team_id>` and `POST /teams/<team_id>/seen` | parts of 5.1 and 6.3 |

Reversal of a run is stretch, outside Story 9.5, and has no PR (D37). It is built only if every core and listed stretch item is done, which the schedule does not expect.
