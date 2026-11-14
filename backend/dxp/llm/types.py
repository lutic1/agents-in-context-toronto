"""Shapes `llm` returns, and the structured-output schemas it asks Claude for.

The AD-14 table names no `Finding` shape, so these are A08's, built from the
AD-2 value entry (`check: { quote_found, supported, confidence, flags }`),
AD-3 (Finding ID `derive("f_", version_id, diagnostic_id)`, V40), AD-5 (at most
one `stage_evidence`), AD-6 and V34/V37 (exact names only; a name in the record
is a mention, not proof of use). If A01's `models.py` adds a `Finding` shape,
these move there at the rebase.

The model-output schemas (`*Out`) carry no constraints: Claude's JSON-schema
output is parsed into them and every limit (quote length, allowed names,
confidence range) is checked in Python, so a bad answer becomes a failure
record instead of a parse error.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Fields extraction may propose (AD-2). `regulatory_status` is filed by rule
# from the FDA list, never by a model; `lifecycle_stage` arrives only through
# `stage_evidence` (AD-5).
EXTRACTABLE_FIELDS: tuple[str, ...] = (
    "modality",
    "provider",
    "clinical_uses",
    "sample_types",
    "tumour_stage_or_line",
    "biomarkers",
    "tumour_types",
    "trials",
    "linked_drugs",
    "study_results",
)

UNRESOLVED = "unresolved"


# --------------------------------------------------------------------------
# Failure records (AD-11, Story 1.5): codes and identifiers only, never
# source text or a provider's error message.
# --------------------------------------------------------------------------


class LLMFailure(BaseModel):
    """A failed model call or a rejected answer. Carries no source text."""

    kind: Literal["failure"] = "failure"
    code: str
    step: str
    model: str | None = None
    attempts: int = 0
    error_type: str | None = None
    http_status: int | None = None
    field: str | None = None
    index: int | None = None

    def line(self) -> str:
        """One log line: codes only."""
        parts = [f"step={self.step}", f"code={self.code}"]
        if self.model:
            parts.append(f"model={self.model}")
        if self.error_type:
            parts.append(f"error={self.error_type}")
        if self.http_status is not None:
            parts.append(f"http={self.http_status}")
        if self.field:
            parts.append(f"field={self.field}")
        if self.index is not None:
            parts.append(f"index={self.index}")
        if self.attempts:
            parts.append(f"attempts={self.attempts}")
        return " ".join(parts)


# --------------------------------------------------------------------------
# What `extract` and `check` return
# --------------------------------------------------------------------------


class ValueCheck(BaseModel):
    """The AD-2 / AD-6 `check` the gate's evidence check reads (never re-judged)."""

    quote_found: bool = False
    supported: bool = False
    confidence: float = 0.0
    flags: list[dict] = Field(default_factory=list)
    checked: bool = False
    detail: str | None = None

    @property
    def passed(self) -> bool:
        return self.quote_found and self.supported


class FindingValue(BaseModel):
    field: str
    raw: str
    value: str | None = None  # registry.canonical(field, raw); None if it failed
    label: str
    quote: str
    check: ValueCheck = Field(default_factory=ValueCheck)

    @property
    def passed(self) -> bool:
        return self.value is not None and self.check.passed


class StageEvidence(BaseModel):
    stage: str
    raw: str
    quote: str
    check: ValueCheck = Field(default_factory=ValueCheck)

    @property
    def passed(self) -> bool:
        return self.check.passed


class NameMention(BaseModel):
    """A name present in the record (V37), kept verbatim. Never proof of use."""

    name: str
    field: str  # e.g. "interventions[0].otherNames[1]" or "text"
    intervention_name: str | None = None
    intervention_type: str | None = None
    resolved_diagnostic_id: str | None = None
    resolution: Literal["exact", "unresolved", "error"] = "unresolved"


class Finding(BaseModel):
    """One Finding per Diagnostic a record names, plus one for the record itself.

    `diagnostic_id` is None for the record-level Finding, whose changes target
    the scope's evidence collection (V35, V43).
    """

    id: str
    source_ref: str
    version_id: str
    nct_id: str | None = None
    diagnostic_id: str | None = None
    target: Literal["scope_collection", "diagnostic"]
    mentions: list[NameMention] = Field(default_factory=list)
    summary: str
    values: list[FindingValue] = Field(default_factory=list)
    stage_evidence: StageEvidence | None = None
    trial_status: str | None = None
    has_results: bool | None = None
    model: str | None = None
    prompt_version: str
    failures: list[LLMFailure] = Field(default_factory=list)

    @property
    def passing_values(self) -> list[FindingValue]:
        return [v for v in self.values if v.passed]


class Extraction(BaseModel):
    """What `llm.extract(item)` returns. Never raised; failures are records.

    `status`:
    - `extracted`: triage said relevant and extraction ran (some values may
      still have failed their checks; see each value's `check`);
    - `not_relevant`: rejected at triage; counts as done, yields no Finding;
    - `failed`: the item could not be extracted; `failures` says why.
    """

    source_ref: str | None
    version_id: str | None
    nct_id: str | None = None
    status: Literal["extracted", "not_relevant", "failed"]
    findings: list[Finding] = Field(default_factory=list)
    mentions: list[NameMention] = Field(default_factory=list)
    unresolved_names: list[str] = Field(default_factory=list)
    intervention_texts: list[str] = Field(default_factory=list)
    triage_reason: str | None = None
    failures: list[LLMFailure] = Field(default_factory=list)
    model_ids: dict[str, str] = Field(default_factory=dict)
    prompt_version: str


# --------------------------------------------------------------------------
# Structured-output schemas (what Claude is asked to return)
# --------------------------------------------------------------------------


class TriageOut(BaseModel):
    concerns_lung_cancer_diagnostic: bool = Field(
        description="True only if the record concerns a diagnostic test, assay or "
        "biomarker testing in lung cancer."
    )
    reason: str = Field(description="One short sentence, no quotes from the record.")


class FieldOut(BaseModel):
    field: str = Field(description="One of the allowed field keys.")
    raw_value: str = Field(description="The value as the record states it.")
    quote: str = Field(
        description="A word-for-word quote from the record, at most 300 characters, "
        "that states this value."
    )
    confidence: float = Field(description="0 to 1.")


class StageOut(BaseModel):
    stage: str = Field(description="One of the allowed lifecycle stages.")
    quote: str = Field(description="A word-for-word quote, at most 300 characters.")
    confidence: float = Field(description="0 to 1.")


class AssayOut(BaseModel):
    name_as_written: str = Field(
        description="The assay name exactly as the record writes it."
    )
    seeded_name: str = Field(
        description="The seeded name it equals exactly, or 'unresolved'."
    )


class ExtractOut(BaseModel):
    summary: str = Field(
        description="One or two plain sentences on what the record investigates and "
        "its design. No assay or product names, no results unless results are posted."
    )
    record_fields: list[FieldOut] = Field(default_factory=list)
    stage_evidence: StageOut | None = None
    assays: list[AssayOut] = Field(default_factory=list)


class VerdictOut(BaseModel):
    index: int
    supported: bool


class CheckOut(BaseModel):
    verdicts: list[VerdictOut] = Field(default_factory=list)
