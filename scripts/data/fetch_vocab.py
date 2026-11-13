"""Download the DxP reference vocabularies (FR-9) into data/vocab/. Standard library only.

Run from the repository root:
    uv run --python 3.12 python scripts/data/fetch_vocab.py

Writes raw/hgnc_complete_set.txt (git-ignored), hgnc_genes.jsonl, oncotree_lung.json,
synonyms.json and manifest.json. Uses http_get from dxp_sources (per-host spacing, backoff).
Synonyms are only what NCI Thesaurus and MeSH return; nothing is added by hand.
"""
import csv, hashlib, io, json, pathlib, socket, sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dxp_sources
from dxp_vocab import HGNC_TSV

# Workaround for the NCI EVS IPv6 stall (see vocabularies.md): resolve that host to IPv4 only.
_getaddrinfo = socket.getaddrinfo


def _ipv4_for_evs(host, *a, **k):
    res = _getaddrinfo(host, *a, **k)
    if host == "api-evsrest.nci.nih.gov":
        res = [r for r in res if r[0] == socket.AF_INET] or res
    return res


socket.getaddrinfo = _ipv4_for_evs

OUT = pathlib.Path(__file__).resolve().parents[2] / "data" / "vocab"
ONCOTREE = "https://oncotree.mskcc.org/api"
VERSION = "oncotree_latest_stable"
EVS = "https://api-evsrest.nci.nih.gov/api/v1"
MESH = "https://id.nlm.nih.gov/mesh/lookup"
COMMAND = "uv run --python 3.12 python scripts/data/fetch_vocab.py"

REQUESTS = {}


def get(url, params=None, **kw):
    host = url.split("/")[2]
    REQUESTS[host] = REQUESTS.get(host, 0) + 1
    return dxp_sources.http_get(url, params, **kw)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Search labels the team chose per term (the terms vocabularies.md names). The labels are
# queries only; every synonym in the output comes from a service response.
TERMS = {
    "liquid biopsy": {"ncit": ["Liquid Biopsy"], "mesh": ["Liquid Biopsy"]},
    "ctDNA": {"ncit": ["ctDNA", "Circulating Tumor DNA"], "mesh": ["Circulating Tumor DNA"]},
    "cfDNA": {"ncit": ["cfDNA", "Cell-free DNA"], "mesh": ["Cell-Free Nucleic Acids"]},
    "circulating tumor cells": {"ncit": ["Circulating Tumor Cell"], "mesh": ["Neoplastic Cells, Circulating"]},
    "MRD": {"ncit": ["MRD", "Minimal Residual Disease"], "mesh": ["Neoplasm, Residual"]},
    "companion diagnostic": {"ncit": ["Companion Diagnostic"], "mesh": ["Companion Diagnostic Tests"]},
    "methylation": {"ncit": ["DNA Methylation"], "mesh": ["DNA Methylation"]},
    "radiomics": {"ncit": ["Radiomics"], "mesh": ["Radiomics"]},
    "digital pathology": {"ncit": ["Digital Pathology"], "mesh": ["Digital Pathology"]},
    "next-generation sequencing": {"ncit": ["Next-Generation Sequencing"], "mesh": ["High-Throughput Nucleotide Sequencing"]},
    "immunohistochemistry": {"ncit": ["Immunohistochemistry"], "mesh": ["Immunohistochemistry"]},
    "tumor mutational burden": {"ncit": ["Tumor Mutational Burden"], "mesh": ["Tumor Mutational Burden"]},
    "microsatellite instability": {"ncit": ["Microsatellite Instability"], "mesh": ["Microsatellite Instability"]},
    "PD-L1": {"ncit": ["PD-L1"], "mesh": ["B7-H1 Antigen"]},
    "Guardant360": {"ncit": ["Guardant360"], "mesh": [], "ncit_type": "contains"},
}


def fetch_hgnc():
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    body, headers = get(HGNC_TSV, min_interval=1.0, timeout=180)
    raw = OUT / "raw" / "hgnc_complete_set.txt"
    raw.write_bytes(body)
    genes = []
    for row in csv.DictReader(io.StringIO(body.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row["status"] != "Approved":
            continue
        split = lambda v: [x for x in v.strip('"').split("|") if x]
        genes.append({"hgnc_id": row["hgnc_id"], "symbol": row["symbol"], "name": row["name"].strip('"'),
                      "alias_symbols": split(row["alias_symbol"]), "prev_symbols": split(row["prev_symbol"]),
                      "locus_group": row["locus_group"]})
    genes.sort(key=lambda g: int(g["hgnc_id"].split(":")[1]))
    path = OUT / "hgnc_genes.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for g in genes:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")
    return {"raw_sha256": sha(raw), "raw_bytes": len(body), "last_modified": headers.get("Last-Modified"),
            "approved_genes": len(genes), "path": path}


def fetch_oncotree():
    versions = json.loads(get(ONCOTREE + "/versions", accept="application/json")[0])
    ver = next(v for v in versions if v["api_identifier"] == VERSION)
    nodes = json.loads(get(ONCOTREE + "/tumorTypes", {"version": VERSION}, accept="application/json")[0])
    lung = [{"code": n["code"], "name": n["name"], "parent": n["parent"], "level": n["level"],
             "tissue": n["tissue"], "main_type": n["mainType"],
             "external_references": n.get("externalReferences", {})}
            for n in nodes if n.get("tissue") == "Lung"]
    lung.sort(key=lambda n: (n["level"], n["code"]))
    doc = {"oncotree_version": VERSION, "release_date": ver["release_date"], "description": ver["description"],
           "source_url": f"{ONCOTREE}/tumorTypes?version={VERSION}", "node_count": len(lung), "nodes": lung}
    path = OUT / "oncotree_lung.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"version": VERSION, "release_date": ver["release_date"], "nodes": len(lung), "path": path}


def ncit_search(label, qtype):
    url = EVS + "/concept/ncit/search"
    body = json.loads(get(url, {"term": label, "type": qtype, "include": "synonyms", "pageSize": 5},
                          accept="application/json", timeout=8, retries=1)[0])
    return body.get("concepts", [])


def ncit_relations(code):
    c = json.loads(get(f"{EVS}/concept/ncit/{code}", {"include": "parents,children"},
                       accept="application/json", timeout=8, retries=1)[0])
    return {"parents": [{"code": p["code"], "name": p["name"]} for p in c.get("parents", [])],
            "children": [{"code": p["code"], "name": p["name"]} for p in c.get("children", [])]}


def mesh_lookup(label):
    hits = json.loads(get(MESH + "/descriptor", {"label": label, "match": "exact", "limit": 5},
                          accept="application/json", timeout=15)[0])
    out = []
    for h in hits:
        ui = h["resource"].rsplit("/", 1)[1]
        d = json.loads(get(MESH + "/details", {"descriptor": ui}, accept="application/json", timeout=15)[0])
        out.append({"descriptor": ui, "label": h["label"], "queried_label": label,
                    "entry_terms": [t["label"] for t in d.get("terms", [])]})
    return out


def build_synonyms(ncit_version):
    result, empty = {}, {"ncit": [], "mesh": [], "both": []}
    for term, spec in TERMS.items():
        ncit, seen = [], set()
        for label in spec["ncit"]:
            for c in ncit_search(label, spec.get("ncit_type", "match")):
                if c["code"] in seen:
                    continue
                seen.add(c["code"])
                ncit.append({"code": c["code"], "name": c["name"], "queried_label": label,
                             "synonyms": sorted({s["name"] for s in c.get("synonyms", [])})})
        mesh, seen = [], set()
        for label in spec["mesh"]:
            for m in mesh_lookup(label):
                if m["descriptor"] not in seen:
                    seen.add(m["descriptor"])
                    mesh.append(m)
        syn = {}  # lower-case text -> {text, sources}
        for c in ncit:
            for text in [c["name"]] + c["synonyms"]:
                syn.setdefault(text.lower(), {"text": text, "sources": []})["sources"].append(f"NCIt:{c['code']}")
        for m in mesh:
            for text in [m["label"]] + m["entry_terms"]:
                syn.setdefault(text.lower(), {"text": text, "sources": []})["sources"].append(f"MeSH:{m['descriptor']}")
        for v in syn.values():
            v["sources"] = sorted(set(v["sources"]))
        if not ncit:
            empty["ncit"].append(term)
        if not mesh:
            empty["mesh"].append(term)
        if not ncit and not mesh:
            empty["both"].append(term)
        result[term] = {
            "preferred_name": ncit[0]["name"] if ncit else (mesh[0]["label"] if mesh else term),
            "ncit_concepts": ncit, "mesh_descriptors": mesh,
            "synonyms": sorted(syn.values(), key=lambda v: v["text"].lower()),
            "queries": {"ncit": spec["ncit"], "ncit_match_type": spec.get("ncit_type", "match"),
                        "mesh": spec["mesh"], "mesh_match_type": "exact"},
        }
    return result, empty


def fr9_check(terms):
    lb, ct = terms["liquid biopsy"], terms["ctDNA"]
    texts = lambda t: {s["text"].lower() for s in t["synonyms"]}
    shared = sorted(texts(lb) & texts(ct))
    rel = {}
    for t in (lb, ct):
        for c in t["ncit_concepts"]:
            if c["name"] in ("Liquid Biopsy", "Circulating Tumor-Derived DNA"):
                rel[c["code"]] = ncit_relations(c["code"])
    ct_codes = {c["code"] for c in ct["ncit_concepts"]}
    lb_codes = {c["code"] for c in lb["ncit_concepts"]}
    linked = any(ch["code"] in ct_codes for code in lb_codes if code in rel for ch in rel[code]["children"]) or \
        any(p["code"] in lb_codes for code in ct_codes if code in rel for p in rel[code]["parents"])
    return {"shared_synonym_texts": shared, "ncit_direct_parent_child_link_between_them": linked,
            "ncit_parents_children": rel,
            "conclusion": ("Public vocabularies connect liquid biopsy to ctDNA." if (shared or linked) else
                           "No link in downloaded synonyms or one-step NCIt parent/child: the team must add "
                           "liquid biopsy -> ctDNA by hand (curated, labelled as such).")}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = now()
    hg = fetch_hgnc()
    ot = fetch_oncotree()
    meta = json.loads(get(EVS + "/metadata/ncit", accept="application/json", timeout=8, retries=1)[0])
    ncit_version = meta["associations"][0]["version"]
    terms, empty = build_synonyms(ncit_version)
    check = fr9_check(terms)
    syn_doc = {"purpose": "Seed synonym list for FR-9. Only terms returned by the services; NCIt and MeSH kept separate per synonym.",
               "ncit_version": ncit_version, "ncit_api": EVS, "mesh_api": MESH,
               "mesh_version": "MeSH as served by id.nlm.nih.gov/mesh/lookup on fetch date (current annual release; no version field is returned)",
               "fetched_at": now(), "terms": terms, "liquid_biopsy_to_ctdna_check": check}
    p = OUT / "synonyms.json"
    p.write_text(json.dumps(syn_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "fetched_at": t0, "finished_at": now(), "command": COMMAND,
        "request_counts_by_host": REQUESTS,
        "files": {
            "raw/hgnc_complete_set.txt": {"git_ignored": True, "source_url": HGNC_TSV, "bytes": hg["raw_bytes"],
                                          "sha256": hg["raw_sha256"], "file_date": hg["last_modified"],
                                          "licence": "CC0", "attribution": "HGNC, genenames.org (recommended, not required)"},
            "hgnc_genes.jsonl": {"source_url": HGNC_TSV, "source_file_date": hg["last_modified"],
                                 "count": hg["approved_genes"], "sha256": sha(hg["path"]), "licence": "CC0",
                                 "attribution": "HGNC, genenames.org (recommended, not required)",
                                 "modification": "Slimmed to approved genes and 6 fields; multi-value columns split into lists."},
            "oncotree_lung.json": {"source_url": f"{ONCOTREE}/tumorTypes?version={VERSION}", "oncotree_version": ot["version"],
                                   "release_date": ot["release_date"], "count": ot["nodes"], "sha256": sha(ot["path"]),
                                   "licence": "CC BY 4.0",
                                   "attribution": "OncoTree (CC BY 4.0), Kundra et al., JCO Clinical Cancer Informatics 2021",
                                   "modification": "Filtered to nodes with tissue = Lung; fields renamed."},
            "synonyms.json": {"source_urls": [EVS + "/concept/ncit/search", MESH + "/descriptor", MESH + "/details"],
                              "ncit_version": ncit_version, "mesh_version": syn_doc["mesh_version"],
                              "terms": len(terms), "synonym_entries": sum(len(t["synonyms"]) for t in terms.values()),
                              "sha256": sha(p),
                              "licences": {"NCI Thesaurus": "CC BY 4.0", "MeSH": "NLM MeSH terms: free; acknowledge NLM; state version"},
                              "attribution": "NCI Thesaurus (NCI EVS, CC BY 4.0); MeSH, U.S. National Library of Medicine (version as stated above). Data: HGNC, OncoTree (CC BY 4.0), NCI Thesaurus (CC BY 4.0). DxP is not endorsed by these organisations.",
                              "modification": "Deduplicated by case-insensitive text; per-source codes kept. This is a derived list, not NCI Thesaurus itself.",
                              "terms_with_no_ncit_result": empty["ncit"], "terms_with_no_mesh_result": empty["mesh"],
                              "terms_with_no_result_from_either": empty["both"]},
        },
        "fr9_liquid_biopsy_to_ctdna": check["conclusion"],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"requests": REQUESTS, "genes": hg["approved_genes"], "oncotree_nodes": ot["nodes"],
                      "no_ncit": empty["ncit"], "no_mesh": empty["mesh"], "fr9": check["conclusion"]}, indent=1))


if __name__ == "__main__":
    main()
