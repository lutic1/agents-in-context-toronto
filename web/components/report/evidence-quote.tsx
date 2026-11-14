import { TriangleAlert } from "lucide-react";

import { ExternalLink } from "@/components/report/external-link";
import { formatDate } from "@/lib/format";
import { shortId } from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * An evidence quote (EXPERIENCE "Evidence Display Rules"): the source's own
 * words in the quote face, with the source name, the identifier link and "data
 * as of" beneath it. A quote the API says it could not find in the source is
 * shown as unchecked, in words, and never as support.
 */
export function EvidenceQuote({
  text,
  found = true,
  sourceName,
  refId,
  href,
  asOf,
  versionId,
  heading,
  className,
}: {
  text: string;
  found?: boolean;
  sourceName?: string | null;
  refId?: string | null;
  href?: string | null;
  asOf?: string | null;
  versionId?: string | null;
  heading?: string;
  className?: string;
}) {
  return (
    <figure className={cn("m-0 flex min-w-0 flex-col gap-2", className)}>
      {heading ? <figcaption className="text-caption font-semibold text-muted-foreground">{heading}</figcaption> : null}
      <blockquote className="evidence-quote m-0 break-words">{text}</blockquote>
      {found ? null : (
        <p className="m-0 flex items-center gap-1.5 text-caption text-low-confidence">
          <TriangleAlert className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
          Quote not found in the source text. Treat it as unchecked.
        </p>
      )}
      <p className="m-0 flex flex-wrap items-center gap-x-2 gap-y-1 text-caption text-muted-foreground">
        {sourceName ? <span>{sourceName}</span> : null}
        {refId ? href ? <ExternalLink href={href}>{refId}</ExternalLink> : <span className="text-identifier">{refId}</span> : null}
        {asOf ? <span>data as of {formatDate(asOf)}</span> : null}
        {versionId ? (
          <span>
            source version <span className="text-identifier">{shortId(versionId)}</span>
          </span>
        ) : null}
      </p>
    </figure>
  );
}
