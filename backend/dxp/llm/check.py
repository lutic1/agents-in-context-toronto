"""`llm.check(finding, source_text)`: the AD-6 evidence check on a Finding.

For every value (and the stage evidence) of a Finding:

- `quote_found` comes only from `evidence.quote_in_source()` against
  `source_text`, the `raw_text` of the source version the Finding pins (V40);
- `supported` comes from one check call on the strong model, asked only about
  values whose quote was found;
- a value passes only when both are true. A failing value stays on the Finding
  with its check and goes no further; the gate's evidence check reads this
  `check` and never re-judges it.

Never raises: a model failure leaves every value unsupported and adds a
failure record to the Finding.
"""

from __future__ import annotations

import json

from dxp.evidence import quote_in_source
from dxp.llm import client
from dxp.llm.prompts import check as prompt
from dxp.llm.types import CheckOut, Finding, LLMFailure, ValueCheck


def _item_line(index: int, field: str, value: str, quote: str) -> str:
    return json.dumps({"index": index, "field": field, "value": value, "quote": quote}, ensure_ascii=False)


async def check_finding(finding: Finding, source_text: str, *, lane: str = "ingest") -> Finding:
    checked = finding.model_copy(deep=True)

    # (index -> check object to fill) for every quote that was found.
    pending: list[tuple[int, ValueCheck]] = []
    lines: list[str] = []

    for value in checked.values:
        c = value.check
        c.quote_found = quote_in_source(value.quote, source_text)
        c.supported = False
        c.checked = False
        if not c.quote_found:
            c.detail = "quote_not_found"
            continue
        if value.value is None:
            c.detail = "not_canonical"
            continue
        index = len(pending)
        pending.append((index, c))
        lines.append(_item_line(index, value.field, value.raw, value.quote))

    stage = checked.stage_evidence
    if stage is not None:
        c = stage.check
        c.quote_found = quote_in_source(stage.quote, source_text)
        c.supported = False
        c.checked = False
        if c.quote_found:
            index = len(pending)
            pending.append((index, c))
            lines.append(_item_line(index, "lifecycle_stage", stage.raw, stage.quote))
        else:
            c.detail = "quote_not_found"

    if not pending:
        return checked

    result = await client.call_structured(
        "strong",
        CheckOut,
        [
            ("system", prompt.SYSTEM),
            ("human", prompt.USER.format(record=source_text, items="\n".join(lines))),
        ],
        lane=lane,
        step="check",
    )

    if isinstance(result, LLMFailure):
        checked.failures.append(result)
        for _, c in pending:
            c.detail = "check_failed"
        return checked

    verdicts = {v.index: v.supported for v in result.verdicts}
    for index, c in pending:
        if index in verdicts:
            c.supported = bool(verdicts[index])
            c.checked = True
            c.detail = None if c.supported else "not_supported"
        else:
            c.detail = "no_verdict"
    return checked
