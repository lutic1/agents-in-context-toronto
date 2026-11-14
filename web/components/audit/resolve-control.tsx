"use client";

import { useEffect, useId, useRef, useState } from "react";
import { SquareCheck } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, ApiUnreachableError, post } from "@/lib/api";

/**
 * Resolve control for an `unknown` Slack alert (Story 9.4, D53). The caller
 * decides whether to show it: only when `GET /whoami`'s `actions` include
 * `resolve_notification`. It calls `POST /actions/<action_id>/resolve` through
 * the server-side key, never posts to Slack, and there is no reconcile button.
 *
 * The form is labelled; focus moves into it when it opens and back to the
 * Resolve button when it closes (Accessibility Floor).
 */
export function ResolveControl({
  actionId,
  onResolved,
}: {
  actionId: string;
  onResolved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [outcome, setOutcome] = useState<"delivered" | "failed" | null>(null);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const buttonRef = useRef<HTMLButtonElement>(null);
  const firstRadioRef = useRef<HTMLInputElement>(null);
  const wasOpen = useRef(false);
  const uid = useId();

  useEffect(() => {
    if (open) firstRadioRef.current?.focus();
    else if (wasOpen.current) buttonRef.current?.focus();
    wasOpen.current = open;
  }, [open]);

  function close() {
    setOpen(false);
    setMessage(null);
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!outcome || !note.trim() || saving) return;
    setSaving(true);
    setMessage(null);
    try {
      await post("/actions/{action_id}/resolve", {
        path: { action_id: actionId },
        body: { outcome, note: note.trim() },
      });
      toast.success(outcome === "delivered" ? "Alert recorded as delivered." : "Alert recorded as failed.");
      setOutcome(null);
      setNote("");
      close();
      onResolved();
    } catch (error) {
      if (error instanceof ApiUnreachableError) {
        setMessage("Couldn't reach the API. Nothing was saved.");
      } else if (error instanceof ApiError) {
        setMessage(error.message);
      } else {
        setMessage("Nothing was saved.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <Button ref={buttonRef} type="button" variant="secondary" size="sm" onClick={() => setOpen(true)}>
        <SquareCheck aria-hidden="true" />
        Resolve
        <span className="sr-only"> Slack alert {actionId}</span>
      </Button>
    );
  }

  return (
    <form
      onSubmit={save}
      aria-label={`Resolve Slack alert ${actionId}`}
      className="flex max-w-prose flex-col gap-3 rounded-md border border-border bg-muted p-3"
    >
      <fieldset className="flex flex-col gap-1.5">
        <legend className="text-table font-semibold">What did you find in #all-mango-db-hackathon?</legend>
        <label className="flex items-center gap-2 text-table">
          <input
            ref={firstRadioRef}
            type="radio"
            name={`${uid}-outcome`}
            checked={outcome === "delivered"}
            onChange={() => setOutcome("delivered")}
            className="size-4 accent-primary"
          />
          Delivered: I found it in the channel
        </label>
        <label className="flex items-center gap-2 text-table">
          <input
            type="radio"
            name={`${uid}-outcome`}
            checked={outcome === "failed"}
            onChange={() => setOutcome("failed")}
            className="size-4 accent-primary"
          />
          Failed: it is not in the channel
        </label>
      </fieldset>
      <div className="flex flex-col gap-1">
        <label htmlFor={`${uid}-note`} className="text-table font-semibold">
          Note (required)
        </label>
        <Textarea
          id={`${uid}-note`}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          required
          aria-describedby={message ? `${uid}-error` : undefined}
        />
      </div>
      {message ? (
        <p id={`${uid}-error`} role="alert" className="text-table text-destructive">
          {message}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={!outcome || !note.trim() || saving}>
          Save resolution
        </Button>
        <Button type="button" variant="ghost" onClick={close}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
