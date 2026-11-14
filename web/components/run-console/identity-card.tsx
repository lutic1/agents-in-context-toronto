"use client";

import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { CapabilityTag } from "@/components/live-source";
import { CopyId } from "@/components/run-console/copy-id";
import { kindName } from "@/components/run-console/names";
import { StopControl } from "@/components/run-console/stop-control";
import type { AuditEntry, Grant, Run, Task } from "@/components/run-console/types";
import { SyntheticBadge } from "@/components/shell/badges";
import { displayName, formatDate, formatDateTime, formatGrant, formatPolicySetParts, formatTime } from "@/lib/format";

type Props = {
  run: Run;
  /** The grant at the version the run pinned, when it could be read. */
  grant: Grant | undefined;
  teamSynthetic: boolean;
  policyCount: number | null;
  task: Task | undefined;
  entries: AuditEntry[] | undefined;
};

function Field({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={className}>
      <dt className="text-caption text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 min-w-0 text-body text-foreground">{children}</dd>
    </div>
  );
}

/**
 * The identity card (EXPERIENCE "Identity card"): two identities, never merged. The
 * agent is the executing agent named by the grant; "Started by" is the principal the
 * API resolved from the caller's key. Nothing here is editable; identifiers are copyable.
 */
export function IdentityCard({ run, grant, teamSynthetic, policyCount, task, entries }: Props) {
  const followUp = run.kind === "task";
  const policy = run.policy_set_version ? formatPolicySetParts(run.policy_set_version, policyCount ?? undefined) : null;
  const teamName = grant?.team_name ?? run.team_id;

  return (
    <section aria-labelledby="identity-heading" className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="identity-heading" className="text-heading">
          {followUp ? "Follow-up task" : "Who is running this"}
        </h2>
        <CapabilityTag
          label="Schema validation"
          hint="Grants and policies are checked by $jsonSchema validation in Atlas, so a malformed grant can't be saved."
        />
      </div>

      {followUp ? (
        <p className="mt-2 text-table">
          Follow-up task for report{" "}
          {task?.report_id ? (
            <Link href={`/reports/${encodeURIComponent(task.report_id)}`} className="rounded-sm font-semibold underline underline-offset-4">
              <span className="text-identifier">{task.report_id}</span>
            </Link>
          ) : (
            <span className="text-muted-foreground">(loading)</span>
          )}
          .{" "}
          {task ? (
            <>
              Authorised by {displayName(run.initiated_by)} at {formatTime(task.created_at)}.
            </>
          ) : null}
        </p>
      ) : null}
      {followUp && task ? (
        <p className="mt-1 text-caption text-muted-foreground">
          The report&apos;s gap: {task.question}
        </p>
      ) : null}

      <dl className="mt-4 grid gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Agent">
          <span className="text-identifier">{run.agent}</span>
          <span className="block text-caption text-muted-foreground">
            {run.model ? <>Model <span className="text-identifier">{run.model}</span></> : "Model not recorded"}
          </span>
        </Field>

        <Field label="Started by">
          {displayName(run.initiated_by)}
          {run.acting_for ? (
            <span className="block text-caption text-muted-foreground">Acting for {displayName(run.acting_for)}</span>
          ) : null}
        </Field>

        <Field label="Run">
          <CopyId value={run.id} label="run ID" />
          <span className="block text-caption text-muted-foreground">
            {run.set === "discover" ? "Discovery scan" : run.set} · {run.mode === "baseline" ? "baseline mode" : "live mode"}
          </span>
        </Field>

        <Field label="Grant" className="sm:col-span-2 lg:col-span-1">
          <span className="text-identifier">{formatGrant(run.grant_id, run.grant_version)}</span>
          {grant || teamName ? (
            <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-table">
              {teamName ? <span>{teamName}</span> : null}
              {teamSynthetic ? <SyntheticBadge /> : null}
            </span>
          ) : null}
          {grant?.scope_name ? <span className="block text-table">Scope: {grant.scope_name}</span> : null}
          {grant ? (
            <>
              <span className="block text-caption text-muted-foreground">
                Allowed: {grant.actions.length > 0 ? grant.actions.map(kindName).join(", ") : "no actions"}
              </span>
              <span className="block text-caption text-muted-foreground">
                {grant.expires_at ? `Expires ${formatDateTime(grant.expires_at)}` : "No expiry"}
                {followUp && (task?.params.max ?? grant.limits?.max_results)
                  ? ` · limit ${task?.params.max ?? grant.limits?.max_results}`
                  : ""}
              </span>
            </>
          ) : null}
        </Field>

        <Field label="Policy set">
          {policy ? (
            <span title={run.policy_set_version ?? undefined}>
              <span className="text-identifier">{policy.hash}</span> {policy.count}
            </span>
          ) : (
            <span className="text-muted-foreground">Not recorded</span>
          )}
        </Field>

        <Field label="Prompt version">
          {run.prompt_version ? (
            <span className="text-identifier">{run.prompt_version}</span>
          ) : (
            <span className="text-muted-foreground">Not recorded</span>
          )}
        </Field>

        {!followUp ? (
          <Field label="Scan cursor" className="sm:col-span-2 lg:col-span-3">
            {run.scan?.cursor_from ? (
              <>
                Scanning trials updated since {formatDate(run.scan.cursor_from)}
                {run.scan.cursor_to && run.scan.cursor_to !== run.scan.cursor_from ? (
                  <span className="block text-caption text-muted-foreground">
                    Cursor after this scan: {formatDate(run.scan.cursor_to)}
                  </span>
                ) : null}
              </>
            ) : (
              <span className="text-muted-foreground">Not set yet</span>
            )}
          </Field>
        ) : null}
      </dl>

      {run.active.length > 0 && (run.status === "running" || run.status === "stopping") ? (
        <p className="mt-4 flex items-start gap-2 text-table text-muted-foreground">
          <ShieldCheck className="mt-0.5 size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          <span>
            Working on{" "}
            {run.active.map((a, i) => (
              <span key={`${a.source_ref}:${a.step}`}>
                {i > 0 ? ", " : ""}
                <span className="text-identifier">{a.source_ref.replace(/^[^:]*:/, "")}</span> ({a.step.replace(/_/g, " ")})
              </span>
            ))}
            .
          </span>
        </p>
      ) : null}

      {run.failures.length > 0 ? (
        <ul className="mt-4 flex flex-col gap-1 text-table text-destructive">
          {run.failures.map((f) => (
            <li key={`${f.source_ref}:${f.error}`}>
              Failed on <span className="text-identifier">{f.source_ref.replace(/^[^:]*:/, "")}</span>: {f.error}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-5 border-t border-border pt-4">
        <StopControl run={run} entries={entries} />
      </div>
    </section>
  );
}
