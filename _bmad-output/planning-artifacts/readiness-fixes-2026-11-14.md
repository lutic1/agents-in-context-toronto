---
title: Readiness fixes after the pivot audit
status: draft (follows two audits; for Luis to confirm before 10:45)
created: 2026-11-14
supplements: sprint-change-proposal-2026-11-13.md
---

Slack replaces GitHub as the external system; where this file mentions GitHub, a review issue or reconciling against GitHub, `sprint-change-proposal-2026-11-14-slack.md` wins.

# Readiness fixes after the pivot audit

An audit of commit `8a49cc5` found that the pivot was documented but not ready for build agents. This file records the decision for each finding. Every planning document is brought into line with it, and where an earlier document disagrees, this file wins.

## D1. No prepared code or assets are reused

- No code from `scripts/data/` or from any `dxp-*` skill is copied into `backend/` or `web/`, and none is run on Saturday. Skills are reference documentation for agents (APIs, limits, gotchas); every line of project code is written during the event.
- Disclosure does not authorise reuse. The README lists prepared material so judges can see it, not so agents can use it.
- **Data.** The files in `data/` were downloaded and filtered before the event. Unless an organiser clears their use in writing on Saturday morning, they are not loaded. Instead, during the event:
  - A05 fetches the selected trials by NCT ID from the ClinicalTrials.gov API v2.
  - A13 fetches the FDA list of cleared or approved companion diagnostics and keeps the lung rows.
- The selected NCT IDs are a planning decision and may be listed in the plan (see D9).
- **Logo.** The prepared logo images are not used unless an organiser clears them. The interface uses a text wordmark, "DxP", set in the interface font during the event.
- `scripts/data/` and `data/` stay in the repository as history, each with a notice saying they are not used on Saturday without written clearance.

## D2. The tracker never sends an agent to deferred work

`sprint_plan.py status` now reads `owners.<story>.scope`. It never recommends a deferred story, and it recommends core before supporting before stretch. When only deferred stories remain it says so instead of recommending a build. Tests cover all three cases.

## D3. Every core endpoint has an owner

- New PR **A18** (Luis, Story 1.1): `search.readmodel`, `GET /diagnostics`, `GET /diagnostics/<dx_id>`, their tests. Starts after A01; merges after A06; 11:45 to 12:45.
- **A14** gains `POST /diagnostics/<dx_id>/values/<value_id>/review` (review of an unreviewed value) and its tests, alongside proposals and decisions.
- A01 stays stubs only; no card is left implying a stub is the finished route.

## D4. A run has two identities: who started it and who executes it

- Every run records `initiated_by` (the principal who started it, resolved from the caller's key) and `agent` (the executing agent principal named by the grant).
- A grant names the agent it authorises and the principals allowed to start runs under it: `startable_by: [principal ids]`.
- `POST /runs { grant_id, set, team_id }`: the server resolves the caller from `X-DxP-Key`, loads the latest version of the grant, checks that it is active and that the caller is in `startable_by`, then creates the run with `agent` from the grant, `initiated_by` from the caller and the grant version pinned. A client-supplied name never confers permission.
- The worker executes with the agent's key and the `run_id`. Every agent write requires a `run_id`, and the worker's key must resolve to the run's `agent`.
- **Reviewer decisions** are written with `run_id: null` and a stamp for the Reviewer, plus `cause: { proposal_id, origin_run_id }`. They are allowed without a run ID; agent writes are not.
- **Seeding** runs only from the command line with a dedicated seed key. Its writes carry the stamp `{ kind: "seed", principal: "seed" }` and `run_id: null`.

## D5. Every gate evaluation is recorded as a decision

- New collection `decisions`: one document per gate evaluation, allowed or blocked. Each keeps:
  - `decision_id`, `run_id`, the agent and `initiated_by`;
  - the action kind and its inputs, the evidence reference (source item, quote, checks), the destination;
  - every check with its result and detail;
  - the grant actually evaluated (`grant_id@version`) and the `policy_set_version`;
  - the outcome (`allowed` or `blocked`) and timestamps.
- An allowed decision creates an action that points back to it (`decision_id`). A blocked decision creates no action, no record change and no external call.
- The `action_blocked` event carries the `decision_id`.
- Audit detail for any entry, allowed or blocked: `GET /decisions/<decision_id>`. `GET /actions/<action_id>` stays for action status and results.
- `GET /runs/<run_id>/audit` lists the run's decisions and actions in order, then a section **"After the run"** with the Reviewer decisions whose `cause.origin_run_id` is this run.

## D6. Policy sets and grants are reconstructable

- New collection `policy_sets`: `{ _id: policy_set_version, members: ["<policy_id>@v<n>", ...], created_at }`, written when a set is first used. The version is the hash of the sorted members.
- **Selection:** for each policy ID, take the latest version first, then check its status. Only versions whose latest status is `active` are members. Grants work the same way: latest version first, then status. A newer `revoked` or `expired` version blocks.
- Each decision records the grant actually evaluated. The run keeps the grant version pinned at start, separately. If they differ and the latest is not active, check 1 fails.

## D7. Stop works the same way everywhere, and recovers

- Check 5, "run still authorised", means: the action holds an admission for this run, and the run is not `stopped`. New admissions are granted only while the run is `running`. An admitted action may finish while the run is `stopping`.
- New collection `admissions`, unique on `(run_id, item_key)`, with status `admitted`, `released` or `abandoned` and a lease `expires_at`.
  - `runs.admit(run_id, item_key)` inserts an admission only if the run is `running` (a conditional check and the insert happen in one transaction, or the run's `admitting` counter guards it).
  - `runs.release(admission_id)` changes `admitted` to `released` with a conditional update, so a second release does nothing.
  - A sweep marks admissions past their lease `abandoned`. Any action they hold that is `dispatching` is marked `unknown`, never retried, and a Reviewer resolves it manually (D24, Slack proposal S8).
  - The run moves from `stopping` to `stopped` when no `admitted` admissions remain.
- FR-33, FR-38, Story 9.3, Story 9.5, AD-19 and AD-21 all use these words.

## D8. Integration 1 proves the governed loop without bypassing review

- In live mode, a change to an existing Diagnostic is filed as a **pending proposal**; it is never applied directly (AD-4). A06 applies the gate, then files the proposal as pending.
- The Slack alert (`notify_slack`, destination `slack:#all-mango-db-hackathon`) tells a human that the proposal awaits review, with links back to it in DxP. Approval and rejection happen in DxP, never in Slack.
- **I1 proves:** one proposal filed as pending, one real Slack alert delivered (HTTP 200 `ok`, recorded as `delivered`), one action blocked before execution, and the audit reconstructing all three. It does not need A14.
- Applying a proposal happens only through a Reviewer decision (A14), proved at I2.

## D9. The demo uses a change the rules allow

- The scripted question is now: **"Who filed trial NCT04712877 against FoundationOne Liquid CDx, and under what authority?"**
- **The scenario, from real data:** held-back trial NCT04712877 names both FoundationOne Liquid CDx (a plasma test) and FoundationOne CDx (a tissue test). Both are FDA-seeded.
  - The grant covers a liquid-biopsy Team. The proposal to add NCT04712877 to FoundationOne Liquid CDx's trials is **allowed**: pending proposal plus a Slack alert in `#all-mango-db-hackathon`.
  - The same trial's proposal for FoundationOne CDx is **blocked before execution**: check 2 fails, because the tissue test is outside the Team's scope. No proposal is filed and no Slack message is sent.
  - Sam opens the proposal from the alert's "Review in DxP" link, approves it in DxP, and the Audit view answers the question.
- No stage transition is demonstrated. The SuperARMS stage-advance story is removed from the demo.
- The selected set (D1) is 10 to 20 held-back trials that name FDA-seeded Diagnostics, NCT04712877 among them.

## D10. Fallbacks can actually run

- **I1** depends only on core PRs. The feed uses polling until A12 lands.
- **I2 (core acceptance)** depends only on core PRs plus the minimal Record and Review screen. Supporting and stretch items each have their own acceptance check and join the rehearsal only if they passed.
- **A16 (rehearsal)** depends on I2 core acceptance only.
- **Supporting and stretch timing.** Agents not needed on the core may build them before 14:30. They never block a core PR. If the loop is not green at 14:30, they pause.
- **B06 (audio)** may be built from 13:00 behind a flag. It merges only after the 14:30 loop is green.
- **B07** is README, submission text and the 60-second video script, done by 14:00. **Story 8.4's recording and submission** is a separate task, **R1** (Luis and Vlad, 16:30 to 16:55).

## D11. Active stories carry one specification

Every kept story's acceptance criteria are rewritten in full for the pivot, and the "Pivot change" override paragraphs are removed. Deferred stories keep their old text, marked deferred.

## D12. The impact view shows only what the run touched

- **Changed elements:** the values, proposals, edges and notifications (`notification:<action_id>`) the run itself created or changed, each with its `run_id`.
- **Context:** a touched Diagnostic's other neighbours are shown only when asked ("Show context"), visibly marked as context, and are not attributed to the run.
- FR-43 and AD-13 say this.

## D13. Applying a proposal cannot be half done

- A proposal goes `pending` → `applying` (claimed) → `applied`.
- The Diagnostic update records the proposal ID in `applied_proposal_ids` and runs only if the ID is not already there, so it is idempotent.
- On recovery, a proposal stuck in `applying` reruns the guarded update (a no-op if it already happened) and then marks itself `applied`.

## D14. The README describes the current project

The README is rewritten: the pivot, the prepared-versus-built-today table (D1), what is not reused, and the open organiser questions.

## D15. No two PRs own the same file

- B01 owns `web/` including `web/package.json`. Its `gen:types` script calls `tools/gen_types.sh`, which A01 owns along with `web/lib/types.ts`.
- A01 owns `backend/dxp/api/app.py`, which reads allowed origins from the environment.
- A04 owns `backend/modal_app.py` and the deploy configuration only, and edits no API file.

## Second audit (14 Nov): decisions D16 to D40

Two independent audits of the D1 to D15 changes found the gaps below. These decisions close them and win in the same way.

### Identity, grants and the gate

- **D16. Seed and Reviewer grants are defined.**
  - Seed grant `seed@v1`: principal `seed`, actions `[apply_value]`, destination `ledger`, scope `{ all: true }`. `all: true` is valid only for the seed principal; the validator rejects it on any other grant.
  - Reviewer grant `sam@v1`: principal Sam, actions `[decide_proposal, review_value, resolve_notification]`, destination `ledger`, scope = the same `diagnostic_ids` as the agent grant.
  - Agent grant: actions `[file_proposal, notify_slack]`, destinations `ledger` and `slack:#all-mango-db-hackathon` (Slack proposal S1, S2).
  - `review_value` is a new action kind, used by `POST /diagnostics/<dx_id>/values/<value_id>/review`.
  - `resolve_notification` is a new action kind, used by `POST /actions/<action_id>/resolve` (D25).
  - Check 4 (evidence) applies only to agent kinds. For `decide_proposal`, `review_value` and `resolve_notification` it records `n/a`; an `edit` or `reject` must carry a reason instead, and a resolution carries a `note`.
- **D17. A key resolves to its principal regardless of grant status.**
  - The principal is found by `key_hash` across all grant versions, whatever their status. 401 means only an unknown key.
  - A revoked or expired grant is caught by check 1 and recorded as a blocked Decision.
- **D18. `POST /runs { grant_id, set }`.**
  - `team_id` is dropped from the body; the grant defines the Team.
  - The web app lists the grants the caller may start, each labelled with its Team. There is no separate Team picker.
- **D19. Agent and Reviewer stamps on decisions.**
  - On Reviewer decisions: `agent: null`, `initiated_by: <reviewer principal>`.
  - On seed decisions: `agent: "seed"`, `initiated_by: "seed"`.
- **D20. IDs never collide.**
  - Decision and action IDs derive from `(run_id or "-", kind, diagnostic_id, proposal_id or value_id or "<field>|<value>")`.
  - Seed changes carry their own derived `p_` IDs.
  - Reviewer decisions add a server-generated `request_id`, so a blocked Reviewer decision can be retried and gets a new Decision.
- **D21. Decision order.** `decision.seq` is the `seq` of its `action_allowed` or `action_blocked` event.

### Admissions, stop and recovery

- **D22. One admission per action.**
  - `item_key = "<source_ref>|<kind>|<diagnostic_id>|<proposal_id or '-'>"`.
  - The admission is taken after extraction, before the gate.
  - The public API is `runs.admit`, `runs.release`, `runs.sweep`, `runs.settle` and `runs.finish`, implemented in `runs/admissions.py`. Every document uses these names.
- **D23. `settle` only stops.**
  - `runs.settle(run_id)` only moves a run from `stopping` to `stopped` when no `admitted` admission remains.
  - `runs.finish(run_id)`, called by the pipeline after the last item, moves it from `running` to `done` once no admission remains.
  - A run becomes `failed` only when the pipeline raises an error it cannot recover from.
- **D24. Orphans are resolved.**
  - The sweep marks `queued` actions of abandoned admissions `failed` with reason `abandoned_before_send`. They were never sent, so this is safe.
  - The sweep marks `dispatching` actions of abandoned admissions `unknown`. They are never retried.
  - Every status update (`dispatching`, `delivered`, `failed`, `unknown`) is conditional on the current status, so a slow worker never overwrites an `unknown` or a manual resolution.
  - `GET /runs/<id>` does not call Slack. It starts the sweep in the background and returns current state, with actions shown as `reconciling` (read time only).
- **D25. No listing; unknown outcomes are resolved by hand** (Slack proposal S7, S8).
  - A webhook post cannot be looked up afterwards, so there is no listing or search. DxP records what it observed: HTTP 200 `ok` is `delivered`; HTTP 4xx is `failed`, never retried; HTTP 429 is retried once after `Retry-After` while holding the claim, and a second 429 is `failed`; a timeout, connection error or HTTP 5xx is `unknown`, never retried automatically.
  - `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }`, gated as kind `resolve_notification`, lets a Reviewer settle an `unknown` notification after checking the channel for the action ID. It is audited as a Decision with the Reviewer's stamp.
  - The GitHub reconcile route and the listing of issues are removed.

### Ledger and review

- **D26. Apply belongs to the ledger, owned by A06.**
  - `ledger/apply.py` (claim, guarded update, recovery) is owned by A06, so seed and I1 do not depend on A14. A14 keeps `decide.py` and `review.py` and calls `ledger.apply(proposal_id)`.
  - Recovery runs at API start, at the start of every run and on every decision call.
- **D27. Apply is complete and recoverable.**
  - The Diagnostic update is one guarded update. Edges are upserted after it, and the `value_applied` event is emitted with a `dedupe_key`.
  - Recovery always re-upserts the derived edges and re-emits the event, whatever the guard returns.
  - An edge's `run_id` is set with `$setOnInsert`, so a later run never takes over an earlier run's edge.
- **D28. No live apply on new Diagnostics.**
  - The branch that applied live changes at once on a Diagnostic the run itself created is removed.
  - Creating a Diagnostic outside the grant's scope is blocked by check 2. In live mode an agent never applies; it only files proposals.
- **D29. API shapes carry what the screens need.**
  - Proposal gains `decision_id` and `notification { action_id, status, posted_at }`.
  - Link gains `status` (`pending` or `applied`) and `proposal_id`.
  - Record gains `applied_proposal_ids`.
  - Run `counts` keep `early_research`.

### Data and the demo

- **D30. The selected set is named.** Twenty public ClinicalTrials.gov trials that name an FDA-listed lung assay, fetched by NCT ID during the event, in this order:
  1. NCT04712877
  2. NCT06284317
  3. NCT04591431
  4. NCT05715229
  5. NCT03248089
  6. NCT03615443
  7. NCT05361564
  8. NCT04265534
  9. NCT04698681
  10. NCT03576937
  11. NCT04624373
  12. NCT04566614
  13. NCT06918782
  14. NCT05846594
  15. NCT04223596
  16. NCT04087473
  17. NCT03199651
  18. NCT03521154
  19. NCT06146920
  20. NCT05935384

  A05 processes them in this order.
- **D31. Hand-written aliases, written during the event by A02.** "FoundationOne Liquid" maps to FoundationOne Liquid CDx, "Guardant360" to Guardant360 CDx, and "FoundationOne" (when not followed by "Liquid") to FoundationOne CDx.
  - The ID alias of a seeded Diagnostic is `normalise_name()` of the FDA list's trade-name column, and the row ID is the PMA or 510(k) number column.
  - A08 passes the seeded alias list into the extraction prompt, and the extracted assay name must be one of them or `new`.
  - I1 asserts that both NCT04712877 Findings resolve to the seeded FoundationOne Liquid CDx and FoundationOne CDx, and that the Slack alert for the allowed FoundationOne Liquid CDx proposal is recorded as `delivered`.
- **D32. Team scope.** The liquid-biopsy Team's grant covers FoundationOne Liquid CDx, Guardant360 CDx, Guardant360 Liquid CDx and Agilent Resolution ctDx FIRST. Every other Diagnostic is out of scope, so proposals for them are blocked by check 2.
- **D33. Demo order and pacing.**
  - The live run uses `DXP_DEMO_PACE` (one item at a time, a few seconds per item), so the first item is NCT04712877 and the stop lands mid-run.
  - Order, for both the 60-second video and the live demo:
    1. start the run;
    2. the allowed proposal and its Slack alert arriving in `#all-mango-db-hackathon` (in the video, 10 to 30 seconds), then the blocked one, which sends no Slack message;
    3. stop the run while items remain;
    4. Sam follows the alert's "Review in DxP" link and approves the pending proposal in DxP (it appears under "After the run");
    5. ask the scripted question in the Audit view.
- **D34. Reset before each take.**
  - A snapshot is taken after seeding and before any run. A16's reset restores it with `mongodump` and `mongorestore`.
  - The reset runs before the video (16:30) and again between submission and the live demo (16:55 to 17:10).

### Plan and ownership

- **D35. Scope labels match dependencies.** Stories 1.3, 2.2, 2.3 and 2.4 are core, because final acceptance (I2) needs them. The status script validates scope values; an unknown value is an error, not silently treated as unscoped.
- **D36. Single owners.**
  - `GET /schema` is owned by A01.
  - `README.md` is owned by B07 alone. Others write `docs/deploy.md` (A04), `docs/demo-and-reset.md` (A16) and `docs/clearance.md` (Luis). R1 adds the video link to the README.
  - `evidence/__init__.py` is owned by A08.
  - A03's seed data folder is `gate/seed_data/`.
  - A01 owns `backend/tests/conftest.py`, `backend/uv.lock`, the package `__init__.py` files and `.env.example`.
  - Fixes found during I1 and I2 go in small PRs reviewed by the owner of the file.
- **D37. Core never depends on supporting work.**
  - The Run console is done with the feed flag off, and the live feed shows only if A12 passed its check.
  - Links to the impact view are hidden when the `impact` flag is off.
  - Reversal is moved out of Story 9.5 into stretch.
  - A06, A07 and A09 (now the Slack notifier, branch `story/9.4-slack-notify`) are never stubbed. Only A12, A15, B05, B06 and A17 may be cut.
- **D38. A13 merges on fake-gate tests.** The first step of I1 (15 minutes) runs the grant seed, the selected-set load and the FDA seed on the sandbox.
- **D39. A04 merges after B01.** B01's done-when is "builds locally; deploys once A04 lands".
- **D40. Clean-up.**
  - Stale active text is removed. That covers the epics' requirement summaries and FR34/FR38 wording, Baseline, PubMed, memory, Learned rules, the M10 cluster, `data/fda/assays.json`, "three-minute video", "Supporting (built after the loop is green)" and `ledger.py`.
  - The titles of Stories 1.1, 1.4 and 8.4 are updated. Tracker keys stay as they are.
  - The Diagnostics list is not built; the Record page is reached from Review, Audit and Impact links.
  - Unreviewed values use Accept, Edit and Reject through the value-review route.
  - "Who authorised" reads the Decision's `authorised_by`.
  - UX polling targets are `GET /runs/<id>` and `GET /runs/<id>/audit`, and the Review count polls `GET /proposals?status=pending`, until A12 passes.
  - Display formats:
    - grants as `{grant_id}@v{version}`;
    - policy sets as `ps_ab12… (N policies)`;
    - example IDs in the `run_` and `act_` forms.
  - Every route has one status (core, supporting, stretch, deferred) in one place.
  - Skills get one line saying Saturday scope is `development-plan.md`, and that Baseline, PubMed, memory, Learned rules, Alerts and Tavily are deferred.
  - The README lists the Slack incoming webhook for `#all-mango-db-hackathon` (created and tested before the event; any test script is not reused, and the notifier is written during the event) and the modified tracker script as prepared material.
  - The sprint tracker's action items drop Agent Memory and Automated Embedding, and add the data and logo clearance item.
  - Open items (Slack proposal S12): the `dxp-review-sandbox` repository and token item is removed. Added: set `DXP_BASE_URL` to the production URL and confirm the alert links resolve (owner Luis, during A04); keep `SLACK_WEBHOOK_URL` only in `.env` and the Modal secret.

## Final audit (14 Nov): decisions D41 to D57

A final independent audit, made after the Slack change, returned "ready with minor fixes". These decisions close the remaining items, and they win in the same way. The status of this file stays draft until Luis confirms it.

### Demo flow and reset

- **D41. Reset before every take.**
  - The reset script `scripts/reset_demo.py` and the post-seed snapshot belong to A13. The snapshot is taken in I1's first step.
  - The reset runs before I2, before each rehearsal (A16), before the video and before the live demo. A16 uses the script; it does not create it.
  - The integrators' smoke test runs in its own database, `DXP_DB=dxp_smoke`, never in the demo database.

### API contract and shapes

- **D42. Loading one proposal.**
  - `GET /proposals/<p_id>` returns one proposal, whatever its status. It is in AD-14, A01's frozen route list, A14 and B04.
  - The Review page's `?proposal=<p_id>` focus uses this route.
  - There is no `p_id=` query parameter.
- **D43. Sweep layering.**
  - `runs` imports nothing from `actions`. `runs.sweep(run_id)` marks expired admissions `abandoned` and returns the actions they held.
  - The background task in `routes_runs.py` then calls `actions.mark_unknown(action_id, "abandoned_in_flight")` for `dispatching` actions, and `actions.mark_failed(action_id, "abandoned_before_send")` for `queued` ones. Finally it calls `runs.settle(run_id)`.
  - These names are used everywhere. The name `mark_abandoned` is retired.
- **D44. Action shape, exactly as AD-14.**
  - `result { http_status, response_body, posted_at, link_urls { report_url, diagnostic_url } }`.
  - `resolution { outcome, note, decision_id, by, at }`.

### Seed data and the gate

- **D45. FDA row IDs and exact names.**
  - An FDA row's ID is `<PMA or 510(k) number>:<first 8 hex characters of sha1 of the normalised row>`, because one number covers many drug rows.
  - The agent grant's scope uses these exact trade-name strings: "FoundationOne Liquid CDx", "Guardant360 CDx", "Guardant360® Liquid CDx" and "Agilent Resolution ctDx FIRST assay". `normalise_name()` removes "®" and folds case.
- **D46. The gate is evaluated once per change.**
  - A10 calls `ledger.file` once for each admitted change. Each filed proposal gets its own `notify_slack` action, so there is one Slack alert per proposal.
  - I1 asserts that at least the NCT04712877 trial proposal for FoundationOne Liquid CDx is filed and its alert delivered, and that the FoundationOne CDx change is blocked.
- **D47. `proposals.notification` is read-time only.** A14 and A11 build it from the proposal's `notify_slack` action, and nothing writes it to the proposal document. Story 9.4 does not update proposals.
- **D48. Keys and configuration.**
  - At 10:45, A03 generates `DXP_AGENT_KEY`, `DXP_API_KEY` and `DXP_SEED_KEY` locally into `.env`. `python -m dxp.gate.seed` computes each `key_hash` from the environment at seed time, and no key is ever committed.
  - A04 puts `DXP_API_KEY` and `NEXT_PUBLIC_API_URL` into Vercel, and puts `DXP_AGENT_KEY`, `SLACK_WEBHOOK_URL`, `ANTHROPIC_API_KEY`, `MONGODB_URI` and `DXP_BASE_URL` into the Modal secret.
  - `.env.example` (A01) lists, with no values:
    - `MONGODB_URI`, `DXP_DB`;
    - `ANTHROPIC_API_KEY`;
    - `DXP_API_KEY`, `DXP_AGENT_KEY`, `DXP_SEED_KEY`;
    - `SLACK_WEBHOOK_URL`, `DXP_BASE_URL`, `DXP_ALLOWED_ORIGINS`, `DXP_FEED`, `DXP_DEMO_PACE`;
    - `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_DXP_FEATURES`;
    - `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`.
- **D49. ID target for resolutions.** For `resolve_notification`, the Decision and Action ID target is the `action_id`. The spine, plan and epics all say this.
- **D50. Check 4 kinds.** Check 4 (evidence) applies only to `file_proposal` and `notify_slack`. It records `n/a` for `apply_value` (seed), `decide_proposal`, `review_value` and `resolve_notification`.

### Plan, screens and identity

- **D51. I1 needs the deploy.** I1 lists A04 directly among its start requirements, because it needs the deploy, `DXP_BASE_URL` and the Modal secret.
- **D52. Video timings.** One version everywhere:
  - 0 to 10 s: the problem and the scope.
  - 10 to 30 s: the allowed proposal and its Slack alert, then the blocked change.
  - 30 to 45 s: stop the run.
  - 45 to 60 s: Sam approves in DxP, then "who authorised this?" in the Audit view.
- **D53. Resolve on screen.**
  - B03 also has the Resolve control.
  - `GET /whoami` returns `Principal { id, name, kind, actions }`, where `actions` are the actions of the caller's current grant. B02 and B03 show Resolve only when `actions` includes `resolve_notification`.
- **D54. Window.** Selected trials are stored with `window: "selected"` instead of `heldback`. Docs call them "the selected trials", not "held-back trials".
- **D55. Skill headers.**
  - "the three-minute video" becomes "the old three-minute recorded video (the 3-minute live demo is in scope)".
  - `dxp-heygen` is marked deferred: it is not in the plan, and no clips are made.
- **D56. Names.**
  - Agent principal `dxp-curator`.
  - Agent grant `lbdx@v1`, Team "Team Liquid Biopsy Dx".
  - Reviewer principal `sam` with grant `sam@v1`.
  - Seed principal `seed` with grant `seed@v1`.

  The A03 card, the spine and the UX all use these.

### Open items

- **D57. The Slack channel is used often.** Every run posts one alert per filed proposal to `#all-mango-db-hackathon` (tuning, I1, I2, rehearsals, the video and the live demo). New open item for Luis: confirm before 10:45 that this is acceptable for that channel, or point the webhook at a team channel.
