"use client";

import { useSyncExternalStore } from "react";
import { ShieldQuestion, X } from "lucide-react";

import { AppLink, Mono, PersonName } from "@/components/audit/common";
import { ChecksList } from "@/components/audit/entry-parts";
import {
  entryState,
  kindName,
  policySetText,
  type Audit,
  type AuditEntry,
} from "@/components/audit/labels";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime, formatGrant } from "@/lib/format";
import { useApi } from "@/lib/use-api";

/**
 * "Who authorised this?" (Story 9.8, D40). Selecting an entry loads
 * `GET /decisions/<decision_id>` and answers from the Decision's
 * `authorised_by` in plain sentences, identifiers in mono: the agent,
 * who started the run, the grant and its version and scope, the policy set,
 * and every check. It reads the grant and policy set as they were at the
 * decision's evaluated version, so a later change never alters the answer.
 *
 * At 1024px and wider it is the 360px right-hand panel; below that it opens as
 * a side sheet, so the page never needs a horizontal scroll.
 */

const WIDE = "(min-width: 1024px)";

function subscribeWide(onChange: () => void) {
  const query = window.matchMedia(WIDE);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

function useIsWide(): boolean {
  return useSyncExternalStore(
    subscribeWide,
    () => window.matchMedia(WIDE).matches,
    () => true,
  );
}

export function WhoAuthorisedDock({
  selected,
  audit,
  onClose,
}: {
  selected: AuditEntry | null;
  audit: Audit;
  onClose: () => void;
}) {
  const wide = useIsWide();

  if (wide) {
    return (
      <aside
        aria-label="Who authorised this?"
        className="sticky top-24 hidden max-h-[calc(100dvh-7rem)] overflow-y-auto rounded-lg border border-border bg-card p-5 shadow-sm lg:block"
      >
        <h2 className="mb-3 flex items-center gap-2 text-heading">
          <ShieldQuestion className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
          Who authorised this?
        </h2>
        {selected ? (
          <>
            <WhoBody entry={selected} audit={audit} />
            <Button type="button" variant="ghost" size="sm" className="mt-4" onClick={onClose}>
              <X aria-hidden="true" />
              Close this answer
            </Button>
          </>
        ) : (
          <p className="text-table text-muted-foreground">
            Choose &ldquo;Who authorised this?&rdquo; on any entry. The answer opens here, and you stay on this page.
          </p>
        )}
      </aside>
    );
  }

  return (
    <Sheet open={selected !== null} onOpenChange={(open) => (open ? undefined : onClose())}>
      <SheetContent
        side="right"
        className="w-full max-w-md overflow-y-auto p-5 sm:max-w-md"
        // Focus goes back to the opening button in the view's onClose, not to the page.
        onCloseAutoFocus={(e) => e.preventDefault()}
      >
        <SheetHeader className="p-0">
          <SheetTitle className="flex items-center gap-2 text-heading">
            <ShieldQuestion className="size-[18px] shrink-0" strokeWidth={1.75} aria-hidden="true" />
            Who authorised this?
          </SheetTitle>
          <SheetDescription className="sr-only">
            The agent, who started the run, the grant, the policy set and every check for the chosen entry.
          </SheetDescription>
        </SheetHeader>
        {selected ? <WhoBody entry={selected} audit={audit} /> : null}
      </SheetContent>
    </Sheet>
  );
}

function WhoBody({ entry, audit }: { entry: AuditEntry; audit: Audit }) {
  const decision = useApi("/decisions/{decision_id}", { path: { decision_id: entry.decision_id } });
  const d = decision.data;
  const by = d?.authorised_by ?? entry.authorised_by ?? null;
  const stamp = d?.stamp ?? entry.stamp ?? null;
  const grantId = by?.grant_id ?? d?.grant_id ?? entry.grant_id;
  const grantVersion = by?.grant_version ?? d?.grant_version ?? entry.grant_version;
  const grant = useApi("/grants/{grant_id}", { path: { grant_id: grantId }, query: { version: grantVersion } });

  const checks = d?.checks?.length ? d.checks : entry.checks;
  const policySetVersion = by?.policy_set_version ?? d?.policy_set_version ?? entry.policy_set_version;
  const setText = policySetText(policySetVersion, audit.run, audit.policies);
  const reviewer = stamp?.kind === "reviewer";
  const state = entryState(entry);
  const target = d?.target ?? null;
  const g = grant.data;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-table text-muted-foreground">
        {kindName(entry)}: {state.word}
      </p>

      {decision.isLoading && !d ? (
        <Skeleton className="h-16 w-full" role="status" aria-label="Loading the decision" />
      ) : null}
      {decision.error && !d ? (
        <p className="text-table text-muted-foreground" role="status">
          The full decision could not be read ({decision.error.message}). This answer uses what the audit already holds.
        </p>
      ) : null}

      <div className="flex flex-col gap-2 text-body">
        {stamp?.kind === "seed" ? (
          <p>Written by the seed loader, not by an agent or a Reviewer.</p>
        ) : reviewer ? (
          <p>
            {by?.principal ?? stamp?.principal ? <PersonName id={(by?.principal ?? stamp?.principal) as string} /> : "A Reviewer"}{" "}
            decided this as a Reviewer. No agent acted.
          </p>
        ) : (
          <p>
            The agent <Mono>{stamp?.agent ?? audit.run.agent}</Mono> did this
            {stamp?.model ? (
              <>
                {" "}
                (model <Mono>{stamp.model}</Mono>)
              </>
            ) : null}
            .
          </p>
        )}
        {by?.initiated_by ?? stamp?.initiated_by ? (
          <p>
            {reviewer ? "Acting for" : "The run was started by"}{" "}
            <PersonName id={(by?.initiated_by ?? stamp?.initiated_by) as string} />
            {by?.acting_for ? (
              <>
                , acting for <Mono>{by.acting_for}</Mono>
              </>
            ) : null}
            .
          </p>
        ) : null}
        <p>
          Under grant <Mono>{formatGrant(grantId, grantVersion)}</Mono>
          {g?.team_name || g?.scope_name ? (
            <>
              {" "}
              ({g.team_name ? `Team ${g.team_name}` : ""}
              {g.team_name && g.scope_name ? ", " : ""}
              {g.scope_name ?? ""})
            </>
          ) : null}
          {by?.granted_by ?? g?.granted_by ? (
            <>
              , granted by <Mono>{(by?.granted_by ?? g?.granted_by) as string}</Mono>
            </>
          ) : null}
          {by?.expires_at ?? g?.expires_at ? <>, expires {formatDateTime(by?.expires_at ?? g?.expires_at)}</> : null}.
        </p>
        {g && "scope_id" in g.scope ? (
          <p>
            Scope <Mono>{g.scope.scope_id}</Mono>
            {g.scope.diagnostic_ids.length > 0 ? `, ${g.scope.diagnostic_ids.length} Diagnostics` : ""}.
          </p>
        ) : null}
        {setText ? (
          <p>
            Policy set <Mono>{setText}</Mono>
            {policySetVersion === audit.run.policy_set_version && audit.policies.length > 0 ? (
              <>
                : <Mono>{audit.policies.map((p) => p.id).join(", ")}</Mono>
              </>
            ) : null}
            .
          </p>
        ) : null}
        {target?.diagnostic_id ? (
          <p>
            Target: Diagnostic{" "}
            <AppLink href={`/diagnostics/${encodeURIComponent(target.diagnostic_id)}`}>{target.diagnostic_id}</AppLink> (Accepted
            knowledge view).
          </p>
        ) : target?.scope_id ? (
          <p>
            Target: the scope&apos;s evidence collection, scope <Mono>{target.scope_id}</Mono>. No Diagnostic.
          </p>
        ) : null}
        {d?.request_id ? (
          <p className="text-caption text-muted-foreground">
            Request <Mono>{d.request_id}</Mono>
          </p>
        ) : null}
      </div>

      <ChecksList checks={checks} />
    </div>
  );
}
