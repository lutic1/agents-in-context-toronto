# Shared demo story for every mock

Every mock uses these dates and states. Where a mock disagrees, this file wins.

## Timeline (all 2026)

| Date | What happened |
|---|---|
| 3 Nov | FDA companion diagnostics list data date ("data as of 3 Nov 2026") |
| 8 Nov | Baseline load; FDA-seeded and Baseline values filed as Unreviewed |
| 9 Nov | Sam accepted the FDA-seeded values (they now show as accepted, by Sam, 9 Nov) |
| 10 Nov | Sam rejected "Disease monitoring" on FoundationOne Liquid CDx, with a reason |
| 11 Nov | Rowan added "Advanced or metastatic" to FoundationOne Liquid CDx's Tumour stage or line, Manually sourced, with a note |
| 12 Nov | Rowan's last visit. Held-back data is "data as of 12 Nov 2026" |
| 13 Nov | The live run. All five changes, all five Alerts, and Sam's rejection and rule happen on this day |

Home and Graph say "5 changes since 12 November". The welcome-back panel says "since yesterday" or "since 12 November", never "six weeks".

## Counts after the live run

- Alerts: 5 (one first-seen Alert for the MRD approach, four update Alerts). Home's panel shows the latest 2 with "See all 5 Alerts".
- Review: 7 pending.
- On the Jobs page (mid-run): Review 4, Alerts 1.

## People

- Rowan (RO), Director of Diagnostics: Home, Graph, Alerts, Find, Categories.
- Sam (SA), curator and Reviewer: Review, Rules, Terms, Jobs, Diagnostics, Record.
- Never use a gendered pronoun for either; use names.

## Find

The last Intended use is "Plasma EGFR and KRAS genotyping in advanced NSCLC". DxP parsed four chips: Sample type plasma, Biomarkers EGFR or KRAS, Tumour type NSCLC, Tumour stage or line advanced or metastatic. Rowan removed the last chip; the table re-ran without a model call to 6 Diagnostics (was 1), with Undo.
