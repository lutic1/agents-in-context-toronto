"""A08 fixtures: fakes for the frozen A02 functions and for Claude.

Unit tests replace A02's `identity.resolve_exact` (which reads Atlas) with an
in-memory exact matcher following its contract (V34); `derive` and
`canonical` are faked the same way so expectations stay independent of the
registry tables. `test_a02_wiring.py` runs the real A02 functions. The fixture items hold only the few public
ClinicalTrials.gov phrases a test needs (titles, intervention names, status),
never a fetched record and never PubMed text.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

import pytest

from dxp.llm import _deps, client

# The four D45 scope strings plus the tissue test (seeded from the FDA list).
SEEDED = {
    "FoundationOne CDx": "dx_tissue_f1cdx",
    "FoundationOne Liquid CDx": "dx_plasma_f1lcdx",
    "Guardant360 CDx": "dx_g360cdx",
    "Guardant360® Liquid CDx": "dx_g360lcdx",
    "Agilent Resolution ctDx FIRST assay": "dx_agilent",
}
SEEDED_NAMES = list(SEEDED)
STAGES = ("discovery", "assay_development", "clinical_validation", "regulatory_approval")


def normalise_name(text: str) -> str:
    """AD-3 reference: NFKC, lower case, drop (R)(TM)(C), non-alphanumerics to one space."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[®™©]", "", text)
    return re.sub(r"[^0-9a-z]+", " ", text).strip()


_BY_NORMAL = {normalise_name(k): v for k, v in SEEDED.items()}


def fake_resolve_exact(name: str) -> str | None:
    return _BY_NORMAL.get(normalise_name(name))


def fake_derive(prefix: str, *parts: Any) -> str:
    joined = "|".join(str(p) for p in parts)
    return prefix + hashlib.sha256(joined.encode()).hexdigest()[:16]


def fake_canonical(field: str, raw: str) -> str | None:
    if field == "lifecycle_stage":
        value = raw.strip().lower().replace(" ", "_")
        return value if value in STAGES else None
    if field == "trials":
        return raw.strip().upper()
    return " ".join(raw.split())


@pytest.fixture
def fake_registry(monkeypatch):
    async def resolve(name: str) -> str | None:
        return fake_resolve_exact(name)

    monkeypatch.setattr(_deps, "resolve_exact", resolve)
    monkeypatch.setattr(_deps, "derive", fake_derive)
    monkeypatch.setattr(_deps, "canonical", fake_canonical)
    monkeypatch.setattr(_deps, "stage_names", lambda: STAGES)
    return SEEDED


# --------------------------------------------------------------------------
# Fake Claude
# --------------------------------------------------------------------------


class FakeRaw:
    def __init__(self, stop_reason: str = "end_turn"):
        self.response_metadata = {"stop_reason": stop_reason}


class FakeLLM:
    """Scripted answers per schema name. Each script entry is either a parsed
    object, an exception to raise, or a dict result passed through as is."""

    def __init__(self):
        self.scripts: dict[str, list[Any]] = {}
        self.calls: list[dict[str, Any]] = []
        self.active = 0
        self.max_active = 0
        self.sleeps: list[float] = []
        self.gate = None  # optional asyncio.Event to hold calls open

    def script(self, schema_name: str, *answers: Any) -> None:
        self.scripts.setdefault(schema_name, []).extend(answers)

    def make_runnable(self, model_id: str, schema: type) -> Any:
        llm = self

        class Runnable:
            async def ainvoke(self, messages):
                name = schema["title"] if isinstance(schema, dict) else schema.__name__
                llm.calls.append({"model": model_id, "schema": name, "messages": messages})
                llm.active += 1
                llm.max_active = max(llm.max_active, llm.active)
                try:
                    if llm.gate is not None:
                        await llm.gate.wait()
                    queue = llm.scripts.get(name) or []
                    if not queue:
                        raise AssertionError(f"no scripted answer for {name}")
                    answer = queue.pop(0)
                    if isinstance(answer, BaseException):
                        raise answer
                    if isinstance(answer, dict):
                        return answer
                    return {"raw": FakeRaw(), "parsed": answer, "parsing_error": None}
                finally:
                    llm.active -= 1

        return Runnable()

    def calls_for(self, schema_name: str) -> list[dict[str, Any]]:
        return [c for c in self.calls if c["schema"] == schema_name]


@pytest.fixture
def fake_llm(monkeypatch):
    llm = FakeLLM()
    monkeypatch.setattr(client, "_make_runnable", llm.make_runnable)

    async def no_sleep(delay: float) -> None:
        llm.sleeps.append(delay)

    monkeypatch.setattr(client, "_sleep", no_sleep)
    client._semaphores.clear()
    return llm


# --------------------------------------------------------------------------
# Items (minimal public phrases only)
# --------------------------------------------------------------------------

NCT04712877_TITLE = (
    "Testing Tumor Tissue and Blood to Help Select Personalized Treatments for "
    "Patients With Suspected Lung Cancers"
)
NCT05715229_TITLE = (
    "Immune Profile Selection By Fraction of ctDNA in Patients With Advanced NSCLC "
    "Treated With Immunotherapy"
)


@pytest.fixture
def item_nct04712877() -> dict[str, Any]:
    raw_text = "\n".join(
        [
            NCT04712877_TITLE,
            "Conditions: Lung Cancer",
            "Interventions: DIAGNOSTIC_TEST: ctDNA, tumor NGS (other names: FoundationOne CDx, FoundationOne Liquid)",
            "Overall status: RECRUITING",
        ]
    )
    return {
        "_id": "sv_test04712877aaaa",
        "source_ref": "clinicaltrials.gov:NCT04712877",
        "title": NCT04712877_TITLE,
        "raw_text": raw_text,
        "overall_status": "RECRUITING",
        "has_results": False,
        "interventions": [
            {
                "type": "DIAGNOSTIC_TEST",
                "name": "ctDNA, tumor NGS",
                "otherNames": ["FoundationOne CDx", "FoundationOne Liquid"],
            }
        ],
    }


@pytest.fixture
def item_nct05715229() -> dict[str, Any]:
    raw_text = "\n".join(
        [
            NCT05715229_TITLE,
            "Conditions: Non-small Cell Lung Cancer",
            "Interventions: DRUG: Nivolumab (other names: Opdivo)",
            "Overall status: TERMINATED",
        ]
    )
    return {
        "_id": "sv_test05715229bbbb",
        "source_ref": "clinicaltrials.gov:NCT05715229",
        "title": NCT05715229_TITLE,
        "raw_text": raw_text,
        "overall_status": "TERMINATED",
        "has_results": False,
        "interventions": [{"type": "DRUG", "name": "Nivolumab", "otherNames": ["Opdivo"]}],
    }
