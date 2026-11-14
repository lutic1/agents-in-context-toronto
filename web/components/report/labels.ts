/** Small text helpers shared by the report, list and accepted knowledge screens. */

/** The NCT ID inside a source reference such as `NCT04712877` or `nct:NCT04712877`, or null. */
export function nctIdOf(ref: string | null | undefined): string | null {
  if (!ref) return null;
  const match = /NCT\d{8}/i.exec(ref);
  return match ? match[0].toUpperCase() : null;
}

/** The public ClinicalTrials.gov page for an NCT ID. */
export function trialUrl(nctId: string): string {
  return `https://clinicaltrials.gov/study/${encodeURIComponent(nctId)}`;
}

/** A registry status word as the source writes it, in sentence case: `ACTIVE_NOT_RECRUITING` becomes "Active not recruiting". */
export function statusWord(raw: string | null | undefined): string {
  if (!raw) return "";
  const text = raw.replace(/_/g, " ").trim().toLowerCase();
  return text ? text[0].toUpperCase() + text.slice(1) : "";
}

/** A canonical snake_case key as a label: `lifecycle_stage` becomes "Lifecycle stage". */
export function keyLabel(key: string): string {
  const text = key.replace(/_/g, " ").trim();
  return text ? text[0].toUpperCase() + text.slice(1) : key;
}

/** Where a related-evidence label sorts: relationships first, "related" last. */
export const LABEL_ORDER = ["supports", "contradicts", "extends", "new_question", "related_unestablished"] as const;
