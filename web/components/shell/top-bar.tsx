"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileSearch, ScrollText, SquareTerminal, type LucideIcon } from "lucide-react";

import { Wordmark } from "@/components/shell/wordmark";
import { SignedInChip } from "@/components/shell/signed-in-chip";
import { ApiError, itemsOf } from "@/lib/api";
import { POLL_MS, useApi } from "@/lib/use-api";
import { latestRun } from "@/lib/runs";
import { cn } from "@/lib/utils";

/**
 * The single top bar (EXPERIENCE "Information Architecture"): the wordmark,
 * Run console, Reports with the pending count, Audit, then the read-only
 * "Signed in as" chip. It is the glass panel.
 */
export function TopBar() {
  const pathname = usePathname() ?? "/";

  const pending = useApi("/reports", {
    query: { status: "pending" },
    interval: POLL_MS,
  });
  const runs = useApi("/runs", { interval: POLL_MS * 2.5 });

  // The count is hidden while the route is not built (501), and while it is unknown.
  const pendingNotBuilt = pending.error instanceof ApiError && pending.error.status === 501;
  const pendingCount = pending.data ? itemsOf(pending.data).length : null;
  const hasMore = Boolean(pending.data?.next);

  // Audit opens the run being looked at, else the latest run, else the run console.
  const viewedRun = /^\/runs\/([^/]+)/.exec(pathname)?.[1];
  const latest = latestRun(itemsOf(runs.data));
  const auditRunId = viewedRun ?? latest?.id ?? null;
  const auditHref = auditRunId ? `/runs/${encodeURIComponent(auditRunId)}/audit` : "/runs";

  const onAudit = /^\/runs\/[^/]+\/audit(\/|$)/.test(pathname);
  const onRunConsole = pathname.startsWith("/runs") && !onAudit;
  const onReports = pathname.startsWith("/reports");

  return (
    <header className="glass-panel-strong sticky top-0 z-40 rounded-none">
      {/* Phones: wordmark and chip on one row, the nav on a second scrollable row. md and up: one row. */}
      <div className="mx-auto flex min-h-16 w-full max-w-content flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2 md:flex-nowrap md:gap-x-8 md:px-8">
        <Wordmark />
        <nav
          aria-label="Main"
          className="order-last -mx-2 flex w-[calc(100%+1rem)] min-w-0 items-center gap-1 overflow-x-auto px-2 [scrollbar-width:none] md:order-none md:mx-0 md:w-auto md:overflow-visible md:px-0"
        >
          <NavItem href="/runs" label="Run console" Icon={SquareTerminal} active={onRunConsole} />
          <NavItem
            href="/reports"
            label="Reports"
            Icon={FileSearch}
            active={onReports}
            trailing={
              // Hidden while unknown, while the route is not built, and at zero: a "0" badge is noise.
              pendingNotBuilt || pendingCount === null || (pendingCount === 0 && !hasMore) ? null : (
                <span
                  className="rounded-full bg-apricot px-2 py-0.5 text-caption font-bold leading-none text-foreground"
                  title={`${pendingCount}${hasMore ? "+" : ""} pending`}
                >
                  {pendingCount}
                  {hasMore ? "+" : ""}
                </span>
              )
            }
          />
          <NavItem href={auditHref} label="Audit" Icon={ScrollText} active={onAudit} />
        </nav>
        {/* Run status and the count announce politely (Accessibility Floor). */}
        <p className="sr-only" role="status" aria-live="polite">
          {pendingNotBuilt || pendingCount === null
            ? ""
            : `${pendingCount}${hasMore ? " or more" : ""} ${pendingCount === 1 && !hasMore ? "report" : "reports"} pending review`}
        </p>
        <div className="ml-auto">
          <SignedInChip />
        </div>
      </div>
    </header>
  );
}

function NavItem({
  href,
  label,
  Icon,
  active,
  trailing,
}: {
  href: string;
  label: string;
  Icon: LucideIcon;
  active: boolean;
  trailing?: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex min-h-11 shrink-0 items-center gap-2 rounded-md px-3 text-table font-semibold whitespace-nowrap text-foreground transition-colors duration-150",
        // Active: ink-tint fill plus a 2px ink bottom edge, so it does not rely on colour alone.
        // The weight stays the same, so the tabs never change width between pages.
        active
          ? "bg-ink-tint shadow-[inset_0_-2px_0_0_var(--periwinkle)]"
          : "hover:bg-ink-tint/60",
      )}
    >
      <Icon className="size-[18px]" strokeWidth={1.75} aria-hidden="true" />
      <span>{label}</span>
      {trailing}
    </Link>
  );
}
