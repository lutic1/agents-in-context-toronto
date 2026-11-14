"use client";

import { useState } from "react";
import { CircleCheck, CircleX, CirclePause, OctagonX, Play, Square } from "lucide-react";
import { useSWRConfig } from "swr";

import { totals } from "@/components/run-console/entry-state";
import type { AuditEntry, Run } from "@/components/run-console/types";
import { Button } from "@/components/ui/button";
import { ApiError, buildPath, isUnreachable, post } from "@/lib/api";
import { formatTime } from "@/lib/format";

/** The status words, one place for the control and the run's live region. */
export function statusText(run: Run, entries: AuditEntry[] | undefined): string {
  switch (run.status) {
    case "running":
      return "Running";
    case "stopping":
      return `Stopping: ${run.in_flight} in flight. No new actions will start.`;
    case "stopped": {
      const at = run.stopped_at ? ` at ${formatTime(run.stopped_at)}` : "";
      if (!entries) return `Stopped${at}.`;
      const t = totals(entries);
      return `Stopped${at}. ${t.tookEffect} took effect, ${t.blocked} blocked, ${t.unknown} unknown.`;
    }
    case "done":
      return run.finished_at ? `Finished at ${formatTime(run.finished_at)}.` : "Finished.";
    case "failed":
      return "Failed.";
  }
}

/**
 * Stop control (EXPERIENCE "Stop control"): "Stop run" while running, one press, no
 * confirmation. New admissions stop at once; the status reads "Stopping: {n} in flight"
 * and then "Stopped" with totals. It works the same on a follow-up task's run. A stopped
 * run is not restarted from here.
 */
export function StopControl({ run, entries }: { run: Run; entries: AuditEntry[] | undefined }) {
  const { mutate } = useSWRConfig();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function stop() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const next = await post("/runs/{run_id}/stop", { path: { run_id: run.id } });
      await mutate(buildPath("/runs/{run_id}", { path: { run_id: run.id } }), next, { revalidate: true });
      await mutate(buildPath("/runs/{run_id}/audit", { path: { run_id: run.id } }));
    } catch (cause) {
      setError(
        isUnreachable(cause)
          ? "Couldn't reach the API. The stop request was not received."
          : cause instanceof ApiError && cause.status === 403
            ? "You are not allowed to stop this run."
            : cause instanceof Error
              ? cause.message
              : "The run could not be stopped.",
      );
    } finally {
      setBusy(false);
    }
  }

  const text = statusText(run, entries);

  return (
    <div className="flex flex-col gap-2">
      {run.status === "running" ? (
        <div>
          <Button type="button" onClick={stop} disabled={busy} aria-busy={busy}>
            <Square aria-hidden="true" />
            Stop run
          </Button>
        </div>
      ) : null}
      {run.status === "stopping" ? (
        <div>
          <Button type="button" variant="secondary" disabled aria-hidden="true" tabIndex={-1} className="text-muted-foreground">
            <CirclePause aria-hidden="true" />
            Stopping: {run.in_flight} in flight
          </Button>
        </div>
      ) : null}

      {/* Run status announces politely. */}
      <p role="status" aria-live="polite" className="flex items-start gap-2 text-table">
        {run.status === "running" ? (
          <Play className="mt-0.5 size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
        ) : run.status === "stopping" ? (
          <CirclePause className="mt-0.5 size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
        ) : run.status === "stopped" ? (
          <OctagonX className="mt-0.5 size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
        ) : run.status === "done" ? (
          <CircleCheck className="mt-0.5 size-[18px] shrink-0 text-accepted" strokeWidth={1.75} aria-hidden="true" />
        ) : (
          <CircleX className="mt-0.5 size-[18px] shrink-0 text-destructive" strokeWidth={1.75} aria-hidden="true" />
        )}
        <span>
          <span className="font-semibold">Run status:</span> {text}
        </span>
      </p>

      {error ? (
        <p role="alert" className="text-table text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}
