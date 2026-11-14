import { SquareArrowOutUpRight } from "lucide-react";

import { cn } from "@/lib/utils";

/** A link to a page outside DxP: opens in a new tab, and says so to a screen reader. */
export function ExternalLink({
  href,
  children,
  className,
  mono = true,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
  mono?: boolean;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "inline-flex items-center gap-1 underline underline-offset-2 hover:text-muted-foreground",
        mono && "text-identifier",
        className,
      )}
    >
      {children}
      <SquareArrowOutUpRight className="size-3 shrink-0" strokeWidth={1.75} aria-hidden="true" />
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}
