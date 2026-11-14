"use client";

import { Loader2, Mic, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

import { MAX_RECORDING_SECONDS, RecorderError, canRecord, startRecording, type Recording } from "./voice-recorder";
import { transcribe, VOICE_DISCLOSURE, VOICE_MESSAGES } from "./voice-api";

type Phase = "idle" | "requesting" | "recording" | "transcribing";

/**
 * Push-to-record question (V73), behind the `voice_input` flag. Press to start, press again to stop; the clip is
 * cut at 30 seconds. The transcript is handed to `onTranscript` for the user to read and edit in the question box.
 * Nothing is submitted from here.
 */
export function VoiceInput({
  reportId,
  disabled,
  onTranscript,
  onStatus,
}: {
  reportId: string;
  /** True while the avatar is starting or speaking, or a question is being answered. Recording is off then. */
  disabled: boolean;
  onTranscript: (text: string) => void;
  /** Words for the page's polite status region. */
  onStatus: (message: string) => void;
}) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [problem, setProblem] = useState<string | null>(null);
  const recordingRef = useRef<Recording | null>(null);
  const timerRef = useRef<number | null>(null);
  const busyRef = useRef(false);
  const mountedRef = useRef(true);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) window.clearInterval(timerRef.current);
    timerRef.current = null;
  }, []);

  const finish = useCallback(async () => {
    const recording = recordingRef.current;
    if (!recording) return;
    recordingRef.current = null;
    clearTimer();
    setPhase("transcribing");
    onStatus("Transcribing");
    let clip: Blob;
    try {
      clip = await recording.stop();
    } catch {
      busyRef.current = false;
      if (!mountedRef.current) return;
      setPhase("idle");
      setProblem(VOICE_MESSAGES.unavailable);
      onStatus("");
      return;
    }
    const outcome = await transcribe(reportId, clip);
    busyRef.current = false;
    if (!mountedRef.current) return;
    setPhase("idle");
    if (outcome.kind === "text") {
      setProblem(null);
      onTranscript(outcome.text);
      onStatus("Transcript ready, review and press Ask");
    } else {
      setProblem(VOICE_MESSAGES[outcome.kind === "refused" ? outcome.reason : "empty"]);
      onStatus(""); // the visible alert below is announced on its own
    }
  }, [clearTimer, onStatus, onTranscript, reportId]);

  async function begin() {
    if (busyRef.current) return;
    busyRef.current = true;
    setProblem(null);
    setPhase("requesting");
    if (!canRecord()) {
      busyRef.current = false;
      setPhase("idle");
      setProblem(VOICE_MESSAGES.unsupported);
      return;
    }
    let recording: Recording;
    try {
      recording = await startRecording();
    } catch (error) {
      busyRef.current = false;
      if (!mountedRef.current) return;
      setPhase("idle");
      const reason = error instanceof RecorderError ? error.reason : "failed";
      setProblem(VOICE_MESSAGES[reason === "denied" ? "denied" : reason === "unsupported" ? "unsupported" : "unavailable"]);
      return;
    }
    if (!mountedRef.current) {
      recording.cancel();
      return;
    }
    recordingRef.current = recording;
    const started = Date.now();
    setElapsed(0);
    setPhase("recording");
    onStatus("Recording");
    timerRef.current = window.setInterval(() => {
      const seconds = Math.floor((Date.now() - started) / 1000);
      setElapsed(Math.min(seconds, MAX_RECORDING_SECONDS));
      if (seconds >= MAX_RECORDING_SECONDS) void finish();
    }, 250);
  }

  // Leaving the page throws a recording away and releases the microphone.
  useEffect(() => {
    mountedRef.current = true;
    const drop = () => {
      clearTimer();
      recordingRef.current?.cancel();
      recordingRef.current = null;
    };
    window.addEventListener("pagehide", drop);
    return () => {
      mountedRef.current = false;
      window.removeEventListener("pagehide", drop);
      drop();
    };
  }, [clearTimer]);

  const recording = phase === "recording";
  const working = phase === "requesting" || phase === "transcribing";
  const left = MAX_RECORDING_SECONDS - elapsed;

  return (
    <div className="flex flex-col gap-2 rounded-md border border-dashed border-border px-3 py-2">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant={recording ? "default" : "outline"}
          aria-pressed={recording}
          disabled={working || (disabled && !recording)}
          onClick={() => void (recording ? finish() : begin())}
        >
          {working ? (
            <Loader2 aria-hidden="true" className="motion-safe:animate-spin" />
          ) : recording ? (
            <Square aria-hidden="true" />
          ) : (
            <Mic aria-hidden="true" />
          )}
          Record question
        </Button>
        <p className="text-caption text-muted-foreground">
          {recording ? (
            <>
              <span aria-hidden="true" className="mr-1.5 inline-block size-2 rounded-full bg-destructive motion-safe:animate-pulse" />
              Recording {formatTime(elapsed)}, {left} s left. Press again to stop.
            </>
          ) : null}
          {phase === "requesting" ? "Waiting for the microphone…" : null}
          {phase === "transcribing" ? "Transcribing…" : null}
          {phase === "idle" && disabled ? "Recording is off while the avatar is starting or speaking." : null}
          {phase === "idle" && !disabled ? `Up to ${MAX_RECORDING_SECONDS} seconds.` : null}
        </p>
      </div>
      <p className="text-caption text-muted-foreground">{VOICE_DISCLOSURE}</p>
      {problem ? (
        <p role="alert" className="text-caption font-medium">
          {problem}
        </p>
      ) : null}
    </div>
  );
}

function formatTime(seconds: number): string {
  return `0:${String(seconds).padStart(2, "0")}`;
}
