"use client";

import Link from "next/link";
import { ChevronRight, CircleAlert, SearchX } from "lucide-react";

import { DecisionBar } from "@/components/report-decision";
import { MemoryPanel } from "@/components/memory-panel";
import { reportStatusWord } from "@/components/report/badges";
import { Discovery } from "@/components/report/discovery";
import { MemoriesUsed } from "@/components/report/memories-used";
import { ProposedUpdates } from "@/components/report/proposed-updates";
import { RecommendedTask } from "@/components/report/recommended-task";
import { RelatedEvidence } from "@/components/report/related-evidence";
import { ScriptPanel } from "@/components/report/script-panel";
import type { Report } from "@/components/report/types";
import { DraftNote, EvidenceGap, Uncertainties } from "@/components/report/uncertainties";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { buttonVariants } from "@/components/ui/button";
import { ApiError, isUnreachable, itemsOf } from "@/lib/api";
import { features } from "@/lib/features";
import { POLL_MS, useApi } from "@/lib/use-api";
import AvatarPlayer from "@/app/reports/[report_id]/avatar/player";
import { InterviewWorkspace } from "@/app/reports/[report_id]/interview/interview-view";
import BriefingPlayer from "@/app/reports/[report_id]/briefing/player";

/** Quiet polling while a report is pending or accepted; fast while a decision is being applied. */
const IDLE_POLL_MS = 5000;

/** The statuses the evidence guide shows for: pending or accepted, and the moves between them. */
const GUIDE_STATUSES = new Set<string>(["pending", "accepting", "accepted", "reverting"]);

/**
 * The report page (Story 10.10, V74): the evidence guide (typed questions and the
 * avatar, which starts only on "Engage") comes first, then the headline, the
 * decisions, the memories used, the blocked-check and follow-up task lines, all
 * open. Related evidence, uncertainties, quotes and source fields, proposed updates
 * and the briefing are collapsed with a one-line count. The memories panel stays in
 * the right-hand column. There is no voice input here: it lives only on the
 * interview page (V73). It renders only what
 * `GET /reports/<report_id>` returns and applies no display rule of its own.
 */
export function ReportView({ reportId }: { reportId: string }) {
  const route = "/reports/{report_id}" as const;
  const { data: report, error, isLoading } = useApi(route, {
    path: { report_id: reportId },
    interval: IDLE_POLL_MS,
  });

  // While an approval or a revert is being applied, read the same key every 2 seconds.
  const inFlight = report?.status === "accepting" || report?.status === "reverting";
  useApi(route, { path: { report_id: reportId }, interval: POLL_MS, enabled: inFlight });

  if (!report) {
    if (isLoading) return <PageSkeleton rows={5} />;
    if (error instanceof ApiError && error.status === 404) {
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">Report</h1>
          <Notice icon={SearchX} title="Report not found" role="status">
            Report not found. Open Reports to see what is pending.
          </Notice>
          <div>
            <Link href="/reports" className={buttonVariants({ variant: "default" })}>
              Open Reports
            </Link>
          </div>
        </div>
      );
    }
    if (error && isUnreachable(error)) {
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">Report</h1>
          <ApiUnreachableNotice />
        </div>
      );
    }
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-title">Report</h1>
        <Notice icon={CircleAlert} title="This report could not be loaded" role="alert">
          {error instanceof ApiError && error.status === 501
            ? "The report route is not available yet."
            : (error?.message ?? "The API answered, but not with a report.")}
        </Notice>
        <div>
          <Link href="/reports" className={buttonVariants({ variant: "default" })}>
            Open Reports
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="flex min-w-0 flex-col gap-6">
        {/* Status changes arrive by polling, so they are announced politely. */}
        <p className="sr-only" role="status" aria-live="polite">
          Report status: {reportStatusWord(report.status)}
        </p>
        {error ? (
          <Notice icon={CircleAlert} title="Couldn't refresh this report" role="status">
            {isUnreachable(error) ? "The API did not answer. What is shown is the last copy read." : error.message}
          </Notice>
        ) : null}

        {/* Kept mounted while a decision is applied (accepting, reverting) so Approve doesn't end the avatar session. */}
        {features.interview && GUIDE_STATUSES.has(report.status) ? (
          <section aria-labelledby="guide-heading" className="flex min-w-0 flex-col gap-3">
            <h2 id="guide-heading" className="text-heading">
              Ask the evidence guide
            </h2>
            <InterviewWorkspace reportId={report.id} stacked allowVoice subtitle={report.headline} />
          </section>
        ) : null}

        <Discovery report={report} part="header" />
        <DecisionBar reportId={report.id} />
        <MemoriesUsed memories={report.memories_used} />
        <DraftNote report={report} />
        <EvidenceGap gap={report.gap} />
        <RecommendedTask report={report} />

        <Collapsed title="Related evidence" summary={relatedSummary(report)}>
          <RelatedEvidence report={report} />
        </Collapsed>
        <Collapsed title="Uncertainties" summary={count(report.uncertainties.length, "uncertainty", "uncertainties")}>
          <Uncertainties items={report.uncertainties} />
        </Collapsed>
        <Collapsed title="Quotes and source fields" summary={count(report.discovery.quotes.length, "quote", "quotes")}>
          <Discovery report={report} part="details" />
        </Collapsed>
        <Collapsed title="Proposed updates" summary={<UpdatesCount reportId={report.id} />}>
          <ProposedUpdates report={report} />
        </Collapsed>
        {features.briefing || features.avatar ? (
          <Collapsed title="Briefing and avatar video" summary="Audio briefing and recorded video">
            <section aria-label="Briefing and avatar video" className="grid min-w-0 gap-4 md:grid-cols-2 empty:hidden">
              {features.briefing ? <BriefingPlayer reportId={report.id} /> : null}
              {features.avatar ? <AvatarPlayer reportId={report.id} /> : null}
            </section>
          </Collapsed>
        ) : null}
        <Collapsed title="Script" summary="The grounded script behind the briefing">
          <ScriptPanel script={report.script} />
        </Collapsed>

        {features.interview && (report.status === "pending" || report.status === "accepted") ? (
          // A plain <a>, not a Next <Link>: the interview page must load fully so the browser applies its own
          // Permissions-Policy (V73 allows the microphone only on the interview route).
          // eslint-disable-next-line @next/next/no-html-link-for-pages
          <a href={`/reports/${encodeURIComponent(report.id)}/interview`} className={buttonVariants({ variant: "default" }) + " self-start"}>
            Interview this evidence
          </a>
        ) : null}
      </div>

      <div className="min-w-0">
        <MemoryPanel reportId={report.id} />
      </div>
    </div>
  );
}

function count(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

function relatedSummary(report: Report): string {
  const n = report.related?.length ?? 0;
  const method = report.retrieval
    ? report.retrieval.method === "text_search"
      ? ", by text search"
      : ", by Vector Search"
    : "";
  return `${count(n, "related item", "related items")}${method}`;
}

/** The number of proposed updates, read from the same key the panel reads (deduplicated by the cache). */
function UpdatesCount({ reportId }: { reportId: string }) {
  const { data } = useApi("/proposals", { query: { report_id: reportId }, interval: 5000 });
  if (!data) return <>Proposed updates</>;
  const n = itemsOf(data).filter((p) => p.op === "add").length;
  return <>{count(n, "update", "updates")}</>;
}

/**
 * A section collapsed by default (V74): a keyboard-focusable <summary> with a one-line count, the section's
 * own content unchanged inside. The open state is the browser's, so polling never closes it.
 */
function Collapsed({ title, summary, children }: { title: string; summary: React.ReactNode; children: React.ReactNode }) {
  return (
    <details className="group min-w-0 rounded-lg border border-border bg-card">
      <summary className="flex cursor-pointer list-none items-center gap-2 rounded-lg px-5 py-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">
        <ChevronRight className="size-4 shrink-0 transition-transform group-open:rotate-90" strokeWidth={1.75} aria-hidden="true" />
        <span className="text-table font-semibold">{title}</span>
        <span className="text-caption text-muted-foreground">{summary}</span>
      </summary>
      <div className="flex min-w-0 flex-col gap-4 px-5 pb-5">{children}</div>
    </details>
  );
}
