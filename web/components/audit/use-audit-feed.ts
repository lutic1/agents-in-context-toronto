"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";

import { ApiError, buildPath, getBuilt } from "@/lib/api";
import { useLiveSource, type LiveSourceMode } from "@/components/live-source";
import { isActiveRun, type Audit } from "@/components/audit/labels";

/**
 * Where the Audit view gets its data, and the one honest label for it (Story 9.12, V48).
 *
 * With the `live_stream` flag on and the run active, B02's live source opens the
 * stream for the run. While it is open the mode is "live" and the audit is read
 * again whenever the stream says something happened. On any error, a 404 or a 501,
 * or with the flag off, the mode is "polling" and the audit is read every 2 seconds
 * as before. The audit is rebuilt server-side from Atlas, so a stream message only
 * triggers a re-read; `seq` stays the ordering source.
 *
 * A run that has ended is not streamed or polled: it is read once, and again when
 * the tab regains focus or on "Refresh now".
 */

/** A 4xx or a 501 will not fix itself by asking again every 2 seconds. */
function stopsPolling(error: unknown): boolean {
  return error instanceof ApiError && ((error.status >= 400 && error.status < 500) || error.status === 501);
}

export function useAuditFeed(runId: string) {
  const key = buildPath("/runs/{run_id}/audit", { path: { run_id: runId } });
  const [halted, setHalted] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);
  // Whether the run is still producing decisions, as of the last read. Unknown counts as active.
  const [active, setActive] = useState(true);

  const live = useLiveSource(runId, { enabled: active && !halted, keys: [key] });

  const { data, error, isLoading, isValidating, mutate } = useSWR<Audit, ApiError | Error>(
    key,
    (path: string) => getBuilt<Audit>(path),
    {
      // Poll while the run is running (or stopping) and the stream is not open. A run
      // that has ended is read once, and again when the tab regains focus or on "Refresh now".
      refreshInterval: (latest) => {
        if (halted) return 0;
        if (latest && !isActiveRun(latest.run.status)) return 0;
        return live.refreshInterval;
      },
      keepPreviousData: true,
      onSuccess: (latest) => {
        setHalted(false);
        setActive(isActiveRun(latest.run.status));
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

  // True while the screen is getting new data by itself, by the stream or by polling.
  const autoRefresh = !halted && (!data || isActiveRun(data.run.status));
  // "live" only while the stream is open and the run is active, so the label is never false.
  const mode: LiveSourceMode = autoRefresh ? live.mode : "polling";

  return { audit: data, error, isLoading, isValidating, refresh, autoRefresh, halted, mode, updatedAt };
}
