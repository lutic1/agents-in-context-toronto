#!/usr/bin/env python3
"""Download the DxP ClinicalTrials.gov Baseline load and Held-back set into data/clinicaltrials/.

Run from the repository root:
    uv run --python 3.12 python scripts/data/fetch_clinicaltrials.py
Standard library only. Uses dxp_sources.fetch_ctgov unchanged (about 1 request per 1.2 s).
"""
import hashlib, json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dxp_sources as S

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "data", "clinicaltrials")
RECENT_FROM = "2024-11-14"
NARROW_TERM = ('ctDNA OR "circulating tumor DNA" OR "liquid biopsy" OR MRD OR "minimal residual disease" '
               'OR "molecular residual disease" OR "companion diagnostic"')
COMMAND = "uv run --python 3.12 python scripts/data/fetch_clinicaltrials.py"


def write_jsonl(path, items):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def fetch_ids(window):
    """Fields-limited request: NCT IDs only, for the narrow topics."""
    flt = {"baseline": "AREA[LastUpdatePostDate]RANGE[MIN,%s]" % S.BASELINE_END.isoformat(),
           "heldback": "AREA[LastUpdatePostDate]RANGE[%s,MAX]" % S.CUTOFF.isoformat()}[window]
    params = {"query.cond": S.CTGOV_COND, "query.term": NARROW_TERM, "filter.advanced": flt,
              "fields": "NCTId", "pageSize": 1000, "countTotal": "true"}
    ids, token = [], None
    while True:
        p = dict(params, pageToken=token) if token else params
        page = json.loads(S.http_get(S.CTGOV + "/studies", p, 1.2)[0])
        ids += [s["protocolSection"]["identificationModule"]["nctId"] for s in page.get("studies", [])]
        token = page.get("nextPageToken")
        if not token:
            return sorted(ids)


def main():
    os.makedirs(OUT, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    version = json.loads(S.http_get(S.CTGOV + "/version", None, 1.2)[0])
    baseline = S.fetch_ctgov("baseline")
    heldback = S.fetch_ctgov("heldback")
    narrow_base, narrow_held = fetch_ids("baseline"), fetch_ids("heldback")

    for name, items in (("baseline", baseline), ("heldback", heldback)):
        write_jsonl(os.path.join(OUT, name + ".jsonl"), items)

    b_ids = [i["source_item_id"] for i in baseline]
    h_ids = [i["source_item_id"] for i in heldback]
    nb, nh = set(narrow_base), set(narrow_held)
    recent = [i["source_item_id"] for i in baseline if i["dates"]["last_update_posted"] >= RECENT_FROM]
    manifest = {
        "source": "ClinicalTrials.gov (API v2)",
        "fetched_at": fetched_at,
        "source_data_timestamp": version["dataTimestamp"],
        "api_version": version.get("apiVersion"),
        "content_current_as_of": "Data processed by ClinicalTrials.gov at %s (dataTimestamp from /api/v2/version)"
                                 % version["dataTimestamp"],
        "queries": {
            "endpoint": S.CTGOV + "/studies",
            "query.cond": S.CTGOV_COND,
            "query.term_wide": S.CTGOV_TERM,
            "query.term_narrow": NARROW_TERM,
            "fields": S.CTGOV_FIELDS,
            "sort": "LastUpdatePostDate:asc",
            "baseline_filter.advanced": "AREA[LastUpdatePostDate]RANGE[MIN,%s]" % S.BASELINE_END.isoformat(),
            "heldback_filter.advanced": "AREA[LastUpdatePostDate]RANGE[%s,MAX]" % S.CUTOFF.isoformat(),
            "split_field": "LastUpdatePostDate (dates.split_date)",
            "narrow_ids": "same cond and filters, query.term_narrow, fields=NCTId",
            "recent_cutoff": "baseline items with dates.last_update_posted >= %s" % RECENT_FROM,
        },
        "counts": {"baseline.jsonl": len(baseline), "heldback.jsonl": len(heldback),
                   "narrow_baseline": len(narrow_base), "narrow_heldback": len(narrow_held),
                   "recent_baseline_wide": len(recent),
                   "recent_baseline_narrow": len([i for i in recent if i in nb]),
                   "heldback_new": sum(1 for i in heldback if i["extra"]["is_new_record"]),
                   "heldback_updated": sum(1 for i in heldback if not i["extra"]["is_new_record"])},
        "subsets": {
            "narrow": {"baseline": narrow_base, "heldback": narrow_held},
            "recent_baseline_wide": sorted(recent),
            "recent_baseline_narrow": sorted(i for i in recent if i in nb),
            "heldback_new": sorted(i["source_item_id"] for i in heldback if i["extra"]["is_new_record"]),
            "heldback_updated": sorted(i["source_item_id"] for i in heldback if not i["extra"]["is_new_record"]),
        },
        "sha256": {n: sha256_file(os.path.join(OUT, n)) for n in ("baseline.jsonl", "heldback.jsonl")},
        "attribution": "Source: ClinicalTrials.gov (U.S. National Library of Medicine), https://clinicaltrials.gov. "
                       "Data processed by ClinicalTrials.gov as of %s. Terms: "
                       "https://clinicaltrials.gov/about-site/terms-conditions. DxP is not endorsed by NLM and "
                       "claims no proprietary rights over this data, which is from a United States Government "
                       "database." % version["dataTimestamp"],
        "licence": "ClinicalTrials.gov Terms and Conditions (attribute, show processing date, state modifications)",
        "modifications": "Selected fields only were requested and flattened into a single raw_text per trial; "
                         "ClinicalTrials.gov markdown escapes (backslash before > < * and similar) were removed; "
                         "no other change to the content. Added fields (text_sha256, retrieved_at, extra) were "
                         "derived by DxP.",
        "reproduce": COMMAND,
        "differences_from_expected": [],
    }
    exp = {"baseline": 699, "heldback": 45, "narrow_b": 557, "narrow_h": 40, "rw": 346, "rn": 293, "new": 11, "upd": 34}
    c = manifest["counts"]
    got = {"baseline": c["baseline.jsonl"], "heldback": c["heldback.jsonl"], "narrow_b": c["narrow_baseline"],
           "narrow_h": c["narrow_heldback"], "rw": c["recent_baseline_wide"], "rn": c["recent_baseline_narrow"],
           "new": c["heldback_new"], "upd": c["heldback_updated"]}
    manifest["expected_counts"] = exp
    manifest["differences_from_expected"] = [
        {"item": k, "expected": exp[k], "got": got[k], "likely_reason": "TO_FILL"} for k in exp if exp[k] != got[k]]
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(got), "ts", version["dataTimestamp"])


if __name__ == "__main__":
    main()
