import { cn } from "@/lib/utils";

/** Pill with a dashed haematoxylin border, ink-tint fill, text "Early research". */
export function EarlyResearchBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-dashed border-foreground bg-ink-tint px-2.5 py-0.5 text-caption font-semibold text-foreground",
        className,
      )}
    >
      Early research
    </span>
  );
}

/** Dotted-outline pill "Synthetic", on every synthetic Team, person, correction and memory author. */
export function SyntheticBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-dotted border-muted-foreground bg-transparent px-2 py-0.5 text-caption text-muted-foreground",
        className,
      )}
    >
      Synthetic
    </span>
  );
}
