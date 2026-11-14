import { ApiError, isUnreachable, post } from "@/lib/api";
import type { components } from "@/lib/types";

type AvatarResponse = components["schemas"]["AvatarResponse"];

/**
 * Where the avatar's session token comes from. The interview page calls this only when the user clicks
 * "Start avatar". Today the token comes from `POST /reports/<report_id>/avatar` (gated `generate_avatar_video`,
 * B08's LiveAvatar session-token route, returning A01's AvatarResponse) through B01's proxy. The LiveAvatar key never reaches the browser; only
 * this short-lived, single-use session token does. If the token source changes, only this file changes.
 */

export type AvatarToken = {
  /** Single use and secret: held in memory, never stored, logged or shown. */
  token: string;
  /** ISO time after which the token is no longer valid. Null when the API does not say. */
  expiresAt: string | null;
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
 * A01's `AvatarResponse` carries `session_token` and `session_expires_at` at the top level, beside `media` and
 * `decision`. A missing token with a blocked Decision is "blocked"; a missing token otherwise is "unavailable".
 */
export async function requestAvatarToken(reportId: string): Promise<AvatarToken> {
  let res: AvatarResponse;
  try {
    res = await post("/reports/{report_id}/avatar", { path: { report_id: reportId } });
  } catch (error) {
    if (isUnreachable(error)) throw new AvatarTokenError("unreachable");
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw new AvatarTokenError("blocked");
    throw new AvatarTokenError("unavailable");
  }
  if (res.decision?.outcome === "blocked") throw new AvatarTokenError("blocked");
  if (typeof res.session_token === "string" && res.session_token.length > 0) {
    return { token: res.session_token, expiresAt: res.session_expires_at ?? null };
  }
  throw new AvatarTokenError("unavailable");
}
