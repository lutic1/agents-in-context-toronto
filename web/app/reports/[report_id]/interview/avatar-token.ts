import { ApiError, isUnreachable, post } from "@/lib/api";

/**
 * Where the avatar's session token comes from. The interview page calls this only when the user clicks
 * "Start avatar". Today the token comes from `POST /reports/<report_id>/avatar` (gated `generate_avatar_video`,
 * B08's LiveAvatar session-token route) through B01's proxy. The LiveAvatar key never reaches the browser; only
 * this short-lived, single-use session token does. If the token source changes, only this file changes.
 */

export type AvatarToken = {
  /** Single use and secret: held in memory, never stored, logged or shown. */
  token: string;
  /** Seconds; the session ends by itself at this limit. Null when the API does not say. */
  maxSeconds: number | null;
};

export type AvatarTokenFailure = "blocked" | "unavailable" | "unreachable";

export class AvatarTokenError extends Error {
  readonly reason: AvatarTokenFailure;
  constructor(reason: AvatarTokenFailure) {
    super(`No avatar session token (${reason}).`);
    this.name = "AvatarTokenError";
    this.reason = reason;
  }
}

/**
 * B08 returns `AvatarResponse` plus `session { session_token, max_session_duration }` and `unavailable_reason`.
 * Those two extra fields are not in the generated types yet (A01 owns them), so they are read defensively
 * from the unknown body instead of being typed.
 */
function readSession(body: unknown): AvatarToken | null {
  if (!body || typeof body !== "object") return null;
  const session = (body as { session?: unknown }).session;
  if (!session || typeof session !== "object") return null;
  const { session_token: token, max_session_duration: max } = session as Record<string, unknown>;
  if (typeof token !== "string" || token.length === 0) return null;
  return { token, maxSeconds: typeof max === "number" ? max : null };
}

export async function requestAvatarToken(reportId: string): Promise<AvatarToken> {
  let body: unknown;
  try {
    body = await post("/reports/{report_id}/avatar", { path: { report_id: reportId } });
  } catch (error) {
    if (isUnreachable(error)) throw new AvatarTokenError("unreachable");
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw new AvatarTokenError("blocked");
    throw new AvatarTokenError("unavailable");
  }
  const token = readSession(body);
  if (token) return token;
  const reason = (body as { unavailable_reason?: unknown } | null)?.unavailable_reason;
  throw new AvatarTokenError(reason === "blocked" ? "blocked" : "unavailable");
}
