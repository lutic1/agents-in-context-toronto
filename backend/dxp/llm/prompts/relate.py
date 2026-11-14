"""Relationship prompt (strong model, AD-26): one label and one quote from each side."""

PROMPT_VERSION = "a19-relate-2026-11-14.1"

SYSTEM = """You compare two clinical-trial records for a diagnostics research team.
The first is new evidence; the second is evidence the team already holds. Say how
the new evidence relates to the existing evidence with exactly one label:

- supports: the new record backs the same point the existing record makes.
- contradicts: the new record conflicts with a point the existing record makes.
- extends: the new record takes the same approach into a new setting, population,
  stage or sample type.
- new_question: the new record raises a question the existing record does not address.

Rules:
- Give one quote from the new record and one quote from the existing record. Each
  quote is copied word for word from that record, is one continuous passage, and is
  at most 300 characters. Do not shorten with an ellipsis, do not paraphrase, and do
  not join separate passages.
- The rationale is one sentence about study design, setting or population.
- A product or assay name that appears in a record is only a name in that record.
  Never write that a trial uses, used, studies, studied or tested a named product,
  and never write that any assay showed, detected or achieved anything.
- Do not state results or performance unless the record itself posts results.
- If you cannot find a fitting quote on both sides, still answer with your best
  label and the closest passages; the quotes are checked afterwards."""

USER = """New evidence ({new_ref}):
<new_record>
{new_text}
</new_record>

Existing evidence ({related_ref}):
<existing_record>
{related_text}
</existing_record>"""

SCHEMA = {
    "title": "relationship",
    "description": "How the new evidence relates to the existing evidence, with one quote from each side.",
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["supports", "contradicts", "extends", "new_question"]},
        "rationale": {"type": "string", "description": "One sentence."},
        "new_quote": {"type": "string", "description": "Word for word from the new record, at most 300 characters."},
        "related_quote": {"type": "string", "description": "Word for word from the existing record, at most 300 characters."},
    },
    "required": ["label", "rationale", "new_quote", "related_quote"],
    "additionalProperties": False,
}
