import type { LiveAvatarSession } from "@heygen/liveavatar-web-sdk";

/**
 * The typed adapter between the player and `@heygen/liveavatar-web-sdk`.
 *
 * It exposes the few things the player needs: join a session with the token the API returned,
 * speak one text with `repeat()`, show captions, learn when the avatar stops, and stop. It never
 * calls `message()` (the avatar's own language model would then say something DxP did not write),
 * never calls `startListening()` and never unmutes the microphone.
 *
 * If the SDK cannot be loaded, `createAvatarAdapter` resolves to null and the player says
 * "Unavailable". The script stays on the page as text either way.
 */

export type AvatarAdapterHandlers = {
  /** The avatar began speaking. */
  onSpeakStarted: () => void;
  /** The avatar finished speaking. */
  onSpeakEnded: () => void;
  /** Words the avatar is saying, for captions. */
  onCaption: (text: string) => void;
  /** The session closed (stopped, max duration, a network failure or the server). Fires once. */
  onClosed: () => void;
};

export type AvatarAdapter = {
  /** Join the session and play the avatar's video and audio in this element. */
  start(video: HTMLVideoElement): Promise<void>;
  /** Speak exactly this text, unchanged (`repeat`, not `message`). */
  speak(text: string): void;
  /** End the session. Safe to call more than once. */
  stop(): Promise<void>;
};

type SdkModule = typeof import("@heygen/liveavatar-web-sdk");

/**
 * Load the SDK. The one place to change if the package moves.
 * `@heygen/liveavatar-web-sdk` is not in package.json yet (B01 owns it): until it is, the import
 * fails, this returns null and the player shows "Unavailable".
 */
async function loadSdk(): Promise<SdkModule | null> {
  try {
    return await import("@heygen/liveavatar-web-sdk");
  } catch {
    return null;
  }
}

// Event names from https://docs.liveavatar.com/docs/full-mode/events.md and the SDK's enums.
const STREAM_READY = "session.stream_ready";
const DISCONNECTED = "session.disconnected";
const SPEAK_STARTED = "avatar.speak_started";
const SPEAK_ENDED = "avatar.speak_ended";
const TRANSCRIPTION = "avatar.transcription";
const SESSION_STOPPED = "session.stopped";

export async function createAvatarAdapter(
  sessionToken: string,
  handlers: AvatarAdapterHandlers,
): Promise<AvatarAdapter | null> {
  const sdk = await loadSdk();
  if (!sdk) return null;

  const session: LiveAvatarSession = new sdk.LiveAvatarSession(sessionToken, {
    // Microphone off: voice chat is muted from the start, and the page never unmutes it.
    voiceChat: { defaultMuted: true },
  });

  let closed = false;
  const close = () => {
    if (closed) return;
    closed = true;
    handlers.onClosed();
  };

  let video: HTMLVideoElement | null = null;
  session.on(STREAM_READY, () => {
    if (video) session.attach(video);
  });
  session.on(SPEAK_STARTED, () => handlers.onSpeakStarted());
  session.on(SPEAK_ENDED, () => handlers.onSpeakEnded());
  session.on(TRANSCRIPTION, (event) => {
    const text = (event as { text?: unknown } | null)?.text;
    if (typeof text === "string" && text) handlers.onCaption(text);
  });
  session.on(DISCONNECTED, close);
  session.on(SESSION_STOPPED, close);

  return {
    async start(element) {
      video = element;
      await session.start();
    },
    speak(text) {
      session.repeat(text);
    },
    async stop() {
      if (closed) return;
      try {
        await session.stop();
      } finally {
        close();
      }
    },
  };
}
