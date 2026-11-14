"use client";

import { Radio, RefreshCcw } from "lucide-react";

import { CapabilityTag } from "@/components/audit/common";
import { Button } from "@/components/ui/button";
import { formatTime } from "@/lib/format";
import type { FeedSource } from "@/components/audit/use-audit-feed";

/**
 * The feed source label above the timeline (V48, DESIGN "Feed source label").
 * It is text, never only an icon, and it is always true to the source:
 * "Live (change stream)" only while a stream is open, "Refreshing every 2 s"
 * while polling. A run that has ended is not refreshed, and says so.
 * A change between the labels is announced politely.
 */
export function FeedSourceLabel({
  source,
  polling,
  halted = false,
  updatedAt,
  refreshing,
  onRefresh,
}: {
  source: FeedSource;
  /** True while the screen is asking for new data by itself. */
  polling: boolean;
  /** True when polling stopped because a refresh failed for good (a 4xx or 501), not because the run ended. */
  halted?: boolean;
  updatedAt: number | null;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const live = source === "stream";
  const active = live || polling;

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-caption text-muted-foreground">
      <p role="status" aria-live="polite" className="flex items-center gap-1.5">
        {active ? (
          live ? (
            <Radio className="size-3.5 text-foreground" strokeWidth={1.75} aria-hidden="true" />
          ) : (
            <RefreshCcw className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          )
        ) : null}
        <span className={live ? "font-semibold text-foreground" : undefined}>
          {live
            ? "Live (change stream)"
            : polling
              ? "Refreshing every 2 s"
              : halted
                ? "Not refreshing: the last refresh failed."
                : "Run ended. Not refreshing."}
        </span>
      </p>
      {active ? (
        live ? (
          <CapabilityTag
            name="Change streams"
            sentence="New actions arrive from an Atlas change stream on the run's events, resuming where they left off."
          />
        ) : (
          <CapabilityTag name="Polling" sentence="The audit view reads new actions from Atlas every 2 seconds." />
        )
      ) : null}
      {updatedAt ? <span>Updated {formatTime(updatedAt)}</span> : null}
      {!active ? (
        <Button type="button" variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
          <RefreshCcw aria-hidden="true" />
          Refresh now
        </Button>
      ) : null}
    </div>
  );
}
