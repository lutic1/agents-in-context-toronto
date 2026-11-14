# DxP datasets

> **Not used on Saturday 14 November without written clearance.** These files were prepared before the event. They are not loaded, and the scripts in `scripts/data/` are not re-run, on Saturday 14 November unless an organiser clears them in writing. The build fetches the selected trials (from the ClinicalTrials.gov API v2) and the FDA list of companion diagnostics during the event. This README is kept as a record of what was downloaded.

Open public data for the DxProvida (DxP) hackathon build, downloaded on 13 November 2026, the day before the event.

## Disclosure

The hackathon rules require work prepared beforehand to be disclosed. This folder and `scripts/data/` are that work: the data was downloaded and split before Saturday 14 November 2026, and the download scripts were written before the event. Nothing here is product code.

## What is here

| Folder | Source | Baseline (to 16 Oct 2026) | Held back (17 Oct to 14 Nov 2026) | In this repo |
|---|---|---|---|---|
| `clinicaltrials/` | ClinicalTrials.gov API v2, lung cancer trials on diagnostics topics | 699 trials | 45 trials (11 new, 34 updated) | Yes |
| `pubmed/` | PubMed through NCBI E-utilities, lung diagnostics abstracts from 14 Nov 2024 | 2,521 records | 90 records | Manifest only |
| `fda/` | FDA list of authorized companion diagnostics, and openFDA PMA decisions | 76 lung rows, 425 decisions | 2 decisions | Yes |
| `vocab/` | HGNC genes, OncoTree lung codes, NCI Thesaurus and MeSH synonyms | 45,387 genes, 30 lung codes, 15 terms | not applicable | Yes |

The baseline was planned as what DxP loads first, with no alerts. The held-back set is real data from the last four weeks, ingested during the demo so that updates and alerts come from real changes (PRD requirement FR-30).

Each folder has a `manifest.json` with the fetch time, the source's own data date, the exact queries, counts, file hashes, the attribution line, and the command that reproduces the download.

## Smaller batches

The downloads are wider than the 300 to 500 item batch the PRD plans for. The manifests list the IDs of narrower subsets, so a batch can be chosen without downloading again:

- `clinicaltrials/manifest.json`: `narrow` (557 baseline, 40 held back) and `recent_baseline_narrow` (293 trials updated since 14 Nov 2024).
- `pubmed/manifest.json`: `narrow` (1,031 and 49), `small` (626 and 24, without reviews and case reports) and `small_one_year` (322).

## PubMed abstracts are not in this repository

PubMed abstracts are public to read, but their copyright may belong to publishers or authors and they are not licensed for redistribution. The text files `pubmed/baseline.jsonl` and `pubmed/heldback.jsonl` are excluded by `.gitignore`. Only the manifest is committed: PMIDs, dates and counts, with no abstract text and no titles.

To get the text on your own machine:

```bash
NCBI_EMAIL=<your email> uv run --python 3.12 python scripts/data/fetch_pubmed.py
```

NCBI asks for a contact email on automated requests. It is read from the environment and is not written to any file.

## How the files were made

All scripts use the Python standard library only, from the repository root:

```bash
uv run --python 3.12 python scripts/data/fetch_clinicaltrials.py
uv run --python 3.12 python scripts/data/fetch_fda.py
uv run --python 3.12 python scripts/data/fetch_vocab.py
```

Do not re-run these on Saturday 14 November unless an organiser clears it in writing. The build fetches the selected trials and the FDA list during the event.

## Known gaps

- **"Liquid biopsy" does not link to ctDNA in the public vocabularies.** NCI Thesaurus and MeSH hold them as separate concepts with no shared synonym. The link that requirement FR-9 tests has to be added by the team as a curated entry, labelled as such.
- **Some synonym matches are noisy.** The MRD query returned unrelated concepts; the usable one is NCI Thesaurus C3896. "Digital pathology" returned nothing from either service. Review `vocab/synonyms.json` before using it to expand searches.
- **One PubMed record is missing.** PMID 30335319 is a book chapter, which the fetcher does not parse.
- **FDA adds little to the held-back set.** Its two decisions in the window are a labelling change and a manufacturing change. Demo updates come from ClinicalTrials.gov and PubMed.
- **No shared identifier.** Nothing links a diagnostic across the three sources except its name. `fda/assays.json` holds normalised assay names with the original spellings alongside.

## Attribution and terms

Data: ClinicalTrials.gov (U.S. National Library of Medicine), PubMed (courtesy of the U.S. National Library of Medicine), U.S. Food and Drug Administration (fda.gov and open.fda.gov), HGNC, OncoTree (CC BY 4.0), NCI Thesaurus (CC BY 4.0), MeSH (U.S. National Library of Medicine). DxP is not endorsed by these organisations. Abstract copyright remains with publishers or authors.

- **ClinicalTrials.gov.** Data as processed by ClinicalTrials.gov on 12 November 2026. Modifications: selected fields only were requested and joined into one `raw_text` field per trial, markdown escape characters were removed, and DxP added a text hash and retrieval time. The files are a dated snapshot and may not be the latest.
- **FDA.** Public domain (fda.gov) and CC0 1.0 (openFDA). List content current as of 3 November 2026. `fda/assays.json` is derived by DxP from the list, with assay names normalised.
- **HGNC.** CC0. `vocab/hgnc_genes.jsonl` is a reduced copy of the complete set dated 10 November 2026.
- **OncoTree.** CC BY 4.0, stable version released 3 October 2025. Kundra et al., JCO Clinical Cancer Informatics, 2021.
- **NCI Thesaurus.** CC BY 4.0, version 26.10d. The synonym file is a selection made by DxP and is not NCI Thesaurus itself.

This is a developer summary of each source's terms, not legal advice. The full notes are in `.claude/skills/dxp-open-data-sources/references/terms.md`.
