# Fetchers: `dxp_sources.py`

Tested on 12 November 2026 against the live public endpoints (Python 3.9, standard library only, no install step). Copy the block below into the backend as `dxp_sources.py`. It needs `NCBI_EMAIL` in the environment; `NCBI_TOOL`, `NCBI_API_KEY` and `OPENFDA_API_KEY` are optional.

Every fetcher returns a list of plain dictionaries with the same shape:

| Key | Meaning |
|---|---|
| `source` | `clinicaltrials.gov`, `pubmed`, `fda_cdx_list` or `openfda_device_pma` |
| `source_item_id` | Stable ID within the source: NCT ID, PMID, FDA row key, or PMA number with supplement |
| `source_url` | Public page for the item, for the Evidence link |
| `ids` | Cross-source identifiers (`nct_id`, `pmids`, `pmid`, `doi`, `pmcid`, `nct_ids`, `fda_submissions`) |
| `dates` | Source date fields as ISO strings, plus `split_date`, the one used for Baseline load versus Held-back set |
| `title`, `raw_text` | `raw_text` is the exact text a quote is checked against (FR-18) |
| `text_sha256` | Hash of the normalised text, to detect a real content change on re-fetch |
| `retrieved_at`, `licence`, `extra` | Fetch time (UTC), terms label, source-specific fields |

Unique key for a Source item in MongoDB: `(source, source_item_id)`.

Usage:

```python
from dxp_sources import (fetch_ctgov, fetch_pubmed, fetch_fda_cdx, fetch_openfda_pma,
                         quote_in_source, PUBMED_QUERY_SMALL)

baseline = fetch_ctgov("baseline") + fetch_pubmed("baseline", query=PUBMED_QUERY_SMALL) + fetch_fda_cdx()
heldback = fetch_ctgov("heldback") + fetch_pubmed("heldback", query=PUBMED_QUERY_SMALL)
pma_numbers = {s["number"] for row in fetch_fda_cdx() for s in row["ids"]["fda_submissions"]
               if s["number"].startswith("P")}
heldback += fetch_openfda_pma(pma_numbers, "heldback")

ok = quote_in_source(field["quote"], source_item["raw_text"])     # FR-18 word-for-word check
```

## The module

```python
"""DxP open-data fetchers. Standard library only (tested on Python 3.9)."""
import hashlib, json, os, re, time, unicodedata, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser

DEMO_DATE = date(2026, 11, 14)
CUTOFF = DEMO_DATE - timedelta(days=28)        # 2026-10-17: first day of the Held-back set
BASELINE_END = CUTOFF - timedelta(days=1)      # 2026-10-16: last day of the Baseline load
BASELINE_START = date(2024, 11, 14)            # PubMed only: two years back
USER_AGENT = "DxP/0.1"          # keep it plain: oncotree.mskcc.org answered 403 when an e-mail address was in it
_last_call = {}

def http_get(url, params=None, min_interval=0.4, accept=None, retries=4, timeout=60):
    """GET with per-host spacing and backoff on 429/5xx. Returns (bytes, headers)."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    host = urllib.parse.urlsplit(url).netloc
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    for attempt in range(retries + 1):
        wait = _last_call.get(host, 0) + min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.monotonic()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(float(e.headers.get("Retry-After") or 2 ** attempt))
                continue
            raise

def normalise(text):
    """Use on BOTH the quote and raw_text before the FR-18 word-for-word check."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "")).strip()

def quote_in_source(quote, raw_text):
    return bool(quote) and normalise(quote) in normalise(raw_text)

def item(source, item_id, url, ids, dates, title, raw_text, licence, extra=None):
    return {
        "source": source, "source_item_id": item_id, "source_url": url,
        "ids": ids, "dates": dates, "title": title, "raw_text": raw_text,
        "text_sha256": hashlib.sha256(normalise(raw_text).encode()).hexdigest(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "licence": licence, "extra": extra or {},
    }

# ---------------------------------------------------------------- ClinicalTrials.gov
CTGOV = "https://clinicaltrials.gov/api/v2"
CTGOV_COND = "lung cancer"
CTGOV_TERM = ('ctDNA OR "circulating tumor DNA" OR "liquid biopsy" OR MRD OR "minimal residual disease" '
              'OR "molecular residual disease" OR "companion diagnostic" OR "digital pathology" '
              'OR radiomics OR methylation')          # add "OR biomarker" for the wide set (about 2,500)
CTGOV_FIELDS = ("NCTId|OrgStudyId|SecondaryId|Acronym|BriefTitle|OfficialTitle|OverallStatus|StudyType|Phase|"
                "EnrollmentCount|StudyFirstSubmitDate|StudyFirstPostDate|LastUpdateSubmitDate|LastUpdatePostDate|"
                "ResultsFirstPostDate|StartDate|PrimaryCompletionDate|LeadSponsorName|CollaboratorName|"
                "BriefSummary|DetailedDescription|Condition|Keyword|InterventionType|InterventionName|"
                "InterventionDescription|InterventionOtherName|PrimaryOutcomeMeasure|PrimaryOutcomeDescription|"
                "SecondaryOutcomeMeasure|EligibilityCriteria|ReferencePMID|ReferenceType|HasResults")
_MD_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!<>&^~|])")

def _ctgov_item(study, data_timestamp):
    p = study.get("protocolSection", {})
    ident, status = p.get("identificationModule", {}), p.get("statusModule", {})
    desc, arms = p.get("descriptionModule", {}), p.get("armsInterventionsModule", {})
    outc, cond = p.get("outcomesModule", {}), p.get("conditionsModule", {})
    nct = ident["nctId"]
    parts = [("Brief title", ident.get("briefTitle")), ("Official title", ident.get("officialTitle")),
             ("Brief summary", desc.get("briefSummary")), ("Detailed description", desc.get("detailedDescription")),
             ("Conditions", "; ".join(cond.get("conditions", []))), ("Keywords", "; ".join(cond.get("keywords", [])))]
    for i in arms.get("interventions", []):
        names = ", ".join([i.get("name", "")] + i.get("otherNames", []))
        parts.append(("Intervention (%s)" % i.get("type", ""), "%s. %s" % (names, i.get("description", ""))))
    for kind in ("primaryOutcomes", "secondaryOutcomes"):
        for o in outc.get(kind, []):
            parts.append((kind[:-1], "%s. %s" % (o.get("measure", ""), o.get("description", ""))))
    parts.append(("Eligibility criteria", p.get("eligibilityModule", {}).get("eligibilityCriteria")))
    raw = "\n\n".join("%s: %s" % (k, _MD_ESCAPE.sub(r"\1", v)) for k, v in parts if v)
    first_post = status.get("studyFirstPostDateStruct", {}).get("date")
    last_post = status.get("lastUpdatePostDateStruct", {}).get("date")
    refs = p.get("referencesModule", {}).get("references", [])
    return item(
        "clinicaltrials.gov", nct, "https://clinicaltrials.gov/study/" + nct,
        ids={"nct_id": nct, "org_study_id": ident.get("orgStudyIdInfo", {}).get("id"),
             "secondary_ids": [s.get("id") for s in ident.get("secondaryIdInfos", [])],
             "pmids": [r["pmid"] for r in refs if r.get("pmid")]},
        dates={"first_posted": first_post, "last_update_posted": last_post,
               "first_submitted": status.get("studyFirstSubmitDate"),
               "last_update_submitted": status.get("lastUpdateSubmitDate"),
               "results_first_posted": status.get("resultsFirstPostDateStruct", {}).get("date"),
               "source_data_timestamp": data_timestamp, "split_date": last_post},
        title=ident.get("briefTitle"), raw_text=raw,
        licence="ClinicalTrials.gov Terms and Conditions (attribute, show processing date, state modifications)",
        extra={"is_new_record": bool(first_post and first_post >= CUTOFF.isoformat()),
               "overall_status": status.get("overallStatus"),
               "phases": p.get("designModule", {}).get("phases", []),
               "lead_sponsor": p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
               "interventions": [{"type": i.get("type"), "name": i.get("name"), "other_names": i.get("otherNames", [])}
                                 for i in arms.get("interventions", [])],
               "has_results": study.get("hasResults")})

def fetch_ctgov(window="baseline", term=CTGOV_TERM, max_items=None):
    """window: 'baseline' (last update posted <= 2026-10-16), 'heldback' (>= 2026-10-17) or 'all'."""
    ts = json.loads(http_get(CTGOV + "/version")[0])["dataTimestamp"]
    params = {"query.cond": CTGOV_COND, "query.term": term, "fields": CTGOV_FIELDS,
              "pageSize": 100, "countTotal": "true", "sort": "LastUpdatePostDate:asc"}
    if window == "baseline":
        params["filter.advanced"] = "AREA[LastUpdatePostDate]RANGE[MIN,%s]" % BASELINE_END.isoformat()
    elif window == "heldback":
        params["filter.advanced"] = "AREA[LastUpdatePostDate]RANGE[%s,MAX]" % CUTOFF.isoformat()
    out, token = [], None
    while True:
        page = json.loads(http_get(CTGOV + "/studies", dict(params, pageToken=token) if token else params, 1.2)[0])
        out += [_ctgov_item(s, ts) for s in page.get("studies", [])]
        token = page.get("nextPageToken")
        if not token or (max_items and len(out) >= max_items):
            return out[:max_items] if max_items else out

# ---------------------------------------------------------------- PubMed (E-utilities)
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_LUNG = ('("Lung Neoplasms"[MeSH Terms] OR "lung cancer"[tiab] OR "lung adenocarcinoma"[tiab] '
               'OR NSCLC[tiab] OR SCLC[tiab])')
PUBMED_DX = ('(ctDNA[tiab] OR "circulating tumor DNA"[tiab] OR "circulating tumour DNA"[tiab] OR "liquid biopsy"[tiab] '
             'OR "minimal residual disease"[tiab] OR "molecular residual disease"[tiab] OR "companion diagnostic"[tiab] '
             'OR "companion diagnostics"[tiab] OR "digital pathology"[tiab] OR radiomics[tiab] OR methylation[tiab])')
PUBMED_QUERY = PUBMED_LUNG + " AND " + PUBMED_DX + " AND hasabstract AND english[la]"
# Smaller variants (counts in SKILL.md): narrower topics, and no reviews, case reports or comment pieces.
PUBMED_DX_NARROW = ('(ctDNA[tiab] OR "circulating tumor DNA"[tiab] OR "circulating tumour DNA"[tiab] OR "liquid biopsy"[tiab] '
                    'OR "minimal residual disease"[tiab] OR "molecular residual disease"[tiab] '
                    'OR "companion diagnostic"[tiab] OR "companion diagnostics"[tiab])')
PUBMED_EXCLUDE = (' NOT (Review[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt] OR "Case Reports"[pt] '
                  'OR Editorial[pt] OR Comment[pt])')
PUBMED_QUERY_SMALL = PUBMED_LUNG + " AND " + PUBMED_DX_NARROW + " AND hasabstract AND english[la]" + PUBMED_EXCLUDE

def _eutils_params(**p):
    p.update(tool=os.environ.get("NCBI_TOOL", "dxp"), email=os.environ["NCBI_EMAIL"])
    if os.environ.get("NCBI_API_KEY"):
        p["api_key"] = os.environ["NCBI_API_KEY"]
    return p

def _ymd(node):
    if node is None or node.findtext("Year") is None:
        return None
    return "%s-%02d-%02d" % (node.findtext("Year"), int(node.findtext("Month") or 1), int(node.findtext("Day") or 1))

def _pubmed_item(art):
    mc, pd = art.find("MedlineCitation"), art.find("PubmedData")
    a = mc.find("Article")
    pmid = mc.findtext("PMID")
    title = "".join(a.find("ArticleTitle").itertext()) if a.find("ArticleTitle") is not None else ""
    sections = []
    for t in a.findall("Abstract/AbstractText"):
        text = "".join(t.itertext()).strip()
        sections.append("%s: %s" % (t.get("Label"), text) if t.get("Label") else text)
    ids = {i.get("IdType"): i.text for i in pd.findall("ArticleIdList/ArticleId")}   # not the ones in ReferenceList
    hist = {h.get("PubStatus"): _ymd(h) for h in pd.findall("History/PubMedPubDate")}
    ncts = [x.text for x in a.findall("DataBankList/DataBank/AccessionNumberList/AccessionNumber")
            if x.text and x.text.startswith("NCT")]
    doi = ids.get("doi")
    return item(
        "pubmed", pmid, "https://pubmed.ncbi.nlm.nih.gov/%s/" % pmid,
        ids={"pmid": pmid, "doi": doi.lower() if doi else None, "pmcid": ids.get("pmc"), "nct_ids": ncts},
        dates={"entered_pubmed": hist.get("entrez"), "revised": _ymd(mc.find("DateRevised")),
               "electronic_publication": _ymd(a.find("ArticleDate")), "split_date": hist.get("entrez")},
        title=title, raw_text=title + "\n\n" + "\n\n".join(sections),
        licence="PubMed metadata: NLM terms. Abstract: copyright may rest with publisher or authors",
        extra={"journal": a.findtext("Journal/ISOAbbreviation") or a.findtext("Journal/Title"),
               "abstract_copyright": a.findtext("Abstract/CopyrightInformation"),
               "publication_types": [x.text for x in a.findall("PublicationTypeList/PublicationType")],
               "mesh_terms": [x.text for x in mc.findall("MeshHeadingList/MeshHeading/DescriptorName")],
               "is_new_record": bool(hist.get("entrez") and hist["entrez"] >= CUTOFF.isoformat())})

def fetch_pubmed(window="baseline", query=PUBMED_QUERY, max_items=None):
    """window: 'baseline' (entered PubMed 2024/11/14 to 2026/10/16) or 'heldback' (2026/10/17 to 2026/11/14)."""
    lo, hi = (BASELINE_START, BASELINE_END) if window == "baseline" else (CUTOFF, DEMO_DATE)
    gap = 0.11 if os.environ.get("NCBI_API_KEY") else 0.4          # 10 rps with a key, 3 rps without
    s = json.loads(http_get(EUTILS + "esearch.fcgi", _eutils_params(
        db="pubmed", term=query, datetype="edat", mindate=lo.strftime("%Y/%m/%d"), maxdate=hi.strftime("%Y/%m/%d"),
        usehistory="y", retmax=0, retmode="json"), gap)[0])["esearchresult"]
    total = min(int(s["count"]), max_items or 9999)                 # ESearch/history paging stops at 9,999 for PubMed
    out = []
    for start in range(0, total, 200):
        xml = http_get(EUTILS + "efetch.fcgi", _eutils_params(
            db="pubmed", query_key=s["querykey"], WebEnv=s["webenv"],
            retstart=start, retmax=min(200, total - start), retmode="xml"), gap)[0]
        out += [_pubmed_item(a) for a in ET.fromstring(xml).findall("PubmedArticle")]
    return out

# ---------------------------------------------------------------- FDA companion diagnostics list + openFDA
FDA_CDX_URL = ("https://www.fda.gov/medical-devices/in-vitro-diagnostics/"
               "list-fda-authorized-companion-diagnostic-devices-in-vitro-and-imaging-tools")
_SUB = re.compile(r"\b((?:P|K|DEN|H|BK|BR|BP)\d{6})(?:\s*/\s*(S\d{3}))?")
_DATE = re.compile(r"\(\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s*\)")
_NAME = re.compile(r"^(.*?)\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)?\s*$", re.S)
_DRUG = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*(?:(NDA|BLA)\s*(\d{5,6}))?", re.S)

class _Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._t, self._r, self._c = [], None, None, None
    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._t = []; self.tables.append(self._t)
        elif tag == "tr" and self._t is not None:
            self._r = []; self._t.append(self._r)
        elif tag in ("td", "th") and self._r is not None:
            self._c = {"text": "", "links": []}; self._r.append(self._c)
        elif tag == "br" and self._c is not None:
            self._c["text"] += "\n"
        elif tag == "a" and self._c is not None and dict(attrs).get("href"):
            self._c["links"].append(dict(attrs)["href"])
    def handle_endtag(self, tag):
        if tag in ("td", "th"): self._c = None
        elif tag == "tr": self._r = None
        elif tag == "table": self._t = None
    def handle_data(self, data):
        if self._c is not None:
            self._c["text"] += data

def fetch_fda_cdx(lung_only=True):
    """One item per table row: one (device, indication, drug, biomarker, submission) combination."""
    html = http_get(FDA_CDX_URL, accept="text/html", min_interval=2.0)[0].decode("utf-8", "replace")
    m = re.search(r"Content current as of:\s*(?:<[^>]+>\s*)*(\d{2})/(\d{2})/(\d{4})", html)
    page_date = "%s-%s-%s" % (m.group(3), m.group(1), m.group(2)) if m else None
    parser = _Tables(); parser.feed(html)
    header = [re.sub(r"\s+", " ", c["text"]).strip() for c in parser.tables[0][0]]
    assert header[0].startswith("Diagnostic Name") and len(header) == 6, "FDA table layout changed: %s" % header
    out = []
    for row in parser.tables[0][1:]:
        cells = [re.sub(r"[ \t\xa0]+", " ", c["text"]).strip() for c in row]
        if len(cells) != 6 or (lung_only and not re.search(r"lung|NSCLC", cells[1], re.I)):
            continue
        name = _NAME.match(cells[0]); drug = _DRUG.match(cells[2])
        subs = [{"number": n, "supplement": s or None} for n, s in _SUB.findall(cells[5])]
        dates = sorted("%s-%02d-%02d" % (y, int(mo), int(d)) for mo, d, y in _DATE.findall(cells[5]))
        indication, _, sample = re.sub(r"\s*[–—]\s*", " - ", cells[1]).rpartition(" - ")
        raw = " | ".join("%s: %s" % (h, re.sub(r"\s+", " ", c)) for h, c in zip(header, cells))
        latest = subs[-1] if subs else {"number": "unknown", "supplement": None}
        key = normalise("|".join(cells[:4] + [cells[5]])).lower()      # ignores edits to the details column
        row_id = "FDA-CDX:%s%s:%s" % (latest["number"], "/" + latest["supplement"] if latest["supplement"] else "",
                                      hashlib.sha256(key.encode()).hexdigest()[:10])
        out.append(item(
            "fda_cdx_list", row_id, FDA_CDX_URL,
            ids={"fda_submissions": subs, "drug_application": "%s %s" % (drug.group(3), drug.group(4))
                 if drug and drug.group(3) else None},
            dates={"decision_dates": dates, "page_content_current_as_of": page_date,
                   "split_date": dates[-1] if dates else None},
            title=cells[0], raw_text=raw, licence="US Government work, public domain (FDA website policies)",
            extra={"assay": name.group(1).strip() if name else cells[0],
                   "company": name.group(2).strip() if name else None,
                   "indication": indication or cells[1], "sample_type": sample or None,
                   "drug_trade_name": drug.group(1).strip() if drug else cells[2],
                   "drug_generic_name": drug.group(2).strip() if drug else None,
                   "biomarkers": cells[3], "biomarker_details": cells[4], "record_links": row[5]["links"],
                   "is_new_record": bool(dates and dates[-1] >= CUTOFF.isoformat())}))
    return out

def fetch_openfda_pma(pma_numbers, window=None):
    """Decision records (original PMA and every supplement) for the given PMA numbers. window as fetch_ctgov."""
    search = "(%s)" % "+OR+".join("pma_number:" + n for n in sorted(set(pma_numbers)))
    if window == "baseline":
        search += "+AND+decision_date:[1976-01-01+TO+%s]" % BASELINE_END.isoformat()
    elif window == "heldback":
        search += "+AND+decision_date:[%s+TO+%s]" % (CUTOFF.isoformat(), DEMO_DATE.isoformat())
    key = "&api_key=" + os.environ["OPENFDA_API_KEY"] if os.environ.get("OPENFDA_API_KEY") else ""
    out, skip = [], 0
    while True:
        url = "https://api.fda.gov/device/pma.json?search=%s&sort=decision_date:asc&limit=1000&skip=%d%s" % (search, skip, key)
        try:
            body = json.loads(http_get(url, min_interval=0.5)[0])
        except urllib.error.HTTPError as e:
            if e.code == 404:                       # openFDA answers 404 when nothing matches
                return out
            raise
        for r in body["results"]:
            sub = r["pma_number"] + ("/" + r["supplement_number"] if r.get("supplement_number") else "")
            raw = "\n".join("%s: %s" % (k, r.get(k, "")) for k in
                            ("trade_name", "generic_name", "applicant", "supplement_type", "supplement_reason",
                             "decision_code", "ao_statement"))
            out.append(item(
                "openfda_device_pma", sub,
                "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpma/pma.cfm?id=" + sub.replace("/", ""),
                ids={"fda_submissions": [{"number": r["pma_number"], "supplement": r.get("supplement_number") or None}],
                     "product_code": r.get("product_code")},
                dates={"decision_date": r.get("decision_date"), "date_received": r.get("date_received"),
                       "source_last_updated": body["meta"]["last_updated"], "split_date": r.get("decision_date")},
                title=r.get("trade_name"), raw_text=raw, licence="CC0 1.0 (openFDA)",
                extra={"assay": r.get("trade_name"), "company": r.get("applicant"),
                       "decision_code": r.get("decision_code"), "supplement_reason": r.get("supplement_reason"),
                       "is_new_record": not r.get("supplement_number")}))
        skip += 1000
        if skip >= body["meta"]["results"]["total"]:
            return out
```

## Notes on the code

- `http_get` spaces calls per host and backs off on 429 and 5xx. Spacing used: ClinicalTrials.gov 1.2 s, E-utilities 0.4 s (0.11 s with a key), fda.gov 2 s, openFDA 0.5 s.
- ClinicalTrials.gov text arrives with markdown backslash escapes (`\>`, `\<`, `\*`, `\[`, `\-`, `\&`, `\^`). `_MD_ESCAPE` removes them before the text is stored, so a quote copied by the model matches.
- `normalise` (Unicode NFKC plus whitespace collapse) must be applied to both sides of the quote check. PubMed abstracts contain thin spaces and non-breaking spaces; the FDA table contains non-breaking spaces.
- PubMed `ArticleIdList` appears twice in a record: once under `PubmedData` (the article's own IDs) and once per cited reference under `ReferenceList`. The code reads only the first. Using `.iter("ArticleId")` would attach other papers' DOIs.
- `fetch_fda_cdx` asserts the six column headers. If FDA changes the table, it fails loudly instead of returning shifted columns.
- `fetch_openfda_pma` treats HTTP 404 as "no results", which is how openFDA answers an empty search.
- The FDA row key is built from the assay, indication, drug, biomarker and submission cells, so an edit to the biomarker details column does not create a new Source item.
