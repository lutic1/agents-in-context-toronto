> Reference only. Do not copy this code into the project; it was written before the event.

# Parallel runner, preflight and token counting

These extend the reference module in SKILL.md and show the approach; write your own during the event. They use `client`, `TRIAGE_MODEL`, `EXTRACT_MODEL`, `ItemFailed`, `system_blocks`, `item_message`, `triage` and `extract`. SDK behaviour checked against `anthropic` 2.8.0 on 2026-11-12.

## Runner (FR-4)

```python
import asyncio
from typing import Awaitable, Callable

import anthropic
from pydantic import ValidationError

RETRYABLE = (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError)


async def run_batch(items: list[dict], worker: Callable[[dict], Awaitable[object]],
                    concurrency: int = 16, on_progress: Callable[[dict], None] | None = None):
    """items need "id" and "text". Returns (results by id, failure reasons by id)."""
    results, failed, retry = {}, {}, []
    stats = {"total": len(items), "done": 0, "failed": 0}

    async def one(item: dict, sem: asyncio.Semaphore, final: bool) -> None:
        async with sem:
            try:
                results[item["id"]] = await worker(item)
                stats["done"] += 1
            except RETRYABLE as e:             # 429, 5xx, 529, network; the SDK already retried 5 times
                if getattr(e, "error_code", None) == "enforced_spend_limit_reached":
                    raise                      # monthly spend cap: nothing will succeed, stop the run
                if final:
                    failed[item["id"]] = repr(e)
                    stats["failed"] += 1
                else:
                    retry.append(item)
            except (ItemFailed, ValidationError, anthropic.APIStatusError) as e:
                failed[item["id"]] = repr(e)   # refusal, truncated JSON, 400 prompt too long, 401
                stats["failed"] += 1
        if on_progress:
            on_progress(dict(stats))           # write these counts where the UI reads them

    if not items:
        return results, failed
    sem = asyncio.Semaphore(concurrency)
    await one(items[0], sem, False)            # first call alone, so the prompt cache exists for the rest
    await asyncio.gather(*(one(i, sem, False) for i in items[1:]))
    if retry:
        await asyncio.sleep(30)                # let the per-minute limits refill
        again, slow = list(retry), asyncio.Semaphore(max(1, concurrency // 4))
        retry.clear()
        await asyncio.gather(*(one(i, slow, True) for i in again))
    return results, failed


async def process(item: dict) -> dict:
    t = await triage(item["text"])
    fields = await extract(item["text"]) if t.is_lung_cancer_diagnostic else []
    return {"triage": t.model_dump(), "fields": fields}

# results, failed = asyncio.run(run_batch(items, process, concurrency=16, on_progress=print))
```

How it behaves:

- `concurrency` counts Source items in flight. Each item makes one triage call and at most one extraction call, in sequence.
- The `except` order matters: `RateLimitError` and `InternalServerError` are subclasses of `APIStatusError`, so the retryable clause comes first.
- A cache entry is usable only after the first response starts. That is why the first item runs alone.
- For FR-4, add a count of items marked Early research in `process` or in `on_progress`. The callback runs after every item.
- Running the same batch twice must not create duplicates (FR-3). That is the database's job: upsert on the match key.
- Ramping: for the first run of the day call `run_batch(items[:50], process, concurrency=8)`, then the rest at 16. Raise to 32 only if the first 50 produced no 429.
- If `failed` holds `ramp_limit_exceeded` errors after the second sweep, rerun those items at a quarter of the concurrency.

## Preflight (PRD section 8, Model limits)

```python
async def preflight() -> None:
    """Confirms the key works and prints the limits that apply to it."""
    for model in (TRIAGE_MODEL, EXTRACT_MODEL):
        raw = await client.messages.with_raw_response.create(
            model=model, max_tokens=16, messages=[{"role": "user", "content": "ping"}])
        print(model, {k: raw.headers.get(f"anthropic-ratelimit-{k}") for k in (
            "requests-limit", "input-tokens-limit", "output-tokens-limit",
            "input-tokens-remaining", "output-tokens-remaining")})

# asyncio.run(preflight())
```

- Costs a fraction of a cent. An `anthropic.AuthenticationError` means the key is wrong or missing. An `anthropic.NotFoundError` means the model ID is wrong.
- Compare the printed limits with the tables in `rate-limits.md`. Start tier shows 4000 requests, 2000000 input tokens and 400000 output tokens for both models. Lower numbers mean the Evaluation tier or a workspace limit.
- For the parsed message as well, call `await raw.parse()`.

## Token counting and the cost estimate

```python
async def count_tokens(model: str, system_text: str, item_text: str) -> int:
    r = await client.messages.count_tokens(
        model=model, system=system_blocks(system_text), messages=item_message(item_text))
    return r.input_tokens
```

- Free. Its rate limit is separate from message creation: 5,000 requests per minute at Start tier.
- The result is an estimate and can differ from billed input by a small amount. It ignores caching.
- Count with the model you will call. Never use `tiktoken` or a character rule for billing figures.
- To size the batch: count the system prompt once and 20 real Source items, take the mean, multiply by the item count, and apply the prices in SKILL.md. Output tokens cannot be counted in advance; read `resp.usage.output_tokens` from the same 20 items run for real.
- After a run, the true figures are in each response: `resp.usage.input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` and `output_tokens`. Total input is the sum of the first three.
