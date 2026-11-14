---
name: dxp-vercel-frontend
description: Next.js 16 App Router front end (TypeScript, React 19) for DxP on Vercel - scaffolding, typed fetches to the Python API on Modal, CORS, server-sent events for live updates, the react-force-graph-2d Graph view, the comparison table with inline Evidence, deploys and Hobby limits. Load when a task touches `next`, `create-next-app`, `app/` routes, `page.tsx`, `route.ts`, `proxy.ts`, `next/dynamic`, `"use client"`, `NEXT_PUBLIC_API_URL`, `EventSource`, `react-force-graph`, the `vercel` CLI, preview or production deployments, or FR-8, FR-13, FR-22, FR-26, FR-27.
---

# Next.js on Vercel for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Event rule: everything in this skill is reference documentation. Do not copy code from it into the project; write new code during the event.
>
> Saturday scope is `_bmad-output/planning-artifacts/development-plan.md`. Baseline loading, PubMed, memory, Learned rules, Alerts, Tavily scans and the old three-minute recorded video (the 3-minute live demo is in scope) are deferred; ignore those parts of this skill.

## Verified

Checked 12 November 2026 against the official docs and the npm registry.

- npm `latest`: `next` 16.4.6, `create-next-app` 16.4.6, `react` and `react-dom` 19.3.1, `vercel` CLI 65.15.0, `react-force-graph-2d` 1.29.2 (MIT). Node.js 20.9 or later. `create-next-app` pins `typescript ^5`, `eslint ^9`, `@types/react ^19` and Tailwind CSS 4.
- Next.js: https://nextjs.org/docs/app/getting-started/installation , https://nextjs.org/docs/app/guides/upgrading/version-16 , https://nextjs.org/docs/app/api-reference/cli/create-next-app , https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents , https://nextjs.org/docs/app/api-reference/functions/fetch , https://nextjs.org/docs/app/api-reference/file-conventions/route , https://nextjs.org/docs/app/guides/lazy-loading , https://nextjs.org/docs/app/guides/streaming , https://nextjs.org/docs/app/guides/environment-variables
- Vercel: https://vercel.com/docs/functions/limitations , https://vercel.com/docs/functions/configuring-functions/duration , https://vercel.com/docs/limits , https://vercel.com/docs/plans/hobby , https://vercel.com/docs/cli/deploy , https://vercel.com/docs/cli/env , https://vercel.com/docs/git , https://vercel.com/docs/deployments/environments , https://vercel.com/docs/deployment-protection , https://vercel.com/kb/guide/publish-and-subscribe-to-realtime-data-on-vercel
- Others: react-force-graph README and `.d.ts`, MDN "Using server-sent events", FastAPI CORS tutorial, Modal request timeouts.
- All TypeScript here and in `references/` was type-checked (tsc 5.9, strict) against the published type declarations of these versions. It was not run in a browser.

## Read this first

1. **The Vercel timeout people remember is out of date.** New projects run on Fluid compute, where the Hobby limit is 300 s default and maximum (Pro: 300 s default, 800 s maximum). The reason the agents stay on Modal is no longer a 10 s cap. It is that a 300 s request cannot hold a 300 to 500 item batch or an unattended scan, and the agents are Python. See "Why the agents do not run here".
2. **`create-next-app` now turns on Cache Components by default.** That mode removes the `dynamic`, `revalidate` and `fetchCache` route exports, rejects any `runtime` export, and raises a blocking-route error for uncached data read outside `<Suspense>`. Generated code trips on all three. Scaffold with `--no-cache-components` (below).
3. **Next.js 16 removed things generated code still writes**: synchronous `params`, `searchParams`, `cookies()`, `headers()`; `middleware.ts` (now `proxy.ts`); `next lint`. See Gotchas.
4. **Browser calls to Modal must finish in under 150 s**, and Modal's long-request redirect does not work with CORS. Start a job, return an id, then stream or poll.
5. **Preview deployments sit behind a Vercel login by default** (Standard Protection). Give judges the production URL only.
6. **Hobby cannot connect a repository owned by a GitHub organisation**, has no team collaboration features (one person owns the project), and builds one deployment at a time.
7. npm `latest` for `typescript` is 7.0.2. Keep the `^5` that `create-next-app` installs. Next.js states a minimum of 5.1; TypeScript 7 with Next.js 16 is UNVERIFIED.

## What DxP uses it for

- FR-26, FR-27: the Graph view, with click to open a Record or Evidence and highlighting of what changed. [references/graph-view.md](references/graph-view.md)
- FR-27, FR-4: changes and run progress appearing in the browser as they land (Alerts, FR-13, are deferred on Saturday). [references/live-updates.md](references/live-updates.md)
- FR-22, FR-7, FR-8, FR-2, FR-16: the comparison table with Evidence inline, the explicit no-data state, and the Early research and unreviewed marks. [references/data-and-table.md](references/data-and-table.md)
- FR-16, FR-21: review and query screens are ordinary pages that call the Python API with `api()`. (Learned rule, FR-19, and memory-based resume, FR-28, are deferred on Saturday.)
- SM-1: a public URL for the submission.

## Setup

```bash
# from the repository root; creates ./web
npx create-next-app@latest web --ts --tailwind --eslint --app --no-src-dir --no-react-compiler \
  --no-cache-components --no-agent-feedback --import-alias "@/*" --disable-git --use-npm --yes
cd web
npm install react-force-graph-2d
npm run dev   # http://localhost:3000
```

This gives TypeScript, Tailwind CSS, ESLint, App Router, Turbopack, the `@/*` import alias, no `src/` directory and an `AGENTS.md` that points at the version-matched docs in `node_modules/next/dist/docs/`. Read those docs before guessing an API. Check `next.config.ts`: if it contains `cacheComponents: true`, the project was scaffolded without the flag and the Cache Components rules in Gotchas apply.

Environment variable names:

- `NEXT_PUBLIC_API_URL`: base URL of the Python API (the `*.modal.run` URL from the `dxp-modal` skill), no trailing slash. Put it in `web/.env.local` for development and in Vercel for Production and Preview.
- `DXP_API_TOKEN`: example name for a server-only secret, needed only if the API checks a token. No `NEXT_PUBLIC_` prefix, so it never reaches the browser.
- On the Python side, `FRONTEND_ORIGIN`: the production origin, used for CORS.

Vercel, one time (Hobby is enough; the person who owns the Vercel account does this). Import the GitHub repository in the Vercel dashboard and set the project's Root Directory to `web`. Then, at the repository root, because the Root Directory setting also applies to the CLI:

```bash
npm i -g vercel@latest
vercel login
vercel link     # choose the project you just imported; writes .vercel/
vercel env add NEXT_PUBLIC_API_URL --environment production,preview --value "https://YOUR-API-URL" --no-sensitive --yes
vercel          # preview deployment; prints the URL
vercel --prod   # production deployment
```

A push to `main` creates a production deployment and a push to any other branch creates a preview. The first deployment of a new project is always production, even without `--prod`, and it builds with the Production variables. Changing a variable affects new deployments only, and `NEXT_PUBLIC_` values are inlined at build time, so redeploy after every change. On Hobby the repository must belong to a personal GitHub account: Vercel will not connect a Hobby project to a repository owned by a GitHub organisation.

| | Preview | Production |
|---|---|---|
| Created by | `vercel`, or a push to a non-production branch | `vercel --prod`, or a push to `main` |
| URL | unique per deployment and per branch | the project's production domain |
| Variables | Preview | Production |
| Access | Vercel login required by default | public |
| CORS origin seen by the API | changes with every deployment | fixed |

## Core patterns

### Why the agents do not run here

Vercel hosts the pages. Python on Modal does the scanning, extraction, batch and scheduling (FR-1, FR-4), because a Vercel Function is one HTTP request with a ceiling: 300 s on Hobby, and the time spent streaming a response counts. Nothing on Vercel runs with no request open. The browser and the Next.js server both call the Modal API over HTTPS:

```
browser ──HTML──> Vercel (Next.js pages)
browser ──fetch / EventSource, CORS──> Modal (FastAPI: records, proposals, graph, events) ──> MongoDB Atlas
Next.js server ──fetch, no CORS──> Modal
```

Do not connect to MongoDB from Next.js. One API keeps the Evidence rules (FR-7) in one place.

### Typed fetch to the API

```ts
// lib/api.ts - one typed fetch helper, usable in Server Components, Route Handlers and Client Components.

// NEXT_PUBLIC_ values are inlined at build time. Always write the full name; process.env[name] is not inlined.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: string,
  ) {
    super(`API ${status}: ${body.slice(0, 200)}`);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const res = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return (await res.json()) as T;
}
```

`cache: "no-store"` matters. Without it, a `fetch` in a page that uses no request-time API runs once during `next build` and the page ships that data for ever. Use `api()` for every backend read and never a bare `fetch`.

```tsx
// app/records/[id]/page.tsx
import { Suspense } from "react";
import { api } from "@/lib/api";

type RecordSummary = { id: string; name: string; lifecycle_stage: string | null };

async function RecordBody({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params; // a Promise since Next.js 15; synchronous access was removed in 16
  const record = await api<RecordSummary>(`/records/${encodeURIComponent(id)}`);
  return (
    <>
      <h1 className="text-2xl font-semibold">{record.name}</h1>
      <p>{record.lifecycle_stage ?? "stage not determined"}</p>
    </>
  );
}

export default function RecordPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <main className="p-6">
      <Suspense fallback={<p>Loading Record…</p>}>
        <RecordBody params={params} />
      </Suspense>
    </main>
  );
}
```

The async child inside `<Suspense>` is correct with Cache Components on or off. A Route Handler that forwards a review decision with a server-only token is in [references/data-and-table.md](references/data-and-table.md).

### CORS lives on the Python API

Server Components and Route Handlers call Modal from Vercel's servers, so CORS does not apply to them. It applies to every `fetch` and `EventSource` from a Client Component. Allow the origins in FastAPI:

```python
import os
from fastapi.middleware.cors import CORSMiddleware

web.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.environ["FRONTEND_ORIGIN"]],  # exact origins, no trailing slash
    allow_origin_regex=r"https://.*\.vercel\.app",  # preview deployments get a new origin each time
    allow_methods=["*"],
    allow_headers=["*"],
)
```

A JSON `POST` from the browser sends an `OPTIONS` preflight first; the middleware answers it. CORS headers set in Next.js (`next.config.ts` `headers` or `proxy.ts`) only affect Next.js Route Handlers called from another origin, which DxP does not need.

### Live updates (FR-27, FR-13, FR-4)

The API sends server-sent events and a Client Component reads them with `EventSource`, straight from the browser to Modal, so Vercel's limits are not in the path. The stream is a nudge: on every event and every reconnect the client refetches the JSON. Full code, the event contract, a same-origin proxy and a polling fallback are in [references/live-updates.md](references/live-updates.md).

```tsx
"use client";
const status = useDxpEvents(onEvent); // onEvent(event: DxpEvent); status is "connecting" | "open" | "reconnecting"
```

### Graph view (FR-26, FR-27)

Use `react-force-graph-2d`. It is one MIT package with the force layout built in, so clusters and the nodes that bridge them appear without layout code; it paints on canvas, so a changed node gets a pulsing ring and a changed link gets moving particles from built-in props. It must be loaded in the browser only: a Client Component wrapper that calls `dynamic(() => import("./GraphCanvas"), { ssr: false })`. The comparison with Sigma.js, Cytoscape.js and React Flow, the data shape and the complete components are in [references/graph-view.md](references/graph-view.md).

### Comparison table (FR-22, FR-8, FR-7)

A cell is one of three states, and the type makes a value without Evidence impossible to render:

```ts
export type Cell =
  | { state: "value"; value: string; evidence: Evidence; reviewed: boolean }
  | { state: "no_data" }   // renders "No data for this indication"
  | { state: "loading" };  // renders a pulsing "Loading…", visibly different from no data
```

The component is in [references/data-and-table.md](references/data-and-table.md).

## Limits and costs

Hobby plan, free, per month unless stated:

| Limit | Value | Why it matters |
|---|---|---|
| Function duration | 300 s default and maximum, streaming included | a proxied stream is cut at 300 s |
| Function memory | 2 GB, 1 vCPU | |
| Request or response body | 4.5 MB (streamed responses exempt) | do not send the whole corpus through a Route Handler |
| Deployments | 100 per day, 1 concurrent build | two people pushing queue behind each other |
| Build time | 45 minutes per deployment | |
| CLI source upload | 100 MB | keep data dumps out of the repository |
| Function invocations | 1,000,000 | |
| Active CPU / provisioned memory | 4 CPU-hours / 360 GB-hours | |
| Fast Data Transfer / CDN requests | 100 GB / 1,000,000 | |
| Image transformations | 5,000 | avoid `next/image` on remote Evidence images |
| Runtime logs | kept 1 hour | read errors straight after they happen |
| External rewrite | upstream must answer within 120 s | |

Exceeding an included amount on Hobby normally means waiting up to 30 days before the feature works again; there is no pay-as-you-go. A short demo with a few viewers uses a tiny fraction of these. The realistic risks are the single build queue, the 300 s cut on anything proxied, and the login wall on preview URLs.

## Gotchas

- `params` and `searchParams` are Promises: `const { id } = await params`. `cookies()`, `headers()` and `draftMode()` must be awaited. Synchronous access was removed in 16. Type a page as `{ params: Promise<{ id: string }> }` or with the generated `PageProps<'/records/[id]'>` helper.
- `middleware.ts` is deprecated. The file is `proxy.ts`, the export is `proxy`, and it runs on Node.js only. DxP does not need one.
- `next lint` is gone and `next build` no longer lints. Use `npm run lint` (ESLint). Type errors still fail `next build`, so run `npm run build` before deploying.
- Turbopack is the default for `next dev` and `next build`. A `webpack` key in `next.config.ts` makes the build fail.
- `GET` Route Handlers are not cached by default (since 15). `revalidateTag` needs a second argument, for example `revalidateTag("records", "max")`.
- If Cache Components is on: delete every `export const dynamic`, `revalidate`, `fetchCache` and `runtime`; put each uncached read in an async component under `<Suspense>`; `maxDuration` is still allowed.
- `dynamic(..., { ssr: false })` in a Server Component is an error. It is only allowed in a file that starts with `"use client"`.
- Hooks, `onClick`, `EventSource`, `window` and the graph need `"use client"` at the top of the file. Props passed from a Server Component to a Client Component must be serialisable, so no functions.
- `process.env.NEXT_PUBLIC_API_URL` must be written out in full. `process.env[name]` is not inlined and is `undefined` in the browser.
- In `next dev`, server-side fetches are held in the HMR cache, so after saving a file a page can show the previous API response. Reload the page.
- `EventSource` reconnects when the server ends the response. If the stream has a final message, call `.close()` when it arrives or the browser loops.
- The umbrella package `react-force-graph` also installs the 3D, VR and AR builds. Install `react-force-graph-2d`.
- `runtime = "edge"` is deprecated. Leave the default Node.js runtime everywhere.
- Preview URLs and `VERCEL_URL` are login-protected; a server-side fetch to your own preview URL gets a login page. Call the API directly.

## Fallback

1. Live stream misbehaves: replace `useDxpEvents` with `usePolling("/graph", 3000)` from [references/live-updates.md](references/live-updates.md). Same data, no long connection.
2. CORS blocks the browser: add a Route Handler that forwards the call (pattern in [references/data-and-table.md](references/data-and-table.md)) and point the Client Component at `/api/...`; server-to-server calls need no CORS.
3. Graph will not render: show the same `GraphPayload` as a list grouped by Category with each Diagnostic's linked trial, drug and Provider as links. It still passes the FR-26 one-step test, and the changed badge passes FR-27.
4. Vercel build or deploy fails near the deadline: run `npm run build && npm run start` locally and record the video against `http://localhost:3000` (allowed by the CORS list above). Say in the description that the hosted URL is behind.
5. Git deploys are blocked or queued: the Vercel account owner runs `vercel --prod` at the repository root.

## Links

- Next.js 16 upgrade guide (every breaking change): https://nextjs.org/docs/app/guides/upgrading/version-16
- Installation and `create-next-app` flags: https://nextjs.org/docs/app/getting-started/installation , https://nextjs.org/docs/app/api-reference/cli/create-next-app
- Fetching data and caching: https://nextjs.org/docs/app/getting-started/fetching-data , https://nextjs.org/docs/app/api-reference/functions/fetch , https://nextjs.org/docs/app/guides/caching-without-cache-components
- Route Handlers and streaming: https://nextjs.org/docs/app/api-reference/file-conventions/route , https://nextjs.org/docs/app/guides/streaming
- `next/dynamic` and `ssr: false`: https://nextjs.org/docs/app/guides/lazy-loading
- Vercel function limits and duration: https://vercel.com/docs/functions/limitations , https://vercel.com/docs/functions/configuring-functions/duration
- Vercel limits and Hobby plan: https://vercel.com/docs/limits , https://vercel.com/docs/plans/hobby
- Vercel CLI: https://vercel.com/docs/cli/deploy , https://vercel.com/docs/cli/env
- Git deploys, environments, protection: https://vercel.com/docs/git , https://vercel.com/docs/deployments/environments , https://vercel.com/docs/deployment-protection
- react-force-graph: https://github.com/vasturiano/react-force-graph
- Server-sent events: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
- FastAPI CORS: https://fastapi.tiangolo.com/tutorial/cors/
