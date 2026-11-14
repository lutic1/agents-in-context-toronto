import {
  Bell,
  CircleCheck,
  CircleHelp,
  CircleX,
  RefreshCw,
  Send,
  ShieldCheck,
  ShieldX,
  type LucideIcon,
} from "lucide-react";

import type { AuditEntry } from "@/components/run-console/types";

/**
 * The state of one gate decision, as the action row shows it (DESIGN "action-state-*").
 * Every state has an icon and a word; colour is never the only signal.
 */
export type EntryTone =
  | "pending"
  | "took-effect"
  | "delivered"
  | "blocked"
  | "claim-blocked"
  | "unknown"
  | "reconciling"
  | "failed";

export type EntryState = {
  tone: EntryTone;
  word: string;
  Icon: LucideIcon;
  /** Blocked, claim blocked, failed and unknown rows are announced as they appear. */
  announce: boolean;
};

/** The first failed claim check of a blocked entry, when the block was a claim block (V7). */
export function failedClaim(entry: AuditEntry) {
  if (entry.outcome !== "blocked") return null;
  return entry.claims.find((claim) => !claim.passed) ?? null;
}

export function entryState(entry: AuditEntry): EntryState {
  if (entry.outcome === "blocked") {
    return failedClaim(entry)
      ? { tone: "claim-blocked", word: "Claim blocked", Icon: ShieldX, announce: true }
      : { tone: "blocked", word: "Blocked", Icon: ShieldX, announce: true };
  }

  const status = entry.status ?? "queued";
  const slack = entry.kind === "notify_slack";

  switch (status) {
    case "delivered":
      return slack
        ? { tone: "delivered", word: "Slack alert delivered", Icon: Bell, announce: false }
        : { tone: "took-effect", word: "Done", Icon: CircleCheck, announce: false };
    case "done":
      return entry.kind === "file_proposal"
        ? { tone: "took-effect", word: "Report filed (pending review)", Icon: CircleCheck, announce: false }
        : entry.kind === "file_related_evidence"
          ? { tone: "took-effect", word: "Related evidence filed (pending review)", Icon: CircleCheck, announce: false }
          : { tone: "took-effect", word: "Done", Icon: CircleCheck, announce: false };
    case "dispatching":
      return { tone: "pending", word: "In flight", Icon: Send, announce: false };
    case "reconciling":
      return { tone: "reconciling", word: "Reconciling", Icon: RefreshCw, announce: false };
    case "unknown":
      return { tone: "unknown", word: "Result unknown", Icon: CircleHelp, announce: true };
    case "failed":
      return {
        tone: "failed",
        word: slack ? "Slack alert failed" : "Failed",
        Icon: CircleX,
        announce: true,
      };
    default:
      return { tone: "pending", word: "Allowed (queued)", Icon: ShieldCheck, announce: false };
  }
}

export type EntryTotals = {
  tookEffect: number;
  blocked: number;
  unknown: number;
  failed: number;
};

/** The totals behind "Stopped at 15:12. 3 took effect, 1 blocked, 0 unknown." */
export function totals(entries: AuditEntry[]): EntryTotals {
  const out: EntryTotals = { tookEffect: 0, blocked: 0, unknown: 0, failed: 0 };
  for (const entry of entries) {
    if (entry.outcome === "blocked") out.blocked += 1;
    else if (entry.status === "done" || entry.status === "delivered") out.tookEffect += 1;
    else if (entry.status === "unknown") out.unknown += 1;
    else if (entry.status === "failed") out.failed += 1;
  }
  return out;
}
