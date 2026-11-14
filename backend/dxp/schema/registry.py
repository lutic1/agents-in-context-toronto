"""The field registry (AD-2, AD-5, Story 1.2).

Field keys, labels, cardinality, enums, the Lifecycle stage order and the
low-confidence threshold live only here. ``GET /api/v1/schema`` (A01) serves
``describe()``; the web app never hard-codes any of it.

``canonical(field, raw)`` is the only value normaliser: every value entry's
``value`` is the string it returns. The small maps below are hand-written for
the biomarkers and tumour types that the FDA lung rows and the selected trials
use; nothing is read from ``data/``. They canonicalise *values*; they never
resolve a Diagnostic name (that is ``identity.resolve_exact``, exact match
only, V34).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field as dc_field
from types import MappingProxyType
from typing import Any, Literal

from dxp.identity import normalise_name

__all__ = [
    "EARLY_RESEARCH_STAGES",
    "FIELDS",
    "FIELD_KEYS",
    "LOW_CONFIDENCE_THRESHOLD",
    "NOT_DETERMINED",
    "STAGE_ORDER",
    "CanonicalError",
    "Field",
    "canonical",
    "describe",
    "get_field",
    "is_early_research",
    "is_later_stage",
    "is_low_confidence",
    "stage_rank",
]

Cardinality = Literal["single", "list"]

# A value whose check confidence is below this is listed first for the
# Reviewer (AD-4). One number, read by the gate's min_confidence default
# and the web app through GET /schema.
LOW_CONFIDENCE_THRESHOLD: float = 0.7


class CanonicalError(ValueError):
    """``raw`` has no canonical form for ``field``. The caller records a
    failure; it never stores the raw text as a value."""

    def __init__(self, field: str, raw: Any, reason: str) -> None:
        super().__init__(f"{field}: cannot canonicalise {raw!r}: {reason}")
        self.field = field
        self.raw = raw
        self.reason = reason


@dataclass(frozen=True)
class Option:
    value: str
    label: str
    synonyms: tuple[str, ...] = ()


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    cardinality: Cardinality
    canonical_form: str
    options: tuple[Option, ...] = ()
    # Normalised spelling -> canonical value; built in __post_init__.
    _lookup: Mapping[str, str] = dc_field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        lookup: dict[str, str] = {}
        for opt in self.options:
            for spelling in (opt.value, opt.value.replace("_", " "), opt.label, *opt.synonyms):
                key = normalise_name(spelling)
                if not key:
                    continue
                if key in lookup and lookup[key] != opt.value:
                    raise ValueError(
                        f"registry: {self.key!r} spelling {spelling!r} maps to both "
                        f"{lookup[key]!r} and {opt.value!r}"
                    )
                lookup[key] = opt.value
        object.__setattr__(self, "_lookup", MappingProxyType(lookup))

    @property
    def enum(self) -> tuple[str, ...] | None:
        return tuple(o.value for o in self.options) or None


def _opt(value: str, label: str, *synonyms: str) -> Option:
    return Option(value, label, tuple(synonyms))


# --- Lifecycle stage (AD-5) -------------------------------------------------

STAGE_ORDER: tuple[str, ...] = (
    "discovery",
    "assay_development",
    "analytical_validation",
    "clinical_validation",
    "clinical_utility",
    "regulatory_approval",
    "guideline_inclusion",
    "reimbursement",
    "adoption",
)
NOT_DETERMINED = "not_determined"
EARLY_RESEARCH_STAGES: frozenset[str] = frozenset({"discovery", "assay_development"})

_STAGE_LABELS = {
    "discovery": "Discovery",
    "assay_development": "Assay development",
    "analytical_validation": "Analytical validation",
    "clinical_validation": "Clinical validation",
    "clinical_utility": "Clinical utility",
    "regulatory_approval": "Regulatory approval",
    "guideline_inclusion": "Guideline inclusion",
    "reimbursement": "Reimbursement",
    "adoption": "Adoption",
    NOT_DETERMINED: "Stage not determined",
}

# --- Hand-written maps for the seeded rows and the selected trials ----------

# HGNC approved symbols, with the spellings sources use.
_BIOMARKER_GENES: tuple[Option, ...] = (
    _opt("EGFR", "EGFR", "epidermal growth factor receptor", "her1", "erbb1"),
    _opt("ALK", "ALK", "anaplastic lymphoma kinase"),
    _opt("ROS1", "ROS1"),
    _opt("BRAF", "BRAF"),
    _opt("KRAS", "KRAS", "k ras"),
    _opt("NRAS", "NRAS"),
    _opt("MET", "MET", "c met", "cmet"),
    _opt("RET", "RET"),
    _opt("ERBB2", "ERBB2", "her2", "her 2", "her2 neu", "neu"),
    _opt("NTRK1", "NTRK1"),
    _opt("NTRK2", "NTRK2"),
    _opt("NTRK3", "NTRK3"),
    _opt("CD274", "CD274 (PD-L1)", "pd l1", "pdl1", "programmed death ligand 1",
         "programmed cell death ligand 1"),
    _opt("PIK3CA", "PIK3CA"),
    _opt("TP53", "TP53", "p53"),
    _opt("STK11", "STK11", "lkb1"),
    _opt("KEAP1", "KEAP1"),
    _opt("BRCA1", "BRCA1"),
    _opt("BRCA2", "BRCA2"),
    _opt("NRG1", "NRG1"),
)
# Analytes that are not one gene: registry enum values.
_BIOMARKER_ANALYTES: tuple[Option, ...] = (
    _opt("tmb", "Tumour mutational burden", "tumor mutational burden", "tmb high"),
    _opt("msi", "Microsatellite instability", "msi high", "msi h"),
    _opt("ctdna", "Circulating tumour DNA (any alteration)", "circulating tumor dna",
         "circulating tumour dna", "cell free tumor dna"),
)

# OncoTree codes for the lung tumour types in scope.
_TUMOUR_TYPES: tuple[Option, ...] = (
    _opt("NSCLC", "Non-small cell lung cancer", "non small cell lung cancer",
         "non small cell lung carcinoma", "non small cell lung neoplasm"),
    _opt("LUAD", "Lung adenocarcinoma", "adenocarcinoma of the lung",
         "lung adenocarcinoma", "adenocarcinoma of lung"),
    _opt("LUSC", "Lung squamous cell carcinoma", "squamous cell lung cancer",
         "squamous cell carcinoma of the lung", "squamous non small cell lung cancer"),
    _opt("SCLC", "Small cell lung cancer", "small cell lung carcinoma"),
    _opt("LUNG", "Lung", "lung cancer", "carcinoma of the lung", "lung carcinoma"),
)

# --- The fields (AD-2) --------------------------------------------------------

_FIELD_LIST: tuple[Field, ...] = (
    Field("modality", "Diagnostic method or modality", "single", "enum", (
        _opt("ngs", "Next-generation sequencing", "next generation sequencing",
             "targeted sequencing", "hybrid capture sequencing", "massively parallel sequencing"),
        _opt("pcr", "PCR", "polymerase chain reaction", "real time pcr", "rt pcr", "qpcr",
             "digital pcr", "ddpcr", "droplet digital pcr"),
        _opt("ihc", "Immunohistochemistry", "immunohistochemical"),
        _opt("fish", "Fluorescence in situ hybridisation", "fluorescence in situ hybridization"),
        _opt("other", "Other method"),
    )),
    Field("biomarkers", "Biomarker or gene", "list", "hgnc_symbol_or_enum",
          _BIOMARKER_GENES + _BIOMARKER_ANALYTES),
    Field("tumour_types", "Tumour type", "list", "oncotree_code", _TUMOUR_TYPES),
    Field("tumour_stage_or_line", "Stage or line of therapy", "list", "enum", (
        _opt("early_stage", "Early stage", "early stage", "resectable"),
        _opt("stage_i", "Stage I", "stage 1", "stage ia", "stage ib"),
        _opt("stage_ii", "Stage II", "stage 2", "stage iia", "stage iib"),
        _opt("stage_iii", "Stage III", "stage 3", "stage iiia", "stage iiib", "stage iiic"),
        _opt("stage_iv", "Stage IV", "stage 4", "stage iva", "stage ivb"),
        _opt("locally_advanced", "Locally advanced", "unresectable locally advanced"),
        _opt("metastatic", "Advanced or metastatic", "advanced", "advanced or metastatic",
             "advanced metastatic"),
        _opt("neoadjuvant", "Neoadjuvant", "preoperative"),
        _opt("adjuvant", "Adjuvant", "postoperative"),
        _opt("perioperative", "Perioperative"),
        _opt("first_line", "First line", "1l", "first line therapy", "treatment naive"),
        _opt("second_line_or_later", "Second line or later", "second line", "2l",
             "later line", "previously treated"),
        _opt("maintenance", "Maintenance"),
    )),
    Field("sample_types", "Sample type", "list", "enum", (
        _opt("plasma", "Plasma (cell-free DNA)", "cfdna", "cell free dna", "ctdna",
             "liquid biopsy", "plasma cfdna"),
        _opt("blood", "Blood", "whole blood", "peripheral blood"),
        _opt("tissue", "Tissue", "tumour tissue", "tumor tissue", "ffpe", "ffpe tissue",
             "formalin fixed paraffin embedded tissue", "tissue biopsy"),
        _opt("urine", "Urine"),
    )),
    Field("clinical_uses", "Clinical use", "list", "enum", (
        _opt("screening", "Screening", "early detection"),
        _opt("treatment_selection", "Treatment selection", "companion diagnostic",
             "therapy selection", "patient selection"),
        _opt("monitoring", "Monitoring", "treatment monitoring", "response monitoring"),
        _opt("mrd", "Minimal residual disease", "molecular residual disease"),
    )),
    Field("study_results", "Study size and key result", "list", "text"),
    Field("provider", "Sponsor or company", "single", "normalised_name"),
    Field("trials", "Trial ID (NCT)", "list", "nct_id"),
    Field("linked_drugs", "Linked drug", "list", "generic_name"),
    Field("regulatory_status", "Regulatory status", "single", "enum", (
        _opt("fda_approved", "FDA approved (PMA)", "pma", "approved", "fda approved",
             "premarket approval"),
        _opt("fda_cleared", "FDA cleared (510(k))", "510 k", "510k", "cleared", "fda cleared"),
        _opt("fda_de_novo", "FDA De Novo", "de novo"),
        _opt("ce_marked", "CE marked", "ce mark", "ce ivd"),
        _opt("health_canada_licensed", "Health Canada licensed", "health canada"),
        _opt("ldt", "Laboratory-developed test", "laboratory developed test",
             "lab developed test"),
        _opt("investigational", "Investigational", "investigational use only", "iuo"),
        _opt("research_use_only", "Research use only", "ruo"),
        _opt("not_determined", "Not determined"),
    )),
    Field("lifecycle_stage", "Lifecycle stage", "single", "enum", tuple(
        _opt(s, _STAGE_LABELS[s]) for s in (*STAGE_ORDER, NOT_DETERMINED)
    )),
)

FIELDS: Mapping[str, Field] = MappingProxyType({f.key: f for f in _FIELD_LIST})
FIELD_KEYS: tuple[str, ...] = tuple(FIELDS)


def get_field(key: str) -> Field:
    try:
        return FIELDS[key]
    except KeyError:
        raise KeyError(f"unknown registry field {key!r}") from None


# --- canonical() ----------------------------------------------------------------

_NCT = re.compile(r"NCT\d{8}")
_MARKS = str.maketrans("", "", "®™©")
_SPACE = re.compile(r"\s+")


def _collapse(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


def _enum(f: Field, raw: str) -> str:
    key = normalise_name(raw)
    if key in f._lookup:
        return f._lookup[key]
    raise CanonicalError(f.key, raw, "not a registry value")


def _biomarker(f: Field, raw: str) -> str:
    # The marker is the leading word or words; what follows ("exon 19
    # deletion", "G12C", "expression") is detail and never affects identity.
    tokens = normalise_name(raw).split(" ")
    for end in range(len(tokens), 0, -1):
        hit = f._lookup.get(" ".join(tokens[:end]))
        if hit is not None:
            return hit
    raise CanonicalError(f.key, raw, "not a known HGNC symbol or analyte")


def _canon_text(raw: str) -> str:
    return _collapse(raw)


def _canon_generic_name(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw.translate(_MARKS)).translate(_MARKS)
    return _collapse(text).lower()


def _canon_nct(f: Field, raw: str) -> str:
    text = raw.strip().upper()
    if not _NCT.fullmatch(text):
        raise CanonicalError(f.key, raw, "not an NCT ID (NCT followed by 8 digits)")
    return text


def canonical(field: str, raw: Any) -> str:
    """Return the canonical ``value`` string for ``raw`` in ``field`` (AD-2).

    Raises ``CanonicalError`` when there is none, and ``KeyError`` for an
    unknown field. The text as written belongs in the entry's ``label``.
    """
    f = get_field(field)
    if not isinstance(raw, str):
        raise CanonicalError(field, raw, "value must be a string")
    if not raw.strip():
        raise CanonicalError(field, raw, "empty value")
    form = f.canonical_form
    if form in ("enum", "oncotree_code"):
        out = _enum(f, raw)
    elif form == "hgnc_symbol_or_enum":
        out = _biomarker(f, raw)
    elif form == "normalised_name":
        out = normalise_name(raw)
    elif form == "nct_id":
        out = _canon_nct(f, raw)
    elif form == "generic_name":
        out = _canon_generic_name(raw)
    elif form == "text":
        out = _canon_text(raw)
    else:  # pragma: no cover - guarded by the field table above
        raise AssertionError(f"no canonical form {form!r}")
    if not out:
        raise CanonicalError(field, raw, "nothing left after normalising")
    return out


# --- Lifecycle helpers (AD-5) ------------------------------------------------------


def stage_rank(stage: str) -> int:
    """Position in ``STAGE_ORDER``; ``not_determined`` ranks before every stage."""
    if stage == NOT_DETERMINED:
        return -1
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        raise ValueError(f"unknown lifecycle stage {stage!r}") from None


def is_later_stage(new: str, current: str | None) -> bool:
    """True when ``new`` comes after ``current`` (the apply rule of AD-5)."""
    return stage_rank(new) > stage_rank(current or NOT_DETERMINED)


def is_early_research(stage: str | None) -> bool:
    """The only test for the Early research label (AD-5): discovery and
    assay development. The label is never stored."""
    return stage in EARLY_RESEARCH_STAGES


def is_low_confidence(confidence: float | None) -> bool:
    return confidence is None or confidence < LOW_CONFIDENCE_THRESHOLD


# --- GET /schema --------------------------------------------------------------------


def describe() -> dict[str, Any]:
    """The registry as plain JSON for ``GET /api/v1/schema``: fields with
    cardinality, canonical form and enum options, the stage order, the Early
    research stages and the low-confidence threshold."""
    return {
        "fields": [
            {
                "key": f.key,
                "label": f.label,
                "cardinality": f.cardinality,
                "canonical_form": f.canonical_form,
                "enum": [{"value": o.value, "label": o.label} for o in f.options] or None,
            }
            for f in _FIELD_LIST
        ],
        "stage_order": list(STAGE_ORDER),
        "not_determined_stage": NOT_DETERMINED,
        "early_research_stages": [s for s in STAGE_ORDER if s in EARLY_RESEARCH_STAGES],
        "low_confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
    }
