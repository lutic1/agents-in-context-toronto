import "server-only";

/**
 * The one place the server talks to the DxP API with the reviewer key.
 *
 * DXP_API_KEY is read here, on the server only. It is never NEXT_PUBLIC_, is
 * never logged, and is never put in a response. NEXT_PUBLIC_API_URL is the API
 * origin; the API itself lives under `/api/v1` (AD-9).
 */

export class UpstreamConfigError extends Error {
  constructor() {
    super("API access is not configured on the web server.");
    this.name = "UpstreamConfigError";
  }
}

/** Upstream timeout. Nothing in the app waits longer than 30 seconds (AD-9). */
const TIMEOUT_MS = 30_000;

function config(): { base: string; key: string } {
  const origin = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, "");
  const key = process.env.DXP_API_KEY?.trim();
  if (!origin || !key) throw new UpstreamConfigError();
  return { base: `${origin}/api/v1`, key };
}

/**
 * Fetch `<api>/api/v1/<path>` with the X-DxP-Key header added. `path` may carry a
 * query string. Throws UpstreamConfigError when the variables are missing, and
 * lets a network error or timeout propagate to the caller.
 */
export async function upstreamFetch(
  path: string,
  init: { method?: string; headers?: Record<string, string>; body?: BodyInit | null } = {},
): Promise<Response> {
  const { base, key } = config();
  const clean = path.replace(/^\/+/, "");
  return fetch(`${base}/${clean}`, {
    method: init.method ?? "GET",
    headers: { ...init.headers, "X-DxP-Key": key },
    body: init.body ?? undefined,
    cache: "no-store",
    redirect: "manual",
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
}
