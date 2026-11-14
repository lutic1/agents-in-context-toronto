> Reference only. Do not copy this code into the project; it was written before the event.

# Reference vocabularies for FR-9

Checked on 12 November 2026. All four pass the "open data only" rule. Load each once at start-up and keep it in MongoDB; do not call these services per Source item.

| Vocabulary | Use in DxP | Access | Licence | Version seen |
|---|---|---|---|---|
| HGNC | Gene symbol for a biomarker (`HER2` to `ERBB2`, `PD-L1` to `CD274`) | Bulk TSV or JSON, or REST | CC0 (attribution recommended, not required) | File last modified 10 November 2026; 45,387 approved symbols |
| OncoTree | Tumour type code (`NSCLC`, `LUAD`, `LUSC`, `SCLC`) | REST, no key | CC BY 4.0 (cite Kundra et al., JCO Clinical Cancer Informatics 2021) | `oncotree_latest_stable`, released 2025-10-03 |
| NCI Thesaurus (NCIt) | Synonyms for modalities and analytes (`liquid biopsy`, `ctDNA`), some named assays | EVS REST API 2.5.1, no key for `ncit` | CC BY 4.0 | - |
| MeSH | Second synonym source, and the terms PubMed indexes with | `id.nlm.nih.gov/mesh/lookup` | NLM MeSH terms: free, acknowledge NLM, state the version if redistributed | - |

## Code: `dxp_vocab.py` (tested, standard library only)

```python
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
```

## HGNC

- Bulk files (public Google Cloud Storage bucket, about 17 MB):
  - `https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt`
  - `https://storage.googleapis.com/public-download-files/hgnc/json/json/hgnc_complete_set.json`
- REST root `https://rest.genenames.org/`. Send `Accept: application/json`. Patterns: `/fetch/{field}/{term}` and `/search/{field}/{term}`. Fields used here: `symbol`, `alias_symbol`, `prev_symbol`, `hgnc_id`, `status`. Results are under `response.docs`, count under `response.numFound`. Limit: 10 requests per second; a 403 may follow overload.
- Resolve in this order: approved symbol, then previous symbol, then alias. Alias-first is wrong: `/search/alias_symbol/MET` returns `SLTM`, because "Met" is an alias of that gene. `load_hgnc` applies the right order.
- Multi-value columns in the TSV are pipe-separated and wrapped in double quotes. Read with `csv.QUOTE_NONE` and strip the quotes.
- Not genes, so HGNC will not resolve them: `MSI-High`, `TMB`, `PD-L1` expression as a protein assay (the gene is `CD274`), fusions written as `EML4-ALK`. Send these to the Reviewer as unmatched terms (FR-9) or keep a small hand-made biomarker list.
- Protein-style names with punctuation (`c-Met`, `HER-2/neu`) need a fallback: strip hyphens and spaces and try again.

## OncoTree

- Endpoints (from `https://oncotree.mskcc.org/swagger/doc.json`): `GET /api/versions`, `GET /api/tumorTypes?version=`, `GET /api/tumorTypes/tree?version=`, `GET /api/tumorTypes/search/{type}/{query}?exactMatch=&version=&levels=`, `GET /api/mainTypes?version=`, `GET /api/tumor_types.txt?version=`.
- Use `version=oncotree_latest_stable`. `oncotree_development` changes without notice.
- The server answered 403 to a `User-Agent` that contained an e-mail address. A plain one (`DxP/0.1`) works.
- Each node carries `externalReferences.NCI` and `.UMLS`, which link OncoTree to NCIt codes.
- Lung nodes in `oncotree_latest_stable` (tissue `Lung`, 30 nodes):

| Level | Codes |
|---|---|
| 1 | `LUNG` Lung |
| 2 | `NSCLC` Non-Small Cell Lung Cancer, `LNET` Lung Neuroendocrine Tumor, `CSCLC` Combined Small Cell Lung Carcinoma, `SARCL` Sarcomatoid Carcinoma of the Lung, `LAIS` Lung Adenocarcinoma In Situ, `IMTL`, `LAM`, `PPB` |
| 3, under `NSCLC` | `LUAD` Lung Adenocarcinoma, `LUSC` Lung Squamous Cell Carcinoma, `LUAS` Lung Adenosquamous Carcinoma, `LCLC` Large Cell Lung Carcinoma, `LUPC` Pleomorphic Carcinoma of the Lung, `NSCLCPD` Poorly Differentiated NSCLC, `SPCC` Spindle Cell Carcinoma of the Lung, `SGTTL` Salivary Gland-Type Tumor of the Lung, `NUTCL`, `CMPT` |
| 3, under `LNET` | `SCLC` Small Cell Lung Cancer, `LUNE` Large Cell Neuroendocrine Carcinoma, `LUCA` Lung Carcinoid, `ALUCA` Atypical Lung Carcinoid |
| 4 | under `LCLC`: `BLCLC`, `CCLC`, `GCLC`, `LECLC`, `RLCLC`; under `SGTTL`: `LUACC`, `LUMEC` |

- `SCLC` sits under `LNET`, not directly under `LUNG`, and its `mainType` is "Small Cell Lung Cancer". Every node under `NSCLC` and most others have `mainType` "Non-Small Cell Lung Cancer", including `LNET` itself, so filter on `code` and `parent`, not on `mainType`.
- All 76 lung rows in the FDA list say "Non-Small Cell Lung Cancer (NSCLC)", which maps to `NSCLC`.

## NCI Thesaurus through the EVS REST API

- Search: `GET https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search?term=...&type=match&include=synonyms&pageSize=5`. `type` is one of `contains`, `match`, `startsWith`, `phrase`, `AND`, `OR`, `fuzzy`. Paging: `fromRecord`, `pageSize`.
- Concept: `GET /api/v1/concept/ncit/{code}?include=synonyms`.
- No key for `ncit`. The `X-EVSRESTAPI-License-Key` header is only for restricted terminologies.
- Checked lookups: `liquid biopsy` gives C135727 "Liquid Biopsy" (synonym "Plasma Biopsy"); `ctDNA` gives C113243 "Circulating Tumor-Derived DNA" (synonyms "Circulating Tumor DNA", "Cell-Free Circulating Tumor DNA", "ctDNA", "ctdDNA"); `Guardant360` with `type=contains` gives C153090 and C172874.
- The host publishes IPv6 addresses. On a network without working IPv6, Python's `urllib` waits the full timeout on each IPv6 address before trying IPv4 (seen during testing: 20 s for two lookups with a 5 s timeout; minutes with the default 60 s). Call it with a short timeout, once, and cache the result.

## MeSH

- `GET https://id.nlm.nih.gov/mesh/lookup/descriptor?label=Liquid%20Biopsy&match=exact&limit=5` returns the descriptor URI (`D000073890`).
- `GET https://id.nlm.nih.gov/mesh/lookup/details?descriptor=D000074141` returns the entry terms: "Circulating Tumor DNA", "Cell-Free Tumor DNA".
- `match=contains` on "ctDNA" returned nothing: abbreviations are often absent, so NCIt is the better synonym source.

## The FR-9 test: "liquid biopsy" returns ctDNA Diagnostics

No vocabulary above states that ctDNA testing is a kind of liquid biopsy: in NCIt they are separate concepts, and a synonym lookup alone will not pass the test. Seed the broader-to-narrower links by hand and label the file as curated by the team:

```python
MODALITY_SEED = {                     # canonical term -> synonyms; "narrower" gives the FR-9 expansion
    "liquid biopsy": {"ncit": "C135727", "mesh": "D000073890",
                      "synonyms": ["liquid biopsies", "plasma biopsy", "blood-based test"],
                      "narrower": ["ctDNA", "cfDNA", "circulating tumour cells", "methylation (plasma)"]},
    "ctDNA": {"ncit": "C113243", "mesh": "D000074141",
              "synonyms": ["circulating tumor DNA", "circulating tumour DNA", "cell-free tumor DNA",
                           "circulating tumor-derived DNA", "ctdDNA"]},
    "MRD": {"synonyms": ["minimal residual disease", "molecular residual disease", "measurable residual disease"]},
}
```

The codes are the ones returned by the calls above. The `narrower` lists and the MRD synonyms are the team's own choices, not taken from a vocabulary.

## Assay and test names

There is no open, complete vocabulary of named cancer assays. Use these, in this order:

1. The FDA companion diagnostics list (public domain). The "Diagnostic Name (Manufacturer)" cell is the authoritative name for an authorised assay: 20 lung assays today, from 11 companies written 14 ways (for example "Foundation Medicine, Inc." and "Foundation Medicine Inc."). Strip `®` and `™`, and note that the list is inconsistent ("Guardant360 CDx" and "Guardant360® Liquid CDx" are two different devices; "Ventana PD-LI (SP263) Assay" is a typo for "PD-L1").
2. openFDA `device/pma` and `device/510k` `trade_name`, `applicant` and `product_code` (CC0). `openfda.device_name` gives the generic device type, for example product code `PQP`, "Next Generation Sequencing Oncology Panel, Somatic Or Germline Variant Detection System". Useful as a modality or Category hint.
3. NCIt (CC BY 4.0) for the few branded assays it lists and for modality terms.
4. Anything else (laboratory-developed tests, research assays in trials) has no standard name. Send it to the Reviewer as an unmatched term, as FR-9 requires.

Not checked today, so not recommended for Saturday: LOINC and the NCBI Genetic Testing Registry (`UNVERIFIED`: licence and access terms were not read).
