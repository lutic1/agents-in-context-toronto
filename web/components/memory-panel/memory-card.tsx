"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { Ban, Brain, History, ShieldX, type LucideIcon } from "lucide-react";
import { toast } from "sonner";
import { useSWRConfig } from "swr";

import { buildPath, post } from "@/lib/api";
import { displayName, formatDate, shortId } from "@/lib/format";
import { features } from "@/lib/features";
import { useApi } from "@/lib/use-api";
import type { components } from "@/lib/types";
import { SyntheticBadge } from "@/components/shell/badges";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { errorText } from "@/components/report-decision/errors";
import { useRefreshRelated } from "@/components/report-decision/refresh";
import { useActions } from "@/components/report-decision/who";

type Memory = components["schemas"]["Memory"];
type MemoryUse = components["schemas"]["MemoryUse"];

const STATUS: Record<Memory["status"], { icon: LucideIcon; word: string }> = {
  active: { icon: Brain, word: "Active" },
  corrected: { icon: History, word: "Corrected" },
  revoked: { icon: Ban, word: "Revoked" },
};

type Form = "correct" | "revoke" | null;

/**
 * One memory in the panel: author, source, tags and status, the effect it had on
 * this report, and Correct and Revoke (behind `memory_edit`, and only for a
 * principal allowed to). Both open an inline form with a required note.
 */
export function MemoryCard({
  memoryId,
  reportId,
  use,
  createdHere,
}: {
  memoryId: string;
  reportId: string;
  use?: MemoryUse;
  createdHere?: boolean;
}) {
  const { data: memory, error, isLoading } = useApi("/memories/{memory_id}", { path: { memory_id: memoryId } });
  const { can, loaded } = useActions();
  const [form, setForm] = useState<Form>(null);
  const lastForm = useRef<Exclude<Form, null>>("correct");
  const correctRef = useRef<HTMLButtonElement>(null);
  const revokeRef = useRef<HTMLButtonElement>(null);

  function openForm(next: Exclude<Form, null>) {
    lastForm.current = next;
    setForm(next);
  }
  function closeForm() {
    setForm(null);
    const target = lastForm.current === "revoke" ? revokeRef : correctRef;
    requestAnimationFrame(() => target.current?.focus());
  }

  if (isLoading && !memory) {
    return <Skeleton className="h-24 w-full" role="status" aria-label="Loading a memory" />;
  }

  const id = shortId(memoryId);
  const source = memory?.source ?? use?.source ?? null;
  const author = memory?.author ?? use?.author ?? null;
  const status = memory?.status ?? "active";
  const StatusIcon = STATUS[status].icon;
  const editable = features.memory_edit && loaded && memory?.status === "active";
  const headingId = `memory-${memoryId}`;

  return (
    <li className="rounded-md border border-border bg-card p-3">
      <article aria-labelledby={headingId} className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 rounded-sm bg-ink-tint px-2 py-1">
          <Brain className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
          <h3 id={headingId} className="text-identifier font-medium">
            {id}
          </h3>
          {memory ? <span className="text-identifier text-muted-foreground">v{memory.version}</span> : null}
          <span className="inline-flex items-center gap-1 text-caption font-medium">
            <StatusIcon className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
            {STATUS[status].word}
          </span>
        </div>

        <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-caption text-muted-foreground">
          {author ? (
            <>
              <span className="text-foreground">{displayName(author)}</span>
              <SyntheticBadge />
            </>
          ) : null}
          {memory?.created_at ? <span>{formatDate(memory.created_at)}</span> : null}
        </p>

        {memory ? (
          <p className={memory.status === "revoked" ? "text-body text-muted-foreground line-through" : "text-body"}>
            {memory.status === "revoked" ? <span className="sr-only">Revoked: </span> : null}
            {memory.text}
          </p>
        ) : (
          <p className="text-caption text-muted-foreground" role={error ? "alert" : undefined}>
            The memory text could not be read right now{error ? "" : "."}
          </p>
        )}

        {memory?.status === "revoked" ? (
          <p className="text-caption text-muted-foreground">
            Revoked{author ? ` by ${displayName(author)}` : ""}
            {memory.created_at ? ` at ${new Date(memory.created_at).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false })}` : ""}
            . It will not be used again.
          </p>
        ) : null}
        {memory?.status === "corrected" ? (
          <p className="text-caption text-muted-foreground">
            Corrected. Replaced by <span className="text-identifier">{id}</span> v{memory.version + 1}. The old version
            stays readable in the audit.
          </p>
        ) : null}
        {memory?.supersedes ? (
          <p className="text-caption text-muted-foreground">
            Supersedes <span className="text-identifier">{memory.supersedes}</span>.
          </p>
        ) : null}
        {memory && use && memory.version !== use.version ? (
          <p className="text-caption text-muted-foreground">
            This report used v{use.version}; the current version is v{memory.version}.
          </p>
        ) : null}

        {memory ? (
          <p className="flex flex-wrap gap-x-3 gap-y-1 text-caption text-muted-foreground">
            <span>
              About:{" "}
              <span className="text-identifier text-foreground">{memory.tags.claim_kind ?? "no claim kind"}</span>
            </span>
            <span>
              Written on: <span className="text-foreground">{memory.tags.assay ?? "no assay"}</span>
            </span>
          </p>
        ) : null}

        <p className="text-caption text-muted-foreground">
          Source:{" "}
          {source?.report_id ? (
            source.report_id === reportId ? (
              "this report"
            ) : (
              <Link href={`/reports/${encodeURIComponent(source.report_id)}`} className="underline underline-offset-2">
                report <span className="text-identifier">{shortId(source.report_id)}</span>
              </Link>
            )
          ) : (
            "no report recorded"
          )}
          {source?.decision_id ? (
            <>
              , decision <span className="text-identifier">{shortId(source.decision_id)}</span>
            </>
          ) : null}
          {createdHere ? ". Created by the decision on this report" : ""}.
        </p>

        {use ? <Effect use={use} /> : null}

        {editable && form === null && (can("correct_memory") || can("revoke_memory")) ? (
          <div className="flex flex-wrap gap-2">
            {can("correct_memory") ? (
              <Button ref={correctRef} type="button" variant="ghost" size="sm" onClick={() => openForm("correct")}>
                Correct<span className="sr-only"> memory {id}</span>
              </Button>
            ) : null}
            {can("revoke_memory") ? (
              <Button ref={revokeRef} type="button" variant="ghost" size="sm" onClick={() => openForm("revoke")}>
                Revoke<span className="sr-only"> memory {id}</span>
              </Button>
            ) : null}
          </div>
        ) : null}

        {editable && form === "correct" && memory ? (
          <CorrectForm memory={memory} onClose={closeForm} />
        ) : null}
        {editable && form === "revoke" && memory ? <RevokeForm memory={memory} onClose={closeForm} /> : null}
      </article>
    </li>
  );
}

/** What the memory did to this report: the labelled Before and After, or "Retrieved, no change" (AD-28). */
function Effect({ use }: { use: MemoryUse }) {
  if (!use.effect) {
    return <p className="text-caption text-muted-foreground">Retrieved, no change.</p>;
  }
  return (
    <div className="flex flex-col gap-1 rounded-sm bg-muted p-2 text-caption">
      <p className="font-medium">
        Wording changed because of {shortId(use.memory_id)} ({displayName(use.author)}): {use.effect.target}
      </p>
      <p>
        <span className="font-medium">Before:</span>{" "}
        <span className="text-muted-foreground line-through decoration-1">{use.effect.before}</span>
      </p>
      <p>
        <span className="font-medium">After:</span> <span>{use.effect.after}</span>
      </p>
    </div>
  );
}

function useMemoryWrite(memory: Memory) {
  const { mutate } = useSWRConfig();
  const refresh = useRefreshRelated();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(call: () => Promise<components["schemas"]["MemoryChangeResponse"]>, success: (m: Memory) => string) {
    setBusy(true);
    setError(null);
    try {
      const res = await call();
      if (res.decision.outcome === "blocked") {
        setError(`Blocked: ${res.decision.failed_check ?? "a check"} failed. Nothing changed.`);
        return false;
      }
      await mutate(buildPath("/memories/{memory_id}", { path: { memory_id: memory.id } }), res.memory, {
        revalidate: false,
      });
      toast.success(success(res.memory));
      refresh();
      return true;
    } catch (e) {
      setError(errorText(e));
      return false;
    } finally {
      setBusy(false);
    }
  }
  return { run, busy, error };
}

function CorrectForm({ memory, onClose }: { memory: Memory; onClose: () => void }) {
  const uid = useId();
  const [text, setText] = useState(memory.text);
  const [note, setNote] = useState("");
  const [missing, setMissing] = useState<"text" | "note" | null>(null);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const { run, busy, error } = useMemoryWrite(memory);
  const id = shortId(memory.id);

  useEffect(() => {
    textRef.current?.focus();
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!text.trim()) {
      setMissing("text");
      textRef.current?.focus();
      return;
    }
    if (!note.trim()) {
      setMissing("note");
      noteRef.current?.focus();
      return;
    }
    const ok = await run(
      () => post("/memories/{memory_id}/correct", { path: { memory_id: memory.id }, body: { text: text.trim(), note: note.trim() } }),
      (m) => `${id} corrected (now version ${m.version}).`,
    );
    if (ok) onClose();
  }

  return (
    <form
      onSubmit={submit}
      onKeyDown={(event) => {
        if (event.key === "Escape" && !busy) {
          event.preventDefault();
          onClose();
        }
      }}
      aria-label={`Correct memory ${id}`}
      className="flex flex-col gap-3 border-t border-border pt-3"
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${uid}-text`}>New text for the memory</Label>
        <Textarea
          id={`${uid}-text`}
          ref={textRef}
          value={text}
          onChange={(event) => setText(event.target.value)}
          required
          aria-required="true"
          aria-invalid={missing === "text" || undefined}
          disabled={busy}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${uid}-note`}>
          Why are you correcting it? <span className="text-muted-foreground">(required)</span>
        </Label>
        <Textarea
          id={`${uid}-note`}
          ref={noteRef}
          value={note}
          onChange={(event) => setNote(event.target.value)}
          required
          aria-required="true"
          aria-invalid={missing === "note" || undefined}
          disabled={busy}
        />
        {missing ? (
          <p className="text-caption text-destructive" role="alert">
            {missing === "text" ? "The new text can't be empty." : "A correction needs a note."}
          </p>
        ) : null}
      </div>
      <p className="text-caption text-muted-foreground">
        Saving creates a new version that supersedes this one. It does not rewrite this report; it affects the next
        relevant discovery.
      </p>
      {error ? (
        <p className="flex items-center gap-2 text-body text-destructive" role="alert">
          <ShieldX className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant="secondary" size="sm" disabled={busy} aria-busy={busy}>
          {busy ? "Saving…" : "Save correction"}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} disabled={busy}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

function RevokeForm({ memory, onClose }: { memory: Memory; onClose: () => void }) {
  const uid = useId();
  const [note, setNote] = useState("");
  const [missing, setMissing] = useState(false);
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const { run, busy, error } = useMemoryWrite(memory);
  const id = shortId(memory.id);

  useEffect(() => {
    noteRef.current?.focus();
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!note.trim()) {
      setMissing(true);
      noteRef.current?.focus();
      return;
    }
    const ok = await run(
      () => post("/memories/{memory_id}/revoke", { path: { memory_id: memory.id }, body: { note: note.trim() } }),
      () => `${id} revoked. It will not be used again.`,
    );
    if (ok) onClose();
  }

  return (
    <form
      onSubmit={submit}
      onKeyDown={(event) => {
        if (event.key === "Escape" && !busy) {
          event.preventDefault();
          onClose();
        }
      }}
      aria-label={`Revoke memory ${id}`}
      className="flex flex-col gap-3 border-t border-border pt-3"
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${uid}-note`}>
          Why revoke this memory? <span className="text-muted-foreground">(required)</span>
        </Label>
        <Textarea
          id={`${uid}-note`}
          ref={noteRef}
          value={note}
          onChange={(event) => {
            setNote(event.target.value);
            if (event.target.value.trim()) setMissing(false);
          }}
          required
          aria-required="true"
          aria-invalid={missing || undefined}
          disabled={busy}
        />
        {missing ? (
          <p className="text-caption text-destructive" role="alert">
            Revoking needs a note.
          </p>
        ) : null}
      </div>
      <p className="text-caption text-muted-foreground">
        A revoked memory is never used again. This report still shows it, as Revoked.
      </p>
      {error ? (
        <p className="flex items-center gap-2 text-body text-destructive" role="alert">
          <ShieldX className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant="secondary" size="sm" disabled={busy} aria-busy={busy}>
          {busy ? "Revoking…" : "Revoke memory"}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} disabled={busy}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
