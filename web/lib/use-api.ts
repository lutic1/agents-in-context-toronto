"use client";

import useSWR, { type SWRConfiguration } from "swr";

import {
  ApiError,
  buildPath,
  getBuilt,
  isUnreachable,
  type ApiPath,
  type ResponseOf,
  type RouteOptions,
} from "@/lib/api";

/** Screens that show live data poll every 2 seconds (D40, EXPERIENCE "Interaction Primitives"). */
export const POLL_MS = 2000;

export type UseApiOptions = {
  /** Poll interval in milliseconds. Omit for a single load. */
  interval?: number;
  /** Pass false to skip the request (for example until an ID is known). */
  enabled?: boolean;
} & Pick<SWRConfiguration, "keepPreviousData">;

type HookArgs<P extends ApiPath<"get">> = Record<string, never> extends RouteOptions<P, "get">
  ? [options?: UseApiOptions & RouteOptions<P, "get">]
  : [options: UseApiOptions & RouteOptions<P, "get">];

/**
 * Read an API route by path, optionally polling. Typed from the schema like `get`:
 *
 *   const { data, error, isLoading } = useApi("/reports/{report_id}", {
 *     path: { report_id: id },
 *     interval: POLL_MS,
 *   });
 *
 * Polling pauses while the tab is hidden. `error` is an ApiError or an
 * ApiUnreachableError (use `isUnreachable`); the shell shows one toast for the
 * unreachable case, so a screen only needs its own inline empty or error state.
 */
export function useApi<P extends ApiPath<"get">>(route: P | null, ...args: HookArgs<P>) {
  const options = (args[0] ?? {}) as UseApiOptions & {
    path?: Record<string, unknown>;
    query?: Record<string, unknown>;
  };
  const { interval, enabled = true, keepPreviousData = true } = options;
  const key = route && enabled ? buildPath(route, options) : null;
  return useSWR<ResponseOf<P, "get">, ApiError | Error>(
    key,
    (p: string) => getBuilt<ResponseOf<P, "get">>(p),
    { refreshInterval: interval ?? 0, keepPreviousData },
  );
}

export { isUnreachable };
