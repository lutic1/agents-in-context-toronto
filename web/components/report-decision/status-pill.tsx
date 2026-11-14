import { CircleCheck, CircleX, Clock, Undo2, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export type PillStatus = "pending" | "accepted" | "rejected" | "reverted";

const PILLS: Record<PillStatus, { icon: LucideIcon; label: string; className: string }> = {
  pending: {
    icon: Clock,
    label: "Pending review",
    className: "border-dashed border-muted-foreground text-muted-foreground",
  },
  accepted: { icon: CircleCheck, label: "Accepted", className: "border-accepted text-accepted" },
  rejected: { icon: CircleX, label: "Rejected", className: "border-destructive text-destructive" },
  reverted: { icon: Undo2, label: "Reverted", className: "border-foreground text-foreground" },
};

/** Pending, accepted, rejected and reverted pills: always an icon and a word, never colour alone. */
export function StatusPill({ status, className }: { status: PillStatus; className?: string }) {
  const { icon: Icon, label, className: tone } = PILLS[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border bg-card px-2.5 py-0.5 text-caption font-medium whitespace-nowrap",
        tone,
        className,
      )}
    >
      <Icon className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
      {label}
    </span>
  );
}
