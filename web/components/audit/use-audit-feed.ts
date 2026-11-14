"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";

import { ApiError, buildPath, getBuilt } from "@/lib/api";
import { POLL_MS } from "@/lib/use-api";
import { isActiveRun, type Audit } from "@/components/audit/labels";

/**
 * Where the Audit view gets its data, and the one honest label for it.
 *
 * ---------------------------------------------------------------------------
 * LIVE STREAM INTEGRATION POINT (Story 9.12, V48, flag `live_stream`)
 *
 * Today every read goes through the 2-second poll below, and `source` is
 * always "polling", so the screen says "Refreshing every 2 s" and never
 * claims to be live. When B02 merges its `web/components/live-source/`
 * (the `EventSource` on `GET /runs/<run_id>/stream` through its streaming
 * proxy, with the fallback and the label), this hook is the only place that
 * changes:
 *   1. read `isEnabled("live_stream")` from `@/lib/features`;
 *   2. with the flag on, open B02's live source for `runId`; on each message,
 *      or on `event: reset`, call `refresh()` to re-read the audit once (the
 *      audit is rebuilt server-side from Atlas, so a message only needs to
 *      trigger a re-read; `seq` stays the ordering source);
 *   3. return `source: "stream"` only while that source reports it is open,
 *      and stop the poll while it is; on any error, a 404 or a 501, return
 *      to `source: "polling"`.
 * `FeedSourceLabel` already renders both labels from `source`.
 * ---------------------------------------------------------------------------
 */

export type FeedSource = "polling" | "stream";

/** A 4xx or a 501 will not fix itself by asking again every 2 seconds. */
function stopsPolling(error: unknown): boolean {
  return error instanceof ApiError && ((error.status >= 400 && error.status < 500) || error.status === 501);
}

export function useAuditFeed(runId: string) {
  const key = buildPath("/runs/{run_id}/audit", { path: { run_id: runId } });
  const [halted, setHalted] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);

  const { data, error, isLoading, isValidating, mutate } = useSWR<Audit, ApiError | Error>(
    key,
    (path: string) => getBuilt<Audit>(path),
    {
      // Poll while the run is running (or stopping). A run that has ended is
      // read once, and again when the tab regains focus or on "Refresh now".
      refreshInterval: (latest) => {
        if (halted) return 0;
        if (latest && !isActiveRun(latest.run.status)) return 0;
        return POLL_MS;
      },
      keepPreviousData: true,
      onSuccess: () => {
        setHalted(false);
        setUpdatedAt(Date.now());
      },
      onError: (e) => {
        if (stopsPolling(e)) setHalted(true);
      },
    },
  );

  const refresh = useCallback(() => {
    setHalted(false);
    return mutate();
  }, [mutate]);

  const polling = !halted && (!data || isActiveRun(data.run.status));
  const source: FeedSource = "polling";

  return { audit: data, error, isLoading, isValidating, refresh, polling, source, updatedAt };
}
