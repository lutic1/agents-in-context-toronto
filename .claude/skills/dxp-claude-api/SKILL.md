---
name: dxp-claude-api
description: Claude API from Python for DxP - model IDs and prices, the fast triage pass and the stronger extraction pass with a source quote per field, the citations feature, rate limits and concurrency for the 300 to 500 item batch, prompt caching, token counting and batch error handling. Load when a task touches `anthropic`, `AsyncAnthropic`, `messages.parse`, `output_config`, `cache_control`, `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `ANTHROPIC_API_KEY`, `langchain-anthropic`, `ChatAnthropic`, triage, extraction, quotes, confidence, 429, 529 or rate limits.
---

# Claude API for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Event rule: everything in this skill is reference documentation. Do not copy code from it into the project; write new code during the event.
>
> Saturday scope is `_bmad-output/planning-artifacts/development-plan.md`. Baseline loading, PubMed, memory, Learned rules, Alerts, Tavily scans and the old three-minute recorded video (the 3-minute live demo is in scope) are deferred; ignore those parts of this skill.

## Verified

Checked 2026-11-12 against platform.claude.com/docs, PyPI and the SDK source on GitHub.

- Python SDK `anthropic` 2.8.0 (released 2026-11-10). Python 3.10 or later. Built on `httpx2`, not `httpx`. SDK 2.x sends API version `2026-10-21`.
- Models: `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-2`. The IDs are complete as written. Never add a date suffix.
- `langchain-anthropic` 1.7.10 (released 2026-11-04).
- Pages used are listed under Links.

## Read this first

### Can 300 to 500 Source items run in parallel on Saturday?

Yes, with a concurrency cap, if the organisation is on the Start tier or above. That condition is not yet confirmed.

- Start tier gives Haiku 5.5 and Sonnet 5.5 each 4,000 requests, 2,000,000 uncached input tokens and 400,000 output tokens per minute. Each model has its own limits.
- The binding limit is output tokens. Extraction of 500 items is about 1M output tokens (estimate, thinking included), so it cannot finish in under about three minutes at Start tier.
- Use `asyncio.Semaphore(16)` and `max_retries=5`. Go to 32 only after 50 items run with no 429. Never send 500 requests at once: a ramp limit returns 429 for a sharp increase in usage even under the per-minute limits.
- Expected time at 16 (estimate, measure on 20 items first): triage about 2 minutes, extraction 5 to 10 minutes. On Saturday only the selected set of 20 trials runs (see `development-plan.md`); the Baseline load and the old three-minute recorded video are deferred (the 3-minute live demo is in scope).
- New organisations can start in an Evaluation tier with lower limits that are not published. On Friday open `https://platform.claude.com/usage/limits`, read the tier, and run `preflight()` from `references/runner.md` (PRD section 8, Model limits). If the limits are too low, use "Request tier increase" on that page.
- Message Batches API: half price and separate limits, but asynchronous. Most batches finish within 1 hour and a batch can take 24 hours. No per-item live progress. Do not use it for the live demo. See `references/batches.md`.

Tier tables, response headers and 429 variants: `references/rate-limits.md`.

### What contradicts the plan or will surprise you

- The most capable model is `claude-fable-5-2` ($8 / $40), not `claude-fable-5-1` ($10 / $50, still served). DxP needs neither.
- Usage tiers are now Evaluation, Start, Build, Scale and Custom. "Tier 1 to 4" no longer exists.
- Citations cannot be combined with structured outputs. Citations plus `output_config.format` returns a 400. Pick one per request.
- "Tool use that returns JSON" is not available on the extraction models: `tool_choice` of type `any` or `tool` returns a 400 on Sonnet 5.5 and Opus 5.5. Use structured outputs.
- `temperature`, `top_p` and `top_k` return a 400. There is no temperature 0. The SDK no longer has the parameters.
- Thinking is on by default and bills as output tokens. `thinking={"type": "disabled"}` returns a 400 on Sonnet 5.5 and Opus 5.5. Control depth with `output_config={"effort": ...}`.
- A safety refusal is an HTTP 200 with `stop_reason == "refusal"`. The `bio` category can fire on beneficial life sciences text, and it is billed.

## What DxP uses it for

- FR-2, FR-4: triage pass. Is the Source item about a lung cancer Diagnostic, and at which Lifecycle stage. `claude-haiku-5-5`.
- FR-5, FR-7, FR-8: extraction pass. Record fields in a fixed format, each with a quote. `claude-sonnet-5-5`.
- FR-18: confidence per field, plus the exact-string check that the quote is in the Source item.
- FR-13, FR-14, FR-15, FR-19, FR-21: topic match, why-it-matters line, Proposed change, Learned rule draft and query parsing. Same `messages.parse()` pattern with a different Pydantic model: Haiku 5.5 for the short classifications, Sonnet 5.5 for drafting.
- FR-4 and PRD section 8: parallel batch with live counts, after the limits are confirmed.

## Setup

```bash
pip install "anthropic>=2.8,<3" "pydantic>=2.7"
```

- Environment variable: `ANTHROPIC_API_KEY`. The client reads it. Never put the key in code.
- No beta headers are needed for structured outputs, citations, prompt caching, token counting or batches.
- Account: a Claude Console organisation with credit. Tier and limits: `https://platform.claude.com/usage/limits`. Spend cap: `https://platform.claude.com/settings/spend-limits`.

## Core patterns

One module. Triage and extraction use `messages.parse()` with a Pydantic model: the SDK sends the schema as `output_config.format` and validates the reply.

```python
import re
import unicodedata
from typing import Literal

from anthropic import AsyncAnthropic
from pydantic import BaseModel

TRIAGE_MODEL = "claude-haiku-5-5"
EXTRACT_MODEL = "claude-sonnet-5-5"  # try "claude-opus-5-5" only if gold-set accuracy falls short
TRIAGE_PROMPT = "..."   # frozen text: ontology + triage rules
EXTRACT_PROMPT = "..."  # frozen text: ontology + field definitions + the quote rules below

client = AsyncAnthropic(max_retries=5, timeout=180.0)  # reads ANTHROPIC_API_KEY


class ItemFailed(Exception):
    """Refusal or truncated output. Retrying the same model will not help."""


def system_blocks(text: str) -> list[dict]:
    # Prompt caching: identical bytes on every call of a pass, at least 512 tokens.
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def item_message(item_text: str) -> list[dict]:
    return [{"role": "user", "content": f"<source_item>\n{item_text}\n</source_item>"}]


def checked(resp):
    if resp.stop_reason != "end_turn" or resp.parsed_output is None:
        category = resp.stop_details.category if resp.stop_details else None
        raise ItemFailed(f"stop_reason={resp.stop_reason} category={category}")
    return resp.parsed_output


class Triage(BaseModel):
    is_lung_cancer_diagnostic: bool
    lifecycle_stage: Literal["discovery", "assay_development", "clinical_validation",
                             "regulatory_review", "marketed", "not_determined"]
    why: str  # one short sentence


async def triage(item_text: str) -> Triage:
    resp = await client.messages.parse(
        model=TRIAGE_MODEL,
        max_tokens=2000,                      # thinking tokens count toward max_tokens
        output_config={"effort": "low"},
        system=system_blocks(TRIAGE_PROMPT),
        messages=item_message(item_text),
        output_format=Triage,
    )
    return checked(resp)


FieldName = Literal[
    "diagnostic_name", "modality", "biomarker", "tumour_type", "stage_or_line", "sample_type",
    "clinical_use", "study_size", "key_result", "sponsor", "trial_id", "linked_drug", "regulatory_status",
]


class FieldEvidence(BaseModel):
    field: FieldName
    value: str
    quote: str         # one contiguous span copied character for character from the source item
    confidence: float  # 0 to 1; the schema cannot enforce the range, so clamp in code


class Extraction(BaseModel):
    fields: list[FieldEvidence]  # one entry per stated value; unstated fields are omitted


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip()


def quote_in_source(quote: str, source: str) -> bool:
    """FR-18 exact-string check. Only whitespace and Unicode form are normalised."""
    q = _norm(quote)
    return bool(q) and q in _norm(source)


async def extract(item_text: str) -> list[dict]:
    resp = await client.messages.parse(
        model=EXTRACT_MODEL,
        max_tokens=8000,
        output_config={"effort": "medium"},
        system=system_blocks(EXTRACT_PROMPT),
        messages=item_message(item_text),
        output_format=Extraction,
    )
    return [
        {**f.model_dump(),
         "confidence": min(max(f.confidence, 0.0), 1.0),
         "quote_check": "pass" if quote_in_source(f.quote, item_text) else "fail"}
        for f in checked(resp).fields
    ]
```

The field names follow the ten fields in the product brief plus regulatory status; architecture owns the final names. A list of entries is deliberate: it handles list-valued fields (trials, drugs), gives the no-data state by omission, and stays clear of the schema limits on optional and nullable properties.

Put these rules in `EXTRACT_PROMPT`. They are what makes quotes pass the check:

```text
Report a field only if the source item states it. Otherwise omit it. Never guess.
`quote` is one contiguous span copied character for character from the source item:
same spelling, numbers, punctuation and capitalisation. No ellipses, no joining of
separate passages, no corrections. The quote alone must support the value.
```

Effort: `low` on Haiku 5.5 is the documented level for simple high-volume requests. `medium` on Sonnet 5.5 is chosen here for batch throughput; the API default is `high`. Compare the two on the gold set before the full run.

A value with `quote_check == "fail"` is stored but never displayed (FR-18, FR-7). For quotes that are word for word by construction, and for the "quote supports the value" check, see `references/citations.md`.

Parallel runner (`run_batch`, `process`), `preflight()` and `count_tokens()`: the reference implementation in `references/runner.md` shows the approach; write your own during the event. The reference runner caps concurrency with a semaphore, sends the first call alone so the prompt cache exists for the rest, reports live counts for FR-4, and gives 429, 5xx and network failures one slower second sweep.

Confirm caching works: from the second call of a pass, `resp.usage.cache_read_input_tokens` is above zero.

LangChain pointer (the `dxp-langgraph-langsmith` skill covers the rest): `from langchain_anthropic import ChatAnthropic`, then `ChatAnthropic(model="claude-sonnet-5-5", max_tokens=8000).with_structured_output(Extraction, method="json_schema")`. The default `method="function_calling"` depends on forced tool use, which these models reject. Leave `temperature` unset (its default is `None`). Call the `anthropic` SDK directly for the batch passes: it exposes the headers, error codes and cache usage.

## Limits and costs

Prices per million tokens, standard API:

| Model | Use in DxP | Input | Output | Cache read | 5-minute cache write |
| --- | --- | --- | --- | --- | --- |
| `claude-haiku-5-5` | triage | $0.10 | $0.50 | $0.01 | $0.125 |
| `claude-sonnet-5-5` | extraction | $2 | $10 | $0.10 | $2.50 |
| `claude-opus-5-5` | escalation only | $4 | $20 | $0.20 | $5 |

- Haiku 5.5 prices are for prompts up to 100,000 tokens. Above that, the whole request is billed at five times these prices.
- Prompt caching: minimum 512 tokens on all three models, 5-minute lifetime refreshed on each read, `"ttl": "1h"` for a 1-hour lifetime at 2 times input price to write. Cache reads do not count toward the input tokens per minute limit. Caches are per model.
- Message Batches API: 50 percent off, and the discount stacks with caching.
- Cost estimate for 500 items through both passes (assumes 4,000-token items, a 3,000-token cached prefix, 300 output tokens for triage and 2,000 for extraction, thinking included): triage about $0.30, extraction about $14 on Sonnet 5.5 or $28 on Opus 5.5. Without caching the Sonnet pass costs about $3 more. Count 20 real items with `count_tokens()` and rescale.
- Start tier monthly spend cap: $500. Token counting: 5,000 requests per minute at Start tier.
- SDK defaults: 2 retries, 10-minute timeout, backoff from 0.5 s to 8 s, `retry-after` honoured. Worst-case wall clock per call is `timeout` times `max_retries + 1`.

## Gotchas

- 429 with `e.error_code == "ramp_limit_exceeded"`: usage rose too fast. Halve concurrency and climb again slowly.
- 429 with `e.error_code == "enforced_spend_limit_reached"`: no `retry-after`, and retries never succeed until the cap is raised.
- 529 `overloaded_error` (`anthropic.OverloadedError`): the API is busy for everyone. The SDK retries it. If it persists, switch that pass to another model.
- Input larger than the 1M-token context window: 400 `invalid_request_error`, "prompt is too long". An item over about 250,000 characters (about 100,000 tokens, the Haiku price threshold) is not a normal abstract or trial record. Flag it as failed with a reason. Do not truncate silently.
- `stop_reason == "max_tokens"` gives truncated JSON, and `messages.parse()` raises pydantic `ValidationError`. Raise `max_tokens`.
- Refusal: retrying the same model usually refuses again. Mark the item failed, or retry once on a different model (the documentation's example is `claude-opus-4-8`). Never name a schema field `reasoning`, `thinking` or `trace`: it can cause a `reasoning_extraction` refusal.
- `messages.parse()` has no top-level `cache_control` argument. Put `cache_control` on the system block.
- `output_format` takes a Pydantic class only. A raw schema goes in `output_config={"format": {"type": "json_schema", "schema": ...}}`.
- Schema limits: no `minimum`, `maximum`, `minLength` or `maxLength`; at most 24 optional properties and 16 union-typed ones (a nullable field is a union) per request. Enum casing is not guaranteed, so use lower-case values. The first call with a new schema is slower while the grammar compiles.
- The cache breaks without an error if the system text changes by one byte (a timestamp, an item ID) or if effort, thinking or the schema changes between calls. A prefix under 512 tokens is not cached.
- Passing an `httpx` client to SDK 2.x raises `TypeError`. Use a float timeout, or objects from `httpx2`.

## Fallback

- Limits too low or persistent 429: set concurrency to 4 and process the selected set one item at a time. (The Baseline load is deferred on Saturday.)
- One model overloaded: change the model constant. Sonnet 5.5, Opus 5.5 and Haiku 5.5 have separate limits. Haiku 5.5 at `effort="high"` can stand in for extraction.
- API unreachable during recording: replay stored extraction results from MongoDB and disclose it. (The memory write and Learned rule are deferred on Saturday.)

## Links

- Rate limits: https://platform.claude.com/docs/en/api/rate-limits
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Citations: https://platform.claude.com/docs/en/build-with-claude/citations
- Models and pricing: https://platform.claude.com/docs/en/about-claude/models/overview and https://platform.claude.com/docs/en/about-claude/pricing
- Errors: https://platform.claude.com/docs/en/api/errors
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Batch processing: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Token counting: https://platform.claude.com/docs/en/build-with-claude/token-counting
- Effort: https://platform.claude.com/docs/en/build-with-claude/effort
- Refusals and fallback: https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
- Context windows: https://platform.claude.com/docs/en/build-with-claude/context-windows
- Python SDK: https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python and https://github.com/anthropics/anthropic-sdk-python
- API version 2026-10-21: https://platform.claude.com/docs/en/api/migration-2026-10-21
- LangChain `ChatAnthropic`: https://reference.langchain.com/python/integrations/langchain_anthropic/ChatAnthropic/
