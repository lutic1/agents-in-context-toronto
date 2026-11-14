"use client";

import { MicOff, Video, VideoOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

import { startAvatar, type AvatarAdapter } from "./avatar-adapter";
import { AvatarTokenError, requestAvatarToken } from "./avatar-token";

type Phase = "idle" | "starting" | "ready" | "ended" | "unavailable";

/** What the page tells the user when the avatar cannot run. The text answer is always shown either way. */
const UNAVAILABLE: Record<string, string> = {
  blocked: "The policy gate did not allow the avatar for this report.",
  unreachable: "Couldn't reach the API to start the avatar.",
  unavailable: "The avatar service did not start a session.",
  mic_unconfirmed: "The microphone block could not be confirmed, so the avatar was not started.",
  sdk_unavailable: "The avatar player could not be loaded.",
  start_failed: "The avatar session could not start.",
};

/**
 * Optional avatar (V70), behind the `avatar` flag. It speaks only text the backend returned, with `repeat`.
 * The microphone is off and nothing is listened to. The answer text is always on the page, so a failure here
 * changes nothing else. The session starts only on "Start avatar" and stops on `pagehide`.
 */
export function AvatarPanel({
  reportId,
  onSpeaker,
}: {
  reportId: string;
  /** Hands the page a `speak(text)` while a session is ready, and null otherwise. */
  onSpeaker: (speak: ((text: string) => void) | null) => void;
}) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [speaking, setSpeaking] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const adapterRef = useRef<AvatarAdapter | null>(null);

  const stop = useCallback(async () => {
    const adapter = adapterRef.current;
    adapterRef.current = null;
    onSpeaker(null);
    setSpeaking(false);
    if (adapter) await adapter.stop();
  }, [onSpeaker]);

  useEffect(() => {
    const onPageHide = () => {
      void stop();
    };
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      void stop();
    };
  }, [stop]);

  async function start() {
    const video = videoRef.current;
    if (!video) return;
    setPhase("starting");
    setNote(null);
    try {
      const { token } = await requestAvatarToken(reportId);
      const adapter = await startAvatar(token, video, {
        onSpeakStarted: () => setSpeaking(true),
        onSpeakEnded: () => setSpeaking(false),
        onSpeakFailed: () => setNote("The avatar could not speak that. The answer is shown as text."),
        onClosed: (why) => {
          adapterRef.current = null;
          onSpeaker(null);
          setSpeaking(false);
          if (why === "mic_activity") {
            setPhase("unavailable");
            setNote("The avatar was stopped because microphone activity was reported. The microphone is meant to stay off.");
          } else {
            setPhase("ended");
          }
        },
      });
      adapterRef.current = adapter;
      onSpeaker((text) => adapter.speak(text));
      setPhase("ready");
    } catch (error) {
      const reason =
        error instanceof AvatarTokenError || (error instanceof Error && "reason" in error)
          ? String((error as { reason: unknown }).reason)
          : "unavailable";
      setPhase("unavailable");
      setNote(UNAVAILABLE[reason] ?? UNAVAILABLE.unavailable);
    }
  }

  return (
    <section aria-labelledby="avatar-heading" className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <h2 id="avatar-heading" className="flex items-center gap-2 text-heading">
        <Video className="size-[18px]" strokeWidth={1.75} aria-hidden="true" />
        Avatar
      </h2>
      <p className="mt-1 flex items-start gap-2 text-caption text-muted-foreground">
        <MicOff className="mt-0.5 size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
        <span>
          Microphone off. Nothing is listened to. The avatar reads aloud only the answer text shown on this page.
        </span>
      </p>

      <div className="mt-4 overflow-hidden rounded-md bg-muted">
        {/* The avatar's own audio and video; there is no caption track because the answer text is on the page. */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          aria-label="Avatar video"
          className={phase === "ready" ? "aspect-video w-full" : "hidden"}
        />
        {phase !== "ready" ? (
          <div className="flex aspect-video items-center justify-center p-4 text-center text-caption text-muted-foreground">
            {phase === "starting" ? "Starting the avatar. The answers on this page are usable now." : null}
            {phase === "idle" ? "Start the avatar to hear an answer read aloud." : null}
            {phase === "ended" ? "Avatar session ended. The answers are still here as text." : null}
            {phase === "unavailable" ? "Avatar unavailable. The answers are shown as text; nothing else is affected." : null}
          </div>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        {phase === "ready" ? (
          <Button type="button" variant="outline" onClick={() => void stop()}>
            <VideoOff aria-hidden="true" />
            Stop avatar
          </Button>
        ) : (
          <Button type="button" onClick={() => void start()} disabled={phase === "starting"}>
            Start avatar
          </Button>
        )}
        <p role="status" aria-live="polite" className="text-caption text-muted-foreground">
          {phase === "ready" ? (speaking ? "The avatar is speaking." : "Ready. Use Speak with avatar under an answer.") : null}
        </p>
      </div>
      {note ? (
        <p role="alert" className="mt-3 text-caption text-muted-foreground">
          {note}
        </p>
      ) : null}
    </section>
  );
}
