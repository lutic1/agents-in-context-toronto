"use client";

import Link from "next/link";

import { CopyId } from "@/components/run-console/copy-id";
import { entryState, failedClaim, type EntryTone } from "@/components/run-console/entry-state";
import { auditEntryHref, checkName, claimName, destinationName, kindName, sourceLabel } from "@/components/run-console/names";
import { PersonName } from "@/components/run-console/person-name";
import { ResolveControl } from "@/components/run-console/resolve-form";
import type { AuditEntry } from "@/components/run-console/types";
import { formatDate, formatPolicySetParts, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";

const TONE_CLASS: Record<EntryTone, string> = {
  pending: "text-muted-foreground",
  "took-effect": "text-accepted",
  delivered: "text-accepted",
  blocked: "text-destructive",
  "claim-blocked": "text-destructive",
  unknown: "text-low-confidence",
  reconciling: "text-low-confidence",
  failed: "text-destructive",
};

type Props = {
  entry: AuditEntry;
  runId: string;
  /** The policy set the run was pinned to and how many policies it has, for "under policy set ps_ab12… (N policies)". */
  policySetVersion: string | null;
  policyCount: number | null;
  /** Resolve is shown only when GET /whoami's actions include `resolve_notification` (D53). */
  canResolve: boolean;
  /** True for a row that appeared after the first load: it fades and slides into place once. */
  animate: boolean;
  onResolved: () => void;
};

/** The action's result as plain fields; each kind reads only the fields it knows. */
function resultOf(entry: AuditEntry): Record<string, unknown> | null {
  const result = entry.result;
  return result && typeof result === "object" ? (result as unknown as Record<string, unknown>) : null;
}

/**
 * One row per gate decision (EXPERIENCE "Action row"): state icon and word, action kind,
 * subject, time. Rows update in place and never jump: the list is keyed by decision ID.
 * Enter on the row's name opens the entry in the Audit view.
 */
export function ActionRow({ entry, runId, policySetVersion, policyCount, canResolve, animate, onResolved }: Props) {
  const state = entryState(entry);
  const Icon = state.Icon;
  const blocked = entry.outcome === "blocked";
  const claim = failedClaim(entry);
  const subject = entry.evidence_ref?.source_ref ? sourceLabel(entry.evidence_ref.source_ref) : destinationName(entry.destination);
  const diagnosticId = typeof entry.inputs?.diagnostic_id === "string" ? entry.inputs.diagnostic_id : null;

  const sameSet = entry.policy_set_version !== null && entry.policy_set_version === policySetVersion;
  const policy = entry.policy_set_version ? formatPolicySetParts(entry.policy_set_version, sameSet && policyCount !== null ? policyCount : undefined) : null;

  return (
    <li
      id={entry.decision_id}
      className={cn(
        "rounded-md border border-border bg-card",
        blocked && "border-l-[3px] border-l-destructive",
        animate && "row-enter",
      )}
    >
      <div className="grid gap-x-4 gap-y-1 p-3 sm:grid-cols-[minmax(10rem,15rem)_minmax(0,1fr)_auto]">
        <p className={cn("flex items-start gap-2 text-table font-semibold", TONE_CLASS[state.tone])}>
          <Icon className="mt-0.5 size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          <span>{state.word}</span>
        </p>

        <div className="min-w-0">
          <p className="text-table">
            <Link
              href={auditEntryHref(runId, entry.decision_id)}
              data-row-link=""
              className="rounded-sm font-semibold text-foreground underline-offset-4 hover:underline"
            >
              {kindName(entry.kind)}
              <span className="sr-only">, open in the Audit view</span>
            </Link>
            <span className="text-muted-foreground"> · </span>
            <span className="text-identifier break-all">{subject}</span>
          </p>
          <Detail
            entry={entry}
            blocked={blocked}
            claim={claim}
            policy={policy}
            diagnosticId={diagnosticId}
          />
        </div>

        <p className="text-identifier text-muted-foreground sm:text-right">
          <time dateTime={entry.decided_at ?? undefined}>{formatTime(entry.decided_at)}</time>
        </p>
      </div>

      {state.tone === "unknown" && canResolve && entry.action_id ? (
        <div className="px-3 pb-3">
          <ResolveControl actionId={entry.action_id} onResolved={onResolved} />
        </div>
      ) : null}
    </li>
  );
}

function Detail({
  entry,
  blocked,
  claim,
  policy,
  diagnosticId,
}: {
  entry: AuditEntry;
  blocked: boolean;
  claim: ReturnType<typeof failedClaim>;
  policy: { hash: string; count: string } | null;
  diagnosticId: string | null;
}) {
  const lines: React.ReactNode[] = [];
  const caption = "text-caption text-muted-foreground";

  if (blocked && claim) {
    lines.push(
      <p key="claim" className="text-caption">
        Claim blocked before filing: {claim.detail ?? `this claim did not pass the check "${claimName(claim.claim_kind)}".`}
      </p>,
      <p key="draft" className="text-table">
        <span className={caption}>Draft: </span>
        <span className="line-through">{claim.text}</span>
      </p>,
      <p key="check" className={caption}>
        Check: {claimName(claim.claim_kind)} <code className="text-identifier">{claim.claim_kind}</code>
      </p>,
      <p key="nothing" className={caption}>
        Nothing filed. No external call made.
      </p>,
    );
  } else if (blocked) {
    const failed = entry.failed_check ? entry.checks.find((check) => check.check === entry.failed_check) : undefined;
    lines.push(
      <p key="blocked" className="text-caption">
        Blocked before it ran: {entry.failed_check ? checkName(entry.failed_check) : "a check"} failed
        {policy ? (
          <>
            {" "}
            under policy set <code className="text-identifier">{policy.hash}</code>
            {policy.count ? ` ${policy.count}` : ""}
          </>
        ) : null}
        .
      </p>,
    );
    if (failed?.detail) {
      lines.push(
        <p key="detail" className={caption}>
          {failed.detail}
        </p>,
      );
    }
    lines.push(
      <p key="nothing" className={caption}>
        Nothing was done. No external call made.
      </p>,
    );
  } else {
    const slack = entry.kind === "notify_slack";
    const status = entry.status ?? "queued";
    const slackResult = slack ? resultOf(entry) : null;
    const searchResult = entry.kind === "search_source" ? resultOf(entry) : null;

    if (slack && status === "delivered") {
      const posted = typeof slackResult?.posted_at === "string" ? slackResult.posted_at : entry.observed_at ?? entry.decided_at;
      lines.push(
        <p key="slack" className="text-caption">
          Slack alert delivered at <span className="text-identifier">{formatTime(posted)}</span> to{" "}
          {destinationName(entry.destination)}. Slack only notifies; the report stays pending until it is decided in DxP.
        </p>,
      );
    } else if (slack && status === "unknown") {
      lines.push(
        <p key="slack" className="text-caption">
          Result unknown. Slack didn&apos;t confirm. Check {destinationName(entry.destination)} for this alert, then
          resolve.{" "}
          {entry.action_id ? (
            <span className="inline-flex items-center gap-1">
              Action ID <CopyId value={entry.action_id} label="action ID" />
            </span>
          ) : null}
        </p>,
      );
    } else if (slack && status === "failed") {
      const http = typeof slackResult?.http_status === "number" ? slackResult.http_status : null;
      lines.push(
        <p key="slack" className="text-caption">
          Slack did not take the alert{http ? ` (HTTP ${http})` : ""}. It was not retried.
        </p>,
      );
    } else if (slack && status === "reconciling") {
      lines.push(
        <p key="slack" className="text-caption">
          DxP is settling whether this alert reached Slack. It is never sent twice.
        </p>,
      );
    }

    if (searchResult) {
      const count = typeof searchResult.count === "number" ? searchResult.count : null;
      const from = typeof searchResult.cursor_from === "string" ? searchResult.cursor_from : null;
      if (count !== null) {
        lines.push(
          <p key="search" className="text-caption">
            {count === 1 ? "1 trial" : `${count} trials`} fetched{from ? `, updated since ${formatDate(from)}` : ""}.
          </p>,
        );
      }
    }

    if (entry.resolution) {
      lines.push(
        <p key="resolution" className={caption}>
          Resolved by <PersonName id={entry.resolution.by} /> at {formatTime(entry.resolution.at)}: marked{" "}
          {entry.resolution.outcome}. {entry.resolution.note}
        </p>,
      );
    }

    if (entry.report_id && (entry.kind === "file_proposal" || entry.kind === "file_related_evidence")) {
      lines.push(
        <p key="report" className="text-caption">
          <Link
            href={`/reports/${encodeURIComponent(entry.report_id)}`}
            className="rounded-sm font-semibold underline underline-offset-4"
          >
            Open report <span className="text-identifier">{entry.report_id}</span>
          </Link>
        </p>,
      );
    }
  }

  if (diagnosticId) {
    lines.push(
      <p key="dx" className="text-caption">
        <Link href={`/diagnostics/${encodeURIComponent(diagnosticId)}`} className="rounded-sm font-semibold underline underline-offset-4">
          Open diagnostic
        </Link>
      </p>,
    );
  }

  return lines.length > 0 ? <div className="mt-1 flex flex-col gap-1">{lines}</div> : null;
}
