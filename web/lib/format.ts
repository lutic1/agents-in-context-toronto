/**
 * Display formats (D40). Identifiers are shown in the mono face by the
 * caller; these helpers only build the text.
 */

/** A grant as `{grant_id}@v{version}`, for example `lbdx@v1` or `task-3fa9@v1`. */
export function formatGrant(grantId: string, version: number | string): string {
  return `${grantId}@v${version}`;
}

/**
 * A policy set as `ps_ab12… (N policies)`. The hash is cut to four characters
 * after the `ps_` prefix.
 */
export function formatPolicySet(policySetVersion: string, policyCount?: number): string {
  const body = policySetVersion.startsWith("ps_")
    ? policySetVersion.slice(3)
    : policySetVersion;
  const short = `ps_${body.slice(0, 4)}…`;
  if (policyCount === undefined) return short;
  return `${short} (${policyCount} ${policyCount === 1 ? "policy" : "policies"})`;
}

/** The same policy set split in two, so a caller can set the hash in the mono face and the count in body text. */
export function formatPolicySetParts(
  policySetVersion: string,
  policyCount?: number,
): { hash: string; count: string } {
  const body = policySetVersion.startsWith("ps_")
    ? policySetVersion.slice(3)
    : policySetVersion;
  return {
    hash: `ps_${body.slice(0, 4)}…`,
    count: policyCount === undefined ? "" : `(${policyCount} ${policyCount === 1 ? "policy" : "policies"})`,
  };
}

/** Shorten a long derived ID for display, keeping its prefix: `run_ab12cd34…`. */
export function shortId(id: string, keep = 8): string {
  const at = id.indexOf("_");
  if (at < 0 || id.length - at - 1 <= keep) return id;
  return `${id.slice(0, at + 1 + keep)}…`;
}

/**
 * A date such as "14 Nov 2026". A date-only string ("2024-07-17", a registry
 * date) is shown as written, never shifted by the viewer's time zone; a full
 * timestamp is shown in the viewer's time zone, so use the time helpers in
 * client components (a server render runs in UTC and would not match the
 * browser). Empty for a missing value.
 */
export function formatDate(value: string | number | Date | null | undefined): string {
  const date = toDate(value);
  if (!date) return "";
  const dateOnly = typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
  // Fixed three-letter months: some ICU versions write "Sept" for September.
  const parts = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "numeric",
    year: "numeric",
    ...(dateOnly ? { timeZone: "UTC" } : {}),
  }).formatToParts(date);
  const pick = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  const month = MONTHS[Number(pick("month")) - 1] ?? "";
  return `${pick("day")} ${month} ${pick("year")}`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** A time of day such as "10:45:03", in the viewer's time zone. Shown in the mono face. */
export function formatTime(value: string | number | Date | null | undefined): string {
  const date = toDate(value);
  if (!date) return "";
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

/** "14 Nov 2026, 10:45" for a decision or filing time. */
export function formatDateTime(value: string | number | Date | null | undefined): string {
  const date = toDate(value);
  if (!date) return "";
  const time = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
  return `${formatDate(date)}, ${time}`;
}

/** Elapsed seconds as `m:ss`, for the briefing and video players. */
export function formatElapsed(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** A similarity or text score as a plain figure, never a bar or a percentage. */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined || Number.isNaN(score)) return "";
  return score.toFixed(2);
}

/** Display name for a principal: sentence case for a lower-case ID such as "sam". */
export function displayName(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "unknown";
  return trimmed === trimmed.toLowerCase() && /^[a-z]/.test(trimmed)
    ? trimmed[0].toUpperCase() + trimmed.slice(1)
    : trimmed;
}

/** Initials for the "Signed in as" avatar: one letter for a single name, two for more. */
export function initials(name: string): string {
  const parts = name.trim().split(/[\s._-]+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const letters = parts.length === 1 ? parts[0][0] : parts[0][0] + parts[1][0];
  return letters.toUpperCase();
}

function toDate(value: string | number | Date | null | undefined): Date | null {
  if (value === null || value === undefined || value === "") return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}
