"""`llm`: the only module that calls Claude (AD-11). Owned by A08.

The three frozen signatures (A01, `tests/a01/test_signatures.py`) are defined
here and delegate to the implementations:

- `extract(item, aliases)` -> `Extraction` as a dict (Story 1.5): triage,
  extraction, name mentions resolved only by `identity.resolve_exact()`, and
  the AD-6 check. `aliases` are the exact seeded trade names (V34).
- `check(finding, source_text)` -> the Finding as a dict, each value's `check`
  set (AD-6).
- `call_structured(model, schema, messages)` -> the parsed object (a dict for
  a JSON-schema dict, the object for a Pydantic class), or an `LLMFailure`.
  The one client A19+A20's `relate` and `draft` use.

Typed callers inside the backend can use `extract_item()` and
`check_finding()`, which return the Pydantic shapes. `MODEL_IDS` and
`PROMPT_VERSION` go into the run's identity (AD-17).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ValidationError

from dxp.llm import client as _client
from dxp.llm.check import check_finding
from dxp.llm.client import MODEL_IDS
from dxp.llm.extract import extract_item
from dxp.llm.prompts import PROMPT_VERSION
from dxp.llm.types import (
    Extraction,
    Finding,
    FindingValue,
    LLMFailure,
    NameMention,
    StageEvidence,
    ValueCheck,
)


async def extract(item: dict[str, Any], aliases: Sequence[str] | None = None) -> dict[str, Any]:
    """Extract Findings from one source item version. Never raises."""
    return (await extract_item(item, aliases)).model_dump()


async def check(finding: dict[str, Any] | Finding, source_text: str) -> dict[str, Any]:
    """Check a Finding's quotes (quote_in_source) and support (one model call)."""
    try:
        parsed = finding if isinstance(finding, Finding) else Finding.model_validate(finding)
    except ValidationError:
        out = dict(finding) if isinstance(finding, dict) else {}
        failure = LLMFailure(code="invalid_finding", step="check").model_dump()
        out["failures"] = [*(out.get("failures") or []), failure]
        return out
    return (await check_finding(parsed, source_text)).model_dump()


async def call_structured(
    model: str,
    schema: dict[str, Any] | type[BaseModel],
    messages: list[Any],
) -> dict[str, Any] | BaseModel | LLMFailure:
    """One structured-output call (JSON schema), no sampling parameters."""
    return await _client.call_structured(model, schema, messages)


__all__ = [
    "MODEL_IDS",
    "PROMPT_VERSION",
    "Extraction",
    "Finding",
    "FindingValue",
    "LLMFailure",
    "NameMention",
    "StageEvidence",
    "ValueCheck",
    "call_structured",
    "check",
    "check_finding",
    "extract",
    "extract_item",
]
