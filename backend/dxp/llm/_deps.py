"""The A02 functions `llm` calls, in one place so tests can replace them.

- `identity.derive(prefix, *parts)` (AD-3): the only ID maker.
- `identity.resolve_exact(name)` (V34): an exact FDA trade-name match after
  `normalise_name()`, read from the store's `aliases` collection, or `None`.
  It raises `ResolverUnavailable` when no collection is reachable; `llm`
  records that as a `resolve_error`, never as "unresolved".
- `registry.canonical(field, raw)` (AD-2): the only canonicaliser; raises
  `CanonicalError` when a value has no canonical form.

Nothing else in `llm` imports `identity` or `schema`.
"""

from __future__ import annotations

import inspect
from typing import Any

from dxp import identity
from dxp.schema import registry


def derive(prefix: str, *parts: Any) -> str:
    return identity.derive(prefix, *(str(p) for p in parts))


async def resolve_exact(name: str) -> str | None:
    """The seeded Diagnostic ID that `name` names exactly, or None."""
    result = identity.resolve_exact(name)
    if inspect.isawaitable(result):
        result = await result
    return diagnostic_id_of(result)


def canonical(field: str, raw: str) -> str | None:
    return registry.canonical(field, raw)


def stage_names() -> tuple[str, ...]:
    """The registry's stage order, for the prompt."""
    return tuple(s for s in registry.STAGE_ORDER if s != registry.NOT_DETERMINED)


def field_guide(field: str) -> str:
    """One prompt line per field: its registry key and the values it accepts."""
    f = registry.get_field(field)
    if f.enum:
        return f"- {field}: one of {', '.join(f.enum)}"
    hints = {
        "text": "the supporting sentence",
        "normalised_name": "the name as written",
        "nct_id": "an NCT ID (NCT followed by 8 digits)",
        "generic_name": "the drug's generic name",
    }
    return f"- {field}: {hints.get(f.canonical_form, 'free text')}"


def diagnostic_id_of(result: Any) -> str | None:
    if result is None:
        return None
    if isinstance(result, str):
        return result or None
    for key in ("_id", "id", "dx_id", "diagnostic_id"):
        value = result.get(key) if isinstance(result, dict) else getattr(result, key, None)
        if isinstance(value, str) and value:
            return value
    return None
