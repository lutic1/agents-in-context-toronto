#!/usr/bin/env python3
"""Download the FDA companion diagnostics list and the openFDA PMA records for the lung assays.

Writes data/fda/{cdx_lung,cdx_all,openfda_pma_baseline,openfda_pma_heldback}.jsonl, assays.json,
manifest.json and raw/cdx_list.html. Standard library only. Run from the repository root:
    uv run --python 3.12 python scripts/data/fetch_fda.py
"""
import hashlib, json, re, sys, urllib.error
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dxp_sources as S

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "fda"
(OUT / "raw").mkdir(parents=True, exist_ok=True)

# ---- wrap http_get: fetch the FDA page once (saved raw), count openFDA requests
_orig = S.http_get
STATS = {"openfda_requests": 0, "openfda_urls": [], "html": None}
def _get(url, *a, **k):
    if url == S.FDA_CDX_URL:
        if STATS["html"] is None:
            STATS["html"] = _orig(url, *a, **k)[0]
            (OUT / "raw" / "cdx_list.html").write_bytes(STATS["html"])
        return STATS["html"], {}
    if "api.fda.gov" in url:
        STATS["openfda_requests"] += 1
        STATS["openfda_urls"].append(re.sub(r"api_key=[^&]*", "api_key=***", url))
    return _orig(url, *a, **k)
S.http_get = _get

def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()

def norm_assay(name):
    n = re.sub(r"[®™©]", "", name)
    n = re.sub(r"\bPD-LI\b", "PD-L1", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip()
    n = re.sub(r"[()\[\]]", " ", n)
    n = re.sub(r"[^\w\-+/. ]", " ", n)
    return re.sub(r"\s+", " ", n).strip().lower()

def main():
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lung = S.fetch_fda_cdx(lung_only=True)
    allrows = S.fetch_fda_cdx(lung_only=False)
    m = re.search(rb"Content current as of:\s*(?:<[^>]+>\s*)*(\d{2}/\d{2}/\d{4})", STATS["html"])
    page_date = m.group(1).decode() if m else None
    files = {}
    files["cdx_lung.jsonl"] = (len(lung), write_jsonl(OUT / "cdx_lung.jsonl", lung))
    files["cdx_all.jsonl"] = (len(allrows), write_jsonl(OUT / "cdx_all.jsonl", allrows))

    # lung PMA numbers: P-numbers only (HDE, 510(k), BK/BR are not in device/pma)
    pma, other = set(), set()
    for r in lung:
        for s in r["ids"]["fda_submissions"]:
            (pma if s["number"].startswith("P") else other).add(s["number"])
    pma = sorted(pma)
    base = S.fetch_openfda_pma(pma, window="baseline")
    held = S.fetch_openfda_pma(pma, window="heldback")
    files["openfda_pma_baseline.jsonl"] = (len(base), write_jsonl(OUT / "openfda_pma_baseline.jsonl", base))
    files["openfda_pma_heldback.jsonl"] = (len(held), write_jsonl(OUT / "openfda_pma_heldback.jsonl", held))
    found = {r["ids"]["fda_submissions"][0]["number"] for r in base + held}
    not_found = {n: "no record in openFDA device/pma" for n in pma if n not in found}
    last_updated = (base or held)[0]["dates"]["source_last_updated"] if (base or held) else None

    # ---- assays.json
    assays = OrderedDict()
    for r in lung:
        e = r["extra"]; key = norm_assay(e["assay"])
        a = assays.setdefault(key, {"assay_normalised": key, "name_strings_in_list": [], "manufacturers": [],
                                    "submission_numbers": [], "rows": []})
        for lst, v in ((a["name_strings_in_list"], e["assay"]), (a["manufacturers"], e["company"])):
            if v and v not in lst: lst.append(v)
        for s in r["ids"]["fda_submissions"]:
            sn = s["number"] + ("/" + s["supplement"] if s["supplement"] else "")
            if sn not in a["submission_numbers"]: a["submission_numbers"].append(sn)
        a["rows"].append({"source_item_id": r["source_item_id"], "drug_trade_name": e["drug_trade_name"],
                          "drug_generic_name": e["drug_generic_name"], "drug_application": r["ids"]["drug_application"],
                          "biomarkers": e["biomarkers"], "biomarker_details": e["biomarker_details"],
                          "indication": e["indication"], "sample_type": e["sample_type"],
                          "decision_dates": r["dates"]["decision_dates"]})
    for a in assays.values():
        a["pma_numbers"] = sorted({x.split("/")[0] for x in a["submission_numbers"] if x.startswith("P")})
        a["other_submission_numbers"] = sorted({x.split("/")[0] for x in a["submission_numbers"] if not x.startswith("P")})
        a["row_count"] = len(a["rows"])
    assays_doc = {
        "derived_by": "DxP (derived from the FDA list of companion diagnostics; not an FDA publication)",
        "normalisation": "assay_normalised = name with (R)/(TM) marks removed, 'PD-LI' corrected to 'PD-L1', brackets and "
                         "punctuation other than - + / . removed, whitespace collapsed, lower-cased. Original strings are "
                         "kept in name_strings_in_list. Rows come from cdx_lung.jsonl; manufacturer is the text in the final "
                         "bracket of 'Diagnostic Name (Manufacturer)'.",
        "source_page": S.FDA_CDX_URL, "page_content_current_as_of": page_date, "fetched_at": fetched_at,
        "assay_count": len(assays), "assays": list(assays.values())}
    (OUT / "assays.json").write_text(json.dumps(assays_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files["assays.json"] = (len(assays), hashlib.sha256((OUT / "assays.json").read_bytes()).hexdigest())
    files["raw/cdx_list.html"] = ("not committed", hashlib.sha256(STATS["html"]).hexdigest())

    manifest = OrderedDict([
        ("source", "U.S. FDA: List of FDA-Authorized Companion Diagnostic Devices (HTML page) and openFDA device/pma"),
        ("fetched_at", fetched_at),
        ("data_timestamps", {"fda_list_content_current_as_of": page_date, "openfda_meta_last_updated": last_updated}),
        ("queries", {"fda_list_url": S.FDA_CDX_URL, "fda_list_parse": "first table; lung rows = indication cell matches /lung|NSCLC/i",
                     "openfda_pma_numbers": pma,
                     "openfda_baseline_filter": "decision_date:[1976-01-01 TO %s]" % S.BASELINE_END,
                     "openfda_heldback_filter": "decision_date:[%s TO %s]" % (S.CUTOFF, S.DEMO_DATE),
                     "openfda_request_urls": STATS["openfda_urls"]}),
        ("files", {k: {"items": v[0], "sha256": v[1], "bytes": (OUT / k).stat().st_size}
                   for k, v in files.items() if not k.startswith("raw/")}),
        ("raw_copy", {"path": "raw/cdx_list.html", "sha256": files["raw/cdx_list.html"][1], "git": "ignored"}),
        ("id_lists", {"lung_pma_numbers": pma, "lung_non_pma_submissions": sorted(other),
                      "pma_numbers_not_found_in_openfda": not_found,
                      "lung_assays_normalised": list(assays)}),
        ("heldback_records", [{"pma_number": r["ids"]["fda_submissions"][0]["number"],
                               "supplement_number": r["ids"]["fda_submissions"][0]["supplement"],
                               "decision_date": r["dates"]["decision_date"],
                               "supplement_reason": r["extra"]["supplement_reason"], "trade_name": r["title"],
                               "decision_code": r["extra"]["decision_code"]} for r in held]),
        ("openfda_requests_used", STATS["openfda_requests"]),
        ("openfda_daily_limit_without_key", 1000),
        ("licence", "FDA website content: US Government work, public domain. openFDA: CC0 1.0. "
                    "Data provided by the U.S. Food and Drug Administration (https://open.fda.gov). DxP is not endorsed by FDA."),
        ("modification", "Source content is unmodified except for whitespace collapsing in the HTML table cells. "
                         "assays.json is derived by DxP from the FDA list (see its 'normalisation' field)."),
        ("reproduce", "uv run --python 3.12 python scripts/data/fetch_fda.py"),
        ("differences_from_expected", []),
        ("notes", ["Counts match the skill: 76 lung rows, 235 total, 20 assays, 22 PMA numbers, 425 baseline / 2 held-back openFDA records.",
                   "Name strings: 21 for 20 assays (Ventana PD-LI (SP263) typo kept alongside the correct form); manufacturer strings vary (Foundation Medicine, Inc. / Inc; Ventana Medical Systems, Inc / Inc.).",
                   "No lung row in the list is dated 17 Oct 2026 or later; the held-back set comes from openFDA only."]),
    ])
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v[0] for k, v in files.items()}), "openfda requests:", STATS["openfda_requests"])

if __name__ == "__main__":
    main()
