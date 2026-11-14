"use client";

import { useEffect, useId, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { components } from "@/lib/types";

export type ClaimKind = NonNullable<components["schemas"]["ReportDecisionRequest"]["claim_kind"]>;
export type FormMode = "correct" | "reject";

/** The three claim-check kinds (V60, V61). The code in mono is what is stored on the memory. */
const CLAIM_KINDS: { value: ClaimKind; label: string }[] = [
  { value: "claim_performed_or_results", label: "Outcome or result stated without posted results" },
  { value: "claim_planned", label: "Planned or recruiting study described as done" },
  { value: "claim_preclinical", label: "Cell-line or animal work not labelled preclinical" },
];
const UNSPECIFIED = "unspecified";

export type DecisionFormValues = { note: string; claimKind: ClaimKind | null };

/**
 * The inline form under the decisions bar for "Approve with correction" and
 * "Reject" (V61): a required note and the "What is this correction about?"
 * select, whose choice becomes the memory's claim kind. Focus moves into the
 * form when it opens; the parent returns it to the button when it closes.
 */
export function DecisionForm({
  mode,
  initialNote = "",
  submitting,
  error,
  onSubmit,
  onCancel,
}: {
  mode: FormMode;
  initialNote?: string;
  submitting: boolean;
  error: string | null;
  onSubmit: (values: DecisionFormValues) => void;
  onCancel: () => void;
}) {
  const uid = useId();
  const noteId = `${uid}-note`;
  const kindId = `${uid}-kind`;
  const hintId = `${uid}-hint`;
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const [note, setNote] = useState(initialNote);
  const [kind, setKind] = useState<string>(UNSPECIFIED);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    noteRef.current?.focus();
  }, []);

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!note.trim()) {
      setMissing(true);
      noteRef.current?.focus();
      return;
    }
    onSubmit({ note: note.trim(), claimKind: kind === UNSPECIFIED ? null : (kind as ClaimKind) });
  }

  const submitLabel = mode === "correct" ? "Approve with correction" : "Reject";

  return (
    <form
      onSubmit={submit}
      onKeyDown={(event) => {
        // Esc cancels, unless the open select list already used it to close itself.
        if (event.key === "Escape" && !event.defaultPrevented && !submitting) {
          event.preventDefault();
          onCancel();
        }
      }}
      aria-label={mode === "correct" ? "Approve with correction" : "Reject this report"}
      className="mt-3 flex flex-col gap-3 border-t border-border pt-3"
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={noteId}>
          What should the agent do differently next time? <span className="text-muted-foreground">(required)</span>
        </Label>
        <Textarea
          id={noteId}
          ref={noteRef}
          value={note}
          onChange={(event) => {
            setNote(event.target.value);
            if (event.target.value.trim()) setMissing(false);
          }}
          required
          aria-required="true"
          aria-invalid={missing || undefined}
          aria-describedby={missing ? hintId : undefined}
          disabled={submitting}
        />
        {missing ? (
          <p id={hintId} className="text-caption text-destructive" role="alert">
            {mode === "correct" ? "A correction needs a note." : "A rejection needs a reason."} Say what the agent
            should do differently.
          </p>
        ) : null}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor={kindId}>What is this correction about?</Label>
        <Select value={kind} onValueChange={setKind} disabled={submitting}>
          <SelectTrigger id={kindId} className="w-full max-w-full sm:w-96" aria-describedby={`${kindId}-help`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={UNSPECIFIED}>Not specified (a general correction)</SelectItem>
            {CLAIM_KINDS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p id={`${kindId}-help`} className="text-caption text-muted-foreground">
          {kind === UNSPECIFIED ? (
            "Choose the kind of claim so the agent finds this memory next time. Without one it is saved as a general correction."
          ) : (
            <>
              Saved on the memory as <span className="text-identifier">{kind}</span>.
            </>
          )}
        </p>
      </div>

      {error ? (
        <p className="text-body text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant={mode === "correct" ? "secondary" : "outline"} disabled={submitting} aria-busy={submitting}>
          {submitting ? "Saving…" : submitLabel}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
