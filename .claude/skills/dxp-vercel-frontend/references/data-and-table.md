> Reference only. Do not copy this code into the project; it was written before the event.

# Shared types, the comparison table and a forwarding Route Handler

Checked 12 November 2026. Type-checked (tsc 5.9, strict) against `@types/react` 19.3.0; not run in a browser.

## `lib/types.ts`

The contract between the Python API and the front end. Agree it with whoever writes the API before building either side; the field names are a proposal, not something fixed by the PRD.

```ts
// lib/types.ts - the wire contract between the Python API and the front end.

export type Evidence = { source_url: string; source_title: string; quote: string };

// FR-7, FR-8: a cell is a value WITH evidence, an explicit no-data state, or still loading. Nothing else renders.
export type Cell =
  | { state: "value"; value: string; evidence: Evidence; reviewed: boolean }
  | { state: "no_data" }
  | { state: "loading" };

export type ComparisonRow = {
  diagnostic_id: string;
  name: string;
  early_research: boolean; // FR-2
  cells: Record<string, Cell>; // keyed by criterion id
};

export type Comparison = { criteria: { id: string; label: string }[]; rows: ComparisonRow[] };

export type NodeKind = "diagnostic" | "biomarker" | "tumour_type" | "trial" | "drug" | "provider";

export type GraphNode = {
  id: string; // unique across kinds, for example "diagnostic:6730f2..." or "trial:NCT01234567"
  kind: NodeKind;
  label: string;
  category?: string; // diagnostics only: the cluster (Category) it belongs to
  lifecycle_stage?: string; // diagnostics only (FR-27); absent means "stage not determined"
  early_research?: boolean; // FR-2
  changed?: boolean; // new or changed since this Team's last visit (FR-27), decided by the API
  href?: string; // "/records/<id>" for a Record, or an absolute Evidence URL
  x?: number; // set by the layout in the browser; the API never sends these
  y?: number;
};

export type GraphLink = {
  source: string; // GraphNode.id
  target: string; // GraphNode.id
  relation: string; // for example "detects", "used_in_trial", "companion_to", "offered_by", "indicated_for"
  changed?: boolean;
};

export type GraphPayload = { nodes: GraphNode[]; links: GraphLink[] };

// One server-sent event: `data: <this as JSON>\n\n`
export type DxpEvent = {
  type: "change" | "alert";
  summary: string; // one line for the banner
  node_ids: string[]; // GraphNode.id values to highlight
  link_keys: string[]; // "<source id>-><target id>"
  at: string; // ISO timestamp
};
```

## `components/ComparisonTable.tsx` (FR-22, FR-7, FR-8, FR-2, FR-16)

One row per Diagnostic, one column per criterion, the quote and its source inside the cell. It has no hooks, so it works as a Server Component or inside a Client Component.

```tsx
import type { Cell, Comparison } from "@/lib/types";

function CellView({ cell }: { cell: Cell | undefined }) {
  if (!cell || cell.state === "loading") {
    return <span className="animate-pulse text-zinc-400" aria-busy="true">Loading…</span>;
  }
  if (cell.state === "no_data") {
    return <span className="italic text-zinc-500" data-state="no-data">No data for this indication</span>;
  }
  return (
    <div>
      <p className="font-medium">
        {cell.value}
        {!cell.reviewed && <span className="ml-2 rounded bg-amber-100 px-1 text-xs text-amber-800">unreviewed</span>}
      </p>
      <blockquote className="mt-1 border-l-2 pl-2 text-xs text-zinc-600">
        “{cell.evidence.quote}”{" "}
        <a href={cell.evidence.source_url} target="_blank" rel="noreferrer" className="underline">
          {cell.evidence.source_title}
        </a>
      </blockquote>
    </div>
  );
}

export function ComparisonTable({ data }: { data: Comparison }) {
  return (
    <table className="w-full border-collapse text-left text-sm">
      <thead>
        <tr>
          <th className="border-b p-2">Diagnostic</th>
          {data.criteria.map((c) => (
            <th key={c.id} className="border-b p-2">{c.label}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.rows.map((row) => (
          <tr key={row.diagnostic_id} className="align-top">
            <th scope="row" className="border-b p-2 font-semibold">
              {row.name}
              {row.early_research && <span className="ml-2 text-xs font-normal text-amber-700">Early research</span>}
            </th>
            {data.criteria.map((c) => (
              <td key={c.id} className="border-b p-2"><CellView cell={row.cells[c.id]} /></td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

Rules it enforces:

- **FR-7.** The `"value"` state requires `evidence`. If the API has a value with no Evidence, it must send `no_data`, never a bare value. Do not add a fourth state that shows a value alone.
- **FR-8.** `no_data` renders the words "No data for this indication" in italics with `data-state="no-data"`; `loading` (or a cell not yet received) renders a pulsing "Loading…" with `aria-busy`. The two are distinguishable by text, style and attribute, which is the FR-8 test.
- **FR-22.** Nothing is behind a click or a hover: the quote is in the cell.
- **FR-16, FR-2.** Unreviewed values and Early research Diagnostics are marked where they appear.

Usage in a page:

```tsx
const data = await api<Comparison>(`/comparison?q=${encodeURIComponent(query)}`);
return <ComparisonTable data={data} />;
```

## A Route Handler that forwards a call (typed, server-only secret)

Use this when the browser must not call the API directly: the call needs a secret, or CORS is in the way. `params` is a Promise in Next.js 16. `maxDuration` is in seconds and cannot exceed the plan limit (300 on Hobby).

```ts
// app/api/proposals/[id]/review/route.ts
import { api, ApiError } from "@/lib/api";

type ReviewBody = { decision: "accept" | "edit" | "reject"; value?: string; reason?: string };
type ReviewResult = { proposal_id: string; status: string };

export const maxDuration = 60; // seconds; this call only forwards a decision

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const body = (await request.json()) as ReviewBody;
  try {
    const result = await api<ReviewResult>(`/proposals/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: JSON.stringify(body),
      headers: { Authorization: `Bearer ${process.env.DXP_API_TOKEN ?? ""}` }, // server-only variable
    });
    return Response.json(result);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 502;
    return Response.json({ error: String(error) }, { status });
  }
}
```

From a Client Component:

```ts
await fetch(`/api/proposals/${id}/review`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ decision: "reject", reason: "Quote is about a different assay" }),
});
```

When the API needs no secret, skip the Route Handler and call `api("/proposals/" + id + "/review", { method: "POST", body: JSON.stringify(...) })` from the Client Component.

Sources: https://nextjs.org/docs/app/api-reference/file-conventions/route , https://nextjs.org/docs/app/getting-started/fetching-data , https://vercel.com/docs/functions/configuring-functions/duration
