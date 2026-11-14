/**
 * Feature flags for what the web app displays (AD-14, V38).
 *
 * Read from NEXT_PUBLIC_DXP_FEATURES, a comma or space separated list of flag
 * names, for example "briefing,avatar,memory_edit". A name may carry "=off",
 * "=false" or "=0" to switch it off explicitly. Everything is off when the
 * variable is empty or missing, so the shell and every core screen work with
 * every flag off.
 *
 * These flags only control display. The backend reads the same names from its
 * own DXP_FEATURES, and only that decides whether an approved task is queued
 * and started (V38). There is no task start button anywhere in the app.
 */

export const FEATURE_NAMES = [
  "briefing",
  "avatar",
  "memory_edit",
  "task_run",
  "revert",
  "live_stream",
] as const;

export type FeatureName = (typeof FEATURE_NAMES)[number];
export type Features = Record<FeatureName, boolean>;

const OFF_VALUES = new Set(["0", "false", "off", "no"]);

/** Parse the raw variable value. Unknown names are ignored. */
export function parseFeatures(raw: string | undefined | null): Features {
  const flags = Object.fromEntries(
    FEATURE_NAMES.map((name) => [name, false]),
  ) as Features;
  if (!raw) return flags;
  for (const token of raw.split(/[\s,]+/)) {
    if (!token) continue;
    const [name, value] = token.split("=");
    const key = name.trim().toLowerCase() as FeatureName;
    if (!(FEATURE_NAMES as readonly string[]).includes(key)) continue;
    flags[key] = value === undefined ? true : !OFF_VALUES.has(value.trim().toLowerCase());
  }
  return flags;
}

// The literal property access lets Next.js inline the value into the client bundle.
export const features: Features = parseFeatures(
  process.env.NEXT_PUBLIC_DXP_FEATURES,
);

export function isEnabled(flag: FeatureName): boolean {
  return features[flag];
}
