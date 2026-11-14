---
title: DxP development plan, Saturday 14 November 2026
status: final
created: 2026-11-13
sources:
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/build-schedule.md
---

# DxP development plan

Who builds what on Saturday, one pull request at a time. Every PR below has an owner, a branch, what must be merged before it starts, what must be merged before it merges, the files it owns and a forecast. Each story in `epics.md` carries its owner and PR IDs, so an agent given a PR ID can find everything it needs. Timing, milestones and fallback cuts are in `build-schedule.md`. The forecasts come from a model, not from a validated run; the milestones in `build-schedule.md` are how the day checks them.

## The two lanes

| | Luis | Vlad |
|---|---|---|
| Agents | Up to 44: builders, reviewer agents, the contract keeper and integrators | Sonnet 5.5 at high effort: one main agent and ten subagents |
| Model budget | Claude plan; the product runs on Luis's API key | Claude Pro plus $300 of API credit |
| Owns | The critical path and the Demo path back end: contracts, ingest pipeline, review loop APIs, Alerts API, graph, memory, Home, shell, Review, Alerts inbox, Diagnostics and Record, deploys, Baseline, the three integration checks, rehearsal, submission | Find and Categories (Epic 4), the Jobs page, Digest and Rules on screen, five isolated stories (1.10, 1.11, 3.4, 3.5, 7.1) and Value history (2.5) |
| PRs | 39 (58.3 agent-hours) | 19 (about 38.6 agent-hours on Sonnet) |
| Merge coordinator | Luis, for Luis's lane | Vlad, for Vlad's lane, after Luis's review agent passes each PR |

PR counts are not workload: Luis's PRs include the critical path, all three integration checks and the production runs, so Luis's attention goes to ingest, integration and failures.

## Contracts come first, and they cover more than API shapes

P01, P02 and P04 start at 9:39 together. Between them they freeze:

- every API route and response shape, including everything `epics.md` adds to AD-14 (shortlists, `Job.active`, Alert detail, graph `team_id` and `sample_type`, `last_seen_at`, `completeness`, `source_date`) and one error shape;
- the registry and identity functions;
- the Finding model and fixtures, drafted from the architecture spine from 9:39 and validated once P01 and P02 merge;
- the function signatures, return types and error behaviour backend PRs code against: `llm.extract()`, `llm.check()`, `ledger.file()`, `ledger.decide()`, the job item, `memory`, `rules.evaluate()`, `alerts.react()` and `search.completeness()`.

After 11:09 a change to any of these goes through the contract keeper in its own PR.

## Start requirements and merge requirements are separate

Each card says two things:

- **Start when merged:** what must be on `main` before the agent starts. For most PRs this is only the contracts, so work runs in parallel instead of one PR after another.
- **Merge after:** what must be on `main` before this PR merges, because it calls real code or another PR's file.

A PR that calls a module not yet merged builds against the frozen signature and the fixtures, and is proved against the real module at an integration check.

## Integration happens three times, not once

| Check | PR | When | What runs |
|---|---|---|---|
| Seeded records | P41 | about 13:18 | Every merged screen against the dev database after the FDA seed |
| Small real ingest | P42 | about 14:24 | Every merged screen against the 50-item run |
| Final acceptance | P38 | about 15:24 | Every demo screen against the full Baseline in production |

Failures surface during the day, not at the end. P38 is the last check, not the first contact with real data.

## How agent slots are used

58 PRs are not 58 builders at once. The forecast peak is about 20 builders in Luis's lane and 8 to 10 in Vlad's. The rest of the slots go to:

- one independent reviewer agent per open PR, checking acceptance criteria, secrets, `.env` values and PubMed text;
- the contract keeper, who rejects any PR that changes a frozen contract without regenerating the types;
- integrators, who run P41, P42 and P38 and keep a smoke test passing on every merge.

People spend their attention on unclear behaviour and failures, not on reading every diff.

## How to brief an agent for one PR

Give each agent one PR ID and this brief, filled in from its card:

```
You are building PR <ID> of DxP: <What>.
Read first: _bmad-output/planning-artifacts/development-plan.md (card <ID>),
the Story <n.n> acceptance criteria in epics.md, the architecture spine
(AD rules it cites), and for screens DESIGN.md, EXPERIENCE.md and the mockup.
Branch: <branch>, from the latest main. Start only when every PR under
"Start when merged" is on main. Code against the frozen contracts and
fixtures from P01, P02 and P04 for anything not merged yet. Only edit the
files this PR owns; anything else goes back to its owner. Do not merge
until every PR under "Merge after" is on main.
Never commit secrets or .env values. Never write PubMed abstract text to
any file. Open the PR as "Story <n.n>: <What> (<ID>)" with the acceptance
criteria as a checklist, and follow the PR and merge steps in epics.md.
```

## Luis's PRs

| PR | Story | What | Branch | Start when merged | Merge after | Start | Finish |
|---|---|---|---|---|---|---|---|
| P03 | 1.3 | Web skeleton (critical) | `story/1.3a-web-skeleton` | none | none | 09:39 | 10:24 |
| P01 | 1.1 | API contract stub and generated types (near-critical) | `story/1.1a-contract` | none | none | 09:39 | 10:39 |
| P02 | 1.2 | Registry and identity | `story/1.2a-registry-identity` | none | none | 09:39 | 10:39 |
| P04 | 1.6 | Finding contract and module interfaces (near-critical) | `story/1.6a-finding-contract` | none | P01, P02 | 09:39 | 10:39 |
| P23 | 6.1 | Memory adapter | `story/6.1-memory` | none | P01 | 09:39 | 12:39 |
| P31 | 3.2 | Alerts inbox | `story/3.2-alerts-inbox` | P03 | none | 10:24 | 12:24 |
| P34 | 6.4 | Home welcome panel, Alerts and Digest layout | `story/6.4b-home-panels` | P03 | none | 10:24 | 12:24 |
| P33 | 5.2 | Graph component (critical) | `story/5.2a-graph-component` | P03 | none | 10:24 | 12:54 |
| P27 | 1.12 | App shell | `story/1.12-app-shell` | P03 | none | 10:24 | 13:24 |
| P26 | 1.3 | Diagnostics and Record pages | `story/1.3b-diagnostics-record` | P03 | P05 | 10:24 | 13:54 |
| P29 | 2.4 | Review screen | `story/2.4-review-screen` | P03 | none | 10:24 | 13:54 |
| P07 | 1.4 | Load Source items | `story/1.4-load-sources` | P01 | none | 10:39 | 11:15 |
| P18 | 2.2 | Proposals queue API | `story/2.2-proposals-api` | P04 | none | 10:39 | 11:33 |
| P05 | 1.1 | Read model and change feed | `story/1.1b-readmodel-changes` | P01 | none | 10:39 | 11:39 |
| P06 | 8.1 | Deploy and CI | `story/8.1-deploy-ci` | P01, P03 | none | 10:39 | 11:39 |
| P09 | 1.5 | Quote and support checks | `story/1.5b-quote-check` | P04 | none | 10:39 | 11:39 |
| P10 | 1.6 | Ledger, Baseline mode | `story/1.6b-ledger-baseline` | P04 | none | 10:39 | 12:03 |
| P08 | 1.5 | Triage and extraction calls (near-critical) | `story/1.5a-triage-extract` | P04 | none | 10:39 | 12:09 |
| P19 | 2.3 | Decisions API | `story/2.3-decisions-api` | P04 | none | 10:39 | 12:09 |
| P20 | 2.6 | Learned rules API | `story/2.6-rules-api` | P04 | none | 10:39 | 13:03 |
| P22 | 5.1 | Graph API | `story/5.1-graph-api` | P04 | none | 10:39 | 13:03 |
| P12 | 1.7 | Batch job (near-critical) | `story/1.7-batch-job` | P04 | none | 10:39 | 13:09 |
| P21 | 3.1 | Alerts API | `story/3.1-alerts-api` | P04 | none | 10:39 | 13:27 |
| P40 | 8.3 | Submission package | `story/8.3-submission` | P06 | none | 11:39 | 12:39 |
| P13 | 1.6 | Ledger, live mode and stage rule | `story/1.6c-ledger-live` | P10 | none | 12:03 | 12:45 |
| P11 | 1.2 | Seed FDA rows, Teams and terms | `story/1.2b-seed` | P10, P02 | none | 12:03 | 12:48 |
| P14 | 1.5 | Tune extraction on real items (near-critical) | `story/1.5c-tune-real-items` | P08, P09, P07 | none | 12:09 | 13:09 |
| P25 | 6.3 | Resume summary | `story/6.3-resume` | P23, P05 | none | 12:39 | 14:15 |
| P41 | 1.3 | Integration: screens on seeded records | `integration/is-seeded` | P11, P05, P06 | none | 12:48 | 13:18 |
| P24 | 6.2 | Synthetic Team history | `story/6.2-team-history` | P23, P11 | none | 12:48 | 13:24 |
| P35 | 5.2 | Graph page (critical) | `story/5.2b-graph-page` | P33 | none | 12:54 | 14:54 |
| P36 | 5.3 | Changed highlight (near-critical) | `story/5.3-changed-highlight` | P33 | none | 12:54 | 14:54 |
| P37 | 6.4 | Home hero network (near-critical) | `story/6.4a-home-hero` | P33 | none | 12:54 | 14:54 |
| P15 | 1.7 | Integration run: 50 items (near-critical) | `integration/i1-pipeline` | P14, P13, P12, P07, P11, P06 | none | 13:09 | 13:54 |
| P17 | 2.1 | Dry run of the Held-back set | `story/2.1-dry-run` | P15 | none | 13:54 | 14:24 |
| P42 | 1.7 | Integration: screens on the small real ingest | `integration/im-small-ingest` | P15 | none | 13:54 | 14:24 |
| P16 | 1.9 | Baseline load and snapshot (near-critical) | `story/1.9-baseline-load` | P15, P11, P06 | none | 13:54 | 14:48 |
| P38 | 8.2 | Final acceptance on production data (critical) | `integration/i2-acceptance` | P16, P42, P26, P27, V17, P29, V19, P31, V18, P35, P36, P37, P34, P18, P19, P20, P21, P22, P24, P25 | none | 14:54 | 15:24 |
| P39 | 8.2 | Rehearsal (critical) | `story/8.2-rehearsal` | P38, P17 | none | 15:24 | 16:09 |

## Vlad's PRs

| PR | Story | What | Branch | Start when merged | Merge after | Start | Finish |
|---|---|---|---|---|---|---|---|
| V01 | 4.8 | Unmatched terms page | `story/4.8-terms-page` | P03 | none | 10:24 | 11:39 |
| V02 | 4.3 | Comparison table: Evidence panel and keyboard | `story/4.3b-evidence-panel` | P03 | none | 10:24 | 12:17 |
| V17 | 1.8 | Jobs page | `story/1.8-jobs-page` | P03 | none | 10:24 | 12:54 |
| V19 | 2.7 | Rules on screen | `story/2.7-rules-screen` | P03 | none | 10:24 | 12:54 |
| V18 | 3.3 | Digest | `story/3.3-digest` | P03 | none | 10:24 | 12:54 |
| V06 | 4.3 | Comparison table and chips | `story/4.3a-compare-table` | P03 | none | 10:24 | 12:54 |
| V07 | 4.6 | Category landscape | `story/4.6-categories` | P03 | P05 | 10:24 | 12:54 |
| V08 | 4.1 | Search index with synonyms | `story/4.1b-synonyms` | P01 | none | 10:39 | 13:31 |
| V09 | 4.1 | Vector Search index | `story/4.1a-vector-index` | P01 | none | 10:39 | 13:47 |
| V11 | 4.2 | Plain-language query API | `story/4.2-query-api` | P04 | none | 10:39 | 14:09 |
| V03 | 4.7 | Add a value API | `story/4.7-add-value-api` | P04 | none | 11:39 | 13:09 |
| V04 | 1.11 | Tavily provider scan | `story/1.11-tavily` | P04 | none | 12:17 | 13:47 |
| V10 | 4.5 | Export | `story/4.5-export` | V06 | none | 12:54 | 14:01 |
| V05 | 7.1 | Quick capture | `story/7.1-quick-capture` | P04 | none | 12:54 | 14:24 |
| V14 | 4.4 | Shortlist | `story/4.4-shortlist` | V06 | none | 12:54 | 15:24 |
| V12 | 1.10 | Scheduled scan | `story/1.10-scheduled-scan` | P12 | none | 13:09 | 14:17 |
| V13 | 3.4 | Audio briefing | `story/3.4-audio-briefing` | P21 | none | 13:27 | 14:35 |
| V16 | 2.5 | Value history | `story/2.5-value-history` | P26 | none | 13:54 | 15:47 |
| V15 | 3.5 | Play button | `story/3.5-play-button` | P31, V13 | none | 14:35 | 15:49 |

Vlad's times assume ten subagents and Sonnet cycle times 1.25 times the Opus figures (see `build-schedule.md`).

## PR cards

### P03: Web skeleton

- **Owner:** Luis · **Story:** 1.3 · **Branch:** `story/1.3a-web-skeleton` · **Forecast:** 09:39 to 10:24 · **Critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** `web/` from `create-next-app` (Next.js 16, TypeScript, App Router, Tailwind), `shadcn init`, `web/lib/api.ts` (typed fetch using `types.ts` once P01 lands, a hand stub before), and the one server route that adds `X-DxP-Key`.
- **Files this PR owns:** web/ (everything except web/lib/types.ts)
- **Done when:** the Story 1.3 acceptance criteria this scope covers pass, and the PR is merged.

### P01: API contract stub and generated types

- **Owner:** Luis · **Story:** 1.1 · **Branch:** `story/1.1a-contract` · **Forecast:** 09:39 to 10:39 · **Near-critical**
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** Create the `backend/` package with `uv`, a Modal app serving FastAPI, every AD-14 Pydantic class in `models.py`, every AD-14 route plus the routes and fields `epics.md` adds (shortlists, `Job.active`, Alert detail, graph `team_id` and `sample_type`, `last_seen_at`, `completeness`, `source_date`) returning 501 except `GET /schema`, the error shape `{ error: { code, message } }` for every route, the `store` module with `ensure_indexes()`, and the `npm` script that generates `web/lib/types.ts`. Leave the read model and `/changes` to P05.
- **Files this PR owns:** backend/pyproject.toml, backend/dxp/api/, backend/dxp/store/, web/lib/types.ts, web/package.json script only
- **Done when:** the Story 1.1 acceptance criteria this scope covers pass, and the PR is merged.

### P02: Registry and identity

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2a-registry-identity` · **Forecast:** 09:39 to 10:39
- **Start when merged:** nothing: start at once
- **Merge after:** nothing beyond its own checks
- **Scope:** `schema/registry.py` (ten fields, cardinality, enums, stage order, confidence threshold, `canonical()`, `is_early_research()`) and `identity.derive()`, `identity.normalise_name()` as AD-3. Seeding is P11.
- **Files this PR owns:** backend/dxp/schema/registry.py, backend/dxp/identity.py, their tests
- **Done when:** the Story 1.2 acceptance criteria this scope covers pass, and the PR is merged.

### P04: Finding contract and module interfaces

- **Owner:** Luis · **Story:** 1.6 · **Branch:** `story/1.6a-finding-contract` · **Forecast:** 09:39 to 10:39 · **Near-critical**
- **Start when merged:** nothing: start at once
- **Merge after:** P01, P02
- **Scope:** Drafted from 9:39 from the architecture spine, alongside P01 and P02, and validated once they merge. The `Finding` model and five JSON fixtures, and the frozen signatures, return types and error behaviour other PRs code against: `llm.extract()` and `llm.check()` (failure record, never raise), `ledger.file(finding_id, changes, mode)` (duplicate-key means exists), `ledger.decide()`, the job item contract, `memory` (empty result on error), `rules.evaluate()`, `alerts.react()`, `search.completeness()`. Bodies raise `NotImplementedError`.
- **Files this PR owns:** backend/dxp/ledger/types.py, backend/dxp/llm/__init__.py (signatures), backend/dxp/jobs/types.py, backend/tests/fixtures/findings/
- **Done when:** the Story 1.6 acceptance criteria this scope covers pass, and the PR is merged.

### P23: Memory adapter

- **Owner:** Luis · **Story:** 6.1 · **Branch:** `story/6.1-memory` · **Forecast:** 09:39 to 12:39
- **Start when merged:** nothing: start at once
- **Merge after:** P01
- **Scope:** `agent_engine` and `collections` backends behind one interface; only `backend/dxp/memory` imports the SDK; errors never fail a request.
- **Files this PR owns:** backend/dxp/memory/
- **Done when:** the Story 6.1 acceptance criteria this scope covers pass, and the PR is merged.

### P31: Alerts inbox

- **Owner:** Luis · **Story:** 3.2 · **Branch:** `story/3.2-alerts-inbox` · **Forecast:** 10:24 to 12:24
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Team picker, Alerts newest first with why line, stage, Evidence, dismiss; the shared Alert item component.
- **Files this PR owns:** web/app/alerts/, web/components/alert-item/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/alerts.html`
- **Done when:** the Story 3.2 acceptance criteria this scope covers pass, and the PR is merged.

### P34: Home welcome panel, Alerts and Digest layout

- **Owner:** Luis · **Story:** 6.4 · **Branch:** `story/6.4b-home-panels` · **Forecast:** 10:24 to 12:24
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Welcome-back panel with memory tag from `NEXT_PUBLIC_MEMORY_BACKEND`, Reopen fallback, latest 2 of 5 Alerts, Digest.
- **Files this PR owns:** web/app/page.tsx, web/components/welcome/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/home.html`
- **Done when:** the Story 6.4 acceptance criteria this scope covers pass, and the PR is merged.

### P33: Graph component

- **Owner:** Luis · **Story:** 5.2 · **Branch:** `story/5.2a-graph-component` · **Forecast:** 10:24 to 12:54 · **Critical**
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** `react-force-graph-2d` via `next/dynamic`, node colours and shapes, legend, focus path rendering; reused by Home.
- **Files this PR owns:** web/components/graph/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/graph.html`
- **Done when:** the Story 5.2 acceptance criteria this scope covers pass, and the PR is merged.

### P27: App shell

- **Owner:** Luis · **Story:** 1.12 · **Branch:** `story/1.12-app-shell` · **Forecast:** 10:24 to 13:24
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Tokens, fonts, logo, top bar v3, tissue field, stage track, badges, toasts, skeletons.
- **Files this PR owns:** web/components/shell/, web/app/layout.tsx, web/styles/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/index.html (top bar on every page)`
- **Done when:** the Story 1.12 acceptance criteria this scope covers pass, and the PR is merged.

### P26: Diagnostics and Record pages

- **Owner:** Luis · **Story:** 1.3 · **Branch:** `story/1.3b-diagnostics-record` · **Forecast:** 10:24 to 13:54
- **Start when merged:** P03
- **Merge after:** P05
- **Scope:** Diagnostics list and Record page with Evidence on every value, Unreviewed values with Accept, Edit, Reject, "your name" picker.
- **Files this PR owns:** web/app/diagnostics/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/diagnostics.html, mockups/record.html`
- **Done when:** the Story 1.3 acceptance criteria this scope covers pass, and the PR is merged.

### P29: Review screen

- **Owner:** Luis · **Story:** 2.4 · **Branch:** `story/2.4-review-screen` · **Forecast:** 10:24 to 13:54
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** The queue with focused row, compact actions, j/k/a/e/r/Esc, reasons required, rule flags.
- **Files this PR owns:** web/app/review/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/review.html`
- **Done when:** the Story 2.4 acceptance criteria this scope covers pass, and the PR is merged.

### P07: Load Source items

- **Owner:** Luis · **Story:** 1.4 · **Branch:** `story/1.4-load-sources` · **Forecast:** 10:39 to 11:15
- **Start when merged:** P01
- **Merge after:** nothing beyond its own checks
- **Scope:** `python -m dxp.sources.load` upserts every item with `window`, `sets` and `source_date`.
- **Files this PR owns:** backend/dxp/sources/load.py and tests
- **Done when:** the Story 1.4 acceptance criteria this scope covers pass, and the PR is merged.

### P18: Proposals queue API

- **Owner:** Luis · **Story:** 2.2 · **Branch:** `story/2.2-proposals-api` · **Forecast:** 10:39 to 11:33
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `GET /proposals?status=pending` with `diagnostic_id=`; low confidence first, then rule-flagged, then the rest; no PubMed text.
- **Files this PR owns:** backend/dxp/api/routes_proposals.py, backend/dxp/review/queue.py
- **Done when:** the Story 2.2 acceptance criteria this scope covers pass, and the PR is merged.

### P05: Read model and change feed

- **Owner:** Luis · **Story:** 1.1 · **Branch:** `story/1.1b-readmodel-changes` · **Forecast:** 10:39 to 11:39
- **Start when merged:** P01
- **Merge after:** nothing beyond its own checks
- **Scope:** `search.readmodel` and the real `GET /diagnostics`, `GET /diagnostics/<dx_id>` and `GET /changes?after=` (plain polling). The read model calls `search.completeness()` (Vlad, V07) through its frozen signature; until V07 merges it returns null.
- **Files this PR owns:** backend/dxp/search/readmodel.py, backend/dxp/api/routes_diagnostics.py, backend/dxp/api/routes_changes.py
- **Done when:** the Story 1.1 acceptance criteria this scope covers pass, and the PR is merged.

### P06: Deploy and CI

- **Owner:** Luis · **Story:** 8.1 · **Branch:** `story/8.1-deploy-ci` · **Forecast:** 10:39 to 11:39
- **Start when merged:** P01, P03
- **Merge after:** nothing beyond its own checks
- **Scope:** GitHub Actions on every pull request (web type check and build, backend tests), Vercel previews and production from `main`, `modal deploy` with `DXP_DB=dxp`, CORS to the Vercel origins, README section on who deploys and the PR steps.
- **Files this PR owns:** .github/workflows/, web/vercel.json if needed, backend/dxp/api/app.py (CORS only), README.md (deploy section)
- **Done when:** the Story 8.1 acceptance criteria this scope covers pass, and the PR is merged.

### P09: Quote and support checks

- **Owner:** Luis · **Story:** 1.5 · **Branch:** `story/1.5b-quote-check` · **Forecast:** 10:39 to 11:39
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `evidence.quote_in_source()` and the support check call; a value passes only when both are true.
- **Files this PR owns:** backend/dxp/evidence/ and its prompt file under backend/dxp/llm/prompts/
- **Done when:** the Story 1.5 acceptance criteria this scope covers pass, and the PR is merged.

### P10: Ledger, Baseline mode

- **Owner:** Luis · **Story:** 1.6 · **Branch:** `story/1.6b-ledger-baseline` · **Forecast:** 10:39 to 12:03
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `ledger.file()` in `baseline` mode: `ensure_diagnostic` on `aliases`, insert-if-absent Findings, values applied `unreviewed`, one update writing value, `rev`, `search_text`, `facets`, `edges`, and `store.emit_event()`.
- **Files this PR owns:** backend/dxp/ledger/file.py, backend/dxp/store/events.py
- **Done when:** the Story 1.6 acceptance criteria this scope covers pass, and the PR is merged.

### P08: Triage and extraction calls

- **Owner:** Luis · **Story:** 1.5 · **Branch:** `story/1.5a-triage-extract` · **Forecast:** 10:39 to 12:09 · **Near-critical**
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** Triage on Haiku 5.5 and extraction on Sonnet 5.5 through `llm`, one Finding per Diagnostic named, raw value, quote and confidence per field, backoff and failure records.
- **Files this PR owns:** backend/dxp/llm/ (client, triage, extract, prompts)
- **Done when:** the Story 1.5 acceptance criteria this scope covers pass, and the PR is merged.

### P19: Decisions API

- **Owner:** Luis · **Story:** 2.3 · **Branch:** `story/2.3-decisions-api` · **Forecast:** 10:39 to 12:09
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** Accept, edit, reject with reason; claim and apply in one update; history kept with reason; review of unreviewed values; events.
- **Files this PR owns:** backend/dxp/ledger/decide.py, backend/dxp/api/routes_decisions.py
- **Done when:** the Story 2.3 acceptance criteria this scope covers pass, and the PR is merged.

### P20: Learned rules API

- **Owner:** Luis · **Story:** 2.6 · **Branch:** `story/2.6-rules-api` · **Forecast:** 10:39 to 13:03
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `rules.draft()`, `rules.evaluate()`, status on and off, flags only, Discard sets the rule off, `GET /rules`, synthetic rules.
- **Files this PR owns:** backend/dxp/rules/, backend/dxp/api/routes_rules.py, backend/dxp/llm/prompts/rule_draft.*
- **Done when:** the Story 2.6 acceptance criteria this scope covers pass, and the PR is merged.

### P22: Graph API

- **Owner:** Luis · **Story:** 5.1 · **Branch:** `story/5.1-graph-api` · **Forecast:** 10:39 to 13:03
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `GET /graph` with `after`, `focus`, `depth`, `team_id`; nodes with `sample_type`; `$graphLookup`; `POST /teams/<id>/seen` storing `last_seen_seq` and `last_seen_at`.
- **Files this PR owns:** backend/dxp/graph/, backend/dxp/api/routes_graph.py
- **Done when:** the Story 5.1 acceptance criteria this scope covers pass, and the PR is merged.

### P12: Batch job

- **Owner:** Luis · **Story:** 1.7 · **Branch:** `story/1.7-batch-job` · **Forecast:** 10:39 to 13:09 · **Near-critical**
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `POST /jobs`, `GET /jobs`, `GET /jobs/<id>`; one LangGraph run with `Send` at concurrency 16; `counts`, `actor`, `started_at`, `finished_at`, `active`, failures; resume via `processed_at`; stall rule. Built with stubbed extraction and ledger.
- **Files this PR owns:** backend/dxp/jobs/, backend/dxp/api/routes_jobs.py
- **Done when:** the Story 1.7 acceptance criteria this scope covers pass, and the PR is merged.

### P21: Alerts API

- **Owner:** Luis · **Story:** 3.1 · **Branch:** `story/3.1-alerts-api` · **Forecast:** 10:39 to 13:27
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `alerts.react()` first and update Alerts, `why` line, `diagnostic_name`, stages and Evidence on the Alert, `GET /alerts`, dismiss.
- **Files this PR owns:** backend/dxp/alerts/, backend/dxp/api/routes_alerts.py, backend/dxp/llm/prompts/why.*
- **Done when:** the Story 3.1 acceptance criteria this scope covers pass, and the PR is merged.

### P40: Submission package

- **Owner:** Luis · **Story:** 8.3 · **Branch:** `story/8.3-submission` · **Forecast:** 11:39 to 12:39
- **Start when merged:** P06
- **Merge after:** nothing beyond its own checks
- **Scope:** README disclosure, what was built on Saturday, MongoDB capability table, credits, links.
- **Files this PR owns:** README.md
- **Done when:** the Story 8.3 acceptance criteria this scope covers pass, and the PR is merged.

### P13: Ledger, live mode and stage rule

- **Owner:** Luis · **Story:** 1.6 · **Branch:** `story/1.6c-ledger-live` · **Forecast:** 12:03 to 12:45
- **Start when merged:** P10
- **Merge after:** nothing beyond its own checks
- **Scope:** Live mode (`pending` on tracked Diagnostics), equal-value and `single`-field rules, stage only moves forward with `stage_advance`, concurrency test.
- **Files this PR owns:** backend/dxp/ledger/file.py
- **Done when:** the Story 1.6 acceptance criteria this scope covers pass, and the PR is merged.

### P11: Seed FDA rows, Teams and terms

- **Owner:** Luis · **Story:** 1.2 · **Branch:** `story/1.2b-seed` · **Forecast:** 12:03 to 12:48
- **Start when merged:** P10, P02
- **Merge after:** nothing beyond its own checks
- **Scope:** Seed the 76 lung FDA rows through `ledger.file()` in Baseline mode, three synthetic Teams, `GET /teams`, the curated "liquid biopsy" synonym. Idempotent.
- **Files this PR owns:** backend/dxp/ledger/seed.py, backend/dxp/api/routes_teams.py
- **Done when:** the Story 1.2 acceptance criteria this scope covers pass, and the PR is merged.

### P14: Tune extraction on real items

- **Owner:** Luis · **Story:** 1.5 · **Branch:** `story/1.5c-tune-real-items` · **Forecast:** 12:09 to 13:09 · **Near-critical**
- **Start when merged:** P08, P09, P07
- **Merge after:** nothing beyond its own checks
- **Scope:** Run 20 baseline trials end to end through `llm` and the checks, fix prompts until quotes are found, print Findings; no PubMed text in any file.
- **Files this PR owns:** backend/dxp/llm/prompts/, backend/dxp/evidence/
- **Done when:** the Story 1.5 acceptance criteria this scope covers pass, and the PR is merged.

### P25: Resume summary

- **Owner:** Luis · **Story:** 6.3 · **Branch:** `story/6.3-resume` · **Forecast:** 12:39 to 14:15
- **Start when merged:** P23, P05
- **Merge after:** nothing beyond its own checks
- **Scope:** `GET /teams/<id>` with changes since `last_seen_seq`, a resume from `recall`, last Intended use and Shortlist; episodes written on search, open and dismiss.
- **Files this PR owns:** backend/dxp/api/routes_teams.py (team detail), backend/dxp/memory/resume.py
- **Done when:** the Story 6.3 acceptance criteria this scope covers pass, and the PR is merged.

### P41: Integration: screens on seeded records

- **Owner:** Luis · **Story:** 1.3 · **Branch:** `integration/is-seeded` · **Forecast:** 12:48 to 13:18
- **Start when merged:** P11, P05, P06
- **Merge after:** nothing beyond its own checks
- **Scope:** Every merged screen against the dev database after the seed (P11): Diagnostics, Record, Review queue, graph. Fix what breaks.
- **Files this PR owns:** fixes only
- **Done when:** the Story 1.3 acceptance criteria this scope covers pass, and the PR is merged.

### P24: Synthetic Team history

- **Owner:** Luis · **Story:** 6.2 · **Branch:** `story/6.2-team-history` · **Forecast:** 12:48 to 13:24
- **Start when merged:** P23, P11
- **Merge after:** nothing beyond its own checks
- **Scope:** Five to ten synthetic episodes per Team, last Intended use and one Shortlist; idempotent.
- **Files this PR owns:** backend/dxp/memory/seed.py
- **Done when:** the Story 6.2 acceptance criteria this scope covers pass, and the PR is merged.

### P35: Graph page

- **Owner:** Luis · **Story:** 5.2 · **Branch:** `story/5.2b-graph-page` · **Forecast:** 12:54 to 14:54 · **Critical**
- **Start when merged:** P33
- **Merge after:** nothing beyond its own checks
- **Scope:** Graph page, click-through to Record and Evidence, focus and neighbourhood, side panel, View as table, `$graphLookup` tag.
- **Files this PR owns:** web/app/graph/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/graph.html`
- **Done when:** the Story 5.2 acceptance criteria this scope covers pass, and the PR is merged.

### P36: Changed highlight

- **Owner:** Luis · **Story:** 5.3 · **Branch:** `story/5.3-changed-highlight` · **Forecast:** 12:54 to 14:54 · **Near-critical**
- **Start when merged:** P33
- **Merge after:** nothing beyond its own checks
- **Scope:** Changed marks with words, the one pulse (not under reduced motion), focus-mode dimming, live updates from `/changes`, Mark as seen.
- **Files this PR owns:** web/components/graph/changes.ts, web/app/graph/ (toolbar)
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/graph.html`
- **Done when:** the Story 5.3 acceptance criteria this scope covers pass, and the PR is merged.

### P37: Home hero network

- **Owner:** Luis · **Story:** 6.4 · **Branch:** `story/6.4a-home-hero` · **Forecast:** 12:54 to 14:54 · **Near-critical**
- **Start when merged:** P33
- **Merge after:** nothing beyond its own checks
- **Scope:** Dark hero with the Team network from `GET /graph?team_id=`, changed glow and pulse, click to Graph focused.
- **Files this PR owns:** web/components/hero/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/home.html`
- **Done when:** the Story 6.4 acceptance criteria this scope covers pass, and the PR is merged.

### P15: Integration run: 50 items

- **Owner:** Luis · **Story:** 1.7 · **Branch:** `integration/i1-pipeline` · **Forecast:** 13:09 to 13:54 · **Near-critical**
- **Start when merged:** P14, P13, P12, P07, P11, P06
- **Merge after:** nothing beyond its own checks
- **Scope:** Wire real extraction and ledger into the job; a 50-item run with one forced failure gives 49 done, 1 failed, no duplicates.
- **Files this PR owns:** fixes only, in the modules above
- **Done when:** the Story 1.7 acceptance criteria this scope covers pass, and the PR is merged.

### P17: Dry run of the Held-back set

- **Owner:** Luis · **Story:** 2.1 · **Branch:** `story/2.1-dry-run` · **Forecast:** 13:54 to 14:24
- **Start when merged:** P15
- **Merge after:** nothing beyond its own checks
- **Scope:** `mode: dry_run` writes nothing; prints matched Diagnostic and fields per item; five camera items recorded in the README demo notes.
- **Files this PR owns:** backend/dxp/jobs/ (dry_run mode), README.md (demo notes)
- **Done when:** the Story 2.1 acceptance criteria this scope covers pass, and the PR is merged.

### P42: Integration: screens on the small real ingest

- **Owner:** Luis · **Story:** 1.7 · **Branch:** `integration/im-small-ingest` · **Forecast:** 13:54 to 14:24
- **Start when merged:** P15
- **Merge after:** nothing beyond its own checks
- **Scope:** Every merged screen against the 50-item run from P15. Fix what breaks.
- **Files this PR owns:** fixes only
- **Done when:** the Story 1.7 acceptance criteria this scope covers pass, and the PR is merged.

### P16: Baseline load and snapshot

- **Owner:** Luis · **Story:** 1.9 · **Branch:** `story/1.9-baseline-load` · **Forecast:** 13:54 to 14:48 · **Near-critical**
- **Start when merged:** P15, P11, P06
- **Merge after:** nothing beyond its own checks
- **Scope:** Run the Baseline in production: trials first, then the 150 most recent PubMed items of `small` in the baseline window. Snapshot with `mongodump` outside the repo; retake procedure in the README.
- **Files this PR owns:** README.md (retake section)
- **Done when:** the Story 1.9 acceptance criteria this scope covers pass, and the PR is merged.

### P38: Final acceptance on production data

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `integration/i2-acceptance` · **Forecast:** 14:54 to 15:24 · **Critical**
- **Start when merged:** P16, P42, P26, P27, V17, P29, V19, P31, V18, P35, P36, P37, P34, P18, P19, P20, P21, P22, P24, P25
- **Merge after:** nothing beyond its own checks
- **Scope:** Final check, not first contact: every demo screen against the full Baseline in production. By now screens have run on seeded records (P41) and the small ingest (P42).
- **Files this PR owns:** fixes only
- **Done when:** the Story 8.2 acceptance criteria this scope covers pass, and the PR is merged.

### P39: Rehearsal

- **Owner:** Luis · **Story:** 8.2 · **Branch:** `story/8.2-rehearsal` · **Forecast:** 15:24 to 16:09 · **Critical**
- **Start when merged:** P38, P17
- **Merge after:** nothing beyond its own checks
- **Scope:** Live run of `narrow.heldback` then PubMed `small` held-back; one accept, one reject with a rule; memory write and read; restore from the snapshot. README notes only.
- **Files this PR owns:** README.md (demo notes)
- **Done when:** the Story 8.2 acceptance criteria this scope covers pass, and the PR is merged.

### V01: Unmatched terms page

- **Owner:** Vlad · **Story:** 4.8 · **Branch:** `story/4.8-terms-page` · **Forecast:** 10:24 to 11:39
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Terms page: term and times seen only.
- **Files this PR owns:** web/app/terms/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/terms.html`
- **Done when:** the Story 4.8 acceptance criteria this scope covers pass, and the PR is merged.

### V02: Comparison table: Evidence panel and keyboard

- **Owner:** Vlad · **Story:** 4.3 · **Branch:** `story/4.3b-evidence-panel` · **Forecast:** 10:24 to 12:17
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Evidence panel for a cell, focusable cells, Enter opens Evidence.
- **Files this PR owns:** web/components/compare/evidence-panel/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/find.html`
- **Done when:** the Story 4.3 acceptance criteria this scope covers pass, and the PR is merged.

### V17: Jobs page

- **Owner:** Vlad · **Story:** 1.8 · **Branch:** `story/1.8-jobs-page` · **Forecast:** 10:24 to 12:54
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Start a job, live counts, agents working now from `active`, failures, earlier jobs.
- **Files this PR owns:** web/app/jobs/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/jobs.html`
- **Done when:** the Story 1.8 acceptance criteria this scope covers pass, and the PR is merged.

### V19: Rules on screen

- **Owner:** Vlad · **Story:** 2.7 · **Branch:** `story/2.7-rules-screen` · **Forecast:** 10:24 to 12:54
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Rule draft panel after a reject or edit, Rules page with switches, Agent Memory tag.
- **Files this PR owns:** web/app/rules/, web/components/rule-panel/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/rules.html, mockups/review.html (rule card)`
- **Done when:** the Story 2.7 acceptance criteria this scope covers pass, and the PR is merged.

### V18: Digest

- **Owner:** Vlad · **Story:** 3.3 · **Branch:** `story/3.3-digest` · **Forecast:** 10:24 to 12:54
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** `GET /digest` and the Digest panel used on Home.
- **Files this PR owns:** backend/dxp/api/routes_digest.py, web/components/digest/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/home.html (Digest panel)`
- **Done when:** the Story 3.3 acceptance criteria this scope covers pass, and the PR is merged.

### V06: Comparison table and chips

- **Owner:** Vlad · **Story:** 4.3 · **Branch:** `story/4.3a-compare-table` · **Forecast:** 10:24 to 12:54
- **Start when merged:** P03
- **Merge after:** nothing beyond its own checks
- **Scope:** Find page: query box, parsed chips (filters-only rerun), table with stage track, Vector Search tag.
- **Files this PR owns:** web/app/find/
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/find.html`
- **Done when:** the Story 4.3 acceptance criteria this scope covers pass, and the PR is merged.

### V07: Category landscape

- **Owner:** Vlad · **Story:** 4.6 · **Branch:** `story/4.6-categories` · **Forecast:** 10:24 to 12:54
- **Start when merged:** P03
- **Merge after:** P05
- **Scope:** Categories page, `search.completeness()` in Vlad's own module (the read model owned by P05 already calls it), and the Category map in `schema/categories.py`. No edit to `readmodel.py`.
- **Files this PR owns:** web/app/categories/, backend/dxp/search/completeness.py, backend/dxp/schema/categories.py
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/categories.html`
- **Done when:** the Story 4.6 acceptance criteria this scope covers pass, and the PR is merged.

### V08: Search index with synonyms

- **Owner:** Vlad · **Story:** 4.1 · **Branch:** `story/4.1b-synonyms` · **Forecast:** 10:39 to 13:31
- **Start when merged:** P01
- **Merge after:** nothing beyond its own checks
- **Scope:** MongoDB Search index with the synonym mapping over `terms`, `search.terms` expansion, unmatched terms written, `GET /terms`.
- **Files this PR owns:** backend/dxp/search/terms.py, backend/dxp/api/routes_terms.py
- **Done when:** the Story 4.1 acceptance criteria this scope covers pass, and the PR is merged.

### V09: Vector Search index

- **Owner:** Vlad · **Story:** 4.1 · **Branch:** `story/4.1a-vector-index` · **Forecast:** 10:39 to 13:47
- **Start when merged:** P01
- **Merge after:** nothing beyond its own checks
- **Scope:** Vector Search index with Automated Embedding on `search_text`, readiness check, text-search fallback.
- **Files this PR owns:** backend/dxp/search/indexes.py
- **Done when:** the Story 4.1 acceptance criteria this scope covers pass, and the PR is merged.

### V11: Plain-language query API

- **Owner:** Vlad · **Story:** 4.2 · **Branch:** `story/4.2-query-api` · **Forecast:** 10:39 to 14:09
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `POST /query`: parsing to registry filters, facets filter, `$vectorSearch` ranking, filters-only path with no model call.
- **Files this PR owns:** backend/dxp/search/query.py, backend/dxp/api/routes_query.py, backend/dxp/llm/prompts/query.*
- **Done when:** the Story 4.2 acceptance criteria this scope covers pass, and the PR is merged.

### V03: Add a value API

- **Owner:** Vlad · **Story:** 4.7 · **Branch:** `story/4.7-add-value-api` · **Forecast:** 11:39 to 13:09
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** `POST /diagnostics/<id>/values` through `ledger.file()` with `evidence.manual`.
- **Files this PR owns:** backend/dxp/api/routes_values.py
- **Done when:** the Story 4.7 acceptance criteria this scope covers pass, and the PR is merged.

### V04: Tavily provider scan

- **Owner:** Vlad · **Story:** 1.11 · **Branch:** `story/1.11-tavily` · **Forecast:** 12:17 to 13:47
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** Provider adapter with `include_domains` from the allow-list.
- **Files this PR owns:** backend/dxp/sources/provider_web.py
- **Done when:** the Story 1.11 acceptance criteria this scope covers pass, and the PR is merged.

### V10: Export

- **Owner:** Vlad · **Story:** 4.5 · **Branch:** `story/4.5-export` · **Forecast:** 12:54 to 14:01
- **Start when merged:** V06
- **Merge after:** nothing beyond its own checks
- **Scope:** CSV export with escaping, formula guard and credits.
- **Files this PR owns:** web/lib/export.ts
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/find.html`
- **Done when:** the Story 4.5 acceptance criteria this scope covers pass, and the PR is merged.

### V05: Quick capture

- **Owner:** Vlad · **Story:** 7.1 · **Branch:** `story/7.1-quick-capture` · **Forecast:** 12:54 to 14:24
- **Start when merged:** P04
- **Merge after:** nothing beyond its own checks
- **Scope:** Capture box API and the top-bar button behaviour.
- **Files this PR owns:** backend/dxp/capture/, web/components/capture/
- **Done when:** the Story 7.1 acceptance criteria this scope covers pass, and the PR is merged.

### V14: Shortlist

- **Owner:** Vlad · **Story:** 4.4 · **Branch:** `story/4.4-shortlist` · **Forecast:** 12:54 to 15:24
- **Start when merged:** V06
- **Merge after:** nothing beyond its own checks
- **Scope:** Implements `POST /shortlists` and `GET /shortlists`, whose shapes are already in the P01 contract, plus row checkboxes and Save shortlist.
- **Files this PR owns:** backend/dxp/api/routes_shortlists.py, web/app/find/shortlist.tsx
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/find.html`
- **Done when:** the Story 4.4 acceptance criteria this scope covers pass, and the PR is merged.

### V12: Scheduled scan

- **Owner:** Vlad · **Story:** 1.10 · **Branch:** `story/1.10-scheduled-scan` · **Forecast:** 13:09 to 14:17
- **Start when merged:** P12
- **Merge after:** nothing beyond its own checks
- **Scope:** `modal.Cron` scan that starts a live job unless one is running; manual "scan now".
- **Files this PR owns:** backend/dxp/sources/scan.py
- **Done when:** the Story 1.10 acceptance criteria this scope covers pass, and the PR is merged.

### V13: Audio briefing

- **Owner:** Vlad · **Story:** 3.4 · **Branch:** `story/3.4-audio-briefing` · **Forecast:** 13:27 to 14:35
- **Start when merged:** P21
- **Merge after:** nothing beyond its own checks
- **Scope:** ElevenLabs briefing, cached, 503 on failure.
- **Files this PR owns:** backend/dxp/alerts/audio.py, backend/dxp/api/routes_audio.py
- **Done when:** the Story 3.4 acceptance criteria this scope covers pass, and the PR is merged.

### V16: Value history

- **Owner:** Vlad · **Story:** 2.5 · **Branch:** `story/2.5-value-history` · **Forecast:** 13:54 to 15:47
- **Start when merged:** P26
- **Merge after:** nothing beyond its own checks
- **Scope:** History disclosure on the Record: superseded and rejected values with Evidence, who, when and reason.
- **Files this PR owns:** web/app/diagnostics/[id]/history.tsx
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/record.html`
- **Done when:** the Story 2.5 acceptance criteria this scope covers pass, and the PR is merged.

### V15: Play button

- **Owner:** Vlad · **Story:** 3.5 · **Branch:** `story/3.5-play-button` · **Forecast:** 14:35 to 15:49
- **Start when merged:** P31, V13
- **Merge after:** nothing beyond its own checks
- **Scope:** Play, pause, loading and error states on the Alert item.
- **Files this PR owns:** web/components/alert-item/audio.tsx
- **Mockup:** `ux-designs/ux-agents-in-context-toronto-2026-11-13/mockups/alerts.html`
- **Done when:** the Story 3.5 acceptance criteria this scope covers pass, and the PR is merged.

