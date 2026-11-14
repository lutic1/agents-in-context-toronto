"use client";

import Link from "next/link";
import { useCallback, useRef } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import {
  Equal,
  EqualNot,
  GitBranchPlus,
  Layers,
  MessageCircleQuestion,
  Minus,
  TextSearch,
  type LucideIcon,
} from "lucide-react";

import { AcceptedBadge, PendingBadge, RevertedBadge } from "@/components/report/badges";
import { CapabilityTag } from "@/components/report/capability-tag";
import { EvidenceQuote } from "@/components/report/evidence-quote";
import { ExternalLink } from "@/components/report/external-link";
import { LABEL_ORDER, nctIdOf, trialUrl } from "@/components/report/labels";
import { Section } from "@/components/report/section";
import type { Relationship, Report } from "@/components/report/types";
import { formatScore, shortId } from "@/lib/format";
import { cn } from "@/lib/utils";

const LABELS: Record<Relationship["label"], { icon: LucideIcon; word: string }> = {
  supports: { icon: Equal, word: "Supports" },
  contradicts: { icon: EqualNot, word: "Contradicts" },
  extends: { icon: GitBranchPlus, word: "Extends" },
  new_question: { icon: MessageCircleQuestion, word: "New question" },
  related_unestablished: { icon: Minus, word: "Related (no relationship established)" },
};

/** Relationships first (supports, contradicts, extends, new question, then related), then by similarity. */
function ordered(items: Relationship[]): Relationship[] {
  return [...items].sort((a, b) => {
    const byLabel = LABEL_ORDER.indexOf(a.label) - LABEL_ORDER.indexOf(b.label);
    if (byLabel !== 0) return byLabel;
    return (b.similarity ?? -Infinity) - (a.similarity ?? -Infinity);
  });
}

/**
 * Related evidence (EXPERIENCE "Related evidence item", "Relationship labels").
 * A label other than "Related (no relationship established)" always comes with
 * the two checked quotes; similarity is a plain figure labelled "similarity, not
 * evidence" and never stands in for a quote. `j` and `k` move between items.
 */
export function RelatedEvidence({ report }: { report: Report }) {
  const items = ordered(report.related);
  const retrieval = report.retrieval;
  const textSearch = retrieval?.method === "text_search";
  const listRef = useRef<HTMLOListElement>(null);

  const move = useCallback((step: 1 | -1) => {
    const nodes = Array.from(listRef.current?.querySelectorAll<HTMLElement>("[data-related-item]") ?? []);
    if (nodes.length === 0) return;
    const at = nodes.findIndex((n) => n === document.activeElement || n.contains(document.activeElement));
    const next = at < 0 ? (step === 1 ? 0 : nodes.length - 1) : Math.min(nodes.length - 1, Math.max(0, at + step));
    nodes[next].focus();
    nodes[next].scrollIntoView({ block: "nearest" });
  }, []);
  useHotkeys("j", () => move(1), [move]);
  useHotkeys("k", () => move(-1), [move]);

  return (
    <Section
      id="related"
      icon={Layers}
      title="Related evidence"
      aside={
        retrieval ? (
          textSearch ? (
            <CapabilityTag
              label="Atlas Search (text)"
              hint="Related evidence is retrieved by text search in Atlas because Vector Search was unavailable."
            />
          ) : (
            <CapabilityTag
              label="Atlas Vector Search"
              hint="Related evidence is retrieved by Vector Search over embeddings stored in Atlas. The score is similarity, not evidence."
            />
          )
        ) : null
      }
    >
      {retrieval ? (
        textSearch ? (
          <p className="m-0 flex items-center gap-1.5 text-caption font-semibold text-low-confidence">
            <TextSearch className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            Related by text search (Vector Search unavailable)
          </p>
        ) : (
          <p className="m-0 text-caption text-muted-foreground">Related by Atlas Vector Search, top {retrieval.top_k}.</p>
        )
      ) : null}
      {items.length > 1 ? (
        <p className="m-0 text-caption text-muted-foreground">Keyboard: j and k move between related items.</p>
      ) : null}

      {items.length === 0 ? (
        <p className="text-body m-0 text-muted-foreground">No related evidence was found for this discovery.</p>
      ) : (
        <ol ref={listRef} className="m-0 flex list-none flex-col gap-4 p-0" aria-label="Related evidence items">
          {items.map((r) => (
            <RelatedItem key={r.id} item={r} fallbackMethod={retrieval?.method ?? null} runId={report.run_id} />
          ))}
        </ol>
      )}
    </Section>
  );
}

function RelatedItem({
  item: r,
  fallbackMethod,
  runId,
}: {
  item: Relationship;
  fallbackMethod: "vector_search" | "text_search" | null;
  runId: string;
}) {
  const { icon: Icon, word } = LABELS[r.label];
  const established = r.label !== "related_unestablished";
  const nct = nctIdOf(r.related_ref);
  const method = r.retrieval_method ?? fallbackMethod;
  const score = formatScore(r.similarity);
  const fromTask = r.origin.startsWith("task:");

  return (
    <li
      data-related-item
      tabIndex={-1}
      className="flex min-w-0 flex-col gap-3 rounded-md border border-border p-4 focus-visible:outline-2"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-sm border bg-card px-2 py-0.5 text-caption font-semibold",
            established ? "border-border" : "border-dashed border-border text-muted-foreground",
          )}
        >
          <Icon className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
          {word}
        </span>
        {r.status === "accepted" ? <AcceptedBadge /> : r.status === "reverted" ? <RevertedBadge /> : <PendingBadge />}
        {fromTask ? <span className="text-caption text-muted-foreground">Filed by the follow-up task</span> : null}
      </div>

      <p className="text-body m-0 flex flex-wrap items-baseline gap-x-2 break-words">
        <span className="font-semibold">{r.related_title ?? (r.related_kind === "finding" ? "Earlier finding" : "Related record")}</span>
        {nct ? (
          <ExternalLink href={trialUrl(nct)}>{nct}</ExternalLink>
        ) : (
          <span className="text-identifier">{r.related_ref}</span>
        )}
      </p>

      {established ? (
        <>
          {r.rationale ? <p className="text-body m-0 max-w-[75ch]">{r.rationale}</p> : null}
          {r.new_quote && r.related_quote ? (
            <div className="grid gap-4 md:grid-cols-2">
              <EvidenceQuote
                heading="New evidence"
                text={r.new_quote.text}
                found={r.new_quote.quote_found}
                refId={nctIdOf(r.new_quote.source_ref) ?? r.new_quote.source_ref}
                href={nctIdOf(r.new_quote.source_ref) ? trialUrl(nctIdOf(r.new_quote.source_ref) as string) : null}
                versionId={r.new_quote.version_id}
              />
              <EvidenceQuote
                heading="Related evidence"
                text={r.related_quote.text}
                found={r.related_quote.quote_found}
                refId={nctIdOf(r.related_quote.source_ref) ?? r.related_quote.source_ref}
                href={nctIdOf(r.related_quote.source_ref) ? trialUrl(nctIdOf(r.related_quote.source_ref) as string) : null}
                versionId={r.related_quote.version_id}
              />
            </div>
          ) : null}
        </>
      ) : (
        <p className="text-caption m-0 text-muted-foreground">Fewer than two checked quotes.</p>
      )}

      <p className="m-0 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-caption text-muted-foreground">
        {score ? (
          <>
            <span>{method === "text_search" ? "Text score" : "Similarity"}</span>
            <span className="text-identifier">{score}</span>
            <span>({method === "text_search" ? "text score, not evidence" : "similarity, not evidence"})</span>
          </>
        ) : (
          <span>No similarity recorded.</span>
        )}
        {r.filed_by_decision_id && !fromTask ? (
          <Link
            href={`/runs/${encodeURIComponent(runId)}/audit#${encodeURIComponent(r.filed_by_decision_id)}`}
            className="underline underline-offset-2"
          >
            Audit entry <span className="text-identifier">{shortId(r.filed_by_decision_id)}</span>
          </Link>
        ) : null}
      </p>
    </li>
  );
}
