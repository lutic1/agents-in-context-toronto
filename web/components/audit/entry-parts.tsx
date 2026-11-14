"use client";

import {
  Ban,
  Brain,
  CircleDashed,
  Equal,
  EqualNot,
  GitBranchPlus,
  History,
  MessageCircleQuestionMark,
  Minus,
  ShieldCheck,
  ShieldX,
  TextSearch,
  type LucideIcon,
} from "lucide-react";

import { AppLink, CapabilityTag, Mono, PersonName, SourceRef, StatusPill } from "@/components/audit/common";
import {
  checkName,
  claimName,
  inputText,
  type AuditEntry,
  type CheckResult,
  type ClaimCheck,
  type MemoryUse,
  type Relationship,
  type Retrieval,
} from "@/components/audit/labels";
import { formatScore } from "@/lib/format";
import { cn } from "@/lib/utils";

/** The five gate checks, each with a result word and icon (DESIGN "Audit entry"). */
export function ChecksList({ checks }: { checks: CheckResult[] }) {
  if (checks.length === 0) return null;
  return (
    <div>
      <h4 className="text-caption font-semibold text-muted-foreground">Checks</h4>
      <ul className="mt-1 flex flex-col gap-1">
        {checks.map((c, i) => {
          const name = checkName(c.check, i);
          const failed = c.passed === false;
          const na = c.passed === "n/a";
          const Icon = failed ? ShieldX : ShieldCheck;
          return (
            <li key={`${c.check}-${i}`} className="text-table">
              <span className="flex flex-wrap items-baseline gap-x-2">
                <span className="font-semibold">{`${i + 1}. ${name}`}</span>
                <span
                  className={cn(
                    "inline-flex items-center gap-1",
                    failed ? "text-destructive" : na ? "text-muted-foreground" : "text-accepted",
                  )}
                >
                  <Icon className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
                  {failed ? "Failed" : na ? "Not applicable" : "Passed"}
                </span>
              </span>
              {c.detail ? <span className="block text-caption text-muted-foreground">{c.detail}</span> : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** The inputs of the decision, as one collapsed list. They carry no secrets and no PubMed text (AD-22). */
export function InputsList({ inputs }: { inputs: AuditEntry["inputs"] }) {
  const keys = Object.keys(inputs ?? {});
  if (keys.length === 0) return null;
  return (
    <details className="text-table">
      <summary className="cursor-pointer text-caption font-semibold text-muted-foreground">
        Inputs ({keys.length})
      </summary>
      <dl className="mt-1 grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-[max-content_minmax(0,1fr)]">
        {keys.map((k) => (
          <div key={k} className="contents">
            <dt className="text-caption text-muted-foreground">{k}</dt>
            <dd className="min-w-0 break-words">
              <Mono>{inputText(inputs[k])}</Mono>
            </dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

/** The Evidence quote with its source, identifier link and the exact version it came from (Evidence Display Rules). */
export function EvidenceQuote({
  quote,
  source,
  versionId,
}: {
  quote: string;
  source: string | null;
  versionId: string | null;
}) {
  return (
    <figure className="flex flex-col gap-1">
      <blockquote className="evidence-quote">{quote}</blockquote>
      <figcaption className="flex flex-wrap items-center gap-x-3 gap-y-1 pl-[15px] text-caption text-muted-foreground">
        {source ? (
          <span>
            Source <SourceRef source={source} />
          </span>
        ) : null}
        {versionId ? (
          <span>
            Source version <Mono>{versionId}</Mono>
          </span>
        ) : null}
      </figcaption>
    </figure>
  );
}

// ---- Retrieval ---------------------------------------------------------------

/** "Atlas Vector Search", or the honest text-search fallback (EXPERIENCE "Related by text search"). */
export function RetrievalBlock({ retrieval }: { retrieval: Retrieval }) {
  const text = retrieval.method === "text_search";
  return (
    <div className="rounded-md border border-border p-3">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <h4 className="flex items-center gap-1.5 text-table font-semibold">
          {text ? (
            <TextSearch className="size-4 text-low-confidence" strokeWidth={1.75} aria-hidden="true" />
          ) : null}
          Retrieval
        </h4>
        {text ? (
          <CapabilityTag
            name="Atlas Search (text)"
            sentence="Related evidence is retrieved by text search in Atlas because Vector Search was unavailable."
          />
        ) : (
          <CapabilityTag
            name="Atlas Vector Search"
            sentence="Related evidence is retrieved by Vector Search over embeddings stored in Atlas. The score is similarity, not evidence."
          />
        )}
      </div>
      <p className={cn("mt-1 text-table", text && "text-low-confidence")}>
        {text ? "Related by text search (Vector Search unavailable)" : "Related by Atlas Vector Search"}
        {". "}
        <span className="text-muted-foreground">
          Top-k {retrieval.top_k}
          {retrieval.index ? (
            <>
              , index <Mono>{retrieval.index}</Mono>
            </>
          ) : null}
          .
        </span>
      </p>
      {retrieval.items.length === 0 ? (
        <p className="mt-1 text-table text-muted-foreground">No related items were retrieved.</p>
      ) : (
        <ol className="mt-2 flex flex-col gap-1">
          {retrieval.items.map((item) => (
            <li key={`${item.ref}-${item.version_id ?? ""}`} className="flex flex-wrap items-baseline gap-x-3 text-table">
              <SourceRef source={item.ref} />
              <ScoreText score={item.score} text={text} />
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

/** A score is a figure with its caveat, never a bar, a percentage or a colour scale. */
export function ScoreText({ score, text }: { score: number | null; text: boolean }) {
  if (score === null || score === undefined) return null;
  return (
    <span className="text-muted-foreground">
      <span className="text-identifier">{formatScore(score)}</span>{" "}
      <span className="text-caption">{text ? "(text score, not evidence)" : "(similarity, not evidence)"}</span>
    </span>
  );
}

// ---- Memories ----------------------------------------------------------------

/** Memories used, with author and before and after effect; "Retrieved, no change" when none (EXPERIENCE "Memory used chip"). */
export function MemoriesUsed({ memories }: { memories: MemoryUse[] }) {
  if (memories.length === 0) return null;
  return (
    <div className="rounded-md border border-border p-3">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <h4 className="text-table font-semibold">Memories used</h4>
        <CapabilityTag
          name="Memory in Atlas"
          sentence="Reviewer corrections are documents in Atlas, scoped to the Team, versioned, and retrieved by similarity to the discovery."
        />
      </div>
      <ul className="mt-2 flex flex-col gap-3">
        {memories.map((m) => (
          <li key={`${m.memory_id}-${m.version}`} className="flex flex-col gap-1.5">
            <p className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="inline-flex items-center gap-1 rounded-sm bg-ink-tint px-1.5 py-0.5">
                <Brain className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
                <Mono>{m.memory_id}</Mono>
                <span className="text-caption">v{m.version}</span>
              </span>
              <PersonName id={m.author} />
              {m.score !== null && m.score !== undefined ? <ScoreText score={m.score} text={false} /> : null}
            </p>
            {m.effect ? (
              <div className="text-table">
                <p className="font-semibold">
                  Wording changed because of <Mono>{m.memory_id}</Mono> ({m.author}): {m.effect.target}
                </p>
                <p className="mt-1">
                  <span className="text-caption font-semibold text-muted-foreground">Before </span>
                  <span className="text-muted-foreground line-through">{m.effect.before}</span>
                </p>
                <p>
                  <span className="text-caption font-semibold text-muted-foreground">After </span>
                  <span>{m.effect.after}</span>
                </p>
              </div>
            ) : (
              <p className="text-table text-muted-foreground">Retrieved, no change.</p>
            )}
            {m.source.report_id ? (
              <p className="text-caption text-muted-foreground">
                Created from report <AppLink href={`/reports/${encodeURIComponent(m.source.report_id)}`}>{m.source.report_id}</AppLink>
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---- Relationships -----------------------------------------------------------

const RELATIONSHIPS: Record<Relationship["label"], { word: string; icon: LucideIcon }> = {
  supports: { word: "Supports", icon: Equal },
  contradicts: { word: "Contradicts", icon: EqualNot },
  extends: { word: "Extends", icon: GitBranchPlus },
  new_question: { word: "New question", icon: MessageCircleQuestionMark },
  related_unestablished: { word: "Related (no relationship established)", icon: Minus },
};

const RELATIONSHIP_ORDER: Relationship["label"][] = [
  "supports",
  "contradicts",
  "extends",
  "new_question",
  "related_unestablished",
];

/** Relationship labels with both quotes side by side. A label never rests on similarity alone (AD-26). */
export function RelationshipsList({ relationships }: { relationships: Relationship[] }) {
  if (relationships.length === 0) return null;
  const ordered = [...relationships].sort(
    (a, b) =>
      RELATIONSHIP_ORDER.indexOf(a.label) - RELATIONSHIP_ORDER.indexOf(b.label) ||
      (b.similarity ?? 0) - (a.similarity ?? 0),
  );
  return (
    <div className="rounded-md border border-border p-3">
      <h4 className="text-table font-semibold">Relationship labels</h4>
      <ul className="mt-2 flex flex-col gap-4">
        {ordered.map((r) => {
          const { word, icon: Icon } = RELATIONSHIPS[r.label];
          const established = r.label !== "related_unestablished";
          const text = r.retrieval_method === "text_search";
          return (
            <li key={r.id} className="flex flex-col gap-2">
              <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="inline-flex items-center gap-1.5 font-semibold">
                  <Icon className="size-4" strokeWidth={1.75} aria-hidden="true" />
                  {word}
                </span>
                <SourceRef source={r.related_ref} />
                {r.related_title ? <span className="text-table">{r.related_title}</span> : null}
                <StatusPill status={r.status === "accepted" ? "accepted" : r.status === "reverted" ? "reverted" : "pending"} />
              </p>
              {r.rationale ? <p className="text-table">{r.rationale}</p> : null}
              {established && r.new_quote && r.related_quote ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  <EvidenceQuote quote={r.new_quote.text} source={r.new_quote.source_ref} versionId={r.new_quote.version_id} />
                  <EvidenceQuote
                    quote={r.related_quote.text}
                    source={r.related_quote.source_ref}
                    versionId={r.related_quote.version_id}
                  />
                </div>
              ) : (
                <p className="text-table text-muted-foreground">Fewer than two checked quotes.</p>
              )}
              {r.similarity !== null && r.similarity !== undefined ? (
                <p className="text-table">
                  <ScoreText score={r.similarity} text={text} />
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ---- Claim blocked -----------------------------------------------------------

/**
 * The claim-blocked treatment: the draft sentence struck through and labelled
 * "Draft", the failed claim check by name with its code, and what did not
 * happen (DESIGN "Claim blocked").
 */
export function ClaimBlocked({
  claims,
  redraftHref,
}: {
  claims: ClaimCheck[];
  redraftHref: string | null;
}) {
  const failed = claims.filter((c) => !c.passed);
  if (failed.length === 0) return null;
  return (
    <div className="flex flex-col gap-2 border-l-[3px] border-destructive pl-3">
      {failed.map((c, i) => (
        <div key={`${c.claim_kind}-${i}`} className="flex flex-col gap-1">
          <p className="text-table">
            <span className="text-caption font-semibold text-muted-foreground">Draft </span>
            <span className="text-muted-foreground line-through">{c.text}</span>
          </p>
          <p className="text-table">
            <span className="font-semibold">{claimName(c.claim_kind)}</span> <Mono className="text-muted-foreground">{c.claim_kind}</Mono>{" "}
            failed under Evidence checks passed.
          </p>
          {c.detail ? <p className="text-caption text-muted-foreground">{c.detail}</p> : null}
        </div>
      ))}
      <p className="text-body">Nothing filed. No external call made.</p>
      {redraftHref ? (
        <p className="text-table">
          The redraft follows as its own entry: <a className="underline underline-offset-2" href={redraftHref}>go to the redraft</a>.
        </p>
      ) : null}
    </div>
  );
}

/** Used where a task or other entry has no body of its own to show. */
export function EmptyNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex items-center gap-1.5 text-table text-muted-foreground">
      <CircleDashed className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
      {children}
    </p>
  );
}

/** Memory status icon for a changed memory. */
export function MemoryStatusIcon({ status }: { status: "active" | "corrected" | "revoked" }) {
  const Icon = status === "active" ? Brain : status === "corrected" ? History : Ban;
  return <Icon className="size-3.5" strokeWidth={1.75} aria-hidden="true" />;
}
