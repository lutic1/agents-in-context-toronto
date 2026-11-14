"use client";

import { CloudOff, ShieldX, SearchX, Volume2 } from "lucide-react";
import { forwardRef } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { CitationsPanel, citationId } from "./citations";
import { splitAnswer, type InterviewResponse, type TurnOutcome } from "./interview-api";

export type Turn = { id: string; question: string; outcome: TurnOutcome | null };

/**
 * One question and what came back. Every state has words and an icon, never colour alone:
 * loading, answered (with its citations), not in the record, refused (medical advice), blocked by the gate,
 * and the error states (API unreachable, interview off, report not accepted, and the rest).
 */
export const TurnView = forwardRef<HTMLElement, { turn: Turn; speak: ((text: string) => void) | null }>(function TurnView(
  { turn, speak },
  ref,
) {
  const { id, question, outcome } = turn;
  return (
    <article
      ref={ref}
      tabIndex={-1}
      aria-labelledby={`${id}-question`}
      aria-busy={outcome === null}
      className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-sm focus:outline-none focus-visible:ring-3 focus-visible:ring-ring"
    >
      <h2 id={`${id}-question`} className="text-heading">
        <span className="sr-only">Question: </span>
        {question}
      </h2>
      {outcome === null ? <Loading /> : <Outcome id={id} outcome={outcome} speak={speak} />}
    </article>
  );
});

function Loading() {
  return (
    <div role="status" className="flex flex-col gap-2">
      <p className="text-caption text-muted-foreground">Reading the accepted record for quotes that answer this.</p>
      <Skeleton className="h-5 w-full max-w-prose" />
      <Skeleton className="h-5 w-4/5 max-w-prose" />
    </div>
  );
}

function Outcome({ id, outcome, speak }: { id: string; outcome: TurnOutcome; speak: ((text: string) => void) | null }) {
  switch (outcome.kind) {
    case "answered":
      return (
        <>
          <Answer id={id} response={outcome.response} />
          <CitationsPanel turnId={id} citations={outcome.response.citations} />
          <Footer response={outcome.response} speak={speak} />
        </>
      );
    case "not_in_record":
      return (
        <>
          <Statement icon={SearchX} title="Not in the accepted record" text={outcome.response.answer} />
          <Footer response={outcome.response} speak={speak} />
        </>
      );
    case "refused_medical":
      return (
        <>
          <Statement icon={ShieldX} title="Refused: medical advice" text={outcome.response.answer} />
          <Footer response={outcome.response} speak={speak} />
        </>
      );
    case "blocked":
      return (
        <>
          <Statement icon={ShieldX} title="Blocked by the policy gate" text={outcome.response.answer} />
          <Footer response={outcome.response} speak={null} />
        </>
      );
    case "error":
      return <Statement icon={CloudOff} title={errorTitle(outcome.reason)} text={outcome.message} alert />;
  }
}

function errorTitle(reason: Extract<TurnOutcome, { kind: "error" }>["reason"]): string {
  switch (reason) {
    case "unreachable":
      return "Couldn't reach the API";
    case "flag_off":
      return "Interview is switched off";
    case "not_accepted":
      return "Report not accepted";
    case "report_not_found":
      return "Report not found";
    case "unauthorised":
      return "Not allowed";
    case "invalid_question":
      return "Question not accepted";
    case "not_available":
      return "Not available yet";
    default:
      return "No answer";
  }
}

function Statement({
  icon: Icon,
  title,
  text,
  alert = false,
}: {
  icon: typeof SearchX;
  title: string;
  text: string;
  alert?: boolean;
}) {
  return (
    <div role={alert ? "alert" : undefined} className="flex items-start gap-3 rounded-md border border-dashed border-border p-4">
      <Icon className="mt-0.5 size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
      <div>
        <h3 className="text-table font-semibold">{title}</h3>
        <p className="mt-1 text-body">{text}</p>
      </div>
    </div>
  );
}

/** The answer, one cited sentence at a time: DxP's lead-in in the sans, the record's words in the serif, then the citation link. */
function Answer({ id, response }: { id: string; response: InterviewResponse }) {
  const parts = splitAnswer(response.answer);
  return (
    <div className="flex flex-col gap-3">
      {parts.map((part, index) =>
        "plain" in part ? (
          <p key={index} className="text-body">
            {part.plain}
          </p>
        ) : (
          <div key={index}>
            <p className="text-body">{part.leadIn}</p>
            <blockquote className="evidence-quote my-1 break-words">{part.quote}</blockquote>
            <a href={`#${citationId(id, part.marker)}`} className="text-identifier text-foreground underline underline-offset-2">
              <span className="sr-only">Citation </span>[{part.marker}]
            </a>
          </div>
        ),
      )}
    </div>
  );
}

function Footer({ response, speak }: { response: InterviewResponse; speak: ((text: string) => void) | null }) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-caption text-muted-foreground">
      <span>
        Logged as decision <span className="text-identifier text-foreground">{response.decision_id}</span>
      </span>
      {speak ? (
        <Button type="button" variant="outline" size="sm" onClick={() => speak(response.answer)}>
          <Volume2 aria-hidden="true" />
          Speak with avatar
        </Button>
      ) : null}
    </div>
  );
}
