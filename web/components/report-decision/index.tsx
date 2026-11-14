"use client";

// B04 builder 2: the decisions bar. Keeps the stub's export and props: DecisionBar({ reportId }).
import { useRef, useState } from "react";
import { Check, PencilLine, ShieldX, X } from "lucide-react";
import { useHotkeys } from "react-hotkeys-hook";
import { toast } from "sonner";
import { useSWRConfig } from "swr";

import { ApiError, buildPath, post } from "@/lib/api";
import { shortId } from "@/lib/format";
import type { components } from "@/lib/types";
import { POLL_MS, useApi } from "@/lib/use-api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { DecidedLine } from "./decided";
import { DecisionForm, type DecisionFormValues, type FormMode } from "./decision-form";
import { errorText } from "./errors";
import { approvalSentence } from "./format";
import { useRefreshRelated } from "./refresh";
import { StatusPill } from "./status-pill";
import { useActions } from "./who";

type DecisionRequest = components["schemas"]["ReportDecisionRequest"];

const SHORTCUTS_KEY = "dxp.report-shortcuts";

function readShortcutsPref(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(SHORTCUTS_KEY) !== "off";
  } catch {
    return true;
  }
}

/**
 * The decisions bar for one report. While the report is pending it shows
 * Approve, "Approve with correction" and Reject (only when the signed-in
 * principal may decide reports); once decided it is replaced by the decision
 * line, the follow-up task in words (no start button, V38) and, behind the
 * `revert` flag, "Revert approval".
 */
export function DecisionBar({ reportId }: { reportId: string }) {
  const { data: report, error, isLoading } = useApi("/reports/{report_id}", { path: { report_id: reportId } });

  // Poll only while the server is mid-transition (accepting or reverting). A second hook on the
  // same key switches polling on, so the first one stays a plain single read.
  const transitional = report?.status === "accepting" || report?.status === "reverting";
  useApi("/reports/{report_id}", {
    path: { report_id: reportId },
    enabled: transitional,
    interval: POLL_MS,
  });

  if (isLoading && !report) {
    return <Skeleton className="h-20 w-full rounded-lg" role="status" aria-label="Loading the decision" />;
  }
  if (!report) {
    // An unknown report ID is the report body's "Report not found"; the bar says nothing.
    if (error instanceof ApiError && error.status === 404) return null;
    return (
      <p className="rounded-lg border border-border bg-card p-4 text-body text-muted-foreground" role="alert">
        The decision is unavailable because the report could not be read. Reload this page once the API is back.
      </p>
    );
  }

  if (report.status === "pending") return <PendingBar reportId={reportId} />;
  if (report.status === "accepting") {
    return (
      <section aria-label="Decision" className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <p role="status" aria-live="polite" className="text-body">
          Approving: the update is being accepted. This page refreshes by itself.
        </p>
      </section>
    );
  }
  return <DecidedLine report={report} />;
}

function PendingBar({ reportId }: { reportId: string }) {
  const { can, loaded, loading, error: whoError } = useActions();
  const { mutate } = useSWRConfig();
  const refresh = useRefreshRelated();
  const [mode, setMode] = useState<FormMode | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blocked, setBlocked] = useState<string | null>(null);
  const [shortcuts, setShortcuts] = useState(readShortcutsPref);
  const correctRef = useRef<HTMLButtonElement>(null);
  const rejectRef = useRef<HTMLButtonElement>(null);
  const lastOpened = useRef<FormMode | null>(null);

  const canDecide = loaded && can("decide_report");
  const active = canDecide && shortcuts && !busy;

  async function send(body: DecisionRequest) {
    setBusy(true);
    setError(null);
    setBlocked(null);
    try {
      const res = await post("/reports/{report_id}/decision", { path: { report_id: reportId }, body });
      if (res.report.status === "pending") {
        // A blocked decision is not an error: nothing changed and the report stays pending.
        const decision = res.decisions.at(-1);
        const check = decision?.outcome === "blocked" ? (decision.failed_check ?? "a check") : null;
        setBlocked(res.message ?? (check ? `Decision blocked: ${check} failed. Nothing changed.` : "Nothing changed. The report is still pending."));
        return;
      }
      // Show the returned state at once; the related reads refresh behind it.
      await mutate(buildPath("/reports/{report_id}", { path: { report_id: reportId } }), res.report, {
        revalidate: false,
      });
      if (res.task) {
        await mutate(buildPath("/tasks/{task_id}", { path: { task_id: res.task.id } }), res.task, {
          revalidate: false,
        });
      }
      setMode(null);
      if (body.action === "reject") {
        // V46: "Memory saved" only after the create succeeded, i.e. the response carries the memory.
        toast.success(res.memory ? `Rejected. Memory saved (${shortId(res.memory.id)}).` : "Rejected.");
      } else if (body.correction) {
        toast.success(
          res.memory
            ? `Approved with correction. Memory saved (${shortId(res.memory.id)}).`
            : "Approved with correction.",
        );
      } else {
        toast.success(res.message ?? approvalSentence(res.report, res.task));
      }
      refresh();
    } catch (e) {
      setError(errorText(e));
      // A 409 means someone else decided first: show what the server now holds.
      refresh();
    } finally {
      setBusy(false);
    }
  }

  function approve() {
    if (busy || !canDecide) return;
    void send({ action: "approve" });
  }

  function open(next: FormMode) {
    if (busy || !canDecide) return;
    lastOpened.current = next;
    setError(null);
    setBlocked(null);
    setMode(next);
  }

  function close() {
    setMode(null);
    setError(null);
    const target = lastOpened.current === "reject" ? rejectRef : correctRef;
    // Return focus to the button that opened the form.
    requestAnimationFrame(() => target.current?.focus());
  }

  function submit(values: DecisionFormValues) {
    if (mode === "reject") {
      void send({ action: "reject", note: values.note, claim_kind: values.claimKind });
    } else {
      void send({ action: "approve", note: values.note, correction: values.note, claim_kind: values.claimKind });
    }
  }

  useHotkeys("a", approve, { enabled: active && mode === null }, [active, mode]);
  useHotkeys("c", () => open("correct"), { enabled: active && mode === null, preventDefault: true }, [active, mode]);
  useHotkeys("r", () => open("reject"), { enabled: active && mode === null, preventDefault: true }, [active, mode]);

  function toggleShortcuts() {
    const next = !shortcuts;
    setShortcuts(next);
    try {
      window.localStorage.setItem(SHORTCUTS_KEY, next ? "on" : "off");
    } catch {
      // The preference is a convenience; it works without storage.
    }
  }

  if (loading) {
    return <Skeleton className="h-20 w-full rounded-lg" role="status" aria-label="Loading the decision" />;
  }

  if (!canDecide) {
    return (
      <section aria-label="Decision" className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill status="pending" />
        </div>
        <p className="mt-2 text-body text-muted-foreground" role={whoError ? "alert" : undefined}>
          {whoError
            ? "Couldn't confirm who is signed in, so the decision buttons are hidden. Reload this page once the API is back."
            : "This report is waiting for a Reviewer. The signed-in principal cannot decide reports."}
        </p>
      </section>
    );
  }

  return (
    <section
      aria-label="Decision"
      className={cn(
        "rounded-lg border border-border bg-glass-strong p-3 shadow-glass backdrop-blur",
        // Sticky only while the bar is short: an open form is tall and would cover the page at narrow widths.
        mode === null && "sticky bottom-0 z-10",
      )}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <StatusPill status="pending" />
        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={approve} disabled={busy} aria-busy={busy && mode === null}>
            <Check aria-hidden="true" data-icon="inline-start" />
            Approve
          </Button>
          <Button
            ref={correctRef}
            type="button"
            variant="secondary"
            onClick={() => open("correct")}
            disabled={busy}
            aria-expanded={mode === "correct"}
          >
            <PencilLine aria-hidden="true" data-icon="inline-start" />
            Approve with correction
          </Button>
          <Button
            ref={rejectRef}
            type="button"
            variant="outline"
            onClick={() => open("reject")}
            disabled={busy}
            aria-expanded={mode === "reject"}
            className="hover:border-destructive hover:text-destructive focus-visible:border-destructive focus-visible:text-destructive"
          >
            <X aria-hidden="true" data-icon="inline-start" />
            Reject
          </Button>
        </div>
      </div>

      {mode ? (
        <DecisionForm
          key={mode}
          mode={mode}
          submitting={busy}
          error={error}
          onSubmit={submit}
          onCancel={close}
        />
      ) : null}

      {/* Errors from a one-click Approve show here; the form shows its own. */}
      {!mode && error ? (
        <p className="mt-3 text-body text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {blocked ? (
        <p
          className="mt-3 flex items-center gap-2 border-l-[3px] border-l-destructive pl-2 text-body text-destructive"
          role="alert"
        >
          <ShieldX className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {blocked}
        </p>
      ) : null}
      {busy && mode === null ? (
        <p className="mt-3 text-caption text-muted-foreground" role="status">
          Approving…
        </p>
      ) : null}

      <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-caption text-muted-foreground">
        {shortcuts ? (
          <span>
            Shortcuts: <kbd className="text-identifier">a</kbd> approve, <kbd className="text-identifier">c</kbd>{" "}
            correct, <kbd className="text-identifier">r</kbd> reject, <kbd className="text-identifier">Esc</kbd> cancel.
          </span>
        ) : (
          <span>Keyboard shortcuts are off.</span>
        )}
        <button
          type="button"
          onClick={toggleShortcuts}
          className="rounded-sm underline underline-offset-2 focus-visible:ring-3 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
        >
          {shortcuts ? "Turn shortcuts off" : "Turn shortcuts on"}
        </button>
      </p>
      <p className="mt-1 text-caption text-muted-foreground">
        Approve promotes the update to accepted knowledge and authorises the follow-up task. Reject promotes
        nothing. Both can save a memory from your note.
      </p>
    </section>
  );
}
