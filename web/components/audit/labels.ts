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

import type { components } from "@/lib/types";
import { formatPolicySet } from "@/lib/format";

/**
 * Types and words for the Audit view. The screen renders what the API returns
 * (AD-6); the only decisions made here are which words and icon go with a
 * status the API already named (EXPERIENCE "Voice and Tone", DESIGN "Icons").
 */

type Schemas = components["schemas"];

export type Audit = Schemas["Audit"];
export type AuditEntry = Schemas["AuditEntry"];
export type AuditSource = Schemas["AuditSource"];
export type Run = Schemas["Run"];
export type Decision = Schemas["Decision"];
export type Report = Schemas["Report"];
export type Task = Schemas["Task"];
export type Grant = Schemas["Grant"];
export type Policy = Schemas["Policy"];
export type Relationship = Schemas["Relationship"];
export type MemoryUse = Schemas["MemoryUse"];
export type Retrieval = Schemas["Retrieval"];
export type CheckResult = Schemas["CheckResult"];
export type ClaimCheck = Schemas["ClaimCheck"];
export type LinkedRun = Schemas["LinkedRun"];
export type ActionKind = AuditEntry["kind"];
export type Destination = AuditEntry["destination"];

export type SlackResult = Schemas["SlackResult"];
export type SearchSourceResult = Schemas["SearchSourceResult"];
export type LedgerResult = Schemas["LedgerResult"];

// ---- Action kinds ------------------------------------------------------------

const KIND_NAMES: Record<ActionKind, string> = {
  search_source: "Search source",
  file_proposal: "File report",
  file_related_evidence: "File related evidence",
  notify_slack: "Send Slack alert",
  apply_value: "Apply value",
  generate_briefing: "Generate briefing",
  generate_avatar_video: "Generate avatar video",
  decide_report: "Decide report",
  authorise_task: "Authorise task",
  create_memory: "Create memory",
  correct_memory: "Correct memory",
  revoke_memory: "Revoke memory",
  review_value: "Review value",
  resolve_notification: "Resolve Slack alert",
  revert_report: "Revert approval",
  decide_proposal: "Decide proposal",
  answer_question: "Answer interview question",
};

/**
 * The kind as the Audit view names it. `file_proposal` is the report-level
 * kind ("File report", V24); a proposal-level one, such as the proposed link
 * of a record's mention to the scope that check 2 blocks, is named for what it is.
 */
export function kindName(entry: Pick<AuditEntry, "kind" | "report_id" | "retrieval">): string {
  if (entry.kind === "file_proposal" && !entry.report_id && !entry.retrieval) {
    return "File proposed update";
  }
  return KIND_NAMES[entry.kind];
}

const DESTINATION_NAMES: Record<Destination, string> = {
  ledger: "DxP ledger",
  "slack:#all-mango-db-hackathon": "#all-mango-db-hackathon",
  "source:clinicaltrials.gov": "ClinicalTrials.gov",
  "tts:elevenlabs": "ElevenLabs",
  "video:heygen": "HeyGen",
};

export function destinationName(destination: Destination): string {
  return DESTINATION_NAMES[destination] ?? destination;
}

/** What the entry is about: the report, else the source it quotes, else where it was going. */
export function entrySubject(entry: AuditEntry): string {
  return entry.report_id ?? entry.evidence_ref?.source_ref ?? destinationName(entry.destination);
}

// ---- Checks ------------------------------------------------------------------

/** The five gate checks in order: the API's ID for each, and its fixed name (V68). */
const CHECKS = [
  { id: "grant_active", name: "Grant active" },
  { id: "team_scope", name: "Diagnostic in team scope" },
  { id: "destination_action", name: "Destination and action match the grant" },
  { id: "evidence_checks", name: "Evidence checks passed" },
  { id: "run_authorised", name: "Run still authorised" },
] as const;

/**
 * The name of a gate check. The API names a check by its ID (`grant_active`); when it
 * already sends a name, that is kept. A text that is neither falls back to the check's
 * fixed name by position, when the caller knows it.
 */
export function checkName(check: string, index?: number): string {
  const byId = CHECKS.find((c) => c.id === check);
  if (byId) return byId.name;
  if (/^[A-Z][a-z]+ /.test(check)) return check;
  return (index === undefined ? undefined : CHECKS[index]?.name) ?? check;
}

/** The blocked line's check: its name, never its ID. */
export function failedCheckName(entry: Pick<AuditEntry, "failed_check" | "checks">): string {
  const failed = entry.failed_check;
  if (!failed) return "a check";
  const position = (entry.checks ?? []).findIndex((c) => c.check === failed);
  return checkName(failed, position >= 0 ? position : undefined);
}

const CLAIM_NAMES: Record<string, string> = {
  claim_performed_or_results: "Performed or results only if reported",
  claim_planned: "Planned or recruiting described as such",
  claim_preclinical: "Cell-line or animal labelled preclinical",
};

export function claimName(kind: string): string {
  return CLAIM_NAMES[kind] ?? kind;
}

/** "Blocked before it ran: {check} failed under policy set ps_ab12… (N policies)." */
export function policySetText(
  version: string | null | undefined,
  run: Pick<Run, "policy_set_version">,
  policies: Policy[],
): string {
  if (!version) return "";
  const count = version === run.policy_set_version ? policies.length : undefined;
  return formatPolicySet(version, count);
}

// ---- Entry state -------------------------------------------------------------

export type Tone = "destructive" | "accepted" | "caution" | "muted" | "ink";

export const TONE_CLASS: Record<Tone, string> = {
  destructive: "text-destructive",
  accepted: "text-accepted",
  caution: "text-low-confidence",
  muted: "text-muted-foreground",
  ink: "text-foreground",
};

export type EntryState = {
  key:
    | "blocked"
    | "claim_blocked"
    | "queued"
    | "dispatching"
    | "reconciling"
    | "delivered"
    | "unknown"
    | "failed"
    | "done"
    | "allowed";
  word: string;
  icon: LucideIcon;
  tone: Tone;
};

export function isClaimBlocked(entry: Pick<AuditEntry, "outcome" | "claims">): boolean {
  return entry.outcome === "blocked" && (entry.claims ?? []).some((c) => !c.passed);
}

/** The state mark of an entry: an icon and a word, never colour alone. */
export function entryState(entry: AuditEntry): EntryState {
  if (entry.outcome === "blocked") {
    return isClaimBlocked(entry)
      ? { key: "claim_blocked", word: "Claim blocked", icon: ShieldX, tone: "destructive" }
      : { key: "blocked", word: "Blocked", icon: ShieldX, tone: "destructive" };
  }
  switch (entry.status) {
    case "queued":
      return { key: "queued", word: "Allowed, queued", icon: ShieldCheck, tone: "muted" };
    case "dispatching":
      return { key: "dispatching", word: "Dispatching", icon: Send, tone: "muted" };
    case "reconciling":
      return { key: "reconciling", word: "Reconciling", icon: RefreshCw, tone: "caution" };
    case "delivered":
      return entry.kind === "notify_slack"
        ? { key: "delivered", word: "Slack alert delivered", icon: Bell, tone: "accepted" }
        : { key: "delivered", word: "Took effect", icon: CircleCheck, tone: "accepted" };
    case "unknown":
      return { key: "unknown", word: "Result unknown", icon: CircleHelp, tone: "caution" };
    case "failed":
      return { key: "failed", word: "Failed", icon: CircleX, tone: "destructive" };
    case "done":
      return entry.kind === "file_proposal" && entry.report_id
        ? { key: "done", word: "Report filed (pending review)", icon: CircleCheck, tone: "accepted" }
        : { key: "done", word: "Took effect", icon: CircleCheck, tone: "accepted" };
    default:
      return { key: "allowed", word: "Allowed", icon: ShieldCheck, tone: "accepted" };
  }
}

/** The entries the feed announces to a screen reader: blocked, claim blocked, failed and unknown (Accessibility Floor). */
export function isAnnounced(entry: AuditEntry): boolean {
  const key = entryState(entry).key;
  return key === "blocked" || key === "claim_blocked" || key === "failed" || key === "unknown";
}

// ---- Result guards -------------------------------------------------------------

type Result = AuditEntry["result"];

export function asSlackResult(result: Result): SlackResult | null {
  return result && "link_urls" in result ? result : null;
}

export function asSearchResult(result: Result): SearchSourceResult | null {
  return result && "source_refs" in result && "count" in result ? result : null;
}

export function asLedgerResult(result: Result): LedgerResult | null {
  return result && "proposal_ids" in result ? result : null;
}

// ---- Small shared helpers ------------------------------------------------------

/**
 * The registry ID inside a source ref, or null. The API stores a trial as
 * `clinicaltrials.gov:NCT04712877` (D40); the ID itself is `NCT04712877`.
 */
export function nctId(ref: string): string | null {
  const bare = ref.replace(/^clinicaltrials\.gov:/i, "");
  return /^NCT\d{8}$/.test(bare) ? bare : null;
}

/** A source ref that names a ClinicalTrials.gov record, with or without its `clinicaltrials.gov:` prefix. */
export function isNct(ref: string): boolean {
  return nctId(ref) !== null;
}

/** The ClinicalTrials.gov page of a trial; the ref may carry its prefix. */
export function trialUrl(ref: string): string {
  return `https://clinicaltrials.gov/study/${encodeURIComponent(nctId(ref) ?? ref)}`;
}

/** An input value as one line of text, for the Inputs list. */
export function inputText(value: unknown): string {
  if (value === null || value === undefined) return "none";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

/** A run still producing decisions. */
export function isActiveRun(status: Run["status"]): boolean {
  return status === "running" || status === "stopping";
}
