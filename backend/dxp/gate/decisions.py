"""Decision and action records for every gate evaluation (D5, D20, D21, AD-19, AD-22).

``record()`` writes, insert-if-absent, one ``decisions`` document per
evaluation. Allowed: it also inserts the ``actions`` document (``queued``),
sets the decision's ``action_id`` and emits ``action_allowed``. Blocked: it
emits ``action_blocked`` and writes nothing else. In both cases the
decision's ``seq`` is set from its event (D21). A repeat of the same run step
finds the stored decision and only completes what is missing.

This module also holds ``deps``: the one seam to modules other PRs own
(``store`` and ``identity`` from A01 and A02, ``gate.policy_sets`` from A03,
``schema.registry`` from A02). The gate and the ledger reach them only
through ``deps``, so the A01 rebase changes this one place.
"""

from __future__ import annotations

import importlib
import inspect
from datetime import datetime, timezone
from typing import Any

from dxp.gate.checks import GateAction, GateCtx


class _Deps:
    """Late-bound access to modules this PR does not own.

    * ``dxp.store.db()`` and ``dxp.store.emit_event(event, *, session=None) -> int`` (A01);
    * ``dxp.identity.derive`` and ``normalise_name`` (A02);
    * ``dxp.gate.policy_sets.current_grant(grant_id) -> Grant | None`` (latest version, any
      status), ``current_set() -> PolicySet``, ``policy_set(version)`` and
      ``policies_in_set(version)`` (A03);
    * ``dxp.schema.registry.STAGE_ORDER`` and ``get_field(key).cardinality`` (A02).

    Grants and policies come back as plain documents (``model_dump``) so the checks stay
    pure. Tests replace any of them with ``deps.override(...)``.
    """

    def __init__(self) -> None:
        self._overrides: dict[str, Any] = {}

    def override(self, **kwargs: Any) -> None:
        self._overrides.update(kwargs)

    def reset(self) -> None:
        self._overrides.clear()

    def _real(self, module: str, name: str) -> Any:
        return getattr(importlib.import_module(module), name)

    def _pick(self, name: str, module: str, attr: str | None = None) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return self._real(module, attr or name)

    def db(self) -> Any:
        return self._pick("db", "dxp.store")()

    async def emit_event(self, event: dict[str, Any], *, session: Any = None) -> int:
        return await _maybe_await(self._pick("emit_event", "dxp.store")(event, session=session))

    def derive(self, prefix: str, *parts: Any) -> str:
        return self._pick("derive", "dxp.identity")(prefix, *parts)

    def normalise_name(self, text: str) -> str:
        return self._pick("normalise_name", "dxp.identity")(text)

    async def current_grant(self, grant_id: str) -> dict[str, Any] | None:
        return as_doc(await _maybe_await(self._pick("current_grant", "dxp.gate.policy_sets")(grant_id)))

    async def current_set(self) -> tuple[str, list[dict[str, Any]]]:
        """The current ``(policy_set_version, policies)``."""
        if "current_set" in self._overrides:
            return await _maybe_await(self._overrides["current_set"]())
        ps = await _maybe_await(self._real("dxp.gate.policy_sets", "current_set")())
        ps_doc = as_doc(ps) or {}
        version = ps_doc.get("id") or ps_doc.get("_id")
        policies = await _maybe_await(self._real("dxp.gate.policy_sets", "policies_in_set")(version))
        return version, [as_doc(p) for p in policies]

    async def policy_set(self, version: str) -> dict[str, Any] | None:
        """A recorded ``policy_sets`` document (a run's pinned set), or ``None``."""
        return await _maybe_await(self._pick("policy_set", "dxp.gate.policy_sets")(version))

    async def policies_in_set(self, version: str) -> list[dict[str, Any]]:
        """The member policy documents of a recorded set (A03)."""
        found = await _maybe_await(self._pick("policies_in_set", "dxp.gate.policy_sets")(version))
        return [as_doc(p) for p in found]

    def stage_order(self) -> list[str]:
        if "stage_order" in self._overrides:
            return list(self._overrides["stage_order"])
        return list(self._real("dxp.schema.registry", "STAGE_ORDER"))

    def cardinality(self, field: str) -> str:
        if "cardinality" in self._overrides:
            return self._overrides["cardinality"](field)
        try:
            return self._real("dxp.schema.registry", "get_field")(field).cardinality
        except (ImportError, AttributeError, KeyError):
            return "single" if field in SINGLE_FIELDS else "list"

    def now(self) -> datetime:
        if "now" in self._overrides:
            return self._overrides["now"]()
        return datetime.now(timezone.utc)


def as_doc(obj: Any) -> dict[str, Any] | None:
    """A model or a document as a plain dict (models keep ``id``; documents keep ``_id``)."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return dict(obj)


def to_api(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    """A stored document with Mongo's ``_id`` mapped to the API's ``id``."""
    if doc is None:
        return None
    out = {k: v for k, v in doc.items() if k != "_id"}
    out.setdefault("id", doc.get("_id"))
    return out


# AD-2 cardinality table, used only until the registry is on main.
SINGLE_FIELDS = frozenset({"modality", "regulatory_status", "lifecycle_stage", "provider"})

deps = _Deps()


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


# --- IDs (AD-3, D20, D49) ----------------------------------------------------

REPORT_TARGET_KINDS = frozenset(
    {"decide_report", "create_memory", "notify_slack", "generate_briefing", "generate_avatar_video", "revert_report"}
)

# Reviewer kinds whose IDs are derived without the request ID, so a retry finds
# the same Decision and a blocked one is final (V48, AD-31: revert_report).
# authorise_task passes its own derived ID instead (AD-29).
NO_REQUEST_ID_KINDS = frozenset({"revert_report"})


def target_key(kind: str, target: dict[str, Any], inputs: dict[str, Any] | None = None) -> str:
    """The AD-3 ``target`` part of a decision or action ID, in AD-3 order."""
    inputs = inputs or {}
    t = target
    if kind == "resolve_notification":
        return _need(t, "action_id", kind)
    if kind in ("correct_memory", "revoke_memory"):
        version = t.get("memory_version")
        return f"{_need(t, 'memory_id', kind)}@v{version}" if version is not None else _need(t, "memory_id", kind)
    if kind == "file_related_evidence":
        return f"{_need(t, 'task_id', kind)}|{_need(t, 'source_ref', kind)}"
    if kind == "authorise_task":
        return _need(t, "task_id", kind)
    if kind == "file_proposal" and t.get("report_id") and t.get("draft"):
        return f"{t['report_id']}|draft{t['draft']}"
    if kind in REPORT_TARGET_KINDS:
        return _need(t, "report_id", kind)
    if kind == "search_source":
        if t.get("task_id"):
            return f"{t['task_id']}|search"
        return f"{_need(t, 'scope_id', kind)}|{t.get('cursor', inputs.get('cursor'))}"
    if t.get("proposal_id"):
        return t["proposal_id"]
    if t.get("value_id"):
        return t["value_id"]
    field, value = t.get("field", inputs.get("field")), t.get("value", inputs.get("value"))
    if field is None:
        raise ValueError(f"{kind}: no target to derive an ID from")
    return f"{field}|{value}"


def _need(t: dict[str, Any], key: str, kind: str) -> str:
    value = t.get(key)
    if not value:
        raise ValueError(f"{kind} needs target.{key}")
    return str(value)


def ids_for(ctx: GateCtx, action: GateAction) -> tuple[str, str]:
    """``(decision_id, action_id)`` from ``(run_id or "-", kind, diagnostic_id or "-", target[, request_id])``."""
    target = action.id_target or target_key(action.kind, action.target, action.inputs)
    parts: list[Any] = [ctx.run_id or "-", action.kind, action.target.get("diagnostic_id") or "-", target]
    if ctx.kind == "reviewer" and ctx.request_id and action.kind not in NO_REQUEST_ID_KINDS:
        parts.append(ctx.request_id)
    decision_id = action.decision_id or deps.derive("dec_", *parts)
    return decision_id, deps.derive("act_", *parts)


# --- records -----------------------------------------------------------------


def authorised_by(ctx: GateCtx, grant: dict[str, Any] | None, policy_set_version: str | None) -> dict[str, Any]:
    grant = grant or {}
    return {
        "principal": ctx.principal,
        "initiated_by": ctx.initiated_by,
        "acting_for": grant.get("acting_for"),
        "granted_by": grant.get("granted_by"),
        "grant_id": grant.get("grant_id", ctx.grant_id),
        "grant_version": grant.get("version") or ctx.run_grant_version,
        "expires_at": grant.get("expires_at"),
        "policy_set_version": policy_set_version,
    }


def build_decision(
    ctx: GateCtx,
    action: GateAction,
    *,
    decision_id: str,
    grant: dict[str, Any] | None,
    policy_set_version: str | None,
    checks: list[dict[str, Any]],
    failed_check: str | None,
    claims: list[dict[str, Any]],
    now: datetime,
) -> dict[str, Any]:
    """The ``decisions`` document, AD-14 shape (``_id`` is the ``decision_id``)."""
    if ctx.kind == "run":
        agent, initiated_by = ctx.agent, ctx.initiated_by
    elif ctx.kind == "seed":
        agent, initiated_by = "seed", "seed"
    else:
        agent, initiated_by = None, ctx.initiated_by or ctx.principal
    target = {
        "diagnostic_id": action.target.get("diagnostic_id"),
        "proposal_id": action.target.get("proposal_id"),
        "value_id": action.target.get("value_id"),
        "report_id": action.target.get("report_id"),
        "memory_id": action.target.get("memory_id"),
        "task_id": action.target.get("task_id"),
        "scope_id": action.target.get("scope_id"),
    }
    for extra in ("diagnostic_ids", "action_id", "source_ref", "draft", "field", "value"):
        if action.target.get(extra) is not None:
            target[extra] = action.target[extra]
    inputs = dict(action.inputs)
    if action.mention:
        inputs.setdefault("mention", action.mention)
    doc = {
        "_id": decision_id,
        "run_id": ctx.run_id,
        "agent": agent,
        "initiated_by": initiated_by,
        "stamp": ctx.stamp,
        "cause": ctx.cause if ctx.kind == "reviewer" else None,
        "request_id": ctx.request_id if ctx.kind == "reviewer" else None,
        "mode": ctx.mode,
        "kind": action.kind,
        "inputs": inputs,
        "evidence_ref": action.evidence_ref,
        "destination": action.destination,
        "target": target,
        "claims": [
            {k: c[k] for k in ("claim_kind", "text", "passed", "detail", "failed_policies")} for c in claims
        ],
        "retrieval": action.retrieval if action.is_report_level else None,
        "memories_used": list(action.memories_used) if action.is_report_level else [],
        "checks": checks,
        "failed_check": failed_check,
        "grant_id": (grant or {}).get("grant_id", ctx.grant_id),
        "grant_version": (grant or {}).get("version") or ctx.run_grant_version,
        "run_grant_version": ctx.run_grant_version,
        "policy_set_version": policy_set_version,
        "outcome": "blocked" if failed_check else "allowed",
        "action_id": None,
        "seq": None,
        "decided_at": now,
        "authorised_by": authorised_by(ctx, grant, policy_set_version),
    }
    if ctx.origin:
        doc["origin"] = ctx.origin
    return doc


def build_action(ctx: GateCtx, action: GateAction, decision: dict[str, Any], action_id: str, now: datetime) -> dict[str, Any]:
    """The ``actions`` document, ``queued``, pointing back to its decision (AD-14, AD-20)."""
    return {
        "_id": action_id,
        "decision_id": decision["_id"],
        "admission_id": ctx.admission_id if ctx.kind == "run" else None,
        "run_id": ctx.run_id,
        "mode": ctx.mode,
        "kind": action.kind,
        "destination": action.destination,
        "target": decision["target"],
        "inputs": decision["inputs"],
        "evidence_ref": action.evidence_ref,
        "stamp": ctx.stamp,
        "error": None,
        "status": "queued",
        "result": None,
        "resolution": None,
        "proposed_at": now,
        "decided_at": now,
        "claimed_at": None,
        "observed_at": None,
        "authorised_by": decision["authorised_by"],
    }


def _is_dup(exc: BaseException) -> bool:
    try:
        from pymongo.errors import DuplicateKeyError
    except ImportError:  # pragma: no cover - pymongo is a project dependency
        DuplicateKeyError = ()  # type: ignore[assignment]
    return isinstance(exc, DuplicateKeyError) or type(exc).__name__ == "DuplicateKeyError"


async def insert_if_absent(coll: Any, doc: dict[str, Any], *, session: Any = None) -> tuple[dict[str, Any], bool]:
    """Insert ``doc``; on a duplicate key return the stored one. ``(doc, inserted)``."""
    try:
        await coll.insert_one(doc, session=session)
        return doc, True
    except Exception as exc:  # noqa: BLE001 - narrowed by _is_dup
        if not _is_dup(exc):
            raise
        stored = await coll.find_one({"_id": doc["_id"]}, session=session)
        return stored, False


async def record(
    ctx: GateCtx,
    action: GateAction,
    decision_doc: dict[str, Any],
    action_id: str,
) -> dict[str, Any]:
    """Persist one evaluation: decision, then (allowed) action, then the event and ``seq``.

    Safe to repeat: every write is insert-if-absent or conditional, and the
    event is deduplicated on the decision ID.
    """
    db = deps.db()
    s = ctx.session
    decision, _ = await insert_if_absent(db["decisions"], decision_doc, session=s)
    allowed = decision["outcome"] == "allowed"

    if allowed:
        act, _ = await insert_if_absent(
            db["actions"], build_action(ctx, action, decision, action_id, decision["decided_at"]), session=s
        )
        if decision.get("action_id") is None:
            await db["decisions"].update_one(
                {"_id": decision["_id"], "action_id": None}, {"$set": {"action_id": act["_id"]}}, session=s
            )
            decision["action_id"] = act["_id"]

    if decision.get("seq") is None:
        event_type = "action_allowed" if allowed else "action_blocked"
        seq = await deps.emit_event(
            {
                "type": event_type,
                "dedupe_key": f"{event_type}|{decision['_id']}",
                "mode": decision.get("mode", ctx.mode),
                "run_id": decision["run_id"],
                "stamp": decision["stamp"],
                "decision_id": decision["_id"],
                "action_id": decision.get("action_id"),
                "outcome": decision["outcome"],
                "failed_check": decision.get("failed_check"),
                "diagnostic_id": decision["target"].get("diagnostic_id"),
                "proposal_id": decision["target"].get("proposal_id"),
                "report_id": decision["target"].get("report_id"),
                "memory_id": decision["target"].get("memory_id"),
                "task_id": decision["target"].get("task_id"),
            },
            session=s,
        )
        await db["decisions"].update_one(
            {"_id": decision["_id"], "seq": None}, {"$set": {"seq": seq}}, session=s
        )
        decision["seq"] = seq
    return decision


async def get(decision_id: str, *, session: Any = None) -> dict[str, Any] | None:
    """Read one decision, for ``GET /decisions/<decision_id>`` (A07+A11) and the audit."""
    return await deps.db()["decisions"].find_one({"_id": decision_id}, session=session)


def api_decision(doc: dict[str, Any]) -> Any:
    """The stored decision as ``api.models.Decision`` (``_id`` mapped to ``id``)."""
    from dxp.api.models import Decision

    return Decision.model_validate(to_api(doc))


__all__: list[str] = [
    "api_decision",
    "as_doc",
    "to_api",
    "authorised_by",
    "build_action",
    "build_decision",
    "deps",
    "get",
    "ids_for",
    "insert_if_absent",
    "record",
    "target_key",
]
