"use client";

import { ListOrdered, Star } from "lucide-react";

import { sourceLabel } from "@/components/run-console/names";
import type { Run } from "@/components/run-console/types";
import type { components } from "@/lib/types";

type Scope = components["schemas"]["Scope"];

/** How many trials are listed before the rest fold into "Show all". */
const SHOWN = 10;

function queryValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && value.every((v) => typeof v === "string" || typeof v === "number")) return value.join(", ");
  return JSON.stringify(value);
}

/** `scan.query` is a string, an object of search terms, or null. Each shows as plain text. */
export function queryLines(query: NonNullable<Run["scan"]>["query"]): { key: string | null; text: string }[] {
  if (query === null || query === undefined) return [];
  if (typeof query === "string") return query.trim() ? [{ key: null, text: query }] : [];
  return Object.entries(query).map(([key, value]) => ({
    key: key.replace(/_/g, " "),
    text: queryValue(value),
  }));
}

/**
 * Why the scan went in the order it did (V52, B02 follow-up): the query the scan sent, the
 * trials it took in the order it took them (`Run.scan.source_refs`, the order the scan
 * recorded), and the scope's `priority_refs`, the references the scan takes first. A trial
 * that is a priority reference is marked in words, so the console can say why NCT04712877
 * came first.
 */
export function ScanOrder({ run, scope }: { run: Run; scope: Scope | undefined }) {
  const scan = run.scan;
  if (!scan) return null;

  const refs = scan.source_refs;
  const priority = new Set((scope?.priority_refs ?? []).map(sourceLabel));
  const lines = queryLines(scan.query);
  const finished = run.status !== "running" && run.status !== "stopping";

  // Leading trials that are priority references: the ones the scan took first because the scope says so.
  let leading = 0;
  while (leading < refs.length && priority.has(sourceLabel(refs[leading]))) leading += 1;
  // Priority references the scan did not list (for example, not updated since the cursor).
  const unlisted = refs.length > 0 ? [...priority].filter((p) => !refs.some((r) => sourceLabel(r) === p)) : [];

  const shown = refs.slice(0, SHOWN);
  const rest = refs.slice(SHOWN);

  return (
    <section aria-labelledby="scan-heading" className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <h2 id="scan-heading" className="flex items-center gap-2 text-heading">
        <ListOrdered className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
        What this scan searched, and in what order
      </h2>

      <dl className="mt-4 flex flex-col gap-4">
        <div>
          <dt className="text-caption text-muted-foreground">Query</dt>
          <dd className="mt-0.5 min-w-0 text-body">
            {lines.length > 0 ? (
              <ul className="flex flex-col gap-0.5">
                {lines.map((line) => (
                  <li key={`${line.key}:${line.text}`} className="[overflow-wrap:anywhere]">
                    {line.key ? <span className="text-muted-foreground">{line.key}: </span> : null}
                    <span className="text-identifier">{line.text}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <span className="text-muted-foreground">Not recorded yet</span>
            )}
          </dd>
        </div>

        <div>
          <dt className="text-caption text-muted-foreground">Priority references in the scope</dt>
          <dd className="mt-0.5 min-w-0 text-body">
            {!run.scope_id ? (
              <span className="text-muted-foreground">This run has no scope.</span>
            ) : !scope ? (
              <span className="text-muted-foreground">Not loaded</span>
            ) : scope.priority_refs.length > 0 ? (
              <span className="flex flex-wrap gap-x-3 gap-y-1">
                {scope.priority_refs.map((ref) => (
                  <span key={ref} className="text-identifier">
                    {sourceLabel(ref)}
                  </span>
                ))}
              </span>
            ) : (
              <span className="text-muted-foreground">None. The scan took trials in the order the source gave them.</span>
            )}
          </dd>
        </div>

        <div>
          <dt className="text-caption text-muted-foreground">Trials, in the order the scan took them</dt>
          <dd className="mt-1 min-w-0 text-body">
            {refs.length === 0 ? (
              <span className="text-muted-foreground">
                {finished ? "The scan listed no trials." : "The scan has not listed its trials yet."}
              </span>
            ) : (
              <>
                {leading > 0 ? (
                  <p className="mb-2 text-table">
                    <span className="text-identifier">{sourceLabel(refs[0])}</span>
                    {leading > 1 ? ` and ${leading - 1} more` : ""} came first because the scope lists{" "}
                    {leading > 1 ? "them" : "it"} as {leading > 1 ? "priority references" : "a priority reference"}.
                  </p>
                ) : null}
                <ol className="flex flex-col gap-1" aria-label="Trials in scan order">
                  {shown.map((ref, i) => (
                    <TrialItem key={`${i}:${ref}`} index={i + 1} sourceRef={ref} isPriority={priority.has(sourceLabel(ref))} />
                  ))}
                </ol>
                {rest.length > 0 ? (
                  <details className="mt-1">
                    <summary className="w-fit cursor-pointer rounded-sm text-table font-semibold underline-offset-4 hover:underline">
                      Show all {refs.length} trials
                    </summary>
                    <ol start={SHOWN + 1} className="mt-1 flex flex-col gap-1" aria-label="The rest of the trials in scan order">
                      {rest.map((ref, i) => (
                        <TrialItem
                          key={`${SHOWN + i}:${ref}`}
                          index={SHOWN + i + 1}
                          sourceRef={ref}
                          isPriority={priority.has(sourceLabel(ref))}
                        />
                      ))}
                    </ol>
                  </details>
                ) : null}
                {unlisted.length > 0 ? (
                  <p className="mt-2 text-caption text-muted-foreground">
                    Priority {unlisted.length === 1 ? "reference" : "references"}{" "}
                    {unlisted.map((p, i) => (
                      <span key={p}>
                        {i > 0 ? ", " : ""}
                        <span className="text-identifier">{p}</span>
                      </span>
                    ))}{" "}
                    {unlisted.length === 1 ? "is" : "are"} not in this scan&apos;s list.
                  </p>
                ) : null}
              </>
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}

function TrialItem({ index, sourceRef, isPriority }: { index: number; sourceRef: string; isPriority: boolean }) {
  return (
    <li value={index} className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-table">
      <span className="w-6 text-right text-identifier tabular-nums text-muted-foreground" aria-hidden="true">
        {index}.
      </span>
      <code className="text-identifier break-all" title={sourceRef}>
        {sourceLabel(sourceRef)}
      </code>
      {isPriority ? (
        <span className="inline-flex items-center gap-1 text-caption font-semibold text-foreground">
          <Star className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Priority reference
        </span>
      ) : null}
    </li>
  );
}
