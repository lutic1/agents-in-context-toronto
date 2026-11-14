"use client";

import { FileClock, SearchX, ToggleLeft } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useId, useRef, useState } from "react";

import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import { isEnabled } from "@/lib/features";
import { isUnreachable, useApi } from "@/lib/use-api";

import { AvatarPanel } from "./avatar-panel";
import { askQuestion, QUESTION_LIMIT, VOICE_LABEL, type TurnOutcome } from "./interview-api";
import { TurnView, type Turn } from "./turn";
import { VoiceInput } from "./voice-input";

/** Announced to screen readers when a question finishes. */
function announcement(outcome: TurnOutcome): string {
  switch (outcome.kind) {
    case "answered":
      return `Answer ready with ${outcome.response.citations.length} citations.`;
    case "not_in_record":
      return "The report's record doesn't answer that.";
    case "refused_medical":
      return "Refused: this page gives no medical advice.";
    case "blocked":
      return "Blocked by the policy gate.";
    case "error":
      // The error block on the page is a role="alert"; announcing it here too would read it twice.
      return "";
  }
}

/**
 * Interview this evidence (V70, V74): ask a question about a pending or accepted report and get back only its own quotes,
 * each cited. The page is a supporting lane behind the `interview` flag and never blocks the core loop.
 */
export function InterviewView({ reportId }: { reportId: string }) {
  const interviewOn = isEnabled("interview");
  const report = useApi("/reports/{report_id}", { path: { report_id: reportId }, enabled: interviewOn });

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <Link href={`/reports/${encodeURIComponent(reportId)}`} className="text-caption text-muted-foreground underline underline-offset-2">
          Back to the report
        </Link>
        <h1 className="text-title">Interview this evidence</h1>
        {report.data ? <p className="text-body text-muted-foreground">{report.data.headline}</p> : null}
        <p className="max-w-prose rounded-md border border-dashed border-border bg-card px-3 py-2 text-caption">{VOICE_LABEL}</p>
      </header>

      <Body
        reportId={reportId}
        interviewOn={interviewOn}
        loading={report.isLoading && !report.data}
        error={report.error}
        status={report.data?.status ?? null}
      >
        <InterviewWorkspace reportId={reportId} allowVoice />
      </Body>
    </div>
  );
}

/**
 * The ask box, the cited answers and the optional avatar panel (V70), reusable outside the interview page.
 * `stacked` puts the avatar panel under the answers instead of beside them. `allowVoice` shows the recorder
 * (V73); it stays false everywhere but the interview route, whose Permissions-Policy allows the microphone.
 * The avatar starts only when the user presses "Engage" in its panel.
 */
export function InterviewWorkspace({
  reportId,
  stacked = false,
  allowVoice = false,
}: {
  reportId: string;
  stacked?: boolean;
  allowVoice?: boolean;
}) {
  const avatarOn = isEnabled("avatar");
  const voiceOn = allowVoice && isEnabled("voice_input");

  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const [announce, setAnnounce] = useState("");
  const [speak, setSpeak] = useState<((text: string) => void) | null>(null);
  // True while the avatar session is starting or speaking: recording is off then (V73).
  const [avatarBusy, setAvatarBusy] = useState(false);
  // Bumped when a transcript lands in the box, so the box takes focus once it holds the new text.
  const [focusTick, setFocusTick] = useState(0);
  const counter = useRef(0);
  const fieldRef = useRef<HTMLTextAreaElement>(null);
  const fieldId = useId();

  const onSpeaker = useCallback((fn: ((text: string) => void) | null) => setSpeak(() => fn), []);

  // A transcript is only ever put in the box for the user to read and edit. It is never submitted from here.
  const onTranscript = useCallback((text: string) => {
    setQuestion((current) => (current.trim() ? `${current.trimEnd()} ${text}` : text).slice(0, QUESTION_LIMIT));
    setFocusTick((n) => n + 1);
  }, []);

  useEffect(() => {
    if (focusTick === 0) return;
    const field = fieldRef.current;
    if (!field) return;
    field.focus();
    field.setSelectionRange(field.value.length, field.value.length);
  }, [focusTick]);

  async function submit() {
    const text = question.trim();
    if (!text || pending) return;
    counter.current += 1;
    const id = `turn-${counter.current}`;
    setPending(true);
    setQuestion("");
    // The Ask button is disabled once the box is empty, so a keyboard user who pressed it would lose focus to the
    // page. Focus goes back to the ask box; the answer is announced by the status region, not by moving focus.
    fieldRef.current?.focus();
    setAnnounce("Looking through the report's record.");
    setTurns((current) => [{ id, question: text, outcome: null }, ...current]);
    const outcome = await askQuestion(reportId, text);
    setTurns((current) => current.map((t) => (t.id === id ? { ...t, outcome } : t)));
    setAnnounce(announcement(outcome));
    setPending(false);
  }

  return (
    <div className={avatarOn && !stacked ? "grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]" : "grid grid-cols-1 gap-6"}>
      {/* Stacked: the avatar and its Engage button come first, the ask box and answers follow. */}
      {avatarOn && stacked ? <AvatarPanel reportId={reportId} onSpeaker={onSpeaker} onBusyChange={setAvatarBusy} /> : null}
      <div className="flex min-w-0 flex-col gap-6">
        <form
          className="flex flex-col gap-2 rounded-lg bg-card p-5 shadow-sm"
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          <Label htmlFor={fieldId} className="text-table font-semibold">
            Ask a question about this report
          </Label>
          <Textarea
            ref={fieldRef}
            id={fieldId}
            value={question}
            maxLength={QUESTION_LIMIT}
            rows={3}
            aria-describedby={`${fieldId}-help ${fieldId}-count`}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                void submit();
              }
            }}
          />
          <p id={`${fieldId}-help`} className="text-caption text-muted-foreground">
            {voiceOn ? "Type or record your question, then read and edit it before you ask. " : "Typed questions only. "}Ask about this record&apos;s status, dates, conditions, phase, design, interventions, sponsor, location, enrollment or posted results. Answers quote only this report&apos;s evidence. DxP does not give medical advice. Press Ctrl+Enter or Command+Enter to ask.
          </p>
          {voiceOn ? (
            <VoiceInput
              reportId={reportId}
              disabled={avatarBusy || pending}
              onTranscript={onTranscript}
              onStatus={setAnnounce}
            />
          ) : null}
          <div className="flex items-center justify-between gap-3">
            <p id={`${fieldId}-count`} className="text-caption text-muted-foreground">
              {question.length} of {QUESTION_LIMIT} characters
            </p>
            <Button type="submit" disabled={pending || question.trim().length === 0}>
              Ask
            </Button>
          </div>
        </form>

        <p role="status" aria-live="polite" className="sr-only">
          {announce}
        </p>

        {turns.length === 0 ? (
          <Notice icon={SearchX} title="No questions yet">
            Ask about the record&apos;s status, dates, conditions, phase, design, names, sponsor, location, enrollment or posted results. Each answer is built only from quotes stored on this
            report and cites them.
          </Notice>
        ) : (
          <ol className="flex flex-col gap-4" aria-label="Questions and answers, newest first">
            {turns.map((turn) => (
              <li key={turn.id}>
                <TurnView turn={turn} speak={speak} />
              </li>
            ))}
          </ol>
        )}
      </div>
      {avatarOn && !stacked ? <AvatarPanel reportId={reportId} onSpeaker={onSpeaker} onBusyChange={setAvatarBusy} /> : null}
    </div>
  );
}

/** The page states that come before the ask box: flag off, loading, unreachable, not found, neither pending nor accepted. */
function Body({
  interviewOn,
  loading,
  error,
  status,
  children,
}: {
  reportId: string;
  interviewOn: boolean;
  loading: boolean;
  error: Error | undefined;
  status: string | null;
  children: React.ReactNode;
}) {
  if (!interviewOn) {
    return (
      <Notice icon={ToggleLeft} title="Interview this evidence is switched off">
        This is a supporting feature and it is off for this deployment. The report and the rest of DxP are not affected.
      </Notice>
    );
  }
  if (loading) return <PageSkeleton rows={2} />;
  if (error) {
    if (isUnreachable(error)) return <ApiUnreachableNotice />;
    if (error instanceof ApiError && error.status === 404) {
      return (
        <Notice icon={SearchX} title="Report not found" role="alert">
          Open Reports to see what is pending or accepted.
        </Notice>
      );
    }
    return (
      <Notice icon={SearchX} title="The report could not be loaded" role="alert">
        The API answered with an error. Nothing was asked.
      </Notice>
    );
  }
  if (status !== "pending" && status !== "accepted") {
    return (
      <Notice icon={FileClock} title="This report can't be interviewed">
        Only a pending or accepted report can be interviewed. This one is {status ?? "not available"}.
      </Notice>
    );
  }
  return <>{children}</>;
}
