import Link from "next/link";
import { Brain } from "lucide-react";

import { CapabilityTag } from "@/components/report/capability-tag";
import { Section } from "@/components/report/section";
import type { MemoryUse } from "@/components/report/types";
import { SyntheticBadge } from "@/components/shell/badges";
import { displayName, formatScore, shortId } from "@/lib/format";

/**
 * Memories used (EXPERIENCE "Memory used chip"): each memory the agent retrieved
 * for this report, with its author, its source and, where it changed the
 * wording, the labelled Before and After. A memory that changed nothing visible
 * reads "Retrieved, no change". A memory informs wording; this panel never
 * presents one as a rule or a permission. The memories panel in the right-hand
 * column is where one is corrected or revoked.
 */
export function MemoriesUsed({ memories }: { memories: MemoryUse[] }) {
  return (
    <Section
      id="memories-used"
      icon={Brain}
      title="Memories used"
      aside={
        <CapabilityTag
          label="Memory in Atlas"
          hint="Reviewer corrections are documents in Atlas, scoped to the Team, versioned, and retrieved by similarity to the discovery."
        />
      }
    >
      {memories.length === 0 ? (
        <p className="text-body m-0 text-muted-foreground">No memories were retrieved for this report.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-4 p-0">
          {memories.map((m) => {
            const author = displayName(m.author);
            const score = formatScore(m.score);
            return (
              <li key={`${m.memory_id}@${m.version}`} className="flex min-w-0 flex-col gap-3 rounded-md border border-border p-4">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                  <span className="inline-flex flex-wrap items-center gap-2 rounded-sm bg-ink-tint px-2 py-1 text-caption">
                    <Brain className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
                    <Link
                      href={`#memory-${encodeURIComponent(m.memory_id)}`}
                      className="text-identifier underline underline-offset-2"
                      aria-label={`Memory ${m.memory_id}, version ${m.version}: show it in the memories panel`}
                    >
                      {shortId(m.memory_id)}
                    </Link>
                    <span className="text-identifier">v{m.version}</span>
                    <span>{author}</span>
                    <SyntheticBadge />
                  </span>
                  {m.source.report_id ? (
                    <span className="text-caption text-muted-foreground">
                      Created in{" "}
                      <Link
                        href={`/reports/${encodeURIComponent(m.source.report_id)}`}
                        className="text-identifier underline underline-offset-2"
                      >
                        {shortId(m.source.report_id)}
                      </Link>
                    </span>
                  ) : null}
                  {score ? (
                    <span className="text-caption text-muted-foreground">
                      Match <span className="text-identifier">{score}</span> (similarity, not evidence)
                    </span>
                  ) : null}
                </div>

                {m.effect ? (
                  <div className="flex flex-col gap-2">
                    <p className="text-body m-0 font-semibold">
                      Wording changed because of {shortId(m.memory_id)} ({author})
                    </p>
                    <p className="text-caption m-0 text-muted-foreground">{m.effect.target}</p>
                    <dl className="m-0 grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-2">
                      <dt className="text-caption font-semibold">Before</dt>
                      <dd className="text-body m-0 break-words text-muted-foreground line-through decoration-1">
                        {m.effect.before}
                      </dd>
                      <dt className="text-caption font-semibold">After</dt>
                      <dd className="text-body m-0 break-words">{m.effect.after}</dd>
                    </dl>
                  </div>
                ) : (
                  <p className="text-body m-0 text-muted-foreground">Retrieved, no change</p>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </Section>
  );
}
