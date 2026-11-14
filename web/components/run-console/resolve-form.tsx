"use client";

import { useEffect, useId, useRef, useState } from "react";
import { SquareCheck } from "lucide-react";

import { ApiError, isUnreachable, post } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type Outcome = "delivered" | "failed";

/**
 * Resolve control for an `unknown` Slack alert (D53, S7, S8). Shown by the caller
 * only when the signed-in principal's `actions` (GET /whoami) include
 * `resolve_notification`. A labelled inline form: focus moves into it when it opens
 * and back to the button when it closes. The request goes through the server-side
 * key; nothing here says who is resolving.
 */
export function ResolveControl({
  actionId,
  onResolved,
}: {
  actionId: string;
  onResolved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const button = useRef<HTMLButtonElement>(null);
  const firstRadio = useRef<HTMLInputElement>(null);
  const wasOpen = useRef(false);
  const formId = useId();
  const noteId = useId();

  useEffect(() => {
    if (open) firstRadio.current?.focus();
    else if (wasOpen.current) button.current?.focus();
    wasOpen.current = open;
  }, [open]);

  function close() {
    setOpen(false);
    setError(null);
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!outcome || !note.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      await post("/actions/{action_id}/resolve", {
        path: { action_id: actionId },
        body: { outcome, note: note.trim() },
      });
      setOpen(false);
      setNote("");
      setOutcome(null);
      onResolved();
    } catch (cause) {
      setError(
        isUnreachable(cause)
          ? "Couldn't reach the API. Nothing was saved."
          : cause instanceof ApiError && cause.status === 403
            ? "You are not allowed to resolve this alert."
            : cause instanceof ApiError && cause.status === 409
              ? "This alert was already resolved or has changed. The row will update."
              : cause instanceof Error
                ? cause.message
                : "The resolution could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-2">
      <Button
        ref={button}
        type="button"
        variant="secondary"
        aria-expanded={open}
        aria-controls={formId}
        onClick={() => (open ? close() : setOpen(true))}
      >
        <SquareCheck aria-hidden="true" />
        Resolve
        <span className="sr-only"> Slack alert {actionId}</span>
      </Button>
      {open ? (
        <form id={formId} onSubmit={save} className="mt-3 flex max-w-xl flex-col gap-3 rounded-md border border-border bg-muted p-3">
          <fieldset className="flex flex-col gap-2">
            <legend className="text-table font-semibold">What happened to the alert?</legend>
            <label className="flex items-start gap-2 text-table">
              <input
                ref={firstRadio}
                type="radio"
                name={`${formId}-outcome`}
                value="delivered"
                checked={outcome === "delivered"}
                onChange={() => setOutcome("delivered")}
                className="mt-1 size-4 accent-[var(--ink-deep)]"
                required
              />
              <span>Delivered: I found it in the channel</span>
            </label>
            <label className="flex items-start gap-2 text-table">
              <input
                type="radio"
                name={`${formId}-outcome`}
                value="failed"
                checked={outcome === "failed"}
                onChange={() => setOutcome("failed")}
                className="mt-1 size-4 accent-[var(--ink-deep)]"
                required
              />
              <span>Failed: it is not in the channel</span>
            </label>
          </fieldset>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={noteId}>Note (required)</Label>
            <Textarea
              id={noteId}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              required
              placeholder="Where you checked and what you saw"
            />
          </div>
          {error ? (
            <p role="alert" className="text-table text-destructive">
              {error}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={busy || !outcome || !note.trim()}>
              Save resolution
            </Button>
            <Button type="button" variant="ghost" onClick={close}>
              Cancel
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
