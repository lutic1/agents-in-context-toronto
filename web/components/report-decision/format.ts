import type { components } from "@/lib/types";
import { features } from "@/lib/features";
import { displayName } from "@/lib/format";

export type Report = components["schemas"]["Report"];
export type Task = components["schemas"]["Task"];
export type Memory = components["schemas"]["Memory"];

/** A time of day such as "15:42", in the viewer's time zone. For client components only. */
export function clock(value: string | null | undefined): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
}

/** "Sam at 15:42", leaving out whatever is missing. */
export function whoAndWhen(who: string | null | undefined, at: string | null | undefined): string {
  const name = who ? displayName(who) : "";
  const time = clock(at);
  if (name && time) return `${name} at ${time}`;
  return name || (time ? `at ${time}` : "");
}

/** The number of updates the report proposed (at least one, so a sentence never says "0 updates accepted"). */
export function updateCount(report: Report): number {
  return Math.max(1, report.proposal_ids.length);
}

export function updatesPhrase(count: number): string {
  return `${count} ${count === 1 ? "update" : "updates"}`;
}

/** Drop a trailing full stop so a reason can sit inside a sentence that adds its own. */
export function trimStop(text: string): string {
  return text.trim().replace(/[.\s]+$/, "");
}

const NOT_AUTHORISED = "Follow-up task not authorised:";

/**
 * The approval sentence (V27, V38, V45, V62), built from the stored report and
 * task so it reads the same after a reload as right after the click.
 * `task` is undefined while it is still loading.
 */
export function approvalSentence(report: Report, task: Task | null | undefined): string {
  const head = `Approved: ${updatesPhrase(updateCount(report))} accepted.`;
  const step = report.approval?.task_step;
  if (step === "blocked") {
    const stored = report.approval?.reason?.trim() ?? "";
    // A24 stores the full sentence ("Follow-up task not authorised: <reason>"); use it as-is then.
    if (stored.startsWith(NOT_AUTHORISED)) return `${head} ${trimStop(stored)}.`;
    return `${head} ${NOT_AUTHORISED} ${stored ? trimStop(stored) : "no reason was recorded"}.`;
  }
  if (step === "pending") return `${head} Follow-up task authorisation is being completed.`;
  // Without the task (still loading, or the read failed), word it from the `task_run` flag (V27, V38).
  const notRun = task ? task.status === "authorised" : !features.task_run;
  if (notRun) return `${head} Follow-up task authorised; not run.`;
  return `${head} Follow-up task authorised; its findings will be pending review.`;
}

/** The task's outcome after a revert, in the words of EXPERIENCE "Revert approval". */
export function revertTaskSentence(task: Task | null | undefined): string | null {
  if (!task) return null;
  switch (task.status) {
    case "cancelled":
    case "authorised":
    case "queued":
      return "Follow-up task cancelled; its grant expired.";
    case "running":
    case "stopped":
      return "Follow-up task stop requested.";
    default:
      return "Follow-up task had finished; its findings stay pending review.";
  }
}
