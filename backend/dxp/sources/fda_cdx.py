"""python -m dxp.sources.fda_cdx: the FDA companion diagnostics list, lung rows (A13, Story 1.2).

Fetches the FDA "List of Cleared or Approved Companion Diagnostic Devices" during the event
(D1), parses its main table, keeps the lung rows and stores each one as a Source item
``fda_cdx_list:<row id>`` (AD-3, D45), with one immutable ``source_versions`` document (V40).

- Row ID: ``<PMA or 510(k) number>:<first 8 hex of sha1 of the normalised row>``, because one
  number covers many drug rows (D45). The number is kept as the list writes it
  (``P170019/S067``).
- ``raw_text`` is the row (its six cells joined with `` | ``); ``source_date`` is the fetch
  date; ``list_date`` is the page's "Content current as of" date, the list's data date.
- Writes are insert-if-absent, so a second run creates and changes nothing.
- Nothing under ``data/`` is read (D1, OD4). ``--html`` parses a copy of the page saved by hand
  during the event, the fallback if the FDA site cannot be fetched.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from dxp.identity import derive, normalise_name

__all__ = [
    "FDA_URL",
    "SOURCE",
    "FdaRow",
    "ParseError",
    "fetch_page",
    "lung_rows",
    "parse_list_date",
    "parse_rows",
    "quote_for",
    "row_id",
    "source_documents",
    "source_ref",
    "split_trade_name",
    "store_rows",
    "version_id",
]

SOURCE = "fda_cdx_list"
FDA_URL = (
    "https://www.fda.gov/medical-devices/in-vitro-diagnostics/"
    "list-cleared-or-approved-companion-diagnostic-devices-in-vitro-and-imaging-tools"
)
# A plain, generic client name: no personal or project details go to an outside service.
USER_AGENT = "Mozilla/5.0 (compatible; dxp-seed/0.1)"

# The six columns of the main table, in order. The page's second table (group labeling) has
# four columns and is not read: its devices also have rows in the main table.
COLUMNS = (
    "diagnostic",  # Diagnostic Name (Manufacturer)
    "indication",  # Indication - Sample Type
    "drug",  # Drug Trade Name (Generic) NDA / BLA
    "biomarker",  # Biomarker(s)
    "biomarker_details",  # Biomarker(s) (Details)
    "approval",  # PMA / 510(k) / 513(f)(2) / HDE (Approval / Clearance / Grant Date)
)
_HEADER_FIRST = "diagnostic name"

_SPACE = re.compile(r"\s+")
_NUMBER = re.compile(r"\b((?:P|K|DEN|H|BK)\d{6}(?:/S\d{3})?)\b")
_DATE = re.compile(r"\((\d{2})/(\d{2})/(\d{4})\)")
_LUNG = re.compile(r"\blung\b|\bnsclc\b", re.IGNORECASE)
_CURRENT_AS_OF = re.compile(r"Content current as of:\s*(?:<[^>]*>\s*)*(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)

MAX_QUOTE = 300  # AD-6: a quote is at most 300 characters
REPO = Path(__file__).resolve().parents[3]


class ParseError(ValueError):
    """The page did not contain the companion diagnostics table in the expected shape."""


def _collapse(text: str) -> str:
    return _SPACE.sub(" ", text.replace("\xa0", " ")).strip()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


class _TableParser(HTMLParser):
    """Collects every table as a list of rows of cell texts (``<br>`` becomes a space)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._stack: list[list[list[str]]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._stack.append([])
        elif tag == "tr" and self._stack:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(_collapse("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._stack:
            if self._row:
                self._stack[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._stack:
            self.tables.append(self._stack.pop())

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def split_trade_name(diagnostic: str) -> tuple[str, str | None]:
    """Split "Trade Name (Manufacturer)" into the exact trade-name string and the manufacturer.

    The manufacturer is the last parenthesis opened at depth 0, so a parenthesis inside the
    name stays ("Ventana ALK (D5F3) CDx Assay (Ventana Medical Systems, Inc.)"), and an
    unbalanced manufacturer such as "(Ventana Medical Systems, Inc. (Roche Tissue Diagnostics)"
    is still cut at its own opening parenthesis.
    """
    text = _collapse(diagnostic)
    if not text.endswith(")"):
        return text, None
    depth = 0
    last_open = -1
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                last_open = i
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1
    if last_open <= 0:
        return text, None
    name = text[:last_open].strip()
    maker = text[last_open + 1 :].strip()
    if maker.endswith(")") and maker.count(")") > maker.count("("):
        maker = maker[:-1].strip()
    return (name, maker or None) if name else (text, None)


def split_indication(indication: str) -> tuple[str, str | None]:
    """"Non-Small Cell Lung Cancer (NSCLC) - Tissue or Plasma" -> (disease, sample text)."""
    for sep in (" - ", " – ", " — "):
        if sep in indication:
            disease, _, sample = indication.rpartition(sep)
            return disease.strip(), sample.strip() or None
    return indication.strip(), None


def _iso(match: re.Match[str] | None) -> str | None:
    if match is None:
        return None
    month, day, year = (int(g) for g in match.groups())
    if year < 1976:  # the list has typos such as 08/22/0218; keep the text, no date
        return None
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


@dataclass(frozen=True)
class FdaRow:
    """One row of the FDA list's main table, exactly as written."""

    cells: tuple[str, ...]
    trade_name: str
    manufacturer: str | None
    disease: str
    sample_text: str | None
    number: str | None
    approval_date: str | None

    @property
    def diagnostic(self) -> str:
        return self.cells[0]

    @property
    def indication(self) -> str:
        return self.cells[1]

    @property
    def drug(self) -> str:
        return self.cells[2]

    @property
    def biomarker(self) -> str:
        return self.cells[3]

    @property
    def biomarker_details(self) -> str:
        return self.cells[4]

    @property
    def approval(self) -> str:
        return self.cells[5]

    @property
    def raw_text(self) -> str:
        """The row: its six cells joined with " | " (what Evidence quotes)."""
        return " | ".join(self.cells)

    @property
    def is_lung(self) -> bool:
        return bool(_LUNG.search(self.indication))


def row_from_cells(cells: list[str] | tuple[str, ...]) -> FdaRow | None:
    """One row from its six cell texts; None for a header or a row of another shape."""
    if len(cells) != len(COLUMNS):
        return None
    cells_t = tuple(_collapse(c) for c in cells)
    if not cells_t[0] or cells_t[0].lower().startswith(_HEADER_FIRST):
        return None
    trade_name, manufacturer = split_trade_name(cells_t[0])
    disease, sample = split_indication(cells_t[1])
    number = _NUMBER.search(cells_t[5])
    return FdaRow(
        cells=cells_t,
        trade_name=trade_name,
        manufacturer=manufacturer,
        disease=disease,
        sample_text=sample,
        number=number.group(1) if number else None,
        approval_date=_iso(_DATE.search(cells_t[5])),
    )


def parse_rows(page: str) -> list[FdaRow]:
    """Every data row of the main table (the one whose header starts "Diagnostic Name").

    Raises ``ParseError`` when no such table is found, so a changed page fails loudly instead
    of seeding nothing.
    """
    parser = _TableParser()
    parser.feed(page)
    parser.close()
    for table in parser.tables:
        if not table:
            continue
        header = [c.lower() for c in table[0]]
        if len(header) == len(COLUMNS) and header[0].startswith(_HEADER_FIRST):
            rows = [r for r in (row_from_cells(cells) for cells in table[1:]) if r is not None]
            if not rows:
                raise ParseError("the companion diagnostics table has no data rows")
            return rows
    raise ParseError("no table with the six companion diagnostics columns was found")


def lung_rows(rows: Iterable[FdaRow]) -> list[FdaRow]:
    """The lung rows (the indication names the lung or NSCLC) that carry a PMA or 510(k)
    number, without exact duplicates (same row ID), in page order."""
    seen: set[str] = set()
    kept: list[FdaRow] = []
    for row in rows:
        if not row.is_lung or not row.number:
            continue
        rid = row_id(row)
        if rid in seen:
            continue
        seen.add(rid)
        kept.append(row)
    return kept


def parse_list_date(page: str) -> str | None:
    """The page's "Content current as of" date as YYYY-MM-DD, or None."""
    return _iso(_CURRENT_AS_OF.search(page))


def row_id(row: FdaRow) -> str:
    """``<PMA or 510(k) number>:<first 8 hex of sha1 of the normalised row>`` (D45)."""
    if not row.number:
        raise ValueError(f"row has no PMA or 510(k) number: {row.diagnostic!r}")
    digest = hashlib.sha1(normalise_name(row.raw_text).encode("utf-8")).hexdigest()
    return f"{row.number}:{digest[:8]}"


def source_ref(row: FdaRow) -> str:
    return f"{SOURCE}:{row_id(row)}"


def content_hash(raw_text: str) -> str:
    """First 16 hex of SHA-256 over the normalised raw text (AD-3, V40)."""
    return hashlib.sha256(normalise_name(raw_text).encode("utf-8")).hexdigest()[:16]


def version_id(ref: str, raw_text: str) -> str:
    """The row's one version (V40). An FDA row ID already hashes its content, so the version
    has no date part ("-"): the same row fetched on another day is the same version."""
    return derive("sv_", ref, "-", content_hash(raw_text))


def quote_for(row: FdaRow) -> str:
    """A word-for-word quote of the row, at most 300 characters, cut at a cell boundary."""
    text = row.raw_text
    if len(text) <= MAX_QUOTE:
        return text
    cut = text.rfind(" | ", 0, MAX_QUOTE)
    return text[:cut] if cut > 0 else text[:MAX_QUOTE].rstrip()


def source_documents(
    row: FdaRow, *, fetched_at: datetime, list_date: str | None, source_url: str = FDA_URL
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The ``source_items`` and ``source_versions`` documents for one lung row."""
    ref = source_ref(row)
    raw = row.raw_text
    vid = version_id(ref, raw)
    item = {
        "_id": ref,
        "source": SOURCE,
        "source_item_id": row_id(row),
        "source_url": source_url,
        "source_date": fetched_at.date().isoformat(),
        "list_date": list_date,
        "raw_text": raw,
        "evidence_text": raw,
        "columns": dict(zip(COLUMNS, row.cells, strict=True)),
        "trade_name": row.trade_name,
        "manufacturer": row.manufacturer,
        "number": row.number,
        "approval_date": row.approval_date,
        "window": "fda",
        "current_version_id": vid,
        "fetched_at": fetched_at,
    }
    version = {
        "_id": vid,
        "source_ref": ref,
        "last_update_post_date": None,
        "content_hash": content_hash(raw),
        "raw_text": raw,
        "evidence_text": raw,
        "interventions": [],
        "previous_version_id": None,
        "run_id": None,
        "fetched_at": fetched_at,
    }
    return item, version


def row_from_item(item: dict[str, Any]) -> FdaRow:
    """Rebuild a row from its stored Source item (the seed reads these, not the page)."""
    columns = item.get("columns") or {}
    row = row_from_cells(tuple(columns.get(c, "") for c in COLUMNS))
    if row is None:
        raise ValueError(f"{item.get('_id')}: not a stored FDA row")
    return row


# ---------------------------------------------------------------------------
# Fetching and storing
# ---------------------------------------------------------------------------


async def fetch_page(url: str = FDA_URL, *, client: Any = None, timeout: float = 30.0) -> str:
    """GET the FDA page and return its HTML. Raises ``ParseError`` on a non-200 answer."""
    import httpx

    owns = client is None
    client = client or httpx.AsyncClient(
        timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    )
    try:
        response = await client.get(url)
        if response.status_code != 200:
            raise ParseError(f"the FDA page answered HTTP {response.status_code}")
        return response.text
    finally:
        if owns:
            await client.aclose()


async def insert_if_absent(collection: Any, doc: dict[str, Any]) -> bool:
    """True when inserted; an existing document is never changed (AD-3)."""
    result = await collection.update_one({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True)
    return getattr(result, "upserted_id", None) is not None


async def store_rows(
    db: Any, rows: Iterable[FdaRow], *, fetched_at: datetime | None = None, list_date: str | None = None
) -> dict[str, int]:
    """Insert each lung row's Source item and version, insert-if-absent. Returns counts."""
    fetched_at = fetched_at or datetime.now(UTC)
    counts = {"rows": 0, "inserted": 0, "existing": 0}
    for row in rows:
        item, version = source_documents(row, fetched_at=fetched_at, list_date=list_date)
        counts["rows"] += 1
        await insert_if_absent(db["source_versions"], version)
        if await insert_if_absent(db["source_items"], item):
            counts["inserted"] += 1
        else:
            counts["existing"] += 1
    return counts


def refuse_data_dir(path: Path) -> None:
    """Prepared files under data/ are not loaded unless an organiser clears them (D1, OD4)."""
    resolved = path.resolve()
    if resolved.is_relative_to(REPO / "data"):
        raise SystemExit(f"refusing to read {path}: files under data/ are not loaded (D1, OD4)")


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dxp.sources.fda_cdx", description=__doc__.splitlines()[0])
    parser.add_argument("--html", type=Path, help="parse a copy of the FDA page saved by hand during the event")
    parser.add_argument("--dry-run", action="store_true", help="print the lung rows; write nothing")
    args = parser.parse_args(argv)

    if args.html:
        refuse_data_dir(args.html)
        page = args.html.read_text(encoding="utf-8")
    else:
        page = await fetch_page()
    rows = lung_rows(parse_rows(page))
    list_date = parse_list_date(page)
    names = sorted({r.trade_name for r in rows})
    print(f"FDA list (current as of {list_date or 'unknown'}): {len(rows)} lung rows, {len(names)} trade names")
    for name in names:
        print(f"  {name}")
    if args.dry_run:
        return 0

    from dxp import store

    await store.ensure_indexes()
    try:
        counts = await store_rows(store.get_db(), rows, list_date=list_date)
    finally:
        await store.close()
    print(f"source_items: {counts['inserted']} inserted, {counts['existing']} already present")
    return 0


if __name__ == "__main__":  # pragma: no cover - command line
    sys.exit(asyncio.run(main()))
