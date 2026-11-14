import type { Metadata } from "next";

import { InterviewView } from "./interview-view";

export const metadata: Metadata = { title: "Interview this evidence" };

/**
 * Interview this evidence (V70, `interview` flag): a question about an accepted report, answered only from its
 * own verbatim quotes. A supporting page; no other page depends on it.
 *
 * This page needs the response header `Permissions-Policy: microphone=()` (set for /reports/:report_id/interview
 * in B01's next.config.ts for every path, camera too) as the outermost layer of the avatar's microphone block. See avatar-adapter.ts.
 */
export default async function InterviewPage({ params }: PageProps<"/reports/[report_id]/interview">) {
  const { report_id } = await params;
  return <InterviewView reportId={report_id} />;
}
