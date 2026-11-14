"use client";

import { useApi } from "@/lib/use-api";

/** The signed-in principal's allowed actions, from GET /whoami (read-only; the page never chooses who it is). */
export function useActions() {
  const { data, error, isLoading } = useApi("/whoami");
  const actions: readonly string[] = data?.actions ?? [];
  return {
    loaded: Boolean(data),
    loading: isLoading && !data,
    error,
    can: (action: string) => actions.includes(action),
  };
}
