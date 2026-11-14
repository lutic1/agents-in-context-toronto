"use client";

import { RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LiveSourceLabel, type LiveSourceMode } from "@/components/live-source";
import { formatTime } from "@/lib/format";

/**
 * The feed source label above the timeline (V48, DESIGN "Feed source label").
 * While the screen is getting new data by itself it is B02's `LiveSourceLabel`:
 * text, never only an icon, always true to the source, "Live (change stream)"
 * only while a stream is open and "Refreshing every 2 s" while polling, with a
 * change between them announced politely. A run that has ended is not
 * refreshed, and says so.
 */
export function FeedSourceLabel({
  mode,
  autoRefresh,
  halted = false,
  updatedAt,
  refreshing,
  onRefresh,
}: {
  mode: LiveSourceMode;
  /** True while the screen is asking for new data by itself, by the stream or by polling. */
  autoRefresh: boolean;
  /** True when refreshing stopped because a refresh failed for good (a 4xx or 501), not because the run ended. */
  halted?: boolean;
  updatedAt: number | null;
  /** True while a read is in flight. */
  refreshing: boolean;
  onRefresh: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-caption text-muted-foreground">
      {autoRefresh ? (
        <LiveSourceLabel mode={mode} />
      ) : (
        <p role="status" aria-live="polite">
          {halted ? "Not refreshing: the last refresh failed." : "Run ended. Not refreshing."}
        </p>
      )}
      {updatedAt ? <span>Updated {formatTime(updatedAt)}</span> : null}
      {!autoRefresh ? (
        <Button type="button" variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
          <RefreshCcw aria-hidden="true" />
          Refresh now
        </Button>
      ) : null}
    </div>
  );
}
