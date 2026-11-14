"""Print checked Findings for a few trials (Story 1.5, last criterion).

    python -m dxp.llm.cli NCT04712877 NCT05715229 --seeded "FoundationOne CDx" ...

Fetches each trial by NCT ID through A05's ClinicalTrials.gov client
(`sources.ctgov.fetch_study` and `parse_study`), builds the item exactly as a
`source_versions` document would hold it (same `raw_text`, same
`version_id`, `load.version_id_for`), extracts it with `llm.extract`, and
prints the Findings with their quotes and checks. It writes nothing: no file,
no Atlas document. Needs `ANTHROPIC_API_KEY`; name resolution reads the store's
`aliases` collection (A02), so run it against a seeded database.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from dxp.llm.extract import extract_item
from dxp.llm.types import Extraction
from dxp.sources import ctgov
from dxp.sources import load as source_load


def item_from_study(study: dict[str, Any]) -> dict[str, Any]:
    """The item a stored source version would be (A05's parse and version ID), in memory only."""
    record = ctgov.parse_study(study)
    version_id = source_load.version_id_for(
        record["source_ref"], record.get("last_update_post_date"), record["content_hash"]
    )
    return {"_id": version_id, "version_id": version_id, **record}


async def fetch_item(nct_id: str) -> dict[str, Any]:
    return item_from_study(await ctgov.fetch_study(ctgov.check_nct(nct_id)))


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
