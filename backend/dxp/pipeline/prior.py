"""python -m dxp.pipeline.prior: the prior collection by NCT ID, filed in baseline mode (A05, Story 1.4, AD-16, AD-25).

Run once in setup (I1 step 1), from a laptop with `DXP_SEED_KEY`, after `python -m dxp.gate.seed`:

1. loads the prior collection through `sources.load.load_prior(scope_id)` (the same code as
   `python -m dxp.sources.load --set prior --scope <scope_id>`): the D30 trials in
   `sources/selected.json` last updated strictly before the scope's cursor, excluding the setup item
   NCT05715229, each fetched by NCT ID and stored as an immutable source version (V40);
2. extracts each loaded version with `llm.extract` and stores its trial-level Finding (insert-if-absent
   on the Finding ID);
3. files that Finding through `ledger.file(finding_id, [change], "baseline", ctx)` under the seed
   grant `seed@v1`, ONLY as an entry in the scope's evidence collection,
   `source_items.collections.<scope_id>` (V54, V35, AD-25). No Diagnostic field value and no
   `lifecycle_stage` is filed from a prior trial (V54, V37: a mention is not proof of use); Diagnostic
   Findings are counted and dropped. It sends no Slack alert and files no pending report.

Running it again changes nothing: versions are insert-if-absent, a version already filed is not
extracted again (`source_items.prior_filed_version_id`), and the ledger's derived IDs make a
repeated filing a no-op. Only NCT IDs, IDs and counts are printed, never record text.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from dxp import ledger, llm, store
from dxp.api import auth
from dxp.api.models import Principal, RunContext, Stamp
from dxp.gate import policy_sets
from dxp.sources import ctgov
from dxp.sources import load as source_load

DEFAULT_SCOPE = "scope_plasma_ctdna_nsclc"
SEED_KEY_ENV = "DXP_SEED_KEY"
SEED_GRANT = "seed"
EVIDENCE_COLLECTION = "evidence_collection"


def _db() -> Any:
    return store.get_db()


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _dump(obj: Any) -> dict[str, Any]:
    dump = getattr(obj, "model_dump", None)
    return dump() if callable(dump) else dict(obj)


async def seed_context() -> RunContext:
    """The seed context (AD-17, D19): the caller must hold the seed key; `run_id` null."""
    key = os.environ.get(SEED_KEY_ENV, "")
    if not key:
        raise PermissionError(f"{SEED_KEY_ENV} is not set: the prior collection is filed only with the seed key.")
    principal: Principal = await auth.resolve_actor(key)
    if principal.kind != "seed":
        raise PermissionError("the key given is not the seed key")
    grant = await policy_sets.current_grant(SEED_GRANT)
    version = int(_get(grant, "version", 1) or 1)
    return RunContext(
        run_id=None,
        principal=principal,
        stamp=Stamp(kind="seed", principal="seed"),
        grant_id=SEED_GRANT,
        grant_version=version,
        mode="baseline",
    )


async def seeded_trade_names() -> list[str]:
    """The exact FDA trade names already seeded (A13), for the extraction prompt only (V34)."""
    names: list[str] = []
    async for a in _db()["aliases"].find({}, {"name": 1}):
        if isinstance(a.get("name"), str) and a["name"] not in names:
            names.append(a["name"])
    return names


def is_trial_level(finding: Any) -> bool:
    """The record-level Finding (no `diagnostic_id`): the only kind the prior collection files (V54)."""
    return not _get(finding, "diagnostic_id")


def changes_for(finding: Any, source_date: str | None, scope_id: str) -> list[dict[str, Any]]:
    """V54 (R19): the prior collection files each trial-level Finding only as an entry in the scope's
    evidence collection, `source_items.collections.<scope_id>` (V35, AD-25), pinned to its version.

    A Diagnostic Finding files nothing: no Diagnostic field value and no `lifecycle_stage` is filed
    from a prior trial, because a mention is not proof of use (V37) and a baseline value would
    become accepted knowledge without review."""
    if not is_trial_level(finding):
        return []
    fid, ref, vid = _get(finding, "id"), _get(finding, "source_ref"), _get(finding, "version_id")
    return [
        {
            "field": EVIDENCE_COLLECTION,
            "value": ref,
            "diagnostic_id": None,
            "scope_id": scope_id,
            "evidence": {"source_ref": ref, "version_id": vid, "finding_id": fid, "source_date": source_date},
        }
    ]


@dataclass
class PriorRun:
    load: source_load.PriorLoad
    extracted: list[str] = field(default_factory=list)
    already_filed: list[str] = field(default_factory=list)
    not_relevant: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    findings: int = 0
    diagnostic_skipped: int = 0  # Diagnostic Findings neither stored nor filed (V54)
    changes: int = 0
    outcomes: dict[str, int] = field(default_factory=dict)

    def lines(self) -> list[str]:
        out = self.load.lines()
        out += [f"{n} extraction FAILED: {e}" for n, e in self.failed.items()]
        out.append(
            f"baseline filing: {len(self.extracted)} extracted, {len(self.already_filed)} already filed, "
            f"{len(self.not_relevant)} not relevant, {len(self.failed)} failed; {self.findings} trial-level findings, "
            f"{self.diagnostic_skipped} Diagnostic findings not filed (V54), {self.changes} evidence-collection entries filed ({', '.join(f'{k} {v}' for k, v in sorted(self.outcomes.items())) or 'none'})"
        )
        return out


async def file_prior(scope_id: str = DEFAULT_SCOPE, *, ctx: RunContext | None = None) -> PriorRun:
    """Load the prior collection, then extract and file each loaded version in baseline mode."""
    ctx = ctx or await seed_context()
    result = PriorRun(load=await source_load.load_prior(scope_id))
    db = _db()
    names = await seeded_trade_names()
    for stored in result.load.loaded:
        nct = ctgov.nct_from_ref(stored.source_ref)
        item = await db["source_items"].find_one({"_id": stored.source_ref}, {"prior_filed_version_id": 1})
        if (item or {}).get("prior_filed_version_id") == stored.version_id:
            result.already_filed.append(nct)
            continue
        version = await db["source_versions"].find_one({"_id": stored.version_id})
        if version is None:
            result.failed[nct] = "version_missing"
            continue
        extraction = await llm.extract({**version, "version_id": stored.version_id}, names or None)
        status = _get(extraction, "status")
        if status == "not_relevant":
            result.not_relevant.append(nct)
        elif status != "extracted":
            codes = [_get(f, "code") for f in (_get(extraction, "failures") or [])]
            result.failed[nct] = ",".join(c for c in codes if c) or "extraction_failed"
            continue
        else:
            result.extracted.append(nct)
        now = datetime.now(UTC)
        for finding in _get(extraction, "findings") or []:
            if not is_trial_level(finding):
                result.diagnostic_skipped += 1  # V54: no Diagnostic value is filed from a prior trial
                continue
            doc = _dump(finding)
            fid = doc.pop("id")
            await db["findings"].update_one(
                {"_id": fid},
                {"$setOnInsert": {**doc, "_id": fid, "run_id": None, "mode": "baseline", "window": "prior",
                                  "scope_ids": [scope_id], "created_at": now}},
                upsert=True,
            )
            result.findings += 1
            for change in changes_for(finding, stored.last_update_post_date, scope_id):
                for filed in await ledger.file(fid, [change], "baseline", ctx):
                    outcome = _get(filed, "outcome") or _get(filed, "status") or "unknown"
                    result.outcomes[outcome] = result.outcomes.get(outcome, 0) + 1
                result.changes += 1
        await db["source_items"].update_one(
            {"_id": stored.source_ref}, {"$set": {"prior_filed_version_id": stored.version_id, "prior_filed_at": now}}
        )
    return result


async def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m dxp.pipeline.prior", description=__doc__.split("\n\n")[0])
    p.add_argument("--scope", default=DEFAULT_SCOPE)
    p.add_argument("--load-only", action="store_true", help="fetch and store the prior collection; no extraction or filing")
    args = p.parse_args(argv)
    try:
        if args.load_only:
            loaded = await source_load.load_prior(args.scope)
            lines, failed = loaded.lines(), bool(loaded.failed)
        else:
            run = await file_prior(args.scope)
            lines, failed = run.lines(), bool(run.failed or run.load.failed)
        for line in lines:
            print(line)
        return 1 if failed else 0
    except (PermissionError, source_load.CursorMovedError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        await store.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
