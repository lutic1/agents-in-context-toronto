import { CircleCheck, CircleX, Clock, Undo2, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ReportStatus } from "@/components/report/types";

/**
 * The pending, accepted, rejected and reverted pills (DESIGN.md "Pending, accepted
 * and rejected badges"). Every pill carries an icon and its word, so colour is
 * never the only signal, and a pending item never wears the accepted pill.
 */
function Pill({
  icon: Icon,
  className,
  children,
}: {
  icon: LucideIcon;
  className: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-full border bg-card px-2.5 py-0.5 text-caption font-semibold",
        className,
      )}
    >
      <Icon className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
      {children}
    </span>
  );
}

export function PendingBadge({ children = "Pending review" }: { children?: React.ReactNode }) {
  return (
    <Pill icon={Clock} className="border-dashed border-muted-foreground text-muted-foreground">
      {children}
    </Pill>
  );
}

export function AcceptedBadge({ children = "Accepted" }: { children?: React.ReactNode }) {
  return (
    <Pill icon={CircleCheck} className="border-accepted text-accepted">
      {children}
    </Pill>
  );
}

export function RejectedBadge({ children = "Rejected" }: { children?: React.ReactNode }) {
  return (
    <Pill icon={CircleX} className="border-destructive text-destructive">
      {children}
    </Pill>
  );
}

/** Ink text and a solid ink edge, never `destructive`: a revert is a Reviewer's decision, not an error. */
export function RevertedBadge({ children = "Reverted" }: { children?: React.ReactNode }) {
  return (
    <Pill icon={Undo2} className="border-foreground text-foreground">
      {children}
    </Pill>
  );
}

/** The badge for a report's status. The two in-flight states say what is happening, in words. */
export function ReportStatusBadge({ status }: { status: ReportStatus }) {
  switch (status) {
    case "pending":
      return <PendingBadge />;
    case "accepting":
      return <PendingBadge>Accepting</PendingBadge>;
    case "accepted":
      return <AcceptedBadge />;
    case "rejected":
      return <RejectedBadge />;
    case "reverting":
      return <RevertedBadge>Reverting</RevertedBadge>;
    case "reverted":
      return <RevertedBadge />;
  }
}

/** The status word alone, for live regions. */
export function reportStatusWord(status: ReportStatus): string {
  switch (status) {
    case "pending":
      return "Pending review";
    case "accepting":
      return "Accepting";
    case "accepted":
      return "Accepted";
    case "rejected":
      return "Rejected";
    case "reverting":
      return "Reverting";
    case "reverted":
      return "Reverted";
  }
}

/** The "New" changed mark: a 6px eosin dot and the word, never a pink fill (DESIGN.md "Changed mark"). */
export function NewMark() {
  return (
    <span className="inline-flex items-center gap-1.5 text-caption font-semibold text-eosin-text">
      <span className="size-1.5 rounded-full bg-eosin" aria-hidden="true" />
      New
    </span>
  );
}
