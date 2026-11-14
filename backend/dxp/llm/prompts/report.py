"""Report drafting prompt (strong model, AD-27): the signal, its claims, one gap, one task."""

PROMPT_VERSION = "a19-report-2026-11-14.1"

SYSTEM = """You draft one research report entry for a diagnostics team from a single
clinical-trial record. The team reviews it before anything is accepted, so write only
what the record itself states.

Fields:
- headline: the trial as a new signal worth investigating, in one sentence built from
  the record's own design fields, in the pattern "This study investigates <what is
  investigated> in <population and stage>, to <aim>." If the record has no posted
  results, add the sentence "No results posted."
- summary: one or two plain sentences on what the trial investigates and how.
- claims: each factual sentence of the summary as its own entry, with a claim_kind and
  one quote copied word for word from the record (one continuous passage, at most 300
  characters) that states it.
  claim_kind is one of: claim_planned (the trial is planned or still running),
  claim_performed_or_results (something was performed or produced a result),
  claim_preclinical (cell-line or animal evidence), claim_design (design, population
  or setting).
- gap: exactly one question the record leaves open, which a search of other trials
  could answer, in the pattern "Have <population and stage> studies that <approach>
  posted results?"
- task: the search that answers exactly that gap. condition is the disease as a
  search term; stage is the disease stage in one word (for example "early");
  testing lists the testing approaches to combine, in the record's general terms.
- intervention_plain: the record's generic intervention in a few plain words, with no
  product or brand name.
- collection_label: a short noun phrase for this study, with no product or brand name.

Rules:
- A product, assay or brand name in the record is only a name present in the record.
  Never write that the trial uses, used, studies, studied or tests a named product.
  Leave product and brand names out of every field.
- Never state or imply a result, performance or outcome unless the record posts
  results. A recruiting or not-yet-recruiting trial is described as planned or ongoing.
- Add no fact, number or date that is not in the record.
- When reviewer guidance is given, follow it. It changes wording and emphasis only;
  it never adds a fact."""

USER = """Record ({source_ref}):
<record>
{record}
</record>

Structured fields of the record:
- overall status: {overall_status}
- results posted: {has_results}
- interventions, verbatim: {interventions}
- names present in the record (do not use them): {names}

Related evidence already held (context only):
{related}
{guidance}"""

GUIDANCE = """
Reviewer guidance to follow:
{memories}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "claim_kind": {
                        "type": "string",
                        "enum": ["claim_planned", "claim_performed_or_results", "claim_preclinical", "claim_design"],
                    },
                    "quote": {"type": "string", "description": "Word for word from the record, at most 300 characters."},
                },
                "required": ["text", "claim_kind", "quote"],
                "additionalProperties": False,
            },
        },
        "gap": {"type": "string", "description": "Exactly one question."},
        "task": {
            "type": "object",
            "properties": {
                "condition": {"type": "string"},
                "stage": {"type": "string"},
                "testing": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["condition", "stage", "testing"],
            "additionalProperties": False,
        },
        "intervention_plain": {"type": "string"},
        "collection_label": {"type": "string"},
    },
    "required": ["headline", "summary", "claims", "gap", "task", "intervention_plain", "collection_label"],
    "additionalProperties": False,
}
