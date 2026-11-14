import type { Metadata } from "next";

import { AuditView } from "@/components/audit/audit-view";

export const metadata: Metadata = { title: "Audit" };

/**
 * `/runs/[run_id]/audit` (Story 9.8, B03). The page only names the run; the
 * view reads and polls the audit in the browser through the key-adding proxy.
 */
export default async function AuditPage({ params }: { params: Promise<{ run_id: string }> }) {
  const { run_id } = await params;
  return <AuditView runId={run_id} />;
}
