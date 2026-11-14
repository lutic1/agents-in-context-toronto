import type { components } from "@/lib/types";

/**
 * The avatar is now a HeyGen LiveAvatar, a live session (pending Luis's approval as V70). A01's
 * `AvatarResponse` is `{ media, decision }` and has no field for the session token, and B08 may not
 * edit `lib/types.ts`, so this local type adds what `POST /reports/<report_id>/avatar` also returns.
 * The proposed contract change is in the B08 report; when it merges and `npm run gen:types` runs,
 * replace this with the generated type.
 */
export type AvatarSessionInfo = {
  session_id: string;
  /** Single use and secret: held in memory only, never stored, logged or shown. */
  session_token: string;
  /** Seconds. The session ends by itself at this limit. */
  max_session_duration: number;
  provider: "liveavatar";
};

export type AvatarUnavailableReason = "blocked" | "no_key" | "no_avatar" | "provider_error";

export type AvatarStartResponse = components["schemas"]["AvatarResponse"] & {
  session: AvatarSessionInfo | null;
  unavailable_reason: AvatarUnavailableReason | null;
};
