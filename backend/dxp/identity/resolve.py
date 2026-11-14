"""Exact trade-name resolution (V34, V37).

A name resolves to a seeded Diagnostic only when ``normalise_name(name)`` is
exactly the ``_id`` of an alias the FDA seed wrote. There are no hand-written
aliases, no prefix, substring or fuzzy matching, and no fallback: anything
else returns ``None`` and stays as the source wrote it (it becomes a report
uncertainty, never an approved product).

The aliases live in the ``aliases`` collection (AD-3), written only by the
ledger (A06 ``ensure_diagnostic``) during the seed (A13). This module only
reads it, with one ``find_one`` by ``_id`` per call, so a seed that runs after
the process starts is seen at once.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable
from typing import Any, Protocol

from .core import derive, normalise_name

__all__ = [
    "AliasLookup",
    "ResolverUnavailable",
    "resolve_exact",
    "use_aliases",
]


class AliasLookup(Protocol):
    """The one call ``resolve_exact`` makes: a PyMongo ``Collection`` fits."""

    def find_one(self, filter: dict[str, Any], *args: Any, **kwargs: Any) -> Any: ...


class ResolverUnavailable(RuntimeError):
    """No ``aliases`` collection could be found to resolve against.

    Raised rather than returning ``None``, so a missing database is never
    mistaken for "this name is unresolved".
    """


_override: AliasLookup | None = None


def use_aliases(collection: AliasLookup | None) -> None:
    """Point ``resolve_exact`` at a given ``aliases`` collection (tests and
    wiring). ``None`` goes back to the default, ``dxp.store``."""
    global _override
    _override = collection


def _default_aliases() -> AliasLookup:
    if _override is not None:
        return _override
    # Imported lazily: identity stays importable and testable without the
    # store module (A01), and the store stays the only MongoDB client maker.
    try:
        from dxp import store  # type: ignore[attr-defined]
    except ImportError as exc:  # pragma: no cover - depends on A01
        raise ResolverUnavailable(
            "dxp.store is not available; pass aliases= or call use_aliases()"
        ) from exc
    getter = getattr(store, "collection", None)
    if callable(getter):
        return getter("aliases")
    db = getattr(store, "db", None)
    if callable(db):
        db = db()
    if db is not None:
        return db["aliases"]
    raise ResolverUnavailable(  # pragma: no cover - depends on A01
        "dxp.store exposes neither collection(name) nor db; "
        "pass aliases= or call use_aliases()"
    )


def _is_seeded_trade_name(doc: dict[str, Any]) -> bool:
    # A live run never applies (AD-4), so an alias it created is not an FDA
    # trade name. The seed writes in baseline mode.
    return doc.get("created_mode") != "live"


def resolve_exact(
    name: str | None, *, aliases: AliasLookup | None = None
) -> str | None | Awaitable[str | None]:
    """Return the ``dx_`` ID of the seeded Diagnostic whose FDA trade name
    equals ``name`` after ``normalise_name()``, or ``None``.

    "FoundationOne CDx" resolves to the tissue Diagnostic and
    "FoundationOne Liquid CDx" to the plasma one; "FoundationOne Liquid",
    "Guardant360" and "FoundationOne" resolve to nothing (V34, V37).
    Reads only; never writes, never creates a Diagnostic.

    The store's collections are async (A01, ``AsyncCollection``), so with the
    default store, or any async collection, this returns an awaitable: callers
    in async code ``await`` it when ``inspect.isawaitable()`` says so. A sync
    collection (tests, scripts) gets the value directly.
    """
    if name is None:
        return None
    if not isinstance(name, str):
        raise TypeError(f"resolve_exact() needs a str, got {type(name).__name__}")
    key = normalise_name(name)
    if not key:
        return None
    collection = aliases if aliases is not None else _default_aliases()
    found = collection.find_one({"_id": key})
    if inspect.isawaitable(found):
        return _finish_async(found, key)
    return _finish(found, key)


def _finish(doc: Any, key: str) -> str | None:
    if doc is None or not _is_seeded_trade_name(doc):
        return None
    return doc.get("diagnostic_id") or derive("dx_", key)


async def _finish_async(found: Awaitable[Any], key: str) -> str | None:
    return _finish(await found, key)
