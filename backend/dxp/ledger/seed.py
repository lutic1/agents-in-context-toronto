"""python -m dxp.ledger.seed: Diagnostics from fda_cdx_list Source items, and the synthetic Teams
(A13, Story 1.2).

Run from the command line only, with the dedicated seed key ``DXP_SEED_KEY`` (AD-18), after
``python -m dxp.gate.seed`` (the seed grant) and ``python -m dxp.sources.fda_cdx`` (the rows).

- Each lung row's trade name is one Diagnostic, found through ``aliases`` by its ID alias,
  ``normalise_name(<trade name as the list writes it>)``; no other alias is added (V34). The
  ledger's ``ensure_diagnostic`` writes the alias and the Diagnostic; this module never writes
  ``aliases`` or ``diagnostics`` itself (AD-1). FoundationOne CDx (tissue) and FoundationOne
  Liquid CDx (plasma) are two Diagnostics and are never merged.
- Every value goes through ``ledger.file(finding_id, changes, "baseline", ctx)`` under
  ``seed@v1``, with a ``RunContext`` that carries the seed principal and the seed stamp
  ``{ kind: seed, principal: seed, run_id: null }``; the ledger gates it and applies it at once as ``unreviewed`` (AD-1, AD-4).
- Values are set by rule from the row, with no model call: ``lifecycle_stage`` is
  ``regulatory_approval``; ``regulatory_status`` follows the number (P: PMA, K: 510(k),
  DEN: De Novo); ``provider`` is the manufacturer; ``biomarkers``, ``linked_drugs``,
  ``tumour_types``, ``sample_types`` and ``clinical_uses`` (treatment selection: the list is of
  companion diagnostics) come from the row's cells, canonicalised by the registry. A cell the
  registry cannot canonicalise is skipped, never stored raw.
- The Finding of a row is ``derive("f_", version_id, diagnostic_id)`` and each change's
  proposal is ``derive("p_", finding_id, field, value)`` (AD-3, D20). A change whose proposal
  already exists is not filed again, so a second run creates and changes nothing.
- The three synthetic Teams are inserted into ``teams`` insert-if-absent, with
  ``synthetic: true``. "Team Liquid Biopsy Dx" gets ``derive("team_", "Team Liquid Biopsy Dx")``,
  the ID A03's grants act for.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import os
import re
import sys
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from dxp.api.models import Principal, RunContext, Stamp
from dxp.identity import derive, diagnostic_id
from dxp.schema import registry
from dxp.sources import fda_cdx

__all__ = [
    "SEED_KEY_VAR",
    "SEED_STAMP",
    "TEAMS",
    "PlannedChange",
    "SeedError",
    "SeedReport",
    "plan_changes",
    "seed",
    "seed_context",
    "seed_diagnostics",
    "seed_teams",
    "team_documents",
    "team_id",
]

SEED_KEY_VAR = "DXP_SEED_KEY"
SEED_GRANT_ID = "seed"
SEED_STAMP: dict[str, Any] = {"kind": "seed", "principal": "seed", "run_id": None}
TRIGGER = "fda_seed"

FileFn = Callable[[str, list[dict[str, Any]], str, RunContext], Awaitable[Any]]


class SeedError(RuntimeError):
    """The seed refused to run (no key, wrong key, no seed grant, no rows)."""


# ---------------------------------------------------------------------------
# Teams (D56, Story 1.2): three synthetic Teams with a profile on modality, biomarker and drug
# ---------------------------------------------------------------------------

LBDX_TEAM = "Team Liquid Biopsy Dx"

TEAMS: tuple[dict[str, Any], ...] = (
    {
        "name": LBDX_TEAM,
        "profile": {
            "modalities": ["ngs"],
            "biomarkers": ["EGFR", "ALK", "ROS1", "KRAS", "MET", "ERBB2", "BRAF"],
            "linked_drugs": ["osimertinib", "sotorasib", "adagrasib", "tepotinib", "capmatinib"],
        },
    },
    {
        "name": "Team Tissue Genomics Dx",
        "profile": {
            "modalities": ["ngs", "pcr"],
            "biomarkers": ["EGFR", "ALK", "ROS1", "RET", "BRAF", "MET"],
            "linked_drugs": ["alectinib", "crizotinib", "selpercatinib", "dabrafenib"],
        },
    },
    {
        "name": "Team Immunohistochemistry Dx",
        "profile": {
            "modalities": ["ihc"],
            "biomarkers": ["CD274", "ALK", "MET"],
            "linked_drugs": ["pembrolizumab", "atezolizumab", "nivolumab"],
        },
    },
)


def team_id(name: str) -> str:
    """The Team's ID, ``derive("team_", name)``: the same rule A03's grant seed uses."""
    return derive("team_", name)


def team_documents(created_at: datetime | None = None) -> list[dict[str, Any]]:
    created_at = created_at or datetime.now(UTC)
    return [
        {
            "_id": team_id(t["name"]),
            "name": t["name"],
            "profile": {k: list(v) for k, v in t["profile"].items()},
            "synthetic": True,
            "last_seen_seq": None,
            "last_seen_at": None,
            "created_at": created_at,
        }
        for t in TEAMS
    ]


async def seed_teams(db: Any, created_at: datetime | None = None) -> dict[str, int]:
    """Insert the three synthetic Teams, insert-if-absent. Returns counts."""
    counts = {"inserted": 0, "existing": 0}
    for doc in team_documents(created_at):
        if await fda_cdx.insert_if_absent(db["teams"], doc):
            counts["inserted"] += 1
        else:
            counts["existing"] += 1
    return counts


# ---------------------------------------------------------------------------
# The seed context (AD-17, D19): no run, the seed grant, the seed stamp
# ---------------------------------------------------------------------------


def seed_context(grant_version: int = 1) -> RunContext:
    """The ``RunContext`` ``ledger.file`` receives for a seed write (the frozen A01 signature).

    No run (``run_id`` null), the seed principal (``kind: seed``), the seed grant ``seed`` at
    the version in force, ``baseline`` mode and the seed stamp ``{ kind: seed, principal:
    seed, run_id: null }`` (AD-17, D19). The ledger and gate record ``agent`` and
    ``initiated_by`` as ``seed`` on each Decision from this seed principal.
    """
    return RunContext(
        run_id=None,
        principal=Principal(id="seed", name="seed", kind="seed", actions=["apply_value"]),
        stamp=Stamp(**SEED_STAMP),
        grant_id=SEED_GRANT_ID,
        grant_version=grant_version,
        mode="baseline",
    )


async def seed_grant(db: Any) -> dict[str, Any] | None:
    """The latest stored version of the seed grant, or None."""
    return await db["grants"].find_one({"grant_id": SEED_GRANT_ID}, sort=[("version", -1)])


# ---------------------------------------------------------------------------
# Planning: which values each row yields, by rule
# ---------------------------------------------------------------------------

_REGULATORY_STATUS = (("DEN", "fda_de_novo"), ("P", "fda_approved"), ("K", "fda_cleared"))
_PARENS = re.compile(r"\(([^()]*)\)")
_SAMPLE_SPLIT = re.compile(r"\s*(?:,|/|\bor\b|\band\b)\s*", re.IGNORECASE)
# Single fields are set once per Diagnostic, from its first row.
_SINGLE_FIELDS = ("lifecycle_stage", "regulatory_status", "provider")


@dataclass(frozen=True)
class PlannedChange:
    """One value to file: its Finding, the change the ledger receives, its derived proposal ID."""

    finding_id: str
    proposal_id: str
    diagnostic_id: str
    change: dict[str, Any]

    @property
    def field(self) -> str:
        return self.change["field"]

    @property
    def value(self) -> str:
        return self.change["value"]


def _canonical(field_key: str, raw: str) -> str | None:
    try:
        return registry.canonical(field_key, raw)
    except registry.CanonicalError:
        return None


def _regulatory_status(number: str | None) -> str | None:
    for prefix, status in _REGULATORY_STATUS:
        if number and number.startswith(prefix):
            return status
    return None


def _tumour_type(disease: str) -> str | None:
    bare = _PARENS.sub(" ", disease)
    for candidate in (bare, *(_PARENS.findall(disease))):
        value = _canonical("tumour_types", candidate)
        if value:
            return value
    return None


def _sample_types(sample_text: str | None) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for part in _SAMPLE_SPLIT.split(sample_text or ""):
        value = _canonical("sample_types", part) if part.strip() else None
        if value and value not in (v for v, _ in out):
            out.append((value, part.strip()))
    return out


def _linked_drugs(drug_cell: str) -> list[tuple[str, str]]:
    """Generic names are the parenthesised part of "Brand (generic) NDA 123456"."""
    out: list[tuple[str, str]] = []
    for generic in _PARENS.findall(drug_cell):
        value = _canonical("linked_drugs", generic)
        if value and value not in (v for v, _ in out):
            out.append((value, generic.strip()))
    return out


def row_values(row: fda_cdx.FdaRow) -> list[tuple[str, str, str, dict[str, Any] | None]]:
    """``(field, canonical value, label as written, detail)`` for one row, in filing order."""
    values: list[tuple[str, str, str, dict[str, Any] | None]] = [
        ("lifecycle_stage", "regulatory_approval", "Regulatory approval", None),
    ]
    status = _regulatory_status(row.number)
    if status:
        values.append(("regulatory_status", status, row.approval, None))
    if row.manufacturer:
        provider = _canonical("provider", row.manufacturer)
        if provider:
            values.append(("provider", provider, row.manufacturer, None))
    values.append(("clinical_uses", "treatment_selection", "Companion diagnostic", None))
    biomarker = _canonical("biomarkers", row.biomarker)
    if biomarker:
        values.append(("biomarkers", biomarker, row.biomarker, {"details": row.biomarker_details}))
    tumour = _tumour_type(row.disease)
    if tumour:
        values.append(("tumour_types", tumour, row.disease, None))
    for value, label in _sample_types(row.sample_text):
        values.append(("sample_types", value, label, None))
    for value, label in _linked_drugs(row.drug):
        values.append(("linked_drugs", value, label, {"drug": row.drug}))
    return values


def plan_changes(items: Iterable[dict[str, Any]]) -> list[PlannedChange]:
    """Every value the stored FDA rows yield, one per (Diagnostic, field, value).

    Rows are taken in ``_id`` order, so the plan is the same on every run. A value repeated by
    a later row of the same Diagnostic is filed once, from the first row that states it.
    """
    planned: list[PlannedChange] = []
    seen: set[tuple[str, str, str]] = set()
    single_done: set[tuple[str, str]] = set()
    for item in sorted(items, key=lambda d: d["_id"]):
        row = fda_cdx.row_from_item(item)
        dx_id = diagnostic_id(row.trade_name)
        version = item.get("current_version_id") or fda_cdx.version_id(item["_id"], item["raw_text"])
        finding = derive("f_", version, dx_id)
        evidence = {
            "source_ref": item["_id"],
            "version_id": version,
            "source": fda_cdx.SOURCE,
            "source_url": item.get("source_url") or fda_cdx.FDA_URL,
            "source_date": item.get("source_date"),
            "quote": fda_cdx.quote_for(row),
            "data_as_of": item.get("list_date") or item.get("source_date"),
        }
        for field_key, value, label, detail in row_values(row):
            key = (dx_id, field_key, value)
            if key in seen or (field_key in _SINGLE_FIELDS and (dx_id, field_key) in single_done):
                continue
            seen.add(key)
            if field_key in _SINGLE_FIELDS:
                single_done.add((dx_id, field_key))
            change = {
                "field": field_key,
                "value": value,
                "label": label,
                "detail": detail,
                # The exact trade-name string: the ledger's ensure_diagnostic matches or creates
                # the Diagnostic through the alias normalise_name(assay_name) (AD-3, V34).
                "assay_name": row.trade_name,
                "diagnostic_name": row.trade_name,
                "evidence": dict(evidence),
                # Set by rule from the row it quotes, not by a model (AD-6 n/a for apply_value).
                "check": {"quote_found": True, "supported": True, "confidence": 1.0, "flags": []},
                "trigger": TRIGGER,
            }
            planned.append(
                PlannedChange(
                    finding_id=finding,
                    proposal_id=derive("p_", finding, field_key, value),
                    diagnostic_id=dx_id,
                    change=change,
                )
            )
    return planned


# ---------------------------------------------------------------------------
# Running the seed
# ---------------------------------------------------------------------------


@dataclass
class SeedReport:
    rows: int = 0
    diagnostics: list[str] = field(default_factory=list)
    filed: int = 0
    skipped_existing: int = 0
    blocked: list[str] = field(default_factory=list)
    teams: dict[str, int] = field(default_factory=dict)


def _outcomes(result: Any) -> list[str]:
    """Statuses the ledger returned for one call (A06's ``Filed`` or a Decision list)."""
    out: list[str] = []
    for item in result if isinstance(result, list) else [result]:
        status = getattr(item, "status", None) or getattr(item, "outcome", None)
        if status is None and isinstance(item, dict):
            status = item.get("status") or item.get("outcome")
        out.append(str(status) if status is not None else "unknown")
    return out


async def seed_diagnostics(db: Any, *, file: FileFn | None = None, ctx: RunContext | None = None) -> SeedReport:
    """File every planned value through the ledger, skipping proposals that already exist."""
    if file is None:
        from dxp import ledger

        file = ledger.file
    if ctx is None:
        grant = await seed_grant(db)
        ctx = seed_context(int(grant["version"]) if grant else 1)
    if not isinstance(ctx, RunContext):
        raise TypeError("ledger.file takes a RunContext (frozen A01 signature)")
    items = [doc async for doc in db["source_items"].find({"source": fda_cdx.SOURCE})]
    report = SeedReport(rows=len(items))
    if not items:
        raise SeedError("no fda_cdx_list Source items: run python -m dxp.sources.fda_cdx first")
    plan = plan_changes(items)
    report.diagnostics = sorted({p.change["diagnostic_name"] for p in plan})
    for planned in plan:
        if await db["proposals"].find_one({"_id": planned.proposal_id}, {"_id": 1}) is not None:
            report.skipped_existing += 1
            continue
        result = file(planned.finding_id, [planned.change], "baseline", ctx)
        if inspect.isawaitable(result):
            result = await result
        statuses = _outcomes(result)
        if "blocked" in statuses:
            report.blocked.append(f"{planned.change['diagnostic_name']}: {planned.field}={planned.value}")
        else:
            report.filed += 1
    return report


async def check_seed_key(db: Any, env: dict[str, str] | None = None) -> None:
    """The seed runs only with ``DXP_SEED_KEY`` matching the latest active ``seed`` grant."""
    env = dict(os.environ) if env is None else env
    key = env.get(SEED_KEY_VAR, "")
    if not key:
        raise SeedError(f"{SEED_KEY_VAR} is not set: the seed runs only with the seed key (AD-18)")
    grant = await seed_grant(db)
    if grant is None:
        raise SeedError("no seed grant: run python -m dxp.gate.seed first")
    if grant.get("key_hash") != hashlib.sha256(key.encode("utf-8")).hexdigest():
        raise SeedError(f"{SEED_KEY_VAR} does not match the seed grant")
    if grant.get("status") != "active":
        raise SeedError(f"the seed grant {grant.get('_id')} is {grant.get('status')}")


async def seed(db: Any, *, file: FileFn | None = None, ctx: RunContext | None = None) -> SeedReport:
    """The Diagnostics from the stored FDA rows, then the Teams. Safe to run twice."""
    report = await seed_diagnostics(db, file=file, ctx=ctx)
    report.teams = await seed_teams(db)
    return report


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dxp.ledger.seed", description=__doc__.splitlines()[0])
    parser.add_argument("--plan", action="store_true", help="print the planned values; file nothing")
    args = parser.parse_args(argv)

    from dxp import store

    try:
        db = store.get_db()
        if args.plan:
            items = [doc async for doc in db["source_items"].find({"source": fda_cdx.SOURCE})]
            for p in plan_changes(items):
                print(f"{p.change['diagnostic_name']}\t{p.field}\t{p.value}\t{p.proposal_id}")
            return 0
        await store.ensure_indexes()
        await check_seed_key(db)
        report = await seed(db)
    except SeedError as exc:
        print(f"seed refused: {exc}", file=sys.stderr)
        return 2
    finally:
        await store.close()
    print(
        f"FDA seed: {report.rows} rows, {len(report.diagnostics)} Diagnostics, {report.filed} values filed, "
        f"{report.skipped_existing} already filed, {len(report.blocked)} blocked; "
        f"Teams: {report.teams.get('inserted', 0)} inserted, {report.teams.get('existing', 0)} already present"
    )
    for line in report.blocked:
        print(f"  blocked: {line}")
    return 1 if report.blocked else 0


if __name__ == "__main__":  # pragma: no cover - command line
    sys.exit(asyncio.run(main()))
