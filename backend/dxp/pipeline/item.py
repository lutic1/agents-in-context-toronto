"""One Source item through the run (Story 1.7, AD-12, V21, V40): extract, check, retrieve,
remember, relate, draft, gate, file, notify.

Rules kept here:
- The item's `version_id` is read once, from the Source item's current pointer, and pinned:
  it goes into the extraction input, every Finding, the retrieval exclusion, the new side of
  every relationship, both drafts, the report and the alert's evidence reference (V40).
- One admission per action (D22), taken after extraction and before the gate, with
  `item_key = "<source_ref>|<kind>|<diagnostic_id or '-'>|<target>"`; every admission is
  released once, in a `finally`, whatever the action's outcome. A refused admission means
  that action is not attempted (`runs.admit` counts it).
- Two gated drafts (V21): draft 1 without memories, draft 2 with them, each a report-level
  `file_proposal` through `reports.file()` (targets `"<report_id>|draft1"` and `|draft2`),
  each its own Decision. Draft 2 is the one filed; a blocked draft 2 ends the item with
  nothing filed. A blocked draft 1 is the "blocked claim"; draft 2 is its one redraft.
- One `notify_slack` per filed report, through `actions.dispatch()` (V11). A blocked report
  gets no alert. A blocked alert (A09 raises `ActionBlocked`) is a blocked step, not an item
  failure. The run never calls ElevenLabs or HeyGen (V29).
- The node never raises: an error becomes a failure line with a code, never source text.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from dxp import actions, identity, llm, memory, reports, retrieval, runs
from dxp.api.models import EvidenceRef, ProposedAction, RunContext, Target
from dxp.pipeline import config, progress

log = logging.getLogger("dxp.pipeline")

NO_RESULTS_CLAIM_KIND = "outcome_claim_without_results"


@dataclass
class RunInfo:
    """What every item of one run shares."""

    run_id: str
    ctx: RunContext
    scope_id: str | None
    team_id: str | None
    seeded_names: list[str]
    tracker: progress.Progress


@dataclass
class ItemResult:
    source_ref: str
    status: str  # done | failed | skipped | not_started
    version_id: str | None = None
    report_id: str | None = None
    filed: bool = False
    draft_decisions: list[Any] = field(default_factory=list)
    alert: Any = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "status": self.status,
            "version_id": self.version_id,
            "report_id": self.report_id,
            "filed": self.filed,
            "error": self.error,
        }


class ItemFailed(Exception):
    """An item failure with a code; its message never holds source text."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


# ---------------------------------------------------------------------------
# Small helpers: other PRs may return pydantic models or plain dicts
# ---------------------------------------------------------------------------


def get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def plain(obj: Any) -> Any:
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        return dump()
    return obj


def outcome(decision: Any) -> str | None:
    return get(decision, "outcome")


def admission_id(admission: Any) -> str | None:
    if admission is None:
        return None
    if isinstance(admission, str):
        return admission
    return get(admission, "id") or get(admission, "_id")


def item_key(source_ref: str, kind: str, diagnostic_id: str | None, target: str) -> str:
    return f"{source_ref}|{kind}|{diagnostic_id or '-'}|{target}"


async def admit(run_id: str, key: str) -> str | None:
    return admission_id(await runs.admit(run_id, key))


async def release(admission_ids: list[str]) -> None:
    for adm in admission_ids:
        try:
            await runs.release(adm)
        except Exception as exc:  # noqa: BLE001 - one failed release must not skip the others
            log.warning("release failed admission=%s error=%s", adm, type(exc).__name__)


def with_admission(ctx: RunContext, adm: str) -> RunContext:
    return ctx.model_copy(update={"admission_id": adm})


def is_action_blocked(exc: BaseException) -> bool:
    """A09's `actions.dispatch` raises `ActionBlocked` when the gate blocks the action. Matched
    by name so this module does not depend on A09 being merged."""
    blocked = getattr(actions, "ActionBlocked", None)
    if isinstance(blocked, type) and isinstance(exc, blocked):
        return True
    return type(exc).__name__ == "ActionBlocked"


def report_id_for(run_id: str, source_ref: str) -> str:
    return identity.derive("rep_", run_id, source_ref)


def split_drafts(drafted: Any) -> list[dict[str, Any]]:
    """`reports.draft()` writes draft 1 (no memories) and draft 2 (with memories), V21.
    Accepts `{ drafts: [d1, d2] }`, `{ draft1, draft2 }` or a single draft."""
    drafted = plain(drafted)
    if not isinstance(drafted, dict):
        raise ItemFailed("draft_shape")
    if isinstance(drafted.get("drafts"), list) and drafted["drafts"]:
        out = [dict(plain(d)) for d in drafted["drafts"]]
    elif isinstance(drafted.get("draft1"), dict) or isinstance(drafted.get("draft2"), dict):
        out = [dict(plain(drafted[k])) for k in ("draft1", "draft2") if isinstance(drafted.get(k), dict)]
    else:
        out = [dict(drafted)]
    for n, d in enumerate(out, start=1):
        d.setdefault("draft", n)
    return out


def change_target(change: dict[str, Any]) -> str:
    """AD-3 target of a per-change file_proposal: the proposal ID, else "<field>|<value>"."""
    if change.get("proposal_id"):
        return str(change["proposal_id"])
    finding_id, fld, value = change.get("finding_id"), change.get("field"), change.get("value")
    if finding_id and fld is not None and value is not None:
        return identity.derive("p_", str(finding_id), str(fld), str(value))
    return f"{fld}|{value}"


def memory_tags(item: dict[str, Any]) -> dict[str, Any] | None:
    """Memories are matched on claim kind, never assay (V22). A record without posted results
    asks for the memories about outcome claims without results (M1 on the demo path)."""
    if item.get("has_results") is True:
        return None
    return {"claim_kind": NO_RESULTS_CLAIM_KIND}


def is_early_research(findings: list[dict[str, Any]]) -> bool:
    try:
        from dxp.schema.registry import is_early_research as early
    except ImportError:  # pragma: no cover - A02 is on main
        return False
    for f in findings:
        stage = get(get(f, "stage_evidence"), "stage")
        if stage and early(stage):
            return True
    return False


# ---------------------------------------------------------------------------
# The steps
# ---------------------------------------------------------------------------


async def load(source_ref: str, info: RunInfo) -> tuple[dict[str, Any], str] | None:
    """The item dict for extraction and its pinned version ID; None when already processed."""
    src, version = await progress.load_source(source_ref)
    if src is None:
        raise ItemFailed("source_item_missing")
    if version is None:
        raise ItemFailed("source_version_missing")
    version_id = version["_id"]
    if progress.processed(src, info.scope_id, version_id):
        return None
    item = {k: v for k, v in src.items() if k not in ("_id", "processed", "embedding")}
    item.update({k: v for k, v in version.items() if k not in ("_id", "embedding")})
    item.update({"source_ref": source_ref, "version_id": version_id})
    return item, version_id


async def extract(item: dict[str, Any], info: RunInfo) -> list[dict[str, Any]] | None:
    """`llm.extract` then `llm.check` on each Finding. None: not relevant (done, nothing filed)."""
    extraction = plain(await llm.extract(item, info.seeded_names))
    status = get(extraction, "status", "extracted")
    if status == "not_relevant":
        return None
    if status == "failed":
        codes = [get(f, "code") for f in get(extraction, "failures") or [] if get(f, "code")]
        raise ItemFailed("extract_failed" + (f":{codes[0]}" if codes else ""))
    item["extraction"] = {
        k: extraction.get(k)
        for k in ("mentions", "unresolved_names", "intervention_texts", "nct_id")
        if isinstance(extraction, dict) and k in extraction
    }
    source_text = item.get("raw_text") or item.get("evidence_text") or ""
    findings: list[dict[str, Any]] = []
    for raw in get(extraction, "findings") or []:
        finding = dict(plain(raw))
        checked = plain(await llm.check(finding, source_text))
        if isinstance(checked, dict) and checked:
            finding = {**finding, **checked}
        # V40: a Finding is pinned to the version the item read.
        if finding.get("version_id") not in (None, item["version_id"]):
            raise ItemFailed("finding_version_mismatch")
        finding["version_id"] = item["version_id"]
        finding.setdefault("source_ref", item["source_ref"])
        findings.append(finding)
    return findings


def discovery_text(item: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    text = item.get("evidence_text")
    if text:
        return str(text)
    summaries = [str(f.get("summary")) for f in findings if f.get("summary")]
    return " ".join(summaries) or str(item.get("title") or item.get("source_ref"))


async def related_items(retrieved: Any) -> list[dict[str, Any]]:
    """Load each retrieved item at the version the retrieval pinned (V40)."""
    out: list[dict[str, Any]] = []
    method = get(retrieved, "method")
    for entry in get(retrieved, "items") or []:
        ref, version_id, score = get(entry, "ref"), get(entry, "version_id"), get(entry, "score")
        if not ref:
            continue
        if str(ref).startswith("f_"):
            doc = await progress.load_finding(ref)
            kind = "finding"
        else:
            doc = await progress.load_version(version_id) if version_id else None
            if doc is None:
                src, doc = await progress.load_source(ref)
                version_id = (doc or {}).get("_id")
            kind = "source_item"
        if doc is None:
            continue
        related = {k: v for k, v in doc.items() if k not in ("_id", "embedding")}
        related.update(
            {"ref": ref, "related_kind": kind, "version_id": version_id or related.get("version_id"),
             "score": score, "retrieval_method": method}
        )
        if kind == "source_item":
            related.setdefault("source_ref", ref)
        out.append(related)
    return out


async def relate_all(new_item: dict[str, Any], related: list[dict[str, Any]]) -> list[Any]:
    """One `reports.relate()` per related item. A failure leaves that item out; it never
    fails the item (Story 10.3: relate itself already turns model errors into
    `related_unestablished`)."""
    out = []
    for other in related:
        try:
            out.append(await reports.relate(new_item, other))
        except Exception as exc:  # noqa: BLE001
            log.warning("relate failed ref=%s error=%s", other.get("ref"), type(exc).__name__)
    return out


async def file_drafts(
    drafts: list[dict[str, Any]], item: dict[str, Any], report_id: str, info: RunInfo, result: ItemResult
) -> dict[str, Any] | None:
    """Gate each draft as the report-level file_proposal; return the filed draft or None."""
    source_ref = item["source_ref"]
    blocked_decision_id: str | None = None
    for index, d in enumerate(drafts):
        final = index == len(drafts) - 1
        n = d.get("draft", index + 1)
        if d.get("version_id") not in (None, item["version_id"]):
            raise ItemFailed("draft_version_mismatch")
        d["version_id"] = item["version_id"]
        d.setdefault("report_id", report_id)
        d.setdefault("source_ref", source_ref)
        d.setdefault("run_id", info.run_id)
        if final and blocked_decision_id:
            d.setdefault("blocked_draft_decision_id", blocked_decision_id)

        held: list[str] = []
        try:
            adm = await admit(info.run_id, item_key(source_ref, "file_proposal", None, f"{report_id}|draft{n}"))
            if adm is None:
                return None  # not admitted: the run is stopping; nothing attempted
            held.append(adm)
            if final:
                # One admission per change (D22); a change not admitted is not attempted.
                admitted_updates = []
                for change in d.get("updates") or []:
                    change = dict(plain(change))
                    key = item_key(source_ref, "file_proposal", change.get("diagnostic_id"), change_target(change))
                    change_adm = await admit(info.run_id, key)
                    if change_adm is None:
                        continue
                    held.append(change_adm)
                    change["admission_id"] = change_adm
                    admitted_updates.append(change)
                if "updates" in d:
                    d["updates"] = admitted_updates
            decision = await reports.file(d, with_admission(info.ctx, adm))
        finally:
            await release(held)
        result.draft_decisions.append(decision)
        if outcome(decision) == "allowed":
            if final:
                return d
        else:
            blocked_decision_id = blocked_decision_id or get(decision, "id")
            if final:
                return None
    return None


async def notify(filed: dict[str, Any], item: dict[str, Any], report_id: str, info: RunInfo) -> Any:
    """The report's one notify_slack (V11), with its own admission. Returns the Action."""
    diagnostic_ids = [d for d in filed.get("diagnostic_ids") or [] if d]
    # Same rule as A09's action ID: the report's first diagnostic_ids entry, else "-" (V43), so
    # the admission key and the action ID line up. The demo report has none.
    dx = diagnostic_ids[0] if diagnostic_ids else None
    adm = await admit(info.run_id, item_key(item["source_ref"], "notify_slack", dx, report_id))
    if adm is None:
        return None
    try:
        action = ProposedAction(
            kind="notify_slack",
            destination=config.SLACK_DESTINATION,
            target=Target(report_id=report_id, diagnostic_id=dx, scope_id=info.scope_id),
            # A06 reads target parts that Target lacks from inputs (source_ref, diagnostic_ids).
            inputs={
                "report_id": report_id,
                "source_ref": item["source_ref"],
                "version_id": item["version_id"],
                "diagnostic_ids": diagnostic_ids,
            },
            evidence_ref=EvidenceRef(source_ref=item["source_ref"], version_id=item["version_id"], report_id=report_id),
        )
        try:
            return await actions.dispatch(action, with_admission(info.ctx, adm))
        except Exception as exc:
            if not is_action_blocked(exc):
                raise
            # The gate blocked the alert: its Decision and action_blocked event are recorded
            # by A09; nothing was sent. A blocked step, not an item failure.
            log.info("alert blocked run=%s report=%s", info.run_id, report_id)
            return {"status": "blocked", "decision_id": get(exc, "decision_id") or get(get(exc, "decision"), "id")}
    finally:
        await release([adm])


async def process(source_ref: str, info: RunInfo) -> ItemResult:
    """Run one item end to end; never raises (except cancellation)."""
    result = ItemResult(source_ref=source_ref, status="failed")
    tracker = info.tracker
    step = "load"
    try:
        status = await progress.run_status(info.run_id)
        if status != "running":
            result.status = "not_started"  # stopped before this item: nothing attempted
            return result
        await tracker.step(source_ref, step)
        loaded = await load(source_ref, info)
        if loaded is None:
            result.status = "skipped"
            await tracker.item_done(source_ref)
            return result
        item, version_id = loaded
        result.version_id = version_id
        report_id = report_id_for(info.run_id, source_ref)
        result.report_id = report_id
        item.update({"run_id": info.run_id, "scope_id": info.scope_id, "team_id": info.team_id, "report_id": report_id})

        step = "extract"
        await tracker.step(source_ref, step)
        findings = await extract(item, info)
        if findings is None:
            result.status = "done"
            await tracker.item_done(source_ref)
            return result
        for f in findings:
            await progress.save_finding(f, info.run_id, info.ctx.stamp)
        early = is_early_research(findings)

        step = "retrieve"
        await tracker.step(source_ref, step)
        text = discovery_text(item, findings)
        retrieved = await retrieval.related(info.scope_id, text, config.RELATED_K, [source_ref])
        item["retrieval"] = plain(retrieved)

        step = "remember"
        await tracker.step(source_ref, step)
        memories: list[Any] = []
        if info.team_id:
            memories, memory_retrieval = await memory.retrieve(info.team_id, text, memory_tags(item))
            item["memory_retrieval"] = plain(memory_retrieval)

        step = "relate"
        await tracker.step(source_ref, step)
        new_item = {**item, "findings": findings}
        relationships = await relate_all(new_item, await related_items(retrieved))

        step = "draft"
        await tracker.step(source_ref, step)
        drafts = split_drafts(await reports.draft(item, findings, relationships, list(memories)))

        step = "file"
        await tracker.step(source_ref, step)
        filed = await file_drafts(drafts, item, report_id, info, result)
        if filed is not None:
            result.filed = True
            await progress.mark_processed(source_ref, info.scope_id, version_id, info.run_id)
            step = "notify"
            await tracker.step(source_ref, step)
            result.alert = await notify(filed, item, report_id, info)

        result.status = "done"
        await tracker.item_done(source_ref, early_research=early)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - each item catches its own error (AD-12)
        code = exc.code if isinstance(exc, ItemFailed) else type(exc).__name__
        result.status = "failed"
        result.error = f"{step}: {code}"
        log.warning("item failed run=%s ref=%s %s", info.run_id, source_ref, result.error)
        try:
            await tracker.item_failed(source_ref, result.error)
        except Exception:  # noqa: BLE001
            log.warning("could not record the failure of %s", source_ref)
    finally:
        try:
            await tracker.recount()
        except Exception:  # noqa: BLE001
            log.warning("could not recount run %s", info.run_id)
    return result
