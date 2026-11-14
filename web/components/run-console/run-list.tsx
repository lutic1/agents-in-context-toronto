"use client";

import Link from "next/link";
import { CircleDashed, SquareTerminal } from "lucide-react";

import { RunStatusBadge } from "@/components/run-console/status-badge";
import type { Run } from "@/components/run-console/types";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, isUnreachable, itemsOf } from "@/lib/api";
import { features } from "@/lib/features";
import { formatDateTime } from "@/lib/format";
import { POLL_MS, useApi } from "@/lib/use-api";

/** What to call a run in a list. A task's run is the follow-up task (flag `task_run`, V66). */
export function runTitle(run: Run): string {
  if (run.kind === "task") return "Follow-up task";
  if (run.set === "discover") return "Discovery scan";
  if (run.set.startsWith("nct:")) return `Setup run for ${run.set.slice(4)}`;
  return "Run";
}

/** Newest first. A task's run is listed only with `task_run` on (V66). */
export function visibleRuns(runs: Run[]): Run[] {
  return runs
    .filter((run) => run.kind !== "task" || features.task_run)
    .sort((a, b) => (b.started_at ?? "").localeCompare(a.started_at ?? ""));
}

/** Every run, newest first, each opening in the Run console. Polls every 2 seconds. */
export function RunList() {
  const { data, error, isLoading } = useApi("/runs", { interval: POLL_MS });

  if (isLoading && !data) {
    return (
      <div className="flex flex-col gap-2" role="status" aria-label="Loading runs">
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (!data) {
    if (error && isUnreachable(error)) return <ApiUnreachableNotice />;
    if (error instanceof ApiError && error.status === 501) {
      return (
        <Notice icon={CircleDashed} title="The run list is not available yet" role="status">
          The API has not built the runs routes yet. Start a scan above once it has.
        </Notice>
      );
    }
    return (
      <Notice icon={CircleDashed} title="The run list could not be loaded" role="alert">
        {error?.message ?? "The API did not return a list of runs."}
      </Notice>
    );
  }

  const runs = visibleRuns(itemsOf(data));
  if (runs.length === 0) {
    return (
      <Notice icon={SquareTerminal} title="No runs yet" role="status">
        Start a scan for the research scope.
      </Notice>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {runs.map((run) => (
        <li key={run.id}>
          <Link
            href={`/runs/${encodeURIComponent(run.id)}`}
            className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-md border border-border bg-card p-3 hover:bg-ink-tint/50"
          >
            <span className="text-table font-semibold">{runTitle(run)}</span>
            <RunStatusBadge status={run.status} />
            <span className="text-identifier text-muted-foreground">{run.id}</span>
            <span className="text-caption text-muted-foreground sm:ml-auto">
              {run.started_at ? `Started ${formatDateTime(run.started_at)}` : "Not started"}
              {" · "}
              {run.counts.reports === 1 ? "1 report filed" : `${run.counts.reports} reports filed`}
              {run.counts.blocked > 0 ? `, ${run.counts.blocked} blocked` : ""}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
