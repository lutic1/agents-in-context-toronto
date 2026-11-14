import Link from "next/link";
import { CircleDashed, ShieldX, TriangleAlert } from "lucide-react";

import { Section } from "@/components/report/section";
import type { Report } from "@/components/report/types";

/** Uncertainties: what the agent cannot say, in the words the report carries (V34, V37). */
export function Uncertainties({ items }: { items: string[] }) {
  return (
    <Section id="uncertainties" icon={TriangleAlert} title="Uncertainties">
      {items.length === 0 ? (
        <p className="text-body m-0 text-muted-foreground">No uncertainties recorded.</p>
      ) : (
        <ul className="m-0 flex list-disc flex-col gap-2 pl-5">
          {items.map((u, i) => (
            <li key={i} className="text-body max-w-[75ch] break-words">
              {u}
            </li>
          ))}
        </ul>
      )}
    </Section>
  );
}

/** Evidence gap: one question the evidence does not yet answer (V26), in a dashed-edged card. */
export function EvidenceGap({ gap }: { gap: string }) {
  return (
    <section
      aria-labelledby="gap-heading"
      className="flex min-w-0 flex-col gap-2 rounded-md border border-dashed border-border bg-card p-5"
    >
      <h2 id="gap-heading" className="text-caption m-0 flex items-center gap-2 font-semibold">
        <CircleDashed className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
        Evidence gap
      </h2>
      <p className="text-body m-0 max-w-[75ch] break-words">{gap}</p>
    </section>
  );
}

/** How this report was drafted: one line when a draft claim was blocked before filing, linking to the audit. */
export function DraftNote({ report }: { report: Report }) {
  if (!report.blocked_draft_decision_id) return null;
  return (
    <section
      aria-labelledby="draft-heading"
      className="flex min-w-0 flex-col gap-1 rounded-md border border-border border-l-[3px] border-l-destructive bg-card p-5"
    >
      <h2 id="draft-heading" className="text-caption m-0 flex items-center gap-2 font-semibold">
        <ShieldX className="size-4 shrink-0 text-destructive" strokeWidth={1.75} aria-hidden="true" />
        How this report was drafted
      </h2>
      <p className="text-body m-0">
        1 draft claim was blocked before filing.{" "}
        <Link
          href={`/runs/${encodeURIComponent(report.run_id)}/audit#${encodeURIComponent(report.blocked_draft_decision_id)}`}
          className="underline underline-offset-2"
        >
          See the audit.
        </Link>
      </p>
      {report.draft === 2 ? <p className="text-caption m-0 text-muted-foreground">The filed text is the second draft.</p> : null}
    </section>
  );
}
