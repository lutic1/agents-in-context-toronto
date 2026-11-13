# Rate limits, headers and 429 handling

Source: https://platform.claude.com/docs/en/api/rate-limits, checked 2026-11-12. The Console shows the values that apply to the DxP organisation; these tables are the published standard limits.

## How limits work

- Limits are per organisation and per model. Each row below has its own requests per minute (RPM), input tokens per minute (ITPM) and output tokens per minute (OTPM).
- Token bucket: capacity refills continuously. 60 RPM can be enforced as 1 request per second, so a short burst can fail under the per-minute figure.
- ITPM counts `input_tokens` and `cache_creation_input_tokens`. It does not count `cache_read_input_tokens`. Prompt caching therefore raises throughput.
- OTPM counts tokens actually generated, thinking included. A high `max_tokens` does not count against it.
- Tiers: Evaluation (new organisations, limits below the tables, not published), Start, Build, Scale, Custom. An organisation moves up automatically with usage history. Higher limits: "Request tier increase" on `https://platform.claude.com/usage/limits`.

## Standard limits by tier

| Model | Start RPM / ITPM / OTPM | Build RPM / ITPM / OTPM | Scale RPM / ITPM / OTPM |
| --- | --- | --- | --- |
| Claude Haiku 5.5 | 4,000 / 2,000,000 / 400,000 | 10,000 / 5,000,000 / 1,000,000 | 13,000 / 10,000,000 / 2,000,000 |
| Claude Sonnet 5.5 | 4,000 / 2,000,000 / 400,000 | 10,000 / 5,000,000 / 1,000,000 | 13,000 / 10,000,000 / 2,000,000 |
| Claude Opus 5.5 | 4,000 / 2,000,000 / 400,000 | 10,000 / 5,000,000 / 1,000,000 | 13,000 / 10,000,000 / 2,000,000 |
| Claude Fable 5.2 | 4,000 / 500,000 / 100,000 | 10,000 / 1,500,000 / 300,000 | 13,000 / 4,000,000 / 800,000 |

| Other limit | Start | Build | Scale |
| --- | --- | --- | --- |
| Monthly spend cap | $500 | $1,000 | $200,000 |
| Token counting RPM (separate from Messages) | 5,000 | 10,000 | 20,000 |
| Message Batches API RPM | 1,000 | 2,000 | 4,000 |
| Batch requests in processing queue | 200,000 | 300,000 | 500,000 |
| Batch requests per batch | 100,000 | 100,000 | 100,000 |

## What the DxP batch needs

Estimates for 500 items, with a 3,000-token cached prefix, 4,000-token items and 2,000 output tokens per extraction:

| Pass | Requests | Uncached input | Output | Binding limit at Start tier |
| --- | --- | --- | --- | --- |
| Triage, Haiku 5.5 | 500 | 2.0M | 0.15M | none within one minute |
| Extraction, Sonnet 5.5 | up to 500 | 2.0M | 1.0M | OTPM 400,000: at least 2.5 minutes |

Concurrency 16 with calls of 10 to 20 seconds is 48 to 96 calls per minute, about 100,000 to 190,000 output tokens per minute. Concurrency 32 is near the Start tier OTPM limit. Build tier allows 64.

## Ramp limits

- A sharp increase in token usage on a model returns 429 even under the RPM, ITPM and OTPM limits. A burst within a few seconds counts.
- The ramp limit is the recent per-minute peak plus a step. It rises each minute as successful usage grows and stops at the rate limit.
- `error.details.error_code` is `ramp_limit_exceeded`. In the SDK: `e.error_code`.
- Fix: wait `retry-after`, hold at a level that succeeds, then increase by at most one step per minute. Start bulk jobs low and spread requests evenly.
- The Message Batches API is not subject to ramp limits.

## 429 variants

| `e.error_code` | Meaning | Action |
| --- | --- | --- |
| none | RPM, ITPM or OTPM exceeded. The message names which. | Wait `retry-after`. The SDK does this. Lower concurrency if it recurs. |
| `ramp_limit_exceeded` | Usage rose too fast. | Halve concurrency, climb slowly. |
| `enforced_spend_limit_reached` | Monthly tier spend cap reached. No `retry-after`. | Stop. Request a tier increase. Retries fail until then. |

A spend limit the organisation set itself returns 400 `invalid_request_error`, with a message starting "You have reached your specified API usage limits".

## Response headers

Every response carries these. Read them with `client.messages.with_raw_response.create(...)`, then `raw.headers.get(name)` and `await raw.parse()` on the async client.

| Header | Meaning |
| --- | --- |
| `retry-after` | Seconds to wait before retrying. Not on every 429. |
| `anthropic-ratelimit-requests-limit`, `-remaining`, `-reset` | Request limit, remaining, and the RFC 3339 time it is full again |
| `anthropic-ratelimit-input-tokens-limit`, `-remaining`, `-reset` | Input tokens. Remaining is rounded to the nearest thousand. |
| `anthropic-ratelimit-output-tokens-limit`, `-remaining`, `-reset` | Output tokens |
| `anthropic-ratelimit-tokens-limit`, `-remaining`, `-reset` | The most restrictive token limit in effect |
| `request-id` | Quote it to support. Also `message._request_id` and `e.request_id`. |

## Where to look

- Tier and limits: `https://platform.claude.com/usage/limits`
- Usage and rate-limit charts, cache hit rate: `https://platform.claude.com/usage`
- Spend cap: `https://platform.claude.com/settings/spend-limits`
- The Rate Limits API (`client.organization.rate_limits.list()`) needs an Admin API key and is not available to individual Console accounts. The Console page and the headers are enough for Saturday.

## SDK retry behaviour (anthropic 2.8.0)

- Retries connection errors, timeouts, 408, 409, 429 and every status of 500 or above, including 529.
- Default `max_retries=2`. Set on the client or per call with `client.with_options(max_retries=5)`.
- Waits `retry-after` when the response has it. Otherwise 0.5 s doubling to a maximum of 8 s, with jitter.
- Default timeout 10 minutes; a timed-out request is retried too.
- Exceptions: `anthropic.RateLimitError` (429), `anthropic.OverloadedError` (529) and other `anthropic.InternalServerError` (500 and above), `anthropic.BadRequestError` (400), `anthropic.APITimeoutError` and `anthropic.APIConnectionError` (network). `APIStatusError` carries `status_code`, `error_code`, `request_id` and `response`.
