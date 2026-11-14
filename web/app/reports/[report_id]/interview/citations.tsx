import { Quote } from "lucide-react";

import type { InterviewCitation } from "./interview-api";

/**
 * The citations panel of one answer. Each citation keeps its quote, source, version and field together
 * (Evidence Display Rules). The quote is the record's words, so it is set as a quote; everything else is DxP's.
 */
export function CitationsPanel({ turnId, citations }: { turnId: string; citations: InterviewCitation[] }) {
  if (citations.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-background p-4">
      <h3 className="flex items-center gap-2 text-table font-semibold">
        <Quote className="size-4" strokeWidth={1.75} aria-hidden="true" />
        Citations ({citations.length})
      </h3>
      <ol className="mt-3 flex flex-col gap-4">
        {citations.map((citation, index) => (
          <li key={`${citation.source_ref}-${citation.version_id}-${index}`} id={citationId(turnId, index + 1)} className="scroll-mt-24">
            <blockquote className="evidence-quote break-words">{citation.quote}</blockquote>
            <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-caption text-muted-foreground">
              <dt>Citation</dt>
              <dd className="text-identifier text-foreground">[{index + 1}]</dd>
              <dt>Source</dt>
              <dd className="text-identifier break-all text-foreground">{citation.source_ref}</dd>
              <dt>Version</dt>
              <dd className="text-identifier break-all text-foreground">{citation.version_id ?? "not recorded"}</dd>
              <dt>Field</dt>
              <dd className="text-foreground">{fieldLabel(citation.field)}</dd>
            </dl>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function citationId(turnId: string, number: number): string {
  return `${turnId}-cite-${number}`;
}

function fieldLabel(field: string | null | undefined): string {
  if (field === "discovery") return "Discovery quote";
  if (field === "related") return "Related evidence quote";
  return field ?? "not recorded";
}
