import type { Metadata } from "next";

import { ReportsList } from "@/components/report/reports-list";

export const metadata: Metadata = { title: "Reports" };

/** The pending reports list: a small table, pending first, decided reports below. */
export default function ReportsPage() {
  return <ReportsList />;
}
