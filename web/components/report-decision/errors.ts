import { ApiError, isUnreachable } from "@/lib/api";

/** The API's `{ error: { code, message } }` body carries the useful sentence; fall back to the client's. */
function apiMessage(error: ApiError): string {
  const body = error.body;
  if (body && typeof body === "object") {
    const inner = (body as Record<string, unknown>).error;
    if (inner && typeof inner === "object") {
      const message = (inner as Record<string, unknown>).message;
      if (typeof message === "string" && message) return message;
    }
  }
  return error.message;
}

/**
 * One plain sentence for a failed request. A 400, 403, 404 or 409 shows as a
 * message and the page stays; the API being unreachable says so and says
 * nothing was changed.
 */
export function errorText(error: unknown): string {
  if (isUnreachable(error)) {
    return "Couldn't reach the API. Nothing was changed. Try again once it is back.";
  }
  if (error instanceof ApiError) {
    const message = apiMessage(error);
    switch (error.status) {
      case 400:
        return `Not accepted: ${message}`;
      case 403:
        return `Not allowed: ${message}`;
      case 404:
        return `Not found: ${message}`;
      case 409:
        return `This report has changed: ${message}`;
      case 501:
        return `Not available yet: ${message}`;
      default:
        return message;
    }
  }
  return "Something went wrong. Nothing was changed.";
}
