"use client";

import Link from "next/link";
import { useState } from "react";
import { Brain, TriangleAlert } from "lucide-react";
import { toast } from "sonner";

import { buildPath, post } from "@/lib/api";
import { shortId } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { useSWRConfig } from "swr";

import { DecisionForm, type DecisionFormValues, type FormMode } from "./decision-form";
import { errorText } from "./errors";
import {
  approvalSentence,
  revertTaskSentence,
  updateCount,
  updatesPhrase,
  whoAndWhen,
  type Report,
} from "./format";
import { useRefreshRelated } from "./refresh";
import { RevertControl } from "./revert-control";
import { StatusPill } from "./status-pill";
import { TaskPanel, useTask } from "./task-panel";
import { useActions } from "./who";

/** The line that replaces the decisions bar once a report is decided (EXPERIENCE "Decisions bar", "Revert approval"). */
export function DecidedLine({ report }: { report: Report }) {
  const taskId = report.task_id ?? report.approval?.task_id ?? null;
  const { data: task } = useTask(taskId);
  const approved = report.status === "accepted" || report.status === "reverting" || report.status === "reverted";
  const updates = updateCount(report);
  const acceptedBy = whoAndWhen(report.approval?.reviewer ?? report.decided_by, report.decided_at);
  const scopeCollection = report.diagnostic_ids.length === 0;

  return (
    <section aria-label="Decision" className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        {report.status === "accepted" ? <StatusPill status="accepted" /> : null}
        {report.status === "rejected" ? <StatusPill status="rejected" /> : null}
        {report.status === "reverted" ? <StatusPill status="reverted" /> : null}
        {report.status === "reverting" ? (
          <span className="text-caption font-medium text-muted-foreground">Reverting</span>
        ) : null}
      </div>

      {/* Polite live region: the decision line announces when it changes. */}
      <div role="status" aria-live="polite" className="mt-2 flex flex-col gap-1.5">
        {report.status === "accepted" ? (
          <>
            <p className="text-body">{approvalSentence(report, taskId ? task : null)}</p>
            <p className="text-caption text-muted-foreground">Accepted by {acceptedBy}</p>
          </>
        ) : null}

        {report.status === "reverting" ? (
          <p className="text-body">Reverting the approval: removing the update from accepted knowledge.</p>
        ) : null}

        {report.status === "reverted" ? (
          <>
            <p className="text-body">
              Approval reverted by {whoAndWhen(report.reverted_by ?? report.revert?.by, report.reverted_at ?? report.revert?.at)}
              : {updatesPhrase(updates)} removed from accepted knowledge.
            </p>
            {report.revert?.note ? (
              <p className="text-caption text-muted-foreground">Reason: {report.revert.note}</p>
            ) : null}
            <p className="text-caption text-muted-foreground">Accepted by {acceptedBy}</p>
          </>
        ) : null}

        {report.status === "rejected" ? (
          <>
            <p className="text-body">Rejected by {whoAndWhen(report.decided_by, report.decided_at)}.</p>
            {report.note ? <p className="text-caption text-muted-foreground">Reason: {report.note}</p> : null}
          </>
        ) : null}

        {approved && report.status !== "reverting" ? (
          <p className="text-caption text-muted-foreground">
            {report.status === "reverted" ? (
              <>
                {scopeCollection
                  ? "Removed from the scope's evidence collection."
                  : "Removed from accepted knowledge."}
              </>
            ) : scopeCollection ? (
              "Accepted into the scope's evidence collection."
            ) : (
              <span className="flex flex-wrap gap-x-3">
                {report.diagnostic_ids.map((id) => (
                  <Link key={id} href={`/diagnostics/${encodeURIComponent(id)}`} className="underline underline-offset-2">
                    Open accepted knowledge<span className="sr-only"> for {id}</span>
                  </Link>
                ))}
              </span>
            )}
          </p>
        ) : null}

        {report.status === "reverted" || report.status === "reverting" ? (
          <p className="text-body">{revertTaskSentence(taskId ? task : null) ?? ""}</p>
        ) : null}
      </div>

      {report.status === "rejected" ? (
        <p className="mt-2 text-caption text-muted-foreground">Not run: the report was rejected. No follow-up task was authorised.</p>
      ) : null}

      <MemoryLine report={report} />

      {taskId && report.status !== "rejected" ? (
        <div className="mt-3">
          <TaskPanel report={report} taskId={taskId} />
        </div>
      ) : null}

      <RevertControl report={report} />
    </section>
  );
}

/**
 * "Memory saved" appears only when the report names a memory, which exists only
 * after `memory.create()` succeeded (V46). If a reject or a correction has no
 * memory, say so and offer the retry that repairs it.
 */
function MemoryLine({ report }: { report: Report }) {
  const correction = report.approval?.correction?.trim() || null;
  const expectsMemory = report.status === "rejected" || (report.status === "accepted" && Boolean(correction));
  const [retrying, setRetrying] = useState(false);

  if (report.memory_id) {
    return (
      <p className="mt-2 flex flex-wrap items-center gap-1.5 text-caption text-muted-foreground">
        <Brain className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
        Memory saved: <span className="text-identifier text-foreground">{shortId(report.memory_id)}</span>. It informs the
        agent&apos;s wording next time; it never changes permissions.
      </p>
    );
  }
  if (!expectsMemory) return null;

  const mode: FormMode = report.status === "rejected" ? "reject" : "correct";
  return (
    <div className="mt-2 flex flex-col gap-2">
      <p className="flex items-center gap-1.5 text-caption text-muted-foreground" role="status">
        <TriangleAlert className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
        The memory has not been saved yet. Retry the decision to save it.
      </p>
      {retrying ? (
        <RetryForm report={report} mode={mode} initialNote={correction ?? report.note ?? ""} onClose={() => setRetrying(false)} />
      ) : (
        <div>
          <Button type="button" variant="secondary" size="sm" onClick={() => setRetrying(true)}>
            Retry saving the memory
          </Button>
        </div>
      )}
    </div>
  );
}

function RetryForm({
  report,
  mode,
  initialNote,
  onClose,
}: {
  report: Report;
  mode: FormMode;
  initialNote: string;
  onClose: () => void;
}) {
  const { mutate } = useSWRConfig();
  const refresh = useRefreshRelated();
  const { can } = useActions();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(values: DecisionFormValues) {
    if (!can("decide_report")) {
      setError("Not allowed: this sign-in cannot decide reports.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await post("/reports/{report_id}/decision", {
        path: { report_id: report.id },
        body:
          mode === "reject"
            ? { action: "reject", note: values.note, claim_kind: values.claimKind }
            : { action: "approve", note: values.note, correction: values.note, claim_kind: values.claimKind },
      });
      await mutate(buildPath("/reports/{report_id}", { path: { report_id: report.id } }), res.report, {
        revalidate: false,
      });
      if (res.memory) toast.success("Memory saved.");
      else setError("The memory still was not saved. Try again.");
      refresh();
      if (res.memory) onClose();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  return <DecisionForm mode={mode} initialNote={initialNote} submitting={busy} error={error} onSubmit={submit} onCancel={onClose} />;
}
