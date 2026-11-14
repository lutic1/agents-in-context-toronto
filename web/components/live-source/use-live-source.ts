"use client";

import { useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";

import { buildPath } from "@/lib/api";
import { features } from "@/lib/features";
import { POLL_MS } from "@/lib/use-api";

/**
 * Where a run's feed gets its updates from, and the honest label for it (Story 9.12, V48).
 *
 * With the `live_stream` flag on, the hook opens `EventSource` on this app's streaming
 * proxy (`/api/stream/<run_id>`). While that stream is open the mode is "live". On any
 * error, a 404 or a 501 (A27 not merged), or with the flag off, the mode is "polling"
 * and the screen reads the run every 2 seconds, exactly as before. The mode is "live"
 * only while the stream is open, so the label can never say "Live (change stream)"
 * while the screen polls.
 *
 * The stream is a wake-up, not the data. Each event of the run makes the screen read
 * `GET /runs/<run_id>` and `GET /runs/<run_id>/audit` again, so the rows are the same
 * rows either way, ordered by `seq` from the audit, and a dropped connection can
 * neither miss nor repeat a row: the screen also reads once whenever the stream
 * (re)opens or says `reset`.
 *
 * A run that is still running or stopping is also read every 10 s while the stream is
 * open (`sweepInterval`), because that read drives the server's sweep and `in_flight`.
 *
 * Reuse (B03): call it with the run ID and pass its `refreshInterval` to `useApi`:
 *
 *   const source = useLiveSource(runId);
 *   const audit = useApi("/runs/{run_id}/audit", { path: { run_id: runId }, interval: source.refreshInterval });
 *   <LiveSourceLabel mode={source.mode} />
 */

export type LiveSourceMode = "live" | "polling";

export const LIVE_LABEL = "Live (change stream)";
export const POLLING_LABEL = "Refreshing every 2 s";

/**
 * While the stream is open the run is not polled every 2 s, but a running or stopping
 * run is still read about every 10 s. The server does its sweep of abandoned admissions
 * and counts `in_flight` when `GET /runs/<run_id>` is read, and the stream's events do not
 * make that read happen when nothing else changes.
 */
export const SWEEP_POLL_MS = 10_000;

/**
 * The `interval` for the run read that keeps the sweep going: `SWEEP_POLL_MS` while the stream
 * is open and the run is `running` or `stopping`, otherwise 0 (while polling, the 2-second read
 * already does this job; a finished run has nothing left to sweep).
 */
export function sweepInterval(mode: LiveSourceMode, status: string | null | undefined): number {
  return mode === "live" && (status === "running" || status === "stopping") ? SWEEP_POLL_MS : 0;
}

export function liveSourceLabel(mode: LiveSourceMode): string {
  return mode === "live" ? LIVE_LABEL : POLLING_LABEL;
}

/** What a stream message says, as far as the screen cares. Everything else about it is ignored. */
export type LiveEvent = {
  /** The event's `seq`, when the message is JSON that carries one. */
  seq: number | null;
  /** The event's `type` (for example `action_blocked`), when present. */
  type: string | null;
};

export type UseLiveSourceOptions = {
  /** Pass false to stay on polling (for example until the run is known). Default true. */
  enabled?: boolean;
  /** Called for each stream message, after the keys below have been queued for re-reading. */
  onEvent?: (event: LiveEvent) => void;
  /**
   * The SWR keys to re-read when the stream says something happened. Defaults to the
   * run and its audit, the two reads the Run console and the Audit view share.
   */
  keys?: string[];
};

export type LiveSource = {
  mode: LiveSourceMode;
  label: string;
  /** Pass as `interval` to `useApi`: 2000 while polling, 0 while the stream is open. */
  refreshInterval: number;
};

// The Event types of AD-14. A server may send them as named SSE events or as plain messages.
const EVENT_TYPES = [
  "diagnostic_created",
  "value_applied",
  "proposal_pending",
  "proposal_rejected",
  "run_status_changed",
  "action_allowed",
  "action_blocked",
  "action_status_changed",
  "scan_finished",
  "report_filed",
  "report_decided",
  "memory_changed",
  "task_status_changed",
  "related_evidence_filed",
  "report_reverted",
  "value_reverted",
  "rule_status_changed",
  "alert_created",
] as const;

/** Events that arrive together are read once. */
const REFRESH_DEBOUNCE_MS = 250;
/** When the browser gives up on a stream for good, try again after these waits (ms), then keep the last. */
const RETRY_AFTER_MS = [2_000, 5_000, 10_000, 20_000, 30_000];
/** After a `reset` the old resume token is useless, so the next connection starts clean. */
const RESET_RECONNECT_MS = 500;

export function runKeys(runId: string): string[] {
  return [
    buildPath("/runs/{run_id}", { path: { run_id: runId } }),
    buildPath("/runs/{run_id}/audit", { path: { run_id: runId } }),
  ];
}

function parseEvent(data: unknown): LiveEvent {
  if (typeof data !== "string") return { seq: null, type: null };
  try {
    const value: unknown = JSON.parse(data);
    if (value && typeof value === "object") {
      const o = value as Record<string, unknown>;
      return {
        seq: typeof o.seq === "number" ? o.seq : null,
        type: typeof o.type === "string" ? o.type : null,
      };
    }
  } catch {
    // A heartbeat or a non-JSON message still means "something happened".
  }
  return { seq: null, type: null };
}

export function useLiveSource(
  runId: string | null | undefined,
  options: UseLiveSourceOptions = {},
): LiveSource {
  const { enabled = true } = options;
  const { mutate } = useSWRConfig();

  const onEventRef = useRef(options.onEvent);
  const keysRef = useRef(options.keys);
  useEffect(() => {
    onEventRef.current = options.onEvent;
    keysRef.current = options.keys;
  });

  const wantsStream = enabled && features.live_stream && Boolean(runId);
  // The run the open stream belongs to; null whenever there is no open stream.
  const [openFor, setOpenFor] = useState<string | null>(null);

  useEffect(() => {
    if (!wantsStream || !runId || typeof EventSource === "undefined") return;
    const id: string = runId;

    let source: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let refreshTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let lastEventId: string | null = null;
    let stopped = false;

    const refresh = () => {
      if (refreshTimer) return;
      refreshTimer = setTimeout(() => {
        refreshTimer = undefined;
        for (const key of keysRef.current ?? runKeys(id)) void mutate(key);
      }, REFRESH_DEBOUNCE_MS);
    };

    const close = () => {
      if (source) {
        source.onopen = null;
        source.onerror = null;
        source.close();
        source = null;
      }
    };

    const connect = () => {
      if (stopped) return;
      const url =
        `/api/stream/${encodeURIComponent(id)}` +
        (lastEventId ? `?lastEventId=${encodeURIComponent(lastEventId)}` : "");
      const es = new EventSource(url);
      source = es;

      es.onopen = () => {
        attempt = 0;
        setOpenFor(id);
        // Cover anything that happened while the stream was down.
        refresh();
      };

      const onMessage = (message: MessageEvent) => {
        if (message.lastEventId) lastEventId = message.lastEventId;
        refresh();
        onEventRef.current?.(parseEvent(message.data));
      };
      es.onmessage = onMessage;
      for (const type of EVENT_TYPES) es.addEventListener(type, onMessage as EventListener);

      // The resume token can no longer be used: read the run and audit once and reconnect clean.
      es.addEventListener("reset", () => {
        lastEventId = null;
        close();
        setOpenFor(null);
        refresh();
        retryTimer = setTimeout(connect, RESET_RECONNECT_MS);
      });

      es.onerror = () => {
        // Say so at once: from here the screen polls.
        setOpenFor(null);
        if (es.readyState !== EventSource.CLOSED) return; // the browser reconnects by itself and resumes
        // The browser gave up (a 404, a 501, a wrong content type): try again later, never faster than the schedule.
        close();
        const wait = RETRY_AFTER_MS[Math.min(attempt, RETRY_AFTER_MS.length - 1)];
        attempt += 1;
        retryTimer = setTimeout(connect, wait);
      };
    };

    connect();

    return () => {
      stopped = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (refreshTimer) clearTimeout(refreshTimer);
      close();
    };
  }, [wantsStream, runId, mutate]);

  const live = wantsStream && runId != null && openFor === runId;
  const mode: LiveSourceMode = live ? "live" : "polling";
  return { mode, label: liveSourceLabel(mode), refreshInterval: live ? 0 : POLL_MS };
}
