"use client";

import Link from "next/link";
import { CircleAlert, SearchX } from "lucide-react";

import { DecisionBar } from "@/components/report-decision";
import { MemoryPanel } from "@/components/memory-panel";
import { reportStatusWord } from "@/components/report/badges";
import { Discovery } from "@/components/report/discovery";
import { MemoriesUsed } from "@/components/report/memories-used";
import { ProposedUpdates } from "@/components/report/proposed-updates";
import { RecommendedTask } from "@/components/report/recommended-task";
import { RelatedEvidence } from "@/components/report/related-evidence";
import { ScriptPanel } from "@/components/report/script-panel";
import { DraftNote, EvidenceGap, Uncertainties } from "@/components/report/uncertainties";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { buttonVariants } from "@/components/ui/button";
import { ApiError, isUnreachable } from "@/lib/api";
import { features } from "@/lib/features";
import { POLL_MS, useApi } from "@/lib/use-api";
import AvatarPlayer from "@/app/reports/[report_id]/avatar/player";
import BriefingPlayer from "@/app/reports/[report_id]/briefing/player";

/** Quiet polling while a report is pending or accepted; fast while a decision is being applied. */
const IDLE_POLL_MS = 5000;

/**
 * The report page (Story 10.10): one pending research report read top to bottom,
 * the decisions area (builder 2) at the end of the main column and the memories
 * panel (builder 2) in the right-hand column. It renders only what
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

        <Discovery report={report} />

        {features.briefing || features.avatar ? (
          <section aria-label="Briefing and avatar video" className="grid min-w-0 gap-4 md:grid-cols-2 empty:hidden">
            {features.briefing ? <BriefingPlayer reportId={report.id} /> : null}
            {features.avatar ? <AvatarPlayer reportId={report.id} /> : null}
          </section>
        ) : null}

        <RelatedEvidence report={report} />
        <MemoriesUsed memories={report.memories_used} />
        <Uncertainties items={report.uncertainties} />
        <EvidenceGap gap={report.gap} />
        <DraftNote report={report} />
        <ProposedUpdates report={report} />
        <RecommendedTask report={report} />
        <ScriptPanel script={report.script} />

        <DecisionBar reportId={report.id} />
      </div>

      <div className="min-w-0">
        <MemoryPanel reportId={report.id} />
      </div>
    </div>
  );
}
