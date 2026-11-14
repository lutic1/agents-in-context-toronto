import Link from "next/link";
import { FlaskConical, Tag } from "lucide-react";

import { AlertState } from "@/components/report/alert-state";
import { NewMark, ReportStatusBadge } from "@/components/report/badges";
import { EvidenceQuote } from "@/components/report/evidence-quote";
import { ExternalLink } from "@/components/report/external-link";
import { nctIdOf, statusWord, trialUrl } from "@/components/report/labels";
import type { Report } from "@/components/report/types";
import { formatDateTime, shortId } from "@/lib/format";

/**
 * The discovery header and the discovery itself (EXPERIENCE "Discovery header").
 * The headline is framed as a signal worth investigating, never as performance
 * (V33). The intervention wording is the record's own, verbatim; any name in it
 * is labelled "Named in the record" and never as a claim about what the trial
 * tests or relies on (V37).
 */
export function Discovery({ report }: { report: Report }) {
  const nct = report.nct_id ?? nctIdOf(report.source_ref);
  const d = report.discovery;
  const status = statusWord(d.trial_status);

  return (
    <section
      aria-labelledby="discovery-heading"
      className="flex min-w-0 flex-col gap-5 rounded-lg border border-border bg-card p-5 shadow-sm"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className="inline-flex items-center gap-1.5">
          <FlaskConical className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          <span className="sr-only">Trial</span>
          {nct ? <ExternalLink href={trialUrl(nct)}>{nct}</ExternalLink> : <span className="text-identifier">{report.source_ref}</span>}
        </span>
        {status ? (
          <span className="text-body">
            <span className="sr-only">Registry status: </span>
            {status}
          </span>
        ) : null}
        {d.has_results === false ? <span className="text-body">No results posted</span> : null}
        {d.has_results === true ? <span className="text-body">Results posted</span> : null}
        {report.status === "pending" ? <NewMark /> : null}
        <ReportStatusBadge status={report.status} />
      </div>

      <div className="flex flex-col gap-2">
        <h1 id="discovery-heading" className="text-title break-words">
          {report.headline}
        </h1>
        {d.summary ? <p className="text-body m-0 max-w-[75ch]">{d.summary}</p> : null}
      </div>

      <dl className="m-0 grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-1 text-caption">
        <Meta label="Found by run">
          <Link href={`/runs/${encodeURIComponent(report.run_id)}`} className="text-identifier underline underline-offset-2">
            {shortId(report.run_id)}
          </Link>
        </Meta>
        <Meta label="Research scope">
          <span className="text-identifier">{report.scope_id}</span>
        </Meta>
        <Meta label="Team">
          <span className="text-identifier">{report.team_id}</span>
        </Meta>
        {report.created_at ? <Meta label="Filed">{formatDateTime(report.created_at)}</Meta> : null}
        <Meta label="Source version">
          <span className="text-identifier">{shortId(report.version_id)}</span>
        </Meta>
        <Meta label="Slack">
          <AlertState notification={report.notification} />
        </Meta>
      </dl>

      <div className="flex flex-col gap-3">
        <h3 className="text-caption font-semibold text-muted-foreground">Intervention, as written in the record</h3>
        {d.intervention_text ? (
          <blockquote className="evidence-quote m-0 break-words">{d.intervention_text}</blockquote>
        ) : (
          <p className="text-body m-0 text-muted-foreground">The record gives no intervention wording.</p>
        )}
        {d.mentions.length > 0 ? (
          <ul className="m-0 flex list-none flex-wrap gap-2 p-0" aria-label="Names the record mentions">
            {d.mentions.map((m, i) => (
              <li key={`${m.name}-${i}`} className="flex flex-col gap-1">
                <span className="inline-flex flex-wrap items-center gap-1.5 rounded-sm border border-dotted border-muted-foreground bg-card px-2 py-1">
                  <Tag className="size-3.5 shrink-0 text-muted-foreground" strokeWidth={1.75} aria-hidden="true" />
                  <span className="text-caption">Named in the record</span>
                  <span className="text-identifier break-all">{m.name}</span>
                </span>
                {m.field || !m.resolved_diagnostic_id ? (
                  <span className="text-caption text-muted-foreground">
                    {m.field ? `in ${m.field}` : null}
                    {m.field && !m.resolved_diagnostic_id ? "; " : null}
                    {!m.resolved_diagnostic_id ? "no exact match in the registry" : null}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="flex flex-col gap-3">
        <h3 className="text-caption font-semibold text-muted-foreground">Supporting quotes</h3>
        {d.quotes.length === 0 ? (
          <p className="text-body m-0 text-muted-foreground">No quotes are attached to this discovery.</p>
        ) : (
          <ul className="m-0 flex list-none flex-col gap-4 p-0">
            {d.quotes.map((q, i) => (
              <li key={i}>
                <EvidenceQuote
                  text={q.text}
                  found={q.quote_found}
                  sourceName="ClinicalTrials.gov"
                  refId={nct}
                  href={nct ? trialUrl(nct) : null}
                  versionId={q.version_id ?? report.version_id}
                />
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function Meta({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="m-0 min-w-0 break-words">{children}</dd>
    </>
  );
}
