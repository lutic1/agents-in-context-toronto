# Terms of use, source by source

Read on 12 November 2026. This is a developer summary, not legal advice. The team rule is "open data only": every Source item openly and publicly available, nothing licensed or paywalled, no congress abstracts or posters.

## ClinicalTrials.gov

Source: `https://clinicaltrials.gov/about-site/terms-conditions` (last updated 31 January 2023).

- Data are available to all requesters at no charge. Downloading means accepting the terms, whatever the format or method.
- In any publication or distribution of the data, DxP should:
  1. attribute the source as ClinicalTrials.gov;
  2. keep the data current;
  3. display the date the data were processed by ClinicalTrials.gov (use `dataTimestamp` from `GET /api/v2/version`, stored as `dates.source_data_timestamp`);
  4. state any modifications made to the content.
- Do not claim proprietary rights over the data or present it as anything other than a United States Government database.
- Do not use e-mail addresses from the records for marketing. The fetcher does not request contact fields.
- The data carry an international copyright outside the United States, and some data may be under third-party copyright.

What this means for DxP: store and display freely, with a "Source: ClinicalTrials.gov, data as of <dataTimestamp>" line on every Evidence panel and export. Extracted field values are a modification: say that fields were extracted by DxP and link to the registration. Point 2 is a reason the Held-back set must be labelled as a dated snapshot in the demo.

## PubMed

Sources: `https://www.ncbi.nlm.nih.gov/home/about/policies/` and `https://www.nlm.nih.gov/databases/download/terms_and_conditions.html` (last reviewed 21 May 2019).

- NLM's own position, in its words: "NLM does not claim the copyright on the abstracts in PubMed; however, journal publishers or authors may."
- NLM gives no legal advice on distributing copyrighted material and tells users to consult their own counsel.
- NCBI asks that its disclaimer and copyright notice be evident to users of a service built on its data.
- NLM data terms: no fee; credit NLM as the source; do not imply NLM endorsement; if redistributing, keep the data current or say clearly that it may not be the latest.
- Many records carry the publisher's notice in `<CopyrightInformation>` inside `<Abstract>`. The fetcher stores it as `extra.abstract_copyright`.

So the citation metadata is free to use, and the abstract text is free to read and fetch but is not licensed for redistribution. No NLM page grants a right to republish abstracts. Team policy for Saturday:

| DxP may | DxP should not |
|---|---|
| Fetch abstracts through E-utilities and keep them in the private Atlas database for extraction and the FR-18 check | Commit abstract text to the public repository, in seed files, fixtures, Gold set files or test snapshots |
| Store PMID, DOI, title, journal, dates, MeSH terms, publication types, linked NCT IDs | Show a whole abstract in the UI, the Digest, the audio briefing or the video |
| Show a short supporting quote per field (a sentence or two) with the citation, PMID, DOI and a link to `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` | Export full abstracts (FR-25): export the quote, citation and link only |
| Show the publisher's copyright line where it exists | Offer a bulk download or API of abstract text |

For the Gold set (30 to 50 hand-labelled Source items), keep PMIDs and labels in the repository and re-fetch the text at run time.

## PubMed Central (full text)

Sources: `https://pmc.ncbi.nlm.nih.gov/about/copyright/`, `https://pmc.ncbi.nlm.nih.gov/tools/textmining/`, `https://pmc.ncbi.nlm.nih.gov/tools/openftlist/`, `https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/`, `https://pmc.ncbi.nlm.nih.gov/tools/oa-service/`.

- Being free to read in PMC does not make an article reusable. Only the PMC Open Access Subset (and the other Article Datasets) are licensed for reuse, and the licence varies by article.
- Licence groups in the Open Access Subset: commercial use allowed (CC0, CC BY, CC BY-SA, CC BY-ND); non-commercial only (CC BY-NC, CC BY-NC-SA, CC BY-NC-ND); other (custom or no machine-readable licence).
- Automated retrieval is allowed only through the PMC Cloud Service, the OAI-PMH service, E-utilities and the BioC API. Scraping article pages on the PMC website is prohibited.
- Find candidates in PubMed with the filter `"pubmed pmc open access"[filter]` (1,768 of the 2,612 abstracts in the wide two-year lung set).
- Retrieve with `efetch.fcgi?db=pmc&id=<numeric PMCID>&retmode=xml` (tested). The licence is in `<license>` with a `license_ref` URL such as `https://creativecommons.org/licenses/by/4.0/`. Keep the full text only when that URL is CC0, CC BY, CC BY-SA or CC BY-ND, store the licence URL with the item, and attribute the article.
- Alternative: BioC API, `https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/<PMID or PMCID>/unicode`. It covers the Open Access Subset and the Author Manuscript collection. It answered HTTP 429 once during light testing.
- Retired in 2026: the PMC OA Web Service (`oa.fcgi`) is no longer available, and the legacy dataset files on FTP and the cloud were removed in the week of 24 August 2026. The cloud bucket is now `https://pmc-oa-opendata.s3.amazonaws.com/`, with licence information in per-article JSON metadata. Do not write code against `oa.fcgi` or the old `oa_comm` and `oa_noncomm` folders.

Full text is optional for Saturday. Abstracts are enough for the ten fields.

## FDA

Sources: `https://www.fda.gov/about-fda/about-website/website-policies`, `https://open.fda.gov/license/`, `https://open.fda.gov/terms/`.

- fda.gov content, unless marked otherwise, is not copyrighted, is in the public domain and may be republished without permission. Credit to FDA is appreciated, not required. FDA suggests noting the date of a copy and linking back.
- openFDA data are public domain under a CC0 1.0 dedication. Credit is requested, not required: "Data provided by the U.S. Food and Drug Administration (https://open.fda.gov)". Do not imply FDA endorsement.
- One exception inside openFDA: GMDN terms (in the UDI dataset) are licensed from the GMDN Agency. DxP does not use the UDI endpoint.
- Every openFDA response carries a disclaimer that results are unvalidated and not for decisions about medical care. That fits the PRD non-goal (not a clinical decision tool).
- Drug and assay trade names are trademarks. Naming them is fine; do not use logos.

## Vocabularies

| Vocabulary | Licence | What to do |
|---|---|---|
| HGNC | CC0 | Nothing required. Citing genenames.org is recommended. |
| OncoTree | CC BY 4.0 (`github.com/cBioPortal/oncotree`, `LICENSE.md`) | Credit OncoTree and cite Kundra et al., JCO Clinical Cancer Informatics 2021. |
| NCI Thesaurus | CC BY 4.0 | Credit NCI Thesaurus (NCI EVS). Do not call a modified copy "NCI Thesaurus". |
| MeSH | NLM MeSH terms | Acknowledge NLM as the source; if redistributed, state the MeSH version or keep it current. |

## Excluded by the team rule

- Congress abstracts, posters and presentations, and photographs of posters (PRD section 6.2).
- Publisher sites and full text outside the PMC Open Access Subset.
- Any source that needs a licence agreement, a paid tier or a login to read.

## One credits line for the app footer and the project description

> Data: ClinicalTrials.gov (U.S. National Library of Medicine), PubMed (courtesy of the U.S. National Library of Medicine), U.S. Food and Drug Administration (fda.gov and open.fda.gov), HGNC, OncoTree (CC BY 4.0), NCI Thesaurus (CC BY 4.0). DxP is not endorsed by these organisations. Abstract copyright remains with publishers or authors.
