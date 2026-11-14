"""A09: structural rules: the import rule (AD-28), one Slack poster (AD-20), A09 writes only
`actions`, and the frozen route and signatures are finished."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import dxp.actions
from dxp.api import routes_resolve

ACTIONS_DIR = Path(dxp.actions.__file__).parent
BACKEND = ACTIONS_DIR.parents[1]


def imported_modules(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_actions_imports_nothing_from_memory_retrieval_or_reports() -> None:
    for path in ACTIONS_DIR.glob("*.py"):
        for name in imported_modules(path):
            assert not name.startswith(("dxp.memory", "dxp.retrieval", "dxp.reports")), (path.name, name)


def test_only_slack_py_posts_to_slack() -> None:
    for path in (BACKEND / "dxp").rglob("*.py"):
        text = path.read_text()
        if path.name != "slack.py" or path.parent != ACTIONS_DIR:
            assert "hooks.slack.com/services" not in text, path


def test_a09_writes_only_actions() -> None:
    text = (ACTIONS_DIR / "records.py").read_text()
    for call in ("insert_one", "update_one"):
        for line in (ln for ln in text.splitlines() if f".{call}(" in ln):
            assert "ACTIONS" in line, line
    for path in ACTIONS_DIR.glob("*.py"):
        if path.name != "records.py":
            assert "insert_one" not in path.read_text() and "update_one" not in path.read_text(), path


def test_no_slack_callback_route() -> None:
    from dxp.api.app import create_app

    paths = create_app().openapi()["paths"]
    assert not [p for p in paths if "slack" in p.lower()]


def test_the_resolve_route_is_finished() -> None:
    assert "raise not_implemented(" not in inspect.getsource(routes_resolve.resolve_action)
