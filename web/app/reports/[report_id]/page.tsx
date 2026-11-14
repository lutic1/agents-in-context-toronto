import type { Metadata } from "next";

import { ReportView } from "@/components/report/report-view";

export const metadata: Metadata = { title: "Report" };

/**
 * The report page, the Slack alert's "Review in DxP" target. The report is read
 * in the browser through the proxy route so the page can poll while a decision
 * or the follow-up task is in flight; the key stays on the server.
 */
export default async function ReportPage({ params }: PageProps<"/reports/[report_id]">) {
  const { report_id } = await params;
  return <ReportView reportId={report_id} />;
}
