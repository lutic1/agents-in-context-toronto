import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export type Stage = { id: string; label: string };

/**
 * The shared stage track (DESIGN.md "Stage track"): nine segments in Lifecycle
 * order. Reached stages are solid ink, except the two Early research stages
 * (the first two: discovery and assay development), which are a solid
 * haematoxylin wash. Future stages are hollow. A tooltip, reachable by hover or
 * keyboard focus, names each stage, and the current stage's name follows in caption text.
 *
 * `stages` comes from GET /schema (the stage order), so the labels are never
 * typed here. `currentIndex` is the zero-based current stage, or null for
 * "Stage not determined" (nine empty segments). `justAdvanced` marks the newest
 * segment in eosin until it is seen.
 */
export const EARLY_RESEARCH_STAGES = 2;
export const STAGE_COUNT = 9;

export function StageTrack({
  stages,
  currentIndex,
  dense = false,
  justAdvanced = false,
  showLabel = true,
  className,
}: {
  stages: Stage[];
  currentIndex: number | null;
  dense?: boolean;
  justAdvanced?: boolean;
  showLabel?: boolean;
  className?: string;
}) {
  const segments = Array.from({ length: STAGE_COUNT }, (_, i) => stages[i] ?? null);
  const current = currentIndex !== null && currentIndex >= 0 && currentIndex < STAGE_COUNT ? currentIndex : null;
  const label = current === null ? "Stage not determined" : (segments[current]?.label ?? `Stage ${current + 1}`);

  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      <ol
        className="m-0 flex list-none gap-[3px] p-0"
        aria-label={`Lifecycle stage: ${label}`}
      >
        {segments.map((stage, i) => {
          const reached = current !== null && i <= current;
          const early = i < EARLY_RESEARCH_STAGES;
          const newest = justAdvanced && current === i;
          const name = stage?.label ?? `Stage ${i + 1}`;
          const state = reached ? (i === current ? "current" : "reached") : "not yet";
          return (
            <Tooltip key={stage?.id ?? i}>
              <TooltipTrigger asChild>
                <li
                  tabIndex={0}
                  className={cn(
                    "rounded-sm",
                    dense ? "h-2 w-3" : "h-2.5 w-4",
                    reached && !early && "bg-foreground",
                    reached && early && "bg-ink-tint",
                    newest && "bg-eosin",
                    !reached && "border border-border bg-transparent",
                  )}
                >
                  <span className="sr-only">
                    {name}: {state}
                  </span>
                </li>
              </TooltipTrigger>
              <TooltipContent>
                {name} ({state})
              </TooltipContent>
            </Tooltip>
          );
        })}
      </ol>
      {showLabel ? <span className="text-caption text-muted-foreground">{label}</span> : null}
    </div>
  );
}
