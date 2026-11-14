"""Identity: derived IDs, the name normaliser and exact trade-name matching.

Frozen signatures (development-plan.md, "Contracts come first"):
``identity.derive()``, ``identity.normalise_name()`` and
``identity.resolve_exact(name)``. There are no hand-written aliases (V34) and
there is no ``identity/aliases.py``.
"""

from .core import derive, diagnostic_id, normalise_name
from .resolve import AliasLookup, ResolverUnavailable, resolve_exact, use_aliases

__all__ = [
    "AliasLookup",
    "ResolverUnavailable",
    "derive",
    "diagnostic_id",
    "normalise_name",
    "resolve_exact",
    "use_aliases",
]
