"use client";

import useSWR, { type SWRConfiguration } from "swr";

import { ApiError, get, isUnreachable, withQuery, type Query } from "@/lib/api";

/** Screens that show live data poll every 2 seconds (D40, EXPERIENCE "Interaction Primitives"). */
export const POLL_MS = 2000;

export type UseApiOptions = {
  /** Poll interval in milliseconds. Omit for a single load. */
  interval?: number;
  query?: Query;
  /** Pass false to skip the request (for example until an ID is known). */
  enabled?: boolean;
} & Pick<SWRConfiguration, "keepPreviousData">;

/**
 * Read an API route by path, optionally polling.
 *
 *   const { data, error, isLoading } = useApi<Report>(`reports/${id}`, { interval: POLL_MS });
 *
 * Polling pauses while the tab is hidden. `error` is an ApiError or an
 * ApiUnreachableError (use `isUnreachable`); the shell shows one toast for the
 * unreachable case, so a screen only needs its own inline empty or error state.
 */
export function useApi<T>(path: string | null, options: UseApiOptions = {}) {
  const { interval, query, enabled = true, keepPreviousData = true } = options;
  const key = path && enabled ? withQuery(path, query) : null;
  return useSWR<T, ApiError | Error>(key, (p: string) => get<T>(p), {
    refreshInterval: interval ?? 0,
    keepPreviousData,
  });
}

export { isUnreachable };
