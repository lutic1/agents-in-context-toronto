"""A13: scripts/reset_demo.py guards and steps, with a fake client and fake MongoDB tools."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

URI = "mongodb+srv://test-user:fake-password@sandbox.example.invalid/"


class SyncColl:
    def __init__(self, db: "SyncDB", name: str) -> None:
        self.db, self.name = db, name

    @property
    def docs(self) -> list[dict[str, Any]]:
        return self.db.data.setdefault(self.name, [])

    def count_documents(self, flt: dict[str, Any]) -> int:
        return sum(1 for d in self.docs if all(d.get(k) == v for k, v in flt.items()))

    def delete_many(self, flt: dict[str, Any]) -> None:
        assert flt == {}
        self.db.client.log.append(("delete_many", self.db.name, self.name))
        self.docs.clear()

    def drop(self) -> None:  # pragma: no cover - must never be called
        raise AssertionError("the reset never drops a collection")


class SyncDB:
    def __init__(self, client: "SyncClient", name: str) -> None:
        self.client, self.name = client, name
        self.data: dict[str, list[dict[str, Any]]] = {}

    def list_collection_names(self) -> list[str]:
        return list(self.data)

    def __getitem__(self, name: str) -> SyncColl:
        return SyncColl(self, name)


class SyncClient:
    def __init__(self) -> None:
        self.dbs: dict[str, SyncDB] = {}
        self.log: list[tuple[str, ...]] = []

    def __getitem__(self, name: str) -> SyncDB:
        self.log.append(("db", name))
        return self.dbs.setdefault(name, SyncDB(self, name))

    def drop_database(self, name: str) -> None:  # pragma: no cover - must never be called
        raise AssertionError("the reset never drops a database")


class FakeTools:
    """Records argv; reads the private config file while it exists; simulates dump and restore."""

    def __init__(self, client: SyncClient, returncode: int = 0) -> None:
        self.client, self.returncode, self.calls, self.configs = client, returncode, [], []

    def __call__(self, argv: list[str], **kwargs: Any) -> SimpleNamespace:
        self.calls.append(argv)
        config = Path(next(a for a in argv if a.startswith("--config=")).split("=", 1)[1])
        self.configs.append((config.read_text(), oct(config.stat().st_mode & 0o777)))
        opts = dict(a[2:].split("=", 1) for a in argv[1:] if a.startswith("--"))
        if self.returncode == 0 and argv[0].endswith("mongodump"):
            out = Path(opts["out"]) / opts["db"]
            out.mkdir(parents=True)
            (out / "dump.json").write_text(json.dumps(self.client.dbs[opts["db"]].data))
        elif self.returncode == 0 and argv[0].endswith("mongorestore"):
            src = opts["nsInclude"].removesuffix(".*")
            target = opts.get("nsTo", opts["nsInclude"]).removesuffix(".*")
            data = json.loads((Path(opts["dir"]) / src / "dump.json").read_text())
            db = self.client.dbs.setdefault(target, SyncDB(self.client, target))
            for name, docs in data.items():
                db.data.setdefault(name, []).extend(docs)
        return SimpleNamespace(returncode=self.returncode, stderr=f"error near {URI}" if self.returncode else "")


TOOLS = {"mongodump": "/usr/bin/mongodump", "mongorestore": "/usr/bin/mongorestore"}


@pytest.fixture
def client() -> SyncClient:
    c = SyncClient()
    db = c["dxp_test_demo"]
    db.data.update({
        "memories": [{"_id": "mem_1@v1", "status": "active"}],
        "teams": [{"_id": "team_a"}, {"_id": "team_b"}],
        "runs": [{"_id": "run_setup", "kind": "items"}],
        "grants": [{"_id": "seed@v1"}],
    })
    c.log.clear()
    return c


def test_refuses_unsafe_targets(reset_demo) -> None:
    for name in ("dxp_smoke", "admin", "local", "config", "", None, "a.b", "x/y"):
        with pytest.raises(reset_demo.ResetError):
            reset_demo.check_target(name)
    assert reset_demo.check_target("dxp") == "dxp"


def test_db_is_required_on_the_command_line(reset_demo) -> None:
    with pytest.raises(SystemExit):
        reset_demo.main([])


def test_snapshot_folder_must_be_outside_the_repo(reset_demo, client) -> None:
    with pytest.raises(reset_demo.ResetError, match="inside the repository"):
        reset_demo.snapshot(client, "dxp_test_demo", reset_demo.REPO / "snapshots", uri=URI, tools=TOOLS,
                            runner=FakeTools(client))


def test_snapshot_then_restore_into_the_named_database_only(reset_demo, client, tmp_path) -> None:
    tools = FakeTools(client)
    snap = tmp_path / "snap"
    manifest = reset_demo.snapshot(client, "dxp_test_demo", snap, uri=URI, tools=TOOLS, runner=tools)
    assert manifest["db"] == "dxp_test_demo"
    assert manifest["collections"] == {"grants": 1, "memories": 1, "runs": 1, "teams": 2}
    dump_argv = tools.calls[0]
    assert dump_argv[:3] == ["/usr/bin/mongodump", "--db=dxp_test_demo", f"--out={snap}"]

    # a discover run happens, then the reset
    demo = client.dbs["dxp_test_demo"]
    demo.data["runs"].append({"_id": "run_live", "kind": "discover"})
    demo.data["reports"] = [{"_id": "rep_1"}]
    other = client["dxp_test_other"]
    other.data["teams"] = [{"_id": "untouched"}]
    client.log.clear()

    restored = reset_demo.restore(client, "dxp_test_demo", snap, uri=URI, tools=TOOLS, runner=tools)
    assert restored == {"grants": 1, "memories": 1, "reports": 0, "runs": 1, "teams": 2}
    assert demo.data["runs"] == [{"_id": "run_setup", "kind": "items"}]
    assert other.data["teams"] == [{"_id": "untouched"}]  # another database is never touched
    assert {entry[1] for entry in client.log if entry[0] in ("db", "delete_many")} == {"dxp_test_demo"}
    assert {entry[2] for entry in client.log if entry[0] == "delete_many"} == {"grants", "memories", "reports", "runs", "teams"}
    restore_argv = tools.calls[1]
    assert restore_argv[0] == "/usr/bin/mongorestore"
    assert f"--nsInclude=dxp_test_demo.*" in restore_argv
    assert not any(a.startswith(("--drop", "--nsFrom", "--nsTo")) for a in restore_argv)


def test_restore_into_another_database_maps_the_namespace(reset_demo, client, tmp_path) -> None:
    tools = FakeTools(client)
    snap = tmp_path / "snap"
    reset_demo.snapshot(client, "dxp_test_demo", snap, uri=URI, tools=TOOLS, runner=tools)
    reset_demo.restore(client, "dxp_test_copy", snap, uri=URI, tools=TOOLS, runner=tools)
    argv = tools.calls[1]
    assert "--nsFrom=dxp_test_demo.*" in argv and "--nsTo=dxp_test_copy.*" in argv
    assert client.dbs["dxp_test_copy"].data["teams"] == [{"_id": "team_a"}, {"_id": "team_b"}]


def test_the_uri_never_reaches_argv_or_output(reset_demo, client, tmp_path) -> None:
    tools = FakeTools(client)
    reset_demo.snapshot(client, "dxp_test_demo", tmp_path / "s", uri=URI, tools=TOOLS, runner=tools)
    assert all(URI not in a for a in tools.calls[0])
    text, mode = tools.configs[0]
    assert text == f'uri: "{URI}"\n' and mode == "0o600"
    failing = FakeTools(client, returncode=1)
    with pytest.raises(reset_demo.ResetError) as err:
        reset_demo.snapshot(client, "dxp_test_demo", tmp_path / "t", uri=URI, tools=TOOLS, runner=failing)
    assert URI not in str(err.value) and "Fallback (OD6)" in str(err.value)


def test_snapshot_needs_m1_and_no_discover_run(reset_demo, client, tmp_path) -> None:
    demo = client.dbs["dxp_test_demo"]
    demo.data["memories"] = []
    with pytest.raises(reset_demo.ResetError, match="no active memory"):
        reset_demo.snapshot(client, "dxp_test_demo", tmp_path / "a", uri=URI, tools=TOOLS, runner=FakeTools(client))
    demo.data["memories"] = [{"_id": "mem_1@v1", "status": "active"}]
    demo.data["runs"].append({"_id": "run_live", "kind": "discover"})
    with pytest.raises(reset_demo.ResetError, match="discover run"):
        reset_demo.snapshot(client, "dxp_test_demo", tmp_path / "b", uri=URI, tools=TOOLS, runner=FakeTools(client))
    reset_demo.snapshot(client, "dxp_test_demo", tmp_path / "c", uri=URI, tools=TOOLS, runner=FakeTools(client),
                        allow_runs=True)


def test_missing_tools_print_the_fallback(reset_demo) -> None:
    with pytest.raises(reset_demo.ResetError, match="Fallback"):
        reset_demo.require_tools(["mongodump"], which=lambda name: None)


def test_restore_refuses_a_folder_that_is_not_a_snapshot(reset_demo, client, tmp_path) -> None:
    with pytest.raises(reset_demo.ResetError, match="manifest"):
        reset_demo.restore(client, "dxp_test_demo", tmp_path, uri=URI, tools=TOOLS, runner=FakeTools(client))
    assert not any(entry[0] == "delete_many" for entry in client.log)  # nothing emptied first


def test_restore_checks_counts(reset_demo, client, tmp_path) -> None:
    tools = FakeTools(client)
    snap = tmp_path / "snap"
    reset_demo.snapshot(client, "dxp_test_demo", snap, uri=URI, tools=TOOLS, runner=tools)
    manifest = json.loads((snap / "manifest.json").read_text())
    manifest["collections"]["teams"] = 5
    (snap / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(reset_demo.ResetError, match="counts differ"):
        reset_demo.restore(client, "dxp_test_demo", snap, uri=URI, tools=TOOLS, runner=tools)


def test_latest_snapshot(reset_demo, tmp_path) -> None:
    for name, taken, db in (("a", "2026-11-14T14:00:00+00:00", "dxp"), ("b", "2026-11-14T15:00:00+00:00", "dxp"),
                            ("c", "2026-11-14T16:00:00+00:00", "other")):
        (tmp_path / name).mkdir()
        (tmp_path / name / "manifest.json").write_text(json.dumps({"db": db, "taken_at": taken}))
    assert reset_demo.latest_snapshot(tmp_path).name == "c"
    assert reset_demo.latest_snapshot(tmp_path, "dxp").name == "b"
    with pytest.raises(reset_demo.ResetError):
        reset_demo.latest_snapshot(tmp_path / "none")


def test_the_script_posts_nothing(reset_demo) -> None:
    source = (reset_demo.REPO / "scripts" / "reset_demo.py").read_text()
    for word in ("httpx", "requests", "urllib", "SLACK_WEBHOOK_URL", "dxp.actions", "hooks.slack"):
        assert word not in source
