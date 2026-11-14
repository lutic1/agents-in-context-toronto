/**
 * The typed adapter between the interview page and `@heygen/liveavatar-web-sdk` (0.0.20), FULL mode (V70).
 *
 * What it does, and the sandbox test that fixed each rule (CONDITIONAL PASS):
 * - `repeat(text)` is the only way anything is spoken. It sends "speak exactly this text". The SDK's other
 *   speaking call hands the words to the avatar's own language model, so nothing here ever calls it.
 * - Listening stays off: the SDK's listening call is never made, and if a `user.*` event (speech or a
 *   transcription chunk) ever arrives the session is stopped at once.
 * - Speech is only ever the reply to a `repeat`. If the avatar starts speaking with no `repeat` pending, the
 *   session is stopped at once. Each `repeat` first interrupts whatever is still being spoken.
 * - SDK 0.0.20 ALWAYS asks the browser for the microphone when a session starts, even muted. So the claim is
 *   "the microphone is never granted", not "never requested". Three layers: (1) the server sends
 *   `Permissions-Policy: microphone=()` for this page (next.config.ts, owned by B01; see the report), (2) this
 *   file makes any audio `getUserMedia` call fail with NotAllowedError while the session lives, which the SDK
 *   swallows (the sandbox "denied" run: session starts, `repeat` speaks, mic never captured), and (3) the
 *   session config is `voiceChat: { defaultMuted: true }`. The voice-chat default would open the mic unmuted.
 * - The session is stopped on `pagehide`, on unmount and when it ends by itself (a token's duration cap).
 */

import type { LiveAvatarSession } from "@heygen/liveavatar-web-sdk";

export type CloseReason = "stopped" | "ended" | "mic_activity" | "unsolicited_speech";

export type AvatarHandlers = {
  onSpeakStarted: () => void;
  onSpeakEnded: () => void;
  /** The session is over (stopped, the duration cap, a network failure or the server). Fires once. */
  onClosed: (why: CloseReason) => void;
  /** `repeat` threw (for example the session was not connected). The text answer is unaffected. */
  onSpeakFailed: () => void;
};

export type AvatarAdapter = {
  /** Speak exactly this text, unchanged. */
  speak(text: string): void;
  /** End the session. Safe to call more than once. */
  stop(): Promise<void>;
};

export type AvatarStartFailure = "mic_unconfirmed" | "sdk_unavailable" | "start_failed";

export class AvatarStartError extends Error {
  readonly reason: AvatarStartFailure;
  constructor(reason: AvatarStartFailure) {
    super(`Avatar did not start (${reason}).`);
    this.name = "AvatarStartError";
    this.reason = reason;
  }
}

type PolicyApi = { allowsFeature?: (feature: string) => boolean };

/** True when this document's Permissions-Policy already blocks the microphone (layer 1). */
export function policyBlocksMicrophone(doc: Document = document): boolean {
  const anyDoc = doc as unknown as { permissionsPolicy?: PolicyApi; featurePolicy?: PolicyApi };
  const policy = anyDoc.permissionsPolicy ?? anyDoc.featurePolicy;
  return typeof policy?.allowsFeature === "function" && policy.allowsFeature("microphone") === false;
}

type MicGuard = { confirmed: boolean; restore: () => void };

/** Layer 2: refuse every audio capture request until `restore()`. Video-only requests pass through. */
export function blockMicrophone(): MicGuard {
  const policy = policyBlocksMicrophone();
  const devices = typeof navigator === "undefined" ? undefined : navigator.mediaDevices;
  if (!devices || typeof devices.getUserMedia !== "function") {
    // No capture API at all (an insecure context): nothing can open the microphone.
    return { confirmed: true, restore: () => {} };
  }
  const original = devices.getUserMedia;
  const hadOwn = Object.prototype.hasOwnProperty.call(devices, "getUserMedia");
  try {
    devices.getUserMedia = function guarded(this: MediaDevices, constraints?: MediaStreamConstraints) {
      if (constraints && constraints.audio) {
        return Promise.reject(new DOMException("The microphone is blocked on this page.", "NotAllowedError"));
      }
      return original.call(devices, constraints);
    };
  } catch {
    return { confirmed: policy, restore: () => {} };
  }
  return {
    confirmed: true,
    restore: () => {
      try {
        if (hadOwn) devices.getUserMedia = original;
        else delete (devices as { getUserMedia?: unknown }).getUserMedia;
      } catch {
        /* nothing to restore */
      }
    },
  };
}

type Sdk = typeof import("@heygen/liveavatar-web-sdk");

async function loadSdk(): Promise<Sdk> {
  try {
    return await import("@heygen/liveavatar-web-sdk");
  } catch {
    throw new AvatarStartError("sdk_unavailable");
  }
}

/** Join the session with the short-lived token, play the avatar in `video`, and hand back the two things the page may do. */
export async function startAvatar(token: string, video: HTMLVideoElement, handlers: AvatarHandlers): Promise<AvatarAdapter> {
  const sdk = await loadSdk();
  const guard = blockMicrophone();
  if (!guard.confirmed) throw new AvatarStartError("mic_unconfirmed");

  const session: LiveAvatarSession = new sdk.LiveAvatarSession(token, {
    // Layer 3. The default is `{}`, which would turn the microphone on unmuted.
    voiceChat: { defaultMuted: true },
  });

  let closed = false;
  const close = (why: CloseReason) => {
    if (closed) return;
    closed = true;
    guard.restore();
    handlers.onClosed(why);
  };

  session.on(sdk.SessionEvent.SESSION_STREAM_READY, () => session.attach(video));
  session.on(sdk.SessionEvent.SESSION_DISCONNECTED, () => close("ended"));
  session.on(sdk.AgentEventsEnum.SESSION_STOPPED, () => close("ended"));
  // True from a `repeat` until the avatar starts speaking it. One `repeat` allows one start; any other start was
  // not asked for. (Not cleared on speak-ended: an interrupt can end the old speech after the next `repeat`.)
  let repeatPending = false;
  const shutDown = (why: CloseReason) => {
    repeatPending = false;
    void session.stop().catch(() => {});
    close(why);
  };
  session.on(sdk.AgentEventsEnum.AVATAR_SPEAK_STARTED, () => {
    if (closed) return;
    if (!repeatPending) {
      shutDown("unsolicited_speech");
      return;
    }
    repeatPending = false;
    handlers.onSpeakStarted();
  });
  session.on(sdk.AgentEventsEnum.AVATAR_SPEAK_ENDED, () => handlers.onSpeakEnded());
  // Listening is off. If the platform ever reports the user speaking, end the session rather than carry on.
  const heard = () => shutDown("mic_activity");
  session.on(sdk.AgentEventsEnum.USER_SPEAK_STARTED, heard);
  session.on(sdk.AgentEventsEnum.USER_TRANSCRIPTION, heard);
  session.on(sdk.AgentEventsEnum.USER_TRANSCRIPTION_CHUNK, heard);

  try {
    await session.start();
  } catch {
    closed = true;
    guard.restore();
    throw new AvatarStartError("start_failed");
  }

  return {
    speak(text: string) {
      if (closed || text.trim().length === 0) return;
      try {
        // Cut off anything still being spoken so two answers never overlap.
        session.interrupt();
        repeatPending = true;
        session.repeat(text);
      } catch {
        repeatPending = false;
        handlers.onSpeakFailed();
      }
    },
    async stop() {
      if (closed) return;
      try {
        await session.stop();
      } catch {
        /* the session is gone either way */
      }
      close("stopped");
    },
  };
}
