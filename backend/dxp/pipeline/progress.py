"""What the run function writes about its own progress (Story 1.7, AD-16, AD-21, D23).

- `runs`: `counts`, `active` (the item and step in progress) and `failures` (one line per
  failed item, a code and never source text). `counts.not_admitted` is `runs.admit`'s
  (AD-21); the outcome counts (`allowed`, `blocked`, `filed`, `reports`, `unknown`) are
  recounted from `decisions`, `proposals`, `reports` and `actions` for this run, so they are
  right however many workers wrote them.
- `runs.status` = `failed`, only on an error the pipeline cannot recover from (D23), by a
  conditional update on `running` or `stopping`, with one `run_status_changed` event.
- `source_items.processed.<scope_id>.<version_id>`: set when an item's report is filed, so a
  later run skips that version and a changed trial (a new version, V40) is processed again.
- `findings`: insert-if-absent on the Finding ID, with the run's stamp (AD-17).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from dxp import store

RUN_ENDED = ("done", "stopped", "failed")


def now() -> datetime:
    return datetime.now(UTC)


class Progress:
    """Progress writes for one run. `active` is kept in memory and written whole, which is
    safe because one run's items share one event loop."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._active: dict[str, str] = {}

    async def _set(self, update: dict[str, Any]) -> None:
        await store.db()["runs"].update_one({"_id": self.run_id}, update)

    async def total(self, count: int) -> None:
        await self._set({"$set": {"counts.total": count}})

    async def step(self, source_ref: str, step: str | None) -> None:
        if step is None:
            self._active.pop(source_ref, None)
        else:
            self._active[source_ref] = step
        active = [{"source_ref": ref, "step": s} for ref, s in self._active.items()]
        await self._set({"$set": {"active": active}})

    async def item_done(self, source_ref: str, *, early_research: bool = False) -> None:
        inc = {"counts.done": 1}
        if early_research:
            inc["counts.early_research"] = 1
        await self._set({"$inc": inc})
        await self.step(source_ref, None)

    async def item_failed(self, source_ref: str, error: str) -> None:
        await self._set({"$inc": {"counts.failed": 1}, "$push": {"failures": {"source_ref": source_ref, "error": error}}})
        await self.step(source_ref, None)

    async def recount(self) -> None:
        """Outcome counts from the stored documents of this run (idempotent)."""
        db = store.db()
        run = {"run_id": self.run_id}
        counts = {
            "counts.allowed": await db["decisions"].count_documents({**run, "outcome": "allowed"}),
            "counts.blocked": await db["decisions"].count_documents({**run, "outcome": "blocked"}),
            "counts.filed": await db["proposals"].count_documents(run),
            "counts.reports": await db["reports"].count_documents(run),
            "counts.unknown": await db["actions"].count_documents({**run, "kind": "notify_slack", "status": "unknown"}),
        }
        await self._set({"$set": counts})

    async def mark_failed(self, error: str, stamp: Any = None) -> bool:
        """running | stopping -> failed (D23). Returns True when this call changed it."""
        result = await store.db()["runs"].update_one(
            {"_id": self.run_id, "status": {"$in": ["running", "stopping"]}},
            {"$set": {"status": "failed", "finished_at": now(), "error": error}},
        )
        if not result.modified_count:
            return False
        await store.emit_event(
            {
                "type": "run_status_changed",
                "dedupe_key": f"run_status_changed|{self.run_id}|failed",
                "run_id": self.run_id,
                "stamp": _plain(stamp),
                "status": "failed",
            }
        )
        return True


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
    any alias a live run created. The verbatim `name` is used when present, else the `_id`."""
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
        {"$set": {f"processed.{scope_id}.{version_id}": {"at": now(), "run_id": run_id}}},
    )


async def save_finding(finding: dict[str, Any], run_id: str, stamp: Any) -> None:
    """Insert-if-absent: a Finding ID is derived from its version and Diagnostic (AD-3, V40)."""
    finding_id = finding.get("id")
    if not finding_id:
        return
    doc = {k: v for k, v in finding.items() if k != "id"}
    doc.update({"run_id": run_id, "stamp": _plain(stamp), "created_at": now()})
    await store.db()["findings"].update_one({"_id": finding_id}, {"$setOnInsert": doc}, upsert=True)
