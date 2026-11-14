> Reference only. Do not copy this code into the project; it was written before the event.

# Message Batches API

Source: https://platform.claude.com/docs/en/build-with-claude/batch-processing, checked 2026-11-12. The code reuses `EXTRACT_MODEL`, `EXTRACT_PROMPT`, `Extraction`, `item_message` and `quote_in_source` from SKILL.md.

## Parallel calls or a batch

| | Parallel `messages.parse()` calls | Message Batches API |
| --- | --- | --- |
| Turnaround | Minutes, under your control | Most batches within 1 hour; up to 24 hours, then unfinished requests expire |
| Live progress | Per item | `request_counts` on each poll only |
| Price | Standard | 50 percent off input and output; stacks with caching |
| Limits | RPM, ITPM, OTPM and ramp limits | Separate limits; no ramp limits; does not use Messages limits |
| Cache hits | Reliable after the first call | Best effort, 30 to 98 percent in the docs |
| Streaming, server-side refusal fallback (beta) | Available | Not available |

Use parallel calls on Saturday. Use a batch only for the Baseline load when the tier limits are too low, and start it early: the turnaround is not guaranteed.

## Limits

- 100,000 requests or 256 MB per batch, whichever comes first.
- Results are kept for 29 days and come back in any order. Match on `custom_id`.
- `custom_id` must match `^[a-zA-Z0-9_-]{1,64}$`. A PubMed ID or NCT number is fine. Hash a URL.
- Not accepted inside a batch: `stream`, `speed`, `fallbacks`, `max_tokens: 0`.
- `messages.parse()` is not available for batches. Send the schema in `output_config.format` and validate the text yourself.

## Code

```python
import hashlib
import time

import anthropic
from anthropic import transform_schema
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

sync_client = anthropic.Anthropic()
SCHEMA = transform_schema(Extraction.model_json_schema())  # same transformation parse() applies


def custom_id(item_id: str) -> str:
    return hashlib.sha256(item_id.encode()).hexdigest()[:32]


def submit(items: list[dict]) -> str:
    batch = sync_client.messages.batches.create(requests=[
        Request(
            custom_id=custom_id(item["id"]),
            params=MessageCreateParamsNonStreaming(
                model=EXTRACT_MODEL,
                max_tokens=8000,
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
                system=[{"type": "text", "text": EXTRACT_PROMPT,
                         "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
                messages=item_message(item["text"]),
            ),
        )
        for item in items
    ])
    return batch.id


def wait(batch_id: str, poll_seconds: int = 30) -> None:
    while True:
        batch = sync_client.messages.batches.retrieve(batch_id)
        print(batch.processing_status, batch.request_counts)  # processing, succeeded, errored, canceled, expired
        if batch.processing_status == "ended":
            return
        time.sleep(poll_seconds)


def collect(batch_id: str, text_by_custom_id: dict[str, str]) -> tuple[dict, dict]:
    results, failed = {}, {}
    for entry in sync_client.messages.batches.results(batch_id):
        outcome = entry.result
        if outcome.type != "succeeded":            # errored, canceled or expired: not billed
            failed[entry.custom_id] = outcome.type
            continue
        message = outcome.message
        if message.stop_reason != "end_turn":      # a refusal comes back as succeeded
            failed[entry.custom_id] = f"stop_reason={message.stop_reason}"
            continue
        text = next(b.text for b in message.content if b.type == "text")
        source = text_by_custom_id[entry.custom_id]
        results[entry.custom_id] = [
            {**f.model_dump(), "quote_check": "pass" if quote_in_source(f.quote, source) else "fail"}
            for f in Extraction.model_validate_json(text).fields
        ]
    return results, failed
```

Notes:

- Keep a map from `custom_id` back to the Source item ID and text before submitting.
- An `errored` result with `outcome.error.error.type == "invalid_request_error"` needs a fixed request. Other errored results can be resubmitted as they are.
- Test one request shape with `client.messages.create()` before submitting 500, so a validation error does not fail the whole batch.
- The 1-hour cache lifetime is the documented advice for batches, because processing can take longer than 5 minutes.
- Cancel with `sync_client.messages.batches.cancel(batch_id)`.
