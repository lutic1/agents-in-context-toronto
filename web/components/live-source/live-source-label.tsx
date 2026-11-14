"use client";

import { Radio, RefreshCw } from "lucide-react";

import { CapabilityTag } from "@/components/live-source/capability-tag";
import { liveSourceLabel, type LiveSourceMode } from "@/components/live-source/use-live-source";
import { cn } from "@/lib/utils";

/**
 * The run feed status, above the feed on the Run console and the Audit view (V48):
 * "Live (change stream)" while the stream is open, "Refreshing every 2 s" while
 * polling. It is text, not only an icon, and a change between the two is announced
 * politely. The tag beside it says "Change streams" or "Polling", matching the label.
 */
export function LiveSourceLabel({ mode, className }: { mode: LiveSourceMode; className?: string }) {
  const label = liveSourceLabel(mode);
  const Icon = mode === "live" ? Radio : RefreshCw;
  return (
    <div className={cn("flex flex-wrap items-center gap-x-3 gap-y-1", className)}>
      <p className="flex items-center gap-1.5 text-table font-semibold text-foreground">
        <Icon className="size-4" strokeWidth={1.75} aria-hidden="true" />
        <span>{label}</span>
      </p>
      {mode === "live" ? (
        <CapabilityTag
          label="Change streams"
          hint="New actions arrive from an Atlas change stream on the run's events, resuming where they left off."
        />
      ) : (
        <CapabilityTag label="Polling" hint="The console reads new actions from Atlas every 2 seconds." />
      )}
      {/* Announced politely when it changes; the visible text is not a live region, so it is not read twice. */}
      <span role="status" aria-live="polite" className="sr-only">
        Feed source: {label}
      </span>
    </div>
  );
}
