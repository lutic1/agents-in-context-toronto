"""A13: parsing the FDA companion diagnostics list and storing the lung rows (D45, V40)."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

import pytest

from dxp.identity import normalise_name
from dxp.sources import fda_cdx

from .conftest import SCOPE_ASSAYS

FETCHED = datetime(2026, 11, 14, 13, 0, tzinfo=UTC)


def test_parses_only_the_six_column_table(fda_page: str) -> None:
    rows = fda_cdx.parse_rows(fda_page)
    assert len(rows) == 11  # every data row of the main table; the group-labeling table is not read
    assert all(len(r.cells) == 6 for r in rows)
    assert "Group labeling text" not in {c for r in rows for c in r.cells}


def test_keeps_lung_rows_with_a_number_once(fda_page: str) -> None:
    rows = fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page))
    names = [r.trade_name for r in rows]
    assert "OncoMate MSI Dx Analysis System" not in names  # not lung
    assert "Example Lung Test" not in names  # no PMA or 510(k) number
    assert names.count("FoundationOne CDx") == 2  # the exact duplicate row is kept once
    assert len(rows) == 8


def test_trade_names_are_the_exact_strings_of_the_list(fda_page: str) -> None:
    rows = fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page))
    names = {r.trade_name for r in rows}
    for assay in SCOPE_ASSAYS:  # the four D45 strings, exactly, "®" included
        assert assay in names
    assert "FoundationOne CDx" in names and "FoundationOne Liquid CDx" in names
    by_name = {r.trade_name: r for r in rows}
    assert by_name["Guardant360® Liquid CDx"].manufacturer == "Guardant Health, Inc."


@pytest.mark.parametrize(
    ("cell", "name", "maker"),
    [
        ("FoundationOne CDx (Foundation Medicine, Inc.)", "FoundationOne CDx", "Foundation Medicine, Inc."),
        ("Ventana ALK (D5F3) CDx Assay (Ventana Medical Systems, Inc.)", "Ventana ALK (D5F3) CDx Assay",
         "Ventana Medical Systems, Inc."),
        ("ONCO/Reveal Dx Lung & Colon Cancer Assay (O/RDx-LCCA) (Pillar Biosciences, Inc.)",
         "ONCO/Reveal Dx Lung & Colon Cancer Assay (O/RDx-LCCA)", "Pillar Biosciences, Inc."),
        ("VENTANA MET (SP44) RxDx Assay (Ventana Medical Systems, Inc. (Roche Tissue Diagnostics)",
         "VENTANA MET (SP44) RxDx Assay", "Ventana Medical Systems, Inc. (Roche Tissue Diagnostics)"),
        ("No Maker Assay", "No Maker Assay", None),
    ],
)
def test_split_trade_name(cell: str, name: str, maker: str | None) -> None:
    assert fda_cdx.split_trade_name(cell) == (name, maker)


def test_row_id_is_number_and_sha1_of_the_normalised_row(fda_page: str) -> None:
    row = fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page))[0]
    expected = hashlib.sha1(normalise_name(row.raw_text).encode()).hexdigest()[:8]
    assert fda_cdx.row_id(row) == f"P170019:{expected}"
    assert fda_cdx.source_ref(row) == f"fda_cdx_list:P170019:{expected}"
    supplement = next(r for r in fda_cdx.parse_rows(fda_page) if r.trade_name == "FoundationOne Liquid CDx")
    assert re.fullmatch(r"P190032/S001:[0-9a-f]{8}", fda_cdx.row_id(supplement))


def test_one_number_many_rows_gives_distinct_ids(fda_page: str) -> None:
    rows = [r for r in fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page)) if r.number == "P170019"]
    assert len(rows) == 2 and len({fda_cdx.row_id(r) for r in rows}) == 2


def test_dates(fda_page: str) -> None:
    assert fda_cdx.parse_list_date(fda_page) == "2026-11-03"
    rows = {r.trade_name: r for r in fda_cdx.parse_rows(fda_page)}
    assert rows["Agilent Resolution ctDx FIRST assay"].approval_date == "2022-12-12"
    assert rows["cobas EGFR Mutation Test v2"].approval_date is None  # "08/22/0218" as written
    assert rows["cobas EGFR Mutation Test v2"].number == "P120019/S019"


def test_parse_error_when_the_table_is_missing() -> None:
    with pytest.raises(fda_cdx.ParseError):
        fda_cdx.parse_rows("<html><table><tr><td>a</td></tr></table></html>")


def test_source_documents(fda_page: str) -> None:
    row = next(r for r in fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page)) if r.trade_name == "FoundationOne Liquid CDx")
    item, version = fda_cdx.source_documents(row, fetched_at=FETCHED, list_date="2026-11-03")
    assert item["_id"] == fda_cdx.source_ref(row) and item["source"] == "fda_cdx_list"
    assert item["raw_text"] == row.raw_text and "FoundationOne Liquid CDx (Foundation Medicine, Inc.)" in item["raw_text"]
    assert item["source_date"] == "2026-11-14"  # the fetch date
    assert item["list_date"] == "2026-11-03"
    assert item["current_version_id"] == version["_id"] and re.fullmatch(r"sv_[0-9a-f]{16}", version["_id"])
    assert re.fullmatch(r"[0-9a-f]{16}", version["content_hash"])
    assert version["source_ref"] == item["_id"] and version["raw_text"] == item["raw_text"]
    quote = fda_cdx.quote_for(row)
    assert quote in item["raw_text"] and len(quote) <= 300


def test_quote_is_cut_at_a_cell_boundary() -> None:
    row = fda_cdx.row_from_cells(
        ["A Test (Maker)", "Non-Small Cell Lung Cancer (NSCLC) - Tissue", "X (y) NDA 1", "EGFR", "d" * 400, "P123456 (01/02/2020)"]
    )
    assert row is not None
    quote = fda_cdx.quote_for(row)
    assert quote == "A Test (Maker) | Non-Small Cell Lung Cancer (NSCLC) - Tissue | X (y) NDA 1 | EGFR"
    assert quote in row.raw_text


async def test_store_rows_is_insert_if_absent(fda_page: str, fake_db) -> None:
    rows = fda_cdx.lung_rows(fda_cdx.parse_rows(fda_page))
    first = await fda_cdx.store_rows(fake_db, rows, fetched_at=FETCHED, list_date="2026-11-03")
    assert first == {"rows": 8, "inserted": 8, "existing": 0}
    before = fake_db.snapshot()
    later = datetime(2026, 11, 15, tzinfo=UTC)
    second = await fda_cdx.store_rows(fake_db, rows, fetched_at=later, list_date="2026-11-03")
    assert second == {"rows": 8, "inserted": 0, "existing": 8}
    assert fake_db.snapshot() == before  # nothing created, nothing changed
    assert len(fake_db["source_versions"].docs) == 8


async def test_fetch_page_uses_the_fda_url_and_fails_loudly() -> None:
    class Response:
        def __init__(self, status: int, text: str) -> None:
            self.status_code, self.text = status, text

    class Client:
        def __init__(self, response: Response) -> None:
            self.response, self.urls = response, []

        async def get(self, url: str) -> Response:
            self.urls.append(url)
            return self.response

    ok = Client(Response(200, "<html/>"))
    assert await fda_cdx.fetch_page(client=ok) == "<html/>"
    assert ok.urls == [fda_cdx.FDA_URL]
    with pytest.raises(fda_cdx.ParseError):
        await fda_cdx.fetch_page(client=Client(Response(503, "")))


def test_refuses_files_under_data(tmp_path) -> None:
    with pytest.raises(SystemExit):
        fda_cdx.refuse_data_dir(fda_cdx.REPO / "data" / "fda" / "page.html")
    fda_cdx.refuse_data_dir(tmp_path / "page.html")  # a copy saved elsewhere is fine


async def test_cli_dry_run_writes_nothing(fda_page: str, tmp_path, capsys) -> None:
    page = tmp_path / "fda.html"
    page.write_text(fda_page, encoding="utf-8")
    assert await fda_cdx.main(["--html", str(page), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "8 lung rows" in out and "Guardant360® Liquid CDx" in out
