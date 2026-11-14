import type { Metadata } from "next";

import { DiagnosticView } from "@/components/report/diagnostic-view";

export const metadata: Metadata = { title: "Accepted knowledge" };

/** The Accepted knowledge view of one Diagnostic (Story 1.3, narrowed): accepted values only, the target of the alert's "Open diagnostic" link. */
export default async function DiagnosticPage({ params }: PageProps<"/diagnostics/[dx_id]">) {
  const { dx_id } = await params;
  return <DiagnosticView dxId={dx_id} />;
}
