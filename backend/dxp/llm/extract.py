"""`llm.extract(item)`: one Source item version to checked Findings (Story 1.5).

1. Name mentions are read from the record's structured interventions, verbatim,
   and resolved only through `identity.resolve_exact()` (V34, V37).
2. Triage on the fast model: does the record concern a lung cancer diagnostic?
   An item rejected here is `not_relevant`: done, not failed, no Finding.
3. Extraction on the strong model: per field a raw value, a quote (at most 300
   characters) and a confidence, plus at most one `stage_evidence`; the assays
   the text names, each as written and either one of the seeded names exactly
   or `unresolved`. Any other answer is a failure record.
4. Findings: one for the record itself (`diagnostic_id` None; its changes go to
   the scope's evidence collection, V35, V43) and one per seeded Diagnostic the
   record names. A Diagnostic Finding records the mention and never says the
   trial uses or studies the product (V37).
5. `check()` on every Finding (AD-6), unless `run_check=False`.

Never raises (except `asyncio.CancelledError`); failure records carry no
source text.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from collections.abc import Sequence
from typing import Any

from dxp.evidence import quote_in_source
from dxp.llm import _deps, client
from dxp.llm.check import check
from dxp.llm.mentions import _get, read_mentions, resolve_mention
from dxp.llm.prompts import PROMPT_VERSION
from dxp.llm.prompts import extract as extract_prompt
from dxp.llm.prompts import triage as triage_prompt
from dxp.llm.types import (
    EXTRACTABLE_FIELDS,
    UNRESOLVED,
    ExtractOut,
    Extraction,
    FieldOut,
    Finding,
    FindingValue,
    LLMFailure,
    NameMention,
    StageEvidence,
    TriageOut,
    ValueCheck,
)

log = logging.getLogger("dxp.llm")

_NCT = re.compile(r"NCT\d{8}")

# Words that state an outcome. A record without posted results never gets a
# summary that uses them (V7, V33); the gate's claim checks still run later.
_OUTCOME = re.compile(
    r"\b(showed|shown|shows|demonstrat\w*|found that|achiev\w*|resulted in|"
    r"(was|were) associated|improv(ed|es|ement)|sensitivity|specificity|accuracy|"
    r"concordance|response rate|outcomes? (was|were)|detected\b.*\b\d+(\.\d+)? ?%|proved|confirmed)\b",
    re.IGNORECASE,
)
_GENERIC_TOKENS = frozenset(
    {"liquid", "tissue", "assay", "assays", "test", "tests", "tumor", "tumour", "ctdna", "ngs", "cdx", "plasma", "blood", "panel"}
)


# --------------------------------------------------------------------------
# Item accessors
# --------------------------------------------------------------------------


def _as_mapping(item: Any) -> Any:
    dump = getattr(item, "model_dump", None)
    if callable(dump):
        try:
            return dump(by_alias=False)
        except Exception:  # noqa: BLE001
            return item
    return item


def _source_ref(item: Any) -> str | None:
    ref = _get(item, "source_ref")
    if isinstance(ref, str) and ref:
        return ref
    _id = _get(item, "_id")
    if isinstance(_id, str) and ":" in _id and not _id.startswith("sv_"):
        return _id
    return None


def _version_id(item: Any) -> str | None:
    for key in ("version_id", "current_version_id"):
        value = _get(item, key)
        if isinstance(value, str) and value:
            return value
    for key in ("_id", "id"):
        value = _get(item, key)
        if isinstance(value, str) and value.startswith("sv_"):
            return value
    return None


def _nct_id(item: Any, source_ref: str | None) -> str | None:
    value = _get(item, "nct_id")
    if isinstance(value, str) and value:
        return value
    if source_ref:
        m = _NCT.search(source_ref)
        if m:
            return m.group(0)
    return None


def _status_words(status: str | None) -> str:
    return (status or "unknown").replace("_", " ").lower()


def _has_results(item: Any) -> bool | None:
    value = _get(item, "has_results")
    return value if isinstance(value, bool) else None


# --------------------------------------------------------------------------
# Summary guard (V33, V37)
# --------------------------------------------------------------------------


def _brand_tokens(names: Sequence[str]) -> set[str]:
    tokens: set[str] = set()
    for name in names:
        for tok in re.findall(r"[A-Za-z0-9]+", name):
            low = tok.lower()
            if low in _GENERIC_TOKENS:
                continue
            if len(tok) >= 8 or any(ch.isdigit() for ch in tok) or (tok[1:] != tok[1:].lower() and len(tok) >= 4):
                tokens.add(low)
    return tokens


def summary_is_safe(summary: str, *, has_results: bool | None, names: Sequence[str]) -> bool:
    """False if the summary names a product the record mentions, or states an
    outcome for a record without posted results."""
    if not summary or not summary.strip():
        return False
    text = summary.lower()
    for name in names:
        if name and name.lower() in text:
            return False
    words = set(re.findall(r"[a-z0-9]+", text))
    if words & _brand_tokens(names):
        return False
    if has_results is not True and _OUTCOME.search(summary):
        return False
    return True


def _status_sentence(status: str | None, has_results: bool | None) -> str:
    results = "results posted" if has_results else "no results posted"
    return f"Status: {_status_words(status)}; {results}."


def _record_summary(model_summary: str | None, item: Any, *, names: Sequence[str]) -> str:
    status = _get(item, "overall_status")
    has_results = _has_results(item)
    summary = (model_summary or "").strip()
    if not summary_is_safe(summary, has_results=has_results, names=names):
        title = _get(item, "title", "brief_title", "official_title")
        summary = f"{title.strip().rstrip('.')}." if isinstance(title, str) and title.strip() else "Clinical trial record."
    return f"{summary} {_status_sentence(status, has_results)}"


def _mention_summary(mentions: Sequence[NameMention], nct_id: str | None) -> str:
    record = f"The record {nct_id}" if nct_id else "The record"
    parts = []
    for m in mentions:
        if m.intervention_name and m.field.startswith("interventions[") and ".otherNames[" in m.field:
            parts.append(f'"{m.name}" as an other name of the intervention "{m.intervention_name}"')
        else:
            parts.append(f'"{m.name}"')
    return f"{record} names {'; '.join(parts)}. It is a name present in the record only."


# --------------------------------------------------------------------------
# Building values
# --------------------------------------------------------------------------


def _loose(name: str) -> str:
    text = unicodedata.normalize("NFKC", name).lower()
    text = re.sub(r"[®™©]", "", text)
    return re.sub(r"[^0-9a-z]+", " ", text).strip()


def _clamp(c: Any) -> float:
    try:
        f = float(c)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, f))


def _values(fields: Sequence[FieldOut], failures: list[LLMFailure]) -> list[FindingValue]:
    out: list[FindingValue] = []
    seen: set[tuple[str, str]] = set()
    for fo in fields:
        if fo.field not in EXTRACTABLE_FIELDS:
            failures.append(LLMFailure(code="field_not_allowed", step="extract", field=fo.field[:64]))
            continue
        raw = (fo.raw_value or "").strip()
        if not raw:
            continue
        try:
            value = _deps.canonical(fo.field, raw)
        except Exception as exc:  # noqa: BLE001
            failures.append(
                LLMFailure(code="canonical_error", step="extract", field=fo.field, error_type=type(exc).__name__)
            )
            value = None
        key = (fo.field, value or raw)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            FindingValue(
                field=fo.field,
                raw=raw,
                value=value,
                label=raw,
                quote=fo.quote or "",
                check=ValueCheck(confidence=_clamp(fo.confidence)),
            )
        )
    return out


def _stage(out: ExtractOut, failures: list[LLMFailure]) -> StageEvidence | None:
    se = out.stage_evidence
    if se is None or not (se.stage or "").strip():
        return None
    try:
        stage = _deps.canonical("lifecycle_stage", se.stage.strip())
    except Exception as exc:  # noqa: BLE001
        failures.append(
            LLMFailure(code="canonical_error", step="extract", field="lifecycle_stage", error_type=type(exc).__name__)
        )
        return None
    if not stage:
        failures.append(LLMFailure(code="stage_not_allowed", step="extract", field="lifecycle_stage"))
        return None
    return StageEvidence(stage=stage, raw=se.stage.strip(), quote=se.quote or "", check=ValueCheck(confidence=_clamp(se.confidence)))


# --------------------------------------------------------------------------
# extract()
# --------------------------------------------------------------------------


async def extract(
    item: Any,
    seeded_names: Sequence[str] | None = None,
    *,
    lane: str = "ingest",
    run_check: bool = True,
) -> Extraction:
    """Extract checked Findings from one Source item version. Never raises.

    `item` is a `source_versions` document (or a `source_items` document with
    `current_version_id`), a mapping or a Pydantic object, with `source_ref`,
    the pinned `version_id`, `raw_text`, `interventions` (verbatim), and
    `overall_status` / `has_results`. `seeded_names` are the seeded FDA trade
    names the extraction prompt may match exactly (Story 1.2, V34); resolution
    itself is always `identity.resolve_exact()`.
    """
    try:
        return await _extract(_as_mapping(item), seeded_names, lane=lane, run_check=run_check)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - a filter never raises
        failure = LLMFailure(code="unexpected_error", step="extract", error_type=type(exc).__name__)
        log.warning("llm failure %s", failure.line())
        ref = None
        try:
            ref = _source_ref(_as_mapping(item))
        except Exception:  # noqa: BLE001
            pass
        return Extraction(
            source_ref=ref, version_id=None, status="failed", failures=[failure],
            model_ids=dict(client.MODEL_IDS), prompt_version=PROMPT_VERSION,
        )


async def _extract(item: Any, seeded_names: Sequence[str] | None, *, lane: str, run_check: bool) -> Extraction:
    source_ref = _source_ref(item)
    version_id = _version_id(item)
    nct_id = _nct_id(item, source_ref)
    raw_text = _get(item, "raw_text")
    result = Extraction(
        source_ref=source_ref,
        version_id=version_id,
        nct_id=nct_id,
        status="failed",
        model_ids=dict(client.MODEL_IDS),
        prompt_version=PROMPT_VERSION,
    )

    if not source_ref or not version_id or not isinstance(raw_text, str) or not raw_text.strip():
        missing = "source_ref" if not source_ref else "version_id" if not version_id else "raw_text"
        result.failures.append(LLMFailure(code=f"invalid_item_{missing}", step="extract"))
        _log_result(result)
        return result

    mentions, texts, mention_failures = await read_mentions(item)
    result.mentions = mentions
    result.intervention_texts = texts
    result.failures.extend(mention_failures)

    # Triage (fast model).
    triage = await client.call_structured(
        "fast",
        TriageOut,
        [("system", triage_prompt.SYSTEM), ("human", triage_prompt.USER.format(record=raw_text))],
        lane=lane,
        step="triage",
    )
    if isinstance(triage, LLMFailure):
        result.failures.append(triage)
        _finish_unresolved(result)
        _log_result(result)
        return result
    result.triage_reason = triage.reason
    if not triage.concerns_lung_cancer_diagnostic:
        result.status = "not_relevant"
        _finish_unresolved(result)
        _log_result(result)
        return result

    # Extraction (strong model).
    names = list(seeded_names) if seeded_names is not None else None
    status = _get(item, "overall_status")
    has_results = _has_results(item)
    out = await client.call_structured(
        "strong",
        ExtractOut,
        [
            (
                "system",
                extract_prompt.SYSTEM.format(
                    fields=", ".join(EXTRACTABLE_FIELDS),
                    stages=", ".join(_deps.stage_names()),
                    seeded_names="\n".join(f"- {n}" for n in names) if names else "(none given)",
                ),
            ),
            (
                "human",
                extract_prompt.USER.format(
                    status=status or "unknown",
                    has_results="yes" if has_results else "no",
                    record=raw_text,
                ),
            ),
        ],
        lane=lane,
        step="extract",
    )
    if isinstance(out, LLMFailure):
        result.failures.append(out)
        _finish_unresolved(result)
        _log_result(result)
        return result

    failures: list[LLMFailure] = []
    seeded_loose = {_loose(n) for n in names} if names is not None else None

    # Assays the text names: validated, then resolved only by resolve_exact().
    by_dx: dict[str, dict[str, Any]] = {}
    for m in mentions:
        if m.resolution == "exact" and m.resolved_diagnostic_id:
            by_dx.setdefault(m.resolved_diagnostic_id, {"mentions": [], "fields": []})["mentions"].append(m)

    for i, assay in enumerate(out.assays):
        written = (assay.name_as_written or "").strip()
        claimed = (assay.seeded_name or "").strip()
        claimed_unresolved = claimed.lower() == UNRESOLVED
        if not written:
            failures.append(LLMFailure(code="assay_name_empty", step="extract", index=i))
            continue
        if not claimed_unresolved and seeded_loose is not None and _loose(claimed) not in seeded_loose:
            failures.append(LLMFailure(code="seeded_name_not_allowed", step="extract", index=i))
            continue
        if not quote_in_source(written, raw_text):
            failures.append(LLMFailure(code="assay_name_not_in_source", step="extract", index=i))
            continue
        mention = await resolve_mention(written, "text")
        if mention.resolution == "error":
            failures.append(LLMFailure(code="resolve_error", step="extract", index=i))
        if not claimed_unresolved and mention.resolution != "exact":
            # The model mapped a name that is not an exact seeded name (V34).
            failures.append(LLMFailure(code="model_mapped_unmatched_name", step="extract", index=i))
        if not any(_same_mention(mention, m) for m in result.mentions):
            result.mentions.append(mention)
        if mention.resolution == "exact" and mention.resolved_diagnostic_id:
            group = by_dx.setdefault(mention.resolved_diagnostic_id, {"mentions": [], "fields": []})
            if not any(_same_mention(mention, m) for m in group["mentions"]):
                group["mentions"].append(mention)
            group["fields"].extend(assay.fields)

    mention_names = [m.name for m in result.mentions]
    common = {
        "source_ref": source_ref,
        "version_id": version_id,
        "nct_id": nct_id,
        "trial_status": status,
        "has_results": has_results,
        "model": client.MODEL_IDS["strong"],
        "prompt_version": PROMPT_VERSION,
    }

    record_failures: list[LLMFailure] = []
    record_finding = Finding(
        id=_deps.derive("f_", version_id, "-"),
        diagnostic_id=None,
        target="scope_collection",
        summary=_record_summary(out.summary, item, names=mention_names),
        values=_values(out.record_fields, record_failures),
        stage_evidence=_stage(out, record_failures),
        failures=record_failures,
        **common,
    )
    findings = [record_finding]

    for dx_id, group in by_dx.items():
        dx_failures: list[LLMFailure] = []
        findings.append(
            Finding(
                id=_deps.derive("f_", version_id, dx_id),
                diagnostic_id=dx_id,
                target="diagnostic",
                mentions=group["mentions"],
                summary=_mention_summary(group["mentions"], nct_id),
                values=_values(group["fields"], dx_failures),
                failures=dx_failures,
                **common,
            )
        )

    if run_check:
        findings = list(await asyncio.gather(*(check(f, raw_text, lane=lane) for f in findings)))

    result.findings = findings
    result.failures.extend(failures)
    result.status = "extracted"
    _finish_unresolved(result)
    _log_result(result)
    return result


def _same_mention(a: NameMention, b: NameMention) -> bool:
    return a.name == b.name and a.resolved_diagnostic_id == b.resolved_diagnostic_id


def _finish_unresolved(result: Extraction) -> None:
    seen: list[str] = []
    for m in result.mentions:
        if m.resolution == "unresolved" and m.name not in seen:
            seen.append(m.name)
    result.unresolved_names = seen


def _log_result(result: Extraction) -> None:
    codes = ",".join(f.code for f in result.failures) or "-"
    log.info(
        "llm extract source_ref=%s status=%s findings=%d unresolved=%d failures=%s",
        result.source_ref, result.status, len(result.findings), len(result.unresolved_names), codes,
    )
