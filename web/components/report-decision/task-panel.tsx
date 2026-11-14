"use client";

import Link from "next/link";
import {
  CircleCheck,
  CircleSlash,
  Clock,
  KeyRound,
  ListChecks,
  OctagonX,
  Play,
  ShieldX,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";

import { formatGrant } from "@/lib/format";
import { POLL_MS, useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

import { clock, whoAndWhen, type Report, type Task } from "./format";
import { StatusPill } from "./status-pill";

/**
 * The follow-up task read by ID, polled while it is queued or running. There
 * is no start button anywhere (V38): approval authorises the task, the
 * backend queues and starts it, and this only says where it is.
 */
export function useTask(taskId: string | null | undefined) {
  const query = useApi("/tasks/{task_id}", {
    path: { task_id: taskId ?? "" },
    enabled: Boolean(taskId),
  });
  const live = query.data?.status === "queued" || query.data?.status === "running";
  // A second hook instance on the same key, only to turn polling on while the task is live.
  useApi("/tasks/{task_id}", {
    path: { task_id: taskId ?? "" },
    enabled: Boolean(taskId) && live,
    interval: POLL_MS,
  });
  return query;
}

type View = { icon: LucideIcon; label: string; tone: string };

const VIEWS: Record<Task["status"], View> = {
  authorised: { icon: KeyRound, label: "Authorised", tone: "text-foreground" },
  queued: { icon: Clock, label: "Queued", tone: "text-muted-foreground" },
  running: { icon: Play, label: "Running", tone: "text-muted-foreground" },
  done: { icon: CircleCheck, label: "Done", tone: "text-accepted" },
  failed: { icon: TriangleAlert, label: "Failed", tone: "text-destructive" },
  blocked: { icon: ShieldX, label: "Blocked", tone: "text-destructive" },
  stopped: { icon: OctagonX, label: "Stopped", tone: "text-foreground" },
  cancelled: { icon: CircleSlash, label: "Cancelled", tone: "text-muted-foreground" },
};

function queryText(query: string | { [key: string]: unknown }): string {
  return typeof query === "string" ? query : JSON.stringify(query);
}

/** The task's state in words, with its answer when it has one (V42). */
export function TaskPanel({ report, taskId }: { report: Report; taskId: string }) {
  const { data: task, error, isLoading } = useTask(taskId);

  if (isLoading && !task) {
    return <Skeleton className="h-16 w-full" role="status" aria-label="Loading the follow-up task" />;
  }
  if (!task) {
    return (
      <p className="text-caption text-muted-foreground" role={error ? "alert" : undefined}>
        {error ? "The follow-up task could not be read right now." : "The follow-up task is not available yet."}
      </p>
    );
  }

  const view = VIEWS[task.status];
  const Icon = view.icon;
  const result = task.result;
  const blocked = task.status === "blocked";

  return (
    <section
      aria-labelledby={`task-${task.id}`}
      className={cn(
        "rounded-md border border-border bg-card p-3",
        blocked && "border-l-[3px] border-l-destructive",
        task.status === "queued" && "opacity-95",
      )}
    >
      <h3 id={`task-${task.id}`} className="flex flex-wrap items-center gap-2 text-body font-semibold">
        <Icon className={cn("size-4", view.tone)} strokeWidth={1.75} aria-hidden="true" />
        <span>Follow-up task</span>
        <span className={cn("text-caption font-medium", view.tone)}>{view.label}</span>
      </h3>

      {/* Polite live region: task status announces without taking focus. */}
      <div role="status" aria-live="polite" className="mt-1 flex flex-col gap-1.5 text-body">
        {task.status === "authorised" ? (
          <p>
            Authorised{report.approval?.reviewer ? ` by ${whoAndWhen(report.approval.reviewer, task.created_at)}` : ""}.
            Follow-up task authorised; not run.
          </p>
        ) : null}
        {task.status === "queued" ? (
          <p>
            Queued: starts by itself when the current run ends. Its findings will be pending review.
          </p>
        ) : null}
        {task.status === "running" ? (
          <p>
            Running, at most {task.params.max} findings.{" "}
            {task.run_id ? (
              <Link href={`/runs/${encodeURIComponent(task.run_id)}`} className="underline underline-offset-2">
                Open the task&apos;s run
              </Link>
            ) : null}
          </p>
        ) : null}
        {blocked ? (
          <p>
            Blocked before it ran.{" "}
            {task.run_id ? (
              <Link href={`/runs/${encodeURIComponent(task.run_id)}/audit`} className="underline underline-offset-2">
                See the blocked decision in the audit
              </Link>
            ) : null}
          </p>
        ) : null}
        {task.status === "failed" ? (
          <p>
            {task.error === "abandoned"
              ? "Failed: the task's run was abandoned. Not restarted."
              : "Failed. Not restarted."}{" "}
            Anything it filed stays pending review.
          </p>
        ) : null}
        {task.status === "stopped" ? (
          <p>
            Stopped. Anything it filed stays pending review.{" "}
            {task.run_id ? (
              <Link href={`/runs/${encodeURIComponent(task.run_id)}`} className="underline underline-offset-2">
                Open the task&apos;s run
              </Link>
            ) : null}
          </p>
        ) : null}
        {task.status === "cancelled" ? (
          <p>
            Cancelled
            {report.reverted_by
              ? `: the approval was reverted by ${whoAndWhen(report.reverted_by, report.reverted_at)}`
              : ""}
            . Its grant expired.
          </p>
        ) : null}
        {task.status === "done" ? (
          <p>
            Done.{" "}
            {result
              ? result.with_posted_results.length > 0
                ? `${result.with_posted_results.length} related items filed (pending review).`
                : result.answer || "No matching results found among the records searched."
              : "Its findings are pending review."}
          </p>
        ) : null}
      </div>

      {task.status === "done" && result ? (
        <div className="mt-2 flex flex-col gap-2 text-caption text-muted-foreground">
          {result.with_posted_results.length > 0 ? (
            <>
              <p className="text-foreground">{result.answer}</p>
              <ul className="flex flex-wrap gap-2" aria-label="Trials with posted results, pending review">
                {result.with_posted_results.map((nct) => (
                  <li key={nct} className="flex items-center gap-2">
                    <a
                      href={`https://clinicaltrials.gov/study/${encodeURIComponent(nct)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-identifier underline underline-offset-2"
                    >
                      {nct}
                      <span className="sr-only"> (opens ClinicalTrials.gov in a new tab)</span>
                    </a>
                    <StatusPill status="pending" />
                  </li>
                ))}
              </ul>
            </>
          ) : null}
          <p>
            Query: <span className="text-identifier break-words">{queryText(result.query)}</span>.{" "}
            {result.searched_count} records searched; limit {result.limit}.
          </p>
        </div>
      ) : null}

      <dl className="mt-3 grid gap-x-4 gap-y-1 text-caption text-muted-foreground sm:grid-cols-[auto_1fr]">
        <dt className="inline-flex items-center gap-1">
          <ListChecks className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          Question
        </dt>
        <dd className="text-foreground">{task.question}</dd>
        <dt>Grant</dt>
        <dd className="text-identifier text-foreground break-all">{formatGrant(task.grant_id, task.grant_version)}</dd>
        {task.queued_at ? (
          <>
            <dt>Queued at</dt>
            <dd className="text-identifier text-foreground">{clock(task.queued_at)}</dd>
          </>
        ) : null}
      </dl>
    </section>
  );
}
