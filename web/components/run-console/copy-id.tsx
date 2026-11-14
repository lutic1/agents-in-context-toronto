"use client";

import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";

import { cn } from "@/lib/utils";

/** An identifier in the mono face with a labelled copy button (EXPERIENCE "Foundation": identifiers are copyable). */
export function CopyId({
  value,
  label,
  display,
  className,
}: {
  value: string;
  /** What it is, for the button's name: "run ID", "action ID". */
  label: string;
  /** The text to show when it differs from the value copied. */
  display?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => () => clearTimeout(timer.current), []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be blocked; the identifier stays selectable on screen.
    }
  }

  return (
    <span className={cn("inline-flex max-w-full items-center gap-1", className)}>
      <code className="text-identifier min-w-0 break-all" title={display ? value : undefined}>
        {display ?? value}
      </code>
      <button
        type="button"
        onClick={copy}
        aria-label={`Copy ${label} ${value}`}
        className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-ink-tint hover:text-foreground"
      >
        {copied ? (
          <Check className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
        ) : (
          <Copy className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
        )}
      </button>
      <span role="status" aria-live="polite" className="sr-only">
        {copied ? `${label} copied` : ""}
      </span>
    </span>
  );
}
