"""The print-only command (Story 1.5): A05's item building and rendering, offline."""

from dxp.llm.cli import item_from_study, render
from dxp.llm.types import Extraction, Finding, FindingValue, NameMention, ValueCheck
from dxp.sources import load as source_load

STUDY = {
    "protocolSection": {
        "identificationModule": {"nctId": "NCT00000001", "briefTitle": "A test title"},
        "statusModule": {"overallStatus": "RECRUITING", "lastUpdatePostDateStruct": {"date": "2026-11-12"}},
        "conditionsModule": {"conditions": ["Lung Cancer"]},
        "armsInterventionsModule": {
            "interventions": [{"type": "DIAGNOSTIC_TEST", "name": "Assay X", "otherNames": ["Brand Y"]}]
        },
    },
    "hasResults": False,
}


def test_item_from_study_is_a05s_source_version():
    item = item_from_study(STUDY)
    assert item["source_ref"] == "clinicaltrials.gov:NCT00000001"
    assert item["version_id"] == item["_id"] == source_load.version_id_for(
        item["source_ref"], "2026-11-12", item["content_hash"]
    )
    assert item["interventions"] == [{"type": "DIAGNOSTIC_TEST", "name": "Assay X", "otherNames": ["Brand Y"]}]
    assert "Assay X (DIAGNOSTIC_TEST); other names: Brand Y" in item["raw_text"]
    assert item["has_results"] is False and item["overall_status"] == "RECRUITING"


def test_render_prints_quotes_and_checks():
    f = Finding(
        id="f_1", source_ref="s", version_id="sv_1", target="scope_collection", summary="Sum.", prompt_version="p",
        values=[FindingValue(field="sample_types", raw="blood", value="blood", label="blood", quote="Blood",
                             check=ValueCheck(quote_found=True, supported=True, confidence=0.9))],
    )
    r = Extraction(source_ref="s", version_id="sv_1", status="extracted", findings=[f], prompt_version="p",
                   mentions=[NameMention(name="Brand Y", field="interventions[0].otherNames[0]")],
                   unresolved_names=["Brand Y"])
    text = render(r)
    assert "quote: 'Blood'" in text and "quote_found=True supported=True" in text and "passed=True" in text
    assert "unresolved names" in text
