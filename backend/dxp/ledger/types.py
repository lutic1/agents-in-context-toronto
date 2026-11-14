"""Types the ledger takes and returns (AD-1, AD-2, AD-4, AD-27).

``LedgerCtx`` is the gate's context (``run`` for agent writes, ``seed`` for
``baseline`` mode); ``Change`` is one Proposed change; ``Filed`` is what
``ledger.file`` returns for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from dxp.gate.checks import GateCtx as LedgerCtx

# The field a scope evidence-collection update uses (AD-27, V35).
EVIDENCE_COLLECTION = "evidence_collection"

# Graph node type for each field that yields an edge (AD-13).
EDGE_NODE_TYPES = {
    "biomarkers": "biomarker",
    "trials": "trial",
    "linked_drugs": "drug",
    "provider": "provider",
    "tumour_types": "tumour",
}

# Fields indexed as facets on the Diagnostic (AD-15).
FACET_FIELDS = (
    "modality",
    "regulatory_status",
    "lifecycle_stage",
    "provider",
    "clinical_uses",
    "sample_types",
    "tumour_stage_or_line",
    "biomarkers",
    "tumour_types",
    "linked_drugs",
)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


@dataclass
class Change:
    """One Proposed change, already canonical (``registry.canonical`` runs upstream, AD-2).

    A change targets a Diagnostic (``diagnostic_id``, or ``assay_name`` /
    ``approach_alias`` for one ``ensure_diagnostic`` would create), or, with
    ``diagnostic_id`` null and ``scope_id`` set, the scope's evidence
    collection (field ``evidence_collection``, value the ``source_ref``, V35,
    V43). ``mention`` is set when the change links a name found in the record
    to a Diagnostic (V37).
    """

    field: str
    value: str
    label: str | None = None
    detail: dict[str, Any] | None = None
    diagnostic_id: str | None = None
    diagnostic_name: str | None = None
    assay_name: str | None = None
    approach_alias: str | None = None
    scope_id: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    check: dict[str, Any] = field(default_factory=dict)
    mention: dict[str, Any] | None = None
    trigger: str | None = None
    admission_id: str | None = None

    @classmethod
    def coerce(cls, change: Any) -> "Change":
        if isinstance(change, cls):
            return change
        names = cls.__dataclass_fields__.keys()
        return cls(**{n: _get(change, n) for n in names if _get(change, n) is not None})

    @property
    def is_scope_collection(self) -> bool:
        return self.diagnostic_id is None and self.scope_id is not None and not self.creates_alias

    @property
    def creates_alias(self) -> str | None:
        """The name ``ensure_diagnostic`` would match or create, when no ID is given."""
        if self.diagnostic_id:
            return None
        return self.assay_name or self.approach_alias


@dataclass
class Filed:
    """The outcome of filing one change.

    ``status`` is ``filed`` (pending proposal), ``applied`` (``baseline``),
    ``blocked`` (the gate said no; only the Decision exists), or
    ``not_filed`` (equal to a current value, or a stage that is not later).
    """

    status: str
    proposal_id: str | None = None
    diagnostic_id: str | None = None
    decision: dict[str, Any] | None = None
    reason: str | None = None

    @property
    def decision_id(self) -> str | None:
        return (self.decision or {}).get("_id")


__all__ = ["Change", "EDGE_NODE_TYPES", "EVIDENCE_COLLECTION", "FACET_FIELDS", "Filed", "LedgerCtx"]
