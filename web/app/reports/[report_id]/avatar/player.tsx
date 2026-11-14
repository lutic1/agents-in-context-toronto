"use client";

import { useEffect, useRef } from "react";
import { Clapperboard, Play, Square, VideoOff } from "lucide-react";

import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";
import { isUnreachable, useApi } from "@/lib/use-api";
import { cn } from "@/lib/utils";

import { useAvatarSession, type AvatarState, type UnavailableWhy } from "./use-avatar-session";

/**
 * The avatar player (Story 10.12, V13, V29, V41), a HeyGen LiveAvatar reading the report's script.
 * B04 places it on the report page behind the `avatar` flag; this file keeps its default export and
 * its `reportId` prop.
 *
 * Nothing starts by itself: "Start avatar" asks the API (which gates it as `generate_avatar_video`
 * and mints a session token), then the page joins the live session and the avatar speaks exactly
 * `report.script`. The microphone stays off. The script is always on screen as text, with captions
 * while it speaks. The report works the same whatever happens here.
 */
export type AvatarPlayerProps = {
  reportId: string;
};

export const AVATAR_LABEL =
  "AI voice for DxP reading the report's script from public records. Not the manufacturer, not medical advice.";

const UNAVAILABLE: Record<UnavailableWhy, string> = {
  blocked: "DxP's policy did not allow this request, and nothing was sent to the avatar service.",
  no_key: "The avatar service is not set up for this deployment.",
  no_avatar: "No avatar is chosen for this deployment.",
  provider_error: "The avatar service did not start a session.",
  api_unreachable: "The API did not answer.",
  not_found: "This report was not found.",
  request_failed: "The request did not go through.",
  no_sdk: "The avatar player could not be loaded in this browser.",
  did_not_start: "The avatar did not start speaking in time.",
  no_script: "This report has no script to read.",
};

const STATUS: Record<Exclude<AvatarState, "unavailable">, string> = {
  idle: "Avatar not started. Press Start avatar to hear the script read aloud.",
  starting: "Starting avatar. The report is ready to review now.",
  speaking: "Avatar speaking. Press Stop avatar to end it.",
  ended: "Avatar finished. The script is shown here as text.",
};

export default function AvatarPlayer({ reportId }: AvatarPlayerProps) {
  const report = useApi("/reports/{report_id}", { path: { report_id: reportId } });
  const script = report.data?.script ?? null;
  const { state, why, caption, videoRef, start, stop } = useAvatarSession(reportId, script);

  // After "Unavailable" the button is gone, so move focus to the message that replaced it.
  const messageRef = useRef<HTMLParagraphElement | null>(null);
  useEffect(() => {
    if (state === "unavailable") messageRef.current?.focus();
  }, [state]);

  const busy = state === "starting" || state === "speaking";
  const showVideo = state === "speaking";

  return (
    <section
      aria-labelledby={`avatar-heading-${reportId}`}
      className="flex min-w-0 flex-col gap-3 rounded-md border border-border bg-card p-4"
    >
      <h3 id={`avatar-heading-${reportId}`} className="flex items-center gap-2 text-heading">
        <Clapperboard className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
        Avatar
      </h3>

      {/* The label is permanent: it is on screen in every state. */}
      <p className="text-caption text-muted-foreground">{AVATAR_LABEL}</p>

      <div className="relative aspect-video w-full overflow-hidden rounded-md border border-border bg-ink-tint">
        {/* No autoplay: the session only starts from the button. The microphone is never used. */}
        <video
          ref={videoRef}
          playsInline
          className={cn("size-full object-cover", showVideo ? "block" : "hidden")}
          aria-label="Avatar video, speaking the report's script"
        />
        {showVideo ? null : (
          <div
            aria-hidden="true"
            className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-4 text-center text-body text-muted-foreground"
          >
            {state === "unavailable" ? (
              <VideoOff className="size-8" strokeWidth={1.75} aria-hidden="true" />
            ) : (
              <Clapperboard className="size-8" strokeWidth={1.75} aria-hidden="true" />
            )}
            <span>
              {state === "unavailable"
                ? "Avatar unavailable."
                : state === "starting"
                  ? "Starting avatar…"
                  : state === "ended"
                    ? "Avatar finished."
                    : "Avatar not started."}
            </span>
          </div>
        )}
      </div>

      {/* Captions: what the avatar is saying now. The whole script is also below, always. */}
      {state === "speaking" ? (
        <p className="text-body" data-testid="avatar-caption">
          <span className="sr-only">Caption: </span>
          {caption || script}
        </p>
      ) : null}

      {/* The live region for state changes (polite). */}
      <div role="status" className="text-body">
        {state === "unavailable" ? (
          <p ref={messageRef} tabIndex={-1} className="text-muted-foreground">
            Avatar unavailable. The script is shown here; the report is unaffected.
            {why ? <span className="block text-caption">{UNAVAILABLE[why]}</span> : null}
          </p>
        ) : (
          <p className="text-muted-foreground">{STATUS[state]}</p>
        )}
      </div>

      {state === "unavailable" ? null : (
        <div className="flex flex-wrap items-center gap-3">
          {/* One button for start and stop, so keyboard focus stays where the person left it. */}
          <Button
            type="button"
            variant="secondary"
            onClick={busy ? stop : start}
            disabled={!busy && !script}
          >
            {busy ? (
              <Square className="size-4" strokeWidth={1.75} aria-hidden="true" />
            ) : (
              <Play className="size-4" strokeWidth={1.75} aria-hidden="true" />
            )}
            {busy ? "Stop avatar" : state === "ended" ? "Start avatar again" : "Start avatar"}
          </Button>
          <span className="text-caption text-muted-foreground">The microphone stays off.</span>
        </div>
      )}

      <ScriptText
        loading={report.isLoading}
        script={script}
        error={report.error}
      />
      <p className="text-caption text-muted-foreground">
        Same script as the briefing, built only from this report&apos;s evidence fields.
      </p>
    </section>
  );
}

/** The script as text, always: loading, empty and error states included. */
function ScriptText({
  loading,
  script,
  error,
}: {
  loading: boolean;
  script: string | null;
  error: Error | undefined;
}) {
  if (loading) return <Skeleton className="h-12 w-full" aria-label="Loading the script" />;
  if (error) {
    if (isUnreachable(error)) return <ApiUnreachableNotice />;
    const notFound = error instanceof ApiError && error.status === 404;
    return (
      <Notice title={notFound ? "Report not found" : "The script is not available"} role="status">
        {notFound ? "There is no report with this ID." : "The API answered, but not with this report."}
      </Notice>
    );
  }
  if (!script) {
    return (
      <Notice title="No script yet" role="status">
        This report has no stored script, so there is nothing for the avatar to read.
      </Notice>
    );
  }
  return (
    <div>
      <h4 className="text-caption font-semibold text-muted-foreground">Script</h4>
      <p className="mt-1 break-words text-body">{script}</p>
    </div>
  );
}
