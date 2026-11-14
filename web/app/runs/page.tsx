import type { Metadata } from "next";

import { RunList } from "@/components/run-console/run-list";
import { StartRun } from "@/components/run-console/start-run";

export const metadata: Metadata = { title: "Run console" };

/** The Run console: start a discovery scan, then see every run. `/` opens the latest one. */
export default function RunsPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">Run console</h1>

      <section aria-labelledby="start-heading" className="rounded-lg border border-border bg-card p-5 shadow-sm">
        <h2 id="start-heading" className="text-heading">
          Start a scan
        </h2>
        <p className="mb-4 mt-1 text-body text-muted-foreground">
          The agent looks for trials updated since the research scope&apos;s last scan and files what it finds as a
          pending report. Nothing is accepted until you approve it.
        </p>
        <StartRun />
      </section>

      <section aria-labelledby="runs-heading" className="flex flex-col gap-3">
        <h2 id="runs-heading" className="text-heading">
          Runs
        </h2>
        <RunList />
      </section>
    </div>
  );
}
