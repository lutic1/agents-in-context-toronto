"""A10 fixtures: a fake world for every module the run calls (Story 1.7).

Each frozen signature the run calls is replaced here by a fake that behaves like the module on
main: admissions with main's `dxp/runs/admissions.py` semantics (#30): the ID is
`derive("adm_", run_id, item_key)`, a repeat of an item_key returns the same admission while it
is still `admitted` and None once it has been released, and a new one is guarded on the run's
status (A07+A11); a gate that blocks an unsupported "showed" claim on a trial without
results and a link to an out-of-scope Diagnostic (A06 inside A19+A20's `reports.file`), and a
notifier that records one Slack post (A09). I1 proves the real modules.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from dxp.api.models import Principal, RunContext, Stamp
from tests.a10.fakedb import FakeDB

RUN_ID = "run_test0001"
SCOPE_ID = "scope_plasma_ctdna_nsclc"
TEAM_ID = "team_lbdx"
ANCHOR = "clinicaltrials.gov:NCT04712877"
SECOND = "clinicaltrials.gov:NCT00000002"
OUT_OF_SCOPE_DX = "dx_f1cdx_tissue"


def version_id_for(ref: str, n: int = 1) -> str:
    return f"sv_{ref.split(':')[-1].lower()}_{n}"


@dataclass
class World:
    db: FakeDB
    run_set: str = "discover"
    scan_refs: list[str] = field(default_factory=lambda: [ANCHOR])
    scan_error: Exception | None = None
    calls: list[tuple[str, Any]] = field(default_factory=list)
    admitted: dict[str, str] = field(default_factory=dict)  # admission_id -> item_key
    releases: Counter = field(default_factory=Counter)
    refused: list[str] = field(default_factory=list)
    repeats: list[str] = field(default_factory=list)  # item_keys refused because already released
    draft1_text: str = "The study showed blood profiling detecting actionable drivers."
    draft2_text: str = "This study is recruiting; no results posted."
    redraft_text: str | None = None  # draft 2's headline on the redraft (attempt 1)
    link_dx: str = OUT_OF_SCOPE_DX  # the Diagnostic the record's mention resolves to
    extract_fail: set[str] = field(default_factory=set)
    with_memories: bool = True
    slack: list[dict[str, Any]] = field(default_factory=list)
    media: list[str] = field(default_factory=list)
    stop_after: str | None = None  # stop the run once this ref is done
    decisions: list[dict[str, Any]] = field(default_factory=list)

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]

    def args(self, name: str) -> list[Any]:
        return [a for n, a in self.calls if n == name]

    @property
    def run(self) -> dict[str, Any]:
        return self.db["runs"].docs[RUN_ID]


def add_source(db: FakeDB, ref: str, *, has_results: bool = False, processed: bool = False) -> None:
    vid = version_id_for(ref)
    item = {"_id": ref, "current_version_id": vid, "window": "discovered", "scope_ids": [SCOPE_ID]}
    if processed:
        item["processed"] = {SCOPE_ID: {vid: datetime(2026, 11, 14, 10, 0, tzinfo=UTC)}}
    db["source_items"].docs[ref] = item
    db["source_versions"].docs[vid] = {
        "_id": vid, "source_ref": ref, "raw_text": "record text", "evidence_text": f"evidence of {ref}",
        "overall_status": "RECRUITING", "has_results": has_results,
    }


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> World:
    import dxp.actions
    import dxp.briefing
    import dxp.discovery
    import dxp.ledger
    import dxp.llm
    import dxp.memory
    import dxp.reports
    import dxp.retrieval
    import dxp.runs
    import dxp.store
    import dxp.tasks

    db = FakeDB()
    w = World(db=db)
    db["runs"].docs[RUN_ID] = {"_id": RUN_ID, "status": "running", "set": "discover", "kind": "discover",
                               "scope_id": SCOPE_ID, "team_id": TEAM_ID, "agent": "dxp-curator", "counts": {}}
    db["aliases"].docs["foundationone cdx"] = {"_id": "foundationone cdx", "name": "FoundationOne CDx",
                                               "diagnostic_id": OUT_OF_SCOPE_DX, "created_mode": "baseline"}
    db["aliases"].docs["guardant360 cdx"] = {"_id": "guardant360 cdx", "diagnostic_id": "dx_g360", "created_mode": "baseline"}
    db["aliases"].docs["made up"] = {"_id": "made up", "diagnostic_id": "dx_x", "created_mode": "live"}
    add_source(db, ANCHOR)
    add_source(db, SECOND)
    db["source_versions"].docs["sv_prior"] = {"_id": "sv_prior", "source_ref": "clinicaltrials.gov:NCT0PRIOR", "raw_text": "prior"}

    events: list[dict[str, Any]] = []

    async def emit_event(event: dict[str, Any], **_: Any) -> int:
        events.append(event)
        return len(events)

    monkeypatch.setattr(dxp.store, "db", lambda: db)
    monkeypatch.setattr(dxp.store, "emit_event", emit_event)
    w.events = events  # type: ignore[attr-defined]

    def log(name: str, value: Any = None) -> None:
        w.calls.append((name, value))

    # --- runs (A07+A11) -------------------------------------------------
    async def context(run_id: str, key: str) -> RunContext:
        log("runs.context", (run_id, key))
        stamp = Stamp(kind="run", run_id=run_id, agent="dxp-curator", initiated_by="sam", principal="dxp-curator",
                      grant_id="lbdx", grant_version=1, policy_set_version="ps_0000000000000001")
        return RunContext(run_id=run_id, principal=Principal(id="dxp-curator", name="dxp-curator", kind="agent"),
                          stamp=stamp, grant_id="lbdx", grant_version=1, policy_set_version="ps_0000000000000001")

    from dxp.runs.admissions import admission_id as derive_admission_id

    async def admit(run_id: str, item_key: str) -> dict[str, Any] | None:
        # main's runs.admit (#30): derived ID; a repeat returns the admission only while it is
        # still admitted, and None once it was released (no not_admitted count, like main).
        log("runs.admit", item_key)
        adm = derive_admission_id(run_id, item_key)
        if adm in w.admitted:
            if w.releases[adm] == 0:
                return {"id": adm, "run_id": run_id, "item_key": item_key, "status": "admitted"}
            w.repeats.append(item_key)
            return None
        run = db["runs"].docs[run_id]
        if run["status"] != "running":
            w.refused.append(item_key)
            run["counts"]["not_admitted"] = run["counts"].get("not_admitted", 0) + 1
            return None
        w.admitted[adm] = item_key
        return {"id": adm, "run_id": run_id, "item_key": item_key, "status": "admitted"}

    async def release(admission_id: str) -> None:
        log("runs.release", admission_id)
        w.releases[admission_id] += 1

    def held() -> int:
        return sum(1 for a in w.admitted if w.releases[a] == 0)

    async def finish(run_id: str) -> None:
        log("runs.finish", run_id)
        run = db["runs"].docs[run_id]
        if run["status"] == "running" and held() == 0:
            run["status"] = "done"

    async def settle(run_id: str) -> None:
        log("runs.settle", run_id)
        run = db["runs"].docs[run_id]
        if run["status"] == "stopping" and held() == 0:
            run["status"] = "stopped"

    # A07+A11's progress functions (PR #30, head c6a31f1), with the same types and returns.
    from dxp.api.models import Run, RunCounts

    async def record_progress(run_id: str, *, counts: dict[str, int], active_items: list[dict[str, str]],
                              failure_lines: list[dict[str, str]]) -> bool:
        log("runs.record_progress", run_id)
        bad = [k for k in counts if k == "not_admitted" or k not in RunCounts.model_fields]
        if bad:
            raise ValueError(f"counts keys not allowed: {bad}")
        run = db["runs"].docs[run_id]
        if run["status"] in ("done", "stopped", "failed"):
            return False
        run.setdefault("counts", {}).update(counts)
        run["active"] = list(active_items)
        run["failures"] = list(failure_lines)
        return True

    async def fail(run_id: str, error: str) -> Run:
        log("runs.fail", (run_id, error))
        run = db["runs"].docs[run_id]
        if run["status"] in ("running", "stopping"):
            run["status"] = "failed"
            run["error"] = error
            run.setdefault("failures", []).append({"source_ref": "-", "error": error})
        return Run(id=run_id, agent="dxp-curator", initiated_by="sam", grant_id="lbdx", grant_version=1,
                   set=run["set"], kind=run.get("kind", "discover"), status=run["status"])

    for name, fn in {"context": context, "admit": admit, "release": release, "finish": finish, "settle": settle,
                     "record_progress": record_progress, "fail": fail}.items():
        monkeypatch.setattr(dxp.runs, name, fn, raising=False)

    async def recover_applying() -> None:
        log("ledger.recover_applying")

    monkeypatch.setattr(dxp.ledger, "recover_applying", recover_applying)

    # --- discovery (A05) ------------------------------------------------
    async def scan(scope_id: str, ctx: RunContext) -> list[str]:
        log("discovery.scan", scope_id)
        if w.scan_error:
            raise w.scan_error
        return list(w.scan_refs)

    monkeypatch.setattr(dxp.discovery, "scan", scan)

    # --- llm (A08) ------------------------------------------------------
    async def extract(item: dict[str, Any], aliases: list[str] | None = None) -> dict[str, Any]:
        log("llm.extract", {"item": item, "aliases": aliases})
        ref = item["source_ref"]
        if ref in w.extract_fail:
            raise RuntimeError("model down")
        vid = item["version_id"]
        return {
            "status": "extracted", "source_ref": ref, "version_id": vid,
            "findings": [
                {"id": f"f_{vid}_record", "source_ref": ref, "version_id": vid, "diagnostic_id": None,
                 "summary": "molecular profiling using blood and tumour tissue", "values": []},
                {"id": f"f_{vid}_f1cdx", "source_ref": ref, "version_id": vid, "diagnostic_id": OUT_OF_SCOPE_DX,
                 "summary": "the record names FoundationOne CDx", "values": []},
            ],
            "unresolved_names": ["FoundationOne Liquid"],
        }

    async def check(finding: dict[str, Any], source_text: str) -> dict[str, Any]:
        log("llm.check", finding["id"])
        return {**finding, "checked": True}

    monkeypatch.setattr(dxp.llm, "extract", extract)
    monkeypatch.setattr(dxp.llm, "check", check)

    # --- retrieval, memory, relate, draft (A19+A20, A21+A22) ------------
    async def related(scope_id: str, text: str, k: int, exclude: list[str] | None = None) -> dict[str, Any]:
        log("retrieval.related", {"scope_id": scope_id, "k": k, "exclude": exclude})
        return {"method": "vector_search", "index": "vs_source_items", "top_k": k,
                "items": [{"ref": "clinicaltrials.gov:NCT0PRIOR", "version_id": "sv_prior", "score": 0.81}]}

    async def retrieve(team_id: str, text: str, tags: dict[str, Any] | None) -> tuple[list[Any], dict[str, Any]]:
        log("memory.retrieve", {"team_id": team_id, "tags": tags})
        mems = [{"id": "mem_m1", "version": 1, "team_id": team_id, "author": "sam", "text": "describe status"}]
        return (mems if w.with_memories else []), {"method": "vector_search", "top_k": 3, "items": []}

    async def relate(new_item: dict[str, Any], related_item: dict[str, Any]) -> dict[str, Any]:
        log("reports.relate", {"new": new_item, "related": related_item})
        return {"id": "rel_1", "related_ref": related_item["ref"], "label": "extends",
                "new_quote": {"version_id": new_item["version_id"]},
                "related_quote": {"version_id": related_item["version_id"]}, "similarity": related_item["score"]}

    # A19+A20's agreed contract (#19 at fee345d, #38 on main): reports.draft returns the final
    # draft at the top level and `drafts`, each self-contained; `updates` [{finding_id, change}]
    # only on the final draft, memories_used only on a draft after draft 1.
    async def draft(item: dict[str, Any], findings: list[Any], related_: list[Any], memories: list[Any]) -> dict[str, Any]:
        log("reports.draft", {"item": item, "findings": findings, "related": related_, "memories": memories})
        attempt = int(item.get("attempt") or 0)
        second = w.redraft_text if attempt and w.redraft_text else w.draft2_text
        contents = [{"draft": 1, "headline": w.draft1_text}]
        if memories:
            contents.append({"draft": 2, "headline": second})
        shared = {"attempt": attempt, "run_id": item["run_id"], "scope_id": item["scope_id"], "team_id": item.get("team_id"),
                  "source_ref": item["source_ref"], "version_id": item["version_id"]}
        updates = [
            {"finding_id": f"f_{item['version_id']}_record", "change": {
                "field": "evidence_collection", "value": item["source_ref"], "diagnostic_id": None, "scope_id": SCOPE_ID}},
            {"finding_id": f"f_{item['version_id']}_f1cdx", "change": {
                "field": "trials", "value": "NCT04712877", "diagnostic_id": w.link_dx,
                "mention": {"name": "FoundationOne CDx", "field": "otherNames"}}},
        ]
        drafts = []
        for index, one in enumerate(contents):
            is_final = index == len(contents) - 1
            out = {**shared, **one,
                   "memories_used": [{"memory_id": "mem_m1", "effect": {"before": "a", "after": "b"}}]
                   if is_final and one["draft"] > 1 else []}
            if is_final:
                out["updates"] = updates
            drafts.append(out)
        return {**drafts[-1], "drafts": drafts}

    def decide(ctx: RunContext, kind: str, target: str, blocked: str | None) -> dict[str, Any]:
        adm = ctx.admission_id
        assert adm in w.admitted and w.releases[adm] == 0, "check 5: no admission held"
        dec = {"_id": f"dec_{len(w.decisions):04d}", "id": f"dec_{len(w.decisions):04d}", "run_id": ctx.run_id,
               "kind": kind, "target": target, "outcome": "blocked" if blocked else "allowed",
               "failed_check": blocked, "admission_id": adm}
        w.decisions.append(dec)
        db["decisions"].docs[dec["_id"]] = dec
        return dec

    async def file(d: dict[str, Any], ctx: RunContext, final: bool = True) -> dict[str, Any]:
        # #19's _check_shape: one draft per call; a non-final draft carries no updates.
        if len(d.get("drafts") or []) > 1:
            raise ValueError("reports.file takes one draft per call")
        if not final and d.get("updates"):
            raise ValueError("a non-final draft carries no updates")
        log("reports.file", {**d, "final": final, "admission_id": ctx.admission_id})
        from dxp import identity
        report_id = identity.derive("rep_", ctx.run_id, d["source_ref"])
        suffix = f".r{d['attempt']}" if d.get("attempt") else ""
        blocked = "showed" in d.get("headline", "")
        dec = decide(ctx, "file_proposal", f"{report_id}|draft{d['draft']}{suffix}",
                     "evidence_checks:claim_performed_or_results" if blocked else None)
        if not final or dec["outcome"] != "allowed":
            return dec  # gate only, or blocked: nothing written
        db["reports"].docs[report_id] = {"_id": report_id, "run_id": ctx.run_id, "version_id": d["version_id"],
                                         "status": "pending", "draft": d["draft"], "diagnostic_ids": [],
                                         "memories_used": d.get("memories_used"), "script_hash": "h",
                                         "blocked_draft_decision_id": d.get("blocked_draft_decision_id")}
        for update in d.get("updates") or []:
            change = {**update["change"], "report_id": report_id}  # keeps the caller's admission_id (D22)
            change_ctx = ctx.model_copy(update={"admission_id": change.get("admission_id")})
            out_of_scope = change.get("diagnostic_id") == OUT_OF_SCOPE_DX
            cdec = decide(change_ctx, "file_proposal", change["field"], "team_scope" if out_of_scope else None)
            if not out_of_scope:
                pid = f"p_{len(db['proposals'].docs)}"
                db["proposals"].docs[pid] = {"_id": pid, "run_id": ctx.run_id, "report_id": report_id,
                                             "version_id": d["version_id"], "decision_id": cdec["id"],
                                             "diagnostic_id": change.get("diagnostic_id")}
        db["reports"].docs[report_id]["diagnostic_ids"] = sorted(
            {p["diagnostic_id"] for p in db["proposals"].docs.values() if p["report_id"] == report_id and p["diagnostic_id"]})
        return dec  # never creates or sends notify_slack (#38)

    async def dispatch(action: Any, ctx: RunContext) -> dict[str, Any]:
        log("actions.dispatch", action)
        dec = decide(ctx, action.kind, action.target.report_id, None)
        w.slack.append({"report_id": action.target.report_id, "action": action, "admission_id": ctx.admission_id})
        act = {"_id": f"act_{len(w.slack)}", "run_id": ctx.run_id, "kind": "notify_slack", "status": "delivered",
               "decision_id": dec["id"], "target": {"report_id": action.target.report_id}}
        db["actions"].docs[act["_id"]] = act
        return act

    monkeypatch.setattr(dxp.retrieval, "related", related)
    monkeypatch.setattr(dxp.memory, "retrieve", retrieve)
    monkeypatch.setattr(dxp.reports, "relate", relate)
    monkeypatch.setattr(dxp.reports, "draft", draft)
    monkeypatch.setattr(dxp.reports, "file", file)
    monkeypatch.setattr(dxp.actions, "dispatch", dispatch)

    # --- media must never be called by the run (V29) --------------------
    async def no_media(*args: Any, **kwargs: Any) -> None:
        w.media.append("called")
        raise AssertionError("the run called a media function")

    for name in ("generate", "render_avatar", "avatar_status"):
        monkeypatch.setattr(dxp.briefing, name, no_media)

    # --- tasks (A24, A25) -------------------------------------------------
    async def recover_authorisations() -> None:
        log("tasks.recover_authorisations")

    async def dispatch_next(start: Any) -> None:
        log("tasks.dispatch_next", start)

    async def task_run(task_id: str) -> dict[str, Any]:
        log("tasks.run", task_id)
        return {"id": task_id, "status": "done"}

    monkeypatch.setattr(dxp.tasks, "recover_authorisations", recover_authorisations)
    monkeypatch.setattr(dxp.tasks, "dispatch_next", dispatch_next)
    monkeypatch.setattr(dxp.tasks, "run", task_run)

    # Stop the run after a given item, as POST /runs/<run_id>/stop would.
    from dxp.pipeline import progress

    original_done = progress.Progress.item_done

    async def item_done(self: Any, source_ref: str, **kw: Any) -> None:
        await original_done(self, source_ref, **kw)
        if w.stop_after == source_ref and w.run["status"] == "running":
            w.run["status"] = "stopping"

    monkeypatch.setattr(progress.Progress, "item_done", item_done)
    monkeypatch.setattr("dxp.pipeline.config.pace_seconds", lambda: None)
    return w
