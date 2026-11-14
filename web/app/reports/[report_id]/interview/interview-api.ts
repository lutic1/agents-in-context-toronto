import { ApiError, isUnreachable, post } from "@/lib/api";
import type { components } from "@/lib/types";

/**
 * The one call the interview page makes to ask a question (V70). It goes through B01's typed `post`, so the
 * path, the body and the result are checked against the generated contract and the key stays on the server.
 */

export type InterviewResponse = components["schemas"]["InterviewResponse"];
export type InterviewCitation = components["schemas"]["InterviewCitation"];

export const QUESTION_LIMIT = 500;

/** The persona (V70 amendment). It never says "I'm" plus a product, company, trial or person. */
export const PERSONA = "DxP's evidence guide";

/** The permanent label (V70). Always on the page, in every state. It names the persona. */
export const VOICE_LABEL = `${PERSONA}: reads quotes from the public record about this report. Not the manufacturer, not a clinician, not medical advice.`;

/** The exact reply the backend gives when the record has no answer. The page shows what the backend returned. */
export const NOT_IN_RECORD_TEXT = "The accepted record doesn't answer that.";

/** What a turn can be once the request has finished. */
export type TurnOutcome =
  | { kind: "answered"; response: InterviewResponse }
  | { kind: "not_in_record"; response: InterviewResponse }
  | { kind: "refused_medical"; response: InterviewResponse }
  | { kind: "blocked"; response: InterviewResponse }
  | { kind: "error"; reason: ErrorReason; message: string };

export type ErrorReason =
  | "unreachable"
  | "flag_off"
  | "not_accepted"
  | "report_not_found"
  | "unauthorised"
  | "invalid_question"
  | "not_available"
  | "other";

/** Sort a backend response into the state the page shows. `refusal_reason` decides; the text is never rewritten. */
export function classify(response: InterviewResponse): TurnOutcome {
  switch (response.refusal_reason) {
    case "medical_advice":
      return { kind: "refused_medical", response };
    case "blocked":
      return { kind: "blocked", response };
    case "not_in_record":
      return { kind: "not_in_record", response };
    default:
      // A refused response with a reason this page does not know is still shown as blocked, never as an answer.
      return response.refused ? { kind: "blocked", response } : { kind: "answered", response };
  }
}

/** Turn a thrown error into one of the page's error states. */
export function classifyError(error: unknown): TurnOutcome {
  if (isUnreachable(error)) {
    return { kind: "error", reason: "unreachable", message: "Couldn't reach the API. Nothing was asked; try again once it is back." };
  }
  if (error instanceof ApiError) {
    switch (error.status) {
      case 404:
        return error.code === "not_found" && /report/i.test(error.message)
          ? { kind: "error", reason: "report_not_found", message: "This report was not found." }
          : { kind: "error", reason: "flag_off", message: "Interview this evidence is switched off on the server." };
      case 409:
        return { kind: "error", reason: "not_accepted", message: "Only an accepted report can be interviewed." };
      case 401:
      case 403:
        return { kind: "error", reason: "unauthorised", message: "This session may not ask questions. Nothing was asked." };
      case 422:
        return { kind: "error", reason: "invalid_question", message: `Ask a question of 1 to ${QUESTION_LIMIT} characters.` };
      case 501:
        return { kind: "error", reason: "not_available", message: "Interview this evidence is not available yet." };
      default:
        return { kind: "error", reason: "other", message: "The API couldn't answer that. Nothing was changed." };
    }
  }
  return { kind: "error", reason: "other", message: "Something went wrong before the question was answered." };
}

export async function askQuestion(reportId: string, question: string): Promise<TurnOutcome> {
  try {
    const response = await post("/reports/{report_id}/interview", {
      path: { report_id: reportId },
      body: { question },
    });
    return classify(response);
  } catch (error) {
    return classifyError(error);
  }
}

/**
 * One block of an answer, as the backend builds them. A cited quote is `"<quote>" [n]` and nothing else; every other
 * block is one of the backend's fixed framing sentences. A quote never holds a line break (the backend collapses
 * blank lines), so a block is always one quote or one framing sentence.
 */
export type AnswerPart = { quote: string; marker: number } | { plain: string };

const CITED_QUOTE = /^"([\s\S]*)" \[(\d+)\]$/;

/** Split an answer into its blocks so a quote is set as a quote. Anything else stays plain text. */
export function splitAnswer(answer: string): AnswerPart[] {
  return answer
    .split(/\n\n+/)
    .filter((block) => block.trim().length > 0)
    .map((block): AnswerPart => {
      const match = CITED_QUOTE.exec(block.trim());
      if (!match) return { plain: block.trim() };
      return { quote: match[1], marker: Number(match[2]) };
    });
}
