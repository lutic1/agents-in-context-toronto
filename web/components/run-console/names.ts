import type { ActionKind, Destination } from "@/components/run-console/types";

/** Action kinds always appear under these names (EXPERIENCE "Voice and Tone"). */
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
};

export function kindName(kind: string): string {
  return KIND_NAMES[kind as ActionKind] ?? kind.replace(/_/g, " ");
}

const DESTINATION_NAMES: Record<Destination, string> = {
  ledger: "Ledger",
  "slack:#all-mango-db-hackathon": "#all-mango-db-hackathon",
  "source:clinicaltrials.gov": "ClinicalTrials.gov",
  "tts:elevenlabs": "ElevenLabs",
  "video:heygen": "HeyGen",
};

export function destinationName(destination: string): string {
  return DESTINATION_NAMES[destination as Destination] ?? destination;
}

/** The five checks always appear under these names, in this order. */
const CHECK_NAMES: Record<string, string> = {
  grant_active: "Grant active",
  team_scope: "Diagnostic in team scope",
  destination_action: "Destination and action match the grant",
  evidence_checks: "Evidence checks passed",
  run_authorised: "Run still authorised",
};

export function checkName(check: string): string {
  return CHECK_NAMES[check] ?? check.replace(/_/g, " ");
}

/** The claim checks, shown by name under "Evidence checks passed" (V7). */
const CLAIM_NAMES: Record<string, string> = {
  claim_performed_or_results: "Performed or results only if reported",
  claim_planned: "Planned or recruiting described as such",
  claim_preclinical: "Cell-line or animal labelled preclinical",
};

export function claimName(kind: string): string {
  return CLAIM_NAMES[kind] ?? kind.replace(/_/g, " ");
}

/** `clinicaltrials.gov:NCT04712877` is shown as `NCT04712877`. */
export function sourceLabel(ref: string): string {
  const at = ref.indexOf(":");
  return at >= 0 ? ref.slice(at + 1) : ref;
}
