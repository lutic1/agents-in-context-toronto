"""Derived IDs and the one name normaliser (AD-3, D45).

Nothing in this module touches a database: both functions are pure.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = ["derive", "diagnostic_id", "normalise_name"]

# Marks removed outright, before and after NFKC. NFKC turns "™" into "TM",
# so it has to go first, or "Foo™" would normalise to "foo tm".
_MARKS = str.maketrans("", "", "®™©")  # ® ™ ©

# A run of anything that is not a letter or digit (underscore counts as
# punctuation here) becomes one space.
_NON_ALNUM = re.compile(r"[\W_]+", re.UNICODE)

_HEX_LEN = 16


def derive(prefix: str, *parts: str | int) -> str:
    """Return ``prefix`` plus the first 16 hex characters of SHA-256 over
    ``parts`` joined with ``|`` (AD-3). It is the only ID maker.

    Parts are strings (integers are written in decimal). ``None`` is refused:
    callers that mean "no Diagnostic" pass ``"-"`` explicitly (D20, V43), so a
    missing value never hashes silently as the text "None".
    """
    if not isinstance(prefix, str) or not prefix:
        raise TypeError("derive() needs a non-empty string prefix")
    if not parts:
        raise ValueError("derive() needs at least one part")
    texts: list[str] = []
    for i, part in enumerate(parts):
        if isinstance(part, bool) or not isinstance(part, (str, int)):
            raise TypeError(
                f"derive() part {i} must be str or int, got {type(part).__name__}"
            )
        texts.append(part if isinstance(part, str) else str(part))
    digest = hashlib.sha256("|".join(texts).encode("utf-8")).hexdigest()
    return prefix + digest[:_HEX_LEN]


def normalise_name(text: str) -> str:
    """The only name normaliser (AD-3, D45).

    Removes "®", "™" and "©", applies Unicode NFKC, folds to lower case,
    replaces each run of non-alphanumeric characters with one space and
    trims. "Guardant360® Liquid CDx" becomes "guardant360 liquid cdx".
    """
    if not isinstance(text, str):
        raise TypeError(f"normalise_name() needs a str, got {type(text).__name__}")
    out = text.translate(_MARKS)
    out = unicodedata.normalize("NFKC", out)
    out = out.translate(_MARKS)
    out = out.lower()
    out = _NON_ALNUM.sub(" ", out)
    return out.strip()


def diagnostic_id(trade_name: str) -> str:
    """The Diagnostic ID for an exact trade name: ``derive("dx_", id_alias)``
    where the ID alias is ``normalise_name(trade_name)`` (AD-3, D31 as kept by
    V34). A03 uses it to derive the scope's ``diagnostic_ids`` from the four
    exact D45 strings; it looks nothing up.
    """
    alias = normalise_name(trade_name)
    if not alias:
        raise ValueError("a trade name must contain at least one letter or digit")
    return derive("dx_", alias)
