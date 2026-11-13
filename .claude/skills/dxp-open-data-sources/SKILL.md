---
name: dxp-open-data-sources
description: The open public sources DxP ingests for lung cancer diagnostics (ClinicalTrials.gov API v2, PubMed through NCBI E-utilities, the FDA companion diagnostics list, openFDA device endpoints) and the vocabularies it normalises to (HGNC, OncoTree, NCI Thesaurus, MeSH). Load when a task touches `clinicaltrials.gov/api/v2`, `query.term`, `filter.advanced`, `esearch`, `efetch`, `eutils`, PMID, NCT ID, DOI, PMA or 510(k) numbers, `api.fda.gov`, companion diagnostic, Baseline load, Held-back set, source fetchers, Source item IDs, quote checking against source text, licences or the "open data only" rule.
---

# Open data sources for DxP

| Source | What DxP takes | Access | Key | Rate limit | Licence or terms | Open data only |
|---|---|---|---|---|---|---|
| ClinicalTrials.gov API v2 | Lung trials that use or study a diagnostic | REST JSON, `GET /api/v2/studies` | None | Not published (`UNVERIFIED`); keep to 1 request per second | Site terms: free; attribute, show processing date, state modifications | Pass |
| PubMed (E-utilities) | Citation and abstract | `esearch` then `efetch`, XML | Optional `api_key` | 3 per second without a key, 10 with | Metadata under NLM terms; abstract copyright may belong to publisher or authors | Pass with conditions: quote, cite and link; never redistribute abstracts |
| PubMed Central | Full text, Open Access Subset only | `efetch` with `db=pmc` | Same | Same | Per-article Creative Commons licence | Pass only for CC0, CC BY, CC BY-SA, CC BY-ND |
| FDA companion diagnostics list | Assay, company, indication, sample type, drug, biomarker, submission number, date | One HTML page, parse the table | None | None published; fetch once and cache | Public domain | Pass |
| openFDA `device/pma`, `device/510k` | Approval and clearance decisions, supplements | REST JSON | Optional `api_key` | 240 per minute; 1,000 per day per IP without a key, 120,000 per day with | CC0 1.0 | Pass |
| HGNC | Gene symbols and aliases | Bulk TSV, or REST | None | REST 10 per second | CC0 | Pass |
| OncoTree | Lung tumour type codes | REST | None | Not published | CC BY 4.0 | Pass, with attribution |
| NCI Thesaurus, MeSH | Synonyms for modalities and analytes | REST | None | Not published | CC BY 4.0; NLM MeSH terms | Pass, with attribution |

Provider websites, the fourth Source in the PRD, are in the `dxp-tavily` skill.

## Verified

Checked 12 November 2026 with live, key-free, read-only requests and these pages.

- ClinicalTrials.gov REST API 2.0.5 (`/api/v2/version`, `dataTimestamp` 2026-11-12T10:00:05): OpenAPI file `https://clinicaltrials.gov/api/oas/v2`, `https://clinicaltrials.gov/data-api/api`, `/find-studies/constructing-complex-search-queries`, `/about-site/terms-conditions`.
- E-utilities (PubMed build 2026.11.12): `https://www.ncbi.nlm.nih.gov/home/about/policies/`, `https://support.nlm.nih.gov/kbArticle/?pn=KA-05317`, `https://www.nlm.nih.gov/dataguide/eutilities/utilities.html`, `https://www.nlm.nih.gov/databases/download/terms_and_conditions.html`, PMC pages listed in `references/terms.md`.
- FDA list, "Content current as of 11/03/2026", 235 rows. openFDA `meta.last_updated` 2026-11-02: `https://open.fda.gov/apis/authentication/`, `/apis/paging/`, `/apis/dates-and-ranges/`, `/apis/device/`, `/license/`, `/terms/`.
- HGNC file dated 10 November 2026; OncoTree `oncotree_latest_stable` released 2025-10-03; NCI EVS REST API 2.5.1.

`UNVERIFIED`: the ClinicalTrials.gov rate limit (none is published; no rate headers are returned). The E-utilities manual (`/books/NBK25497/`, `NBK25499`, `NBK25501`) sits behind a browser check and could not be read, so `usehistory`, `WebEnv` and `query_key` are confirmed by live calls only, and the status code for exceeding the limit was not seen. Where HDE (`H…`) and CBER (`BK…`, `BR…`) submissions live in openFDA. That DOIs are case-insensitive.

## Read this first

1. **The FDA page has moved and has no data file.** It is now "List of FDA-Authorized Companion Diagnostic Devices (In Vitro and Imaging Tools)" at `.../list-fda-authorized-companion-diagnostic-devices-in-vitro-and-imaging-tools`. The old `list-cleared-or-approved-...` URL returns a 301. There is no CSV, Excel or JSON download (the Excel button is browser-side), so parse the HTML table.
2. **FDA gives the Held-back set almost nothing.** The list has no lung row dated after 16 October 2026 (the newest is 9 September). openFDA has two PMA decisions in the window for lung assays: `P240037/S003` (23 October, labelling update, VENTANA MET (SP44) RxDx Assay) and a manufacturing notice. Real updates and Alerts on Saturday must come from ClinicalTrials.gov (45 items) and PubMed (90 items).
3. **PubMed abstracts are public, not openly licensed.** They pass "publicly available, not paywalled", but they may not be redistributed. The submission needs a public repository: do not commit abstract text to it. Details in `references/terms.md`.
4. **The wide query is far larger than the 300 to 500 batch in FR-4.** About 3,300 Baseline items. Pick a smaller set from the sizing table below.
5. **ClinicalTrials.gov returns only the current version of a record.** A trial updated after the cut-off cannot be fetched as it stood before. The split below therefore keeps such trials out of the Baseline load.
6. **ClinicalTrials.gov text has markdown escapes** (`\>`, `\<`, `\*`) that break a word-for-word quote check unless removed.
7. **No identifier for a Diagnostic is shared by the three sources.** NCT IDs and PMIDs link trials to papers; nothing links either to an FDA submission except the assay name.
8. **The PMC OA Web Service (`oa.fcgi`) was retired in 2026.** Use `efetch` with `db=pmc`.
9. **ClinicalTrials.gov refreshes Monday to Friday** by about 09:00 Eastern. On Saturday the data is Friday's. NCBI asks that runs of more than 100 requests happen at weekends or 21:00 to 05:00 Eastern on weekdays: Saturday is fine, a Friday afternoon bulk pull is not.

## What DxP uses it for

- FR-1, FR-4: fetch Source items for scheduled and manual scans, in batches.
- FR-2: every item carries a `source` from an approved Source type.
- FR-3: stable Source item IDs and the cross-source identifiers for the match key.
- FR-5, FR-7, FR-18: `raw_text` and `source_url` for Evidence and the word-for-word quote check.
- FR-9: HGNC, OncoTree, NCI Thesaurus and MeSH for standard terms and synonyms.
- FR-15: an updated trial or a new PMA supplement is the trigger for a Proposed change.
- FR-30: exact date filters for the Baseline load and the Held-back set.
- Constraint "Open data only": the table above and `references/terms.md`.

## Setup

No packages: the fetchers use the Python standard library. No account is needed for any source.

Environment variable names (the code's own names; the services take them as URL parameters):

- `NCBI_EMAIL` (required): sent as `email` on every E-utilities call. `NCBI_TOOL` (optional, default `dxp`): sent as `tool`, no spaces.
- `NCBI_API_KEY` (optional): sent as `api_key`; raises the limit from 3 to 10 requests per second. Created in NCBI account settings, "API Key Management". Not needed for Saturday's volumes.
- `OPENFDA_API_KEY` (optional): only matters above 1,000 requests a day from one IP.

## Core patterns

Complete tested code: `references/fetchers.md` (`dxp_sources.py`: `fetch_ctgov`, `fetch_pubmed`, `fetch_fda_cdx`, `fetch_openfda_pma`, `quote_in_source`) and `references/vocabularies.md` (`dxp_vocab.py`). Each fetcher pages through the source and returns plain dictionaries:

```python
{"source": "clinicaltrials.gov", "source_item_id": "NCT05925530",
 "source_url": "https://clinicaltrials.gov/study/NCT05925530",
 "ids": {"nct_id": "NCT05925530", "pmids": ["42934326"], "secondary_ids": [...]},
 "dates": {"first_posted": "...", "last_update_posted": "...", "source_data_timestamp": "...", "split_date": "..."},
 "title": "...", "raw_text": "Brief title: ...\n\nBrief summary: ...",   # what a quote is checked against
 "text_sha256": "...", "retrieved_at": "...", "licence": "...", "extra": {"is_new_record": False, ...}}
```

### ClinicalTrials.gov

`GET https://clinicaltrials.gov/api/v2/studies` with `query.cond`, `query.term`, `filter.advanced`, `fields` (pipe-separated), `pageSize` (default 10, maximum 1,000), `countTotal=true`, `sort`, then `pageToken=<nextPageToken>` until the response has no `nextPageToken`. Later pages must repeat the same parameters. `totalCount` is returned on the first page only.

Tested `query.term` values with `query.cond=lung cancer` (all registrations):

| Topic | `query.term` | Trials |
|---|---|---|
| ctDNA | `ctDNA OR "circulating tumor DNA"` | 455 |
| Liquid biopsy | `"liquid biopsy"` | 176 |
| MRD | `MRD OR "minimal residual disease" OR "molecular residual disease"` | 133 |
| Companion diagnostic | `"companion diagnostic"` | 8 |
| Biomarker | `biomarker` | 2,000 |
| Digital pathology | `"digital pathology"` | 10 |
| Radiomics | `radiomics` | 79 |
| Methylation | `methylation` | 108 |
| All of the above | joined with `OR` | 2,477 |
| All except biomarker (`CTGOV_TERM`, the default) | joined with `OR` | 744 |

Date filters use the Essie `AREA[...]RANGE[...]` syntax in `filter.advanced`, dates as `YYYY-MM-DD`, `MIN` and `MAX` for open ends, both ends inclusive:

- First posted in the last four weeks: `AREA[StudyFirstPostDate]RANGE[2026-10-17,MAX]` (11 with the default term).
- Updated in the last four weeks: `AREA[LastUpdatePostDate]RANGE[2026-10-17,MAX]` (45).
- Older trials updated in the last four weeks: `AREA[StudyFirstPostDate]RANGE[MIN,2026-10-16] AND AREA[LastUpdatePostDate]RANGE[2026-10-17,MAX]` (34).

### PubMed

Base `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`. `esearch.fcgi?db=pubmed&term=...&datetype=edat&mindate=YYYY/MM/DD&maxdate=YYYY/MM/DD&usehistory=y&retmode=json` returns `count`, `webenv` and `querykey`; then `efetch.fcgi?db=pubmed&query_key=...&WebEnv=...&retstart=N&retmax=200&retmode=xml` returns `PubmedArticle` records. Send `tool` and `email` on every call.

Tested query (`PUBMED_QUERY`), lung cancer diagnostics abstracts, entered in PubMed 14 November 2024 to 14 November 2026: 2,612 records.

```text
("Lung Neoplasms"[MeSH Terms] OR "lung cancer"[tiab] OR "lung adenocarcinoma"[tiab] OR NSCLC[tiab] OR SCLC[tiab])
AND (ctDNA[tiab] OR "circulating tumor DNA"[tiab] OR "circulating tumour DNA"[tiab] OR "liquid biopsy"[tiab]
  OR "minimal residual disease"[tiab] OR "molecular residual disease"[tiab] OR "companion diagnostic"[tiab]
  OR "companion diagnostics"[tiab] OR "digital pathology"[tiab] OR radiomics[tiab] OR methylation[tiab])
AND hasabstract AND english[la]
```

By topic over the same two years: ctDNA 582, liquid biopsy 623, MRD 144, companion diagnostic 45, digital pathology 99, radiomics 908, methylation 655, biomarker 6,068 (left out of the query).

### FDA

`fetch_fda_cdx()` reads the first table on the page. Six columns: "Diagnostic Name (Manufacturer)", "Indication - Sample Type", "Drug Trade Name (Generic) NDA / BLA", "Biomarker(s)", "Biomarker(s) (Details)", "PMA / 510(k) / 513(f)(2) / HDE (Approval / Clearance / Grant Date)". One row is one combination of assay, indication, drug and biomarker, so one assay spans many rows (FoundationOne CDx has 14 lung rows). 76 of 235 rows are lung, all NSCLC, across 20 assays (21 name strings, one a typo) and 22 PMA numbers. A second table lists group labelling claims.

openFDA adds the decision history: `https://api.fda.gov/device/pma.json?search=pma_number:P200010+AND+supplement_number:S027` gives applicant, `trade_name`, `decision_date`, `decision_code`, `supplement_reason` and `ao_statement` (the approval order text, usable as a quote source). `device/510k.json?search=k_number:K173492` covers 510(k) clearances and also De Novo numbers (`k_number:DEN170058` resolves). `search` takes `field:term`, `+AND+`, `+OR+`, date ranges `[2026-10-17+TO+2026-11-14]`; `limit` maximum 1,000; `skip` for paging.

### FR-30: Baseline load and Held-back set

Demo date 14 November 2026. Cut-off: Baseline load is everything dated up to and including **16 October 2026**; Held-back set is **17 October to 14 November 2026**.

| Source | Split on | Baseline load | Held-back set | Counts today |
|---|---|---|---|---|
| ClinicalTrials.gov | `LastUpdatePostDate` | `filter.advanced=AREA[LastUpdatePostDate]RANGE[MIN,2026-10-16]` | `AREA[LastUpdatePostDate]RANGE[2026-10-17,MAX]` | 699 / 45 (11 new, 34 updated older trials) |
| PubMed | Entry date `[edat]` | `datetype=edat&mindate=2024/11/14&maxdate=2026/10/16` | `datetype=edat&mindate=2026/10/17&maxdate=2026/11/14` | 2,522 / 90 |
| FDA list | Latest date in the last column | date on or before 2026-10-16 | date on or after 2026-10-17 | 76 lung rows / 0 |
| openFDA PMA | `decision_date` | `decision_date:[1976-01-01+TO+2026-10-16]` | `decision_date:[2026-10-17+TO+2026-11-14]` | 425 / 2 (22 lung PMA numbers) |

- ClinicalTrials.gov: `LastUpdatePostDate` is the date a change became public, so an older trial with a new update lands in the Held-back set and counts as an update. `extra.is_new_record` is true when `StudyFirstPostDate` is also inside the window. Do not split on `StudyFirstPostDate`: the 34 updated trials would enter the Baseline load with their post-cut-off content. Use the "post" dates, not the "submit" dates, which precede publication.
- PubMed: `[edat]` is the date the record entered PubMed and never changes, so it partitions cleanly. The modification date `[mdat]` is too noisy to split on: 470 records in the set were modified in the window, 209 of them older records, mostly indexing changes. For later scans, re-fetch records with a recent `[mdat]` and treat one as updated only when `text_sha256` differs.
- FDA: a new supplement on an existing PMA (for example `P200010/S027` adding an indication) is how an existing assay is updated. It appears as a new list row and a new openFDA record with its own `decision_date`.

Sizing for FR-4 (Baseline / Held-back):

| Set | ClinicalTrials.gov | PubMed |
|---|---|---|
| Wide (defaults) | 699 / 45 | 2,522 / 90 |
| Narrow topics: ctDNA, liquid biopsy, MRD, companion diagnostic | 557 / 40 | 1,032 / 49 |
| Narrow, PubMed without reviews and case reports (`PUBMED_QUERY_SMALL`) | - | 627 / 24 (323 for one year back) |
| Baseline limited to trials updated since 14 November 2024 | 346 wide, 293 narrow | - |

### FR-3: stable identifiers

| Identifier | Format | Where it comes from | Notes |
|---|---|---|---|
| NCT ID | `NCT` and 8 digits | `protocolSection.identificationModule.nctId` | Upper-case it. Old IDs redirect (`NCTIdAlias`) |
| PMID | Digits | `MedlineCitation/PMID` | Unique key for a PubMed item |
| DOI | `10.…` | `PubmedData/ArticleIdList/ArticleId[@IdType="doi"]` | Lower-case before comparing. Missing on some records |
| PMCID | `PMC` and digits | Same list, `IdType="pmc"` | Present only when full text is in PMC |
| FDA submission | `P` and 6 digits, optional `/S` and 3 digits; `K` and 6; `DEN` and 6; `H` and 6; `BK` or `BR` and 6 | Last column of the list; `pma_number` and `supplement_number`, or `k_number` | The PMA number without supplement identifies the device; the supplement identifies one decision |

How one Diagnostic appears, using Guardant360 CDx:

- FDA list: "Guardant360 CDx (Guardant Health, Inc.)", `P200010` and supplements, one row per drug and biomarker. "Guardant360® Liquid CDx" (`P250027`) is a different device.
- openFDA: `trade_name` "Guardant360 CDx" or "Guardant360® CDx" (it varies between records), `applicant`, `product_code` `PQP`.
- ClinicalTrials.gov: free text only, in intervention names, other names, descriptions and keywords (10 lung trials mention "Guardant360"). No FDA number.
- PubMed: free text in title and abstract (69 lung records). No device identifier.
- Trial to paper links exist both ways: `referencesModule.references[].pmid` in a trial, and `DataBankList/.../AccessionNumber` in a PubMed record (search with `NCT05925530[si]`).

So the match key cannot be an external ID. Workable inputs for architecture: normalised assay name (lower-case, `®` and `™` removed, punctuation and spaces collapsed) plus normalised Provider, with the PMA or 510(k) number as a strong alias when known. Source items are deduplicated separately on `(source, source_item_id)`.

## Limits and costs

- All sources are free. A full wide Baseline load is about 8 ClinicalTrials.gov calls, 14 E-utilities calls, 1 FDA page and 1 openFDA call: under a minute.
- Fetch once, store, then run the 300 to 500 item batch from MongoDB. Never call these sources from inside the parallel extraction workers.
- E-utilities: 3 requests per second per IP without a key, shared by everyone on the venue network if it uses one public address. `X-RateLimit-Limit: 3` is returned.
- PubMed search results stop at 9,999 records per query; split by date range if a query is larger.
- openFDA without a key: 1,000 requests per day per IP.
- ClinicalTrials.gov `pageSize` above 1,000 is reduced to 1,000.

## Gotchas

- ClinicalTrials.gov `fields` rejects unknown names with HTTP 400 and names the bad field. Names are the "piece" names (`NCTId`, `LastUpdatePostDate`), while JSON keys are camelCase and nested (`statusModule.lastUpdatePostDateStruct.date`).
- ClinicalTrials.gov partial dates occur (`"2029-02"` for a planned completion). The post dates were full `YYYY-MM-DD` dates in every record fetched, so string comparison is safe for those only.
- `markupFormat=legacy` avoids the markdown escapes but hard-wraps lines; the default with escapes removed is easier to match quotes against.
- The `COVERAGE` and `EXPANSION` operators are not fully implemented in the current API. Do not rely on them.
- Search terms are expanded with synonyms by default, so `query.cond=lung cancer` also returns trials worded differently. A bare abbreviation such as `MRD` can match unrelated meanings; let the triage pass drop those.
- PubMed `AbstractText` can contain inline tags (`<i>`, `<sup>`); read it with `itertext()`. Structured abstracts have several `AbstractText` elements with a `Label`.
- PubMed MeSH terms are missing on new records, so the query needs title and abstract words as well as MeSH.
- openFDA returns HTTP 404 with `NOT_FOUND` for an empty result, not an empty list.
- openFDA does not hold HDE numbers (`H140005` is not in `device/pma`), and there is no De Novo endpoint.
- The FDA list has typos and inconsistent names (a missing closing bracket, "PD-LI" for "PD-L1", `®` on some rows only). Normalise before matching.
- OncoTree answers 403 when the `User-Agent` contains an e-mail address. The NCI EVS host stalls Python `urllib` on networks without working IPv6. Both are in `references/vocabularies.md`.

## Fallback

- Before the event, run the fetchers once and save each list as JSON Lines. Event rules require data prepared beforehand to be disclosed: say so in the demo.
- ClinicalTrials.gov, FDA and openFDA snapshots may be committed, with the source and fetch date. Keep the PubMed snapshot out of the public repository (commit the PMID list and re-fetch).
- If a source is down on the day, load its snapshot and filter on `dates.split_date` in Python: at or before `2026-10-16` for the Baseline load, after it for the Held-back set.
- If ClinicalTrials.gov paging fails, one call with `pageSize=1000` returns the whole default set.
- If the FDA page layout changes, `fetch_fda_cdx` raises on the header check; fall back to openFDA `device/pma` for the 22 lung PMA numbers.

## Links

- ClinicalTrials.gov API: https://clinicaltrials.gov/data-api/api and https://clinicaltrials.gov/api/oas/v2
- ClinicalTrials.gov query syntax: https://clinicaltrials.gov/find-studies/constructing-complex-search-queries
- ClinicalTrials.gov terms: https://clinicaltrials.gov/about-site/terms-conditions
- E-utilities parameters: https://www.nlm.nih.gov/dataguide/eutilities/utilities.html
- NCBI policies (scripting rules, abstract copyright): https://www.ncbi.nlm.nih.gov/home/about/policies/
- E-utilities manual (browser only): https://www.ncbi.nlm.nih.gov/books/NBK25501/
- FDA list: https://www.fda.gov/medical-devices/in-vitro-diagnostics/list-fda-authorized-companion-diagnostic-devices-in-vitro-and-imaging-tools
- openFDA device APIs: https://open.fda.gov/apis/device/ and https://open.fda.gov/apis/authentication/
- PMC text mining and licences: https://pmc.ncbi.nlm.nih.gov/tools/textmining/
- HGNC REST: https://www.genenames.org/help/rest/ ; OncoTree API: https://oncotree.mskcc.org/swagger/index.html ; NCI EVS: https://api-evsrest.nci.nih.gov/swagger-ui/index.html
