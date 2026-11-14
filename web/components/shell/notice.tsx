import type { LucideIcon } from "lucide-react";
import { CloudOff, Inbox } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Solid inline notice on the coverslip surface. Screens use it for the empty
 * and error states in EXPERIENCE "State Patterns", so a page never goes blank
 * and never crashes when the API is unreachable.
 */
export function Notice({
  icon: Icon = Inbox,
  title,
  children,
  role,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  children?: React.ReactNode;
  role?: "status" | "alert";
  className?: string;
}) {
  return (
    <section
      role={role}
      className={cn(
        "flex items-start gap-3 rounded-lg border border-border bg-card p-5 shadow-sm",
        className,
      )}
    >
      <Icon className="mt-0.5 size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
      <div className="min-w-0">
        <h2 className="text-heading">{title}</h2>
        {children ? <div className="mt-1 text-body text-muted-foreground">{children}</div> : null}
      </div>
    </section>
  );
}

/** The inline state for an unreachable API. The toast says it once; the page says it where the data would be. */
export function ApiUnreachableNotice({ className }: { className?: string }) {
  return (
    <Notice icon={CloudOff} title="Couldn't reach the API" role="alert" className={className}>
      The page will fill in by itself when the API answers. Nothing here is lost.
    </Notice>
  );
}
