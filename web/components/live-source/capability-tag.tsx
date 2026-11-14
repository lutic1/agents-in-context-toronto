"use client";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/**
 * The quiet MongoDB capability tag (EXPERIENCE "MongoDB Capability Tags"): one per
 * panel, static, with one sentence on hover or keyboard focus.
 */
export function CapabilityTag({
  label,
  hint,
  className,
}: {
  label: string;
  hint: string;
  className?: string;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          tabIndex={0}
          className={cn(
            "inline-flex items-center rounded-sm border border-border bg-transparent px-1.5 py-0.5 text-caption text-muted-foreground",
            className,
          )}
        >
          {label}
          <span className="sr-only">. {hint}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent>{hint}</TooltipContent>
    </Tooltip>
  );
}
