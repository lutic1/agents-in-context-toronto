import { ApiError, isUnreachable, parseResponse } from "@/lib/api";
import type { components } from "@/lib/types";

/**
 * The one call the interview page makes to transcribe a recorded question (V73). The raw audio goes through B01's
 * proxy, which adds the key server-side; the backend sends it to ElevenLabs speech-to-text behind the gate and
 * never stores it. The result is text for the user to read and edit. It is never submitted automatically.
 */

export type TranscribeResponse = components["schemas"]["TranscribeResponse"];

export type VoiceRefusal = "blocked" | "too_long" | "unavailable";

export type VoiceOutcome =
  | { kind: "text"; text: string }
  | { kind: "empty" }
  | { kind: "refused"; reason: VoiceRefusal };

/** What the page shows for each refusal. Fixed wording; the backend's text is never shown in its place. */
export const VOICE_MESSAGES: Record<VoiceRefusal | "empty" | "denied" | "unsupported", string> = {
  blocked: "Recording not allowed",
  too_long: "Recording too long — keep it under 30 seconds",
  unavailable: "Transcription unavailable — type your question",
  empty: "No speech was heard — try again or type your question",
  denied: "Microphone access was not given — type your question",
  unsupported: "This browser cannot record — type your question",
};

/** The disclosure, always shown beside the record button. */
export const VOICE_DISCLOSURE = "Your recording is sent to ElevenLabs to be transcribed. DxP does not store it.";

function refusal(reason: string | null | undefined): VoiceRefusal {
  return reason === "blocked" || reason === "too_long" ? reason : "unavailable";
}

/** POST the clip as the raw body. Every failure becomes a refusal the page can show; nothing throws. */
export async function transcribe(reportId: string, clip: Blob): Promise<VoiceOutcome> {
  try {
    const res = await fetch(`/api/dxp/reports/${encodeURIComponent(reportId)}/interview/transcribe`, {
      method: "POST",
      headers: { "Content-Type": clip.type },
      body: clip,
      cache: "no-store",
    });
    const body = await parseResponse<TranscribeResponse>(res);
    if (body.refused) return { kind: "refused", reason: refusal(body.refusal_reason) };
    const text = (body.text ?? "").trim();
    return text ? { kind: "text", text } : { kind: "empty" };
  } catch (error) {
    if (isUnreachable(error)) return { kind: "refused", reason: "unavailable" };
    if (error instanceof ApiError) {
      if (error.status === 413) return { kind: "refused", reason: "too_long" };
      if (error.status === 401 || error.status === 403) return { kind: "refused", reason: "blocked" };
    }
    // Flag off (404), not accepted (409), not implemented (501), a network error or anything else.
    return { kind: "refused", reason: "unavailable" };
  }
}
