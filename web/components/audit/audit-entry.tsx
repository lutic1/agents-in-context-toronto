"use client";

import { ShieldQuestion } from "lucide-react";

import {
  AppLink,
  CapabilityTag,
  CopyId,
  Mono,
  PersonName,
  SourceRef,
  StatusPill,
} from "@/components/audit/common";
import {
  ChecksList,
  ClaimBlocked,
  EvidenceQuote,
  InputsList,
  MemoriesUsed,
  RelationshipsList,
  RetrievalBlock,
} from "@/components/audit/entry-parts";
import { ResolveControl } from "@/components/audit/resolve-control";
import {
  TONE_CLASS,
  asSearchResult,
  asSlackResult,
  entryState,
  entrySubject,
  isClaimBlocked,
  kindName,
  policySetText,
  type Audit,
  type AuditEntry,
} from "@/components/audit/labels";
import { Button } from "@/components/ui/button";
import { displayName, formatDate, formatDateTime, formatGrant, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";

/** What every entry needs from the page around it. */
export type AuditContext = {
  audit: Audit;
  /** True when `GET /whoami`'s actions include `resolve_notification` (D53). */
  canResolve: boolean;
  onResolved: () => void;
  selectedId: string | null;
  onWho: (entry: AuditEntry) => void;
};

export function entryAnchor(decisionId: string): string {
  return `entry-${decisionId}`;
}

// ---- The shell ---------------------------------------------------------------

/**
 * One entry of the timeline: the state mark and word, the kind, the subject
 * and the time, then whatever the kind adds (`children`), then the checks,
 * inputs, grant and policy set and "Who authorised this?".
 */
export function EntryShell({
  entry,
  position,
  ctx,
  children,
  who,
}: {
  entry: AuditEntry;
  position: number;
  ctx: AuditContext;
  children?: React.ReactNode;
  /** Words for who acted. Run entries name the agent; Reviewer decisions name the Reviewer. */
  who: React.ReactNode;
}) {
  const state = entryState(entry);
  const StateIcon = state.icon;
  const blocked = entry.outcome === "blocked";
  const when = entry.decided_at ?? entry.observed_at;
  const selected = ctx.selectedId === entry.decision_id;

  return (
    <li className="relative">
      <span
        className="absolute -left-[37px] top-4 flex size-6 items-center justify-center rounded-full border border-border bg-card"
        aria-hidden="true"
      >
        <StateIcon className={cn("size-3.5", TONE_CLASS[state.tone])} strokeWidth={1.75} />
      </span>
      <article
        id={entryAnchor(entry.decision_id)}
        tabIndex={-1}
        data-audit-entry=""
        aria-label={`Entry ${position}: ${kindName(entry)}, ${state.word}`}
        className={cn(
          "flex flex-col gap-3 rounded-md border border-border bg-card p-4 scroll-mt-24",
          blocked && "border-l-[3px] border-l-destructive",
          selected && "bg-ink-tint/40",
        )}
      >
        <header className="flex flex-col gap-1">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h3 className="flex flex-wrap items-baseline gap-x-2 text-heading">
              <span>{kindName(entry)}</span>
              <span className="text-table font-normal text-muted-foreground">
                <SubjectText entry={entry} />
              </span>
            </h3>
            {when ? <span className="text-identifier text-muted-foreground">{formatTime(when)}</span> : null}
          </div>
          <p className={cn("flex items-center gap-1.5 text-table font-semibold", TONE_CLASS[state.tone])}>
            <StateIcon className="size-4" strokeWidth={1.75} aria-hidden="true" />
            {state.word}
          </p>
          <p className="text-caption text-muted-foreground">{who}</p>
        </header>

        {blocked ? <BlockedLine entry={entry} ctx={ctx} /> : null}
        {children}

        <EntryFooter entry={entry} ctx={ctx} />
      </article>
    </li>
  );
}

function SubjectText({ entry }: { entry: AuditEntry }) {
  const subject = entrySubject(entry);
  if (entry.report_id) {
    return <AppLink href={`/reports/${encodeURIComponent(entry.report_id)}`}>{subject}</AppLink>;
  }
  const source = entry.evidence_ref?.source_ref;
  if (source && subject === source) return <SourceRef source={source} />;
  return <>{subject}</>;
}

/** "Blocked before it ran: {check} failed under policy set ps_ab12… (N policies)." plus the failed check's reason. */
function BlockedLine({ entry, ctx }: { entry: AuditEntry; ctx: AuditContext }) {
  if (isClaimBlocked(entry)) return null; // the claim treatment says it
  const { run, policies } = ctx.audit;
  const set = policySetText(entry.policy_set_version, run, policies);
  const detail = entry.checks.find((c) => c.passed === false)?.detail ?? null;
  return (
    <div className="flex flex-col gap-1 text-body">
      <p>
        Blocked before it ran: {entry.failed_check ?? "a check"} failed{set ? " under policy set " : ""}
        {set ? <Mono>{set}</Mono> : null}.
      </p>
      {detail ? <p className="text-table text-muted-foreground">{detail}</p> : null}
      <p>No record changed. No external call made.</p>
    </div>
  );
}

function EntryFooter({ entry, ctx }: { entry: AuditEntry; ctx: AuditContext }) {
  const { run, policies } = ctx.audit;
  const set = policySetText(entry.policy_set_version, run, policies);
  const selected = ctx.selectedId === entry.decision_id;
  return (
    <>
      {entry.evidence_ref?.quote ? (
        <EvidenceQuote
          quote={entry.evidence_ref.quote}
          source={entry.evidence_ref.source_ref}
          versionId={entry.evidence_ref.version_id}
        />
      ) : null}
      <ChecksList checks={entry.checks} />
      <InputsList inputs={entry.inputs} />
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-border pt-3">
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-caption text-muted-foreground">
          <span>
            Grant <Mono>{formatGrant(entry.grant_id, entry.grant_version)}</Mono>
          </span>
          {set ? (
            <span>
              Policy set <Mono>{set}</Mono>
            </span>
          ) : null}
          <Timestamps entry={entry} />
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          aria-pressed={selected}
          data-who-for={entry.decision_id}
          onClick={() => ctx.onWho(entry)}
        >
          <ShieldQuestion aria-hidden="true" />
          Who authorised this?
          <span className="sr-only"> ({kindName(entry)}, entry decision {entry.decision_id})</span>
        </Button>
      </div>
    </>
  );
}

function Timestamps({ entry }: { entry: AuditEntry }) {
  return (
    <>
      {entry.decided_at ? <span>Decided {formatDateTime(entry.decided_at)}</span> : null}
      {entry.claimed_at ? <span>Claimed {formatTime(entry.claimed_at)}</span> : null}
      {entry.observed_at ? <span>Observed {formatTime(entry.observed_at)}</span> : null}
    </>
  );
}

// ---- Run entries -------------------------------------------------------------

/** Words for who acted on a run entry: the agent, and who started the run. */
function RunActor({ entry, audit }: { entry: AuditEntry; audit: Audit }) {
  const agent = entry.stamp?.agent ?? audit.run.agent;
  const by = entry.stamp?.initiated_by ?? audit.run.initiated_by;
  return (
    <>
      Agent <Mono>{agent}</Mono>, started by {by ? <PersonName id={by} className="align-middle" /> : "unknown"}
    </>
  );
}

/** The redraft that follows a blocked claim: the next allowed report-level entry. */
function redraftOf(entry: AuditEntry, entries: AuditEntry[]): string | null {
  const at = entries.findIndex((e) => e.decision_id === entry.decision_id);
  const next = entries.slice(at + 1).find((e) => e.kind === entry.kind && e.outcome === "allowed" && (e.report_id || e.retrieval));
  return next ? `#${entryAnchor(next.decision_id)}` : null;
}

export function RunEntry({
  entry,
  position,
  ctx,
}: {
  entry: AuditEntry;
  position: number;
  ctx: AuditContext;
}) {
  const { audit } = ctx;
  const claimBlocked = isClaimBlocked(entry);
  const scan = entry.scan ?? null;
  const search = asSearchResult(entry.result);

  return (
    <EntryShell entry={entry} position={position} ctx={ctx} who={<RunActor entry={entry} audit={audit} />}>
      {claimBlocked ? (
        <ClaimBlocked claims={entry.claims} redraftHref={redraftOf(entry, audit.entries)} />
      ) : null}

      {entry.kind === "search_source" && (scan || search) ? <SearchSourceBlock entry={entry} /> : null}

      {entry.kind === "notify_slack" ? <SlackBlock entry={entry} ctx={ctx} /> : null}

      {entry.outcome === "allowed" && entry.claims.length > 0 && !claimBlocked ? (
        <PassedClaims entry={entry} />
      ) : null}

      {entry.retrieval ? <RetrievalBlock retrieval={entry.retrieval} /> : null}
      {entry.memories_used.length > 0 ? <MemoriesUsed memories={entry.memories_used} /> : null}
      {entry.relationships.length > 0 ? <RelationshipsList relationships={entry.relationships} /> : null}

      {entry.proposal_review ? (
        <ReviewStatus
          label="Proposal"
          status={entry.proposal_review.status}
          by={entry.proposal_review.decided_by}
          at={entry.proposal_review.decided_at}
        />
      ) : null}
      {entry.report_review ? (
        <ReviewStatus
          label="Report"
          status={entry.report_review.status}
          by={entry.report_review.decided_by}
          at={entry.report_review.decided_at}
        />
      ) : null}
    </EntryShell>
  );
}

/** Claim checks that passed on an allowed entry (a redraft), named by their check. */
function PassedClaims({ entry }: { entry: AuditEntry }) {
  return (
    <p className="text-table text-muted-foreground">
      Claim checks passed:{" "}
      {entry.claims.map((c, i) => (
        <span key={`${c.claim_kind}-${i}`}>
          {i > 0 ? "; " : ""}
          {c.text}
        </span>
      ))}
    </p>
  );
}

/** The live DxP review status of the report or proposal, read at request time (AD-22). */
export function ReviewStatus({
  label,
  status,
  by,
  at,
}: {
  label: string;
  status: "pending" | "accepting" | "accepted" | "rejected" | "reverting" | "reverted" | "applying" | "applied";
  by: string | null;
  at: string | null;
}) {
  const pill =
    status === "accepted" || status === "applied"
      ? "accepted"
      : status === "rejected"
        ? "rejected"
        : status === "reverted"
          ? "reverted"
          : status === "accepting" || status === "applying" || status === "reverting"
            ? "working"
            : "pending";
  const verb =
    status === "accepted" ? "Accepted" : status === "applied" ? "Applied" : status === "rejected" ? "Rejected" : status === "reverted" ? "Reverted" : null;
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-table">
      <span className="text-caption font-semibold text-muted-foreground">{label} review status now</span>
      <StatusPill status={pill} />
      {verb && by ? (
        <span className="text-muted-foreground">
          {verb} by {displayName(by)}
          {at ? ` at ${formatDateTime(at)}` : ""}
        </span>
      ) : null}
    </p>
  );
}

// ---- Search source -------------------------------------------------------------

function SearchSourceBlock({ entry }: { entry: AuditEntry }) {
  const scan = entry.scan ?? null;
  const result = asSearchResult(entry.result);
  const from = scan?.cursor_from ?? result?.cursor_from ?? null;
  const to = scan?.cursor_to ?? result?.cursor_to ?? null;
  const refs = scan?.source_refs?.length ? scan.source_refs : (result?.source_refs ?? []);
  const query = scan?.query ? (typeof scan.query === "string" ? scan.query : JSON.stringify(scan.query)) : null;
  return (
    <div className="flex flex-col gap-1 text-table">
      {query ? (
        <p>
          Query: <Mono>{query}</Mono>
        </p>
      ) : null}
      <p>
        {from ? `Scanned trials updated since ${formatDate(from)}.` : "Scan cursor not recorded."}{" "}
        {to ? (
          <>
            Cursor after the scan: {formatDate(to)}.
          </>
        ) : null}
      </p>
      <p>
        {result ? `${result.count} ${result.count === 1 ? "record" : "records"} fetched` : "Sources fetched"}
        {result?.http_status ? (
          <>
            {" "}(HTTP <Mono>{result.http_status}</Mono>)
          </>
        ) : null}
        {refs.length > 0 ? ":" : "."}
      </p>
      {refs.length > 0 ? (
        <ul className="flex flex-wrap gap-x-4 gap-y-1">
          {refs.map((r) => (
            <li key={r}>
              <SourceRef source={r} />
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

// ---- Slack -------------------------------------------------------------------

/** The Slack result: delivered with its time, failed, or unknown with Resolve; the HTTP status, Slack's reply and the link URLs sent (S9). Never the webhook URL. */
function SlackBlock({ entry, ctx }: { entry: AuditEntry; ctx: AuditContext }) {
  const result = asSlackResult(entry.result);
  const status = entry.status;
  const actionId = entry.action_id;
  const resolved = entry.resolution;

  return (
    <div className="flex flex-col gap-2 rounded-md border border-border p-3">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <h4 className="text-table font-semibold">Slack result</h4>
        <CapabilityTag
          name="Atomic updates"
          sentence="Each Slack alert is claimed with one conditional update in Atlas, so two workers never both post it."
        />
      </div>

      {status === "delivered" ? (
        <p className="text-table text-accepted">
          Slack alert delivered{result?.posted_at ? ` at ${formatTime(result.posted_at)}` : ""} to #all-mango-db-hackathon
        </p>
      ) : null}

      {status === "unknown" && actionId ? (
        <div className="flex flex-col gap-2">
          <p className="text-table text-low-confidence">
            Unknown: check #all-mango-db-hackathon for the action ID <CopyId value={actionId} />, then resolve.
          </p>
          {ctx.canResolve ? <ResolveControl actionId={actionId} onResolved={ctx.onResolved} /> : null}
        </div>
      ) : null}

      {status === "failed" ? (
        <p className="text-table text-destructive">
          Failed{result?.response_body ? `: ${result.response_body}` : ""}. Not retried.
        </p>
      ) : null}

      {status === "reconciling" ? (
        <p className="text-table text-low-confidence">Reconciling: the sweep is settling this alert.</p>
      ) : null}

      {status === "queued" || status === "dispatching" ? (
        <p className="text-table text-muted-foreground">Waiting for Slack to answer.</p>
      ) : null}

      {actionId && status !== "unknown" ? (
        <p className="text-caption text-muted-foreground">
          Action <CopyId value={actionId} />
        </p>
      ) : null}

      {resolved ? (
        <p className="text-table">
          Resolved by {displayName(resolved.by)} at {formatTime(resolved.at)} as{" "}
          {resolved.outcome === "delivered" ? "delivered" : "failed"}. Note: {resolved.note}
        </p>
      ) : null}

      {result ? (
        <dl className="grid grid-cols-1 gap-x-4 gap-y-1 text-table sm:grid-cols-[max-content_minmax(0,1fr)]">
          <dt className="text-caption text-muted-foreground">HTTP status</dt>
          <dd>{result.http_status !== null ? <Mono>{result.http_status}</Mono> : "No response arrived"}</dd>
          <dt className="text-caption text-muted-foreground">Slack&apos;s response</dt>
          <dd>{result.response_body !== null ? <Mono>{result.response_body}</Mono> : "None"}</dd>
          <dt className="text-caption text-muted-foreground">Review in DxP link</dt>
          <dd>
            <Mono>{result.link_urls.report_url}</Mono>
          </dd>
          <dt className="text-caption text-muted-foreground">Open diagnostic link</dt>
          <dd>{result.link_urls.diagnostic_url ? <Mono>{result.link_urls.diagnostic_url}</Mono> : "Not sent: no Diagnostic resolved"}</dd>
        </dl>
      ) : null}
    </div>
  );
}
