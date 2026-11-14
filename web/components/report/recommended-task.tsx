import { ListChecks } from "lucide-react";

import { Section } from "@/components/report/section";
import type { Report } from "@/components/report/types";

/**
 * Recommended task (EXPERIENCE "Recommended task"): one research task as a
 * sentence that answers the evidence gap, with its limits in plain words. There
 * is no start button anywhere (V38): when task execution is on, approval queues
 * the task and it starts by itself; otherwise it reads "authorised; not run".
 * The task's state after a decision (queued, running, done, blocked, cancelled),
 * its answer and the decision line belong to the decisions area below this panel.
 */
export function RecommendedTask({ report }: { report: Report }) {
  const task = report.recommended_task;
  const pending = report.status === "pending";

  return (
    <Section id="task" icon={ListChecks} title="Recommended task">
      {task ? (
        <>
          <p className="text-body m-0 max-w-[75ch]">{taskSentence(task.params)}</p>
          <p className="text-caption m-0 text-muted-foreground">
            It answers the evidence gap: <span className="text-foreground">{report.gap}</span>
          </p>
          <p className="text-caption m-0 text-muted-foreground">
            Runs under its own grant after approval: search and file related evidence only, same scope, max{" "}
            {task.params.max}, expires one hour after approval.
          </p>
          {pending ? <p className="text-body m-0 text-muted-foreground">Recommended. Runs only if approved.</p> : null}
        </>
      ) : (
        <p className="text-body m-0 text-muted-foreground">This report recommends no follow-up task.</p>
      )}
    </Section>
  );
}

function taskSentence(p: NonNullable<Report["recommended_task"]>["params"]): string {
  const stage = p.stage ? `${p.stage}-stage ` : "";
  const testing = p.testing.length > 0 ? ` that combine ${p.testing.join(" and ")}` : "";
  const results = p.has_results ? ", and report which have posted results" : "";
  return `Search ClinicalTrials.gov for ${stage}${p.condition} trials${testing}${results} (at most ${p.max}).`;
}
