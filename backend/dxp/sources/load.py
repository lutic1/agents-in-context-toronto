"""Source items and immutable source versions (A05, Story 1.4, Story 10.1, AD-16, AD-25, V40).

Every fetch (the discovery scan, the prior collection and the setup item) goes through
`store_record()`:

1. one immutable `source_versions` document, insert-if-absent on
   `derive("sv_", source_ref, last_update_post_date, content_hash)`, holding `raw_text`,
   `evidence_text`, the status fields, the interventions verbatim and `previous_version_id`;
2. `source_items.current_version_id` moves to it by a conditional update on the previous
   pointer, and `source_items` keeps a copy of the current version's fields for reading.

A version is never overwritten or deleted. A changed record (a new `lastUpdatePostDate` or a new
content hash) gets a new version and the pointer moves; an unchanged one changes nothing but its
set and scope membership. The pointer never moves back to an older `last_update_post_date`.

Command line (setup, I1 step 1):

    python -m dxp.sources.load --set prior --scope <scope_id>   # the prior collection (Story 1.4)
    python -m dxp.sources.load --nct NCT05715229               # the setup item, window "setup"

Nothing is read from `data/` (D1); every record is fetched from the ClinicalTrials.gov API v2.
Only NCT IDs, dates and counts are printed, never record text.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pymongo.errors import DuplicateKeyError

from dxp import store
from dxp.identity import derive
from dxp.sources import ctgov

MANIFEST = Path(__file__).with_name("selected.json")
WINDOWS = ("prior", "discovered", "setup")
_MAX_ATTEMPTS = 5
_FETCH_CONCURRENCY = 4


def _db() -> Any:
    return store.get_db()


def _now() -> datetime:
    return datetime.now(UTC)


def cursor_text(value: Any) -> str | None:
    """A cursor as the `YYYY-MM-DD` text ClinicalTrials.gov compares against (a BSON date is accepted)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


def version_id_for(source_ref: str, last_update_post_date: str | None, content_hash: str) -> str:
    """AD-3 / V40: `derive("sv_", source_ref, last_update_post_date, content_hash)`; "-" for no date."""
    return derive("sv_", source_ref, last_update_post_date or "-", content_hash)


# ---------------------------------------------------------------------------
# One record into source_versions and source_items
# ---------------------------------------------------------------------------


@dataclass
class Stored:
    source_ref: str
    version_id: str
    previous_version_id: str | None
    new_version: bool  # this call inserted the version document
    moved: bool  # this call moved current_version_id
    last_update_post_date: str | None = None

    @property
    def changed(self) -> bool:
        """A known item moved to a new version: a signal to process it again (V40)."""
        return self.moved and self.previous_version_id is not None


_COPIED = (
    "nct_id",
    "source",
    "url",
    "title",
    "raw_text",
    "evidence_text",
    "overall_status",
    "has_results",
    "last_update_post_date",
    "conditions",
    "interventions",
    "content_hash",
)


async def store_record(
    record: dict[str, Any],
    *,
    window: str,
    set_name: str,
    scope_id: str | None = None,
    run_id: str | None = None,
) -> Stored:
    """Write one parsed record (`ctgov.parse_study`) as a source version and point its item at it."""
    if window not in WINDOWS:
        raise ValueError(f"unknown window {window!r}")
    db = _db()
    items, versions = db["source_items"], db["source_versions"]
    ref = record["source_ref"]
    lupd = record.get("last_update_post_date")
    vid = version_id_for(ref, lupd, record["content_hash"])
    membership: dict[str, Any] = {"sets": set_name}
    if scope_id:
        membership["scope_ids"] = scope_id

    new_version = False
    for _ in range(_MAX_ATTEMPTS):
        now = _now()
        item = await items.find_one({"_id": ref}, {"current_version_id": 1, "last_update_post_date": 1})
        prev = (item or {}).get("current_version_id")

        if prev != vid:
            try:
                await versions.insert_one(
                    {
                        "_id": vid,
                        "source_ref": ref,
                        **{k: record.get(k) for k in _COPIED},
                        "window": window,
                        "previous_version_id": prev,
                        "run_id": run_id,
                        "fetched_at": now,
                    }
                )
                new_version = True
            except DuplicateKeyError:
                pass  # the same version is already stored: immutable, never rewritten

        stale = item is not None and prev is not None and (item.get("last_update_post_date") or "") > (lupd or "")
        if prev == vid or stale:
            await items.update_one({"_id": ref}, {"$set": {"window": window, "updated_at": now}, "$addToSet": membership})
            return Stored(ref, vid, prev, new_version, False, lupd)

        current = {k: record.get(k) for k in _COPIED}
        current.update(
            {"source_date": lupd, "current_version_id": vid, "window": window, "fetched_at": now, "updated_at": now}
        )
        if item is None:
            doc = {"_id": ref, **current, "sets": [set_name], "scope_ids": [scope_id] if scope_id else [], "created_at": now}
            try:
                await items.insert_one(doc)
                return Stored(ref, vid, None, new_version, True, lupd)
            except DuplicateKeyError:
                continue  # another fetch created it first: read it again
        res = await items.update_one(
            {"_id": ref, "current_version_id": prev}, {"$set": current, "$addToSet": membership}
        )
        if res.matched_count:
            return Stored(ref, vid, prev, new_version, True, lupd)
        # the pointer moved under us: read it again and decide again
    raise RuntimeError(f"{ref}: could not move current_version_id after {_MAX_ATTEMPTS} attempts")


# ---------------------------------------------------------------------------
# The manifest, the setup item and the prior collection (Story 1.4)
# ---------------------------------------------------------------------------


def manifest() -> dict[str, Any]:
    """`selected.json`: the D30 trials by NCT ID and the setup item."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["nct_ids"] = [ctgov.check_nct(n) for n in data["nct_ids"]]
    data["setup_item"] = ctgov.check_nct(data["setup_item"])
    return data


async def load_nct(
    nct_id: str, *, window: str = "setup", set_name: str | None = None, scope_id: str | None = None, run_id: str | None = None
) -> Stored:
    """Fetch one trial by NCT ID and store it (the setup item: window "setup")."""
    study = await ctgov.fetch_study(nct_id)
    record = ctgov.parse_study(study)
    return await store_record(
        record, window=window, set_name=set_name or f"nct:{record['nct_id']}", scope_id=scope_id, run_id=run_id
    )


@dataclass
class PriorLoad:
    scope_id: str
    cursor: str
    manifest_count: int = 0
    loaded: list[Stored] = field(default_factory=list)
    left_for_scan: list[tuple[str, str | None]] = field(default_factory=list)  # (nct_id, last update)
    excluded: list[str] = field(default_factory=list)  # the setup item
    failed: dict[str, str] = field(default_factory=dict)  # nct_id -> error class and status

    @property
    def accounted(self) -> int:
        return len(self.loaded) + len(self.left_for_scan) + len(self.excluded) + len(self.failed)

    def lines(self) -> list[str]:
        out = [f"{s.source_ref.split(':', 1)[1]} loaded {s.version_id} ({s.last_update_post_date})" for s in self.loaded]
        out += [f"{n} left for the discovery scan (last update {d} is on or after the cursor)" for n, d in self.left_for_scan]
        out += [f"{n} excluded (the setup item)" for n in self.excluded]
        out += [f"{n} FAILED: {e}" for n, e in self.failed.items()]
        out.append(
            f"prior collection for {self.scope_id}, cursor {self.cursor}: {len(self.loaded)} loaded, "
            f"{len(self.left_for_scan)} left for the scan, {len(self.excluded)} excluded, {len(self.failed)} failed; "
            f"{self.accounted} of {self.manifest_count} in the manifest"
        )
        return out


async def scope_document(scope_id: str) -> dict[str, Any]:
    scope = await _db()["research_scopes"].find_one({"_id": scope_id})
    if scope is None:
        raise LookupError(f"research scope {scope_id!r} not found (run python -m dxp.gate.seed first)")
    return scope


async def load_prior(scope_id: str, *, cursor: str | None = None, nct_ids: list[str] | None = None) -> PriorLoad:
    """The prior collection (Story 1.4, AD-16): every manifest trial last updated strictly before the
    scope's cursor, excluding the setup item, stored with window "prior" and set "prior".

    A trial on or after the cursor is left for the discovery scan; a trial that fails to fetch is
    reported by NCT ID and the rest still load.
    """
    data = manifest()
    if cursor is None:
        cursor = cursor_text(((await scope_document(scope_id)).get("cursor") or {}).get("last_update_post_date"))
    if not cursor:
        raise ValueError(f"{scope_id}: the scope has no cursor (OD2)")
    ids = nct_ids if nct_ids is not None else data["nct_ids"]
    result = PriorLoad(scope_id=scope_id, cursor=cursor, manifest_count=len(ids))
    gate = asyncio.Semaphore(_FETCH_CONCURRENCY)

    async def fetch(nct: str) -> tuple[str, dict[str, Any] | Exception]:
        async with gate:
            try:
                return nct, ctgov.parse_study(await ctgov.fetch_study(nct))
            except Exception as exc:  # noqa: BLE001 - reported by NCT ID, the rest still load
                return nct, exc

    wanted = [n for n in ids if n != data["setup_item"]]
    result.excluded = [n for n in ids if n == data["setup_item"]]
    for nct, got in await asyncio.gather(*(fetch(n) for n in wanted)):
        if isinstance(got, Exception):
            status = getattr(got, "http_status", None)
            result.failed[nct] = type(got).__name__ + (f" HTTP {status}" if status else "")
            continue
        lupd = got.get("last_update_post_date")
        if not lupd or lupd >= cursor:
            result.left_for_scan.append((nct, lupd))
            continue
        try:
            result.loaded.append(await store_record(got, window="prior", set_name="prior", scope_id=scope_id))
        except Exception as exc:  # noqa: BLE001
            result.failed[nct] = type(exc).__name__
    order = {n: i for i, n in enumerate(ids)}
    result.loaded.sort(key=lambda s: order.get(ctgov.nct_from_ref(s.source_ref), 0))
    return result


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m dxp.sources.load", description=__doc__.split("\n\n")[0])
    what = p.add_mutually_exclusive_group(required=True)
    what.add_argument("--set", dest="set_name", choices=["prior"], help="load a named set (prior: Story 1.4)")
    what.add_argument("--nct", help="load one trial by NCT ID (the setup item: NCT05715229)")
    p.add_argument("--scope", default=None, help="the research scope (required for --set prior)")
    p.add_argument("--window", default="setup", choices=WINDOWS, help="window for --nct (default setup)")
    return p


async def _main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.set_name == "prior":
            if not args.scope:
                print("--scope is required with --set prior", file=sys.stderr)
                return 2
            result = await load_prior(args.scope)
            for line in result.lines():
                print(line)
            return 1 if result.failed else 0
        stored = await load_nct(args.nct, window=args.window, scope_id=args.scope)
        state = "new version" if stored.new_version else "unchanged"
        print(f"{ctgov.nct_from_ref(stored.source_ref)} {args.window}: {stored.version_id} ({state}, last update {stored.last_update_post_date})")
        return 0
    finally:
        await store.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
