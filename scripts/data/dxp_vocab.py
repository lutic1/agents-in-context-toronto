# Copied verbatim from .claude/skills/dxp-open-data-sources/references/vocabularies.md on 2026-11-13.
# Data preparation code written before the hackathon; disclosed in data/README.md.
"""DxP reference vocabularies (FR-9). Standard library only. Uses http_get from dxp_sources."""
import csv, io, json, urllib.parse
from dxp_sources import http_get

HGNC_TSV = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"

def load_hgnc():
    """Returns (genes, lookup). lookup maps an upper-cased name to an HGNC ID; approved symbols always win."""
    text = http_get(HGNC_TSV, min_interval=1.0)[0].decode("utf-8")      # about 17 MB, 47,000 rows, one request
    genes, approved, previous, alias = {}, {}, {}, {}
    for row in csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row["status"] != "Approved":
            continue
        split = lambda v: [x for x in v.strip('"').split("|") if x]
        genes[row["hgnc_id"]] = {"hgnc_id": row["hgnc_id"], "symbol": row["symbol"], "name": row["name"],
                                 "aliases": split(row["alias_symbol"]), "previous": split(row["prev_symbol"])}
        approved[row["symbol"].upper()] = row["hgnc_id"]
        for p in split(row["prev_symbol"]):
            previous.setdefault(p.upper(), row["hgnc_id"])
        for a in split(row["alias_symbol"]):
            alias.setdefault(a.upper(), row["hgnc_id"])
    return genes, {**alias, **previous, **approved}                       # precedence: approved > previous > alias

def load_oncotree_lung(version="oncotree_latest_stable"):
    """All OncoTree nodes whose tissue is Lung, keyed by code."""
    nodes = json.loads(http_get("https://oncotree.mskcc.org/api/tumorTypes", {"version": version},
                                accept="application/json")[0])
    return {n["code"]: {"code": n["code"], "name": n["name"], "parent": n["parent"], "main_type": n["mainType"],
                        "level": n["level"], "nci": n["externalReferences"].get("NCI", []),
                        "umls": n["externalReferences"].get("UMLS", [])}
            for n in nodes if n.get("tissue") == "Lung"}

def ncit_synonyms(term):
    """Exact-match lookup in NCI Thesaurus. Returns [{code, name, synonyms}]."""
    url = "https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search"
    body = json.loads(http_get(url, {"term": term, "type": "match", "include": "synonyms", "pageSize": 5},
                               accept="application/json", timeout=5)[0])   # short: see the IPv6 gotcha
    return [{"code": c["code"], "name": c["name"],
             "synonyms": sorted({s["name"] for s in c.get("synonyms", [])})} for c in body.get("concepts", [])]
