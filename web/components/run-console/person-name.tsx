import { SyntheticBadge } from "@/components/shell/badges";
import { displayName } from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * The people the demo knows to be synthetic: the Reviewer, Sam (DESIGN "Synthetic badge",
 * EXPERIENCE "Started by Sam (Synthetic)"). No API record carries a `synthetic` flag for a
 * person (only Teams, rules and records do), so this is the one list. A principal that is
 * not named here is a real person and is never badged.
 */
const KNOWN_SYNTHETIC_PEOPLE: ReadonlySet<string> = new Set(["sam"]);

export function isSyntheticPerson(id: string): boolean {
  return KNOWN_SYNTHETIC_PEOPLE.has(id.trim().toLowerCase());
}

/** A person's name, with the shared Synthetic badge when they are a synthetic person. */
export function PersonName({ id, className }: { id: string; className?: string }) {
  const name = displayName(id);
  if (!isSyntheticPerson(id)) return <span className={className}>{name}</span>;
  return (
    <span className={cn("inline-flex flex-wrap items-center gap-x-1.5 gap-y-1 align-middle", className)}>
      <span>{name}</span>
      <SyntheticBadge />
    </span>
  );
}
