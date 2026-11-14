# DxP web app

Next.js 16 (App Router, TypeScript, Tailwind 4) with shadcn/ui. The app talks only to the DxP API (AD-9).

```
npm install
cp .env.example .env.local   # fill in the values; .env.local is never committed
npm run dev
```

| Variable | Where | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | server and client | API origin, without `/api/v1` |
| `NEXT_PUBLIC_DXP_FEATURES` | client | display flags: `briefing`, `avatar`, `memory_edit`, `task_run`, `revert`, `live_stream` (comma separated; empty means off) |
| `DXP_API_KEY` | server only | reviewer key; added as `X-DxP-Key` by `app/api/dxp/[...path]/route.ts`; never `NEXT_PUBLIC_` |

Scripts: `npm run build`, `npm run lint`, `npm run typecheck`, `npm run gen:types` (writes `lib/types.ts` from the API's OpenAPI document, `OPENAPI_URL` defaults to `http://localhost:8000/openapi.json`).

Calling the API: client code uses `get` and `post` from `lib/api.ts` (through the proxy route) or `useApi` from `lib/use-api.ts` for polling. Server components use `serverGet` and `serverPost` from `lib/server-api.ts`.
