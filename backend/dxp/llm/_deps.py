"""The frozen functions `llm` calls in other cards' modules, imported late.

A08 drafts before A01 and A02 are on `main` (lever L1), so these imports are
resolved at call time against the frozen signatures:

- `identity.derive(prefix, *parts)` (A02, AD-3): the only ID maker.
- `identity.resolve_exact(name)` (A02, V34): an exact FDA trade-name match
  after `normalise_name()`, or `None`. No hand-written aliases.
- `registry.canonical(field, raw)` (A02, AD-2): the only canonicaliser.

Tests replace these three functions; nothing else in `llm` imports `identity`
or `schema` directly.
"""

from __future__ import annotations

import inspect
from typing import Any


def derive(prefix: str, *parts: Any) -> str:
    from dxp import identity

    return identity.derive(prefix, *parts)


async def resolve_exact(name: str) -> str | None:
    """Return the seeded Diagnostic ID that `name` names exactly, or None.

    Accepts whatever A02 returns (an ID string, a document with `_id`, `id` or
    `dx_id`, or an object with one of those attributes), sync or async.
    """
    from dxp import identity

    result = identity.resolve_exact(name)
    if inspect.isawaitable(result):
        result = await result
    return diagnostic_id_of(result)


def canonical(field: str, raw: str) -> str | None:
    from dxp.schema import registry

    return registry.canonical(field, raw)


# Only shown to the model; `registry.canonical("lifecycle_stage", raw)` decides.
_FALLBACK_STAGES = ("discovery", "assay_development", "clinical_validation", "regulatory_approval")


def stage_names() -> tuple[str, ...]:
    """The registry's stage order, for the prompt. A02 owns the real list."""
    try:
        from dxp.schema import registry
    except ImportError:
        return _FALLBACK_STAGES
    for attr in ("STAGE_ORDER", "STAGES", "LIFECYCLE_STAGES"):
        value = getattr(registry, attr, None)
        if value:
            return tuple(str(s) for s in value if str(s) != "not_determined")
    return _FALLBACK_STAGES


def diagnostic_id_of(result: Any) -> str | None:
    if result is None:
        return None
    if isinstance(result, str):
        return result or None
    for key in ("_id", "id", "dx_id", "diagnostic_id"):
        if isinstance(result, dict):
            value = result.get(key)
        else:
            value = getattr(result, key, None)
        if isinstance(value, str) and value:
            return value
    return None
