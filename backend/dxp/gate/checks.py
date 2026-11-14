"""The five gate checks, in order (AD-19, Story 9.3).

Every check here is a pure function over documents that ``gate.evaluate``
has already loaded (the latest grant version, the policies of the policy set,
the run, the admission, the report, the scope). Nothing in this module reads
or writes Atlas, so the order and each check's outcome are testable on their
own. ``run_checks`` stops at the first failure and records the checks it did
not reach as not run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from dxp.gate import claims as claim_checks

CHECK_ORDER = (
    "grant_active",
    "team_scope",
    "destination_action",
    "evidence_checks",
    "run_authorised",
)

SLACK_DESTINATION = "slack:#all-mango-db-hackathon"
LEDGER = "ledger"

# Action kinds (AD-14).
MACHINE_KINDS = frozenset(
    {"search_source", "file_proposal", "file_related_evidence", "notify_slack", "apply_value"}
)
MEDIA_KINDS = frozenset({"generate_briefing", "generate_avatar_video"})
HUMAN_KINDS = frozenset(
    {
        "decide_report",
        "authorise_task",
        "create_memory",
        "correct_memory",
        "revoke_memory",
        "review_value",
        "resolve_notification",
        "revert_report",  # V48, AD-31
    }
)
SUPERSEDED_KINDS = frozenset({"decide_proposal"})
KNOWN_KINDS = MACHINE_KINDS | MEDIA_KINDS | HUMAN_KINDS
MEMORY_KINDS = frozenset({"create_memory", "correct_memory", "revoke_memory"})

# The one destination each kind may use (AD-19 check 3, S2).
EXPECTED_DESTINATION = {
    "search_source": "source:clinicaltrials.gov",
    "notify_slack": SLACK_DESTINATION,
    "generate_briefing": "tts:elevenlabs",
    "generate_avatar_video": "video:heygen",
}
KNOWN_DESTINATIONS = frozenset(
    {LEDGER, SLACK_DESTINATION, "source:clinicaltrials.gov", "tts:elevenlabs", "video:heygen"}
)

# Check 4 applies to these kinds (D50, extended 14 Nov); every other kind records n/a.
EVIDENCE_KINDS = frozenset(
    {"file_proposal", "file_related_evidence", "notify_slack", "generate_briefing", "generate_avatar_video"}
)
# Of those, these derive from a filed report and pass only when it was filed allowed.
REPORT_DERIVED_KINDS = frozenset({"notify_slack", "generate_briefing", "generate_avatar_video"})

PASSED = True
NA = "n/a"
NOT_RUN = "not_run"


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


@dataclass
class GateCtx:
    """Who is acting, under what authority (AD-17).

    ``kind`` is ``run`` for an agent write inside a run, ``reviewer`` for a
    Reviewer decision and ``seed`` for the command-line seed. ``grant_id`` is
    the run's grant (``lbdx`` or a task grant) or, outside a run, the caller's
    grant. ``policy_set_version`` is pinned at run start; outside a run it is
    left ``None`` and the current set is used.
    """

    kind: str
    principal: str
    grant_id: str
    run_id: str | None = None
    agent: str | None = None
    initiated_by: str | None = None
    run_grant_version: int | None = None
    policy_set_version: str | None = None
    admission_id: str | None = None
    request_id: str | None = None
    cause: dict[str, Any] | None = None
    stamp: dict[str, Any] = field(default_factory=dict)
    mode: str = "live"
    report_id: str | None = None
    origin: str | None = None
    session: Any = None

    @classmethod
    def coerce(cls, ctx: Any) -> "GateCtx":
        if isinstance(ctx, cls):
            return ctx
        names = cls.__dataclass_fields__.keys()
        values = {n: _get(ctx, n) for n in names if _get(ctx, n) is not None}
        stamp = values.get("stamp") or {}
        # A run stamp names the run, the agent and who started it (AD-17).
        for key in ("run_id", "agent", "initiated_by", "grant_id", "policy_set_version"):
            if key not in values and stamp.get(key) is not None:
                values[key] = stamp[key]
        if "run_grant_version" not in values and stamp.get("grant_version") is not None and stamp.get("kind") == "run":
            values["run_grant_version"] = stamp["grant_version"]
        if "kind" not in values:
            values["kind"] = stamp.get("kind") or ("run" if values.get("run_id") else "reviewer")
        if "principal" not in values:
            values["principal"] = stamp.get("principal") or values.get("agent") or values.get("initiated_by")
        return cls(**values)

    def validate(self) -> None:
        if self.kind not in ("run", "reviewer", "seed"):
            raise ValueError(f"unknown context kind {self.kind!r}")
        if self.kind == "run" and not self.run_id:
            raise ValueError("an agent write requires a run_id (AD-17)")
        if self.kind != "run" and self.run_id:
            raise ValueError("Reviewer and seed writes carry run_id null (AD-17)")
        if self.kind == "reviewer" and not self.request_id:
            raise ValueError("a Reviewer decision needs a server-generated request_id (D20)")
        if not self.grant_id:
            raise ValueError("the context names no grant")


@dataclass
class GateAction:
    """One proposed action, judged once (D46).

    ``target`` follows ``Decision.target``: ``diagnostic_id`` (``None`` for a
    scope-collection update, V43), ``diagnostic_ids`` for a report, and the
    ``proposal_id``, ``value_id``, ``report_id``, ``memory_id``, ``task_id``,
    ``scope_id``, ``action_id``, ``source_ref`` the action is about.
    ``id_target`` is the AD-3 target string; when omitted it is derived by
    ``decisions.target_key``.
    """

    kind: str
    destination: str
    target: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    evidence_ref: dict[str, Any] | None = None
    # AD-6 checks this action rests on: one per change, or one per quote for a report.
    checks: list[dict[str, Any]] = field(default_factory=list)
    # Claim checks (report-level file_proposal).
    claims: list[dict[str, Any]] = field(default_factory=list)
    source_fields: dict[str, Any] | None = None
    checked_quotes: list[dict[str, Any]] = field(default_factory=list)
    # A name found in the record, proposed as a link to a Diagnostic (V37).
    mention: dict[str, Any] | None = None
    creates_diagnostic: bool = False
    # search_source: the query's terms and condition, and the requested count.
    query: dict[str, Any] | None = None
    requested_count: int | None = None
    # file_related_evidence: items already filed by the task, and the item's scopes.
    filed_count: int | None = None
    item_scope_ids: list[str] | None = None
    # notify_slack, generate_briefing, generate_avatar_video: the text's script hash.
    script_hash: str | None = None
    # memory kinds: the memory's Team.
    team_id: str | None = None
    # Report-level file_proposal only (V14).
    retrieval: dict[str, Any] | None = None
    memories_used: list[dict[str, Any]] = field(default_factory=list)
    id_target: str | None = None
    # An explicit decision ID (authorise_task: derive("dec_", approval.decision_id, "authorise_task")).
    decision_id: str | None = None

    @classmethod
    def coerce(cls, action: Any) -> "GateAction":
        if isinstance(action, cls):
            return action
        names = cls.__dataclass_fields__.keys()
        return cls(**{n: _get(action, n) for n in names if _get(action, n) is not None})

    @property
    def is_report_level(self) -> bool:
        """The report-level file_proposal (target ``<report_id>|draft<n>``), V24."""
        return self.kind == "file_proposal" and bool(self.target.get("report_id")) and bool(self.target.get("draft"))


@dataclass
class Loaded:
    """Everything the checks read, loaded once by ``gate.evaluate``."""

    grant: dict[str, Any] | None
    policies: list[dict[str, Any]]
    run: dict[str, Any] | None = None
    admission: dict[str, Any] | None = None
    scope: dict[str, Any] | None = None
    report: dict[str, Any] | None = None
    report_file_decision: dict[str, Any] | None = None
    now: datetime | None = None


def _result(check: str, passed: Any, detail: str) -> dict[str, Any]:
    return {"check": check, "passed": passed, "detail": detail}


def _aware(dt: Any) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# --- check 1 -----------------------------------------------------------------


def check_grant_active(ctx: GateCtx, action: GateAction, loaded: Loaded) -> dict[str, Any]:
    grant = loaded.grant
    if grant is None:
        return _result("grant_active", False, f"no grant {ctx.grant_id!r} exists")
    version = grant.get("version")
    label = f"{grant.get('grant_id', ctx.grant_id)}@v{version}"
    status = grant.get("status")
    pinned = ctx.run_grant_version
    pinned_note = f" (run pinned v{pinned})" if pinned is not None and pinned != version else ""
    if status != "active":
        return _result("grant_active", False, f"latest version {label} is {status}{pinned_note}")
    expires = _aware(grant.get("expires_at"))
    now = loaded.now or datetime.now(timezone.utc)
    if expires is not None and expires <= now:
        return _result("grant_active", False, f"{label} expired at {expires.isoformat()}")
    principal = grant.get("principal")
    if ctx.kind != "run" and principal and ctx.principal and principal != ctx.principal:
        return _result(
            "grant_active", False, f"{label} authorises {principal!r}, not the caller {ctx.principal!r}"
        )
    return _result("grant_active", PASSED, f"{label} is active{pinned_note}")


# --- check 2 -----------------------------------------------------------------


def _scope_rule(grant: Mapping[str, Any]) -> str:
    scope = grant.get("scope") or {}
    return (
        f"grant {grant.get('grant_id')}@v{grant.get('version')} scope: "
        f"scope_id {scope.get('scope_id')!r}, diagnostic_ids {sorted(scope.get('diagnostic_ids') or [])}"
    )


def _target_diagnostics(action: GateAction) -> list[str]:
    ids: list[str] = []
    dx = action.target.get("diagnostic_id")
    if dx:
        ids.append(dx)
    for d in action.target.get("diagnostic_ids") or []:
        if d and d not in ids:
            ids.append(d)
    return ids


def check_team_scope(ctx: GateCtx, action: GateAction, loaded: Loaded) -> dict[str, Any]:
    grant = loaded.grant or {}
    scope = grant.get("scope") or {}
    if scope.get("all") is True:
        if grant.get("principal") == "seed" and grant.get("kind") == "seed":
            return _result("team_scope", PASSED, "seed grant, scope { all: true } (D16)")
        return _result("team_scope", False, "scope { all: true } is valid only on the seed grant (D16)")

    allowed_dx = set(scope.get("diagnostic_ids") or [])
    grant_scope_id = scope.get("scope_id")
    limits = grant.get("limits") or {}
    max_results = limits.get("max_results")

    if action.kind == "search_source":
        query = action.query or {}
        scope_doc = loaded.scope or {}
        if query.get("scope_id", grant_scope_id) != grant_scope_id:
            return _result(
                "team_scope", False, f"query scope {query.get('scope_id')!r} is not the grant's scope {grant_scope_id!r}"
            )
        if scope_doc:
            allowed_terms = {t.lower() for t in (scope_doc.get("assays") or [])}
            allowed_terms |= {t.lower() for t in (scope_doc.get("aliases") or [])}
            extra = [t for t in (query.get("terms") or []) if t.lower() not in allowed_terms]
            if query.get("terms") is not None and extra:
                return _result("team_scope", False, f"query terms outside scope {grant_scope_id!r}: {extra}")
            cond = query.get("condition")
            if cond is not None and cond.lower() != (scope_doc.get("condition") or "").lower():
                return _result(
                    "team_scope",
                    False,
                    f"query condition {cond!r} is not the scope's condition {scope_doc.get('condition')!r}",
                )
        if max_results is not None and action.requested_count is not None and action.requested_count > max_results:
            return _result(
                "team_scope", False, f"requested {action.requested_count} results, over the limit {max_results}"
            )
        return _result("team_scope", PASSED, f"query within scope {grant_scope_id!r}")

    if action.kind == "file_related_evidence":
        item_scopes = action.item_scope_ids
        if item_scopes is not None and grant_scope_id not in item_scopes:
            return _result(
                "team_scope", False, f"item is not in scope {grant_scope_id!r} (item scopes {item_scopes})"
            )
        if max_results is not None and action.filed_count is not None and action.filed_count + 1 > max_results:
            return _result(
                "team_scope",
                False,
                f"filing item {action.filed_count + 1} would exceed the task limit of {max_results}",
            )

    if action.kind in MEMORY_KINDS:
        team = action.team_id or action.target.get("team_id")
        if team != grant.get("team_id"):
            return _result("team_scope", False, f"memory Team {team!r} is not the grant's Team {grant.get('team_id')!r}")
        return _result("team_scope", PASSED, f"memory Team {team!r} is the grant's Team")

    target_scope = action.target.get("scope_id")
    if target_scope is not None and target_scope != grant_scope_id:
        return _result(
            "team_scope", False, f"target scope {target_scope!r} is not the grant's scope {grant_scope_id!r}"
        )

    outside = [d for d in _target_diagnostics(action) if d not in allowed_dx]
    if outside:
        dx = outside[0]
        if action.mention:
            name = action.mention.get("name")
            detail = (
                f"the record's mention {name!r} resolves to Diagnostic {dx}, which is outside the scope; "
                f"{_scope_rule(grant)}"
            )
        elif action.creates_diagnostic:
            detail = f"creating Diagnostic {dx} outside the scope is blocked (D28); {_scope_rule(grant)}"
        else:
            detail = f"Diagnostic {dx} is outside the scope; {_scope_rule(grant)}"
        return _result("team_scope", False, detail)

    if _target_diagnostics(action):
        return _result("team_scope", PASSED, f"Diagnostics {_target_diagnostics(action)} are in the scope")
    if target_scope is not None:
        return _result("team_scope", PASSED, f"targets the scope's evidence collection {target_scope!r} (V35, V43)")
    return _result("team_scope", PASSED, "no Diagnostic or scope outside the grant")


# --- check 3 -----------------------------------------------------------------


def check_destination_action(ctx: GateCtx, action: GateAction, loaded: Loaded) -> dict[str, Any]:
    grant = loaded.grant or {}
    kind, dest = action.kind, action.destination
    if kind in SUPERSEDED_KINDS:
        return _result("destination_action", False, f"{kind} is superseded (V8) and granted to no one")
    if kind not in KNOWN_KINDS:
        return _result("destination_action", False, f"unknown action kind {kind!r}")
    if dest not in KNOWN_DESTINATIONS:
        return _result("destination_action", False, f"unknown destination {dest!r}")
    expected = EXPECTED_DESTINATION.get(kind, LEDGER)
    if dest != expected:
        return _result("destination_action", False, f"{kind} must go to {expected!r}, not {dest!r}")
    if dest not in (grant.get("destinations") or []):
        return _result("destination_action", False, f"destination {dest!r} is not on the grant")
    if kind not in (grant.get("actions") or []):
        return _result("destination_action", False, f"action {kind!r} is not on the grant")
    return _result("destination_action", PASSED, f"{kind} to {dest} is on the grant")


# --- check 4 -----------------------------------------------------------------


def _policies_for(kind: str, policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [p for p in policies if kind in (p.get("applies_to") or [])]


def _claim_policies(policies: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for p in policies:
        pid = p.get("policy_id")
        if pid in claim_checks.CLAIM_POLICIES:
            names.append(pid)
        for c in (p.get("requires") or {}).get("claim_checks") or []:
            if c in claim_checks.CLAIM_POLICIES:
                names.append(c)
    return [c for c in claim_checks.CLAIM_POLICIES if c in names]


def _requires_failures(policies: list[dict[str, Any]], checks: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for p in policies:
        req = p.get("requires") or {}
        pid = f"{p.get('policy_id')}@v{p.get('version')}"
        for i, chk in enumerate(checks):
            where = f"check {i + 1}" if len(checks) > 1 else "the change's check"
            if req.get("quote_found") and chk.get("quote_found") is not True:
                failures.append(f"{pid}: quote not found ({where})")
            if req.get("supported") and chk.get("supported") is not True:
                failures.append(f"{pid}: not supported ({where})")
            min_conf = req.get("min_confidence")
            if min_conf is not None:
                conf = chk.get("confidence")
                if conf is None or conf < min_conf:
                    failures.append(f"{pid}: confidence {conf} below {min_conf} ({where})")
    return failures


def check_evidence(ctx: GateCtx, action: GateAction, loaded: Loaded) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Check 4. Returns the check result and the ``Decision.claims`` entries."""
    if action.kind not in EVIDENCE_KINDS:
        return _result("evidence_checks", NA, f"check 4 does not apply to {action.kind} (D50)"), []

    applying = _policies_for(action.kind, loaded.policies)
    claim_results: list[dict[str, Any]] = []

    if action.kind in REPORT_DERIVED_KINDS:
        report = loaded.report
        decision = loaded.report_file_decision
        if report is None:
            return _result("evidence_checks", False, f"report {action.target.get('report_id')!r} was not filed"), []
        if decision is None or decision.get("outcome") != "allowed":
            return _result("evidence_checks", False, "the report was not filed allowed"), []
        if action.script_hash is not None and action.script_hash != report.get("script_hash"):
            return _result(
                "evidence_checks", False, "the text is not the report's own script (script_hash differs, AD-30)"
            ), []

    failures = _requires_failures(applying, action.checks)

    if action.is_report_level:
        active_claims = _claim_policies(applying)
        if active_claims:
            claim_results = claim_checks.evaluate_claims(
                action.claims, action.source_fields, action.checked_quotes, active_claims
            )
            failed = claim_checks.failed_claim_policies(claim_results)
            if failed:
                blocked = [r for r in claim_results if not r["passed"]]
                texts = "; ".join(f"{r['text']!r} ({', '.join(r['failed_policies'])})" for r in blocked)
                failures.append(f"failed claim policy {', '.join(failed)}: {texts}")

    if failures:
        return _result("evidence_checks", False, "; ".join(failures)), claim_results
    names = sorted(f"{p.get('policy_id')}@v{p.get('version')}" for p in applying)
    detail = f"met: {', '.join(names)}" if names else f"no policy in the set applies to {action.kind}"
    return _result("evidence_checks", PASSED, detail), claim_results


# --- check 5 -----------------------------------------------------------------


def check_run_authorised(ctx: GateCtx, action: GateAction, loaded: Loaded) -> dict[str, Any]:
    if ctx.kind != "run":
        return _result("run_authorised", NA, f"{ctx.kind} write outside a run")
    run = loaded.run
    if run is None:
        return _result("run_authorised", False, f"run {ctx.run_id!r} not found")
    if run.get("status") == "stopped":
        return _result("run_authorised", False, f"run {ctx.run_id} is stopped")
    adm = loaded.admission
    if adm is None:
        return _result("run_authorised", False, "the action holds no admission for this run")
    if adm.get("run_id") != ctx.run_id:
        return _result("run_authorised", False, f"admission {adm.get('_id')} belongs to another run")
    if adm.get("status") != "admitted":
        return _result("run_authorised", False, f"admission {adm.get('_id')} is {adm.get('status')}")
    return _result("run_authorised", PASSED, f"admission {adm.get('_id')} admitted; run is {run.get('status')}")


def run_checks(ctx: GateCtx, action: GateAction, loaded: Loaded) -> tuple[list[dict[str, Any]], str | None, list[dict[str, Any]]]:
    """Run the five checks in order, stopping at the first failure.

    Returns ``(checks, failed_check, claims)``. Checks after a failure are
    recorded ``not_run`` so the Decision always lists all five.
    """
    results: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    failed: str | None = None
    steps = (
        check_grant_active,
        check_team_scope,
        check_destination_action,
        check_evidence,
        check_run_authorised,
    )
    for name, step in zip(CHECK_ORDER, steps):
        if failed is not None:
            results.append(_result(name, NOT_RUN, f"not run: {failed} failed"))
            continue
        out = step(ctx, action, loaded)
        if isinstance(out, tuple):
            out, claims = out
        results.append(out)
        if out["passed"] is False:
            failed = name
    return results, failed, claims
