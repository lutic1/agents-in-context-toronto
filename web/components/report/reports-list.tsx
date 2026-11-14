"use client";

import Link from "next/link";
import { CircleAlert, FileSearch, Inbox } from "lucide-react";

import { AlertState } from "@/components/report/alert-state";
import { ReportStatusBadge } from "@/components/report/badges";
import { nctIdOf } from "@/components/report/labels";
import type { Report } from "@/components/report/types";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { buttonVariants } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiError, isUnreachable, itemsOf } from "@/lib/api";
import { formatDateTime, shortId } from "@/lib/format";
import { POLL_MS, useApi } from "@/lib/use-api";

/** Newest first. */
function newestFirst(reports: Report[]): Report[] {
  return [...reports].sort((a, b) => Date.parse(b.created_at ?? "") - Date.parse(a.created_at ?? "") || 0);
}

/**
 * The pending reports list (Story 2.4, narrowed): headline, trial, run, Slack
 * alert state, filed time and status badge. Pending first, newest first,
 * polling `GET /reports?status=pending` every 2 seconds like the top bar's
 * count; decided reports sit below under "Decided". Each row opens the report
 * page. No bulk actions and no filters; the decider is never chosen here.
 */
export function ReportsList() {
  const pending = useApi("/reports", { query: { status: "pending" }, interval: POLL_MS });
  const all = useApi("/reports", { interval: POLL_MS * 2.5 });

  if (!pending.data) {
    if (pending.isLoading) return <PageSkeleton rows={4} />;
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-title">Reports</h1>
        {isUnreachable(pending.error) ? (
          <ApiUnreachableNotice />
        ) : (
          <Notice icon={CircleAlert} title="The report list could not be loaded" role="alert">
            {pending.error instanceof ApiError && pending.error.status === 501
              ? "The reports route is not available yet."
              : (pending.error?.message ?? "The API answered, but not with a list of reports.")}
          </Notice>
        )}
      </div>
    );
  }

  const pendingReports = newestFirst(itemsOf(pending.data));
  const decided = newestFirst(itemsOf(all.data).filter((r) => r.status !== "pending"));
  const morePending = Boolean(pending.data.next);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <h1 className="text-title">Reports</h1>
        <p className="text-body m-0 text-muted-foreground">
          Research reports the agent filed. A report stays pending until it is approved or rejected in DxP.
        </p>
      </div>

      {pending.error ? (
        <Notice icon={CircleAlert} title="Couldn't refresh the list" role="status">
          {isUnreachable(pending.error) ? "The API did not answer. What is shown is the last copy read." : pending.error.message}
        </Notice>
      ) : null}

      <section aria-labelledby="pending-heading" className="flex flex-col gap-3">
        <h2 id="pending-heading" className="text-heading flex items-center gap-2">
          <FileSearch className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          Pending review
          <span className="text-identifier text-muted-foreground">
            ({pendingReports.length}
            {morePending ? "+" : ""})
          </span>
        </h2>
        {pendingReports.length === 0 ? (
          <Notice icon={Inbox} title="No reports are waiting for review" role="status">
            Start a scan in the Run console. A report the agent files appears here and in the Slack alert.
          </Notice>
        ) : (
          <ReportRows reports={pendingReports} caption="Reports pending review" />
        )}
        {morePending ? (
          <p className="text-caption m-0 text-muted-foreground">More pending reports exist than are listed here.</p>
        ) : null}
      </section>

      <section aria-labelledby="decided-heading" className="flex flex-col gap-3">
        <h2 id="decided-heading" className="text-heading">
          Decided
        </h2>
        {all.data === undefined ? (
          all.isLoading ? (
            <p className="text-body m-0 text-muted-foreground" role="status">
              Loading decided reports.
            </p>
          ) : (
            <p className="text-body m-0 text-muted-foreground" role="status">
              {isUnreachable(all.error)
                ? "Couldn't reach the API, so decided reports are not shown."
                : "Decided reports could not be loaded."}
            </p>
          )
        ) : decided.length === 0 ? (
          <p className="text-body m-0 text-muted-foreground">No report has been decided yet.</p>
        ) : (
          <ReportRows reports={decided} caption="Decided reports" />
        )}
      </section>

      <div>
        <Link href="/runs" className={buttonVariants({ variant: "outline" })}>
          Open the Run console
        </Link>
      </div>
    </div>
  );
}

function counts(r: Report): string {
  const related = `${r.related.length} related ${r.related.length === 1 ? "item" : "items"}`;
  const memories = `${r.memories_used.length} ${r.memories_used.length === 1 ? "memory" : "memories"} used`;
  return `${related}, ${memories}`;
}

/** A table from md up; stacked rows below that, so nothing scrolls sideways at 320px. Only one is ever in the accessibility tree. */
function ReportRows({ reports, caption }: { reports: Report[]; caption: string }) {
  return (
    <>
      <div className="hidden rounded-lg border border-border bg-card shadow-sm md:block">
        <Table>
          <caption className="sr-only">{caption}</caption>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Headline</TableHead>
              <TableHead scope="col">Trial</TableHead>
              <TableHead scope="col">Run</TableHead>
              <TableHead scope="col">Slack alert</TableHead>
              <TableHead scope="col">Filed</TableHead>
              <TableHead scope="col">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map((r) => (
              <TableRow key={r.id}>
                <TableCell className="max-w-md whitespace-normal align-top">
                  <Link href={`/reports/${encodeURIComponent(r.id)}`} className="text-table font-semibold underline underline-offset-2">
                    {r.headline}
                  </Link>
                  <span className="text-caption block text-muted-foreground">{counts(r)}</span>
                </TableCell>
                <TableCell className="text-identifier align-top">{r.nct_id ?? nctIdOf(r.source_ref) ?? r.source_ref}</TableCell>
                <TableCell className="align-top">
                  <Link href={`/runs/${encodeURIComponent(r.run_id)}`} className="text-identifier underline underline-offset-2">
                    {shortId(r.run_id)}
                  </Link>
                </TableCell>
                <TableCell className="whitespace-normal align-top">
                  <AlertState notification={r.notification} />
                </TableCell>
                <TableCell className="text-table align-top">{formatDateTime(r.created_at)}</TableCell>
                <TableCell className="align-top">
                  <ReportStatusBadge status={r.status} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <ul aria-label={caption} className="m-0 flex list-none flex-col gap-3 p-0 md:hidden">
        {reports.map((r) => (
          <li key={r.id} className="flex min-w-0 flex-col gap-2 rounded-lg border border-border bg-card p-4 shadow-sm">
            <Link href={`/reports/${encodeURIComponent(r.id)}`} className="text-table break-words font-semibold underline underline-offset-2">
              {r.headline}
            </Link>
            <span className="text-caption text-muted-foreground">{counts(r)}</span>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <ReportStatusBadge status={r.status} />
              <span className="text-identifier">{r.nct_id ?? nctIdOf(r.source_ref) ?? r.source_ref}</span>
            </div>
            <AlertState notification={r.notification} />
            <span className="text-caption text-muted-foreground">
              Filed {formatDateTime(r.created_at)} by run <span className="text-identifier">{shortId(r.run_id)}</span>
            </span>
          </li>
        ))}
      </ul>
    </>
  );
}
