"use client";

import { AudioLines, FileClock, SearchX, Square, ToggleLeft } from "lucide-react";
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
import { startConversation, type Conversation, type ConversationState } from "./conversation";
import { askQuestion, QUESTION_LIMIT, VOICE_LABEL, type TurnOutcome } from "./interview-api";
import { TurnView, type Turn } from "./turn";
import { VOICE_DISCLOSURE, VOICE_MESSAGES, transcribe } from "./voice-api";
import { VoiceInput } from "./voice-input";
import { RecorderError } from "./voice-recorder";

/** How long after the answer and the avatar are done before listening resumes, so the avatar's voice is never recorded. */
const RESUME_DELAY_MS = 300;
/** How long to wait for the avatar to start speaking an answer it was handed before listening anyway. */
const AVATAR_START_WAIT_MS = 5000;

/** Suggested questions: a click fills the box and asks. */
const SUGGESTIONS = [
  "What is this study designed to do?",
  "What is the trial's recruitment status?",
  "Has this trial posted any results?",
];

/** The answer text shown on the page for this outcome, which the avatar reads aloud; null when there is none to read. */
function spokenText(outcome: TurnOutcome): string | null {
  if (outcome.kind !== "answered" && outcome.kind !== "not_in_record" && outcome.kind !== "refused_medical") return null;
  const text = outcome.response.answer;
  return typeof text === "string" && text.trim().length > 0 ? text : null;
}

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
 * The avatar starts by itself when its panel mounts (V75); once it is ready, conversation mode starts too, and its
 * Talk / End conversation control and status line sit under the avatar video.
 */
export function InterviewWorkspace({
  reportId,
  stacked = false,
  allowVoice = false,
  subtitle,
}: {
  reportId: string;
  /** Which report this is, shown in the avatar card header. */
  subtitle?: string;
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

  // Conversation mode (V75): hands-free questions. The microphone stays open; each spoken segment is transcribed and
  // asked through the same submit() path. Listening is paused while transcribing, while an answer is pending and while
  // the avatar is starting or speaking (or has been handed an answer and not yet started).
  const [conversationOn, setConversationOn] = useState(false);
  const [conversationStarting, setConversationStarting] = useState(false);
  const [conversationProblem, setConversationProblem] = useState<string | null>(null);
  const [listenState, setListenState] = useState<ConversationState>("paused");
  const [transcribing, setTranscribing] = useState(false);
  const [awaitingAvatar, setAwaitingAvatar] = useState(false);
  const [missed, setMissed] = useState(false);
  // True while the browser keeps the microphone's audio context suspended until a click or key press.
  const [conversationBlocked, setConversationBlocked] = useState(false);
  const avatarReadyRef = useRef(false);
  const beginRef = useRef<() => Promise<void>>(async () => {});
  const conversationRef = useRef<Conversation | null>(null);
  const submitRef = useRef<(text: string) => Promise<void>>(async () => {});

  // The current speaker, read when an answer lands (the answer may arrive after the closure that asked was made).
  const speakRef = useRef<((text: string) => void) | null>(null);
  const onSpeaker = useCallback((fn: ((text: string) => void) | null) => {
    speakRef.current = fn;
    setSpeak(() => fn);
  }, []);

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

  async function submit(asked?: string) {
    const text = (asked ?? question).trim();
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
    // When the avatar session is ready it reads the answer shown on the page aloud, the same as "Speak with avatar".
    const spoken = spokenText(outcome);
    if (spoken && speakRef.current) {
      // In conversation mode, listening stays paused until the avatar has started (and then finished) speaking.
      if (conversationRef.current) setAwaitingAvatar(true);
      speakRef.current(spoken);
    }
  }

  useEffect(() => {
    submitRef.current = (text: string) => submit(text);
  });

  const endConversation = useCallback(() => {
    conversationRef.current?.stop();
    conversationRef.current = null;
    setConversationOn(false);
    setTranscribing(false);
    setAwaitingAvatar(false);
    setMissed(false);
    setConversationBlocked(false);
    setListenState("paused");
  }, []);

  async function beginConversation() {
    if (conversationRef.current || conversationStarting) return;
    setConversationStarting(true);
    setConversationProblem(null);
    let conversation: Conversation | null = null;
    try {
      conversation = await startConversation({
        onState: (state) => {
          setListenState(state);
          if (state === "hearing") setMissed(false);
        },
        onBlocked: setConversationBlocked,
        onSegment: (clip) => {
          void (async () => {
            const mine = conversation;
            setTranscribing(true);
            setMissed(false);
            const result = await transcribe(reportId, clip);
            // The conversation was ended (or replaced) while transcribing: drop the text.
            if (!mine || conversationRef.current !== mine) return;
            if (result.kind === "text") {
              await submitRef.current(result.text.slice(0, QUESTION_LIMIT));
            } else {
              setMissed(true);
            }
            if (conversationRef.current === mine) setTranscribing(false);
          })();
        },
      });
      conversationRef.current = conversation;
      setConversationOn(true);
    } catch (error) {
      const reason = error instanceof RecorderError ? error.reason : "failed";
      setConversationProblem(reason === "denied" ? VOICE_MESSAGES.denied : reason === "unsupported" ? VOICE_MESSAGES.unsupported : VOICE_MESSAGES.unavailable);
    } finally {
      setConversationStarting(false);
    }
  }

  useEffect(() => {
    beginRef.current = () => beginConversation();
  });

  // Each time the avatar becomes ready (on page load, or after "Start avatar"), open the microphone too (V75).
  const onAvatarReady = useCallback(
    (ready: boolean) => {
      const was = avatarReadyRef.current;
      avatarReadyRef.current = ready;
      if (ready && !was && voiceOn) void beginRef.current();
    },
    [voiceOn],
  );

  // Pause at once when anything is busy; resume RESUME_DELAY_MS after everything is idle.
  const shouldListen = conversationOn && !transcribing && !pending && !avatarBusy && !awaitingAvatar;
  useEffect(() => {
    const conversation = conversationRef.current;
    if (!conversation) return;
    if (!shouldListen) {
      conversation.setPaused(true);
      return;
    }
    const timer = window.setTimeout(() => conversation.setPaused(false), RESUME_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [shouldListen, conversationOn]);

  // The avatar was handed an answer: stop waiting once it is busy, or after a few seconds if it never starts.
  useEffect(() => {
    if (!awaitingAvatar) return;
    // Once busy, `avatarBusy` itself keeps listening paused, so the wait can end on the next tick.
    const timer = window.setTimeout(() => setAwaitingAvatar(false), avatarBusy ? 0 : AVATAR_START_WAIT_MS);
    return () => window.clearTimeout(timer);
  }, [awaitingAvatar, avatarBusy]);

  // The microphone is closed on unmount and when the page is hidden for good.
  useEffect(() => {
    const onPageHide = () => endConversation();
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      conversationRef.current?.stop();
      conversationRef.current = null;
    };
  }, [endConversation]);

  const conversationStatus = conversationBlocked
    ? "Click anywhere to start talking"
    : transcribing && !pending
      ? "Heard you — transcribing…"
      : pending
        ? "Finding the answer…"
        : avatarBusy || awaitingAvatar
          ? "Speaking…"
          : missed
            ? "Didn't catch that — keep talking"
            : listenState === "calibrating"
              ? "Getting ready — listening in a moment…"
              : listenState === "hearing"
                ? "Listening… (hearing you)"
                : "Listening…";

  const conversationHelp = `Speak your question and pause: it is asked after about 1.5 seconds of silence. The microphone is paused while an answer is found or spoken. ${VOICE_DISCLOSURE}`;
  const conversationButton = conversationOn ? (
    <Button type="button" variant="outline" aria-pressed={true} onClick={endConversation}>
      <Square aria-hidden="true" />
      End conversation
    </Button>
  ) : (
    <Button type="button" aria-pressed={false} disabled={conversationStarting || pending} onClick={() => void beginConversation()}>
      <AudioLines aria-hidden="true" />
      {conversationStarting ? "Opening the microphone…" : "Talk"}
    </Button>
  );
  const conversationLine = (
    <>
      {shouldListen && !conversationBlocked ? <span aria-hidden="true" className="inline-block size-2 rounded-full bg-destructive motion-safe:animate-pulse" /> : null}
      {conversationStatus}
    </>
  );
  // With the avatar on, the conversation control and status sit under the avatar video, beside "Stop avatar".
  const avatarConversation = voiceOn
    ? {
        control: conversationButton,
        status: conversationOn ? conversationLine : undefined,
        note: conversationOn ? (
          conversationHelp
        ) : conversationProblem ? (
          <p role="alert" className="font-medium text-foreground">
            {conversationProblem}
          </p>
        ) : null,
      }
    : undefined;
  const avatarPanel = (
    <AvatarPanel
      reportId={reportId}
      onSpeaker={onSpeaker}
      onBusyChange={setAvatarBusy}
      onReadyChange={onAvatarReady}
      onStopped={endConversation}
      conversation={avatarConversation}
      subtitle={subtitle}
      answering={pending}
    />
  );

  return (
    <div className={avatarOn && !stacked ? "grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]" : "grid grid-cols-1 gap-6"}>
      {/* Stacked: the avatar and its Engage button come first, the ask box and answers follow. */}
      {avatarOn && stacked ? avatarPanel : null}
      <div className="flex min-w-0 flex-col gap-6">
        {conversationOn && avatarOn ? (
          <p className="rounded-lg bg-card p-5 text-caption text-muted-foreground shadow-sm">
            Conversation is on: speak your question. The controls are under the avatar video.
          </p>
        ) : conversationOn ? (
          <section aria-label="Conversation" className="flex flex-col gap-3 rounded-lg bg-card p-5 shadow-sm">
            <div className="flex flex-wrap items-center gap-3">
              {conversationButton}
              <p role="status" aria-live="polite" className="flex items-center gap-2 text-body font-medium">
                {conversationLine}
              </p>
            </div>
            <p className="text-caption text-muted-foreground">{conversationHelp}</p>
          </section>
        ) : (
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
          <div className="flex flex-wrap gap-2" aria-label="Suggested questions">
            {SUGGESTIONS.map((suggestion) => (
              <Button
                key={suggestion}
                type="button"
                variant="outline"
                size="sm"
                disabled={pending}
                onClick={() => {
                  setQuestion(suggestion);
                  void submit(suggestion);
                }}
              >
                {suggestion}
              </Button>
            ))}
          </div>
          {voiceOn && !avatarOn ? (
            <div className="flex flex-col gap-2 rounded-md border border-dashed border-border px-3 py-2">
              <div className="flex flex-wrap items-center gap-3">
                <Button type="button" aria-pressed={false} disabled={conversationStarting || pending} onClick={() => void beginConversation()}>
                  <AudioLines aria-hidden="true" />
                  {conversationStarting ? "Opening the microphone…" : "Start conversation"}
                </Button>
                <p className="text-caption text-muted-foreground">Hands-free: speak, pause, and the question is asked for you.</p>
              </div>
              {conversationProblem ? (
                <p role="alert" className="text-caption font-medium">
                  {conversationProblem}
                </p>
              ) : null}
            </div>
          ) : null}
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
        )}

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
      {avatarOn && !stacked ? avatarPanel : null}
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
