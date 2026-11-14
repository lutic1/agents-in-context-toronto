"""Response and request shapes of the DxP API (AD-14), written once.

This module is the contract. Every class matches a shape in the AD-14 table of
the architecture spine, plus the Epic 10 shapes and the V38 to V47 additions
(the decision ID is cited beside each). `web/lib/types.ts` is generated from
`/openapi.json` by `tools/gen_types.sh` and is never edited by hand.

Rules kept here:
- JSON keys are snake_case end to end; IDs are strings; dates are ISO 8601.
- A field AD-14 shows as `x | null` is optional with a `None` default.
- `SourceVersion.raw_text` is never returned by the API (V40), so it has no field.
- After 11:45 a change to this file goes through the contract keeper.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Shape(BaseModel):
    """Base for every API shape: output schemas list every key as present."""

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


# ---------------------------------------------------------------------------
# Enumerations (AD-14, AD-18, AD-10)
# ---------------------------------------------------------------------------

ActionKind = Literal[
    # machine kinds (agent and task grants)
    "search_source",
    "file_proposal",
    "file_related_evidence",
    "notify_slack",
    # seed
    "apply_value",
    # on-demand external kinds, Reviewer only under sam@v1 (V29)
    "generate_briefing",
    "generate_avatar_video",
    # human kinds
    "decide_report",
    "authorise_task",
    "create_memory",
    "correct_memory",
    "revoke_memory",
    "review_value",
    "resolve_notification",
    "revert_report",  # V48, AD-31
    # superseded by decide_report (V8); granted to no one
    "decide_proposal",
]

Destination = Literal[
    "ledger",
    "slack:#all-mango-db-hackathon",
    "source:clinicaltrials.gov",
    "tts:elevenlabs",
    "video:heygen",
]

PrincipalKind = Literal["agent", "person", "seed"]
ClaimKind = Literal["claim_performed_or_results", "claim_planned", "claim_preclinical"]
# AD-14 lists agent | person | seed; the plan (A03, A24) also names a task
# grant kind, so `task` is accepted here until the contract keeper settles it.
GrantKind = Literal["agent", "person", "seed", "task"]
Mode = Literal["baseline", "live"]
RunStatus = Literal["running", "stopping", "stopped", "done", "failed"]
RunKind = Literal["discover", "items", "task"]
Outcome = Literal["allowed", "blocked"]
ActionStatus = Literal[
    "queued",
    "dispatching",
    "delivered",
    "failed",
    "unknown",
    "done",
    # returned in place of dispatching while the background sweep settles it; never stored (D24)
    "reconciling",
]
ProposalStatus = Literal["pending", "applying", "applied", "rejected"]
ReportStatus = Literal["pending", "accepting", "accepted", "rejected", "reverting", "reverted"]  # reverting, reverted: V48
MemoryStatus = Literal["active", "corrected", "revoked"]
TaskStatus = Literal["authorised", "queued", "running", "done", "failed", "blocked", "stopped", "cancelled"]  # cancelled: V48, only by a revert
MediaStatus = Literal["rendering", "ready", "unavailable"]
RelationshipLabel = Literal["supports", "contradicts", "extends", "new_question", "related_unestablished"]
RetrievalMethod = Literal["vector_search", "text_search"]
EventType = Literal[
    "diagnostic_created",
    "value_applied",
    "proposal_pending",
    "proposal_rejected",
    "run_status_changed",
    "action_allowed",
    "action_blocked",
    "action_status_changed",
    "scan_finished",
    "report_filed",
    "report_decided",
    "memory_changed",
    "task_status_changed",
    "related_evidence_filed",
    "report_reverted",  # V48
    "value_reverted",  # V48
    # deferred
    "rule_status_changed",
    "alert_created",
]


# ---------------------------------------------------------------------------
# Errors (one shape for every route)
# ---------------------------------------------------------------------------


class ErrorBody(Shape):
    code: str = Field(description="snake_case error code, for example not_implemented")
    message: str


class ErrorResponse(Shape):
    """`{ error: { code, message } }` with a 4xx or 5xx status. A blocked action is not an error."""

    error: ErrorBody


# ---------------------------------------------------------------------------
# Identity, stamps and grants (AD-17, AD-18)
# ---------------------------------------------------------------------------


class Stamp(Shape):
    """run: run_id set, principal = agent; reviewer: run_id null, agent null, initiated_by = Reviewer;
    seed: { kind: seed, principal: seed, run_id: null } only (D19)."""

    kind: Literal["run", "reviewer", "seed"]
    run_id: str | None = None
    agent: str | None = None
    initiated_by: str | None = None
    principal: str
    acting_for: str | None = None
    grant_id: str | None = None
    grant_version: int | None = None
    model: str | None = None
    prompt_version: str | None = None
    policy_set_version: str | None = None


class Principal(Shape):
    """From GET /whoami; `actions` are the caller's current grant's actions (D53)."""

    id: str
    name: str
    kind: PrincipalKind
    actions: list[ActionKind] = []


class AuthorisedBy(Shape):
    principal: str
    initiated_by: str | None = None
    acting_for: str | None = None
    granted_by: str | None = None
    grant_id: str
    grant_version: int | None = Field(default=None, description="null when no grant version exists (check 1 blocked)")
    expires_at: datetime | None = None
    policy_set_version: str | None = None


class GrantScope(Shape):
    diagnostic_ids: list[str] = []
    scope_id: str | None = None


class GrantScopeAll(Shape):
    """Valid only on the seed grant (D16)."""

    all: Literal[True]


class GrantLimits(Shape):
    max_results: int


class Grant(Shape):
    id: str = Field(description="<grant_id>@v<version>")
    grant_id: str
    version: int
    principal: str
    kind: GrantKind
    acting_for: str | None = None
    granted_by: str | None = None
    startable_by: list[str] = []
    team_id: str | None = None
    team_name: str | None = None
    scope_name: str | None = Field(default=None, description="the research scope's title, for display (A03)")
    scope: GrantScope | GrantScopeAll
    destinations: list[Destination] = []
    actions: list[ActionKind] = []
    limits: GrantLimits | None = None
    task_id: str | None = None
    expires_at: datetime | None = None
    status: Literal["active", "revoked", "expired"]
    created_at: datetime | None = None


class PolicyRequires(Shape):
    quote_found: bool | None = None
    supported: bool | None = None
    min_confidence: float | None = None
    claim_checks: list[Literal["claim_performed_or_results", "claim_planned", "claim_preclinical"]] = []


class Policy(Shape):
    id: str = Field(description="<policy_id>@v<version>")
    policy_id: str
    version: int
    status: Literal["draft", "active", "retired"]
    applies_to: list[ActionKind] = []
    requires: PolicyRequires
    text: str
    author: str | None = None
    approved_by: str | None = None
    created_at: datetime | None = None


class PolicySet(Shape):
    id: str = Field(description="policy_set_version, ps_<hash of the sorted members>")
    members: list[str] = Field(description='["<policy_id>@v<n>", ...]')
    created_at: datetime | None = None


class Team(Shape):
    id: str
    name: str
    profile: dict[str, list[str]] = Field(default_factory=dict, description="modalities, biomarkers, linked_drugs")
    last_seen_seq: int | None = None
    last_seen_at: datetime | None = None
    synthetic: bool = False


# ---------------------------------------------------------------------------
# Research scope and source versions (AD-25, V40)
# ---------------------------------------------------------------------------


class ScopeCursor(Shape):
    last_update_post_date: str | None = None
    set_at: datetime | None = None
    set_by_run_id: str | None = None


class Scope(Shape):
    id: str = Field(description="scope_id, hand-written: scope_ plus a slug")
    name: str
    team_id: str
    assays: list[str] = Field(description="the four exact D45 trade-name strings")
    aliases: list[str] = Field(default_factory=list, description="search terms only; never resolve a name (V34)")
    condition: str
    condition_aliases: list[str] = Field(default_factory=list, description="search terms for the condition only (A03 seeds them)")
    priority_refs: list[str] = Field(default_factory=list, description="source_refs the scan takes first (A03 seeds them)")
    source: Literal["clinicaltrials.gov"] = "clinicaltrials.gov"
    cursor: ScopeCursor


class SourceVersion(Shape):
    """Immutable; source_items.current_version_id points at the current one (V40).
    raw_text is stored but never returned by the API."""

    id: str = Field(description="version_id, sv_")
    source_ref: str
    last_update_post_date: str | None = None
    content_hash: str
    evidence_text: str | None = None
    overall_status: str | None = None
    has_results: bool | None = None
    interventions: list[dict[str, Any]] = Field(default_factory=list, description="verbatim")
    previous_version_id: str | None = None
    run_id: str | None = None
    fetched_at: datetime | None = None


# ---------------------------------------------------------------------------
# Runs and admissions (AD-16, AD-17, AD-21)
# ---------------------------------------------------------------------------


class RunScan(Shape):
    cursor_from: str | None = None
    cursor_to: str | None = None
    query: dict[str, Any] | str | None = None
    source_refs: list[str] = []


class RunCounts(Shape):
    total: int = 0
    done: int = 0
    failed: int = 0
    filed: int = 0
    reports: int = 0
    allowed: int = 0
    blocked: int = 0
    unknown: int = 0
    not_admitted: int = 0
    early_research: int = 0


class RunActive(Shape):
    source_ref: str
    step: str


class RunFailure(Shape):
    source_ref: str
    error: str


class Run(Shape):
    id: str
    agent: str
    initiated_by: str
    model: str | None = None
    prompt_version: str | None = None
    policy_set_version: str | None = None
    acting_for: str | None = None
    grant_id: str
    grant_version: int = Field(description="pinned at start")
    team_id: str | None = Field(default=None, description="from the grant")
    mode: Mode = "live"
    source: str | None = None
    set: str = Field(description="discover | nct:<NCT ID> | task:<task_id>")
    kind: RunKind
    scope_id: str | None = None
    task_id: str | None = Field(default=None, description='task runs only; their id is derive("run_", task_id) (V38)')
    scan: RunScan | None = None
    status: RunStatus
    in_flight: int = Field(default=0, description="count of admitted admissions")
    counts: RunCounts = Field(default_factory=RunCounts)
    active: list[RunActive] = []
    failures: list[RunFailure] = []
    started_at: datetime | None = None
    stopping_at: datetime | None = None
    stopped_at: datetime | None = None
    finished_at: datetime | None = None


class Admission(Shape):
    id: str = Field(description='derive("adm_", run_id, item_key)')
    run_id: str
    item_key: str
    status: Literal["admitted", "released", "abandoned"]
    admitted_at: datetime | None = None
    expires_at: datetime | None = None
    released_at: datetime | None = None


# ---------------------------------------------------------------------------
# Retrieval and memory use (AD-15, AD-26, AD-28)
# ---------------------------------------------------------------------------


class RetrievalFilter(Shape):
    scope_id: str | None = None
    team_id: str | None = None
    status: str | None = None
    tags: dict[str, Any] | None = None


class RetrievalItem(Shape):
    ref: str = Field(description="source_ref | finding_id | memory_id")
    version_id: str | None = Field(default=None, description="source items (V40)")
    score: float


class Retrieval(Shape):
    """The UI says "related by text search" when method is text_search, never "Vector Search"."""

    method: RetrievalMethod
    index: str | None = None
    top_k: int
    filter: RetrievalFilter = Field(default_factory=RetrievalFilter)
    items: list[RetrievalItem] = []


class MemorySource(Shape):
    decision_id: str | None = None
    report_id: str | None = None


class MemoryEffect(Shape):
    target: str = Field(description="sentence or label")
    before: str
    after: str


class MemoryUse(Shape):
    """A null effect means "retrieved, no change" (AD-28)."""

    memory_id: str
    version: int
    author: str
    source: MemorySource
    score: float | None = None
    effect: MemoryEffect | None = None


# ---------------------------------------------------------------------------
# Decisions and actions (AD-19, AD-20, AD-22)
# ---------------------------------------------------------------------------


class DecisionCause(Shape):
    """Reviewer decisions only: one of proposal_id | report_id | memory_id | action_id, plus origin_run_id."""

    proposal_id: str | None = None
    report_id: str | None = None
    memory_id: str | None = None
    action_id: str | None = None
    origin_run_id: str | None = None


class EvidenceRef(Shape):
    source_ref: str | None = None
    version_id: str | None = Field(default=None, description="pinned (V40)")
    finding_id: str | None = None
    proposal_id: str | None = None
    report_id: str | None = None
    quote: str | None = None
    check: dict[str, Any] | None = None


class Target(Shape):
    diagnostic_id: str | None = Field(default=None, description="null for a scope-collection update (V43)")
    proposal_id: str | None = None
    value_id: str | None = None
    report_id: str | None = None
    memory_id: str | None = None
    task_id: str | None = None
    scope_id: str | None = None


class ClaimCheck(Shape):
    claim_kind: str
    text: str
    passed: bool
    detail: str | None = None


class CheckResult(Shape):
    check: str = Field(description="one of the five gate checks, in order")
    passed: bool | Literal["n/a"]
    detail: str | None = None


class Decision(Shape):
    """One per gate evaluation, allowed or blocked (D5).
    run: agent = run.agent, initiated_by = run.initiated_by; Reviewer: agent null,
    initiated_by = Reviewer; seed: agent "seed", initiated_by "seed" (D19).
    seq = the seq of its action_allowed or action_blocked event (D21)."""

    id: str = Field(description="decision_id, dec_")
    run_id: str | None = None
    agent: str | None = None
    initiated_by: str | None = None
    stamp: Stamp
    cause: DecisionCause | None = None
    request_id: str | None = Field(default=None, description="Reviewer decisions only, server-generated (D20)")
    kind: ActionKind
    inputs: dict[str, Any] = {}
    evidence_ref: EvidenceRef | None = None
    destination: Destination
    target: Target = Field(default_factory=Target)
    claims: list[ClaimCheck] = Field(default_factory=list, description="check 4 claim checks; empty when n/a")
    retrieval: Retrieval | None = Field(default=None, description="report-level file_proposal only (V14)")
    memories_used: list[MemoryUse] = []
    checks: list[CheckResult] = []
    failed_check: str | None = None
    grant_id: str
    grant_version: int | None = Field(description="evaluated; null when the grant does not exist (check 1 blocked)")
    run_grant_version: int | None = Field(default=None, description="pinned at run start")
    policy_set_version: str | None = None
    outcome: Outcome
    action_id: str | None = None
    seq: int | None = None
    decided_at: datetime | None = None
    authorised_by: AuthorisedBy | None = None


class SlackLinkUrls(Shape):
    report_url: str
    diagnostic_url: str | None = Field(default=None, description="null when no Diagnostic resolves (V43)")


class SlackResult(Shape):
    """notify_slack; http_status and response_body null when no response arrived."""

    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)
    http_status: int | None
    response_body: str | None
    posted_at: datetime | None
    link_urls: SlackLinkUrls


class SearchSourceResult(Shape):
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)
    http_status: int | None
    cursor_from: str | None
    cursor_to: str | None
    source_refs: list[str]
    count: int


class BriefingResult(Shape):
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)
    audio_id: str


class AvatarResult(Shape):
    """generate_avatar_video, render accepted."""

    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)
    media_id: str
    provider_video_id: str | None


class LedgerResult(Shape):
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)
    proposal_ids: list[str] = []
    value_ids: list[str] = []
    report_id: str | None = None
    memory_id: str | None = None
    task_id: str | None = None


ActionResult = SlackResult | SearchSourceResult | BriefingResult | AvatarResult | LedgerResult


class Resolution(Shape):
    """AD-20 manual resolution of an unknown notification."""

    outcome: Literal["delivered", "failed"]
    note: str
    decision_id: str
    by: str
    at: datetime


class Action(Shape):
    """External kinds (notify_slack, search_source, generate_briefing, generate_avatar_video):
    queued | dispatching | delivered | failed | unknown. DxP kinds: queued | done | failed.
    `reconciling` is returned in place of dispatching while the sweep settles it (D24)."""

    id: str = Field(description="action_id, act_")
    decision_id: str
    admission_id: str | None = None
    run_id: str | None = None
    kind: ActionKind
    destination: Destination
    target: Target = Field(default_factory=Target)
    inputs: dict[str, Any] = {}
    evidence_ref: EvidenceRef | None = None
    stamp: Stamp
    error: Literal["abandoned_before_send", "abandoned_in_flight"] | None = None
    status: ActionStatus
    result: ActionResult | None = None
    resolution: Resolution | None = None
    proposed_at: datetime | None = None
    decided_at: datetime | None = Field(default=None, description="queued")
    claimed_at: datetime | None = None
    observed_at: datetime | None = None
    authorised_by: AuthorisedBy | None = None


# ---------------------------------------------------------------------------
# Records, values and proposals (AD-1, AD-2)
# ---------------------------------------------------------------------------


class ValueEvidence(Shape):
    source_ref: str
    version_id: str | None = Field(default=None, description="V40")
    source: str | None = None
    source_url: str | None = None
    source_date: str | None = None
    quote: str | None = None
    data_as_of: str | None = Field(default=None, description="from source_date")


class ManualEvidence(Shape):
    manual: Literal[True]
    submitter: str | None = None
    note: str | None = None


class ValueFlag(Shape):
    rule_id: str
    note: str | None = None


class ValueCheck(Shape):
    quote_found: bool | None = None
    supported: bool | None = None
    confidence: float | None = None
    flags: list[ValueFlag] = []


class Value(Shape):
    """The AD-2 value entry, plus evidence.data_as_of."""

    value_id: str
    value: str = Field(description="canonical form, from registry.canonical()")
    label: str | None = None
    detail: dict[str, Any] | str | None = None
    state: Literal["current", "superseded", "rejected"]
    review: Literal["unreviewed", "accepted", "edited", "manual"]
    evidence: ValueEvidence | ManualEvidence
    check: ValueCheck | None = None
    proposal_id: str | None = None
    action_id: str | None = None
    stamp: Stamp | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None
    reason: str | None = None


class RecordField(Shape):
    values: list[Value] = []
    no_data: bool = False


class Completeness(Shape):
    """Deferred (4.6)."""

    filled: int
    of: int
    thin: bool
    stale: bool


class Record(Shape):
    id: str = Field(description="dx_")
    name: str
    lifecycle_stage: str | None = None
    early_research: bool = False
    created_mode: Mode | None = None
    rev: int | None = None
    synthetic: bool = False
    applied_proposal_ids: list[str] = []
    fields: dict[str, RecordField] = {}
    completeness: Completeness | None = None


class ProposalNotification(Shape):
    """Read-time only, built from the report's notify_slack action (D47, V11)."""

    action_id: str
    status: ActionStatus
    posted_at: datetime | None = None


class ProposalTarget(Shape):
    scope_id: str | None = None


class Proposal(Shape):
    id: str = Field(description="p_")
    diagnostic_id: str | None = Field(default=None, description="null for a scope-collection update, with target.scope_id (V43)")
    diagnostic_name: str | None = None
    target: ProposalTarget | None = None
    op: Literal["add", "remove"] = Field(default="add", description="remove only for a reverse proposal (AD-31, V48)")
    reverts_proposal_id: str | None = Field(default=None, description="V48")
    field: str
    value: str
    label: str | None = None
    current_value: Any = None
    evidence: ValueEvidence | ManualEvidence | None = None
    check: ValueCheck | None = None
    status: ProposalStatus
    mode: Mode
    trigger: str | None = None
    run_id: str | None = None
    report_id: str | None = None
    action_id: str | None = None
    decision_id: str | None = None
    stamp: Stamp | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None
    reason: str | None = None
    notification: ProposalNotification | None = None


class Event(Shape):
    seq: int
    type: EventType
    mode: Mode | None = None
    run_id: str | None = None
    stamp: Stamp | None = None
    decision_id: str | None = None
    action_id: str | None = None
    outcome: Outcome | None = None
    failed_check: str | None = None
    status: str | None = None
    diagnostic_id: str | None = None
    proposal_id: str | None = None
    report_id: str | None = None
    memory_id: str | None = None
    task_id: str | None = None
    field: str | None = None
    trigger: str | None = None
    at: datetime | None = None


class Node(Shape):
    """Graph node (cut with A15; kept for the Story 1.1 contract)."""

    id: str
    type: str
    label: str
    lifecycle_stage: str | None = None
    early_research: bool = False
    sample_type: str | None = None
    url: str | None = None
    run_id: str | None = None
    changed: bool = False
    context: bool = False


class Link(Shape):
    """Graph link (cut with A15; kept for the Story 1.1 contract) (D29)."""

    source: str
    target: str
    kind: str
    status: Literal["pending", "applied"]
    proposal_id: str | None = None
    run_id: str | None = None
    changed: bool = False
    context: bool = False


# ---------------------------------------------------------------------------
# Reports, relationships, memories, tasks and media (Epic 10)
# ---------------------------------------------------------------------------


class RelationshipQuote(Shape):
    source_ref: str
    version_id: str | None = Field(default=None, description="V40")
    text: str
    quote_found: bool


class Relationship(Shape):
    """label is related_unestablished unless both quotes are found (AD-26);
    similarity never stands in for a quote."""

    id: str = Field(description="rel_")
    related_ref: str
    related_kind: Literal["source_item", "finding"]
    related_title: str | None = None
    label: RelationshipLabel
    rationale: str | None = None
    new_quote: RelationshipQuote | None = None
    related_quote: RelationshipQuote | None = None
    similarity: float | None = None
    retrieval_method: RetrievalMethod | None = None
    origin: str = Field(description="discovery | task:<task_id>")
    status: Literal["pending", "accepted", "reverted"]  # reverted: V48
    filed_by_decision_id: str | None = None


class ReportQuote(Shape):
    text: str
    quote_found: bool
    version_id: str | None = None


class NameMention(Shape):
    """A name the record gives, verbatim: "named in the record", never proof of use (V37)."""

    name: str = Field(description="verbatim")
    resolved_diagnostic_id: str | None = Field(default=None, description="exact FDA trade-name match only (V34)")
    field: str | None = Field(default=None, description="the record field it came from, for example otherNames")


class ReportDiscovery(Shape):
    summary: str
    quotes: list[ReportQuote] = []
    trial_status: str | None = None
    has_results: bool | None = None
    intervention_text: str | None = Field(default=None, description="verbatim")
    mentions: list[NameMention] = Field(default_factory=list, description="the record's name mentions (V33, V37)")


class TaskParams(Shape):
    condition: str
    stage: str = "early"
    testing: list[str] = []
    has_results: bool = True
    max: int = 5


class RecommendedTask(Shape):
    kind: Literal["search_related"] = "search_related"
    params: TaskParams


class ReportBriefingState(Shape):
    status: Literal["none", "ready", "failed"] = "none"
    audio_id: str | None = None


class ReportApproval(Shape):
    """Stored by the claim pending -> accepting so an interrupted authorisation can be
    completed without a second click (V45)."""

    decision_id: str
    request_id: str | None = None
    reviewer: str
    note: str | None = None
    correction: str | None = None
    task_id: str | None = None
    task_step: Literal["pending", "done", "blocked"]
    reason: str | None = Field(default=None, description='why the task was not authorised: "Follow-up task not authorised: <reason>" (V45)')


class ReportRevert(Shape):
    """Stored by the claim accepted -> reverting (AD-31, V48)."""

    decision_id: str
    request_id: str | None = None
    by: str
    at: datetime | None = None
    note: str
    step: Literal["pending", "done"]


class Media(Shape):
    id: str = Field(description="media_")
    report_id: str
    kind: Literal["avatar_video"] = "avatar_video"
    provider: Literal["heygen"] = "heygen"
    provider_video_id: str | None = None
    status: MediaStatus
    video_url: str | None = None
    script_hash: str | None = None
    decision_id: str | None = None
    created_at: datetime | None = None
    checked_at: datetime | None = None


class Report(Shape):
    id: str = Field(description='report_id, derive("rep_", run_id, source_ref)')
    run_id: str
    scope_id: str
    team_id: str
    source_ref: str
    version_id: str = Field(description="the source version used (V40)")
    nct_id: str | None = None
    headline: str
    status_line: str | None = None
    discovery: ReportDiscovery
    related: list[Relationship] = []
    uncertainties: list[str] = []
    gap: str = Field(description="one question (V26)")
    retrieval: Retrieval | None = None
    memories_used: list[MemoryUse] = []
    proposal_ids: list[str] = []
    diagnostic_ids: list[str] = Field(default_factory=list, description="empty when no Diagnostic resolves (V43)")
    recommended_task: RecommendedTask | None = None
    draft: Literal[1, 2] = 1
    blocked_draft_decision_id: str | None = None
    stamp: Stamp | None = None
    file_decision_id: str | None = None
    status: ReportStatus
    decided_by: str | None = None
    decided_at: datetime | None = None
    note: str | None = None
    approval: ReportApproval | None = Field(default=None, description="V45")
    revert: ReportRevert | None = Field(default=None, description="AD-31, V48")
    reverted_by: str | None = None
    reverted_at: datetime | None = None
    task_id: str | None = None
    memory_id: str | None = None
    notification: ProposalNotification | None = Field(default=None, description="read time")
    script: str = Field(description="the grounded text script, built at filing by reports.script_for (V41)")
    script_hash: str
    briefing: ReportBriefingState = Field(default_factory=ReportBriefingState)
    avatar: Media | None = None
    created_at: datetime | None = None


class MemoryTags(Shape):
    assay: str | None = None
    claim_kind: str | None = None


class Memory(Shape):
    """No embedding in responses (AD-28)."""

    id: str = Field(description="memory_id, mem_")
    version: int
    team_id: str
    author: str
    source: MemorySource
    text: str
    tags: MemoryTags = Field(default_factory=MemoryTags)
    status: MemoryStatus
    supersedes: str | None = Field(default=None, description="memory_id@v<n>")
    decision_id: str | None = Field(default=None, description="the gate decision that wrote this version")
    created_at: datetime | None = None


class TaskResult(Shape):
    """`answer` is one sentence answering `question`; with_posted_results may be empty, and then
    `answer` is "No matching results found among the records searched"; query, searched_count
    and limit are always shown (V42)."""

    answer: str
    with_posted_results: list[str] = Field(default_factory=list, description="NCT IDs")
    query: str | dict[str, Any]
    searched_count: int
    limit: int
    source_refs: list[str] = []
    related_ids: list[str] = []


class Task(Shape):
    """Inserted `queued` with task_run on, `authorised` and never queued with it off (V38).
    Findings are pending related evidence, never accepted knowledge (V27)."""

    id: str = Field(description='task_id, derive("task_", report_id)')
    report_id: str
    kind: Literal["search_related"] = "search_related"
    question: str = Field(description="the report's gap")
    params: TaskParams
    grant_id: str = Field(description="task-<hex>")
    grant_version: int = 1
    status: TaskStatus
    error: Literal["abandoned"] | None = None
    queued_at: datetime | None = None
    run_id: str | None = Field(default=None, description='derive("run_", task_id)')
    authorised_by_decision_id: str | None = None
    result: TaskResult | None = None
    created_at: datetime | None = None


class Briefing(Shape):
    """The report briefing (B06). The script is always returned as text, whatever the audio
    status (V29, V41); `unavailable` without a key (OD3)."""

    report_id: str
    script: str
    script_hash: str | None = None
    status: Literal["none", "ready", "failed", "unavailable"]
    audio_id: str | None = None
    audio_url: str | None = None


# ---------------------------------------------------------------------------
# Audit (AD-22, with the V14 sections)
# ---------------------------------------------------------------------------


class ProposalReview(Shape):
    status: ProposalStatus
    decided_by: str | None = None
    decided_at: datetime | None = None


class ReportReview(Shape):
    status: ReportStatus
    decided_by: str | None = None
    decided_at: datetime | None = None


class AuditEntry(Shape):
    """proposal_review and report_review are read live at request time (AD-22)."""

    seq: int | None = None
    decision_id: str
    outcome: Outcome
    failed_check: str | None = None
    checks: list[CheckResult] = []
    kind: ActionKind
    destination: Destination
    inputs: dict[str, Any] = {}
    evidence_ref: EvidenceRef | None = None
    stamp: Stamp | None = None
    cause: DecisionCause | None = None
    grant_id: str
    grant_version: int
    policy_set_version: str | None = None
    action_id: str | None = None
    status: ActionStatus | None = None
    result: ActionResult | None = None
    resolution: Resolution | None = None
    decided_at: datetime | None = None
    claimed_at: datetime | None = None
    observed_at: datetime | None = None
    authorised_by: AuthorisedBy | None = None
    proposal_review: ProposalReview | None = None
    report_id: str | None = None
    task_id: str | None = None
    memory_id: str | None = None
    claims: list[ClaimCheck] = []
    scan: RunScan | None = Field(default=None, description="search_source entries: cursor_from, cursor_to, source_refs")
    retrieval: Retrieval | None = None
    memories_used: list[MemoryUse] = []
    relationships: list[Relationship] = Field(default_factory=list, description="report entries: labels and both quotes")
    report_review: ReportReview | None = None


class AuditSource(Shape):
    source_ref: str
    window: str | None = None
    source_date: str | None = None


class LinkedRun(Shape):
    run_id: str
    kind: Literal["task"] = "task"
    task_id: str
    status: RunStatus


class Audit(Shape):
    """after_run: Reviewer decisions whose cause.origin_run_id is this run; linked_runs: task runs
    authorised from this run's reports (V14)."""

    run: Run
    policies: list[Policy] = []
    sources: list[AuditSource] = []
    entries: list[AuditEntry] = []
    after_run: list[AuditEntry] = []
    linked_runs: list[LinkedRun] = []


# ---------------------------------------------------------------------------
# Deferred shapes, kept so the deferred routes are typed (AD-14)
# ---------------------------------------------------------------------------


class Rule(Shape):
    id: str
    field: str
    text: str
    status: str
    from_proposal_id: str | None = None
    synthetic: bool = False


class Alert(Shape):
    id: str
    team_id: str
    diagnostic_id: str
    diagnostic_name: str | None = None
    kind: Literal["first", "update"]
    trigger: str | None = None
    why: str | None = None
    lifecycle_stage: str | None = None
    from_stage: str | None = None
    evidence: ValueEvidence | None = None
    early_research: bool = False
    seq: int | None = None
    at: datetime | None = None
    dismissed: bool = False


class Shortlist(Shape):
    id: str
    team_id: str
    intended_use: str
    query: dict[str, Any] | str | None = None
    diagnostic_ids: list[str] = []
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# GET /schema (AD-2: the registry's fields, enums and stage order)
# ---------------------------------------------------------------------------


class SchemaEnumValue(Shape):
    value: str = Field(description="the canonical value (lower snake_case, or an HGNC or OncoTree code)")
    label: str


class SchemaField(Shape):
    key: str
    label: str
    cardinality: Literal["single", "list"]
    canonical_form: str | None = Field(default=None, description="how registry.canonical() forms the value")
    enum: list[SchemaEnumValue] | None = Field(default=None, description="the allowed values, when the field has an enum")


class SchemaResponse(Shape):
    """A02's `registry.describe()`, served as is, plus `enums` (AD-14: "fields, enums, stage order"),
    derived here as { field key: [values] } for the fields that have an enum."""

    fields: list[SchemaField]
    enums: dict[str, list[str]]
    stage_order: list[str]
    not_determined_stage: str | None = None
    early_research_stages: list[str] = []
    low_confidence_threshold: float | None = None


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class RunCreate(Shape):
    """No team_id: the grant defines the Team (D18). A `task:` set is refused with 403 (V38)."""

    grant_id: str
    set: str = Field(description="discover | nct:<NCT ID> (setup only)")


class ReportDecisionRequest(Shape):
    action: Literal["approve", "reject"]
    note: str | None = Field(default=None, description="required for reject and for a correction")
    correction: str | None = None
    claim_kind: ClaimKind | None = Field(
        default=None, description="tags the memory a reject or correction creates (M1: claim_performed_or_results)"
    )


class MemoryCorrectRequest(Shape):
    text: str
    note: str


class MemoryRevokeRequest(Shape):
    note: str


class ResolveRequest(Shape):
    outcome: Literal["delivered", "failed"]
    note: str


class ValueReviewRequest(Shape):
    action: Literal["accept", "edit", "reject"]
    value: str | None = None
    reason: str | None = Field(default=None, description="required for edit and reject (D16)")


class ProposalDecisionRequest(Shape):
    """Superseded (V8)."""

    action: Literal["accept", "edit", "reject"]
    value: str | None = None
    reason: str | None = None


class PolicyApproveRequest(Shape):
    """Cut (9.11)."""

    version: int


class ValueAddRequest(Shape):
    """Deferred (4.7)."""

    field: str
    value: str
    note: str | None = None


class QueryRequest(Shape):
    """Deferred (4.2)."""

    text: str
    filters: dict[str, Any] | None = None
    team_id: str | None = None


class ShortlistCreate(Shape):
    """Deferred (4.4)."""

    team_id: str
    intended_use: str
    query: dict[str, Any] | str | None = None
    diagnostic_ids: list[str] = []


class ReportRevertRequest(Shape):
    """V48: note required before the gate (400)."""

    note: str


class TeamSeenRequest(Shape):
    """Deferred (5.1)."""

    seq: int


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------


class RunList(Shape):
    items: list[Run]
    next: str | None = None


class ActionList(Shape):
    items: list[Action]
    next: str | None = None


class ScopeList(Shape):
    items: list[Scope]
    next: str | None = None


class ReportList(Shape):
    items: list[Report]
    next: str | None = None


class MemoryList(Shape):
    items: list[Memory]
    next: str | None = None


class TaskList(Shape):
    items: list[Task]
    next: str | None = None


class GrantList(Shape):
    items: list[Grant]
    next: str | None = None


class PolicyList(Shape):
    items: list[Policy]
    policy_set_version: str | None = None


class TeamList(Shape):
    items: list[Team]


class ProposalList(Shape):
    items: list[Proposal]
    next: str | None = None


class RecordList(Shape):
    """Deferred (D40)."""

    items: list[Record]
    next: str | None = None


class ReportDecisionResponse(Shape):
    """A report not pending returns it unchanged with its existing decisions, task and run (V38).
    `message` carries the approval sentence (V27, V38)."""

    report: Report
    decisions: list[Decision]
    task: Task | None = None
    memory: Memory | None = None
    message: str | None = None


class ReportRevertResponse(Shape):
    """AD-31, V48. `removed`: the number of accepted updates undone."""

    report: Report
    decision: Decision
    task: Task | None = None
    removed: int


class MemoryChangeResponse(Shape):
    memory: Memory
    decision: Decision


class ResolveResponse(Shape):
    action: Action
    decision: Decision


class ValueReviewResponse(Shape):
    record: Record
    decision: Decision


class BriefingResponse(Shape):
    briefing: Briefing
    decision: Decision


class AvatarResponse(Shape):
    media: Media
    decision: Decision


class ProposalDecisionResponse(Shape):
    """Superseded (V8)."""

    proposal: Proposal
    decision: Decision
    rule_draft: Rule | None = None


class ChangesResponse(Shape):
    """Cut (A12)."""

    events: list[Event]
    last_seq: int


class GraphResponse(Shape):
    """Cut (A15)."""

    nodes: list[Node]
    links: list[Link]


class DigestResponse(Shape):
    """Deferred (3.3)."""

    pending: list[Proposal]
    alerts: list[Alert]


class QueryResponse(Shape):
    """Deferred (4.2)."""

    parsed: dict[str, Any]
    columns: list[str]
    rows: list[Record]


# ---------------------------------------------------------------------------
# Internal types of the frozen signatures (not API responses)
# ---------------------------------------------------------------------------


class RunContext(BaseModel):
    """What `runs.context(run_id, key)` returns for a run write, or what a Reviewer route builds
    for a Reviewer decision (run_id None, request_id and cause set). Passed to gate.evaluate()."""

    run_id: str | None = None
    principal: Principal
    stamp: Stamp
    grant_id: str
    grant_version: int
    run_grant_version: int | None = None
    policy_set_version: str | None = None
    mode: Mode = "live"
    request_id: str | None = None
    cause: DecisionCause | None = None
    admission_id: str | None = None


class ProposedAction(BaseModel):
    """The action a caller asks the gate to evaluate: the Decision's inputs before the checks."""

    kind: ActionKind
    destination: Destination
    target: Target = Field(default_factory=Target)
    inputs: dict[str, Any] = {}
    evidence_ref: EvidenceRef | None = None
    claims: list[ClaimCheck] = []
    retrieval: Retrieval | None = None
    memories_used: list[MemoryUse] = []
