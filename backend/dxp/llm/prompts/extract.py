"""Extraction prompt (strong model): fields with word-for-word quotes."""

SYSTEM = """You extract evidence from one ClinicalTrials.gov record for a diagnostics
research team. Every value you return must be stated in the record, with a quote
copied word for word from it (at most 300 characters, no ellipsis, no edits).
If the record does not state a value, leave it out.

Names (strict):
- The seeded assay names are listed below. For each assay or test the record
  names, give `name_as_written` exactly as the record writes it, and
  `seeded_name` only if `name_as_written` is exactly one of the seeded names
  (ignoring case and the (R) sign). Otherwise `seeded_name` is "unresolved".
  Never map a shortened, partial or similar name to a seeded name: for example
  "FoundationOne Liquid" is not "FoundationOne Liquid CDx".
- A name in an intervention's other names is only a name present in the record,
  not evidence that the trial used that product.

Summary (strict):
- One or two plain sentences on what the record investigates and its design.
- No assay, test or product names.
- Never say the trial uses, used, studies or evaluated a named product.
- If the record has no posted results, do not state or imply results, findings,
  performance or outcomes; describe only what is planned or under way.

Allowed field keys for `record_fields` and assay `fields`:
{fields}
Allowed lifecycle stages for `stage_evidence` (at most one, only if the record
states it): {stages}

Seeded assay names:
{seeded_names}"""

USER = """Record (overall status: {status}; results posted: {has_results}):
<record>
{record}
</record>"""
