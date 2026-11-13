#!/usr/bin/env python3
"""Download the wide PubMed set (baseline + held-back) into data/pubmed/.

Usage (from repo root):
  NCBI_EMAIL=<your email> uv run --python 3.12 python scripts/data/fetch_pubmed.py

Writes baseline.jsonl and heldback.jsonl (abstract text; git-ignored, never commit)
and manifest.json (PMIDs, DOIs, dates, publication types, counts, hashes; no text, no titles).
Standard library only.
"""
import hashlib, json, os, sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dxp_sources as S

if not os.environ.get("NCBI_EMAIL"):
    sys.exit("NCBI_EMAIL is not set. NCBI requires a contact email on every request. "
             "Run: NCBI_EMAIL=<your email> uv run --python 3.12 python scripts/data/fetch_pubmed.py")

OUT = Path(__file__).resolve().parents[2] / "data" / "pubmed"
OUT.mkdir(parents=True, exist_ok=True)
ONE_YEAR_FROM = date(2025, 11, 14)
GAP = 0.11 if os.environ.get("NCBI_API_KEY") else 0.4
NARROW_QUERY = S.PUBMED_LUNG + " AND " + S.PUBMED_DX_NARROW + " AND hasabstract AND english[la]"
WINDOWS = {"baseline": (S.BASELINE_START, S.BASELINE_END), "heldback": (S.CUTOFF, S.DEMO_DATE)}


def esearch_ids(query, lo, hi):
    """IDs only (no efetch). Returns (count, [pmids])."""
    r = json.loads(S.http_get(S.EUTILS + "esearch.fcgi", S._eutils_params(
        db="pubmed", term=query, datetype="edat", mindate=lo.strftime("%Y/%m/%d"),
        maxdate=hi.strftime("%Y/%m/%d"), retmax=9999, retmode="json"), GAP)[0])["esearchresult"]
    ids = r["idlist"]
    assert int(r["count"]) == len(ids) < 9999, "esearch result truncated or inconsistent"
    return int(r["count"]), ids


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
data, esearch_counts, files, missing = {}, {}, {}, {}
for w, (lo, hi) in WINDOWS.items():
    items = S.fetch_pubmed(w)
    items.sort(key=lambda i: int(i["source_item_id"]))
    p = OUT / (w + ".jsonl")
    with p.open("w", encoding="utf-8", newline="\n") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    data[w] = items
    n_es, all_ids = esearch_ids(S.PUBMED_QUERY, lo, hi)
    esearch_counts[w] = n_es
    missing[w] = sorted(set(all_ids) - {i["source_item_id"] for i in items}, key=int)
    files[w] = {"file": "data/pubmed/%s.jsonl" % w, "count": len(items),
                "esearch_count": esearch_counts[w], "sha256": sha(p), "bytes": p.stat().st_size}
    print(w, len(items), "esearch", esearch_counts[w], flush=True)

downloaded = {w: {i["source_item_id"] for i in data[w]} for w in data}


def subset(query, window, lo=None):
    lo0, hi = WINDOWS[window]
    _, ids = esearch_ids(query, lo or lo0, hi)
    return sorted((x for x in ids if x in downloaded[window]), key=int), len(ids)


subsets, sub_notes = {}, {}
for name, query, lo in (("narrow", NARROW_QUERY, None), ("small", S.PUBMED_QUERY_SMALL, None)):
    subsets[name], sub_notes[name] = {}, {}
    for w in WINDOWS:
        subsets[name][w], n = subset(query, w)
        sub_notes[name][w] = {"esearch_count": n, "in_download": len(subsets[name][w])}
subsets["small_one_year"] = {"baseline": subset(S.PUBMED_QUERY_SMALL, "baseline", ONE_YEAR_FROM)[0]}
sub_notes["small_one_year"] = {"baseline": {"in_download": len(subsets["small_one_year"]["baseline"])}}

records = {}
for w in data:
    records[w] = [{"pmid": i["source_item_id"], "doi": i["ids"]["doi"],
                   "entered_pubmed": i["dates"]["entered_pubmed"],
                   "publication_types": i["extra"]["publication_types"]} for i in data[w]]
n_copy = {w: sum(1 for i in data[w] if i["extra"].get("abstract_copyright")) for w in data}

edge = {w: [{"pmid": i["source_item_id"], "split_date": i["dates"]["split_date"]} for i in data[w]
            if not (WINDOWS[w][0].isoformat() <= (i["dates"]["split_date"] or "") <= WINDOWS[w][1].isoformat())]
        for w in data}

manifest = {
    "source": "PubMed (NCBI E-utilities esearch + efetch)",
    "fetched_at": fetched_at,
    "content_current_as_of": fetched_at[:10] + " (live PubMed at fetch time; entered-date filter is stable)",
    "split_field": "Entry date [edat] (datetype=edat); inclusive ranges",
    "windows": {"baseline": "2024/11/14 to 2026/10/16", "heldback": "2026/10/17 to 2026/11/14"},
    "queries": {"wide (PUBMED_QUERY)": S.PUBMED_QUERY, "narrow": NARROW_QUERY,
                "small (PUBMED_QUERY_SMALL)": S.PUBMED_QUERY_SMALL,
                "small_one_year": "small, baseline only, edat 2025/11/14 to 2026/10/16"},
    "files": files,
    "split_date_outside_window": {
        "items": edge,
        "reason": "Membership is decided by the esearch [edat] filter. dates.split_date is the History entrez date, "
                  "which can differ by one day at the window edges (time zone); items were kept as fetched."},
    "found_by_esearch_but_not_downloaded": {
        "pmids": missing,
        "reason": "efetch returns these as PubmedBookArticle (for example StatPearls book chapters); "
                  "the shared fetcher parses PubmedArticle only, so they are skipped."},
    "subset_counts": sub_notes,
    "abstract_copyright_counts": n_copy,
    "subsets": subsets,
    "records": records,
    "attribution": "PubMed (courtesy of the U.S. National Library of Medicine). DxP is not endorsed by NLM. "
                   "Abstract copyright remains with publishers or authors. Abstract text is not redistributed: "
                   "re-fetch from the PMIDs listed here.",
    "modification": "None to source content; only restructured into Source item dictionaries "
                    "(title + abstract joined into raw_text).",
    "reproduce": "NCBI_EMAIL=<your email> uv run --python 3.12 python scripts/data/fetch_pubmed.py",
    "expected_counts_from_skill": {"baseline": 2522, "heldback": 90, "narrow": [1032, 49],
                                   "small": [627, 24], "small_one_year": 323},
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("manifest written")
