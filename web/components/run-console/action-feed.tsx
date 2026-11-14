"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CircleDashed, FileX } from "lucide-react";

import { ActionRow } from "@/components/run-console/action-row";
import { entryState } from "@/components/run-console/entry-state";
import { destinationName, kindName, sourceLabel } from "@/components/run-console/names";
import type { AuditEntry, Run } from "@/components/run-console/types";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, isUnreachable } from "@/lib/api";
import { formatDate } from "@/lib/format";

/** Decisions in the order the run made them: `seq` is the only ordering source (AD-10). */
export function orderEntries(entries: AuditEntry[]): AuditEntry[] {
  return [...entries].sort((a, b) => {
    if (a.seq !== null && b.seq !== null) return a.seq - b.seq;
    if (a.seq !== null) return -1;
    if (b.seq !== null) return 1;
    return (a.decided_at ?? "").localeCompare(b.decided_at ?? "");
  });
}

function announcementKey(entry: AuditEntry): string {
  return `${entry.decision_id}:${entry.outcome}:${entry.status ?? ""}`;
}

function describe(entry: AuditEntry): string {
  const state = entryState(entry);
  const subject = entry.evidence_ref?.source_ref ? sourceLabel(entry.evidence_ref.source_ref) : destinationName(entry.destination);
  return `${state.word}: ${kindName(entry.kind)}, ${subject}`;
}

type Props = {
  run: Run;
  entries: AuditEntry[] | undefined;
  loading: boolean;
  error: Error | undefined;
  policyCount: number | null;
  canResolve: boolean;
  onResolved: () => void;
};

/**
 * The action feed: one row per gate decision, in order. Blocked, claim blocked, failed
 * and unknown rows are announced as they appear (EXPERIENCE "Accessibility Floor"); the
 * others are not. `j` and `k` move between rows, Enter opens the entry in the Audit view.
 */
export function ActionFeed({ run, entries, loading, error, policyCount, canResolve, onResolved }: Props) {
  const ordered = useMemo(() => (entries ? orderEntries(entries) : undefined), [entries]);
  const list = useRef<HTMLUListElement>(null);

  // Rows already on screen when the first read lands do not animate and are not announced.
  const [baseline, setBaseline] = useState<Set<string> | null>(null);
  const [announced, setAnnounced] = useState<Set<string> | null>(null);
  const [message, setMessage] = useState("");

  if (ordered && baseline === null) {
    setBaseline(new Set(ordered.map((entry) => entry.decision_id)));
    setAnnounced(new Set(ordered.filter((e) => entryState(e).announce).map(announcementKey)));
  } else if (ordered && announced !== null) {
    const fresh = ordered.filter((e) => entryState(e).announce && !announced.has(announcementKey(e)));
    if (fresh.length > 0) {
      setAnnounced(new Set([...announced, ...fresh.map(announcementKey)]));
      setMessage(fresh.map(describe).join(". "));
    }
  }

  // j and k move between rows from anywhere on the page, unless a form field has focus.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.key !== "j" && event.key !== "k") || event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable='true'], [role='dialog']")) return;
      const links = Array.from(list.current?.querySelectorAll<HTMLElement>("[data-row-link]") ?? []);
      if (links.length === 0) return;
      const at = links.findIndex((link) => link.closest("li")?.contains(document.activeElement));
      const next = event.key === "j" ? Math.min(at + 1, links.length - 1) : Math.max(at - 1, 0);
      links[Math.max(next, 0)].focus();
      event.preventDefault();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  if (!ordered) {
    if (error) {
      if (isUnreachable(error)) return <ApiUnreachableNotice />;
      if (error instanceof ApiError && error.status === 501) {
        return (
          <Notice icon={CircleDashed} title="The action feed is not available yet" role="status">
            The API has not built the run audit yet. The run itself still shows above.
          </Notice>
        );
      }
      return (
        <Notice icon={FileX} title="The action feed could not be loaded" role="alert">
          {error.message}
        </Notice>
      );
    }
    return (
      <div className="flex flex-col gap-2" role="status" aria-label="Loading the action feed">
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (ordered.length === 0 && !loading) {
    return <EmptyFeed run={run} />;
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Only blocked, claim blocked, failed and unknown rows are announced. */}
      <p role="status" aria-live="polite" className="sr-only">
        {message}
      </p>
      <ul ref={list} aria-label="Actions this run has decided" className="flex flex-col gap-2">
        {ordered.map((entry) => (
          <ActionRow
            key={entry.decision_id}
            entry={entry}
            runId={run.id}
            policySetVersion={run.policy_set_version}
            policyCount={policyCount}
            canResolve={canResolve}
            animate={baseline !== null && !baseline.has(entry.decision_id)}
            onResolved={onResolved}
          />
        ))}
      </ul>
      <p className="text-caption text-muted-foreground">
        Shortcuts: <kbd className="text-identifier">j</kbd> and <kbd className="text-identifier">k</kbd> move between
        rows; Enter opens the entry in the Audit view.
      </p>
    </div>
  );
}

function EmptyFeed({ run }: { run: Run }) {
  const since = run.scan?.cursor_from ? formatDate(run.scan.cursor_from) : null;
  if (run.status === "running" || run.status === "stopping") {
    return (
      <Notice icon={CircleDashed} title="No actions yet" role="status">
        The agent is scanning ClinicalTrials.gov for the scope.
      </Notice>
    );
  }
  if (run.status === "done") {
    return (
      <Notice icon={CircleDashed} title="Scan finished" role="status">
        No trials in scope updated since {since ?? "the cursor"}. The cursor advances.
      </Notice>
    );
  }
  if (run.status === "stopped") {
    return (
      <Notice icon={CircleDashed} title="Stopped before any action" role="status">
        The run was stopped before it decided anything.
      </Notice>
    );
  }
  return (
    <Notice icon={CircleDashed} title="No actions" role="status">
      The run ended before it decided anything.
    </Notice>
  );
}
