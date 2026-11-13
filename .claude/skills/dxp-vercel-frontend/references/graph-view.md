# Graph view (FR-26, FR-27)

Checked 12 November 2026. The TypeScript below type-checks (tsc 5.9, strict) against `react-force-graph-2d` 1.29.2, `@types/react` 19.3.0 and the `next/dynamic` types of Next.js 16.4.6. It was not run in a browser.

## Library choice

| Library | npm `latest` | Licence | React 19 | Weekly downloads | For DxP |
|---|---|---|---|---|---|
| `react-force-graph-2d` (canvas) | 1.29.2, 29 Sep 2026 | MIT | peer `react: *`; ships types | 1.28 M | **Chosen.** Force layout built in, custom canvas painting, click and hover callbacks, animated particles on links |
| `react-force-graph-3d` (three.js, WebGL) | 1.29.2, 29 Sep 2026 | MIT | peer `react: *` | 0.36 M | Same props. Looks striking, but labels are harder to read and it is heavier. Swap the import later if there is time; `nodeCanvasObject` becomes `nodeThreeObject` |
| `sigma` with `graphology` and `@react-sigma/core` | sigma 4.0.6 (4.0.0 released 8 Oct 2026), graphology 0.26.0, @react-sigma/core 6.0.0 | MIT | wrapper peers `react ^18 \|\| ^19`, `sigma ^4` | 0.73 M | WebGL, built for very large graphs. Layout is a separate step. Version 4 is five weeks old, so most examples and most model knowledge are for older majors |
| `cytoscape` with `react-cytoscapejs` | cytoscape 3.35.0, 10 Nov 2026; react-cytoscapejs 2.0.0, Sep 2022 | MIT | core has no React dependency; the wrapper has had no release since 2022 and ships no types | 25.9 M / 88 K | Strong layouts and a stylesheet model, but you would mount it by hand in an effect and spend longer making it look good |
| `@xyflow/react` (React Flow 12) | 12.12.1, 2 Nov 2026 | MIT | peer `react >=17` | 20.9 M | Nodes are React components, which suits flow diagrams. No layout engine: its docs send you to dagre, d3-hierarchy, d3-force or elkjs. The older `reactflow` package (11.11.4, 2024) is the legacy name |

Why `react-force-graph-2d`: the team wants connections between clusters visible, and a force layout produces exactly that with no layout code: Diagnostics in one Category pull together around their shared biomarkers, and a drug, trial or Provider linked to two Categories sits between them. Highlighting is a few props. One `npm install`, MIT, and the official examples cover highlight, click to focus and dynamic data. It handles hundreds to a few thousand nodes on canvas, which covers a 300 to 500 item batch.

Install only the 2D package. The umbrella `react-force-graph` also depends on the 3D, VR and AR builds.

## Data shape

The API returns one `GraphPayload` from `GET /graph`. Node ids must be unique across kinds. The API decides `changed` from the Team's last visit (FR-27, FR-28); live changes arrive as events and are added on top. Types are in `lib/types.ts` ([data-and-table.md](data-and-table.md)):

```ts
export type NodeKind = "diagnostic" | "biomarker" | "tumour_type" | "trial" | "drug" | "provider";
export type GraphNode = {
  id: string; kind: NodeKind; label: string;
  category?: string; lifecycle_stage?: string; early_research?: boolean;
  changed?: boolean; href?: string; x?: number; y?: number;
};
export type GraphLink = { source: string; target: string; relation: string; changed?: boolean };
export type GraphPayload = { nodes: GraphNode[]; links: GraphLink[] };
```

Example payload: one Diagnostic linked to its biomarker, trial, drug and Provider, each one step away (the FR-26 test).

```json
{
  "nodes": [
    { "id": "diagnostic:d1", "kind": "diagnostic", "label": "Example ctDNA assay", "category": "ctDNA", "lifecycle_stage": "clinical validation", "changed": true, "href": "/records/d1" },
    { "id": "biomarker:EGFR", "kind": "biomarker", "label": "EGFR" },
    { "id": "tumour_type:NSCLC", "kind": "tumour_type", "label": "NSCLC" },
    { "id": "trial:NCT00000000", "kind": "trial", "label": "NCT00000000", "href": "https://clinicaltrials.gov/study/NCT00000000" },
    { "id": "drug:osimertinib", "kind": "drug", "label": "osimertinib" },
    { "id": "provider:p1", "kind": "provider", "label": "Example Labs" }
  ],
  "links": [
    { "source": "diagnostic:d1", "target": "biomarker:EGFR", "relation": "detects" },
    { "source": "diagnostic:d1", "target": "tumour_type:NSCLC", "relation": "indicated_for" },
    { "source": "diagnostic:d1", "target": "trial:NCT00000000", "relation": "used_in_trial", "changed": true },
    { "source": "diagnostic:d1", "target": "drug:osimertinib", "relation": "companion_to" },
    { "source": "diagnostic:d1", "target": "provider:p1", "relation": "offered_by" }
  ]
}
```

## How it is drawn

- **Cluster colour.** A Diagnostic takes the colour of its Category. Other kinds have one fixed colour each. A link takes the Category colour of its Diagnostic end, so a shared node with spokes in two colours is a visible connection between clusters.
- **Bridges.** A biomarker, trial, drug, tumour type or Provider linked to Diagnostics in two or more Categories is drawn larger with a dark outline.
- **Changed.** A changed node gets a pulsing amber ring; a changed link turns amber, thickens and carries moving particles.
- **Lifecycle stage and Early research** (FR-27, FR-2) are written under each Diagnostic.
- **Click** calls `onSelect`, and the side panel links to the Record or the Evidence.

## `components/graph/GraphCanvas.tsx`

Imports the library, so it must only ever load in the browser.

```tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import type { ForceGraphMethods, LinkObject, NodeObject } from "react-force-graph-2d";
import type { GraphLink, GraphNode, GraphPayload, NodeKind } from "@/lib/types";

type FGNode = NodeObject<GraphNode>;
type FGLink = LinkObject<GraphNode, GraphLink>;

const KIND_COLOUR: Record<NodeKind, string> = {
  diagnostic: "#2563eb", // replaced by the Category colour when the node has one
  biomarker: "#16a34a",
  tumour_type: "#dc2626",
  trial: "#9333ea",
  drug: "#ea580c",
  provider: "#64748b",
};
const CATEGORY_PALETTE = ["#2563eb", "#0891b2", "#7c3aed", "#db2777", "#ca8a04", "#059669", "#4f46e5", "#be123c"];
const CHANGED = "#f59e0b";
const NODE_R = 5;

// force-graph replaces link.source and link.target (ids) with the node objects once the layout starts.
const endId = (end: unknown): string =>
  typeof end === "object" && end !== null ? String((end as { id?: unknown }).id) : String(end);

// Tooltips are rendered as HTML and labels come from scraped sources, so escape them.
const escapeHtml = (text: string): string =>
  text.replace(/[&<>"']/g, (ch) => `&#${ch.charCodeAt(0)};`);

export const linkKey = (link: { source?: unknown; target?: unknown }): string =>
  `${endId(link.source)}->${endId(link.target)}`;

export default function GraphCanvas({
  data,
  changedNodes,
  changedLinks,
  onSelect,
}: {
  data: GraphPayload;
  changedNodes: Set<string>; // GraphNode.id values that changed live
  changedLinks: Set<string>; // linkKey values that changed live
  onSelect: (node: GraphNode) => void;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<ForceGraphMethods<FGNode, FGLink> | undefined>(undefined);
  const fitted = useRef(false);
  const [size, setSize] = useState({ width: 800, height: 600 });

  // The canvas defaults to the window size, so measure the container.
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) =>
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height }),
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Cluster colours, and which shared nodes bridge two or more Categories.
  const { categoryColour, bridges, categoryOfLink } = useMemo(() => {
    const categories = [...new Set(data.nodes.flatMap((n) => (n.category ? [n.category] : [])))].sort();
    const categoryColour = new Map(categories.map((c, i) => [c, CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]]));
    const byId = new Map(data.nodes.map((n) => [n.id, n]));
    const reach = new Map<string, Set<string>>(); // shared node id -> Categories of the Diagnostics it touches
    const categoryOfLink = new Map<string, string>(); // linkKey -> Category of its Diagnostic end
    for (const link of data.links) {
      const a = byId.get(endId(link.source));
      const b = byId.get(endId(link.target));
      if (!a || !b) continue;
      for (const [diagnostic, other] of [
        [a, b],
        [b, a],
      ]) {
        if (diagnostic.kind !== "diagnostic" || !diagnostic.category) continue;
        categoryOfLink.set(linkKey(link), diagnostic.category);
        if (other.kind === "diagnostic") continue;
        const seen = reach.get(other.id) ?? new Set<string>();
        seen.add(diagnostic.category);
        reach.set(other.id, seen);
      }
    }
    const bridges = new Set([...reach].filter(([, seen]) => seen.size > 1).map(([id]) => id));
    return { categoryColour, bridges, categoryOfLink };
  }, [data]);

  const isChangedNode = (n: FGNode) => Boolean(n.changed) || changedNodes.has(n.id);
  const isChangedLink = (l: FGLink) => Boolean(l.changed) || changedLinks.has(linkKey(l));
  const sizeOf = (n: FGNode) => (n.kind === "diagnostic" ? 4 : bridges.has(n.id) ? 3 : 1.5);
  const colourOf = (n: FGNode) =>
    (n.kind === "diagnostic" && n.category ? categoryColour.get(n.category) : undefined) ?? KIND_COLOUR[n.kind];

  // Painted after the default circle: a pulsing ring on changed nodes, an outline on bridges, and the label.
  const paint = (n: FGNode, ctx: CanvasRenderingContext2D, scale: number) => {
    const x = n.x ?? 0;
    const y = n.y ?? 0;
    const r = Math.sqrt(sizeOf(n)) * NODE_R;
    if (bridges.has(n.id)) {
      ctx.beginPath();
      ctx.arc(x, y, r + 1.5 / scale, 0, 2 * Math.PI);
      ctx.strokeStyle = "#0f172a";
      ctx.lineWidth = 1.5 / scale;
      ctx.stroke();
    }
    if (isChangedNode(n)) {
      const pulse = 1.5 + 0.3 * Math.sin(Date.now() / 250);
      ctx.beginPath();
      ctx.arc(x, y, r * pulse, 0, 2 * Math.PI);
      ctx.strokeStyle = CHANGED;
      ctx.lineWidth = 2.5 / scale;
      ctx.stroke();
    }
    if (n.kind === "diagnostic" || scale > 1.4) {
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.font = `${11 / scale}px sans-serif`;
      ctx.fillStyle = "#0f172a";
      ctx.fillText(n.label, x, y + r + 2 / scale);
      if (n.kind === "diagnostic") {
        const stage = n.lifecycle_stage ?? "stage not determined";
        ctx.font = `${9 / scale}px sans-serif`;
        ctx.fillStyle = n.early_research ? "#b45309" : "#64748b";
        ctx.fillText(n.early_research ? `Early research · ${stage}` : stage, x, y + r + 15 / scale);
      }
    }
  };

  return (
    <div ref={wrapRef} className="h-[70vh] w-full overflow-hidden rounded-lg border">
      <ForceGraph2D<GraphNode, GraphLink>
        ref={graphRef}
        graphData={data}
        width={size.width}
        height={size.height}
        nodeRelSize={NODE_R}
        nodeVal={sizeOf}
        nodeColor={colourOf}
        nodeLabel={(n) => escapeHtml(`${n.kind.replace("_", " ")}: ${n.label}`)}
        nodeCanvasObjectMode={() => "after"}
        nodeCanvasObject={paint}
        linkLabel="relation"
        linkColor={(l) =>
          isChangedLink(l) ? CHANGED : `${categoryColour.get(categoryOfLink.get(linkKey(l)) ?? "") ?? "#94a3b8"}99`
        }
        linkWidth={(l) => (isChangedLink(l) ? 2.5 : 1)}
        linkDirectionalParticles={(l) => (isChangedLink(l) ? 4 : 0)}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleColor={() => CHANGED}
        autoPauseRedraw={false} // keep drawing after the layout settles so the ring keeps pulsing
        cooldownTicks={150}
        onEngineStop={() => {
          if (fitted.current) return;
          fitted.current = true;
          graphRef.current?.zoomToFit(400, 60);
        }}
        onNodeClick={(n) => onSelect(n)}
      />
    </div>
  );
}
```

## `components/graph/GraphView.tsx`

The client-only import, live updates and the side panel.

```tsx
"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DxpEvent, GraphNode, GraphPayload } from "@/lib/types";
import { useDxpEvents } from "@/lib/useDxpEvents";

// The graph library needs window and canvas, so it must never render on the server.
// `ssr: false` is only allowed inside a Client Component, which is why this wrapper exists.
const GraphCanvas = dynamic(() => import("./GraphCanvas"), {
  ssr: false,
  loading: () => <p className="p-4 text-sm text-zinc-500">Loading graph…</p>,
});

// force-graph mutates the objects it is given (x, y, and link ends become node objects),
// so hand it copies, and carry positions over so the layout does not jump on every update.
function forCanvas(next: GraphPayload, previous?: GraphPayload): GraphPayload {
  const old = new Map(previous?.nodes.map((n) => [n.id, n]));
  return {
    nodes: next.nodes.map((n) => ({ ...n, x: old.get(n.id)?.x, y: old.get(n.id)?.y })),
    links: next.links.map((l) => ({ ...l })),
  };
}

export default function GraphView({ initial }: { initial: GraphPayload }) {
  const [data, setData] = useState(() => forCanvas(initial));
  const [liveNodes, setLiveNodes] = useState<Set<string>>(new Set());
  const [liveLinks, setLiveLinks] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [banner, setBanner] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const next = await api<GraphPayload>("/graph");
      setData((previous) => forCanvas(next, previous));
    } catch {
      // keep the current graph on screen
    }
  }, []);

  const onEvent = useCallback(
    (event: DxpEvent) => {
      setBanner(event.summary);
      setLiveNodes((current) => new Set([...current, ...event.node_ids]));
      setLiveLinks((current) => new Set([...current, ...event.link_keys]));
      void refresh();
    },
    [refresh],
  );
  const status = useDxpEvents(onEvent);

  // The stream is only a nudge. Refetch on every (re)connect so nothing sent during a gap is missed.
  useEffect(() => {
    if (status === "open") void refresh();
  }, [status, refresh]);

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <div>
        <p className="mb-2 text-xs text-zinc-500" aria-live="polite">
          {status === "open" ? "Live" : "Connecting…"}
          {banner ? ` · ${banner}` : ""}
        </p>
        <GraphCanvas data={data} changedNodes={liveNodes} changedLinks={liveLinks} onSelect={setSelected} />
      </div>
      <aside className="rounded-lg border p-4 text-sm">
        {selected ? (
          <>
            <p className="text-xs uppercase text-zinc-500">{selected.kind.replace("_", " ")}</p>
            <h2 className="text-lg font-semibold">{selected.label}</h2>
            {selected.kind === "diagnostic" && (
              <p className="mt-1">
                {selected.early_research ? "Early research · " : ""}
                {selected.lifecycle_stage ?? "stage not determined"}
              </p>
            )}
            {selected.href?.startsWith("/") && (
              <Link href={selected.href} className="mt-3 inline-block underline">
                Open Record
              </Link>
            )}
            {selected.href && !selected.href.startsWith("/") && (
              <a href={selected.href} target="_blank" rel="noreferrer" className="mt-3 inline-block underline">
                Open Evidence
              </a>
            )}
          </>
        ) : (
          <p className="text-zinc-500">Select a node to open its Record or Evidence.</p>
        )}
      </aside>
    </div>
  );
}
```

## `app/graph/page.tsx`

A Server Component fetches the first payload, so the graph has data as soon as the library loads.

```tsx
import { Suspense } from "react";
import GraphView from "@/components/graph/GraphView";
import { api } from "@/lib/api";
import type { GraphPayload } from "@/lib/types";

async function Graph() {
  const initial = await api<GraphPayload>("/graph");
  return <GraphView initial={initial} />;
}

export default function GraphPage() {
  return (
    <main className="p-6">
      <h1 className="mb-4 text-2xl font-semibold">Graph view</h1>
      <Suspense fallback={<p className="text-sm text-zinc-500">Loading graph…</p>}>
        <Graph />
      </Suspense>
    </main>
  );
}
```

## Notes

- **Why two client files.** `force-graph` touches `document` and `window` when the module is evaluated, so importing it during server rendering fails. `next/dynamic` with `ssr: false` prevents that, and Next.js only allows `ssr: false` inside a Client Component. Wrapping your own component, not the library, keeps the `ref` and the types simple.
- **The library mutates its input.** It writes `x`, `y`, `vx`, `vy` onto nodes and replaces `link.source` and `link.target` with node objects. That is why `GraphView` copies the payload, why `forCanvas` carries `x` and `y` across refreshes, and why link ends go through `endId()`.
- **`graphData` identity.** A new object restarts the layout. Call `setData` only when the payload changed, never on every render.
- **Size.** The canvas defaults to the window size. The `ResizeObserver` keeps it inside its container; the container needs a height (`h-[70vh]`).
- **Tooltips are HTML.** `nodeLabel` and `linkLabel` accept HTML, and labels come from scraped sources, so `escapeHtml` is not optional.
- **`autoPauseRedraw={false}`** keeps the canvas drawing after the layout settles. Without it the ring stops pulsing.
- **Tuning.** `graphRef.current.d3Force("charge")` returns the repulsion force and `d3Force("link")` the link force. Calling `.strength(-150)` or `.distance(60)` on them is the d3-force API and is UNVERIFIED here. `cooldownTicks` controls how long the layout runs.
- **Clearing highlights.** `changed` from the API clears on the next visit. To clear live highlights, reset `liveNodes` and `liveLinks` to empty sets.
- **Keep it readable.** Send the Monitored set and its neighbours, not every Finding. A few hundred nodes read well; labels for non-Diagnostics appear only when zoomed in.

Sources: https://github.com/vasturiano/react-force-graph (README, `example/highlight`), https://unpkg.com/react-force-graph-2d@1.29.2/dist/react-force-graph-2d.d.ts , https://nextjs.org/docs/app/guides/lazy-loading , https://www.sigmajs.org/ , https://reactflow.dev/learn/layouting/layouting , npm registry metadata for each package.
