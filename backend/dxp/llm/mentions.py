"""Name mentions read from a record's structured interventions (V34, V37).

No model is involved: each intervention's name and `otherNames` are taken
verbatim and resolved only through `identity.resolve_exact()`. A name that
resolves is a mention of that seeded Diagnostic, never evidence that the trial
used it. A name that does not resolve stays as written; when it sits in an
assay-like intervention it is returned as an unresolved name for the report's
uncertainties (never mapped to an approved product, never `new`).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from dxp.llm import _deps
from dxp.llm.types import LLMFailure, NameMention

# Intervention types whose unresolved names are assay candidates. A drug's
# brand name (for example "Opdivo") is not an unresolved assay.
_GENERIC_TOKENS = frozenset(
    {"liquid", "tissue", "assay", "assays", "test", "tests", "tumor", "tumour", "ctdna", "ngs", "cdx", "plasma", "blood", "panel"}
)


def _brand_tokens(names: Sequence[str]) -> set[str]:
    tokens: set[str] = set()
    for name in names:
        for tok in re.findall(r"[A-Za-z0-9]+", name):
            low = tok.lower()
            if low in _GENERIC_TOKENS:
                continue
            if len(tok) >= 8 or any(ch.isdigit() for ch in tok) or (tok[1:] != tok[1:].lower() and len(tok) >= 4):
                tokens.add(low)
    return tokens


TEST_TYPES = frozenset({"DIAGNOSTIC_TEST", "DEVICE"})
ASSAY_LIKE_TYPES = frozenset({"DIAGNOSTIC_TEST", "DEVICE", "GENETIC", "OTHER", "PROCEDURE"})


def _get(obj: Any, *keys: str) -> Any:
    for key in keys:
        if isinstance(obj, Mapping):
            if key in obj and obj[key] is not None:
                return obj[key]
        else:
            value = getattr(obj, key, None)
            if value is not None:
                return value
    return None


def interventions_of(item: Any) -> list[dict[str, Any]]:
    """The record's interventions as `{name, type, other_names}`, verbatim."""
    raw = _get(item, "interventions") or []
    out: list[dict[str, Any]] = []
    if not isinstance(raw, Sequence) or isinstance(raw, str):
        return out
    for entry in raw:
        name = _get(entry, "name")
        if not isinstance(name, str):
            continue
        other = _get(entry, "other_names", "otherNames") or []
        out.append(
            {
                "name": name,
                "type": _get(entry, "type"),
                "other_names": [n for n in other if isinstance(n, str)],
            }
        )
    return out


async def read_mentions(item: Any) -> tuple[list[NameMention], list[str], list[LLMFailure]]:
    """(mentions, intervention texts verbatim, failures)."""
    mentions: list[NameMention] = []
    failures: list[LLMFailure] = []
    texts: list[str] = []
    for i, iv in enumerate(interventions_of(item)):
        texts.append(iv["name"])
        candidates = [(iv["name"], f"interventions[{i}].name")]
        candidates += [(n, f"interventions[{i}].otherNames[{j}]") for j, n in enumerate(iv["other_names"])]
        for name, field in candidates:
            mention = await resolve_mention(
                name, field, intervention_name=iv["name"], intervention_type=iv["type"]
            )
            if mention.resolution == "error":
                failures.append(LLMFailure(code="resolve_error", step="mentions", field=field))
            assay_like = (iv["type"] or "").upper() in ASSAY_LIKE_TYPES
            # The intervention's own name is its wording, not a product name:
            # keep it as a mention only when it resolves exactly.
            is_other_name = field.endswith("]") and ".otherNames[" in field
            # An unresolved intervention name is kept only when the intervention
            # is a test or device and its name looks like a product name (for
            # example "Guardant360"); generic wording such as "ctDNA, tumor NGS"
            # is the intervention text, not an assay name.
            test_named = (iv["type"] or "").upper() in TEST_TYPES and bool(_brand_tokens([name]))
            if (
                mention.resolution in ("exact", "error")
                or (assay_like and is_other_name)
                or (test_named and not is_other_name)
            ):
                mentions.append(mention)
    return mentions, texts, failures


async def resolve_mention(
    name: str,
    field: str,
    *,
    intervention_name: str | None = None,
    intervention_type: str | None = None,
) -> NameMention:
    try:
        dx_id = await _deps.resolve_exact(name)
    except Exception:  # noqa: BLE001 - resolution failure is recorded, never raised
        return NameMention(
            name=name,
            field=field,
            intervention_name=intervention_name,
            intervention_type=intervention_type,
            resolution="error",
        )
    return NameMention(
        name=name,
        field=field,
        intervention_name=intervention_name,
        intervention_type=intervention_type,
        resolved_diagnostic_id=dx_id,
        resolution="exact" if dx_id else "unresolved",
    )
