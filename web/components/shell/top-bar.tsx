"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileSearch, ScrollText, SquareTerminal, type LucideIcon } from "lucide-react";

import { Wordmark } from "@/components/shell/wordmark";
import { SignedInChip } from "@/components/shell/signed-in-chip";
import { ApiError, itemsOf } from "@/lib/api";
import { POLL_MS, useApi } from "@/lib/use-api";
import { latestRun, type RunLike } from "@/lib/runs";
import { cn } from "@/lib/utils";

type Page<T> = { items?: T[]; next?: string | null };

/**
 * The single top bar (EXPERIENCE "Information Architecture"): the wordmark,
 * Run console, Reports with the pending count, Audit, then the read-only
 * "Signed in as" chip. It is the glass panel.
 */
export function TopBar() {
  const pathname = usePathname() ?? "/";

  const pending = useApi<Page<unknown>>("reports", {
    query: { status: "pending" },
    interval: POLL_MS,
  });
  const runs = useApi<Page<RunLike>>("runs", { interval: POLL_MS * 2.5 });

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
    <header className="glass-panel-strong sticky top-0 z-40 rounded-none border-x-0 border-t-0 border-b border-border">
      <div className="mx-auto flex h-16 w-full max-w-content items-center gap-8 px-8">
        <Wordmark />
        <nav aria-label="Main" className="flex items-center gap-1">
          <NavItem href="/runs" label="Run console" Icon={SquareTerminal} active={onRunConsole} />
          <NavItem
            href="/reports"
            label="Reports"
            Icon={FileSearch}
            active={onReports}
            trailing={
              pendingNotBuilt || pendingCount === null ? null : (
                <span
                  className="rounded-full bg-primary px-2 py-0.5 text-[12px] font-bold leading-none text-primary-foreground"
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
        "flex items-center gap-2 rounded-md px-3 py-2 text-table font-semibold text-foreground transition-colors hover:bg-ink-tint",
        active && "bg-ink-tint",
      )}
    >
      <Icon className="size-[18px]" strokeWidth={1.75} aria-hidden="true" />
      <span>{label}</span>
      {trailing}
    </Link>
  );
}
