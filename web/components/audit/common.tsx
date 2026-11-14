"use client";

import { useState } from "react";
import {
  Check,
  CircleCheck,
  CircleX,
  Clock,
  Copy,
  SquareArrowOutUpRight,
  Undo2,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { SyntheticBadge } from "@/components/shell/badges";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { displayName } from "@/lib/format";
import { cn } from "@/lib/utils";
import { isNct, trialUrl } from "@/components/audit/labels";

/** A solid coverslip panel with an icon heading (DESIGN "Glass panel": only the top bar is glass). */
export function Panel({
  icon: Icon,
  title,
  headingId,
  aside,
  children,
  className,
}: {
  icon: LucideIcon;
  title: string;
  headingId: string;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      aria-labelledby={headingId}
      className={cn("rounded-lg border border-border bg-card p-5 shadow-sm", className)}
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h2 id={headingId} className="flex items-center gap-2 text-heading">
          <Icon className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {title}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

/** An identifier in the mono face. Breaks anywhere so it never forces a horizontal scroll at 320px. */
export function Mono({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("text-identifier [overflow-wrap:anywhere]", className)}>{children}</span>;
}

/** A mono identifier with a copy button (identifiers are copyable, DESIGN "Identity card"). */
export function CopyId({ value, label }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked: the ID stays selectable on screen.
    }
  }

  return (
    <span className="inline-flex max-w-full items-center gap-1">
      <Mono>{value}</Mono>
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        onClick={copy}
        aria-label={`Copy ${label ?? value}`}
      >
        {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
      </Button>
      <span className="sr-only" role="status" aria-live="polite">
        {copied ? "Copied" : ""}
      </span>
    </span>
  );
}

/** A person's name. The demo's people are synthetic and say so (DESIGN "Synthetic badge"). */
export function PersonName({ id, className }: { id: string; className?: string }) {
  return (
    <span className={cn("inline-flex flex-wrap items-center gap-1.5", className)}>
      <span className="font-semibold">{displayName(id)}</span>
      <SyntheticBadge />
    </span>
  );
}

/** A trial ID that links to its ClinicalTrials.gov record; any other ref is plain mono. */
export function SourceRef({ source }: { source: string }) {
  if (!isNct(source)) return <Mono>{source}</Mono>;
  return (
    <a
      href={trialUrl(source)}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 underline underline-offset-2"
    >
      <Mono>{source}</Mono>
      <SquareArrowOutUpRight className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
      <span className="sr-only">(opens ClinicalTrials.gov in a new tab)</span>
    </a>
  );
}

/** A link inside the app, in the same underlined style. */
export function AppLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="underline underline-offset-2">
      {children}
    </Link>
  );
}

/** Pending, accepted, rejected and reverted pills: an icon and a word, never colour alone (DESIGN). */
export function StatusPill({
  status,
}: {
  status: "pending" | "accepted" | "rejected" | "reverted" | "working";
}) {
  const base = "inline-flex items-center gap-1 rounded-full border bg-card px-2 py-0.5 text-caption font-semibold";
  switch (status) {
    case "accepted":
      return (
        <span className={cn(base, "border-accepted text-accepted")}>
          <CircleCheck className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Accepted
        </span>
      );
    case "rejected":
      return (
        <span className={cn(base, "border-destructive text-destructive")}>
          <CircleX className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Rejected
        </span>
      );
    case "reverted":
      return (
        <span className={cn(base, "border-solid border-foreground text-foreground")}>
          <Undo2 className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Reverted
        </span>
      );
    case "working":
      return (
        <span className={cn(base, "border-dashed border-muted-foreground text-muted-foreground")}>
          <Clock className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Being applied
        </span>
      );
    default:
      return (
        <span className={cn(base, "border-dashed border-muted-foreground text-muted-foreground")}>
          <Clock className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Pending review
        </span>
      );
  }
}

/** The quiet capability tag: one per panel, with a one-sentence hover and focus explanation (EXPERIENCE "MongoDB Capability Tags"). */
export function CapabilityTag({ name, sentence }: { name: string; sentence: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          tabIndex={0}
          className="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-caption text-muted-foreground"
        >
          {name}
          <span className="sr-only">. {sentence}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent side="bottom" aria-hidden="true">
        {sentence}
      </TooltipContent>
    </Tooltip>
  );
}
