"""What the run function records about its own progress (Story 1.7, AD-16, AD-21, D23).

Only Governance writes `runs` (spine layer table), so the run's progress goes through two
`runs` functions added by A07+A11 (coded against these signatures; A10 merges after them):

- `runs.record_progress(run_id, *, counts, active_items, failure_lines)`: `counts` holds the
  keys this run owns (`total`, `done`, `failed`, `early_research` and the outcome counts
  `allowed`, `blocked`, `filed`, `reports`, `unknown`, recounted from `decisions`,
  `proposals`, `reports` and `actions` for this run); never `not_admitted`, which is
  `runs.admit`'s (AD-21). `active_items` is the whole list of `{ source_ref, step }` in
  progress and `failure_lines` the whole list of `{ source_ref, error }` (codes, never source
  text); each call sends the full current values, so a repeat is harmless.
- `runs.fail(run_id, error)`: `running | stopping` -> `failed`, only on an error the pipeline
  cannot recover from (D23).

This module still writes what the layer table gives the ingest filters:
`source_items.processed.<scope_id>.<version_id>` = processed_at, a timestamp (set when an item's report is filed, so a
later run skips that version and a changed trial, a new version, V40, is processed again) and
`findings` (insert-if-absent on the Finding ID, with the run's stamp, AD-17).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from dxp import runs, store

RUN_ENDED = ("done", "stopped", "failed")
OUTCOME_COUNTS = ("allowed", "blocked", "filed", "reports", "unknown")


def now() -> datetime:
    return datetime.now(UTC)


class Progress:
    """Progress of one run, kept in memory and sent whole through `runs.record_progress`.
    Safe because one run's items share one event loop."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.counts: dict[str, int] = {"total": 0, "done": 0, "failed": 0, "early_research": 0}
        self._active: dict[str, str] = {}
        self.failures: list[dict[str, str]] = []

    @property
    def active(self) -> list[dict[str, str]]:
        return [{"source_ref": ref, "step": s} for ref, s in self._active.items()]

    async def _record(self) -> None:
        await runs.record_progress(
            self.run_id,
            counts=dict(self.counts),
            active_items=self.active,
            failure_lines=[dict(f) for f in self.failures],
        )

    async def total(self, count: int) -> None:
        self.counts["total"] = count
        await self._record()

    async def step(self, source_ref: str, step: str | None) -> None:
        if step is None:
            self._active.pop(source_ref, None)
        else:
            self._active[source_ref] = step
        await self._record()

    async def item_done(self, source_ref: str, *, early_research: bool = False) -> None:
        self.counts["done"] += 1
        if early_research:
            self.counts["early_research"] += 1
        await self.step(source_ref, None)

    async def item_failed(self, source_ref: str, error: str) -> None:
        self.counts["failed"] += 1
        self.failures.append({"source_ref": source_ref, "error": error})
        await self.step(source_ref, None)

    async def recount(self) -> None:
        """Outcome counts from the stored documents of this run (reads only; idempotent)."""
        db = store.db()
        run = {"run_id": self.run_id}
        self.counts.update(
            {
                "allowed": await db["decisions"].count_documents({**run, "outcome": "allowed"}),
                "blocked": await db["decisions"].count_documents({**run, "outcome": "blocked"}),
                "filed": await db["proposals"].count_documents(run),
                "reports": await db["reports"].count_documents(run),
                "unknown": await db["actions"].count_documents({**run, "kind": "notify_slack", "status": "unknown"}),
            }
        )
        await self._record()

    async def mark_failed(self, error: str) -> None:
        """D23: through `runs.fail`, which owns the conditional update and its event."""
        await runs.fail(self.run_id, error)


def _plain(value: Any) -> Any:
    dump = getattr(value, "model_dump", None)
    return dump(mode="json") if callable(dump) else value


async def load_run(run_id: str) -> dict[str, Any] | None:
    return await store.db()["runs"].find_one({"_id": run_id})


async def run_status(run_id: str) -> str | None:
    run = await store.db()["runs"].find_one({"_id": run_id}, {"status": 1})
    return (run or {}).get("status")


async def seeded_names() -> list[str]:
    """The exact seeded FDA trade names for extraction (V34), read once per run from
    `aliases` (A13 seeds `{ _id: normalised name, diagnostic_id, created_mode }`), leaving out
    any alias a live run created. The verbatim `name` is used when present, else the `_id`.
    They only inform the extraction prompt: a name resolves to a Diagnostic only through
    `identity.resolve_exact()` (AD-3, V34), inside `llm`."""
    names: list[str] = []
    cursor = store.db()["aliases"].find({"created_mode": {"$ne": "live"}})
    async for doc in cursor:
        name = doc.get("name") or doc.get("_id")
        if isinstance(name, str) and name and not name.startswith("approach:") and name not in names:
            names.append(name)
    return names


async def load_source(source_ref: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The Source item and its current version (V40). The version ID read here is pinned for
    the whole item; a later pointer move never changes what this item used."""
    db = store.db()
    item = await db["source_items"].find_one({"_id": source_ref})
    if item is None:
        return None, None
    version_id = item.get("current_version_id")
    version = await db["source_versions"].find_one({"_id": version_id}) if version_id else None
    return item, version


async def load_version(version_id: str) -> dict[str, Any] | None:
    return await store.db()["source_versions"].find_one({"_id": version_id})


async def load_finding(finding_id: str) -> dict[str, Any] | None:
    return await store.db()["findings"].find_one({"_id": finding_id})


def processed(item: dict[str, Any], scope_id: str | None, version_id: str) -> bool:
    if not scope_id:
        return False
    return bool(((item.get("processed") or {}).get(scope_id) or {}).get(version_id))


async def mark_processed(source_ref: str, scope_id: str | None, version_id: str, run_id: str) -> None:
    if not scope_id:
        return
    await store.db()["source_items"].update_one(
        {"_id": source_ref},
        {"$set": {f"processed.{scope_id}.{version_id}": now()}},  # processed_at (AD-16)
    )


async def save_finding(finding: dict[str, Any], run_id: str, stamp: Any) -> None:
    """Insert-if-absent: a Finding ID is derived from its version and Diagnostic (AD-3, V40)."""
    finding_id = finding.get("id")
    if not finding_id:
        return
    doc = {k: v for k, v in finding.items() if k != "id"}
    doc.update({"run_id": run_id, "stamp": _plain(stamp), "created_at": now()})
    await store.db()["findings"].update_one({"_id": finding_id}, {"$setOnInsert": doc}, upsert=True)
