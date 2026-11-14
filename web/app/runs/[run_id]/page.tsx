import type { Metadata } from "next";
import { Suspense } from "react";

import { RunView } from "@/components/run-console/run-view";
import { PageSkeleton } from "@/components/shell/page-skeleton";

export const metadata: Metadata = { title: "Run console" };

/** One run in the Run console: identity card, stop control, source label and action feed. */
export default function RunPage({ params }: { params: Promise<{ run_id: string }> }) {
  return (
    <Suspense fallback={<PageSkeleton rows={3} />}>
      <OpenRun params={params} />
    </Suspense>
  );
}

async function OpenRun({ params }: { params: Promise<{ run_id: string }> }) {
  const { run_id } = await params;
  return <RunView runId={run_id} />;
}
