"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, isUnreachable, post } from "@/lib/api";

import { createAvatarAdapter, type AvatarAdapter } from "./liveavatar-sdk";
import type { AvatarStartResponse, AvatarUnavailableReason } from "./types";

/** The four states of the player (EXPERIENCE "Avatar video player"), plus the one before a press. */
export type AvatarState = "idle" | "starting" | "speaking" | "ended" | "unavailable";

/** Why the avatar is unavailable, in words for the screen. None of these are errors of the loop. */
export type UnavailableWhy =
  | AvatarUnavailableReason
  | "api_unreachable"
  | "not_found"
  | "request_failed"
  | "no_sdk"
  | "did_not_start"
  | "no_script";

/** How long to wait for the avatar to begin speaking before giving up (seconds). */
export const START_TIMEOUT_S = 25;
/** The most a session may speak for, whatever the server's limit (seconds): about ten seconds of script. */
const SPEAK_CAP_S = 90;

export function useAvatarSession(reportId: string, script: string | null) {
  const [state, setState] = useState<AvatarState>("idle");
  const [why, setWhy] = useState<UnavailableWhy | null>(null);
  const [caption, setCaption] = useState("");
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const adapterRef = useRef<AvatarAdapter | null>(null);
  const spokeRef = useRef(false); // true once the avatar began speaking in the current run
  const runRef = useRef(0); // bumps on every start and stop, so a late callback of an old session is ignored
  const timers = useRef<number[]>([]);

  const clearTimers = useCallback(() => {
    for (const id of timers.current) window.clearTimeout(id);
    timers.current = [];
  }, []);

  /** End the session and settle in `next`. Safe to call at any time and more than once. */
  const finish = useCallback(
    (next: AvatarState, reason: UnavailableWhy | null = null) => {
      runRef.current += 1;
      clearTimers();
      const adapter = adapterRef.current;
      adapterRef.current = null;
      if (adapter) void adapter.stop().catch(() => undefined);
      setWhy(reason);
      setState(next);
    },
    [clearTimers],
  );

  const start = useCallback(async () => {
    if (adapterRef.current) return;
    if (!script || !script.trim()) {
      finish("unavailable", "no_script");
      return;
    }
    const run = ++runRef.current;
    const current = () => runRef.current === run;
    spokeRef.current = false;
    setCaption("");
    setWhy(null);
    setState("starting");

    // 1. The API gates the request and, if allowed, mints one live session token.
    let started: AvatarStartResponse;
    try {
      started = (await post("/reports/{report_id}/avatar", {
        path: { report_id: reportId },
      })) as unknown as AvatarStartResponse;
    } catch (error) {
      if (!current()) return;
      finish(
        "unavailable",
        isUnreachable(error) ? "api_unreachable" : error instanceof ApiError && error.status === 404 ? "not_found" : "request_failed",
      );
      return;
    }
    if (!current()) return;
    if (started.decision.outcome !== "allowed") return finish("unavailable", "blocked");
    if (!started.session) return finish("unavailable", started.unavailable_reason ?? "provider_error");

    // 2. Join the live session. The microphone stays off (the adapter mutes voice chat).
    let spoke = false;
    const adapter = await createAvatarAdapter(started.session.session_token, {
      onSpeakStarted: () => {
        if (!current()) return;
        spoke = true;
        spokeRef.current = true;
        setState("speaking");
      },
      onSpeakEnded: () => {
        if (current() && spoke) finish("ended");
      },
      onCaption: (text) => {
        if (current()) setCaption(text);
      },
      onClosed: () => {
        if (!current()) return;
        finish(spoke ? "ended" : "unavailable", spoke ? null : "did_not_start");
      },
    });
    if (!current()) {
      if (adapter) void adapter.stop().catch(() => undefined);
      return;
    }
    if (!adapter) return finish("unavailable", "no_sdk");
    adapterRef.current = adapter;

    try {
      const video = videoRef.current;
      if (!video) throw new Error("no video element");
      await adapter.start(video);
      if (!current()) return;
      // 3. Speak exactly report.script (V41): repeat(), never message().
      adapter.speak(script);
    } catch {
      if (current()) finish("unavailable", "did_not_start");
      return;
    }
    timers.current.push(
      window.setTimeout(() => {
        if (!spoke) finish("unavailable", "did_not_start");
      }, START_TIMEOUT_S * 1000),
      window.setTimeout(
        () => finish(spoke ? "ended" : "unavailable", spoke ? null : "did_not_start"),
        Math.min(started.session.max_session_duration, SPEAK_CAP_S) * 1000,
      ),
    );
  }, [finish, reportId, script]);

  // Stopping before the avatar ever spoke settles in "idle", not "Avatar finished".
  const stop = useCallback(() => finish(spokeRef.current ? "ended" : "idle"), [finish]);

  // Stop the session when the page is hidden for good (pagehide), and when the player unmounts.
  useEffect(() => {
    /** Drop the session without touching the screen; true when one was running. */
    const endQuietly = () => {
      runRef.current += 1;
      clearTimers();
      const adapter = adapterRef.current;
      adapterRef.current = null;
      if (adapter) void adapter.stop().catch(() => undefined);
      return adapter !== null;
    };
    // A page restored from the back-forward cache must not show a session that no longer exists.
    const onPageHide = () => {
      if (endQuietly()) setState("ended");
    };
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      endQuietly();
    };
  }, [clearTimers]);

  return { state, why, caption, videoRef, start, stop };
}
