"use client";

import { Brain, KeyRound, ListChecks, Undo2 } from "lucide-react";

import { AppLink, CopyId, Mono, PersonName, StatusPill } from "@/components/audit/common";
import { EmptyNote, MemoryStatusIcon } from "@/components/audit/entry-parts";
import { EntryShell, ReviewStatus, entryAnchor, type AuditContext } from "@/components/audit/audit-entry";
import {
  asLedgerResult,
  destinationName,
  failedCheckName,
  type AuditEntry,
  type Report,
  type Task,
} from "@/components/audit/labels";
import { Skeleton } from "@/components/ui/skeleton";
import { displayName, formatDateTime, formatGrant, formatTime } from "@/lib/format";
import { useApi } from "@/lib/use-api";

/**
 * "After the run": the Reviewer decisions caused by this run, in the same
 * timeline as the run's own entries (EXPERIENCE "After the run", AD-22). Each
 * is "Decided by Sam" with no agent. The words for the approval, the task
 * and a revert come from the report, task and proposal records the API
 * returns; nothing here decides what is accepted.
 */
export function AfterRunEntry({
  entry,
  position,
  ctx,
}: {
  entry: AuditEntry;
  position: number;
  ctx: AuditContext;
}) {
  const reviewer = entry.stamp?.principal ?? entry.stamp?.initiated_by ?? null;
  const verb = entry.kind === "resolve_notification" ? "Resolved by" : "Decided by";
  const reportId = entry.report_id ?? entry.cause?.report_id ?? null;

  return (
    <EntryShell
      entry={entry}
      position={position}
      ctx={ctx}
      who={
        <>
          {verb} {reviewer ? <PersonName id={reviewer} className="align-middle" /> : "a Reviewer"}. No agent acted.
          {entry.cause?.origin_run_id ? (
            <>
              {" "}
              Caused by run <Mono>{entry.cause.origin_run_id}</Mono>.
            </>
          ) : null}
        </>
      }
    >
      {entry.kind === "decide_report" ? <ApprovalBlock entry={entry} reportId={reportId} /> : null}
      {entry.kind === "authorise_task" ? <TaskAuthorisationBlock entry={entry} reportId={reportId} ctx={ctx} /> : null}
      {entry.kind === "revert_report" ? <RevertBlock entry={entry} reportId={reportId} ctx={ctx} /> : null}
      {entry.kind === "create_memory" || entry.kind === "correct_memory" || entry.kind === "revoke_memory" ? (
        <MemoryChangeBlock entry={entry} />
      ) : null}
      {entry.kind === "resolve_notification" ? <ResolveBlock entry={entry} ctx={ctx} /> : null}
      {reportId && entry.kind !== "decide_report" && entry.kind !== "authorise_task" && entry.kind !== "revert_report" ? (
        <p className="text-table">
          Report <AppLink href={`/reports/${encodeURIComponent(reportId)}`}>{reportId}</AppLink>
        </p>
      ) : null}
      {entry.cause?.action_id && entry.kind !== "resolve_notification" ? (
        <p className="text-table">
          Action <CopyId value={entry.cause.action_id} />
        </p>
      ) : null}
    </EntryShell>
  );
}

// ---- Loading and failure of the records an entry reads --------------------------

function Reading({ what }: { what: string }) {
  return <Skeleton className="h-5 w-64 max-w-full" role="status" aria-label={`Loading ${what}`} />;
}

function Unavailable({ what, error }: { what: string; error: Error }) {
  return (
    <p className="text-table text-muted-foreground" role="status">
      {what} could not be read: {error.message}
    </p>
  );
}

// ---- The report decision ----------------------------------------------------------

/**
 * The words of an approval (V27, V38, V62), from the report's own approval
 * record and its task:
 *  - the task is authorised and queued or started: "...its findings will be pending review.";
 *  - authorised and never queued (task execution off): "...authorised; not run.";
 *  - blocked at authorisation: "Follow-up task not authorised: <reason>" (V62).
 */
export function approvalSentence(report: Report, task: Task | null): string {
  const count = report.proposal_ids.length;
  const base = count > 1 ? `Approved: ${count} updates accepted.` : "Approved: 1 update accepted.";
  const approval = report.approval;
  if (approval?.task_step === "blocked") {
    return `${base} Follow-up task not authorised: ${approval.reason ?? "no reason recorded"}.`;
  }
  if (task) {
    switch (task.status) {
      case "authorised":
        return `${base} Follow-up task authorised; not run.`;
      case "queued":
      case "running":
      case "done":
        return `${base} Follow-up task authorised; its findings will be pending review.`;
      default:
        return `${base} ${taskStateLine(task)}`;
    }
  }
  return `${base} The follow-up task authorisation is still being completed.`;
}

/** A rejected report: nothing was accepted and no task was authorised (EXPERIENCE "Reject"). */
function rejectionSentence(report: Report, entry: AuditEntry): string {
  const by = displayName(report.decided_by ?? entry.report_review?.decided_by ?? entry.stamp?.principal ?? "the Reviewer");
  const at = report.decided_at ?? entry.report_review?.decided_at ?? entry.decided_at;
  return `Report rejected by ${by}${at ? ` at ${formatTime(at)}` : ""}. No update was accepted. No follow-up task was authorised.`;
}

function ApprovalBlock({ entry, reportId }: { entry: AuditEntry; reportId: string | null }) {
  const report = useApi("/reports/{report_id}", {
    path: { report_id: reportId ?? "" },
    enabled: Boolean(reportId) && entry.outcome === "allowed",
  });
  const taskId = report.data?.task_id ?? entry.task_id ?? null;
  const task = useApi("/tasks/{task_id}", { path: { task_id: taskId ?? "" }, enabled: Boolean(taskId) });

  if (entry.outcome === "blocked") return <p className="text-body">No report was accepted.</p>;
  if (!reportId) return null;

  return (
    <div className="flex flex-col gap-2">
      {report.data ? (
        <>
          <p className="text-body font-semibold">
            {report.data.status === "rejected" || (!report.data.approval && entry.report_review?.status === "rejected")
              ? rejectionSentence(report.data, entry)
              : approvalSentence(report.data, task.data ?? null)}
          </p>
          {report.data.status === "rejected" && report.data.note ? (
            <p className="text-table">Note: {report.data.note}</p>
          ) : null}
        </>
      ) : report.error ? (
        <Unavailable what="The report" error={report.error} />
      ) : (
        <Reading what="the report decision" />
      )}
      {entry.decided_at ? (
        <p className="text-table text-muted-foreground">
          {report.data?.status === "rejected" ? "Decided" : "Accepted"} by {displayName(entry.stamp?.principal ?? "the Reviewer")} at{" "}
          {formatDateTime(entry.decided_at)}
        </p>
      ) : null}
      {entry.report_review ? (
        <ReviewStatus
          label="Report"
          status={entry.report_review.status}
          by={entry.report_review.decided_by}
          at={entry.report_review.decided_at}
        />
      ) : null}
      <p className="text-table">
        Report <AppLink href={`/reports/${encodeURIComponent(reportId)}`}>{reportId}</AppLink>
      </p>
    </div>
  );
}

// ---- The task authorisation ------------------------------------------------------

/** The task's state in words (EXPERIENCE "Follow-up task"), from the task record. */
function taskStateLine(task: Task): string {
  switch (task.status) {
    case "authorised":
      return "Follow-up task authorised; not run.";
    case "queued":
      return "Queued: starts by itself when the current run ends. Its findings will be pending review.";
    case "running":
      return "Running. Its findings will be pending review.";
    case "done":
      return "Done.";
    case "failed":
      return "Failed: the task's run was abandoned. Not restarted.";
    case "blocked":
      return "Blocked before it ran.";
    case "stopped":
      return "Stopped.";
    case "cancelled":
      return "Cancelled: the approval was reverted. Its grant expired.";
  }
}

function TaskAuthorisationBlock({
  entry,
  reportId,
  ctx,
}: {
  entry: AuditEntry;
  reportId: string | null;
  ctx: AuditContext;
}) {
  const report = useApi("/reports/{report_id}", {
    path: { report_id: reportId ?? "" },
    enabled: Boolean(reportId) && entry.outcome === "blocked",
  });

  if (entry.outcome === "blocked") {
    const reason = report.data?.approval?.reason ?? entry.checks.find((c) => c.passed === false)?.detail ?? null;
    return (
      <div className="flex flex-col gap-1">
        <p className="text-body font-semibold">Follow-up task not authorised{reason ? `: ${reason}` : ""}.</p>
        <p className="text-table text-muted-foreground">The evidence stays accepted. No task and no start button.</p>
      </div>
    );
  }

  const taskId = entry.task_id ?? asLedgerResult(entry.result)?.task_id ?? null;
  if (!taskId) return <EmptyNote>No task is linked to this authorisation.</EmptyNote>;
  return <TaskDetail taskId={taskId} entry={entry} ctx={ctx} />;
}

function TaskDetail({ taskId, entry, ctx }: { taskId: string; entry: AuditEntry; ctx: AuditContext }) {
  const task = useApi("/tasks/{task_id}", { path: { task_id: taskId } });
  const t = task.data;
  const grant = useApi("/grants/{grant_id}", {
    path: { grant_id: t?.grant_id ?? "" },
    query: { version: t?.grant_version ?? 1 },
    enabled: Boolean(t),
  });

  if (task.error && !t) return <Unavailable what="The task" error={task.error} />;
  if (!t) return <Reading what="the task" />;

  const linked = ctx.audit.linked_runs.find((r) => r.task_id === t.id);
  const runId = linked?.run_id ?? t.run_id;
  const ran = Boolean(runId) && t.status !== "authorised";
  const result = t.result;

  return (
    <div className="flex flex-col gap-3">
      <p className="text-body font-semibold">
        Task authorised by {displayName(entry.stamp?.principal ?? "the Reviewer")}
        {entry.decided_at ? ` at ${formatTime(entry.decided_at)}` : ""}.
      </p>
      <dl className="grid grid-cols-1 gap-x-4 gap-y-1 text-table sm:grid-cols-[max-content_minmax(0,1fr)]">
        <dt className="text-caption text-muted-foreground">Gap it answers</dt>
        <dd>{t.question}</dd>
        <dt className="text-caption text-muted-foreground">Task</dt>
        <dd>
          <CopyId value={t.id} />
        </dd>
        <dt className="text-caption text-muted-foreground">Runs under grant</dt>
        <dd className="flex flex-wrap items-center gap-x-2">
          <KeyRound className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          <Mono>{formatGrant(t.grant_id, t.grant_version)}</Mono>
          {grant.data?.expires_at ? <span>, expires {formatTime(grant.data.expires_at)}</span> : null}
        </dd>
        <dt className="text-caption text-muted-foreground">Limit</dt>
        <dd>Search and file related evidence only, same scope, at most {t.params.max}.</dd>
      </dl>

      <p className="flex items-center gap-1.5 text-table font-semibold">
        <ListChecks className="size-4" strokeWidth={1.75} aria-hidden="true" />
        {taskStateLine(t)}
      </p>

      {result ? (
        <div className="flex flex-col gap-1 text-table">
          <p>{result.answer}</p>
          <p className="text-muted-foreground">
            Query: <Mono>{typeof result.query === "string" ? result.query : JSON.stringify(result.query)}</Mono>.{" "}
            {result.searched_count} records searched; limit {result.limit}.
          </p>
          {result.related_ids.length > 0 ? (
            <>
              <p>
                {result.related_ids.length} related {result.related_ids.length === 1 ? "item" : "items"} filed.
              </p>
              <ul className="flex flex-col gap-1">
                {result.related_ids.map((id) => (
                  <li key={id} className="flex flex-wrap items-center gap-2">
                    <Mono>{id}</Mono>
                    <StatusPill status="pending" />
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}

      {ran && runId ? (
        <LinkedRunLine runId={runId} />
      ) : (
        <p className="text-table text-muted-foreground">
          {t.status === "authorised" ? "Authorised, not run: no task run exists." : "No task run is linked yet."}
        </p>
      )}
    </div>
  );
}

/** "Follow-up task run run_…: 2 allowed, 1 blocked. Open audit" */
function LinkedRunLine({ runId }: { runId: string }) {
  const run = useApi("/runs/{run_id}", { path: { run_id: runId } });
  const counts = run.data?.counts;
  return (
    <p className="text-table">
      Follow-up task run <Mono>{runId}</Mono>
      {counts ? `: ${counts.allowed} allowed, ${counts.blocked} blocked` : ""}.{" "}
      <AppLink href={`/runs/${encodeURIComponent(runId)}/audit`}>Open audit</AppLink>
    </p>
  );
}

// ---- A revert (V48) --------------------------------------------------------------

function RevertBlock({
  entry,
  reportId,
  ctx,
}: {
  entry: AuditEntry;
  reportId: string | null;
  ctx: AuditContext;
}) {
  const blocked = entry.outcome === "blocked";
  const report = useApi("/reports/{report_id}", {
    path: { report_id: reportId ?? "" },
    enabled: Boolean(reportId) && !blocked,
  });
  const taskId = report.data?.task_id ?? entry.task_id ?? null;
  const task = useApi("/tasks/{task_id}", { path: { task_id: taskId ?? "" }, enabled: Boolean(taskId) && !blocked });

  if (blocked) {
    return (
      <p className="text-body font-semibold">
        Revert blocked: {failedCheckName(entry)} failed. Nothing changed.
      </p>
    );
  }

  const revert = report.data?.revert ?? null;
  const proposalIds = asLedgerResult(entry.result)?.proposal_ids ?? [];
  // How many updates came out: the reverse proposals the revert filed, else the report's own list.
  const removed = proposalIds.length > 0 ? proposalIds.length : (report.data?.proposal_ids.length ?? 0);
  const by = displayName(revert?.by ?? entry.stamp?.principal ?? "the Reviewer");
  const at = revert?.at ?? entry.decided_at;
  const slack = ctx.audit.entries.filter(
    (e) => e.kind === "notify_slack" && (e.report_id ?? null) === reportId && e.status === "delivered",
  );

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <StatusPill status="reverted" />
        <p className="text-body font-semibold">
          Approval reverted by {by}
          {at ? ` at ${formatTime(at)}` : ""}
          {removed > 0
            ? `: ${removed} ${removed === 1 ? "update" : "updates"} removed from accepted knowledge.`
            : "."}
        </p>
      </div>
      {revert?.note ? <p className="text-table">Note: {revert.note}</p> : null}
      <p className="text-table text-muted-foreground">
        The original approval stays in this list, unchanged. Nothing is deleted.
      </p>

      {proposalIds.length > 0 ? (
        <ul className="flex flex-col gap-1">
          {proposalIds.map((id) => (
            <li key={id}>
              <ReverseProposal proposalId={id} />
            </li>
          ))}
        </ul>
      ) : null}

      {taskId ? (
        task.data ? (
          <p className="text-table">{revertedTaskLine(task.data)}</p>
        ) : task.error ? (
          <Unavailable what="The follow-up task" error={task.error} />
        ) : (
          <Reading what="the follow-up task" />
        )
      ) : null}

      {slack.map((s) => {
        const posted = asSlackPostedAt(s);
        return (
          <p key={s.decision_id} className="text-table">
            Slack alert{" "}
            {s.action_id ? <CopyId value={s.action_id} /> : null} to {destinationName(s.destination)}: still delivered
            {posted ? ` (posted ${formatTime(posted)})` : ""}. A sent alert stays sent; the audit records it.
          </p>
        );
      })}
      {reportId ? (
        <p className="text-table">
          Report <AppLink href={`/reports/${encodeURIComponent(reportId)}`}>{reportId}</AppLink>
        </p>
      ) : null}
    </div>
  );
}

function asSlackPostedAt(entry: AuditEntry): string | null {
  const result = entry.result;
  return result && "posted_at" in result ? result.posted_at : null;
}

/** What happened to the follow-up task when the approval was reverted (EXPERIENCE "Revert approval"). */
function revertedTaskLine(task: Task): string {
  switch (task.status) {
    case "cancelled":
      return "Follow-up task cancelled; its grant expired.";
    case "running":
    case "stopped":
      return "Follow-up task stop requested.";
    case "done":
      return "Follow-up task had finished; its findings stay pending review.";
    default:
      return `Follow-up task is ${task.status}.`;
  }
}

function ReverseProposal({ proposalId }: { proposalId: string }) {
  const proposal = useApi("/proposals/{p_id}", { path: { p_id: proposalId } });
  const p = proposal.data;
  if (proposal.error && !p) {
    return (
      <p className="text-table">
        Proposal <Mono>{proposalId}</Mono>
      </p>
    );
  }
  if (!p) return <Reading what="the reverse proposal" />;
  const reverse = p.op === "remove";
  return (
    <p className="flex flex-wrap items-center gap-x-2 text-table">
      <Undo2 className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
      <span>{reverse ? "Reverse proposal" : "Proposal"}</span>
      <Mono>{p.id}</Mono>
      <span>
        {reverse ? "removes" : "adds"} <Mono>{p.field}</Mono> <Mono>{p.value}</Mono>
      </span>
      {p.reverts_proposal_id ? (
        <span>
          (reverts <Mono>{p.reverts_proposal_id}</Mono>)
        </span>
      ) : null}
    </p>
  );
}

// ---- Memory changes ----------------------------------------------------------------

function MemoryChangeBlock({ entry }: { entry: AuditEntry }) {
  const memoryId = entry.memory_id ?? entry.cause?.memory_id ?? asLedgerResult(entry.result)?.memory_id ?? null;
  const memory = useApi("/memories/{memory_id}", {
    path: { memory_id: memoryId ?? "" },
    enabled: Boolean(memoryId) && entry.outcome === "allowed",
  });
  if (entry.outcome === "blocked") return <p className="text-body">No memory changed.</p>;
  if (!memoryId) return null;
  const m = memory.data;
  const sentence =
    entry.kind === "create_memory"
      ? `Memory ${memoryId} created.`
      : entry.kind === "correct_memory"
        ? `Memory ${memoryId} corrected${m ? ` (now version ${m.version})` : ""}.`
        : `Memory ${memoryId} revoked. It will not be used again.`;
  return (
    <div className="flex flex-col gap-1">
      <p className="flex flex-wrap items-center gap-x-2 text-body font-semibold">
        <Brain className="size-4" strokeWidth={1.75} aria-hidden="true" />
        {sentence}
      </p>
      {m ? (
        <div className="flex flex-col gap-1 text-table">
          <p>
            <span className="text-caption font-semibold text-muted-foreground">Text </span>
            {m.text}
          </p>
          <p className="flex flex-wrap items-center gap-x-3 text-muted-foreground">
            <PersonName id={m.author} />
            <span className="inline-flex items-center gap-1">
              <MemoryStatusIcon status={m.status} />
              {m.status === "active" ? "Active" : m.status === "corrected" ? "Corrected" : "Revoked"} v{m.version}
            </span>
            {m.tags.claim_kind ? <Mono>{m.tags.claim_kind}</Mono> : null}
          </p>
        </div>
      ) : memory.error ? (
        <Unavailable what="The memory" error={memory.error} />
      ) : (
        <Reading what="the memory" />
      )}
      <p className="text-caption text-muted-foreground">Memories inform the agent&apos;s wording. They never change permissions.</p>
    </div>
  );
}

// ---- Resolving a Slack alert -------------------------------------------------------

function ResolveBlock({ entry, ctx }: { entry: AuditEntry; ctx: AuditContext }) {
  const actionId = entry.cause?.action_id ?? null;
  const alert = actionId ? ctx.audit.entries.find((e) => e.action_id === actionId) : undefined;
  const resolution = alert?.resolution ?? null;
  return (
    <div className="flex flex-col gap-1 text-table">
      {actionId ? (
        <p>
          Slack alert <CopyId value={actionId} />
          {alert ? (
            <>
              {" "}
              (<a className="underline underline-offset-2" href={`#${entryAnchor(alert.decision_id)}`}>see its entry</a>)
            </>
          ) : null}
        </p>
      ) : null}
      {resolution ? (
        <p>
          Recorded as {resolution.outcome === "delivered" ? "delivered" : "failed"} at {formatTime(resolution.at)}. Note:{" "}
          {resolution.note}
        </p>
      ) : (
        <p className="text-muted-foreground">The outcome is recorded on the alert&apos;s entry.</p>
      )}
    </div>
  );
}
