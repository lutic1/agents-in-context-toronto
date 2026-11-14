"use client";

import { Radar } from "lucide-react";

import { Mono, Panel, SourceRef } from "@/components/audit/common";
import { isActiveRun, type Audit } from "@/components/audit/labels";
import { formatDate } from "@/lib/format";

/**
 * Sources fetched, with the scan cursor before and after (V14). The cursor
 * and the query come from the run's `scan`; the sources from the audit.
 */
export function SourcesPanel({ audit }: { audit: Audit }) {
  const { run, sources } = audit;
  const scan = run.scan;
  const running = isActiveRun(run.status);
  const query = scan?.query ? (typeof scan.query === "string" ? scan.query : JSON.stringify(scan.query)) : null;

  return (
    <Panel icon={Radar} title="Sources fetched" headingId="sources-heading">
      {scan ? (
        <dl className="mb-4 grid grid-cols-1 gap-x-6 gap-y-1 text-table sm:grid-cols-[max-content_minmax(0,1fr)]">
          <dt className="text-caption text-muted-foreground">Cursor before</dt>
          <dd>{scan.cursor_from ? formatDate(scan.cursor_from) : "Not recorded"}</dd>
          <dt className="text-caption text-muted-foreground">Cursor after</dt>
          <dd>{scan.cursor_to ? formatDate(scan.cursor_to) : running ? "Not advanced yet" : "Not advanced"}</dd>
          {query ? (
            <>
              <dt className="text-caption text-muted-foreground">Query</dt>
              <dd className="min-w-0">
                <Mono>{query}</Mono>
              </dd>
            </>
          ) : null}
        </dl>
      ) : null}

      {sources.length === 0 ? (
        <p className="text-body text-muted-foreground">
          {running
            ? "No sources fetched yet. The agent is scanning ClinicalTrials.gov for the scope."
            : scan?.cursor_from
              ? `Scan finished. No trials in scope updated since ${formatDate(scan.cursor_from)}.`
              : "No sources were fetched in this run."}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {sources.map((s) => (
            <li key={s.source_ref} className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-table">
              <SourceRef source={s.source_ref} />
              {s.source_date ? <span className="text-muted-foreground">updated {formatDate(s.source_date)}</span> : null}
              {s.window ? <span className="text-muted-foreground">{s.window}</span> : null}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
