"use client";

import Link from "next/link";
import { ClipboardCheck } from "lucide-react";

import { AcceptedBadge, PendingBadge, RejectedBadge, RevertedBadge } from "@/components/report/badges";
import { EvidenceQuote } from "@/components/report/evidence-quote";
import { nctIdOf, trialUrl } from "@/components/report/labels";
import { Section } from "@/components/report/section";
import type { Proposal, Report } from "@/components/report/types";
import { ApiError, isUnreachable, itemsOf } from "@/lib/api";
import { displayName, formatDateTime, formatScore, shortId } from "@/lib/format";
import { useApi } from "@/lib/use-api";

/**
 * Proposed updates (EXPERIENCE "Proposed updates"): each knowledge update the
 * agent filed with this report, read from `GET /proposals?report_id=`. Pending
 * updates carry "Pending review"; after approval each shows "Accepted". An update
 * aimed at a Diagnostic links to the Accepted knowledge view once accepted; a
 * scope-collection update (`diagnostic_id: null`, V43) says "Accepted into the
 * scope's evidence collection" in place and never links. A reverse proposal (a
 * revert, V48) is not an update to review and is left to the audit.
 */
export function ProposedUpdates({ report }: { report: Report }) {
  const { data, error, isLoading } = useApi("/proposals", {
    query: { report_id: report.id },
    interval: 5000,
  });
  const updates = itemsOf(data).filter((p) => p.op === "add");

  return (
    <Section id="updates" icon={ClipboardCheck} title="Proposed updates">
      {isLoading && !data ? (
        <p className="text-body m-0 text-muted-foreground" role="status">
          Loading the proposed updates.
        </p>
      ) : error && !data ? (
        <p className="text-body m-0 text-muted-foreground" role="status">
          {isUnreachable(error)
            ? "Couldn't reach the API, so the proposed updates are not shown."
            : error instanceof ApiError && error.status === 501
              ? "The proposed updates are not available yet."
              : `The proposed updates could not be loaded. ${error.message}`}
        </p>
      ) : updates.length === 0 ? (
        <p className="text-body m-0 text-muted-foreground">This report proposes no updates.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-4 p-0">
          {updates.map((p) => (
            <UpdateRow key={p.id} proposal={p} reportStatus={report.status} />
          ))}
        </ul>
      )}
    </Section>
  );
}

function UpdateRow({ proposal: p, reportStatus }: { proposal: Proposal; reportStatus: Report["status"] }) {
  const toScope = p.diagnostic_id === null;
  const reverted = reportStatus === "reverted" && p.status === "applied";
  const accepted = p.status === "applied" && !reverted;
  const evidence = p.evidence;
  const checked = p.check;

  return (
    <li className="flex min-w-0 flex-col gap-3 rounded-md border border-border p-4">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        {reverted ? (
          <RevertedBadge />
        ) : accepted ? (
          <AcceptedBadge />
        ) : p.status === "rejected" ? (
          <RejectedBadge />
        ) : p.status === "applying" ? (
          <PendingBadge>Accepting</PendingBadge>
        ) : (
          <PendingBadge />
        )}
        {p.decided_by && p.decided_at && (accepted || p.status === "rejected") ? (
          <span className="text-caption text-muted-foreground">
            {accepted ? "Accepted" : "Rejected"} by {displayName(p.decided_by)} at {formatDateTime(p.decided_at)}
          </span>
        ) : null}
      </div>

      <p className="text-body m-0 max-w-[75ch] break-words">
        {toScope ? (
          <>
            Add <span className="font-semibold">{p.value}</span> to the scope&apos;s evidence collection
            {p.label ? `, as ${p.label}` : ""}. No assay record changes.
          </>
        ) : (
          <>
            Add <span className="font-semibold">{p.value}</span> to {p.field.replace(/_/g, " ")} on{" "}
            <span className="font-semibold">{p.diagnostic_name ?? p.diagnostic_id}</span>.
          </>
        )}
      </p>

      {accepted && toScope ? (
        <p className="text-body m-0 font-semibold">Accepted into the scope&apos;s evidence collection</p>
      ) : null}
      {accepted && !toScope && p.diagnostic_id ? (
        <p className="text-caption m-0">
          <Link href={`/diagnostics/${encodeURIComponent(p.diagnostic_id)}`} className="underline underline-offset-2">
            Open accepted knowledge
          </Link>
        </p>
      ) : null}

      {evidence && "manual" in evidence ? (
        <div className="flex flex-col gap-1">
          <p className="text-caption m-0 font-semibold">Manually sourced</p>
          {evidence.note ? <p className="text-body m-0">{evidence.note}</p> : null}
        </div>
      ) : evidence && evidence.quote ? (
        <EvidenceQuote
          text={evidence.quote}
          found={checked?.quote_found ?? true}
          sourceName={evidence.source}
          refId={nctIdOf(evidence.source_ref) ?? evidence.source_ref}
          href={evidence.source_url ?? (nctIdOf(evidence.source_ref) ? trialUrl(nctIdOf(evidence.source_ref) as string) : null)}
          asOf={evidence.data_as_of ?? evidence.source_date}
          versionId={evidence.version_id}
        />
      ) : null}

      <p className="m-0 flex flex-wrap items-baseline gap-x-4 gap-y-1 text-caption text-muted-foreground">
        {checked?.confidence !== null && checked?.confidence !== undefined ? (
          <span>
            Confidence <span className="text-identifier">{formatScore(checked.confidence)}</span>
          </span>
        ) : null}
        {p.run_id ? (
          <span>
            Filed by run{" "}
            <Link href={`/runs/${encodeURIComponent(p.run_id)}`} className="text-identifier underline underline-offset-2">
              {shortId(p.run_id)}
            </Link>
          </span>
        ) : null}
      </p>
    </li>
  );
}
