#!/usr/bin/env python3
"""Snapshot and restore the demo database (A13; D34, D41, V15, OD6).

    uv run --project backend python scripts/reset_demo.py --db dxp --snapshot
    uv run --project backend python scripts/reset_demo.py --db dxp            # restore the latest

Snapshot (`--snapshot`): `mongodump` of the one database named by `--db` into a folder outside
the repository (default `~/dxp-snapshots/<db>-<UTC time>`), plus `manifest.json` with the
database name and each collection's document count. Take it at the end of I1 setup, only after
`GET /memories?team_id=` shows M1 (created by Sam through the real UI) and before any discover
run: the script refuses when the database has no active memory or already has a discover run,
unless told otherwise.

Restore (the default): without `--dir`, the newest snapshot of the same database under
`--root`; a snapshot of another database is restored only when named with `--dir`. Then, for
every collection of the database named by `--db`,
`delete_many({})` (never a drop, so validators and indexes, including the Atlas Search and
Vector Search indexes, stay), then `mongorestore` of the snapshot into that database only
(`--nsInclude`, and `--nsFrom`/`--nsTo` when the snapshot came from another database), then a
count check against the manifest. Before emptying anything it checks that the dump holds a
BSON file for every non-empty collection and runs `mongorestore --dryRun` (it connects,
authenticates and reads the dump, writing nothing), so a broken dump or a refused login never
leaves the database empty.

Rules:
- It touches only the database named by `--db`; there is no default. It refuses `dxp_smoke`
  (the integrators' smoke tests, D41) and MongoDB's own databases.
- It posts nothing to Slack and calls no other service.
- `MONGODB_URI` is read from the environment and handed to the MongoDB tools in a private
  temporary config file, never on the command line, and is never printed.
- If `mongodump` or `mongorestore` is missing or does not work against the sandbox (OD6), it
  stops and prints the fallback: rerun the setup commands, with Sam recreating the memory
  through the UI (about 30 minutes).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = Path.home() / "dxp-snapshots"
MANIFEST = "manifest.json"
REFUSED_DBS = frozenset({"dxp_smoke", "admin", "local", "config"})

FALLBACK = """\
Fallback (OD6): reset by rerunning the setup, in this order (docs/demo-and-reset.md):
  1. python -m dxp.gate.seed
  2. python -m dxp.sources.fda_cdx, then python -m dxp.ledger.seed
  3. python -m dxp.pipeline.prior
  4. retrieval.ensure_indexes(), and wait until every index is queryable
  5. Sam recreates memory M1 through the UI (V15), then take a new snapshot if the tools work
This takes about 30 minutes."""

Runner = Callable[..., Any]


class ResetError(RuntimeError):
    """The reset refused to run or failed; nothing after the failing step ran."""


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def check_target(db_name: str | None) -> str:
    if not db_name or not db_name.strip():
        raise ResetError("--db is required: the reset touches only the database it is told to")
    name = db_name.strip()
    if name in REFUSED_DBS:
        raise ResetError(f"refusing database {name!r}: the reset never touches it")
    if any(ch in name for ch in "/\\. \"$*"):
        raise ResetError(f"{name!r} is not a plain database name")
    return name


def check_outside_repo(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == REPO or resolved.is_relative_to(REPO):
        raise ResetError(f"{path} is inside the repository: snapshots live outside it")
    return resolved


def require_tools(names: Sequence[str], which: Callable[[str], str | None] = shutil.which) -> dict[str, str]:
    found = {name: which(name) for name in names}
    missing = [name for name, path in found.items() if not path]
    if missing:
        raise ResetError(f"{', '.join(missing)} not found on PATH (OD6).\n{FALLBACK}")
    return {name: path for name, path in found.items() if path}


def mongo_uri(env: dict[str, str] | None = None) -> str:
    uri = (env if env is not None else os.environ).get("MONGODB_URI", "").strip()
    if not uri:
        raise ResetError("MONGODB_URI is not set")
    return uri


# ---------------------------------------------------------------------------
# Running the MongoDB tools without the URI on the command line
# ---------------------------------------------------------------------------


def _run_tool(argv: list[str], uri: str, runner: Runner) -> None:
    with tempfile.TemporaryDirectory(prefix="dxp-reset-") as tmp:
        config = Path(tmp) / "tool.yaml"
        fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(f"uri: {json.dumps(uri)}\n")  # a JSON string is a valid YAML scalar
        result = runner([*argv, f"--config={config}"], capture_output=True, text=True)
    if getattr(result, "returncode", 1) != 0:
        tail = (getattr(result, "stderr", "") or "").strip().splitlines()[-5:]
        # The tools never echo the URI from a config file; strip it anyway, to be sure.
        detail = "\n".join(line.replace(uri, "<MONGODB_URI>") for line in tail)
        raise ResetError(f"{Path(argv[0]).name} failed (exit {result.returncode}):\n{detail}\n{FALLBACK}")


def user_collections(db: Any) -> list[str]:
    return sorted(n for n in db.list_collection_names() if not n.startswith("system."))


def collection_counts(db: Any) -> dict[str, int]:
    return {name: db[name].count_documents({}) for name in user_collections(db)}


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def snapshot(
    client: Any,
    db_name: str,
    out_dir: Path,
    *,
    uri: str,
    runner: Runner = subprocess.run,
    tools: dict[str, str] | None = None,
    allow_no_memory: bool = False,
    allow_runs: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """mongodump the database into ``out_dir`` and write the manifest. Returns the manifest."""
    db_name = check_target(db_name)
    out_dir = check_outside_repo(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ResetError(f"{out_dir} is not empty: choose a new snapshot folder")
    tools = tools or require_tools(["mongodump"])
    db = client[db_name]
    if not allow_no_memory and db["memories"].count_documents({"status": "active"}) == 0:
        raise ResetError(
            "no active memory: take the snapshot only after GET /memories?team_id= shows M1 (V15); "
            "pass --allow-no-memory to snapshot anyway"
        )
    if not allow_runs and db["runs"].count_documents({"kind": "discover"}) > 0:
        raise ResetError(
            "a discover run already exists: the snapshot is taken before any discover run; "
            "pass --allow-runs to snapshot anyway"
        )
    counts = collection_counts(db)
    out_dir.mkdir(parents=True, exist_ok=True)
    _run_tool([tools["mongodump"], f"--db={db_name}", f"--out={out_dir}"], uri, runner)
    manifest = {
        "db": db_name,
        "taken_at": (now or datetime.now(UTC)).isoformat(),
        "collections": counts,
    }
    (out_dir / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------


def read_manifest(snapshot_dir: Path) -> dict[str, Any]:
    path = snapshot_dir / MANIFEST
    if not path.is_file():
        raise ResetError(f"{snapshot_dir} has no {MANIFEST}: not a snapshot taken by this script")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not (snapshot_dir / manifest["db"]).is_dir():
        raise ResetError(f"{snapshot_dir} has no dump folder for database {manifest['db']!r}")
    return manifest


def latest_snapshot(root: Path, db_name: str | None = None) -> Path:
    """The most recent snapshot under ``root`` (by its manifest's ``taken_at``)."""
    found: list[tuple[str, Path]] = []
    if root.is_dir():
        for child in root.iterdir():
            path = child / MANIFEST
            if path.is_file():
                manifest = json.loads(path.read_text(encoding="utf-8"))
                if db_name is None or manifest.get("db") == db_name:
                    found.append((manifest.get("taken_at", ""), child))
    if not found:
        raise ResetError(f"no snapshot found under {root}")
    return max(found)[1]


def restore(
    client: Any,
    db_name: str,
    snapshot_dir: Path,
    *,
    uri: str,
    runner: Runner = subprocess.run,
    tools: dict[str, str] | None = None,
    allow_other_source: bool = False,
) -> dict[str, int]:
    """Empty every collection of ``db_name`` (never drop), then mongorestore the snapshot into it.

    A snapshot of another database is restored only with ``allow_other_source`` (on the
    command line: only when the snapshot folder is named with ``--dir``), so a test snapshot
    can never be poured into ``dxp`` by accident. Checked before anything is emptied.
    Returns the restored counts; raises ``ResetError`` if they differ from the manifest.
    """
    db_name = check_target(db_name)
    snapshot_dir = snapshot_dir.expanduser().resolve()
    manifest = read_manifest(snapshot_dir)
    source = manifest["db"]
    if source != db_name and not allow_other_source:
        raise ResetError(
            f"{snapshot_dir} is a snapshot of {source!r}, not {db_name!r}: name it with --dir "
            "to restore it into another database"
        )
    tools = tools or require_tools(["mongorestore"])
    missing = sorted(
        name for name, count in manifest["collections"].items()
        if count and not (snapshot_dir / source / f"{name}.bson").is_file()
    )
    if missing:
        raise ResetError(f"the dump has no BSON file for {', '.join(missing)}: not restoring")
    argv = [tools["mongorestore"], f"--dir={snapshot_dir}", f"--nsInclude={source}.*"]
    if source != db_name:
        argv += [f"--nsFrom={source}.*", f"--nsTo={db_name}.*"]
    # A dry run first (connects, authenticates and reads the dump, writes nothing), so a
    # failure that would leave the database empty is found before anything is emptied.
    _run_tool([*argv, "--dryRun"], uri, runner)
    db = client[db_name]
    for name in user_collections(db):
        db[name].delete_many({})
    _run_tool(argv, uri, runner)
    restored = collection_counts(db)
    expected = {k: v for k, v in manifest["collections"].items() if v}
    wrong = {k: (v, restored.get(k, 0)) for k, v in expected.items() if restored.get(k, 0) != v}
    if wrong:
        raise ResetError(f"restored counts differ from the snapshot (expected, found): {wrong}")
    return restored


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def _client(uri: str) -> Any:
    from pymongo import MongoClient

    return MongoClient(uri, tz_aware=True, appname="dxp-reset", serverSelectionTimeoutMS=15_000)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reset_demo.py", description="Snapshot or restore the demo database.")
    parser.add_argument("--db", required=True, help="the one database to snapshot or reset (for the demo: dxp)")
    parser.add_argument("--snapshot", action="store_true", help="take a snapshot instead of restoring")
    parser.add_argument("--dir", type=Path, help="snapshot folder (default: new or latest under --root)")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help=f"snapshot root (default {DEFAULT_ROOT})")
    parser.add_argument("--allow-no-memory", action="store_true", help="snapshot even with no active memory")
    parser.add_argument("--allow-runs", action="store_true", help="snapshot even after a discover run")
    args = parser.parse_args(argv)

    try:
        db_name = check_target(args.db)
        uri = mongo_uri()
        client = _client(uri)
        try:
            if args.snapshot:
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
                out_dir = args.dir or (args.root / f"{db_name}-{stamp}")
                manifest = snapshot(
                    client, db_name, out_dir, uri=uri,
                    allow_no_memory=args.allow_no_memory, allow_runs=args.allow_runs,
                )
                total = sum(manifest["collections"].values())
                print(f"snapshot of {db_name}: {total} documents in {len(manifest['collections'])} collections -> {out_dir}")
            else:
                # Without --dir, only a snapshot of this same database is ever picked.
                snapshot_dir = args.dir or latest_snapshot(args.root.expanduser(), db_name)
                restored = restore(client, db_name, snapshot_dir, uri=uri, allow_other_source=args.dir is not None)
                print(f"restored {db_name} from {snapshot_dir}: {sum(restored.values())} documents")
        finally:
            client.close()
    except ResetError as exc:
        print(f"reset_demo: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover - command line
    sys.exit(main())
