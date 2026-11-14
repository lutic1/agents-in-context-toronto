"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { ShieldX, Undo2 } from "lucide-react";
import { toast } from "sonner";
import { useSWRConfig } from "swr";

import { buildPath, post } from "@/lib/api";
import { entryAnchor } from "@/components/audit/audit-entry";
import { features } from "@/lib/features";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { errorText } from "./errors";
import { useRefreshRelated } from "./refresh";
import { useActions } from "./who";
import type { Report } from "./format";

/**
 * "Revert approval" (Story 10.13, V48), built last and behind the `revert`
 * flag. Only on an accepted report, only for a principal whose actions include
 * `revert_report`. The confirm step is inline, not a modal, and needs a note.
 * It is a secondary button, never destructive: a revert is a Reviewer's decision.
 */
export function RevertControl({ report }: { report: Report }) {
  const { can, loaded } = useActions();
  const { mutate } = useSWRConfig();
  const refresh = useRefreshRelated();
  const uid = useId();
  const noteId = `${uid}-note`;
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blocked, setBlocked] = useState<{ text: string; href: string } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const noteRef = useRef<HTMLTextAreaElement>(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    if (open) noteRef.current?.focus();
    else if (wasOpen.current) buttonRef.current?.focus();
    wasOpen.current = open;
  }, [open]);

  if (!features.revert || report.status !== "accepted" || !loaded || !can("revert_report")) return null;

  async function confirm(event: React.FormEvent) {
    event.preventDefault();
    if (!note.trim()) return;
    setBusy(true);
    setError(null);
    setBlocked(null);
    try {
      const res = await post("/reports/{report_id}/revert", {
        path: { report_id: report.id },
        body: { note: note.trim() },
      });
      if (res.decision.outcome === "blocked") {
        // A blocked revert changes nothing: the report stays accepted.
        const check = res.decision.failed_check ?? "a check";
        const runId = res.decision.run_id ?? report.run_id;
        setBlocked({
          text: `Revert blocked: ${check} failed. Nothing changed.`,
          href: `/runs/${encodeURIComponent(runId)}/audit#${entryAnchor(res.decision.id)}`,
        });
      } else {
        await mutate(buildPath("/reports/{report_id}", { path: { report_id: report.id } }), res.report, {
          revalidate: false,
        });
        toast.success("Approval reverted.");
        setOpen(false);
        setNote("");
      }
      refresh();
    } catch (e) {
      setError(errorText(e));
      refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-3 flex flex-col gap-3">
      {!open ? (
        <div>
          <Button ref={buttonRef} type="button" variant="secondary" onClick={() => setOpen(true)}>
            <Undo2 aria-hidden="true" data-icon="inline-start" />
            Revert approval
          </Button>
        </div>
      ) : (
        <form
          onSubmit={confirm}
          onKeyDown={(event) => {
            if (event.key === "Escape" && !busy) {
              event.preventDefault();
              setOpen(false);
            }
          }}
          aria-label="Revert approval"
          className="flex flex-col gap-3 rounded-lg border border-border bg-glass-strong p-3"
        >
          <p className="text-body">
            Revert this approval? The update leaves accepted knowledge. Nothing is deleted, and the Slack alert
            already sent stays sent.
          </p>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={noteId}>
              Why revert this approval? <span className="text-muted-foreground">(required)</span>
            </Label>
            <Textarea
              id={noteId}
              ref={noteRef}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              required
              aria-required="true"
              disabled={busy}
            />
          </div>
          {blocked ? (
            <p className="flex items-center gap-2 border-l-[3px] border-l-destructive pl-2 text-body text-destructive" role="alert">
              <ShieldX className="size-4" strokeWidth={1.75} aria-hidden="true" />
              <span>
                {blocked.text}{" "}
                <Link href={blocked.href} className="underline underline-offset-2">
                  See the blocked decision in the audit
                </Link>
              </span>
            </p>
          ) : null}
          {error ? (
            <p className="text-body text-destructive" role="alert">
              {error}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button type="submit" variant="secondary" disabled={busy || !note.trim()} aria-busy={busy}>
              {busy ? "Reverting…" : "Revert approval"}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)} disabled={busy}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
