"""The structured-output schemas must be accepted by the client A08 uses (langchain-anthropic,
JSON-schema method). The conversion runs locally: no request is made."""

import importlib

import pytest

relate_prompt = importlib.import_module("dxp.llm.prompts.relate")
report_prompt = importlib.import_module("dxp.llm.prompts.report")

SCHEMAS = [("relationship", relate_prompt.SCHEMA), ("report_draft", report_prompt.SCHEMA),
           ("report_revision", report_prompt.REVISE_SCHEMA)]


@pytest.mark.parametrize(("title", "schema"), SCHEMAS)
def test_schema_is_accepted_by_the_structured_output_conversion(title, schema):
    from langchain_anthropic import ChatAnthropic

    chat = ChatAnthropic(model="claude-sonnet-5-5", api_key="test-anthropic-key", max_retries=0)
    assert schema["title"] == title and schema["description"]
    chat.with_structured_output(schema, method="json_schema", include_raw=True)


def test_a_schema_without_a_title_is_what_the_client_refuses():
    from langchain_anthropic import ChatAnthropic

    chat = ChatAnthropic(model="claude-sonnet-5-5", api_key="test-anthropic-key", max_retries=0)
    untitled = {k: v for k, v in relate_prompt.SCHEMA.items() if k != "title"}
    with pytest.raises(ValueError):
        chat.with_structured_output(untitled, method="json_schema", include_raw=True)


def test_claim_kinds_are_the_gates_vocabulary():
    kinds = report_prompt.SCHEMA["properties"]["claims"]["items"]["properties"]["claim_kind"]["enum"]
    assert kinds == ["claim_performed_or_results", "claim_planned", "claim_preclinical"]
    assert "claim_kind" not in report_prompt.SCHEMA["properties"]["claims"]["items"]["required"]
    for text in (report_prompt.SYSTEM, report_prompt.REVISE_SYSTEM, relate_prompt.SYSTEM):
        assert "outcome_claim_without_results" not in text and "claim_design" not in text


def test_prompts_fill_without_missing_fields():
    fields = dict(source_ref="r", record="x", overall_status="RECRUITING", has_results=False,
                  interventions="[]", names="[]", related="- none")
    assert "<record>" in report_prompt.USER.format(**fields)
    revised = report_prompt.REVISE_USER.format(draft="{}", memories="- mem_1: text", **fields)
    assert "Reviewer memories:" in revised and "mem_1" in revised
    assert relate_prompt.USER.format(new_ref="a", new_text="b", related_ref="c", related_text="d")
