"use client";

// B04 builder 2: the memories panel. Keeps the stub's export and props: MemoryPanel({ reportId }).
import { Brain } from "lucide-react";

import { ApiError } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

import { MemoryCard } from "./memory-card";

/**
 * The memories panel in the report page's right-hand column: every memory
 * retrieved for this report, plus the one this report's decision created, each
 * with author, source, tags and status. Correct and Revoke sit behind the
 * `memory_edit` flag. Memories inform the agent's wording and never change
 * permissions.
 */
export function MemoryPanel({ reportId }: { reportId: string }) {
  const { data: report, error, isLoading } = useApi("/reports/{report_id}", { path: { report_id: reportId } });

  // Retrieved memories first, then the one this report's decision created (if it is not already listed).
  const used = report?.memories_used ?? [];
  const seen = new Set<string>();
  const entries: { id: string; use?: (typeof used)[number]; createdHere?: boolean }[] = [];
  for (const use of used) {
    if (seen.has(use.memory_id)) continue;
    seen.add(use.memory_id);
    entries.push({ id: use.memory_id, use });
  }
  if (report?.memory_id && !seen.has(report.memory_id)) {
    entries.push({ id: report.memory_id, createdHere: true });
  }

  return (
    <aside aria-labelledby="memory-panel-title" className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 id="memory-panel-title" className="flex items-center gap-2 text-heading">
          <Brain className="size-[18px]" strokeWidth={1.75} aria-hidden="true" />
          Memories
        </h2>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="rounded-full border border-border px-2 py-0.5 text-caption text-muted-foreground focus-visible:ring-3 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
            >
              Memory in Atlas
            </button>
          </TooltipTrigger>
          <TooltipContent>
            Reviewer corrections are documents in Atlas, scoped to the Team, versioned, and retrieved by similarity
            to the discovery.
          </TooltipContent>
        </Tooltip>
      </div>
      <p className="mt-1 text-caption text-muted-foreground">
        Retrieved for the same kind of claim; the assay need not match.
      </p>

      <div className="mt-3">
        {isLoading && !report ? (
          <div className="flex flex-col gap-2" role="status" aria-label="Loading memories">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : !report ? (
          error instanceof ApiError && error.status === 404 ? (
            <p className="text-body text-muted-foreground">No report, so no memories.</p>
          ) : (
            <p className="text-body text-muted-foreground" role="alert">
              The memories could not be read because the report could not be read. Reload this page once the API is
              back.
            </p>
          )
        ) : entries.length === 0 ? (
          <p className="text-body text-muted-foreground">
            No memories were used for this report. A Reject, or an approval with a correction, saves one.
          </p>
        ) : (
          <ul className="flex flex-col gap-3" aria-label="Memories for this report">
            {entries.map((entry) => (
              <MemoryCard
                key={entry.id}
                memoryId={entry.id}
                reportId={reportId}
                use={entry.use}
                createdHere={entry.createdHere}
              />
            ))}
          </ul>
        )}
      </div>

      <p className="mt-4 border-t border-border pt-3 text-caption text-muted-foreground">
        Memories inform the agent&apos;s wording. They never change permissions.
      </p>
    </aside>
  );
}
