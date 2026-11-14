"use client";

import { useId, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CircleDashed, Play } from "lucide-react";
import { useSWRConfig } from "swr";

import type { Grant } from "@/components/run-console/types";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { SyntheticBadge } from "@/components/shell/badges";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, buildPath, get, isUnreachable, itemsOf, post } from "@/lib/api";
import { formatGrant } from "@/lib/format";
import { useApi } from "@/lib/use-api";

/** The grants the caller may start: active agent grants that allow a source search and name the caller in `startable_by`. */
export function startableGrants(grants: Grant[], principalId: string | null): Grant[] {
  return grants.filter(
    (grant) =>
      grant.kind === "agent" &&
      grant.status === "active" &&
      grant.actions.includes("search_source") &&
      (principalId === null || grant.startable_by.includes(principalId)),
  );
}

type Problem = { message: string; runId?: string };

/**
 * Start a discovery scan: choose a grant, each labelled with its Team and scope (there
 * is no Team picker, D18), then `POST /runs { grant_id, set: "discover" }` through the
 * server-side key. A 403 and a 409 (a run is already running, with a link to it) are
 * shown as messages.
 */
export function StartRun() {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const grants = useApi("/grants");
  const whoami = useApi("/whoami");
  const teams = useApi("/teams");

  const [chosen, setChosen] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<Problem | null>(null);
  const legendId = useId();

  const options = useMemo(
    () => startableGrants(itemsOf(grants.data), whoami.data ? whoami.data.id : null),
    [grants.data, whoami.data],
  );
  const syntheticTeams = useMemo(
    () => new Set(itemsOf(teams.data).filter((t) => t.synthetic).map((t) => t.id)),
    [teams.data],
  );

  // A single grant needs no choosing.
  const selected = chosen ?? (options.length === 1 ? options[0].grant_id : null);

  async function start(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || busy) return;
    setBusy(true);
    setProblem(null);
    try {
      const run = await post("/runs", { body: { grant_id: selected, set: "discover" } });
      await mutate(buildPath("/runs"));
      router.push(`/runs/${encodeURIComponent(run.id)}`);
    } catch (cause) {
      setProblem(await explain(cause));
      setBusy(false);
    }
  }

  if ((grants.isLoading && !grants.data) || (whoami.isLoading && !whoami.data)) {
    return (
      <div role="status" aria-label="Loading grants" className="flex flex-col gap-2">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-9 w-32" />
      </div>
    );
  }

  if (!grants.data) {
    if (grants.error && isUnreachable(grants.error)) return <ApiUnreachableNotice />;
    if (grants.error instanceof ApiError && grants.error.status === 501) {
      return (
        <Notice icon={CircleDashed} title="Grants are not available yet" role="status">
          The API has not built the grants routes yet, so a scan cannot be started from here.
        </Notice>
      );
    }
    return (
      <Notice icon={CircleDashed} title="The grants could not be loaded" role="alert">
        {grants.error?.message ?? "The API did not return a list of grants."}
      </Notice>
    );
  }

  if (options.length === 0) {
    return (
      <Notice icon={CircleDashed} title="No grant to start a scan under" role="status">
        None of the active grants names you in <span className="text-identifier">startable_by</span>. Ask the person who
        manages grants to add you.
      </Notice>
    );
  }

  return (
    <form onSubmit={start} className="flex flex-col gap-4" aria-describedby={problem ? "start-problem" : undefined}>
      <fieldset className="flex flex-col gap-2" aria-labelledby={legendId}>
        <legend id={legendId} className="text-table font-semibold">
          Grant to scan under
        </legend>
        {options.map((grant) => {
          const checked = selected === grant.grant_id;
          return (
            <label
              key={grant.id}
              className="flex cursor-pointer items-start gap-3 rounded-md border border-border bg-card p-3 has-[:checked]:border-ink-deep has-[:checked]:bg-ink-tint/60"
            >
              <input
                type="radio"
                name="grant"
                value={grant.grant_id}
                checked={checked}
                onChange={() => setChosen(grant.grant_id)}
                className="mt-1 size-4 shrink-0 accent-[var(--ink-deep)]"
              />
              <span className="min-w-0">
                <span className="text-identifier font-semibold">{formatGrant(grant.grant_id, grant.version)}</span>
                <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-table">
                  <span>{grant.team_name ?? "No Team named"}</span>
                  {grant.team_id && syntheticTeams.has(grant.team_id) ? <SyntheticBadge /> : null}
                </span>
                <span className="block text-caption text-muted-foreground">
                  {grant.scope_name ? `Scope: ${grant.scope_name}` : "Scope not named"}
                </span>
              </span>
            </label>
          );
        })}
      </fieldset>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={!selected || busy} aria-busy={busy}>
          <Play aria-hidden="true" />
          Start run
        </Button>
        <p className="text-caption text-muted-foreground">
          The run scans the research scope its grant names. Who you are comes from the server-side key.
        </p>
      </div>

      {problem ? (
        <p id="start-problem" role="alert" className="text-table text-destructive">
          {problem.message}{" "}
          {problem.runId ? (
            <Link href={`/runs/${encodeURIComponent(problem.runId)}`} className="rounded-sm font-semibold underline underline-offset-4">
              Open the run in progress
            </Link>
          ) : null}
        </p>
      ) : null}
    </form>
  );
}

async function explain(cause: unknown): Promise<Problem> {
  if (isUnreachable(cause)) return { message: "Couldn't reach the API. No run was started." };
  if (cause instanceof ApiError) {
    if (cause.status === 403) {
      return { message: "You are not allowed to start a run under this grant." };
    }
    if (cause.status === 409) {
      // The API does not say which run; find it so the message can link to it.
      let runId: string | undefined;
      try {
        const page = await get("/runs");
        runId = itemsOf(page).find((run) => run.status === "running" || run.status === "stopping")?.id;
      } catch {
        runId = undefined;
      }
      return { message: "A run is already running. Only one run is allowed at a time.", runId };
    }
    return { message: cause.message };
  }
  return { message: "The run could not be started." };
}
