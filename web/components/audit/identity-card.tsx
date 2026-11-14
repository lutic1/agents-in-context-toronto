"use client";

import { CircleCheck, CirclePause, CircleX, OctagonX, Play, ScrollText, type LucideIcon } from "lucide-react";

import { AppLink, CapabilityTag, CopyId, Mono, PersonName } from "@/components/audit/common";
import type { Audit, Run } from "@/components/audit/labels";
import { formatDate, formatGrant, formatPolicySet, formatTime } from "@/lib/format";
import { useApi } from "@/lib/use-api";

/**
 * The identity card at the top of the Audit view (EXPERIENCE "Identity card"):
 * two identities, never merged. The agent that executed, and the principal who
 * started it. Also the run, grant, policy set, scan cursor and status. Nothing
 * here is editable; identifiers are copyable.
 */
export function IdentityCard({ audit }: { audit: Audit }) {
  const { run, policies } = audit;
  const grant = useApi("/grants/{grant_id}", {
    path: { grant_id: run.grant_id },
    query: { version: run.grant_version },
  });
  const status = runStatus(run);
  const StatusIcon = status.icon;

  return (
    <section
      aria-labelledby="identity-heading"
      className="rounded-lg border border-border bg-card p-5 shadow-sm"
    >
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h2 id="identity-heading" className="flex items-center gap-2 text-heading">
          <ScrollText className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {run.kind === "task" ? "Follow-up task run" : "Run"}
        </h2>
        <p className="flex items-center gap-1.5 text-table font-semibold" role="status" aria-live="polite">
          <StatusIcon className="size-4" strokeWidth={1.75} aria-hidden="true" />
          {status.text}
        </p>
      </div>

      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-[max-content_minmax(0,1fr)]">
        <Row label="Agent">
          <Mono>{run.agent}</Mono>
          {run.model ? (
            <>
              {" "}
              <span className="text-muted-foreground">model</span> <Mono>{run.model}</Mono>
            </>
          ) : null}
        </Row>
        <Row label="Started by">
          <PersonName id={run.initiated_by} />
        </Row>
        <Row label="Run">
          <CopyId value={run.id} />
          <span className="text-muted-foreground">
            {" "}
            <AppLink href={`/runs/${encodeURIComponent(run.id)}`}>Open in the Run console</AppLink>
          </span>
        </Row>
        {run.prompt_version ? (
          <Row label="Prompt version">
            <Mono>{run.prompt_version}</Mono>
          </Row>
        ) : null}
        <Row label="Grant">
          <CopyId value={formatGrant(run.grant_id, run.grant_version)} />
          {grant.data ? (
            <span className="block text-table text-muted-foreground">
              {grant.data.team_name ? `Team ${grant.data.team_name}` : null}
              {grant.data.team_name && grant.data.scope_name ? ", " : null}
              {grant.data.scope_name ? grant.data.scope_name : null}
            </span>
          ) : null}
        </Row>
        {run.policy_set_version ? (
          <Row label="Policy set">
            <Mono>{formatPolicySet(run.policy_set_version, policies.length)}</Mono>{" "}
            <CapabilityTag
              name="Schema validation"
              sentence="Grants and policies are checked by $jsonSchema validation in Atlas, so a malformed grant can't be saved."
            />
          </Row>
        ) : null}
        {run.scan ? (
          <Row label="Scan cursor">
            {run.scan.cursor_from
              ? `${run.status === "running" || run.status === "stopping" ? "Scanning" : "Scanned"} trials updated since ${formatDate(run.scan.cursor_from)}`
              : "Scan cursor not recorded"}
            {run.scan.cursor_to ? `. Cursor after the scan: ${formatDate(run.scan.cursor_to)}` : null}
          </Row>
        ) : null}
        {run.kind === "task" && run.task_id ? <TaskRows taskId={run.task_id} /> : null}
        {run.failures.length > 0 ? (
          <Row label="Failed items">
            <ul className="flex flex-col gap-1">
              {run.failures.map((f) => (
                <li key={`${f.source_ref}-${f.error}`} className="text-table">
                  <Mono>{f.source_ref}</Mono>: {f.error}
                </li>
              ))}
            </ul>
          </Row>
        ) : null}
      </dl>
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="contents">
      <dt className="text-caption text-muted-foreground sm:pt-0.5">{label}</dt>
      <dd className="min-w-0 text-body">{children}</dd>
    </div>
  );
}

/** A task run adds "Follow-up task for report {id}" with a link back, and who authorised it. */
function TaskRows({ taskId }: { taskId: string }) {
  const task = useApi("/tasks/{task_id}", { path: { task_id: taskId } });
  const decision = useApi("/decisions/{decision_id}", {
    path: { decision_id: task.data?.authorised_by_decision_id ?? "" },
    enabled: Boolean(task.data?.authorised_by_decision_id),
  });
  if (!task.data) return null;
  const t = task.data;
  const by = decision.data?.stamp.principal ?? decision.data?.initiated_by ?? null;
  return (
    <>
      <Row label="Follow-up task">
        For report <AppLink href={`/reports/${encodeURIComponent(t.report_id)}`}>{t.report_id}</AppLink>. Task <Mono>{t.id}</Mono>.
      </Row>
      <Row label="Authorised by">
        {by ? <PersonName id={by} /> : "The Reviewer"}
        {decision.data?.decided_at ? ` at ${formatTime(decision.data.decided_at)}` : ""}. Task grant{" "}
        <Mono>{formatGrant(t.grant_id, t.grant_version)}</Mono>, limit {t.params.max}.
      </Row>
    </>
  );
}

function runStatus(run: Run): { text: string; icon: LucideIcon } {
  const c = run.counts;
  switch (run.status) {
    case "running":
      return { text: "Running", icon: Play };
    case "stopping":
      return { text: `Stopping: ${run.in_flight} in flight. No new actions will start.`, icon: CirclePause };
    case "stopped":
      return {
        text: `Stopped${run.stopped_at ? ` at ${formatTime(run.stopped_at)}` : ""}. ${c.done} took effect, ${c.blocked} blocked, ${c.unknown} unknown.`,
        icon: OctagonX,
      };
    case "done":
      return {
        text: `Finished${run.finished_at ? ` at ${formatTime(run.finished_at)}` : ""}. ${c.done} took effect, ${c.blocked} blocked, ${c.unknown} unknown.`,
        icon: CircleCheck,
      };
    case "failed":
      return { text: "Failed", icon: CircleX };
  }
}
