"""A10 fixtures: a fake world for every module the run calls (Story 1.7).

Nothing the run calls is merged yet except A01's stubs, so each frozen signature is replaced
here by a fake that behaves like its card says: admissions guarded on the run's status and
released once (A07+A11), a gate that blocks an unsupported "showed" claim on a trial without
results and a link to an out-of-scope Diagnostic (A06 inside A19+A20's `reports.file`), and a
notifier that records one Slack post (A09). I1 proves the real modules.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
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
SCOPE_UPDATE = {"finding_id": "f_record", "field": "evidence_collection", "value": ANCHOR, "diagnostic_id": None, "scope_id": SCOPE_ID}
MENTION_LINK = {"finding_id": "f_f1cdx", "field": "scope_link", "value": SCOPE_ID, "diagnostic_id": OUT_OF_SCOPE_DX,
                "mention": "FoundationOne CDx"}


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
    draft1_text: str = "The study showed blood profiling detecting actionable drivers."
    draft2_text: str = "This study is recruiting; no results posted."
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
        item["processed"] = {SCOPE_ID: {vid: {"run_id": "run_old"}}}
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

    async def admit(run_id: str, item_key: str) -> dict[str, Any] | None:
        log("runs.admit", item_key)
        run = db["runs"].docs[run_id]
        if run["status"] != "running":
            w.refused.append(item_key)
            run["counts"]["not_admitted"] = run["counts"].get("not_admitted", 0) + 1
            return None
        adm = f"adm_{len(w.admitted):04d}"
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

    # A07+A11's progress functions (not on main yet): merge counts, replace active and failures.
    async def record_progress(run_id: str, *, counts: dict[str, int], active_items: list[Any],
                              failure_lines: list[Any]) -> None:
        log("runs.record_progress", run_id)
        assert "not_admitted" not in counts, "not_admitted belongs to runs.admit"
        run = db["runs"].docs[run_id]
        run.setdefault("counts", {}).update(counts)
        run["active"] = list(active_items)
        run["failures"] = list(failure_lines)

    async def fail(run_id: str, error: str) -> None:
        log("runs.fail", (run_id, error))
        run = db["runs"].docs[run_id]
        if run["status"] in ("running", "stopping"):
            run["status"] = "failed"
            run["error"] = error

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

    async def draft(item: dict[str, Any], findings: list[Any], related_: list[Any], memories: list[Any]) -> dict[str, Any]:
        log("reports.draft", {"item": item, "findings": findings, "related": related_, "memories": memories})
        base = {"report_id": item["report_id"], "version_id": item["version_id"], "diagnostic_ids": [],
                "updates": [dict(SCOPE_UPDATE, value=item["source_ref"]), dict(MENTION_LINK)]}
        return {"drafts": [{**base, "draft": 1, "headline": w.draft1_text},
                           {**base, "draft": 2, "headline": w.draft2_text, "memories_used": memories}]}

    def decide(ctx: RunContext, kind: str, target: str, blocked: str | None) -> dict[str, Any]:
        assert ctx.admission_id in w.admitted and w.releases[ctx.admission_id] == 0, "check 5: no admission held"
        dec = {"_id": f"dec_{len(w.decisions):04d}", "id": f"dec_{len(w.decisions):04d}", "run_id": ctx.run_id,
               "kind": kind, "target": target, "outcome": "blocked" if blocked else "allowed",
               "failed_check": blocked, "admission_id": ctx.admission_id}
        w.decisions.append(dec)
        db["decisions"].docs[dec["_id"]] = dec
        return dec

    async def file(d: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        log("reports.file", d)
        report_id = d["report_id"]
        claim_blocked = "showed" in d.get("headline", "")
        dec = decide(ctx, "file_proposal", f"{report_id}|draft{d['draft']}",
                     "evidence_checks:claim_performed_or_results" if claim_blocked else None)
        if claim_blocked or d["draft"] != 2:
            return dec  # draft 1 is only evaluated; draft 2 is the one filed (V21)
        db["reports"].docs[report_id] = {"_id": report_id, "run_id": ctx.run_id, "version_id": d["version_id"],
                                         "status": "pending", "draft": d["draft"],
                                         "blocked_draft_decision_id": d.get("blocked_draft_decision_id")}
        for change in d.get("updates") or []:
            change_ctx = ctx.model_copy(update={"admission_id": change["admission_id"]})
            out_of_scope = change.get("diagnostic_id") == OUT_OF_SCOPE_DX
            cdec = decide(change_ctx, "file_proposal", change["field"], "team_scope" if out_of_scope else None)
            if not out_of_scope:
                pid = f"p_{len(db['proposals'].docs)}"
                db["proposals"].docs[pid] = {"_id": pid, "run_id": ctx.run_id, "report_id": report_id,
                                             "version_id": d["version_id"], "decision_id": cdec["id"]}
        return dec

    async def dispatch(action: Any, ctx: RunContext) -> dict[str, Any]:
        log("actions.dispatch", action)
        dec = decide(ctx, action.kind, action.target.report_id, None)
        w.slack.append({"report_id": action.target.report_id, "action": action})
        act = {"_id": f"act_{len(w.slack)}", "run_id": ctx.run_id, "kind": "notify_slack", "status": "delivered",
               "decision_id": dec["id"]}
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
    import dxp.pipeline.progress as progress

    original_done = progress.Progress.item_done

    async def item_done(self: Any, source_ref: str, **kw: Any) -> None:
        await original_done(self, source_ref, **kw)
        if w.stop_after == source_ref and w.run["status"] == "running":
            w.run["status"] = "stopping"

    monkeypatch.setattr(progress.Progress, "item_done", item_done)
    monkeypatch.setattr("dxp.pipeline.config.pace_seconds", lambda: None)
    return w
