"""Print checked Findings for a few trials (Story 1.5, last criterion).

    python -m dxp.llm.cli NCT04712877 NCT05715229 --seeded "FoundationOne CDx" ...

Fetches each trial by NCT ID from the ClinicalTrials.gov API v2 into memory,
extracts it with `llm.extract`, and prints the Findings with their quotes and
checks. It writes nothing: no file, no Atlas document. Needs
`ANTHROPIC_API_KEY`, and A02's `identity` and `registry` for resolution,
IDs and canonical values.

Until A05's `sources/ctgov.py` is on `main`, `item_from_study()` builds a
print-only item here (its `version_id` follows AD-3/V40 but is never stored);
at the rebase this switches to A05's fetch and `evidence_text` builder.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from typing import Any

from dxp.evidence import normalise_for_quote
from dxp.llm import _deps
from dxp.llm.extract import extract_item
from dxp.llm.types import Extraction

CTGOV_STUDY_URL = "https://clinicaltrials.gov/api/v2/studies/{nct_id}"


def _lines(label: str, value: Any) -> list[str]:
    if value is None or value == "" or value == []:
        return []
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value)
    return [f"{label}: {value}"]


def item_from_study(study: dict[str, Any]) -> dict[str, Any]:
    """An in-memory item from a ClinicalTrials.gov API v2 study (print only)."""
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    desc = p.get("descriptionModule", {})
    cond = p.get("conditionsModule", {})
    design = p.get("designModule", {})
    arms = p.get("armsInterventionsModule", {})
    outcomes = p.get("outcomesModule", {})
    elig = p.get("eligibilityModule", {})

    nct_id = ident.get("nctId")
    interventions = [
        {"type": iv.get("type"), "name": iv.get("name"), "otherNames": list(iv.get("otherNames") or [])}
        for iv in arms.get("interventions", [])
        if iv.get("name")
    ]
    lines: list[str] = []
    lines += _lines("Title", ident.get("briefTitle"))
    lines += _lines("Official title", ident.get("officialTitle"))
    lines += _lines("Overall status", status.get("overallStatus"))
    lines += _lines("Brief summary", desc.get("briefSummary"))
    lines += _lines("Detailed description", desc.get("detailedDescription"))
    lines += _lines("Conditions", cond.get("conditions"))
    lines += _lines("Keywords", cond.get("keywords"))
    lines += _lines("Study type", design.get("studyType"))
    lines += _lines("Phases", design.get("phases"))
    for iv in arms.get("interventions", []):
        other = iv.get("otherNames") or []
        suffix = f" (other names: {', '.join(other)})" if other else ""
        lines += _lines("Intervention", f"{iv.get('type')}: {iv.get('name')}{suffix}")
        lines += _lines("Intervention description", iv.get("description"))
    for arm in arms.get("armGroups", []):
        lines += _lines("Arm", f"{arm.get('label')}: {arm.get('description') or ''}".strip())
    for o in outcomes.get("primaryOutcomes", []) + outcomes.get("secondaryOutcomes", []):
        lines += _lines("Outcome measure", o.get("measure"))
    lines += _lines("Eligibility", elig.get("eligibilityCriteria"))
    raw_text = "\n".join(lines)

    source_ref = f"clinicaltrials.gov:{nct_id}"
    last_update = (status.get("lastUpdatePostDateStruct") or {}).get("date")
    content_hash = hashlib.sha256(normalise_for_quote(raw_text).encode()).hexdigest()[:16]
    return {
        "source_ref": source_ref,
        "version_id": _deps.derive("sv_", source_ref, last_update, content_hash),
        "nct_id": nct_id,
        "title": ident.get("briefTitle"),
        "raw_text": raw_text,
        "overall_status": status.get("overallStatus"),
        "has_results": bool(study.get("hasResults")),
        "last_update_posted": last_update,
        "interventions": interventions,
    }


async def fetch_item(nct_id: str) -> dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.get(CTGOV_STUDY_URL.format(nct_id=nct_id))
        response.raise_for_status()
        return item_from_study(response.json())


def render(result: Extraction) -> str:
    out = [f"{result.source_ref}  status={result.status}  version={result.version_id}"]
    out.append(f"  interventions (verbatim): {json.dumps(result.intervention_texts, ensure_ascii=False)}")
    for m in result.mentions:
        out.append(f"  mention {m.name!r} [{m.field}] -> {m.resolved_diagnostic_id or m.resolution}")
    if result.unresolved_names:
        out.append(f"  unresolved names: {json.dumps(result.unresolved_names, ensure_ascii=False)}")
    for f in result.findings:
        out.append(f"  Finding {f.id} diagnostic={f.diagnostic_id or '-'} ({f.target})")
        out.append(f"    summary: {f.summary}")
        for v in f.values:
            c = v.check
            out.append(
                f"    {v.field} = {v.value!r} [quote_found={c.quote_found} supported={c.supported} "
                f"confidence={c.confidence:.2f} passed={v.passed}]"
            )
            out.append(f"      quote: {v.quote!r}")
        if f.stage_evidence:
            se = f.stage_evidence
            out.append(f"    stage = {se.stage} [quote_found={se.check.quote_found} supported={se.check.supported}]")
            out.append(f"      quote: {se.quote!r}")
        for failure in f.failures:
            out.append(f"    failure: {failure.line()}")
    for failure in result.failures:
        out.append(f"  failure: {failure.line()}")
    return "\n".join(out)


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("nct_ids", nargs="+")
    parser.add_argument("--seeded", action="append", default=[], help="a seeded FDA trade name (repeat)")
    args = parser.parse_args(argv)
    for nct_id in args.nct_ids:
        try:
            item = await fetch_item(nct_id)
        except Exception as exc:  # noqa: BLE001
            print(f"{nct_id}: fetch failed ({type(exc).__name__})", file=sys.stderr)
            continue
        result = await extract_item(item, args.seeded or None)
        print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
