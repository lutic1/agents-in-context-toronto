"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useSWRConfig } from "swr";

/** Reads that a decision, a revert or a memory change can make stale. */
const RELATED = /^(reports|tasks|memories|proposals|diagnostics)/;

/**
 * After a successful write, re-read everything that may have changed: the
 * report, its task, its memories, and the pending list the top bar polls. It
 * also asks the router to refresh, in case the report body renders from the server.
 */
export function useRefreshRelated() {
  const { mutate } = useSWRConfig();
  const router = useRouter();
  return useCallback(() => {
    void mutate((key) => typeof key === "string" && RELATED.test(key));
    router.refresh();
  }, [mutate, router]);
}
