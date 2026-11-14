"use client";

import { totals } from "@/components/run-console/entry-state";
import { StopControl } from "@/components/run-console/stop-control";
import type { AuditEntry, Run } from "@/components/run-console/types";

/**
 * What the run did, first on the page: the three totals as large tabular figures,
 * then the stop control with the run's status words. The setup details (agent,
 * grant, policy set) sit lower down in the identity card.
 */
export function OutcomeSummary({ run, entries }: { run: Run; entries: AuditEntry[] | undefined }) {
  const t = entries ? totals(entries) : null;
  const stats = [
    { label: "Took effect", value: t?.tookEffect },
    { label: "Blocked", value: t?.blocked },
    { label: "Unknown", value: t?.unknown },
  ];

  return (
    <section aria-label="Outcome" className="flex flex-col gap-4 rounded-lg bg-card p-5 shadow-sm">
      <dl className="grid grid-cols-3 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="flex flex-col gap-1">
            <dt className="text-caption text-muted-foreground">{s.label}</dt>
            {/* Fixed line height and tabular figures, so the row never shifts as counts arrive. */}
            <dd className="text-display tabular-nums text-foreground">{s.value ?? "–"}</dd>
          </div>
        ))}
      </dl>
      <div className="border-t border-border pt-4">
        <StopControl run={run} entries={entries} />
      </div>
    </section>
  );
}
