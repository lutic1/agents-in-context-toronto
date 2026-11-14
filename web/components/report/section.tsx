import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * A solid panel with its heading, the icon inline before it on the same left
 * edge (DESIGN.md "Glass panel"). `aside` is the panel's one capability tag.
 */
export function Section({
  id,
  icon: Icon,
  title,
  aside,
  children,
  className,
}: {
  id: string;
  icon: LucideIcon;
  title: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      aria-labelledby={`${id}-heading`}
      className={cn("flex min-w-0 flex-col gap-4 rounded-lg border border-border bg-card p-5 shadow-sm", className)}
    >
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h2 id={`${id}-heading`} className="text-heading flex items-center gap-2">
          <Icon className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {title}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  );
}
