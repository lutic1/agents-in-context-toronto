import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

/**
 * A quiet outlined MongoDB capability tag (DESIGN.md "Capability tag"). One per
 * panel. The sentence shows on hover and on keyboard focus.
 */
export function CapabilityTag({ label, hint }: { label: string; hint: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className="rounded-sm border border-border bg-card px-2 py-0.5 text-caption text-muted-foreground"
        >
          {label}
        </button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">{hint}</TooltipContent>
    </Tooltip>
  );
}
