"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { POLL_MS, useApi } from "@/lib/use-api";
import { displayName, initials } from "@/lib/format";
import type { PrincipalLike } from "@/lib/runs";

/**
 * The read-only "Signed in as" chip from GET /whoami. It is a label, not a
 * control: who the caller is comes from the server-side key, and nothing here
 * can change it (EXPERIENCE "Foundation").
 */
export function SignedInChip() {
  const { data, error, isLoading } = useApi<PrincipalLike>("whoami", {
    // Re-read slowly so a changed grant is picked up without a reload.
    interval: POLL_MS * 15,
  });

  if (isLoading && !data) {
    return <Skeleton className="h-9 w-44 rounded-full" aria-label="Loading who is signed in" />;
  }

  if (!data) {
    return (
      <div
        className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-caption text-muted-foreground"
        title={error ? error.message : undefined}
      >
        Signed in as: unavailable
      </div>
    );
  }

  const name = displayName(data.name || data.id);
  return (
    <div
      className="flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-3"
      role="group"
      aria-label={`Signed in as ${name}`}
    >
      <span
        className="flex size-7 items-center justify-center rounded-full bg-ink-deep text-[12px] font-bold text-primary-foreground"
        aria-hidden="true"
      >
        {initials(name)}
      </span>
      <span className="text-caption text-muted-foreground">Signed in as</span>
      <span className="text-table font-semibold text-foreground">{name}</span>
    </div>
  );
}
