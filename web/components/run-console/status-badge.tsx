import { CircleCheck, CirclePause, CircleX, OctagonX, Play, type LucideIcon } from "lucide-react";

import type { Run } from "@/components/run-console/types";
import { cn } from "@/lib/utils";

const STATUS: Record<Run["status"], { word: string; Icon: LucideIcon; tone: string }> = {
  running: { word: "Running", Icon: Play, tone: "text-foreground" },
  stopping: { word: "Stopping", Icon: CirclePause, tone: "text-muted-foreground" },
  stopped: { word: "Stopped", Icon: OctagonX, tone: "text-foreground" },
  done: { word: "Finished", Icon: CircleCheck, tone: "text-accepted" },
  failed: { word: "Failed", Icon: CircleX, tone: "text-destructive" },
};

/** A run's status as icon and word, never colour alone. */
export function RunStatusBadge({ status, className }: { status: Run["status"]; className?: string }) {
  const { word, Icon, tone } = STATUS[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-border bg-card px-2 py-0.5 text-caption font-semibold",
        tone,
        className,
      )}
    >
      <Icon className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
      {word}
    </span>
  );
}
