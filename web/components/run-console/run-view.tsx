"use client";

import Link from "next/link";
import { ArrowLeft, CircleDashed, FileSearch, ScrollText, SearchX } from "lucide-react";
import { useSWRConfig } from "swr";

import { LiveSourceLabel, runKeys, sweepInterval, useLiveSource } from "@/components/live-source";
import { ActionFeed } from "@/components/run-console/action-feed";
import { IdentityCard } from "@/components/run-console/identity-card";
import { runTitle } from "@/components/run-console/run-list";
import { ScanOrder } from "@/components/run-console/scan-order";
import { RunStatusBadge } from "@/components/run-console/status-badge";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { buttonVariants } from "@/components/ui/button";
import { ApiError, isUnreachable, itemsOf } from "@/lib/api";
import { features } from "@/lib/features";
import { latestRun } from "@/lib/runs";
import { useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

/**
 * One run in the Run console: identity card, stop control, the source label and the
 * action feed. It reads `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` every 2
 * seconds, or, with `live_stream` on and the stream open, whenever the stream says
 * something happened (Story 9.12). The label above the feed says which. While the stream
 * is open and the run is running or stopping, the run is still read every 10 s: that read
 * drives the server's sweep and the `in_flight` count.
 */
export function RunView({ runId }: { runId: string }) {
  const { mutate } = useSWRConfig();
  const source = useLiveSource(runId);

  const run = useApi("/runs/{run_id}", { path: { run_id: runId }, interval: source.refreshInterval });
  // Same read as above on a slow timer, only while the stream is open: it keeps the sweep and `in_flight` moving.
  useApi("/runs/{run_id}", { path: { run_id: runId }, interval: sweepInterval(source.mode, run.data?.status) });
  const audit = useApi("/runs/{run_id}/audit", { path: { run_id: runId }, interval: source.refreshInterval });
  const whoami = useApi("/whoami");
  const teams = useApi("/teams");

  const data = run.data;
  const followUp = data?.kind === "task";
  const grant = useApi("/grants/{grant_id}", {
    path: { grant_id: data?.grant_id ?? "" },
    query: { version: data?.grant_version },
    enabled: Boolean(data),
  });
  const scope = useApi("/scopes/{scope_id}", {
    path: { scope_id: data?.scope_id ?? "" },
    enabled: Boolean(data?.scope_id && data.kind !== "task"),
  });
  const task = useApi("/tasks/{task_id}", {
    path: { task_id: data?.task_id ?? "" },
    enabled: Boolean(followUp && data?.task_id && features.task_run),
  });

  if (run.isLoading && !data) return <PageSkeleton rows={3} />;

  if (!data) {
    return <RunProblem error={run.error} />;
  }

  // A task's run is shown only with `task_run` on (V66).
  if (followUp && !features.task_run) {
    return <TaskRunHidden />;
  }

  const entries = audit.data?.entries;
  const canResolve = whoami.data?.actions.includes("resolve_notification") ?? false;
  const teamSynthetic = Boolean(
    data.team_id && itemsOf(teams.data).some((team) => team.id === data.team_id && team.synthetic),
  );
  const reports = [
    ...new Set((entries ?? []).filter((e) => e.kind === "file_proposal" && e.report_id).map((e) => e.report_id as string)),
  ];
  const linkedRuns = features.task_run ? (audit.data?.linked_runs ?? []) : [];

  const refresh = () => {
    for (const key of runKeys(runId)) void mutate(key);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <Link href="/runs" className="inline-flex w-fit items-center gap-1 rounded-sm text-table font-semibold underline-offset-4 hover:underline">
          <ArrowLeft className="size-4" strokeWidth={1.75} aria-hidden="true" />
          All runs and start a new scan
        </Link>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <h1 className="text-title">{runTitle(data)}</h1>
          <RunStatusBadge status={data.status} />
          <Link
            href={`/runs/${encodeURIComponent(runId)}/audit`}
            className={cn(buttonVariants({ variant: "outline" }), "sm:ml-auto")}
          >
            <ScrollText aria-hidden="true" />
            Open the audit
          </Link>
        </div>
      </div>

      <IdentityCard
        run={data}
        grant={grant.data}
        teamSynthetic={teamSynthetic}
        policyCount={audit.data ? audit.data.policies.length : null}
        task={task.data}
        entries={entries}
      />

      {!followUp ? <ScanOrder run={data} scope={scope.data} /> : null}

      <section aria-labelledby="feed-heading" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
          <h2 id="feed-heading" className="text-heading">
            Actions
          </h2>
          <LiveSourceLabel mode={source.mode} />
        </div>
        <ActionFeed
          run={data}
          entries={entries}
          loading={audit.isLoading}
          error={audit.error}
          policyCount={audit.data ? audit.data.policies.length : null}
          canResolve={canResolve}
          onResolved={refresh}
        />
      </section>

      {reports.length > 0 ? (
        <section aria-labelledby="reports-heading" className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <h2 id="reports-heading" className="text-heading">
            Reports this run filed
          </h2>
          <ul className="mt-2 flex flex-col gap-1">
            {reports.map((id) => (
              <li key={id}>
                <Link
                  href={`/reports/${encodeURIComponent(id)}`}
                  className="inline-flex items-center gap-2 rounded-sm text-table font-semibold underline-offset-4 hover:underline"
                >
                  <FileSearch className="size-4" strokeWidth={1.75} aria-hidden="true" />
                  <span className="text-identifier">{id}</span>
                  <span className="font-normal text-muted-foreground">Pending review until it is decided</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {linkedRuns.length > 0 ? (
        <section aria-labelledby="linked-heading" className="rounded-lg border border-border bg-card p-5 shadow-sm">
          <h2 id="linked-heading" className="text-heading">
            Follow-up task
          </h2>
          <ul className="mt-2 flex flex-col gap-1">
            {linkedRuns.map((linked) => (
              <li key={linked.run_id} className="flex flex-wrap items-center gap-2 text-table">
                <Link
                  href={`/runs/${encodeURIComponent(linked.run_id)}`}
                  className="rounded-sm font-semibold underline underline-offset-4"
                >
                  Follow-up task run <span className="text-identifier">{linked.run_id}</span>
                </Link>
                <RunStatusBadge status={linked.status} />
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function RunProblem({ error }: { error: Error | undefined }) {
  if (error && isUnreachable(error)) {
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-title">Run console</h1>
        <ApiUnreachableNotice />
      </div>
    );
  }
  if (error instanceof ApiError && error.status === 404) {
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-title">Run console</h1>
        <Notice icon={SearchX} title="Run not found" role="status">
          No run has this ID. Open the Run console to see the runs there are.
        </Notice>
        <div>
          <Link href="/runs" className={buttonVariants({ variant: "default" })}>
            Open the Run console
          </Link>
        </div>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">Run console</h1>
      <Notice
        icon={CircleDashed}
        title={error instanceof ApiError && error.status === 501 ? "Runs are not available yet" : "This run could not be loaded"}
        role={error instanceof ApiError && error.status === 501 ? "status" : "alert"}
      >
        {error instanceof ApiError && error.status === 501
          ? "The API has not built the runs routes yet."
          : (error?.message ?? "The API did not return the run.")}
      </Notice>
      <div>
        <Link href="/runs" className={buttonVariants({ variant: "default" })}>
          Open the Run console
        </Link>
      </div>
    </div>
  );
}

/** With `task_run` off, a task's run is not shown (V66); the way back is the latest discovery run. */
function TaskRunHidden() {
  const runs = useApi("/runs");
  const latest = latestRun(itemsOf(runs.data).filter((r) => r.kind !== "task"));
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">Follow-up task</h1>
      <Notice icon={CircleDashed} title="Follow-up task runs are not shown" role="status">
        Task execution is off, so the follow-up task is authorised but not run. Nothing here is lost.
      </Notice>
      <div className="flex flex-wrap gap-3">
        {latest ? (
          <Link href={`/runs/${encodeURIComponent(latest.id)}`} className={buttonVariants({ variant: "default" })}>
            Open the latest discovery run
          </Link>
        ) : null}
        <Link href="/runs" className={buttonVariants({ variant: "outline" })}>
          Open the Run console
        </Link>
      </div>
    </div>
  );
}
