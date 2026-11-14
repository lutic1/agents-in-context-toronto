"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useHotkeys } from "react-hotkeys-hook";
import { CircleDashed, Gavel, ListOrdered, SearchX } from "lucide-react";

import { AfterRunEntry } from "@/components/audit/after-run";
import { RunEntry, type AuditContext } from "@/components/audit/audit-entry";
import { Mono, Panel } from "@/components/audit/common";
import { FeedSourceLabel } from "@/components/audit/feed-source-label";
import { IdentityCard } from "@/components/audit/identity-card";
import {
  entryState,
  isActiveRun,
  isAnnounced,
  kindName,
  type Audit,
  type AuditEntry,
} from "@/components/audit/labels";
import { SourcesPanel } from "@/components/audit/sources-panel";
import { useAuditFeed } from "@/components/audit/use-audit-feed";
import { WhoAuthorisedDock } from "@/components/audit/who-authorised";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { Button, buttonVariants } from "@/components/ui/button";
import { ApiError, isUnreachable } from "@/lib/api";
import { POLL_MS, useApi } from "@/lib/use-api";

/**
 * The Audit view (Story 9.8, V14): one run reconstructed from
 * `GET /runs/<run_id>/audit`, polled while the run is running. The screen
 * renders what the API returns and applies no rule of its own: it answers
 * "What did the agent find, which memory changed its wording, what was
 * blocked, and who authorised the follow-up?" without leaving the page.
 */
export function AuditView({ runId }: { runId: string }) {
  const feed = useAuditFeed(runId);
  const whoami = useApi("/whoami", { interval: POLL_MS * 15 });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const rawAudit = feed.audit;
  const announcement = useAnnouncement(rawAudit);

  // j and k move between entries (EXPERIENCE "Interaction Primitives").
  const move = (step: 1 | -1) => {
    const rows = Array.from(listRef.current?.querySelectorAll<HTMLElement>("[data-audit-entry]") ?? []);
    if (rows.length === 0) return;
    const current = document.activeElement?.closest<HTMLElement>("[data-audit-entry]") ?? null;
    const at = current ? rows.indexOf(current) : step === 1 ? -1 : rows.length;
    const next = rows[Math.min(rows.length - 1, Math.max(0, at + step))];
    next?.focus();
    next?.scrollIntoView({ block: "nearest" });
  };
  // Closing "Who authorised this?" returns focus to the button that opened it
  // (WCAG 2.4.3): the Sheet has no trigger and the dock unmounts its content.
  const closeWho = (decisionId: string | null) => {
    setSelectedId(null);
    if (!decisionId) return;
    requestAnimationFrame(() => {
      document.querySelector<HTMLElement>(`[data-who-for="${CSS.escape(decisionId)}"]`)?.focus();
    });
  };
  useHotkeys("j", () => move(1));
  useHotkeys("k", () => move(-1));

  if (!rawAudit) {
    if (feed.error) return <AuditFailure error={feed.error} runId={runId} onRetry={feed.refresh} />;
    return <PageSkeleton rows={5} />;
  }

  // Normalise once so a payload that omits a list never reaches the error boundary.
  const audit: Audit = {
    ...rawAudit,
    entries: rawAudit.entries ?? [],
    after_run: rawAudit.after_run ?? [],
    policies: rawAudit.policies ?? [],
    sources: rawAudit.sources ?? [],
    linked_runs: rawAudit.linked_runs ?? [],
  };
  const entries = bySeq(audit.entries);
  const afterRun = bySeq(audit.after_run);
  const selected = [...entries, ...afterRun].find((e) => e.decision_id === selectedId) ?? null;
  const running = isActiveRun(audit.run.status);

  const ctx: AuditContext = {
    audit: { ...audit, entries, after_run: afterRun },
    canResolve: whoami.data?.actions.includes("resolve_notification") ?? false,
    onResolved: () => void feed.refresh(),
    selectedId,
    onWho: (entry) => setSelectedId((id) => (id === entry.decision_id ? null : entry.decision_id)),
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-title">Audit</h1>
        <p className="text-table text-muted-foreground">
          One run, decision by decision. Run <Mono>{audit.run.id}</Mono>. Shortcuts: <kbd className="text-identifier">j</kbd> and{" "}
          <kbd className="text-identifier">k</kbd> move between entries.
        </p>
      </div>

      <p className="sr-only" role="status" aria-live="polite">
        {announcement}
      </p>

      {feed.error ? (
        <Notice icon={CircleDashed} title="Showing the last answer" role="status">
          {isUnreachable(feed.error)
            ? "The API did not answer the latest refresh. This is the last audit it returned; it will keep trying."
            : `The latest refresh failed: ${feed.error.message}`}
        </Notice>
      ) : null}

      <IdentityCard audit={audit} />

      <FeedSourceLabel
        source={feed.source}
        polling={feed.polling}
        halted={feed.halted}
        updatedAt={feed.updatedAt}
        refreshing={feed.isValidating}
        onRefresh={() => void feed.refresh()}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div ref={listRef} className="flex min-w-0 flex-col gap-6">
          <SourcesPanel audit={audit} />

          <Panel icon={ListOrdered} title="Decisions, in order" headingId="entries-heading">
            {entries.length === 0 ? (
              <p className="text-body text-muted-foreground">
                {running
                  ? "No actions yet. The agent is scanning ClinicalTrials.gov for the scope."
                  : "This run recorded no decisions."}
              </p>
            ) : (
              <ol className="relative ml-3 flex flex-col gap-4 border-l border-border pl-6" aria-label="Decisions in order">
                {entries.map((entry, i) => (
                  <RunEntry key={entry.decision_id} entry={entry} position={i + 1} ctx={ctx} />
                ))}
              </ol>
            )}
          </Panel>

          <Panel icon={Gavel} title="After the run" headingId="after-run-heading">
            {afterRun.length === 0 ? (
              <p className="text-body text-muted-foreground">No Reviewer decisions yet.</p>
            ) : (
              <ol className="relative ml-3 flex flex-col gap-4 border-l border-border pl-6" aria-label="Reviewer decisions after the run">
                {afterRun.map((entry, i) => (
                  <AfterRunEntry key={entry.decision_id} entry={entry} position={i + 1} ctx={ctx} />
                ))}
              </ol>
            )}
          </Panel>
        </div>

        <WhoAuthorisedDock selected={selected} audit={ctx.audit} onClose={() => closeWho(selectedId)} />
      </div>
    </div>
  );
}

/** Entries are ordered by their decision's `seq` (D21); an entry without one keeps its place after those with one. */
function bySeq(entries: AuditEntry[]): AuditEntry[] {
  return entries
    .map((entry, index) => ({ entry, index }))
    .sort((a, b) => {
      const sa = a.entry.seq ?? Number.POSITIVE_INFINITY;
      const sb = b.entry.seq ?? Number.POSITIVE_INFINITY;
      return sa === sb ? a.index - b.index : sa - sb;
    })
    .map((x) => x.entry);
}

/**
 * What the polite live region says. The feed announces only blocked, claim
 * blocked, failed and unknown entries that are new since the last read, and
 * a change of run status (Accessibility Floor). Nothing is announced for the
 * first read, so opening the page does not read out the whole run.
 */
function useAnnouncement(audit: Audit | undefined): string {
  const [seen, setSeen] = useState<{ marks: string[]; status: string; message: string } | null>(null);
  if (!audit) return seen?.message ?? "";

  const all = [...(audit.entries ?? []), ...(audit.after_run ?? [])];
  const marks = all.map((e) => `${e.decision_id}:${entryState(e).key}`);
  const status = audit.run.status;

  if (!seen) {
    setSeen({ marks, status, message: "" });
    return "";
  }
  if (seen.status === status && seen.marks.length === marks.length && seen.marks.every((m, i) => m === marks[i])) {
    return seen.message;
  }

  const known = new Set(seen.marks);
  const parts: string[] = [];
  if (seen.status !== status) parts.push(`Run ${status}.`);
  all.forEach((e, i) => {
    if (!known.has(marks[i]) && isAnnounced(e)) parts.push(`${entryState(e).word}: ${kindName(e)}.`);
  });
  const message = parts.length > 0 ? parts.join(" ") : seen.message;
  setSeen({ marks, status, message });
  return message;
}

/** The states a run's audit can fail into: not reachable, not found, not built yet, or another error. */
function AuditFailure({
  error,
  runId,
  onRetry,
}: {
  error: Error;
  runId: string;
  onRetry: () => void | Promise<unknown>;
}) {
  const status = error instanceof ApiError ? error.status : null;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-title">Audit</h1>
      {isUnreachable(error) ? (
        <ApiUnreachableNotice />
      ) : status === 404 ? (
        <Notice icon={SearchX} title="Run not found" role="alert">
          There is no run <Mono>{runId}</Mono>. Open the Run console to see the runs there are.
        </Notice>
      ) : status === 501 ? (
        <Notice icon={CircleDashed} title="The audit is not available yet" role="status">
          The API has not finished this route. Try again in a moment.
        </Notice>
      ) : (
        <Notice icon={CircleDashed} title="The audit could not be read" role="alert">
          {error.message}
        </Notice>
      )}
      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={() => void onRetry()}>
          Try again
        </Button>
        <Link href="/runs" className={buttonVariants({ variant: "outline" })}>
          Open the Run console
        </Link>
      </div>
    </div>
  );
}
