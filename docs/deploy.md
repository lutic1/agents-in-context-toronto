# Deploy on the Atlas Sandbox

Story 8.1, PR A04. This page names every variable, never its value (D48). Values live only in Luis's local `.env`, in the Modal secret and in the Vercel project settings. Nothing here is a secret.

## Who deploys what

| Part | Where | Who deploys | How |
|---|---|---|---|
| Web app (`web/`, Next.js) | Vercel | Vercel itself | A preview for every pull request; production from every merge to `main` |
| API and runs (`backend/`, FastAPI on Modal) | Modal app `dxp` | **Luis**, one person only | `DXP_DB=dxp modal deploy modal_app.py` from `backend/`, after each merge that changes the API (epics.md, "PR and merge", step 6) |
| Database | Organisers' Atlas Sandbox | nobody deploys it | `DXP_DB=dxp` for the demo; `dxp_smoke` for the integrators' smoke test; one `dxp_<name>` per developer; CI uses throwaway names (AD-24, D41) |

Nobody else runs `modal deploy`. Developers use `modal serve` with their own database and suffix (below).

## Continuous integration

`.github/workflows/ci.yml` runs on every pull request into `main` and on every push to `main`. Its three jobs are the required checks:

| Job | What it runs |
|---|---|
| `No committed .env` | Fails if any `.env` file other than `.env.example` is tracked |
| `Backend tests` | `uv sync --locked`, then `uv run pytest` in `backend/`, with `MONGODB_URI` from the repository secret and `DXP_DB=dxp_ci_<run>`; A01's `tests/conftest.py` then works in a fresh `dxp_test_<hex>` database and drops it. Never `dxp` or `dxp_smoke`. Then it imports `modal_app` (builds the app definition; no deploy, no Modal credentials). Skipped with a notice while `backend/pyproject.toml` (A01) is not on the branch |
| `Web type check and build` | Install, `typecheck` script (or `tsc --noEmit`), `build` in `web/`, with placeholder `NEXT_PUBLIC_*` values. Skipped with a notice while `web/package.json` (B01) is not on the branch |

GitHub Actions secrets (set by Luis) reach CI only; they never reach Modal or Vercel. The Modal secret and the Vercel variables are still set by hand (below). CI passes exactly two of them, to the pytest step:

| Actions secret | Passed to CI as | Why |
|---|---|---|
| `MONGODB_URI` | `MONGODB_URI` | Atlas Sandbox tests, in throwaway databases |
| `ANTHROPIC_KEY` | `DXP_LIVE_ANTHROPIC_API_KEY` only | A01's conftest replaces `ANTHROPIC_API_KEY` with a fake for every test, so A08's live extraction tests read the real key from `DXP_LIVE_ANTHROPIC_API_KEY`. The deployed code reads `ANTHROPIC_API_KEY` from the Modal secret |
| `SLACK_WEBHOOK_URL` | not passed | CI and merges never post to the real Slack channel |
| `ELEVENLABS_API_KEY` | not passed | Media tests use fakes |
| `LIVEAVATAR_API_KEY` | not passed | Media tests use fakes |

**Key name (V70):** the avatar is LiveAvatar, and B08 reads only `LIVEAVATAR_API_KEY`. `HEYGEN_API_KEY` is no longer used. The Modal secret also carries `LIVEAVATAR_AVATAR_ID` and `LIVEAVATAR_VOICE_ID` (not secret); `ELEVENLABS_VOICE_ID` is optional (B06 defaults to ElevenLabs "Jessica").

The workflow never prints a secret; GitHub masks them in logs. Backend flags stay off in CI (`DXP_FEATURES` empty).

## Variables

| Variable | Vercel | Modal secret `dxp` | Laptop `.env` only | Notes |
|---|---|---|---|---|
| `DXP_API_KEY` | yes (Production) | no | yes | Sam's key, added server-side by B01's route as `X-DxP-Key`; never `NEXT_PUBLIC_` |
| `NEXT_PUBLIC_API_URL` | yes | no | yes | The Modal API URL, without `/api/v1` (the web app appends it) |
| `NEXT_PUBLIC_DXP_FEATURES` | yes | no | yes | Display flags only (not a secret); see "Feature flags" |
| `MONGODB_URI` | no | yes (required) | yes | Atlas Sandbox connection string |
| `DXP_AGENT_KEY` | no | yes (required) | yes | The agent's key |
| `ANTHROPIC_API_KEY` | no | yes (required) | yes | |
| `SLACK_WEBHOOK_URL` | no | yes (required) | yes | Never in a log, trace, event, action or screen (AD-20) |
| `DXP_BASE_URL` | no | yes (required) | yes | The Vercel production URL; Slack links are `${DXP_BASE_URL}/reports/<report_id>` and `${DXP_BASE_URL}/diagnostics/<dx_id>` |
| `DXP_ALLOWED_ORIGINS` | no | yes (required) | yes | Comma-separated; the Vercel production URL (read by A01's `app.py`) |
| `DXP_EMBEDDING` | no | yes (required) | yes | `auto`, `voyage` or `none`, by the OD1 result |
| `DXP_FEATURES` | no | optional | yes | Backend flags; leave it out of the secret while every flag is off |
| `ELEVENLABS_API_KEY` | no | optional (OD3) | yes | Without it the briefing says "unavailable" |
| `LIVEAVATAR_API_KEY` | no | optional (OD7, V70) | yes | Without it the avatar says "unavailable" |
| `VOYAGE_API_KEY` | no | only if cleared (OD1) | yes | |
| `DXP_DB` | no | no | yes | Passed at deploy time from the shell by `modal_app.py` (`modal.Secret.from_dict`); required, never defaulted |
| `DXP_SEED_KEY` | no | no | yes | Command line only (seed, prior collection) |
| `DXP_DEMO_PACE` | no | add when rehearsing | yes | Set for the demo run pace (V16) |
| `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | no | optional | yes | |
| `MODAL_DEV_SUFFIX` | no | no | developer shell | Names a developer's app `dxp-<suffix>` |
| `DXP_MODAL_SECRET` | no | no | developer shell | Which Modal secret to read; default `dxp` |

`modal_app.py` refuses to deploy unless the Modal secret has every key marked "required". `DXP_FEED`, `DXP_GITHUB_TOKEN` and `DXP_GITHUB_REPO` exist nowhere.

## Feature flags

`task_run`, `revert` and `live_stream` stay **off** in both places (V38, V46, V48): `DXP_FEATURES` in the Modal secret is left out (or lists none of them), and `NEXT_PUBLIC_DXP_FEATURES` in Vercel does not list them.

- `task_run` only once A25 is merged and I3b passed.
- `revert` only once A26 passed S4.
- `live_stream` only once A27 and OD5 passed S5.
- `briefing`, `avatar` and `memory_edit` (display flags) only once S1, S2 and S3 passed.

Turning a flag on or off needs no code change: update the value, then redeploy (`modal deploy` for the backend; a Vercel redeploy for `NEXT_PUBLIC_*`, which is inlined at build time).

## Hand steps (Luis)

Run these yourself. Never paste a value into a chat, an issue, a commit or this file, and do not run `set -x` while values are loaded.

### 1. GitHub: protect `main`

In the repository settings:

1. Settings, General, Pull Requests: allow **squash merging** only; turn on "Automatically delete head branches".
2. Settings, Rules (or Branches): a rule for `main` that requires a pull request before merging and requires the status checks `Backend tests`, `Web type check and build` and `No committed .env` to pass, with the branch up to date.
3. Settings, Secrets and variables, Actions: `MONGODB_URI` is already set.

### 2. Vercel: the web project

1. Import the repository in Vercel; **Root Directory** `web`, framework Next.js (`web/vercel.json` pins it). Production branch `main`. Note the production domain: it is `DXP_BASE_URL`.
2. From `web/` on the laptop:

   ```bash
   vercel link
   vercel env add DXP_API_KEY production          # prompts for the value; paste from .env
   vercel env add NEXT_PUBLIC_API_URL production  # the Modal API URL from step 3
   vercel env add NEXT_PUBLIC_API_URL preview
   vercel env add NEXT_PUBLIC_DXP_FEATURES production   # flags that passed their check, or leave empty
   ```

   Previews get no `DXP_API_KEY`, so a preview never acts as Sam on the demo database; they build and render the shell.
3. After B01 is merged, Vercel deploys `main`. Redeploy production after any change to a `NEXT_PUBLIC_*` value.

### 3. Modal: the secret and the deploy

From `backend/` on the laptop, with the Modal CLI logged in (`modal token new` once):

```bash
# Load .env into this shell only, without echoing anything.
set +x; set -a; . ../.env; set +a

modal secret create dxp --force \
  MONGODB_URI="$MONGODB_URI" \
  DXP_AGENT_KEY="$DXP_AGENT_KEY" \
  ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL" \
  DXP_BASE_URL="$DXP_BASE_URL" \
  DXP_ALLOWED_ORIGINS="$DXP_ALLOWED_ORIGINS" \
  DXP_EMBEDDING="$DXP_EMBEDDING" \
  ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" \
  LIVEAVATAR_API_KEY="$LIVEAVATAR_API_KEY"
# Add VOYAGE_API_KEY="$VOYAGE_API_KEY" only if OD1 cleared it.
# Add DXP_FEATURES="..." only when a backend flag is turned on (see "Feature flags").
# Leave out any optional key that is still empty in .env (ElevenLabs, HeyGen).

DXP_DB=dxp modal deploy modal_app.py
```

`--force` replaces the whole secret, so every later change repeats the full command. Alternatively, enter the same keys one by one in the Modal dashboard (Secrets, `dxp`). Do not use `--from-dotenv ../.env`: it would copy `DXP_SEED_KEY` and `DXP_API_KEY` into Modal.

The deploy prints the API URL (`https://<workspace>--dxp.modal.run`): that is `NEXT_PUBLIC_API_URL` in Vercel. If `DXP_BASE_URL` was not known yet, set it after the first Vercel production deploy, rerun `modal secret create ... --force` and `modal deploy`.

### 4. Check the deploy

```bash
API=https://<workspace>--dxp.modal.run
curl -sS "$API/api/v1/schema" | head -c 200; echo                      # 200 with the registry
curl -sS -w ' %{http_code}\n' "$API/api/v1/changes"                   # 501 {"error":{"code":...,"message":...}}
curl -sS -o /dev/null -w '%{http_code}\n' "$API/openapi.json"         # 200
```

Then open the Vercel production URL: the shell loads. Once B04 is deployed, open `${DXP_BASE_URL}/reports/<report_id>` and `${DXP_BASE_URL}/diagnostics/<dx_id>` for a real report and Diagnostic and confirm both resolve (the integrator repeats this in I1).

### Developer and smoke-test backends

```bash
DXP_DB=dxp_<name> MODAL_DEV_SUFFIX=<name> modal serve modal_app.py   # own app dxp-<name>, own database
DXP_DB=dxp_smoke MODAL_DEV_SUFFIX=smoke modal serve modal_app.py     # integrators' smoke test
```

A suffixed app refuses `DXP_DB=dxp`. Under `modal serve` the API spawns its own run function, never production's (AD-16). A developer who needs different credentials creates their own secret and sets `DXP_MODAL_SECRET`.

## Sandbox checks

Recorded here as each check is run. Results are not filled in until someone has run the check.

| # | Check | Owner (records it here) | Result |
|---|---|---|---|
| OD1 | Vector Search indexes and Automated Embedding on the sandbox; else a cleared Voyage key; else `DXP_EMBEDDING=none` with text search, labelled | Gregorio (checked at 10:45, decided with Luis by 11:45) | To be recorded |
| OD5 | Change streams on the sandbox tier (`events.watch()` receives an insert); a long-lived `StreamingResponse` from `@modal.asgi_app`, and through a Vercel streaming proxy, with the point where each is cut | Gregorio (checked at 10:45, decided with Luis by 11:45) | To be recorded |
| OD6 | `mongodump` and `mongorestore` of a test database against the sandbox | Luis (by 12:20; proven at the I1 snapshot) | To be recorded |
| OD3 | `ELEVENLABS_API_KEY` set in the Modal secret | Luis | To be recorded |
| OD7 | `LIVEAVATAR_API_KEY` set in the Modal secret (account check by Vlad) | Luis | To be recorded |
| Deploy | Production URL loads the shell; `/api/v1/schema` answers; a stub route returns the 501 error shape | Luis | To be recorded |
| Links | `${DXP_BASE_URL}/reports/<report_id>` and `/diagnostics/<dx_id>` resolve | Luis (during A04), the integrator in I1 | To be recorded |

## PR and merge steps

From `epics.md`, "How every story lands":

1. Branch from the latest `main` as `story/<n.n>-<short-name>`; integration PRs use `integration/<name>`.
2. Open a pull request into `main` titled `Story <n.n>: <What> (<ID>)`, with the acceptance criteria as a checklist.
3. CI passes: `No committed .env`, `Backend tests`, `Web type check and build`.
4. The other developer (or their agent) reads the diff: no secret, `.env` value or Slack webhook URL in it, and each criterion met. Fixes found in I1, I3 or A16 go in small PRs reviewed by the file's owner (D36).
5. Squash-merge and delete the branch. If an API model changed, rebase first and regenerate `web/lib/types.ts`.
6. After the merge, check the deploy: Vercel deploys `main` itself; Luis runs `DXP_DB=dxp modal deploy modal_app.py` for API changes.
