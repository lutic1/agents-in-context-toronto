"""`llm`: the only module that calls Claude (AD-11). Owned by A08.

Frozen signatures (development plan, "Contracts come first"):

- `extract(item)` -> `Extraction` (Story 1.5): triage, extraction, name
  mentions resolved only by `identity.resolve_exact()`, and the AD-6 check.
  Optional `seeded_names` (the seeded FDA trade names for the prompt, V34).
- `check(finding, source_text)` -> `Finding` with each value's `check` set.
- `call_structured(model, schema, messages)` -> parsed object or `LLMFailure`;
  the one client A19+A20's `relate` and `draft` use.

`MODEL_IDS` and `PROMPT_VERSION` go into the run's identity (AD-17).
"""

from dxp.llm.check import check
from dxp.llm.client import MODEL_IDS, call_structured
from dxp.llm.extract import extract
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
    "extract",
]
