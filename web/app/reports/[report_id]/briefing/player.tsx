"use client";

import { AudioLines, CloudOff, Pause, Play, ShieldX, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, isUnreachable, post } from "@/lib/api";
import { isEnabled } from "@/lib/features";
import { formatElapsed } from "@/lib/format";
import { useApi } from "@/lib/use-api";

/**
 * The ten-second briefing player (Story 10.11, V29), inside the report page, behind the
 * `briefing` flag (EXPERIENCE "Briefing player", DESIGN `briefing-player`).
 *
 * - The transcript, the report's own `script`, is always on screen, so the audio has a text
 *   equivalent. This panel never builds or edits a script.
 * - Nothing is generated automatically: a "Generate briefing" button calls
 *   `POST /reports/<report_id>/briefing`, then "Play briefing (10 s)". Nothing autoplays.
 * - If ElevenLabs has no key or fails, the panel says "Briefing unavailable. The script is
 *   shown above." in faded ink, never as an error. The report, the decision and the task never
 *   wait on this panel.
 *
 * B04 places `<BriefingPlayer reportId={...} />` behind the flag; this file keeps B01's default
 * export and `reportId` prop. With the flag off it renders nothing.
 */
export type BriefingPlayerProps = {
  reportId: string;
};

const CAPTION = "Built only from this report's evidence fields.";
const UNAVAILABLE = "Briefing unavailable. The script is shown above.";

type AudioState = "idle" | "loading" | "playing" | "paused" | "error";

/** The API's error shape is `{ error: { code, message } }`; B01's client reads a flat body. */
function messageOf(error: ApiError): string {
  const body = error.body;
  if (body && typeof body === "object" && "error" in body) {
    const inner = (body as { error?: unknown }).error;
    if (inner && typeof inner === "object" && typeof (inner as { message?: unknown }).message === "string") {
      return (inner as { message: string }).message;
    }
  }
  return error.message;
}

export default function BriefingPlayer({ reportId }: BriefingPlayerProps) {
  if (!isEnabled("briefing")) return null;
  return <BriefingPanel reportId={reportId} />;
}

function BriefingPanel({ reportId }: BriefingPlayerProps) {
  const { data, error, isLoading, mutate } = useApi("/reports/{report_id}/briefing", {
    path: { report_id: reportId },
  });

  const [generating, setGenerating] = useState(false);
  const [blockedBy, setBlockedBy] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [failedHere, setFailedHere] = useState(false);
  const [announce, setAnnounce] = useState("");

  const [audioState, setAudioState] = useState<AudioState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const playRef = useRef<HTMLButtonElement | null>(null);
  const focusPlayNext = useRef(false);

  const status = data?.status ?? "none";
  const audioSrc = `/api/dxp/reports/${encodeURIComponent(reportId)}/briefing?audio=1`;
  const unavailable = failedHere || status === "failed" || status === "unavailable" || audioState === "error";
  const ready = status === "ready" && !unavailable;

  // After "Generate briefing" the button is replaced by the play button: keep keyboard focus.
  useEffect(() => {
    if (ready && focusPlayNext.current) {
      focusPlayNext.current = false;
      playRef.current?.focus();
    }
  }, [ready]);

  async function generate() {
    setGenerating(true);
    setBlockedBy(null);
    setRequestError(null);
    setAnnounce("Preparing briefing");
    let refreshed = false;
    try {
      const res = await post("/reports/{report_id}/briefing", { path: { report_id: reportId } });
      if (res.decision.outcome === "blocked") {
        const check = res.decision.failed_check;
        setBlockedBy(check ? `check ${check}` : "a policy check");
        setAnnounce("Briefing not generated: blocked by a policy check.");
      } else {
        focusPlayNext.current = true;
        setAnnounce("Briefing ready. Play briefing (10 s).");
      }
    } catch (e) {
      if (e instanceof ApiError && [403, 404, 409].includes(e.status)) {
        const message = messageOf(e);
        setRequestError(message);
        setAnnounce(message);
      } else if (e instanceof ApiError || !isUnreachable(e)) {
        // The route is a stub (501) or failed some other way: the player says unavailable.
        setFailedHere(true);
        setAnnounce(UNAVAILABLE);
      } else {
        // B01's client reads every 503 as "unreachable", and the API answers 503 when ElevenLabs has
        // no key or fails. Read the briefing again: if the API is there, its status says which.
        refreshed = true;
        const fresh = await mutate();
        if (fresh && (fresh.status === "failed" || fresh.status === "unavailable")) {
          setAnnounce(UNAVAILABLE);
        } else {
          setRequestError("Couldn't reach the API. Nothing was generated; try again once it is back.");
          setAnnounce("Couldn't reach the API.");
        }
      }
    } finally {
      setGenerating(false);
      if (!refreshed) void mutate();
    }
  }

  async function toggle() {
    const el = audioRef.current;
    if (!el) return;
    if (audioState === "playing" || audioState === "loading") {
      el.pause();
      return;
    }
    setAudioState("loading");
    try {
      await el.play();
    } catch {
      setAudioState("error");
      setAnnounce(UNAVAILABLE);
    }
  }

  const heading = (
    <div>
      <h3 id={`briefing-${reportId}`} className="text-heading">
        Briefing, 10 seconds
      </h3>
      <p className="text-caption text-muted-foreground">{CAPTION}</p>
    </div>
  );

  let body: React.ReactNode;
  if (isLoading && !data) {
    body = <Skeleton className="h-16 w-full" role="status" aria-label="Loading briefing" />;
  } else if (!data) {
    body = (
      <p className="flex items-start gap-2 text-body text-muted-foreground" role="status">
        {error && isUnreachable(error) ? (
          <>
            <CloudOff className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            Couldn&apos;t reach the API. The briefing shows here once it is back.
          </>
        ) : (
          <>
            <VolumeX className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            Briefing unavailable. The script is on the report.
          </>
        )}
      </p>
    );
  } else {
    body = (
      <>
        <p className="max-w-prose text-body" data-testid="briefing-transcript">
          <span className="sr-only">Transcript: </span>
          {data.script || "This report has no script."}
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          {unavailable ? (
            <p className="flex items-center gap-2 text-body text-muted-foreground">
              <VolumeX className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
              {UNAVAILABLE}
            </p>
          ) : ready ? (
            <>
              <Button
                ref={playRef}
                type="button"
                variant="secondary"
                onClick={toggle}
                aria-busy={audioState === "loading"}
              >
                {audioState === "playing" || audioState === "loading" ? (
                  <Pause strokeWidth={1.75} aria-hidden="true" />
                ) : (
                  <Play strokeWidth={1.75} aria-hidden="true" />
                )}
                {audioState === "playing" || audioState === "loading" ? "Pause" : "Play briefing (10 s)"}
              </Button>
              <span className="text-identifier tabular-nums" aria-label={`Elapsed ${formatElapsed(elapsed)}`}>
                {formatElapsed(elapsed)}
              </span>
              <audio
                ref={audioRef}
                src={audioSrc}
                preload="none"
                onPlaying={() => setAudioState("playing")}
                onPause={() => setAudioState("paused")}
                onEnded={() => {
                  setAudioState("idle");
                  setElapsed(0);
                }}
                onTimeUpdate={(e) => setElapsed(e.currentTarget.currentTime)}
                onError={() => setAudioState("error")}
              />
            </>
          ) : (
            <Button type="button" variant="secondary" onClick={generate} disabled={generating} aria-busy={generating}>
              <AudioLines strokeWidth={1.75} aria-hidden="true" />
              {generating ? "Preparing briefing" : "Generate briefing"}
            </Button>
          )}
        </div>

        {blockedBy ? (
          <p className="mt-2 flex items-start gap-2 text-caption text-muted-foreground">
            <ShieldX className="mt-0.5 size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            Not generated: the request was blocked by {blockedBy}. Nothing was sent.
          </p>
        ) : null}
        {requestError ? (
          <p className="mt-2 text-caption text-muted-foreground" role="alert">
            {requestError}
          </p>
        ) : null}
      </>
    );
  }

  return (
    <section
      aria-labelledby={`briefing-${reportId}`}
      className="flex flex-col gap-3 rounded-md border border-border bg-card p-4"
    >
      {heading}
      {body}
      <div role="status" aria-live="polite" className="sr-only">
        {announce}
      </div>
    </section>
  );
}
