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

/** Announced to screen readers when a question finishes. */
function announcement(outcome: TurnOutcome): string {
  switch (outcome.kind) {
    case "answered":
      return `Answer ready with ${outcome.response.citations.length} citations.`;
    case "not_in_record":
      return "The accepted record doesn't answer that.";
    case "refused_medical":
      return "Refused: this page gives no medical advice.";
    case "blocked":
      return "Blocked by the policy gate.";
    case "error":
      return outcome.message;
  }
}

/**
 * Interview this evidence (V70): ask a question about an accepted report and get back only its own quotes,
 * each cited. The page is a supporting lane behind the `interview` flag and never blocks the core loop.
 */
export function InterviewView({ reportId }: { reportId: string }) {
  const interviewOn = isEnabled("interview");
  const avatarOn = isEnabled("avatar");
  const report = useApi("/reports/{report_id}", { path: { report_id: reportId }, enabled: interviewOn });

  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const [announce, setAnnounce] = useState("");
  const [speak, setSpeak] = useState<((text: string) => void) | null>(null);
  const counter = useRef(0);
  const turnRefs = useRef(new Map<string, HTMLElement>());
  const focusTurn = useRef<string | null>(null);
  const fieldId = useId();

  const onSpeaker = useCallback((fn: ((text: string) => void) | null) => setSpeak(() => fn), []);

  // Move focus to a turn once its answer has arrived, so the result is read and reachable by keyboard.
  useEffect(() => {
    const id = focusTurn.current;
    if (!id) return;
    const outcome = turns.find((t) => t.id === id)?.outcome;
    if (!outcome) return;
    turnRefs.current.get(id)?.focus();
    focusTurn.current = null;
  }, [turns]);

  async function submit() {
    const text = question.trim();
    if (!text || pending) return;
    counter.current += 1;
    const id = `turn-${counter.current}`;
    setPending(true);
    setQuestion("");
    setAnnounce("Looking through the accepted record.");
    setTurns((current) => [{ id, question: text, outcome: null }, ...current]);
    focusTurn.current = id;
    const outcome = await askQuestion(reportId, text);
    setTurns((current) => current.map((t) => (t.id === id ? { ...t, outcome } : t)));
    setAnnounce(announcement(outcome));
    setPending(false);
  }

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
        <div className={avatarOn ? "grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]" : "grid grid-cols-1 gap-6"}>
          <div className="flex min-w-0 flex-col gap-6">
            <form
              className="flex flex-col gap-2 rounded-lg border border-border bg-card p-5 shadow-sm"
              onSubmit={(event) => {
                event.preventDefault();
                void submit();
              }}
            >
              <Label htmlFor={fieldId} className="text-table font-semibold">
                Ask a question about this accepted report
              </Label>
              <Textarea
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
                Answers quote only this report&apos;s evidence. DxP does not give medical advice. Press Ctrl+Enter or Command+Enter to ask.
              </p>
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
                Ask about the trial&apos;s status, the names in the record or the related evidence. Each answer is built only from quotes stored on this
                report and cites them.
              </Notice>
            ) : (
              <ol className="flex flex-col gap-4" aria-label="Questions and answers, newest first">
                {turns.map((turn) => (
                  <li key={turn.id}>
                    <TurnView
                      turn={turn}
                      speak={speak}
                      ref={(node) => {
                        if (node) turnRefs.current.set(turn.id, node);
                        else turnRefs.current.delete(turn.id);
                      }}
                    />
                  </li>
                ))}
              </ol>
            )}
          </div>
          {avatarOn ? <AvatarPanel reportId={reportId} onSpeaker={onSpeaker} /> : null}
        </div>
      </Body>
    </div>
  );
}

/** The page states that come before the ask box: flag off, loading, unreachable, not found, not accepted. */
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
  if (status !== "accepted") {
    return (
      <Notice icon={FileClock} title="This report is not accepted">
        Only an accepted report can be interviewed. This one is {status ?? "not available"}. Accept it on the report page first.
      </Notice>
    );
  }
  return <>{children}</>;
}
