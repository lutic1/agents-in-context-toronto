---
title: DxP development plan, Saturday 14 November 2026
status: final
created: 2026-11-13
updated: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/build-schedule.md
---

# DxP development plan

Who builds what on Saturday, one pull request at a time, after the approved pivot to Statement 1, "Agents You Can Audit" (`sprint-change-proposal-2026-11-13.md`). The governed agent is the product: it cannot change a record or act in another system without a named identity, a scoped grant, a policy check before the action and an audit trail a reviewer can replay. Screens only inspect it.

Every PR below has an owner, a story, a branch, what must be merged before it starts, what must be merged before it merges, the files it owns and a forecast. Timing, milestones and fallback cuts are in `build-schedule.md`. The forecasts come from a model, not from a validated run; the milestones in `build-schedule.md` are how the day checks them.

## The two lanes

| | Luis | Vlad |
|---|---|---|
| Agents | Up to 44: builders, reviewer agents, the contract keeper and the integrator | Sonnet 5.5 at high effort: one main agent and ten subagents |
| Model budget | Claude plan; the product runs on Luis's API key | Claude Pro plus $300 of API credit (forecast about $100) |
| Owns | The critical path: contract, registry, grants and policies, deploy, ledger and gate, runs and stop, extraction, the GitHub action, the run, audit API, feed, seed, proposals API, graph API, both integrations, rehearsal, stretch policy draft | The web skeleton and shell, Run console, Audit view, Record and Review, Run impact view, stretch spoken briefing, submission package |
| PRs | 19 (A01 to A17, I1, I2) | 7 (B01 to B07) |
| Merge coordinator | Luis, for Luis's lane | Vlad, for Vlad's lane, after Luis's review agent passes each PR |

PR counts are not workload: Luis's lane holds every core back-end behaviour and both integrations, so Luis's attention goes to the loop and its failures.

## Contracts come first, and they cover more than API shapes

A01 and A02 start at 10:45 and merge by 11:45. A03 drafts against A01 from 10:45 and merges after it. Between them they freeze:

- **Every route and response shape** in the AD-14 table of the architecture spine, under `/api/v1`, returning 501 until built: identity (`GET /whoami`), runs (`POST /runs`, `GET /runs`, `GET /runs/<run_id>`, `POST /runs/<run_id>/stop`), actions (`GET /actions?run_id=&status=`, `GET /actions/<action_id>` with `authorised_by`, `POST /actions/<action_id>/reconcile`), audit (`GET /runs/<run_id>/audit`), grants and policies (`GET /grants`, `GET /grants/<grant_id>`, `GET /policies?status=`), the feed (`GET /changes?after=<seq>&run_id=`), diagnostics (`GET /diagnostics`, `GET /diagnostics/<dx_id>`), proposals (`GET /proposals`, `POST /proposals/<p_id>/decision`), teams (`GET /teams`) and graph (`GET /graph?run_id=`).
- **One error shape** for every route: `{ error: { code, message } }`. A blocked action is not an error: it returns 200 with the `Decision`, and it is recorded as one `action_blocked` event, not as an `actions` document (AD-19).
- **The shapes** in `models.py`, exactly as AD-14, and the generated `web/lib/types.ts`:
  - `Run`: `id`, `agent`, `model`, `prompt_version`, `policy_set_version`, `acting_for`, `principal`, `grant_id`, `grant_version`, `team_id`, `mode`, `source`, `set`, `limit`, `status` (`running`, `stopping`, `stopped`, `done`, `failed`), `in_flight`, `counts`, `active`, `failures`, `started_at`, `stopping_at`, `stopped_at`, `finished_at`.
  - `Principal`: `id`, `kind` (`agent`, `person`), `name`, `acting_for`, `grant_id`, `grant_version`.
  - `Grant`: `grant_id`, `version`, `principal`, `kind`, `acting_for`, `granted_by`, `team_id`, `scope.diagnostic_ids`, `destinations`, `actions`, `expires_at`, `status` (`active`, `revoked`).
  - `Policy`: `policy_id`, `version`, `status` (`draft`, `active`, `retired`), `applies_to`, `requires` (only `quote_found`, `supported`, `min_confidence`), `text`, `author`, `approved_by`, `created_at`.
  - `Action`: `id`, `run_id`, `kind` (`file_proposal`, `apply_value`, `decide_proposal`, `create_review_issue`), `destination` (`ledger`, `github:dxp-review-sandbox`), `target`, `inputs`, `evidence_ref`, `stamp`, `decision: allowed`, `checks`, `status` (`queued`, `dispatching`, `sent`, `done`, `failed`, `unknown`), `result` (`issue_number` and `issue_url`, or proposal and value IDs), timestamps `proposed_at`, `decided_at`, `claimed_at`, `sent_at`, `observed_at`, and `authorised_by`.
  - `AuditEntry` and `Audit`: every action of a run in decision order, allowed ones from `actions` and blocked ones from `action_blocked` events, with `decision` (`allowed`, `blocked`), `failed_check` and `authorised_by` (principal, acting for, granted by, grant and version, expiry, policy-set version).
  - `Event` types: `diagnostic_created`, `value_applied`, `proposal_pending`, `proposal_rejected`, `run_status_changed`, `action_allowed`, `action_blocked`, `action_status_changed`.
- **The frozen signatures**, return types and error behaviour back-end PRs code against (bodies raise `NotImplementedError` until built), as AD-19 to AD-21:
  - `gate.evaluate(ctx, action) -> Decision` with `allowed`, `failed_check`, `checks`, `grant_id`, `grant_version`, `policy_set_version`. The five checks, in order: `grant_active`; `team_scope`; `destination_action`; `evidence_checks`; `run_authorised`. Allowed inserts the `actions` document (`queued`) and emits `action_allowed`; blocked emits one `action_blocked` event and writes nothing else.
  - `actions.dispatch(action, ctx) -> Action`: calls `gate.evaluate` first; on `allowed` claims, sends, reads back, reconciles; never raises on an ambiguous result, returns `unknown`.
  - `runs.admit(run_id) -> bool`: one conditional update on `status: running` that increments `in_flight`, or refuses.
  - `runs.release(run_id)`: decrements `in_flight` and moves `stopping` to `stopped` at zero (part of the `runs` contract).
  - `runs.stop(run_id) -> Run`.
  - `runs.stamp(run_id) -> Stamp`: the only stamp maker.
  - `ledger.file(finding_id, changes, mode, ctx) -> FileResult`: calls `gate.evaluate` first; on `blocked` writes one audit event and nothing else.
  - `llm.extract(item) -> list[Finding] | Failure` and `llm.check(finding, source_text) -> CheckResult`: failure record, never raise.

After 11:45 a change to any of these goes through the contract keeper in its own PR.

## Required acceptance behaviours

These six are binding on Stories 9.3 to 9.6. Each card below restates the ones that apply to it, and the reviewer agent checks them.

| Concern | Required behaviour |
|---|---|
| Ambiguous GitHub result | Save an action ID in Atlas before sending and include it in the issue. If the outcome is uncertain (timeout, 5xx), reconcile by searching the repository for the action ID; never blindly retry creation. If still unresolved, mark the action `unknown` for manual reconciliation |
| Concurrent retries | Claim the action atomically in Atlas (`queued` to `dispatching` with a conditional update) so two workers can never both dispatch it |
| Stop semantics | Admission is an atomic, conditional update on the run (only while it is `running`), so a stop and an admission cannot race. After stop, nothing new is admitted; admitted actions may finish and show as in flight; the run shows `stopping` until in-flight reaches zero, then `stopped` |
| Blocked action | No business-record change and no external call; one audit event is written with the policy and grant versions and the failed check |
| Authority | The actor and grant are resolved server-side from the API key; a client-supplied name never confers permission |
| Audit reconstruction | Each action keeps its inputs, evidence reference, grant version, policy-set version, decision, timestamps (proposed, decided, sent, observed) and external result (issue number and URL, or `unknown`) |

## Start requirements and merge requirements are separate

Each card says two things:

- **Start when merged:** what must be on `main` before the agent starts. For most PRs this is only A01, so work runs in parallel instead of one PR after another.
- **Merge after:** what must be on `main` before this PR merges, because it calls real code or another PR's file.

A PR that calls a module not yet merged builds against the frozen signature and is proved against the real module at I1.

## Integration happens twice

| Check | PR | When | What runs |
|---|---|---|---|
| Allowed-and-blocked loop | I1 | 13:45 to 14:30 | On the sandbox: a run over the selected trials; one allowed action updates a record with its quote and creates a real issue in `dxp-review-sandbox`; one out-of-scope action is blocked before execution; the audit API reconstructs both |
| Final acceptance | I2 | 15:00 to 15:30 | On the sandbox: every core and supporting piece, every merged screen, stop mid-run, the audit view answering "who authorised this" |

I1 is where the real modules first meet. I2 is the final acceptance, not first contact: by then the loop has run since 14:30 and the screens have been wired to it between 14:30 and 15:00.

## How agent slots are used

26 PRs are not 26 builders at once. The forecast peak is about 11 builders in Luis's lane (11:45 to 13:15) and 5 in Vlad's (12:00 to 14:00). The rest of Luis's slots go to:

- a second builder on each of A06, A08 and A09, which have no slack, writing the tests;
- one independent reviewer agent per open PR, checking acceptance criteria, the required behaviours, secrets, `.env` values, tokens and PubMed text;
- the contract keeper, who rejects any PR that changes a frozen contract without regenerating the types;
- the integrator, who runs I1 and I2 and keeps a smoke test (one allowed action, one blocked action, audit read) passing on every merge after 13:45.

People spend their attention on unclear behaviour and failures, not on reading every diff.

## Done rule

A story is done only when its PRs have merged and its acceptance criteria pass on the integrated build on the Atlas Sandbox.

## How to brief an agent for one PR

Give each agent one PR ID and this brief, filled in from its card:

```
You are building PR <ID> of DxP: <What>.
Read first: _bmad-output/planning-artifacts/development-plan.md (card <ID>
and "Required acceptance behaviours"), the Story <n.n> acceptance criteria
in epics.md, the architecture spine (AD rules it cites), and for screens
DESIGN.md and EXPERIENCE.md. There are no mockups: every screen is built during the event.
Branch: <branch>, from the latest main. Start only when every PR under
"Start when merged" is on main. Code against the frozen contracts and
signatures from A01 and A02 for anything not merged yet. Only edit the
files this PR owns; anything else goes back to its owner. Do not merge
until every PR under "Merge after" is on main. Build and test against the
Atlas Sandbox.
Never commit secrets, tokens or .env values. Never write PubMed abstract
text to any file. Open the PR as "Story <n.n>: <What> (<ID>)" with the
acceptance criteria and required behaviours as a checklist, and follow
the PR and merge steps in epics.md.
```

For example: "You are building PR A06 of DxP: ledger with the policy gate before every write", branch `story/9.3-policy-gate`; or "PR B02: Run console", branch `story/9.7-run-console`.

## Luis's PRs

| PR | Story | What | Branch | Start when merged | Merge after | Start | Finish |
|---|---|---|---|---|---|---|---|
| A01 | 1.1, 9.1 | Contract: routes, shapes, error shape, frozen signatures (critical) | `story/1.1-contract` | none | none | 10:45 | 11:45 |
| A02 | 1.2 | Registry and identity (critical) | `story/1.2a-registry-identity` | none | none | 10:45 | 11:45 |
| A03 | 9.2 | Grants and policies with schema validation, seeded; server-side actor resolution | `story/9.2-grants-policies` | none (drafts against A01) | A01 | 10:45 | 12:15 |
| A04 | 8.1 | CI, Vercel and Modal deploy on the Atlas Sandbox; change streams checked | `story/8.1-deploy-sandbox` | none (starts on the bare package) | A01 | 11:00 | 12:00 |
| A05 | 1.4 | Load the selected trial set | `story/1.4-selected-trials` | A01 | none | 11:45 | 12:15 |
| A06 | 1.6, 9.3 | Ledger with the policy gate before every write (critical) | `story/9.3-policy-gate` | A01, A02 | A03 | 11:45 | 13:45 |
| A07 | 9.1, 9.5 | Runs: identity stamping, atomic admission, stop (critical) | `story/9.5-runs-stop` | A01 | A03 | 11:45 | 13:15 |
| A08 | 1.5 | Extraction with quote and support checks, tuned on the selected set (critical) | `story/1.5-extraction` | A01 | A05 | 11:45 | 13:45 |
| A09 | 9.4 | GitHub review issue: claim, read-back, reconcile, `unknown` (critical) | `story/9.4-github-action` | A01 | A03 | 11:45 | 13:45 |
| A10 | 1.7 | The run: LangGraph over the selected set (critical) | `story/1.7-run` | A01 | none | 11:45 | 13:30 |
| A11 | 9.6 | Audit API and "who authorised" | `story/9.6-audit-api` | A01 | none | 11:45 | 13:15 |
| A14 | 2.2, 2.3 | Proposals and decisions API, minimal | `story/2.3-proposals-decisions` | A01 | none | 11:45 | 13:15 |
| A12 | 9.9 | Change-stream feed with polling fallback | `story/9.9-change-feed` | A01, A04 | none | 12:00 | 13:00 |
| A15 | 5.1 | Graph API scoped by `run_id`, GitHub issues as nodes | `story/5.1-graph-api` | A01 | none | 12:00 | 13:30 |
| A13 | 1.2 | Seed the FDA rows and synthetic Teams through the ledger (critical) | `story/1.2b-seed` | A01, A02 | A06 | 13:15 | 13:45 |
| I1 | 9.3, 9.4 | Integration: the allowed-and-blocked loop on the sandbox (critical) | `integration/i1-allowed-blocked` | A05 to A13 | none | 13:45 | 14:30 |
| A17 | 9.11 | Stretch: rejection drafts a policy for approval | `story/9.11-policy-draft` | I1 green | A14 | 14:30 | 15:30 |
| I2 | 8.2 | Final acceptance on the sandbox (critical) | `integration/i2-acceptance` | I1, A14, A15, B02 to B05 | none | 15:00 | 15:30 |
| A16 | 8.2 | Live-demo rehearsal and reset procedure (critical) | `story/8.2-rehearsal` | I2 | none | 15:30 | 16:15 |

## Vlad's PRs

| PR | Story | What | Branch | Start when merged | Merge after | Start | Finish |
|---|---|---|---|---|---|---|---|
| B01 | 1.3, 1.12 | Web skeleton and minimal shell | `story/1.12-web-shell` | none | none | 10:45 | 12:00 |
| B02 | 9.7 | Run console | `story/9.7-run-console` | B01 | A01 | 12:00 | 14:15 |
| B03 | 9.8 | Audit view | `story/9.8-audit-view` | B01 | A01 | 12:00 | 14:00 |
| B04 | 1.3, 2.4 | Record and Review screen, minimal | `story/2.4-record-review` | B01 | A01 | 12:00 | 14:00 |
| B05 | 5.2 | Run impact view | `story/5.2-impact-view` | B01 | A01 | 12:00 | 14:30 |
| B06 | 9.10 | Stretch: spoken audit briefing with ElevenLabs | `story/9.10-audio-briefing` | B01 | A11 | 13:00 | 14:30 |
| B07 | 8.3, 8.4 | README with the prepared vs built-today table, submission text, 60-second video script | `story/8.3-submission` | none | none | 13:00 | 14:00 |

Vlad's times assume Sonnet 5.5 at high effort with ten subagents.

## PR cards

### A01: Contract

- **Owner:** Luis · **Story:** 1.1, 9.1 · **Branch:** `story/1.1-contract` · **Forecast:** 10:45 to 11:45 · **Critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** Create the `backend/` package with `uv`, a Modal app serving FastAPI, every route and shape listed under "Contracts come first" returning 501 except `GET /schema`, the error shape `{ error: { code, message } }`, the `store` module with `ensure_indexes()` and `emit_event()` (events carry `run_id` and `action_id`), the signature stubs for `gate`, `actions`, `runs`, `ledger` and `llm`, and the `npm` script that generates `web/lib/types.ts`.
- **Files this PR owns:** backend/pyproject.toml, backend/modal_app.py, backend/dxp/api/ (app, models.py and route stubs; each route file goes to the PR that builds it), backend/dxp/store/ (except the `grants` and `policies` validator schemas in store/schemas/, which A03 fills), the signature stubs in backend/dxp/{gate,actions,runs,ledger,llm}/__init__.py, web/lib/types.ts, the web/package.json script only
- **Done when:** the Story 1.1 and 9.1 contract criteria pass, `types.ts` regenerates cleanly, and the PR is merged.

### A02: Registry and identity

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2a-registry-identity` · **Forecast:** 10:45 to 11:45 · **Critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** `schema/registry.py` (fields, cardinality, enums, stage order, confidence threshold, `canonical()`) and `identity.derive()`, `identity.normalise_name()` as AD-3. Seeding is A13.
- **Files this PR owns:** backend/dxp/schema/registry.py, backend/dxp/identity/, their tests
- **Done when:** the Story 1.2 registry and identity criteria pass, and the PR is merged.

### A03: Grants and policies

- **Owner:** Luis · **Story:** 9.2 · **Branch:** `story/9.2-grants-policies` · **Forecast:** 10:45 to 12:15
- **Start when merged:** nothing: drafts against the A01 shapes from 10:45
- **Merge after:** A01
- **Scope:** The `$jsonSchema` validator schemas for `grants` and `policies` (AD-18), which `store.ensure_indexes()` applies at collection creation; versioned, hand-written grant and policy documents, each policy's `requires` limited to `quote_found`, `supported` and `min_confidence`; the seed `python -m dxp.gate.seed` for the demo (one agent principal and one Reviewer principal, one team scope, destinations `ledger` and `github:dxp-review-sandbox`, allowed actions, an expiry, and one out-of-scope Diagnostic for the blocked case); `resolve_actor(api_key)`, which hashes `X-DxP-Key` and resolves the principal and grant server-side (401 on no match); `GET /whoami`, `GET /grants`, `GET /grants/<grant_id>`, `GET /policies?status=`.
- **Required behaviour (Authority):** the actor and grant are resolved server-side from the API key; a client-supplied name never confers permission.
- **Files this PR owns:** backend/dxp/gate/seed.py, backend/dxp/gate/seed/, backend/dxp/store/schemas/ (the `grants` and `policies` validator schemas only), backend/dxp/api/auth.py, backend/dxp/api/routes_grants.py
- **Done when:** the Story 9.2 criteria pass, a write with an invalid grant is rejected by the validator, and the PR is merged.

### A04: Deploy on the Atlas Sandbox

- **Owner:** Luis · **Story:** 8.1 · **Branch:** `story/8.1-deploy-sandbox` · **Forecast:** 11:00 to 12:00
- **Start when merged:** nothing: starts on the bare package and CI
- **Merge after:** A01
- **Scope:** GitHub Actions on every pull request (web type check and build, backend tests), Vercel previews and production from `main`, `modal deploy` against the Atlas Sandbox, CORS to the Vercel origins. Check change streams on the sandbox tier and record the result in the README; if they are not available, A12 ships polling only (`DXP_FEED=poll`). README section on who deploys and the PR steps.
- **Files this PR owns:** .github/workflows/, web/vercel.json if needed, backend/dxp/api/app.py (CORS only), README.md (deploy section)
- **Done when:** the Story 8.1 criteria pass on the sandbox, the change-stream result is recorded, and the PR is merged.

### A05: Load the selected trial set

- **Owner:** Luis · **Story:** 1.4 · **Branch:** `story/1.4-selected-trials` · **Forecast:** 11:45 to 12:15
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Scope:** `python -m dxp.sources.load --set selected` upserts 10 to 20 held-back trials that hit FDA-seeded Diagnostics, including at least one that produces an allowed action and one that targets an out-of-scope Diagnostic. The list is a checked-in manifest of NCT IDs.
- **Files this PR owns:** backend/dxp/sources/load.py, backend/dxp/sources/selected.json, tests
- **Done when:** the Story 1.4 criteria this scope covers pass, the set loads idempotently on the sandbox, and the PR is merged.

### A06: Ledger with the policy gate

- **Owner:** Luis · **Story:** 1.6, 9.3 · **Branch:** `story/9.3-policy-gate` · **Forecast:** 11:45 to 13:45 · **Critical, no slack**
- **Start when merged:** A01, A02
- **Merge after:** A03
- **Scope:** `gate.evaluate(ctx, action)` with the five checks in order (`grant_active`, `team_scope`, `destination_action`, `evidence_checks`, `run_authorised`), each returning the failed check by name. On `allowed` the gate inserts the `actions` document (`queued`) and emits `action_allowed`; on `blocked` it emits one `action_blocked` event and nothing else. `ledger.file()` calls the gate before every write; on `allowed` it applies the change in one update with `rev`, field history and an event carrying the AD-17 stamp (`run_id`, principal, grant and policy-set versions) and the `action_id`, then sets the action `done`. The Baseline-mode path the seed (A13) uses goes through the same gate with the seed's own grant.
- **Required behaviours:**
  - **Blocked action:** no business-record change and no external call; one audit event is written with the policy and grant versions and the failed check.
  - **Authority:** the actor and grant are resolved server-side from the API key; a client-supplied name never confers permission.
  - **Audit reconstruction (fields this PR writes):** each action keeps its inputs, evidence reference, grant version, policy-set version, decision and the proposed and decided timestamps.
  - **Stop semantics (the gate's fifth check):** `run_authorised` passes only when the run is `running` or `stopping` and the action was admitted (AD-21); since admission refuses after stop, nothing new passes the gate after stop.
- **Files this PR owns:** backend/dxp/gate/ (except seed.py and seed/, which are A03's), backend/dxp/ledger/file.py, backend/dxp/ledger/types.py
- **Done when:** tests prove each of the five checks blocks on its own and that a blocked action leaves the record and GitHub untouched; the Story 1.6 and 9.3 criteria pass; the PR is merged.

### A07: Runs, admission and stop

- **Owner:** Luis · **Story:** 9.1, 9.5 · **Branch:** `story/9.5-runs-stop` · **Forecast:** 11:45 to 13:15 · **Critical, 30 minutes slack**
- **Start when merged:** A01
- **Merge after:** A03
- **Scope:** `POST /runs { source, set, limit, team_id }` creates a run (`_id` `run_<random>`) with agent, model, prompt version, policy-set version, principal and the person it acts for, all resolved server-side, and returns 409 while another run is `running` or `stopping`; `runs.stamp()`, the only stamp maker, used by every write, event and external action; `runs.admit()` as one conditional update (`status: running`, increment `in_flight`); `runs.release()`; `runs.stop()` and `POST /runs/<run_id>/stop` moving the run to `stopping`, then `stopped` when `in_flight` reaches zero; `run_status_changed` on every status change; `GET /runs`, `GET /runs/<run_id>`.
- **Required behaviours:**
  - **Stop semantics:** admission is an atomic, conditional update on the run (only while it is `running`), so a stop and an admission cannot race. After stop, nothing new is admitted; admitted actions may finish and show as in flight; the run shows `stopping` until in-flight reaches zero, then `stopped`.
  - **Authority:** the actor and grant are resolved server-side from the API key; a client-supplied name never confers permission. A run's `acting_for`, `principal`, `grant_id` and `grant_version` come from `resolve_actor`, never from the request body.
- **Files this PR owns:** backend/dxp/runs/, backend/dxp/api/routes_runs.py
- **Done when:** a concurrency test fires stop and admissions together and never admits after stop; a run with in-flight actions shows `stopping` then `stopped`; the Story 9.1 and 9.5 criteria pass; the PR is merged.

### A08: Extraction with quote and support checks

- **Owner:** Luis · **Story:** 1.5 · **Branch:** `story/1.5-extraction` · **Forecast:** 11:45 to 13:45 · **Critical, no slack**
- **Start when merged:** A01
- **Merge after:** A05
- **Scope:** `llm.extract()` (Sonnet 5.5) and `llm.check()` through the one `llm` module: one Finding per Diagnostic named, raw value, quote and confidence per field, backoff and failure records; `evidence.quote_in_source()` and the support check, a value passes only when both are true. Tune the prompts on the selected set until quotes are found. No PubMed text in any file.
- **Files this PR owns:** backend/dxp/llm/ (client, extract, check, prompts), backend/dxp/evidence/
- **Done when:** extraction over the selected set returns Findings with found quotes; the Story 1.5 criteria pass; the PR is merged.

### A09: GitHub review issue

- **Owner:** Luis · **Story:** 9.4 · **Branch:** `story/9.4-github-action` · **Forecast:** 11:45 to 13:45 · **Critical, no slack**
- **Start when merged:** A01 (A03 lands at 12:15; until then the agent codes against the frozen grant shapes)
- **Merge after:** A03
- **Scope:** `actions.dispatch()` for `create_review_issue` actions on `dxp-review-sandbox` with the fine-grained token from `DXP_GITHUB_TOKEN` (`.env` locally, issues only): call `gate.evaluate()` first and send nothing when blocked; claim (`queued` to `dispatching`); create the evidence-review issue with the action ID in its title and body; read the issue back; reconcile on an ambiguous result; set `sent_at`, `observed_at` and `result` (`issue_number`, `issue_url`), or `unknown`, or `failed` on another 4xx; emit `action_status_changed` on every status change; `POST /actions/<action_id>/reconcile`, which searches and never creates. A fake GitHub client for tests, with timeout and 5xx modes.
- **Required behaviours:**
  - **Ambiguous GitHub result:** save an action ID in Atlas before sending and include it in the issue. If the outcome is uncertain (timeout, 5xx), reconcile by searching the repository for the action ID; never blindly retry creation. If still unresolved, mark the action `unknown` for manual reconciliation.
  - **Concurrent retries:** claim the action atomically in Atlas (`queued` to `dispatching` with a conditional update) so two workers can never both dispatch it.
  - **Blocked action:** a blocked action makes no external call; `dispatch` sends nothing when the gate blocks it.
  - **Audit reconstruction (fields this PR writes):** the sent and observed timestamps and the external result (issue number and URL, or `unknown`).
- **Files this PR owns:** backend/dxp/actions/ (dispatch, github.py, fake client, tests), backend/dxp/api/routes_reconcile.py
- **Done when:** tests prove two concurrent dispatches create one issue, a timeout followed by a found issue reconciles without a second issue, and an unresolved one ends `unknown`; one real issue is created on the sandbox repository; the Story 9.4 criteria pass; the PR is merged.

### A10: The run

- **Owner:** Luis · **Story:** 1.7 · **Branch:** `story/1.7-run` · **Forecast:** 11:45 to 13:30 · **Critical, 15 minutes slack**
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks (real modules are wired in I1)
- **Scope:** One LangGraph run over the selected set at low concurrency, started by `POST /runs`: for each item, `llm.extract()` and `llm.check()`, then for each proposed action `runs.admit()`, `gate.evaluate()` through `ledger.file()` or `actions.dispatch()` for GitHub actions, and `runs.release()` in a `finally` once the action is blocked, `done`, `failed` or `unknown`. Stops admitting when the run is stopped. Built against stubs of the frozen signatures.
- **Files this PR owns:** backend/dxp/pipeline/
- **Done when:** the run completes over stubs with one allowed and one blocked action; the Story 1.7 criteria this scope covers pass; the PR is merged.

### A11: Audit API

- **Owner:** Luis · **Story:** 9.6 · **Branch:** `story/9.6-audit-api` · **Forecast:** 11:45 to 13:15
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Scope:** `search.audit` and `GET /runs/<run_id>/audit` return every action in decision order, allowed (from `actions`) and blocked (from `action_blocked` events), with identity, grant and policy versions, decision, failed check, timestamps and external result; `GET /actions/<action_id>` returns the action with `authorised_by`, which answers "who authorised this action" (principal, the person the run acts for, who granted it, grant and version, expiry, policy-set version); `GET /actions?run_id=&status=`. Built from `actions`, `runs` and `events`, with grants and policies read at the recorded versions; nothing is recomputed from current grants or policies.
- **Required behaviours:**
  - **Audit reconstruction:** each action keeps its inputs, evidence reference, grant version, policy-set version, decision, timestamps (proposed, decided, sent, observed) and external result (issue number and URL, or `unknown`).
  - **Blocked action:** the blocked action's one audit event appears in the trail with the policy and grant versions and the failed check.
  - **Authority:** "who authorised" reports the server-resolved actor and grant, never a client-supplied name.
- **Files this PR owns:** backend/dxp/search/audit.py, backend/dxp/api/routes_audit.py, backend/dxp/api/routes_actions.py
- **Done when:** the trail for a fixture run with one allowed and one blocked action reconstructs both in order with every field above; the Story 9.6 criteria pass; the PR is merged.

### A12: Change-stream feed

- **Owner:** Luis · **Story:** 9.9 · **Branch:** `story/9.9-change-feed` · **Forecast:** 12:00 to 13:00 · **Supporting**
- **Start when merged:** A01, A04
- **Merge after:** nothing beyond its own checks
- **Scope:** The live action feed for a run, served to the web as `GET /changes?after=<seq>&run_id=` over `events` (AD-10, AD-23). With `DXP_FEED=change_stream` it waits up to 25 seconds, woken by `events.watch()` on inserts; with `DXP_FEED=poll` (when A04 found no change streams on the sandbox) it returns at once and the web app polls every 2 seconds. The query on `seq` is the only source of truth, and the response is the same either way.
- **Files this PR owns:** backend/dxp/search/changes.py, backend/dxp/api/routes_changes.py
- **Done when:** an action written on the sandbox appears in the feed within a few seconds, by change stream or polling; the Story 9.9 criteria pass; the PR is merged.

### A13: Seed through the ledger

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2b-seed` · **Forecast:** 13:15 to 13:45 · **Critical, no slack**
- **Start when merged:** A01, A02 (A06 finishes at 13:45, so the agent codes against the frozen `ledger.file` signature)
- **Merge after:** A06
- **Scope:** Seed the lung FDA rows and three synthetic Teams through `ledger.file()` in Baseline mode under the seed's grant; `GET /teams`. Idempotent.
- **Files this PR owns:** backend/dxp/ledger/seed.py, backend/dxp/api/routes_teams.py
- **Done when:** the seed runs twice on the sandbox with no duplicates; the Story 1.2 seed criteria pass; the PR is merged.

### A14: Proposals and decisions API

- **Owner:** Luis · **Story:** 2.2, 2.3 · **Branch:** `story/2.3-proposals-decisions` · **Forecast:** 11:45 to 13:15 · **Supporting**
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Scope:** `GET /proposals?status=pending&run_id=`, `POST /proposals/<p_id>/decision` (accept, edit, reject with reason) claimed and applied in one update through the ledger after `gate.evaluate` with the Reviewer's grant, history kept, events stamped (`run_id: null` and the Reviewer's principal, AD-17); `rule_draft` is always null. Minimal: no rule flags, no learned rules.
- **Files this PR owns:** backend/dxp/ledger/decide.py, backend/dxp/api/routes_proposals.py
- **Done when:** the trimmed Story 2.2 and 2.3 criteria pass; the PR is merged.

### A15: Graph API by run

- **Owner:** Luis · **Story:** 5.1 · **Branch:** `story/5.1-graph-api` · **Forecast:** 12:00 to 13:30 · **Supporting**
- **Start when merged:** A01
- **Merge after:** nothing beyond its own checks
- **Scope:** `GET /graph?run_id=` returns what one run touched: Diagnostics, trials, changed fields and the GitHub issues as nodes, with `$graphLookup` for neighbours.
- **Files this PR owns:** backend/dxp/search/graph.py, backend/dxp/api/routes_graph.py
- **Done when:** the trimmed Story 5.1 criteria pass for a fixture run; the PR is merged.

### I1: Integration, the allowed-and-blocked loop

- **Owner:** Luis · **Story:** 9.3, 9.4 · **Branch:** `integration/i1-allowed-blocked` · **Forecast:** 13:45 to 14:30 · **Critical**
- **Start when merged:** A05, A06, A07, A08, A09, A10, A11, A12, A13
- **Merge after:** nothing beyond its own checks
- **Scope:** Wire the real modules into the run on the sandbox. A run over the selected set: one allowed action updates a record with its quote and creates a real issue in `dxp-review-sandbox` (open it); one out-of-scope action is blocked before execution; the audit API reconstructs both with identity, grant, policy version and result. Fix what breaks in the modules above, through their owners' files.
- **Required behaviours checked here:** all six, end to end.
- **Files this PR owns:** fixes only
- **Done when:** the loop passes on the sandbox by 14:30, and the PR is merged.

### A17: Stretch, rejection drafts a policy

- **Owner:** Luis · **Story:** 9.11 · **Branch:** `story/9.11-policy-draft` · **Forecast:** 14:30 to 15:30 · **Stretch, only if I1 is green**
- **Start when merged:** I1 green
- **Merge after:** A14
- **Scope:** When Sam rejects a proposal with a reason, the model drafts a policy as structured data: a `requires` object limited to `quote_found`, `supported` and `min_confidence`, with `applies_to`; it stays `draft` until a person principal approves it through `POST /policies/<policy_id>/approve { version }`, and then becomes a new `active` version and a new policy-set version. Model prose is never executable authority.
- **Files this PR owns:** backend/dxp/gate/drafts.py, backend/dxp/llm/prompts/policy_draft.*, backend/dxp/api/routes_policy_drafts.py
- **Done when:** the Story 9.11 criteria pass; the PR is merged.

### I2: Final acceptance

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `integration/i2-acceptance` · **Forecast:** 15:00 to 15:30 · **Critical**
- **Start when merged:** I1, A14, A15, B02, B03, B04, B05
- **Merge after:** nothing beyond its own checks
- **Scope:** Final check, not first contact: every core and supporting piece on the sandbox through the screens. Start a run from the Run console; watch actions stream in; open the real issue; see the blocked action and its failed check; Sam reviews a proposal; stop the run mid-flight (`stopping`, then `stopped`); the Audit view answers "who moved SuperARMS to clinical utility, and under what authority?"; the impact view shows what the run touched.
- **Files this PR owns:** fixes only
- **Done when:** the Story 8.2 acceptance criteria pass on the sandbox, and the PR is merged.

### A16: Rehearsal and reset

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `story/8.2-rehearsal` · **Forecast:** 15:30 to 16:15 · **Critical**
- **Start when merged:** I2
- **Merge after:** nothing beyond its own checks
- **Scope:** Rehearse the 3-minute live demo and the 60-second video script on the sandbox twice; a reset procedure that restores the seeded state, clears runs and actions, and closes the test issues in `dxp-review-sandbox`. README notes only.
- **Files this PR owns:** README.md (demo notes and reset section), scripts/reset_demo.py
- **Done when:** the demo runs twice from a reset without a fix, and the PR is merged.

### B01: Web skeleton and minimal shell

- **Owner:** Vlad · **Story:** 1.3, 1.12 · **Branch:** `story/1.12-web-shell` · **Forecast:** 10:45 to 12:00
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** `web/` from `create-next-app` (Next.js 16, TypeScript, App Router, Tailwind), `shadcn init`, `web/lib/api.ts` (typed fetch using `types.ts` once A01 lands, a hand stub before), the one server route that adds `X-DxP-Key`, and a minimal shell: tokens and fonts from `DESIGN.md`, a top bar with Run console, Audit, Review and Impact and the read-only "Signed in as" chip from `GET /whoami` (no name picker), badges, toasts, skeletons.
- **Files this PR owns:** web/ (everything except web/lib/types.ts and the screens below), web/components/shell/
- **Design reference:** tokens from `DESIGN.md`; the interface is built during the event
- **Done when:** the trimmed Story 1.3 and 1.12 criteria pass, the skeleton deploys on Vercel, and the PR is merged.

### B02: Run console

- **Owner:** Vlad · **Story:** 9.7 · **Branch:** `story/9.7-run-console` · **Forecast:** 12:00 to 14:15 · **Core**
- **Start when merged:** B01
- **Merge after:** A01
- **Scope:** Start a run; identity card (agent, model, prompt version, policy-set version, acting for, grant and scope); live action feed from `/changes` with allowed, blocked (failed check named), in flight and unknown states; stop button with `stopping` then `stopped`; links to the GitHub issues and to the Audit view.
- **Files this PR owns:** web/app/runs/[run_id]/page.tsx, web/app/runs/page.tsx, web/components/run-console/
- **Design reference:** the Run console section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the Story 9.7 criteria pass against the sandbox, and the PR is merged.

### B03: Audit view

- **Owner:** Vlad · **Story:** 9.8 · **Branch:** `story/9.8-audit-view` · **Forecast:** 12:00 to 14:00 · **Core**
- **Start when merged:** B01
- **Merge after:** A01
- **Scope:** One run reconstructed action by action from `GET /runs/<run_id>/audit`: inputs, evidence quote, grant and policy versions, decision and failed check, the four timestamps, issue link or `unknown`; a "who authorised this" panel from `authorised_by` on `GET /actions/<action_id>`.
- **Files this PR owns:** web/app/runs/[run_id]/audit/, web/components/audit/
- **Design reference:** the Audit view section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the Story 9.8 criteria pass against the sandbox, and the PR is merged.

### B04: Record and Review, minimal

- **Owner:** Vlad · **Story:** 1.3, 2.4 · **Branch:** `story/2.4-record-review` · **Forecast:** 12:00 to 14:00 · **Supporting**
- **Start when merged:** B01
- **Merge after:** A01
- **Scope:** The Record page with Evidence on every value and the `run_id` that last changed it; a minimal Review queue for one run's proposals with accept, edit and reject with reason.
- **Files this PR owns:** web/app/diagnostics/, web/app/review/
- **Design reference:** the Record and Review section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the trimmed Story 1.3 and 2.4 criteria pass against the sandbox, and the PR is merged.

### B05: Run impact view

- **Owner:** Vlad · **Story:** 5.2 · **Branch:** `story/5.2-impact-view` · **Forecast:** 12:00 to 14:30 · **Supporting**
- **Start when merged:** B01
- **Merge after:** A01
- **Scope:** `react-force-graph-2d` through `next/dynamic` over `GET /graph?run_id=`: what the run touched, with the GitHub issues as nodes, click-through to the Record and to the issue, and View as table.
- **Files this PR owns:** web/app/runs/[run_id]/impact/, web/components/graph/
- **Design reference:** the Run impact view section of `EXPERIENCE.md`, with `DESIGN.md` tokens
- **Done when:** the trimmed Story 5.2 criteria pass against the sandbox, and the PR is merged.

### B06: Stretch, spoken audit briefing

- **Owner:** Vlad · **Story:** 9.10 · **Branch:** `story/9.10-audio-briefing` · **Forecast:** 13:00 to 14:30 · **Stretch**
- **Start when merged:** B01
- **Merge after:** A11
- **Scope:** `GET /runs/<run_id>/audit/audio`: ElevenLabs reads a run's audit summary, a short script built from the `GET /runs/<run_id>/audit` response only, cached in `audio` per run, 503 on failure; a play, pause, loading and error control on the Audit view.
- **Files this PR owns:** backend/dxp/api/briefing.py, backend/dxp/api/routes_audio.py, web/components/audit/audio.tsx
- **Done when:** the Story 9.10 criteria pass, and the PR is merged.

### B07: Submission package

- **Owner:** Vlad · **Story:** 8.3, 8.4 · **Branch:** `story/8.3-submission` · **Forecast:** 13:00 to 14:00
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** README with the problem statement (Statement 1), a prepared vs built-today table, the MongoDB capability table, credits and links; the submission description; the 60-second video script (0 to 10 s scope, 10 to 30 s allowed action across two systems, 30 to 45 s blocked action, 45 to 60 s stop and "who authorised").
- **Files this PR owns:** README.md (submission sections), docs/video-script.md
- **Done when:** the Story 8.3 and 8.4 criteria pass, and the PR is merged.

## Deferred work

Deferred (pivot, 13 Nov). No agent builds these on Saturday. The old PR IDs P01 to P42 and V01 to V19 are retired; do not reuse them.

| Deferred | Stories |
|---|---|
| Full Baseline load and snapshot, scheduled scan, Tavily provider scan | 1.9, 1.10, 1.11 |
| Jobs page (replaced by the Run console, 9.7) | 1.8 |
| Dry run of the Held-back set, Value history, Learned rules API and Rules on screen | 2.1, 2.5, 2.6, 2.7 (2.6 returns only as stretch Story 9.11) |
| Alerts API, Alerts inbox, Digest, audio briefing and play button (audio returns as stretch Story 9.10) | 3.1, 3.2, 3.3, 3.4, 3.5 |
| Find and Categories: search indexes, query API, comparison table, shortlist, export, add a value, Category landscape, unmatched terms | 4.1 to 4.8 |
| Changed highlight on the graph | 5.3 |
| Memory and resume, synthetic Team history, Home hero and welcome panel | 6.1 to 6.4 |
| Quick capture | 7.1 |
| The broad Home dashboard and the full app shell beyond B01 | parts of 1.12 |
