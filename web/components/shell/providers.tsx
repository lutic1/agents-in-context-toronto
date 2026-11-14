"use client";

import type { ReactNode } from "react";
import { SWRConfig } from "swr";
import { toast } from "sonner";

import { ApiError, isUnreachable } from "@/lib/api";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

const UNREACHABLE_TOAST = "api-unreachable";
const RETRY_MS = 5000;

/** Retry anything except a client error that retrying cannot fix (4xx other than 408 and 429). */
function shouldRetry(error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return error.status === 408 || error.status === 429;
  }
  return true;
}

/**
 * Client providers for the whole app: one SWR configuration, tooltips and the
 * toaster. When the API cannot be reached, exactly one toast says so
 * ("Couldn't reach the API. Retrying in 5 seconds."), and it clears on the
 * next successful read. Other errors (404, 501, ...) are left to each screen.
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        errorRetryInterval: RETRY_MS,
        shouldRetryOnError: (error) => shouldRetry(error),
        onError: (error) => {
          if (isUnreachable(error)) {
            toast.error("Couldn't reach the API. Retrying in 5 seconds.", {
              id: UNREACHABLE_TOAST,
              duration: RETRY_MS,
            });
          }
        },
        onSuccess: () => {
          toast.dismiss(UNREACHABLE_TOAST);
        },
        onErrorRetry: (error, _key, config, revalidate, { retryCount }) => {
          // Polled keys keep coming back by themselves: no retry cap.
          if (!shouldRetry(error)) return;
          setTimeout(() => revalidate({ retryCount }), config.errorRetryInterval);
        },
      }}
    >
      <TooltipProvider delayDuration={150}>{children}</TooltipProvider>
      <Toaster position="bottom-right" />
    </SWRConfig>
  );
}
