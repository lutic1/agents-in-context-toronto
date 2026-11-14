"use client";

import type { ReactNode } from "react";
import { SWRConfig } from "swr";
import { toast } from "sonner";

import { ApiError, isUnreachable } from "@/lib/api";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

const UNREACHABLE_TOAST = "api-unreachable";
const RETRY_MS = 5000;

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
        shouldRetryOnError: (error) => isUnreachable(error),
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
          if (error instanceof ApiError && !isUnreachable(error)) return;
          if (retryCount >= 50) return;
          setTimeout(() => revalidate({ retryCount }), config.errorRetryInterval);
        },
      }}
    >
      <TooltipProvider delayDuration={150}>{children}</TooltipProvider>
      <Toaster position="bottom-right" />
    </SWRConfig>
  );
}
