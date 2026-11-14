"use client";

import Link from "next/link";
import { CircleAlert, CircleDashed, Clock, SearchX } from "lucide-react";

import { AcceptedBadge } from "@/components/report/badges";
import { EvidenceQuote } from "@/components/report/evidence-quote";
import { keyLabel, nctIdOf, trialUrl } from "@/components/report/labels";
import type { components } from "@/lib/types";
import { SyntheticBadge, EarlyResearchBadge } from "@/components/shell/badges";
import { ApiUnreachableNotice, Notice } from "@/components/shell/notice";
import { PageSkeleton } from "@/components/shell/page-skeleton";
import { StageTrack } from "@/components/shell/stage-track";
import { buttonVariants } from "@/components/ui/button";
import { ApiError, isUnreachable, itemsOf } from "@/lib/api";
import { displayName, formatDateTime, shortId } from "@/lib/format";
import { POLL_MS, useApi } from "@/lib/use-api";

type Value = components["schemas"]["Value"];
type SchemaField = components["schemas"]["SchemaField"];

/** A stage ID such as `assay_development` as a label. */
function stageLabel(id: string): string {
  return keyLabel(id);
}

/**
 * The Accepted knowledge view of one Diagnostic (Story 1.3, narrowed), from
 * `GET /diagnostics/<dx_id>`. It shows the Diagnostic's accepted values with
 * their Evidence, each linked to the report that accepted it. Pending content
 * is never shown here: a pending report that would change this Diagnostic
 * appears only as a notice above, linking to the report. No value-level
 * Accept, Edit or Reject controls are built (EXPERIENCE "Cut or deferred").
 */
export function DiagnosticView({ dxId }: { dxId: string }) {
  const route = "/diagnostics/{dx_id}" as const;
  const record = useApi(route, { path: { dx_id: dxId }, interval: POLL_MS * 5 });
  const schema = useApi("/schema");
  const pending = useApi("/reports", { query: { status: "pending" }, interval: POLL_MS });

  if (!record.data) {
    if (record.isLoading) return <PageSkeleton rows={5} />;
    if (record.error instanceof ApiError && record.error.status === 404) {
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">Diagnostic not found</h1>
          <Notice icon={SearchX} title="Diagnostic not found" role="status">
            This Diagnostic was not found. Open Reports to see what is pending.
          </Notice>
          <div>
            <Link href="/reports" className={buttonVariants({ variant: "default" })}>
              Open Reports
            </Link>
          </div>
        </div>
      );
    }
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-title">Accepted knowledge</h1>
        {isUnreachable(record.error) ? (
          <ApiUnreachableNotice />
        ) : (
          <Notice icon={CircleAlert} title="This Diagnostic could not be loaded" role="alert">
            {record.error instanceof ApiError && record.error.status === 501
              ? "The Diagnostic route is not available yet."
              : (record.error?.message ?? "The API answered, but not with a Diagnostic.")}
          </Notice>
        )}
      </div>
    );
  }

  const dx = record.data;
  const stages = (schema.data?.stage_order ?? []).map((id) => ({ id, label: stageLabel(id) }));
  const stageIndex = dx.lifecycle_stage ? stages.findIndex((s) => s.id === dx.lifecycle_stage) : -1;
  const lowThreshold = schema.data?.low_confidence_threshold ?? null;
  const affecting = itemsOf(pending.data).filter((r) => r.diagnostic_ids.includes(dx.id));

  // Show every field the schema names, in its order, then any other field the record carries.
  const schemaFields: SchemaField[] = schema.data?.fields ?? [];
  const known = new Set(schemaFields.map((f) => f.key));
  const fields: { key: string; label: string; field: SchemaField | null }[] = [
    ...schemaFields.map((f) => ({ key: f.key, label: f.label, field: f })),
    ...Object.keys(dx.fields)
      .filter((k) => !known.has(k))
      .map((k) => ({ key: k, label: keyLabel(k), field: null })),
  ];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex min-w-0 flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-sm">
        <p className="text-caption m-0 font-semibold text-muted-foreground">Accepted knowledge</p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <h1 className="text-title break-words">{dx.name}</h1>
          {dx.early_research ? <EarlyResearchBadge /> : null}
          {dx.synthetic ? <SyntheticBadge /> : null}
        </div>
        {stages.length > 0 ? (
          <StageTrack stages={stages} currentIndex={stageIndex >= 0 ? stageIndex : null} />
        ) : (
          <p className="text-caption m-0 text-muted-foreground">
            {dx.lifecycle_stage ? `Stage: ${stageLabel(dx.lifecycle_stage)}` : "Stage not determined"}
          </p>
        )}
        <p className="text-caption m-0 text-muted-foreground">
          <span className="text-identifier">{dx.id}</span>
          {dx.completeness ? ` · ${dx.completeness.filled} of ${dx.completeness.of} fields filled` : null}
        </p>
      </header>

      {affecting.length > 0 ? (
        <section
          aria-label="Pending reports for this Diagnostic"
          role="status"
          className="flex flex-col gap-2 rounded-md border border-dashed border-muted-foreground bg-card p-4"
        >
          <p className="text-body m-0 flex items-center gap-2 font-semibold">
            <Clock className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            {affecting.length} pending {affecting.length === 1 ? "report would" : "reports would"} change this Diagnostic.
          </p>
          <ul className="m-0 flex list-none flex-col gap-1 p-0">
            {affecting.map((r) => (
              <li key={r.id} className="text-body">
                <Link href={`/reports/${encodeURIComponent(r.id)}`} className="underline underline-offset-2">
                  Open report: {r.headline}
                </Link>
              </li>
            ))}
          </ul>
          <p className="text-caption m-0 text-muted-foreground">Pending content is not shown below. Only accepted knowledge is.</p>
        </section>
      ) : null}

      {fields.map(({ key, label, field }) => {
        const entry = dx.fields[key];
        // Accepted knowledge shows only current values.
        const values = (entry?.values ?? []).filter((v) => v.state === "current");
        return (
          <section
            key={key}
            aria-labelledby={`field-${key}`}
            className="flex min-w-0 flex-col gap-4 rounded-lg border border-border bg-card p-5 shadow-sm"
          >
            <h2 id={`field-${key}`} className="text-heading">
              {label}
            </h2>
            {values.length === 0 ? (
              <p className="text-body m-0 flex items-center gap-2 text-muted-foreground">
                <CircleDashed className="size-4 shrink-0" strokeWidth={1.75} aria-hidden="true" />
                No data for this indication
              </p>
            ) : (
              <ul className="m-0 flex list-none flex-col gap-4 p-0">
                {values.map((v) => (
                  <ValueRow key={v.value_id} value={v} field={field} lowThreshold={lowThreshold} />
                ))}
              </ul>
            )}
          </section>
        );
      })}

      {fields.length === 0 ? (
        <Notice icon={CircleDashed} title="No accepted knowledge yet" role="status">
          Nothing has been accepted for this Diagnostic.
        </Notice>
      ) : null}
    </div>
  );
}

function ValueRow({ value: v, field, lowThreshold }: { value: Value; field: SchemaField | null; lowThreshold: number | null }) {
  const enumLabel = field?.enum?.find((e) => e.value === v.value)?.label ?? null;
  const evidence = v.evidence;
  const low =
    lowThreshold !== null && v.check?.confidence !== null && v.check?.confidence !== undefined && v.check.confidence < lowThreshold;

  return (
    <li className="flex min-w-0 flex-col gap-3 rounded-md border border-border p-4">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className="text-body break-words font-semibold">{enumLabel ?? v.value}</span>
        {enumLabel ? <span className="text-identifier text-muted-foreground">{v.value}</span> : null}
        <AcceptedBadge />
        {v.review === "unreviewed" ? <span className="text-caption text-muted-foreground">Unreviewed</span> : null}
        {low ? (
          <span className="inline-flex items-center gap-1 text-caption text-low-confidence">
            <CircleDashed className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
            Low confidence
          </span>
        ) : null}
      </div>

      {"manual" in evidence ? (
        <div className="flex flex-col gap-1">
          <p className="text-caption m-0 font-semibold">Manually sourced</p>
          {evidence.note ? <p className="text-body m-0">{evidence.note}</p> : null}
          {evidence.submitter ? (
            <p className="text-caption m-0 text-muted-foreground">Submitted by {displayName(evidence.submitter)}</p>
          ) : null}
        </div>
      ) : evidence.quote ? (
        <EvidenceQuote
          text={evidence.quote}
          found={v.check?.quote_found ?? true}
          sourceName={evidence.source}
          refId={nctIdOf(evidence.source_ref) ?? evidence.source_ref}
          href={evidence.source_url ?? (nctIdOf(evidence.source_ref) ? trialUrl(nctIdOf(evidence.source_ref) as string) : null)}
          asOf={evidence.data_as_of ?? evidence.source_date}
          versionId={evidence.version_id}
        />
      ) : (
        <p className="text-caption m-0 text-muted-foreground">
          {evidence.source ?? "Source"} {evidence.source_ref}
          {evidence.data_as_of ? `, data as of ${evidence.data_as_of}` : ""}
        </p>
      )}

      <p className="m-0 flex flex-wrap items-baseline gap-x-4 gap-y-1 text-caption text-muted-foreground">
        <WrittenBy value={v} />
        {v.decided_by && v.decided_at ? (
          <span>
            Accepted by {displayName(v.decided_by)} at {formatDateTime(v.decided_at)}
          </span>
        ) : null}
        <PromotedBy proposalId={v.proposal_id} />
      </p>
    </li>
  );
}

/** The run that wrote the value, or "seed" (the value's own stamp). */
function WrittenBy({ value: v }: { value: Value }) {
  const stamp = v.stamp;
  if (stamp?.run_id) {
    return (
      <span>
        Written by run{" "}
        <Link href={`/runs/${encodeURIComponent(stamp.run_id)}`} className="text-identifier underline underline-offset-2">
          {shortId(stamp.run_id)}
        </Link>
      </span>
    );
  }
  return <span>Written by {stamp?.kind === "seed" ? "seed" : stamp ? displayName(stamp.principal) : "an unknown source"}</span>;
}

/**
 * The report that promoted a value (V58): found through the value's
 * `proposal_id`, whose proposal carries the `report_id`. Nothing shows for a
 * value no proposal wrote.
 */
function PromotedBy({ proposalId }: { proposalId: string | null }) {
  const { data } = useApi("/proposals/{p_id}", { path: { p_id: proposalId ?? "" }, enabled: Boolean(proposalId) });
  if (!proposalId) return null;
  if (!data?.report_id) return <span>Proposal <span className="text-identifier">{shortId(proposalId)}</span></span>;
  return (
    <span>
      Accepted in report{" "}
      <Link href={`/reports/${encodeURIComponent(data.report_id)}`} className="text-identifier underline underline-offset-2">
        {shortId(data.report_id)}
      </Link>
    </span>
  );
}
